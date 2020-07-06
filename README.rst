========
ytdl2rss
========

.. image:: https://img.shields.io/travis/kevinoid/ytdl2rss/master.svg?style=flat&label=build+on+linux
   :alt: Build Status: Linux
   :target: https://travis-ci.org/kevinoid/ytdl2rss
.. image:: https://img.shields.io/appveyor/ci/kevinoid/ytdl2rss/master.svg?style=flat&label=build+on+windows
   :alt: Build Status: Windows
   :target: https://ci.appveyor.com/project/kevinoid/ytdl2rss
.. image:: https://img.shields.io/codecov/c/github/kevinoid/ytdl2rss.svg?style=flat
   :alt: Coverage
   :target: https://codecov.io/github/kevinoid/ytdl2rss?branch=master
.. image:: https://img.shields.io/david/kevinoid/ytdl2rss.svg?style=flat
   :alt: Dependency Status
   :target: https://david-dm.org/kevinoid/ytdl2rss
.. image:: https://img.shields.io/pypi/pyversions/ytdl2rss.svg?style=flat
   :alt: Python Versions
   :target: https://pypi.org/project/ytdl2rss/
.. image:: https://img.shields.io/pypi/v/ytdl2rss.svg?style=flat
   :alt: Version on PyPI
   :target: https://pypi.org/project/ytdl2rss/

Create podcast_ RSS_ of media downloaded from YouTube_, Vimeo_, Twitch_ or
any other site supported by youtube-dl_.


Introductory Example
====================

To create an audio podcast from videos in GoogleTechTalks_ `Make the Web
Faster`_ playlist:

.. code:: sh

   youtube-dl --write-info-json -f bestaudio https://www.youtube.com/playlist?list=PLE0E03DF19D90B5F4
   ytdl2rss *.info.json >podcast.rss


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

.. code:: crontab

   0 5 * * * cd path/to/podcast && youtube-dl --download-archive ytdl-archive.txt --write-info-json -f bestaudio https://www.youtube.com/playlist?list=PLE0E03DF19D90B5F4 && ytdl2rss *.info.json >|podcast.rss

Hosted Thumbnails
-----------------

Episode thumbnail images can be hosted alongside downloaded media, so
podcatchers will not download them from the original host, by using
``--write-thumbnail`` and modifying the ``.info.json`` files to use the
downloaded thumbnails:

.. code:: sh

   youtube-dl --write-info-json --write-thumbnail -f bestaudio https://www.youtube.com/playlist?list=PLE0E03DF19D90B5F4
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

.. === End of Sphinx index content ===


API Docs
========

To use this module as a library, see the generated `API Documentation`_.


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

This template is available under the terms of `CC0 1.0 Universal`_.

.. === Begin reference names ===

.. _API documentation: https://kevinoid.github.io/ytdl2rss/api
.. _CC0 1.0 Universal: https://creativecommons.org/publicdomain/zero/1.0/
.. _Podsync: https://github.com/mxpv/podsync
.. _RSS: https://en.wikipedia.org/wiki/RSS
.. _Twitch: https://www.twitch.tv/
.. _Vimeo: https://vimeo.com/
.. _YouCast: https://github.com/i3arnon/YouCast
.. _YouTube: https://www.youtube.com/
.. _contributing guidelines: CONTRIBUTING.rst
.. _cron: https://help.ubuntu.com/community/CronHowto
.. _pip: https://pip.pypa.io/
.. _podcast: https://en.wikipedia.org/wiki/Podcast
.. _this package: https://pypi.org/project/ytdl2rss/
.. _GoogleTechTalks: https://www.youtube.com/c/googletechtalks
.. _Make the Web Faster: https://www.youtube.com/playlist?list=PLE0E03DF19D90B5F4
.. _youtube-dl: https://ytdl-org.github.io/youtube-dl/
