You need `VirtualBox <https://www.virtualbox.org>`_ with the command line tools available in your path.

- run ``make``
- Place your public ssh key in ``etc/authorized_keys``
- ``make startvm``
- wait till the login prompt
- ``bin/ploy bootstrap-jailhost vm-master``
- answer ``y`` for the questions coming up
- after reboot run ``bin/ploy configure-jailhost vm-master``
- ``./bin/ploy start test``
- ``./bin/pssh test`` (this might fail the first time, try again)


To destroy the virtual machine, run ``make destroyvm``.

To stop the virtual machine, run ``make stopvm``.
