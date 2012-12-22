#!/usr/bin/env python2
"""
Analyze superblock in ext2 filesystem.

Usage:
    superblock.py <filename>
"""
import sys
import string
from binascii import hexlify
from datetime import datetime

BLOCKSIZE = 512


def dump(filename):

    def nonprintable_replace(char):
        if char not in string.printable:
            return '.'
        if char in '\n\r\t\x0b\x0c':
            return '.'
        return char

    with open(filename, 'rb') as f:
        f.seek(2 * BLOCKSIZE)
        for i in xrange(BLOCKSIZE / 16):
            word = f.read(4), f.read(4), f.read(4), f.read(4)
            hex_string = ' '.join(map(hexlify, word))
            ascii_string = ''.join(map(nonprintable_replace, ''.join(word)))
            print '{0:2}:  {1}  {2}'.format(i + 1, hex_string, ascii_string)


def analyze(filename):

    # Binary conversion functions

    def lsb2hex(b_string):
        """Take a binary string (from ``file.read()``) and convert it into a
        hex string by assuming 2 byte little endian byte order."""
        msb_string = hexlify(b_string)
        lsb_string = ''.join([msb_string[x:x + 2] for x in range(0, len(msb_string), 2)][::-1])
        return lsb_string

    def lsb2ascii(b_string):
        """Take a msb hex string and convert it to an ascii string."""
        msb_string = hexlify(b_string)
        pairs = (msb_string[x:x + 2] for x in range(0, len(msb_string), 2))
        values = (int(x, 16) for x in pairs)
        return ''.join(map(chr, values))

    def lsb2int(b_string):
        """Take a binary string (from ``file.read()``) and convert it into a
        integer by assuming 2 byte little endian byte order."""
        lsb_string = lsb2hex(b_string)
        return int(lsb_string, 16)

    # Formatting functions

    def uuid(h_string):
        """Format a hex string like an UUID."""
        split = lambda x: [x[:8], x[8:12], x[12:16], x[16:20], x[20:]]
        return '-'.join(split(h_string))

    def timestamp(seconds):
        return datetime.fromtimestamp(seconds)

    with open(filename, 'rb') as f:
        f.seek(2 * BLOCKSIZE)

        # Bytes 0-15
        print 'Total number of inodes: {0:d}'.format(lsb2int(f.read(4)))
        print 'Filesystem size in blocks: {0:d}'.format(lsb2int(f.read(4)))
        print 'Number of reserved blocks: {0:d}'.format(lsb2int(f.read(4)))
        print 'Free blocks counter: {0:d}'.format(lsb2int(f.read(4)))

        # Bytes 16-31
        print 'Free inodes counter: {0:d}'.format(lsb2int(f.read(4)))
        print 'Number of first block: {0:d}'.format(lsb2int(f.read(4)))
        val = lsb2int(f.read(4))
        print 'Block size: {0:d} ({1:d} Byte)'.format(val, 1024 * 2 ** val)
        print 'Fragment size: {0:d}'.format(lsb2int(f.read(4)))

        # Bytes 32-47
        print 'Number blocks per group: {0:d}'.format(lsb2int(f.read(4)))
        print 'Number fragments per group: {0:d}'.format(lsb2int(f.read(4)))
        print 'Number inodes per group: {0:d}'.format(lsb2int(f.read(4)))
        val = lsb2int(f.read(4))
        print 'Time of last mount: {0:d} ({1:%Y-%m-%d %H:%M:%S})'.format(val, timestamp(val))

        # Bytes 48-63
        print 'Time of last write: {0:%Y-%m-%d %H:%M:%S}'.format(timestamp(lsb2int(f.read(4))))
        print 'Mount operations counter: {0:d}'.format(lsb2int(f.read(2)))
        print 'Number of mount operations before check: {0:d}'.format(lsb2int(f.read(2)))
        print 'Magic signature: {0:#X}'.format(lsb2int(f.read(2)))
        print 'Status flag: {0:d}'.format(lsb2int(f.read(2)))
        print 'Behavior when detecting errors: {0:d}'.format(lsb2int(f.read(2)))
        print 'Minor revision level: {0:d}'.format(lsb2int(f.read(2)))

        # Bytes 64-79
        print 'Time of last check: {0:%Y-%m-%d %H:%M:%S}'.format(timestamp(lsb2int(f.read(4))))
        print 'Time between checks: {0:d}'.format(lsb2int(f.read(4)))
        print 'OS Filesystem created: {0:d}'.format(lsb2int(f.read(4)))
        print 'Revision level: {0:d}'.format(lsb2int(f.read(4)))

        # Bytes 80-95
        print 'Default user ID for reserved blocks: {0:d}'.format(lsb2int(f.read(2)))
        print 'Default group ID for reserved blocks: {0:d}'.format(lsb2int(f.read(2)))
        print 'Number first nonreserved inode: {0:d}'.format(lsb2int(f.read(4)))
        print 'Size of on-disk inode structure: {0:d}'.format(lsb2int(f.read(2)))
        print 'Block group number of this superblock: {0:d}'.format(lsb2int(f.read(2)))
        print 'Compatibility features bitmap: {0:#X}'.format(lsb2int(f.read(4)))

        # Bytes 96-103
        print 'Incompatible features bitmap: {0:#X}'.format(lsb2int(f.read(4)))
        print 'Read-only compatible features bitmap: {0:#X}'.format(lsb2int(f.read(4)))

        # Bytes 104-119
        print '128-bit filesystem identifier: {0}'.format(uuid(hexlify(f.read(16))))

        # Bytes 120-135
        print 'Volume name: {0}'.format(lsb2ascii(f.read(16)))

        # Bytes 136-199
        print 'Path of last mount point: {0}'.format(lsb2ascii(f.read(64)))

        # Bytes 200-207
        print 'Compression: {0:#X}'.format(lsb2int(f.read(8)))
        print 'Number of blocks to preallocate: {0:d}'.format(lsb2int(f.read(1)))
        print 'Number of blocks to preallocate for directories: {0:d}'.format(lsb2int(f.read(1)))


if __name__ == '__main__':

    if len(sys.argv) < 3 or sys.argv[1] not in ['dump', 'analyze']:
        print 'Usage: superblock.py [dump|analyze] <filename>'
        sys.exit(1)

    action = sys.argv[1]
    filename = sys.argv[2]

    if action == 'dump':
        print '\nPrinting superblock (bytes 1024-1535) of file %s.\n' % filename
        print ' ' * 5 + 'HEX'.center(35) + '  ' + 'ASCII'.center(16)
        dump(filename)
    elif action == 'analyze':
        print '\nAnalyzing superblock (bytes 1024-1535) of file %s.\n' % filename
        analyze(filename)
