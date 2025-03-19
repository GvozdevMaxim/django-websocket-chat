import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from .models import Room, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Подключение пользователя к комнате"""
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]  # Динамическое имя комнаты из URL
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]  # Получаем пользователя

        print(f"[CONNECT] Пользователь {self.user} подключается к комнате {self.room_name}")

        # Проверяем, существует ли комната
        self.room = await sync_to_async(Room.objects.filter(name=self.room_name).first)()
        if not self.room:
            print(f"[ERROR] Комната {self.room_name} не найдена. Отключение пользователя {self.user}.")
            await self.close()
            return

        # Проверяем, состоит ли пользователь в комнате
        is_member = await sync_to_async(lambda: self.room.users.filter(id=self.user.id).exists())()
        print(f"[DEBUG] Проверка участия {self.user} в комнате {self.room_name}: {is_member}")

        if not is_member:
            print(f"[ERROR] Пользователь {self.user} не является участником комнаты {self.room_name}. Отключение.")
            await self.close()
            return

        # Добавляем пользователя в WebSocket-группу
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        print(f"[SUCCESS] Пользователь {self.user} успешно подключился к комнате {self.room_name}")

        # Отправляем историю сообщений
        await self.send_chat_history()

    async def disconnect(self, close_code):
        """Отключение пользователя"""
        print(f"[DISCONNECT] Пользователь {self.user} покидает комнату {self.room_name}")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Получение сообщения от клиента"""
        print(f"[RECEIVE] Сообщение от пользователя {self.user}: {text_data}")

        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()

            if not message:
                print(f"[WARNING] Пользователь {self.user} отправил пустое сообщение.")
                return

            # Сохраняем сообщение в базу данных
            msg = await self.save_message(self.user, self.room, message)
            print(f"[DB] Сообщение сохранено в базе: {msg.text}")

            # Рассылаем сообщение всем участникам комнаты
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "user": self.user.username,
                    "message": msg.text,
                    "timestamp": str(msg.time_create)
                }
            )
            print(f"[BROADCAST] Сообщение отправлено в чат {self.room_name}")

        except Exception as e:
            print(f"[ERROR] Ошибка при обработке сообщения: {e}")

    async def chat_message(self, event):
        """Отправка сообщений клиентам"""
        print(f"[SEND] Отправка сообщения пользователям в комнате {self.room_name}")

        try:
            await self.send(text_data=json.dumps({
                "type": "chat_message",
                "user": event["user"],
                "message": event["message"],
                "timestamp": event["timestamp"]
            }))
        except Exception as e:
            print(f"[ERROR] Ошибка при отправке сообщения: {e}")

    async def send_chat_history(self):
        """Отправка истории сообщений при подключении"""
        messages = await sync_to_async(list)(
            Message.objects.filter(room=self.room).select_related("user").order_by("time_create")[:50]
        )

        print(f"[DEBUG] Найдено {len(messages)} сообщений для комнаты {self.room.name}")

        for msg in messages:
            user_username = await sync_to_async(lambda: msg.user.username)()  # Получаем username асинхронно
            print(f"[DEBUG] Отправка сообщения: {user_username}: {msg.text}")

            await self.send(text_data=json.dumps({
                "type": "chat_message",
                "user": user_username,
                "message": msg.text,
                "timestamp": str(msg.time_create)
            }))

    @sync_to_async
    def save_message(self, user, room, text):
        """Сохранение сообщения в базу данных"""
        try:
            msg = Message.objects.create(user=user, room=room, text=text)
            return msg
        except Exception as e:
            print(f"[ERROR] Ошибка при сохранении сообщения от {user}: {e}")
            return None
