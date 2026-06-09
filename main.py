import os
import requests
from datetime import datetime
import json
import random
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlunparse

# ------------------- Базовые данные рынка -------------------
def get_crypto():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_market_cap": "true"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ CoinGecko: {e}")
        return None

def get_fear_greed_index():
    url = "https://api.alternative.me/fng/"
    try:
        resp = requests.get(url, params={"limit": 1}, timeout=10)
        resp.raise_for_status()
        return resp.json()["data"][0]
    except:
        return None

# ------------------- Очистка ссылок -------------------
def clean_url(url):
    """Удаляет UTM-метки и лишние параметры из URL"""
    if not url:
        return url
    parsed = urlparse(url)
    # Оставляем только схему, домен и путь, убираем query и fragment
    clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    return clean

# ------------------- Генерация картинки-заглушки -------------------
def generate_news_image(title, source):
    """Создаёт картинку с заголовком новости и источником через QuickChart"""
    # Экранируем спецсимволы для JSON
    safe_title = title[:100].replace('"', "'").replace('\n', ' ')
    safe_source = source.replace('"', "'")
    
    config = {
        "type": "bar",
        "data": {
            "labels": [""],
            "datasets": [{
                "data": [100],
                "backgroundColor": "#f7931a" if "Coin" in source else "#3b82f6",
                "barPercentage": 1.0,
                "categoryPercentage": 1.0
            }]
        },
        "options": {
            "plugins": {
                "title": {
                    "display": True,
                    "text": [safe_title],
                    "color": "#ffffff",
                    "font": {"size": 14, "weight": "bold"},
                    "padding": 10
                },
                "subtitle": {
                    "display": True,
                    "text": f"Источник: {safe_source}",
                    "color": "#cccccc",
                    "font": {"size": 12}
                },
                "legend": {"display": False}
            },
            "scales": {
                "x": {"display": False},
                "y": {"display": False}
            }
        }
    }
    chart_json = json.dumps(config)
    return f"https://quickchart.io/chart?c={chart_json}&width=500&height=300&backgroundColor=%231a1a2e"

# ------------------- Новости (стабильные RSS) -------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def extract_image_from_item(item):
    """Пытается достать картинку из элемента RSS (enclosure, media:content, description)"""
    # enclosure
    enc = item.find("enclosure")
    if enc is not None:
        url = enc.get("url", "")
        if url and any(url.lower().endswith(ext) for ext in ['.jpg','.jpeg','.png','.webp']):
            return url
    
    # media:content
    media = item.find("{http://search.yahoo.com/mrss/}content")
    if media is not None:
        url = media.get("url", "")
        if url:
            return url
    
    # в описании
    desc = item.find("description")
    if desc is not None and desc.text:
        match = re.search(r'<img[^>]+src="([^"]+)"', desc.text)
        if match:
            return match.group(1)
    return ""

def get_coinmarketcap_news():
    print("📡 CoinMarketCap...")
    try:
        url = "https://coinmarketcap.com/headlines/news/feed/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"   Статус: {resp.status_code}")
            return []
        root = ET.fromstring(resp.content)
        news = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title")
            link = item.find("link")
            title_text = title.text if title is not None else ""
            link_text = link.text if link is not None else ""
            if title_text and link_text:
                image = extract_image_from_item(item)
                news.append({
                    "title": title_text,
                    "link": clean_url(link_text),
                    "image": image,
                    "source": "CoinMarketCap"
                })
        print(f"   ✅ Получено: {len(news)}")
        return news
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return []

def get_cryptopanic_news():
    print("📡 CryptoPanic...")
    try:
        url = "https://cryptopanic.com/news/feed/?filter=all"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"   Статус: {resp.status_code}")
            return []
        root = ET.fromstring(resp.content)
        news = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title")
            link = item.find("link")
            title_text = title.text if title is not None else ""
            link_text = link.text if link is not None else ""
            if title_text and link_text:
                image = extract_image_from_item(item)
                news.append({
                    "title": title_text,
                    "link": clean_url(link_text),
                    "image": image,
                    "source": "CryptoPanic"
                })
        print(f"   ✅ Получено: {len(news)}")
        return news
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return []

def get_cointelegraph_news():
    print("📡 CoinTelegraph...")
    try:
        url = "https://cointelegraph.com/rss/feed/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"   Статус: {resp.status_code}")
            return []
        root = ET.fromstring(resp.content)
        news = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title")
            link = item.find("link")
            title_text = title.text if title is not None else ""
            link_text = link.text if link is not None else ""
            if title_text and link_text:
                image = extract_image_from_item(item)
                news.append({
                    "title": title_text,
                    "link": clean_url(link_text),
                    "image": image,
                    "source": "CoinTelegraph"
                })
        print(f"   ✅ Получено: {len(news)}")
        return news
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return []

def get_google_news_crypto():
    """Резервный источник – Google News (криптовалюты)"""
    print("📡 Google News (резерв)...")
    try:
        url = "https://news.google.com/rss/search?q=криптовалюта&hl=ru&gl=RU&ceid=RU:ru"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"   Статус: {resp.status_code}")
            return []
        root = ET.fromstring(resp.content)
        news = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title")
            link = item.find("link")
            title_text = title.text if title is not None else ""
            link_text = link.text if link is not None else ""
            if title_text and link_text:
                news.append({
                    "title": title_text,
                    "link": clean_url(link_text),
                    "image": "",  # Google News редко даёт картинки в RSS
                    "source": "Google News"
                })
        print(f"   ✅ Получено: {len(news)}")
        return news
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return []

def get_all_news():
    print("\n📰 СБОР НОВОСТЕЙ")
    all_news = []
    all_news.extend(get_coinmarketcap_news())
    all_news.extend(get_cryptopanic_news())
    all_news.extend(get_cointelegraph_news())
    
    if len(all_news) < 3:
        print("⚠️ Мало новостей, добавляем Google News")
        all_news.extend(get_google_news_crypto())
    
    # Убираем дубликаты
    seen = set()
    unique = []
    for n in all_news:
        if n["title"] and n["title"] not in seen:
            seen.add(n["title"])
            unique.append(n)
    print(f"✅ ИТОГО уникальных: {len(unique)}")
    return unique

# ------------------- Экономкалендарь -------------------
def get_economic_calendar():
    return {
        "🇺🇸 ФРС": "Решение по ставке — 12.06",
        "🇪🇺 ЕЦБ": "Решение по ставке — 06.06",
        "📊 CPI США": "Инфляция — ежемесячно",
        "💼 Non-Farm": "Занятость США — первая пятница",
        "🏦 ЦБ РФ": "Заседание по ставке — 07.06"
    }

# ------------------- Графики и индикаторы -------------------
def signal(change):
    if change > 5: return "🟢 Сильный рост"
    elif change > 2: return "🟢 Рост"
    elif change > 0: return "📈 Плюс"
    elif change > -2: return "🔴 Минус"
    elif change > -5: return "📉 Падение"
    else: return "🔻 Сильное падение"

def get_market_sentiment(btc_ch):
    if btc_ch > 5: return "🟢 Жадность"
    elif btc_ch > 2: return "🟡 Оптимизм"
    elif btc_ch > 0: return "⚪ Нейтрально"
    elif btc_ch > -5: return "🟠 Страх"
    else: return "🔴 Сильный страх"

