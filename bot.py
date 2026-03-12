import requests
import os
import sys
from datetime import datetime, timezone, timedelta

# Config
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Torres, RS — coordenadas
LAT = -29.3347
LON = -49.7256

# Limites para alerta urgente
LIMITE_RAJADA_URGENTE = 60    # km/h
LIMITE_CHUVA_PROB = 80        # %
LIMITE_CHUVA_MM = 10          # mm nas próximas 3h

# Arquivo de controle anti-spam
ARQUIVO_ULTIMO_ALERTA = "ultimo_alerta.txt"


def get_previsao():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": [
            "temperature_2m",
            "precipitation_probability",
            "precipitation",
            "windspeed_10m",
            "windgusts_10m",
            "weathercode"
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "windspeed_10m_max",
            "windgusts_10m_max",
            "precipitation_probability_max",
            "weathercode"
        ],
        "timezone": "America/Sao_Paulo",
        "forecast_days": 1
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()


def weather_emoji(code):
    if code == 0:
        return "☀️"
    elif code in [1, 2]:
        return "🌤️"
    elif code == 3:
        return "☁️"
    elif code in [45, 48]:
        return "🌫️"
    elif code in [51, 53, 55]:
        return "🌦️"
    elif code in [61, 63, 65]:
        return "🌧️"
    elif code in [71, 73, 75]:
        return "❄️"
    elif code in [80, 81, 82]:
        return "🌧️"
    elif code in [95, 96, 99]:
        return "⛈️"
    else:
        return "🌡️"


def weather_desc(code):
    descs = {
        0: "Céu limpo",
        1: "Principalmente limpo",
        2: "Parcialmente nublado",
        3: "Nublado",
        45: "Neblina",
        48: "Neblina com geada",
        51: "Garoa leve",
        53: "Garoa moderada",
        55: "Garoa intensa",
        61: "Chuva leve",
        63: "Chuva moderada",
        65: "Chuva forte",
        71: "Neve leve",
        73: "Neve moderada",
        75: "Neve forte",
        80: "Pancadas de chuva leve",
        81: "Pancadas moderadas",
        82: "Pancadas fortes",
        95: "Tempestade",
        96: "Tempestade com granizo leve",
        99: "Tempestade com granizo"
    }
    return descs.get(code, "Condição desconhecida")


def resumo_periodo(hourly, indices):
    chuva_prob = max(hourly["precipitation_probability"][i] for i in indices)
    chuva_mm = sum(hourly["precipitation"][i] for i in indices)
    vento_max = max(hourly["windspeed_10m"][i] for i in indices)
    rajada_max = max(hourly["windgusts_10m"][i] for i in indices)
    temp_vals = [hourly["temperature_2m"][i] for i in indices]
    codes = [hourly["weathercode"][i] for i in indices]
    return {
        "chuva_prob": chuva_prob,
        "chuva_mm": chuva_mm,
        "vento_max": vento_max,
        "rajada_max": rajada_max,
        "temp_min": min(temp_vals),
        "temp_max": max(temp_vals),
        "code": max(codes)
    }


def alertas_periodo(periodo, nome):
    alertas = []
    if periodo["chuva_prob"] >= 70 and periodo["chuva_mm"] >= 5:
        alertas.append(f"🌧️ *Chance de chuva forte* {nome} — {periodo['chuva_mm']:.1f}mm ({periodo['chuva_prob']}%)")
    elif periodo["chuva_prob"] >= 50:
        alertas.append(f"🌦️ *Chuva possível* {nome} — {periodo['chuva_prob']}% de chance")
    if periodo["rajada_max"] >= 60:
        alertas.append(f"💨 *Chance de vento forte* {nome} — rajadas de até {periodo['rajada_max']:.0f} km/h")
    if periodo["code"] in [95, 96, 99]:
        alertas.append(f"⛈️ *Chance de tempestade* {nome}")
    return alertas


