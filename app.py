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
        # Read CSV - skip first 2 rows (metadata/header rows)
        df = pd.read_csv(file, skiprows=2, header=None)
        
        print(f"[v0] CSV loaded with {len(df)} rows")
        print(f"[v0] Column count: {len(df.columns)}")
        
        # Column 1: Category, Column 2: Description, Column 3: Code, Column 4: Date, Column 7: Quantity
        if len(df.columns) < 7:
            return jsonify({'error': 'CSV must have at least 7 columns'}), 400
        
        # Get all categories
        categories = {cat['name']: cat['id'] for cat in DatabaseModels.get_all_categories()}
        
        summary = {
            'added': 0,
            'duplicates': 0,
            'errors': 0,
            'error_details': []
        }
        
        # First pass: extract and aggregate data by category, code, and date
        aggregated_data = {}  # key: (category_name, code, date_str) -> total_quantity
        date_errors = []
        
        for idx, (_, row) in enumerate(df.iterrows()):
            row_number = idx + 4
            
            # Skip if entire row is NaN
            if row.isna().all():
                continue
            
            try:
                # Extract columns
                category_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                description = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                code = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
                date_str = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
                
                # Parse quantity
                try:
                    quantity = int(float(row.iloc[6]))
                except (ValueError, TypeError):
                    summary['errors'] += 1
                    summary['error_details'].append(f"Row {row_number}: Invalid quantity value '{row.iloc[6]}'")
                    continue
                
                # Validate required fields
                if not category_name or not code:
                    summary['errors'] += 1
                    summary['error_details'].append(f"Row {row_number}: Missing category or code")
                    continue
                
                # Parse date
                try:
                    sale_date = pd.to_datetime(date_str).date()
                except:
                    summary['errors'] += 1
                    summary['error_details'].append(f"Row {row_number}: Invalid date format '{date_str}'")
                    continue
                
                # Aggregate by (category, code, date)
                key = (category_name, code, str(sale_date))
                if key in aggregated_data:
                    aggregated_data[key] += quantity
                else:
                    aggregated_data[key] = quantity
                    
            except Exception as e:
                summary['errors'] += 1
                summary['error_details'].append(f"Row {row_number}: {str(e)}")
        
        # Second pass: insert aggregated data, checking for duplicates
        for (category_name, code, date_str), total_quantity in aggregated_data.items():
            try:
                sale_date = pd.to_datetime(date_str).date()
                
                # Auto-create category if needed
                if category_name not in categories:
                    result = DatabaseModels.add_category(category_name)
                    if result['success']:
                        categories[category_name] = result['id']
                    else:
                        summary['errors'] += 1
                        summary['error_details'].append(f"Failed to create category '{category_name}'")
                        continue
                
                category_id = categories[category_name]
                
                # Add record to database
                result = DatabaseModels.add_sales_record(category_id, code, code, total_quantity, sale_date)
                
                if result['success']:
                    summary['added'] += 1
                elif result['action'] == 'duplicate':
                    summary['duplicates'] += 1
                else:
                    summary['errors'] += 1
                    summary['error_details'].append(f"Failed to add: {category_name} - {code} ({date_str}): {result.get('error', 'Unknown error')}")
            
            except Exception as e:
                summary['errors'] += 1
                summary['error_details'].append(f"Error processing {category_name} - {code}: {str(e)}")
        
        return jsonify(summary)
    
    except Exception as e:
        return jsonify({'error': f'Error processing CSV: {str(e)}'}), 400
    
    except Exception as e:
        return jsonify({'error': f'Error processing CSV: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
