docs/create-simple-html-from-rst.html: docs/index.rst
		./get-download-counts-from-galaxy.py
		cd docs && rst2html4 index.rst index.html
