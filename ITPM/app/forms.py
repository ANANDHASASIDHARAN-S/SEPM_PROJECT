from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, FloatField, TextAreaField, BooleanField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange
from app.models import User, Skill, Role

class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    """Registration form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    role = SelectField('Role', choices=[], validators=[DataRequired()])
    submit = SubmitField('Register')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role.choices = [
            (Role.EMPLOYEE.value, 'Employee'),
            (Role.PROJECT_MANAGER.value, 'Project Manager'),
            (Role.HR_MANAGER.value, 'HR Manager'),
            (Role.TOP_MANAGEMENT.value, 'Top Management')
        ]
    
    def validate_username(self, field):
        """Check if username is unique"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')
    
    def validate_email(self, field):
        """Check if email is unique"""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')

class EmployeeForm(FlaskForm):
    """Employee form"""
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    department = StringField('Department', validators=[Length(max=100)])
    position = StringField('Position', validators=[Length(max=100)])
    years_of_experience = IntegerField('Years of Experience', validators=[NumberRange(min=0, max=80)])
    availability = IntegerField('Availability (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    is_available = BooleanField('Currently Available')
    hire_date = DateField('Hire Date', format='%Y-%m-%d')
    skills = SelectField('Skills', coerce=int, render_kw={'multiple': True})
    submit = SubmitField('Save Employee')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skills.choices = [(s.id, s.name) for s in Skill.query.all()]

class ProjectForm(FlaskForm):
    """Project form"""
    name = StringField('Project Name', validators=[DataRequired(), Length(min=2, max=200)])
    description = TextAreaField('Description')
    status = SelectField('Status', choices=[
        ('Planning', 'Planning'),
        ('In Progress', 'In Progress'),
        ('On Hold', 'On Hold'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d')
    deadline = DateField('Deadline', format='%Y-%m-%d', validators=[DataRequired()])
    budget = FloatField('Budget', validators=[NumberRange(min=0)])
    required_skills = SelectField('Required Skills', coerce=int, render_kw={'multiple': True})
    submit = SubmitField('Save Project')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_skills.choices = [(s.id, s.name) for s in Skill.query.all()]

class ResourceAllocationForm(FlaskForm):
    """Resource allocation form"""
    employee = SelectField('Employee', coerce=int, validators=[DataRequired()])
    project = SelectField('Project', coerce=int, validators=[DataRequired()])
    allocation_percentage = FloatField('Allocation (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    end_date = DateField('End Date', format='%Y-%m-%d')
    notes = TextAreaField('Notes')
    submit = SubmitField('Allocate Resource')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Employee, Project
        self.employee.choices = [(e.id, e.get_full_name()) for e in Employee.query.all()]
        self.project.choices = [(p.id, p.name) for p in Project.query.all()]

class SkillForm(FlaskForm):
    """Skill form"""
    name = StringField('Skill Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Save Skill')
    
    def validate_name(self, field):
        """Check if skill name is unique"""
        skill = Skill.query.filter_by(name=field.data).first()
        if skill and (not hasattr(self, 'skill_id') or self.skill_id != skill.id):
            raise ValidationError('Skill already exists')

class FilterForm(FlaskForm):
    """Filter form for various lists"""
    search = StringField('Search', validators=[Length(max=100)])
    status = SelectField('Status', choices=[('', 'All')], default='')
    department = SelectField('Department', choices=[('', 'All')], default='')
    submit = SubmitField('Filter')
