PYTHON = python2.7
PYTHON_TARGETS = bin/python lib/python* include/python*

VIRTUALENV_URL = https://pypi.python.org/packages/py2.py3/v/virtualenv/virtualenv-1.11.2-py2.py3-none-any.whl
VIRTUALENV_MD5 = a18326dc067b528cfd2b3fce495d540d
VIRTUALENV_FILENAME = $(lastword $(subst /, ,$(VIRTUALENV_URL)))
VIRTUALENV_PATH = downloads/$(VIRTUALENV_FILENAME)
VIRTUALENV = $(PYTHON) virtualenv/virtualenv.py

MFSBSD_URL = http://mfsbsd.vx.sk/files/iso/9/amd64/mfsbsd-se-9.2-RELEASE-amd64.iso
MFSBSD_FILENAME = $(lastword $(subst /, ,$(MFSBSD_URL)))
MFSBSD_PATH = downloads/$(MFSBSD_FILENAME)
MFSBSD_MD5 = 660d2b65e55a982c071891b7996fe684

VM_BASEFOLDER = $(abspath vm)
VM_NAME = freebsd-test-dummy
VM_PATH = $(VM_BASEFOLDER)/$(VM_NAME)
VM_VBOX = $(VM_PATH)/$(VM_NAME).vbox
VM_BOOT_DISK = $(VM_PATH)/boot.vdi

all: .installed.cfg

.SUFFIXES:

.SECONDARY: virtualenv/virtualenv.py

.INTERMEDIATE: check_virtualenv_download \
	python
	check_mfsbsd_download mfsbsd_download

.PHONY: all \
	vm startvm stopvm bootstrapvm destroyvm \
	clean dist-clean


downloads:
	mkdir -p downloads


check_virtualenv_download:
	@test "`md5 -q $(VIRTUALENV_PATH)`" = "$(VIRTUALENV_MD5)" || rm -f $(VIRTUALENV_PATH)

$(VIRTUALENV_PATH): downloads
	wget -c "$(VIRTUALENV_URL)" -O $(VIRTUALENV_PATH)

virtualenv/virtualenv.py: check_virtualenv_download $(VIRTUALENV_PATH)
	$(PYTHON) -m zipfile -e $(VIRTUALENV_PATH) virtualenv


$(PYTHON_TARGETS): python

python: virtualenv/virtualenv.py
	$(VIRTUALENV) --clear .
	-./clear-setuptools-dependency-links
	touch $(PYTHON_TARGETS)


bin/ansible: $(PYTHON_TARGETS)
	bin/pip install --upgrade --force-reinstall ansible
	touch bin/ansible


bin/buildout: $(PYTHON_TARGETS) bin/ansible
	bin/pip install --upgrade --force-reinstall zc.buildout
	touch bin/buildout
	-./clear-setuptools-dependency-links


.installed.cfg: bin/buildout buildout.cfg src/*/setup.py
	bin/buildout -v


check_mfsbsd_download:
	@test "`md5 -q $(MFSBSD_PATH)`" = "$(MFSBSD_MD5)" || rm -f $(MFSBSD_PATH)

$(MFSBSD_PATH): downloads
	wget -c "$(MFSBSD_URL)" -O $(MFSBSD_PATH)
	touch $(MFSBSD_PATH)

mfsbsd_download: check_mfsbsd_download $(MFSBSD_PATH)


$(VM_PATH):
	mkdir -p $(VM_PATH)


%.vdi: $(VM_PATH)
	VBoxManage createhd --filename $@ --size 102400 --format VDI


$(VM_VBOX): $(VM_BOOT_DISK)
	VBoxManage createvm --name $(VM_NAME) --basefolder $(VM_BASEFOLDER) --ostype FreeBSD_64 --register
	VBoxManage modifyvm $(VM_NAME) --memory 512 --accelerate3d off --boot1 disk --boot2 dvd --acpi on --rtcuseutc on
	VBoxManage storagectl $(VM_NAME) --name "SATA" --add sata
	VBoxManage storageattach $(VM_NAME) --storagectl "SATA" --type dvddrive --port 0 --medium $(MFSBSD_PATH)
	VBoxManage storageattach $(VM_NAME) --storagectl "SATA" --type hdd --port 1 --medium $(VM_BOOT_DISK)
	VBoxManage modifyvm $(VM_NAME) --natpf1 "ssh,tcp,,47022,,22"


vm: mfsbsd_download $(VM_VBOX)


startvm: vm
	VBoxManage startvm $(VM_NAME)


stopvm:
	VBoxManage controlvm $(VM_NAME) acpipowerbutton


bootstrapvm: .installed.cfg
	./bin/ploy do vm-master bootstrap


destroyvm:
	-VBoxManage controlvm $(VM_NAME) poweroff && sleep 2
	-VBoxManage unregistervm $(VM_NAME) --delete


clean: destroyvm
	rm -rf bin lib include share


dist-clean: clean
	git clean -dxxf src
