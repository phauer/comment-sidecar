.PHONY: all test import

SHELL:=/bin/bash
VENV:=.venv
ACTIVATE=source $(VENV)/bin/activate
test?=test_POST_and_GET_comment

all: test

import: $(VENV)
	$(ACTIVATE);\
	python3 import/import_disqus_comments.py

test: $(VENV)
	$(ACTIVATE);\
	python3 -m unittest discover test

test-main: $(VENV)
	$(ACTIVATE);\
	python3 test/test_comment_sidecar.py

test-single: $(VENV)
	$(ACTIVATE);\
	python3 test/test_comment_sidecar.py CommentSidecarTest.$(test)

$(VENV):
	python3 -m venv $(VENV)
	$(ACTIVATE);\
	pip3 install --requirement requirements.txt

clean:
	rm -r ./$(VENV)