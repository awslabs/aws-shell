"""AWS Shell application.

Main entry point to the AWS Shell.

"""
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.shortcuts import create_default_application
from prompt_toolkit.shortcuts import create_default_layout
from prompt_toolkit import Application, CommandLineInterface, AbortAction
from prompt_toolkit.filters import Always
from prompt_toolkit.interface import AcceptAction
from prompt_toolkit.key_binding.manager import KeyBindingManager


def create_layout():
    return create_default_layout(
        u'aws> ', reserve_space_for_menu=True,
        display_completions_in_columns=True)


def create_buffer(completer, history):
    return Buffer(
        history=history,
        completer=completer,
        complete_while_typing=Always(),
        accept_action=AcceptAction.RETURN_DOCUMENT)


def create_application(completer, history):
    key_bindings_registry = KeyBindingManager(
        enable_vi_mode=True,
        enable_system_bindings=False,
        enable_open_in_editor=False).registry


    return Application(
        layout=create_layout(),
        buffer=create_buffer(completer, history),
        on_abort=AbortAction.RAISE_EXCEPTION,
        on_exit=AbortAction.RAISE_EXCEPTION,
        key_bindings_registry=key_bindings_registry,
    )


def create_cli_interface(completer, history):
    # A CommandLineInterface from prompt_toolkit
    # accepts two things: an application and an
    # eventloop.
    loop = create_eventloop()
    app = create_application(completer, history)
    cli = CommandLineInterface(application=app, eventloop=loop)
    return cli
