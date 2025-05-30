.. program:: qvm-start-daemon

:program:`qvm-start-daemon` -- start GUI/AUDIO for qube(s)
==========================================================

.. note::

   `qvm-start-gui` has been renamed to `qvm-start-daemon` as it handles now
   `gui` and `audio`.

.. warning::

   This page was autogenerated from command-line parser. It shouldn't be 1:1
   conversion, because it would add little value. Please revise it and add
   more descriptive help, which normally won't fit in standard ``--help``
   option.

   After rewrite, please remove this admonition.

Synopsis
--------

:command:`qvm-start-daemon` [-h] [--verbose] [--quiet] [--all] [--exclude *EXCLUDE*] [--watch] [--kde] [--force] [--force-stubdomain] [--pidfile *PIDFILE*] [--notify-monitory-layout] [*VMNAME* [*VMNAME* ...]]

Options
-------

.. option:: --help, -h

   show this help message and exit

.. option:: --debug, -d

   Show debug messages

.. option:: --verbose, -v

   increase verbosity

.. option:: --quiet, -q

   decrease verbosity

.. option:: --all

   perform the action on all qubes

.. option:: --exclude

   exclude the qube from --all

.. option:: --watch

   Keep watching for further domain startups

.. option:: --force-stubdomain

   Start GUI to stubdomain-emulated VGA, even if gui-agent is running in the VM

.. option:: --force

   Force running, even if this isn't GUI/Audio domain. GUI domain is a domain
   with 'guivm' qvm-service enabled. Similarly for Audio domain it is
   'audiovm' qvm-service.

.. option:: --kde

   Set KDE specific arguments to gui-daemon - required for proper windows
   decoration on KDE.

.. option:: --pidfile

   Pidfile path to create in --watch mode

.. option:: --notify-monitor-layout

   Notify running instance in --watch mode about changed monitor layout

.. option:: --version

   Show program's version number and exit

Authors
-------

| Joanna Rutkowska <joanna at invisiblethingslab dot com>
| Rafal Wojtczuk <rafal at invisiblethingslab dot com>
| Marek Marczykowski <marmarek at invisiblethingslab dot com>
| Wojtek Porczyk <woju at invisiblethingslab dot com>

| For complete author list see: https://github.com/QubesOS/qubes-core-admin-client.git

.. vim: ts=3 sw=3 et tw=80
