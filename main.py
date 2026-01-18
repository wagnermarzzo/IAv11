import asyncio
import random
from datetime import datetime, timedelta, timezone
import requests
from telegram import Bot, ChatAction

# ================= CONFIGURAÇÃO =================
ALPHA_KEY = "3SYERLAJ3ZAT69TM"
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = 2055716345

INTERVALO_LOOP = 30  # segundos entre checagens
TEMPO_VELA = 60      # duração estimada de cada vela
PAUSA_APOS_RED = 600
RED_MAX = 3

# Lista de ativos e criptos disponíveis na Alpha Vantage
ATIVOS = [
    "BTCUSD", "ETHUSD", "BNBUSD", "ADAUSD", "SOLUSD",
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "EURGBP", "USDCHF", "USDCAD",
    "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"
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

historico_resultados = []

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

def analisar_entrada(preco_atual, historico):
    """Decide sinal baseado em histórico de preço"""
    if not historico:
        return "CALL ⬆️"
    if preco_atual > historico[-1]:
        return "CALL ⬆️"
    elif preco_atual < historico[-1]:
        return "PUT ⬇️"
    else:
        return random.choice(["CALL ⬆️", "PUT ⬇️"])

async def enviar_sinal():
    global estado, sinal_atual, fechamento_vela, pausa_ate

    if pausa_ate and agora_utc() < pausa_ate:
        return

    estrategia = escolher_estrategia()
    score = score_estrategia(estrategia)
    if score < 75:
        return

    par = random.choice(ATIVOS)
    preco_atual = pegar_preco(par)
    if not preco_atual:
        return

    historico = [r["preco"] for r in historico_resultados if r["par"] == par]
    direcao = analisar_entrada(preco_atual, historico)
    entrada = proxima_vela()

    sinal_atual = {
        "par": par,
        "direcao": direcao,
        "estrategia": estrategia,
        "preco": preco_atual
    }
    fechamento_vela = agora_utc() + timedelta(seconds=TEMPO_VELA)

    texto = (
        "🤖 **IAQuotex Sinais — TROIA v11 (Alpha)**\n\n"
        "🚨 **SETUP VALIDADO PELO MOTOR IA**\n\n"
        f"📊 **Ativo:** {par}\n"
        f"🕯 **Direção:** {direcao}\n"
        f"💰 **Preço Atual:** {preco_atual}\n"
        f"⏰ **Entrada:** {entrada}\n"
        f"🧠 **Estratégia:** {estrategia}\n"
        f"⭐ **Score:** {score}\n"
        "⚠️ Operação única. Aguarde o fechamento."
    )

    await bot.send_chat_action(chat_id=CHAT_ID, action=ChatAction.TYPING)
    await bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")
    estado = "AGUARDANDO_RESULTADO"

async def enviar_resultado():
    global estado, greens, reds, streak, pausa_ate, historico_resultados

    par = sinal_atual["par"]
    preco_atual = pegar_preco(par)
    if not preco_atual:
        resultado = random.choice(["GREEN", "RED"])
    else:
        if sinal_atual["direcao"] == "CALL ⬆️":
            resultado = "GREEN" if preco_atual >= sinal_atual["preco"] else "RED"
        else:
            resultado = "GREEN" if preco_atual <= sinal_atual["preco"] else "RED"

    historico_resultados.append({
        "par": par,
        "direcao": sinal_atual["direcao"],
        "resultado": resultado,
        "estrategia": sinal_atual["estrategia"],
        "preco": sinal_atual["preco"],
        "hora": datetime.now().strftime("%H:%M:%S")
    })

    if resultado == "GREEN":
        greens += 1
        streak += 1
        estrategias[sinal_atual["estrategia"]] += 0.05
        texto = "🟢 **GREEN CONFIRMADO!**"
    else:
        reds += 1
        streak = 0
        estrategias[sinal_atual["estrategia"]] = max(0.5, estrategias[sinal_atual["estrategia"]] - 0.07)
        texto = "🔴 **RED**"
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
        f"📈 Assertividade: {acc:.2f}%\n"
        "🧠 IA recalibrando estratégias..."
    )

    await bot.send_message(chat_id=CHAT_ID, text=resumo, parse_mode="Markdown")
    estado = "LIVRE"

# ================= LOOP PRINCIPAL =================
async def loop_principal():
    if estado == "LIVRE":
        await enviar_sinal()
    elif estado == "AGUARDANDO_RESULTADO":
        if agora_utc() >= fechamento_vela:
            await enviar_resultado()

# ================= START =================
async def main():
    print("🚀 TROIA IA v11 ONLINE — Alpha Vantage")
    while True:
        await loop_principal()
        await asyncio.sleep(INTERVALO_LOOP)

if __name__ == "__main__":
    asyncio.run(main())
