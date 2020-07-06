#!/bin/sh
# Convert thumbnails downloaded with `youtube-dl --write-thumbnail` to JPEG
# and update .info.json files with the converted files.

set -Ceu

if [ $# -eq 0 ] || [ "$1" = --help ]; then
	echo "Usage: $0 <info.json file...>" >&2
	exit 1
fi

# Find convert from GraphicsMagick or ImageMagick
if command -v gm >/dev/null; then
	convert='gm convert'
elif command -v magick >/dev/null; then
	convert='magick convert'
else
	convert=convert
fi

# Convert WebP thumbnails to JPEG, for better podcatcher support
exit_code=0
for info; do
	base=${info%.info.json}
	if [ -e "$base.webp" ] && [ ! -e "$base.jpg" ]; then
		$convert "$base.webp" "$base.jpg"
	fi
	if [ -e "$base.jpg" ]; then
		jq --arg t "$base.jpg" '.thumbnail = $t' "$info" >"$info.new"
		mv -f "$info.new" "$info"
	else
		exit_code=1
		echo "Skipping $info: $base.{jpg,webp} not found." >&2
	fi
done

exit "$exit_code"
