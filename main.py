import os
import requests
from datetime import datetime
import json
import random
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlunparse, quote

# ------------------- НАСТРОЙКИ -------------------
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # ваш ID для ошибок
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
TELEGRAM_API = "https://api.telegram.org/bot"

# ------------------- БАЗОВЫЕ ДАННЫЕ -------------------
def get_crypto():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_market_cap": "true"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        notify_admin(f"❌ CoinGecko simple: {e}")
        return None

def get_global_data():
    """Доминация BTC, общая капитализация"""
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        r.raise_for_status()
        return r.json()["data"]
    except Exception as e:
        notify_admin(f"❌ CoinGecko global: {e}")
        return None

def get_fear_greed_index():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        r.raise_for_status()
        return r.json()["data"][0]
    except:
        return None

def get_sp500():
    """S&P 500 через Alpha Vantage (бесплатный ключ)"""
    key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not key:
        return None
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=SPY&apikey={key}"
        r = requests.get(url, timeout=10)
        data = r.json().get("Global Quote", {})
        price = data.get("05. price")
        change_pct = data.get("10. change percent", "0%").replace("%", "")
        if price:
            return {"price": float(price), "change": float(change_pct)}
    except:
        return None

def get_top_coins():
    """Топ-10 монет по рыночной капитализации для тепловой карты"""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1},
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except:
        return []

# ------------------- НОВОСТИ (стабильные RSS) -------------------
def fetch_rss(url, source_name, limit=5):
    print(f"📡 {source_name}...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"   Статус: {r.status_code}")
            return []
        root = ET.fromstring(r.content)
        news = []
        for item in root.findall(".//item")[:limit]:
            title = item.find("title")
            link = item.find("link")
            desc = item.find("description")
            if title is None or link is None:
                continue
            title_text = title.text or ""
            link_text = link.text or ""
            if not title_text or not link_text:
                continue
            # текст
            html = desc.text if desc is not None else ""
            text = clean_html(html)
            # картинки
            images = extract_images_from_html(html)
            enc = item.find("enclosure")
            if enc is not None:
                img = enc.get("url", "")
                if img:
                    images.append(img)
            # иногда картинка в media:content
            media = item.find("{http://search.yahoo.com/mrss/}content")
            if media is not None:
                img = media.get("url", "")
                if img:
                    images.append(img)
            images = list(set(images))
            news.append({
                "title": title_text,
                "link": clean_url(link_text),
                "content": text,
                "images": images,
                "source": source_name
            })
        print(f"   ✅ {len(news)}")
        return news
    except Exception as e:
        print(f"   ❌ {e}")
        return []

def get_coindesk_news():
    return fetch_rss("https://www.coindesk.com/arc/outboundfeeds/feed/", "CoinDesk")

def get_decrypt_news():
    return fetch_rss("https://decrypt.co/feed", "Decrypt")

def get_theblock_news():
    return fetch_rss("https://www.theblock.co/rss/feed", "The Block")

def get_cryptopanic_news():
    return fetch_rss("https://cryptopanic.com/news/feed/?filter=all", "CryptoPanic")

def get_all_news():
    print("📰 СБОР НОВОСТЕЙ")
    all_news = []
    all_news.extend(get_coindesk_news())
    all_news.extend(get_decrypt_news())
    all_news.extend(get_theblock_news())
    if len(all_news) < 5:
        all_news.extend(get_cryptopanic_news())
    seen = set()
    unique = []
    for n in all_news:
        if n["title"] and n["title"] not in seen:
            seen.add(n["title"])
            unique.append(n)
    print(f"✅ Итого уникальных: {len(unique)}")
    return unique

# ------------------- ОЧИСТКА HTML -------------------
def clean_html(html):
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def extract_images_from_html(html):
    return re.findall(r'<img[^>]+src="([^"]+)"', html)

def clean_url(url):
    if not url:
        return url
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

# ------------------- ГРАФИКИ -------------------
def quickchart(config, w=600, h=350, bg="1a1a2e"):
    encoded = quote(json.dumps(config), safe='')
    return f"https://quickchart.io/chart?c={encoded}&width={w}&height={h}&backgroundColor=%23{bg}"

def create_price_chart(coin_id, coin_name, color):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
        data = requests.get(url, timeout=15).json()["prices"]
        step = max(len(data)//20, 1)
        labels, values = [], []
        for i in range(0, len(data), step):
            labels.append(datetime.fromtimestamp(data[i][0]/1000).strftime('%d.%m'))
            values.append(round(data[i][1]))
        config = {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "borderColor": color,
                    "backgroundColor": color + "33",
                    "borderWidth": 2, "fill": True, "tension": 0.3, "pointRadius": 0
                }]
            },
            "options": {
                "plugins": {
                    "title": {"display": True, "text": f"{coin_name} за 7 дней", "color": "#fff", "font": {"size": 16}},
                    "legend": {"display": False}
                },
                "scales": {
                    "y": {"ticks": {"color": "#ccc", "callback": "function(v){return '$'+v.toLocaleString()}"}, "grid": {"color": "#333"}},
                    "x": {"ticks": {"color": "#ccc"}, "grid": {"color": "#333"}}
                }
            }
        }
        return quickchart(config, 600, 300)
    except:
        return None

