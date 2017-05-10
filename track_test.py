'''
Usage: track_test.py FLAGS file_name idx
'''

import re
from trainer import tiny_collection_parser
from google.apputils import app
import gflags

gflags.DEFINE_bool('lily', False, 'Whether to show the music sheet',
                   short_name='l')

FLAGS = gflags.FLAGS


def test_tiny(file_name, idx):
    with open(file_name, 'r') as f:
        lines = f.readlines()

    keyed_lines = dict([(int(re.search('X:([0-9]*)', l).groups()[0]), l)
                        for l in lines])

    if idx not in keyed_lines:
        raise ValueError('No example with such key: ' + str(idx))

    s = tiny_collection_parser(keyed_lines[idx])
    s.show('midi')
    if FLAGS.lily:
        s.show('lily')


def main(argv):
    test_tiny(argv[1], int(argv[2]))


if __name__ == '__main__':
    app.run()
