# Eventually I'll add:
# py.test --cov awsshell --cov-report term-missing --cov-fail-under 95 tests/
# which will fail if tests are under 95%

check:
	###### FLAKE8 #####
	# No unused imports, no undefined vars,
	# follow pep8, and max cyclomatic complexity of 15.
	# I'd eventually like to lower this down to < 10.
	flake8 --exclude awsshell/compat.py --max-complexity 15 awsshell/*.py
	#
	#
	##### DOC8 ######
	# Correct rst formatting for docstrings
	#
	##
	doc8 awsshell/*.py
	#
	#
	#
	###### PYLINT ######
	# Python linter.
	#
	#
	#
	pylint --rcfile .pylintrc awsshell
	#
	#
	#
	# Proper docstring conventions according to pep257
	#
	#
	pep257 --add-ignore=D100,D101,D102,D103,D104,D105
