*************************
Gardena Bluetooth Control
*************************

This module support controlling gardena bluetooth enabled watering
computers.

It's main target is for use with Home Assistant. But can be used
standalone as well. Its mainly consist of list of know services
and characteristics, and parser for these.

.. note::
    The devices only allow a single paired connection, and require
    a factory reset to allow a new controller to connect.

Module
======

Commandline
===========

Scan for possible devices

.. code-block:: bash

    python -m gardena_bluetooth scan

Connect to device and dump it's data

.. code-block:: bash

    pyhton -m gardena_bluetooth connect [ADDRESS]
