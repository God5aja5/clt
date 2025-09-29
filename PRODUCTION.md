# Baign Mart - Production Deployment Guide

## Features
- Course Categories System (Andrew Tate Course, Grant Cardone Course, Dating Course, Fitness Course, Business Course)
- Hot Products functionality
- Order management with Telegram integration
- Admin panel for product and category management
- My Orders section for customers

## Production Setup

### Prerequisites
- Python 3.8+
- Virtual environment tools

### Installation Steps

1. Clone or copy the project files
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables for production:
   ```bash
   cp .env.prod .env
   # Edit .env with your actual values
   ```

5. Initialize the database:
   ```bash
   python production.py --init
   ```

6. Start the application:
   ```bash
   python production.py
   # or use the startup script
   ./start.sh
   ```

## Security Features Implemented

- Admin credentials are now stored as environment variables
- Default admin credentials are no longer visible in UI
- Enhanced UI for all pages
- Telegram username updated to @wctw_private

## Production Endpoints

- Main site: `http://your-domain.com/`
- Admin panel: `http://your-domain.com/admin-pn`
- My Orders: `http://your-domain.com/my-orders`
- Order Lookup: `http://your-domain.com/order-lookup`

## Admin Credentials

Default credentials (should be changed in production):
- Username: `admin`
- Password: `admin @root`

## Important Security Notes

1. Change default admin credentials in production
2. Use HTTPS in production
3. Set proper SECRET_KEY environment variable
4. Protect the database in production
5. Regularly update dependencies

## Telegram Integration

Customers can contact `@wctw_private` with their order ID to complete purchases.

## Running in Production

For production deployment, consider using a proper WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 run:app
```

Or use the provided startup script:
```bash
./start.sh
```

The application is now ready for production deployment with enhanced security and UI improvements!