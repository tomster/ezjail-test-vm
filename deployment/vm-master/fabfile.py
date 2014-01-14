# coding: utf-8
from fabric.api import env, put, run, settings, hide
from mr.awsome.ezjail.fabric import bootstrap

# shutup pyflakes
(bootstrap, )


env.shell = '/bin/sh -c'


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
        result = run('zfs list -H /usr/jails')
    if result.return_code != 0:
        run('zfs create -o mountpoint=/usr/jails {data_pool_name}/jails'.format(data_pool_name=data_pool_name))
    with settings(hide('warnings'), warn_only=True):
        result = run('test -e /usr/jails/basejail')
    if result.return_code != 0:
        run('ezjail-admin install')
    run('rm -rf /usr/jails/flavours/base')
    run('mkdir -p /usr/jails/flavours/base/etc/ssh')
    run('mkdir -p /usr/jails/flavours/base/root/.ssh')
    run('chmod 0600 /usr/jails/flavours/base/root/.ssh')
    run('cp /etc/resolv.conf /usr/jails/flavours/base/etc/resolv.conf')
    put('../roles/common/files/make.conf', '/usr/jails/flavours/base/etc/make.conf')
    run('mkdir -p /usr/jails/flavours/base/usr/local/etc/pkg/repos')
    put('../roles/common/files/pkg.conf', '/usr/jails/flavours/base/usr/local/etc/pkg.conf')
    put('../roles/common/files/FreeBSD.conf', '/usr/jails/flavours/base/usr/local/etc/pkg/repos/FreeBSD.conf')
    run("tar -x -C /usr/jails/flavours/base --chroot --exclude '+*' -f /var/cache/pkg/All/pkg.txz")
    run('echo sshd_enable=\\"YES\\" >> /usr/jails/flavours/base/etc/rc.conf')
    run('echo PermitRootLogin without-password >> /usr/jails/flavours/base/etc/ssh/sshd_config')
    run('echo Subsystem sftp /usr/libexec/sftp-server >> /usr/jails/flavours/base/etc/ssh/sshd_config')
    run('cp /root/.ssh/authorized_keys /usr/jails/flavours/base/root/.ssh/authorized_keys')
    run(u'echo Gehe nicht über Los. > /usr/jails/flavours/base/etc/motd'.encode('utf-8'))
