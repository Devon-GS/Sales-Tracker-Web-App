from flask import Flask, render_template, request, jsonify
from database import init_db
from models import DatabaseModels
from datetime import datetime
import pandas as pd
import os
import io
import threading
import queue

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

log_queue = queue.Queue()
upload_complete = False

init_db()

def add_log(message):
    """Add a log message to the queue for real-time streaming."""
    log_queue.put(message)

@app.route('/api/logs')
def stream_logs():
    """Stream logs in real-time using SSE."""
    def generate():
        last_sent = False
        timeout = 0
        while timeout < 60:
            try:
                msg = log_queue.get(timeout=1)
                yield f"data: {msg}\n\n"
                timeout = 0
            except queue.Empty:
                if upload_complete and not last_sent:
                    yield f"data: __UPLOAD_COMPLETE__\n\n"
                    last_sent = True
                timeout += 1
    
    return generate(), 200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    }

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
    """Handle CSV upload and process sales data asynchronously."""
    global upload_complete
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV format'}), 400
    
    file_content = file.read()
    
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break
    upload_complete = False
    
    thread = threading.Thread(target=process_csv_file, args=(file_content,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Upload started, check /api/logs for progress'}), 202

def process_csv_file(file_content):
    """Process CSV file asynchronously."""
    global upload_complete
    
    try:
        add_log("Starting CSV upload...")
        
        file_obj = io.BytesIO(file_content)
        df = pd.read_csv(file_obj, skiprows=2, header=None)
        
        if len(df.columns) < 7:
            add_log("Error: CSV must have at least 7 columns")
            upload_complete = True
            return
        
        categories = {cat['name']: cat['id'] for cat in DatabaseModels.get_all_categories()}
        
        summary = {
            'added': 0,
            'duplicates': 0,
            'errors': 0,
            'error_details': []
        }
        
        aggregated_data = {}
        add_log("Parsing and aggregating data...")
        
        for idx, (_, row) in enumerate(df.iterrows()):
            row_number = idx + 4
            
            if row.isna().all():
                continue
            
            try:
                category_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                description = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                
                try:
                    code = int(float(row.iloc[2]))
                except (ValueError, TypeError):
                    summary['errors'] += 1
                    summary['error_details'].append(f"Row {row_number}: Invalid stock code '{row.iloc[2]}'")
                    continue
                
                date_str = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
                
                try:
                    quantity = int(float(row.iloc[6]))
                except (ValueError, TypeError):
                    summary['errors'] += 1
                    summary['error_details'].append(f"Row {row_number}: Invalid quantity value '{row.iloc[6]}'")
                    continue
                
                if not category_name or code is None:
                    summary['errors'] += 1
                    summary['error_details'].append(f"Row {row_number}: Missing category or code")
                    continue
                
                try:
                    sale_date = pd.to_datetime(date_str, format='%d/%m/%Y').date()
                except:
                    summary['errors'] += 1
                    summary['error_details'].append(f"Row {row_number}: Invalid date format '{date_str}'")
                    continue
                
                key = (category_name, code, str(sale_date))
                if key in aggregated_data:
                    aggregated_data[key]['quantity'] += quantity
                else:
                    aggregated_data[key] = {'quantity': quantity, 'description': description}
                    
            except Exception as e:
                summary['errors'] += 1
                summary['error_details'].append(f"Row {row_number}: {str(e)}")
        
        add_log(f"Aggregated {len(aggregated_data)} unique daily sales records")
        add_log("Inserting data into database...")
        
        for idx, ((category_name, code, date_str), data) in enumerate(aggregated_data.items()):
            try:
                sale_date = pd.to_datetime(date_str, format='%Y-%m-%d').date()
                total_quantity = data['quantity']
                description = data['description']
                
                if category_name not in categories:
                    result = DatabaseModels.add_category(category_name)
                    if result['success']:
                        categories[category_name] = result['id']
                    else:
                        summary['errors'] += 1
                        summary['error_details'].append(f"Failed to create category '{category_name}'")
                        continue
                
                category_id = categories[category_name]
                
                result = DatabaseModels.add_sales_record(category_id, description, code, total_quantity, sale_date)
                
                if result['success']:
                    summary['added'] += 1
                elif result['action'] == 'duplicate':
                    summary['duplicates'] += 1
                else:
                    summary['errors'] += 1
                    summary['error_details'].append(f"Failed to add: {category_name} - {code} ({date_str}): {result.get('error', 'Unknown error')}")
                
                if (idx + 1) % 10 == 0:
                    add_log(f"Progress: Processed {idx + 1}/{len(aggregated_data)} records")
            
            except Exception as e:
                summary['errors'] += 1
                summary['error_details'].append(f"Error processing {category_name} - {code}: {str(e)}")
        
        add_log(f"Processing complete: {summary['added']} added, {summary['duplicates']} duplicates, {summary['errors']} errors")
        
    except Exception as e:
        add_log(f"Error processing CSV: {str(e)}")
    
    finally:
        upload_complete = True

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
