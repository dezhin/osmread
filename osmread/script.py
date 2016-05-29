import sys
from argparse import ArgumentParser

from osmread import parse_file, Node, Way, Relation

def main(argv=sys.argv):
    argparser = ArgumentParser()

    argparser.add_argument('filename', type=str)

    argparser.add_argument('-f', dest='format', metavar='format', type=str,
        help='file format: xml or pbf')
    argparser.add_argument('-c', dest='compression', metavar='compression', type=str,
        help='override compression autodetection: bz2')
    argparser.add_argument('-d', dest='dump', action='store_true',
        help='dump elements to stdout (debug)')

    args = argparser.parse_args(argv[1:])

    element_count, node_count, way_count, relation_count = 0, 0, 0, 0
    for e in parse_file(args.filename):
        element_count += 1

        if isinstance(e, Node):
            node_count += 1

        elif isinstance(e, Way):
            way_count += 1

        elif isinstance(e, Relation):
            relation_count += 1

        if args.dump:
            print(repr(e))

    print("%d elements read (nodes=%d, ways=%d, relations=%d)" % (element_count, node_count, way_count, relation_count))
