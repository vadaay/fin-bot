import os
import requests
from datetime import datetime
import json
import random
import re
import xml.etree.ElementTree as ET

# ------------------- Функции получения данных -------------------
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
        print(f"❌ Ошибка CoinGecko: {e}")
        return None

def get_fear_greed_index():
    url = "https://api.alternative.me/fng/"
    try:
        resp = requests.get(url, params={"limit": 1}, timeout=10)
        resp.raise_for_status()
        return resp.json()["data"][0]
    except:
        return None

# ------------------- Новости: Криптовалюты -------------------
def get_rss_news_rbc_crypto():
    """РБК Крипто"""
    try:
        url = "https://www.rbc.ru/v10/ajax/get-news-feed/project/rbcfree/latest/crypto/"
        headers = {"User-Agent": "Mozilla/5.0"}
        data = requests.get(url, headers=headers, timeout=10).json()
        news = []
        for item in data.get("items", [])[:5]:
            title = item.get("title", "")
            link = item.get("fronturl", "")
            image = item.get("image", {}).get("big_preview", "")
            if title:
                news.append({"title": title, "link": link, "image": image, "source": "РБК Крипто"})
        return news
    except Exception as e:
        print(f"❌ РБК Крипто: {e}")
        return []

def get_forklog_news():
    """Forklog (крипто)"""
    try:
        url = "https://forklog.com/feed/"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(resp.content)
        news = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title")
            link = item.find("link")
            image_tag = item.find(".//{http://search.yahoo.com/mrss/}content")
            title_text = title.text if title is not None else ""
            link_text = link.text if link is not None else ""
            image_url = image_tag.get("url", "") if image_tag is not None else ""
            if title_text:
                news.append({"title": title_text, "link": link_text, "image": image_url, "source": "Forklog"})
        return news
    except Exception as e:
        print(f"❌ Forklog: {e}")
        return []

def get_bitsmedia_news():
    """Bits.media"""
    try:
        url = "https://bits.media/news/"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        titles = re.findall(r'<a class="news-item__title"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', resp.text)
        news = []
        for link, title in titles[:5]:
            title = re.sub(r'<[^>]+>', '', title).strip()
            if title:
                news.append({"title": title, "link": f"https://bits.media{link}" if link.startswith("/") else link, "image": "", "source": "Bits.media"})
        return news
    except Exception as e:
        print(f"❌ Bits.media: {e}")
        return []

def get_coindesk_news():
    """CoinDesk"""
    try:
        url = "https://www.coindesk.com/arc/outboundfeeds/v2/feed/articles/?pageSize=5"
        headers = {"User-Agent": "Mozilla/5.0"}
        data = requests.get(url, headers=headers, timeout=10).json()
        news = []
        for item in data.get("articles", []):
            title = item.get("title", "")
            link = item.get("link", "")
            image = item.get("promoImage", {}).get("url", "")
            if title:
                news.append({"title": title, "link": link, "image": image, "source": "CoinDesk"})
        return news
    except:
        return []

# ------------------- Новости: Ценные бумаги, фондовый рынок -------------------
def get_rbc_investments_news():
    """РБК Инвестиции (акции, облигации)"""
    try:
        url = "https://www.rbc.ru/v10/ajax/get-news-feed/project/rbcfree/latest/investments/"
        headers = {"User-Agent": "Mozilla/5.0"}
        data = requests.get(url, headers=headers, timeout=10).json()
        news = []
        for item in data.get("items", [])[:5]:
            title = item.get("title", "")
            link = item.get("fronturl", "")
            image = item.get("image", {}).get("big_preview", "")
            if title:
                news.append({"title": title, "link": link, "image": image, "source": "РБК Инвестиции"})
        return news
    except Exception as e:
        print(f"❌ РБК Инвестиции: {e}")
        return []

def get_finam_news():
    """Финам.ру (рынки, акции)"""
    try:
        url = "https://www.finam.ru/international/feed/rss/"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(resp.content)
        news = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title")
            link = item.find("link")
            desc = item.find("description")
            # Поиск картинки в description
            image = ""
            if desc is not None and desc.text:
                img_match = re.search(r'<img[^>]+src="([^"]+)"', desc.text)
                if img_match:
                    image = img_match.group(1)
            title_text = title.text if title is not None else ""
            link_text = link.text if link is not None else ""
            if title_text:
                news.append({"title": title_text, "link": link_text, "image": image, "source": "Финам"})
        return news
    except Exception as e:
        print(f"❌ Финам: {e}")
        return []

