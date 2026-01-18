# main.py
import asyncio
import sys
import subprocess
from datetime import datetime

# ===============================
# INSTALAÇÃO AUTOMÁTICA DE BIBLIOTECAS (caso não esteja no ambiente)
# ===============================
def instalar(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

try:
    from pyquotex.stable_api import Quotex
except ImportError:
    instalar("git+https://github.com/cleitonleonel/pyquotex.git")
    from pyquotex.stable_api import Quotex

try:
    from telegram import Bot
except ImportError:
    instalar("python-telegram-bot")
    from telegram import Bot

# ===============================
# CONFIGURAÇÃO
# ===============================
TOKEN = "123456789:ABCDEFGHIJKLMN_OPQRSTUVWXYZ"  # Seu token do Telegram
CHAT_ID = "2055716345"                           # Seu chat ID do Telegram
TIMEFRAME = 60                                   # 1 minuto
EMAIL = "apgwagner2@gmail.com"                 # Seu email da Quotex
PASSWORD = "@Aa88691553"                     # Sua senha da Quotex

bot = Bot(token=TOKEN)

# ===============================
# ATIVOS (incluindo OTC)
# ===============================
ASSETS = [
    "EURUSD", "EURUSD_otc", "GBPUSD", "GBPUSD_otc", "AUDUSD", "AUDUSD_otc", "USDJPY", "USDJPY_otc",
    "USDBRL", "USDBRL_otc", "EURGBP", "EURGBP_otc", "USDCHF", "USDCHF_otc", "USDVND_otc", "USDZAR_otc"
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
    # Conecta e autentica na Quotex
    client = Quotex(email=EMAIL, password=PASSWORD, lang="en")
    success, msg = await client.connect()
    if not success:
        print("Erro ao conectar:", msg)
        return

    print("Conectado na Quotex com sucesso!")

    # Inscreve para receber dados de velas de todos os ativos
    for asset in ASSETS:
        await client.subscribe_candles(asset=asset, period=TIMEFRAME)

    # Dicionário para guardar últimas velas
    candles = {asset: [] for asset in ASSETS}

    # Loop principal de recebimento de dados
    async for item in client.iter_candles_stream():
        par = item.get("asset")
        if par not in candles:
            continue

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

        # Envia cada vela recebida para Telegram
        await enviar_sinal_par(par, candle)


async def main():
    while True:
        try:
            await monitorar_mercado()
        except Exception as e:
            print("Erro no loop principal:", e)
            print("Reconectando em 5 segundos...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
