"""AWS Shell application.

Main entry point to the AWS Shell.

"""
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.shortcuts import create_default_application
from prompt_toolkit import Application, CommandLineInterface
from prompt_toolkit.filters import Always


def create_application(completer, history):
    app = create_default_application(u'aws> ', completer=completer,
                                     display_completions_in_columns=True,
                                     vi_mode=Always(), history=history)
    return app


def create_cli_interface(completer, history):
    # A CommandLineInterface from prompt_toolkit
    # accepts two things: an application and an
    # eventloop.
    loop = create_eventloop()
    app = create_application(completer, history)
    cli = CommandLineInterface(application=app, eventloop=loop)
    return cli
