import pika
import random
from mongoengine import connect
from faker import Faker
from models_contact import Contact

import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MY_SECRET_URL")

# 1. Підключення до БД
connect(host=uri)

# 2. Підключення до RabbitMQ
credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters(host='localhost', port=5672, credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Оголошуємо дві окремі черги
channel.queue_declare(queue='sms_queue', durable=True)
channel.queue_declare(queue='email_queue', durable=True)

fake = Faker()

def generate_and_route_contacts(count=12):
    print(f"Починаємо генерацію {count} контактів з розподілом за чергами...")
    
    for _ in range(count):
        # Випадково обираємо кращий спосіб надсилання
        method = random.choice(['sms', 'email'])
        
        contact = Contact(
            fullname=fake.name(),
            email=fake.email(),
            phone_number=fake.phone_number(),
            preferred_method=method,
            message_body=fake.text(max_nb_chars=50)
        )
        contact.save()
        
        contact_id_str = str(contact.id)
        
        # Визначаємо цільову чергу на основі preferred_method
        target_queue = 'sms_queue' if method == 'sms' else 'email_queue'
        
        channel.basic_publish(
            exchange='',
            routing_key=target_queue,
            body=contact_id_str,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"[PRODUCER] Контакт {contact.fullname} ({method}) -> Черга {target_queue}")

    connection.close()
    print("Генерацію та розподіл контактів завершено.")

if __name__ == '__main__':
    generate_and_route_contacts(12)
