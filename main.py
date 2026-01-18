import time
import requests
import telebot
import asyncio
import websockets

# ===============================
# CONFIGURAÇÃO (hardcoded)
# ===============================
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"  # Seu token real
CHAT_ID = "2055716345"                                     # Seu chat id real
EMAIL = "apgwagner2@gmail.com"
SENHA = "@Aa88691553"

# Intervalo entre verificações (segundos)
INTERVALO = 60  

# Lista de ativos válidos (WebSocket)
ATIVOS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "EURGBP",
    "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC",
    "AUDUSD-OTC", "EURJPY-OTC", "GBPJPY-OTC"
]

# Inicializa o bot do Telegram
bot = telebot.TeleBot(TOKEN, threaded=False)

# ===============================
# FUNÇÃO DE ALERTA NO TELEGRAM
# ===============================
def enviar_mensagem(texto):
    try:
        bot.send_message(CHAT_ID, texto)
        print(f"[TELEGRAM] {texto}")
    except Exception as e:
        print(f"[ERRO TELEGRAM] {e}")

# ===============================
# FUNÇÃO DE CONEXÃO WEBSOCKET
# ===============================
async def monitor_ativo(ativo):
    uri = f"wss://qxbroker.com/realtime/{ativo}"  # ws ou wss obrigatório
    while True:
        try:
            async with websockets.connect(uri) as ws:
                await ws.send("ping")
                resp = await ws.recv()
                enviar_mensagem(f"Conexão OK: {ativo} → {resp}")
                await asyncio.sleep(INTERVALO)
        except Exception as e:
            print(f"Erro no {ativo}: {e}. Reconectando em 5s...")
            await asyncio.sleep(5)

# ===============================
# FUNÇÃO PRINCIPAL
# ===============================
async def main():
    enviar_mensagem("Bot iniciado ✅")
    tasks = [monitor_ativo(ativo) for ativo in ATIVOS]
    await asyncio.gather(*tasks)

# ===============================
# EXECUÇÃO
# ===============================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot interrompido manualmente.")
