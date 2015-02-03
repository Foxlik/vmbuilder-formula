=================
vmbuilder-formula
=================
This formula create vm machine using vmbuilder.

.. note::

    See the full `Salt Formulas installation and usage instructions
    <http://docs.saltstack.com/en/latest/topics/development/conventions/formulas.html>`_.

Install
=======


    gitfs:
      - https://github.com/saltstack-formulas/vmbuilder-formula.git

or copy vmbuilder dir in /srv/salt.

You should copy states in /srv/salt, because formula using my states, vmbuilder.py

Available states
================

``vmbuilder``
-------------

Installs the ``vmbuilder`` and package and service for libvirt.

``vmbuilder.machine``
---------------------

Create and confire virtual machine from pillar.

Support
=======
Check in Ubuntu 14.04
