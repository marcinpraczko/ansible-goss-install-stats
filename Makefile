.PHONY: help
help: ## Help: Show this help message
	@echo 'usage: make [target] ...'
	@echo
	@echo 'Targets:'
	@echo '========'
	@egrep '^(.+)\:\ ##\ (.+)' ${MAKEFILE_LIST} | column -t -c 2 -s ':#'

.PHONY: build-all
build-all: ## Build: Build all the things
build-all: get-download-counts-from-galaxy create-simple-html-from-rst

.PHONY: get-download-counts-from-galaxy
get-download-counts-from-galaxy: ## Build: Get download counts from Galaxy
	@echo "---> Makefile: Getting download counts from Galaxy..."
	./get-download-counts-from-galaxy.py

.PHONY: create-simple-html-from-rst
create-simple-html-from-rst: ## Build: Create simple HTML from RST
	@echo "---> Makefile: Creating simple HTML from RST..."
	cd docs && rst2html4 index.rst index.html
	
