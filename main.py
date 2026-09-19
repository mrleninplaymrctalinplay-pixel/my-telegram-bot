import os
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Ваши данные
TOKEN = os.getenv('BOT_TOKEN', 'ВАШ_ТОКЕН_БОТА')
ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID', '-1001234567890')) # ID вашей группы админов

app = Flask(__name__)
CORS(app) # Разрешает запросы с GitHub Pages

@app.route('/')
def home():
    return "GreeLand Bot Server is running!", 200

# Эндпоинт для приема заявок/жалоб из Mini App
@app.route('/api/submit', methods=['POST'])
def handle_submit():
    try:
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'No data'}), 400

        content = data.get('content', '')
        image = data.get('image', None)

        if image:
            # Если есть скриншот, отправляем как фото с подписью
            header, encoded = image.split(",", 1)
            image_data = base64.b64decode(encoded)
            
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            files = {'photo': ('screenshot.jpg', image_data, 'image/jpeg')}
            data_payload = {'chat_id': ADMIN_GROUP_ID, 'caption': content, 'parse_mode': 'HTML'}
            
            response = requests.post(url, data=data_payload, files=files)
        else:
            # Если только текст
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data_payload = {
                'chat_id': ADMIN_GROUP_ID, 
                'text': content, 
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data_payload)

        if response.status_code == 200:
            return jsonify({'status': 'success'})
        else:
            print(f"Telegram API Error: {response.text}")
            return jsonify({'status': 'error', 'message': 'Telegram API error'}), 500

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
