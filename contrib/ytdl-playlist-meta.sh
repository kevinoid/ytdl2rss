#!/bin/sh
# Create playlist JSON from info JSON files with description and thumbnail from
# Open Graph Metadata <https://ogp.me/> and write to stdout.

set -Ceu

if [ $# -lt 2 ]; then
	echo "Usage: $0 <URL> <info.json file...>" >&2
	exit 1
fi

url=$1
shift

html=$(curl -fLsS "$url")

# FIXME: Need to HTML-decode values before use.
# In practice, they don't include encoded characters.

description=${html##*'<meta property="og:description" content="'}
if [ "$description" = "$html" ]; then
	echo 'Warning: <meta property="og:description"> not found.' >&2
	description=
else
	description=${description%%\"*}
fi

if [ -e channel.jpg ]; then
	image=channel.jpg
else
	image=${html##*'<meta property="og:image" content="'}
	if [ "$image" = "$html" ]; then
		echo 'Warning: <meta property="og:image"> not found.' >&2
		image=
	else
		image=${image%%\"*}
		curl -fLsS -o channel.jpg "$image"
		image=channel.jpg
	fi
fi

# shellcheck disable=2016
exec jq -s \
	--arg d "$description" \
	--arg t "$image" \
	--arg u "$url" \
	'{
  _type: "playlist",
  entries: .,
  id: .[0].playlist_id,
  title: .[0].playlist_title,
  uploader: .[0].playlist_uploader,
  uploader_id: .[0].playlist_uploader_id,
  webpage_url: $u,
  description: $d,
  thumbnail: $t
}' "$@"
