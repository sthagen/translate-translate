#
# Copyright 2004-2014 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.

"""
Convert OpenDocument (ODF) files to XLIFF localization files.

See: https://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/odf2xliff.html
for examples and usage instructions.
"""

from io import BytesIO

from translate.convert import convert
from translate.storage import factory, xliff
from translate.storage.odf_io import open_odf
from translate.storage.odf_shared import (
    ODF_INPUT_EXTENSIONS,
    inline_elements,
    no_translate_content_elements,
)
from translate.storage.xml_extract.extract import ParseState, build_store


def convertodf(inputfile, outputfile, templates) -> bool:
    """Convert an ODF package to XLIFF."""
    store = factory.getobject(outputfile)
    if not isinstance(store, xliff.xlifffile):
        raise TypeError("ODF extraction requires an XLIFF 1.x output store")

    contents = open_odf(inputfile)
    for filename, data in contents.items():
        store.switchfile(filename, createifmissing=True)
        parse_state = ParseState(no_translate_content_elements, inline_elements)
        build_store(BytesIO(data), store, parse_state, collect_ids=False)

    store.removedefaultfile()
    store.save()
    return True


def main(argv=None) -> None:
    formats = tuple(
        (extension, (output_extension, convertodf))
        for output_extension in ("xlf", "xliff")
        for extension in ODF_INPUT_EXTENSIONS
    )
    parser = convert.ConvertOptionParser(formats, description=__doc__)
    parser.run(argv)


if __name__ == "__main__":
    main()
