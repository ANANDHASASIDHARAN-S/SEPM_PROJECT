from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_required
from app.models import db, User, Employee, Project, ResourceAllocation, Role
from app.utils import require_role
from sqlalchemy import func
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    # Get statistics
    total_employees = Employee.query.count()
    total_projects = Project.query.count()
    active_projects = Project.query.filter(Project.status.in_(['Planning', 'In Progress'])).count()
    total_allocations = ResourceAllocation.query.count()
    
    # Calculate utilization
    avg_utilization = 0
    if total_employees > 0:
        utilizations = []
        for emp in Employee.query.all():
            utilizations.append(emp.get_current_workload())
        avg_utilization = sum(utilizations) / len(utilizations)
    
    # Get recent activities
    from app.models import AuditLog
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    
    # Get chart data
    project_status_data = db.session.query(
        Project.status,
        func.count(Project.id).label('count')
    ).group_by(Project.status).all()
    
    # Employee workload data
    employee_workload = []
    for emp in Employee.query.limit(10).all():
        employee_workload.append({
            'name': emp.get_full_name(),
            'workload': emp.get_current_workload()
        })
    
    context = {
        'title': 'Dashboard',
        'total_employees': total_employees,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_allocations': total_allocations,
        'avg_utilization': round(avg_utilization, 2),
        'recent_logs': recent_logs,
        'project_status_data': project_status_data,
        'employee_workload': employee_workload
    }
    
    return render_template('main/dashboard.html', **context)

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    employee = None
    if current_user.employee:
        employee = current_user.employee
        allocations = ResourceAllocation.query.filter_by(employee_id=employee.id).all()
    else:
        allocations = []
    
    return render_template('main/profile.html', 
                         title='Profile',
                         employee=employee,
                         allocations=allocations)

@main_bp.route('/audit-logs')
@login_required
@require_role('Admin', 'Top Management', 'HR Manager')
def audit_logs():
    """View audit logs"""
    from app.models import AuditLog
    page = request.args.get('page', 1, type=int)
    
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50)
    
    return render_template('main/audit_logs.html',
                         title='Audit Logs',
                         logs=logs)

@main_bp.route('/reports/workforce')
@login_required
@require_role('Admin', 'Top Management', 'HR Manager', 'Project Manager')
def workforce_report():
    """Workforce utilization report"""
    employees = Employee.query.all()
    
    report_data = []
    for emp in employees:
        current_workload = emp.get_current_workload()
        allocations_count = len(emp.allocations)
        
        report_data.append({
            'id': emp.id,
            'name': emp.get_full_name(),
            'department': emp.department,
            'position': emp.position,
            'skills_count': len(emp.skills),
            'current_workload': current_workload,
            'available_capacity': 100 - current_workload,
            'allocations_count': allocations_count,
            'is_available': emp.is_available
        })
    
    return render_template('main/workforce_report.html',
                         title='Workforce Report',
                         report_data=report_data)

@main_bp.route('/reports/project')
@login_required
@require_role('Admin', 'Top Management', 'HR Manager', 'Project Manager')
def project_report():
    """Project resource report"""
    projects = Project.query.all()
    
    report_data = []
    for project in projects:
        total_allocation = project.get_total_allocation()
        allocated_employees = len(project.allocations)
        
        report_data.append({
            'id': project.id,
            'name': project.name,
            'status': project.status,
            'deadline': project.deadline,
            'allocated_employees': allocated_employees,
            'total_allocation': total_allocation,
            'required_skills': len(project.required_skills),
            'budget': project.budget
        })
    
    return render_template('main/project_report.html',
                         title='Project Report',
                         report_data=report_data)

@main_bp.route('/resource-planning')
@login_required
@require_role('Admin', 'Project Manager', 'Top Management', 'HR Manager')
def resource_planning():
    """Resource planning dashboard showing all project requirements and gaps"""
    from app.models import Skill
    
    # Get all active projects
    projects = Project.query.filter(Project.status.in_(['Planning', 'In Progress'])).all()
    
    # Analyze resource gaps for each project
    project_analysis = []
    total_skills_required = 0
    total_skills_covered = 0
    
    for project in projects:
        allocated_emp_ids = [a.employee_id for a in ResourceAllocation.query.filter_by(project_id=project.id).all()]
        allocated_employees = Employee.query.filter(Employee.id.in_(allocated_emp_ids)).all() if allocated_emp_ids else []
        
        skill_gaps = []
        skill_coverage = {}
        
        for skill in project.required_skills:
            total_skills_required += 1
            employees_with_skill = [emp for emp in allocated_employees if skill in emp.skills]
            
            if employees_with_skill:
                total_skills_covered += 1
                skill_coverage[skill.id] = {'skill': skill, 'covered': True, 'by': len(employees_with_skill)}
            else:
                available_employees = Employee.query.filter(
                    ~Employee.id.in_(allocated_emp_ids),
                    Employee.skills.contains(skill)
                ).all()
                skill_gaps.append({'skill': skill, 'available': len(available_employees)})
                skill_coverage[skill.id] = {'skill': skill, 'covered': False, 'by': 0}
        
        project_analysis.append({
            'project': project,
            'allocated_count': len(allocated_employees),
            'skill_coverage': skill_coverage,
            'skill_gaps': skill_gaps,
            'gap_count': len(skill_gaps),
            'coverage_percentage': (len([s for s in skill_coverage.values() if s['covered']]) / len(project.required_skills) * 100) if project.required_skills else 100
        })
    
    overall_coverage = (total_skills_covered / total_skills_required * 100) if total_skills_required > 0 else 100
    
    return render_template('main/resource_planning.html',
                         title='Resource Planning',
                         project_analysis=project_analysis,
                         overall_coverage=overall_coverage,
                         total_projects=len(projects),
                         total_gaps=sum(p['gap_count'] for p in project_analysis))

