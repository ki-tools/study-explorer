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
from django.conf import settings


def export_vars(request):
    data = {}
    data['CONTINUOUS_INTEGRATION'] = os.environ.get("CONTINUOUS_INTEGRATION", False)
    data['DEBUG'] = settings.DEBUG
    data['GTM_CONTAINER_ID'] = settings.GTM_CONTAINER_ID
    return data
