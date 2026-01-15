from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app import db
from app.models import User, Class, Section, Group, Subject, Chapter, Topic, teacher_assignments
from app.forms import UserForm, ClassForm, SubjectForm, ChapterForm, TopicForm, AssignmentForm
from app.utils import role_required
from sqlalchemy import or_, func

bp = Blueprint('admin', __name__)

@bp.route('/')
@role_required('admin')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')

# --- User Management ---
@bp.route('/users')
@role_required('admin')
@login_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/assignment/create', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def create_assignment():
    import time
    call_timestamp = time.time()
    print("=" * 50)
    print(f"create_assignment function called at {call_timestamp}")
    print(f"Request method: {request.method}")
    print("=" * 50)

    form = AssignmentForm()
    form.teacher_id.choices = [(t.id, t.full_name) for t in User.query.filter_by(role='teacher').order_by('full_name').all()]
    form.class_id.choices = [(c.id, c.name) for c in Class.query.order_by('name').all()]

    # Always set these choices BEFORE validate_on_submit!
    class_id = form.class_id.data or request.form.get('class_id', type=int)
    if class_id:
        form.subject_id.choices = [(s.id, s.name) for s in Subject.query.filter_by(class_id=class_id).all()]
        # Add None option for optional fields (using None instead of empty string)
        form.section_id.choices = [(None, 'Select Section')] + [(s.id, s.name) for s in Section.query.filter_by(class_id=class_id).all()]
        form.group_id.choices = [(None, 'Select Group')] + [(g.id, g.name) for g in Group.query.filter_by(class_id=class_id).all()]
    else:
        form.subject_id.choices = []
        form.section_id.choices = [(None, 'Select Section')]
        form.group_id.choices = [(None, 'Select Group')]

    if request.method == 'POST':
        print("Form errors:", form.errors)
        print("Request.form:", request.form)
        print("POST request received")
        print("subject_id choices:", form.subject_id.choices)
        print("subject_id submitted value:", request.form.get('subject_id'))
        print("section_id choices:", form.section_id.choices)
        print("section_id submitted value:", request.form.get('section_id'))
        print("group_id choices:", form.group_id.choices)
        print("group_id submitted value:", request.form.get('group_id'))
        print("form.validate() result:", form.validate())
        print("form.validate_on_submit() result:", form.validate_on_submit())

    if form.validate_on_submit():
        print("Form validation successful")
        print("Creating assignment for:")
        print(f"  Teacher ID: {form.teacher_id.data}")
        print(f"  Class ID: {form.class_id.data}")
        print(f"  Subject ID: {form.subject_id.data} (will be validated)")
        print(f"  Section ID: {form.section_id.data}")
        print(f"  Group ID: {form.group_id.data}")

        # Validate that subject_id is actually selected (not None or empty)
        if not form.subject_id.data:
            flash('Please select a subject.', 'danger')
            return render_template('admin/edit_assignments.html', form=form, title='Create Assignment')
        
        # Ensure subject_id is a single integer (not a list or multiple values)
        subject_id = form.subject_id.data
        if isinstance(subject_id, list):
            flash('Please select only one subject.', 'danger')
            return render_template('admin/edit_assignments.html', form=form, title='Create Assignment')
        if not isinstance(subject_id, int):
            try:
                subject_id = int(subject_id)
            except (ValueError, TypeError):
                flash('Invalid subject selected.', 'danger')
                return render_template('admin/edit_assignments.html', form=form, title='Create Assignment')
        
        print(f"Validated Subject ID: {subject_id} (single integer)")

        # Get section_id and group_id from form (they're now properly coerced to None if empty)
        section_id = form.section_id.data
        group_id = form.group_id.data

        # Check for existing assignment - EXACT match required
        existing = db.session.execute(
            db.select(teacher_assignments).where(
                teacher_assignments.c.teacher_id == form.teacher_id.data,
                teacher_assignments.c.class_id == form.class_id.data,
                teacher_assignments.c.subject_id == subject_id,
                teacher_assignments.c.section_id == section_id,
                teacher_assignments.c.group_id == group_id
            )
        ).first()

        if existing:
            flash('This assignment already exists.', 'warning')
            return redirect(url_for('admin.assignments'))
        
        # Count existing assignments BEFORE insert
        count_before = db.session.execute(
            db.select(func.count()).select_from(teacher_assignments)
        ).scalar()
        print(f"Assignments in database BEFORE insert: {count_before}")
        
        # Create ONLY ONE assignment - ensure we're using the validated subject_id
        print("=" * 50)
        print("INSERTING SINGLE ASSIGNMENT:")
        print(f"  Teacher ID: {form.teacher_id.data}")
        print(f"  Class ID: {form.class_id.data}")
        print(f"  Subject ID: {subject_id} (SINGLE SUBJECT ONLY)")
        print(f"  Section ID: {section_id}")
        print(f"  Group ID: {group_id}")
        print("=" * 50)
        
        # CRITICAL: Verify we're only inserting ONE record
        # This is a SINGLE insert statement - it will only create ONE row
        stmt = teacher_assignments.insert().values(
            teacher_id=form.teacher_id.data,
            class_id=form.class_id.data,
            section_id=section_id,
            group_id=group_id,
            subject_id=subject_id  # SINGLE subject_id, not a loop
        )
        
        try:
            result = db.session.execute(stmt)
            db.session.commit()
            
            # Verify only ONE row was inserted
            inserted_id = result.lastrowid
            count_after = db.session.execute(
                db.select(func.count()).select_from(teacher_assignments)
            ).scalar()
            
            print(f"Assignment inserted with ID: {inserted_id}")
            print(f"Assignments in database AFTER insert: {count_after}")
            print(f"Difference: {count_after - count_before} assignment(s) created")
            
            if count_after - count_before != 1:
                print("=" * 50)
                print("WARNING: More than ONE assignment was created!")
                print("This should not happen - investigating...")
                print("=" * 50)
            else:
                print("SUCCESS: Only ONE assignment created!")
                print("=" * 50)
            
            flash('Teacher assigned successfully.', 'success')
            return redirect(url_for('admin.assignments'))
        except Exception as e:
            print("=" * 50)
            print("ERROR creating assignment:", str(e))
            print("Form errors:", form.errors)
            print("Request form data:", request.form)
            print("=" * 50)
            db.session.rollback()
            flash(f'Error creating assignment: {str(e)}', 'danger')

    return render_template('admin/edit_assignments.html', form=form, title='Create Assignment')