def get_smartlab_news():
    """Смарт-лаб (трейдерские новости)"""
    try:
        url = "https://smart-lab.ru/rss/news/"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(resp.content)
        news = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title")
            link = item.find("link")
            desc = item.find("description")
            image = ""
            if desc is not None and desc.text:
                img_match = re.search(r'<img[^>]+src="([^"]+)"', desc.text)
                if img_match:
                    image = img_match.group(1)
            title_text = title.text if title is not None else ""
            link_text = link.text if link is not None else ""
            if title_text:
                news.append({"title": title_text, "link": link_text, "image": image, "source": "Смарт-лаб"})
        return news
    except Exception as e:
        print(f"❌ Смарт-лаб: {e}")
        return []

def get_newsapi():
    api_key = os.environ.get("NEWS_API_KEY", "")
    if not api_key:
        return []
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "акции OR облигации OR криптовалюта OR биткоин OR фондовый рынок",
        "language": "ru",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": api_key
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        news = []
        for article in data.get("articles", []):
            news.append({
                "title": article.get("title", ""),
                "link": article.get("url", ""),
                "image": article.get("urlToImage", ""),
                "source": article.get("source", {}).get("name", "NewsAPI")
            })
        return news
    except:
        return []

# ------------------- Сбор всех новостей -------------------
def get_all_news():
    print("📰 Собираем новости криптовалют и ценных бумаг...")
    all_news = []
    
    # Криптоисточники
    all_news.extend(get_rss_news_rbc_crypto())
    all_news.extend(get_forklog_news())
    all_news.extend(get_bitsmedia_news())
    all_news.extend(get_coindesk_news())
    
    # Фондовые источники
    all_news.extend(get_rbc_investments_news())
    all_news.extend(get_finam_news())
    all_news.extend(get_smartlab_news())
    
    # Внешний API (если есть ключ)
    all_news.extend(get_newsapi())
    
    # Удаление дубликатов
    seen_titles = set()
    unique = []
    for n in all_news:
        if n["title"] and n["title"] not in seen_titles:
            seen_titles.add(n["title"])
            unique.append(n)
    
    print(f"✅ Собрано {len(unique)} уникальных новостей")
    return unique

# ------------------- Экономический календарь -------------------
def get_economic_calendar():
    return {
        "🇺🇸 ФРС": "Решение по ставке — 12.06",
        "🇪🇺 ЕЦБ": "Решение по ставке — 06.06",
        "📊 CPI США": "Инфляция — ежемесячно",
        "💼 Non-Farm": "Занятость США — первая пятница",
        "🛢 ОПЕК": "Встреча — ежеквартально",
        "🏦 ЦБ РФ": "Заседание по ставке — 07.06"
    }

# ------------------- Вспомогательные функции -------------------
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

# ------------------- Основная логика -------------------
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
    events = get_economic_calendar()
    text3 = "📅 <b>Ключевые события:</b>\n\n" + "\n".join([f"• {k}: {v}" for k,v in events.items()])
    text3 += "\n\n💡 <b>Факторы влияния:</b>\n• Ставки ЦБ\n• Инфляция CPI\n• DXY\n• Регуляция\n\n📌 <i>Диверсифицируйте риски</i>"
    send_message(token, channel, text3)
    
    # 4. Новости (крипто + ценные бумаги)
    all_news = get_all_news()
    if all_news:
        random.shuffle(all_news)
        for news in all_news[:5]:
            caption = f"📰 <b>{news['title']}</b>\n📍 {news['source']}\n\n{news['link']}"
            img = news.get("image", "")
            if img:
                send_photo(token, channel, img, caption)
            else:
                send_message(token, channel, caption)
    else:
        send_message(token, channel, "📰 Нет свежих новостей")
    
    print("✅ Все посты отправлены")
    return True

if __name__ == "__main__":
    print("🚀 Старт бота (крипто + фондовый рынок)")
    exit(0 if send_post() else 1)
