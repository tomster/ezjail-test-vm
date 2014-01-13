# coding: utf-8
from fabric.api import env, put, run, settings, hide
import os
import sys


env.shell = '/bin/sh -c'


def bootstrap(**kwargs):
    from mr.awsome.common import yesno
    if not os.path.exists('../roles/common/files/identity.pub'):
        print "You have to create deployment/roles/common/files/identity.pub first."
        sys.exit(1)
    env.server.config['fingerprint'] = '02:2e:b4:dd:c3:8a:b7:7b:ba:b2:4a:f0:ab:13:f4:2d'
    env.server.config['password-fallback'] = True
    env.server.config['password'] = 'mfsroot'
    env.server.config.update(kwargs)
    with settings(hide('output', 'warnings'), warn_only=True):
        import math
        mounts = run('mount')
        sysctl_devices = run('sysctl -n kern.disks').strip().split()
        realmem = run('sysctl -n hw.realmem').strip()
        realmem = float(realmem) / 1024 / 1024
        realmem = 2 ** int(math.ceil(math.log(realmem, 2)))
    cd_device = env.server.config.get('bootstrap-cd-device', 'cd0')
    if '/dev/{dev} on /rw/cdrom'.format(dev=cd_device) not in mounts:
        run('test -e /dev/{dev} && mount_cd9660 /dev/{dev} /cdrom || true'.format(dev=cd_device))
    usb_device = env.server.config.get('bootstrap-usb-device', 'da0a')
    if '/dev/{dev} on /rw/media'.format(dev=usb_device) not in mounts:
        run('test -e /dev/{dev} && mount /dev/{dev} /media || true'.format(dev=usb_device))
    bsd_url = env.server.config.get('bootstrap-bsd-url')
    if not bsd_url:
        bsd_url = run("find /cdrom/ /media/ -name 'base.txz' -exec dirname {} \;").strip()
    if not bsd_url:
        print "Found no BSD system to install, please specify bootstrap-bsd-url"
        return
    devices = set(sysctl_devices) - set([cd_device, usb_device])
    devices = env.server.config.get('bootstrap-system-devices', ' '.join(devices)).split()
    print "Found the following disk devices on the system:\n    %s" % ' '.join(sysctl_devices)
    if not yesno("Continuing will destroy the existing data on the following devices:\n%s\nContinue?" % ' '.join(devices)):
        return
    zfsinstall = env.server.config.get('bootstrap-zfsinstall')
    if zfsinstall:
        put(zfsinstall, '/root/bin/myzfsinstall', mode='0755')
        zfsinstall = 'myzfsinstall'
    else:
        zfsinstall = 'zfsinstall'
    # install FreeBSD in ZFS root
    devices_args = ' '.join('-d %s' % x for x in devices)
    system_pool_name = env.server.config.get('bootstrap-system-pool-name', 'system')
    data_pool_name = env.server.config.get('bootstrap-data-pool-name', 'tank')
    swap_arg = ''
    swap_size = env.server.config.get('bootstrap-swap-size', '%iM' % (realmem * 2))
    if swap_size:
        swap_arg = '-s %s' % swap_size
    system_pool_size = env.server.config.get('bootstrap-system-pool-size', '20G')
    run('destroygeom {devices_args} -p {system_pool_name} -p {data_pool_name}'.format(
        devices_args=devices_args,
        system_pool_name=system_pool_name,
        data_pool_name=data_pool_name))
    run('{zfsinstall} {devices_args} -p {system_pool_name} -V 28 -u {bsd_url} {swap_arg} -z {system_pool_size}'.format(
        zfsinstall=zfsinstall,
        devices_args=devices_args,
        system_pool_name=system_pool_name,
        bsd_url=bsd_url,
        swap_arg=swap_arg,
        system_pool_size=system_pool_size))
    # create partitions for data pool
    for device in devices:
        run('gpart add -t freebsd-zfs -l {data_pool_name}_{device} {device}'.format(
            data_pool_name=data_pool_name,
            device=device))
    # mount devfs inside the new system
    if 'devfs on /rw/dev' not in mounts:
        run('mount -t devfs devfs /mnt/dev')
    # setup authorized_keys
    run('mkdir -p /mnt/root/.ssh && chmod 0600 /mnt/root/.ssh')
    put('../roles/common/files/identity.pub', '/mnt/root/.ssh/authorized_keys')
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
    # install pkg, the tarball is also used for the ezjail flavour in bootstrap_ezjail
    run('mkdir -p /mnt/var/cache/pkg/All')
    run('fetch -o /mnt/var/cache/pkg/All/pkg.txz http://pkg.freebsd.org/freebsd:9:x86:64/latest/Latest/pkg.txz')
    run('chmod 0600 /mnt/var/cache/pkg/All/pkg.txz')
    run("tar -x -C /mnt --chroot --exclude '+*' -f /mnt/var/cache/pkg/All/pkg.txz")
    # run pkg2ng for which the shared library path needs to be updated
    run('chroot /mnt /etc/rc.d/ldconfig start')
    run('chroot /mnt pkg2ng')
    # install some base packages
    run('chroot /mnt pkg install ezjail python')
    put('../common/ezjail.conf', '/mnt/usr/local/etc/ezjail.conf')
    # remove autoboot delay
    run('echo autoboot_delay=-1 >> /mnt/boot/loader.conf')
    # ssh host keys
    if os.path.exists('ssh_host_key'):
        put('ssh_host_key', '/mnt/etc/ssh/ssh_host_key', mode=0600)
        put('ssh_host_key.pub', '/mnt/etc/ssh/ssh_host_key.pub', mode=0644)
    else:
        run("ssh-keygen -t rsa1 -b 1024 -f /mnt/etc/ssh/ssh_host_key -N ''")
    if os.path.exists('ssh_host_rsa_key'):
        put('ssh_host_rsa_key', '/mnt/etc/ssh/ssh_host_rsa_key', mode=0600)
        put('ssh_host_rsa_key.pub', '/mnt/etc/ssh/ssh_host_rsa_key.pub', mode=0644)
    else:
        run("ssh-keygen -t rsa -f /mnt/etc/ssh/ssh_host_rsa_key -N ''")
    if os.path.exists('ssh_host_dsa_key'):
        put('ssh_host_dsa_key', '/mnt/etc/ssh/ssh_host_dsa_key', mode=0600)
        put('ssh_host_dsa_key.pub', '/mnt/etc/ssh/ssh_host_dsa_key.pub', mode=0644)
    else:
        run("ssh-keygen -t dsa -f /mnt/etc/ssh/ssh_host_dsa_key -N ''")
    if os.path.exists('ssh_host_ecdsa_key'):
        put('ssh_host_ecdsa_key', '/mnt/etc/ssh/ssh_host_ecdsa_key', mode=0600)
        put('ssh_host_ecdsa_key.pub', '/mnt/etc/ssh/ssh_host_ecdsa_key.pub', mode=0644)
    else:
        run("ssh-keygen -t ecdsa -f /mnt/etc/ssh/ssh_host_ecdsa_key -N ''")
    fingerprint = run("ssh-keygen -lf /mnt/etc/ssh/ssh_host_rsa_key")
    # reboot
    with settings(hide('warnings'), warn_only=True):
        run('reboot')
    print "The SSH fingerprint of the newly bootstrapped server is:"
    print fingerprint


