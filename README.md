Gym Booking API

A RESTful gym class booking system built with Django REST Framework.

Features
- Gym class and time slot management
- Secure booking with race-condition protection
- Slot availability tracking
- Booking cancellation with slot restoration
- Email notifications
- Atomic transactions & row-level locking

Tech Stack
- Python
- Django
- Django REST Framework
- PostgreSQL / SQLite
- GitHub

API Endpoints
- POST /bookings/
- GET /bookings/my_bookings/?email=
- POST /bookings/{id}/cancel/

Key Engineering Concepts
- Database transactions
- Race condition prevention
- Custom ViewSet actions
- Row-level locking (`select_for_update`)

Setup
```bash
git clone https://github.com/yourusername/gym-booking-api.git
cd gym-booking-api
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
