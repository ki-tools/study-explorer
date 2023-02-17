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

from django.conf.urls import url

from .views import (
    ExportByAgeView,
    ExportView,
    StudyListView,
    StudyFilterView,
    StudyExplorerView,
    VariableListView,
)

urlpatterns = [
    url(r'^list$', StudyListView.as_view(), name='study-list'),
    url(r'^filter$', StudyFilterView.as_view(), name='study-filter'),
    url(r'^variables/(?P<domain_code>[-\S]+)', VariableListView.as_view(), name='variable-list'),
    url(r'^explorer', StudyExplorerView.as_view(), name='study-explorer'),
    url(r'^export/domain_(?P<domain_id>[0-9]+)', ExportView.as_view(), name='export'),
    url(r'^export_by_age/domain_(?P<domain_id>[0-9]+)', ExportByAgeView.as_view(), name='export_by_age'),  # noqa
]
