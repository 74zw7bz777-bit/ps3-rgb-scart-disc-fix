PYTHON ?= python3
.PHONY: build test verify
build:
	$(PYTHON) -B src/build.py
test:
	cd src && $(PYTHON) -B test_reuse.py && $(PYTHON) -B test_contention.py && $(PYTHON) -B test_session.py && $(PYTHON) -B test_installer.py && $(PYTHON) -B test_lifetime.py && $(PYTHON) -B test_decoder.py && $(PYTHON) -B test_analyze.py && $(PYTHON) -B test_samsara.py && $(PYTHON) -B audit.py
verify: build test
