import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =========================
# HTTP CLIENT (REUSABLE)
# =========================
def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = create_session()


def safe_get(url: str, params=None, timeout=10) -> Optional[Dict[str, Any]]:
    try:
        r = SESSION.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ GET error {url}: {e}")
        return None


def safe_post(url: str, data=None, json_data=None, timeout=10) -> Optional[Dict[str, Any]]:
    try:
        r = SESSION.post(url, data=data, json=json_data, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ POST error {url}: {e}")
        return None


# =========================
# DATA PROVIDERS
# =========================
def get_crypto():
    return safe_get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
        },
    )


def get_fear_greed_index():
    data = safe_get("https://api.alternative.me/fng/", params={"limit": 1})
    return data["data"][0] if data and "data" in data else None


def get_financial_news():
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return []

    data = safe_get(
        "https://newsapi.org/v2/everything",
        params={
            "q": "ставка OR инфляция OR биткоин OR криптовалюта OR фрс",
            "language": "ru",
            "sortBy": "publishedAt",
            "pageSize": 5,
            "apiKey": api_key,
        },
    )
    return data.get("articles", []) if data else []


def get_economic_calendar():
    return {
        "ФРС": "Решение по ставке: 12.06.2024",
        "ЕЦБ": "Решение по ставке: 06.06.2024",
        "Данные CPI": "Инфляция США: ежемесячно",
        "Non-Farm": "Занятость США: первая пятница месяца",
    }


# =========================
# ANALYTICS
# =========================
def signal(change: float) -> str:
    return (
        "🟢 Сильный рост" if change > 5 else
        "🟢 Рост" if change > 2 else
        "📈 Плюс" if change > 0 else
        "🔴 Минус" if change > -2 else
        "📉 Падение" if change > -5 else
        "🔻 Сильное падение"
    )


def market_sentiment(change: float) -> str:
    return (
        "🟢 Жадность" if change > 5 else
        "🟡 Оптимизм" if change > 2 else
        "⚪ Нейтрально" if change > 0 else
        "🟠 Страх" if change > -5 else
        "🔴 Сильный страх"
    )


# =========================
# CHARTS
# =========================
def create_price_chart(coin_id: str, name: str, color: str) -> Optional[str]:
    data = safe_get(
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
        params={"vs_currency": "usd", "days": 7},
        timeout=15,
    )

    if not data or "prices" not in data:
        return None

    prices = data["prices"]
    step = max(len(prices) // 20, 1)

    labels, values = [], []

    for i in range(0, len(prices), step):
        ts, price = prices[i]
        dt = datetime.fromtimestamp(ts / 1000)
        labels.append(dt.strftime("%d.%m"))
        values.append(round(price))

    chart = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": f"{name} USD",
                "data": values,
                "borderColor": color,
                "fill": True,
                "tension": 0.3,
                "pointRadius": 0,
            }],
        },
    }

    return (
        "https://quickchart.io/chart"
        f"?c={json.dumps(chart)}&width=600&height=350"
    )


def create_fear_greed_gauge(value: int, label: str) -> str:
    color = "#ef5350" if value < 25 else "#ff9800" if value < 45 else "#8bc34a"

    chart = {
        "type": "radialGauge",
        "data": {"datasets": [{"data": [value], "backgroundColor": color}]},
    }

    return (
        "https://quickchart.io/chart"
        f"?c={json.dumps(chart)}&width=400&height=350"
    )


# =========================
# TELEGRAM
# =========================
def tg_send_message(token: str, chat: str, text: str) -> bool:
    res = safe_post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json_data={
            "chat_id": chat,
            "text": text,
            "parse_mode": "HTML",
        },
    )
    return bool(res and res.get("ok"))


def tg_send_photo(token: str, chat: str, photo: str, caption: str) -> bool:
    res = safe_post(
        f"https://api.telegram.org/bot{token}/sendPhoto",
        json_data={
            "chat_id": chat,
            "photo": photo,
            "caption": caption,
            "parse_mode": "HTML",
        },
    )
    return bool(res and res.get("ok"))


def tg_send_album(token: str, chat: str, items: List[Tuple[str, str]]) -> bool:
    media = [
        {"type": "photo", "media": url, "caption": cap}
        for url, cap in items
    ]

    res = safe_post(
        f"https://api.telegram.org/bot{token}/sendMediaGroup",
        data={"chat_id": chat, "media": json.dumps(media)},
    )

    return bool(res and res.get("ok"))


# =========================
# MAIN POST
# =========================
def send_post():
    token = os.getenv("BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHANNEL", "@finanis")

    if not token:
        print("❌ BOT_TOKEN missing")
        return False

    crypto = get_crypto()
    fg = get_fear_greed_index()

    if not crypto:
        print("❌ No crypto data")
        return False

    btc = crypto["bitcoin"]["usd"]
    btc_ch = crypto["bitcoin"]["usd_24h_change"]
    eth = crypto["ethereum"]["usd"]
    eth_ch = crypto["ethereum"]["usd_24h_change"]

    now = datetime.now()

    # ===== POST 1 =====
    if fg:
        value = int(fg["value"])
        label = fg["value_classification"]

        gauge = create_fear_greed_gauge(value, label)

        msg = (
            f"📊 <b>Крипто рынок</b>\n"
            f"{now:%d.%m.%Y %H:%M}\n\n"
            f"🎭 {value}/100 — {label}\n"
            f"🌡 {market_sentiment(btc_ch)}"
        )

        tg_send_photo(token, chat, gauge, msg)
    else:
        tg_send_message(token, chat, "Нет индекса F&G")

    # ===== POST 2 =====
    btc_chart = create_price_chart("bitcoin", "Bitcoin", "#f7931a")
    eth_chart = create_price_chart("ethereum", "Ethereum", "#627eea")

    if btc_chart and eth_chart:
        tg_send_album(token, chat, [
            (btc_chart, f"BTC ${btc:,.0f} {btc_ch:+.2f}%"),
            (eth_chart, f"ETH ${eth:,.0f} {eth_ch:+.2f}%"),
        ])

    # ===== POST 3 =====
    news = get_financial_news()
    events = get_economic_calendar()

    text = "📅 <b>События</b>\n\n"
    text += "\n".join([f"• {k}: {v}" for k, v in events.items()])

    if news:
        text += "\n\n📰 <b>Новости</b>\n"
        for a in news[:3]:
            text += f"• {a.get('title','')}\n"

    tg_send_message(token, chat, text)

    print("✅ Done")
    return True


if __name__ == "__main__":
    send_post()
