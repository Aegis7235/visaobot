import requests
import os
from datetime import datetime

# Config
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Torres, RS — coordenadas
LAT = -29.3347
LON = -49.7256


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
        alertas.append(f"🌧️ *CHUVA FORTE* {nome} — {periodo['chuva_mm']:.1f}mm ({periodo['chuva_prob']}%)")
    elif periodo["chuva_prob"] >= 50:
        alertas.append(f"🌦️ *Chuva possível* {nome} — {periodo['chuva_prob']}% de chance")
    if periodo["rajada_max"] >= 60:
        alertas.append(f"💨 *VENTO FORTE* {nome} — rajadas de {periodo['rajada_max']:.0f} km/h")
    if periodo["code"] in [95, 96, 99]:
        alertas.append(f"⛈️ *TEMPESTADE* {nome}")
    return alertas


def montar_mensagem(data):
    hourly = data["hourly"]
    daily = data["daily"]
    hoje = datetime.now()

    periodos = {
        "🌅 Madrugada (00h–06h)": list(range(0, 6)),
        "🌄 Manhã (06h–12h)":     list(range(6, 12)),
        "☀️ Tarde (12h–18h)":     list(range(12, 18)),
        "🌙 Noite (18h–00h)":     list(range(18, 24)),
    }

    t_max = daily["temperature_2m_max"][0]
    t_min = daily["temperature_2m_min"][0]
    code_dia = daily["weathercode"][0]
    emoji_dia = weather_emoji(code_dia)
    desc_dia = weather_desc(code_dia)

    msg = "🏖️ *Previsão do Tempo — Torres, RS*\n"
    msg += f"📅 {hoje.strftime('%d/%m/%Y às %H:%M')}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"{emoji_dia} *Hoje — {hoje.strftime('%d/%m')}*\n"
    msg += f"   🌡️ {t_min:.0f}°C – {t_max:.0f}°C  |  {desc_dia}\n\n"

    todos_alertas = []

    for nome, indices in periodos.items():
        p = resumo_periodo(hourly, indices)
        emoji = weather_emoji(p["code"])
        desc = weather_desc(p["code"])
        nome_curto = nome.split("(")[0].strip().split(" ", 1)[1].strip()

        msg += f"{nome}\n"
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


if __name__ == "__main__":
    print("🔍 Buscando previsão do tempo para Torres, RS...")
    data = get_previsao()
    msg = montar_mensagem(data)
    print(msg)
    enviar_telegram(msg)
