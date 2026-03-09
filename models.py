from database import get_db_connection
from datetime import datetime
import calendar

class DatabaseModels:
    
    @staticmethod
    def get_all_categories():
        """Get all categories."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, name FROM categories ORDER BY name')
        categories = [dict(row) for row in c.fetchall()]
        conn.close()
        return categories
    
    @staticmethod
    def add_category(name):
        """Add a new category."""
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute('INSERT INTO categories (name) VALUES (?)', (name,))
            conn.commit()
            category_id = c.lastrowid
            conn.close()
            return {'success': True, 'id': category_id}
        except sqlite3.IntegrityError:
            conn.close()
            return {'success': False, 'error': 'Category already exists'}
    
    @staticmethod
    def delete_category(category_id):
        """Delete a category."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        conn.close()
        return {'success': True}
    
    @staticmethod
    def add_sales_record(category_id, stock_description, stock_code, quantity, sale_date):
        """Add a sales record. Returns success status and message."""
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO sales (category_id, stock_description, stock_code, quantity, sale_date)
                        VALUES (?, ?, ?, ?, ?)''',
                     (category_id, stock_description, stock_code, quantity, sale_date))
            conn.commit()
            conn.close()
            return {'success': True, 'action': 'added'}
        except Exception as e:
            conn.close()
            if 'UNIQUE constraint failed' in str(e):
                return {'success': False, 'action': 'duplicate'}
            return {'success': False, 'action': 'error', 'error': str(e)}
    
    @staticmethod
    def get_sales_by_month(year, month, category_id=None):
        """Get all sales for a specific month."""
        conn = get_db_connection()
        c = conn.cursor()
        
        # Calculate date range
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date()
        else:
            last_day = datetime(year, month + 1, 1).date()
        
        if category_id:
            c.execute('''SELECT s.stock_code, s.stock_description, s.quantity, s.sale_date, c.name as category
                        FROM sales s
                        JOIN categories c ON s.category_id = c.id
                        WHERE s.sale_date >= ? AND s.sale_date < ? AND s.category_id = ?
                        ORDER BY s.stock_code''',
                     (first_day, last_day, category_id))
        else:
            c.execute('''SELECT s.stock_code, s.stock_description, s.quantity, s.sale_date, c.name as category
                        FROM sales s
                        JOIN categories c ON s.category_id = c.id
                        WHERE s.sale_date >= ? AND s.sale_date < ?
                        ORDER BY c.name, s.stock_code''',
                     (first_day, last_day))
        
        sales = [dict(row) for row in c.fetchall()]
        conn.close()
        return sales
    
    @staticmethod
    def get_sales_by_item_yearly(year, stock_code):
        """Get monthly sales totals for a specific item across the year."""
        conn = get_db_connection()
        c = conn.cursor()
        
        first_day = datetime(year, 1, 1).date()
        last_day = datetime(year + 1, 1, 1).date()
        
        c.execute('''SELECT strftime('%m', sale_date) as month, SUM(quantity) as total_quantity
                    FROM sales
                    WHERE stock_code = ? AND sale_date >= ? AND sale_date < ?
                    GROUP BY month
                    ORDER BY month''',
                 (stock_code, first_day, last_day))
        
        results = [dict(row) for row in c.fetchall()]
        conn.close()
        return results
    
    @staticmethod
    def get_all_items_for_year(year, category_id=None):
        """Get all unique items for a year (optionally filtered by category)."""
        conn = get_db_connection()
        c = conn.cursor()
        
        first_day = datetime(year, 1, 1).date()
        last_day = datetime(year + 1, 1, 1).date()
        
        if category_id:
            c.execute('''SELECT DISTINCT stock_code, stock_description, category_id
                        FROM sales
                        WHERE sale_date >= ? AND sale_date < ? AND category_id = ?
                        ORDER BY stock_code''',
                     (first_day, last_day, category_id))
        else:
            c.execute('''SELECT DISTINCT stock_code, stock_description, category_id
                        FROM sales
                        WHERE sale_date >= ? AND sale_date < ?
                        ORDER BY stock_code''',
                     (first_day, last_day))
        
        items = [dict(row) for row in c.fetchall()]
        conn.close()
        return items
    
    @staticmethod
    def get_monthly_sales_summary(year, stock_code):
        """Get sales data for all 12 months for an item."""
        monthly_data = [0] * 12
        
        results = DatabaseModels.get_sales_by_item_yearly(year, stock_code)
        for row in results:
            month_idx = int(row['month']) - 1
            monthly_data[month_idx] = row['total_quantity']
        
        return monthly_data

import sqlite3
