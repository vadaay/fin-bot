import os
import requests
from datetime import datetime
import json
import random
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlunparse, quote

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
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
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
    if not url:
        return url
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

# ------------------- Обработка HTML / текста -------------------
def clean_html(html):
    """Удаляет HTML-теги и лишние пробелы"""
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def extract_images_from_html(html):
    """Извлекает URL картинок из HTML (из атрибутов src)"""
    return re.findall(r'<img[^>]+src="([^"]+)"', html)

# ------------------- Генерация картинки‑заглушки -------------------
def generate_news_image(title, source):
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
                "title": {"display": True, "text": [safe_title], "color": "#ffffff", "font": {"size": 14, "weight": "bold"}, "padding": 10},
                "subtitle": {"display": True, "text": f"Источник: {safe_source}", "color": "#cccccc", "font": {"size": 12}},
                "legend": {"display": False}
            },
            "scales": {"x": {"display": False}, "y": {"display": False}}
        }
    }
    encoded = quote(json.dumps(config), safe='')
    return f"https://quickchart.io/chart?c={encoded}&width=500&height=300&backgroundColor=%231a1a2e"

# ------------------- Источники новостей -------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_coinmarketcap_news():
    """CoinMarketCap – JSON API, пробуем достать текст и картинки"""
    print("📡 CoinMarketCap...")
    try:
        url = "https://api.coinmarketcap.com/content/v3/news?page=1&size=5"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"   Статус: {resp.status_code}")
            return []
        data = resp.json()
        news = []
        for item in data.get("data", []):
            title = item.get("title", "")
            link = item.get("link", "")
            image = item.get("thumbnail", "") or item.get("image", "")
            # Контент может быть в 'content' или 'body'
            content = item.get("content", "") or item.get("body", "")
            # Если контент – HTML, очистим
            text = clean_html(content) if content else ""
            images = [image] if image else []
            if content:
                images.extend(extract_images_from_html(content))
            # Убираем дубли
            images = list(set(images))
            if title and link:
                news.append({
                    "title": title,
                    "link": clean_url(link),
                    "content": text,
                    "images": images,
                    "source": "CoinMarketCap"
                })
        print(f"   ✅ Получено: {len(news)}")
        return news
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return []

def get_cryptopanic_news():
    """CryptoPanic – RSS с полным текстом из description"""
    print("📡 CryptoPanic...")
    try:
        url = "https://cryptopanic.com/news/feed/?filter=all"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"   Статус: {resp.status_code}")
            return []
        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError:
            # Чистим от невалидных символов
            cleaned = re.sub(r'[^\x20-\x7E\xA0-\xFF]', '', resp.text)
            root = ET.fromstring(cleaned)
        news = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title")
            link = item.find("link")
            desc = item.find("description")
            if title is None or link is None:
                continue
            title_text = title.text or ""
            link_text = link.text or ""
            if not title_text or not link_text:
                continue
            # Полный текст из description (HTML)
            html_content = desc.text if desc is not None else ""
            text = clean_html(html_content)
            # Картинки из description + возможно enclosure
            images = extract_images_from_html(html_content)
            enc = item.find("enclosure")
            if enc is not None:
                img = enc.get("url", "")
                if img:
                    images.append(img)
            images = list(set(images))
            news.append({
                "title": title_text,
                "link": clean_url(link_text),
                "content": text,
                "images": images,
                "source": "CryptoPanic"
            })
        print(f"   ✅ Получено: {len(news)}")
        return news
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return []

def get_cointelegraph_news():
    """CoinTelegraph – пробуем несколько RSS-адресов"""
    print("📡 CoinTelegraph...")
    for feed_url in [
        "https://cointelegraph.com/rss",
        "https://cointelegraph.com/feed/",
        "https://cointelegraph.com/rss/feed/"
    ]:
        try:
            resp = requests.get(feed_url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.content)
            news = []
            for item in root.findall(".//item")[:5]:
                title = item.find("title")
                link = item.find("link")
                desc = item.find("description")
                if title is None or link is None:
                    continue
                title_text = title.text or ""
                link_text = link.text or ""
                if not title_text or not link_text:
                    continue
                html_content = desc.text if desc is not None else ""
                text = clean_html(html_content)
                images = extract_images_from_html(html_content)
                enc = item.find("enclosure")
                if enc is not None:
                    img = enc.get("url", "")
                    if img:
                        images.append(img)
                images = list(set(images))
                news.append({
                    "title": title_text,
                    "link": clean_url(link_text),
                    "content": text,
                    "images": images,
                    "source": "CoinTelegraph"
                })
            if news:
                print(f"   ✅ Получено ({feed_url}): {len(news)}")
                return news
        except Exception as e:
            print(f"   ❌ Ошибка {feed_url}: {e}")
    print("   ❌ Все RSS недоступны")
    return []

