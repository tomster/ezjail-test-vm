# coding: utf-8
from fabric.api import env, put, run, settings, hide
from mr.awsome.common import yesno
import os
import sys


env.shell = '/usr/local/bin/bash -l -c'


def bootstrap():
    if not os.path.exists('../common/authorized_keys'):
        print "You have to create deployment/common/authorized_keys first."
        sys.exit(1)
    env.server.config['fingerprint'] = '02:2e:b4:dd:c3:8a:b7:7b:ba:b2:4a:f0:ab:13:f4:2d'
    env.server.config['password-fallback'] = True
    env.server.config['password'] = 'mfsroot'
    env.shell = '/bin/sh -c'
    put('../zfsinstall/zfsinstall', '/root/bin/myzfsinstall', mode='0755')
    with settings(hide('output', 'warnings'), warn_only=True):
        mounts = run('mount')
    if '/dev/cd0 on /rw/cdrom' not in mounts:
        run('mount_cd9660 /dev/cd0 /cdrom')
    devices = ('ada0',)
    if not yesno("Continuing will destroy the existing data on the following devices: %s\nContinue?" % ', '.join(devices)):
        return
    # install FreeBSD in ZFS root
    devices_args = ' '.join('-d %s' % x for x in devices)
    run('destroygeom %s -p system -p tank' % devices_args)
    run('myzfsinstall %s -p system -V 28 -u /cdrom/9.2-RELEASE-amd64 -s 1G -z 4G' % devices_args)
    # mount devfs inside the new system
    if 'devfs on /rw/dev' not in mounts:
        run('mount -t devfs devfs /mnt/dev')
    # setup authorized_keys
    run('mkdir -p /mnt/root/.ssh && chmod 0600 /mnt/root/.ssh')
    put('../common/authorized_keys', '/mnt/root/.ssh/authorized_keys')
    # setup config files
    put('rc.conf', '/mnt/etc/rc.conf')
    put('sysctl.conf', '/mnt/etc/sysctl.conf')
    put('ipf.rules', '/mnt/etc/ipf.rules')
    put('ipnat.rules', '/mnt/etc/ipnat.rules')
    put('sshd_config', '/mnt/etc/ssh/sshd_config')
    put('sshd_config', '/mnt/etc/ssh/sshd_config.base')
    put('dhclient-exit-hooks', '/mnt/etc/dhclient-exit-hooks', mode=0744)
    run('cp /etc/resolv.conf /mnt/etc/resolv.conf')
    # setup pkgng
    put('../common/make.conf', '/mnt/etc/make.conf')
    run('mkdir -p /mnt/usr/local/etc/pkg/repos')
    put('../common/pkg.conf', '/mnt/usr/local/etc/pkg.conf')
    put('../common/FreeBSD.conf', '/mnt/usr/local/etc/pkg/repos/FreeBSD.conf')
    with settings(hide('warnings'), warn_only=True):
        run('chroot /mnt pkg')
    # run pkg2ng for which the shared library path needs to be updated
    run('chroot /mnt /etc/rc.d/ldconfig start')
    run('chroot /mnt pkg2ng')
    # install some base packages
    run('chroot /mnt pkg install ezjail sudo screen bash python')
    # create data partition and zfs pool and make sure it's aligned at 4k
    run('gpart add -t freebsd-zfs -l tank-ada0 ada0')
    run('gnop create -S 4096 /dev/gpt/tank-ada0')
    run('zpool create -o version=28 -o altroot=/mnt -o cachefile=/boot/zfs/zpool.cache -m none tank /dev/gpt/tank-ada0.nop')
    run('zfs set atime=off tank')
    run('zfs set checksum=fletcher4 tank')
    run('zpool export tank')
    run('gnop destroy /dev/gpt/tank-ada0.nop')
    run('zpool import -o altroot=/mnt -o cachefile=/boot/zfs/zpool.cache tank')
    # add jails filesystem and ezjail.conf
    run('zfs create -o mountpoint=/var/jails tank/jails')
    put('../common/ezjail.conf', '/mnt/usr/local/etc/ezjail.conf')
    # copy zpool.cache again (was done in zfsinstall before, but we added more)
    run('/bin/cp /boot/zfs/zpool.cache /mnt/boot/zfs/')
    # reduce autoboot delay
    run('echo autoboot_delay=-1 >> /mnt/boot/loader.conf')
    # generate ssh host keys
    run("ssh-keygen -t rsa1 -b 1024 -f /mnt/etc/ssh/ssh_host_key -N ''")
    # run("ssh-keygen -t rsa -f /mnt/etc/ssh/ssh_host_rsa_key -N ''")
    put('ssh_host_rsa_key', '/mnt/etc/ssh/ssh_host_rsa_key', mode=0600)
    put('ssh_host_rsa_key.pub', '/mnt/etc/ssh/ssh_host_rsa_key.pub', mode=0644)
    run("ssh-keygen -t dsa -f /mnt/etc/ssh/ssh_host_dsa_key -N ''")
    run("ssh-keygen -t ecdsa -f /mnt/etc/ssh/ssh_host_ecdsa_key -N ''")
    fingerprint = run("ssh-keygen -lf /mnt/etc/ssh/ssh_host_rsa_key")
    # reboot
    with settings(hide('warnings'), warn_only=True):
        run('reboot')
    print "The SSH fingerprint of the newly bootstrapped server is:"
    print fingerprint


def bootstrap_ezjail():
    with settings(hide('warnings'), warn_only=True):
        result = run('test -e /var/jails/basejail')
    if result.return_code != 0:
        run('ezjail-admin install')
    run('rm -rf /var/jails/flavours/base')
    run('mkdir -p /var/jails/flavours/base/etc/ssh')
    run('mkdir -p /var/jails/flavours/base/root/.ssh')
    run('chmod 0600 /var/jails/flavours/base/root/.ssh')
    run('cp /etc/resolv.conf /var/jails/flavours/base/etc/resolv.conf')
    put('../common/make.conf', '/var/jails/flavours/base/etc/make.conf')
    run('mkdir -p /var/jails/flavours/base/usr/local/etc/pkg/repos')
    put('../common/pkg.conf', '/var/jails/flavours/base/usr/local/etc/pkg.conf')
    put('../common/FreeBSD.conf', '/var/jails/flavours/base/usr/local/etc/pkg/repos/FreeBSD.conf')
    run('echo sshd_enable=\\"YES\\" >> /var/jails/flavours/base/etc/rc.conf')
    run('echo PermitRootLogin without-password >> /var/jails/flavours/base/etc/ssh/sshd_config')
    run('cp /root/.ssh/authorized_keys /var/jails/flavours/base/root/.ssh/authorized_keys')
    run(u'echo Gehe nicht über Los. > /var/jails/flavours/base/etc/motd'.encode('utf-8'))