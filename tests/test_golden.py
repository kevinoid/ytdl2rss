"""ytdl2rss test "golden" fixture files."""

import os

from collections.abc import Iterator
from io import StringIO
from pathlib import Path
from typing import Final, NoReturn

import pytest

from ytdl2rss import info_to_rss

INFO_EXT: Final[str] = '.info.json'
RSS_EXT: Final[str] = '.rss'
TEST_INDENT: Final[str] = '  '
TEST_SELF_URL: Final[str] = 'https://example.com/podcasts'


def _raise(ex: Exception) -> NoReturn:
    raise ex


def _get_golden_pairs(fixtures_path: Path) -> Iterator[tuple[Path, Path]]:
    """
    Generate pairs of file paths with info JSON input and RSS output.

    Recursively searches ``fixtures_path`` for ``.info.json`` and ``.rss`` file
    pairs, where ``.info.json`` is taken to be the input youtube-dl info JSON
    file and ``.rss`` the ytdl2rss output RSS file.

    :param fixtures_path: path to directory containing golden file pairs.

    :return: yields (info, rss) Path pairs.
    """
    for dirpath, _, files in os.walk(fixtures_path, onerror=_raise):
        dirpath_path = Path(dirpath)

        rss_files = {rss for rss in files if rss.endswith(RSS_EXT)}
        info_files = sorted(info for info in files if info.endswith(INFO_EXT))

        for info_file in info_files:
            rss_file = info_file[: -len(INFO_EXT)] + RSS_EXT
            info_path = dirpath_path / info_file
            rss_path = dirpath_path / rss_file
            try:
                rss_files.remove(rss_file)
            except KeyError:
                raise FileNotFoundError(
                    f'Missing output fixture {rss_path} for {info_path}'
                ) from None
            yield (info_path, rss_path)

        for rss_file in rss_files:
            info_file = rss_file[: -len(RSS_EXT)] + INFO_EXT
            info_path = dirpath_path / info_file
            rss_path = dirpath_path / rss_file
            raise FileNotFoundError(
                f'Missing input fixture {info_path} for {rss_path}'
            )


@pytest.mark.parametrize(
    ('info_path', 'rss_path'),
    _get_golden_pairs(Path(__file__).parent / 'fixtures'),
)
def test_golden(info_path: Path, rss_path: Path) -> None:
    rss_stringio = StringIO()
    info_to_rss(
        (str(info_path),),
        TEST_SELF_URL,
        str(rss_path),
        TEST_INDENT,
        write=rss_stringio.write,
    )
    assert rss_stringio.getvalue() == rss_path.read_text(encoding='UTF-8')
