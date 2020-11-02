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
from django.core.urlresolvers import reverse
from django.core.management import call_command
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .factories import DomainFactory, FilterFactory, VariableFactory


@pytest.fixture
def page(live_server, selenium, transactional_db):
    selenium.get(live_server.url)
    yield selenium


@pytest.fixture
def setup_domain_and_load_data(transactional_db):
    domain = DomainFactory()
    VariableFactory(domain=domain)
    FilterFactory(study_field=None)
    file_path = os.path.dirname(os.path.abspath(__file__))
    sample_csv = os.path.join(file_path, 'IDX_SAMPLE.csv')
    call_command('load_idx', sample_csv)


def test_accordion_expands_showing_domains(live_server, selenium, setup_domain_and_load_data):
    """Checks that clicking the accordion expands the domain filter"""

    url = live_server.url + reverse('study-filter')
    selenium.get(url)

    accordion = selenium.find_element_by_class_name("accordion-navigation")
    accordion.click()

    domain_search = selenium.find_element_by_id("SAMPLE_autocomplete")
    assert domain_search.is_displayed()

    category_dropdown = selenium.find_element_by_id("SAMPLE_dropdown")
    assert category_dropdown.is_displayed()

    selectall_button = selenium.find_element_by_id("SAMPLE_selectall")
    assert selectall_button.is_displayed()

    unselectall_button = selenium.find_element_by_id("SAMPLE_unselectall")
    assert unselectall_button.is_displayed()

    domain_table = selenium.find_element_by_id("SAMPLE_table")
    assert domain_table.is_displayed()


def _test_autocomplete_search(selenium, category, code, label, search, completions):
    accordion = selenium.find_element_by_class_name("accordion-navigation")
    accordion.click()

    domain_search = selenium.find_element_by_id("SAMPLE_autocomplete")

    # wait for autocomplete to populate
    domain_search.send_keys(search)
    while selenium.execute_script('return $("#SAMPLE_autocomplete").autocomplete("widget").toArray()[0].innerText') == "":
        time.sleep(1)

    autocompletions = selenium.execute_script('return $("#SAMPLE_autocomplete").autocomplete("widget").toArray()[0].innerText')
    assert autocompletions == '\n'.join(completions)

    domain_table = selenium.find_element_by_id("SAMPLE_table")
    rows = domain_table.find_elements_by_tag_name('tr')
    for row in rows:
        if row.find_elements_by_tag_name('th'):
            continue
        if row.is_displayed():
            spans = row.find_elements_by_tag_name('span')
            cat_span, code_span, label_span = spans[:3]
            assert cat_span.text == category
            assert code_span.text == code
            assert label_span.text == label


def test_domain_autocomplete_filtering_by_code(live_server, selenium, setup_domain_and_load_data):
    """Checks that autocomplete filtering works when filtering by code"""

    category = 'Biochemistry'
    code = 'BILI'
    label = 'Bilirubin'

    url = live_server.url + reverse('study-filter')
    selenium.get(url)

    _test_autocomplete_search(selenium, category, code, label, code, [code, label])


def test_domain_autocomplete_filtering_by_label(live_server, selenium, setup_domain_and_load_data):
    """Checks that autocomplete filtering works when filtering by code"""

    category = 'Biochemistry'
    code = 'BILI'
    label = 'Bilirubin'

    url = live_server.url + reverse('study-filter')
    selenium.get(url)

    _test_autocomplete_search(selenium, category, code, label, label, [label])


def test_domain_autocomplete_filtering_multiple(live_server, selenium, setup_domain_and_load_data):
    """Checks that autocomplete filtering works and filters table"""

    valid_completions = ['ARDBODY', 'ARDNECKL', 'ARDNECKT']

    url = live_server.url + reverse('study-filter')
    selenium.get(url)

    accordion = selenium.find_element_by_class_name("accordion-navigation")
    accordion.click()

    domain_search = selenium.find_element_by_id("SAMPLE_autocomplete")

    # wait for autocomplete to populate
    domain_search.send_keys('ARD')
    while selenium.execute_script('return $("#SAMPLE_autocomplete").autocomplete("widget").toArray()[0].innerText') == "":
        time.sleep(1)

    completions = selenium.execute_script('return $("#SAMPLE_autocomplete").autocomplete("widget").toArray()[0].innerText')
    assert completions == '\n'.join(valid_completions)

    domain_table = selenium.find_element_by_id("SAMPLE_table")
    rows = domain_table.find_elements_by_tag_name('tr')
    for row in rows:
        if row.find_elements_by_tag_name('th'):
            continue
        if row.is_displayed():
            spans = row.find_elements_by_tag_name('span')
            cat_span, code_span, label_span = spans[:3]
            assert cat_span.text in valid_completions
            assert code_span.text in valid_completions
            assert label_span.text in valid_completions