def get_google_news_crypto():
    """Резерв – Google News (без полного текста, только заголовок)"""
    print("📡 Google News (резерв)...")
    try:
        url = "https://news.google.com/rss/search?q=криптовалюта&hl=ru&gl=RU&ceid=RU:ru"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
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
                    "content": "",
                    "images": [],
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
        encoded = quote(json.dumps(config), safe='')
        return f"https://quickchart.io/chart?c={encoded}&width=600&height=350&backgroundColor=%231a1a2e"
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
    encoded = quote(json.dumps(config), safe='')
    return f"https://quickchart.io/chart?c={encoded}&width=400&height=350&backgroundColor=%231a1a2e"

# ------------------- Отправка в Telegram -------------------
def send_photo(token, channel, photo_url, caption):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        r = requests.post(url, json={"chat_id":channel,"photo":photo_url,"caption":caption,"parse_mode":"HTML"}, timeout=15)
        ok = r.json().get("ok", False)
        if not ok:
            print(f"   ❌ Фото: {r.json().get('description')}")
        return ok
    except Exception as e:
        print(f"   ❌ Исключение фото: {e}")
        return False

def send_message(token, channel, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id":channel,"text":text,"parse_mode":"HTML","disable_web_page_preview":True}, timeout=10)
    ok = r.json().get("ok", False)
    if not ok:
        print(f"   ❌ Текст: {r.json().get('description')}")
    return ok

def send_media_group(token, channel, photos):
    """Отправляет альбом до 10 фото с подписями"""
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    media = []
    for url_img, caption in photos:
        media.append({"type":"photo","media":url_img,"caption":caption,"parse_mode":"HTML"})
    if not media:
        return True
    # Отправляем не более 10 за раз
    for i in range(0, len(media), 10):
        chunk = media[i:i+10]
        r = requests.post(url, data={"chat_id":channel,"media":json.dumps(chunk)}, timeout=20)
        ok = r.json().get("ok", False)
        if not ok:
            print(f"   ❌ Альбом: {r.json().get('description')}")
            return False
    return True

def split_long_text(text, limit=4000):
    """Разбивает длинный текст на куски по лимиту, стараясь не резать слова"""
    if len(text) <= limit:
        return [text]
    parts = []
    while len(text) > limit:
        # Ищем последний пробел перед лимитом
        idx = text.rfind(' ', 0, limit)
        if idx == -1:
            idx = limit
        parts.append(text[:idx])
        text = text[idx:].lstrip()
    if text:
        parts.append(text)
    return parts

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
    
    # 1. Индекс страха
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
    
    # 2. Графики
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
    
    # 4. Новости с полным текстом и картинками
    all_news = get_all_news()
    if all_news:
        random.shuffle(all_news)
        for news in all_news[:5]:
            print(f"\n📰 Обработка: {news['title'][:50]}...")
            # Формируем текстовое сообщение
            header = f"📰 <b>{news['title']}</b>\n📍 {news['source']}\n\n"
            content = news.get("content", "")
            if content:
                # Ограничим длину, если текст слишком большой
                if len(content) > 3500:
                    content = content[:3500] + "..."
                full_text = header + content + f"\n\n🔗 <a href='{news['link']}'>Читать оригинал</a>"
            else:
                full_text = header + f"🔗 <a href='{news['link']}'>Читать статью</a>"
            
            # Отправляем текст (если длинный — частями)
            for part in split_long_text(full_text):
                send_message(token, channel, part)
            
            # Отправляем картинки
            images = news.get("images", [])
            if images:
                # Если одна картинка – просто фото с подписью (заголовок)
                if len(images) == 1:
                    send_photo(token, channel, images[0], f"{news['title']}")
                else:
                    # Альбом с подписями (только первые 10)
                    img_captions = [(img, "") for img in images[:10]]
                    send_media_group(token, channel, img_captions)
            elif not content:
                # Если нет ни текста, ни картинок – генерируем заглушку
                img_url = generate_news_image(news["title"], news["source"])
                send_photo(token, channel, img_url, f"{news['title']}")
    else:
        send_message(token, channel, "📰 Нет свежих новостей")
    
    print("✅ Все посты отправлены")
    return True

if __name__ == "__main__":
    print("🚀 Старт бота")
    exit(0 if send_post() else 1)
