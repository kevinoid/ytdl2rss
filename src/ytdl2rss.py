#!/usr/bin/env python3
"""Create podcast RSS from youtube-dl info JSON."""

import argparse
import codecs
import json
import os
import sys
import time
import traceback

from datetime import datetime
from email.utils import formatdate
from xml.sax.saxutils import escape, quoteattr  # nosec

__version__ = '0.1.0'

_VERSION_MESSAGE = (
    '%(prog)s '
    + __version__
    + '''

Copyright 2020 Kevin Locke <kevin@kevinlocke.name>

%(prog) is free and unencumbered software released into the public domain.

%(prog) is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the Unlicense for details.'''
)


def _ymd_to_rfc2822(datestr):
    """Convert a date in YYYYMMDD format to RFC 2822 for RSS."""
    tt = time.strptime(datestr, '%Y%m%d')
    ts = time.mktime(tt)
    # Convert to UTC so formatted date is midnight with -0000 (unknown) TZ.
    # https://stackoverflow.com/a/19238551
    offset = datetime.fromtimestamp(ts) - datetime.utcfromtimestamp(ts)
    return formatdate(ts + offset.total_seconds())


def get_entry_media_type(entry):
    """Get media type (i.e. MIME type) from youtube-dl JSON entry info."""
    ext = entry['ext']
    acodec = entry.get('acodec')
    if acodec == 'none':
        acodec = None
    vcodec = entry.get('vcodec')
    if vcodec == 'none':
        vcodec = None

    media_type = 'audio/' if not vcodec else 'video/'
    if ext == '3gp':
        media_type += '3gpp'    # FIXME: How to recognize 3gpp2?
    elif ext == 'avi':
        media_type = 'video/vnd.avi'
    elif ext in (
            'f4a',
            'f4b',
            'f4p',
            'f4v',
            'm4a',
            'm4b',
            'm4p',
            'm4r',
            'm4v',
    ):
        media_type += 'mp4'
    elif ext == 'flv':
        media_type = 'video/x-flv'
    elif ext in ('mk3d', 'mka', 'mks', 'mkv'):
        media_type += 'x-matroska'
    elif ext == 'mp3':
        media_type += 'mpeg'
    elif ext == 'ogv':
        media_type += 'ogg'
    elif ext == 'wav':
        media_type += 'vnd.wave'
    else:
        media_type += ext

    # Add codecs parameter from https://tools.ietf.org/html/rfc4281
    if (acodec or vcodec) and ext not in ('3gp', 'flv', 'mp3', 'opus'):
        media_type += '; codecs='
        if acodec and vcodec:
            media_type += '"' + vcodec + ', ' + acodec + '"'
        else:
            media_type += acodec or vcodec

    return media_type


def entry_to_rss(entry, rss, indent=None):
    """Convert youtube-dl entry info object to podcast RSS."""
    if indent is None:
        indent2 = ''
        indent3 = ''
        eol = ''
    else:
        indent2 = indent * 2
        indent3 = indent * 3
        eol = '\n'

    rss.write(indent2)
    rss.write('<item>')
    rss.write(eol)

    webpage_url = entry.get('webpage_url')
    if webpage_url:
        rss.write(indent3)
        rss.write('<guid isPermaLink="true">')
        rss.write(escape(webpage_url))
        rss.write('</guid>')
        rss.write(eol)
    else:
        rss.write(indent3)
        rss.write('<guid>')
        rss.write(escape(entry['id']))
        rss.write('</guid>')
        rss.write(eol)

    title = entry.get('title')
    if title is not None:
        rss.write(indent3)
        rss.write('<title>')
        rss.write(escape(title))
        rss.write('</title>')
        rss.write(eol)

    upload_date = entry.get('upload_date')
    if upload_date is not None:
        rss.write(indent3)
        rss.write('<pubDate>')
        rss.write(_ymd_to_rfc2822(upload_date))
        rss.write('</pubDate>')
        rss.write(eol)

    filesize = entry.get('filesize')
    media_type = get_entry_media_type(entry)
    rss.write(indent3)
    rss.write('<enclosure')
    if media_type is not None:
        rss.write(' type=')
        rss.write(quoteattr(media_type))
    if filesize is not None:
        rss.write(' length=')
        rss.write(quoteattr(str(filesize)))
    rss.write(' url=')
    rss.write(quoteattr(entry['_filename']))
    rss.write('/>')
    rss.write(eol)

    thumbnail = entry.get('thumbnail')
    if thumbnail is not None:
        rss.write(indent3)
        rss.write('<itunes:image href=')
        rss.write(quoteattr(thumbnail))
        rss.write('/>')
        rss.write(eol)

    duration = entry['duration']
    if duration is not None:
        rss.write(indent3)
        rss.write('<itunes:duration>')
        rss.write(str(duration))
        rss.write('</itunes:duration>')
        rss.write(eol)

    age_limit = entry.get('age_limit')
    if age_limit is not None:
        rss.write(indent3)
        rss.write('<itunes:explicit>')
        # Note: Spotify wants yes/no/clean for item, yes/clean for channel,
        # Google wants yes or absent, Apple wants true/false,
        # W3C Feed Validator wants yes/no/clean
        rss.write('yes' if age_limit > 0 else 'clean')
        rss.write('</itunes:explicit>')
        rss.write(eol)

    # TODO: <itunes:order> from autonumber (not in .info.json)
    # or playlist_index (may not be relevant/sequential for single file)
    # or sorted order?

    description = entry.get('description')
    if description is not None:
        rss.write(indent3)
        rss.write('<description>')
        rss.write(escape(description))
        rss.write('</description>')
        rss.write(eol)

    rss.write(indent2)
    rss.write('</item>')
    rss.write(eol)


