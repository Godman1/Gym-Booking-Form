from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import GymClass, TimeSlot, Booking, ContactMessage
from .serializers import (
    GymClassSerializer, 
    TimeSlotSerializer, 
    BookingSerializer, 
    BookingCreateSerializer,
    ContactMessageSerializer
)
from .emails import send_booking_confirmation, send_booking_cancellation, send_contact_confirmation

class GymClassViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GymClass.objects.filter(is_active=True)
    serializer_class = GymClassSerializer
    permission_classes = [AllowAny]


class TimeSlotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TimeSlotSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = TimeSlot.objects.filter(is_available=True, start_time__gt=timezone.now())
        gym_class_id = self.request.query_params.get('gym_class')
        if gym_class_id:
            queryset = queryset.filter(gym_class_id=gym_class_id)
        return queryset


class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        # By default not strictly limited, but 'my_bookings' handles user filtering.
        # For admin/debug purposes, listed all or filtered by user could be done here.
        # Restricting standard list to empty for security if no auth is used, 
        # but PRD implies open for now or just my_bookings.
        return Booking.objects.all()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Lock the time slot
            time_slot = TimeSlot.objects.select_for_update().get(id=serializer.validated_data['time_slot'].id)
            
            if time_slot.available_spots <= 0:
                return Response(
                    {"error": "No spots available", "message": "This class is fully booked."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create booking
            booking = serializer.save()
            
            # Decrement spots
            time_slot.available_spots -= 1
            if time_slot.available_spots == 0:
                time_slot.is_available = False
            time_slot.save()
            
            # Send confirmation email
            send_booking_confirmation(booking)
            
            # Return full booking details
            response_serializer = BookingSerializer(booking)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except TimeSlot.DoesNotExist:
             return Response(
                {"error": "Time slot not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Log error
            return Response(
                {"error": "Booking failed", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response(
                {"error": "Email parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bookings = Booking.objects.filter(email=email).exclude(status='CANCELLED').order_by('-created_at')
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def cancel(self, request, pk=None):
        booking = self.get_object()
        
        # Security check: PRD request to require booking_reference in body for cancellation
        booking_reference = request.data.get('booking_reference')
        if booking.booking_reference != booking_reference:
             return Response(
                {"error": "Invalid request", "message": "Booking reference matches are required for cancellation."},
                status=status.HTTP_403_FORBIDDEN
            )

        if booking.status == 'CANCELLED':
            return Response(
                {"error": "Already cancelled", "message": "This booking is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update booking status
        booking.status = 'CANCELLED'
        booking.save()
        
        # Increment spots
        time_slot = TimeSlot.objects.select_for_update().get(id=booking.time_slot.id)
        time_slot.available_spots += 1
        time_slot.is_available = True
        time_slot.save()
        
        # Send cancellation email
        send_booking_cancellation(booking)
        
        return Response(
            {"message": "Booking cancelled successfully", "booking": BookingSerializer(booking).data},
            status=status.HTTP_200_OK
        )


class ContactMessageViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Send confirmation email
        # Need to fetch the instance created to pass to email function.
        # But 'super().create' returns response data, not instance.
        # So we can just use validated_data or retrieve instance if needed.
        # Actually simplest is to override perform_create or access serializer.instance?
        # But for generic viewset 'create' method logic:
        # It calls serializer.save().
        
        # Let's customize to get instance easily.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact_message = serializer.save()
        
        send_contact_confirmation(contact_message)
        
        return Response(
            {"message": "Message sent successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )
