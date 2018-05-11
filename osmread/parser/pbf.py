from struct import unpack
import zlib
import sys

from osmread.parser import Parser
from osmread.elements import Node, Way, Relation, RelationMember
if sys.version_info > (3,):
    from osmread.protobuf.fileformat_pb2 import BlobHeader, Blob
    from osmread.protobuf.osmformat_pb2 import HeaderBlock, PrimitiveBlock
    long = int
else:
    from osmread.protobuf.osm_pb2 import BlobHeader, Blob, HeaderBlock, PrimitiveBlock


class PBFException(Exception):
    pass


class PBFNotImplemented(PBFException):
    pass


class PbfParser(Parser):

    def __init__(self, **kwargs):
        Parser.__init__(self, **kwargs)

    def parse(self, fp):
        blob_header = self.__read_blob_header(fp, 'OSMHeader')
        blob_data = self.__read_blob_data(fp, blob_header)

        header_block = HeaderBlock()
        header_block.ParseFromString(blob_data)

        for feature in header_block.required_features:
            if not (feature in ('OsmSchema-V0.6', 'DenseNodes')):
                raise PBFNotImplemented(
                    'Required feature %s not implemented!',
                    feature)

        while True:
            blob_header = self.__read_blob_header(fp, 'OSMData')

            if not blob_header:
                # EOF
                break

            blob_data = self.__read_blob_data(fp, blob_header)
            pblock = PrimitiveBlock()
            pblock.ParseFromString(blob_data)

            for group in pblock.primitivegroup:
                if len(group.nodes) > 0:
                    for i in self.__parse_nodes(pblock, group.nodes):
                        yield i
                elif len(group.dense.id) > 0:
                    for i in self.__parse_dense(pblock, group.dense):
                        yield i
                elif len(group.ways) > 0:
                    for i in self.__parse_ways(pblock, group.ways):
                        yield i
                elif len(group.relations) > 0:
                    for i in self.__parse_relations(pblock, group.relations):
                        yield i

    def __read_blob_header(self, fp, header_type):
        buf = fp.read(4)

        if len(buf) == 0:
            return None
        elif len(buf) != 4:
            raise PBFException('Invalid header len!')

        msg_len = unpack('!L', buf)[0]

        msg = BlobHeader()
        msg.ParseFromString(fp.read(msg_len))

        if msg.type != header_type:
            raise PBFException('Invalid header type!')

        return msg

    def __read_blob_data(self, fp, blob_header):
        msg = Blob()
        msg.ParseFromString(fp.read(blob_header.datasize))

        if len(msg.raw) > 0:
            return msg.raw
        elif len(msg.zlib_data) > 0:
            return zlib.decompress(msg.zlib_data)
        else:
            raise PBFNotImplemented("Unsupported data type!")

    def __parse_tags(self, itm, pblock):
        d = dict()
        for k, v in zip(itm.keys, itm.vals):
            d[pblock.stringtable.s[k].decode('utf-8')] = \
                pblock.stringtable.s[v].decode('utf-8')
        return d

    def __parse_nodes(self, pblock, data):
        granularity = pblock.granularity
        lon_offset = pblock.lon_offset
        lat_offset = pblock.lat_offset

        for e in data:
            try:
                uid = e.info.uid
            except:
                uid = 0  # An obj can miss an uid (when anonymous edits were possible)
            try:
                cs = int(e.info.changeset)
            except:
                cs = 0 # GeoFabrik's (May 2018) public snapshots strip the changeset attribute out of their data
            yield Node(
                id=e.id,
                version=e.info.version,
                changeset=cs,
                timestamp=int(e.info.timestamp),
                uid = uid,
                tags=self.__parse_tags(e, pblock),
                lon=float(e.lon * granularity + lon_offset) / long(1000000000),
                lat=float(e.lat * granularity + lat_offset) / long(1000000000),
            )

    def __parse_dense(self, pblock, data):
        node_granularity = pblock.granularity
        timestamp_granularity = pblock.date_granularity
        lon_offset = pblock.lon_offset
        lat_offset = pblock.lat_offset
        cid = 0
        clon = 0
        clat = 0
        cuid = 0
        cts = 0
        ccs = 0
        tag_idx = 0

        for did, version, dlon, dlat, duid, dts, dcs in zip(
                data.id, data.denseinfo.version,
                data.lon, data.lat,
                data.denseinfo.uid, data.denseinfo.timestamp,
                data.denseinfo.changeset):
            cid += did
            clon += dlon
            clat += dlat
            cuid += duid
            cts += dts
            ccs += dcs

            tags = {}
            if tag_idx < len(data.keys_vals):
                while data.keys_vals[tag_idx] != 0:
                    k = data.keys_vals[tag_idx]
                    v = data.keys_vals[tag_idx + 1]
                    tag_idx += 2
                    tags[pblock.stringtable.s[k].decode('utf-8')] = \
                        pblock.stringtable.s[v].decode('utf-8')

            tag_idx += 1

            yield Node(
                id=cid,
                version=version,
                changeset=int(ccs),
                timestamp=int(cts * timestamp_granularity / 1000),
                uid=cuid,
                tags=tags,
                lon=float(clon * node_granularity + lon_offset) / long(1000000000),
                lat=float(clat * node_granularity + lat_offset) / long(1000000000),
            )

    def __parse_ways(self, pblock, data):
        for e in data:
            nid = 0
            nodes = []
            for delta in e.refs:
                nid += delta
                nodes.append(nid)

            yield Way(
                id=e.id,
                version=e.info.version,
                changeset=int(e.info.changeset),
                timestamp=int(e.info.timestamp),
                uid=e.info.uid,
                tags=self.__parse_tags(e, pblock),
                nodes=tuple(nodes),
            )

    def __parse_relations(self, pblock, data):
        for e in data:
            members = []
            mid = 0
            for role_id, mtype, mid_delta in zip(
                    e.roles_sid, e.types, e.memids):
                mid += mid_delta
                members.append(
                    RelationMember(
                        pblock.stringtable.s[role_id].decode('utf-8'),
                        (Node, Way, Relation)[mtype],
                        mid
                    )
                )

            yield Relation(
                id=e.id,
                version=e.info.version,
                changeset=int(e.info.changeset),
                timestamp=int(e.info.timestamp),
                uid=e.info.uid,
                tags=self.__parse_tags(e, pblock),
                members=tuple(members)
            )
