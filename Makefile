PYTHON?=python
SOURCES=squatter

UV:=$(shell uv --version)
ifdef UV
	VENV:=uv venv
	PIP:=uv pip
else
	VENV:=python -m venv
	PIP:=python -m pip
endif

.PHONY: venv
venv:
	$(VENV) .venv
	source .venv/bin/activate && make install
	@echo 'run `source .venv/bin/activate` to use virtualenv'

# The rest of these are intended to be run within the venv, where python points
# to whatever was used to set up the venv.

.PHONY: install
install:
	$(PIP) install -Ue .[dev]

.PHONY: test
test:
	python -m coverage run -m squatter.tests $(TESTOPTS)
	python -m coverage report

.PHONY: format
format:
	python -m ufmt format $(SOURCES)

.PHONY: lint
lint:
	python -m ufmt check $(SOURCES)
	python -m flake8 $(SOURCES)
	python -m mypy squatter

.PHONY: release
release:
	rm -rf dist
	hatch build
	hatch publish
