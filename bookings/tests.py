from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta
from .models import GymClass, TimeSlot, Booking

class BookingAPITests(APITestCase):
    def setUp(self):
        self.gym_class = GymClass.objects.create(
            name='Yoga Basics',
            class_type='YOGA',
            description='Intro to Yoga',
            duration_minutes=60,
            max_participants=10
        )
        self.future_time = timezone.now() + timedelta(days=1)
        self.time_slot = TimeSlot.objects.create(
            gym_class=self.gym_class,
            start_time=self.future_time,
            end_time=self.future_time + timedelta(minutes=60),
            available_spots=2
        )
        self.booking_url = reverse('booking-list')

    def test_create_booking_success(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'gym_class': self.gym_class.id,
            'time_slot': self.time_slot.id
        }
        response = self.client.post(self.booking_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.time_slot.refresh_from_db()
        self.assertEqual(self.time_slot.available_spots, 1)

    def test_create_booking_no_spots(self):
        self.time_slot.available_spots = 0
        self.time_slot.is_available = False
        self.time_slot.save()
        
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'phone': '1234567890',
            'gym_class': self.gym_class.id,
            'time_slot': self.time_slot.id
        }
        response = self.client.post(self.booking_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_duplicate_booking(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'unique@example.com',
            'phone': '1234567890',
            'gym_class': self.gym_class.id,
            'time_slot': self.time_slot.id
        }
        self.client.post(self.booking_url, data, format='json')
        # Try booking again
        response = self.client.post(self.booking_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_booking(self):
        # Create booking first
        booking = Booking.objects.create(
            first_name='Cancel',
            last_name='Me',
            email='cancel@example.com',
            phone='123',
            gym_class=self.gym_class,
            time_slot=self.time_slot,
            status='CONFIRMED'
        )
        self.time_slot.available_spots -= 1
        self.time_slot.save()
        
        url = reverse('booking-cancel', args=[booking.id])
        data = {'booking_reference': booking.booking_reference}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        
        self.time_slot.refresh_from_db()
        self.assertEqual(self.time_slot.available_spots, 2)
