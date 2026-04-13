from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from flask_login import current_user, login_required
from app.models import db, Project, Skill, ResourceAllocation, Employee, User
from app.forms import ProjectForm
from app.utils import require_role, log_audit
from datetime import datetime
import csv
from io import StringIO

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/')
@login_required
@require_role('Admin', 'Project Manager', 'Top Management', 'HR Manager')
def list_projects():
    """List all projects"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Project.query
    
    if search:
        query = query.filter(Project.name.ilike(f'%{search}%'))
    
    if status:
        query = query.filter(Project.status == status)
    
    projects = query.order_by(Project.deadline).paginate(page=page, per_page=20)
    
    statuses = db.session.query(Project.status).distinct().all()
    statuses = [s[0] for s in statuses]
    
    return render_template('projects/list.html',
                         title='Projects',
                         projects=projects,
                         statuses=statuses,
                         search=search,
                         status=status)

@projects_bp.route('/<int:project_id>')
@login_required
@require_role('Admin', 'Project Manager', 'Top Management', 'HR Manager')
def view_project(project_id):
    """View project details with resource analysis"""
    from datetime import datetime, timedelta
    
    project = Project.query.get_or_404(project_id)
    allocations = ResourceAllocation.query.filter_by(project_id=project_id).all()
    show_allocate_prompt = request.args.get('allocate', 0, type=int)
    
    # Get allocated employees
    allocated_employee_ids = [a.employee_id for a in allocations]
    allocated_employees = Employee.query.filter(Employee.id.in_(allocated_employee_ids)).all() if allocated_employee_ids else []
    
    # Get required skills
    required_skills = project.required_skills
    
    # Calculate skill coverage
    skill_coverage = {}
    for skill in required_skills:
        employees_with_skill = [emp for emp in allocated_employees if skill in emp.skills]
        skill_coverage[skill.id] = {
            'skill': skill,
            'covered_by': len(employees_with_skill),
            'employees': employees_with_skill
        }
    
    # Get available employees who can fill skill gaps
    all_employees = Employee.query.filter(~Employee.id.in_(allocated_employee_ids)).all()
    available_by_skill = {}
    for skill in required_skills:
        available_employees = [emp for emp in all_employees 
                             if skill in emp.skills and emp.can_add_more_work(50)]
        available_by_skill[skill.id] = available_employees
    
    # Calculate resource suggestions
    resource_suggestions = {}
    
    # 1. Budget Analysis
    resource_suggestions['budget'] = {
        'total': project.budget or 0,
        'team_members': len(allocations) if allocations else 0,
        'per_member': (project.budget / len(allocations)) if allocations and project.budget else 0,
        'recommendation': f"Budget of ${project.budget:,.2f}" if project.budget else "No budget allocated"
    }
    
    # 2. Timeline analysis
    if project.start_date and project.deadline:
        days_duration = (project.deadline - project.start_date).days
        resource_suggestions['timeline'] = {
            'start': project.start_date.strftime('%b %d, %Y'),
            'end': project.deadline.strftime('%b %d, %Y'),
            'days': days_duration,
            'weeks': round(days_duration / 7, 1),
            'status': 'Short-term' if days_duration <= 30 else ('Medium-term' if days_duration <= 90 else 'Long-term')
        }
    
    # 3. Skills Analysis
    skills_gap = len([s for s in required_skills if skill_coverage[s.id]['covered_by'] == 0])
    resource_suggestions['skills'] = {
        'total_required': len(required_skills),
        'covered': len(required_skills) - skills_gap,
        'gaps': skills_gap,
        'coverage_percentage': round((len(required_skills) - skills_gap) / len(required_skills) * 100, 0) if required_skills else 0,
        'list': [s.name for s in required_skills]
    }
    
    # 4. Team size recommendation
    team_efficiency = {
        'Small': (1, 3, 'Best for 1-3 skilled developers, high focus tasks'),
        'Medium': (4, 7, 'Ideal for 4-7 members, balanced team, most projects'),
        'Large': (8, 15, 'For 8-15+ members, complex projects, cross-functional teams')
    }
    
    recommended_team_size = 'Small'
    if skills_gap > 2 or len(required_skills) > 4:
        recommended_team_size = 'Large'
    elif skills_gap > 0 or len(required_skills) > 2:
        recommended_team_size = 'Medium'
    
    resource_suggestions['team_size'] = {
        'recommendation': recommended_team_size,
        'recommended_range': team_efficiency[recommended_team_size][0:2],
        'description': team_efficiency[recommended_team_size][2],
        'current_size': len(allocations)
    }
    
    # 5. Critical recommendations
    recommendations = []
    if skills_gap > 0:
        recommendations.append({
            'type': 'warning',
            'icon': 'exclamation-triangle',
            'title': f'{skills_gap} Skill Gap{"s" if skills_gap > 1 else ""}',
            'message': f'You need to allocate employees with the following missing skills: {", ".join([s.name for s in required_skills if skill_coverage[s.id]["covered_by"] == 0])}'
        })
    
    if len(allocations) == 0:
        recommendations.append({
            'type': 'danger',
            'icon': 'users',
            'title': 'No Team Members',
            'message': 'Add team members to start working on this project'
        })
    elif len(allocations) < 2:
        recommendations.append({
            'type': 'info',
            'icon': 'info-circle',
            'title': 'Small Team',
            'message': f'Consider adding more team members for backup and risk distribution'
        })
    
    if not project.budget:
        recommendations.append({
            'type': 'warning',
            'icon': 'dollar-sign',
            'title': 'Budget Not Set',
            'message': 'Please set a budget for resource planning'
        })
    
    if project.deadline:
        days_left = (project.deadline - datetime.now().date()).days
        if days_left < 0:
            recommendations.append({
                'type': 'danger',
                'icon': 'calendar-times',
                'title': 'Deadline Passed',
                'message': f'Project deadline was {abs(days_left)} days ago'
            })
        elif days_left < 7:
            recommendations.append({
                'type': 'warning',
                'icon': 'calendar',
                'title': 'Urgent Deadline',
                'message': f'Only {days_left} days remaining to deadline'
            })
    
    resource_suggestions['recommendations'] = recommendations
    
    context = {
        'title': project.name,
        'project': project,
        'allocations': allocations,
        'total_allocation': project.get_total_allocation(),
        'required_skills': required_skills,
        'allocated_employees_count': len(allocations),
        'allocated_employees': allocated_employees,
        'skill_coverage': skill_coverage,
        'available_by_skill': available_by_skill,
        'all_available_employees': all_employees[:10],  # Limit to 10 for display
        'show_allocate_prompt': bool(show_allocate_prompt),
        'resource_suggestions': resource_suggestions
    }
    
    return render_template('projects/view.html', **context)

@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_role('Admin', 'Project Manager')
def create_project():
    """Create new project"""
    form = ProjectForm()
    
    if form.validate_on_submit():
        try:
            project = Project(
                name=form.name.data,
                description=form.description.data,
                status=form.status.data,
                start_date=form.start_date.data,
                deadline=form.deadline.data,
                budget=form.budget.data,
                created_by=current_user.id
            )
            
            # Add required skills
            if form.required_skills.data:
                skills = Skill.query.filter(Skill.id.in_(form.required_skills.data)).all()
                project.required_skills.extend(skills)
            
            db.session.add(project)
            db.session.commit()
            
            log_audit('CREATE', 'Project', project.id, {
                'name': project.name,
                'deadline': str(project.deadline)
            })
            
            flash(f'✓ Project "{project.name}" created successfully!', 'success')
            # Redirect with flag to show allocation prompt
            return redirect(url_for('projects.view_project', project_id=project.id, allocate=1))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating project: {str(e)}', 'danger')
    
    return render_template('projects/form.html',
                         title='Create Project',
                         form=form,
                         action='Create')

@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('Admin', 'Project Manager')
def edit_project(project_id):
    """Edit project"""
    project = Project.query.get_or_404(project_id)
    form = ProjectForm()
    
    if form.validate_on_submit():
        try:
            old_data = {
                'name': project.name,
                'status': project.status,
                'deadline': str(project.deadline)
            }
            
            project.name = form.name.data
            project.description = form.description.data
            project.status = form.status.data
            project.start_date = form.start_date.data
            project.deadline = form.deadline.data
            project.budget = form.budget.data
            
            # Update required skills
            project.required_skills.clear()
            if form.required_skills.data:
                skills = Skill.query.filter(Skill.id.in_(form.required_skills.data)).all()
                project.required_skills.extend(skills)
            
            db.session.commit()
            
            log_audit('UPDATE', 'Project', project.id, {
                'old_data': old_data,
                'new_data': {
                    'name': form.name.data,
                    'status': form.status.data,
                    'deadline': str(form.deadline.data)
                }
            })
            
            flash(f'Project updated successfully!', 'success')
            return redirect(url_for('projects.view_project', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating project: {str(e)}', 'danger')
    elif request.method == 'GET':
        form.name.data = project.name
        form.description.data = project.description
        form.status.data = project.status
        form.start_date.data = project.start_date
        form.deadline.data = project.deadline
        form.budget.data = project.budget
        form.required_skills.data = [s.id for s in project.required_skills]
    
    return render_template('projects/form.html',
                         title=f'Edit {project.name}',
                         form=form,
                         action='Edit',
                         project=project)

@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
@require_role('Admin', 'Project Manager')
def delete_project(project_id):
    """Delete project"""
    project = Project.query.get_or_404(project_id)
    
    try:
        proj_name = project.name
        
        db.session.delete(project)
        db.session.commit()
        
        log_audit('DELETE', 'Project', project_id, {
            'name': proj_name
        })
        
        flash(f'Project {proj_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {str(e)}', 'danger')
    
    return redirect(url_for('projects.list_projects'))

@projects_bp.route('/export/csv')
@login_required
@require_role('Admin', 'Project Manager', 'Top Management', 'HR Manager')
def export_projects_csv():
    """Export projects to CSV"""
    projects = Project.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Project Name', 'Status', 'Start Date', 'Deadline', 'Budget', 'Allocated Employees', 'Total Allocation %', 'Required Skills'])
    
    for proj in projects:
        skills = ', '.join([s.name for s in proj.required_skills])
        writer.writerow([
            proj.name,
            proj.status,
            proj.start_date.strftime('%Y-%m-%d') if proj.start_date else '',
            proj.deadline.strftime('%Y-%m-%d'),
            proj.budget or '',
            len(proj.allocations),
            round(proj.get_total_allocation(), 2),
            skills
        ])
    
    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=projects.csv"}
    )
    return response

@projects_bp.route('/<int:project_id>/resources-api')
@login_required
def project_resources_api(project_id):
    """API endpoint for project resources"""
    project = Project.query.get_or_404(project_id)
    allocations = ResourceAllocation.query.filter_by(project_id=project_id).all()
    
    data = {
        'project_id': project.id,
        'name': project.name,
        'status': project.status,
        'total_allocation': project.get_total_allocation(),
        'allocations': [
            {
                'employee_id': a.employee_id,
                'employee_name': a.employee.get_full_name(),
                'allocation_percentage': a.allocation_percentage,
                'skills': [s.name for s in a.employee.skills]
            } for a in allocations
        ],
        'required_skills': [s.name for s in project.required_skills]
    }
    
    return jsonify(data)
