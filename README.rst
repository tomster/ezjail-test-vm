This is an example of how to use `BSDploy`_ to provision and configure a `FreeBSD`_ jailhost in a local `VirtualBox`_ container and how to create various jails inside it.


Requirements
============

`BSDploy`_ is currently still in development. This means that for now you will need ``git``, ``python`` and ``virtualenv`` to install it.

This example uses `VirtualBox`_ and assumes that that is already installed and its command line tools are available in your path.

Installation
============

If you want to install the latest stable release of bsdploy, run ``make install``, if you are keen on the bleeding edge and want to install the development version, run ``make develop``.


Creating and configuring the jail host
======================================

- Next run ``make start-vm``. This will download a `FreeBSD ISO image (mfsBSD)`_ (ca. 136Mb) so you might want to give it a minute :) 
- It will boot up VirtualBox from the downloaded image – wait until the login prompt appears, then...
- Run ``bin/ploy bootstrap-jailhost`` - this will install FreeBSD from the image onto the VirtualBox container
- Answer ``y`` for the questions coming up
- After the installation has completed the machine will automatically reboot.
- After the machine has booted into the fresh installation, run ``bin/ploy configure-jailhost`` – this will prepare the `FreeBSD`_ installation for our use (by installing `ezjail`_ and `Python`_ etc. onto it).


Install a simple web server
===========================

The first example will install a (very) minimal ``nginx`` webserver along with a 'hello world' page. The pattern ``bsdploy`` offers is to first create and start the 'naked' jail and then allows you to run an ansible playbook against it.

- So, first run ``./bin/ploy start webserver``
- Then you configure it by running ``./bin/ploy playbook deployment/webserver.yml`` (currently the SSH connection can randomly fail upon the first attempt – if this happens, simply try again)

If the above succeeded, you should be able to visit `http://localhost:47023/ <http://localhost:47023/>`_ in your browser and it should display the sample web page.


Install a Bittorrent Sync node
==============================

As a slightly less simple example let's install a `BitTorrent Sync <http://www.bittorrent.com/sync>`_ node.

As before, first create the jail::

	bin/ploy start btsync

Then configure it by running the playbook against it like so::

	bin/ploy playbook deployment/btsync.yml

After the playbook has run its course you should be able to log into the ``btsync`` web interface at `http://localhost:16668 <http://localhost:16668/gui/en/index.html>`_ using the credentials from ``etc/ploy.conf`` (by default ``admin``/``admin``).

Try clicking on `Add Folder <http://localhost:16668/gui/en/index.html#add-dialog>`_, select the pre-created folder inside the jail at ``/var/btsync-data`` and create a secret for it. You now should be able to connect to the node from any client.


Clean up
========

To stop the virtual machine, run ``make stopvm``.

To destroy the virtual machine, run ``make destroyvm``.


.. _`BSDploy`: https://github.com/tomster/bsdploy
.. _`FreeBSD`: http://freebsd.org
.. _`VirtualBox`: https://www.virtualbox.org
.. _`FreeBSD ISO image (mfsBSD)`: http://mfsbsd.vx.sk
.. _`ezjail`: http://erdgeist.org/arts/software/ezjail/
.. _`Python`: http://www.python.org


TODO:
-----

- [ ] fix online installation (`/mnt/var/cache/pkg/digest.txz` missing)
- [ ] allow providing of the jailhost, even if there is only one