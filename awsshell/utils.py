"""Utility module for misc aws shell functions."""
from awsshell.compat import HTMLParser


def remove_html(html):
    s = DataOnly()
    s.feed(html)
    return s.get_data()


class DataOnly(HTMLParser):
    def __init__(self):
        self.reset()
        self.lines = []

    def handle_data(self, data):
        self.lines.append(data)

    def get_data(self):
        return ''.join(self.lines)
