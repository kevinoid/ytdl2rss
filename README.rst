========
ytdl2rss
========

.. image:: https://img.shields.io/github/actions/workflow/status/kevinoid/ytdl2rss/Tox/main.svg?style=flat&label=build
   :alt: Build Status
   :target: https://github.com/kevinoid/ytdl2rss/actions/workflows/tox.yml?query=branch%3Amain
.. image:: https://img.shields.io/codecov/c/github/kevinoid/ytdl2rss.svg?style=flat
   :alt: Coverage
   :target: https://codecov.io/github/kevinoid/ytdl2rss?branch=main
.. image:: https://img.shields.io/librariesio/release/pypi/ytdl2rss.svg?style=flat
   :alt: Dependency Status
   :target: https://libraries.io/github/kevinoid/ytdl2rss
.. image:: https://readthedocs.org/projects/ytdl2rss/badge/?version=latest
   :target: https://ytdl2rss.readthedocs.io/en/latest/
   :alt: Documentation Status
.. image:: https://img.shields.io/pypi/pyversions/ytdl2rss.svg?style=flat
   :alt: Python Versions
   :target: https://pypi.org/project/ytdl2rss/
.. image:: https://img.shields.io/pypi/v/ytdl2rss.svg?style=flat
   :alt: Version on PyPI
   :target: https://pypi.org/project/ytdl2rss/

Create podcast_ RSS_ of media downloaded from YouTube_, Vimeo_, Twitch_ or
any other site supported by youtube-dl_ (or yt-dlc_, yt-dlp_, or other forks).


Introductory Example
====================

To create an audio podcast from videos in GoogleTechTalks_ `Make the Web
Faster`_ playlist:

.. code:: sh

   youtube-dl --write-info-json --no-clean-info-json -f bestaudio https://www.youtube.com/playlist?list=PLE0E03DF19D90B5F4
   ytdl2rss *.info.json >podcast.rss


Features
========

* Attempts to produce RSS which complies with guidelines from:
  * `Apple <https://help.apple.com/itc/podcasts_connect/#/itcb54353390>`_
  * `Spotify <https://podcasters.spotify.com/terms/Spotify_Podcast_Delivery_Specification_v1.6.pdf>`_
  * `W3C <https://validator.w3.org/feed/>`_


Installation
============

`This package`_ can be installed using pip_, by running:

.. code:: sh

   pip install ytdl2rss

Or by saving ytdl2rss.py as an executable file in ``$PATH``.


Recipes
=======

Periodic Updates
----------------

A podcast can be periodically updated by running ``youtube-dl`` and ``ytdl2rss``
from cron_.  Using ``--download-archive`` is recommended.  For example, to
update the introductory example daily at 5 a.m., the following can be added to
``crontab``:

.. code::

   0 5 * * * cd path/to/podcast && youtube-dl --download-archive ytdl-archive.txt --write-info-json --no-clean-info-json -f bestaudio https://www.youtube.com/playlist?list=PLE0E03DF19D90B5F4 && ytdl2rss *.info.json >|podcast.rss

Hosted Thumbnails
-----------------

Episode thumbnail images can be hosted alongside downloaded media, so
podcatchers will not download them from the original host, by using
``--write-thumbnail`` and modifying the ``.info.json`` files to use the
downloaded thumbnails:

.. code:: sh

   youtube-dl --write-info-json --no-clean-info-json --write-thumbnail -f bestaudio https://www.youtube.com/playlist?list=PLE0E03DF19D90B5F4
   for info in *.info.json; do
       jq --arg t "${info%.info.json}.webp" '.thumbnail = $t' "$info" >"$info.new"
       mv -f "$info.new" "$info"
   done
   ytdl2rss *.info.json >podcast.rss

See `<contrib/ytdl-thumbnails.sh>`_ for an example that includes conversion from
WebP to JPEG.

Podcast Metadata
----------------

In addition to JSON for individual videos, ``ytdl2rss`` accepts JSON for
playlists (produced by ``youtube-dl --print-json`` for channel/playlist/user
URLs).  This can be used to define a podcast metadata not currently saved by ``youtube-dl``, such as a description, thumbnail, and webpage URL.  To
combine info JSON into a playlist with custom metadata:

.. code:: sh

   jq -s \
       --arg desc "My awesome podcast." \
       --arg thumb "channel_thumbnail.jpg" \
       --arg url "http://example.com/podcast-home.html" \
       '{
     _type: "playlist",
     entries: .,
     # Copy playlist metadata from info for first video
     id: .[0].playlist_id,
     title: .[0].playlist_title,
     uploader: .[0].playlist_uploader,
     uploader_id: .[0].playlist_uploader_id,
     # Add custom playlist metadata
     webpage_url: $url,
     description: $desc,
     thumbnail: $thumb
   }' ./*.info.json | ytdl2rss - >|podcast.rss

See `<contrib/ytdl-playlist-meta.sh>`_ for an example which gets playlist
metadata from `Open Graph Metadata`_ in the playlist HTML.

.. === End of Sphinx index content ===


Documentation
=============

The `project documentation`_ is hosted on `Read the Docs`_.  See the `CLI
documentation`_ for command-line options and usage, and the `API documentation`_
for the Python API.


Contributing
============

Contributions are welcome and appreciated!  See the `contributing
guidelines`_ for recommendations.


Alternatives
============

If you are looking for an all-in-one podcast media download, conversion, and hosting tool, you may be interested in:

- Podsync_
- YouCast_


License
=======

This project is available under the terms of the `MIT License`_.
See the `summary at TLDRLegal`_

.. === Begin reference names ===

.. _API documentation: https://ytdl2rss.readthedocs.io/en/latest/api/modules.html
.. _CLI documentation: https://ytdl2rss.readthedocs.io/en/latest/cli.html
.. _MIT License: https://github.com/kevinoid/ytdl2rss/blob/main/LICENSE.txt
.. _Open Graph Metadata: https://ogp.me/
.. _Podsync: https://github.com/mxpv/podsync
.. _Read the Docs: https://readthedocs.org/
.. _RSS: https://en.wikipedia.org/wiki/RSS
.. _Twitch: https://www.twitch.tv/
.. _Vimeo: https://vimeo.com/
.. _YouCast: https://github.com/i3arnon/YouCast
.. _YouTube: https://www.youtube.com/
.. _contributing guidelines: https://github.com/kevinoid/ytdl2rss/blob/main/CONTRIBUTING.rst
.. _cron: https://help.ubuntu.com/community/CronHowto
.. _pip: https://pip.pypa.io/
.. _project documentation: https://ytdl2rss.readthedocs.io/
.. _podcast: https://en.wikipedia.org/wiki/Podcast
.. _summary at TLDRLegal: https://tldrlegal.com/license/mit-license
.. _this package: https://pypi.org/project/ytdl2rss/
.. _GoogleTechTalks: https://www.youtube.com/c/googletechtalks
.. _Make the Web Faster: https://www.youtube.com/playlist?list=PLE0E03DF19D90B5F4
.. _youtube-dl: https://ytdl-org.github.io/youtube-dl/
.. _yt-dlc: https://github.com/blackjack4494/yt-dlc
.. _yt-dlp: https://github.com/yt-dlp/yt-dlp
