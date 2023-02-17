import zipfile

import pytest
import os
from ..utils import Utils


@pytest.fixture
def cwd():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def nbsp_columns():
    return ['STUDYID', 'RELTIVEN', 'RELTIVE', 'MBSPECN', 'MBSPEC', 'MBCAT', 'MBTESTCD']


def test_read_csv_loads_from_csv_file(cwd, nbsp_columns):
    file_path = os.path.join(cwd, 'IDX_NBSP.csv')
    df = Utils.read_csv(file_path)
    assert list(df.columns) == nbsp_columns

    df = Utils.read_csv(file_path, encoding='utf-8')
    assert list(df.columns) == nbsp_columns

    df = Utils.read_csv(file_path, encoding='bad-code')
    assert list(df.columns) == nbsp_columns


def test_read_csv_loads_from_zip_file(cwd, nbsp_columns):
    file_path = os.path.join(cwd, 'IDX_NBSP.csv.zip')
    zip_file = zipfile.ZipFile(file_path)
    for zf in zip_file.filelist:
        df = Utils.read_csv(zf.filename, zip_file)
        assert list(df.columns) == nbsp_columns

        df = Utils.read_csv(zf.filename, zip_file, encoding='utf-8')
        assert list(df.columns) == nbsp_columns

        df = Utils.read_csv(zf.filename, zip_file, encoding='bad-code')
        assert list(df.columns) == nbsp_columns
