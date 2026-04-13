from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

db = SQLAlchemy()

class Role(enum.Enum):
    """User role enumeration"""
    ADMIN = 'Admin'
    TOP_MANAGEMENT = 'Top Management'
    HR_MANAGER = 'HR Manager'
    PROJECT_MANAGER = 'Project Manager'
    EMPLOYEE = 'Employee'

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.EMPLOYEE)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('Employee', backref='user', uselist=False, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role
    
    def __repr__(self):
        return f'<User {self.username}>'

class Skill(db.Model):
    """Skill model"""
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    employees = db.relationship('Employee', secondary='employee_skills', backref='skills', lazy=True)
    projects = db.relationship('Project', secondary='project_skills', backref='required_skills', lazy=True)
    
    def __repr__(self):
        return f'<Skill {self.name}>'

# Association table for Employee-Skill relationship
employee_skills = db.Table(
    'employee_skills',
    db.Column('employee_id', db.Integer, db.ForeignKey('employees.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True)
)

# Association table for Project-Skill relationship
project_skills = db.Table(
    'project_skills',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True)
)

class Employee(db.Model):
    """Employee model"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    years_of_experience = db.Column(db.Integer, default=0)
    availability = db.Column(db.Integer, default=100)  # Percentage
    is_available = db.Column(db.Boolean, default=True)
    hire_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    allocations = db.relationship('ResourceAllocation', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    def get_full_name(self):
        """Get employee's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_current_workload(self):
        """Calculate current workload percentage"""
        total = 0
        for allocation in self.allocations:
            if allocation.project.status != 'Completed' and allocation.project.status != 'Cancelled':
                total += allocation.allocation_percentage
        return total
    
    def can_add_more_work(self, additional_percentage):
        """Check if employee can take more work"""
        current_workload = self.get_current_workload()
        return (current_workload + additional_percentage) <= 100
    
    def __repr__(self):
        return f'<Employee {self.get_full_name()}>'

class Project(db.Model):
    """Project model"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Planning')  # Planning, In Progress, On Hold, Completed, Cancelled
    start_date = db.Column(db.Date)
    deadline = db.Column(db.Date, nullable=False)
    budget = db.Column(db.Float)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_projects')
    allocations = db.relationship('ResourceAllocation', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def get_allocated_employees(self):
        """Get list of allocated employees"""
        return [(alloc.employee, alloc.allocation_percentage) for alloc in self.allocations]
    
    def get_total_allocation(self):
        """Get total allocation percentage for project"""
        return sum(alloc.allocation_percentage for alloc in self.allocations)
    
    def __repr__(self):
        return f'<Project {self.name}>'

class ResourceAllocation(db.Model):
    """Resource allocation model"""
    __tablename__ = 'resource_allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    allocation_percentage = db.Column(db.Float, nullable=False)  # 0-100%
    allocation_date = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    end_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    allocated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    allocator = db.relationship('User', foreign_keys=[allocated_by], backref='allocations_created')
    
    # Unique constraint to prevent duplicate allocations
    __table_args__ = (db.UniqueConstraint('employee_id', 'project_id', name='unique_emp_proj'),)
    
    def __repr__(self):
        return f'<ResourceAllocation {self.employee_id}-{self.project_id}>'

class AuditLog(db.Model):
    """Audit log model for tracking changes"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    entity_type = db.Column(db.String(50), nullable=False)  # User, Employee, Project, ResourceAllocation
    entity_id = db.Column(db.Integer)
    changes = db.Column(db.Text)  # JSON string of changes
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.entity_type}>'
