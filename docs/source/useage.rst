Quickstart
**********

``inline_reference`` relies on a sphinx domain, but within the domain, all the provided roles can be
used like normal sphinx roles; the one caveat is that for all roles, the full syntax, e.g.
``:iref:ref:`title<id>```, which specifies both the title to be displayed and the link ID, *must* be
used. For example, to create :iref:ref:`this hyperlink<id1>`, the
``:iref:ref:`this hyperlink<id1>``` rst was used.


Simple cross-reference links
----------------------------

As shown above, to create a link, the ``:iref:ref:`title<id>``` role has to be used. However, a link
needs a destination, or a target, which is created using the ``:iref:target:`title<id>``` role. For
a link to be created, an ``:iref:ref:`` role and a ``:iref:target:`` role must share an ID. For
example, the above reference can be linked :iref:target:`here<id1>` by using
``:iref:target:`here<id1>```. Any number of references can be created to point to the same target,
but:

.. warning::

    creating multiple ``:iref:target:`` with the same ID *will* lead to errors.


.. note::

    The IDs used with ``:iref:`` are **global**, meaning that a cross-reference can be created
    between different documents. However, it also means that the IDs must be *globally unique*.

Formatting
^^^^^^^^^^

- The ``title`` provided to the ``:iref:ref:`` role is formatted like any other
  :iref:ref:`sphinx hyperlink<target-formatting>`. The ``id`` is only used for cross-referencing and
  is not visible. All of this is the case even when the ``:iref:ref:`` is used to link to a
  :iref:ref:`backlink<more-backlinks>`.

- The ``title`` provided to ``:iref:target:`` is formatted like the
  :iref:target:`surrounding text<target-formatting>` and therefore should not be distinguishable.
  The ``id`` is likewise used only for cross-referencing and is not made visible.


Backlinks
---------

Backlinks are similar to the targets above, but with the added fun that they also contain links back
to the ``:iref:ref:`` that links to them. They are created with the ``:iref:backlink:`title<id>```
role, where ``title`` is the text that will be displayed and ``id`` is the *globally unique* ID used
to link to the correct backlink. Any number of references can be created to point to the same
target, but:

.. warning::

    creating multiple ``:iref:backlink:`` with the same ID *will* lead to errors.


.. note::

    The IDs used with ``:iref:`` are **global**, meaning that a cross-reference can be created
    between different documents. However, it also means that the IDs must be *globally unique*.

Formatting
^^^^^^^^^^

- If no ``:iref:ref:`` links are created to a backlink, i.e. an empty backlink, the
  :iref:backlink:`backlink<empty-backlink>` will be
  formatted like the surrounding text and so should not be distinguishable.

- If exactly one ``:iref:ref:`` link is created to a backlink, like
  :iref:ref:`this backlink<one-backlink>`, then the :iref:backlink:`backlink<one-backlink>`
  will be formatted like a normal sphinx link. In this case, the pair effectively functions like a
  :ref:`mutual link<mutual_links>`.

- If more than one ``:iref:ref:`` link is created to the same backlink - like
  :iref:ref:`this one<more-backlinks>`, :iref:ref:`this one<more-backlinks>`, and the one in the
  section above - then the :iref:backlink:`backlink<more-backlinks>` itself will be formatted like
  the surrounding text while subscript numbers are used to create the links to the individual
  ``:iref:ref:`` instances.

.. _mutual_links:

Mutual Links
------------

Mutual links form a *pair* of links that link to each other. They are created using the
``:iref:mref:`title<id>``` syntax, where ``title`` is the text that will be displayed and ``id`` is
used for cross-referencing. Exactly two mutual references have to be created for each ID:

.. warning::

    If only one ``:iref:mref:`` with the given ``id`` is created, no link will be made.

.. warning::

    If more than two ``:iref:mref:`` with a given ``id`` are created, the extension will attempt to
    create at least one link between two of them, but the rest will be ignored.

.. note::

    The IDs used with ``:iref:`` are **global**, meaning that a cross-reference can be created
    between different documents. However, it also means that the IDs must be *globally unique*.

Formatting
^^^^^^^^^^

Both mutual links are formatted like normal sphinx references, as can be seen between this
:iref:mref:`link<mref-format>` and this :iref:mref:`link<mref-format>`.