def create_fear_greed_gauge(value, classification):
    if value < 25: color = "#ef5350"
    elif value < 45: color = "#ff9800"
    elif value < 55: color = "#ffc107"
    elif value < 75: color = "#8bc34a"
    else: color = "#4caf50"
    config = {
        "type": "radialGauge",
        "data": {"datasets": [{"data": [value], "backgroundColor": color}]},
        "options": {
            "centerArea": {"displayText": True, "text": str(value), "fontSize": 50, "fontColor": "#fff"},
            "title": {"display": True, "text": ["Индекс страха", "и жадности"], "color": "#ccc", "fontSize": 14},
            "subtitle": {"display": True, "text": classification, "color": color, "fontSize": 16}
        }
    }
    return quickchart(config, 400, 350)

def create_dominance_chart(btc_dom, eth_dom, others):
    config = {
        "type": "doughnut",
        "data": {
            "labels": ["Bitcoin", "Ethereum", "Остальные"],
            "datasets": [{"data": [btc_dom, eth_dom, others], "backgroundColor": ["#f7931a", "#627eea", "#666666"]}]
        },
        "options": {
            "plugins": {
                "title": {"display": True, "text": "Доминация BTC", "color": "#fff", "font": {"size": 16}},
                "legend": {"labels": {"color": "#ccc"}}
            }
        }
    }
    return quickchart(config, 400, 300)

def create_heatmap(top_coins):
    """Столбчатая диаграмма топ-10 монет по капитализации"""
    labels = [c["symbol"].upper() for c in top_coins[:10]]
    data = [c["market_cap"] for c in top_coins[:10]]
    config = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{"data": data, "backgroundColor": "#3b82f6"}]
        },
        "options": {
            "indexAxis": "y",
            "plugins": {
                "title": {"display": True, "text": "Топ-10 по капитализации (USD)", "color": "#fff"},
                "legend": {"display": False}
            },
            "scales": {
                "x": {"ticks": {"color": "#ccc", "callback": "function(v){return (v/1e9).toFixed(1)+'B'}"}, "grid": {"color": "#333"}},
                "y": {"ticks": {"color": "#ccc"}, "grid": {"color": "#333"}}
            }
        }
    }
    return quickchart(config, 500, 400)

# ------------------- ОБРАЗОВАТЕЛЬНЫЙ БЛОК -------------------
TERMS = [
    ("FOMO", "Fear Of Missing Out — страх упустить рост, заставляющий покупать на пике."),
    ("DeFi", "Децентрализованные финансы: кредиты, обмен и заработок без банков."),
    ("Сложный процент", "Начисление процентов на проценты. Главный секрет долгосрочного роста."),
    ("Киты", "Крупные держатели криптовалюты, способные двигать рынок."),
    ("Халвинг", "Уменьшение награды майнерам вдвое. Происходит раз в 4 года у Bitcoin."),
    ("Стейблкоин", "Криптовалюта, привязанная к цене доллара (USDT, USDC)."),
    ("DAO", "Децентрализованная автономная организация — управление без директоров."),
]

def get_term_of_day():
    """Возвращает (термин, определение) в зависимости от дня месяца"""
    idx = datetime.now().day % len(TERMS)
    return TERMS[idx]

# ------------------- ОТПРАВКА В TELEGRAM -------------------
def send_message(chat_id, text, parse_mode="HTML", disable_preview=True):
    try:
        r = requests.post(f"{TELEGRAM_API}{os.environ['BOT_TOKEN']}/sendMessage",
                         json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": disable_preview},
                         timeout=10)
        return r.json().get("ok", False)
    except Exception as e:
        print(f"   ❌ sendMessage: {e}")
        return False

