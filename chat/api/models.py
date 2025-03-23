from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.db import models


class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    time_create = models.DateField(auto_now_add=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_rooms")
    users = models.ManyToManyField(User, related_name="joined_rooms")

    def perform_create(self, serializer):
        """Устанавливаем владельца и добавляем его в участники"""
        room = serializer.save(owner=self.request.user)
        room.users.add(self.request.user)

    class Meta:
        ordering = ['-time_create']
        indexes = [
            models.Index(fields=['-time_create'])
        ]

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.name}, Created at: {self.time_create}"


class Message(models.Model):
    text = models.TextField(max_length=264)
    time_create = models.DateField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class Meta:
        ordering = ['time_create']
        indexes = [
            models.Index(fields=['time_create'])
        ]

    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"
