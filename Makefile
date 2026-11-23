PY ?= python3

.PHONY: validate build test extract segment checksums site audit-links audit-catalog-links

validate:
	$(PY) tools/build.py --check

build:
	$(PY) tools/build.py

test: build
	$(PY) -m unittest discover -s tests -v

site: build
	$(PY) tools/build_site.py

# Network-only audit of the official links in the nine instrument panels.
# Kept out of `make test` so the test suite never depends on the network.
audit-links:
	$(PY) tools/audit_sources.py

# Network-only audit of every official source link in all catalogue records.
audit-catalog-links:
	$(PY) tools/audit_sources.py --scope catalog --workers 8 --output build/catalog-link-audit.json

# Example: make extract ID=un-ga-res-78-265 SRC=source/A_RES_78_265-en.pdf
extract:
	$(PY) tools/extract_text.py $(ID) $(SRC)

# Example: make segment ID=un-ga-res-78-265 MODE=resolution
segment:
	$(PY) tools/segment.py $(ID) --mode $(MODE)
