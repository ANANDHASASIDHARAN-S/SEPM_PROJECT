from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app.models import db, ResourceAllocation, Employee, Project, User
from app.forms import ResourceAllocationForm
from app.utils import require_role, log_audit, calculate_skill_match
from datetime import datetime

allocations_bp = Blueprint('allocations', __name__)

@allocations_bp.route('/')
@login_required
@require_role('Admin', 'Project Manager', 'HR Manager', 'Top Management')
def list_allocations():
    """List all resource allocations"""
    page = request.args.get('page', 1, type=int)
    employee_id = request.args.get('employee', '', type=int)
    project_id = request.args.get('project', '', type=int)
    
    query = ResourceAllocation.query
    
    if employee_id:
        query = query.filter(ResourceAllocation.employee_id == employee_id)
    
    if project_id:
        query = query.filter(ResourceAllocation.project_id == project_id)
    
    allocations = query.order_by(ResourceAllocation.created_at.desc()).paginate(page=page, per_page=20)
    
    employees = Employee.query.all()
    projects = Project.query.all()
    
    return render_template('allocations/list.html',
                         title='Resource Allocations',
                         allocations=allocations,
                         employees=employees,
                         projects=projects,
                         selected_employee=employee_id,
                         selected_project=project_id)

@allocations_bp.route('/<int:allocation_id>')
@login_required
@require_role('Admin', 'Project Manager', 'HR Manager', 'Top Management')
def view_allocation(allocation_id):
    """View allocation details"""
    allocation = ResourceAllocation.query.get_or_404(allocation_id)
    
    skill_match = calculate_skill_match(
        allocation.employee.skills,
        allocation.project.required_skills
    )
    
    context = {
        'title': 'Allocation Details',
        'allocation': allocation,
        'skill_match': round(skill_match, 2)
    }
    
    return render_template('allocations/view.html', **context)

