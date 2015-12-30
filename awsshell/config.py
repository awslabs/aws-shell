# Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import os
import shutil

from configobj import ConfigObj

from awsshell.utils import build_config_file_path


class Config(object):
    """Reads and writes the config template and user config file."""

    def load(self, config_template, config_file=None):
        """Read the config file if it exists, else read the default config.

        Creates the user config file if it doesn't exist using the template.

        :type config_template: str
        :param config_template: The config template file name.

        :type config_file: str
        :param config_file: (Optional) The config file name.
            If None, the config_file name will be set to the config_template.

        :rtype: :class:`configobj.ConfigObj`
        :return: The config information for reading and writing.
        """
        if config_file is None:
            config_file = config_template
        config_path = build_config_file_path(config_file)
        template_path = os.path.join(os.path.dirname(__file__),
                                     config_template)
        self._copy_template_to_config(template_path, config_path)
        return self._load_template_or_config(template_path, config_path)

    def _load_template_or_config(self, template_path, config_path):
        """Load the config file if it exists, else read the default config.

        :type template_path: str
        :param template_path: The template config file path.

        :type config_path: str
        :param config_path: The user's config file path.

        :rtype: :class:`configobj.ConfigObj`
        :return: The config information for reading and writing.
        """
        expanded_config_path = os.path.expanduser(config_path)
        cfg = ConfigObj()
        cfg.filename = expanded_config_path
        cfg.merge(ConfigObj(template_path, interpolation=False))
        cfg.merge(ConfigObj(expanded_config_path, interpolation=False))
        return cfg

    def _copy_template_to_config(self, template_path,
                                 config_path, overwrite=False):
        """Write the default config from a template.

        :type template_path: str
        :param template_path: The template config file path.

        :type config_path: str
        :param config_path: The user's config file path.

        :type overwrite: bool
        :param overwrite: (Optional) Determines whether to overwrite the
            existing config file, if it exists.

        :raises: :class:`OSError <exceptions.OSError>`
        """
        config_path = os.path.expanduser(config_path)
        if not overwrite and os.path.isfile(config_path):
            return
        else:
            try:
                config_path_dir_name = os.path.dirname(config_path)
                os.makedirs(config_path_dir_name)
            except OSError:
                if not os.path.isdir(config_path_dir_name):
                    raise
            shutil.copyfile(template_path, config_path)
