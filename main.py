import os
import requests
from datetime import datetime
import base64
from io import BytesIO

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
        "q": "interest rates OR federal reserve OR ECB OR central bank OR inflation OR криптовалюта OR биткоин",
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
        "Non-Farm": "Данные по занятости: первая пятница месяца"
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
        return "🟡 Умеренный оптимизм"
    elif btc_ch > 0:
        return "⚪ Нейтрально"
    elif btc_ch > -5:
        return "🟠 Страх"
    else:
        return "🔴 Сильный страх"

def create_price_chart(coin_id, coin_name):
    """
    Создаёт график цены через QuickChart API
    Бесплатно, не требует API ключа
    """
    # Получаем исторические данные за 7 дней
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": 7
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        prices = data["prices"]
        
        # Берём каждую 12-ю точку для графика (примерно каждые 6 часов)
        prices_simplified = prices[::12]
        labels = []
        values = []
        
        for timestamp, price in prices_simplified:
            dt = datetime.fromtimestamp(timestamp/1000)
            labels.append(dt.strftime('%d.%m'))
            values.append(round(price))
        
        # Создаём график через QuickChart
        chart_config = {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": f"{coin_name} (USD)",
                    "data": values,
                    "borderColor": "#f7931a" if coin_id == "bitcoin" else "#627eea",
                    "backgroundColor": "rgba(247, 147, 26, 0.1)" if coin_id == "bitcoin" else "rgba(98, 126, 234, 0.1)",
                    "borderWidth": 3,
                    "fill": True,
                    "tension": 0.4
                }]
            },
            "options": {
                "plugins": {
                    "title": {
                        "display": True,
                        "text": f"{coin_name} за 7 дней",
                        "color": "#ffffff",
                        "font": {
                            "size": 16
                        }
                    }
                },
                "scales": {
                    "yAxes": [{
                        "ticks": {
                            "color": "#999999",
                            "callback": "'$' + value"
                        }
                    }],
                    "xAxes": [{
                        "ticks": {
                            "color": "#999999"
                        }
                    }]
                },
                "legend": {
                    "display": False
                }
            }
        }
        
        import json
        chart_json = json.dumps(chart_config)
        chart_url = f"https://quickchart.io/chart?c={chart_json}&width=600&height=300&backgroundColor=transparent"
        
        return chart_url
        
    except Exception as e:
        print(f"❌ Ошибка создания графика для {coin_name}: {e}")
        return None

def create_fear_greed_chart():
    """Создаёт шкалу страха и жадности"""
    fng = get_fear_greed_index()
    if not fng:
        return None
    
    value = int(fng["value"])
    
    # Выбираем цвет в зависимости от значения
    if value < 30:
        color = "#ef5350"  # Красный
    elif value < 50:
        color = "#ffa726"  # Оранжевый
    else:
        color = "#66bb6a"  # Зелёный
    
    chart_config = {
        "type": "radialGauge",
        "data": {
            "datasets": [{
                "data": [value],
                "backgroundColor": color
            }]
        },
        "options": {
            "centerArea": {
                "displayText": True,
                "text": f"{value}",
                "fontSize": 40,
                "fontColor": "#ffffff"
            },
            "title": {
                "display": True,
                "text": "Индекс страха и жадности",
                "color": "#ffffff"
            }
        }
    }
    
    import json
    chart_json = json.dumps(chart_config)
    return f"https://quickchart.io/chart?c={chart_json}&width=400&height=250&backgroundColor=transparent"

