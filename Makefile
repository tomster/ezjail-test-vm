# set up deployment infrastructure

VIRTUALENV = virtualenv

install: bin/ploy

bin/ploy: bin/pip
	bin/pip install -r requirements.txt

bin/pip:
	$(VIRTUALENV) --clear .

develop: .installed.cfg

.installed.cfg: bin/buildout buildout.cfg
	bin/buildout -v

bin/buildout: bin/pip
	bin/pip install -r dev-requirements.txt

fetch_assets: bin/ploy
	bin/ploy do vm-master fetch_assets


# download assets required to install freebsd

MFSBSD_URL = http://mfsbsd.vx.sk/files/iso/9/amd64/mfsbsd-se-9.2-RELEASE-amd64.iso
MFSBSD_FILENAME = $(lastword $(subst /, ,$(MFSBSD_URL)))
MFSBSD_PATH = downloads/$(MFSBSD_FILENAME)
MFSBSD_SHA = 4ef70dfd7b5255e36f2f7e1a5292c7a05019c8ce

check-mfsbsd-download:
	echo "$(MFSBSD_SHA)  $(MFSBSD_PATH)" | shasum -c || rm -f $(MFSBSD_PATH)

downloads:
	mkdir -p downloads

$(MFSBSD_PATH): downloads
	wget -c "$(MFSBSD_URL)" -O $(MFSBSD_PATH)
	touch $(MFSBSD_PATH)

mfsbsd-download: check-mfsbsd-download $(MFSBSD_PATH)


# setup and manage a virtualbox instance:

VM_BASEFOLDER = $(abspath vm)
VM_NAME = ezjail-test-vm
VM_PATH = $(VM_BASEFOLDER)/$(VM_NAME)
VM_VBOX = $(VM_PATH)/$(VM_NAME).vbox
VM_BOOT_DISK = $(VM_PATH)/boot.vdi

$(VM_PATH):
	mkdir -p $(VM_PATH)

%.vdi: $(VM_PATH)
	VBoxManage createhd --filename $@ --size 102400 --format VDI

$(VM_VBOX): $(VM_BOOT_DISK)
	VBoxManage createvm --name $(VM_NAME) --basefolder $(VM_BASEFOLDER) --ostype FreeBSD_64 --register
	VBoxManage modifyvm $(VM_NAME) --memory 2048 --accelerate3d off --boot1 disk --boot2 dvd --acpi on --rtcuseutc on
	VBoxManage storagectl $(VM_NAME) --name "SATA" --add sata
	VBoxManage storageattach $(VM_NAME) --storagectl "SATA" --type dvddrive --port 0 --medium $(MFSBSD_PATH)
	VBoxManage storageattach $(VM_NAME) --storagectl "SATA" --type hdd --port 1 --medium $(VM_BOOT_DISK)
	VBoxManage modifyvm $(VM_NAME) --natpf1 "ssh,tcp,,47024,,22" --natpf1 "http,tcp,,47025,,47025" --natpf1 "https,tcp,,47026,,47026"

vm: mfsbsd-download $(VM_VBOX)

start-vm: vm
	VBoxManage startvm $(VM_NAME)

stop-vm:
	VBoxManage controlvm $(VM_NAME) acpipowerbutton

destroy-vm:
	-VBoxManage controlvm $(VM_NAME) poweroff && sleep 2
	-VBoxManage unregistervm $(VM_NAME) --delete


# clean up:

clean-vm: destroy-vm clean

clean:
	git clean -dxxf


.PHONY: clean start-vm stop-vm clean-vm destroy-vm fetch_assets
