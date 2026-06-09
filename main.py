import os
import requests
from datetime import datetime
import json
import random

def get_crypto():
    """Получает данные о криптовалютах с CoinGecko"""
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
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе к CoinGecko: {e}")
        return None

def get_fear_greed_index():
    """Получает индекс страха и жадности"""
    url = "https://api.alternative.me/fng/"
    params = {"limit": 1}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["data"][0]
    except:
        return None

def get_rss_news_rbc():
    """Новости из РБК Крипто"""
    try:
        url = "https://www.rbc.ru/v10/ajax/get-news-feed/project/rbcfree/latest/crypto/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        news = []
        for item in data.get("items", [])[:5]:
            title = item.get("title", "")
            link = item.get("fronturl", "")
            image = item.get("image", {}).get("big_preview", "")
            date = item.get("publish_date_t", "")
            
            if title:
                news.append({
                    "title": title,
                    "link": link,
                    "image": image,
                    "date": date,
                    "source": "РБК Крипто"
                })
        return news
    except Exception as e:
        print(f"❌ Ошибка РБК: {e}")
        return []

def get_rss_news_forklog():
    """Новости из Forklog"""
    try:
        url = "https://forklog.com/feed/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # Парсим XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        news = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title")
            link = item.find("link")
            description = item.find("description")
            image_tag = item.find(".//{http://search.yahoo.com/mrss/}content")
            
            title_text = title.text if title is not None else ""
            link_text = link.text if link is not None else ""
            
            # Ищем картинку
            image_url = ""
            if image_tag is not None:
                image_url = image_tag.get("url", "")
            
            if title_text:
                news.append({
                    "title": title_text,
                    "link": link_text,
                    "image": image_url,
                    "source": "Forklog"
                })
        return news
    except Exception as e:
        print(f"❌ Ошибка Forklog: {e}")
        return []

def get_news_bitsmedia():
    """Новости из Bits.media"""
    try:
        url = "https://bits.media/news/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # Простой парсинг HTML (без библиотек)
        news = []
        text = response.text
        
        # Ищем заголовки новостей
        import re
        titles = re.findall(r'<a class="news-item__title"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', text)
        
        for link, title in titles[:5]:
            title = re.sub(r'<[^>]+>', '', title).strip()
            if title:
                news.append({
                    "title": title,
                    "link": f"https://bits.media{link}" if link.startswith("/") else link,
                    "image": "",
                    "source": "Bits.media"
                })
        return news
    except Exception as e:
        print(f"❌ Ошибка Bits.media: {e}")
        return []

def get_news_coindesk():
    """Новости из CoinDesk"""
    try:
        url = "https://www.coindesk.com/arc/outboundfeeds/v2/feed/articles/?pageSize=5"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        news = []
        for item in data.get("articles", []):
            title = item.get("title", "")
            link = item.get("link", "")
            
            # Картинка
            image = ""
            promo = item.get("promoImage", {})
            if promo:
                image = promo.get("url", "")
            
            if title:
                news.append({
                    "title": title,
                    "link": link,
                    "image": image,
                    "source": "CoinDesk"
                })
        return news
    except Exception as e:
        print(f"❌ Ошибка CoinDesk: {e}")
        return []

def get_news_api():
    """Новости через NewsAPI (если есть ключ)"""
    api_key = os.environ.get("NEWS_API_KEY", "")
    if not api_key:
        return []
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "биткоин OR криптовалюта OR блокчейн OR ставка ЦБ OR инфляция",
        "language": "ru",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
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

