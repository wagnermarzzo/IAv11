import asyncio
import random
from datetime import datetime

class Quotex:
    def __init__(self):
        # Credenciais já inseridas
        self.email = "apgwagner2@gmail.com"
        self.senha = "@Aa88691553"
        self.conectado = False

    async def connect(self):
        # Conecta à API (simulado aqui)
        print(f"Conectando à conta Quotex: {self.email}")
        await asyncio.sleep(1)  # simula delay de login
        self.conectado = True
        print("Conectado à Quotex!")

    def get_candles(self, asset, interval, count):
        if not self.conectado:
            raise Exception("Não conectado à conta Quotex")
        
        # Retorno fake de candles para teste Railway
        now = datetime.utcnow()
        candles = []
        for _ in range(count):
            o = random.uniform(1.0, 2.0)
            c = o + random.uniform(-0.05, 0.05)
            candles.append({
                "open": o,
                "close": c,
                "timestamp": now.timestamp()
            })
        return candles
