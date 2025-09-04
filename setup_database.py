#!/usr/bin/env python3
"""
Database Setup Script for Bartr Application
Run this to create and initialize the MySQL database
"""

import pymysql
import sys
import os

def create_mysql_database():
    """Create MySQL database and user if they don't exist"""
    print("[SETUP] Setting up MySQL database...")
    try:
        # Connect to MySQL server without specifying database
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',  # Update this with your MySQL root password if needed
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            print("[SETUP] Creating database...")
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS bartr_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            print("[SETUP] Creating database user...")
            # Create user and grant privileges
            cursor.execute("CREATE USER IF NOT EXISTS 'bartr_user'@'localhost' IDENTIFIED BY 'bartr_password'")
            cursor.execute("GRANT ALL PRIVILEGES ON bartr_db.* TO 'bartr_user'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            
        connection.commit()
        connection.close()
        print("[SUCCESS] MySQL database and user created successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating MySQL database: {e}")
        print("[INFO] Please ensure:")
        print("1. MySQL server is running")
        print("2. MySQL root user has proper permissions")
        print("3. Update the root password in this script if needed")
        return False



def create_database_tables():
    """Create all database tables and initial data"""
    print("\n[SETUP] Creating database tables...")
    try:
        # Import Flask app and models
        from bartr import create_app, db
        from bartr.models import Category
        
        app = create_app()
        with app.app_context():
            # Check if tables already exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if existing_tables:
                print(f"[INFO] Database tables already exist ({len(existing_tables)} tables found)")
                print("[INFO] Skipping table creation to preserve existing data")
                print("[INFO] If you want to reset the database, manually drop tables first")
            else:
                print("[SETUP] No existing tables found, creating new tables...")
                db.create_all()
            
            # Verify table creation by testing a simple query
            print("[VERIFY] Verifying table creation...")
            
            # Test each major table
            tables_to_test = [
                ('category', 'SELECT COUNT(*) FROM category'),
                ('user', 'SELECT COUNT(*) FROM user'),
                ('item', 'SELECT COUNT(*) FROM item'),
                ('trade', 'SELECT COUNT(*) FROM trade'),
                ('message', 'SELECT COUNT(*) FROM message')
            ]
            
            for table_name, test_query in tables_to_test:
                try:
                    result = db.session.execute(db.text(test_query))
                    count = result.scalar()
                    print(f"  [OK] {table_name} table: {count} records")
                except Exception as table_error:
                    print(f"  [ERROR] {table_name} table: {table_error}")
                    return False
            
            # Add initial categories
            category_count = Category.query.count()
            if category_count == 0:
                print("\n[SETUP] Adding initial categories...")
                categories = [
                    Category(name='Electronics & Gadgets', description='Phones, laptops, tablets, and other electronic devices'),
                    Category(name='Fashion', description='Clothing, accessories, and footwear for men and women'),
                    Category(name='Watches & Accessories', description='Watches, jewelry, and fashion accessories'),
                    Category(name='Beauty & Personal Care', description='Cosmetics, skincare, and personal care items'),
                    Category(name='Gaming & Entertainment', description='Gaming consoles, games, and entertainment equipment'),
                    Category(name='Photography & Audio', description='Cameras, audio equipment, and related accessories'),
                    Category(name='Home & Living', description='Furniture, appliances, and home decor'),
                    Category(name='Sports & Outdoors', description='Sports equipment, outdoor gear, and fitness items'),
                    Category(name='Kids & Baby', description='Baby gear, toys, and children\'s items'),
                    Category(name='Books & Hobbies', description='Books, collectibles, and hobby items'),
                    Category(name='Tickets & Vouchers', description='Event tickets, gift cards, and vouchers'),
                    Category(name='Automotive', description='Auto parts, accessories, and car care items'),
                    Category(name='Others', description='Items that don\'t fit in other categories')
                ]
                
                for category in categories:
                    db.session.add(category)
                
                db.session.commit()
                print(f"[SUCCESS] Added {len(categories)} categories")
            else:
                print(f"[INFO] Categories already exist ({category_count} categories)")
            
            return True
            
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("BARTR DATABASE SETUP")
    print("=" * 50)
    
    # Step 1: Create MySQL database and user
    if not create_mysql_database():
        print("\n[ERROR] Database creation failed. Please fix MySQL connection issues.")
        return False
    
    # Step 2: Create tables and initial data
    if not create_database_tables():
        print("\n[ERROR] Table creation failed. Please check the error messages above.")
        return False
    
    print("\n[SUCCESS] Database setup completed successfully!")
    print("[INFO] Your Bartr application is ready to use!")
    print("\n[NEXT] Next steps:")
    print("1. Run: python3 run.py")
    print("2. Open: http://localhost:5001")
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)