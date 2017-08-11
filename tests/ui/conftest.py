import datetime
import json
import os
import random
import string
import urlparse

import jwt
import pytest
import requests
from django.core.management import call_command
from django.conf import settings
from fxapom.fxapom import DEV_URL, PROD_URL, FxATestAccount
from olympia import amo
from olympia.addons.forms import icons
from olympia.addons.models import AddonUser, Preview
from olympia.addons.utils import generate_addon_guid
from olympia.amo.tests import (
    addon_factory,
    create_switch,
    user_factory,
    version_factory,
)
from olympia.constants.applications import APPS, FIREFOX
from olympia.constants.base import (
    ADDON_EXTENSION,
    ADDON_PERSONA,
    STATUS_PUBLIC
)
from olympia.landfill.collection import generate_collection
from olympia.landfill.generators import generate_themes
from olympia.reviews.models import Review
from olympia.users.models import UserProfile


@pytest.fixture(scope='function')
def my_base_url(base_url, request, pytestconfig, variables):
    pytestconfig.option.usingliveserver = False

    with open('tests/ui/variables.json') as fobj:
        variables.update(json.load(fobj))

    return base_url


@pytest.fixture
def capabilities(capabilities):
    # In order to run these tests in Firefox 48, marionette is required
    capabilities['marionette'] = True
    capabilities['acceptInsecureCerts'] = True
    return capabilities


@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.set_preference(
        'extensions.install.requireBuiltInCerts', False)
    firefox_options.set_preference('xpinstall.signatures.required', False)
    firefox_options.set_preference('extensions.webapi.testing', True)
    return firefox_options


@pytest.fixture
def fxa_account(my_base_url):
    """Account used to login to the AMO site."""
    url = DEV_URL if 'dev' or 'localhost' in my_base_url else PROD_URL
    return FxATestAccount(url)


@pytest.fixture
def jwt_issuer(my_base_url, variables):
    """JWT Issuer from variables file or env variable named 'JWT_ISSUER'"""
    try:
        hostname = urlparse.urlsplit(my_base_url).hostname
        return variables['api'][hostname]['jwt_issuer']
    except KeyError:
        return os.getenv('JWT_ISSUER')


@pytest.fixture
def jwt_secret(my_base_url, variables):
    """JWT Secret from variables file or env vatiable named "JWT_SECRET"""
    try:
        hostname = urlparse.urlsplit(my_base_url).hostname
        return variables['api'][hostname]['jwt_secret']
    except KeyError:
        return os.getenv('JWT_SECRET')


@pytest.fixture
def initial_data(my_base_url, jwt_token):
    """Fixture used to fill database will dummy addons.

    Creates exactly 10 random addons with users that are also randomly
    generated.
    """
    headers = {'Authorization': 'JWT {token}'.format(token=jwt_token)}

    response = requests.post(
        '{base}/api/v3/landfill/cleanup/'.format(base=my_base_url),
        headers=headers)
    print('XXXXXXXXXXXXXXXXXXXXXXX', response.json())

    assert requests.codes.ok == response.status_code

    url = '{base_url}/api/v3/landfill/generate-addons/'.format(
        base_url=my_base_url)
    print('xxxxxxxxx', url)

    response = requests.post(
        url,
        data={'count': 10},
        headers=headers)

    print('XXXXXXXXXXXXXXXXXXXXXXX', response.json())

    assert requests.codes.created == response.status_code

    yield

    response = requests.post(
        '{base}/api/v3/landfill/cleanup/'.format(base=my_base_url))
    assert requests.codes.ok == response.status_code


