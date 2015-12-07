import json
import os


class JSONIndexLoader(object):
    def __init__(self):
        pass

    @staticmethod
    def index_filename(version_string, type_name='completions'):
        return os.path.join(
            os.path.expanduser('~'),
            '.aws', 'shell', '%s-%s.json'
            % (version_string, type_name))

    def load_index(self, filename):
        with open(filename, 'r') as f:
            return json.load(f)
