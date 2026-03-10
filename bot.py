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


def analisar_alertas(daily, idx):
    alertas = []
    prob_chuva = daily["precipitation_probability_max"][idx]
    chuva_mm = daily["precipitation_sum"][idx]
    vento_max = daily["windspeed_10m_max"][idx]
    rajada_max = daily["windgusts_10m_max"][idx]
    code = daily["weathercode"][idx]

    if prob_chuva >= 70 and chuva_mm >= 10:
        alertas.append(f"🌧️ *CHUVA SIGNIFICATIVA* — {chuva_mm:.1f}mm esperados ({prob_chuva}% de chance)")
    elif prob_chuva >= 50:
        alertas.append(f"🌦️ *Possibilidade de chuva* — {prob_chuva}% de chance ({chuva_mm:.1f}mm)")

    if rajada_max >= 60:
        alertas.append(f"💨 *VENTO FORTE* — rajadas de até {rajada_max:.0f} km/h (vento médio {vento_max:.0f} km/h)")
    elif vento_max >= 40:
        alertas.append(f"🌬️ *Vento moderado* — até {vento_max:.0f} km/h")

    if code in [95, 96, 99]:
        alertas.append("⛈️ *ALERTA DE TEMPESTADE*")

    return alertas


def montar_mensagem(data):
    daily = data["daily"]
    hoje = datetime.now()

    msg = "🏖️ *Previsão do Tempo — Torres, RS*\n"
    msg += f"📅 {hoje.strftime('%d/%m/%Y às %H:%M')}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"

    code = daily["weathercode"][0]
    t_max = daily["temperature_2m_max"][0]
    t_min = daily["temperature_2m_min"][0]
    prob_chuva = daily["precipitation_probability_max"][0]
    chuva_mm = daily["precipitation_sum"][0]
    vento = daily["windspeed_10m_max"][0]
    rajada = daily["windgusts_10m_max"][0]

    emoji = weather_emoji(code)
    desc = weather_desc(code)

    msg += f"{emoji} *Hoje — {hoje.strftime('%d/%m')}*\n"
    msg += f"   🌡️ {t_min:.0f}°C – {t_max:.0f}°C\n"
    msg += f"   ☁️ {desc}\n"
    msg += f"   🌧️ Chuva: {prob_chuva}% chance / {chuva_mm:.1f}mm\n"
    msg += f"   💨 Vento: {vento:.0f} km/h (rajadas {rajada:.0f} km/h)\n"

    alertas = analisar_alertas(daily, 0)
    if alertas:
        msg += f"\n   ⚠️ *Alertas:*\n"
        for a in alertas:
            msg += f"      • {a}\n"
        msg += "\n━━━━━━━━━━━━━━━━━━━━\n"
        msg += "⚠️ *Fique atento aos alertas acima!*\n"

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
