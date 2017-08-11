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
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys


class KeyManager(object):
    """A custom :class:`prompt_toolkit.KeyBindingManager`.

    Handles togging of:
        * Fuzzy or substring matching.
        * Vi or Emacs key bindings.
        * Multi or single columns in the autocompletion menu.
        * Showing or hiding the help pane.

    :type manager: :class:`prompt_toolkit.KeyBindingManager`
    :param manager: A custom `KeyBindingManager`.
    """

    def __init__(self, get_match_fuzzy, set_match_fuzzy,
                 get_enable_vi_bindings, set_enable_vi_bindings,
                 get_show_completion_columns, set_show_completion_columns,
                 get_show_help, set_show_help, stop_input_and_refresh_cli):
        self.manager = None
        self._create_key_manager(
            get_match_fuzzy, set_match_fuzzy,
            get_enable_vi_bindings, set_enable_vi_bindings,
            get_show_completion_columns, set_show_completion_columns,
            get_show_help, set_show_help, stop_input_and_refresh_cli)

    def _create_key_manager(self, get_match_fuzzy, set_match_fuzzy,
                            get_enable_vi_bindings, set_enable_vi_bindings,
                            get_show_completion_columns,
                            set_show_completion_columns,
                            get_show_help, set_show_help,
                            stop_input_and_refresh_cli):
        """Create and initialize the keybinding manager.

        :type get_fuzzy_match: callable
        :param get_fuzzy_match: Gets the fuzzy matching config.

        :type set_fuzzy_match: callable
        :param set_fuzzy_match: Sets the fuzzy matching config.

        :type get_enable_vi_bindings: callable
        :param get_enable_vi_bindings: Gets the vi (or emacs) key bindings
            config.

        :type set_enable_vi_bindings: callable
        :param set_enable_vi_bindings: Sets the vi (or emacs) key bindings
            config.

        :type get_show_completion_columns: callable
        :param get_show_completion_columns: Gets the show completions in
            multiple or single columns config.

        type set_show_completion_columns: callable
        :param set_show_completion_columns: Sets the show completions in
            multiple or single columns config.

        :type get_show_help: callable
        :param get_show_help: Gets the show help pane config.

        :type set_show_help: callable
        :param set_show_help: Sets the show help pane config.

        :type stop_input_and_refresh_cli: callable
        param stop_input_and_refresh_cli: Stops input by raising an
            `InputInterrupt`, forces a cli refresh to ensure certain
            options take effect within the current session.

        :rtype: :class:`prompt_toolkit.KeyBindingManager`
        :return: A custom `KeyBindingManager`.

        """
        assert callable(get_match_fuzzy)
        assert callable(set_match_fuzzy)
        assert callable(get_enable_vi_bindings)
        assert callable(set_enable_vi_bindings)
        assert callable(get_show_completion_columns)
        assert callable(set_show_completion_columns)
        assert callable(get_show_help)
        assert callable(set_show_help)
        assert callable(stop_input_and_refresh_cli)
        self.manager = KeyBindingManager(
            enable_search=True,
            enable_abort_and_exit_bindings=True,
            enable_system_bindings=True,
            enable_auto_suggest_bindings=True,
            enable_open_in_editor=False)

        @self.manager.registry.add_binding(Keys.F2)
        def handle_f2(_):
            """Toggle fuzzy matching.

            :type _: :class:`prompt_toolkit.Event`
            :param _: (Unused)

            """
            set_match_fuzzy(not get_match_fuzzy())

        @self.manager.registry.add_binding(Keys.F3)
        def handle_f3(_):
            """Toggle Vi mode keybindings matching.

            Disabling Vi keybindings will enable Emacs keybindings.

            :type _: :class:`prompt_toolkit.Event`
            :param _: (Unused)

            """
            set_enable_vi_bindings(not get_enable_vi_bindings())
            stop_input_and_refresh_cli()

        @self.manager.registry.add_binding(Keys.F4)
        def handle_f4(_):
            """Toggle multiple column completions.

            :type _: :class:`prompt_toolkit.Event`
            :param _: (Unused)

            """
            set_show_completion_columns(not get_show_completion_columns())
            stop_input_and_refresh_cli()

        @self.manager.registry.add_binding(Keys.F5)
        def handle_f5(_):
            """Toggle the help container.

            :type _: :class:`prompt_toolkit.Event`
            :param _: (Unused)

            """
            set_show_help(not get_show_help())
            stop_input_and_refresh_cli()

        @self.manager.registry.add_binding(Keys.F9)
        def handle_f9(event):
            """Switch between the default and docs buffers.

            :type event: :class:`prompt_toolkit.Event`
            :param event: Contains info about the event, namely the cli
                which is used to changing which buffer is focused.

            """
            if event.cli.current_buffer_name == u'clidocs':
                event.cli.focus(u'DEFAULT_BUFFER')
            else:
                event.cli.focus(u'clidocs')

        @self.manager.registry.add_binding(Keys.F10)
        def handle_f10(event):
            """Quit when the `F10` key is pressed.

            :type event: :class:`prompt_toolkit.Event`
            :param event: Contains info about the event, namely the cli
                which is used for exiting the app.

            """
            event.cli.set_exit()
