# Resource Allocation & Workforce Planning System (RAWP)

A comprehensive Full Stack Flask-based system for managing organizational resources, project allocation, and workforce planning with role-based access control.

## 📋 Features

### Authentication & Security
- ✅ User registration and secure login system
- ✅ Role-based access control (5 roles)
- ✅ Password hashing with Werkzeug
- ✅ Session management
- ✅ Audit logging for all changes
- ✅ Account status management

### Employee Management
- ✅ Employee profile management
- ✅ Skills and competency tracking
- ✅ Years of experience tracking
- ✅ Department and position assignment
- ✅ Availability management
- ✅ Hire date tracking
- ✅ Employee workload analysis

### Project Management
- ✅ Project creation and tracking
- ✅ Project status management (Planning, In Progress, On Hold, Completed, Cancelled)
- ✅ Required skills specification
- ✅ Budget tracking
- ✅ Deadline management
- ✅ Team member assignment

### Resource Allocation
- ✅ Smart allocation system preventing employee overloading
- ✅ Workload calculation and validation (max 100%)
- ✅ Skills matching analysis
- ✅ Allocation percentage tracking
- ✅ End date management for allocations
- ✅ Duplicate allocation prevention

### Dashboard & Reporting
- ✅ Real-time dashboard with statistics
- ✅ Interactive charts using Chart.js
- ✅ Project status distribution visualization
- ✅ Employee workload visualization
- ✅ Workforce utilization report with CSV export
- ✅ Project resource report with CSV export
- ✅ Comprehensive audit logging

### Role-Based Features
- **Admin**: Full system control, user management, skill management, audit logs
- **Top Management**: View reports, system health, audit logs, strategic insights
- **HR Manager**: Employee management, skill management, allocation tracking
- **Project Manager**: Project management, resource allocation, team management
- **Employee**: View own profile, skills, allocated projects, workload

### UI/UX
- ✅ Dark professional theme using Bootstrap 5
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Sidebar navigation with role-based menu
- ✅ Flash messages for user feedback
- ✅ Data pagination
- ✅ Search and filtering capabilities
- ✅ Progress bars for workload visualization

## 📁 Project Structure

```
ITPM/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # SQLAlchemy database models
│   ├── forms.py                 # WTForms form definitions
│   ├── utils.py                 # Utilities, decorators, helpers
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication routes
│   │   ├── main.py              # Dashboard, profile, reports
│   │   ├── employees.py         # Employee management
│   │   ├── projects.py          # Project management
│   │   ├── allocations.py       # Resource allocation
│   │   └── admin.py             # Admin & system management
│   ├── templates/
│   │   ├── base.html            # Base template with navbar/sidebar
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── main/
│   │   │   ├── dashboard.html
│   │   │   ├── profile.html
│   │   │   ├── audit_logs.html
│   │   │   ├── workforce_report.html
│   │   │   └── project_report.html
│   │   ├── employees/
│   │   │   ├── list.html
│   │   │   ├── form.html
│   │   │   └── view.html
│   │   ├── projects/
│   │   │   ├── list.html
│   │   │   ├── form.html
│   │   │   └── view.html
│   │   ├── allocations/
│   │   │   ├── list.html
│   │   │   ├── form.html
│   │   │   └── view.html
│   │   └── admin/
│   │       ├── dashboard.html
│   │       ├── system_health.html
│   │       ├── skills/
│   │       │   ├── list.html
│   │       │   └── form.html
│   │       └── users/
│   │           └── list.html
│   └── static/
│       ├── css/
│       └── js/
├── config.py                     # Flask configuration
├── run.py                        # Application entry point
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Installation

1. **Clone or download the project**
```bash
cd ITPM
```

2. **Create a virtual environment (recommended)**
```bash
python -m venv venv
```

3. **Activate virtual environment**

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Initialize the database with sample data**
```bash
python run.py init-db
```

This will:
- Create the SQLite database
- Create all necessary tables
- Populate with comprehensive sample data
- Display login credentials

6. **Run the application**
```bash
python run.py
```

The application will be available at: `http://localhost:5000`

## 👤 Demo Credentials

