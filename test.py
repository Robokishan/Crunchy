import csv
import regex as re
import pycountry
from currency_converter import CurrencyConverter
from babel import Locale
from datetime import datetime

currencyRates = CurrencyConverter()

def create_reverse_currency_mapping(locale_str):
    locale = Locale.parse(locale_str)
    currency_symbols = locale.currency_symbols
    reverse_mapping = {symbol: code for code, symbol in currency_symbols.items()}
    return reverse_mapping

def symbol_to_currency_code(symbol, locale_str='en_US'):
    reverse_mapping = create_reverse_currency_mapping(locale_str)
    return reverse_mapping.get(symbol, None)


pattern = r'\p{Sc}'

# Specify the path to your CSV file
csv_file = '/Users/kishan/Work/CrunchyScrapper/crunchy.databucket_crunchbase.csv'

def convert_to_usd(amount, currency_code):
    last_date = currencyRates.bounds[currency_code].last_date
    r0 = currencyRates._get_rate(currency_code, last_date)
    r1 = currencyRates._get_rate('USD', last_date)
    exchangeRate =  round(1 / r0 * r1, 4)
    return currencyRates.convert(amount, currency_code,'USD'), exchangeRate

def get_multiplier(multiplier):
    multiplier = multiplier.upper()
    if multiplier == 'M':
        return 1e6
    elif multiplier == 'B':
        return 1e9
    elif multiplier == 'K':
        return 1e3
    elif multiplier == '':
        return 1
    else:
        raise ValueError(f"Invalid multiplier: {multiplier}")

# Open the CSV file
with open(csv_file, 'r') as file:
    # Create a CSV reader object
    csv_reader = csv.reader(file)

    # Find the index of the "funding" column
    header = next(csv_reader)
    funding_index = header.index("funding")

    # Iterate over each row in the CSV file
    for row in csv_reader:
        # Access the "funding" column in each row
        funding = row[funding_index]
        currency_symbol = re.findall(pattern, funding)
        currency_code = None
        currency_amount = None

        # handle currency with symbols
        if len(currency_symbol) > 0:
            currency_symbol = currency_symbol[-1]
            amount_str = funding.split(currency_symbol)[-1]
            match = re.match(r'([\d\.]+)([A-Za-z]?)', amount_str)
            number, multiplier = match.groups()
            currency_amount = float(number) * get_multiplier(multiplier)
            currency_code = symbol_to_currency_code(currency_symbol)

        # handle currency with currency code
        elif funding and funding != '—':
            currency_code_pattern = re.compile(r'([A-Z]{3})(\d+(\.\d+)?)([A-Za-z]?)')
            match = currency_code_pattern.match(funding)
            currency_code, amount, _, suffix = match.groups()
            currency_amount = float(number) * get_multiplier(multiplier)
            currency_code = pycountry.currencies.get(alpha_3=currency_code).alpha_3
        
        if currency_amount and currency_code:
            try:
                currency_amount_usd, exchangeRate = convert_to_usd(currency_amount, currency_code)
                # print(currency_amount, exchangeRate,  currency_code, currency_amount_usd)
            except Exception as e:
                print(f"Error converting {currency_amount} {currency_code} to USD: {e}")
                
            
        
        
