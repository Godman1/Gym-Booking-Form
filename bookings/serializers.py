from django.utils import timezone
import uuid
from rest_framework import serializers
from .models import GymClass, TimeSlot, Booking, ContactMessage

class GymClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymClass
        fields = ['id', 'name', 'class_type', 'description', 'duration_minutes', 'max_participants', 'instructor']


class TimeSlotSerializer(serializers.ModelSerializer):
    gym_class = GymClassSerializer(read_only=True)
    gym_class_id = serializers.PrimaryKeyRelatedField(
        queryset=GymClass.objects.all(), source='gym_class', write_only=True
    )

    class Meta:
        model = TimeSlot
        fields = ['id', 'gym_class', 'gym_class_id', 'start_time', 'end_time', 'available_spots', 'is_available']
        read_only_fields = ['is_available']

    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        gym_class = data.get('gym_class')
        available_spots = data.get('available_spots')

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time")
        
        if start_time and start_time < timezone.now():
             raise serializers.ValidationError("Start time cannot be in the past")

        if gym_class and available_spots is not None:
            if available_spots > gym_class.max_participants:
                raise serializers.ValidationError("Available spots cannot exceed class capacity")
        
        return data


class BookingSerializer(serializers.ModelSerializer):
    gym_class = GymClassSerializer(read_only=True)
    time_slot = TimeSlotSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'booking_reference', 'first_name', 'last_name', 'email', 'phone', 
                  'gym_class', 'time_slot', 'status', 'special_requests', 'created_at', 'updated_at']
        read_only_fields = ['booking_reference', 'status', 'created_at', 'updated_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    gym_class = serializers.PrimaryKeyRelatedField(queryset=GymClass.objects.filter(is_active=True))
    time_slot = serializers.PrimaryKeyRelatedField(queryset=TimeSlot.objects.filter(is_available=True))

    class Meta:
        model = Booking
        fields = ['first_name', 'last_name', 'email', 'phone', 'gym_class', 'time_slot', 'special_requests']

    def validate(self, data):
        time_slot = data.get('time_slot')
        email = data.get('email')

        # Check availability
        if time_slot:
            if not time_slot.is_available or time_slot.available_spots <= 0:
                 raise serializers.ValidationError({"time_slot": "This time slot is no longer available"})
            if time_slot.start_time < timezone.now():
                raise serializers.ValidationError({"time_slot": "Cannot book past time slots"})

        # Check for duplicates
        if email and time_slot:
            existing_booking = Booking.objects.filter(
                email=email, 
                time_slot=time_slot, 
                status__in=['PENDING', 'CONFIRMED']
            ).exists()
            if existing_booking:
                raise serializers.ValidationError({"detail": "You already have a booking for this time slot"})

        return data

    def create(self, validated_data):
        validated_data['booking_reference'] = f"GYM-{uuid.uuid4().hex[:8].upper()}"
        return super().create(validated_data)


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'message', 'created_at']
        read_only_fields = ['created_at']