def test_domain_category_filtering(live_server, selenium, setup_domain_and_load_data):
    """Checks that filtering by domain category filters the table"""

    category = 'Hematology'
    valid_codes = ['HCT', 'HGB']
    valid_labels = ['Hematocrit', 'Hemoglobin']

    url = live_server.url + reverse('study-filter')
    selenium.get(url)

    accordion = selenium.find_element_by_class_name("accordion-navigation")
    accordion.click()

    # Simpler approach using Selenium Select ui element not working
    category_dropdown = selenium.find_element_by_id("SAMPLE_dropdown")
    selenium.execute_script("var select = arguments[0]; for(var i = 0; i < select.options.length; i++){ if(select.options[i].value == arguments[1]){ select.options[i].selected = true; } }; select.dispatchEvent(new Event('change'));", category_dropdown, category)

    domain_table = selenium.find_element_by_id("SAMPLE_table")
    rows = domain_table.find_elements_by_tag_name('tr')
    for row in rows:
        if row.find_elements_by_tag_name('th'):
            continue
        if row.is_displayed():
            spans = row.find_elements_by_tag_name('span')
            cat_span, code_span, label_span = spans[:3]
            assert cat_span.text == category
            assert code_span.text in valid_codes
            assert label_span.text in valid_labels


def test_domain_category_filter_select_all_visible(live_server, selenium, setup_domain_and_load_data):
    """Check that select all button only selects visible entries in the domain table"""
    category = 'Hematology'

    url = live_server.url + reverse('study-filter')
    selenium.get(url)

    accordion = selenium.find_element_by_class_name("accordion-navigation")
    accordion.click()

    # Simpler approach using Selenium Select ui element not working
    category_dropdown = selenium.find_element_by_id("SAMPLE_dropdown")
    selenium.execute_script("var select = arguments[0]; for(var i = 0; i < select.options.length; i++){ if(select.options[i].value == arguments[1]){ select.options[i].selected = true; } }; select.dispatchEvent(new Event('change'));", category_dropdown, category)

    selectall_button = selenium.find_element_by_id("SAMPLE_selectall")
    selectall_button.click()

    domain_table = selenium.find_element_by_id("SAMPLE_table")
    rows = domain_table.find_elements_by_tag_name('tr')
    for row in rows:
        if row.find_elements_by_tag_name('th'):
            continue
        checkbox = row.find_element_by_tag_name('input')
        if row.is_displayed():
            assert checkbox.get_property("checked") is True
        else:
            assert checkbox.get_property("checked") is False


def test_domain_filter_select_and_unselect_all(live_server, selenium, setup_domain_and_load_data, hide_cookie_banner):
    """Checks that select and unselect buttons work"""

    url = live_server.url + reverse('study-filter')
    selenium.get(url)
    hide_cookie_banner(selenium)

    accordion = selenium.find_element_by_class_name("accordion-navigation")
    accordion.click()

    selectall_button = selenium.find_element_by_id("SAMPLE_selectall")
    selectall_button.click()

    domain_table = selenium.find_element_by_id("SAMPLE_table")
    checkboxes = domain_table.find_elements_by_class_name('domain-checkbox')
    for checkbox in checkboxes:
        assert checkbox.get_property("checked") is True

    # scroll up until the unselectall_button is out from under the apply warning and clickable
    row = selenium.find_element_by_class_name("row")
    selenium.execute_script("return arguments[0].scrollIntoView(true);", row)
    unselectall_button = WebDriverWait(selenium, 10).until(EC.element_to_be_clickable((By.ID, "SAMPLE_unselectall")))
    unselectall_button.click()

    for checkbox in checkboxes:
        assert checkbox.get_property("checked") is False


def test_domain_filter_new_update_sticky_is_working(live_server, selenium, setup_domain_and_load_data):
    no_update_text = "No new filters."
    update_text = "New filters have been selected. Click Apply to refresh studies."

    url = live_server.url + reverse('study-filter')
    selenium.get(url)

    accordion = selenium.find_element_by_class_name("accordion-navigation")
    accordion.click()

    sticky_menu = selenium.find_element_by_id("sticky-menu")

    # assert sticky_menu.location == {'x': 35, 'y': 277}
    assert sticky_menu.value_of_css_property('z-index') == '100'
    assert sticky_menu.text == no_update_text

    # scroll to last domain in table
    last_checkbox = selenium.find_element_by_id("id_SAMPLE_18")
    selenium.execute_script("return arguments[0].scrollIntoView(true);", last_checkbox)
    WebDriverWait(selenium, 10).until(EC.element_to_be_clickable((By.ID, "id_SAMPLE_18")))

    assert sticky_menu.location['y'] > 277
    assert sticky_menu.value_of_css_property('z-index') == '100'

    # make a change to selection
    last_checkbox.click()
    assert sticky_menu.text == update_text