def get_all_news():
    """Собирает новости со всех источников"""
    print("📰 Собираем новости...")
    
    all_news = []
    
    # 1. РБК
    print("   • РБК...")
    rbc_news = get_rss_news_rbc()
    all_news.extend(rbc_news)
    
    # 2. Forklog
    print("   • Forklog...")
    forklog_news = get_rss_news_forklog()
    all_news.extend(forklog_news)
    
    # 3. Bits.media
    print("   • Bits.media...")
    bits_news = get_news_bitsmedia()
    all_news.extend(bits_news)
    
    # 4. CoinDesk (английский)
    print("   • CoinDesk...")
    coindesk_news = get_news_coindesk()
    all_news.extend(coindesk_news)
    
    # 5. NewsAPI
    newsapi_news = get_news_api()
    all_news.extend(newsapi_news)
    
    # Убираем дубликаты по заголовку
    seen = set()
    unique_news = []
    for n in all_news:
        if n["title"] not in seen and n["title"]:
            seen.add(n["title"])
            unique_news.append(n)
    
    print(f"✅ Собрано {len(unique_news)} новостей")
    return unique_news

def get_economic_calendar():
    """Экономический календарь"""
    events = {
        "🇺🇸 ФРС": "Решение по ставке — 12.06",
        "🇪🇺 ЕЦБ": "Решение по ставке — 06.06",
        "📊 CPI США": "Инфляция — ежемесячно",
        "💼 Non-Farm": "Занятость США — первая пятница месяца",
        "🛢 ОПЕК": "Встреча — ежеквартально"
    }
    return events

def signal(change):
    """Сигнал изменения цены"""
    if change > 5:
        return "🟢 Сильный рост"
    elif change > 2:
        return "🟢 Рост"
    elif change > 0:
        return "📈 Плюс"
    elif change > -2:
        return "🔴 Минус"
    elif change > -5:
        return "📉 Падение"
    else:
        return "🔻 Сильное падение"

def get_market_sentiment(btc_ch):
    """Настроение рынка"""
    if btc_ch > 5:
        return "🟢 Жадность"
    elif btc_ch > 2:
        return "🟡 Оптимизм"
    elif btc_ch > 0:
        return "⚪ Нейтрально"
    elif btc_ch > -5:
        return "🟠 Страх"
    else:
        return "🔴 Сильный страх"

