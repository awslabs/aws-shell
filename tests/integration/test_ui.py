import pyte
import time
import unittest
import threading
from awsshell import shellcomplete, autocomplete
from awsshell.app import AWSShell
from awsshell.docs import DocRetriever
from prompt_toolkit.keys import Keys
from prompt_toolkit.input import PipeInput
from prompt_toolkit.layout.screen import Size
from prompt_toolkit.terminal.vt100_output import Vt100_Output
from prompt_toolkit.terminal.vt100_input import ANSI_SEQUENCES

_polly_index = {
    "children": {
        "describe-voices": {
            "children": {},
            "argument_metadata": {
                "--language-code": {
                    "type_name": "string",
                    "example": "",
                    "api_name": "LanguageCode",
                    "required": False,
                    "minidoc": "LanguageCode minidoc string"
                }
            },
            "arguments": ["--language-code"],
            "commands": []
        }
    },
    "argument_metadata": {},
    "arguments": [],
    "commands": ["describe-voices"]
}

_index_data = {
    'aws': {
        'commands': ['polly'],
        'children': {'polly': _polly_index},
        'arguments': [],
        'argument_metadata': {},
    }
}

_doc_db = {b'aws.polly': 'Polly is a service'}


class PyteOutput(object):

    def __init__(self, columns=80, lines=24):
        self._columns = columns
        self._lines = lines
        self._screen = pyte.Screen(self._columns, self._lines)
        self._stream = pyte.ByteStream(self._screen)
        self.encoding = 'utf-8'

    def write(self, data):
        self._stream.feed(data)

    def flush(self):
        pass

    def get_size(self):
        def _get_size():
            return Size(columns=self._columns, rows=self._lines)
        return _get_size

    def display(self):
        return self._screen.display


def _create_shell(ptk_input, ptk_output):
    io = {
        'input': ptk_input,
        'output': ptk_output,
    }
    doc_data = DocRetriever(_doc_db)
    model_completer = autocomplete.AWSCLIModelCompleter(_index_data)
    completer = shellcomplete.AWSShellCompleter(model_completer)
    return AWSShell(completer, model_completer, doc_data, **io)


_ansi_sequence = dict((key, ansi) for ansi, key in ANSI_SEQUENCES.items())


class VirtualShell(object):

    def __init__(self, shell=None):
        self._ptk_input = PipeInput()
        self._pyte = PyteOutput()
        self._ptk_output = Vt100_Output(self._pyte, self._pyte.get_size())

        if shell is None:
            shell = _create_shell(self._ptk_input, self._ptk_output)

        def _run_shell():
            shell.run()

        self._thread = threading.Thread(target=_run_shell)
        self._thread.start()

    def write(self, data):
        self._ptk_input.send_text(data)

    def press_keys(self, *keys):
        sequences = [_ansi_sequence[key] for key in keys]
        self.write(''.join(sequences))

    def display(self):
        return self._pyte.display()

    def quit(self):
        # figure out a better way to quit
        self.press_keys(Keys.F10)
        self._thread.join()
        self._ptk_input.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()


class ShellTest(unittest.TestCase):

    def setUp(self):
        self.shell = VirtualShell()

    def tearDown(self):
        self.shell.quit()

    def write(self, data):
        self.shell.write(data)

    def press_keys(self, *keys):
        self.shell.press_keys(*keys)

    def _poll_display(self, timeout=2, interval=0.1):
        start = time.time()
        while time.time() <= start + timeout:
            display = self.shell.display()
            yield display
            time.sleep(interval)

    def await_text(self, text):
        for display in self._poll_display():
            for line in display:
                if text in line:
                    return
        display = '\n'.join(display)
        fail_message = '"{text}" not found on screen: \n{display}'
        self.fail(fail_message.format(text=text, display=display))

    def test_toolbar_appears(self):
        self.await_text('[F3] Keys')

    def test_input_works(self):
        self.write('ec2')
        self.await_text('ec2')

    def test_completion_menu_operation(self):
        self.write('polly desc')
        self.await_text('describe-voices')

    def test_completion_menu_argument(self):
        self.write('polly describe-voices --l')
        self.await_text('--language-code')

    def test_doc_menu_appears(self):
        self.write('polly ')
        self.await_text('Polly is a service')

    def test_doc_menu_is_searchable(self):
        self.write('polly ')
        self.await_text('Polly is a service')
        self.press_keys(Keys.F9)
        self.write('/')
        # wait for the input timeout
        time.sleep(0.6)
        self.await_text('Polly is a service')
