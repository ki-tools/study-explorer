from toolz.itertoolz import groupby
import pytest

from ..dataframes import (
    get_counts_df,
    get_counts_by_domain,
    pivot_counts_df,
    get_variable_counts,
    get_variable_count_by_variable
)

from ..plots import get_summary_heatmap, get_heatmap, get_age_heatmap
from ..plot_utils import add_categorical_offsets

from ..models import (
    Domain,
    Study,
    Variable
)
from .factories import (
    AgeVariableFactory,
    CountFactory,
    QualifierVariableFactory,
    StudyFactory,
    VariableFactory,
)


@pytest.fixture
def plot_data():
    age_var_1 = AgeVariableFactory(label='age_1', code='4')
    age_var_2 = AgeVariableFactory(label='age_2', code='3')
    age_var_3 = AgeVariableFactory(label='age_3', code='-1')
    age_var_4 = AgeVariableFactory(label='age_4', code='1')
    var_var_1 = VariableFactory(domain__label='violin')
    var_var_2 = VariableFactory(domain__label='piano')
    study_1 = StudyFactory(study_id='study_1')
    study_2 = StudyFactory(study_id='study_2')
    StudyFactory(study_id='study_3')
    qual_var_1 = QualifierVariableFactory(domain__code='QUAL', domain__label='qual', label='qual_var_1')
    qual_var_2 = QualifierVariableFactory(domain=qual_var_1.domain, domain__label='qual', label='qual_var_2')
    codes_1 = [age_var_1, var_var_1, qual_var_1]
    codes_2 = [age_var_1, qual_var_2]
    codes_3 = [age_var_2, var_var_1, qual_var_1]
    codes_4 = [age_var_2, var_var_1, qual_var_2]
    codes_5 = [age_var_3, var_var_2, qual_var_1]
    codes_6 = [age_var_3, qual_var_2]
    codes_7 = [age_var_4, var_var_1, qual_var_1]
    codes_8 = [age_var_4, var_var_1, qual_var_2]
    CountFactory(codes=codes_1, study=study_1, count=11)
    CountFactory(codes=codes_2, study=study_1, count=12)
    CountFactory(codes=codes_3, study=study_1, count=13)
    CountFactory(codes=codes_4, study=study_1, count=14)
    CountFactory(codes=codes_1, study=study_2, count=21)
    CountFactory(codes=codes_2, study=study_2, count=22)
    CountFactory(codes=codes_3, study=study_2, count=23)
    CountFactory(codes=codes_4, study=study_2, count=24)
    CountFactory(codes=codes_5, study=study_1, count=11)
    CountFactory(codes=codes_6, study=study_1, count=12)
    CountFactory(codes=codes_7, study=study_1, count=13)
    CountFactory(codes=codes_8, study=study_1, count=14)
    CountFactory(codes=codes_5, study=study_2, count=21)
    CountFactory(codes=codes_6, study=study_2, count=22)
    CountFactory(codes=codes_7, study=study_2, count=23)
    CountFactory(codes=codes_8, study=study_2, count=24)
    df = get_counts_df(studies=Study.objects.all())
    return df


@pytest.mark.django_db
def test_summary_heatmap_axes_are_sorted_study_ids_and_sorted_domain_labels(plot_data):
    summary_heatmap_df = get_counts_by_domain(plot_data)

    study_ids = Study.objects.all().values_list('study_id', flat=True)
    column = get_summary_heatmap(summary_heatmap_df, study_ids)
    plot = column.children[1]
    x_factors = plot.x_range.factors
    domain_factors = plot.y_range.factors
    assert x_factors == ['study_1', 'study_2', 'study_3']
    assert domain_factors == ['Age', 'piano', 'qual', 'violin']


@pytest.mark.django_db
def test_by_var_heatmap_axes_are_sorted_study_ids_and_properly_sorted_age_factors(plot_data):
    pivot_df = pivot_counts_df(plot_data)
    # implementation detail to avoid repeating query
    variables = Variable.objects.all()
    var_lookup = groupby('id', variables.values('id', 'label', 'code'))

    domain = Domain.objects.get(code='AGECAT')
    domain_heatmap_df = get_variable_counts(pivot_df, var_lookup, domain.code)

    study_ids = Study.objects.all().values_list('study_id', flat=True)
    column = get_heatmap(domain_heatmap_df, study_ids)
    plot = column.children[1]
    x_factors = plot.x_range.factors
    age_factors = plot.y_range.factors
    assert x_factors == ['study_1', 'study_2', 'study_3']
    # Note ordered by code
    # AgeVariableFactory(label='age_1', code=4)
    # AgeVariableFactory(label='age_2', code=3)
    # AgeVariableFactory(label='age_3', code=-1)
    # AgeVariableFactory(label='age_4', code=1)
    assert age_factors == ['age_3', 'age_4', 'age_2', 'age_1']


@pytest.mark.django_db
def test_by_var_and_ageheatmap_axes_are_sorted_qualifier_labels_and_properly_sorted_age_factors(plot_data):
    pivot_df = pivot_counts_df(plot_data)
    # implementation detail to avoid repeating query
    variables = Variable.objects.all()
    var_lookup = groupby('id', variables.values('id', 'label', 'code'))

    domain = Domain.objects.get(code='QUAL')
    domain_age_heatmap_df = get_variable_count_by_variable(pivot_df, var_lookup, domain.code, qualifier_code="AGECAT")
    column = get_age_heatmap(domain_age_heatmap_df)
    plot = column.children[1]
    age_factors = plot.x_range.factors
    y_factors = plot.y_range.factors
    assert y_factors == ['qual_var_1', 'qual_var_2']
    # Note ordered by code
    # AgeVariableFactory(label='age_1', code=4)
    # AgeVariableFactory(label='age_2', code=3)
    # AgeVariableFactory(label='age_3', code=-1)
    # AgeVariableFactory(label='age_4', code=1)
    assert age_factors == ['age_3', 'age_4', 'age_2', 'age_1']


@pytest.mark.django_db
def test_by_var_and_ageheatmap_add_categorical_offsets(plot_data):
    pivot_df = pivot_counts_df(plot_data)
    # implementation detail to avoid repeating query
    variables = Variable.objects.all()
    var_lookup = groupby('id', variables.values('id', 'label', 'code'))

    domain = Domain.objects.get(code='QUAL')
    domain_age_heatmap_df = get_variable_count_by_variable(pivot_df, var_lookup, domain.code, qualifier_code="AGECAT")

    df = add_categorical_offsets(domain_age_heatmap_df)
    assert list(df['var_label_adjusted'].values) == ['qual_var_1:0.8', 'qual_var_2:0.8'] * 8
    assert list(df['age_label_adjusted'].values) == ['age_1:0.2', 'age_1:0.2',
                                                     'age_2:0.2', 'age_2:0.2',
                                                     'age_3:0.2', 'age_3:0.2',
                                                     'age_4:0.2', 'age_4:0.2',
                                                     'age_1:0.4', 'age_1:0.4',
                                                     'age_2:0.4', 'age_2:0.4',
                                                     'age_3:0.4', 'age_3:0.4',
                                                     'age_4:0.4', 'age_4:0.4']
