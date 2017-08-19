SHELL:=/bin/bash
VENV:=.venv
ACTIVATE=source $(VENV)/bin/activate

all: test

test: $(VENV)
	$(ACTIVATE);\
	python3 -m unittest discover test

test-main: $(VENV)
	$(ACTIVATE);\
	python3 test/test_comment_sidecar.py

$(VENV):
	python3 -m venv $(VENV)
	$(ACTIVATE);\
	pip3 install --requirement requirements.txt

clean:
	rm -r ./$(VENV)