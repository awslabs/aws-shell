EMPTY = {'arguments': [], 'commands': [], 'children': {}}

class AWSCLICompleter(object):
    def __init__(self, index_data):
        self._index = index_data
        self._root_name = 'aws'
        self._current_name = 'aws'
        self._current = index_data[self._root_name]
        self._global_options = index_data[self._root_name]['arguments']
        self._last_position = 0

    def reset(self):
        # Resets all the state.  Called after a user runs
        # a command.
        self._current_name = self._root_name
        self._current = self._index[self._root_name]

    def autocomplete(self, line):
        """Given a line, return a list of suggestions."""
        current_length = len(line)
        if current_length == 1 and self._last_position > 1:
            # Reset state.  This is likely from a user completing
            # a previous command.
            self.reset()
        elif current_length < self._last_position:
            # The user has hit backspace.  We'll need to check
            # the current words.
            return []

        self._last_position = len(line)
        if not line:
            return []
        if line and not line.strip():
            # Special case, autocomplete all the top level commands.
            return self._current['commands']
        last_word = line.split()[-1]
        if last_word.startswith('-'):
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
        if line and line[-1] == ' ':
            self._current = self._current['children'].get(
                last_word, EMPTY)
            self._current_name = last_word
            return self._current['commands'][:]
        return [cmd for cmd in self._current['commands'] if
                cmd.startswith(last_word)]