@bp.route('/user/create', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def create_user():
    form = UserForm(original_username='')
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing_user:
            if existing_user.username == form.username.data:
                flash(f'A user with the username "{form.username.data}" already exists.', 'warning')
            else:
                flash(f'A user with the email "{form.email.data}" already exists.', 'warning')
            return render_template('admin/edit_user.html', form=form, title='Create User')
        
        user = User(username=form.username.data, email=form.email.data, full_name=form.full_name.data, role=form.role.data)
        user.set_password('defaultpassword') # Set a default password
        db.session.add(user)
        try:
        db.session.commit()
        flash(f'User {form.username.data} created with default password: defaultpassword', 'success')
        return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'danger')
            return render_template('admin/edit_user.html', form=form, title='Create User')
    return render_template('admin/edit_user.html', form=form, title='Create User')

@bp.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(original_username=user.username, obj=user)
    if form.validate_on_submit():
        # Check if username or email is being changed and already exists
        if form.username.data != user.username:
            existing_username = User.query.filter_by(username=form.username.data).first()
            if existing_username:
                flash(f'A user with the username "{form.username.data}" already exists.', 'warning')
                return render_template('admin/edit_user.html', form=form, title='Edit User')
        
        if form.email.data != user.email:
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash(f'A user with the email "{form.email.data}" already exists.', 'warning')
                return render_template('admin/edit_user.html', form=form, title='Edit User')
        
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.role = form.role.data
        try:
        db.session.commit()
        flash('User information updated.', 'success')
        return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
            return render_template('admin/edit_user.html', form=form, title='Edit User')
    return render_template('admin/edit_user.html', form=form, title='Edit User')

# --- Class, Section, Group Management ---
@bp.route('/classes')
@role_required('admin')
@login_required
def classes():
    all_classes = Class.query.all()
    return render_template('admin/classes.html', all_classes=all_classes)

