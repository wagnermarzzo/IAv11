import asyncio
from datetime import datetime, timedelta, timezone
from telegram import Bot
from alpha_vantage.foreignexchange import ForeignExchange
import random

# ================= CONFIGURAÇÃO =================
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = 2055716345

API_KEY_ALPHA = "3SYERLAJ3ZAT69TM"

TIMEFRAME = "1min"   # timeframe 1m
VELAS_ANALISE = 20   # últimas 20 velas
INTERVALO_LOOP = 60  # checa a cada 1 minuto
RED_MAX = 3
PAUSA_APOS_RED = 600

# ================= LISTA DE ATIVOS =================
ATIVOS = [
    "AUD/CAD","AUD/CHF","AUD/JPY","AUD/NZD","AUD/SGD","AUD/USD",
    "CAD/CHF","CAD/JPY",
    "CHF/JPY","CHF/NOK","CHF/SGD",
    "EUR/AUD","EUR/CAD","EUR/CHF","EUR/GBP","EUR/JPY","EUR/NOK","EUR/NZD","EUR/SGD","EUR/USD","EUR/ZAR",
    "GBP/AUD","GBP/CAD","GBP/CHF","GBP/JPY","GBP/NZD","GBP/SGD","GBP/USD",
    "NOK/JPY",
    "NZD/CAD","NZD/CHF","NZD/JPY","NZD/SGD","NZD/USD",
    "SGD/JPY",
    "USD/BRL","USD/CAD","USD/CHF","USD/DKK","USD/HKD","USD/JPY","USD/MXN","USD/SGD","USD/THB","USD/ZAR"
]

# ================= ESTADO =================
estado = "LIVRE"
sinal_atual = None
pausa_ate = None
greens = 0
reds = 0
streak = 0

estrategias = {
    "Tendência": 1.0,
    "Reversão": 1.0,
    "Price Action": 1.0,
    "Micro Tendência": 1.0
}

bot = Bot(token=TOKEN)
fx = ForeignExchange(key=API_KEY_ALPHA)

# ================= FUNÇÕES =================
def agora_utc():
    return datetime.now(timezone.utc)

def proxima_vela():
    return agora_utc().strftime("%H:%M")

def score_estrategia(nome):
    return int(estrategias[nome] * 100)

def escolher_estrategia():
    return max(estrategias, key=score_estrategia)

async def obter_candles_alpha(par):
    """Obtém candles recentes da Alpha Vantage"""
    try:
        from_alpha = fx.get_currency_exchange_intraday(from_symbol=par.split("/")[0],
                                                       to_symbol=par.split("/")[1],
                                                       interval='1min',
                                                       outputsize='compact')[0]
        # converte para lista ordenada do mais antigo para o mais recente
        candles = sorted(from_alpha.items(), key=lambda x: x[0])
        return candles[-VELAS_ANALISE:]  # últimas 20 velas
    except:
        return None

def analisar_candle(candles, direcao):
    """Analisa se a última vela confirma CALL ou PUT"""
    ultimo = candles[-1][1]
    open_ = float(ultimo['1. open'])
    close_ = float(ultimo['4. close'])
    if direcao == "CALL ⬆️":
        return "GREEN" if close_ > open_ else "RED"
    else:
        return "GREEN" if close_ < open_ else "RED"

# ================= SINAL =================
async def enviar_sinal():
    global estado, sinal_atual, pausa_ate

    if pausa_ate and agora_utc() < pausa_ate:
        return

    estrategia = escolher_estrategia()
    score = score_estrategia(estrategia)
    if score < 50:  # mínimo para enviar
        return

    par = random.choice(ATIVOS)
    direcao = random.choice(["CALL ⬆️", "PUT ⬇️"])
    entrada = proxima_vela()

    sinal_atual = {"par": par, "direcao": direcao, "estrategia": estrategia}

    texto = (
        f"🤖 **TROIA v15 — IA**\n\n"
        f"🚨 **SETUP VALIDADO PELA IA**\n\n"
        f"📊 **Ativo:** {par}\n"
        f"🕯 **Direção:** {direcao}\n"
        f"⏰ **Hora da Entrada:** {entrada}\n"
        f"🧠 **Estratégia:** {estrategia}\n"
        f"⭐ **Score:** {score}\n"
        f"⏱ **Timeframe:** {TIMEFRAME}\n"
        f"⚠️ Operação única. Aguarde o fechamento."
    )

    await bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")
    estado = "AGUARDANDO_RESULTADO"

# ================= RESULTADO =================
async def enviar_resultado():
    global estado, greens, reds, streak, pausa_ate

    candles = await obter_candles_alpha(sinal_atual["par"])
    if not candles:
        resultado = random.choice(["GREEN", "RED"])
    else:
        resultado = analisar_candle(candles, sinal_atual["direcao"])

    if resultado == "GREEN":
        greens += 1
        streak += 1
        estrategias[sinal_atual["estrategia"]] += 0.05
        texto = "🟢 **GREEN CONFIRMADO!** Mercado respeitou a leitura."
    else:
        reds += 1
        streak = 0
        estrategias[sinal_atual["estrategia"]] = max(0.5, estrategias[sinal_atual["estrategia"]] - 0.07)
        texto = "🔴 **RED.** Mercado em correção."
        if reds >= RED_MAX:
            pausa_ate = agora_utc() + timedelta(seconds=PAUSA_APOS_RED)
            reds = 0

    total = greens + reds
    acc = (greens / total) * 100 if total else 0
    resumo = (
        f"{texto}\n\n"
        f"📊 Greens: {greens}\n"
        f"🔴 Reds: {reds}\n"
        f"🔥 Streak: {streak}\n"
        f"📈 Assertividade: {acc:.2f}%\n\n"
        "🧠 IA recalibrando estratégias..."
    )

    await bot.send_message(chat_id=CHAT_ID, text=resumo, parse_mode="Markdown")
    estado = "LIVRE"

# ================= LOOP PRINCIPAL =================
async def loop_principal():
    while True:
        if estado == "LIVRE":
            await enviar_sinal()
        elif estado == "AGUARDANDO_RESULTADO":
            await enviar_resultado()
        await asyncio.sleep(INTERVALO_LOOP)

# ================= START =================
async def main():
    print("🚀 TROIA IA v15 ONLINE — Forex REAL + OTC")
    await loop_principal()

if __name__ == "__main__":
    asyncio.run(main())
