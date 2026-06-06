import os
import requests
from datetime import datetime

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
    """Получает важные финансовые новости о ставках и экономике"""
    # Используем бесплатный API новостей (можно заменить на свой ключ)
    url = "https://newsapi.org/v2/everything"
    
    # ⚠️ Получите бесплатный ключ на https://newsapi.org
    api_key = os.environ.get("NEWS_API_KEY", "")
    
    if not api_key:
        return None
    
    params = {
        "q": "interest rates OR federal reserve OR ECB OR central bank OR inflation OR ставка OR инфляция",
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
    """Получает важные экономические события (упрощённая версия)"""
    # Основные события на ближайшие дни
    today = datetime.now()
    
    events = {
        "ФРС": "Решение по ставке: 12.06.2024",
        "ЕЦБ": "Решение по ставке: 06.06.2024",
        "Данные CPI": f"Инфляция США: {today.strftime('%m')} месяц",
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

def send_post():
    """Отправляет пост в Telegram канал"""
    
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
    
    # Проверяем данные
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
    
    # 📝 Формируем сообщение
    current_date = datetime.now().strftime('%d.%m.%Y')
    current_time = datetime.now().strftime('%H:%M МСК')
    
    # Заголовок
    text = f"📊 <b>Крипто-рынок • {current_date}</b>\n"
    text += f"🕐 Обновлено: {current_time}\n\n"
    
    # Индекс страха и жадности
    if fear_greed:
        fg_value = fear_greed["value"]
        fg_class = fear_greed["value_classification"]
        
        if int(fg_value) < 30:
            fg_emoji = "🔴"
        elif int(fg_value) < 50:
            fg_emoji = "🟡"
        else:
            fg_emoji = "🟢"
            
        text += f"🎭 <b>Индекс страха:</b> {fg_emoji} {fg_value}/100 ({fg_class})\n\n"
    
    # Криптовалюты
    text += "💎 <b>Основные активы:</b>\n\n"
    
    text += f"₿ <b>Bitcoin:</b> ${btc:,.0f}\n"
    text += f"   Изменение: {btc_ch:+.2f}% {signal(btc_ch)}\n"
    text += f"   Капитализация: ${btc_mcap/1e9:,.1f}B\n\n"
    
    text += f"Ξ <b>Ethereum:</b> ${eth:,.0f}\n"
    text += f"   Изменение: {eth_ch:+.2f}% {signal(eth_ch)}\n"
    text += f"   Капитализация: ${eth_mcap/1e9:,.1f}B\n\n"
    
    # Настроение рынка
    text += f"🌡 <b>Настроение:</b> {get_market_sentiment(btc_ch)}\n\n"
    
    # Экономический календарь
    text += "📅 <b>Ключевые события:</b>\n"
    events = get_economic_calendar()
    for event, date in events.items():
        text += f"• {event}: {date}\n"
    
    text += "\n"
    
    # Финансовые новости
    news = get_financial_news()
    if news:
        text += "📰 <b>Важные новости:</b>\n\n"
        for i, article in enumerate(news[:3], 1):
            title = article.get("title", "Без заголовка")
            source = article.get("source", {}).get("name", "Источник")
            text += f"{i}. {title}\n"
            text += f"   📍 {source}\n\n"
    
    # Финансовый совет
    text += "💡 <b>На что обратить внимание:</b>\n"
    text += "• Решения центробанков по ставкам\n"
    text += "• Данные по инфляции в США и ЕС\n"
    text += "• Заседания ФРС и комментарии Пауэлла\n"
    text += "• Динамика индекса доллара (DXY)\n\n"
    
    text += "📌 <i>Не инвестируйте на эмоциях. Диверсифицируйте риски.</i>"
    
    # 📤 Отправляем сообщение
    telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            print(f"✅ Сообщение успешно отправлено в {channel}")
            return True
        else:
            print(f"❌ Telegram API вернул ошибку: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при отправке: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск бота...")
    success = send_post()
    
    if success:
        print("🎉 Работа завершена успешно")
        exit(0)
    else:
        print("💥 Работа завершена с ошибкой")
        exit(1)
