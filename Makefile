BOOK_OUTPUT := _book
VERIFY_ARGS ?=

.PHONY: build
build:
	npm run build

.PHONY: serve
serve:
	npm run serve

.PHONY: epub
epub:
	npm run epub

.PHONY: pdf
pdf:
	npm run pdf

.PHONY: mobi
mobi:
	npm run mobi

.PHONY: install
install:
	npm ci

.PHONY: check-book
check-book:
	npm run check:book

.PHONY: test
test:
	npm test

.PHONY: verify
verify:
	uv run --locked --script scripts/verify.py $(VERIFY_ARGS)

.PHONY: verify-cluster
verify-cluster:
	uv run --locked --script scripts/verify.py --cluster $(VERIFY_ARGS)

.PHONY: clean
clean:
	rm -rf $(BOOK_OUTPUT)

.PHONY: spell
spell:
	go get github.com/client9/misspell/cmd/misspell
	git ls-files | grep -v /vendor/ | xargs misspell -error -o stderr

.PHONY: help
help:
	@echo "Help for make"
	@echo "make / make build  - Build the book"
	@echo "make serve         - Serve the book on localhost:4000"
	@echo "make install       - Install exact local npm dependencies"
	@echo "make check-book    - Check rendered book output"
	@echo "make test          - Run rendering/checker unit tests"
	@echo "make verify        - Run local manifest/schema checks (may fetch schemas)"
	@echo "make verify-cluster - Run isolated checks; pass --image through VERIFY_ARGS"
	@echo "make epub          - Export EPUB"
	@echo "make pdf           - Export PDF (requires Calibre)"
	@echo "make mobi          - Export MOBI (requires Calibre)"
	@echo "make spell         - Check spelling"
	@echo "make clean         - Remove generated site files"
