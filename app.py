from flask import Flask, render_template, request, jsonify
from database import init_db
from models import DatabaseModels
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
init_db()

@app.route('/')
def index():
    """Monthly view page."""
    categories = DatabaseModels.get_all_categories()
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    return render_template('index.html', 
                         categories=categories,
                         current_year=current_year,
                         current_month=current_month)

@app.route('/yearly')
def yearly():
    """Yearly view page."""
    categories = DatabaseModels.get_all_categories()
    current_year = datetime.now().year
    
    return render_template('yearly.html', 
                         categories=categories,
                         current_year=current_year)

@app.route('/settings')
def settings():
    """Settings page."""
    categories = DatabaseModels.get_all_categories()
    return render_template('settings.html', categories=categories)

# API Endpoints

@app.route('/api/sales/month', methods=['GET'])
def get_sales_month():
    """Get sales data for a specific month."""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    category_id = request.args.get('category_id', type=int)
    
    if not year or not month:
        return jsonify({'error': 'Year and month required'}), 400
    
    sales = DatabaseModels.get_sales_by_month(year, month, category_id)
    return jsonify(sales)

@app.route('/api/sales/yearly-item', methods=['GET'])
def get_yearly_item_sales():
    """Get yearly sales for a specific item."""
    year = request.args.get('year', type=int)
    stock_code = request.args.get('stock_code', type=str)
    
    if not year or not stock_code:
        return jsonify({'error': 'Year and stock_code required'}), 400
    
    monthly_data = DatabaseModels.get_monthly_sales_summary(year, stock_code)
    return jsonify({'data': monthly_data, 'stock_code': stock_code})

@app.route('/api/items/year', methods=['GET'])
def get_items_for_year():
    """Get all items for a year."""
    year = request.args.get('year', type=int)
    category_id = request.args.get('category_id', type=int)
    
    if not year:
        return jsonify({'error': 'Year required'}), 400
    
    items = DatabaseModels.get_all_items_for_year(year, category_id)
    return jsonify(items)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories."""
    categories = DatabaseModels.get_all_categories()
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
def create_category():
    """Create a new category."""
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Category name required'}), 400
    
    result = DatabaseModels.add_category(name)
    if result['success']:
        return jsonify({'id': result['id'], 'name': name}), 201
    else:
        return jsonify({'error': result['error']}), 400

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category."""
    DatabaseModels.delete_category(category_id)
    return jsonify({'success': True})

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Handle CSV upload and process sales data."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV format'}), 400
    
    try:
        # Read CSV file
        df = pd.read_csv(file)
        
        # Extract required columns (1-indexed in the request, 0-indexed in pandas)
        # Column 1: Category, Column 2: Description, Column 3: Code, Column 7: Quantity
        required_cols = [0, 1, 2, 6]  # 0-indexed
        
        if len(df.columns) < 7:
            return jsonify({'error': 'CSV must have at least 7 columns'}), 400
        
        category_col = df.iloc[:, 0]
        description_col = df.iloc[:, 1]
        code_col = df.iloc[:, 2]
        quantity_col = df.iloc[:, 6]
        
        # Get all categories
        categories = {cat['name']: cat['id'] for cat in DatabaseModels.get_all_categories()}
        
        summary = {
            'added': 0,
            'duplicates': 0,
            'errors': 0,
            'error_details': []
        }
        
        # Process each row
        for idx, row in enumerate(df.iterrows()):
            try:
                category_name = str(row[1][0]).strip()
                description = str(row[1][1]).strip()
                code = str(row[1][2]).strip()
                quantity = int(row[1][6])
                
                # Validate data
                if not category_name or not code:
                    summary['errors'] += 1
                    summary['error_details'].append(f"Row {idx + 2}: Missing category or code")
                    continue
                
                # Check if category exists
                if category_name not in categories:
                    summary['errors'] += 1
                    summary['error_details'].append(f"Row {idx + 2}: Category '{category_name}' not found")
                    continue
                
                category_id = categories[category_name]
                
                # Use current date if not specified
                sale_date = datetime.now().date()
                
                # Add record to database
                result = DatabaseModels.add_sales_record(category_id, description, code, quantity, sale_date)
                
                if result['success']:
                    if result['action'] == 'added':
                        summary['added'] += 1
                elif result['action'] == 'duplicate':
                    summary['duplicates'] += 1
                else:
                    summary['errors'] += 1
                    summary['error_details'].append(f"Row {idx + 2}: {result.get('error', 'Unknown error')}")
            
            except Exception as e:
                summary['errors'] += 1
                summary['error_details'].append(f"Row {idx + 2}: {str(e)}")
        
        return jsonify(summary)
    
    except Exception as e:
        return jsonify({'error': f'Error processing CSV: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
