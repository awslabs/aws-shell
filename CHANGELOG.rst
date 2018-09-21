=========
CHANGELOG
=========

0.2.1
=====

* bugfix:AWS CLI: Fixes `#208 <https://github.com/awslabs/aws-shell/issues/208>`__. Update the AWS Shell to support the latest version of the AWS CLI.

0.2.0
=====

* bugfix:Command History: Ensure aws prefix is not prepended twice in command history.
  Fixes `#157 <https://github.com/awslabs/aws-shell/issues/157>`__
* bugfix:Keybinding: Switching between emacs/vi keybindings now functions properly
* enhancement:Documentation: The documentation pane can now be focused and navigated.
  Fixes `#74 <https://github.com/awslabs/aws-shell/issues/74>`__, `#159 <https://github.com/awslabs/aws-shell/issues/159>`__

0.1.1
=====

* bugfix:AWS CLI: Fix issue with latest version of the AWS CLI
  that would cause the AWS Shell to raise an exception on startup.
  The minimum version of the AWS CLI has been bumped to 1.10.30.
  (`issue 118 <https://github.com/awslabs/aws-shell/issues/118>`__)

0.1.0
=====

* feature:Dot Commands: Add ``.exit/.quit`` dot commands
  (`issue 97 <https://github.com/awslabs/aws-shell/pull/97>`__)
* feature:Documentation: Show documentation for global arguments
  (`issue 51 <https://github.com/awslabs/aws-shell/issues/51>`__)
* feature:Dot Commands: Add ``.cd`` dot command
  (`issue 97 <https://github.com/awslabs/aws-shell/issues/76>`__)
* feature:Dot Commands: Add ``.profile`` dot command
  (`issue 97 <https://github.com/awslabs/aws-shell/issues/9>`__)
* feature:Command Line Arguments: Add ``--profile`` command line
  option (`issue 89 <https://github.com/awslabs/aws-shell/issues/89>`__)
* bugfix:Completer: Fix crash when attempting server side completion
  with no region configured option
  (`issue 84 <https://github.com/awslabs/aws-shell/issues/84>`__)
* feature:Lexer: Add lexer/syntax highlighting
  (`issue 27 <https://github.com/awslabs/aws-shell/issues/27>`__)
* feature:Server Side Completion: Add server side completion for
  Elastic Load Balancing
  (`issue 79 <https://github.com/awslabs/aws-shell/pull/79>`__)
* feature:Server Side Completion: Add server side completion for
  Amazon Kinesis
  (`issue 73 <https://github.com/awslabs/aws-shell/pull/73>`__)
* bugfix:Windows: Fix crash when using ``.edit`` on Windows
  (`issue 55 <https://github.com/awslabs/aws-shell/pull/55>`__)
