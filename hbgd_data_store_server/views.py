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

from django.db.models import Sum
from django.views.generic import TemplateView

from studies.models import Count, Domain, Study


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        if Domain.objects.count() != 0:
            context['first_domain'] = Domain.objects.all().order_by('label')[0]
        context['total_obs'] = Count.objects.all().aggregate(Sum('count'))['count__sum'] or 0
        context['total_studies'] = Study.objects.count()
        return context
