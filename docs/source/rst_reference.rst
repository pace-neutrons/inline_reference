RST Reference
=============


.. rst:role:: iref:ref

    Creates a reference to either a :rst:role:`iref:target` or a :rst:role:`iref:backlink`.

    *Must* use the full syntax of ``:iref:ref:`title<id>``` where ``title`` is the text that will be
    rendered and ``id`` is the ID used to find the target of the reference. Any number of references
    with the same ``id`` can be created (they will link to the same place).


.. rst:role:: iref:target

    Creates a target for a reference. :rst:role:`iref:ref` can be used to link to this target.

    *Must* use the full syntax of ``:iref:target:`title<id>``` where ``title`` is the text that will
    be rendered and ``id`` is the *globally unique* ID used to distinguish the target from others.


.. rst:role:: iref:backlink

    Creates a target for a reference, while also creating links back to all the :rst:role:`iref:ref`
    that link to itself.

    *Must* use the full syntax of ``:iref:backlink:`title<id>``` where ``title`` is the text that will
    be rendered and ``id`` is the *globally unique* ID used to distinguish the target from others.


.. rst:role:: iref:mref

    Creates a link to its paired :rst:role:`iref:mref` while also being a target for the link from
    its paired :rst:role:`iref:mref`.

    *Must* use the full syntax of ``:iref:mref:`title<id>``` where ``title`` is the text that will
    be rendered and ``id`` is the *globally unique* ID used to pair up :rst:role:`iref:mref`.
    Exactly *two* instances of :rst:role:`iref:mref` must share the same ``id``.

