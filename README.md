# Bartr - Trading Application

A simple web application for trading items between users, now running on MySQL database.

## Quick Start

Just run one command to start the application:

```bash
python3 run.py
```

The script will automatically:
- ✅ Check and install dependencies
- ✅ Create MySQL database and user
- ✅ Setup all database tables
- ✅ Add initial categories
- ✅ Start the application on http://localhost:5001

## Requirements

- Python 3.7+
- MySQL Server (running locally)

## First Time Setup

1. **Install MySQL** (if not already installed)
2. **Start MySQL service**
3. **Run the application:**
   ```bash
   python3 run.py
   ```

That's it! Everything else is automatic.

## Database Configuration

The application uses these default MySQL settings (in `.env` file):
- Database: `bartr_db`
- Username: `bartr_user`
- Password: `bartr_password`
- Host: `localhost`

You can modify these in the `.env` file if needed.

## Features

- User registration and authentication
- Item listing and browsing
- Trading system
- Real-time messaging
- Reviews and ratings
- Admin panel
- File uploads

## Troubleshooting

If you encounter issues:

1. **MySQL connection failed**: Make sure MySQL is running
2. **Dependencies missing**: The app will install them automatically
3. **Port 5001 in use**: Stop other applications using this port

The application provides helpful error messages and guidance for common issues.