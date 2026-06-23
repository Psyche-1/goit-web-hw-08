import json
from mongoengine import connect
from models import Author, Quote

import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MY_SECRET_URL")

# Підключення до MongoDB Atlas
connect(host=uri)

def upload_data():
    # 1. Завантаження авторів
    with open('authors.json', 'r', encoding='utf-8') as f:
        authors_data = json.load(f)
        
    for auth_dict in authors_data:
        # Перевіряємо, чи автор вже існує, щоб уникнути дублікатів
        if not Author.objects(fullname=auth_dict['fullname']).first():
            Author(**auth_dict).save()
            print(f"Автор {auth_dict['fullname']} збережений.")

    # 2. Завантаження цитат
    with open('quotes.json', 'r', encoding='utf-8') as f:
        quotes_data = json.load(f)
        
    for q_dict in quotes_data:
        # Шукаємо автора в БД за іменем для отримання його ObjectID
        author_obj = Author.objects(fullname=q_dict['author']).first()
        
        if author_obj:
            # Створюємо цитату, замінивши рядок автора на об'єкт ReferenceField
            Quote(
                tags=q_dict['tags'],
                author=author_obj,
                quote=q_dict['quote']
            ).save()
            print(f"Цитату автора {author_obj.fullname} збережено.")
        else:
            print(f"Помилка: автора {q_dict['author']} не знайдено в базі!")

if __name__ == '__main__':
    upload_data()
