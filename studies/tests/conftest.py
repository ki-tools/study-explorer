import time

import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@pytest.fixture
def hide_cookie_banner(selenium):
    def _f():
        cookie_banner = None
        manage_button = None
        while cookie_banner is None and manage_button is None:
            try:
                cookie_banner = selenium.find_element_by_id('onetrust-banner-sdk')
            except:
                pass
            try:
                manage_button = selenium.find_element_by_id('ot-sdk-btn-floating')
            except:
                pass
            if cookie_banner is None and manage_button is None:
                time.sleep(0.5)

        if cookie_banner:
            selenium.find_element_by_id('onetrust-accept-btn-handler').click()
            # Wait for the banner to be hidden.
            WebDriverWait(selenium, 5).until(EC.invisibility_of_element_located((By.ID, 'onetrust-banner-sdk')))

        # Wait for the settings button to be visible.
        WebDriverWait(selenium, 5).until(EC.visibility_of_element_located((By.ID, 'ot-sdk-btn-floating')))
    yield _f

