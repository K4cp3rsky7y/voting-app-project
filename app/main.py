"""
Voting Application - Flask Backend
Aplikacja do głosowania z wykorzystaniem Redis i RabbitMQ
"""

from flask import Flask, request, render_template, jsonify
import os
import redis
import pika
import json
import logging
from datetime import datetime

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Konfiguracja z zmiennych środowiskowych
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'admin123')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'votes')

# Opcje głosowania
VOTE_OPTION_1 = os.getenv('VOTE_OPTION_1', 'Python')
VOTE_OPTION_2 = os.getenv('VOTE_OPTION_2', 'JavaScript')
APP_TITLE = os.getenv('APP_TITLE', 'Voting App - Projekt Zaliczeniowy')

# Połączenie z Redis
try:
    if REDIS_PASSWORD:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
    else:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
    redis_client.ping()
    logger.info("Połączono z Redis")
except redis.ConnectionError as e:
    logger.error(f"Błąd połączenia z Redis: {e}")
    redis_client = None

RECENT_VOTES_KEY = "recent_votes"
FAN_MESSAGES_KEY = "fan_messages"
MAX_RECENT_VOTES = 20
MAX_FAN_MESSAGES = 50


def init_redis():
    """Inicjalizuje wartości głosów i struktur pomocniczych w Redis jeśli nie istnieją"""
    if not redis_client:
        return

    # Liczniki głosów
    if not redis_client.exists(VOTE_OPTION_1):
        redis_client.set(VOTE_OPTION_1, 0)
    if not redis_client.exists(VOTE_OPTION_2):
        redis_client.set(VOTE_OPTION_2, 0)

    # Listy pomocnicze
    if not redis_client.exists(RECENT_VOTES_KEY):
        redis_client.delete(RECENT_VOTES_KEY)
    if not redis_client.exists(FAN_MESSAGES_KEY):
        redis_client.delete(FAN_MESSAGES_KEY)

    logger.info("Zainicjalizowano wartości w Redis")

