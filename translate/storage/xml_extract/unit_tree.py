#
# Copyright 2008-2010 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

from translate.storage import xliff


class XPathTree:
    def __init__(self, unit=None):
        self.unit = unit
        self.children = {}

    def __eq__(self, other):
        return (
            isinstance(other, XPathTree)
            and self.unit == other.unit
            and self.children == other.children
        )


def _split_xpath_component(xpath_component: str) -> tuple[str, int]:
    """
    Split an xpath component into a tag-index tuple.

    >>> split_xpath_component('{urn:oasis:names:tc:opendocument:xmlns:office:1.0}document-content[0]')
    ('{urn:oasis:names:tc:opendocument:xmlns:office:1.0}document-content', 0).
    """
    lbrac = xpath_component.rfind("[")
    rbrac = xpath_component.rfind("]")
    if lbrac == -1 or rbrac == -1:
        try:
            return "", int(xpath_component)
        except ValueError:
            return xpath_component, 0
    tag = xpath_component[:lbrac]
    index = int(xpath_component[lbrac + 1 : rbrac])
    return tag, index


def _split_xpath(xpath: str) -> list[tuple[str, int]]:
    """
    Split an 'xpath' string separated by / into a reversed list of its components.

    Thus:

    >>> split_xpath('document-content[1]/body[2]/text[3]/p[4]')
    [('p', 4), ('text', 3), ('body', 2), ('document-content', 1)]

    The list is reversed so that it can be used as a stack, where the top of the stack is
    the first component.
    """
    if xliff.ID_SEPARATOR in xpath:
        xpath = xpath.rsplit(xliff.ID_SEPARATOR, 1)[-1]
    components = xpath.split("/")
    components = [_split_xpath_component(component) for component in components]
    return list(reversed(components))


def _add_unit_to_tree(node, xpath_components, unit):
    """
    Walk down the tree rooted a node, and follow nodes which correspond to the
    components of xpath_components. When reaching the end of xpath_components,
    set the reference of the node to unit.

    With reference to the tree diagram in build_unit_tree::

      add_unit_to_tree(node, [('p', 2), ('text', 3), ('body', 2), ('document-content', 1)], unit)

    would begin by popping ('document-content', 1) from the path and
    following the node marked ``('document-content', 1)`` in the tree.
    Likewise, will descend down the nodes marked ``('body', 2)``
    and ``('text', 3)``.

    Since the node marked ``('text', 3)`` has no child node marked
    ``('p', 2)``, this node is created. Then the ``add_unit_to_tree``
    descends down this node. When this happens, there are no xpath
    components left to pop. Thus, ``node.unit = unit`` is executed.
    """
    if len(xpath_components) > 0:
        component = (
            xpath_components.pop()
        )  # pop the stack; is a component such as ('p', 4)
        # if the current node does not have any children indexed by
        # the current component, add such a child
        if component not in node.children:
            node.children[component] = XPathTree()
        _add_unit_to_tree(node.children[component], xpath_components, unit)
    else:
        node.unit = unit


def build_unit_tree(store, filename=None):
    """
    Enumerate a translation store and build a tree with XPath components as nodes
    and where a node contains a unit if a path from the root of the tree to the node
    containing the unit, is equal to the XPath of the unit.

    The tree looks something like this::

        root
           `- ('document-content', 1)
              `- ('body', 2)
                 |- ('text', 1)
                 |  `- ('p', 1)
                 |     `- <reference to a unit>
                 |- ('text', 2)
                 |  `- ('p', 1)
                 |     `- <reference to a unit>
                 `- ('text', 3)
                    `- ('p', 1)
                       `- <reference to a unit>
    """
    tree = XPathTree()
    is_xliff = isinstance(store, xliff.xlifffile)
    for unit in store.units:
        if unit.source and not unit.isfuzzy():
            locations = [unit.getid()] if is_xliff else unit.getlocations()
            if filename is not None and len(locations) > 1 and filename != locations[1]:
                # Skip units that don't come from the filename we are currently
                # trying to get units for.
                # This is not used for ODF, right now only for IDML.
                continue
            location = _split_xpath(locations[0])
            _add_unit_to_tree(tree, location, unit)
    return tree
