import requests
from django.conf import settings

TELEGRAM_BOT_TOKEN = '8186097372:AAHqtIGf0VLrYkq1DuWqP5vzUJTURfxFFGE'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

def send_telegram_message(chat_id, message):
    """
    Send a message to a specific Telegram chat.
    
    Args:
        chat_id (str): The Telegram chat ID to send the message to
        message (str): The message text to send
    """
    try:
        response = requests.post(
            f'{TELEGRAM_API_URL}/sendMessage',
            json={
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def notify_training_request(request):
    """
    Send a notification about a new training request to the Telegram bot.
    
    Args:
        request (TrainingRequest): The training request object
    """
    message = (
        f"🔔 <b>Новая заявка на обучение</b>\n\n"
        f"👤 Сотрудник: {request.user.get_full_name() or request.user.username}\n"
        f"📚 Курс: {request.course.title}\n"
        f"⏰ Дата: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📝 Причина: {request.reason}\n\n"
        f"Для рассмотрения заявки перейдите в панель управления."
    )
    
    admin_chat_id = "1011836048"  # Your Telegram chat ID
    return send_telegram_message(admin_chat_id, message) 