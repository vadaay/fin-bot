import os
import requests
from datetime import datetime
import json

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

def get_financial_news():
    """Получает важные финансовые новости"""
    api_key = os.environ.get("NEWS_API_KEY", "")
    
    if not api_key:
        return None
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "ставка OR инфляция OR биткоин OR криптовалюта OR фрс",
        "language": "ru",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
    except:
        return None

def get_economic_calendar():
    """Получает важные экономические события"""
    events = {
        "ФРС": "Решение по ставке: 12.06.2024",
        "ЕЦБ": "Решение по ставке: 06.06.2024",
        "Данные CPI": "Инфляция США: ежемесячно",
        "Non-Farm": "Занятость США: первая пятница месяца"
    }
    return events

def signal(change):
    """Определяет сигнал на основе изменения цены"""
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
    """Определяет настроение рынка"""
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
    """Создаёт график цены через QuickChart API"""
    try:
        # Получаем данные за 7 дней
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 7}
        
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        prices = data["prices"]
        
        # Упрощаем для графика (каждая 8-я точка)
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
        
        # Конфигурация графика
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
                    "legend": {
                        "display": False
                    }
                },
                "scales": {
                    "y": {
                        "ticks": {
                            "color": "#cccccc",
                            "callback": "function(value) { return '$' + value.toLocaleString(); }"
                        },
                        "grid": {
                            "color": "#333333"
                        }
                    },
                    "x": {
                        "ticks": {
                            "color": "#cccccc"
                        },
                        "grid": {
                            "color": "#333333"
                        }
                    }
                }
            }
        }
        
        # Создаём URL для графика
        chart_json = json.dumps(chart_config)
        chart_url = f"https://quickchart.io/chart?c={chart_json}&width=600&height=350&backgroundColor=%231a1a2e"
        
        return chart_url
        
    except Exception as e:
        print(f"❌ Не удалось создать график для {coin_name}: {e}")
        return None

def create_fear_greed_gauge(value, classification):
    """Создаёт шкалу страха и жадности"""
    # Цвет в зависимости от значения
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
                "fontColor": "#ffffff",
                "fontFamily": "Arial"
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
            },
            "needle": {
                "color": "#ffffff"
            }
        }
    }
    
    try:
        chart_json = json.dumps(chart_config)
        return f"https://quickchart.io/chart?c={chart_json}&width=400&height=350&backgroundColor=%231a1a2e"
    except Exception as e:
        print(f"❌ Ошибка создания шкалы: {e}")
        return None

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
            print(f"   ❌ Ошибка: {result}")
            return False
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False

def send_telegram_message(token, channel, text):
    """Отправка текста в Telegram"""
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
            print(f"   ❌ Ошибка: {result}")
            return False
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False

def send_media_group(token, channel, photos):
    """Отправка группы фото (альбом)"""
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
            print(f"   ❌ Ошибка: {result}")
            return False
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False

def send_post():
    """Отправляет посты с картинками в Telegram"""
    
    # 🔑 Токен
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN не найден!")
        return False
    
    channel = os.environ.get("TELEGRAM_CHANNEL", "@finanis")
    
    print("📊 Получаем данные...")
    
    # Данные
    data = get_crypto()
    fear_greed = get_fear_greed_index()
    
    if not data:
        print("❌ Нет данных о криптовалютах")
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
    
    # ====== ПОСТ 1: Индекс страха и жадности ======
    print("\n📤 ПОСТ 1: Индекс страха и жадности")
    
    if fear_greed:
        fg_value = int(fear_greed["value"])
        fg_class = fear_greed["value_classification"]
        
        # Создаём шкалу
        gauge_url = create_fear_greed_gauge(fg_value, fg_class)
        
        caption1 = (
            f"📊 <b>Крипто-рынок • {current_date}</b>\n"
            f"🕐 {current_time}\n\n"
            f"🎭 <b>Индекс страха и жадности:</b>\n"
            f"<b>{fg_value}/100 — {fg_class}</b>\n\n"
            f"🌡 <b>Настроение рынка:</b> {get_market_sentiment(btc_ch)}\n\n"
            f"📌 <i>Когда все боятся — покупай\n"
            f"Когда все жадничают — продавай</i>"
        )
        
        if gauge_url:
            send_telegram_photo(token, channel, gauge_url, caption1)
        else:
            send_telegram_message(token, channel, caption1)
    else:
        caption1 = (
            f"📊 <b>Крипто-рынок • {current_date}</b>\n"
            f"🕐 {current_time}\n\n"
            f"🌡 <b>Настроение рынка:</b> {get_market_sentiment(btc_ch)}"
        )
        send_telegram_message(token, channel, caption1)
    
    # ====== ПОСТ 2: Графики BTC и ETH ======
    print("\n📤 ПОСТ 2: Графики")
    
    btc_chart_url = create_price_chart("bitcoin", "Bitcoin", "#f7931a")
    eth_chart_url = create_price_chart("ethereum", "Ethereum", "#627eea")
    
    if btc_chart_url and eth_chart_url:
        # Отправляем альбом
        photos = [
            (btc_chart_url, f"₿ <b>Bitcoin:</b> ${btc:,.0f}\n{btc_ch:+.2f}% {signal(btc_ch)}"),
            (eth_chart_url, f"Ξ <b>Ethereum:</b> ${eth:,.0f}\n{eth_ch:+.2f}% {signal(eth_ch)}")
        ]
        send_media_group(token, channel, photos)
    else:
        # Текстовый вариант
        text2 = (
            f"💎 <b>Основные активы:</b>\n\n"
            f"₿ <b>Bitcoin:</b> ${btc:,.0f}\n"
            f"   {btc_ch:+.2f}% {signal(btc_ch)}\n\n"
            f"Ξ <b>Ethereum:</b> ${eth:,.0f}\n"
            f"   {eth_ch:+.2f}% {signal(eth_ch)}"
        )
        send_telegram_message(token, channel, text2)
    
    # ====== ПОСТ 3: Новости и события ======
    print("\n📤 ПОСТ 3: Новости и события")
    
    text3 = "📅 <b>Ключевые события:</b>\n\n"
    events = get_economic_calendar()
    for event, date in events.items():
        text3 += f"• <b>{event}:</b> {date}\n"
    
    # Новости
    news = get_financial_news()
    if news:
        text3 += "\n📰 <b>Важные новости:</b>\n\n"
        count = 0
        for article in news:
            if count >= 3:
                break
            title = article.get("title", "")
            source = article.get("source", {}).get("name", "")
            url_article = article.get("url", "")
            
            if title and source:
                text3 += f"• {title}\n"
                text3 += f"  📍 {source}\n\n"
                count += 1
    
    text3 += "💡 <b>Факторы влияния на рынок:</b>\n"
    text3 += "• Ставки центробанков (ФРС, ЕЦБ)\n"
    text3 += "• Данные по инфляции CPI\n"
    text3 += "• Индекс доллара DXY\n"
    text3 += "• Новости регулирования\n\n"
    text3 += "📌 <i>Думай долгосрочно, не паникуй</i>"
    
    send_telegram_message(token, channel, text3)
    
    print("\n✅ Все посты отправлены!")
    return True

if __name__ == "__main__":
    print("🚀 Запуск финансового бота...")
    print("=" * 40)
    
    success = send_post()
    
    print("=" * 40)
    if success:
        print("🎉 Готово! Все посты в канале")
        exit(0)
    else:
        print("💥 Ошибка при отправке")
        exit(1)
