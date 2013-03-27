# This Makefile is only used by developers.
PYTHON:=python
VERSION:=$(shell $(PYTHON) setup.py --version)
APPNAME:=$(shell $(PYTHON) setup.py --name)
# Pytest options:
# --resultlog: write test results in file
# -s: do not capture stdout/stderr (some tests fail otherwise)
PYTESTOPTS?=--resultlog=testresults.txt -s
# which test modules to run
TESTS ?= tests/
# set test options
TESTOPTS=

all:


check:
# The check programs used here are mostly local scripts on my private system.
# So for other developers there is no need to execute this target.
	py-tabdaddy
	py-unittest2-compat tests/
	$(MAKE) doccheck

doccheck:
	py-check-docstrings --force \
	  woklib \
	  wok \
	  *.py

pyflakes:
	pyflakes setup.py wok woklib tests

clean:
	find . -name \*.pyc -delete
	find . -name \*.pyo -delete
	rm -rf build dist

localbuild:
	$(PYTHON) setup.py build

test:	localbuild
	$(PYTHON) -m pytest $(PYTESTOPTS) $(TESTOPTS) $(TESTS)

.PHONY: test clean pyflakes check all doccheck localbuild
