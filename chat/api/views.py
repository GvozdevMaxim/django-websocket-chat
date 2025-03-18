from rest_framework import generics, status, permissions
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from .models import Room
from .serializers import RoomCreateSerializer, JoinRoomSerializer


class JoinRoom(generics.GenericAPIView):
    serializer_class = JoinRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        name = self.kwargs.get('name')
        return get_object_or_404(Room, name=name)

    def post(self, request):
        room = self.get_object()

        serializer = self.get_serializer(data=request.data, context={'room': room})
        serializer.is_valid(raise_exception=True)

        room.users.add(request.user)

        return Response({"message": "Вы успешно присоединились к комнате"})


# Create your views here.
class CreateRoom(generics.CreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class DeleteRoom(generics.DestroyAPIView):
    queryset = Room.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        name = self.kwargs.get('name')
        return get_object_or_404(Room, name=name)

    def delete(self, request, *args, **kwargs):
        room = self.get_object()

        if room.owner != request.user:
            return Response(
                {"error": "Вы не являетесь создателем комнаты"},
                status=status.HTTP_403_FORBIDDEN
            )
        room.delete()
        return Response({"message": "Комната удалена"}, status=status.HTTP_204_NO_CONTENT)
