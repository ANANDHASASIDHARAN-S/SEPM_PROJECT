from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.models import db, Skill, User, Employee, Role, AuditLog
from app.forms import SkillForm
from app.utils import require_role, log_audit
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@require_role('Admin', 'Top Management')
def admin_dashboard():
    """Admin dashboard"""
    total_users = User.query.count()
    total_skills = Skill.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Recent audit logs
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    
    # User growth (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= seven_days_ago).count()
    
    # Audit activity
    audit_counts = db.session.query(
        AuditLog.action,
        db.func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).all()
    
    context = {
        'title': 'Admin Dashboard',
        'total_users': total_users,
        'total_skills': total_skills,
        'active_users': active_users,
        'new_users_week': new_users_week,
        'recent_logs': recent_logs,
        'audit_counts': audit_counts
    }
    
    return render_template('admin/dashboard.html', **context)

@admin_bp.route('/skills')
@login_required
@require_role('Admin', 'HR Manager')
def list_skills():
    """List all skills"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Skill.query
    
    if search:
        query = query.filter(Skill.name.ilike(f'%{search}%'))
    
    skills = query.paginate(page=page, per_page=20)
    
    return render_template('admin/skills/list.html',
                         title='Skills',
                         skills=skills,
                         search=search)

@admin_bp.route('/skills/create', methods=['GET', 'POST'])
@login_required
@require_role('Admin', 'HR Manager')
def create_skill():
    """Create new skill"""
    form = SkillForm()
    
    if form.validate_on_submit():
        try:
            skill = Skill(
                name=form.name.data,
                description=form.description.data
            )
            
            db.session.add(skill)
            db.session.commit()
            
            log_audit('CREATE', 'Skill', skill.id, {
                'name': skill.name
            })
            
            flash(f'Skill {skill.name} created successfully!', 'success')
            return redirect(url_for('admin.list_skills'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating skill: {str(e)}', 'danger')
    
    return render_template('admin/skills/form.html',
                         title='Create Skill',
                         form=form,
                         action='Create')

@admin_bp.route('/skills/<int:skill_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('Admin', 'HR Manager')
def edit_skill(skill_id):
    """Edit skill"""
    skill = Skill.query.get_or_404(skill_id)
    form = SkillForm()
    
    if form.validate_on_submit():
        try:
            old_name = skill.name
            
            skill.name = form.name.data
            skill.description = form.description.data
            
            db.session.commit()
            
            log_audit('UPDATE', 'Skill', skill.id, {
                'old_name': old_name,
                'new_name': form.name.data
            })
            
            flash('Skill updated successfully!', 'success')
            return redirect(url_for('admin.list_skills'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating skill: {str(e)}', 'danger')
    elif request.method == 'GET':
        form.name.data = skill.name
        form.description.data = skill.description
    
    return render_template('admin/skills/form.html',
                         title=f'Edit {skill.name}',
                         form=form,
                         action='Edit',
                         skill=skill)

@admin_bp.route('/skills/<int:skill_id>/delete', methods=['POST'])
@login_required
@require_role('Admin', 'HR Manager')
def delete_skill(skill_id):
    """Delete skill"""
    skill = Skill.query.get_or_404(skill_id)
    
    try:
        skill_name = skill.name
        
        db.session.delete(skill)
        db.session.commit()
        
        log_audit('DELETE', 'Skill', skill_id, {
            'name': skill_name
        })
        
        flash(f'Skill {skill_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting skill: {str(e)}', 'danger')
    
    return redirect(url_for('admin.list_skills'))

@admin_bp.route('/users')
@login_required
@require_role('Admin')
def list_users():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    role = request.args.get('role', '')
    
    query = User.query
    
    if role:
        query = query.filter(User.role == Role[role.upper().replace(' ', '_')])
    
    users = query.paginate(page=page, per_page=20)
    
    roles = [r.value for r in Role]
    
    return render_template('admin/users/list.html',
                         title='Users',
                         users=users,
                         roles=roles,
                         selected_role=role)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@require_role('Admin')
def toggle_user_status(user_id):
    """Toggle user active status"""
    if user_id == current_user.id:
        flash('You cannot disable your own account!', 'danger')
        return redirect(url_for('admin.list_users'))
    
    user = User.query.get_or_404(user_id)
    
    try:
        old_status = user.is_active
        user.is_active = not user.is_active
        
        db.session.commit()
        
        log_audit('UPDATE', 'User', user.id, {
            'status_changed': f'{old_status} to {user.is_active}'
        })
        
        status_text = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.username} {status_text}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user status: {str(e)}', 'danger')
    
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/system-health')
@login_required
@require_role('Admin', 'Top Management')
def system_health():
    """System health and statistics"""
    from app.models import Employee, Project, ResourceAllocation
    
    # Database statistics
    total_records = {
        'users': User.query.count(),
        'employees': Employee.query.count(),
        'projects': Project.query.count(),
        'allocations': ResourceAllocation.query.count(),
        'skills': Skill.query.count(),
        'audit_logs': AuditLog.query.count()
    }
    
    # Role distribution
    role_distribution = db.session.query(
        User.role,
        db.func.count(User.id).label('count')
    ).group_by(User.role).all()
    
    # Project status distribution
    project_status = db.session.query(
        Project.status,
        db.func.count(Project.id).label('count')
    ).group_by(Project.status).all()
    
    # Employee utilization statistics
    employees = Employee.query.all()
    underutilized = sum(1 for emp in employees if emp.get_current_workload() < 50)
    fully_utilized = sum(1 for emp in employees if emp.get_current_workload() >= 100)
    
    context = {
        'title': 'System Health',
        'total_records': total_records,
        'role_distribution': role_distribution,
        'project_status': project_status,
        'underutilized_employees': underutilized,
        'fully_utilized_employees': fully_utilized
    }
    
    return render_template('admin/system_health.html', **context)
