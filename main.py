#!/usr/bin/env python3
"""Entrypoint for the news-image-20261122 front page (THE SUNDAY GLOBE).

Writes the bundled front-page image to the output directory as
entry.png. The output is byte-identical to the bundled image on every
run, and the program refuses to write anything that is not a complete
JPEG inside the competition's size limits.

The image itself was drawn in the build session with PIL (draw.py,
kept outside this repository); this entrypoint uses only the standard
library, as the sandbox provides nothing else.
"""
import hashlib
import os
import shutil
import struct
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BUNDLED = os.path.join(BASE, "entry.png")
BYTE_LIMIT = 1_048_576
SIDE_LIMIT = 1024


def read_jpeg_size(blob):
    """Return (width, height) from a JPEG byte string, or None.

    Walks the marker segments from the SOI marker until the first
    Start-Of-Frame marker, which carries the dimensions.
    """
    if len(blob) < 4 or blob[0:2] != b"\xff\xd8":
        return None
    pos = 2
    while pos + 9 <= len(blob):
        if blob[pos] != 0xFF:
            return None
        kind = blob[pos + 1]
        if kind in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", blob[pos + 5:pos + 9])
            return width, height
        if kind == 0xDA:
            # Start of scan: compressed data follows, no more markers to read.
            return None
        if kind in (0xD8, 0x01) or 0xD0 <= kind <= 0xD9:
            pos += 2
            continue
        seg_len = struct.unpack(">H", blob[pos + 2:pos + 4])[0]
        pos += 2 + seg_len
    return None


def check_image(blob):
    """Raise unless blob is a complete JPEG within the size limits."""
    if len(blob) < 4:
        raise SystemExit("image too short to be a JPEG")
    if len(blob) > BYTE_LIMIT:
        raise SystemExit(f"image too large: {len(blob)} bytes")
    if blob[-2:] != b"\xff\xd9":
        raise SystemExit("image is not a complete JPEG (no EOI marker)")
    size = read_jpeg_size(blob)
    if size is None:
        raise SystemExit("cannot read JPEG dimensions")
    width, height = size
    if width > SIDE_LIMIT or height > SIDE_LIMIT:
        raise SystemExit(f"image too big: {width}x{height}")
    return width, height


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(BUNDLED, "rb") as fh:
        blob = fh.read()
    width, height = check_image(blob)
    target = os.path.join(out_dir, "entry.png")
    shutil.copyfile(BUNDLED, target)
    with open(target, "rb") as fh:
        written = fh.read()
    if written != blob:
        raise SystemExit("output differs from bundled image")
    digest = hashlib.sha256(written).hexdigest()
    print(f"entry.png: {width}x{height}, {len(written)} bytes, sha256 {digest}")


if __name__ == "__main__":
    main()
