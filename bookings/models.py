import uuid
from django.db import models
from django.utils import timezone

class GymClass(models.Model):
    CLASS_TYPES = [
        ('PERSONAL', 'Personal Training'),
        ('GROUP', 'Group Fitness'),
        ('YOGA', 'Yoga'),
        ('STRENGTH', 'Strength'),
        ('CARDIO', 'Cardio'),
        ('NUTRITION', 'Nutrition'),
    ]

    name = models.CharField(max_length=100)
    class_type = models.CharField(max_length=20, choices=CLASS_TYPES)
    description = models.TextField()
    duration_minutes = models.IntegerField(default=60)
    max_participants = models.IntegerField(default=20)
    instructor = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'class_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_class_type_display()})"


class TimeSlot(models.Model):
    gym_class = models.ForeignKey(GymClass, on_delete=models.CASCADE, related_name='time_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    available_spots = models.IntegerField()
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_time']
        unique_together = ['gym_class', 'start_time']
        indexes = [
            models.Index(fields=['is_available', 'start_time']),
        ]

    def __str__(self):
        return f"{self.gym_class.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    booking_reference = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    gym_class = models.ForeignKey(GymClass, on_delete=models.PROTECT, related_name='bookings')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT, related_name='bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    special_requests = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'status', 'created_at']),
        ]
        # Unique constraint to prevent duplicate bookings for same slot by same email
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'time_slot'],
                condition=models.Q(status__in=['PENDING', 'CONFIRMED']),
                name='unique_active_booking'
            )
        ]

    def __str__(self):
        return f"{self.booking_reference} - {self.email}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField(max_length=1000)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_read', 'created_at']),
        ]

    def __str__(self):
        return f"Message from {self.name} - {self.created_at.strftime('%Y-%m-%d')}"
