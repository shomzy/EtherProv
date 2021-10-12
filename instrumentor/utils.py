import errno
import os

import argparse

from slither import Slither


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def safe_open(path, attr):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    mkdir_p(os.path.dirname(path))
    return open(path, attr)


def parse_args():
    """
    """
    parser = argparse.ArgumentParser(
        description='Call graph printer. Similar to --print call-graph, but without printing the view/pure functions',
        usage='call_graph.py filename')

    parser.add_argument('filename',
                        help='The filename of the contract or truffle directory to analyze.')

    parser.add_argument('--solc', help='solc path', default='solc')

    return parser.parse_args()


def get_output_path(output_dir, file_name):
    base = os.path.basename(file_name)
    output_dir += base
    return output_dir


def extract_src_details(exp_src):
    exp_src = exp_src.split(':')
    start = int(exp_src[0])
    len = int(exp_src[1])
    return start, len


def slitherfy_file(s):
    parser = argparse.ArgumentParser(
        description='Call graph printer. Similar to --print call-graph, but without printing the view/pure functions',
        usage='call_graph.py filename')
    parser.add_argument('filename',
                        help='The filename of the contract or truffle directory to analyze.')
    parser.add_argument('--solc', help='solc path', default='solc')
    args = parser.parse_args(args=[s])
    slither = Slither(s, is_truffle=False, solc=args.solc)
    return slither