Requirements
============

BSDploy is currently still in development. This means that for now you will need ``git``, ``python`` and ``virtualenv`` to install it.

This example uses `VirtualBox <https://www.virtualbox.org>`_ and assumes that that is already installed and its command line tools are available in your path.

Running the example
===================

- run ``make``
- If your SSH public key is *not* in ``~/.ssh/identity.pub``, copy it to ``etc/authorized_keys``
- ``make startvm``
- wait till the login prompt
- ``bin/ploy bootstrap-jailhost vm-master``
- answer ``y`` for the questions coming up
- after reboot run ``bin/ploy configure-jailhost vm-master``
- ``./bin/ploy start webserver``
- ``./bin/pssh webserver`` (this might fail the first time, try again)
- ``./bin/ploy playbook deployment/webserver.yml``

If all of the above succeeds, you should be able to visit ``http://localhost:47023/ <http://localhost:47023/>`_ in your browser and it should display a sample web page.

To destroy the virtual machine, run ``make destroyvm``.

To stop the virtual machine, run ``make stopvm``.
