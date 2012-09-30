from lxml.etree import iterparse
from datetime import datetime
from time import mktime

from osmread.parser import Parser
from osmread.elements import Node, Way, Relation, RelationMember


class XmlParser(Parser):

    def __init__(self, **kwargs):
        Parser.__init__(self, **kwargs)
        self._compression = kwargs.get('compression', None)

    def parse(self, fp):
        context = iterparse(fp, events=('start', 'end'))

        # common
        _type = None
        _id = None
        _version = None
        _changeset = None
        _timestamp = None
        _uid = None
        _tags = None
        # node only
        _lon = None
        _lat = None
        # way only
        _nodes = None
        # relation only
        _members = None

        for event, elem in context:

            if event == 'start':
                attrs = elem.attrib
                if elem.tag in ('node', 'way', 'relation'):
                    _id = long(attrs['id'])
                    _version = int(attrs['version'])
                    _changeset = int(attrs['changeset'])
                    # TODO: improve timestamp parsing - dateutil too slow
                    _tstxt = attrs['timestamp']
                    _timestamp = int((
                        datetime(
                            year=int(_tstxt[0:4]),
                            month=int(_tstxt[5:7]),
                            day=int(_tstxt[8:10]),
                            hour=int(_tstxt[11:13]),
                            minute=int(_tstxt[14:16]),
                            second=int(_tstxt[17:19]),
                            tzinfo=None
                        ) - datetime(
                            year=1970,
                            month=1,
                            day=1,
                            tzinfo=None
                        )
                    ).total_seconds())
                    _uid = int(attrs['uid'])
                    _tags = {}

                    if elem.tag == 'node':
                        _type = Node
                        _lon = float(attrs['lon'])
                        _lat = float(attrs['lat'])
                    elif elem.tag == 'way':
                        _type = Way
                        _nodes = []
                    elif elem.tag == 'relation':
                        _type = Relation
                        _members = []

                elif elem.tag == 'tag':
                    _tags[unicode(attrs['k'])] = unicode(attrs['v'])

                elif elem.tag == 'nd':
                    _nodes.append(long(attrs['ref']))

                elif elem.tag == 'member':
                    _members.append(
                        RelationMember(
                            unicode(attrs['role']),
                            {
                                'node': Node,
                                'way': Way,
                                'relation': Relation
                            }[attrs['type']],
                            long(attrs['ref'])
                        )
                    )

            elif event == 'end':
                if elem.tag in ('node', 'way', 'relation'):
                    args = [
                        _id, _version, _changeset,
                        _timestamp, _uid, _tags
                    ]

                    if elem.tag == 'node':
                        args.extend((_lon, _lat))

                    elif elem.tag == 'way':
                        args.append(tuple(_nodes))

                    elif elem.tag == 'relation':
                        args.append(tuple(_members))

                    elem.clear()

                    yield _type(*args)
