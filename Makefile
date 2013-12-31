VIRTUALENV = virtualenv

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


bin/python:
	$(VIRTUALENV) --system-site-packages --clear .
	-./clear-setuptools-dependency-links


bin/buildout: bin/python
	bin/pip install zc.buildout


.installed.cfg: bin/buildout buildout.cfg
	bin/buildout -v


check_mfsbsd_download:
	@test "`md5 -q $(MFSBSD_PATH)`" = "660d2b65e55a982c071891b7996fe684" || rm -f $(MFSBSD_PATH)


downloads:
	mkdir -p downloads


$(MFSBSD_PATH): downloads
	wget -c "$(MFSBSD_URL)" -O $(MFSBSD_PATH)
	touch $(MFSBSD_PATH)


mfsbsd_download: check_mfsbsd_download $(MFSBSD_PATH)


$(VM_PATH):
	mkdir -p $(VM_PATH)


$(VM_BOOT_DISK): $(VM_PATH)
	VBoxManage createhd --filename $(VM_BOOT_DISK) --size 102400 --format VDI


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
	./bin/aws do vm-master bootstrap


destroyvm:
	-VBoxManage controlvm $(VM_NAME) poweroff && sleep 2
	VBoxManage unregistervm $(VM_NAME) --delete
