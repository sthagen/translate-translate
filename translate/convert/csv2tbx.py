#
# Copyright 2006-2007 Zuza Software Foundation
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

"""
Convert Comma-Separated Value (.csv) files to a TermBase eXchange (.tbx)
glossary file.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/csv2tbx.html
for examples and usage instructions
"""

from translate.storage import csvl10n, tbx


class csv2tbx:
    """
    a class that takes translations from a .csv file and puts them in a .tbx
    file.
    """

    def __init__(self, charset=None):
        """Construct the converter..."""
        self.charset = charset

    def convertfile(self, csvfile):
        """
        Converts a csvfile to a tbxfile, and returns it. uses templatepo if
        given at construction.
        """
        mightbeheader = True
        self.tbxfile = tbx.tbxfile()
        for csvunit in csvfile.units:
            if mightbeheader:
                # ignore typical header strings...
                mightbeheader = False
                if csvunit.match_header():
                    continue
                if (
                    len(csvunit.location.strip()) == 0
                    and csvunit.source.find("Content-Type:") != -1
                ):
                    continue
            term = tbx.tbxunit.buildfromunit(csvunit)
            # TODO: we might want to get the location or other information
            # from CSV
            self.tbxfile.addunit(term)
        return self.tbxfile


def convertcsv(inputfile, outputfile, templatefile, charset=None, columnorder=None):
    """
    Reads in inputfile using csvl10n, converts using csv2tbx, writes to
    outputfile.
    """
    inputstore = csvl10n.csvfile(inputfile, fieldnames=columnorder)
    convertor = csv2tbx(charset=charset)
    outputstore = convertor.convertfile(inputstore)
    if len(outputstore.units) == 0:
        return 0
    outputstore.serialize(outputfile)
    return 1


def main():
    from translate.convert import convert

    formats = {
        ("csv", "tbx"): ("tbx", convertcsv),
        ("csv", None): ("tbx", convertcsv),
    }
    parser = convert.ConvertOptionParser(
        formats, usetemplates=False, description=__doc__
    )
    parser.add_option(
        "",
        "--charset",
        dest="charset",
        default=None,
        help="set charset to decode from csv files",
        metavar="CHARSET",
    )
    parser.add_option(
        "",
        "--columnorder",
        dest="columnorder",
        default=None,
        help="specify the order and position of columns (comment,source,target)",
    )
    parser.passthrough.append("charset")
    parser.passthrough.append("columnorder")
    parser.run()


if __name__ == "__main__":
    main()
