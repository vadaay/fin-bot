import os
import requests
from datetime import datetime

def get_crypto():
    """Получает данные о криптовалютах с CoinGecko"""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Проверяем на HTTP ошибки
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе к CoinGecko: {e}")
        return None

def signal(change):
    """Определяет сигнал на основе изменения цены"""
    if change > 2:
        return "🟢 Рост"
    elif change > 0:
        return "📈 Плюс"
    elif change > -2:
        return "🔴 Минус"
    else:
        return "📉 Сильное падение"

def send_post():
    """Отправляет пост в Telegram канал"""
    
    # 🔑 Безопасно получаем токен из переменных окружения
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ Ошибка: BOT_TOKEN не найден в переменных окружения!")
        print("💡 Убедитесь, что секрет добавлен в GitHub Secrets")
        return False
    
    # 🔑 Получаем канал (можно тоже через переменную окружения)
    channel = os.environ.get("TELEGRAM_CHANNEL", "@finanis")
    
    # 📊 Получаем данные о криптовалютах
    data = get_crypto()
    if not data:
        print("❌ Не удалось получить данные о криптовалютах")
        return False
    
    # Проверяем структуру данных
    try:
        btc = data["bitcoin"]["usd"]
        btc_ch = data["bitcoin"]["usd_24h_change"]
        
        eth = data["ethereum"]["usd"]
        eth_ch = data["ethereum"]["usd_24h_change"]
    except KeyError as e:
        print(f"❌ Ошибка в структуре данных: отсутствует ключ {e}")
        print(f"📊 Полученные данные: {data}")
        return False
    
    # 📝 Формируем сообщение
    current_date = datetime.now().strftime('%d.%m.%Y')
    text = (
        f"📊 Крипто-рынок • {current_date}\n\n"
        f"₿ BTC: ${btc:,.2f} ({btc_ch:+.2f}%) {signal(btc_ch)}\n"
        f"Ξ ETH: ${eth:,.2f} ({eth_ch:+.2f}%) {signal(eth_ch)}\n\n"
        f"📌 Не инвестируйте на эмоциях"
    )
    
    # 📤 Отправляем сообщение в Telegram
    telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel,
        "text": text,
        "parse_mode": "HTML"
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
        print(f"❌ Ошибка при отправке в Telegram: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
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
