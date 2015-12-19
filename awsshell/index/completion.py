"""Module for completion index.

Generates, loads, and writes out completion index.
Also provides an interface for working with the
indexed data.

The the subpackage docstring of awsshell.index for
a higher level overview.

"""
import os
import json

from awsshell.utils import FSLayer, FileReadError, build_config_file_path
from awsshell import utils


class IndexLoadError(Exception):
    """Raised when an index could not be loaded."""


class CompletionIndex(object):
    """Handles working with the local commmand completion index.

    :type commands: list
    :param commands: ec2, s3, elb...

    :type subcommands: list
    :param subcommands: start-instances, stop-instances, terminate-instances...

    :type global_opts: list
    :param global_opts: --profile, --region, --output...

    :type args_opts: set, to filter out duplicates
    :param args_opts: ec2 start-instances: --instance-ids, --dry-run...
    """

    # The completion index can read/write to a cache dir
    # so that it doesn't have to recompute the completion cache
    # every time the CLI starts up.
    DEFAULT_CACHE_DIR = build_config_file_path('cache')

    def __init__(self, cache_dir=DEFAULT_CACHE_DIR, fslayer=None):
        self._cache_dir = cache_dir
        if fslayer is None:
            fslayer = FSLayer()
        self._fslayer = fslayer
        self.commands = []
        self.subcommands = []
        self.global_opts = []
        self.args_opts = set()
        self.load_completions()

    def load_index(self, version_string):
        """Load the completion index for a given CLI version.

        :type version_string: str
        :param version_string: The AWS CLI version, e.g "1.9.2".

        """
        filename = self._filename_for_version(version_string)
        try:
            contents = self._fslayer.file_contents(filename)
        except FileReadError as e:
            raise IndexLoadError(str(e))
        return contents

    def _filename_for_version(self, version_string):
        return os.path.join(
            self._cache_dir, 'completions-%s.json' % version_string)

    def load_completions(self):
        """Loads completions from the completion index.

        Updates the following attributes:
            * commands
            * subcommands
            * global_opts
            * args_opts
        """
        index_str = self.load_index(utils.AWSCLI_VERSION)
        index_data = json.loads(index_str)
        index_root = index_data['aws']
        # ec2, s3, elb...
        self.commands = index_root['commands']
        # --profile, --region, --output...
        self.global_opts = index_root['arguments']
        for command in self.commands:
            # ec2: start-instances, stop-instances, terminate-instances...
            subcommands_current = index_root['children'] \
                .get(command)['commands']
            self.subcommands.extend(subcommands_current)
            for subcommand_current in subcommands_current:
                # start-instances: --instance-ids, --dry-run...
                args_opts_current = index_root['children'] \
                    .get(command)['children'] \
                    .get(subcommand_current)['arguments']
                self.args_opts.update(args_opts_current)
