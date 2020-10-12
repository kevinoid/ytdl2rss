#!/usr/bin/env python3
"""Create podcast RSS from youtube-dl info JSON."""

import argparse
import codecs
import io
import json
import os
import sys
import time
import traceback

from datetime import datetime
from email.utils import formatdate
from xml.sax.saxutils import escape, quoteattr  # nosec

try:
    from urllib.parse import urljoin, urlparse
    from urllib.request import pathname2url, url2pathname
except ImportError:
    from urllib import pathname2url, url2pathname
    from urlparse import urljoin, urlparse

__version__ = '0.1.0'

_JSON_PATH_KEY = object()
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


def _resolve_path(path, src_path, dst_path, dst_base):
    """Resolve a path in src_path to a URL in dst_path served at dst_base."""
    if not path:
        return path
    src_dir = os.path.dirname(src_path)
    cur_path = os.path.join(src_dir, path)
    dst_dir = os.path.dirname(dst_path)
    rel_path = os.path.relpath(cur_path, dst_dir)
    rel_url = pathname2url(rel_path)
    return urljoin(dst_base, rel_url)


def _resolve_url(url, src_path, dst_path, dst_base):
    """Resolve a URL in src_path to a URL in dst_path served at dst_base."""
    url_parts = urlparse(url)
    if url_parts.scheme:
        # url is absolute
        return url

    if url_parts.netloc:
        # url is scheme-relative
        return urljoin(dst_base, url)

    # Resolve url from containing file
    url_path = url2pathname(url)
    return _resolve_path(url_path, src_path, dst_path, dst_base)


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

    media_type = 'audio/' if acodec and not vcodec else 'video/'
    if ext == '3g2':
        media_type += '3gpp2'
    elif ext == '3gp':
        media_type += '3gpp'
    elif ext == 'avi':
        media_type = 'video/vnd.avi'
    elif ext in (
            'f4a',
            'f4b',
            'f4p',
            'm4a',
            'm4b',
            'm4p',
            'm4r',
    ):
        # These extensions are intended for audio.
        # If codecs are not known, assume it is audio.
        if not acodec and not vcodec:
            media_type = 'audio/mp4'
        else:
            media_type += 'mp4'
    elif ext in ('f4v', 'm4v'):
        media_type += 'mp4'
    elif ext == 'flv':
        media_type = 'video/x-flv'
    elif ext == 'gif':
        media_type = 'image/gif'
    elif ext in ('mk3d', 'mks', 'mkv'):
        media_type += 'x-matroska'
    elif ext == 'mka':
        # This extension is intended for audio.
        # If codecs are not known, assume it is audio.
        if not acodec and not vcodec:
            media_type = 'audio/'
        media_type += 'x-matroska'
    elif ext == 'mp3':
        media_type = 'audio/mpeg'
    elif ext == 'ogg':
        # Xiph recommends this extension for (vorbis) audio and ogv for video.
        # If video codec not known, assume it is audio.
        if not vcodec:
            media_type = 'audio/'
        media_type += 'ogg'
    elif ext == 'opus':
        # Note: ext: opus could be used to refer to "raw" audio/opus.
        # However, this has not been observed on ytdl-supported sites.
        # Since Xiph recommends .opus for Opus-in-Ogg
        # https://wiki.xiph.org/index.php/MIMETypesCodecs
        # and the ytdl extractor for media.ccc.de uses it this way,
        # unconditionally convert to ogg.
        # If uses of audio/opus are found, consider how to differentiate.
        ext = 'ogg'
        if acodec is None:
            acodec = 'opus'
        media_type = 'audio/ogg'
    elif ext == 'ogv':
        media_type += 'ogg'
    elif ext == 'wav':
        media_type = 'audio/vnd.wave'
    else:
        media_type += ext

    # Add codecs parameter from https://tools.ietf.org/html/rfc6381
    if (acodec or vcodec) and ext not in ('flv', 'gif', 'mp3'):
        # Note: Add space after ; as in RFC 6381 section 3.6 Examples
        media_type += '; codecs='
        if acodec and vcodec:
            # Note: Add space after , as in RFC 6381 section 3.6 Examples
            # TODO: Apply encoding from RFC 2231 if required, see examples
            # in RFC 6381 section 3.1
            media_type += '"' + vcodec + ', ' + acodec + '"'
        else:
            media_type += acodec or vcodec

    return media_type


def entry_to_rss(entry, rss, base=None, indent=None):
    """Convert youtube-dl entry info object to podcast RSS."""
    if indent is None:
        indent2 = ''
        indent3 = ''
        eol = ''
    else:
        indent2 = indent * 2
        indent3 = indent * 3
        eol = '\n'

    json_path = entry[_JSON_PATH_KEY]

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

    filename = entry['_filename']
    fileurl = _resolve_path(filename, json_path, rss.name, base)
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
    rss.write(quoteattr(fileurl))
    rss.write('/>')
    rss.write(eol)

    thumbnail = entry.get('thumbnail')
    if thumbnail is not None:
        thumbnail = _resolve_url(thumbnail, json_path, rss.name, base)
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


