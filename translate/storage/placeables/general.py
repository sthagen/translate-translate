#
# Copyright 2009-2010 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""
Contains general placeable implementations. That is placeables that does not
fit into any other sub-category.
"""

from __future__ import annotations

import re

from translate.storage.placeables.base import G, Ph, StringElem

__all__ = (
    "AltAttrPlaceable",
    "XMLEntityPlaceable",
    "XMLTagPlaceable",
    "parsers",
    "to_general_placeables",
)


def regex_parse(cls, pstr: str) -> list[StringElem]:
    """
    A parser method to extract placeables from a string based on a regular
    expression. Use this function as the ``@parse()`` method of a placeable
    class.
    """
    if cls.regex is None:
        return None
    matches = []
    oldend = 0
    for match in cls.regex.finditer(pstr):
        start, end = match.start(), match.end()
        if oldend != start:
            matches.append(StringElem(pstr[oldend:start]))
        matches.append(cls([pstr[start:end]]))
        oldend = end
    if oldend != len(pstr) and matches:
        matches.append(StringElem(pstr[oldend:]))
    return matches or None


class AltAttrPlaceable(G):
    """Placeable for the "alt=..." attributes inside XML tags."""

    regex = re.compile(r'alt=".*?"')
    parse = classmethod(regex_parse)


class NewlinePlaceable(Ph):
    """Placeable for new-lines."""

    iseditable = False
    isfragile = True
    istranslatable = False
    regex = re.compile(r"\r\n|\n|\r")
    parse = classmethod(regex_parse)


class NumberPlaceable(Ph):
    """Placeable for numbers."""

    istranslatable = False
    regex = re.compile(r"[-+]?[0-9]+([\u00a0.,][0-9]+)*")
    parse = classmethod(regex_parse)


class QtFormattingPlaceable(Ph):
    """
    Placeable representing a Qt string formatting variable.

    Implemented following Qt documentation on
    `QString::arg <http://doc.trolltech.com/4.5/qstring.html#arg>`_ where
    the placeables are refered to as 'place markers'

    Notes
    -----
      - Place markers can be reordered
      - Place markers may be repeated
      - 'L' use a localised representation e.g. in a number
      - %% some in the wild to escape real %, not documented (not in regex)

    """

    iseditable = False
    istranslatable = False
    regex = re.compile(
        r"""(?x)
                       %                 # Start of a place marker
                       L?                # The sequence is replaced with a localized representation (optional)
                       [1-9]\d{0,1}      # Place marker numbers must be in the range 1 to 99.
                       (?=([^\d]|$))     # Double check that we aren't matching %100+ (non consuming match)
                       """
    )
    parse = classmethod(regex_parse)


class PythonFormattingPlaceable(Ph):
    """
    Placeable representing a Python string formatting variable.

    Implemented following Python documentation on `String Formatting Operations
    <http://docs.python.org/library/stdtypes.html#string-formatting-operations>`_
    """

    iseditable = False
    istranslatable = False
    # Need to correctly define a python identifier.
    regex = re.compile(
        r"""(?x)
                       %                     # Start of formatting specifier
                       (%|                   # No argument converted %% creates a %
                       (\([^)]+\)){0,1}      # Mapping key value (optional)
                       [\-\+0\s\#]{0,1}      # Conversion flags (optional)
                       (\d+|\*){0,1}         # Minimum field width (optional)
                       (\.(\d+|\*)){0,1}     # Precision (optional)
                       [hlL]{0,1}            # Length modifier (optional)
                       [diouxXeEfFgGcrs]{1}) # Conversion type"""
    )
    parse = classmethod(regex_parse)


class JavaMessageFormatPlaceable(Ph):
    """
    Placeable representing a Java MessageFormat formatting variable.

    Implemented according to the Java `MessageFormat documentation
    <http://java.sun.com/j2se/1.4.2/docs/api/java/text/MessageFormat.html>`_.

    Information about custom formats:
      - number - `DecimalFormat <http://java.sun.com/j2se/1.4.2/docs/api/java/text/DecimalFormat.html>`_
      - date/time - `SimpleDateFormat <http://java.sun.com/j2se/1.4.2/docs/api/java/text/SimpleDateFormat.html>`_
      - choice - `ChoiceFormat <http://java.sun.com/j2se/1.4.2/docs/api/java/text/ChoiceFormat.html>`_
    """

    iseditable = False  # TODO: Technically incorrect as you need to change
    istranslatable = False
    # things in a choice entry
    regex = re.compile(
        r"""(?x)
      {                      # Start of MessageFormat
      [0-9]+                 # Number, positive array reference
      (,\s*                  # FormatType (optional) one of number,date,time,choice
        (number(,\s*(integer|currency|percent|[-0#.,E;%\u2030\u00a4']+)?)?|  # number FormatStyle (optional)
         (date|time)(,\s*(short|medium|long|full|.+?))?|                  # date/time FormatStyle (optional)
         choice,([^{]+({.+})?)+)?                                      # choice with format, format required
      )?                     # END: (optional) FormatType
      }                      # END: MessageFormat"""
    )
    parse = classmethod(regex_parse)


