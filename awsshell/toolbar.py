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
    """Shows information about the aws-shell in a tool bar.

    :type handler: callable
    :param handler: `get_toolbar_items`.
    """

    def __init__(self, match_fuzzy, enable_vi_bindings,
                 show_completion_columns, show_help):
        self.handler = self._create_toolbar_handler(
            match_fuzzy, enable_vi_bindings,
            show_completion_columns, show_help)

    def _create_toolbar_handler(self, match_fuzzy, enable_vi_bindings,
                                show_completion_columns, show_help):
        """Creates the toolbar handler.

        :type fuzzy_match: callable
        :param fuzzy_match: Gets/sets the fuzzy matching config.

        :type enable_vi_bindings: callable
        :param enable_vi_bindings: Gets/sets the vi (or emacs) key bindings
            config.

        :type show_completion_columns: callable
        :param show_completion_columns: Gets/sets the show completions in
            multiple or single columns config.

        :type show_help: callable
        :param show_help: Gets/sets the show help pane config.

        :rtype: callable
        :returns: get_toolbar_items.
        """
        assert callable(match_fuzzy)
        assert callable(enable_vi_bindings)
        assert callable(show_completion_columns)
        assert callable(show_help)

        def get_toolbar_items(_):
            """Returns the toolbar items.

            :type _: :class:`prompt_toolkit.Cli`
            :param _: (Unused)

            :rtype: list
            :return: A list of (pygments.Token.Toolbar, str).
            """
            if match_fuzzy():
                match_fuzzy_token = Token.Toolbar.On
                match_fuzzy_cfg = 'ON'
            else:
                match_fuzzy_token = Token.Toolbar.Off
                match_fuzzy_cfg = 'OFF'
            if enable_vi_bindings():
                enable_vi_bindings_token = Token.Toolbar.On
                enable_vi_bindings_cfg = 'Vi'
            else:
                enable_vi_bindings_token = Token.Toolbar.On
                enable_vi_bindings_cfg = 'Emacs'
            if show_completion_columns():
                show_columns_token = Token.Toolbar.On
                show_columns_cfg = 'Multi'
            else:
                show_columns_token = Token.Toolbar.On
                show_columns_cfg = 'Single'
            if show_help():
                show_help_token = Token.Toolbar.On
                show_help_cfg = 'ON'
            else:
                show_help_token = Token.Toolbar.Off
                show_help_cfg = 'OFF'
            return [
                (match_fuzzy_token,
                    ' [F2] Fuzzy: {0} '.format(match_fuzzy_cfg)),
                (enable_vi_bindings_token,
                    ' [F3] Keys: {0} '.format(enable_vi_bindings_cfg)),
                (show_columns_token,
                    ' [F4] {0} Column '.format(show_columns_cfg)),
                (show_help_token,
                    ' [F5] Help: {0} '.format(show_help_cfg)),
                (Token.Toolbar,
                    ' [F10] Exit ')
            ]

        return get_toolbar_items
