from django.contrib import admin
from .models import Room, Message


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "time_create")
    search_fields = ("name", "owner__username")
    ordering = ("-time_create",)
    readonly_fields = ("time_create",)
    filter_horizontal = ("users",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("user", "room", "text", "time_create")
    search_fields = ("text", "user__username", "room__name")
    ordering = ("-time_create",)
    readonly_fields = ("time_create",)
