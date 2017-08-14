import random

from rest_framework import serializers

from olympia.amo.tests import user_factory, addon_factory
from olympia import amo
from olympia.addons.forms import icons
from olympia.addons.models import Preview
from olympia.addons.utils import generate_addon_guid
from olympia.constants.applications import FIREFOX
from olympia.constants.base import (
    ADDON_EXTENSION,
    STATUS_PUBLIC
)
from olympia.landfill.collection import generate_collection
from olympia.reviews.models import Review
from olympia.users.models import UserProfile


class GenerateAddonsSerializer(serializers.Serializer):
    count = serializers.IntegerField(default=10)

    def create(self):
        for idx in range(self.validated_data['count']):
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
                developer_comments='This is a testing addon.',
            )
            Preview.objects.create(addon=addon, position=1)
            Review.objects.create(addon=addon, rating=5, user=user_factory())
            Review.objects.create(addon=addon, rating=3, user=user_factory())
            addon.reload()

            addon.save()
            generate_collection(
                addon,
                app=FIREFOX,
                type=amo.COLLECTION_FEATURED)
            print(
                'Created addon {0} for testing successfully'
                .format(addon.name))