@pytest.fixture
def theme(create_superuser, pytestconfig):
    """Creates a custom theme named 'Ui-Test Theme'.

    This theme will be a featured theme and will belong to the user created by
    the 'create_superuser' fixture.

    It has one author.
    """
    if not pytestconfig.option.usingliveserver:
        return

    addon = addon_factory(
        status=STATUS_PUBLIC,
        type=ADDON_PERSONA,
        average_daily_users=4242,
        users=[UserProfile.objects.get(username='uitest')],
        average_rating=5,
        description=u'My UI Theme description',
        file_kw={
            'hash': 'fakehash',
            'platform': amo.PLATFORM_ALL.id,
            'size': 42,
        },
        guid=generate_addon_guid(),
        homepage=u'https://www.example.org/',
        name=u'Ui-Test Theme',
        public_stats=True,
        slug='ui-test',
        summary=u'My UI theme summary',
        support_email=u'support@example.org',
        support_url=u'https://support.example.org/support/ui-theme-addon/',
        tags=['some_tag', 'another_tag', 'ui-testing',
                'selenium', 'python'],
        total_reviews=777,
        weekly_downloads=123456,
        developer_comments='This is a testing theme, used within pytest.',
    )
    addon.save()
    generate_collection(addon, app=FIREFOX,
                        author=UserProfile.objects.get(username='uitest'))
    print('Created Theme {0} for testing successfully'.format(addon.name))
    return addon


@pytest.fixture
def selenium(selenium):
    selenium.implicitly_wait(10)
    selenium.maximize_window()
    return selenium


@pytest.fixture
def addon(create_superuser, pytestconfig):
    """Creates a custom addon named 'Ui-Addon'.

    This addon will be a featured addon and will have a featured collecton
    attatched to it. It will belong to the user created by the
    'create_superuser' fixture.

    It has 1 preview, 5 reviews, and 2 authors. The second author is named
    'ui-tester2'. It has a version number as well as a beta version.
    """
    if not pytestconfig.option.usingliveserver:
        return

    default_icons = [x[0] for x in icons() if x[0].startswith('icon/')]
    addon = addon_factory(
        status=STATUS_PUBLIC,
        type=ADDON_EXTENSION,
        average_daily_users=5567,
        users=[UserProfile.objects.get(username='uitest')],
        average_rating=5,
        description=u'My Addon description',
        file_kw={
            'platform': amo.PLATFORM_ALL.id,
            'size': 42,
        },
        guid='test-desktop@nowhere',
        homepage=u'https://www.example.org/',
        icon_type=random.choice(default_icons),
        name=u'Ui-Addon',
        public_stats=True,
        slug='ui-test',
        summary=u'My Addon summary',
        support_email=u'support@example.org',
        support_url=u'https://support.example.org/support/ui-test-addon/',
        tags=['some_tag', 'another_tag', 'ui-testing',
              'selenium', 'python'],
        total_reviews=888,
        weekly_downloads=2147483647,
        developer_comments='This is a testing addon, used within pytest.',
        is_experimental=True,
    )
    Preview.objects.create(addon=addon, position=1)
    Review.objects.create(addon=addon, rating=5, user=user_factory())
    Review.objects.create(addon=addon, rating=3, user=user_factory())
    Review.objects.create(addon=addon, rating=2, user=user_factory())
    Review.objects.create(addon=addon, rating=1, user=user_factory())
    addon.reload()
    AddonUser.objects.create(user=user_factory(username='ui-tester2'),
                             addon=addon, listed=True)
    version_factory(addon=addon, file_kw={'status': amo.STATUS_BETA},
                    version='1.1beta')
    addon.save()
    generate_collection(addon, app=FIREFOX)
    print('Created addon {0} for testing successfully'.format(addon.name))
    return addon


