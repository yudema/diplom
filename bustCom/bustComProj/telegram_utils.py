import requests
from django.conf import settings

TELEGRAM_BOT_TOKEN = '8186097372:AAHqtIGf0VLrYkq1DuWqP5vzUJTURfxFFGE'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

def send_telegram_message(chat_id, message):

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

    message = (
        f"🔔 <b>Новая заявка на обучение</b>\n\n"
        f"👤 Сотрудник: {request.user.get_full_name() or request.user.username}\n"
        f"📚 Курс: {request.course.title}\n"
        f"⏰ Дата: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📝 Причина: {request.reason}\n\n"
        f"Для рассмотрения заявки перейдите в панель управления."
    )
    
    admin_chat_id = "1011836048"  
    return send_telegram_message(admin_chat_id, message) 