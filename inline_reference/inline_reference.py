from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING
import warnings

from docutils import nodes

from sphinx.application import Sphinx
from sphinx.domains import Domain, Index
from sphinx.roles import XRefRole
from sphinx.util.typing import ExtensionMetadata
from sphinx.util.docutils import SphinxRole
from sphinx.util.nodes import make_refnode


if TYPE_CHECKING:
    from sphinx.builders import Builder


class id_reference(nodes.reference):
    """A reference node that contains the ``ids`` parameter."""
    pass


def make_id_refnode(
    builder: Builder,
    fromdocname: str,
    todocname: str,
    targetid: str | None,
    child: nodes.Node | list[nodes.Node],
    title: str | None = None,
) -> nodes.reference:
    """Shortcut to create a id_reference node."""
    node = id_reference('', '', internal=True)
    if fromdocname == todocname and targetid:
        node['refid'] = targetid
    else:
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


class mutual_ref(nodes.General,
                 nodes.BackLinkable,
                 nodes.TextElement,
                 nodes.Targetable,
                 nodes.Inline):
    """Node representing a text target to a reference while being a reference itself back."""
    pass


def visit_mutual_ref_node_latex(self, node):
    """Visits the `mutual_ref` node for the LaTeX builder."""
    id = self.curfilestack[-1] + ':' + node['ids'][0]
    escaped_id = str(self.idescape(id))

    ref_id = str(self.idescape(self.curfilestack[-1] + ':' + node['refid']))
    self.body.append(r'\hyperlink{' + ref_id + r'}{\hypertarget{' + escaped_id + r'}{')


def depart_mutual_ref_node_latex(self, node):
    """Departs the `mutual_ref` node for the LaTeX builder."""
    self.body.append(r'}}')


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

        node = mutual_ref(text=text, ids=[anchor], title=text)

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
    self.body.append(self.hypertarget_to(node, False))


def depart_reference_target_node_latex(self, node):
    """Depart `reference_target` for LaTeX writer."""
    pass


class backlink(nodes.TextElement, nodes.Targetable, nodes.Inline, nodes.BackLinkable):
    """Node representing an arbitrary target for a reference."""
    pass


def visit_backlink_node_html(self, node):
    """Visit `backlink` for HTML writer."""
    backrefs = node.get('backrefs', [])

    if len(backrefs) == 1:
        atts = {'href': '#' + backrefs[0], 'classes': ['reference', 'internal']}

        self.body.append(self.starttag(node, 'a', '', **atts))
    else:
        visit_reference_target_node_html(self, node)


def depart_backlink_node_html(self, node):
    """Depart `backlink` for HTML writer."""
    backrefs = node.get('backrefs', [])

    if len(backrefs) == 1:
        self.body.append('</a>')
    elif len(backrefs) > 1:
        elements = [f'<a href=#{ref}><sub>{i}</sub></a>' for i, ref in enumerate(backrefs)]
        self.body.append(','.join(elements))


def visit_backlink_node_latex(self, node):
    """Visit `backlink` for LaTeX writer."""
    backrefs = node.get('backrefs', [])

    if len(backrefs) == 1:
        node['refid'] = backrefs[0]
        visit_mutual_ref_node_latex(self, node)
    else:
        id = str(self.idescape(self.curfilestack[-1] + ':' + node['ids'][0]))
        self.body.append(r'\hypertarget{' + id + '}{')


def depart_backlink_node_latex(self, node):
    """Depart `backlink` for LaTeX writer."""
    backrefs = node.get('backrefs', [])

    if len(backrefs) == 1:
        depart_mutual_ref_node_latex(self, node)
    else:
        elements = []
        for i, ref in enumerate(backrefs):
            ref_id = str(self.idescape(self.curfilestack[-1] + ':' + ref))
            elements.append(r'\hyperlink{' + ref_id + '}{' + str(i) + '}')

        self.body.append('}_{' + ','.join(elements) + '}')


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
        anchor = domain.add_reference_target(signature, self.code)

        node = self.target_class(text=text, refid=anchor, ids=[anchor], title=text)

        return [node], []


class ReferenceTarget(Target):
    """Role for creating a target that looks like the text around it."""
    target_class = reference_target
    code = 'looseref'


class BackLink(Target):
    """Role for creating a target that includes a link to each link that links to the target."""
    target_class = backlink
    code = 'backlink'


