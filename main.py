# main.py
import asyncio
import random
import subprocess
import sys
from datetime import datetime

# ===============================
# INSTALAÇÃO AUTOMÁTICA DE BIBLIOTECAS
# ===============================
# Isso garante que as bibliotecas necessárias estejam instaladas antes de rodar
def instalar(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

try:
    from alpha_vantage.foreignexchange import ForeignExchange
except ImportError:
    instalar("alpha_vantage")
    from alpha_vantage.foreignexchange import ForeignExchange

try:
    from telegram import Bot
except ImportError:
    instalar("python-telegram-bot")
    from telegram import Bot

# ===============================
# CONFIGURAÇÃO
# ===============================
ALPHA_KEY = "3SYERLAJ3ZAT69TM"                     # Sua Alpha Vantage Key
TOKEN = "123456789:ABCDEFGHIJKLMN_OPQRSTUVWXYZ"    # Seu token do Telegram
CHAT_ID = "2055716345"                             # Seu chat ID no Telegram
TIMEFRAME = "1min"                                 # Timeframe 1m
VELAS_ANALISE = 20                                  # Últimas 20 velas

# Inicializa cliente Alpha
fx = ForeignExchange(key=ALPHA_KEY, output_format='json')

# Inicializa bot Telegram
bot = Bot(token=TOKEN)

# Lista de pares
PAIRS = [
    "AUDCAD","AUDCHF","AUDJPY","AUDNZD","AUDSGD","AUDUSD",
    "CADCHF","CADJPY","CHFJPY","CHFNOK","CHFSGD",
    "EURAUD","EURCAD","EURCHF","EURGBP","EURJPY","EURNOK","EURNZD","EURSGD","EURUSD","EURZAR",
    "GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPSGD","GBPUSD",
    "NOKJPY",
    "NZDCAD","NZDCHF","NZDJPY","NZDSGD","NZDUSD",
    "SGDJPY",
    "USDBRL","USDCAD","USDCHF","USDDKK","USDHKD","USDJPY","USDMXN","USDSGD","USDTHB","USDZAR"
]

# ===============================
# FUNÇÕES
# ===============================
def analisar_candles(data):
    """
    Analisa os últimos 20 candles.
    Retorna 'CALL' ou 'PUT' baseado em fechamento/abertura.
    """
    sinais = {}
    for par, candles in data.items():
        ultimas = candles[-VELAS_ANALISE:]
        altas = sum(1 for c in ultimas if float(c['close']) > float(c['open']))
        baixas = VELAS_ANALISE - altas
        if altas > baixas:
            sinais[par] = "CALL"
        elif baixas > altas:
            sinais[par] = "PUT"
        else:
            sinais[par] = "NEUTRO"
    return sinais

async def enviar_sinal(sinal, par):
    """
    Envia mensagem para Telegram com hora, par e sinal.
    """
    hora = datetime.now().strftime("%H:%M:%S")
    msg = f"🤖 **TROIA v15 — IA**\nHora: {hora}\nPar: {par}\nSinal: {sinal}\nTimeframe: {TIMEFRAME}"
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

async def main():
    while True:
        data = {}
        for par in PAIRS:
            try:
                # Pega candles 1min (Alpha retorna JSON)
                raw, _ = fx.get_currency_exchange_intraday(
                    from_symbol=par[:3],
                    to_symbol=par[3:],
                    interval='1min',
                    outputsize='compact'
                )
                candles = []
                for time_str, val in list(raw.items())[:VELAS_ANALISE]:
                    candles.append({
                        'open': val['1. open'],
                        'high': val['2. high'],
                        'low': val['3. low'],
                        'close': val['4. close']
                    })
                data[par] = candles
            except Exception as e:
                print(f"Erro ao buscar {par}: {e}")

        sinais = analisar_candles(data)

        for par, sinal in sinais.items():
            if sinal != "NEUTRO":
                await enviar_sinal(sinal, par)

        # Espera de 10 a 20 minutos para próxima análise
        espera = random.randint(600, 1200)  # 600s = 10min, 1200s = 20min
        print(f"Próxima análise em {espera // 60} minutos")
        await asyncio.sleep(espera)

if __name__ == "__main__":
    asyncio.run(main())