def send_photo(token, channel, photo_url, caption=""):
    """Отправляет фото с подписью в Telegram"""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {
        "chat_id": channel,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json().get("ok", False)
    except:
        return False

def send_media_group(token, channel, media_list):
    """Отправляет группу изображений"""
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    payload = {
        "chat_id": channel,
        "media": media_list
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json().get("ok", False)
    except:
        return False

def send_post():
    """Отправляет серию постов в Telegram канал"""
    
    # 🔑 Получаем токен
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ Ошибка: BOT_TOKEN не найден!")
        return False
    
    channel = os.environ.get("TELEGRAM_CHANNEL", "@finanis")
    
    # 📊 Получаем данные
    data = get_crypto()
    fear_greed = get_fear_greed_index()
    
    if not data:
        print("❌ Не удалось получить данные о криптовалютах")
        return False
    
    try:
        btc = data["bitcoin"]["usd"]
        btc_ch = data["bitcoin"]["usd_24h_change"]
        btc_mcap = data["bitcoin"].get("usd_market_cap", 0)
        
        eth = data["ethereum"]["usd"]
        eth_ch = data["ethereum"]["usd_24h_change"]
        eth_mcap = data["ethereum"].get("usd_market_cap", 0)
    except KeyError as e:
        print(f"❌ Ошибка в структуре данных: {e}")
        return False
    
    current_date = datetime.now().strftime('%d.%m.%Y')
    current_time = datetime.now().strftime('%H:%M МСК')
    
    print("📊 Создаём графики...")
    
    # Создаём графики
    btc_chart = create_price_chart("bitcoin", "Bitcoin")
    eth_chart = create_price_chart("ethereum", "Ethereum")
    fng_chart = create_fear_greed_chart()
    
    # === ПОСТ 1: Индекс страха и жадности + Обзор ===
    print("📤 Отправляем пост 1...")
    
    text1 = f"📊 <b>Крипто-рынок • {current_date}</b>\n"
    text1 += f"🕐 {current_time}\n\n"
    
    if fear_greed:
        fg_value = fear_greed["value"]
        fg_class = fear_greed["value_classification"]
        text1 += f"🎭 <b>Индекс страха:</b> {fg_value}/100\n"
        text1 += f"📊 <i>{fg_class}</i>\n\n"
    
    text1 += f"🌡 <b>Настроение рынка:</b> {get_market_sentiment(btc_ch)}\n\n"
    text1 += "📌 <i>Не инвестируйте на эмоциях</i>"
    
    if fng_chart:
        send_photo(token, channel, fng_chart, text1)
    else:
        # Отправляем без картинки если не получилось
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": channel, "text": text1, "parse_mode": "HTML"}
        )
    
    # === ПОСТ 2: Графики BTC и ETH ===
    print("📤 Отправляем пост 2 (графики)...")
    
    if btc_chart and eth_chart:
        media = [
            {
                "type": "photo",
                "media": btc_chart,
                "caption": f"₿ <b>BTC:</b> ${btc:,.0f} ({btc_ch:+.2f}%) {signal(btc_ch)}",
                "parse_mode": "HTML"
            },
            {
                "type": "photo",
                "media": eth_chart,
                "caption": f"Ξ <b>ETH:</b> ${eth:,.0f} ({eth_ch:+.2f}%) {signal(eth_ch)}",
                "parse_mode": "HTML"
            }
        ]
        send_media_group(token, channel, media)
    else:
        # Если графики не создались, отправляем текстом
        text2 = "💎 <b>Основные активы:</b>\n\n"
        text2 += f"₿ Bitcoin: ${btc:,.0f}\n"
        text2 += f"   {btc_ch:+.2f}% {signal(btc_ch)}\n"
        text2 += f"   Кап.: ${btc_mcap/1e9:,.1f}B\n\n"
        text2 += f"Ξ Ethereum: ${eth:,.0f}\n"
        text2 += f"   {eth_ch:+.2f}% {signal(eth_ch)}\n"
        text2 += f"   Кап.: ${eth_mcap/1e9:,.1f}B"
        
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": channel, "text": text2, "parse_mode": "HTML"}
        )
    
    # === ПОСТ 3: Новости и события ===
    print("📤 Отправляем пост 3 (новости)...")
    
    text3 = "📅 <b>Ключевые события:</b>\n\n"
    events = get_economic_calendar()
    for event, date in events.items():
        text3 += f"• {event}: {date}\n"
    
    # Новости
    news = get_financial_news()
    if news:
        text3 += "\n📰 <b>Важные новости:</b>\n\n"
        for i, article in enumerate(news[:3], 1):
            title = article.get("title", "Без заголовка")
            source = article.get("source", {}).get("name", "Источник")
            text3 += f"{i}. {title}\n"
            text3 += f"   📍 {source}\n\n"
    
    text3 += "💡 <b>Факторы влияния:</b>\n"
    text3 += "• Решения центробанков по ставкам\n"
    text3 += "• Инфляция в США и ЕС\n"
    text3 += "• Индекс доллара (DXY)\n"
    text3 += "• Геополитическая ситуация\n\n"
    text3 += "📌 <i>Диверсифицируйте риски</i>"
    
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": channel, "text": text3, "parse_mode": "HTML", "disable_web_page_preview": True}
    )
    
    print("✅ Все посты отправлены!")
    return True

if __name__ == "__main__":
    print("🚀 Запуск бота...")
    success = send_post()
    
    if success:
        print("🎉 Работа завершена успешно")
        exit(0)
    else:
        print("💥 Работа завершена с ошибкой")
        exit(1)
