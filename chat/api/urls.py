from django.urls import path
from .views import CreateRoom, JoinRoom, DeleteRoom, chat_view

app_name = 'api'

urlpatterns = [
    path('createroom/', CreateRoom.as_view(), name='create-room'),
    path('joinroom/<str:name>/', JoinRoom.as_view(), name='join-room'),
    path('deleteroom/<str:name>/', DeleteRoom.as_view(), name='delete-room'),
    path('<str:name>/', chat_view, name='chat-room'),
]