import csv
import regex as re
import pycountry
from babel import Locale
import requests
import json
import time

# Specify the path to your CSV file
csv_file = '/Users/kishan/Work/CrunchyScrapper/crunchy.databucket_crunchbase.csv'

class CurrencyConverter:
    url = 'https://open.er-api.com/v6/latest/USD'
    rates = None
    TMP_FOLDER = '/tmp'
    TMP_FILE = 'rates.json'
    next_update = None

    def __init__(self):
        # read rates from file
        self.tmpFile = f'{self.TMP_FOLDER}/{self.TMP_FILE}'
        try:
            with open(self.tmpFile, 'r') as f:
                self.rates = json.load(f)
            self.next_update = self.rates['time_next_update_unix']
        except Exception as e:
            print(e)
        
        # if rates are old or not present, fetch new rates
        if self.rates is None or self.rates['time_next_update_unix'] < time.time():
            self.rates = self._get_rates()
        else:
            self.rates = self.rates['rates']

    def getRate(self, currency):
        if self.next_update < time.time():
            self.rates = self._get_rates()
        return self.rates.get(currency, None)
    
    def convert(self, amount, from_currency, to_currency):
        if from_currency == to_currency:
            return round(amount,2), 1
        from_rate = self.getRate(from_currency)
        to_rate = self.getRate(to_currency)
        if from_rate is None or to_rate is None:
            raise Exception("Invalid currency")
        return round((amount * to_rate / from_rate), 2), round((1 * from_rate / to_rate), 6)
    
    def _get_rates(self):
        max_retries = 5
        retries = 0
        delay = 1
        while retries < max_retries:
            try:
                print("Fetching rates...")
                response = requests.get(self.url)
                data = response.json()
                # save rates to file
                with open(self.tmpFile, 'w') as f:
                    json.dump(data, f)
                self.next_update = data['time_next_update_unix']
                return data['rates']
            except Exception as e:
                print(f"Error retrieving rates: {e}")
                retries += 1
                delay *= 2
                if retries > max_retries:
                    raise Exception("Failed to retrieve rates")
                time.sleep(delay)
            
    def get_currency_symbol(self, str):
        return re.findall(r'\p{Sc}', str)
    
    def create_reverse_currency_mapping(self, locale_str):
        locale = Locale.parse(locale_str)
        currency_symbols = locale.currency_symbols
        reverse_mapping = {symbol: code for code, symbol in currency_symbols.items()}
        return reverse_mapping

    def symbol_to_currency_code(self, symbol, locale_str='en_US'):
        reverse_mapping = self.create_reverse_currency_mapping(locale_str)
        return reverse_mapping.get(symbol, None)
    
    def get_multiplier(self, multiplier):
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


currencyConvert = CurrencyConverter() 

def get_currency_in_usd(funding):
    currency_symbol = currencyConvert.get_currency_symbol(funding)
    currency_code = None
    currency_amount = None

    # handle currency with symbols
    if len(currency_symbol) > 0:
        currency_symbol = currency_symbol[-1]
        amount_str = funding.split(currency_symbol)[-1]
        # sample $1.5M, €1.5M, £1.5M, ¥1.5M, ₹1.5M
        match = re.match(r'([\d\.]+)([A-Za-z]?)', amount_str)
        if match:
            number, multiplier = match.groups()
            currency_amount = float(number) * currencyConvert.get_multiplier(multiplier)
            currency_code = currencyConvert.symbol_to_currency_code(currency_symbol)

    # handle currency with currency code
    elif funding and funding != '—':
        # sample USD1.5M, EUR1.5M, GBP1.5M, JPY1.5M, INR1.5M
        currency_code_pattern = re.compile(r'([A-Z]{3})(\d+(\.\d+)?)([A-Za-z]?)')
        match = currency_code_pattern.match(funding)
        if match:    
            currency_code, amount, _, suffix = match.groups()
            currency_amount = float(amount) * currencyConvert.get_multiplier(suffix)
            currency_code = pycountry.currencies.get(alpha_3=currency_code).alpha_3
    
    if currency_amount and currency_code:
        currency_amount_usd, rate = currencyConvert.convert(currency_amount, currency_code,'USD')
        return currency_amount_usd, rate, currency_code, currency_amount
    return None

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
        
        result = get_currency_in_usd(funding)
        if result is not None:
            currency_amount_usd, rate, currency_code, currency_amount = result
            print(currency_amount_usd, rate, currency_code, currency_amount)



        
                
            
        
        
