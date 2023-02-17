import pandas as pd
from io import StringIO


class Utils:

    @staticmethod
    def read_csv(file_path, zip_file=None, encoding=None, **kwargs):
        """Loads a CSV file from a file or ZIP file, cleans it and returns a DataFrame.

        Parameters
        ----------
        file_path: Path to the local file, or path to the file in a zip file.
        zip_file: The zip file to load the file from.
        encoding: Encoding to use when reading the file.
        kwargs: kwargs for pandas.read_csv.

        Returns
        -------
        DataFrame
        """
        encodings = [encoding, 'cp1252']

        is_retry = False
        contents = None
        for encoding in encodings:
            try:
                if is_retry:
                    print('Retrying CSV load with encoding: {0}'.format(encoding))
                if zip_file:
                    with zip_file.open(file_path) as f:
                        if encoding is not None:
                            contents = f.read().decode(encoding=encoding)
                        else:
                            contents = f.read().decode()
                else:
                    with open(file_path, encoding=encoding) as f:
                        contents = f.read()
                        break
            except Exception as ex:
                print('Error reading CSV file: {0}'.format(ex))
                is_retry = True

        result = None
        if contents is not None:
            contents = contents.encode('ascii', 'ignore').decode()
            result = pd.read_csv(StringIO(contents), sep=',', **kwargs)
        return result
