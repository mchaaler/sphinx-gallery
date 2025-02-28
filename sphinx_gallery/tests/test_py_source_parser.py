# -*- coding: utf-8 -*-
r"""
Test source parser
==================


"""
# Author: Óscar Nájera
# License: 3-clause BSD

from __future__ import division, absolute_import, print_function

import os.path as op
import pytest
import textwrap
from sphinx.errors import ExtensionError
import sphinx_gallery.py_source_parser as sg


def test_get_docstring_and_rest(unicode_sample, tmpdir, monkeypatch):
    docstring, rest, lineno, _ = sg._get_docstring_and_rest(unicode_sample)
    assert u'Únicode' in docstring
    assert u'heiß' in rest
    # degenerate
    fname = op.join(str(tmpdir), 'temp')
    with open(fname, 'w') as fid:
        fid.write('print("hello")\n')
    with pytest.raises(ExtensionError, match='Could not find docstring'):
        sg._get_docstring_and_rest(fname)
    with open(fname, 'w') as fid:
        fid.write('print hello\n')
    assert sg._get_docstring_and_rest(fname)[0] == sg.SYNTAX_ERROR_DOCSTRING
    monkeypatch.setattr(sg, 'parse_source_file', lambda x: ('', None))
    with pytest.raises(ExtensionError, match='only supports modules'):
        sg._get_docstring_and_rest('')


@pytest.mark.parametrize('content, file_conf', [
    ("No config\nin here.",
     {}),
    ("# sphinx_gallery_line_numbers = True",
     {'line_numbers': True}),
    ("  #   sphinx_gallery_line_numbers   =   True   ",
     {'line_numbers': True}),
    ("#sphinx_gallery_line_numbers=True",
     {'line_numbers': True}),
    ("#sphinx_gallery_thumbnail_number\n=\n5",
     {'thumbnail_number': 5}),
    ("#sphinx_gallery_thumbnail_number=1foo",
     None),
    ("# sphinx_gallery_defer_figures",
     {}),
])
def test_extract_file_config(content, file_conf, log_collector):
    if file_conf is None:
        assert sg.extract_file_config(content) == {}
        assert len(log_collector.calls['warning']) == 1
        assert '1foo' == log_collector.calls['warning'][0].args[2]
    else:
        assert sg.extract_file_config(content) == file_conf
        assert len(log_collector.calls['warning']) == 0


@pytest.mark.parametrize('contents, result', [
    ("No config\nin here.",
     "No config\nin here."),
    ("# sphinx_gallery_line_numbers = True",
     ""),
    ("  #   sphinx_gallery_line_numbers   =   True   ",
     ""),
    ("#sphinx_gallery_line_numbers=True",
     ""),
    ("#sphinx_gallery_thumbnail_number\n=\n5",
     ""),
    ("a = 1\n# sphinx_gallery_line_numbers = True\nb = 1",
     "a = 1\nb = 1"),
    ("a = 1\n\n# sphinx_gallery_line_numbers = True\n\nb = 1",
     "a = 1\n\n\nb = 1"),
    ("# comment\n# sphinx_gallery_line_numbers = True\n# comment 2",
     "# comment\n# comment 2"),
    ("# sphinx_gallery_defer_figures",
     ""),
])
def test_remove_config_comments(contents, result):
    assert sg.remove_config_comments(contents) == result


def test_remove_ignore_comments():
    normal_code = "# Regular code\n# should\n# be untouched!"
    assert sg.remove_ignore_blocks(normal_code) == normal_code

    mismatched_code = "# sphinx_gallery_start_ignore"
    with pytest.raises(ExtensionError) as error:
        sg.remove_ignore_blocks(mismatched_code)
    assert "must have a matching" in str(error)

    code_with_ignores = textwrap.dedent("""\
    # Indented ignores should work
        # sphinx_gallery_start_ignore
        # The variable name should do nothing
        sphinx_gallery_end_ignore = 0
        # sphinx_gallery_end_ignore

    # New line above should stay intact
    # sphinx_gallery_start_ignore
    # sphinx_gallery_end_ignore
    # Empty ignore blocks are fine too
    """)
    assert sg.remove_ignore_blocks(code_with_ignores) == textwrap.dedent("""\
    # Indented ignores should work

    # New line above should stay intact
    # Empty ignore blocks are fine too
    """)