def playlist_to_rss(playlist, rss, indent=None):
    """
    Convert youtube-dl playlist info object to podcast RSS.

    Playlist is expected to follow the schema defined in
    https://github.com/ytdl-org/youtube-dl/pull/21822
    Values which are null or missing will be omitted from RSS output where
    possible.

    Attempts to comply with guidelines from:
    https://help.apple.com/itc/podcasts_connect/#/itcb54353390
    https://support.google.com/podcast-publishers/answer/9476656
    https://podcasters.spotify.com/terms/Spotify_Podcast_Delivery_Specification_v1.6.pdf
    """
    if indent is None:
        indent1 = ''
        indent2 = ''
        eol = ''
    else:
        indent1 = indent
        indent2 = indent * 2
        eol = '\n'

    rss.write(
        '<rss version="2.0" '
        + 'xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"'
        + '>'
    )
    rss.write(eol)
    rss.write(indent1)
    rss.write('<channel>')
    rss.write(eol)

    title = playlist.get('title')
    if title is not None:
        rss.write(indent2)
        rss.write('<title>')
        rss.write(escape(title))
        rss.write('</title>')
        rss.write(eol)

    uploader = playlist.get('uploader')
    if uploader is not None:
        rss.write(indent2)
        rss.write('<itunes:author>')
        rss.write(escape(uploader))
        rss.write('</itunes:author>')
        rss.write(eol)

    webpage_url = playlist.get('webpage_url')
    if webpage_url is not None:
        rss.write(indent2)
        rss.write('<link>')
        rss.write(escape(webpage_url))
        rss.write('</link>')
        rss.write(eol)

    upload_date = playlist.get('upload_date')
    if upload_date is None:
        upload_date = max(
            entry.get('upload_date') for entry in playlist['entries'] if entry
        )
    if upload_date is not None:
        rss.write(indent2)
        rss.write('<pubDate>')
        rss.write(_ymd_to_rfc2822(upload_date))
        rss.write('</pubDate>')
        rss.write(eol)

    # TODO: Channel description
    # TODO: Channel image
    # https://github.com/ytdl-org/youtube-dl/issues/16130

    age_limits = [entry.get('age_limit') for entry in playlist['entries']]
    if age_limits and None not in age_limits:
        rss.write(indent2)
        rss.write('<itunes:explicit>')
        # Note: Spotify wants yes/no/clean for item, yes/clean for channel,
        # Google wants yes or absent, Apple wants true/false,
        # W3C Feed Validator wants yes/no/clean
        rss.write('yes' if max(age_limits) > 0 else 'clean')
        rss.write('</itunes:explicit>')
        rss.write(eol)

    rss.write(indent2)
    rss.write('<generator>')
    rss.write(escape(os.path.basename(__file__) + ' ' + __version__))
    rss.write('</generator>')
    rss.write(eol)

    for entry in playlist['entries']:
        entry_to_rss(entry, rss, indent=indent)

    rss.write(indent1)
    rss.write('</channel>')
    rss.write(eol)

    rss.write('</rss>\n')


