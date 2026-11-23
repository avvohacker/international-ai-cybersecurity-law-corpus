PY ?= python3

.PHONY: validate build test extract segment checksums

validate:
	$(PY) tools/build.py --check

build:
	$(PY) tools/build.py

test: build
	$(PY) -m unittest discover -s tests -v

# Example: make extract ID=un-ga-res-78-265 SRC=source/A_RES_78_265-en.pdf
extract:
	$(PY) tools/extract_text.py $(ID) $(SRC)

# Example: make segment ID=un-ga-res-78-265 MODE=resolution
segment:
	$(PY) tools/segment.py $(ID) --mode $(MODE)