def create_price_chart(coin_id, coin_name, color):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        resp = requests.get(url, params={"vs_currency":"usd","days":7}, timeout=15)
        prices = resp.json()["prices"]
        step = max(len(prices)//20, 1)
        labels, values = [], []
        for i in range(0, len(prices), step):
            dt = datetime.fromtimestamp(prices[i][0]/1000)
            labels.append(dt.strftime('%d.%m'))
            values.append(round(prices[i][1]))
        config = {
            "type":"line",
            "data":{
                "labels":labels,
                "datasets":[{
                    "data":values,
                    "borderColor":color,
                    "backgroundColor":color+"33",
                    "borderWidth":2,"fill":True,"tension":0.3,"pointRadius":0
                }]
            },
            "options":{
                "plugins":{
                    "title":{"display":True,"text":f"{coin_name} за 7 дней","color":"#fff","font":{"size":18}},
                    "legend":{"display":False}
                },
                "scales":{
                    "y":{"ticks":{"color":"#ccc","callback":"function(v){return '$'+v.toLocaleString()}"},"grid":{"color":"#333"}},
                    "x":{"ticks":{"color":"#ccc"},"grid":{"color":"#333"}}
                }
            }
        }
        return f"https://quickchart.io/chart?c={json.dumps(config)}&width=600&height=350&backgroundColor=%231a1a2e"
    except:
        return None

def create_fear_greed_gauge(value, classification):
    if value<25: color="#ef5350"
    elif value<45: color="#ff9800"
    elif value<55: color="#ffc107"
    elif value<75: color="#8bc34a"
    else: color="#4caf50"
    config = {
        "type":"radialGauge",
        "data":{"datasets":[{"data":[value],"backgroundColor":color}]},
        "options":{
            "centerArea":{"displayText":True,"text":str(value),"fontSize":50,"fontColor":"#fff"},
            "title":{"display":True,"text":["Индекс страха","и жадности"],"color":"#ccc","fontSize":14},
            "subtitle":{"display":True,"text":classification,"color":color,"fontSize":16}
        }
    }
    return f"https://quickchart.io/chart?c={json.dumps(config)}&width=400&height=350&backgroundColor=%231a1a2e"

# ------------------- Отправка в Telegram -------------------
def send_photo(token, channel, photo_url, caption):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    r = requests.post(url, json={"chat_id":channel,"photo":photo_url,"caption":caption,"parse_mode":"HTML"}, timeout=15)
    ok = r.json().get("ok", False)
    print("   ✅ Фото" if ok else f"   ❌ {r.json().get('description')}")
    return ok

def send_message(token, channel, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id":channel,"text":text,"parse_mode":"HTML","disable_web_page_preview":False}, timeout=10)
    ok = r.json().get("ok", False)
    print("   ✅ Текст" if ok else f"   ❌ {r.json().get('description')}")
    return ok

def send_media_group(token, channel, photos):
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    media = [{"type":"photo","media":u,"caption":c,"parse_mode":"HTML"} for u,c in photos]
    r = requests.post(url, data={"chat_id":channel,"media":json.dumps(media)}, timeout=20)
    ok = r.json().get("ok", False)
    print("   ✅ Альбом" if ok else f"   ❌ {r.json().get('description')}")
    return ok

# ------------------- Главный пост -------------------
def send_post():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN не найден")
        return False
    channel = os.environ.get("TELEGRAM_CHANNEL", "@finanis")
    
    data = get_crypto()
    fg = get_fear_greed_index()
    if not data:
        return False
    
    btc = data["bitcoin"]["usd"]
    btc_ch = data["bitcoin"]["usd_24h_change"]
    eth = data["ethereum"]["usd"]
    eth_ch = data["ethereum"]["usd_24h_change"]
    
    now = datetime.now()
    date_str = now.strftime('%d.%m.%Y')
    time_str = now.strftime('%H:%M МСК')
    
    # 1. Индекс страха и жадности
    if fg:
        caption = (
            f"📊 <b>Крипто-рынок • {date_str}</b>\n"
            f"🕐 {time_str}\n\n"
            f"🎭 <b>Индекс страха:</b> {fg['value']}/100 ({fg['value_classification']})\n"
            f"🌡 <b>Настроение:</b> {get_market_sentiment(btc_ch)}"
        )
        gauge = create_fear_greed_gauge(int(fg["value"]), fg["value_classification"])
        if gauge:
            send_photo(token, channel, gauge, caption)
        else:
            send_message(token, channel, caption)
    
    # 2. Графики BTC и ETH
    btc_chart = create_price_chart("bitcoin", "Bitcoin", "#f7931a")
    eth_chart = create_price_chart("ethereum", "Ethereum", "#627eea")
    if btc_chart and eth_chart:
        send_media_group(token, channel, [
            (btc_chart, f"₿ <b>BTC:</b> ${btc:,.0f}\n{btc_ch:+.2f}% {signal(btc_ch)}"),
            (eth_chart, f"Ξ <b>ETH:</b> ${eth:,.0f}\n{eth_ch:+.2f}% {signal(eth_ch)}")
        ])
    else:
        send_message(token, channel, f"💎 <b>Активы:</b>\n₿ BTC: ${btc:,.0f} ({btc_ch:+.2f}%)\nΞ ETH: ${eth:,.0f} ({eth_ch:+.2f}%)")
    
    # 3. Экономкалендарь
    cal = get_economic_calendar()
    text3 = "📅 <b>Ключевые события:</b>\n\n" + "\n".join([f"• {k}: {v}" for k,v in cal.items()])
    text3 += "\n\n💡 <b>Факторы:</b>\n• Ставки ЦБ\n• Инфляция CPI\n• DXY\n• Регуляция\n\n📌 <i>Диверсифицируйте риски</i>"
    send_message(token, channel, text3)
    
    # 4. Новости с картинками и чистыми ссылками
    all_news = get_all_news()
    if all_news:
        random.shuffle(all_news)
        for news in all_news[:5]:
            caption = f"📰 <b>{news['title']}</b>\n📍 {news['source']}\n\n{news['link']}"
            image_url = news.get("image", "")
            if not image_url:
                # Генерируем картинку-заглушку с заголовком
                image_url = generate_news_image(news["title"], news["source"])
            send_photo(token, channel, image_url, caption)
    else:
        send_message(token, channel, "📰 Нет свежих новостей")
    
    print("✅ Все посты отправлены")
    return True

if __name__ == "__main__":
    print("🚀 Старт бота (чистые ссылки + картинки)")
    exit(0 if send_post() else 1)
