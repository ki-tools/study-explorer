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
