from utils.Founded import FoundedToDate
import unittest
from datetime import datetime


class TestFounded(unittest.TestCase):
    def setUp(self):
        self.founded = FoundedToDate()

    def test_only_year(self):
        self.assertEqual(self.founded.getDateFromFounded(
            '2018'), datetime(2018, 1, 1))

    def test_year_month(self):
        self.assertEqual(self.founded.getDateFromFounded(
            'Aug2015'), datetime(2015, 8, 1))

    def test_year_month_with_comma(self):
        self.assertEqual(self.founded.getDateFromFounded(
            'Jan1,2015'), datetime(2015, 1, 1))

        self.assertEqual(self.founded.getDateFromFounded(
            'Jan01,2015'), datetime(2015, 1, 1))

        self.assertEqual(self.founded.getDateFromFounded(
            'Jan24,2015'), datetime(2015, 1, 24))

        self.assertEqual(self.founded.getDateFromFounded(
            'Dec2013'), datetime(2013, 12, 1))

    def test_none(self):
        self.assertEqual(self.founded.getDateFromFounded(None), None)

    def test_unrecognized(self):
        self.assertEqual(self.founded.getDateFromFounded(''), None)
        self.assertEqual(self.founded.getDateFromFounded('a'), None)
        self.assertEqual(self.founded.getDateFromFounded('123'), None)
        self.assertEqual(self.founded.getDateFromFounded('Jan   2015'), None)
        self.assertEqual(self.founded.getDateFromFounded(
            'random-string,234'), None)
        self.assertEqual(self.founded.getDateFromFounded(
            'rand01,2234'), None)


if __name__ == '__main__':
    unittest.main()
