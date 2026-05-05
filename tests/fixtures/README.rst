=====================
ytdl2rss Golden Files
=====================

This directory contains `golden files`_ with the expected RSS output for many
different youtube-dl info JSON files observed in the wild.  The files are
grouped into directories by the extractor used for convenience.  Each
``.info.json`` file is expected to have a corresponding ``.rss`` file
representing the expected output.

sdist
=====

Currently golden files are not distributed as part of the source distribution,
due to their size relative to the rest of the project, limited value for
installation testing, and potential issues with their uncontrolled content.
These files may be obtained from the project website and version control system.

.. _`golden files`: https://softwareengineering.stackexchange.com/a/358792
