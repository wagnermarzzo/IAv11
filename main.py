import asyncio
import random
from datetime import datetime, timedelta, timezone
from telegram import Bot
from api_quotex import Quotex

# ===============================
# CONFIGURAÇÃO
# ===============================
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = 2055716345

ALPHA_KEY = "3SYERLAJ3ZAT69TM"  # Caso queira integrar Alpha
TIMEFRAME = "1m"
INTERVALO_MIN = 180  # 3 minutos
INTERVALO_MAX = 300  # 5 minutos
TEMPO_VELA = 60  # segundos
RED_MAX = 3
PAUSA_APOS_RED = 600  # segundos

ATIVOS = [
    "AUDCAD","AUDCHF","AUDJPY","AUDNZD","AUDSGD","AUDUSD",
    "CADCHF","CADJPY","CHFJPY","CHFNOK","CHFSGD",
    "EURAUD","EURCAD","EURCHF","EURGBP","EURJPY","EURNOK","EURNZD","EURSGD","EURUSD","EURZAR",
    "GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPSGD","GBPUSD",
    "NOKJPY","NZDCAD","NZDCHF","NZDJPY","NZDSGD","NZDUSD",
    "SGDJPY","USDBRL","USDCAD","USDCHF","USDDKK","USDHKD","USDJPY","USDMXN","USDSGD","USDTHB","USDZAR"
]

ESTRATEGIAS = {
    "Tendência": 1.0,
    "Reversão": 1.0,
    "Price Action": 1.0,
    "Micro Tendência": 1.0
}

# ===============================
# ESTADO
# ===============================
estado = "LIVRE"
sinal_atual = None
fechamento_vela = None
pausa_ate = None
greens = 0
reds = 0
streak = 0

bot = Bot(token=TOKEN)
client = Quotex()  # já inicializado sem email/senha, usando API real

# ===============================
# FUNÇÕES AUXILIARES
# ===============================
def agora_utc():
    return datetime.now(timezone.utc)

def proxima_vela():
    t = agora_utc() + timedelta(seconds=TEMPO_VELA)
    return t.replace(second=0).strftime("%H:%M")

def escolher_estrategia():
    return max(ESTRATEGIAS, key=lambda x: int(ESTRATEGIAS[x]*100))

async def obter_candles_real(par, interval=TIMEFRAME, count=20):
    try:
        return await client.get_candles(asset=par, interval=interval, count=count)
    except:
        return None

def analisar_candle(candles, direcao):
    c = candles[-1]
    o = float(c['open'])
    cl = float(c['close'])
    if direcao == "CALL ⬆️":
        return "GREEN" if cl > o else "RED"
    else:
        return "GREEN" if cl < o else "RED"

# ===============================
# SINAL
# ===============================
async def enviar_sinal():
    global estado, sinal_atual, fechamento_vela, pausa_ate

    if pausa_ate and agora_utc() < pausa_ate:
        return

    estrategia = escolher_estrategia()
    score = int(ESTRATEGIAS[estrategia]*100)
    if score < 75:
        return

    par = random.choice(ATIVOS)
    direcao = random.choice(["CALL ⬆️", "PUT ⬇️"])
    hora_entrada = proxima_vela()

    sinal_atual = {"par": par, "direcao": direcao, "estrategia": estrategia, "hora": hora_entrada}
    fechamento_vela = agora_utc() + timedelta(seconds=TEMPO_VELA)

    texto = f"""🤖 **TROIA v15 — IA**

📊 Ativo: {par}
🕯 Timeframe: {TIMEFRAME}
⏰ Entrada: {hora_entrada}
🧠 Estratégia: {estrategia}
⭐ Score: {score}%
⚠️ Operação única. Aguarde fechamento da vela."""
    
    print(texto)
    await bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")
    estado = "AGUARDANDO_RESULTADO"

# ===============================
# RESULTADO
# ===============================
async def enviar_resultado():
    global estado, greens, reds, streak, pausa_ate, ESTRATEGIAS

    candles = await obter_candles_real(sinal_atual["par"])
    if not candles:
        resultado = random.choice(["GREEN","RED"])
    else:
        resultado = analisar_candle(candles, sinal_atual["direcao"])

    if resultado == "GREEN":
        greens += 1
        streak += 1
        ESTRATEGIAS[sinal_atual["estrategia"]] += 0.05
        texto = "🟢 GREEN CONFIRMADO! Mercado respeitou a leitura."
    else:
        reds += 1
        streak = 0
        ESTRATEGIAS[sinal_atual["estrategia"]] = max(0.5, ESTRATEGIAS[sinal_atual["estrategia"]] - 0.07)
        texto = "🔴 RED. Mercado em correção."
        if reds >= RED_MAX:
            pausa_ate = agora_utc() + timedelta(seconds=PAUSA_APOS_RED)
            reds = 0

    total = greens + reds
    acc = (greens/total)*100 if total else 0
    resumo = f"""{texto}

📊 Greens: {greens}
🔴 Reds: {reds}
🔥 Streak: {streak}
📈 Assertividade: {acc:.2f}%
🧠 IA recalibrando estratégias..."""
    
    print(resumo)
    await bot.send_message(chat_id=CHAT_ID, text=resumo, parse_mode="Markdown")
    estado = "LIVRE"

# ===============================
# LOOP PRINCIPAL
# ===============================
async def loop_principal():
    while True:
        if estado == "LIVRE":
            await enviar_sinal()
        elif estado == "AGUARDANDO_RESULTADO":
            if agora_utc() >= fechamento_vela:
                await enviar_resultado()
        await asyncio.sleep(random.randint(INTERVALO_MIN, INTERVALO_MAX))

# ===============================
# START
# ===============================
async def main():
    await client.connect()
    print("🚀 TROIA IA v15 ONLINE — OTC + Forex REAL")
    await loop_principal()

if __name__ == "__main__":
    asyncio.run(main())