def montar_mensagem(data):
    hourly = data["hourly"]
    daily = data["daily"]
    hoje = datetime.now(timezone(timedelta(hours=-3)))

    periodos = {
        "🌅 *〔 MADRUGADA 〕* 00h – 06h": list(range(0, 6)),
        "🌄 *〔 MANHÃ 〕* 06h – 12h":     list(range(6, 12)),
        "☀️ *〔 TARDE 〕* 12h – 18h":     list(range(12, 18)),
        "🌙 *〔 NOITE 〕* 18h – 00h":     list(range(18, 24)),
    }

    t_max = daily["temperature_2m_max"][0]
    t_min = daily["temperature_2m_min"][0]
    code_dia = daily["weathercode"][0]
    emoji_dia = weather_emoji(code_dia)
    desc_dia = weather_desc(code_dia)

    dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    dia_semana = dias_semana[hoje.weekday()]

    msg = "🏖️ *Previsão: Torres, RS*\n"
    msg += f"📅 {dia_semana}, {hoje.strftime('%d/%m/%Y')}\n\n"
    msg += f"🌡️ {t_min:.0f}°C – {t_max:.0f}°C  |  {desc_dia}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"

    todos_alertas = []

    for nome, indices in periodos.items():
        p = resumo_periodo(hourly, indices)
        emoji = weather_emoji(p["code"])
        desc = weather_desc(p["code"])
        nome_curto = nome.split("(")[0].strip().split(" ", 1)[1].strip()

        msg += f"▸ {nome}\n"
        msg += f"   {emoji} {desc}\n"
        msg += f"   🌡️ {p['temp_min']:.0f}°C – {p['temp_max']:.0f}°C\n"
        msg += f"   🌧️ Chuva: {p['chuva_prob']}% / {p['chuva_mm']:.1f}mm\n"
        msg += f"   💨 Vento: {p['vento_max']:.0f} km/h (rajadas {p['rajada_max']:.0f} km/h)\n\n"

        todos_alertas += alertas_periodo(p, nome_curto)

    if todos_alertas:
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "⚠️ *ALERTAS DO DIA:*\n"
        for a in todos_alertas:
            msg += f"   • {a}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"

    msg += "\n_Fonte: Open-Meteo | Torres, RS_"
    return msg


# ─────────────────────────────────────────
# ALERTA URGENTE
# ─────────────────────────────────────────

def hora_atual_brt():
    brt = timezone(timedelta(hours=-3))
    return datetime.now(brt)


def ja_alertou_recentemente():
    """Verifica se já enviou alerta nas últimas 3 horas."""
    if not os.path.exists(ARQUIVO_ULTIMO_ALERTA):
        return False
    try:
        with open(ARQUIVO_ULTIMO_ALERTA, "r") as f:
            conteudo = f.read().strip()
        ultimo = datetime.fromisoformat(conteudo)
        ultimo = ultimo.replace(tzinfo=timezone(timedelta(hours=-3)))
        agora = hora_atual_brt()
        diff = agora - ultimo
        return diff.total_seconds() < 3 * 3600  # 3 horas
    except Exception:
        return False


def salvar_timestamp_alerta():
    agora = hora_atual_brt()
    with open(ARQUIVO_ULTIMO_ALERTA, "w") as f:
        f.write(agora.isoformat())


def verificar_alerta_urgente(data):
    """Olha as próximas 3 horas e detecta condições críticas."""
    hourly = data["hourly"]
    agora = hora_atual_brt()
    hora_atual = agora.hour

    # Próximas 3 horas
    indices = [hora_atual, hora_atual + 1, hora_atual + 2]
    indices = [i for i in indices if i < 24]

    problemas = []

    for i in indices:
        hora_str = hourly["time"][i][11:16]  # ex: "15:00"
        code = hourly["weathercode"][i]
        rajada = hourly["windgusts_10m"][i]
        chuva_prob = hourly["precipitation_probability"][i]
        chuva_mm = hourly["precipitation"][i]

        if code in [95, 96, 99]:
            problemas.append(f"   ⛈️ *Chance de tempestade* às {hora_str}")
        if rajada >= LIMITE_RAJADA_URGENTE:
            problemas.append(f"   💨 *Chance de vento forte* às {hora_str} — rajadas de até {rajada:.0f} km/h")
        if chuva_prob >= LIMITE_CHUVA_PROB and chuva_mm >= LIMITE_CHUVA_MM:
            problemas.append(f"   🌧️ *Chance de chuva forte* às {hora_str} — {chuva_mm:.1f}mm ({chuva_prob}%)")

    return problemas


def montar_mensagem_urgente(problemas):
    agora = hora_atual_brt()
    msg = "🚨 *ALERTA URGENTE — Torres, RS*\n"
    msg += f"📅 {agora.strftime('%d/%m/%Y às %H:%M')}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "⚠️ *Condição desfavorável prevista nas próximas horas:*\n\n"
    for p in problemas:
        msg += f"{p}\n"
    msg += "\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🟡 *Fique atento às condições do tempo!*\n"
    msg += "\n_Fonte: Open-Meteo | Torres, RS_"
    return msg


def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()
    print("✅ Mensagem enviada com sucesso!")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "resumo"

    print(f"🔍 Modo: {modo}")
    data = get_previsao()

    if modo == "resumo":
        # Resumo diário normal (7h e 18h)
        print("📋 Montando resumo diário...")
        msg = montar_mensagem(data)
        print(msg)
        enviar_telegram(msg)

    elif modo == "alerta":
        # Verificação de alerta urgente (a cada hora)
        print("🔎 Verificando condições críticas...")
        problemas = verificar_alerta_urgente(data)

        if not problemas:
            print("✅ Sem condições críticas nas próximas 3 horas.")
        elif ja_alertou_recentemente():
            print("⏸️ Alerta já enviado nas últimas 3 horas. Pulando.")
        else:
            print(f"🚨 {len(problemas)} problema(s) detectado(s)! Enviando alerta...")
            msg = montar_mensagem_urgente(problemas)
            print(msg)
            enviar_telegram(msg)
            salvar_timestamp_alerta()
