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

import re
import os
import zipfile
import fnmatch

from pandas import read_csv
from django.core.management.base import BaseCommand, CommandError

from ...models import Study, Count, Variable, Domain, EMPTY_IDENTIFIERS

# Regex file pattern defining the naming convention of IDX files
FILE_PATTERN = r'^IDX_(\w*)\.csv'

# Suffixes of domain name, code and category columns
# e.g. LB domain columns are LBTEST, LBTESTCD and LBCAT
DOMAIN_FORMAT = '{domain}TEST'
DOMAIN_CODE_FORMAT = '{domain}TESTCD'
DOMAIN_CAT_FORMAT = '{domain}CAT'


def get_study(row, study_cache=None, **kwargs):
    """
    Finds the study for an entry.
    """
    study_id_field = kwargs['study_id_field']

    if not study_cache:
        study_cache = {}
    study_id = row[study_id_field]
    if study_id in EMPTY_IDENTIFIERS:
        return None
    elif study_id in study_cache:
        return study_cache[study_id]
    study, study_created = Study.objects.get_or_create(study_id=study_id)
    if study_created:
        print('Created Study: {0}'.format(study.study_id))
    study_cache[study_id] = study
    return study


def get_domain_variable(row, domain, variable_cache=None):
    """
    Get a Variable model specifying the rows domain, category and
    code.
    """
    if not variable_cache:
        variable_cache = {}
    decode_idx = DOMAIN_FORMAT.format(domain=domain.code)
    code_idx = DOMAIN_CODE_FORMAT.format(domain=domain.code)
    cat_idx = DOMAIN_CAT_FORMAT.format(domain=domain.code)

    code = row[code_idx]
    if code in EMPTY_IDENTIFIERS:
        return None

    attrs = dict(domain=domain, code=code)
    cache_key = (domain.id, code)
    if cache_key in variable_cache:
        return variable_cache[cache_key]
    try:
        var = Variable.objects.get(**attrs)
    except Variable.DoesNotExist:
        category = row.get(cat_idx)
        if category not in EMPTY_IDENTIFIERS:
            attrs['category'] = category
        var = Variable.objects.create(label=row[decode_idx], **attrs)
        print('Created Variable: Domain: {0}, Label: {1}, Code: {2}'.format(domain.label, var.label, var.code))
    variable_cache[cache_key] = var
    return var


def get_qualifiers(row, valid_qualifiers, qualifier_cache=None):
    """
    Extract qualifier variables from row
    """
    if not qualifier_cache:
        qualifier_cache = {}
    qualifiers = []
    for qualifier, qual_code, suffix in valid_qualifiers:
        code = row.get(qual_code + suffix)
        if code in EMPTY_IDENTIFIERS:
            raise ValueError('Qualifiers cannot be empty')
        elif isinstance(code, float) and code.is_integer():
            code = int(code)
        attrs = dict(domain=qualifier, code=str(code))

        cache_key = (qualifier.id, str(code))
        if cache_key in qualifier_cache:
            qualifiers.append(qualifier_cache[cache_key])
            continue

        try:
            var = Variable.objects.get(**attrs)
        except Variable.DoesNotExist:
            var = Variable.objects.create(label=row[qual_code], **attrs)
            print('Created Variable: Domain: {0}, Label: {1}, Code: {2}'.format(var.domain.label, var.label, var.code))
        qualifier_cache[cache_key] = var
        qualifiers.append(var)
    return qualifiers


def get_valid_qualifiers(columns):
    """
    Returns a list of the valid qualifier columns.
    """
    valid_qualifiers = []
    qualifiers = Domain.objects.filter(is_qualifier=True)
    for qual in qualifiers:
        wildcard_re = fnmatch.translate(qual.code)
        cols = [col for col in columns if re.match(wildcard_re, col)]
        if not cols:
            continue
        elif len(cols) > 1:
            raise Exception('Qualifier code must match only one column per file.')
        qual_code = cols[0]
        suffix_re = qual_code + r'(\w{1,})'
        potential_suffixes = [re.match(suffix_re, col).group(1) for col in columns
                              if re.match(suffix_re, col)]
        suffix = ''
        if len(potential_suffixes) > 0:
            suffix = potential_suffixes[0]
        valid_qualifiers.append((qual, qual_code, suffix))
    return valid_qualifiers