def create_price_chart(coin_id, coin_name, color):
    """График цены"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 7}
        
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        prices = data["prices"]
        step = len(prices) // 20
        if step < 1:
            step = 1
            
        labels = []
        values = []
        
        for i in range(0, len(prices), step):
            timestamp = prices[i][0] / 1000
            price = prices[i][1]
            dt = datetime.fromtimestamp(timestamp)
            labels.append(dt.strftime('%d.%m'))
            values.append(round(price))
        
        chart_config = {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": f"{coin_name} (USD)",
                    "data": values,
                    "borderColor": color,
                    "backgroundColor": color + "33",
                    "borderWidth": 2,
                    "fill": True,
                    "tension": 0.3,
                    "pointRadius": 0
                }]
            },
            "options": {
                "plugins": {
                    "title": {
                        "display": True,
                        "text": f"{coin_name} за 7 дней",
                        "color": "#ffffff",
                        "font": {"size": 18}
                    },
                    "legend": {"display": False}
                },
                "scales": {
                    "y": {
                        "ticks": {
                            "color": "#cccccc",
                            "callback": "function(value) { return '$' + value.toLocaleString(); }"
                        },
                        "grid": {"color": "#333333"}
                    },
                    "x": {
                        "ticks": {
                            "color": "#cccccc"
                        },
                        "grid": {"color": "#333333"}
                    }
                }
            }
        }
        
        chart_json = json.dumps(chart_config)
        return f"https://quickchart.io/chart?c={chart_json}&width=600&height=350&backgroundColor=%231a1a2e"
    except Exception as e:
        print(f"❌ График {coin_name}: {e}")
        return None

def create_fear_greed_gauge(value, classification):
    """Шкала страха и жадности"""
    if value < 25:
        color = "#ef5350"
    elif value < 45:
        color = "#ff9800"
    elif value < 55:
        color = "#ffc107"
    elif value < 75:
        color = "#8bc34a"
    else:
        color = "#4caf50"
    
    chart_config = {
        "type": "radialGauge",
        "data": {
            "datasets": [{
                "data": [value],
                "backgroundColor": color,
                "borderWidth": 0
            }]
        },
        "options": {
            "centerArea": {
                "displayText": True,
                "text": f"{value}",
                "fontSize": 50,
                "fontColor": "#ffffff"
            },
            "title": {
                "display": True,
                "text": ["Индекс страха", "и жадности"],
                "color": "#cccccc",
                "fontSize": 14
            },
            "subtitle": {
                "display": True,
                "text": classification,
                "color": color,
                "fontSize": 16
            }
        }
    }
    
    try:
        chart_json = json.dumps(chart_config)
        return f"https://quickchart.io/chart?c={chart_json}&width=400&height=350&backgroundColor=%231a1a2e"
    except:
        return None

def create_news_image(news_title, source):
    """Создаёт картинку для новости"""
    chart_config = {
        "type": "radialGauge",
        "data": {
            "datasets": [{"data": [50], "backgroundColor": "#f7931a"}]
        },
        "options": {
            "centerArea": {
                "displayText": True,
                "text": "📰",
                "fontSize": 60
            },
            "title": {
                "display": True,
                "text": source,
                "color": "#ffffff",
                "fontSize": 20
            },
            "subtitle": {
                "display": True,
                "text": news_title[:100],
                "color": "#cccccc",
                "fontSize": 12
            }
        }
    }
    
    chart_json = json.dumps(chart_config)
    return f"https://quickchart.io/chart?c={chart_json}&width=400&height=400&backgroundColor=%231a1a2e"

def send_telegram_photo(token, channel, photo_url, caption):
    """Отправка фото в Telegram"""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    data = {
        "chat_id": channel,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=data, timeout=15)
        result = response.json()
        
        if result.get("ok"):
            print("   ✅ Фото отправлено")
            return True
        else:
            print(f"   ❌ Ошибка: {result.get('description', result)}")
            return False
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False

def send_telegram_message(token, channel, text):
    """Отправка текста"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": channel,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            print("   ✅ Текст отправлен")
            return True
        else:
            print(f"   ❌ Ошибка: {result.get('description', result)}")
            return False
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False

def send_media_group(token, channel, photos):
    """Отправка альбома фото"""
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    
    media = []
    for i, (photo_url, caption) in enumerate(photos):
        media.append({
            "type": "photo",
            "media": photo_url,
            "caption": caption,
            "parse_mode": "HTML"
        })
    
    data = {
        "chat_id": channel,
        "media": json.dumps(media)
    }
    
    try:
        response = requests.post(url, data=data, timeout=20)
        result = response.json()
        
        if result.get("ok"):
            print("   ✅ Альбом отправлен")
            return True
        else:
            print(f"   ❌ Ошибка: {result.get('description', result)}")
            return False
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False

