This is an example of how to use `BSDploy <https://github.com/tomster/bsdploy>`_ to provision and configure a simple webserver in local VirtualBox container.

Requirements
============

BSDploy is currently still in development. This means that for now you will need ``git``, ``python`` and ``virtualenv`` to install it.

This example uses `VirtualBox <https://www.virtualbox.org>`_ and assumes that that is already installed and its command line tools are available in your path.

Running the example
===================

- Run ``make``. This will install development versions of ``BSDploy`` and its dependencies. Give it a minute :)
- If your SSH public key is *not* in ``~/.ssh/identity.pub``, copy it to ``etc/authorized_keys``
- Next run ``make startvm``. This will download a FreeBSD ISO image (ca. 136Mb) so you might want to give that a minute, as well :) 
- It will boot up virtualbox from the downloaded image – wait till the login prompt appears, then...
- Run ``bin/ploy bootstrap-jailhost vm-master`` - this will install FreeBSD from the image onto the VirtualBox container
- Answer ``y`` for the questions coming up
  After reboot run ``bin/ploy configure-jailhost vm-master`` – this will prepare the FreeBSD installation for our use (by installing ezjail and Python etc. onto it).
- Now you can run ``./bin/ploy start webserver`` – this will create a 'naked' jail which we then...
- configure by running ``./bin/ploy playbook deployment/webserver.yml`` (this can randomly fail the first time, simply try again)

If all of the above succeeds, you should be able to visit `http://localhost:47023/ <http://localhost:47023/>`_ in your browser and it should display a sample web page.

To stop the virtual machine, run ``make stopvm``.
To destroy the virtual machine, run ``make destroyvm``.
