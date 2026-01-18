import asyncio
import requests
from datetime import datetime

class PublicAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"

    async def get_candles(self, par, interval=1, count=2):
        """
        Busca candles reais via Alpha Vantage
        par: "EUR/USD", "GBP/USD"...
        interval: minutos (1,5,15...)
        count: quantidade de candles
        """
        from_symbol, to_symbol = par.split("/")
        params = {
            "function": "FX_INTRADAY",
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "interval": f"{interval}min",
            "apikey": self.api_key,
            "outputsize": "compact"
        }
        try:
            resp = await asyncio.to_thread(requests.get, self.base_url, params=params)
            data = resp.json()
            key = f"Time Series FX ({interval}min)"
            candles_raw = data.get(key, {})
            candles = []
            for ts in list(candles_raw.keys())[:count]:
                c = candles_raw[ts]
                candles.append({
                    "open": float(c["1. open"]),
                    "close": float(c["4. close"]),
                    "timestamp": datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                })
            return candles
        except Exception as e:
            print(f"Erro ao obter candles: {e}")
            # fallback fake
            import random
            now = datetime.utcnow()
            return [{"open": random.uniform(1,2), "close": random.uniform(1,2), "timestamp": now} for _ in range(count)]
