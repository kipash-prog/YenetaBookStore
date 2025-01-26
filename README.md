# Library Management System API

This is a Django-based API for managing a library system. It includes features for managing books, users, and transactions, as well as tracking overdue books and sending email notifications.

## Features

- User roles: Admin and Member
- Book management: Add, update, delete, and view books
- User management: Add, update, delete, and view users
- Transactions: Check out and return books
- Overdue tracking: Track overdue books and calculate penalties
- Email notifications: Send email notifications for overdue books and availability alerts
- Pagination and filtering: Paginate and filter book listings

## Installation

1. Clone the repository:

```sh
git clone https://github.com/kipash-prog/library_management_system_api.git
cd library_management_system_api


## Create a virtual environment and activate it:

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`


## Install the required packages:

pip install -r requirements.txt

## set up database

python manage.py makemigrations
python manage.py migrate


## Create a superuser:

python manage.py createsuperuser

## Run the development server:

python manage.py runserver


Configuration

Email Settings
Configure your email settings in settings.py:

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@example.com'
EMAIL_HOST_PASSWORD = 'your_email_password'
DEFAULT_FROM_EMAIL = 'Library Management System <noreply@example.com>'


JWT Authentication
Configure JWT authentication in settings.py:

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}


API Endpoints

Authentication

Obtain JWT token: POST /api/token/
Refresh JWT token: POST /api/token/refresh/

### Books

List all books: GET /books/
Retrieve a book: GET /books/{id}/
Create a book: POST /books/
Update a book: PUT /books/{id}/
Delete a book: DELETE /books/{id}/

### Users

List all users: GET /users/
Retrieve a user: GET /users/{id}/
Create a user: POST /users/
Update a user: PUT /users/{id}/
Delete a user: DELETE /users/{id}/

##Transactions

Check out a book: POST /checkout/
Return a book: POST /checkout/return/
User Borrowing History
Retrieve borrowing history: GET /api/borrowing-history/



This `README.md` file provides an overview of the project, installation instructions, configuration details, and API endpoints. Adjust the content as needed to fit your specific project details.
