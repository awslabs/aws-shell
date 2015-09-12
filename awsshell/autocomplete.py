EMPTY = {'arguments': [], 'commands': [], 'children': {}}

class AWSCLICompleter(object):
    def __init__(self, index_data):
        self._index = index_data
        self._current = index_data['aws']
        self._last_position = 0

    def autocomplete(self, line):
        """Given a line, return a list of suggestions."""
        current_length = len(line)
        if current_length == 1 and self._last_position > 1:
            # Reset state.  This is likely from a user completing
            # a previous command.
            self._current = self._index['aws']
        self._last_position = len(line)
        if not line:
            return []
        if line and not line.strip():
            # Special case, autocomplete all the top level commands.
            return self._current['commands']
        last_word = line.split()[-1]
        if line and line[-1] == ' ':
            self._current = self._current['children'].get(
                last_word, EMPTY)
            return self._current['commands'][:]
        return [cmd for cmd in self._current['commands'] if
                cmd.startswith(last_word)]
