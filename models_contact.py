from mongoengine import Document, StringField, BooleanField, connect

class Contact(Document):
    meta = {'collection': 'contacts'}
    fullname = StringField(required=True)
    email = StringField(required=True)
    phone_number = StringField(required=True)  # Нове поле для телефону
    preferred_method = StringField(choices=['sms', 'email'], required=True)  # Спосіб надсилання
    is_sent = BooleanField(default=False)
    message_body = StringField()