def _load_json(json_path):
    """Load JSON from a file with a given path."""
    # Note: Binary so load can detect encoding (as in Section 3 of RFC 4627)
    with open(json_path, 'rb') as json_file:
        try:
            return json.load(json_file)
        except Exception as ex:
            if sys.version_info[0] >= 3:
                ex2 = Exception('Error loading ' + json_path)
                exec('raise ex2 from ex')   # nosec
            else:
                ex2 = Exception('Error loading ' + json_path + ': ' + str(ex))
                ex2.__cause__ = ex
                raise ex2


def entries_to_playlist(entries):
    """Combine youtube-dl entries into a playlist with common metadata."""
    # entry playlist metadata keys
    keys = {
        'playlist_id',
        'playlist_title',
        'playlist_uploader',
        'playlist_uploader_id',
    }

    # get playlist metadata, if same for all entries
    entries_playlist = None
    for entry in entries:
        entry_playlist = {k: v for k, v in entry.items() if v and k in keys}
        if entry_playlist:
            if entries_playlist is None:
                entries_playlist = entry_playlist
            elif entry_playlist != entries_playlist:
                # playlist metadata differs between entries
                entries_playlist = None
                break

    if entries_playlist:
        # Chop "playlist_" from entry playlist keys for use as playlist keys
        playlist = {k[9:]: v for k, v in entries_playlist.items()}
    else:
        playlist = {}
    playlist['_type'] = 'playlist'
    playlist['entries'] = entries
    return playlist


def _load_info(info_paths):
    """Load youtube-dl JSON info files into a single playlist object."""
    entries = []
    info_count = 0
    last_playlist = None
    for info_path in info_paths:
        info_count += 1

        if info_path == '-':
            info = json.load(sys.stdin)
        else:
            info = _load_json(info_path)

        info_entries = info.get('entries')
        has_entries = isinstance(info_entries, list)
        has_formats = isinstance(info.get('formats'), list)
        if has_entries == has_formats:
            raise ValueError('Unrecognized JSON in ' + info_path)
        if has_formats:
            # info for a single video
            entries.append(info)
        else:
            # info for a playlist
            last_playlist = info
            entries.extend(info_entries)

    # If the user provided a single playlist, use it as-is
    # This lets users easily specify whatever metadata they'd like
    if info_count == 1 and last_playlist:
        return last_playlist

    return entries_to_playlist(entries)


def _parse_args(args, namespace=None):
    """
    Parse command-line arguments.

    :param args: command-line arguments (usually :py:data:`sys.argv`)
    :param namespace: object to take the parsed attributes.

    :return: parsed arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        usage='%(prog)s [options] <JSON file...>',
        description=__doc__,
        # Use raw formatter to avoid mangling version text
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        help='Output version and license information',
        version=_VERSION_MESSAGE,
    )
    parser.add_argument(
        'json_files',
        nargs='+',
        metavar='JSON file...',
        help='youtube-dl .info.json files',
    )
    return parser.parse_args(args, namespace)


def main(*argv):
    """
    Entry point for command-line use.

    :param argv: command-line arguments (usually :py:data:`sys.argv`)

    :return: exit code
    :rtype: int
    """
    args = _parse_args(argv[1:])

    encoding = sys.stdout.encoding
    if encoding is not None:
        writer = sys.stdout
    else:
        # Note: Could use locale.getpreferredencoding().  Most users likely
        # "prefer" ISO-8859-1.  UTF-8 is a safer default to support more
        # characters and for wider podcast distributor/aggregator support.
        # (e.g. Apple instructs podcasters to use UTF-8.)
        encoding = 'UTF-8'
        writer = codecs.getwriter(encoding)(sys.stdout)

    indent = '  '

    writer.write('<?xml version="1.0" encoding=')
    writer.write(quoteattr(encoding))
    writer.write('?>')
    if indent is not None:
        writer.write('\n')

    try:
        playlist_to_rss(_load_info(args.json_files), writer, indent=indent)
    except UnicodeEncodeError:
        # FIXME: Should use a proper XML writer which would represent
        # characters outside the file encoding using XML entities.
        traceback.print_exc()
        sys.stderr.write(
            'Consider specifying a different encoding in PYTHONIOENCODING.\n'
        )
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv))
