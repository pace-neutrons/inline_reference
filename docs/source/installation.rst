Installation
************

Installation
============

Pip
---

Currently, the only way to install the extension is by ``pip`` from GitHub. This can be done either
directly from GitHub::

    pip install git+https://github.com/pace-neutrons/inline_reference

Or from a local copy::

    git clone https://github.com/pace-neutrons/inline_reference.git
    pip install inline_reference

Enabling Extension
==================

Before the extension can be used, it has to be added to the list of used extensions inside conf.py::

    extensions = ['inline_reference']