class LooseRefIndex(Index):
    """A custom index that creates an index of references."""
    name = 'looseref'
    localname = 'Loose Reference Index'
    shortname = 'looseref'

    def generate(self, docnames=None):
        content = defaultdict(list)

        # sort the list of code_blocks in alphabetical order
        code_blocks = self.domain.get_objects()
        code_blocks = sorted(code_blocks, key=lambda recipe: recipe[0])

        # generate the expected output, shown below, from the above using the
        # first letter of the recipe as a key to group thing
        #
        # name, subtype, docname, anchor, extra, qualifier, description
        for _name, dispname, typ, docname, anchor, _priority in code_blocks:
            content[dispname[0].lower()].append((
                dispname,
                0,
                docname,
                anchor,
                docname,
                '',
                typ,
            ))

        # convert the dict to the sorted list of tuples expected
        content = sorted(content.items())

        return content, True


class InlineReferenceDomain(Domain):
    name = 'iref'
    label = 'Inline Reference'
    roles = {
        'ref': XRefRole(),
        'target': ReferenceTarget(),
        'backlink': BackLink(),
        'mref': MutualReference(),
    }
    indices = {
        LooseRefIndex,
    }
    initial_data = {
        'loose_references': [],
    }
    data_version = 0

    def get_full_qualified_name(self, node):
        return f'iref.{node.arguments[0]}'

    def get_objects(self):
        yield from self.data['loose_references']

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        match = [
            (docname, anchor, typ2)
            for name, sig, typ2, docname, anchor, prio in self.get_objects()
            if sig == target and typ2 != 'mutual'
        ]

        if len(match) == 0:
            warnings.warn(f'Reference "{target}" not found.', Warning)
            return None

        todocname = match[-1][0]
        targ = match[-1][1]

        # Backlinks require the id param in order to be able to be linked back to
        if match[-1][2] == 'backlink':
            reference_node = make_id_refnode(builder, fromdocname, todocname, targ, contnode, targ)

            try:
                reference_node['ids'].append(targ + '-ref' + str(env.new_serialno()))
            except KeyError:
                reference_node['ids'] = [targ + '-ref' + str(env.new_serialno())]
        else:
            reference_node = make_refnode(builder, fromdocname, todocname, targ, contnode, targ)

        return reference_node

    def add_mutual_reference(self, signature: str) -> str:
        """Adds a mutual reference to the domain."""
        name = f'mutual.{signature}'
        anchor = f'mutual-{signature}'

        # name, dispname, type, docname, anchor, priority
        self.data['loose_references'].append((
            name,
            signature,
            'mutual',
            self.env.docname,
            anchor,
            0,
        ))

        return anchor

    def add_reference_target(self, signature: str, code: str) -> str:
        """Adds a target reference to the domain."""
        name = f'{code}.{signature}'
        anchor = f'{code}-{signature}'

        # name, dispname, type, docname, anchor, priority
        self.data['loose_references'].append((
            name,
            signature,
            code,
            self.env.docname,
            anchor,
            0,
        ))

        return anchor


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
    paired_nodes = {}
    for node in doctree.findall(mutual_ref):
        try:
            paired_nodes[node['ids'][0]].append(node)
        except KeyError:
            paired_nodes[node['ids'][0]] = [node]

    for name, pair in paired_nodes.items():
        if len(pair) > 2:
            warnings.warn(f'mutual reference "{pair[0]["ids"][0]}" has more than two uses. This '
                          f'could be because it was used more than twice, or because of issues '
                          f'across multiple files.', Warning)
        elif len(pair) < 2:
            warnings.warn(f'mutual reference "{pair[0]["ids"][0]}" does not have a pair', Warning)
            continue

        node1, node2 = pair[0], pair[1]

        node1['ids'][0] += '-1'
        node2['ids'][0] += '-2'

        node1['refid'] = node2['ids'][0]
        node2['refid'] = node1['ids'][0]

        node1.add_backref(node2['ids'][0])
        node2.add_backref(node1['ids'][0])


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
    backlinks = {}
    for node in doctree.findall(backlink):
        backlinks[node['ids'][0]] = node

    for ref_node in doctree.findall(id_reference):
        try:
            bln = backlinks[ref_node['refid']]
        except KeyError:
            try:
                bln = backlinks[ref_node['refuri'].split('#')[-1]]
            except KeyError:
                warnings.warn(f'Reference "{ref_node["refid"]}" does not point to a known node.',
                              Warning)
                continue

        bln.add_backref(ref_node['ids'][0])


def setup(app: Sphinx) -> ExtensionMetadata:
    """Plugs the extension into Sphinx."""
    app.add_domain(InlineReferenceDomain)

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
                 latex=(visit_reference_node_default, depart_reference_node_default),
                 text=(visit_reference_node_default, depart_reference_node_default))
    app.add_node(backlink,
                 html=(visit_backlink_node_html, depart_backlink_node_html),
                 text=(visit_reference_node_default, depart_reference_node_default),
                 latex=(visit_backlink_node_latex, depart_backlink_node_latex))

    app.connect('doctree-resolved', process_mutual_reference_nodes)
    app.connect('doctree-resolved', process_backlink_nodes)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
