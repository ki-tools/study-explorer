# Copyright 2017-present, Bill & Melinda Gates Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from django.core.urlresolvers import reverse
from django.core.management import call_command

from .factories import (
    StudyFactory,
    StudyVariableFactory,
    DomainFactory,
    FilterFactory,
    AgeDomainFactory,
)

from ..models import Study, Variable


def scroll_shim(passed_in_driver, obj):
    x = obj.location['x']
    y = obj.location['y']
    scroll_by_coord = 'window.scrollTo(%s,%s);' % (
        x,
        y
    )
    scroll_nav_out_of_way = 'window.scrollBy(0, -120);'
    passed_in_driver.execute_script(scroll_by_coord)
    passed_in_driver.execute_script(scroll_nav_out_of_way)


@pytest.fixture
def page(live_server, selenium, transactional_db):
    selenium.get(live_server.url)
    yield selenium


@pytest.fixture
def setup_domain_and_load_data(transactional_db):
    AgeDomainFactory()
    rel_domain = DomainFactory(code='RELTIVE', label='Relative', is_qualifier=True)
    FilterFactory(study_field=None)
    FilterFactory(domain=rel_domain, label='Relative', study_field=None)

    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, 'IDX_SAMPLE.csv')
    call_command('load_idx', sample_csv)


def test_title_of_home_page_is_HBGD_Data_Store_Server(page):
    assert 'HBGD Data Store Server' in page.title


def test_it_shows_the_cookie_banner(page):
    cookie_banner = page.find_element_by_class_name('cookie-banner')
    assert cookie_banner.is_displayed() is True


def test_it_hides_the_cookie_banner(page, live_server, selenium, hide_cookie_banner):
    cookie_banner = page.find_element_by_class_name('cookie-banner')
    assert cookie_banner.is_displayed() is True

    hide_cookie_banner()
    assert cookie_banner.is_displayed() is False

    # reload the page and make sure the banner does not show
    selenium.get(live_server.url)
    cookie_banner = selenium.find_element_by_class_name('cookie-banner')
    assert cookie_banner.is_displayed() is False


def test_admin_panel_redirect_if_no_studies(page):
    admin_panel = page.find_element_by_name('admin_panel')
    assert 'Admin Portal' in admin_panel.text


def test_study_panels_on_home_even_if_no_domains(live_server, selenium, transactional_db, hide_cookie_banner):
    StudyVariableFactory(studies=StudyFactory.create_batch(3))
    selenium.get(live_server.url)
    hide_cookie_banner()

    panel = selenium.find_element_by_name('study-list_panel')
    assert 'Study List' in panel.text

    panel = selenium.find_element_by_name('study-filter_panel')
    assert 'Study Filter' in panel.text


