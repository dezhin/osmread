from collections import namedtuple

__einfo = ('id', 'version', 'changeset', 'timestamp', 'uid')

Node = namedtuple('Node', __einfo + ('tags', 'lon', 'lat'))
Way = namedtuple('Way', __einfo + ('tags', 'nodes', ))
Relation = namedtuple('Relation', __einfo + ('tags', 'members', ))

RelationMember = namedtuple('RelationMember', ('role', 'type', 'member_id'))

TYPE_NODE, TYPE_WAY, TYPE_RELATION = range(3)