@bp.route('/class/create', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def create_class():
    form = ClassForm()
    if form.validate_on_submit():
        # Check if class with this name already exists
        existing_class = Class.query.filter_by(name=form.name.data).first()
        if existing_class:
            flash(f'A class with the name "{form.name.data}" already exists.', 'warning')
            return render_template('admin/edit_class.html', form=form, title='Create Class')
        
        new_class = Class(name=form.name.data)
        db.session.add(new_class)
        try:
        db.session.commit()
        flash(f'{form.name.data} created.', 'success')
        return redirect(url_for('admin.classes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating class: {str(e)}', 'danger')
            return render_template('admin/edit_class.html', form=form, title='Create Class')
    return render_template('admin/edit_class.html', form=form, title='Create Class')

# --- Subject Management ---
@bp.route('/subjects')
@role_required('admin')
@login_required
def subjects():
    all_subjects = Subject.query.all()
    return render_template('admin/subjects.html', all_subjects=all_subjects)

@bp.route('/subject/create', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def create_subject():
    form = SubjectForm()
    form.class_id.choices = [(c.id, c.name) for c in Class.query.order_by('name').all()]
    if form.validate_on_submit():
        new_subject = Subject(name=form.name.data, class_id=form.class_id.data)
        db.session.add(new_subject)
        try:
        db.session.commit()
        flash(f'Subject {form.name.data} created.', 'success')
        return redirect(url_for('admin.subjects'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating subject: {str(e)}', 'danger')
            return render_template('admin/edit_subject.html', form=form, title='Create Subject')
    return render_template('admin/edit_subject.html', form=form, title='Create Subject')

# --- Syllabus Management ---
@bp.route('/syllabus')
@role_required('admin')
@login_required
def syllabus():
    # Get all classes with their subjects, ordered by class name
    classes = Class.query.order_by('name').all()
    return render_template('admin/syllabus.html', classes=classes)

@bp.route('/chapter/create', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def create_chapter():
    form = ChapterForm()
    form.subject_id.choices = [(s.id, f"{s.name} ({s.class_obj.name})") for s in Subject.query.order_by('name').all()]
    if form.validate_on_submit():
        new_chapter = Chapter(name=form.name.data, subject_id=form.subject_id.data)
        db.session.add(new_chapter)
        try:
        db.session.commit()
        flash(f'Chapter {form.name.data} created.', 'success')
        return redirect(url_for('admin.syllabus'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating chapter: {str(e)}', 'danger')
            return render_template('admin/edit_chapter.html', form=form, title='Create Chapter')
    return render_template('admin/edit_chapter.html', form=form, title='Create Chapter')

@bp.route('/topic/create', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def create_topic():
    form = TopicForm()
    # Populate choices dynamically
    chapters = Chapter.query.join(Subject).join(Class).order_by(Class.name, Subject.name, Chapter.name).all()
    form.chapter_id.choices = [(c.id, f"{c.subject.class_obj.name} > {c.subject.name} > {c.name}") for c in chapters]
    if form.validate_on_submit():
        new_topic = Topic(name=form.name.data, chapter_id=form.chapter_id.data)
        db.session.add(new_topic)
        try:
        db.session.commit()
        flash(f'Topic {form.name.data} created.', 'success')
        return redirect(url_for('admin.syllabus'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating topic: {str(e)}', 'danger')
            return render_template('admin/edit_topic.html', form=form, title='Create Topic')
    return render_template('admin/edit_topic.html', form=form, title='Create Topic')

# --- Teacher Assignments ---
@bp.route('/assignments')
@role_required('admin')
@login_required
def assignments():
    # This is a complex query to get all assignments with IDs
    print("=" * 50)
    print("FETCHING ASSIGNMENTS FROM DATABASE...")
    
    # First, let's check what's actually in the database
    all_assignments_raw = db.session.execute(
        db.select(teacher_assignments)
    ).all()
    print(f"Raw assignments in database: {len(all_assignments_raw)}")
    for row in all_assignments_raw:
        print(f"  Assignment ID: {row.id}, Teacher: {row.teacher_id}, Class: {row.class_id}, Subject: {row.subject_id}, Section: {row.section_id}")
    
    # Now get the formatted assignments
    # CRITICAL FIX: Start from teacher_assignments table to avoid cartesian product
    assigns = db.session.execute(
        db.select(
            teacher_assignments.c.id.label('assignment_id'),
            User.full_name.label('teacher_name'),
            Class.name.label('class_name'),
            Section.name.label('section_name'),
            Group.name.label('group_name'),
            Subject.name.label('subject_name')
        ).select_from(teacher_assignments)
        .join(User, teacher_assignments.c.teacher_id == User.id)
        .join(Class, teacher_assignments.c.class_id == Class.id)
        .join(Subject, teacher_assignments.c.subject_id == Subject.id)  # This is the KEY - join on the actual subject_id in the assignment
        .join(Section, teacher_assignments.c.section_id == Section.id, isouter=True)
        .join(Group, teacher_assignments.c.group_id == Group.id, isouter=True)
        .order_by(Class.name, Subject.name, User.full_name)
    ).all()
    
    print(f"Formatted assignments returned: {len(assigns)}")
    for assign in assigns:
        print(f"  ID: {assign.assignment_id}, Teacher: {assign.teacher_name}, Class: {assign.class_name}, Subject: {assign.subject_name}")
    print("=" * 50)
    
    return render_template('admin/assignments.html', assignments=assigns)

<<<<<<< HEAD
@bp.route('/assignment/create', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def create_assignment():
    form = AssignmentForm()
    form.teacher_id.choices = [(t.id, t.full_name) for t in User.query.filter_by(role='teacher').order_by('full_name').all()]
    form.class_id.choices = [(c.id, c.name) for c in Class.query.order_by('name').all()]

    # Initialize dynamic choices to empty lists to avoid TypeError
    form.subject_id.choices = []
    form.section_id.choices = []
    form.group_id.choices = []

    if request.method == 'POST':
        class_id = request.form.get('class_id', type=int)
        if class_id:
            form.subject_id.choices = [(s.id, s.name) for s in Subject.query.filter_by(class_id=class_id).all()]
            form.section_id.choices = [(s.id, s.name) for s in Section.query.filter_by(class_id=class_id).all()]
            form.group_id.choices = [(g.id, g.name) for g in Group.query.filter_by(class_id=class_id).all()]
    
    if form.validate_on_submit():
        # Get section_id and group_id from request form (they come from JavaScript)
        section_id = request.form.get('section_id') or None
        group_id = request.form.get('group_id') or None
        
        # Convert to int if not None
        if section_id:
            section_id = int(section_id)
        if group_id:
            group_id = int(group_id)
        
        # Check for existing assignment
        existing = db.session.execute(
            db.select(teacher_assignments).where(
                teacher_assignments.c.teacher_id == form.teacher_id.data,
                teacher_assignments.c.class_id == form.class_id.data,
                teacher_assignments.c.subject_id == form.subject_id.data,
                teacher_assignments.c.section_id == section_id,
                teacher_assignments.c.group_id == group_id
            )
        ).first()

        if existing:
            flash('This assignment already exists.', 'warning')
        else:
            stmt = teacher_assignments.insert().values(
                teacher_id=form.teacher_id.data,
                class_id=form.class_id.data,
                section_id=section_id,
                group_id=group_id,
                subject_id=form.subject_id.data
            )
            try:
            db.session.execute(stmt)
            db.session.commit()
            flash('Teacher assigned successfully.', 'success')
        return redirect(url_for('admin.assignments'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating assignment: {str(e)}', 'danger')
    
    return render_template('admin/edit_assignments.html', form=form, title='Create Assignment')

    print("Form errors:", form.errors) # Debugging line
    print("Request form data on validation fail:", request.form) # Debugging line


=======
>>>>>>> d272804f59c5a5dc8c1761db6f211c7d14627af9
@bp.route('/api/sections-for-class/<int:class_id>')
def api_sections_for_class(class_id):
    sections = Section.query.filter_by(class_id=class_id).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in sections])

@bp.route('/api/groups-for-class/<int:class_id>')
def api_groups_for_class(class_id):
    groups = Group.query.filter_by(class_id=class_id).all()
    return jsonify([{'id': g.id, 'name': g.name} for g in groups])

@bp.route('/api/subjects-for-class/<int:class_id>')
def api_subjects_for_class(class_id):
    subjects = Subject.query.filter_by(class_id=class_id).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in subjects])

@bp.route('/assignment/<int:id>/delete', methods=['POST'])
@role_required('admin')
@login_required
def delete_assignment(id):
    print("=" * 50)
    print(f"DELETE ASSIGNMENT REQUEST - ID: {id}")
    
    # Check what assignment we're about to delete
    assignment_to_delete = db.session.execute(
        db.select(teacher_assignments).where(teacher_assignments.c.id == id)
    ).first()
    
    if assignment_to_delete:
        print(f"Assignment to delete:")
        print(f"  ID: {assignment_to_delete.id}")
        print(f"  Teacher ID: {assignment_to_delete.teacher_id}")
        print(f"  Class ID: {assignment_to_delete.class_id}")
        print(f"  Subject ID: {assignment_to_delete.subject_id}")
        print(f"  Section ID: {assignment_to_delete.section_id}")
        print(f"  Group ID: {assignment_to_delete.group_id}")
    else:
        print("WARNING: Assignment with ID {id} not found!")
    
    # Count before delete
    count_before = db.session.execute(
        db.select(func.count()).select_from(teacher_assignments)
    ).scalar()
    print(f"Assignments BEFORE delete: {count_before}")
    
    try:
        stmt = teacher_assignments.delete().where(teacher_assignments.c.id == id)
        result = db.session.execute(stmt)
        db.session.commit()
        
        # Count after delete
        count_after = db.session.execute(
            db.select(func.count()).select_from(teacher_assignments)
        ).scalar()
        print(f"Assignments AFTER delete: {count_after}")
        print(f"Difference: {count_before - count_after} assignment(s) deleted")
        
        if count_before - count_after != 1:
            print("WARNING: More than ONE assignment was deleted!")
        else:
            print("SUCCESS: Only ONE assignment deleted!")
        print("=" * 50)
        
        flash('Assignment deleted successfully.', 'success')
    except Exception as e:
        print(f"ERROR deleting assignment: {str(e)}")
        print("=" * 50)
        db.session.rollback()
        flash(f'Error deleting assignment: {str(e)}', 'danger')
    return redirect(url_for('admin.assignments'))