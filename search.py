import sys
import json
import redis
from mongoengine import connect
from models import Author, Quote

import os
from dotenv import load_dotenv

# Налаштування виведення консолі в UTF-8
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

uri = os.getenv("MY_SECRET_URL")

# Підключення до MongoDB Atlas
connect(host=uri)

# Підключення до Redis (локально або через Cloud URL)
# Якщо використовуєте хмарний Redis, замініть параметри на host='...', port=..., password='...'
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_cached_or_db(cache_key, search_type, search_value):
    """
    Перевіряє наявність даних у кеші Redis.
    Якщо даних немає — робить запит до MongoDB, серіалізує в JSON,
    записує в Redis із терміном дії (TTL) 1 година та повертає результат.
    """
    # 1. Спроба взяти дані з кешу Redis
    cached_data = redis_client.get(cache_key)
    if cached_data:
        print("[REDIS CACHE] Результат взято з кешу:")
        return json.loads(cached_data)

    # 2. Якщо в кеші порожньо — шукаємо в MongoDB
    print("[MONGODB] Кеш порожній. Робимо запит до бази даних:")
    results = []

    if search_type == 'name':
        # Пошук за регулярним виразом: ^ означає "починається з", i означає "ігнорувати регістр"
        authors = Author.objects(fullname__istartswith=search_value)
        for author in authors:
            quotes = Quote.objects(author=author)
            for q in quotes:
                results.append(f"- {q.quote} (Автор: {author.fullname})")

    elif search_type == 'tag':
        # Пошук за префіксом тегу (ігноруючи регістр)
        quotes = Quote.objects(tags__istartswith=search_value)
        for q in quotes:
            results.append(f"- {q.quote} (Автор: {q.author.fullname})")

    # 3. Зберігаємо знайдені результати в Redis на 3600 секунд (1 година)
    if results:
        redis_client.setex(cache_key, 3600, json.dumps(results))
    
    return results

def search_quotes():
    print("Консольний пошук (з Redis-кешуванням та автодоповненням) запущено.")
    print("Доступні команди: name, tag, tags, exit.")
    
    while True:
        try:
            user_input = input("\nВведіть команду: ").strip()
            
            if not user_input:
                continue
                
            if user_input == 'exit':
                print("Завершення роботи.")
                break

            if ':' not in user_input:
                print("Некоректний формат. Використовуйте 'команда: значення'")
                continue
                
            command, value = user_input.split(':', 1)
            command = command.strip().lower()
            value = value.strip()

            if not value:
                print("Значення для пошуку не може бути порожнім.")
                continue

            # Створюємо унікальний ключ для Redis (наприклад, "search:name:st" або "search:tag:li")
            cache_key = f"search:{command}:{value.lower()}"

            # Обробка команд name та tag (з кешуванням)
            if command in ['name', 'tag']:
                quotes_list = get_cached_or_db(cache_key, command, value)
                
                if quotes_list:
                    for quote in quotes_list:
                        print(quote)
                else:
                    print("За вашим запитом нічого не знайдено.")

            # Обробка команди tags (без обов'язкового кешування, як у ТЗ)
            elif command == 'tags':
                tag_list = value.split(',')
                # Створюємо регулярні вирази для пошуку кожного тегу за початком слова
                # (для відповідності поведінці скороченого запису)
                quotes = Quote.objects(tags__in=tag_list)
                if quotes:
                    for q in quotes:
                        print(f"- {q.quote} (Автор: {q.author.fullname})")
                else:
                    print("Цитат із такими тегами не знайдено.")
            
            else:
                print(f"Невідома команда: {command}")
                
        except Exception as e:
            print(f"Сталася помилка під час виконання: {e}")

if __name__ == '__main__':
    search_quotes()
