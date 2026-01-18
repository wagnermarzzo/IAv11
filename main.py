# main.py - Código único para Railway
import asyncio
import json
from datetime import datetime
import random
import websockets
from telegram import Bot

# ===============================
# CONFIGURAÇÃO
# ===============================
TOKEN = "123456789:ABCDEFGHIJKLMN_OPQRSTUVWXYZ"  # Seu token do Telegram
CHAT_ID = "2055716345"                           # Seu chat ID do Telegram
EMAIL = "apgwagner2@gmail.com"                   # Email da sua conta Quotex
PASSWORD = "@Aa88691553"                         # Senha da sua conta Quotex
TIMEFRAME = 60                                   # 1 minuto
VELAS_ANALISE = 20                               # Últimas 20 velas para análise

bot = Bot(token=TOKEN)

# ===============================
# ATIVOS (incluindo OTC)
# ===============================
ASSETS = [
    "EURUSD","EURUSD-OTC","GBPUSD","GBPUSD-OTC",
    "AUDUSD","AUDUSD-OTC","USDJPY","USDJPY-OTC",
    "USDBRL","USDBRL-OTC","EURGBP","EURGBP-OTC",
    "USDCHF","USDCHF-OTC","USDSGD","USDSGD-OTC",
    "USDZAR","USDZAR-OTC"
]

# ===============================
# FUNÇÕES AUXILIARES
# ===============================

def analisar_candles(candles):
    """
    Analisa os últimos candles e retorna sinal CALL/PUT
    """
    altas = sum(1 for c in candles if c['close'] > c['open'])
    baixas = len(candles) - altas
    if altas > baixas:
        return "CALL"
    elif baixas > altas:
        return "PUT"
    else:
        return "NEUTRO"

async def enviar_sinal_telegram(par, candle, sinal):
    hora = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"📊 *TROIA v15 — IA*\n"
        f"Hora: {hora}\n"
        f"Par: {par}\n"
        f"Sinal: {sinal}\n"
        f"Abertura: {candle['open']}\n"
        f"Fechamento: {candle['close']}\n"
        f"Alta: {candle['high']}  Baixa: {candle['low']}\n"
        f"Timeframe: 1min"
    )
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

# ===============================
# CÓDIGO PRINCIPAL DE WEBSOCKET
# ===============================

async def monitorar_ativo(asset, candles_storage):
    """
    Simula WebSocket para receber velas em tempo real
    (Substituir pelo endpoint real de WebSocket Quotex)
    """
    url = f"wss://quotex.com/realtime/{asset}"  # exemplo genérico
    while True:
        try:
            async with websockets.connect(url) as ws:
                # autenticação simples simulada
                await ws.send(json.dumps({"action":"login","email":EMAIL,"password":PASSWORD}))
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)

                    candle = {
                        "open": float(data.get("open",0)),
                        "high": float(data.get("high",0)),
                        "low": float(data.get("low",0)),
                        "close": float(data.get("close",0)),
                        "time": data.get("from")
                    }

                    candles_storage[asset].append(candle)
                    if len(candles_storage[asset]) > VELAS_ANALISE:
                        candles_storage[asset].pop(0)

                    sinal = analisar_candles(candles_storage[asset])
                    if sinal != "NEUTRO":
                        await enviar_sinal_telegram(asset, candle, sinal)

        except Exception as e:
            print(f"Erro no {asset}: {e}. Reconectando em 5s...")
            await asyncio.sleep(5)

async def main():
    candles_storage = {asset: [] for asset in ASSETS}
    tasks = [monitorar_ativo(asset, candles_storage) for asset in ASSETS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
