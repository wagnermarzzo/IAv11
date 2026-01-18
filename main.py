# main.py
import asyncio
import subprocess
import sys
from datetime import datetime
import json

# ===============================
# INSTALAÇÃO AUTOMÁTICA DE BIBLIOTECAS
# ===============================
def instalar(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

try:
    from pyquotex.stable_api import Quotex
except ImportError:
    instalar("pyquotex")
    from pyquotex.stable_api import Quotex

try:
    from telegram import Bot
except ImportError:
    instalar("python-telegram-bot")
    from telegram import Bot

# ===============================
# CONFIGURAÇÃO
# ===============================
TOKEN = "123456789:ABCDEFGHIJKLMN_OPQRSTUVWXYZ"   # Seu token do Telegram
CHAT_ID = "2055716345"                            # Seu chat ID do Telegram
TIMEFRAME = 60                                    # Velas de 1min no PyQuotex
EMAIL = "apgwagner2@gmail.com"                   # Seu email da Quotex
PASSWORD = "@Aa88691553"                       # Sua senha da Quotex

bot = Bot(token=TOKEN)

# Lista de ativos que você quer monitorar
# Inclui OTC e ativos suportados (ex.: EURUSD_otc, GBPUSD_otc, etc.)
ASSETS = [
    "EURUSD_otc", "GBPUSD_otc", "AUDUSD_otc", "USDJPY_otc",
    "USDBRL_otc", "EURGBP_otc", "USDCHF_otc", "USDVND_otc",
    "USDZAR_otc", "EURUSD", "GBPUSD", "AUDUSD", "USDJPY"
]

# ===============================
# FUNÇÕES
# ===============================

async def enviar_sinal_par(par, candle):
    hora = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"📊 *TROIA v15 — IA*\n"
        f"Hora: {hora}\n"
        f"Par: {par}\n"
        f"Abertura: {candle['open']}\n"
        f"Fechamento: {candle['close']}\n"
        f"Alta: {candle['high']}  Baixa: {candle['low']}\n"
        f"Timeframe: 1min"
    )
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def monitorar_mercado():
    # Conecta e autentica no Quotex
    client = Quotex(email=EMAIL, password=PASSWORD, lang="en")
    success, msg = await client.connect()
    if not success:
        print("Erro ao conectar:", msg)
        return

    print("Conectado no Quotex com sucesso!")
    
    # Inscreve para receber dados de velas de todos os ativos
    for asset in ASSETS:
        await client.subscribe_candles(asset=asset, period=TIMEFRAME)

    # Dicionário para guardar últimas velas
    candles = {asset: [] for asset in ASSETS}

    # Loop principal de dados
    async for item in client.iter_candles_stream():
        par = item.get("asset")
        if par not in candles:
            continue

        # Monta candle em formato legível
        candle = {
            "open": item.get("open"),
            "high": item.get("high"),
            "low": item.get("low"),
            "close": item.get("close"),
            "time": item.get("from")
        }
        candles[par].append(candle)
        if len(candles[par]) > 20:
            candles[par].pop(0)

        # Envia sinal para cada nova vela
        await enviar_sinal_par(par, candle)

    await client.close()

async def main():
    while True:
        try:
            await monitorar_mercado()
        except Exception as e:
            print("Erro no loop principal:", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