def send_post():
    """Отправляет серию постов в Telegram"""
    
    # 🔑 Токен
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN не найден!")
        return False
    
    channel = os.environ.get("TELEGRAM_CHANNEL", "@finanis")
    
    print("📊 Получаем данные рынка...")
    
    # Данные
    data = get_crypto()
    fear_greed = get_fear_greed_index()
    
    if not data:
        print("❌ Нет данных")
        return False
    
    try:
        btc = data["bitcoin"]["usd"]
        btc_ch = data["bitcoin"]["usd_24h_change"]
        eth = data["ethereum"]["usd"]
        eth_ch = data["ethereum"]["usd_24h_change"]
    except KeyError as e:
        print(f"❌ Нет данных: {e}")
        return False
    
    current_date = datetime.now().strftime('%d.%m.%Y')
    current_time = datetime.now().strftime('%H:%M МСК')
    
    # ====== ПОСТ 1: Индекс страха и графики ======
    print("\n📤 ПОСТ 1: Индекс страха")
    
    if fear_greed:
        fg_value = int(fear_greed["value"])
        fg_class = fear_greed["value_classification"]
        gauge_url = create_fear_greed_gauge(fg_value, fg_class)
        
        caption1 = (
            f"📊 <b>Крипто-рынок • {current_date}</b>\n"
            f"🕐 {current_time}\n\n"
            f"🎭 <b>Индекс страха:</b> {fg_value}/100\n"
            f"📊 {fg_class}\n\n"
            f"🌡 <b>Настроение:</b> {get_market_sentiment(btc_ch)}"
        )
        
        if gauge_url:
            send_telegram_photo(token, channel, gauge_url, caption1)
        else:
            send_telegram_message(token, channel, caption1)
    
    # ====== ПОСТ 2: Графики ======
    print("\n📤 ПОСТ 2: Графики BTC и ETH")
    
    btc_chart = create_price_chart("bitcoin", "Bitcoin", "#f7931a")
    eth_chart = create_price_chart("ethereum", "Ethereum", "#627eea")
    
    if btc_chart and eth_chart:
        photos = [
            (btc_chart, f"₿ <b>BTC:</b> ${btc:,.0f}\n{btc_ch:+.2f}% {signal(btc_ch)}"),
            (eth_chart, f"Ξ <b>ETH:</b> ${eth:,.0f}\n{eth_ch:+.2f}% {signal(eth_ch)}")
        ]
        send_media_group(token, channel, photos)
    else:
        text2 = (
            f"💎 <b>Основные активы:</b>\n\n"
            f"₿ BTC: ${btc:,.0f} ({btc_ch:+.2f}%)\n"
            f"Ξ ETH: ${eth:,.0f} ({eth_ch:+.2f}%)"
        )
        send_telegram_message(token, channel, text2)
    
    # ====== ПОСТ 3: Экономический календарь ======
    print("\n📤 ПОСТ 3: Экономический календарь")
    
    text3 = "📅 <b>Ключевые события:</b>\n\n"
    events = get_economic_calendar()
    for event, date in events.items():
        text3 += f"• {event}: {date}\n"
    
    text3 += "\n💡 <b>Факторы влияния:</b>\n"
    text3 += "• Решения центробанков по ставкам\n"
    text3 += "• Инфляция в США и ЕС\n"
    text3 += "• Индекс доллара DXY\n\n"
    text3 += "📌 <i>Следите за макроэкономикой</i>"
    
    send_telegram_message(token, channel, text3)
    
    # ====== ПОСТЫ 4-6: Новости с картинками ======
    print("\n📤 ПОСТЫ С НОВОСТЯМИ:")
    
    all_news = get_all_news()
    
    if all_news:
        # Перемешиваем и выбираем 5 лучших
        random.shuffle(all_news)
        top_news = all_news[:5]
        
        for i, news in enumerate(top_news, 1):
            print(f"\n📤 Новость {i}/5: {news['source']}")
            
            # Используем картинку из новости или создаём свою
            image_url = news.get("image", "")
            if not image_url:
                image_url = create_news_image(news["title"], news["source"])
            
            # Текст новости
            caption = (
                f"📰 <b>{news['title']}</b>\n\n"
                f"📍 Источник: {news['source']}\n"
                f"🔗 <a href='{news['link']}'>Читать полностью</a>"
            )
            
            send_telegram_photo(token, channel, image_url, caption)
    else:
        send_telegram_message(token, channel, "📰 Пока нет свежих новостей")
    
    print("\n✅ Все посты отправлены!")
    return True

if __name__ == "__main__":
    print("🚀 Запуск финансового бота...")
    print("=" * 40)
    
    success = send_post()
    
    print("=" * 40)
    if success:
        print("🎉 Готово!")
        exit(0)
    else:
        print("💥 Ошибка!")
        exit(1)
