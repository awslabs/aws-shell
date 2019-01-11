# Eventually I'll add:
# py.test --cov awsshell --cov-report term-missing --cov-fail-under 95 tests/
# which will fail if tests are under 95%

prepare:
	###### FLAKE8 #####
	# Install all requirements for testing and debugging
	pip install -U -r requirements-dev.txt
	pip install -U -r requirements-test.txt
	python scripts/ci/install

check:
	###### FLAKE8 #####
	# No unused imports, no undefined vars,
	# follow pep8, and max cyclomatic complexity of 15.
	# I'd eventually like to lower this down to < 10.
	flake8 --ignore=E731,W503 --exclude awsshell/compat.py --max-complexity 15 awsshell/*.py
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
	# Proper docstring conventions according to pep257
	#
	#
	pep257 --add-ignore=D100,D101,D102,D103,D104,D105,D204
	#
	#
	#
	###### PYLINT ERRORS ONLY ######
	#
	#
	#
	pylint --rcfile .pylintrc -E awsshell

test:
	python scripts/ci/run-tests

integration:
	python scripts/ci/run-integ-tests

pylint:
	###### PYLINT ######
	# Python linter.  This will generally not have clean output.
	# So you'll need to manually verify this output.
	#
	#
	pylint --rcfile .pylintrc awsshell

coverage:
	py.test --cov awsshell --cov-report term-missing tests/
