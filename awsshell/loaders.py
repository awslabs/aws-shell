import json
import os

from awsshell.utils import build_config_file_path


class JSONIndexLoader(object):
    def __init__(self):
        pass

    @staticmethod
    def index_filename(version_string, type_name='completions'):
        return build_config_file_path(
            '%s-%s.json' % (version_string, type_name))

    def load_index(self, filename):
        with open(filename, 'r') as f:
            return json.load(f)
