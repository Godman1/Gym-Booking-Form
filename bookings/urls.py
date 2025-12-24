from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GymClassViewSet, TimeSlotViewSet, BookingViewSet, ContactMessageViewSet

router = DefaultRouter()
router.register(r'classes', GymClassViewSet)
router.register(r'timeslots', TimeSlotViewSet, basename='timeslot')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'contact', ContactMessageViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
]
