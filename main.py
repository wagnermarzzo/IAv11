import requests
import time
import asyncio
from telegram import Bot

# ==============================
# CONFIGURAÇÃO
# ==============================
ALPHA_KEY = "3SYERLAJ3ZAT69TM"  # Sua API Key Alpha Vantage
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"  # Seu Token Telegram
CHAT_ID = "2055716345"  # Seu Chat ID Telegram
INTERVALO = 60  # Tempo entre checagens (segundos)

# ==============================
# LISTA DE ATIVOS
# ==============================
ATIVOS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",  # Ações USA
    "BTC", "ETH", "DOGE", "LTC", "XRP"        # Criptos
]

# ==============================
# FUNÇÕES
# ==============================
def obter_preco(symbol):
    """Busca o preço atual usando Alpha Vantage"""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "Global Quote" in data:
            return float(data["Global Quote"]["05. price"])
        else:
            print(f"Erro na API para {symbol}: {data}")
            return None
    except Exception as e:
        print(f"Erro ao consultar {symbol}: {e}")
        return None

async def enviar_telegram(msg):
    """Envia mensagem para Telegram"""
    bot = Bot(TOKEN)
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

async def main():
    while True:
        for ativo in ATIVOS:
            preco = obter_preco(ativo)
            if preco:
                msg = f"💹 {ativo}: ${preco:.2f}"
                print(msg)
                await enviar_telegram(msg)
            await asyncio.sleep(1)  # Evita sobrecarga de requests
        await asyncio.sleep(INTERVALO)

# ==============================
# EXECUÇÃO
# ==============================
if __name__ == "__main__":
    asyncio.run(main())
