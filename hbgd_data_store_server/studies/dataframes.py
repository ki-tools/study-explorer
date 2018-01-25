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

import pandas as pd
from toolz.dicttoolz import valmap

from .models import Domain, Count


def get_counts_df(studies):
    """
    Returns a dataframe of Count records with some relevant meta data.

    Columns:
        id (Count.id, int)
        study (Count.study.id, int)
        study_label (Count.study.study_id, str)
        count (int)
        domain_code (Count.codes.domain.code, str)
        domain_label (Count.codes.domain.label, str)
        codes (Count.codes.id, int)

    Parameters:
        studies(Queryset) - Studies for which counts must be retrieved

    Returns:
        pandas.Dataframe
    """
    # Replaced by pandas code below to minimize SQL queries
    # counts = (Count.objects.filter(study__in=studies)
    #                        .values('id', 'study', 'study__study_id', 'count',
    #                                'codes__domain__code', 'codes__domain__label', 'codes'))

    value_names = ['id', 'count', 'subjects', 'codes', 'study']
    count_vals = Count.objects.filter(study__in=studies).values(*value_names)

    if len(count_vals) == 0:
        columns = ['id', 'study', 'study_label', 'count', 'codes',
                   'subjects', 'domain_code', 'domain_label']
        return pd.DataFrame(columns=columns)

    study_vals = studies.values('id', 'study_id')

    df = pd.merge(pd.DataFrame(list(count_vals)),
                  pd.DataFrame(list(study_vals)),
                  left_on='study', right_on='id', how='left', suffixes=('_count', '_study'))

    code_vals = Domain.objects.values('variable', 'code', 'label')

    df = pd.merge(df,
                  pd.DataFrame(list(code_vals)),
                  left_on='codes', right_on='variable', how='left')

    df = df.rename(columns={'id_count': 'id',
                            'code': 'domain_code',
                            'label': 'domain_label',
                            'study_id': 'study_label'})

    return df[['id', 'study', 'study_label', 'count', 'subjects',
               'domain_code', 'domain_label', 'codes']]


def get_counts_by_domain(df):
    """
    Parameters:
        df (pandas.Dataframe) - form of `get_counts_df` output

    Returns:
        pandas.Dataframe
    """

    columns = ['study', 'study_label', 'domain_code', 'domain_label']
    df2 = df.groupby(columns, as_index=False)[["count", "subjects"]].sum()

    return df2


def pivot_counts_df(df):
    """
    Parameters:
        df (pandas.Dataframe) - form of `get_counts_df` output

    Returns:
        pandas.Dataframe
    """
    df2 = pd.pivot_table(df,
                         values='codes',
                         index=['id', 'study', 'study_label', 'count', 'subjects'],
                         columns=['domain_code'])

    return df2


def get_variable_counts(df, var_lookup, domain_code):
    """
    Parameters:
        df (pandas.Dataframe) - form of `pivot_counts_df` output
        var_lookup (dict) - mapping of Variable ids to labels
        domain_code (str) - column accessor name for aggregation

    Returns:
        pandas.Dataframe or None
    """
    if domain_code not in df.columns:
        return None

    df2 = df[domain_code].reset_index()

    grouped = df2.groupby(['study', 'study_label', domain_code], as_index=False).sum()

    if len(grouped['count'].dropna()) == 0:
        return None

    grouped['var_code'] = grouped[domain_code].map(valmap(lambda x: x[0]['code'], var_lookup))
    grouped['var_label'] = grouped[domain_code].map(valmap(lambda x: x[0]['label'], var_lookup))

    return grouped


def get_variable_count_by_variable(df, var_lookup, domain_code, qualifier_code="AGECAT"):
    """
    Parameters:
        df (pandas.Dataframe) - form of `pivot_counts_df` output
        var_lookup (dict) - mapping of Variable ids to labels
        domain_code (str) - column accessor name for aggregation
        qualifier_code (str) - column accessor name for aggregation

    Returns:
        pandas.Dataframe or None
    """

    if domain_code not in df.columns or qualifier_code not in df.columns or domain_code == qualifier_code:  # noqa
        return None

    df2 = df[[domain_code, qualifier_code]].reset_index()
    grouped = (df2.groupby(['study', 'study_label', qualifier_code, domain_code], as_index=False)
                  .sum())

    if len(grouped['count'].dropna()) == 0:
        return None

    grouped['var_code'] = grouped[domain_code].map(valmap(lambda x: x[0]['code'], var_lookup))
    grouped['var_label'] = grouped[domain_code].map(valmap(lambda x: x[0]['label'], var_lookup))
    grouped['qual_code'] = grouped[qualifier_code].map(valmap(lambda x: x[0]['code'], var_lookup))
    grouped['qual_label'] = grouped[qualifier_code].map(valmap(lambda x: x[0]['label'], var_lookup))  # noqa

    return grouped