@pytest.fixture
def minimal_addon(create_superuser, pytestconfig):
    """Creates a custom addon named 'Ui-Addon-2'.

    It will belong to the user created by the 'create_superuser' fixture.

    It has 1 preview, and 2 reviews.
    """
    if not pytestconfig.option.usingliveserver:
        return

    default_icons = [x[0] for x in icons() if x[0].startswith('icon/')]
    addon = addon_factory(
        status=STATUS_PUBLIC,
        type=ADDON_EXTENSION,
        average_daily_users=7000,
        users=[UserProfile.objects.get(username='uitest')],
        average_rating=3,
        description=u'My Addon description',
        file_kw={
            'hash': 'fakehash',
            'platform': amo.PLATFORM_ALL.id,
            'size': 42,
        },
        guid=generate_addon_guid(),
        icon_type=random.choice(default_icons),
        name=u'Ui-Addon-2',
        public_stats=True,
        slug='ui-test-2',
        summary=u'My Addon summary',
        tags=['some_tag', 'another_tag', 'ui-testing',
              'selenium', 'python'],
        total_reviews=777,
        weekly_downloads=22233879,
        developer_comments='This is a testing addon, used within pytest.',
    )
    Preview.objects.create(addon=addon, position=1)
    Review.objects.create(addon=addon, rating=5, user=user_factory())
    Review.objects.create(addon=addon, rating=3, user=user_factory())
    addon.reload()

    addon.save()
    generate_collection(addon, app=FIREFOX, type=amo.COLLECTION_FEATURED)
    print('Created addon {0} for testing successfully'.format(addon.name))
    return addon


@pytest.fixture
def themes(create_superuser, pytestconfig):
    """Creates exactly 6 themes that will be not featured.

    These belong to the user created by the 'create_superuser' fixture.
    It will also create 6 themes that are featured with random authors.
    """
    if not pytestconfig.option.usingliveserver:
        return

    owner = UserProfile.objects.get(username='uitest')
    generate_themes(6, owner)
    for _ in range(6):
        addon = addon_factory(status=STATUS_PUBLIC, type=ADDON_PERSONA)
        generate_collection(addon, app=FIREFOX)


@pytest.fixture
def collections(pytestconfig):
    """Creates exactly 4 collections that are featured.

    This fixture uses the generate_collection function from olympia.
    """
    if not pytestconfig.option.usingliveserver:
        return

    for _ in range(4):
        addon = addon_factory(type=amo.ADDON_EXTENSION)
        generate_collection(
            addon, APPS['firefox'], type=amo.COLLECTION_FEATURED)


@pytest.fixture
def gen_webext(create_superuser, pytestconfig, tmpdir):
    """Creates a a blank webextenxtension."""
    if not pytestconfig.option.usingliveserver:
        return

    from olympia.files.models import File, FileUpload
    from olympia.versions.models import Version
    from olympia.amo.tests.test_helpers import get_addon_file
    from django.utils.translation import activate
    import os

    manifest = tmpdir.mkdir('webext').join('manifest.json')
    # print(manifest)
    webext = {
        'applications': {
            'gecko': {
                'id': 'ui-addon@mozilla.org',
            }
        },
        'manifest_version': 2,
        'name': 'Ui-Addon',
        'version': 3.1,
        'description': 'Blank Webextension for testing',
        'permissions': [],
        'background': {
            'scripts': 'background.js',
        }
    }
    activate('en')
    # manifest.write(json.dump(webext, manifest, indent=2))
    # json.dump(webext, manifest, indent=2)
    with open(str(manifest), 'w') as outfile:
        json.dump(webext, outfile, indent=2)
    default_icons = [x[0] for x in icons() if x[0].startswith('icon/')]
    addon = addon_factory(
        status=STATUS_PUBLIC,
        type=ADDON_EXTENSION,
        average_daily_users=5567,
        users=[UserProfile.objects.get(username='uitest')],
        average_rating=5,
        description=u'My Addon description',
        file_kw={
            'hash': 'fakehash',
            'platform': amo.PLATFORM_ALL.id,
            'size': 42,
        },
        guid='firebug@software.joehewitt.com',
        homepage=u'https://www.example.org/',
        icon_type=random.choice(default_icons),
        name=u'Ui-Addon',
        public_stats=True,
        slug='ui-test',
        summary=u'My Addon summary',
        support_email=u'support@example.org',
        support_url=u'https://support.example.org/support/ui-test-addon/',
        tags=['some_tag', 'another_tag', 'ui-testing',
              'selenium', 'python'],
        total_reviews=888,
        weekly_downloads=2147483647,
        developer_comments='This is a testing addon, used within pytest.',
    )
    Preview.objects.create(addon=addon, position=1)
    version = version_factory(addon=addon, file_kw={'status': amo.STATUS_BETA},
                    version='1.1beta')
    addon.reload()
    # zip as .xpi
    # os.system('zip -r {0} {1}'.format(tmpdir.join('webext_comp.xpi'), manifest))
    # return tmpdir.join('webext_comp.xpi').open()
    # print(tmpdir.listdir())
    # with open(str(tmpdir.join('webext_comp.xpi')), 'r') as outfile:
    Version.from_upload(upload=upload, addon=addon, platforms=[amo.PLATFORM_ALL.id], channel=amo.RELEASE_CHANNEL_LISTED)
    addon.save()


