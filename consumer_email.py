import pika
import time
from mongoengine import connect
from bson import ObjectId
from models_contact import Contact
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MY_SECRET_URL")

connect(host=uri)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', port=5672))
channel = connection.channel()
channel.queue_declare(queue='email_queue', durable=True)

def fake_send_email(contact):
    print(f"[EMAIL SENDER] Надсилання листа на {contact.email} для {contact.fullname}...")
    time.sleep(1)
    print(f"[EMAIL SENDER] Лист успішно надіслано на {contact.email}!")

def callback(ch, method, properties, body):
    contact_id_str = body.decode()
    print(f"\n[CONSUMER EMAIL] Отримано ID: {contact_id_str}")
    
    try:
        contact = Contact.objects(id=ObjectId(contact_id_str)).first()
        if contact and not contact.is_sent:
            fake_send_email(contact)
            contact.is_sent = True
            contact.save()
            print(f"[DATABASE] Статус контакту {contact_id_str} оновлено: is_sent=True.")
    except Exception as e:
        print(f"[ERROR] Помилка: {e}")
        
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='email_queue', on_message_callback=callback)

print("[-] Скрипт consumer_email.py запущено. Очікування Email повідомлень...")
channel.start_consuming()
