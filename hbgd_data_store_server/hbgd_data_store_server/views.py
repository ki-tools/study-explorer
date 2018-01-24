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
