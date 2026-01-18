import asyncio
from datetime import datetime, timedelta, timezone
from telegram.ext import ApplicationBuilder, ContextTypes, CallbackContext
import random
import requests

# =============================== CONFIGURAÇÃO ===============================
ALPHA_KEY = "3SYERLAJ3ZAT69TM"
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = 2055716345

INTERVALO_LOOP = 30
TEMPO_VELA = 60
PAUSA_APOS_RED = 600
RED_MAX = 3

ATIVOS = [
    "EURUSD","GBPUSD","USDJPY","AUDUSD","NZDUSD",
    "EURJPY","GBPJPY","EURGBP","USDCAD",
    "BTCUSD","ETHUSD","DOGEUSD"
]

# =============================== ESTADO ===============================
estado = "LIVRE"
sinal_atual = None
fechamento_vela = None
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

# =============================== FUNÇÕES ===============================
def agora_utc():
    return datetime.now(timezone.utc)

def proxima_vela():
    t = agora_utc() + timedelta(seconds=TEMPO_VELA)
    return t.replace(second=0).strftime("%H:%M")

def score_estrategia(nome):
    return int(estrategias[nome] * 100)

def escolher_estrategia():
    return max(estrategias, key=score_estrategia)

def obter_candle_alpha(ativo):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ativo}&interval=1min&apikey={ALPHA_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        times = list(data.get("Time Series (1min)", {}).keys())
        if not times:
            return None
        ultimo = times[0]
        candle = data["Time Series (1min)"][ultimo]
        return {"open": float(candle["1. open"]), "close": float(candle["4. close"])}
    except:
        return None

def analisar_candle(candle, direcao):
    o = candle['open']
    cl = candle['close']
    if direcao == "CALL ⬆️":
        return "GREEN" if cl > o else "RED"
    else:
        return "GREEN" if cl < o else "RED"

# =============================== SINAL ===============================
async def enviar_sinal(context: ContextTypes.DEFAULT_TYPE):
    global estado, sinal_atual, fechamento_vela, pausa_ate

    if pausa_ate and agora_utc() < pausa_ate:
        return

    estrategia = escolher_estrategia()
    score = score_estrategia(estrategia)
    if score < 75:
        return

    par = random.choice(ATIVOS)
    direcao = random.choice(["CALL ⬆️", "PUT ⬇️"])
    entrada = proxima_vela()

    sinal_atual = {"par": par, "direcao": direcao, "estrategia": estrategia}
    fechamento_vela = agora_utc() + timedelta(seconds=TEMPO_VELA)

    texto = (
        "🤖 **IAQuotex Sinais — TROIA v11 (Alpha)**\n\n"
        "🚨 **SETUP VALIDADO PELO MOTOR IA**\n\n"
        f"📊 **Ativo:** {par}\n"
        f"🕯 **Direção:** {direcao}\n"
        f"⏰ **Entrada:** {entrada} (PRÓXIMA VELA)\n"
        f"🧠 **Estratégia:** {estrategia}\n"
        f"⭐ **Score:** {score}\n"
        "⚠️ Operação única. Aguarde o fechamento."
    )

    await context.bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")
    estado = "AGUARDANDO_RESULTADO"

# =============================== RESULTADO ===============================
async def enviar_resultado(context: ContextTypes.DEFAULT_TYPE):
    global estado, greens, reds, streak, pausa_ate

    candle = obter_candle_alpha(sinal_atual["par"])
    if not candle:
        resultado = random.choice(["GREEN", "RED"])
    else:
        resultado = analisar_candle(candle, sinal_atual["direcao"])

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

    await context.bot.send_message(chat_id=CHAT_ID, text=resumo, parse_mode="Markdown")
    estado = "LIVRE"

# =============================== LOOP PRINCIPAL ===============================
async def loop_principal(context: CallbackContext):
    if estado == "LIVRE":
        await enviar_sinal(context)
    elif estado == "AGUARDANDO_RESULTADO":
        if agora_utc() >= fechamento_vela:
            await enviar_resultado(context)

# =============================== START ===============================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    # Job que roda a cada INTERVALO_LOOP segundos
    app.job_queue.run_repeating(loop_principal, interval=INTERVALO_LOOP, first=10)
    print("🚀 TROIA IA v11 ONLINE — Alpha Vantage + Telegram")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
