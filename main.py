import asyncio
import json
import websockets
import time
import telegram

# ===============================
# CONFIGURAÇÃO
# ===============================
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"   # Seu token do Telegram
CHAT_ID = "2055716345"                                      # Seu chat ID
RECONNECT_DELAY = 5                                         # Tempo de reconexão em segundos

# Lista de todos os ativos (normais + OTC)
ATIVOS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "EURGBP", "USDBRL", "USDZAR",
    "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC", "AUDUSD-OTC",
    "EURJPY-OTC", "GBPJPY-OTC", "EURGBP-OTC", "USDBRL-OTC", "USDZAR-OTC"
]

# URL base do WebSocket
WS_BASE = "wss://qxbroker.com/realtime/"

# Inicializa o bot do Telegram
bot = telegram.Bot(token=TOKEN)

async def conectar_ativo(ativo):
    url = WS_BASE + ativo
    while True:
        try:
            async with websockets.connect(url) as ws:
                print(f"Conectado em {ativo}")
                async for mensagem in ws:
                    dados = json.loads(mensagem)
                    # Aqui você pode ajustar o que quer enviar ao Telegram
                    if "ask" in dados and "bid" in dados:
                        preco = (dados["ask"] + dados["bid"]) / 2
                        texto = f"{ativo} preço atual: {preco}"
                        await enviar_telegram(texto)
        except Exception as e:
            print(f"Erro no {ativo}: {e}. Reconectando em {RECONNECT_DELAY}s...")
            await asyncio.sleep(RECONNECT_DELAY)

async def enviar_telegram(texto):
    try:
        bot.send_message(chat_id=CHAT_ID, text=texto)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

async def main():
    # Cria uma tarefa para cada ativo
    tarefas = [conectar_ativo(ativo) for ativo in ATIVOS]
    await asyncio.gather(*tarefas)

if __name__ == "__main__":
    asyncio.run(main())
