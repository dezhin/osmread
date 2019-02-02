from osmread.elements import Node, Way, Relation


def parse_file(filename, **kwargs):
    parser_cls = None
    kwargs = dict(kwargs)

    if filename.endswith(('.osm', '.xml', '.osm.bz2', '.xml.bz2', '.osm.gz', '.xml.gz')) \
            or kwargs.get('format', None) == 'xml':

        from osmread.parser.xml import XmlParser
        parser_cls = XmlParser

        if filename.endswith('.bz2'):
            kwargs['compression'] = 'bz2'
        elif filename.endswith('.gz'):
            kwargs['compression'] = 'gz'

    elif filename.endswith('.pbf') \
            or kwargs.get('format', None) == 'pbf':

        from osmread.parser.pbf import PbfParser
        parser_cls = PbfParser

    parser = parser_cls(**kwargs)

    for e in parser.parse_file(filename):
        yield e
