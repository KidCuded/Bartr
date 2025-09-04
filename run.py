#!/usr/bin/env python3
"""
Bartr - Simple Trading Application
Run this script to start the application easily
"""

import sys
import subprocess

def install_dependencies():
    """Install required dependencies if not already installed"""
    try:
        # Test core imports
        import flask
        import flask_sqlalchemy
        import flask_login
        import pymysql
        import pytz
        print("[OK] All dependencies are installed")
        return True
    except ImportError as e:
        print(f"[WARNING] Missing dependency: {e}")
        print("[SETUP] Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("[SUCCESS] Dependencies installed successfully!")
            # Test imports again after installation
            import flask
            import flask_sqlalchemy
            import flask_login
            import pymysql
            import pytz
            return True
        except (subprocess.CalledProcessError, ImportError) as install_error:
            print(f"[ERROR] Failed to install dependencies: {install_error}")
            print("[INFO] Please manually run: pip install -r requirements.txt")
            return False


def check_mysql_connection():
    """Check if MySQL connection is working and setup if needed"""
    try:
        from bartr import create_app, db
        app = create_app()
        with app.app_context():
            # Try to connect to database and test a simple query
            with db.engine.connect() as connection:
                connection.execute(db.text("SELECT 1"))
            
            # Try to test if tables exist
            try:
                connection.execute(db.text("SELECT COUNT(*) FROM category"))
                print("[OK] MySQL connection and tables verified")
                return True
            except Exception:
                print("[WARNING] Database connected but tables missing")
                raise Exception("Tables not found")
                
    except Exception as e:
        print(f"[WARNING] Database issue: {e}")
        print("[SETUP] Running database setup...")
        
        # Run the database setup script
        try:
            import subprocess
            result = subprocess.run([sys.executable, 'setup_database.py'], 
                                  capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                print("[SUCCESS] Database setup completed successfully!")
                return True
            else:
                print(f"[ERROR] Database setup failed:")
                print(result.stdout)
                print(result.stderr)
        except Exception as setup_error:
            print(f"[ERROR] Could not run database setup: {setup_error}")
        
        print("\n[INFO] Manual setup required:")
        print("1. Make sure MySQL is running")
        print("2. Run: python3 setup_database.py")
        print("3. Then run: python3 run.py")
        return False

def main():
    print("STARTING BARTR APPLICATION")
    print("="*50)
    
    # Check dependencies
    if not install_dependencies():
        return
    
    # Check MySQL connection and auto-setup if needed
    if not check_mysql_connection():
        print("\n[ERROR] Database setup failed.")
        print("Please ensure MySQL is running and try again.")
        return
    
    # Start the application
    print("\n[START] Starting Bartr on http://localhost:5001")
    print("Press Ctrl+C to stop the application")
    print("="*50)
    
    from bartr import create_app, socketio
    app = create_app()
    try:
        socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=5001, host='0.0.0.0')
    except KeyboardInterrupt:
        print("\n[STOP] Bartr application stopped")

if __name__ == '__main__':
    main() 