import sqlite3
import os
from datetime import datetime

DATABASE_PATH = 'sales_tracker.db'

def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Categories table
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Sales table
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        stock_description TEXT NOT NULL,
        stock_code INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        sale_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id),
        UNIQUE(category_id, stock_code, sale_date)
    )''')
    
    # Create index for faster queries
    c.execute('''CREATE INDEX IF NOT EXISTS idx_sale_date ON sales (sale_date)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_category_id ON sales (category_id)''')
    
    conn.commit()
    conn.close()

def clear_database():
    """Clear all tables (for development/testing)."""
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    init_db()

if __name__ == '__main__':
    init_db()
    print(f"Database initialized at {DATABASE_PATH}")
