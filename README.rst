AWS Shell - the interactive productivity booster for the AWS CLI
================================================================

.. image:: https://aws-developer-blog-media.s3-us-west-2.amazonaws.com/cli/Super-Charge-Your-AWS-Command-Line-Experience-with-aws-shell/aws-shell-final.gif


Installation
============

You can install the AWS Shell using `pip`_::

    $ pip install aws-shell

If you are not installing into a virtualenv you can run::

    $ sudo pip install aws-shell

If you want to upgrade to the latest version of the AWS Shell,
you can run::

    $ pip install --upgrade aws-shell

You can also use this upgrade command whenever a new version of the AWS CLI is
released that includes new services and API updates.  You will then be
able to use these new services and API updates in the AWS Shell.

Once you've installed the AWS Shell, you can now run::

    $ aws-shell

To exit the shell, press ``Ctrl-D``.

Supported Python Versions
-------------------------

The AWS Shell works on the same python versions supported by the AWS CLI:

* 2.6.5 and greater
* 2.7.x and greater
* 3.3.x and greater
* 3.4.x and greater


Configuration
=============

The AWS Shell uses the same configuration settings as the AWS CLI.
If you've never used the AWS CLI before, the easiest way to get
started is to run the ``configure`` command::

    $ aws-shell
    aws> configure
    AWS Access Key ID [None]: your-access-key-id
    AWS Secret Access Key [None]: your-secret-access-key
    Default region name [None]: region-to-use (e.g us-west-2, us-west-1, etc).
    Default output format [None]:
    aws>

For more information about configure settings, see the
`AWS CLI Getting Started Guide`_.

Basic Usage
===========

