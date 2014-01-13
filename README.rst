You need `VirtualBox <https://www.virtualbox.org>`_ with the command line tools available in your path.

- Place your public ssh key in ``deployment/common/authorized_keys``
- ``make startvm``
- wait till the login prompt
- ``make bootstrapvm``
- answer ``y`` for the questions coming up
- after reboot run ``/bin/aws playbook deployment/vm-master.yml``
- then ``./bin/aws do vm-master bootstrap_ezjail``
- ``./bin/aws start test``
- ``./bin/assh test`` (this might fail the first time, try again)
- ???
- Profit!

To destroy the virtual machine, run ``make destroyvm``.

To stop the virtual machine, run ``make stopvm``.
