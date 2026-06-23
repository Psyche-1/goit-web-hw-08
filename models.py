from mongoengine import Document, StringField, ListField, ReferenceField, connect

# Підключення до бази даних (замініть <connection_string> на ваш URL з MongoDB Atlas)
# connect(host="mongodb+srv://<username>:<password>@cluster.mongodb.net/myDatabase?retryWrites=true&w=majority")

class Author(Document):
    meta = {'collection': 'authors'}
    fullname = StringField(required=True, unique=True)
    born_date = StringField()
    born_location = StringField()
    description = StringField()

class Quote(Document):
    meta = {'collection': 'quotes'}
    tags = ListField(StringField())
    author = ReferenceField(Author, reverse_delete_rule=2)  # NULLIFY при видаленні автора
    quote = StringField(required=True)
