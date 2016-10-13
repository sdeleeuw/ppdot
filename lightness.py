#!/usr/bin/python

from __future__ import unicode_literals
from __future__ import print_function

import argparse
import codecs
import struct

from colorsys import rgb_to_hls, hls_to_rgb


def process(in_hex, offset):

    # remove leading #
    in_hex = in_hex[1:] if in_hex[0] == '#' else in_hex

    # convert to rgb
    in_rgb = struct.unpack(b'BBB', codecs.decode(in_hex, 'hex'))
    print('  in_rgb: {}'.format(in_rgb))

    # convert to hls
    in_rgb = tuple(value / 255.0 for value in in_rgb)
    in_hls = rgb_to_hls(*in_rgb)
    print('  in_hls: {}'.format(in_hls))

    # add offset

    offset /= 255.0
    print('  offset: {}'.format(offset))

    if offset > 0:
        lightness = in_hls[1] + offset if in_hls[1] + offset <= 1 else 1
    else:
        lightness = in_hls[1] + offset if in_hls[1] + offset >= 0 else 0

    out_hls = (in_hls[0], lightness, in_hls[2])
    print(' out_hls: {}'.format(out_hls))

    # convert to rgb
    out_rgb = hls_to_rgb(*out_hls)
    out_rgb = tuple(int(value * 255.0) for value in out_rgb)
    print(' out_rgb: {}'.format(out_rgb))

    # convert to hex
    out_hex = codecs.encode(struct.pack(b'BBB', *out_rgb), 'hex')
    out_hex = codecs.decode(out_hex, 'latin-1')
    print(' out_hex: #{}'.format(out_hex))


# entry point

parser = argparse.ArgumentParser()
parser.add_argument('color')
parser.add_argument('offset', type=int)

script_args = parser.parse_args()

process(script_args.color, script_args.offset)