# Funkcja do wysyłania głosu do RabbitMQ
def send_vote_to_queue(vote_option, timestamp):
    """Wysyła głos do kolejki RabbitMQ do asynchronicznego przetwarzania"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Deklaracja kolejki
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        # Przygotowanie wiadomości
        message = {
            'option': vote_option,
            'timestamp': timestamp,
            'ip': request.remote_addr
        }
        
        # Wysłanie wiadomości
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Uczynienie wiadomości trwałą
            )
        )
        
        connection.close()
        logger.info(f"Wysłano głos '{vote_option}' do kolejki RabbitMQ")
        return True
    except Exception as e:
        logger.error(f"Błąd wysyłania do RabbitMQ: {e}")
        return False

# Funkcja do przetwarzania głosu z Redis
def process_vote(vote_option):
    """Przetwarza głos bezpośrednio w Redis"""
    if redis_client:
        try:
            redis_client.incr(vote_option)

            # Zapamiętaj ostatni głos (lista ograniczona do MAX_RECENT_VOTES)
            vote_entry = {
                "option": vote_option,
                "timestamp": datetime.now().isoformat(),
                "ip": request.remote_addr,
            }
            redis_client.lpush(RECENT_VOTES_KEY, json.dumps(vote_entry))
            redis_client.ltrim(RECENT_VOTES_KEY, 0, MAX_RECENT_VOTES - 1)

            logger.info(f"Zaktualizowano głos dla '{vote_option}'")
            return True
        except Exception as e:
            logger.error(f"Błąd przetwarzania głosu: {e}")
            return False
    return False

@app.route('/')
def index():
    """Strona główna z formularzem głosowania"""
    if redis_client:
        init_redis()
        vote1 = int(redis_client.get(VOTE_OPTION_1) or 0)
        vote2 = int(redis_client.get(VOTE_OPTION_2) or 0)
        # Początkowe dane do wyświetlenia ostatnich głosów i ściany kibica
        recent_votes_raw = redis_client.lrange(RECENT_VOTES_KEY, 0, MAX_RECENT_VOTES - 1)
        fan_messages_raw = redis_client.lrange(FAN_MESSAGES_KEY, 0, MAX_FAN_MESSAGES - 1)

        recent_votes = []
        for item in recent_votes_raw:
            try:
                recent_votes.append(json.loads(item))
            except json.JSONDecodeError:
                continue

        fan_messages = []
        for item in fan_messages_raw:
            try:
                fan_messages.append(json.loads(item))
            except json.JSONDecodeError:
                continue
    else:
        vote1 = 0
        vote2 = 0
        recent_votes = []
        fan_messages = []
    
    return render_template(
        'index.html',
        title=APP_TITLE,
        option1=VOTE_OPTION_1,
        option2=VOTE_OPTION_2,
        vote1=vote1,
        vote2=vote2,
        total=vote1 + vote2,
        recent_votes=recent_votes,
        fan_messages=fan_messages,
    )

@app.route('/vote', methods=['POST'])
def vote():
    """Endpoint do głosowania"""
    vote_option = request.form.get('vote')
    timestamp = datetime.now().isoformat()
    
    if vote_option not in [VOTE_OPTION_1, VOTE_OPTION_2]:
        return jsonify({'error': 'Nieprawidłowa opcja głosowania'}), 400
    
    # Wysłanie do kolejki RabbitMQ (asynchroniczne przetwarzanie)
    send_vote_to_queue(vote_option, timestamp)
    
    # Bezpośrednie przetwarzanie w Redis (synchroniczne)
    process_vote(vote_option)
    
    # Pobranie aktualnych wyników
    if redis_client:
        vote1 = int(redis_client.get(VOTE_OPTION_1) or 0)
        vote2 = int(redis_client.get(VOTE_OPTION_2) or 0)
    else:
        vote1 = 0
        vote2 = 0
    
    return jsonify({
        'success': True,
        'option1': VOTE_OPTION_1,
        'option2': VOTE_OPTION_2,
        'vote1': vote1,
        'vote2': vote2,
        'total': vote1 + vote2
    })

@app.route('/reset', methods=['POST'])
def reset():
    """Resetuje wszystkie głosy"""
    if redis_client:
        redis_client.set(VOTE_OPTION_1, 0)
        redis_client.set(VOTE_OPTION_2, 0)
        redis_client.delete(RECENT_VOTES_KEY)
        logger.info("Zresetowano głosy")
    
    return jsonify({'success': True, 'message': 'Głosy zostały zresetowane'})

@app.route('/api/stats', methods=['GET'])
def stats():
    """API endpoint zwracający statystyki głosowania"""
    if redis_client:
        vote1 = int(redis_client.get(VOTE_OPTION_1) or 0)
        vote2 = int(redis_client.get(VOTE_OPTION_2) or 0)
        total = vote1 + vote2
        
        return jsonify({
            'option1': VOTE_OPTION_1,
            'option2': VOTE_OPTION_2,
            'vote1': vote1,
            'vote2': vote2,
            'total': total,
            'percentage1': round((vote1 / total * 100) if total > 0 else 0, 2),
            'percentage2': round((vote2 / total * 100) if total > 0 else 0, 2)
        })
    else:
        return jsonify({'error': 'Redis nie jest dostępny'}), 500


@app.route('/api/recent_votes', methods=['GET'])
def recent_votes():
    """Zwraca listę ostatnich głosów"""
    if not redis_client:
        return jsonify({'error': 'Redis nie jest dostępny'}), 500

    items = redis_client.lrange(RECENT_VOTES_KEY, 0, MAX_RECENT_VOTES - 1)
    votes = []
    for item in items:
        try:
            votes.append(json.loads(item))
        except json.JSONDecodeError:
            continue

    return jsonify(votes)


@app.route('/fan-message', methods=['POST'])
def fan_message():
    """Dodaje wiadomość kibica do ściany"""
    if not redis_client:
        return jsonify({'error': 'Redis nie jest dostępny'}), 500

    name = request.form.get('name', '').strip() or 'Anonim'
    message = request.form.get('message', '').strip()
    team = request.form.get('team', '').strip()

    if not message:
        return jsonify({'error': 'Wiadomość nie może być pusta'}), 400

    if team not in [VOTE_OPTION_1, VOTE_OPTION_2]:
        return jsonify({'error': 'Nieprawidłowy klub'}), 400

    entry = {
        'name': name,
        'message': message,
        'team': team,
        'timestamp': datetime.now().isoformat(),
    }

    try:
        redis_client.lpush(FAN_MESSAGES_KEY, json.dumps(entry))
        redis_client.ltrim(FAN_MESSAGES_KEY, 0, MAX_FAN_MESSAGES - 1)
        logger.info(f"Dodano wiadomość kibica dla '{team}'")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Błąd zapisu wiadomości kibica: {e}")
        return jsonify({'error': 'Nie udało się zapisać wiadomości'}), 500


@app.route('/api/fan_messages', methods=['GET'])
def fan_messages_api():
    """Zwraca listę wiadomości kibiców"""
    if not redis_client:
        return jsonify({'error': 'Redis nie jest dostępny'}), 500

    items = redis_client.lrange(FAN_MESSAGES_KEY, 0, MAX_FAN_MESSAGES - 1)
    messages = []
    for item in items:
        try:
            messages.append(json.loads(item))
        except json.JSONDecodeError:
            continue

    return jsonify(messages)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    redis_status = 'ok' if redis_client and redis_client.ping() else 'error'
    
    return jsonify({
        'status': 'ok',
        'redis': redis_status,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    init_redis()
    app.run(host='0.0.0.0', port=5000, debug=True)
