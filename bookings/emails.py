import logging
import threading
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

def send_email_async(subject, message, from_email, recipient_list, html_message=None):
    """
    Sends email in a separate thread to avoid blocking the API response.
    """
    def _send():
        try:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Email sent to {recipient_list}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_list}: {str(e)}")

    thread = threading.Thread(target=_send)
    thread.start()

def send_booking_confirmation(booking):
    subject = f"Booking Confirmation - {booking.gym_class.name}"
    
    # In a real app, use templates. For now, constructing string/HTML here or simple template.
    # Using f-strings for simplicity as per requirement implies dynamic content.
    
    context = {
        'first_name': booking.first_name,
        'booking_reference': booking.booking_reference,
        'class_name': booking.gym_class.name,
        'start_time': booking.time_slot.start_time.strftime("%B %d, %Y at %I:%M %p"),
        'duration': booking.gym_class.duration_minutes,
        'instructor': booking.gym_class.instructor,
        'special_requests': booking.special_requests or "None",
    }

    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #DC2626;">Hi {context['first_name']},</h2>
            <p>Your booking is confirmed!</p>
            <p><strong>Booking Reference:</strong> {context['booking_reference']}</p>
            <p><strong>Class:</strong> {context['class_name']}</p>
            <p><strong>Time:</strong> {context['start_time']}</p>
            <p><strong>Duration:</strong> {context['duration']} minutes</p>
            <p><strong>Instructor:</strong> {context['instructor']}</p>
            <p><strong>Special Requests:</strong> {context['special_requests']}</p>
            <br>
            <p>Please arrive 10 minutes early and bring a water bottle and towel.</p>
            <p>See you there!</p>
            <p><em>The Gym Fitness Team</em></p>
        </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_email_async(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.email],
        html_message=html_message
    )

def send_booking_cancellation(booking):
    subject = f"Booking Cancelled - {booking.gym_class.name}"
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #DC2626;">Booking Cancelled</h2>
            <p>Hi {booking.first_name},</p>
            <p>Your booking for <strong>{booking.gym_class.name}</strong> on {booking.time_slot.start_time.strftime("%B %d, %Y at %I:%M %p")} has been cancelled successfully.</p>
            <p>We hope to see you again soon!</p>
            <p><em>The Gym Fitness Team</em></p>
        </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_email_async(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.email],
        html_message=html_message
    )

def send_contact_confirmation(contact_message):
    subject = "We received your message"
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Hello {contact_message.name},</h2>
            <p>Thanks for reaching out! We've received your message and will get back to you within 24-48 hours.</p>
            <hr>
            <p><em>"{contact_message.message}"</em></p>
            <hr>
            <p>Best regards,<br>The Gym Fitness Team</p>
        </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_email_async(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [contact_message.email],
        html_message=html_message
    )