def send_photo(chat_id, photo_url, caption=""):
    try:
        r = requests.post(f"{TELEGRAM_API}{os.environ['BOT_TOKEN']}/sendPhoto",
                         json={"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "HTML"},
                         timeout=15)
        return r.json().get("ok", False)
    except Exception as e:
        print(f"   ❌ sendPhoto: {e}")
        return False

def send_media_group(chat_id, photos):
    """photos = [(url, caption), ...]"""
    if not photos:
        return True
    media = [{"type": "photo", "media": url, "caption": cap, "parse_mode": "HTML"} for url, cap in photos]
    try:
        for i in range(0, len(media), 10):
            chunk = media[i:i+10]
            r = requests.post(f"{TELEGRAM_API}{os.environ['BOT_TOKEN']}/sendMediaGroup",
                             data={"chat_id": chat_id, "media": json.dumps(chunk)}, timeout=20)
            if not r.json().get("ok"):
                print(f"   ❌ MediaGroup: {r.json().get('description')}")
                return False
        return True
    except Exception as e:
        print(f"   ❌ sendMediaGroup: {e}")
        return False

def send_poll(chat_id, question, options):
    try:
        r = requests.post(f"{TELEGRAM_API}{os.environ['BOT_TOKEN']}/sendPoll",
                         json={"chat_id": chat_id, "question": question, "options": options, "is_anonymous": False},
                         timeout=10)
        return r.json().get("ok", False)
    except Exception as e:
        print(f"   ❌ sendPoll: {e}")
        return False

def notify_admin(text):
    if ADMIN_CHAT_ID:
        send_message(ADMIN_CHAT_ID, f"⚠️ Бот ошибка:\n{text}")

# ------------------- РАЗДЕЛИТЕЛЬ ДЛИННЫХ ТЕКСТОВ -------------------
def split_text(text, limit=4000):
    if len(text) <= limit:
        return [text]
    parts = []
    while len(text) > limit:
        idx = text.rfind(' ', 0, limit)
        if idx == -1:
            idx = limit
        parts.append(text[:idx])
        text = text[idx:].lstrip()
    if text:
        parts.append(text)
    return parts

# ------------------- СИГНАЛЫ И НАСТРОЕНИЕ -------------------
def signal(change):
    if change > 5: return "🟢 Сильный рост"
    elif change > 2: return "🟢 Рост"
    elif change > 0: return "📈 Плюс"
    elif change > -2: return "🔴 Минус"
    elif change > -5: return "📉 Падение"
    else: return "🔻 Сильное падение"

def sentiment(btc_ch):
    if btc_ch > 5: return "🟢 Жадность"
    elif btc_ch > 2: return "🟡 Оптимизм"
    elif btc_ch > 0: return "⚪ Нейтрально"
    elif btc_ch > -5: return "🟠 Страх"
    else: return "🔴 Сильный страх"

# ------------------- ФОРМАТЫ ПОСТОВ ПО ВРЕМЕНИ -------------------
def post_0700():
    """Утренний брифинг"""
    data = get_crypto()
    fg = get_fear_greed_index()
    global_data = get_global_data()
    if not data:
        return
    btc = data["bitcoin"]["usd"]
    btc_ch = data["bitcoin"]["usd_24h_change"]
    eth = data["ethereum"]["usd"]
    eth_ch = data["ethereum"]["usd_24h_change"]
    dom = global_data["market_cap_percentage"]["btc"] if global_data else None

    now = datetime.now()
    text = (
        f"🌅 <b>Утренний брифинг</b> • {now.strftime('%d.%m.%Y')} 07:00 МСК\n"
        f"#утро #BTC #ETH\n\n"
        f"₿ Bitcoin: <b>${btc:,.0f}</b> ({btc_ch:+.2f}%) {signal(btc_ch)}\n"
        f"Ξ Ethereum: <b>${eth:,.0f}</b> ({eth_ch:+.2f}%) {signal(eth_ch)}"
    )
    if dom:
        text += f"\n📊 Доминация BTC: <b>{dom:.1f}%</b>"
    if fg:
        text += f"\n🎭 Индекс страха: {fg['value']}/100 ({fg['value_classification']})"
    send_message(CHANNEL, text)
    # График доминации
    if dom:
        others = 100 - dom - (global_data["market_cap_percentage"]["eth"] if global_data else 15)
        eth_dom = global_data["market_cap_percentage"]["eth"] if global_data else 15
        chart_url = create_dominance_chart(dom, eth_dom, others)
        if chart_url:
            send_photo(CHANNEL, chart_url, "📊 Доминация BTC/ETH")

def post_1000():
    """Основной обзор рынка"""
    data = get_crypto()
    fg = get_fear_greed_index()
    if not data:
        return
    btc = data["bitcoin"]["usd"]
    btc_ch = data["bitcoin"]["usd_24h_change"]
    eth = data["ethereum"]["usd"]
    eth_ch = data["ethereum"]["usd_24h_change"]

    now = datetime.now()
    text = (
        f"📊 <b>Обзор рынка</b> • {now.strftime('%d.%m.%Y')} 10:00 МСК\n"
        f"#обзор #BTC #ETH\n\n"
        f"₿ Bitcoin: <b>${btc:,.0f}</b> ({btc_ch:+.2f}%) {signal(btc_ch)}\n"
        f"Ξ Ethereum: <b>${eth:,.0f}</b> ({eth_ch:+.2f}%) {signal(eth_ch)}"
    )
    if fg:
        text += f"\n🎭 Индекс страха: {fg['value']}/100 ({fg['value_classification']})"
    send_message(CHANNEL, text)

    # Графики
    btc_chart = create_price_chart("bitcoin", "Bitcoin", "#f7931a")
    eth_chart = create_price_chart("ethereum", "Ethereum", "#627eea")
    if btc_chart and eth_chart:
        send_media_group(CHANNEL, [
            (btc_chart, f"₿ BTC: ${btc:,.0f} ({btc_ch:+.2f}%)"),
            (eth_chart, f"Ξ ETH: ${eth:,.0f} ({eth_ch:+.2f}%)")
        ])
    # Индекс страха
    if fg:
        gauge = create_fear_greed_gauge(int(fg["value"]), fg["value_classification"])
        if gauge:
            send_photo(CHANNEL, gauge, f"🎭 Индекс страха: {fg['value']}/100")

    # Новости (2 штуки)
    all_news = get_all_news()
    for n in all_news[:2]:
        caption = f"📰 <b>{n['title']}</b>\n📍 {n['source']}\n\n{n['link']}"
        imgs = n.get("images", [])
        if imgs:
            send_photo(CHANNEL, imgs[0], caption)
        else:
            send_message(CHANNEL, caption)

def post_1300():
    """Дайджест + опрос + термин дня"""
    all_news = get_all_news()
    if not all_news:
        send_message(CHANNEL, "📭 Пока новостей нет.")
        return
    now = datetime.now()
    text = f"📋 <b>Дайджест новостей</b> • {now.strftime('%d.%m.%Y')} 13:00 МСК\n#дайджест\n\n"
    for n in all_news[:5]:
        text += f"• <b>{n['title']}</b> ({n['source']})\n"
    send_message(CHANNEL, text)

    # Термин дня
    term, desc = get_term_of_day()
    send_message(CHANNEL, f"📘 <b>Термин дня: {term}</b>\n{desc} #обучение")

    # Опрос
    send_poll(CHANNEL, "Куда пойдёт BTC сегодня?", ["🟢 Вверх", "🔴 Вниз", "↔️ Боковик"])

def post_1600():
    """Аналитика: тепловая карта, S&P 500"""
    data = get_crypto()
    if not data:
        return
    btc = data["bitcoin"]["usd"]
    btc_ch = data["bitcoin"]["usd_24h_change"]
    eth = data["ethereum"]["usd"]
    eth_ch = data["ethereum"]["usd_24h_change"]

    now = datetime.now()
    text = (
        f"📈 <b>Аналитика</b> • {now.strftime('%d.%m.%Y')} 16:00 МСК\n"
        f"#аналитика #BTC #ETH\n\n"
        f"₿ BTC: <b>${btc:,.0f}</b> ({btc_ch:+.2f}%)\n"
        f"Ξ ETH: <b>${eth:,.0f}</b> ({eth_ch:+.2f}%)"
    )
    send_message(CHANNEL, text)

    # Тепловая карта
    top = get_top_coins()
    if top:
        heatmap_url = create_heatmap(top)
        if heatmap_url:
            send_photo(CHANNEL, heatmap_url, "🗺 Топ-10 по капитализации")

    # S&P 500
    sp = get_sp500()
    if sp:
        sp_text = f"🇺🇸 S&P 500: <b>${sp['price']}</b> ({sp['change']:+.2f}%)"
        send_message(CHANNEL, sp_text)

    # Новости (2 штуки)
    all_news = get_all_news()
    for n in all_news[:2]:
        caption = f"📰 <b>{n['title']}</b>\n📍 {n['source']}\n\n{n['link']}"
        imgs = n.get("images", [])
        if imgs:
            send_photo(CHANNEL, imgs[0], caption)
        else:
            send_message(CHANNEL, caption)

def post_1900():
    """Итоги дня"""
    data = get_crypto()
    fg = get_fear_greed_index()
    global_data = get_global_data()
    if not data:
        return
    btc = data["bitcoin"]["usd"]
    btc_ch = data["bitcoin"]["usd_24h_change"]
    eth = data["ethereum"]["usd"]
    eth_ch = data["ethereum"]["usd_24h_change"]
    dom = global_data["market_cap_percentage"]["btc"] if global_data else None

    now = datetime.now()
    text = (
        f"🌆 <b>Итоги дня</b> • {now.strftime('%d.%m.%Y')} 19:00 МСК\n"
        f"#итоги #BTC #ETH\n\n"
        f"₿ Bitcoin: <b>${btc:,.0f}</b> ({btc_ch:+.2f}%) {signal(btc_ch)}\n"
        f"Ξ Ethereum: <b>${eth:,.0f}</b> ({eth_ch:+.2f}%) {signal(eth_ch)}"
    )
    if dom:
        text += f"\n📊 Доминация BTC: <b>{dom:.1f}%</b>"
    if fg:
        text += f"\n🎭 Индекс страха: {fg['value']}/100"
    send_message(CHANNEL, text)
    # График доминации
    if dom:
        eth_dom = global_data["market_cap_percentage"]["eth"] if global_data else 15
        chart_url = create_dominance_chart(dom, eth_dom, 100 - dom - eth_dom)
        if chart_url:
            send_photo(CHANNEL, chart_url, "📊 Доминация")

def post_2200():
    """Американская сессия"""
    sp = get_sp500()
    btc = get_crypto()
    if not btc:
        return
    btc_price = btc["bitcoin"]["usd"]
    now = datetime.now()
    text = (
        f"🌙 <b>Американская сессия</b> • {now.strftime('%d.%m.%Y')} 22:00 МСК\n"
        f"#вечер #BTC #SP500\n\n"
        f"₿ Bitcoin: <b>${btc_price:,.0f}</b>"
    )
    if sp:
        text += f"\n🇺🇸 S&P 500: <b>${sp['price']}</b> ({sp['change']:+.2f}%)"
    send_message(CHANNEL, text)
    if sp:
        # График корреляции (символический)
        config = {
            "type": "scatter",
            "data": {
                "datasets": [{
                    "label": "BTC vs S&P",
                    "data": [{"x": sp["price"], "y": btc_price}],
                    "backgroundColor": "#f7931a"
                }]
            },
            "options": {
                "plugins": {"title": {"display": True, "text": "BTC / S&P 500", "color": "#fff"}},
                "scales": {
                    "x": {"title": {"text": "S&P 500", "color": "#ccc"}, "ticks": {"color": "#ccc"}},
                    "y": {"title": {"text": "Bitcoin", "color": "#ccc"}, "ticks": {"color": "#ccc"}}
                }
            }
        }
        chart_url = quickchart(config, 400, 300)
        send_photo(CHANNEL, chart_url, "📍 Текущая точка (не инвестиционная рекомендация)")

# ------------------- ГЛАВНЫЙ РАСПРЕДЕЛИТЕЛЬ -------------------
CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "@finanis")

def main():
    hour_utc = datetime.now().hour  # на GitHub Actions время UTC
    hour_msk = (hour_utc + 3) % 24   # переводим в МСК

    print(f"🚀 Запуск бота. МСК: {hour_msk}:00")
    try:
        if hour_msk == 7:
            post_0700()
        elif hour_msk == 10:
            post_1000()
        elif hour_msk == 13:
            post_1300()
        elif hour_msk == 16:
            post_1600()
        elif hour_msk == 19:
            post_1900()
        elif hour_msk == 22:
            post_2200()
        else:
            # На всякий случай (если вдруг запуск не по расписанию) — обычный обзор
            print("⚠️ Внеплановый запуск – делаем базовый обзор")
            post_1000()
    except Exception as e:
        err = f"Критическая ошибка: {e}"
        print(err)
        notify_admin(err)
        raise

if __name__ == "__main__":
    main()
