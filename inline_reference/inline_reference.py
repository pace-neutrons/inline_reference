from __future__ import annotations

from typing import TYPE_CHECKING
import warnings

from docutils import nodes
from docutils.nodes import Node

from sphinx.application import Sphinx
from sphinx.domains import Domain
from sphinx.roles import XRefRole
from sphinx.util.typing import ExtensionMetadata
from sphinx.util.docutils import SphinxRole


if TYPE_CHECKING:
    from sphinx.builders import Builder


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
    """Shortcut to create a id_reference node."""
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


def visit_reference_node_default(self, node):
    """Visit the default reference node in any builder."""
    self.visit_reference(node)


def depart_reference_node_default(self, node):
    """Depart the default reference node in any builder."""
    self.depart_reference(node)


def visit_reference_node_latex(self, node):
    """Visit the `reference` node in the LaTeX builder."""
    ref_id = str(self.idescape(node['refid']))
    self.body.append(r'\hyperlink{' + ref_id + '}{')


def depart_reference_node_latex(self, node):
    """Depart the `reference` node in the LaTeX builder."""
    self.body.append('}')


class RegisteredXRefRole(XRefRole):
    def run(self) -> tuple[list[Node], list[nodes.system_message]]:
        _, signature = self.text.replace('>', '').split('<')
        domain: InlineReferenceDomain = self.env.get_domain('iref')
        domain.add_loose_reference(self.env.docname, signature)
        return super().run()


class mutual_ref(nodes.General,
                 nodes.BackLinkable,
                 nodes.TextElement,
                 nodes.Targetable,
                 nodes.Inline):
    """Node representing a text target to a reference while being a reference itself back."""
    pass


def visit_mutual_ref_node_latex(self, node):
    """Visits the `mutual_ref` node for the LaTeX builder."""
    escaped_id = str(self.idescape(node['ids'][0]))

    ref_id = str(self.idescape(node['refid']))
    self.body.append(r'\hyperlink{' + ref_id + r'}{')
    visit_reference_target_node_latex(self, node)


def depart_mutual_ref_node_latex(self, node):
    """Departs the `mutual_ref` node for the LaTeX builder."""
    self.body.append(r'}')
    depart_reference_target_node_latex(self, node)


class MutualReference(SphinxRole):
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
    """Node representing an arbitrary target for a reference."""
    pass


def visit_reference_target_node_html(self, node):
    """Visit `reference_target`."""
    try:
        classes = node['classes']
        node['classes'] = []
    except KeyError:
        classes = []

    atts = {'style': 'color: inherit; text-decoration: inherit'}
    self.body.append(self.starttag(node, 'a', '', **atts))

    node['classes'] = classes


def depart_reference_target_node_html(self, node):
    """Depart `reference_target` for HTML writer."""
    self.body.append('</a>')


def visit_reference_target_node_latex(self, node):
    """Visit `reference_target`for LaTeX writer."""
    for id in node['ids']:
        self.body.append(r'\hypertarget{' + str(self.idescape(id)) + '}{')


def depart_reference_target_node_latex(self, node):
    """Depart `reference_target` for LaTeX writer."""
    self.body.append('}' * len(node['ids']))


class backlink(nodes.TextElement, nodes.Targetable, nodes.Inline, nodes.BackLinkable):
    """Node representing an arbitrary target for a reference."""
    pass


def visit_backlink_node_html(self, node):
    """Visit `backlink` for HTML writer."""
    backrefs = node.get('backrefs', [])

    if len(backrefs) == 1:
        atts = {'href': backrefs[0], 'classes': ['reference', 'internal']}

        self.body.append(self.starttag(node, 'a', '', **atts))
    else:
        visit_reference_target_node_html(self, node)


def depart_backlink_node_html(self, node):
    """Depart `backlink` for HTML writer."""
    backrefs = node.get('backrefs', [])

    if len(backrefs) == 1:
        self.body.append('</a>')
    elif len(backrefs) > 1:
        elements = [f'<a href={ref}><sub>{i}</sub></a>' for i, ref in enumerate(backrefs)]
        self.body.append(','.join(elements))


def visit_backlink_node_latex(self, node):
    """Visit `backlink` for LaTeX writer."""
    backrefs = node.get('backrefs', [])

    if len(backrefs) == 1:
        node['refid'] = backrefs[0].split('#', 1)[-1]
        visit_mutual_ref_node_latex(self, node)
    else:
        for id in node['ids']:
            self.body.append(r'\hypertarget{' + str(self.idescape(id)) + '}{')


def depart_backlink_node_latex(self, node):
    """Depart `backlink` for LaTeX writer."""
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


class Target(SphinxRole):
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


class ReferenceTarget(Target):
    """Role for creating a target that looks like the text around it."""
    target_class = reference_target
    code = 'looseref'


class BackLink(Target):
    """Role for creating a target that includes a link to each link that links to the target."""
    target_class = backlink
    code = 'backlink'


class InlineReferenceDomain(Domain):
    name = 'iref'
    label = 'Inline Reference'
    roles = {
        'ref': RegisteredXRefRole(),
        'target': ReferenceTarget(),
        'backlink': BackLink(),
        'mref': MutualReference(),
    }
    initial_data = {
        'targets': [],
        'mutual_refs': {},
        'loose_refs': {},
    }
    data_version = 0

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
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
        """Adds a mutual reference to the domain."""
        id = f'{self.env.docname}-{signature}-id{self.env.new_serialno(signature)}'

        data = (signature, self.env.docname, id)

        try:
            self.data['mutual_refs'][signature].append(data)
        except KeyError:
            self.data['mutual_refs'][signature] = [data]

        return id

    def add_reference_target(self, signature: str, code: str) -> None:
        """Adds a target reference to the domain."""
        self.data['targets'].append((signature, code, self.env.docname))

    def add_loose_reference(self, from_doc: str, target_signature: str) -> None:
        """Adds a `RegisteredXRefRole` to the domain."""
        id = f'{target_signature}-ref{self.env.new_serialno()}'
        try:
            self.data['loose_refs'][target_signature].append((from_doc, id, False))
        except KeyError:
            self.data['loose_refs'][target_signature] = [(from_doc, id, False)]


def process_mutual_reference_nodes(app: Sphinx, doctree, fromdocname) -> None:
    """
    Processes all mutual reference nodes.

    Iterates over all `mutual_ref` nodes and edits them so that they link to each other.

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


def process_backlink_nodes(app: Sphinx, doctree, fromdocname) -> None:
    """
    Processes all backlink nodes.

    Iterates over all `backlink` nodes and edits them so that they contain the backreferences
    to the nodes that link to them.

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
