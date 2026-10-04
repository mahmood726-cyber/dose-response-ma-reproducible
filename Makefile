PYTHON ?= python
.PHONY: reproduce quick setup serve clean
reproduce:
	$(PYTHON) reproduce.py
quick:
	$(PYTHON) reproduce.py --quick
setup:
	Rscript bench/install_r_packages.R
	$(PYTHON) -m pip install -r requirements.txt
serve:
	$(PYTHON) -m http.server 8080
clean:
	rm -rf results outputs
