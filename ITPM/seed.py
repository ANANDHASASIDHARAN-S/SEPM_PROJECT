"""Seed the database with sample data for testing."""
from app import app
from models import db, User, LeaveType, LeaveBalance, LeavePolicy
from datetime import date


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        current_year = date.today().year

        # ── Leave Types ──────────────────────────────────────────────────
        leave_types = [
            LeaveType(name='Annual Leave', days_per_year=20,
                      description='Regular paid vacation days.'),
            LeaveType(name='Sick Leave', days_per_year=12,
                      description='Leave for medical reasons.'),
            LeaveType(name='Casual Leave', days_per_year=6,
                      description='Short-notice personal leave.'),
            LeaveType(name='Maternity Leave', days_per_year=90,
                      description='Leave for expecting mothers.'),
            LeaveType(name='Paternity Leave', days_per_year=10,
                      description='Leave for new fathers.'),
        ]
        db.session.add_all(leave_types)
        db.session.commit()

        # ── Leave Policy ─────────────────────────────────────────────────
        policy = LeavePolicy(
            name='Standard Leave Policy',
            description='Default company-wide leave policy.',
            max_consecutive_days=15,
            min_days_notice=2,
            carry_forward_allowed=True,
            carry_forward_max_days=5,
            is_active=True
        )
        db.session.add(policy)
        db.session.commit()

        # ── Admin User ───────────────────────────────────────────────────
        admin = User(
            username='admin', email='admin@company.com',
            first_name='System', last_name='Admin',
            role='admin', department='HR', is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

        # ── Managers ─────────────────────────────────────────────────────
        mgr1 = User(
            username='john.manager', email='john@company.com',
            first_name='John', last_name='Smith',
            role='manager', department='Engineering', is_active=True
        )
        mgr1.set_password('manager123')

        mgr2 = User(
            username='sarah.manager', email='sarah@company.com',
            first_name='Sarah', last_name='Johnson',
            role='manager', department='Marketing', is_active=True
        )
        mgr2.set_password('manager123')

        db.session.add_all([mgr1, mgr2])
        db.session.commit()

        # ── Employees ────────────────────────────────────────────────────
        employees = [
            User(username='alice.emp', email='alice@company.com',
                 first_name='Alice', last_name='Williams',
                 role='employee', department='Engineering',
                 manager_id=mgr1.id, is_active=True),
            User(username='bob.emp', email='bob@company.com',
                 first_name='Bob', last_name='Brown',
                 role='employee', department='Engineering',
                 manager_id=mgr1.id, is_active=True),
            User(username='carol.emp', email='carol@company.com',
                 first_name='Carol', last_name='Davis',
                 role='employee', department='Marketing',
                 manager_id=mgr2.id, is_active=True),
            User(username='dave.emp', email='dave@company.com',
                 first_name='Dave', last_name='Wilson',
                 role='employee', department='Marketing',
                 manager_id=mgr2.id, is_active=True),
        ]
        for emp in employees:
            emp.set_password('employee123')
        db.session.add_all(employees)
        db.session.commit()

        # ── Leave Balances (for all non-admin users) ─────────────────────
        all_users = User.query.filter(User.role.in_(['employee', 'manager'])).all()
        for user in all_users:
            for lt in leave_types:
                bal = LeaveBalance(
                    user_id=user.id, leave_type_id=lt.id,
                    year=current_year, total_days=lt.days_per_year, used_days=0
                )
                db.session.add(bal)
        db.session.commit()

        print("=" * 60)
        print("  Database seeded successfully!")
        print("=" * 60)
        print()
        print("  Login Credentials:")
        print("  ──────────────────────────────────────")
        print("  Admin:    admin / admin123")
        print("  Manager:  john.manager / manager123")
        print("  Manager:  sarah.manager / manager123")
        print("  Employee: alice.emp / employee123")
        print("  Employee: bob.emp / employee123")
        print("  Employee: carol.emp / employee123")
        print("  Employee: dave.emp / employee123")
        print("  ──────────────────────────────────────")
        print()


if __name__ == '__main__':
    seed()
