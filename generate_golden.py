#!/usr/bin/env python3
"""Script to generate RSS "golden files" from youtube-dl info JSON files."""

import logging
import os
import sys

from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

# Add src to sys.path so ytdl2rss can be imported
_project_path = Path(__file__).resolve().parent
sys.path.insert(0, str(_project_path / 'src'))

# pylint: disable-next=wrong-import-position
from tests.test_golden import (  # noqa: E402
    INFO_EXT,
    RSS_EXT,
    TEST_INDENT,
    TEST_SELF_URL,
)

# pylint: disable-next=wrong-import-position
from ytdl2rss import info_to_rss  # noqa: E402

_logger = logging.getLogger(__name__)


def _raise(ex: Exception) -> NoReturn:
    raise ex


def generate_test_fixture(info_path: Path) -> None:
    """
    Generate an RSS file for a given info JSON file.

    :param info_path: path info JSON file.
    """
    info_file = info_path.name
    rss_file = info_file[: -len(INFO_EXT)] + RSS_EXT
    rss_path = info_path.parent / rss_file

    _logger.info('Generating %s from %s...', rss_path, info_path)

    # pylint: disable-next=duplicate-code
    info_to_rss(
        (str(info_path),),
        TEST_SELF_URL,
        str(rss_path),
        TEST_INDENT,
    )


def generate_test_fixtures(fixtures_path: Path) -> None:
    """
    Generate RSS files for each info JSON file in ``fixtures_path``.

    :param fixtures_path: path to directory containing golden file pairs.
    """
    for dirpath, _, files in os.walk(fixtures_path, onerror=_raise):
        dirpath_path = Path(dirpath)
        for file in files:
            if file.endswith(INFO_EXT):
                generate_test_fixture(dirpath_path / file)


def main(argv: Sequence[str] = sys.argv) -> int:
    """
    Entry point for generate-test-fixtures.

    :param argv: command-line arguments

    :return: exit code
    """
    if len(sys.argv) < 2:  # noqa: PLR2004
        fixtures_path = Path(__file__).parent / 'tests/fixtures'
    elif len(sys.argv) == 2:  # noqa: PLR2004
        fixtures_path = Path(sys.argv[1])
    else:
        script_name = Path(argv[0]).name
        sys.stderr.write(
            f'Error: Expected at most 1 argument.  Got {len(sys.argv) - 1}.\n'
            f'Usage: {script_name} [fixtures_dir]\n'
        )
        return 1

    logging.basicConfig(level=logging.INFO)

    _logger.info('Generating golden files in %s...', fixtures_path)
    generate_test_fixtures(fixtures_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
