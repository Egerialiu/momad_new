#!/bin/bash
set -e
echo "Merging split .pkl files..."
for partsdir in $(find . -name '*.pkl.parts' -type d | sort); do
    orig=$(cat "$partsdir/original_filename.txt")
    echo "  $partsdir -> $orig"
    cat $(ls "$partsdir"/chunk_* | sort) > "$orig"
    expected=$(cat "$partsdir/checksum.md5")
    actual=$(md5sum "$orig" | awk '{print $1}')
    if [ "$expected" = "$actual" ]; then
        echo "    Checksum OK"
    else
        echo "    WARNING: Checksum mismatch!"
    fi
done
echo "Done."