After running `init-db`, use these credentials to test different roles:

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@123` |
| HR Manager | `hr_manager` | `HR@123` |
| Project Manager | `pm_john` | `PM@123` |
| Top Management | `exec` | `Exec@123` |
| Employee | `alice` | `Employee@123` |

## 📊 Database Models

### User
- Username, Email, Password (hashed)
- Role (enum): Admin, Top Management, HR Manager, Project Manager, Employee
- Active status
- Created/Updated timestamps

### Employee
- First/Last Name, Email
- Department, Position
- Years of Experience
- Availability percentage
- Status (available/unavailable)
- Hire Date
- Skills (many-to-many relationship)

### Project
- Name, Description
- Status (Planning, In Progress, On Hold, Completed, Cancelled)
- Start Date, Deadline
- Budget
- Required Skills (many-to-many relationship)
- Creator (User relationship)

### Skill
- Name, Description
- Associated Employees and Projects (many-to-many)

### ResourceAllocation
- Employee, Project (relationship)
- Allocation Percentage (0-100)
- Start/End Date
- Notes
- Allocated By (User relationship)

### AuditLog
- User, Action, Entity Type, Entity ID
- Changes (JSON)
- IP Address
- Timestamp

## 🔐 Security Features

1. **Password Security**: Passwords hashed using Werkzeug (PBKDF2)
2. **CSRF Protection**: Flask-WTF CSRF token validation
3. **SQL Injection Prevention**: SQLAlchemy ORM usage
4. **Role-Based Access Control**: Authorization decorators on routes
5. **Audit Trail**: All changes logged with user and timestamp
6. **Session Management**: Secure session cookies

## 🎯 Key Business Logic

### Workload Management
- Employees cannot be allocated more than 100% capacity
- System validates before creating/updating allocations
- Prevents overbooking of resources

### Skill Matching
- System calculates skill match percentage for allocations
- Helps identify skill gaps
- Recommends employees based on required skills

### Allocation Constraints
- Unique constraint: One employee per project
- Prevents duplicate allocations
- Automatic validation on save

## 🛠️ Technologies Used

- **Backend**: Flask 2.3.3
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login with password hashing
- **Forms**: WTForms with Flask-WTF
- **Frontend**: Bootstrap 5, Chart.js
- **Database Migrations**: Flask-Migrate

## 📈 Reports & Analytics

1. **Workforce Utilization Report**
   - Employee workload analysis
   - Available capacity tracking
   - Skill inventory

2. **Project Resource Report**
   - Team composition per project
   - Budget vs. allocation
   - Resource requirements

3. **System Health Dashboard**
   - User statistics by role
   - Project status distribution
   - Employee utilization levels
   - Database integrity checks

4. **Audit Logs**
   - Complete change history
   - User action tracking
   - Data integrity verification

## 📤 Export Features

- CSV export for employee lists
- CSV export for project information
- Customizable report generation
- Data can be imported into Excel/Google Sheets

## 🔧 Configuration

Edit `config.py` to customize:
- Secret key (change in production)
- Database location
- Session timeout
- CSRF settings

## 📝 Usage Examples

### Adding a New Employee
1. Navigate to Employees → Add Employee
2. Fill in personal information
3. Select skills from the list
4. Set availability percentage
5. Save

### Creating a Project
1. Navigate to Projects → Create Project
2. Enter project details
3. Select required skills
4. Set deadline and status
5. Save

### Allocating Resources
1. Navigate to Allocations → New Allocation
2. Select employee and project
3. Set allocation percentage
4. System validates workload capacity
5. Add optional notes
6. Save

### Generating Reports
1. Dashboard: View real-time statistics
2. Workforce Report: Employee utilization analysis
3. Project Report: Resource allocation overview
4. Audit Logs: Complete activity history

## ⚙️ Maintenance

### Reset Database
```bash
# Delete the database file
rm resource_allocation.db

# Reinitialize
python run.py init-db
```

### Database Location
The SQLite database (`resource_allocation.db`) is created in the project root directory by default.

## 🚀 Deployment Considerations

For production deployment:

1. **Environment Variables**
   ```bash
   FLASK_ENV=production
   SECRET_KEY=<strong-random-key>
   ```

2. **Security Updates**
   - Change SECRET_KEY
   - Use environment variables for sensitive data
   - Enable HTTPS
   - Set SESSION_COOKIE_SECURE=True

3. **Database**
   - Consider PostgreSQL for production
   - Regular backups
   - Use connection pooling

4. **Web Server**
   - Use Gunicorn or uWSGI
   - Run behind Nginx/Apache
   - Enable proper logging

## 📚 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Employees
- `GET /employees/` - List all employees
- `GET /employees/<id>` - View employee details
- `POST /employees/create` - Create employee
- `POST /employees/<id>/edit` - Edit employee
- `POST /employees/<id>/delete` - Delete employee
- `GET /employees/export/csv` - Export employees

### Projects
- `GET /projects/` - List all projects
- `GET /projects/<id>` - View project details
- `POST /projects/create` - Create project
- `POST /projects/<id>/edit` - Edit project
- `POST /projects/<id>/delete` - Delete project
- `GET /projects/export/csv` - Export projects

### Allocations
- `GET /allocations/` - List all allocations
- `GET /allocations/<id>` - View allocation details
- `POST /allocations/create` - Create allocation
- `POST /allocations/<id>/edit` - Edit allocation
- `POST /allocations/<id>/delete` - Delete allocation

### Reports
- `GET /` - Dashboard
- `GET /workforce-report` - Workforce utilization report
- `GET /project-report` - Project resource report
- `GET /audit-logs` - Audit trail logs

## 🤝 Contributing

This is a complete, production-ready system. For modifications:

1. Follow the existing code structure
2. Maintain role-based access control
3. Add audit logs for new entities
4. Test workload validation logic
5. Keep templates consistent with dark theme

## 📄 License

This project is provided as-is for organizational use.

## 🆘 Troubleshooting

### Database Issues
```bash
# Recreate database
python run.py init-db
```

### Port Already in Use
```bash
# Run on different port
python -c "from app import create_app; app = create_app(); app.run(port=5001)"
```

### Template Not Found
- Ensure all template files are in correct directories
- Check template paths in routes

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## 📞 Support

For issues, review the code comments and docstrings. The system is designed to be self-documenting.

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Status**: Production Ready
