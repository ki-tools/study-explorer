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
