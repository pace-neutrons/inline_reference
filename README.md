# inline_reference

Sphinx extension for creating cross-reference links to arbitrary inline text

## Intro

Have you ever tried to create a cross-reference to a specific bullet point? Or a hyperlink to a line 
of a `literal` block? Or in any other way attempted to refer to an arbitrary part of the document? 
If yes, you have probably run into a wall, because in sphinx the only way to designate a target to 
link to via `:ref:` is a `directive`:

```
.. _my-ref:: my_label
   
* list
```

which means that links can be created only to higher-level elements, like headings, figures, entire 
lists, paragraphs, etc. However, this extension removes that limitation by providing a `role` for 
creating targets for links.

## Quickstart

The extension can be installed via pip (see Installation):

```
pip install git+https://github.com/pace-neutrons/inline_reference
```

Then, you have to add the extension to your `conf.py`:

```python
extensions = [
    'inline_reference',
]
```

And with that, you are ready to use it in your `.rst` documents; `inline_reference` provides a 
sphinx `domain` (`:iref:`), within which all the roles are available:

- `:iref:ref:`
- `:iref:target:`
- `:iref:backlink:`
- `:iref:mref:`

The simplest use-case is the combination of `:iref:ref:`, which functions effectively identical to 
the base sphinx `:ref:` role, and `:iref:target:`, which is the `role` equivalent of the `.. _name:`
domain:

```
This is my text, and I want to create a :iref:ref:`link to a list item<id-list>` and a 
:iref:ref:`link to a word in a paragraph<id-word>` and a 
:iref:ref:`link to a part of a literal<id-literal>`. To do that, I need to

1. Used ``:iref:ref:`` to specify where the cross-reference hyperlink will be placed

   * I need to have used the full ``:ref:title<link-id>`` syntax to specify the ``title``, or the 
     text to be displayed, and the ``link-id``, or the name of the link.
     
2. Used ``:iref:target:`` to specify where I want the link to piont to, for example 
   :iref:target:`right here<id-list>`
   
   * I need to have used the same ``:iref:target:text<link-id>`` syntax here. The ``link-id`` must 
     correspond to an ``:iref:ref:`` role with the same ``link-id``.
     
There can be multiple ``:iref:ref:`` roles pointing to the same ``:iref:target:``, 
:iref:ref:`like so<id-list>`, but there cannot be multiple ``:iref:target:`` with the same 
``link-id``. Still, if properly managed, I can create links to (almost) anywhere, e.g. 
:iref:target:`right here<id-word>`.

.. parsed-literal::

    I can even create a link that points to the inside of a literal block, 
    :iref:target:`like here<id-literal>`, but I need to have used the parsed-literal directive 
    instead of the literal directive.
```

For more information, see the [documentation](https://pace-neutrons.github.io/inline_reference).

## Installation

At the moment, the only way is to install manually via pip, either directly from GitHub:

```
pip install git+https://github.com/pace-neutrons/inline_reference
```

or from a local copy:

```
git clone https://github.com/pace-neutrons/inline_reference.git
pip install inline_reference
```

## Functionality

This extension exposes a sphinx domain which contains 4 roles:

- `:iref:ref:` creates a cross-reference to the specified ID, like the default sphinx `:ref:`
- `:iref:target:` creates a target for `:iref:ref:`, i.e. the location that the created link points to.
  The text specified in `:iref:target:` appears with the same formatting as surrounding text.
- `:iref:backlink:` creates a target for `:iref:ref:` while also creating a link to every 
  `:iref:ref:` that is linked to it.
- `:iref:mref:`, or mutual reference, can be used instead of `:iref:ref:`; it creates both a link to 
  the matching `:iref:mref:` while serving as a target to the matching `:iref:mref:`. These must 
  come in pairs. These links look like sphinx links.