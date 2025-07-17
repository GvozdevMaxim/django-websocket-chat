from rest_framework import serializers
from .models import Room

class RoomCreateSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Room
        fields = ['id','name', 'password', 'owner']
        read_only_fields = ['id', 'owner']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        room = Room.objects.create(**validated_data)

        if password:
            room.set_password(password)
        return room


class JoinRoomSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Проверяем правильность пароля"""
        room = self.context['room']
        if room.password and not room.check_password(data['password']):
            raise serializers.ValidationError("Неверный пароль")
        return data


