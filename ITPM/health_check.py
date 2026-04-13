#!/usr/bin/env python
"""
Health Check Script for ITPM Application
Verifies that the app is running correctly and can access the database
"""

import sys
import os
import urllib.request
import urllib.error
from datetime import datetime

def print_status(status, message):
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"  # Green or Red
    reset = "\033[0m"
    print(f"{color}[{symbol}]{reset} {message}")
    return status

def check_python_version():
    """Check if Python version is 3.9+"""
    version = sys.version_info
    status = version.major == 3 and version.minor >= 9
    print_status(status, f"Python version: {version.major}.{version.minor}.{version.micro}")
    return status

def check_dependencies():
    """Check if required packages are installed"""
    packages = ['flask', 'flask_sqlalchemy', 'flask_login', 'wtforms']
    all_ok = True
    
    for package in packages:
        try:
            __import__(package.replace('_', '-'))
            print_status(True, f"Package installed: {package}")
        except ImportError:
            print_status(False, f"Package missing: {package}")
            all_ok = False
    
    return all_ok

def check_database():
    """Check if database exists and is accessible"""
    db_path = 'resource_allocation.db'
    
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print_status(True, f"Database exists: {db_path} ({size} bytes)")
        
        # Try to connect
        try:
            from app import create_app
            app = create_app()
            with app.app_context():
                from app.models import User, Project, Employee
                user_count = User.query.count()
                project_count = Project.query.count()
                print_status(True, f"Database connected: {user_count} users, {project_count} projects")
            return True
        except Exception as e:
            print_status(False, f"Database connection failed: {str(e)}")
            return False
    else:
        print_status(False, f"Database not found: {db_path}")
        return False

def check_application():
    """Check if Flask application starts"""
    try:
        from app import create_app
        app = create_app()
        print_status(True, "Flask application creates successfully")
        return True
    except Exception as e:
        print_status(False, f"Application startup failed: {str(e)}")
        return False

def check_server(url='http://localhost:5000'):
    """Check if server is running"""
    try:
        response = urllib.request.urlopen(url, timeout=5)
        if response.status == 200:
            print_status(True, f"Server is running: {url}")
            return True
    except urllib.error.URLError:
        print_status(False, f"Server is not running: {url}")
        return False
    except Exception as e:
        print_status(False, f"Server check failed: {str(e)}")
        return False

def check_static_files():
    """Check if static files directory exists"""
    static_dir = 'app/static'
    
    if os.path.exists(static_dir) and os.path.isdir(static_dir):
        files = len([f for f in os.listdir(static_dir) if os.path.isfile(os.path.join(static_dir, f))])
        print_status(True, f"Static files directory exists with {files} files")
        return True
    else:
        print_status(False, f"Static files directory not found: {static_dir}")
        return False

def check_templates():
    """Check if templates directory exists"""
    template_dir = 'app/templates'
    
    if os.path.exists(template_dir) and os.path.isdir(template_dir):
        files = len([f for f in os.listdir(template_dir) if f.endswith('.html')])
        print_status(True, f"Templates directory exists with {files} HTML files")
        return True
    else:
        print_status(False, f"Templates directory not found: {template_dir}")
        return False

def main():
    print("\n" + "="*60)
    print("ITPM Application Health Check")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    results = []

    print("1. Environment Checks")
    print("-" * 60)
    results.append(("Python Version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    print()

    print("2. File Structure Checks")
    print("-" * 60)
    results.append(("Static Files", check_static_files()))
    results.append(("Templates", check_templates()))
    results.append(("Database", check_database()))
    print()

    print("3. Application Checks")
    print("-" * 60)
    results.append(("Flask App", check_application()))
    results.append(("Server Running", check_server()))
    print()

    print("="*60)
    print("Summary")
    print("="*60)
    
    passed = sum(1 for _, status in results if status)
    total = len(results)
    
    for name, status in results:
        symbol = "✓" if status else "✗"
        color = "\033[92m" if status else "\033[91m"
        reset = "\033[0m"
        print(f"{color}[{symbol}]{reset} {name}")

    print()
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! Application is ready to use.")
        print(f"   Access at: http://localhost:5000")
        return 0
    else:
        print(f"\n✗ {total - passed} check(s) failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
