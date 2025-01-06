inline_reference
****************

Sphinx extension for creating cross-reference links to arbitrary inline text

Why?
====

Have you ever tried to create a cross-reference to a specific bullet point? Or a hyperlink to a line
of a ``literal`` block? Or in any other way attempted to refer to an arbitrary part of the document?
If yes, you have probably run into a wall, because in sphinx the only way to designate a target to
link to via ``:ref:`` is a ``directive``::

    .. _my-ref:: my_label

    * list


which means that links can be created only to higher-level elements, like headings, figures, entire
lists, paragraphs, etc. However, this extension removes that limitation by providing a ``role`` for
creating targets for links.


What can it do?
===============

Roles
-----

This extension provides a new domain (``:iref:``) which exposes four roles that can be used anywhere
in text:

* ``:iref:ref:`` which works similar to the
  `sphinx <https://www.sphinx-doc.org/en/master/usage/referencing.html#role-ref>`_
  ``:ref:`` role, but works with (only) the other new roles.

* ``:iref:target:`` which is a role version of the
  `sphinx <https://www.sphinx-doc.org/en/master/usage/referencing.html#role-ref>`_
  ``.. _ref::`` and so can be used anywhere.

* ``:iref:backlink:`` which is similar to ``:iref:target:``, but it additionally creates a link to
  each ``:iref:ref:`` that links to it.

* ``:iref:mref:`` which must be used twice and creates a set of 2 mutually linked hyperlinks.


Output Formats
--------------

Presently, the following output formats are supported:

* HTML5
* Text
* LaTeX


Features
========

* Cross-reference hyperlink creation across pages (LaTeX currently not supported, see sphinx
  `#12063`_

* Parallel-write safe

.. _#12063: https://github.com/sphinx-doc/sphinx/issues/12063


Contents
========

.. toctree::
    :maxdepth: 1

    installation
    useage
    rst_reference
    api

