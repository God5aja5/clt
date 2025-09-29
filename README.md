# Baign Mart - E-commerce Platform

A comprehensive e-commerce platform with course categories and advanced product management features.

## Features

- **Course Categories System**: Organize products by course types (Andrew Tate Course, Grant Cardone Course, Dating Course, Fitness Course, Business Course)
- **Hot Products**: Highlight featured products on homepage
- **Admin Panel**: Complete product and category management
- **Logo Integration**: Custom logo in the header
- **Responsive Design**: Mobile-friendly UI with Tailwind CSS
- **Category Navigation**: Easy navigation with dropdown menus

## Setup Instructions

1. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables** (Optional):
   Create a `.env` file with:
   ```
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///baign_mart.db
   ```

4. **Initialize Database**:
   ```bash
   python init_db.py
   ```

5. **Run the Application**:
   ```bash
   python run.py
   ```
   Or to specify port:
   ```bash
   FLASK_APP=run.py flask run --port 5000
   ```

## Admin Panel

- Access: `/admin-pn`
- Default credentials: `admin` / `admin @root`

## New Features Added

### Course Categories
- Category management system
- Ability to assign products to categories
- Category navigation in header
- Category-specific product pages

### Hot Products
- Admin can mark products as "hot"
- Hot products displayed prominently on homepage
- Special "Hot Products" section with attractive styling

### UI Improvements
- Logo integration in header
- Dropdown navigation for course categories
- Enhanced product displays
- Improved category browsing experience

### Admin Functionality
- Categories management (add, edit, delete, activate/deactivate)
- Hot product toggling for products
- Product-category assignment
- Enhanced product management forms

## File Structure Changes

```
baign_mart/
├── models.py          # Added Category model, updated Product model
├── admin.py           # Added category management routes
├── main.py            # Added category routes and hot products logic
├── forms.py           # Added CategoryForm
├── templates/
│   ├── base.html      # Updated with logo and category navigation
│   ├── public/
│   │   ├── index.html # Added hot products section
│   │   └── categories.html # New template for category browsing
│   └── admin/
│       ├── categories.html     # Category management UI
│       ├── category_form.html  # Category creation/edit form
│       └── products.html       # Updated with hot product toggle
├── static/images/logo.jpg # Logo image
└── run.py               # Updated application runner
```

## Admin Credentials

- Username: `admin`
- Password: `admin @root`

## API Endpoints

- `/` - Homepage (with hot products)
- `/categories` - Browse all categories
- `/category/<int:category_id>` - Products in specific category
- `/admin-pn` - Admin panel
- `/admin-pn/categories` - Category management
- `/admin-pn/products` - Product management

## Database Schema Changes

- Added `categories` table with name, description, is_active, featured fields
- Updated `products` table with `category_id` foreign key and `is_hot_product` boolean field

## Running the Application

The application runs on port 5000 by default. Access:
- Frontend: `http://localhost:5000`
- Admin Panel: `http://localhost:5000/admin-pn`