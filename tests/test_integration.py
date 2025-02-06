import glob
import os.path
import re
from pathlib import Path
import pytest

from sphinx.testing.path import path

pytest_plugins = ('sphinx.testing.fixtures',)


@pytest.fixture(scope='session')
def rootdir():
    return path(__file__).parent.abspath() / 'roots'


def clean_up(text: str) -> list[str]:
    text = text.split('\n')
    out = []
    for i, line in enumerate(text):
        line = line.replace('\n', '').strip()
        if line:
            if '(16505646556160)' in line:
                continue

            out.append(line)

    return out


def remove_edges_html(lines: list[str], start: str) -> list[str]:
    i = 0
    for i, line in enumerate(lines):
        if line == start:
            break

    j = -1
    for j, line in enumerate(reversed(lines)):
        if 'ENDOFFILE!!!!!!!!!!!!!!!!!' in line:
            break

    return lines[i:-j]


def remove_edges_latex(lines: str) -> list[str]:
    """
    Removes the top part of a latex document.

    Removes everything up to the first ``\begin{document}``. This is necessary because sphinx
    prints the date the document was created into the document itself. Furthermore, it should
    prevent upstream configuration changes from causing test failure (e.g. if sphinx changes which
    latex modules it imports). This should make the tests less flaky.

    Parameters
    ----------
    lines
        The latex document.

    Returns
    -------
    lines
        The latex document as a list of strings, without the header.
    """
    lines = lines.split('\n')
    i = 0
    for i, line in enumerate(lines):
        if line.strip() == r'\begin{document}':
            break

    return lines[i:]


@pytest.mark.sphinx("html", testroot="integration")
def test_integration_html(app, status):
    root_dir = path(__file__).parent.abspath()

    app.build()
    assert "build succeeded" in status.getvalue()  # Build succeeded

    result = clean_up((Path(app.srcdir) / "_build/html/test.html").read_text())
    expected = clean_up((root_dir / 'roots' / 'test-integration' / "expected.html").read_text())

    result_crosspage = clean_up((Path(app.srcdir) / "_build/html/test_crosspage.html").read_text())
    expected_crosspage = clean_up((root_dir / 'roots' / 'test-integration' / "expected_crosspage.html").read_text())

    start1 = '<section id="title-16505646556160">'
    start2 = '<section id="another-title-16505646556160">'

    result, expected = remove_edges_html(result, start1), remove_edges_html(expected, start1)
    result_crosspage, expected_crosspage = remove_edges_html(result_crosspage, start2), remove_edges_html(expected_crosspage, start2)

    assert expected != ''
    assert expected_crosspage != ''

    assert result == expected
    assert result_crosspage == expected_crosspage


@pytest.mark.sphinx("text", testroot="integration")
def test_integration_text(app, status):
    root_dir = path(__file__).parent.abspath()

    app.build()
    assert "build succeeded" in status.getvalue()  # Build succeeded

    result = (Path(app.srcdir) / "_build/text/test.txt").read_text()
    expected = (root_dir / 'roots' / 'test-integration' / "expected.txt").read_text()

    result_crosspage = (Path(app.srcdir) / "_build/text/test_crosspage.txt").read_text()
    expected_crosspage = (root_dir / 'roots' / 'test-integration' / "expected_crosspage.txt").read_text()

    assert result == expected
    assert result_crosspage == expected_crosspage


@pytest.mark.sphinx("latex", testroot="integration")
def test_integration_latex(app, status):
    root_dir = path(__file__).parent.abspath()

    app.build()
    assert "build succeeded" in status.getvalue()  # Build succeeded

    result = (Path(app.srcdir) / "_build/latex/inline_reference.tex").read_text()
    expected = (root_dir / 'roots' / 'test-integration' / "expected.tex").read_text()

    result, expected = remove_edges_latex(result), remove_edges_latex(expected)

    assert expected

    assert result == expected
