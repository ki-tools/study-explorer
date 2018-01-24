import os
from django.conf import settings


def export_vars(request):
    data = {}
    data['CONTINUOUS_INTEGRATION'] = os.environ.get("CONTINUOUS_INTEGRATION", False)
    data['DEBUG'] = settings.DEBUG
    return data