def bootstrap_ezjail():
    from mr.awsome.config import value_asbool
    # create data partition and zfs pool and make sure it's aligned at 4k
    geli = value_asbool(env.server.config.get('bootstrap-geli', ''))
    data_pool_name = env.server.config.get('bootstrap-data-pool-name', 'tank')
    with settings(hide('warnings'), warn_only=True):
        result = run('zpool list -H {data_pool_name}'.format(
            data_pool_name=data_pool_name))
    if result.return_code != 0:
        devices = run("find /dev/gpt/ -name '{data_pool_name}_*' \\! -name '*.eli' -exec basename {{}} \\;".format(
            data_pool_name=data_pool_name)).strip().split()
        if geli:
            data_devices = []
            rc_geli_devices = []
            geli_passphrase_location = '/root/geli-passphrase'
            run('openssl rand -base64 32 > {geli_passphrase_location}'.format(
                geli_passphrase_location=geli_passphrase_location))
            run('chmod 0600 {geli_passphrase_location}'.format(
                geli_passphrase_location=geli_passphrase_location))
            for device in devices:
                run('geli init -s 4096 -l 256 -J {geli_passphrase_location} /dev/gpt/{device}'.format(
                    geli_passphrase_location=geli_passphrase_location,
                    device=device))
                run('geli attach -j {geli_passphrase_location} /dev/gpt/{device}'.format(
                    geli_passphrase_location=geli_passphrase_location,
                    device=device))
                data_device = '/dev/gpt/{device}.eli'.format(
                    device=device)
                data_devices.append(data_device)
                rc_geli_device = 'gpt/{device}'.format(
                    device=device)
                rc_geli_devices.append(rc_geli_device)
            rc = 'geli_devices="%s"' % ' '.join(rc_geli_devices)
            for rc_geli_device in rc_geli_devices:
                rc = '{rc}\ngeli_{rc_geli_device}_flags="-j {geli_passphrase_location}"'.format(
                    rc=rc,
                    rc_geli_device=rc_geli_device.replace('/', '_'),
                    geli_passphrase_location=geli_passphrase_location)
            print rc
        else:
            data_devices = []
            for device in devices:
                run('gnop create -S 4096 {device}'.format(
                    device=device))
                data_device = '{device}.nop'.format(
                    device=device)
                data_devices.append(data_device)
        run('zpool create -o version=28 -m none {data_pool_name} {data_devices}'.format(
            data_pool_name=data_pool_name,
            data_devices=' '.join(data_devices)))
        run('zfs set atime=off {data_pool_name}'.format(data_pool_name=data_pool_name))
        run('zfs set checksum=fletcher4 {data_pool_name}'.format(data_pool_name=data_pool_name))
        run('zpool export {data_pool_name}'.format(data_pool_name=data_pool_name))
        if not geli:
            for data_device in data_devices:
                run('gnop destroy {data_device}'.format(data_device=data_device))
        run('zpool import {data_pool_name}'.format(data_pool_name=data_pool_name))
    # add jails filesystem and ezjail.conf
    with settings(hide('warnings'), warn_only=True):
        result = run('zfs list -H /var/jails')
    if result.return_code != 0:
        run('zfs create -o mountpoint=/var/jails {data_pool_name}/jails'.format(data_pool_name=data_pool_name))
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
    run("tar -x -C /var/jails/flavours/base --chroot --exclude '+*' -f /var/cache/pkg/All/pkg.txz")
    run('echo sshd_enable=\\"YES\\" >> /var/jails/flavours/base/etc/rc.conf')
    run('echo PermitRootLogin without-password >> /var/jails/flavours/base/etc/ssh/sshd_config')
    run('echo Subsystem sftp /usr/libexec/sftp-server >> /var/jails/flavours/base/etc/ssh/sshd_config')
    run('cp /root/.ssh/authorized_keys /var/jails/flavours/base/root/.ssh/authorized_keys')
    run(u'echo Gehe nicht über Los. > /var/jails/flavours/base/etc/motd'.encode('utf-8'))