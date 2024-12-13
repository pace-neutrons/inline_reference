"""
In order to work, this extension adds a number of new classes and functions:

* 1 domain - `InlineReferenceDomain` - through which all user-level interactions are exposed and
  which manages persistent data.

* 4 roles within the domain, which allow users to create hyperlinks

  * ``:iref:ref:`` which is handled by `RegisteredXRefRole`
  * ``:iref:target:`` which is handled by `ReferenceTargetRole`
  * ``:iref:backlink:`` which is handled by `BackLinkRole`
  * ``:iref:mref:`` which is handled by `MutualReferenceRole`

* 5 nodes created by the roles and which handle the creation of the links

  * `inline_reference` which identical to the `docutils.nodes.reference` class except for the LaTeX
    build system, and which handles the normal references, from ``:iref:ref:`` to ``:iref:target:``

  * `id_reference` which is similar to `docutils.nodes.reference`, but which holds its own ID to be
    able to be hyperlinked to, and which is used in the references from ``:iref:ref:`` to
    ``:iref:backlink:``

  * `reference_target` which is the simple target for hyperlinks and which is used to represent
    ``:iref:target:``

  * `backlink` which is a new class for representing ``:iref:backlink:``

  * `mutual_ref` which is a new class for working with ``:iref:mref:``

* 2 event hooks for the ``doctree-resolved`` event

  * `process_mutual_reference_nodes` for connecting the pairs of `mutual_ref` nodes, once all the
    nodes have been created.

  * `process_backlink_nodes` for connecting each `backlink` node to each `id_reference` node that
    links to it.

* various ``visit_`` and ``depart_`` functions that implement the writing of each supported output
  format in the cases where the default implementations are not sufficient or similar enough
  functionality does not exist.


How This Works
--------------

Referencing a Normal Target
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By creating a link from ``:iref:ref:name<id>`` to ``:iref:target:name<id>``, two nodes are created
in the middle of the paragraph: a `sphinx.addnodes.pending_xref` node for the reference, and a
`reference_target` node for the target. On creation of the target, it is registered with the domain.
Then, once the entire .rst document is read and all nodes are finished loading, sphinx starts
resolving pending references, which calls the `ReferenceDomain.resolve_xref` method for each
``pending_xref`` node. The domain matches the ``id`` from the ``pending_xref`` to the appropriate
``target``, using the saved information. An `inline_reference` node is created, which will replace
the ``pending_xref`` node. This new node has the ``refid`` and ``refuri`` parameters set and
pointing to the ``ids`` parameter of the `reference_target` node. All that happens after is that
the writer for the selected format will appropriately use this information so that a hyperlink is
created in the output.


Referencing a Backlink
^^^^^^^^^^^^^^^^^^^^^^

By creating a link from ``:iref:ref:name<id>`` to ``:iref:backlink:name<id>``, two nodes are created
in the middle of the paragraph: a `sphinx.addnodes.pending_xref` node for the reference, and a
`reference_target` node for the target. On creation of each, they are registered with the domain,
the reference in the ``loose_refs`` dict and the target in the ``targets`` list. However, since
the reference will need an ID to be able to be linked to, but the only information we have is the ID
of the backlink, the domain creates a unique ID for the reference when registering it.

Then, once the entire .rst document is read and all nodes are finished loading, sphinx starts
resolving pending references, which calls the `ReferenceDomain.resolve_xref` method for each
``pending_xref`` node. Similar to the target case above, the domain matches the ``id`` from the
``pending_xref`` to the appropriate `backlink`. An `id_reference` node is created with the
``refid`` and ``refuri`` parameters set and pointing to the ``ids`` parameter of the `backlink`,
which will allow for the creation of a hyperlink from the reference to the backlink. To enable the
converse, the `id_reference` node's ``ids`` parameter is set to the first stored unique ID that has
not been used yet.

Furthermore, once the tree for the document has been fully resolved, sphinx emits the
``doctree-resolved`` event and calls the `process_backlink_nodes`` function, which finishes the job.
It populates the ``backrefs`` parameter of each `backlink` node with the unique IDs of each
`id_reference` node, using the data from the domain. All that happens after is that
the writer for the selected format will appropriately use this information so that a hyperlink is
created in the output.

Mutual References
^^^^^^^^^^^^^^^^^

By using ``:iref:mref:name<id>`` twice, with the same ID, two `mutual_ref` nodes are created in the
middle of the paragraph. On creation of each, they are registered with the domain, in the
``mutual_refs`` dict. However, since the user provides only one ID, and two will be required under
the hood (one for each node), the domain also creates a unique ID for each, which is immediately
set to the ``ids`` parameter of the created nodes.

Then, once the tree for the document has been fully resolved, sphinx emits the ``doctree-resolved``
event and calls the `process_mutual_reference_nodes` function. This goes over each `mutual_ref` in
the document and edits its ``refid`` and ``refuri`` parameters to point to the ID of the other
corresponding `mutual_ref` node. All that happens after is that
the writer for the selected format will appropriately use this information so that a hyperlink is
created in the output.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
import warnings

from docutils import nodes

from sphinx.application import Sphinx
from sphinx.domains import Domain
from sphinx.roles import XRefRole
from sphinx.util.typing import ExtensionMetadata
from sphinx.util.docutils import SphinxRole


if TYPE_CHECKING:
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
    from sphinx.addnodes import pending_xref, document


class id_reference(nodes.reference):
    """A reference node that contains the ``ids`` parameter."""
    pass


class inline_reference(nodes.reference):
    """A reference node. Required for custom LaTeX writer."""
    pass


def make_refnode(
    builder: Builder,
    fromdocname: str,
    todocname: str,
    targetid: str | None,
    child: nodes.Node | list[nodes.Node],
    title: str | None = None,
    cls: type(nodes.reference) = nodes.reference,
) -> nodes.reference:
    """
    Shortcut to create a reference node.

    This function is mostly copied from the ``sphinx.utils`` package, but further contains the
    `cls` parameter allowing the specification of the particular `docutils.nodes.reference`
    subclass to create.

    Parameters
    ----------
    builder
        The Sphinx builder that is being used.
    fromdocname
        The name of the document in which the reference lies. The origin of the link.
    todocname
        The name of the document in which the target lies. The target of the link.
    targetid
        The id of the target. Use for cross-referencing within a document. Only set if provided.
    child
        The children nodes of the node being made into a link. These nodes are added as children
        nodes to the created reference node.
    title
        The title of the reference. Only set if provided.
    cls
        The class to instantiate. The returned node will be of this type.

    Returns
    -------
    reference_node
        A reference node with 'refid', 'refuri', and 'reftitle' set (if these were provided).
    """
    node = cls('', '', internal=True)
    if targetid:
        node['refid'] = targetid
    if  fromdocname != todocname:
        if targetid:
            node['refuri'] = (
                builder.get_relative_uri(fromdocname, todocname) + '#' + targetid
            )
        else:
            node['refuri'] = builder.get_relative_uri(fromdocname, todocname)
    if title:
        node['reftitle'] = title
    node += child
    return node


def visit_reference_node_default(self: nodes.NodeVisitor, node: nodes.Node) -> None:
    """
    Visit the default reference node in any builder.

    A wrapper around the default ``visit_reference`` method. Used in this package for reference-like
    nodes where the default implementation is sufficient.
    """
    self.visit_reference(node)


def depart_reference_node_default(self: nodes.NodeVisitor, node: nodes.Node) -> None:
    """
    Depart the default reference node in any builder.

    A wrapper around the default ``depart_reference`` method. Used in this package for
    reference-like nodes where the default implementation is sufficient.
    """
    self.depart_reference(node)


def visit_reference_node_latex(self: nodes.NodeVisitor, node: nodes.reference) -> None:
    """
    Visit the `inline_reference` node in the LaTeX builder.

    Creates a LaTeX hyperlink with no hypertarget attached. Should create similar effect to the
    default implementation (which uses ``\hyperref``), but this version has to supercede because
    ``\hyperref`` does not work with ``\hypertarget`` that this package relies on in LaTeX.
    """
    ref_id = str(self.idescape(node['refid']))
    self.body.append(r'\hyperlink{' + ref_id + '}{')


def depart_reference_node_latex(self: nodes.NodeVisitor, _: nodes.reference) -> None:
    """Depart the `inline_reference` node in the LaTeX builder."""
    self.body.append('}')


class RegisteredXRefRole(XRefRole):
    """
    A cross-referencing role that adds an entry to the domain registry.

    Functionally identical to the default `sphinx.roles.XRefRole`, but with the addition that it
    integrates with the domain defined in this package. This is necessary to support the
    `backlink` functionality.
    """
    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        """Creates a pending reference node and registers the data with the domain."""
        _, signature = self.text.replace('>', '').split('<')
        domain: InlineReferenceDomain = self.env.get_domain('iref')
        domain.add_loose_reference(self.env.docname, signature)
        return super().run()


class mutual_ref(nodes.General,
                 nodes.BackLinkable,
                 nodes.TextElement,
                 nodes.Targetable,
                 nodes.Inline):
    """
    Node representing a text target to a reference while being a reference itself back.

    In other words, this node is used to create two nodes with hyperlinks to each other. In effect
    a special case of the `backlink` node.
    """
    pass


def visit_mutual_ref_node_latex(self: nodes.NodeVisitor, node: mutual_ref) -> None:
    """
    Visits the `mutual_ref` node for the LaTeX builder.

    Creates a LaTeX hyperlink that also contains a hypertarget for each ``id`` that the `node`
    contains.
    """
    ref_id = str(self.idescape(node['refid']))
    self.body.append(r'\hyperlink{' + ref_id + r'}{')
    visit_reference_target_node_latex(self, node)


def depart_mutual_ref_node_latex(self: nodes.NodeVisitor, node: mutual_ref) -> None:
    """Departs the `mutual_ref` node for the LaTeX builder."""
    self.body.append(r'}')
    depart_reference_target_node_latex(self, node)


class MutualReferenceRole(SphinxRole):
    """
    Role for creating a mutual reference.

    In this context, a mutual reference is a set of two references which link to each other.
    """
    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        """Creates a `mutual_ref` node and registers with the domain."""
        text, signature = self.text.replace('>', '').split('<')
        domain: InlineReferenceDomain = self.env.get_domain('iref')
        anchor = domain.add_mutual_reference(signature)

        node = mutual_ref(text=text, refid=anchor, ids=[signature, anchor], title=text)

        return [node], []


class reference_target(nodes.TextElement, nodes.Targetable, nodes.Inline):
    """
    Node representing an arbitrary target for a reference.

    This node is turned into the text it contains while containing some of form of anchor that
    allows the reference-like nodes to create hyperlinks with this node as the target.
    """
    pass


def visit_reference_target_node_html(self: nodes.NodeVisitor, node: reference_target) -> None:
    """
    Visit `reference_target` node in the HTML writer.

    This method creates the ``a`` HTML tag that uses CSS such that the text does not appear like a
    hyperlink but like the surrounding text, but including the ``id`` property to allow the text to
    be hyperlinked to.
    """
    try:
        classes = node['classes']
        node['classes'] = []
    except KeyError:
        classes = []

    atts = {'style': 'color: inherit; text-decoration: inherit'}
    self.body.append(self.starttag(node, 'a', '', **atts))

    node['classes'] = classes


def depart_reference_target_node_html(self: nodes.NodeVisitor, _: reference_target) -> None:
    """Depart `reference_target` for HTML writer."""
    self.body.append('</a>')


def visit_reference_target_node_latex(self: nodes.NodeVisitor, node: reference_target) -> None:
    """
    Visit `reference_target`for LaTeX writer.

    Creates a ``\hypertarget`` value for each ``id`` in the `node`, with the text that appears in
    the document being the text in the node.
    """
    for id in node['ids']:
        self.body.append(r'\hypertarget{' + str(self.idescape(id)) + '}{')


def depart_reference_target_node_latex(self: nodes.NodeVisitor, node: reference_target) -> None:
    """Depart `reference_target` for LaTeX writer."""
    self.body.append('}' * len(node['ids']))


class backlink(nodes.TextElement, nodes.Targetable, nodes.Inline, nodes.BackLinkable):
    """
    Node that serves as an arbitrary target, while also containing hyperlinks to each hyperlink that
    links to it.

    This node should act like normal text when not linked to, like `mutual_ref` when linked to once,
    and similar to a citation when linked to multiple times.
    """
    pass


def visit_backlink_node_html(self: nodes.NodeVisitor, node: backlink) -> None:
    """
    Visit `backlink` for HTML writer.

    Creates the ``a`` HTML tag with the contents of the `node` and the ``id`` parameter set to the
    ``id`` of the `node`. If the `node` contains 0 backrefs or more than 1 backref, little is done
    in this method - only a normal text with ``id`` set is created. Instead, most of the work is
    performed in the `depart_backlink_node_html` method.
    """
    backrefs = node.get('backrefs', [])

    if len(backrefs) == 1:
        atts = {'href': backrefs[0], 'classes': ['reference', 'internal']}

        self.body.append(self.starttag(node, 'a', '', **atts))
    else:
        visit_reference_target_node_html(self, node)


def depart_backlink_node_html(self: nodes.NodeVisitor, node: backlink) -> None:
    """
    Depart `backlink` for HTML writer.

    If the `node` contains fewer than 2 backrefs, the ``a`` HTML tag is simply closed. Otherwise,
    a series of subscript numbers, each containing a link to one of the backrefs, is created.
    """
    backrefs = node.get('backrefs', [])

    if len(backrefs) > 1:
        elements = [f'<a href={ref}><sub>{i}</sub></a>' for i, ref in enumerate(backrefs)]
        self.body.append(','.join(elements))
    else:
        self.body.append('</a>')


def visit_backlink_node_latex(self: nodes.NodeVisitor, node: backlink) -> None:
    """
    Visit `backlink` for LaTeX writer.

    Similar to `visit_backlink_node_html`, if 0 or more than 1 backrefs exist in the `node`, simply
    a ``\hypertarget`` is created for each ``id``. Otherwise, the text itself is turned into a
    hyperlink and a hypertarget, similar to `visit_mutual_ref_node_latex`.
    """
    backrefs = node.get('backrefs', [])

    if len(backrefs) == 1:
        node['refid'] = backrefs[0].split('#', 1)[-1]
        visit_mutual_ref_node_latex(self, node)
    else:
        for id in node['ids']:
            self.body.append(r'\hypertarget{' + str(self.idescape(id)) + '}{')


def depart_backlink_node_latex(self: nodes.NodeVisitor, node: backlink) -> None:
    """
    Depart `backlink` for LaTeX writer.

    Similar to `depart_backlink_node_html` in that the LaTeX tag is simply closed for 0-1 backrefs,
    and for more, a list of subscript numbers hyperlinking to each hyperlink linking to the `node`,
    is created.
    """
    backrefs = node.get('backrefs', [])

    if len(backrefs) == 1:
        depart_mutual_ref_node_latex(self, node)
    else:
        self.body.append('}' * len(node['ids']))

        if len(backrefs) > 1:
            elements = []
            for i, ref in enumerate(backrefs):
                # resolve_backlinks prepends each backref with %docname# - we want to remove this
                ref_id = str(self.idescape(ref.split('#', 1)[-1]))
                elements.append(r'\hyperlink{' + ref_id + '}{' + str(i) + '}')

            self.body.append(r'\texorpdfstring{\textsubscript{' + ','.join(elements) + '}}{}')


class TargetRole(SphinxRole):
    """
    Base class for target roles, or roles specifically for being cross-linked to.

    Subclasses should only specify the two new attributes.

    Attributes
    ----------
    target_class
        The node class that the role instantiates.
    code
        The code to use for the anchor and signature in the domain.
    """
    target_class: nodes.Element = nodes.Element
    code: str = ''

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        """Creates a target node - node with ``id`` so that it can be linked to."""
        text, signature = self.text.replace('>', '').split('<')
        domain: InlineReferenceDomain = self.env.get_domain('iref')
        domain.add_reference_target(signature, self.code)

        node = self.target_class(text=text, refid=signature, ids=[signature], title=text)

        return [node], []


class ReferenceTargetRole(TargetRole):
    """Role for creating a target that looks like the text around it."""
    target_class = reference_target
    code = 'looseref'


class BackLinkRole(TargetRole):
    """Role for creating a target that includes a link to each link that links to the target."""
    target_class = backlink
    code = 'backlink'


class InlineReferenceDomain(Domain):
    name = 'iref'
    label = 'Inline Reference'
    roles = {
        'ref': RegisteredXRefRole(),
        'target': ReferenceTargetRole(),
        'backlink': BackLinkRole(),
        'mref': MutualReferenceRole(),
    }
    initial_data = {
        'targets': [],
        'mutual_refs': {},
        'loose_refs': {},
    }
    data_version = 0

    def resolve_xref(self,
                     env: BuildEnvironment,
                     fromdocname: str,
                     builder: Builder,
                     typ: str,
                     target: str,
                     node: pending_xref,
                     contnode: nodes.Element) -> id_reference | inline_reference | None:
        """
        Resolves a pending xref node.

        Creates a new node that will replace the pending xref `node`. This is done by matching the
        pending xref `node` to the appropriate ``target`` registered with the domain.

        Parameters
        ----------
        env
            The build environment.
        fromdocname
            The name of the document in which `node` is found.
        builder
            The sphinx builder being used.
        typ
            The name of the pending xref node.
        target
            The code/label used to identify the target of the pending xref `node`.
        node
            The pending xref node.
        contnode
            The node containing the contents of the pending xref `node`.

        Returns
        -------
        reference_node
            The reference node with the target set. None is returned when a match cannot be found.
        """
        match = [
            (sig, code, docname)
            for sig, code, docname in self.data['targets']
            if sig == target
        ]

        if len(match) == 0:
            warnings.warn(f'Reference "{target}" not found.', Warning)
            return None

        signature, match_type, todocname = match[-1]

        # Backlinks require the id param in order to be able to be linked back to
        if match_type == 'backlink':
            reference_node = make_refnode(builder, fromdocname, todocname, signature, contnode, signature, id_reference)

            for i, (from_doc, id, assigned) in enumerate(self.data['loose_refs'][signature]):
                if from_doc == fromdocname and not assigned:
                    break
            else:
                return reference_node

            try:
                reference_node['ids'].append(id)
            except KeyError:
                reference_node['ids'] = [id]

            self.data['loose_refs'][signature][i] = (from_doc, id, True)
        else:
            reference_node = make_refnode(builder, fromdocname, todocname, signature, contnode, signature, inline_reference)

        return reference_node

    def add_mutual_reference(self, signature: str) -> str:
        """
        Adds a mutual reference (`MutualReference`) to the domain and generates a unique ID for the
        node.

        Saves the original signature of the node, the name of the document in which the node was
        found, and the new unique ID, to the domain data for mutual references.

        The unique ID can be used do distinguish between the two `mutual_ref` nodes, since they are
        created using the same `signature`. This is an internal implementation detail required to
        make the hyperlinks work without placing undue effort on the users.

        Parameters
        ----------
        signature
            The signature of the node - the code/label used to identify the target for the reference

        Returns
        -------
        id
            The unique ID for the node.
        """
        id = f'{self.env.docname}-{signature}-id{self.env.new_serialno(signature)}'

        data = (signature, self.env.docname, id)

        try:
            self.data['mutual_refs'][signature].append(data)
        except KeyError:
            self.data['mutual_refs'][signature] = [data]

        return id

    def add_reference_target(self, signature: str, code: str) -> None:
        """
        Adds a target reference (`Target`) to the domain.

        Saves the signature of the node, the type of the target, and the document in which the node
        is found, to the domain data.

        Parameters
        ----------
        signature
            The signature of the node - the code/label used to identify the target for the reference
        code
            The name of the type of target, e.g. 'target' or 'backlink'.
        """
        self.data['targets'].append((signature, code, self.env.docname))

    def add_loose_reference(self, from_doc: str, target_signature: str) -> None:
        """
        Adds a `RegisteredXRefRole` to the domain.

        Saves the document in which the node is found and a unique ID to the domain data.

        Parameters
        ----------
        from_doc
            The name of the document in which the node is found.
        target_signature
            The signature of the target that the reference points to.
        """
        id = f'{target_signature}-ref{self.env.new_serialno()}'
        try:
            self.data['loose_refs'][target_signature].append((from_doc, id, False))
        except KeyError:
            self.data['loose_refs'][target_signature] = [(from_doc, id, False)]


def process_mutual_reference_nodes(app: Sphinx, doctree: document, fromdocname: str) -> None:
    """
    Processes all mutual reference nodes.

    Iterates over all `mutual_ref` nodes in the document and edits them so that they link to their
    corresponding paired nodes.

    Parameters
    ----------
    app
        Sphinx app.
    doctree
        The document tree.
    fromdocname
        The name of the document calling this function.
    """
    domain: InlineReferenceDomain = app.builder.env.get_domain('iref')

    for node in doctree.findall(mutual_ref):
        anchor = node['ids'].pop(0)

        mutual_nodes = domain.data['mutual_refs'][anchor]

        if len(mutual_nodes) > 2:
            warnings.warn(f'mutual reference "{anchor}" has more than two uses. This '
                          f'could be because it was used more than twice, or because of issues '
                          f'across multiple files.', Warning)
        elif len(mutual_nodes) < 2:
            warnings.warn(f'mutual reference "{anchor}" does not have a pair', Warning)
            continue

        if mutual_nodes[0][2] == node['ids'][0]:
            this_node, other_node = 0, 1
        elif mutual_nodes[1][2] == node['ids'][0]:
            this_node, other_node = 1, 0
        else:
            warnings.warn(f'mutual reference "{anchor}" is not mutually matching up: both '
                          f'{mutual_nodes[0][2]} and {mutual_nodes[0][2]} != {node["ids"][0]}',
                          Warning)
            continue

        from_doc, to_doc = mutual_nodes[this_node][1], mutual_nodes[other_node][1]
        node['refid'] = mutual_nodes[other_node][2]

        if from_doc != to_doc:
            node['refuri'] = app.builder.get_relative_uri(from_doc, to_doc)
            node['refuri'] += '#' + mutual_nodes[other_node][2]


def process_backlink_nodes(app: Sphinx, doctree: document, fromdocname: str) -> None:
    """
    Processes all backlink nodes.

    Iterates over all `backlink` nodes in the document and edits them so that they contain the
    backreferences to all nodes that link to them.

    Parameters
    ----------
    app
        Sphinx app.
    doctree
        The document tree.
    fromdocname
        The name of the document calling this function.
    """
    domain: InlineReferenceDomain = app.builder.env.get_domain('iref')

    for node in doctree.findall(backlink):
        try:
            backlinks = domain.data['loose_refs'][node['ids'][0]]
        except KeyError:
            # This backlink has no :iref:ref: pointing to it.
            continue

        for to_doc, ref_id, _ in backlinks:
            backref = app.builder.get_relative_uri(fromdocname, to_doc) + '#' + ref_id

            node.add_backref(backref)


def setup(app: Sphinx) -> ExtensionMetadata:
    """Plugs the extension into Sphinx."""
    app.add_domain(InlineReferenceDomain)

    app.add_node(inline_reference,
                 html=(visit_reference_node_default, depart_reference_node_default),
                 text=(visit_reference_node_default, depart_reference_node_default),
                 latex=(visit_reference_node_latex, depart_reference_node_latex))
    app.add_node(id_reference,
                 html=(visit_reference_node_default, depart_reference_node_default),
                 text=(visit_reference_node_default, depart_reference_node_default),
                 latex=(visit_mutual_ref_node_latex, depart_mutual_ref_node_latex))
    app.add_node(reference_target,
                 html=(visit_reference_target_node_html, depart_reference_target_node_html),
                 text=(visit_reference_node_default, depart_reference_node_default),
                 latex=(visit_reference_target_node_latex, depart_reference_target_node_latex))
    app.add_node(mutual_ref,
                 html=(visit_reference_node_default, depart_reference_node_default),
                 latex=(visit_mutual_ref_node_latex, depart_mutual_ref_node_latex),
                 text=(visit_reference_node_default, depart_reference_node_default))
    app.add_node(backlink,
                 html=(visit_backlink_node_html, depart_backlink_node_html),
                 text=(visit_reference_node_default, depart_reference_node_default),
                 latex=(visit_backlink_node_latex, depart_backlink_node_latex))

    app.connect('doctree-resolved', process_mutual_reference_nodes)
    app.connect('doctree-resolved', process_backlink_nodes)

    return {
        'version': '0.1',
        'parallel_read_safe': False,
        'parallel_write_safe': True,
    }
