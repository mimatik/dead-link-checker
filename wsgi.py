"""WSGI entry point for production deployment"""

from app import create_app

# Create the application instance for Gunicorn
application = create_app()

if __name__ == "__main__":
    application.run()