@allocations_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_role('Admin', 'Project Manager', 'HR Manager')
def create_allocation():
    """Create new resource allocation"""
    form = ResourceAllocationForm()
    
    if form.validate_on_submit():
        try:
            employee = Employee.query.get(form.employee.data)
            project = Project.query.get(form.project.data)
            
            # Check if allocation already exists
            existing = ResourceAllocation.query.filter_by(
                employee_id=form.employee.data,
                project_id=form.project.data
            ).first()
            
            if existing:
                flash('This employee is already allocated to this project.', 'warning')
                return redirect(url_for('allocations.view_allocation', allocation_id=existing.id))
            
            # Check workload
            if not employee.can_add_more_work(form.allocation_percentage.data):
                current_workload = employee.get_current_workload()
                available = 100 - current_workload
                flash(f'Cannot allocate {form.allocation_percentage.data}%. Employee has {available}% capacity available.', 'danger')
                return redirect(url_for('allocations.create_allocation'))
            
            allocation = ResourceAllocation(
                employee_id=form.employee.data,
                project_id=form.project.data,
                allocation_percentage=form.allocation_percentage.data,
                end_date=form.end_date.data,
                notes=form.notes.data,
                allocated_by=current_user.id
            )
            
            db.session.add(allocation)
            db.session.commit()
            
            log_audit('CREATE', 'ResourceAllocation', allocation.id, {
                'employee': employee.get_full_name(),
                'project': project.name,
                'percentage': form.allocation_percentage.data
            })
            
            flash(f'{employee.get_full_name()} allocated to {project.name} for {form.allocation_percentage.data}%!', 'success')
            return redirect(url_for('allocations.view_allocation', allocation_id=allocation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating allocation: {str(e)}', 'danger')
    
    return render_template('allocations/form.html',
                         title='Allocate Resource',
                         form=form,
                         action='Create')

@allocations_bp.route('/<int:allocation_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('Admin', 'Project Manager', 'HR Manager')
def edit_allocation(allocation_id):
    """Edit resource allocation"""
    allocation = ResourceAllocation.query.get_or_404(allocation_id)
    form = ResourceAllocationForm()
    
    if form.validate_on_submit():
        try:
            employee = Employee.query.get(form.employee.data)
            old_percentage = allocation.allocation_percentage
            new_percentage = form.allocation_percentage.data
            
            # Check workload if percentage increased
            if new_percentage > old_percentage:
                additional = new_percentage - old_percentage
                if not employee.can_add_more_work(additional):
                    current_workload = employee.get_current_workload()
                    available = 100 - current_workload + old_percentage
                    flash(f'Cannot allocate {new_percentage}%. Employee has {available}% capacity available.', 'danger')
                    return redirect(url_for('allocations.edit_allocation', allocation_id=allocation_id))
            
            allocation.allocation_percentage = new_percentage
            allocation.end_date = form.end_date.data
            allocation.notes = form.notes.data
            
            db.session.commit()
            
            log_audit('UPDATE', 'ResourceAllocation', allocation.id, {
                'old_percentage': old_percentage,
                'new_percentage': new_percentage
            })
            
            flash('Allocation updated successfully!', 'success')
            return redirect(url_for('allocations.view_allocation', allocation_id=allocation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating allocation: {str(e)}', 'danger')
    elif request.method == 'GET':
        form.employee.data = allocation.employee_id
        form.project.data = allocation.project_id
        form.allocation_percentage.data = allocation.allocation_percentage
        form.end_date.data = allocation.end_date
        form.notes.data = allocation.notes
    
    return render_template('allocations/form.html',
                         title='Edit Allocation',
                         form=form,
                         action='Edit',
                         allocation=allocation)

@allocations_bp.route('/<int:allocation_id>/delete', methods=['POST'])
@login_required
@require_role('Admin', 'Project Manager', 'HR Manager')
def delete_allocation(allocation_id):
    """Delete resource allocation"""
    allocation = ResourceAllocation.query.get_or_404(allocation_id)
    
    try:
        alloc_details = f'{allocation.employee.get_full_name()} from {allocation.project.name}'
        
        db.session.delete(allocation)
        db.session.commit()
        
        log_audit('DELETE', 'ResourceAllocation', allocation_id, {
            'employee': allocation.employee.get_full_name(),
            'project': allocation.project.name
        })
        
        flash(f'Allocation {alloc_details} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting allocation: {str(e)}', 'danger')
    
    return redirect(url_for('allocations.list_allocations'))

@allocations_bp.route('/employee/<int:employee_id>/available-capacity')
@login_required
def employee_available_capacity(employee_id):
    """API endpoint to get employee available capacity"""
    employee = Employee.query.get_or_404(employee_id)
    
    current_workload = employee.get_current_workload()
    available_capacity = 100 - current_workload
    
    data = {
        'employee_id': employee.id,
        'current_workload': current_workload,
        'available_capacity': available_capacity,
        'can_allocate': available_capacity > 0
    }
    
    return jsonify(data)

@allocations_bp.route('/project/<int:project_id>/team-composition')
@login_required
def project_team_composition(project_id):
    """API endpoint for project team composition"""
    project = Project.query.get_or_404(project_id)
    allocations = ResourceAllocation.query.filter_by(project_id=project_id).all()
    
    team = []
    for alloc in allocations:
        skill_match = calculate_skill_match(
            alloc.employee.skills,
            project.required_skills
        )
        team.append({
            'employee_id': alloc.employee_id,
            'name': alloc.employee.get_full_name(),
            'allocation_percentage': alloc.allocation_percentage,
            'skill_match_percentage': round(skill_match, 2),
            'skills': [s.name for s in alloc.employee.skills]
        })
    
    data = {
        'project_id': project.id,
        'project_name': project.name,
        'team': team,
        'total_allocation': project.get_total_allocation(),
        'required_skills': [s.name for s in project.required_skills]
    }
    
    return jsonify(data)
