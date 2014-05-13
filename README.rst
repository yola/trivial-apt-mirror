============================
Mirror a trivial APT archive
============================

A trivial archive is one without pools and components. The kind of thing
you'd create with ``dpkg-scanpackages``. For a full, official style
archive, you can use debmirror_ or apt-mirror_.

.. _debmirror: https://packages.debian.org/debmirror
.. _apt-mirror: https://packages.debian.org/apt-mirror

A trivial archive has a line in ``sources.list`` that looks like::

    deb http://archive.example.net/debian/ binary/

----
TODO
----

This works on the Jenkins CI mirror, but probably not on anything else,
yet. Notably, it doesn't yet support:

* Source packages.
* Cleanup.
* Mirroring to S3.
* Unsigned archives.
* ``Release.gpg`` signature verification.
* ``InRelease``.
* Atomic updates.
