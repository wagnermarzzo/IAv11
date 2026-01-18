import asyncio
import random
from datetime import datetime, timedelta, timezone
from telegram import Bot
import requests

# ===============================
# CONFIGURAÇÃO
# ===============================

TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"  # SEU TOKEN AQUI
CHAT_ID = 2055716345  # SEU CHAT ID AQUI
ALPHA_KEY = "3SYERLAJ3ZAT69TM"

INTERVALO_MIN = 180  # 3 minutos
INTERVALO_MAX = 300  # 5 minutos
TIMEFRAME = "1min"
ULTIMAS_VELAS = 20

# Lista completa de pares
ATIVOS = [
    "AUDCAD","AUDCHF","AUDJPY","AUDNZD","AUDSGD","AUDUSD",
    "CADCHF","CADJPY",
    "CHFJPY","CHFNOK","CHFSGD",
    "EURAUD","EURCAD","EURCHF","EURGBP","EURJPY","EURNOK","EURNZD","EURSGD","EURUSD","EURZAR",
    "GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPSGD","GBPUSD",
    "NOKJPY",
    "NZDCAD","NZDCHF","NZDJPY","NZDSGD","NZDUSD",
    "SGDJPY",
    "USDBRL","USDCAD","USDCHF","USDDKK","USDHKD","USDJPY","USDMXN","USDSGD","USDTHB","USDZAR"
]

bot = Bot(token=TOKEN)

# ===============================
# HISTÓRICO DE ESTUDO
# ===============================

historico = {}  # {ativo: [{"sinal": ..., "hora": ..., "resultado": ...}, ...] }
score_estrategia = {}  # {ativo: score}

# Inicializa scores
for ativo in ATIVOS:
    score_estrategia[ativo] = 1.0
    historico[ativo] = []

# ===============================
# FUNÇÕES DE ANÁLISE
# ===============================

def pegar_velas(ativo, interval=TIMEFRAME, count=ULTIMAS_VELAS):
    """Pega as últimas velas do ativo da Alpha Vantage"""
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ativo}&interval={interval}&outputsize=compact&apikey={ALPHA_KEY}"
    try:
        resp = requests.get(url, timeout=10).json()
        key = f"Time Series ({interval})"
        if key in resp:
            velas = list(resp[key].values())[:count][::-1]
            return velas
    except Exception as e:
        print(f"Erro ao pegar velas {ativo}: {e}")
    return []

def analisar_velas(velas):
    """Analisa sequência de velas e retorna sinal e score"""
    sequencia = []
    for v in velas:
        open_price = float(v["1. open"])
        close_price = float(v["4. close"])
        if close_price > open_price:
            sequencia.append("GREEN")
        elif close_price < open_price:
            sequencia.append("RED")
        else:
            sequencia.append("DOJI")
    # Últimas 3 velas
    if len(sequencia) >= 3:
        ult3 = sequencia[-3:]
        if ult3.count("GREEN") == 3:
            return "CALL ⬆️", 95
        elif ult3.count("RED") == 3:
            return "PUT ⬇️", 95
    # Últimas 2 velas
    if len(sequencia) >= 2:
        ult2 = sequencia[-2:]
        if ult2.count("GREEN") == 2:
            return "CALL ⬆️", 80
        elif ult2.count("RED") == 2:
            return "PUT ⬇️", 80
    # Tendência geral
    greens = sequencia.count("GREEN")
    reds = sequencia.count("RED")
    if greens > reds:
        return "CALL ⬆️", 60
    elif reds > greens:
        return "PUT ⬇️", 60
    else:
        return "NEUTRO", 50

def resultado_entrada(velas, sinal):
    """Verifica se a última vela confirma o sinal"""
    ultima = velas[-1]
    open_price = float(ultima["1. open"])
    close_price = float(ultima["4. close"])
    if sinal == "CALL ⬆️":
        return "GREEN" if close_price > open_price else "RED"
    elif sinal == "PUT ⬇️":
        return "GREEN" if close_price < open_price else "RED"
    return "NEUTRO"

async def enviar_telegram(texto):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=texto)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

# ===============================
# FUNÇÃO DASHBOARD
# ===============================

async def enviar_dashboard():
    texto = "📊 **TROIA v15 — Dashboard IA**\n\n"
    for ativo in ATIVOS:
        greens = sum(1 for h in historico[ativo] if h["resultado"] == "GREEN")
        reds = sum(1 for h in historico[ativo] if h["resultado"] == "RED")
        streak = 0
        if historico[ativo]:
            for h in reversed(historico[ativo]):
                if h["resultado"] == "GREEN":
                    streak += 1
                else:
                    break
        texto += f"{ativo} | Score: {score_estrategia[ativo]:.2f} | 🟢 {greens} | 🔴 {reds} | Streak: {streak}\n"
    await enviar_telegram(texto)

# ===============================
# LOOP PRINCIPAL
# ===============================

async def main():
    print("🚀 TROIA v15 IA ONLINE — Estudo automático ativado")
    contador_dashboard = 0
    while True:
        for ativo in ATIVOS:
            velas = pegar_velas(ativo)
            if velas:
                sinal, score = analisar_velas(velas)
                hora_entrada = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

                if sinal != "NEUTRO":
                    texto = (
                        f"🤖 **TROIA v15 — IA**\n\n
