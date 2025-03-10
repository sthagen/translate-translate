#
# Copyright 2007-2009 Zuza Software Foundation
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
Convert Windows RC files to Gettext PO localization files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/rc2po.html
for examples and usage instructions.
"""

import logging

from translate.storage import po, rc

logger = logging.getLogger(__name__)


class rc2po:
    """Convert a .rc file to a .po file for handling the translation."""

    def convert_store(self, input_store, duplicatestyle="msgctxt"):
        """Converts a .rc file to a .po file..."""
        output_store = po.pofile()
        output_header = output_store.init_headers(
            x_accelerator_marker="&",
            x_merge_on="location",
        )
        output_header.addnote(f"extracted from {input_store.filename}", "developer")
        for input_unit in input_store.units:
            output_unit = self.convert_unit(input_unit, "developer")
            if output_unit is not None:
                output_store.addunit(output_unit)
        output_store.removeduplicates(duplicatestyle)
        return output_store

    def merge_store(
        self, template_store, input_store, blankmsgstr=False, duplicatestyle="msgctxt"
    ):
        """Converts two .rc files to a .po file..."""
        output_store = po.pofile()
        output_header = output_store.init_headers(
            x_accelerator_marker="&",
            x_merge_on="location",
        )
        output_header.addnote(
            f"extracted from {template_store.filename}, {input_store.filename}",
            "developer",
        )
        input_store.makeindex()
        for template_unit in template_store.units:
            origpo = self.convert_unit(template_unit, "developer")
            # try and find a translation of the same name...
            template_unit_name = "".join(template_unit.getlocations())
            if template_unit_name in input_store.locationindex:
                translatedrc = input_store.locationindex[template_unit_name]
                translatedpo = self.convert_unit(translatedrc, "translator")
            else:
                translatedpo = None
            # if we have a valid po unit, get the translation and add it...
            if origpo is not None:
                if translatedpo is not None and not blankmsgstr:
                    origpo.target = translatedpo.source
                output_store.addunit(origpo)
            elif translatedpo is not None:
                logger.error(
                    "error converting original rc definition %s", template_unit.name
                )
        output_store.removeduplicates(duplicatestyle)
        return output_store

    @staticmethod
    def convert_unit(input_unit, commenttype):
        """
        Converts a .rc unit to a .po unit. Returns None if empty or not for
        translation.
        """
        if input_unit is None:
            return None
        # escape unicode
        output_unit = po.pounit(encoding="UTF-8")
        output_unit.addlocation("".join(input_unit.getlocations()))
        output_unit.source = input_unit.source
        output_unit.target = ""
        return output_unit


def convertrc(
    input_file,
    output_file,
    template_file,
    pot=False,
    duplicatestyle="msgctxt",
    charset=None,
    lang=None,
    sublang=None,
):
    """Reads in input_file using rc, converts using rc2po, writes to output_file."""
    input_store = rc.rcfile(input_file, lang, sublang, encoding=charset)
    convertor = rc2po()
    if template_file is None:
        output_store = convertor.convert_store(
            input_store, duplicatestyle=duplicatestyle
        )
    else:
        template_store = rc.rcfile(template_file, lang, sublang, encoding=charset)
        output_store = convertor.merge_store(
            template_store, input_store, blankmsgstr=pot, duplicatestyle=duplicatestyle
        )
    if output_store.isempty():
        return 0
    output_store.serialize(output_file)
    return 1


def main(argv=None):
    from translate.convert import convert

    formats = {
        "rc": ("po", convertrc),
        ("rc", "rc"): ("po", convertrc),
        "nls": ("po", convertrc),
        ("nls", "nls"): ("po", convertrc),
    }
    parser = convert.ConvertOptionParser(
        formats, usetemplates=True, usepots=True, description=__doc__
    )
    parser.add_option(
        "",
        "--charset",
        dest="charset",
        default="auto",
        help="charset to use to decode the RC files (autodetection is used by default)",
        metavar="CHARSET",
    )
    DEFAULTLANG = None
    parser.add_option(
        "-l",
        "--lang",
        dest="lang",
        default=DEFAULTLANG,
        help=f"LANG entry (default: {DEFAULTLANG})",
        metavar="LANG",
    )
    DEFAULTSUBLANG = None
    parser.add_option(
        "",
        "--sublang",
        dest="sublang",
        default=DEFAULTSUBLANG,
        help=f"SUBLANG entry (default: {DEFAULTSUBLANG})",
        metavar="SUBLANG",
    )
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.passthrough.append("charset")
    parser.passthrough.append("lang")
    parser.passthrough.append("sublang")
    parser.run(argv)


if __name__ == "__main__":
    main()
