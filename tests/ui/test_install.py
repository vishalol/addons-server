import pytest

from pages.desktop.home import Home


@pytest.mark.nondestructive
def test_installing_an_addon(
        my_base_url, selenium, gen_webext2):
    # url = my_base_url + '/' + gen_webext1.path
    page = Home(selenium, my_base_url).open()
    # assert False
    import time
    time.sleep(500)