def process_idx_df(df, domain, **kwargs):
    """
    Process an IDX csv file, creating Code, Count and Study
    objects.
    """
    count_subj_field = kwargs['count_subj_field']
    count_obs_field = kwargs['count_obs_field']
    study_id_field = kwargs['study_id_field']

    for required in [study_id_field, count_subj_field, count_obs_field]:
        if required not in df.columns:
            raise ValueError('IDX file does not contain %s column, '
                             'skipping.' % required)

    valid_qualifiers = get_valid_qualifiers(df.columns)

    study_cache, variable_cache, qualifier_cache = {}, {}, {}
    df = df.fillna('NaN')
    for _, row in df.iterrows():
        count = row[count_obs_field]
        subjects = row[count_subj_field]
        if any(c in EMPTY_IDENTIFIERS for c in (count, subjects)):
            continue
        try:
            qualifiers = get_qualifiers(row, valid_qualifiers, qualifier_cache)
        except ValueError:
            continue

        study = get_study(row, study_cache, **kwargs)
        if not study:
            continue
        variable = get_domain_variable(row, domain, variable_cache)
        if variable:
            qualifiers = [variable] + qualifiers
        query = Count.objects.create(count=count, subjects=subjects, study=study)
        query.codes = qualifiers
        query.save()


class Command(BaseCommand):
    help = """
    Loads queries into database given one or more IDX csv files or zip
    files containing IDX csv files (disregarding all zipfile structure).
    """

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str,
                            help='One or more csv or zip files')
        parser.add_argument('-study_id_field', type=str, default='STUDYID',
                            help='Name of column to use as study_id.')
        parser.add_argument('-count_subj_field', type=str, default='COUNT_SUBJ',
                            help='Name of column to use as subject count.')
        parser.add_argument('-count_obs_field', type=str, default='COUNT_OBS',
                            help='Name of column to use as observation count.')
        parser.add_argument('--clear', action='store_true',
                            default=True, dest='clear',
                            help='Clear database before processing data.')

    def process_file(self, filepath, zip_file=None, **kwargs):
        # Ensure the file matches the FILE_PATTERN
        basename = os.path.basename(filepath)
        match = re.search(FILE_PATTERN, basename)
        if not match:
            return False

        # Ensure that Domain exists
        domain = match.group(1).upper()
        try:
            domain = Domain.objects.get(code=domain)
        except Domain.DoesNotExist:
            self.stderr.write('Could not find domain: {0}'.format(domain))
            return False

        # Load file
        try:
            if zip_file:
                with zip_file.open(filepath) as f:
                    df = read_csv(f, encoding='windows-1254')
            else:
                with open(filepath) as f:
                    df = read_csv(f, encoding='windows-1254')
        except Exception as ex:
            self.stderr.write(str(ex))
            self.stderr.write('%s could not be read ensure '
                              'it is a valid csv file.' % basename)
            return False

        # Process dataframe
        self.stdout.write('Processing %s' % basename)
        try:
            process_idx_df(df, domain, **kwargs)
        except ValueError as e:
            self.stderr.write(str(e))
        return True

    def handle(self, *args, **options):
        if options['clear']:
            queries = Count.objects.all()
            self.stdout.write('Deleting %s counts' % len(queries))
            queries.delete()

            codes = Variable.objects.all()
            self.stdout.write('Deleting %s variables' % len(codes))
            codes.delete()

        n_queries = Count.objects.count()
        n_studies = Study.objects.count()
        n_codes = Variable.objects.count()

        failed_to_process = []
        try:
            for f in options['files']:
                if f.endswith('.csv'):
                    if not re.search(FILE_PATTERN, os.path.basename(f)):
                        self.stderr.write('Processing %s skipped, does '
                                          'not match %s naming convention.'
                                          % (f, FILE_PATTERN))
                        failed_to_process.append(f)
                        continue
                    if not self.process_file(f, **options):
                        failed_to_process.append(f)
                elif f.endswith('.zip') or f.endswith('.upload'):
                    zip_file = zipfile.ZipFile(f)
                    for zf in zip_file.filelist:
                        if not self.process_file(zf.filename, zip_file, **options):
                            failed_to_process.append(zf.filename)
                else:
                    failed_to_process.append(f)
        except Exception as ex:
            raise CommandError(str(ex))

        if failed_to_process:
            raise CommandError('Files could not be processed: {0}'.format(', '.join(failed_to_process)))

        self.stdout.write('Wrote %s Study entries' %
                          (Study.objects.count() - n_studies))
        self.stdout.write('Wrote %s Variable entries' %
                          (Variable.objects.count() - n_codes))
        self.stdout.write('Wrote %s Count entries' %
                          (Count.objects.count() - n_queries))