def playlist_to_rss(playlist, rss, base=None, indent=None):
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
    https://validator.w3.org/feed/
    """
    if indent is None:
        indent1 = ''
        indent2 = ''
        indent3 = ''
        eol = ''
    else:
        indent1 = indent
        indent2 = indent * 2
        indent3 = indent * 3
        eol = '\n'

    json_path = playlist.get(_JSON_PATH_KEY)

    rss.write(
        '<rss version="2.0"'
        + ' xmlns:atom="http://www.w3.org/2005/Atom"'
        + ' xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"'
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

    # Not produced by youtube-dl:
    description = playlist.get('description')
    if description is not None:
        rss.write(indent2)
        rss.write('<description>')
        rss.write(escape(description))
        rss.write('</description>')
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

    # Not produced by youtube-dl:
    # https://github.com/ytdl-org/youtube-dl/issues/16130
    thumbnail = playlist.get('thumbnail')
    if thumbnail is not None:
        thumbnail = _resolve_url(thumbnail, json_path, rss.name, base)
        rss.write(indent2)
        rss.write('<image>')
        rss.write(eol)

        rss.write(indent3)
        rss.write('<url>')
        rss.write(escape(thumbnail))
        rss.write('</url>')
        rss.write(eol)

        # "Note, in practice the image <title> and <link> should have the
        # same value as the channel's <title> and <link>."
        # https://www.rssboard.org/rss-specification#ltimagegtSubelementOfLtchannelgt
        if title is not None:
            rss.write(indent3)
            rss.write('<title>')
            rss.write(escape(title))
            rss.write('</title>')
            rss.write(eol)

        if webpage_url is not None:
            rss.write(indent3)
            rss.write('<link>')
            rss.write(escape(webpage_url))
            rss.write('</link>')
            rss.write(eol)

        rss.write(indent2)
        rss.write('</image>')
        rss.write(eol)

        # Apple instructs podcasters to use <itunes:image>, doesn't document
        # standardized <image>.  Include both.
        rss.write(indent2)
        rss.write('<itunes:image href=')
        rss.write(quoteattr(thumbnail))
        rss.write('/>')
        rss.write(eol)

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

    # Provide self link, as recommended
    # https://validator.w3.org/feed/docs/warning/MissingAtomSelfLink.html
    if base:
        rss.write(indent2)
        rss.write('<atom:link rel="self" type="application/rss+xml" href=')
        rss.write(quoteattr(base))
        rss.write('/>')
        rss.write(eol)

    rss.write(indent2)
    rss.write('<generator>')
    rss.write(escape(os.path.basename(__file__) + ' ' + __version__))
    rss.write('</generator>')
    rss.write(eol)

    for entry in playlist['entries']:
        entry_to_rss(entry, rss, base=base, indent=indent)

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
            info[_JSON_PATH_KEY] = info_path
            entries.append(info)
        else:
            # info for a playlist
            last_playlist = info
            info[_JSON_PATH_KEY] = info_path
            for entry in info_entries:
                entry[_JSON_PATH_KEY] = info_path
            entries.extend(info_entries)

    # If the user provided a single playlist, use it as-is
    # This lets users easily specify whatever metadata they'd like
    if info_count == 1 and last_playlist:
        return last_playlist

    return entries_to_playlist(entries)


def _parse_indent(indent):
    """Parse indent argument to indent string."""
    try:
        return ' ' * int(indent)
    except ValueError:
        return indent


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
    # Note: Match name of wget -B/--base option with similar purpose
    parser.add_argument(
        '-B',
        '--base',
        help='URL from which files will be served, to resolve relative URLs',
    )
    parser.add_argument(
        '-i',
        '--indent',
        help='XML indent string, or number of spaces to indent',
        nargs='?',
        type=_parse_indent,
    )
    parser.add_argument(
        '-o',
        '--output',
        help='Output RSS file.',
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

    if not args.base or not urlparse(args.base).scheme:
        # Note: Not just a spec compliance issue.  Affects real aggregators:
        # https://github.com/AntennaPod/AntennaPod/issues/2880
        sys.stderr.write(
            'Warning: URLs in RSS 2.0 must start with a URI scheme per:\n'
            '- https://www.rssboard.org/rss-specification#comments\n'
            '- https://cyber.harvard.edu/rss/rss.html#comments\n'
            'Use -B,--base to specify an absolute URL at which the RSS will '
            'be served.\n'
        )

    # Note: Could use default locale.getpreferredencoding().  Many users would
    # "prefer" ISO-8859-1.  UTF-8 is a safer default to support more characters
    # and for wider podcast distributor/aggregator support.
    # (e.g. Apple instructs podcasters to use UTF-8.)
    encoding = 'UTF-8'
    if args.output:
        writer = io.open(args.output, 'w', encoding=encoding)
    elif sys.stdout.isatty():
        # TTY unlikely to interpret XML declaration.  Use Python's encoding.
        if sys.stdout.encoding is not None:
            encoding = sys.stdout.encoding
            writer = sys.stdout
        else:
            import locale
            encoding = locale.getpreferredencoding()
            writer = codecs.getwriter(encoding)(sys.stdout)
    elif sys.stdout.encoding and sys.stdout.encoding.upper() == encoding:
        writer = sys.stdout
    elif hasattr(sys.stdout, 'buffer'):
        writer = codecs.getwriter(encoding)(sys.stdout.buffer)
    else:
        writer = codecs.getwriter(encoding)(sys.stdout)

    try:
        writer.write('<?xml version="1.0" encoding=')
        writer.write(quoteattr(encoding))
        writer.write('?>')
        if args.indent is not None:
            writer.write('\n')

        playlist_to_rss(
            _load_info(args.json_files),
            writer,
            base=args.base,
            indent=args.indent,
        )
    except UnicodeEncodeError:
        # FIXME: Should use a proper XML writer which would represent
        # characters outside the file encoding using XML entities.
        traceback.print_exc()
        sys.stderr.write(
            'Consider specifying a different encoding in PYTHONIOENCODING.\n'
        )
        return 1
    finally:
        if args.output:
            writer.close()

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv))
