import asyncio
import json
import websockets
from datetime import datetime
import telebot

# ===============================
# CONFIGURAÇÃO (DADOS INCLUÍDOS)
# ===============================
TELEGRAM_TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = "2055716345"

QUOTEX_EMAIL = "apgwagner2@gmail.com"
QUOTEX_PASSWORD = "@Aa88691553"

# Ativos e OTC
ASSETS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "EURGBP",
    "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC", "AUDUSD-OTC",
    "USDBRL", "USDBRL-OTC", "USDCHF", "USDCHF-OTC", "USDZAR", "USDZAR-OTC",
    "USDSGD", "USDSGD-OTC", "GBPUSD-OTC", "EURUSD-OTC"
]

INTERVAL = 60  # Intervalo em segundos

# ===============================
# BOT TELEGRAM
# ===============================
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

def send_telegram(message):
    try:
        bot.send_message(CHAT_ID, message)
        print(f"[Telegram] Enviado: {message}")
    except Exception as e:
        print(f"[Telegram] Erro ao enviar: {e}")

# ===============================
# CONEXÃO QUOTEX
# ===============================
async def connect_asset(asset):
    # Formato seguro de WebSocket
    uri = f"wss://realtime.quotex.io/{asset}"
    while True:
        try:
            async with websockets.connect(uri) as ws:
                print(f"[{asset}] Conectado ao WebSocket.")
                send_telegram(f"✅ Conectado ao {asset}")
                while True:
                    data = await ws.recv()
                    process_data(asset, data)
        except Exception as e:
            print(f"[{asset}] Erro: {e}. Reconectando em 5s...")
            await asyncio.sleep(5)

# ===============================
# PROCESSAMENTO DE DADOS
# ===============================
def process_data(asset, data):
    try:
        info = json.loads(data)
        signal = None
        if "candle" in info:
            candle = info["candle"]
            if candle["close"] > candle["open"]:
                signal = "CALL"
            elif candle["close"] < candle["open"]:
                signal = "PUT"

        if signal:
            msg = f"[{asset}] Sinal: {signal} - {datetime.now().strftime('%H:%M:%S')}"
            print(msg)
            send_telegram(msg)
    except Exception as e:
        print(f"[{asset}] Erro no processamento: {e}")

# ===============================
# LOOP PRINCIPAL
# ===============================
async def main():
    tasks = [connect_asset(asset) for asset in ASSETS]
    await asyncio.gather(*tasks)

# ===============================
# EXECUÇÃO
# ===============================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot encerrado manualmente.")
