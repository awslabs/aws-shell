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

    def __init__(self, match_fuzzy, enable_vi_bindings,
                 show_completion_columns, show_help):
        self.manager = None
        self._create_key_manager(match_fuzzy, enable_vi_bindings,
                                 show_completion_columns, show_help)

    def _create_key_manager(self, match_fuzzy, enable_vi_bindings,
                            show_completion_columns, show_help):
        """Creates and initializes the keybinding manager.

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

        :rtype: :class:`prompt_toolkit.KeyBindingManager`
        :return: A custom `KeyBindingManager`.
        """
        assert callable(match_fuzzy)
        assert callable(enable_vi_bindings)
        assert callable(show_completion_columns)
        assert callable(show_help)
        self.manager = KeyBindingManager(
            enable_search=True,
            enable_abort_and_exit_bindings=True,
            enable_system_bindings=True,
            enable_auto_suggest_bindings=True,
            enable_vi_mode=enable_vi_bindings(),
            enable_open_in_editor=False)

        @self.manager.registry.add_binding(Keys.F2)
        def handle_f2(_):
            """Enables/disables fuzzy matching.

            :type _: :class:`prompt_toolkit.Event`
            :param _: (Unused)
            """
            match_fuzzy(not match_fuzzy())

        @self.manager.registry.add_binding(Keys.F3)
        def handle_f3(_):
            """Enables/disables Vi mode keybindings matching.

            Disabling Vi keybindings will enable Emacs keybindings.

            :type _: :class:`prompt_toolkit.Event`
            :param _: (Unused)
            """
            enable_vi_bindings(not enable_vi_bindings(), refresh_ui=True)

        @self.manager.registry.add_binding(Keys.F4)
        def handle_f4(_):
            """Enables/disables multiple column completions.

            :type _: :class:`prompt_toolkit.Event`
            :param _: (Unused)
            """
            show_completion_columns(not show_completion_columns(),
                                    refresh_ui=True)

        @self.manager.registry.add_binding(Keys.F5)
        def handle_f5(_):
            """Shows/hides the help container.

            :type _: :class:`prompt_toolkit.Event`
            :param _: (Unused)
            """
            show_help(not show_help(), refresh_ui=True)

        @self.manager.registry.add_binding(Keys.F10)
        def handle_f10(event):
            """Quits when the `F10` key is pressed.

            :type _: :class:`prompt_toolkit.Event`
            :param _: (Unused) Contains info about the event, namely the cli
                which is used for exiting the app.
            """
            event.cli.set_exit()