class FormattingPlaceable(Ph):
    """Placeable representing string formatting variables."""

    # For more information, see  man 3 printf
    # We probably don't want to support absolutely everything

    iseditable = False
    istranslatable = False
    regex = re.compile(
        r"""
        %                         # introduction
        (\d+\$)?                  # selection of non-next variable (reordering)
        [\-\+0 \#'I]?             # optional flag
        ((\d+)|[*])?              # field width
        (\.\d+)?                  # precision
        [hlI]?                    # length
        [cCdiouxXeEfgGnpsS]       # conversion specifier
        """,
        re.VERBOSE,
    )
    parse = classmethod(regex_parse)


class DoubleAtPlaceable(Ph):
    istranslatable = False
    iseditable = False
    # Matches placeholders that use two at symbols @@placeable@@.
    regex = re.compile(r"@@.*?@@", re.VERBOSE)
    parse = classmethod(regex_parse)


class BracePlaceable(Ph):
    istranslatable = False
    iseditable = False
    # Matches placeholders that use two braces {{placeable}} or one brace {placeable}.
    # The negative character groups with closing brace [^}] stop the regex from counting several placeholders
    # as one (e.g. '{open}something{closed}' should produce two distinct BracePlaceables '{open}' and '{closed}')
    regex = re.compile(r"{{[^}]*}}|{[^}]*}", re.VERBOSE)
    parse = classmethod(regex_parse)


class UrlPlaceable(Ph):
    """Placeable handling URI."""

    istranslatable = False
    regex = re.compile(
        r"""
    ((((news|nttp|file|https?|ftp|irc)://)       # has to start with a protocol
    |((www|ftp)[-A-Za-z0-9]*\.))                 # or www... or ftp... hostname
    ([-A-Za-z0-9]+(\.[-A-Za-z0-9]+)*)            # hostname
    |(\d{1,3}(\.\d{1,3}){3,3}))                  # or IP address
    (:[0-9]{1,5})?                               # optional port
    (/[-A-Za-z0-9_\$\.\+\!\*\(\),;:@&=\?/~\#\%]*)?     # optional trailing path
    (?=$|\s|([]'}>\),\"]))
    """,
        re.VERBOSE,
    )
    parse = classmethod(regex_parse)


class FilePlaceable(Ph):
    """Placeable handling file locations."""

    istranslatable = False
    regex = re.compile(r"(~/|/|\./)([-A-Za-z0-9_\$\.\+\!\*\(\),;:@&=\?/~\#\%]|\\){3,}")
    # TODO: Handle Windows drive letters. Some common Windows paths won't be
    # handled correctly while not allowing spaces, such as
    #     "C:\Documents and Settings"
    #     "C:\Program Files"
    parse = classmethod(regex_parse)


class EmailPlaceable(Ph):
    """Placeable handling emails."""

    istranslatable = False
    regex = re.compile(
        r"((mailto:)|)[A-Za-z0-9]+[-a-zA-Z0-9._%]*@(([-A-Za-z0-9]+)\.)+[a-zA-Z]{2,4}"
    )
    # TODO: What about internationalised domain names? ;-)
    parse = classmethod(regex_parse)


class PunctuationPlaceable(Ph):
    """Placeable handling punctuation."""

    iseditable = False
    istranslatable = False
    # FIXME this should really be a list created as being the inverse of what
    # is available on the translators keyboard.  Or easily expanded by their
    # configuration.
    regex = re.compile(
        r"""([™©®]|          # Marks
             [℃℉°]|          # Degree related
             [±πθ×÷−√∞∆Σ′″]| # Maths
             [‘’ʼ‚‛“”„‟]|    # Quote characters
             [«»]|           # Guillemets
             [£¥€]|          # Currencies
             …|              # U2026 - horizontal ellipsis
             —|              # U2014 - em dash
             –|              # U2013 - en dash
             [ ]             # U202F - narrow no-break space
            )+""",
        re.VERBOSE,
    )
    parse = classmethod(regex_parse)


