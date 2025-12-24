from django.contrib import admin
from .models import GymClass, TimeSlot, Booking, ContactMessage

@admin.register(GymClass)
class GymClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'class_type', 'instructor', 'duration_minutes', 'is_active')
    list_filter = ('class_type', 'is_active')
    search_fields = ('name', 'instructor')
    list_per_page = 20

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('gym_class', 'start_time', 'end_time', 'available_spots', 'is_available')
    list_filter = ('gym_class', 'is_available')
    date_hierarchy = 'start_time'
    list_per_page = 20
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('gym_class')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'full_name', 'email', 'gym_class', 'status', 'created_at')
    list_filter = ('status', 'gym_class', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'booking_reference')
    readonly_fields = ('booking_reference', 'created_at', 'updated_at')
    list_per_page = 20

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('gym_class', 'time_slot')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)
    list_per_page = 20
