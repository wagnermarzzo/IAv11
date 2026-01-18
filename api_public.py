import requests

class AlphaVantage:
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key):
        self.api_key = api_key

    def get_forex(self, from_currency, to_currency):
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": self.api_key
        }
        resp = requests.get(self.BASE_URL, params=params)
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_crypto(self, symbol, market="USD"):
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": symbol,
            "to_currency": market,
            "apikey": self.api_key
        }
        resp = requests.get(self.BASE_URL, params=params)
        if resp.status_code == 200:
            return resp.json()
        return None