class XMLEntityPlaceable(Ph):
    """Placeable handling XML entities (``&xxxxx;``-style entities)."""

    iseditable = False
    istranslatable = False
    regex = re.compile(
        r"""&(
        ([a-zA-Z][a-zA-Z0-9\.-]*)            #named entity
         |([#](\d{1,5}|x[a-fA-F0-9]{1,5})+)  #numeric entity
        );""",
        re.VERBOSE,
    )
    parse = classmethod(regex_parse)


class CapsPlaceable(Ph):
    """Placeable handling long all-caps strings."""

    iseditable = True
    regex = re.compile(r"\b[A-Z][A-Z_/\-:*0-9]{2,}\b[+]?")
    parse = classmethod(regex_parse)


class CamelCasePlaceable(Ph):
    """Placeable handling camel case strings."""

    iseditable = True
    regex = re.compile(
        r"""(?x)
            \b(
               [a-z]+[A-Z]|         #Not that strict if we start with lower (iPod)
               [A-Z]+[a-z]+[A-Z]|   #One capital at the start is not enough (OpenTran)
               [A-Z]{2,}[a-z]       #Two capitals at the start is enough (KBabel)
            )[a-zA-Z0-9]*           #Let's allow any final lower/upper/digit
            \b"""
    )
    parse = classmethod(regex_parse)


class SpacesPlaceable(Ph):
    """Placeable handling unusual spaces in strings."""

    iseditable = True
    istranslatable = False
    regex = re.compile(
        r"""(?m)  #Multiline expression
        [ ]{2,}|     #More than two consecutive
        ^[ ]+|       #At start of a line
        [ ]+$        #At end of line""",
        re.VERBOSE,
    )

    parse = classmethod(regex_parse)


class XMLTagPlaceable(Ph):
    """Placeable handling XML tags."""

    iseditable = True
    istranslatable = False
    regex = re.compile(
        r"""
        <                         # start of opening tag
        ([\w.:]+)                 # tag name, possibly namespaced
        (\s([\w.:]+=              # space and attribute name followed by =
            ((".*?")|('.*?'))     # attribute value, single or double quoted
        )?)*/?>                   # end of opening tag, possibly self closing
        |</([\w.]+)>              # or a closing tag
        """,
        re.VERBOSE,
    )
    parse = classmethod(regex_parse)


class OptionPlaceable(Ph):
    """Placeble handling command line options e.g. --help."""

    istranslatable = False
    regex = re.compile(
        r"""(?x)
                      \B(             # Empty string at the start of a non-word, ensures [space]-
                        -[a-zA-Z]|    # Single letter options: -i, -I
                        --[a-z\-]+    # Word options: --help
                      )\b"""
    )
    # regex = re.compile(r'''(-[a-zA-Z]|--[-a-z]+)\b''')
    parse = classmethod(regex_parse)


def to_general_placeables(
    tree,
    classmap={
        G: (AltAttrPlaceable,),
        Ph: (
            NumberPlaceable,
            XMLEntityPlaceable,
            XMLTagPlaceable,
            UrlPlaceable,
            FilePlaceable,
            EmailPlaceable,
            OptionPlaceable,
            PunctuationPlaceable,
        ),
    },
):
    if not isinstance(tree, StringElem):
        return tree

    newtree = None

    for baseclass, gclasslist in classmap.items():
        if isinstance(tree, baseclass):
            gclass = [c for c in gclasslist if c.parse(str(tree))]
            if gclass:
                newtree = gclass[0]()

    if newtree is None:
        newtree = tree.__class__()

    newtree.id = tree.id
    newtree.rid = tree.rid
    newtree.xid = tree.xid
    newtree.sub = []

    for subtree in tree.sub:
        newtree.sub.append(to_general_placeables(subtree))

    return newtree


# The order of these parsers are very important
parsers = [
    NewlinePlaceable.parse,
    XMLTagPlaceable.parse,
    AltAttrPlaceable.parse,
    XMLEntityPlaceable.parse,
    PythonFormattingPlaceable.parse,
    JavaMessageFormatPlaceable.parse,
    FormattingPlaceable.parse,
    # The Qt variables can consume the %1 in %1$s which will mask a printf
    # placeable, so it has to come later.
    QtFormattingPlaceable.parse,
    UrlPlaceable.parse,
    FilePlaceable.parse,
    EmailPlaceable.parse,
    CapsPlaceable.parse,
    CamelCasePlaceable.parse,
    OptionPlaceable.parse,
    PunctuationPlaceable.parse,
    NumberPlaceable.parse,
]
