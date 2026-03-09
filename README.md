# Sales Tracker App

A Python Flask-based web application for tracking sales from CSV uploads with monthly and yearly analytics.

## Features

- **CSV Upload**: Upload sales data with automatic duplicate detection based on date
- **Monthly View**: Select a month and category to view detailed sales data with a bar chart
- **Yearly View**: View all items for the year with monthly trend lines
- **Category Management**: Add, view, and delete product categories
- **Database**: SQLite3 with automatic schema creation

## Requirements

- Python 3.9+
- Flask 3.0.0
- Pandas 2.1.1
- python-dateutil 2.8.2

## Installation

1. Clone or download the project
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # or
   uv pip install -r requirements.txt
   ```

## Running the App

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### 1. Settings Page (First Time Setup)
- Create categories that match your CSV data
- Upload CSV files with the following column structure:
  - Column 1: Category
  - Column 2: Stock Description
  - Column 3: Stock Code
  - Column 7: Quantity

### 2. Monthly View
- Select year, month, and optionally a category
- View a bar chart showing quantities by stock code
- See detailed table of all sales for that period

### 3. Yearly View
- Select year and optionally a category
- Click on items from the list to view their monthly trend line
- See sales patterns across all 12 months

## CSV Format

Your CSV file should have at least 7 columns:

```
Category,Stock Description,Stock Code,Col4,Col5,Col6,Quantity
Electronics,USB Cable,USB-001,,,5
Electronics,Monitor,MON-001,,,2
```

The app will extract:
- Column 1: Category
- Column 2: Stock Description
- Column 3: Stock Code
- Column 7: Quantity

## Database

The app uses SQLite3 to store data. The database file `sales_tracker.db` will be created automatically in the project root.

### Database Schema

**categories** table:
- id (INTEGER, PRIMARY KEY)
- name (TEXT, UNIQUE)
- created_at (TIMESTAMP)

**sales** table:
- id (INTEGER, PRIMARY KEY)
- category_id (INTEGER, FOREIGN KEY)
- stock_description (TEXT)
- stock_code (TEXT)
- quantity (INTEGER)
- sale_date (DATE)
- created_at (TIMESTAMP)
- UNIQUE constraint on (category_id, stock_code, sale_date) to prevent duplicates

## File Structure

```
.
├── app.py                 # Main Flask application
├── database.py            # Database initialization and connection
├── models.py              # Database models and queries
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Monthly view
│   ├── yearly.html       # Yearly view
│   └── settings.html     # Settings and uploads
├── static/
│   └── css/
│       └── style.css     # Application styles
└── sales_tracker.db      # SQLite database (created automatically)
```

## API Endpoints

### GET /api/sales/month
Get sales for a specific month
- Parameters: `year`, `month`, `category_id` (optional)

### GET /api/sales/yearly-item
Get monthly sales for a specific item
- Parameters: `year`, `stock_code`

### GET /api/items/year
Get all items for a year
- Parameters: `year`, `category_id` (optional)

### GET /api/categories
Get all categories

### POST /api/categories
Create a new category
- Body: `{"name": "Category Name"}`

### DELETE /api/categories/:id
Delete a category

### POST /api/upload-csv
Upload and process a CSV file
- Body: multipart/form-data with `file` field

## Development

To modify the app:

1. Edit Python files and restart the Flask server (it will auto-reload if debug=True)
2. Edit templates to change the UI
3. Edit `static/css/style.css` for styling changes

## Troubleshooting

### Database Issues
To reset the database:
```bash
python -c "from database import clear_database; clear_database()"
```

### Port Already in Use
If port 5000 is already in use, modify the port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### CSV Upload Errors
- Ensure your CSV has at least 7 columns
- Verify that categories in the CSV already exist in the app
- Check that quantity values are valid numbers

## License

This project is open source and available for personal and commercial use.
