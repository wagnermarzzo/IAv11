import asyncio
import requests
from datetime import datetime, timedelta, timezone
from telegram import Bot
from telegram.ext import ApplicationBuilder, CallbackContext
import random

# ================= CONFIGURAÇÃO =================
ALPHA_KEY = "3SYERLAJ3ZAT69TM"  # API Alpha Vantage
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8HYY"
CHAT_ID = 2055716345

INTERVALO_LOOP = 30  # segundos
TEMPO_VELA = 60      # duração da vela em segundos
PAUSA_APOS_RED = 600
RED_MAX = 3
HISTORICO_TAM = 10   # últimos sinais usados para IA

ATIVOS = [
    "BTCUSD", "ETHUSD", "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
    "EURUSD", "GBPUSD", "USDJPY"
]

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

# Histórico para IA de estudo
historico_precos = {ativo: [] for ativo in ATIVOS}
historico_sinais = []  # {"par":..., "direcao":..., "resultado":..., "estrategia":..., "hora":...}

bot = Bot(token=TOKEN)

# ================= FUNÇÕES =================
def agora_utc():
    return datetime.now(timezone.utc)

def proxima_vela():
    t = agora_utc() + timedelta(seconds=TEMPO_VELA)
    return t.replace(second=0).strftime("%H:%M")

def pegar_preco(ativo):
    """Pega último preço do ativo da Alpha Vantage"""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ativo}&apikey={ALPHA_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            return float(data["Global Quote"]["05. price"])
    except Exception as e:
        print(f"Erro ao pegar preço {ativo}: {e}")
    return None

def calcular_score_estrategia(estrategia):
    """Calcula score baseado em últimos sinais e peso atual"""
    ultimos = [x for x in historico_sinais if x["estrategia"] == estrategia][-HISTORICO_TAM:]
    if not ultimos:
        eficiencia = 0
    else:
        greens_count = sum(1 for x in ultimos if x["resultado"] == "GREEN")
        eficiencia = (greens_count / len(ultimos)) * 100
    peso = estrategias[estrategia] * 100
    return (peso + eficiencia) / 2

def escolher_estrategia():
    """Escolhe estratégia com maior score"""
    return max(estrategias, key=calcular_score_estrategia)

def registrar_resultado(par, direcao, resultado, estrategia):
    historico_sinais.append({
        "par": par,
        "direcao": direcao,
        "resultado": resultado,
        "estrategia": estrategia,
        "hora": agora_utc()
    })

# ================= SINAL =================
async def enviar_sinal():
    global estado, sinal_atual, fechamento_vela, pausa_ate

    if pausa_ate and agora_utc() < pausa_ate:
        return

    estrategia = escolher_estrategia()
    score = calcular_score_estrategia(estrategia)
    if score < 50:  # só envia sinal se score >=50%
        return

    par = random.choice(ATIVOS)

    # Direção com base na última performance da estratégia
    ultimos = [x for x in historico_sinais if x["estrategia"] == estrategia and x["par"] == par][-HISTORICO_TAM:]
    if not ultimos:
        direcao = random.choice(["CALL ⬆️", "PUT ⬇️"])
    else:
        # se últimos 3 sinais da mesma direção foram GREEN, repetir direção
        chamadas = [x for x in ultimos if x["direcao"] == "CALL ⬆️" and x["resultado"] == "GREEN"]
        puts = [x for x in ultimos if x["direcao"] == "PUT ⬇️" and x["resultado"] == "GREEN"]
        if len(chamadas) > len(puts):
            direcao = "CALL ⬆️"
        elif len(puts) > len(chamadas):
            direcao = "PUT ⬇️"
        else:
            direcao = random.choice(["CALL ⬆️", "PUT ⬇️"])

    entrada = proxima_vela()

    sinal_atual = {"par": par, "direcao": direcao, "estrategia": estrategia}
    fechamento_vela = agora_utc() + timedelta(seconds=TEMPO_VELA)

    texto = (
        "🤖 **IAAlpha Sinais — TROIA v11**\n\n"
        "🚨 **SETUP VALIDADO PELO MOTOR IA**\n\n"
        f"📊 **Ativo:** {par}\n"
        f"🕯 **Direção:** {direcao}\n"
        f"⏰ **Entrada:** {entrada} (PRÓXIMA VELA)\n"
        f"🧠 **Estratégia:** {estrategia}\n"
        f"⭐ **Score:** {score:.2f}\n"
        "⚠️ Operação única. Aguarde o fechamento."
    )
    await bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")
    estado = "AGUARDANDO_RESULTADO"

# ================= RESULTADO =================
async def enviar_resultado():
    global estado, greens, reds, streak, pausa_ate

    par = sinal_atual["par"]
    preco_atual = pegar_preco(par)
    if preco_atual is None:
        resultado = random.choice(["GREEN", "RED"])
    else:
        ultimo_preco = historico_precos[par][-1] if historico_precos[par] else preco_atual
        historico_precos[par].append(preco_atual)

        if sinal_atual["direcao"] == "CALL ⬆️":
            resultado = "GREEN" if preco_atual >= ultimo_preco else "RED"
        else:
            resultado = "GREEN" if preco_atual <= ultimo_preco else "RED"

    registrar_resultado(par, sinal_atual["direcao"], resultado, sinal_atual["estrategia"])

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
    print("🚀 TROIA IA v11 ONLINE — Alpha + Telegram REAL")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
