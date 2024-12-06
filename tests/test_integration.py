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


def mask_random_ids(lines: list[str]) -> list[str]:
    num = 1
    map = {}
    for i, line in enumerate(lines):
        regex = r'(?:\blooseref\b|\bbacklink\b|\bmutual\b)-[bm]?id[0-9]+-([0-9]+)"'
        found = re.findall(r'id="' + regex, line)
        found.extend(re.findall(r'href="?#' + regex + '?', line))

        for match in found:
            try:
                n = map[match]
            except KeyError:
                map[match] = num
                n = num
                num += 1

            line = line.replace(match, str(n))

        lines[i] = line

    return lines


@pytest.mark.sphinx("html", testroot="integration")
def test_integration(app, status):
    root_dir = path(__file__).parent.abspath()

    app.build()
    assert "build succeeded" in status.getvalue()  # Build succeeded

    result = clean_up((Path(app.srcdir) / "_build/html/test.html").read_text())
    expected = clean_up((root_dir / 'roots' / 'test-integration' / "expected.html").read_text())

    assert mask_random_ids(remove_edges(result)) == mask_random_ids(remove_edges(expected))
