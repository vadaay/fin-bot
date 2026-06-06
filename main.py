import os
import requests
from datetime import datetime

def get_crypto():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    return requests.get(url, params=params).json()

def signal(change):
    if change > 2:
        return "🟢 Рост"
    elif change > 0:
        return "📈 Плюс"
    elif change > -2:
        return "🔴 Минус"
    else:
        return "📉 Сильное падение"

def send_post():
    # 🔑 БЕРЁМ ТОКЕН ИЗ GITHUB SECRETS
    token = os.environ["8807568809:AAFuPcm0m84g4eGV5-nagVS6RyxOKL7HmtM"]
    channel = "@crypto-x-news"

    data = get_crypto()

    btc = data["bitcoin"]["usd"]
    btc_ch = data["bitcoin"]["usd_24h_change"]

    eth = data["ethereum"]["usd"]
    eth_ch = data["ethereum"]["usd_24h_change"]

    text = (
        f"📊 Крипто-рынок • {datetime.now().strftime('%d.%m.%Y')}\n\n"
        f"₿ BTC: ${btc} ({btc_ch:.2f}%) {signal(btc_ch)}\n"
        f"Ξ ETH: ${eth} ({eth_ch:.2f}%) {signal(eth_ch)}\n\n"
        "📌 Не инвестируйте на эмоциях"
    )

    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": channel, "text": text}
    )

if __name__ == "__main__":
    send_post()
