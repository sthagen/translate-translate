#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of translate.
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
This module contains functions for identifying languages based on language
models.
"""

from os import extsep, path

from translate.lang.ngram import NGram
from translate.misc.file_discovery import get_abs_data_filename
from translate.storage.base import TranslationStore


class LanguageIdentifier:
    MODEL_DIR = get_abs_data_filename("langmodels")
    """The directory containing the ngram language model files."""
    CONF_FILE = "fpdb.conf"
    """
    The name of the file that contains language name-code pairs
    (relative to ``MODEL_DIR``).
    """

    def __init__(self, model_dir=None, conf_file=None):
        if model_dir is None:
            model_dir = self.MODEL_DIR
        if not path.isdir(model_dir):
            raise ValueError(f"Directory does not exist: {model_dir}")

        if conf_file is None:
            conf_file = self.CONF_FILE
        conf_file = path.abspath(path.join(model_dir, conf_file))
        if not path.isfile(conf_file):
            raise ValueError(f"File does not exist: {conf_file}")

        self._lang_codes = {}
        self._load_config(conf_file)
        self.ngram = NGram(model_dir)

    def _load_config(self, conf_file):
        """
        Load the mapping of language names to language codes as given in the
        configuration file.
        """
        with open(conf_file) as fp:
            for line in fp:
                parts = line.split()
                if not parts or line.startswith("#"):
                    continue  # Skip comment- and empty lines
                lname, lcode = parts[0], parts[1]

                # Make sure lname is not prefixed by directory names
                lname = path.split(lname)[-1]
                if extsep in lname:
                    lname = lname[: lname.rindex(extsep)]  # Remove extension if it has

                # Remove trailing '[_-]-utf8' from code
                lcode = lcode.removesuffix("-utf8")
                if lcode.endswith(("-", "_")):
                    lcode = lcode[:-1]

                self._lang_codes[lname] = lcode

    def identify_lang(self, text):
        """Identify the language of the text in the given string."""
        if not text:
            return None
        result = self.ngram.classify(text)
        if result in self._lang_codes:
            result = self._lang_codes[result]
        return result

    def identify_source_lang(self, instore):
        """
        Identify the source language of the given translation store or
        units.

        :type  instore: ``TranslationStore`` or list or tuple of
            ``TranslationUnit``s.
        :param instore: The translation store to extract source text from.
        :returns: The identified language's code or ``None`` if the language
            could not be identified.
        """
        if not isinstance(instore, (TranslationStore, list, tuple)):
            return None

        text = " ".join(
            unit.source
            for unit in instore[:50]
            if unit.istranslatable() and unit.source
        )
        if not text:
            return None
        return self.identify_lang(text)

    def identify_target_lang(self, instore):
        """
        Identify the target language of the given translation store or
        units.

        :type  instore: ``TranslationStore`` or list or tuple of
            ``TranslationUnit``s.
        :param instore: The translation store to extract target text from.
        :returns: The identified language's code or ``None`` if the language
            could not be identified.
        """
        if not isinstance(instore, (TranslationStore, list, tuple)):
            return None

        text = " ".join(
            unit.target
            for unit in instore[:200]
            if unit.istranslatable() and unit.target
        )
        if not text:
            return None
        return self.identify_lang(text)


if __name__ == "__main__":
    from sys import argv

    script_dir = path.abspath(path.dirname(argv[0]))
    identifier = LanguageIdentifier()
    with open(argv[1]) as fh:
        text = fh.read()
    print("Language detected:", identifier.identify_lang(text))  # noqa: T201
