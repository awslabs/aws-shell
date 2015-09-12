EMPTY = {'arguments': [], 'commands': [], 'children': {}}
import logging
logging.basicConfig(filename='/tmp/completions', level=logging.DEBUG)

LOG = logging.getLogger(__name__)


class AWSCLICompleter(object):
    def __init__(self, index_data):
        self._index = index_data
        self._root_name = 'aws'
        self._global_options = index_data[self._root_name]['arguments']
        # These values mutate as autocompletions occur.
        # They track state to improve the autocompletion speed.
        self._current_name = 'aws'
        self._current = index_data[self._root_name]
        self._last_position = 0

    def reset(self):
        # Resets all the state.  Called after a user runs
        # a command.
        self._current_name = self._root_name
        self._current = self._index[self._root_name]
        self._last_position = 0

    def autocomplete(self, line):
        """Given a line, return a list of suggestions."""
        LOG.debug("line: %s", line)
        current_length = len(line)
        if current_length == 1 and self._last_position > 1:
            # Reset state.  This is likely from a user completing
            # a previous command.
            self.reset()
        elif current_length < self._last_position:
            # The user has hit backspace.  We'll need to check
            # the current words.
            return self._handle_backspace()

        self._last_position = len(line)
        if not line:
            return []
        if line and not line.strip():
            # Special case, the user hits a space on a new line so
            # we autocomplete all the top level commands.
            return self._current['commands']

        last_word = line.split()[-1]
        if line[-1] == ' ':
            # At this point the user has autocompleted a command
            # or an argument and has hit space.  If they've
            # just completed a command, we need to change the
            # current context and traverse into the subcommand.
            # "ec2 "
            #      ^--here, need to traverse into "ec2"
            #
            # Otherwise:
            # "ec2 --no-validate-ssl "
            #                        ^-- here, stay on "ec2" context.
            if not last_word.startswith('-'):
                next_command = self._current['children'].get(last_word)
                if next_command is not None:
                    self._current = next_command
                    self._current_name = last_word
            # Even if we don't change context, we still want to
            # autocomplete all the commands for the current context
            # in either of the above two cases.
            return self._current['commands'][:]
        elif last_word.startswith('-'):
            return self._autocomplete_options(last_word)
        return [cmd for cmd in self._current['commands'] if
                cmd.startswith(last_word)]

    def _handle_backspace(self):
        return []

    def _autocomplete_options(self, last_word):
        global_args = []
        # Autocomplete argument names.
        current_arg_completions = [
            cmd for cmd in self._current['arguments']
            if cmd.startswith(last_word)]
        if self._current_name != self._root_name:
            # Also autocomplete global arguments.
            global_args = [
                cmd for cmd in self._global_options if
                cmd.startswith(last_word)]
        return current_arg_completions + global_args
