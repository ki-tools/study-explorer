import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@pytest.fixture
def hide_cookie_banner(selenium):
    def _f():
        selenium.find_element_by_class_name('cookie-close').click()
        WebDriverWait(selenium, 3).until(EC.invisibility_of_element_located((By.CLASS_NAME, 'cookie-banner')))
    yield _f