The AWS Shell accepts the same commands as the AWS CLI, except you don't
need to provide the ``aws`` prefix.  For example, here are a few commands
you can try::


    $ aws-shell
    aws> ec2 describe-regions
    {
        "Regions": [
            {
                "Endpoint": "ec2.eu-west-1.amazonaws.com",
                "RegionName": "eu-west-1"
            },
            ...
    aws> s3 ls
    2015-12-07 15:03:34 bucket1
    2015-12-07 15:03:34 bucket2
    aws> dynamodb list-tables --output text
    TABLENAMES     First
    TABLENAMES     Second
    TABLENAMES     Third


Features
========

Auto Completion of Commands and Options
---------------------------------------

The AWS Shell provides auto completion of commands and
options as you type.


.. image:: https://cloud.githubusercontent.com/assets/368057/11824078/784a613e-a32c-11e5-8ac5-f1d1873cc643.png


Shorthand Auto Completion
-------------------------

The AWS Shell can also fill in an example of the
shorthand syntax used for various AWS CLI options:

.. image:: https://cloud.githubusercontent.com/assets/368057/11823453/e95d85da-a328-11e5-8b8d-67566eccf9e3.png


Server Side Auto Completion
---------------------------

The AWS Shell also leverages `boto3`_, the AWS SDK for Python, to auto complete
server side resources such as Amazon EC2 instance Ids, Amazon Dynamodb table
names, AWS IAM user names, Amazon S3 bucket names, etc.

This feature is under active development.  The list of supported resources
continues to grow.

.. image:: https://cloud.githubusercontent.com/assets/368057/11824022/3648b4fc-a32c-11e5-8e18-92f028eb1cee.png


Fuzzy Searching
---------------

Every auto completion value supports fuzzy searching.  This enables you to
specify the commands, options, and values you want to run with even less
typing.  You can try typing:

* The first letter of each sub word: ``ec2 describe-reserved-instances-offerings``
  -> ``ec2 drio``
* A little bit of each word: ``ec2 describe-instances`` -> ``ec2 descinst``
* Any part of the command: ``dynamodb table`` -> Offers all commands that
  contain the subsequence ``table``.


.. image:: https://cloud.githubusercontent.com/assets/368057/11823996/18e69d16-a32c-11e5-80a2-defbaa6a8a80.png

Inline Documentation
--------------------

The AWS Shell will automatically pull up documentation as you type commands.
It will show inline documentation for CLI options.  There is also a separate
documentation panel that will show documentation for the current command or
option you are typing.

.. image:: https://cloud.githubusercontent.com/assets/368057/11823320/36ae9b04-a328-11e5-9661-81abfc0afe5a.png


Fish-Style Auto Suggestions
---------------------------

The AWS Shell supports Fish-style auto-suggestions. Use the right arrow key to
complete a suggestion.

.. image:: https://cloud.githubusercontent.com/assets/368057/11822961/4bceff94-a326-11e5-87fa-c664e1e82be4.png

Command History
---------------

The AWS Shell records the commands you run and writes them to
``~/.aws/shell/history``.  You can use the up and down arrow keys to scroll
through your history.

.. image:: https://cloud.githubusercontent.com/assets/368057/11823211/b5851e9a-a327-11e5-877f-687dc1f90e27.png

Toolbar Options
---------------

The AWS Shell has a bottom toolbar that provides several options:

* ``F2`` toggles between fuzzy and substring matching
* ``F3`` toggles between VI and Emacs key bindings
* ``F4`` toggles between single and multi column auto completions
* ``F5`` shows and hides the help documentation pane
* ``F10`` or ``Ctrl-D`` exits the AWS Shell

As you toggle options in the toolbar, your preferences are persisted
to the ``~/.aws/shell/awsshellrc`` file so that the next time you run
the AWS Shell, your preferences will be restored.

.. image:: https://cloud.githubusercontent.com/assets/368057/11823907/8c3f1e60-a32b-11e5-9f99-fe504ea0a5dc.png

Dot Commands
------------

The AWS Shell provides additional commands specific to the AWS Shell.
The commands are available by adding the ``.`` prefix before a command.

Creating Shell Scripts with .edit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are times when you may want to take a sequence of commands
you've run in the AWS Shell and combine them into a shell script.
In addition to the command history that's persisted to the
history file, the AWS Shell also keeps track of all the commands
you've run since you first started your AWS Shell session.

You can run the ``.edit`` command to open all these commands in
an editor.  The AWS Shell will use the ``EDITOR`` environment
variable before defaulting to ``notepad`` on Windows and
``vim`` on other platforms.

::

    aws> ec2 describe-instances
    aws> dynamodb list-tables
    aws> .edit


Executing Shell Commands
------------------------

The AWS Shell integrates with other commands in several ways.
First, you can pipe AWS CLI commands to other processes as well
as redirect output to a file::

    aws> dynamodb list-tables --output text | head -n 1
    TABLENAMES     First
    aws> dynamodb list-tables --output text > /tmp/foo.txt

Second, if you want to run a shell command rather than an AWS CLI
command, you can add the ``!`` prefix to your command::

    aws> !ls /tmp/
    foo.txt                                    bar.txt

Developer Preview Status
========================

The AWS Shell is currently in developer preview.
We welcome feedback, feature requests, and bug reports.
There may be backwards incompatible changes made in order
to respond to customer feedback as we continue to iterate
on the AWS Shell.


More Information
================

Below are miscellaneous links for more information:

* `AWS CLI Reference Docs`_
* `AWS CLI User Guide`_
* `AWS CLI Blog`_
* `AWS CLI Github Repo`_

.. _pip: http://www.pip-installer.org/en/latest/
.. _AWS CLI Getting Started Guide: http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html
.. _boto3: https://github.com/boto/boto3
.. _AWS CLI Reference Docs: http://docs.aws.amazon.com/cli/latest/reference/
.. _AWS CLI User Guide: http://docs.aws.amazon.com/cli/latest/userguide/
.. _AWS CLI Blog: https://blogs.aws.amazon.com/cli/
.. _AWS CLI Github Repo: https://github.com/aws/aws-cli
