from django.contrib import admin

from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "time_create")  # Показываем имя комнаты и дату создания
    search_fields = ("name", )  # Поиск по имени комнаты
    ordering = ("-time_create", )  # Сортировка от новых к старым
    readonly_fields = ("time_create", )  # Поле только для чтения


