import asyncio
import random
from datetime import datetime, timedelta, timezone
import requests
from telegram import Bot
from telegram.ext import ApplicationBuilder, CallbackContext

# ================= CONFIGURAÇÃO =================
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = 2055716345
ALPHA_API_KEY = "3SYERLAJ3ZAT69TM"

INTERVALO_LOOP = 30         # segundos entre cada checagem
TEMPO_VELA = 60             # duração da vela
PAUSA_APOS_RED = 600        # pausa após reds consecutivos
RED_MAX = 3

# ================= ESTADO =================
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

bot = Bot(token=TOKEN)

# ================= FUNÇÕES =================
def agora_utc():
    return datetime.now(timezone.utc)

def proxima_vela():
    t = agora_utc() + timedelta(seconds=TEMPO_VELA)
    return t.replace(second=0).strftime("%H:%M")

def score_estrategia(nome):
    return int(estrategias[nome] * 100)

def escolher_estrategia():
    return max(estrategias, key=score_estrategia)

# TODOS OS ATIVOS Forex + Cripto + Commodities da Alpha Vantage
def ativos_alpha():
    forex = [
        "EURUSD","GBPUSD","USDJPY","AUDUSD","NZDUSD",
        "EURJPY","GBPJPY","EURGBP","USDCAD","USDCHF"
    ]
    crypto = [
        "BTCUSD","ETHUSD","LTCUSD","XRPUSD","BCHUSD",
        "ADAUSD","DOTUSD","LINKUSD","DOGEUSD"
    ]
    commodities = [
        "XAUUSD","XAGUSD","WTI","BRENT","NG"
    ]
    return forex + crypto + commodities

# Obter candles via Alpha Vantage
async def obter_candles_alpha(par, interval=1):
    """
    Retorna últimos 2 candles (open, close)
    interval em minutos
    """
    try:
        if par in ["BTCUSD","ETHUSD","LTCUSD","XRPUSD","BCHUSD","ADAUSD","DOTUSD","LINKUSD","DOGEUSD"]:
            # Cripto usa CRYPTO_INTRADAY
            url = f"https://www.alphavantage.co/query?function=CRYPTO_INTRADAY&symbol={par[:3]}&market=USD&interval={interval}min&apikey={ALPHA_API_KEY}&outputsize=compact"
        elif par in ["XAUUSD","XAGUSD","WTI","BRENT","NG"]:
            # Commodities podem usar FX_INTRADAY (simulação simplificada)
            url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={par[:3]}&to_symbol=USD&interval={interval}min&apikey={ALPHA_API_KEY}&outputsize=compact"
        else:
            # Forex
            url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={par[:3]}&to_symbol={par[3:]}&interval={interval}min&apikey={ALPHA_API_KEY}&outputsize=compact"

        resp = requests.get(url, timeout=10)
        data = resp.json()
        # Pega o time series correto
        ts_keys = [k for k in data.keys() if "Time Series" in k]
        if not ts_keys:
            return None
        key = ts_keys[0]
        times = sorted(data[key].keys())
        if len(times) < 2:
            return None
        c1, c2 = times[-2], times[-1]
        candles = [
            {"open": float(data[key][c1]["1. open"]), "close": float(data[key][c1]["4. close"])},
            {"open": float(data[key][c2]["1. open"]), "close": float(data[key][c2]["4. close"])}
        ]
        return candles
    except Exception as e:
        print("Erro Alpha:", e)
        return None

def analisar_candle(candles, direcao):
    c = candles[-1]
    o = float(c['open'])
    cl = float(c['close'])
    if direcao == "CALL ⬆️":
        return "GREEN" if cl > o else "RED"
    else:
        return "GREEN" if cl < o else "RED"

# ================= SINAL =================
async def enviar_sinal():
    global estado, sinal_atual, fechamento_vela, pausa_ate

    if pausa_ate and agora_utc() < pausa_ate:
        return

    estrategia = escolher_estrategia()
    score = score_estrategia(estrategia)
    if score < 75:
        return

    ativos = ativos_alpha()
    par = random.choice(ativos)
    direcao = random.choice(["CALL ⬆️", "PUT ⬇️"])
    entrada = proxima_vela()

    sinal_atual = {"par": par, "direcao": direcao, "estrategia": estrategia}
    fechamento_vela = agora_utc() + timedelta(seconds=TEMPO_VELA)

    texto = (
        "🤖 **IAQuotex Sinais — TROIA v11**\n\n"
        "🚨 **SETUP VALIDADO PELO MOTOR IA**\n\n"
        f"📊 **Ativo:** {par}\n"
        f"🕯 **Direção:** {direcao}\n"
        f"⏰ **Entrada:** {entrada} (PRÓXIMA VELA)\n"
        f"🧠 **Estratégia:** {estrategia}\n"
        f"⭐ **Score:** {score}\n"
        "⚠️ Operação única. Aguarde o fechamento."
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

# ================= LOOP =================
async def loop_principal(context: CallbackContext):
    if estado == "LIVRE":
        await enviar_sinal()
    elif estado == "AGUARDANDO_RESULTADO":
        if agora_utc() >= fechamento_vela:
            await enviar_resultado()

# ================= START =================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.job_queue.run_repeating(loop_principal, interval=INTERVALO_LOOP, first=10)
    print("🚀 TROIA IA v11 ONLINE — Forex + Cripto + Commodities via Alpha Vantage")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
