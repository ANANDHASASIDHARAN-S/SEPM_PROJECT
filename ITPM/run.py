#!/usr/bin/env python
"""
Resource Allocation & Workforce Planning System
Run this file to start the application
"""
import os
from app import create_app, db
from app.models import User, Employee, Skill, Project, ResourceAllocation, AuditLog, Role
from datetime import datetime, timedelta
from flask_migrate import Migrate

app = create_app(os.environ.get('FLASK_ENV', 'development'))
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """Context for flask shell"""
    return {
        'db': db,
        'User': User,
        'Employee': Employee,
        'Skill': Skill,
        'Project': Project,
        'ResourceAllocation': ResourceAllocation,
        'AuditLog': AuditLog
    }

def init_sample_data():
    """Initialize sample data for testing"""
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create skills
        skills_data = [
            ('Python', 'Python programming language'),
            ('JavaScript', 'JavaScript and web development'),
            ('SQL', 'Database and SQL expertise'),
            ('DevOps', 'DevOps and deployment'),
            ('Project Management', 'Project management skills'),
            ('Data Analysis', 'Data analysis and visualization'),
            ('UI/UX Design', 'User interface and user experience'),
            ('Cloud Architecture', 'Cloud infrastructure and architecture'),
        ]
        
        skills = []
        for name, desc in skills_data:
            skill = Skill(name=name, description=desc)
            db.session.add(skill)
            skills.append(skill)
        
        db.session.commit()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@company.com',
            role=Role.ADMIN
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
        
        # Create HR Manager
        hr_manager = User(
            username='hr_manager',
            email='hr@company.com',
            role=Role.HR_MANAGER
        )
        hr_manager.set_password('HR@123')
        db.session.add(hr_manager)
        
        # Create Project Manager
        pm1 = User(
            username='pm_john',
            email='john@company.com',
            role=Role.PROJECT_MANAGER
        )
        pm1.set_password('PM@123')
        db.session.add(pm1)
        
        # Create Top Management user
        tm = User(
            username='exec',
            email='executive@company.com',
            role=Role.TOP_MANAGEMENT
        )
        tm.set_password('Exec@123')
        db.session.add(tm)
        
        # Commit users to generate their IDs
        db.session.commit()
        
        # Now create employees with valid user IDs
        hr_emp = Employee(
            user_id=hr_manager.id,
            first_name='Sarah',
            last_name='Johnson',
            email='hr@company.com',
            department='Human Resources',
            position='HR Manager',
            years_of_experience=7,
            availability=80,
            is_available=True,
            hire_date=datetime(2018, 1, 15).date()
        )
        db.session.add(hr_emp)
        
        pm1_emp = Employee(
            user_id=pm1.id,
            first_name='John',
            last_name='Smith',
            email='john@company.com',
            department='Management',
            position='Project Manager',
            years_of_experience=8,
            availability=70,
            is_available=True,
            hire_date=datetime(2017, 3, 20).date()
        )
        pm1_emp.skills.append(skills[0])  # Python
        pm1_emp.skills.append(skills[4])  # Project Management
        db.session.add(pm1_emp)
        
        # Create sample employees
        employees_data = [
            ('Alice', 'Brown', 'alice@company.com', 'Development', 'Senior Developer', 10),
            ('Bob', 'Wilson', 'bob@company.com', 'Development', 'Developer', 5),
            ('Carol', 'Davis', 'carol@company.com', 'Development', 'Full Stack Developer', 6),
            ('David', 'Miller', 'david@company.com', 'DevOps', 'DevOps Engineer', 7),
            ('Emma', 'Garcia', 'emma@company.com', 'Analytics', 'Data Analyst', 4),
            ('Frank', 'Martinez', 'frank@company.com', 'Design', 'UI/UX Designer', 3),
            ('Grace', 'Rodriguez', 'grace@company.com', 'Development', 'Backend Developer', 8),
            ('Henry', 'Lee', 'henry@company.com', 'Infrastructure', 'Cloud Architect', 9),
        ]
        
        created_employees = []
        for first, last, email, dept, pos, exp in employees_data:
            user = User(
                username=email.split('@')[0],
                email=email,
                role=Role.EMPLOYEE
            )
            user.set_password('Employee@123')
            db.session.add(user)
            db.session.flush()
            
            emp = Employee(
                user_id=user.id,
                first_name=first,
                last_name=last,
                email=email,
                department=dept,
                position=pos,
                years_of_experience=exp,
                availability=100,
                is_available=True,
                hire_date=(datetime.utcnow() - timedelta(days=365*exp)).date()
            )
            db.session.add(emp)
            created_employees.append(emp)
        
        db.session.flush()
        
        # Assign skills to employees
        created_employees[0].skills.extend([skills[0], skills[2]])  # Alice: Python, SQL
        created_employees[1].skills.extend([skills[0], skills[1]])  # Bob: Python, JavaScript
        created_employees[2].skills.extend([skills[0], skills[1], skills[2]])  # Carol: Python, JS, SQL
        created_employees[3].skills.extend([skills[1], skills[3]])  # David: JavaScript, DevOps
        created_employees[4].skills.extend([skills[5]])  # Emma: Data Analysis
        created_employees[5].skills.extend([skills[6]])  # Frank: UI/UX Design
        created_employees[6].skills.extend([skills[2], skills[0]])  # Grace: SQL, Python
        created_employees[7].skills.extend([skills[7], skills[3]])  # Henry: Cloud Architecture, DevOps
        
        db.session.commit()
        
        # Create sample projects
        projects_data = [
            ('Mobile App Development', 'Develop new mobile application', 'In Progress', datetime(2024, 1, 1), datetime(2024, 6, 30), 150000),
            ('Data Pipeline Migration', 'Migrate data to cloud infrastructure', 'Planning', datetime(2024, 2, 1), datetime(2024, 8, 31), 200000),
            ('API Modernization', 'Refactor legacy APIs', 'In Progress', datetime(2024, 1, 15), datetime(2024, 5, 15), 100000),
            ('Dashboard Redesign', 'Redesign company dashboard', 'In Progress', datetime(2024, 2, 1), datetime(2024, 4, 30), 80000),
            ('Infrastructure Upgrade', 'Upgrade cloud infrastructure', 'Planning', datetime(2024, 3, 1), datetime(2024, 9, 30), 250000),
        ]
        
        projects = []
        for name, desc, status, start, deadline, budget in projects_data:
            proj = Project(
                name=name,
                description=desc,
                status=status,
                start_date=start.date(),
                deadline=deadline.date(),
                budget=budget,
                created_by=pm1.id
            )
            db.session.add(proj)
            projects.append(proj)
        
        db.session.flush()
        
        # Assign skills to projects
        projects[0].required_skills.extend([skills[0], skills[1], skills[6]])  # Mobile: Python, JS, Design
        projects[1].required_skills.extend([skills[0], skills[2], skills[7]])  # Data: Python, SQL, Cloud
        projects[2].required_skills.extend([skills[0], skills[2]])  # API: Python, SQL
        projects[3].required_skills.extend([skills[6], skills[1]])  # Dashboard: Design, JS
        projects[4].required_skills.extend([skills[3], skills[7]])  # Infrastructure: DevOps, Cloud
        
        db.session.commit()
        
        # Create resource allocations
        allocations_data = [
            (created_employees[0].id, projects[0].id, 60),  # Alice -> Mobile App
            (created_employees[1].id, projects[0].id, 100),  # Bob -> Mobile App
            (created_employees[5].id, projects[3].id, 80),  # Frank -> Dashboard
            (created_employees[2].id, projects[1].id, 70),  # Carol -> Data Pipeline
            (created_employees[6].id, projects[2].id, 50),  # Grace -> API
            (created_employees[7].id, projects[4].id, 100),  # Henry -> Infrastructure
            (created_employees[3].id, projects[1].id, 40),  # David -> Data Pipeline
        ]
        
        for emp_id, proj_id, percentage in allocations_data:
            alloc = ResourceAllocation(
                employee_id=emp_id,
                project_id=proj_id,
                allocation_percentage=percentage,
                allocated_by=pm1.id
            )
            db.session.add(alloc)
        
        db.session.commit()
        
        print("✓ Sample data initialized successfully!")
        print("\nLogin credentials:")
        print("Admin: admin / Admin@123")
        print("HR Manager: hr_manager / HR@123")
        print("Project Manager: pm_john / PM@123")
        print("Executive: exec / Exec@123")
        print("Employee: alice (or any other employee) / Employee@123")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'init-db':
        init_sample_data()
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)