def test_all_panels_on_home_if_data_loaded(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    selenium.get(live_server.url)
    hide_cookie_banner()

    panel = selenium.find_element_by_name('study-list_panel')
    assert 'Study List' in panel.text

    panel = selenium.find_element_by_name('study-filter_panel')
    assert 'Study Filter' in panel.text

    panel = selenium.find_element_by_name('study-explorer_panel')
    assert 'Study Explorer' in panel.text

    panel = selenium.find_element_by_name('variable-list_panel')
    assert 'Variable List' in panel.text


def test_study_filter_accordion_expands_showing_domains(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    """Checks that clicking the accordion expands the domain filter"""

    url = live_server.url + reverse('study-filter')
    selenium.get(url)
    hide_cookie_banner()

    accordions = selenium.find_elements_by_class_name("accordion-navigation")
    for accordion in accordions:
        accordion.click()

    qual_filter = selenium.find_element_by_id("id_RELTIVE_1")
    assert qual_filter.is_displayed()

    domain_search = selenium.find_element_by_id("id_SAMPLE_1")
    assert domain_search.is_displayed()


def test_study_explorer_shows_tabs_for_domain(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    """Checks that tabs are shown for the domains"""

    url = live_server.url + reverse('study-explorer')
    selenium.get(url)
    hide_cookie_banner()

    study_checkbox = selenium.find_element_by_id("id_study_1")
    if 'firefox' in selenium.capabilities['browserName']:
        scroll_shim(selenium, study_checkbox)
    ActionChains(selenium).move_to_element(study_checkbox).click().perform()

    apply_button = selenium.find_element_by_id("submit-id-apply")
    apply_button.click()

    WebDriverWait(selenium, 10).until(EC.presence_of_element_located((By.ID, "RELTIVE_tab")))

    age_variable_tab = selenium.find_element_by_id("AGECAT_tab")
    reltive_variable_tab = selenium.find_element_by_id("RELTIVE_tab")
    reltive_by_age_tab = selenium.find_element_by_id("RELTIVE_tab_age")
    sample_domain_variable_tab = selenium.find_element_by_id("SAMPLE_tab")
    sample_domain_by_age_tab = selenium.find_element_by_id("SAMPLE_tab_age")

    # reltive content should be visible and sample not (because alphabetically ordererd)
    assert age_variable_tab.is_displayed() is True
    assert reltive_by_age_tab.is_displayed() is True
    assert sample_domain_by_age_tab.is_displayed() is False
    assert sample_domain_variable_tab.is_displayed() is False

    sample_tabs = selenium.find_elements_by_css_selector("[href*='#SAMPLE_tab']")
    assert len(sample_tabs) == 2
    for tab in sample_tabs:
        tab.click()

    # Now sample content should be visible and reltive content not visible
    assert reltive_variable_tab.is_displayed() is False
    assert reltive_by_age_tab.is_displayed() is False
    assert sample_domain_variable_tab.is_displayed() is True
    assert sample_domain_by_age_tab.is_displayed() is True


def test_study_explorer_autocomplete_returns_tabs(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    study_id = "CPP"
    n = 0

    url = live_server.url + reverse('study-explorer')
    selenium.get(url)
    hide_cookie_banner()

    study_search = selenium.find_element_by_id("id_search")

    # wait for autocomplete to populate
    while selenium.execute_script('return $("#id_search").autocomplete( "widget").toArray()[0].innerText') == "":
        study_search.send_keys(study_id[n])
        n += 1
        time.sleep(1)

    choices = selenium.execute_script('return $("#id_search").autocomplete( "widget").toArray()[0].innerText').strip()
    assert choices == study_id

    study_search.send_keys(Keys.RETURN)

    apply_button = selenium.find_element_by_id("submit-id-apply")
    apply_button.click()

    tabs = WebDriverWait(selenium, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tabs")))
    assert tabs.is_displayed()


def test_filter_by_variable_code_returns_variable_to_field(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    code = "RELTIVE"
    mother = "Mother"
    n = 0

    url = live_server.url + reverse('variable-list', kwargs={"domain_code": code})
    selenium.get(url)
    hide_cookie_banner()

    variable_search = selenium.find_element_by_id("id_variable")

    # wait for autocomplete to populate
    while selenium.execute_script('return $("#id_variable").autocomplete( "widget").toArray()[0].innerText') == "":
        variable_search.send_keys(mother[n])
        n += 1
        time.sleep(1)

    choices = selenium.execute_script('return $("#id_variable").autocomplete( "widget").toArray()[0].innerText').strip()
    assert choices == "Mother"

    variable_search.send_keys(Keys.RETURN)
    assert variable_search.get_attribute('value') == "Mother"


def test_pagination_at_top_of_page(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    code = "RELTIVE"
    url = live_server.url + reverse('variable-list', kwargs={"domain_code": code})
    selenium.get(url)
    hide_cookie_banner()

    assert selenium.find_element_by_class_name("pagination")


def test_filter_to_explorer_transition(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    var_id = Variable.objects.get(domain__code='RELTIVE', label='Child').id
    url = live_server.url + reverse('study-filter') + '?RELTIVE=%s' % var_id
    explorer_url = live_server.url + reverse('study-explorer') + '?RELTIVE=%s' % var_id

    selenium.get(url)
    hide_cookie_banner()

    chevron = selenium.find_element_by_class_name("fa-chevron-right")
    chevron.click()

    timeout = 5
    try:
        element_present = EC.presence_of_element_located((By.ID, 'div_id_search'))
        WebDriverWait(selenium, timeout).until(element_present)
    except TimeoutException:
        # ToDo - don't understand why this is in TryExcept
        print("Timed out waiting for page to load")

    # Correctly redirected
    assert selenium.current_url == explorer_url

    # Applied filters shown
    applied_filters = selenium.find_element_by_class_name('applied-filters')
    assert applied_filters

    # Correctly filtered
    selected_p = applied_filters.find_element_by_tag_name('p')
    assert selected_p.text == '1 out of 1 studies'

    # Lists correct filters
    filter_list = applied_filters.find_elements_by_tag_name('li')
    assert len(filter_list) == 1
    assert filter_list[0].text == 'Relative\nChild'

    # Ensure link to return to study-filter is correct
    back_link = applied_filters.find_element_by_tag_name('a')
    assert back_link.get_attribute('href') == url


def test_explorer_page_contains_summary_and_variable_plot(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    # Fairly crude test looking for:
    # - the plot titles.
    # - height of bk-root divs as a proxy for whether bokeh has rendered successfully
    study_id = Study.objects.get().id
    url = live_server.url + reverse('study-explorer') + '?study=%s' % study_id
    selenium.get(url)
    hide_cookie_banner()

    WebDriverWait(selenium, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tabs")))

    assert "Number of observations by domain" in selenium.page_source
    assert "Number of observations by variable" in selenium.page_source

    roots = selenium.find_elements_by_class_name('bk-root')
    for root in roots:
        if root.is_displayed():
            assert root.size["height"] >= 200


def test_filter_page_contains_summary_plot(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    # Fairly crude test looking for:
    # - the plot titles.
    # - height of bk-root divs as a proxy for whether bokeh has rendered successfully
    url = live_server.url + reverse('study-filter')
    selenium.get(url)
    hide_cookie_banner()

    assert "Number of observations by domain" in selenium.page_source

    root = selenium.find_element_by_class_name('bk-root')
    assert root.size["height"] >= 200


def test_study_explorer_new_update_sticky_is_working(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    no_update_text = "No new filters."
    update_text = "New filters have been selected. Click Apply to refresh studies."
    StudyFactory.create_batch(20)

    # Mak sure the browser window is small enough so it has to scroll vertically.
    selenium.set_window_size(1024, 500)

    url = live_server.url + reverse('study-explorer')
    selenium.get(url)
    hide_cookie_banner()

    sticky_menu = selenium.find_element_by_id("sticky-menu")

    initial_y_loc = sticky_menu.location['y']
    assert sticky_menu.value_of_css_property('z-index') in ('100', 'auto')
    assert sticky_menu.text == no_update_text

    checkbox = selenium.find_element_by_id("id_study_21")
    selenium.execute_script("return arguments[0].scrollIntoView(true);", checkbox)
    WebDriverWait(selenium, 10).until(EC.element_to_be_clickable((By.ID, "id_study_21")))

    assert sticky_menu.location['y'] > initial_y_loc
    assert sticky_menu.value_of_css_property('z-index') == '100'

    # make a change to selection
    ActionChains(selenium).move_to_element(checkbox).click().perform()
    assert sticky_menu.text == update_text


def test_study_explorer_new_update_works_on_autocomplete_select(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    no_update_text = "No new filters."
    update_text = "New filters have been selected. Click Apply to refresh studies."

    url = live_server.url + reverse('study-explorer')
    selenium.get(url)
    hide_cookie_banner()

    sticky_menu = selenium.find_element_by_id("sticky-menu")
    assert sticky_menu.text == no_update_text

    study_search = selenium.find_element_by_id("id_search")
    study_search.send_keys('CPP')
    time.sleep(1)
    study_search.send_keys(Keys.RETURN)
    assert sticky_menu.text == update_text


def test_filter_page_summary_plot_toggles_observations(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    # Tests whether the bokeh observations/subjects toggle buttons work
    # - Checks if toggling the button changes the title
    # - Cannot directly check heatmap and colormapper changes
    url = live_server.url + reverse('study-filter')
    selenium.get(url)
    hide_cookie_banner()

    # Check original title is correct
    title = selenium.find_element_by_class_name("bk-annotation")
    assert title.text == "Number of observations by domain"

    # Check toggle buttons exist
    toggle_buttons = selenium.find_elements_by_class_name("bk-bs-btn")
    assert len(toggle_buttons) == 2

    # Check toggling button updates title
    toggle_buttons[1].click()
    assert title.text == "Number of subjects by domain"

    # Check button toggles back back to original title
    toggle_buttons = selenium.find_elements_by_class_name("bk-bs-btn")
    toggle_buttons[0].click()
    assert title.text == "Number of observations by domain"


def test_explorer_page_summary_and_variable_plot_toggle_observations(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    # Tests whether the bokeh observations/subjects toggle buttons work
    study_id = Study.objects.get().id
    url = live_server.url + reverse('study-explorer') + '?study=%s' % study_id
    selenium.get(url)
    hide_cookie_banner()

    WebDriverWait(selenium, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tabs")))

    orig_domain_title = "Number of observations by domain"
    orig_var_title = "Number of observations by variable"
    orig_var_age_title = "Number of observations by variable and age"

    # Check plot title initialized correctly
    titles = selenium.find_elements_by_class_name("bk-annotation")
    assert titles[0].text == orig_domain_title
    assert titles[1].text == orig_var_title
    assert titles[4].text == orig_var_age_title

    # Check that toggling to subjects works on all plots
    toggle_buttons = selenium.find_elements_by_class_name("bk-bs-btn")
    toggle_buttons[1].click()
    assert titles[0].text == "Number of subjects by domain"
    toggle_buttons[3].click()
    assert titles[1].text == "Number of subjects by variable"
    toggle_buttons[9].click()
    assert titles[4].text == "Number of subjects by variable and age"

    # Check that toggling back to observations works on all plots
    toggle_buttons = selenium.find_elements_by_class_name("bk-bs-btn")
    toggle_buttons[0].click()
    assert titles[0].text == orig_domain_title
    toggle_buttons[2].click()
    assert titles[1].text == orig_var_title
    toggle_buttons[8].click()
    assert titles[4].text == orig_var_age_title
