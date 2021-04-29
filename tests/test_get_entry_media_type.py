"""ytdl2rss.get_entry_media_type unit tests."""

import pytest

from ytdl2rss import get_entry_media_type

entry_types = (
    ({'ext': '3g2', 'vcodec': 'none', 'acodec': 'mp4a.40.2'}, 'audio/3gpp2; codecs=mp4a.40.2'),
    ({'ext': '3g2', 'vcodec': 'avc1.64001F', 'acodec': 'mp4a.40.2'}, 'video/3gpp2; codecs="avc1.64001F, mp4a.40.2"'),

    ({'ext': '3gp', 'vcodec': 'none', 'acodec': 'mp4a.40.2'}, 'audio/3gpp; codecs=mp4a.40.2'),
    ({'ext': '3gp', 'vcodec': 'avc1.64001F', 'acodec': 'mp4a.40.2'}, 'video/3gpp; codecs="avc1.64001F, mp4a.40.2"'),

    ({'ext': 'avi', 'vcodec': 'mp1v', 'acodec': 'mpga'}, 'video/vnd.avi; codecs="mp1v, mpga"'),

    ({'ext': 'flv', 'vcodec': 'avc1.64001E', 'acodec': 'none'}, 'video/x-flv'),

    ({'ext': 'gif'}, 'image/gif'),
    # Produced by imgur
    ({'ext': 'gif', 'vcodec': 'gif'}, 'image/gif'),

    ({'ext': 'm4a', 'vcodec': 'none', 'acodec': 'none'}, 'audio/mp4'),
    ({'ext': 'm4a', 'vcodec': 'none', 'acodec': 'mp4a.40.2'}, 'audio/mp4; codecs=mp4a.40.2'),

    ({'ext': 'm4v', 'vcodec': 'none', 'acodec': 'none'}, 'video/mp4'),
    ({'ext': 'm4v', 'vcodec': 'avc1.4d400c', 'acodec': 'none'}, 'video/mp4; codecs=avc1.4d400c'),
    ({'ext': 'm4v', 'vcodec': 'avc1.4d400c', 'acodec': 'mp4a.40.2'}, 'video/mp4; codecs="avc1.4d400c, mp4a.40.2"'),

    ({'ext': 'mka', 'vcodec': 'none', 'acodec': 'none'}, 'audio/x-matroska'),
    ({'ext': 'mka', 'vcodec': 'none', 'acodec': 'mp4a.40.2'}, 'audio/x-matroska; codecs=mp4a.40.2'),

    ({'ext': 'mkv', 'vcodec': 'none', 'acodec': 'none'}, 'video/x-matroska'),
    ({'ext': 'mkv', 'vcodec': 'avc1.4d400c', 'acodec': 'none'}, 'video/x-matroska; codecs=avc1.4d400c'),
    ({'ext': 'mkv', 'vcodec': 'avc1.4d400c', 'acodec': 'mp4a.40.2'}, 'video/x-matroska; codecs="avc1.4d400c, mp4a.40.2"'),

    ({'ext': 'mp3'}, 'audio/mpeg'),

    # Produced by media.ccc.de:
    ({'ext': 'mp4', 'vcodec': 'h264'}, 'video/mp4; codecs=avc1'),
    # Produced by vimeo:
    ({'ext': 'mp4', 'vcodec': 'av01.0.01M.08.0.111.01.01.01.0', 'acodec': 'none'}, 'video/mp4; codecs=av01.0.01M.08.0.111.01.01.01.0'),

    # Produced by media.ccc.de:
    # Note: See discussion of audio/opus in get_entry_media_type()
    ({'ext': 'opus'}, 'audio/ogg; codecs=opus'),
    ({'ext': 'opus', 'acodec': 'opus'}, 'audio/ogg; codecs=opus'),

    # Note: ogg codecs values defined in Section 4 of RFC 5334
    # and https://wiki.xiph.org/index.php/MIMETypesCodecs
    ({'ext': 'ogg'}, 'audio/ogg'),
    ({'ext': 'ogg', 'acodec': 'vorbis'}, 'audio/ogg; codecs=vorbis'),
    # Note: Not observed in practice:
    ({'ext': 'ogg', 'vcodec': 'theora', 'acodec': 'vorbis'}, 'video/ogg; codecs="theora, vorbis"'),

    ({'ext': 'ogv'}, 'video/ogg'),
    # Note: Not observed in practice:
    ({'ext': 'ogv', 'vcodec': 'theora', 'acodec': 'vorbis'}, 'video/ogg; codecs="theora, vorbis"'),

    ({'ext': 'wav'}, 'audio/vnd.wave'),

    # Produced by media.ccc.de:
    ({'ext': 'webm', 'vcodec': None}, 'video/webm'),
    ({'ext': 'webm', 'vcodec': 'h264'}, 'video/webm; codecs=avc1'),
    ({'ext': 'webm', 'vcodec': 'none', 'acodec': 'opus'}, 'audio/webm; codecs=opus'),
    ({'ext': 'webm', 'vcodec': 'vp9', 'acodec': 'none'}, 'video/webm; codecs=vp9'),
)


def entry_type_to_id(entry_type):
    """Convert entry/type pair to a test ID."""
    entry = entry_type[0]
    return (entry['ext']
            + '_' + str(entry.get('vcodec'))
            + '_' + str(entry.get('acodec')))


@pytest.mark.parametrize(
    'entry,media_type',
    entry_types,
    ids=[entry_type_to_id(entry_type) for entry_type in entry_types])
def test_known(entry, media_type):
    assert get_entry_media_type(entry) == media_type


def test_avi_includes_unknown_vcodec():
    assert get_entry_media_type({
        'ext': 'avi',
        'vcodec': 'foo',
    }) == 'video/vnd.avi; codecs=foo'


def test_video_for_no_codec():
    """If neither vcodec nor acodec is known, use video type."""
    assert get_entry_media_type({'ext': 'mp4', 'vcodec': 'none', 'acodec': 'none'}) == 'video/mp4'
    assert get_entry_media_type({'ext': 'mp4', 'vcodec': None, 'acodec': None}) == 'video/mp4'
    assert get_entry_media_type({'ext': 'mp4'}) == 'video/mp4'
