$(eval VERSION := $(shell python setup.py --version))
SDIST := dist/django-readwrite-$(VERSION).tar.gz

all: build

build: $(SDIST)

$(SDIST):
	python setup.py sdist
	rm -rf django_readwrite.egg-info

.PHONY: install
install: $(SDIST)
	sudo pip install $(SDIST)

.PHONY: uninstall
uninstall:
	sudo pip uninstall django-readwrite

.PHONY: register
register:
	python setup.py register

.PHONY: upload
upload:
	python setup.py sdist upload
	rm -rf django_readwrite.egg-info

.PHONY: clean
clean:
	rm -rf dist django_readwrite.egg django_readwrite.egg-info
