from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import current_user, login_required
from app.models import db, Employee, User, Skill, ResourceAllocation, Role
from app.forms import EmployeeForm
from app.utils import require_role, log_audit, export_to_csv
from datetime import datetime
import csv
from io import StringIO

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/')
@login_required
@require_role('Admin', 'HR Manager', 'Project Manager', 'Top Management')
def list_employees():
    """List all employees"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    
    query = Employee.query
    
    if search:
        query = query.filter(
            (Employee.first_name.ilike(f'%{search}%')) |
            (Employee.last_name.ilike(f'%{search}%')) |
            (Employee.email.ilike(f'%{search}%'))
        )
    
    if department:
        query = query.filter(Employee.department == department)
    
    employees = query.paginate(page=page, per_page=20)
    
    # Get departments for filter
    departments = db.session.query(Employee.department).distinct().filter(Employee.department != None).all()
    departments = [d[0] for d in departments]
    
    return render_template('employees/list.html',
                         title='Employees',
                         employees=employees,
                         departments=departments,
                         search=search,
                         department=department)

@employees_bp.route('/<int:employee_id>')
@login_required
@require_role('Admin', 'HR Manager', 'Project Manager', 'Top Management')
def view_employee(employee_id):
    """View employee details"""
    employee = Employee.query.get_or_404(employee_id)
    
    allocations = ResourceAllocation.query.filter_by(employee_id=employee_id).all()
    
    context = {
        'title': f'{employee.get_full_name()}',
        'employee': employee,
        'allocations': allocations,
        'current_workload': employee.get_current_workload(),
        'available_capacity': 100 - employee.get_current_workload()
    }
    
    return render_template('employees/view.html', **context)

@employees_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_role('Admin', 'HR Manager')
def create_employee():
    """Create new employee"""
    form = EmployeeForm()
    
    if form.validate_on_submit():
        try:
            # Create user account
            user = User(
                username=form.email.data.split('@')[0],
                email=form.email.data,
                role=Role.EMPLOYEE
            )
            user.set_password('InitialPassword123')  # Default password
            
            db.session.add(user)
            db.session.flush()
            
            # Create employee record
            employee = Employee(
                user_id=user.id,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                department=form.department.data,
                position=form.position.data,
                years_of_experience=form.years_of_experience.data,
                availability=form.availability.data,
                is_available=form.is_available.data,
                hire_date=form.hire_date.data
            )
            
            # Add skills
            if form.skills.data:
                skills = Skill.query.filter(Skill.id.in_(form.skills.data)).all()
                employee.skills.extend(skills)
            
            db.session.add(employee)
            db.session.commit()
            
            log_audit('CREATE', 'Employee', employee.id, {
                'name': employee.get_full_name(),
                'email': employee.email
            })
            
            flash(f'Employee {employee.get_full_name()} created successfully!', 'success')
            return redirect(url_for('employees.view_employee', employee_id=employee.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating employee: {str(e)}', 'danger')
    
    return render_template('employees/form.html',
                         title='Create Employee',
                         form=form,
                         action='Create')

@employees_bp.route('/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('Admin', 'HR Manager')
def edit_employee(employee_id):
    """Edit employee"""
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm()
    
    if form.validate_on_submit():
        try:
            old_data = {
                'first_name': employee.first_name,
                'department': employee.department,
                'availability': employee.availability
            }
            
            employee.first_name = form.first_name.data
            employee.last_name = form.last_name.data
            employee.email = form.email.data
            employee.department = form.department.data
            employee.position = form.position.data
            employee.years_of_experience = form.years_of_experience.data
            employee.availability = form.availability.data
            employee.is_available = form.is_available.data
            employee.hire_date = form.hire_date.data
            
            # Update skills
            employee.skills.clear()
            if form.skills.data:
                skills = Skill.query.filter(Skill.id.in_(form.skills.data)).all()
                employee.skills.extend(skills)
            
            db.session.commit()
            
            log_audit('UPDATE', 'Employee', employee.id, {
                'old_data': old_data,
                'new_data': {
                    'first_name': form.first_name.data,
                    'department': form.department.data,
                    'availability': form.availability.data
                }
            })
            
            flash(f'Employee updated successfully!', 'success')
            return redirect(url_for('employees.view_employee', employee_id=employee.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating employee: {str(e)}', 'danger')
    elif request.method == 'GET':
        form.first_name.data = employee.first_name
        form.last_name.data = employee.last_name
        form.email.data = employee.email
        form.department.data = employee.department
        form.position.data = employee.position
        form.years_of_experience.data = employee.years_of_experience
        form.availability.data = employee.availability
        form.is_available.data = employee.is_available
        form.hire_date.data = employee.hire_date
        form.skills.data = [s.id for s in employee.skills]
    
    return render_template('employees/form.html',
                         title=f'Edit {employee.get_full_name()}',
                         form=form,
                         action='Edit',
                         employee=employee)

@employees_bp.route('/<int:employee_id>/delete', methods=['POST'])
@login_required
@require_role('Admin', 'HR Manager')
def delete_employee(employee_id):
    """Delete employee"""
    employee = Employee.query.get_or_404(employee_id)
    
    try:
        emp_name = employee.get_full_name()
        user_id = employee.user_id
        
        db.session.delete(employee)
        # Also delete associated user
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
        
        db.session.commit()
        
        log_audit('DELETE', 'Employee', employee_id, {
            'name': emp_name
        })
        
        flash(f'Employee {emp_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting employee: {str(e)}', 'danger')
    
    return redirect(url_for('employees.list_employees'))

@employees_bp.route('/export/csv')
@login_required
@require_role('Admin', 'HR Manager', 'Top Management')
def export_employees_csv():
    """Export employees to CSV"""
    employees = Employee.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['First Name', 'Last Name', 'Email', 'Department', 'Position', 'Years of Experience', 'Availability %', 'Hire Date', 'Current Workload %', 'Skills'])
    
    for emp in employees:
        skills = ', '.join([s.name for s in emp.skills])
        writer.writerow([
            emp.first_name,
            emp.last_name,
            emp.email,
            emp.department or '',
            emp.position or '',
            emp.years_of_experience,
            emp.availability,
            emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else '',
            round(emp.get_current_workload(), 2),
            skills
        ])
    
    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=employees.csv"}
    )
    return response

@employees_bp.route('/<int:employee_id>/workload-api')
@login_required
def employee_workload_api(employee_id):
    """API endpoint for employee workload data"""
    employee = Employee.query.get_or_404(employee_id)
    allocations = ResourceAllocation.query.filter_by(employee_id=employee_id).all()
    
    data = {
        'employee_id': employee.id,
        'name': employee.get_full_name(),
        'total_workload': employee.get_current_workload(),
        'available_capacity': 100 - employee.get_current_workload(),
        'allocations': [
            {
                'project_id': a.project_id,
                'project_name': a.project.name,
                'allocation_percentage': a.allocation_percentage,
                'status': a.project.status
            } for a in allocations
        ]
    }
    
    return jsonify(data)
