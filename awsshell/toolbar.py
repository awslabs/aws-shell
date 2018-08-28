# Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from pygments.token import Token


class Toolbar(object):
    """Show information about the aws-shell in a tool bar.

    :type handler: callable
    :param handler: Wraps the callable `get_toolbar_items`.

    """

    def __init__(self, get_match_fuzzy, get_enable_vi_bindings,
                 get_show_completion_columns, get_show_help, key_bindings):
        self.key_bindings = key_bindings
        self.handler = self._create_toolbar_handler(
            get_match_fuzzy, get_enable_vi_bindings,
            get_show_completion_columns, get_show_help,)

    def _create_toolbar_handler(self, get_match_fuzzy, get_enable_vi_bindings,
                                get_show_completion_columns, get_show_help):
        """Create the toolbar handler.

        :type get_fuzzy_match: callable
        :param fuzzy_match: Gets the fuzzy matching config.

        :type get_enable_vi_bindings: callable
        :param get_enable_vi_bindings: Gets the vi (or emacs) key bindings
            config.

        :type get_show_completion_columns: callable
        :param get_show_completion_columns: Gets the show completions in
            multiple or single columns config.

        :type get_show_help: callable
        :param get_show_help: Gets the show help pane config.

        :rtype: callable
        :returns: get_toolbar_items.

        """
        assert callable(get_match_fuzzy)
        assert callable(get_enable_vi_bindings)
        assert callable(get_show_completion_columns)
        assert callable(get_show_help)

        def get_toolbar_items(cli):
            """Return the toolbar items.

            :type cli: :class:`prompt_toolkit.Cli`
            :param cli: The command line interface from prompt_toolkit

            :rtype: list
            :return: A list of (pygments.Token.Toolbar, str).
            """
            if get_match_fuzzy():
                match_fuzzy_token = Token.Toolbar.On
                match_fuzzy_cfg = 'ON'
            else:
                match_fuzzy_token = Token.Toolbar.Off
                match_fuzzy_cfg = 'OFF'
            if get_enable_vi_bindings():
                enable_vi_bindings_token = Token.Toolbar.On
                enable_vi_bindings_cfg = 'Vi'
            else:
                enable_vi_bindings_token = Token.Toolbar.On
                enable_vi_bindings_cfg = 'Emacs'
            if get_show_completion_columns():
                show_columns_token = Token.Toolbar.On
                show_columns_cfg = 'Multi'
            else:
                show_columns_token = Token.Toolbar.On
                show_columns_cfg = 'Single'
            if get_show_help():
                show_help_token = Token.Toolbar.On
                show_help_cfg = 'ON'
            else:
                show_help_token = Token.Toolbar.Off
                show_help_cfg = 'OFF'
            if cli.current_buffer_name == 'DEFAULT_BUFFER':
                show_buffer_name = 'cli'
            else:
                show_buffer_name = 'doc'
            return [
                (match_fuzzy_token,
                 ' [{0}] Fuzzy: {1} '.format(
                     self.key_bindings['toggle_fuzzy'],
                     match_fuzzy_cfg)),
                (enable_vi_bindings_token,
                 ' [{0}] Keys: {1} '.format(
                     self.key_bindings['toggle_editor'],
                     enable_vi_bindings_cfg)),
                (show_columns_token,
                 ' [{0}] {1} Column '.format(
                     self.key_bindings['toggle_column'],i
                     show_columns_cfg)),
                (show_help_token,
                 ' [{0}] Help: {1} '.format(
                     self.key_bindings['toggle_help'],i
                     show_help_cfg)),
                (Token.Toolbar,
                 ' [{0}] Focus: {1} '.format(
                     self.key_bindings['toggle_focus'],i
                     show_buffer_name)),
                (Token.Toolbar,
                 ' [{0}] Exit '.format(self.key_bindings['exit']))
            ]

        return get_toolbar_items
