PYTHON = python2.7
PYTHON_TARGETS = bin/python lib/python* include/python* src/*/setup.py
VIRTUALENV = virtualenv

MFSBSD_URL = http://mfsbsd.vx.sk/files/iso/9/amd64/mfsbsd-se-9.2-RELEASE-amd64.iso
MFSBSD_FILENAME = $(lastword $(subst /, ,$(MFSBSD_URL)))
MFSBSD_PATH = downloads/$(MFSBSD_FILENAME)
MFSBSD_SHA = 4ef70dfd7b5255e36f2f7e1a5292c7a05019c8ce

all: .installed.cfg mfsbsd_download

.SUFFIXES:

.INTERMEDIATE: python \
	check_mfsbsd_download mfsbsd_download

.PHONY: all \
	destroyvm \
	clean dist-clean

downloads:
	mkdir -p downloads


$(PYTHON_TARGETS): python

python:
	$(VIRTUALENV) --clear .


bin/ansible: $(PYTHON_TARGETS)
	bin/pip install --upgrade --force-reinstall ansible
	touch bin/ansible


bin/buildout: $(PYTHON_TARGETS) bin/ansible
	bin/pip install --upgrade --force-reinstall zc.buildout
	touch bin/buildout


.installed.cfg: bin/buildout buildout.cfg src/*/setup.py
	bin/buildout -v

check_mfsbsd_download: .installed.cfg
	bin/python bin/ploy-download "$(MFSBSD_URL)" $(MFSBSD_SHA) "$(MFSBSD_PATH)"

$(MFSBSD_PATH): downloads
	touch $(MFSBSD_PATH)

mfsbsd_download: check_mfsbsd_download $(MFSBSD_PATH)


destroyvm: .installed.cfg
	bin/ploy terminate ezjail-test-vm


clean: destroyvm
	rm -rf bin lib include share


dist-clean: clean
	git clean -dxxf src