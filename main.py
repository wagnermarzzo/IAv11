import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from api_alpha import AlphaVantage

# ===============================
# CONFIGURAÇÃO FIXA
# ===============================
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = "2055716345"
API_KEY = "3SYERLAJ3ZAT69TM"

alpha = AlphaVantage(API_KEY)

# ===============================
# COMANDOS DO BOT
# ===============================
async def start(update, context):
    await context.bot.send_message(chat_id=CHAT_ID,
                                   text="Troia v11 Alpha Vantage ativo ✅")

async def get_signals(update, context):
    mensagens = []

    # ---------- FOREX ----------
    forex_list = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD",
        "EURJPY", "GBPJPY", "EURGBP", "USDCAD", "USDCHF"
    ]
    for pair in forex_list:
        data = alpha.get_forex(pair[:3], pair[3:])
        if data:
            rate = data.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate", "N/A")
            mensagens.append(f"{pair} = {rate}")

    # ---------- CRIPTO ----------
    crypto_list = [
        "BTC", "ETH", "XRP", "LTC", "DOGE", "ADA", "SOL", "BNB"
    ]
    for coin in crypto_list:
        data = alpha.get_crypto(coin)
        if data:
            rate = data.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate", "N/A")
            mensagens.append(f"{coin}/USD = {rate}")

    # ---------- COMMODITIES EXEMPLO ----------
    commodities = {
        "Gold": ("XAU", "USD"),
        "Silver": ("XAG", "USD")
    }
    for name, (from_c, to_c) in commodities.items():
        data = alpha.get_forex(from_c, to_c)
        if data:
            rate = data.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate", "N/A")
            mensagens.append(f"{name} = {rate}")

    # Envia mensagem final
    msg_text = "\n".join(mensagens) if mensagens else "Nenhum dado disponível."
    await context.bot.send_message(chat_id=CHAT_ID, text=msg_text)

# ===============================
# BOT
# ===============================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signals", get_signals))

    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
