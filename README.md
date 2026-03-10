# 🏖️ Torres Clima Bot

Bot do Telegram que envia previsão do tempo diária para Torres, RS — com alertas de chuva, vento forte e tempestade.

## ⚙️ Como funciona

- Roda automaticamente via **GitHub Actions** (sem servidor)
- Busca dados na **Open-Meteo API** (gratuita, sem cadastro)
- Envia mensagem no **Telegram** 2x por dia: 7h e 18h
- Pode ser disparado manualmente a qualquer hora

## 🔔 Alertas

| Condição | Gatilho |
|----------|---------|
| 🌦️ Possibilidade de chuva | ≥ 50% de chance |
| 🌧️ Chuva significativa | ≥ 70% chance e ≥ 10mm |
| 🌬️ Vento moderado | vento médio ≥ 40 km/h |
| 💨 Vento forte | rajadas ≥ 60 km/h |
| ⛈️ Tempestade | código meteorológico de tempestade |

## 🔑 Secrets necessários

Configure em **Settings → Secrets and variables → Actions**:

| Secret | Descrição |
|--------|-----------|
| `TELEGRAM_TOKEN` | Token do bot gerado pelo @BotFather |
| `TELEGRAM_CHAT_ID` | Seu chat ID numérico do Telegram |

## 🚀 Como obter o Chat ID

1. Crie o bot no @BotFather e guarde o token
2. Inicie uma conversa com seu bot no Telegram
3. Acesse: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
4. Copie o valor de `"chat":{"id": XXXXXXX}`

## 📁 Estrutura

```
torres-clima-bot/
├── .github/
│   └── workflows/
│       └── clima.yml   # Cronjob GitHub Actions
├── bot.py              # Script principal
├── requirements.txt    # Dependências Python
└── README.md
```
