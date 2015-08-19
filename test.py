import unittest
import os
from router import search, search_all, RegexStructure, Router

DIR = 'sampleconfigs'
FILENAME = 'router_1_conf.cfg'


class TestRouter(unittest.TestCase):
    config = None

    @classmethod
    def setUpClass(cls):
        path = os.path.join(DIR, FILENAME)
        file = open(path, 'rb')
        cls.config = file.readlines()
        file.close

    def test_load(self):
        self.r = Router(self.config)
        self.assertEqual(self.r.config, self.config)

    def test_hostname(self):
        self.r = Router(self.config)
        self.assertEqual(self.r.hostname, 'router-1')


if __name__ == '__main__':
    unittest.main()
