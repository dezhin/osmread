from bz2 import BZ2File
import gzip

class Parser(object):

    def __init__(self, **kwargs):
        self._compression = kwargs.get('compression', None)

    def parse(fp):
        pass

    def parse_file(self, filename):
        if self._compression == 'bz2':
            fp = BZ2File(filename, 'r')
        elif self._compression == 'gz':
            fp = gzip.open(filename, 'r')
        else:
            fp = open(filename, 'rb')

        try:
            for e in self.parse(fp):
                yield e
        except Exception:
            fp.close()
            raise
