# Sales Tracker App

A Python Flask-based web application for tracking and analyzing sales data from CSV uploads with real-time processing, monthly and yearly analytics views.

## Features

- **CSV Upload with Real-Time Processing**: Upload sales data with live terminal output showing upload progress and status
- **Automatic Daily Aggregation**: Multiple transactions per item per day are automatically totaled into single daily records
- **Duplicate Detection**: Prevents duplicate entries based on category, stock code, and date combination
- **Auto-Category Creation**: Categories are automatically created when importing CSV data
- **Monthly Sales View**: 
  - Select year, month, and optionally filter by category
  - Sortable sales details table (click column headers to sort ascending/descending)
  - Bar chart with alphabetically ordered product names
  - Horizontal scrolling for charts with many products
  - Summary statistics block
- **Yearly Sales View**: 
  - View all items for a year in alphabetically sorted list
  - Select individual items to see monthly trend line graphs
  - Analyze sales patterns across all 12 months
- **Categories Section**: View all automatically populated categories from uploaded data
- **Database**: SQLite3 with automatic schema creation and indexing

## Requirements

- Python 3.9+
- Flask 3.0.0
- Pandas 2.0.3
- python-dateutil 2.8.2

## Installation

### Using Poetry (Recommended)

1. Clone or download the project
2. Install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

### Using pip

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

### Using Poetry
```bash
poetry run python app.py
```

### Using pip
```bash
python app.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### 1. Settings Page (First Time Setup)
- Upload CSV files containing sales data
- The app automatically creates categories based on data in your CSV
- View all categories that have been populated from uploaded files
- Live terminal shows real-time upload progress including:
  - CSV loading information
  - Category creation logs
  - Records being added/duplicates skipped
  - Processing summaries

### 2. Monthly View
- Select year and month (category filter is optional)
- View summary statistics at the top
- **Sales Chart**: Bar chart showing total quantities by product name, alphabetically ordered with horizontal scrolling support
- **Sales Details Table**: 
  - Sortable columns (click headers to sort A→Z or Z→A with visual indicators)
  - Shows category, stock code, description, quantity, and date
  - Displays each daily record for selected month

### 3. Yearly View
- Select year (category filter is optional)
- View alphabetically sorted list of all items
- Click any item to see its monthly sales trend across all 12 months
- Analyze year-over-year sales patterns per product

## CSV Format Requirements

Your CSV file should have at least 7 columns. The app extracts:
- **Column 1**: Category (auto-created if doesn't exist)
- **Column 2**: Stock Description (product name)
- **Column 3**: Stock Code (numeric product ID)
- **Column 4**: Date (in DD/MM/YYYY format)
- **Column 7**: Quantity (numeric sales quantity)

Example CSV structure:
```
Category,Stock Description,Stock Code,Date,Col5,Col6,Quantity
AUTO,SHIELD DIESEL INJECTOR CL,6001878002312,06/03/2026,,5,19
BEVERA,COKE REGULAR GLASS 500ML,54490123,06/03/2026,,10,58
BEVERA,POWERADE ORANGE 500ML,54490345,04/03/2026,,1,25
```

**Note**: The app skips the first 2 rows of your CSV (typically metadata/header rows) and begins processing from row 4 onwards.

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
- stock_code (INTEGER)
- quantity (INTEGER)
- sale_date (DATE)
- created_at (TIMESTAMP)
- UNIQUE constraint on (category_id, stock_code, sale_date) prevents duplicate daily entries

## File Structure

```
.
├── app.py                 # Main Flask application with routes and CSV processing
├── database.py            # Database initialization and connection management
├── models.py              # Database models and query functions
├── pyproject.toml         # Poetry configuration and dependencies
├── README.md              # This file
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Monthly sales view
│   ├── yearly.html       # Yearly sales view
│   └── settings.html     # Settings, CSV upload, and categories
├── static/
│   └── css/
│       └── style.css     # Application styles and responsive design
└── sales_tracker.db      # SQLite database (created automatically)
```

## API Endpoints

### GET /
Home page redirects to monthly view

### GET /monthly
Monthly sales view page

### GET /yearly
Yearly sales view page

### GET /settings
Settings and CSV upload page

### GET /api/sales/month
Get sales for a specific month
- Parameters: `year` (int), `month` (int), `category_id` (optional)
- Returns: Array of sales records with category, stock_code, stock_description, quantity, sale_date

### GET /api/sales/yearly-item
Get monthly sales totals for a specific item throughout the year
- Parameters: `year` (int), `stock_code` (int)
- Returns: Array of monthly sales aggregates

### GET /api/items/year
Get all unique items for a year
- Parameters: `year` (int), `category_id` (optional)
- Returns: Array of items with stock_code, stock_description, category

### GET /api/categories
Get all categories
- Returns: Array of category objects with id and name

### POST /api/categories
Create a new category
- Body: `{"name": "Category Name"}`
- Returns: Created category object

### DELETE /api/categories/:id
Delete a category by ID

### POST /api/upload-csv
Upload and process a CSV file
- Body: multipart/form-data with `file` field
- Returns: Upload summary with added count, duplicates, and errors

### GET /api/logs
Server-Sent Events (SSE) stream for real-time upload progress logs
- Opens persistent connection that streams upload logs in real-time

## Development Notes

- The app automatically reloads when Python files are modified (debug mode enabled)
- Stock codes are stored as integers for consistency
- Dates are parsed as DD/MM/YYYY format and stored as ISO date strings
- All times are in UTC/application server timezone
- The CSV processor runs asynchronously in a background thread to keep the UI responsive

## Troubleshooting

### Database Issues
To reset the database and start fresh:
1. Stop the Flask application
2. Delete the `sales_tracker.db` file
3. Restart the application (it will recreate the database)

### CSV Upload Shows Errors
- Ensure your CSV has at least 7 columns
- Verify date format is DD/MM/YYYY (e.g., 06/03/2026 for 6th March 2026)
- Check that quantity values are valid numbers
- The first 2 rows are skipped; ensure your actual data starts from row 3 (row 4 in the file)

### Port Already in Use
If port 5000 is already in use, modify the port in `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
```

### No Data Appearing After Upload
- Check the upload terminal for error messages
- Verify categories in your CSV are being created (visible in Settings page)
- Ensure dates are properly formatted and within your selected month/year range

## Performance Considerations

- Large CSV files (10,000+ rows) are processed efficiently with real-time progress updates
- Monthly views with 500+ unique items will enable horizontal scrolling on charts
- Database queries are optimized with indexes on frequently searched columns (sale_date, category_id)
- Charts are non-responsive to enable horizontal scrolling with many products

## License

This project is open source and available for personal and commercial use.
