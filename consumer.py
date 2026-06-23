import pika
import time
from mongoengine import connect
from bson import ObjectId
from models_contact import Contact

import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MY_SECRET_URL")

# 1. Підключення до бази даних
connect(host=uri)

# 2. Підключення до RabbitMQ
credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters(host='localhost', port=5672, credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

queue_name = 'email_queue'
channel.queue_declare(queue=queue_name, durable=True)

def fake_send_email(contact):
    """ Функція-заглушка для імітації надсилання email """
    print(f"[EMAIL SENDER] Надсилання листа для: {contact.fullname} ({contact.email})...")
    # Імітуємо затримку мережі (наприклад, 1 секунда)
    time.sleep(1)
    print(f"[EMAIL SENDER] Лист успішно надіслано на {contact.email}!")

def callback(ch, method, properties, body):
    # RabbitMQ передає дані в байтах, тому декодуємо в рядок
    contact_id_str = body.decode()
    print(f"\n[CONSUMER] Отримано ID з черги: {contact_id_str}")
    
    try:
        # Шукаємо контакт в MongoDB за отриманим ObjectID
        contact = Contact.objects(id=ObjectId(contact_id_str)).first()
        
        if contact:
            # Якщо контакт знайдено і йому ще не надсилали листа
            if not contact.is_sent:
                fake_send_email(contact)
                
                # Оновлюємо статус в базі даних на True
                contact.is_sent = True
                contact.save()
                print(f"[DATABASE] Статус контакту {contact_id_str} змінено на is_sent=True.")
            else:
                print(f"[INFO] Лист для контакту {contact_id_str} вже було надіслано раніше.")
        else:
            print(f"[ERROR] Контакт з ID {contact_id_str} не знайдено в MongoDB.")
            
    except Exception as e:
        print(f"[ERROR] Помилка обробки контакту: {e}")
        
    # Підтверджуємо успішну обробку повідомлення, щоб RabbitMQ видалив його з черги
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Налаштовуємо RabbitMQ так, щоб консюмер не брав більше 1 повідомлення одночасно
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=callback)

print("[-] Скрипт consumer.py запущено. Очікування повідомлень. Для виходу натисніть CTRL+C")
channel.start_consuming()