# @pytest.fixture
# def gen_webext2(addon):
#     import django

#     from olympia.files.models import File, FileUpload
#     from olympia.versions.models import Version
#     from olympia.amo.tests.test_helpers import get_addon_file
#     from django.utils.translation import activate
#     from olympia.files.tests.test_helpers import get_file

#     activate('en')

#     f = File()
#     upload = FileUpload.objects.create(path=get_file('webextension_no_id.xpi'), hash=f.generate_hash(get_file('webextension_no_id.xpi')))
#     # upload = FileUpload.objects.create(path=tmpdir.join('webext_comp.xpi'))
#     Version.from_upload(upload=upload, addon=addon, platforms=[amo.PLATFORM_ALL.id], channel=amo.RELEASE_CHANNEL_LISTED)


@pytest.fixture
def create_superuser(my_base_url, tmpdir, variables):
    """Creates a superuser."""
    if not pytestconfig.option.usingliveserver:
        return

    create_switch('super-create-accounts')
    call_command('loaddata', 'initial.json')

    call_command(
        'createsuperuser',
        interactive=False,
        username='uitest',
        email='uitester@mozilla.org',
        add_to_supercreate_group=True,
        save_api_credentials=str(tmpdir.join('variables.json')),
        hostname=urlparse.urlsplit(my_base_url).hostname
    )
    with tmpdir.join('variables.json').open() as f:
        variables.update(json.load(f))


@pytest.fixture
def user(my_base_url, fxa_account, jwt_token):
    """This creates a user for logging into the AMO site."""
    url = '{base_url}/api/v3/accounts/super-create/'.format(
        base_url=my_base_url)
    print('xxxxxxxxx', url)
    params = {
        'email': fxa_account.email,
        'password': fxa_account.password,
        'username': fxa_account.email.split('@')[0]}
    headers = {'Authorization': 'JWT {token}'.format(token=jwt_token)}
    response = requests.post(url, data=params, headers=headers)
    print('XXXXXXXXXXXXXXXXXXXXXXX', response.json())
    assert requests.codes.created == response.status_code
    params.update(response.json())
    return params


@pytest.fixture
def jwt_token(my_base_url, jwt_issuer, jwt_secret):
    """This creates a JWT Token"""
    payload = {
        'iss': jwt_issuer,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=30)}
    return jwt.encode(payload, jwt_secret, algorithm='HS256')


def pytest_configure(config):
    from olympia.amo.tests import prefix_indexes

    prefix_indexes(config)


@pytest.fixture(scope='session')
def es_test(pytestconfig):
    from olympia.amo.tests import (
        start_es_mocks, stop_es_mocks, amo_search, setup_es_test_data)

    stop_es_mocks()

    es = amo_search.get_es(timeout=settings.ES_TIMEOUT)
    _SEARCH_ANALYZER_MAP = amo.SEARCH_ANALYZER_MAP
    amo.SEARCH_ANALYZER_MAP = {
        'english': ['en-us'],
        'spanish': ['es'],
    }

    setup_es_test_data(es)

    yield

    amo.SEARCH_ANALYZER_MAP = _SEARCH_ANALYZER_MAP
    start_es_mocks()
