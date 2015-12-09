import textwrap
from awsshell import makeindex

def test_can_convert_rst_text():
    content = textwrap.dedent("""\
        MySection
        =========

        This is some text.
        Here's a list:

        * foo
        * bar

        Literal text: ``--foo-bar``
    """)
    converted = makeindex.convert_rst_to_basic_text(content)
    assert converted == textwrap.dedent("""\

        MYSECTION

        This is some text. Here's a list:

        * foo

        * bar

        Literal text: --foo-bar
    """)
