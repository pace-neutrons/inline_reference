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
            if '<a class="headerlink" href="' in line and 'title="Link to this' in line:
                continue

            out.append(line)

    return out


def remove_edges(lines: list[str]) -> list[str]:
    i = 0
    for i, line in enumerate(lines):
        if line == '<section id="title">':
            break

    j = -1
    for j, line in enumerate(reversed(lines)):
        if 'ENDOFFILE!!!!!!!!!!!!!!!!!' in line:
            break

    return lines[i:-j]


@pytest.mark.sphinx("html", testroot="integration")
def test_integration_html(app, status):
    root_dir = path(__file__).parent.abspath()

    app.build()
    assert "build succeeded" in status.getvalue()  # Build succeeded

    result = clean_up((Path(app.srcdir) / "_build/html/test.html").read_text())
    expected = clean_up((root_dir / 'roots' / 'test-integration' / "expected.html").read_text())

    result_crosspage = clean_up((Path(app.srcdir) / "_build/html/test_crosspage.html").read_text())
    expected_crosspage = clean_up((root_dir / 'roots' / 'test-integration' / "expected_crosspage.html").read_text())

    assert remove_edges(result) == remove_edges(expected)
    assert remove_edges(result_crosspage) == remove_edges(expected_crosspage)


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
