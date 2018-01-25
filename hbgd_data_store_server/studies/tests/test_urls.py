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

from django.core.urlresolvers import reverse


def test_studies_list_view_url_resolve():
    assert "/studies/list" == reverse("study-list")


def test_studies_filter_view_url_resolve():
    assert "/studies/filter" == reverse("study-filter")


def test_studies_variables_list_view_url_resolve():
    slug = "LB"
    assert "/studies/variables/%s" % slug == reverse('variable-list', kwargs={"domain_code": slug})


def test_studies_variables_list_wildcard_view_url_resolve():
    slug = "*SPEC"
    assert "/studies/variables/%s" % slug == reverse('variable-list', kwargs={"domain_code": slug})


def test_studies_explorer_view_url_resolve():
    assert "/studies/explorer" == reverse("study-explorer")
