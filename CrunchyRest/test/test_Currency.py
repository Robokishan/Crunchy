from utils.Currency import CurrencyConverter
import unittest
import regex as re


million_rupee = "₹1M"
one_point_file_million_usd = "$1.5M"
thirty_three_million_usd = "$33M"
pound = "£179K"
w = "₩8B"
china = "CN¥13M"
ca = "CA$3.9M"
czk = "CZK13M"
sek = "SEK30M"


class TestFounded(unittest.TestCase):
    def setUp(self):
        self.currencyConverter = CurrencyConverter()

    def test_currency_code(self):
        self.assertEqual(
            self.currencyConverter.get_currency_symbol(million_rupee)[-1], "₹")
        self.assertEqual(self.currencyConverter.get_currency_symbol(
            one_point_file_million_usd)[-1], "$")
        self.assertEqual(self.currencyConverter.get_currency_symbol(
            thirty_three_million_usd)[-1], "$")
        self.assertEqual(
            self.currencyConverter.get_currency_symbol(pound)[-1], "£")
        self.assertEqual(
            self.currencyConverter.get_currency_symbol(w)[-1], "₩")
        self.assertEqual(
            self.currencyConverter.get_currency_symbol(china)[-1], "¥")
        self.assertEqual(
            self.currencyConverter.get_currency_symbol(ca)[-1], "$")

        # TODO: migrate to class
        currency_code_pattern = re.compile(
            r'([A-Z]{3})(\d+(\.\d+)?)([A-Za-z]?)')
        match = currency_code_pattern.match(czk)
        currency_code = None
        if match:
            currency_code, amount, _, suffix = match.groups()

        self.assertEqual(currency_code, "CZK")

        currency_code_pattern = re.compile(
            r'([A-Z]{3})(\d+(\.\d+)?)([A-Za-z]?)')
        match = currency_code_pattern.match(sek)
        currency_code = None
        if match:
            currency_code, amount, _, suffix = match.groups()
        self.assertEqual(currency_code, "SEK")


if __name__ == '__main__':
    unittest.main()
