"""ytdl2rss._ymd_to_rfc2822 unit tests."""

import pytest

from ytdl2rss import _ymd_to_rfc2822


@pytest.mark.parametrize(
    ('ymd', 'rfc2822'),
    [
        ('20120101', 'Sun, 01 Jan 2012 00:00:00 -0000'),
        ('20120310', 'Sat, 10 Mar 2012 00:00:00 -0000'),
        ('20120311', 'Sun, 11 Mar 2012 00:00:00 -0000'),
        ('20120312', 'Mon, 12 Mar 2012 00:00:00 -0000'),
        ('20121110', 'Sat, 10 Nov 2012 00:00:00 -0000'),
        ('20121111', 'Sun, 11 Nov 2012 00:00:00 -0000'),
        ('20121112', 'Mon, 12 Nov 2012 00:00:00 -0000'),
        ('20121231', 'Mon, 31 Dec 2012 00:00:00 -0000'),
    ],
)
def test_valid(ymd: str, rfc2822: str) -> None:
    assert _ymd_to_rfc2822(ymd) == rfc2822


@pytest.mark.parametrize(
    'ymd',
    [
        '',
        'a',
        '2012010',
        'a20120101',
        '20120101a',
        '20120101 a',
        ' 20120101',
        '20120101 ',
    ],
)
def test_raise_valueerror_for_invalid_ymd(ymd: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        _ymd_to_rfc2822(ymd)
