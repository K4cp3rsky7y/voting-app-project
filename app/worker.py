"""
Worker do przetwarzania wiadomości z RabbitMQ
Opcjonalny komponent do asynchronicznego przetwarzania głosów
"""

import os
import json
import redis
import pika
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfiguracja
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'admin123')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'votes')

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
    logger.info("Worker: Połączono z Redis")
except redis.ConnectionError as e:
    logger.error(f"Worker: Błąd połączenia z Redis: {e}")
    redis_client = None

def process_vote(ch, method, properties, body):
    """Przetwarza głos z kolejki RabbitMQ"""
    try:
        message = json.loads(body)
        vote_option = message.get('option')
        timestamp = message.get('timestamp')
        ip = message.get('ip')
        
        logger.info(f"Worker: Przetwarzanie głosu - Opcja: {vote_option}, IP: {ip}, Czas: {timestamp}")
        
        if redis_client and vote_option:
            redis_client.incr(vote_option)
            logger.info(f"Worker: Zaktualizowano głos dla '{vote_option}'")
        
        # Potwierdzenie przetworzenia wiadomości
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except json.JSONDecodeError as e:
        logger.error(f"Worker: Błąd parsowania JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Worker: Błąd przetwarzania głosu: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_worker():
    """Uruchamia worker do przetwarzania wiadomości"""
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
        
        # Ustawienie QoS - przetwarzanie jednej wiadomości na raz
        channel.basic_qos(prefetch_count=1)
        
        # Konfiguracja konsumenta
        channel.basic_consume(
            queue=RABBITMQ_QUEUE,
            on_message_callback=process_vote
        )
        
        logger.info("Worker: Oczekiwanie na wiadomości. Aby zatrzymać naciśnij CTRL+C")
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Worker: Zatrzymywanie workera...")
        channel.stop_consuming()
        connection.close()
    except Exception as e:
        logger.error(f"Worker: Błąd uruchomienia: {e}")

if __name__ == '__main__':
    start_worker()
