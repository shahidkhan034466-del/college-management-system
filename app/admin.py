from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app import db
from app.models import User, Class, Section, Group, Subject, Chapter, Topic, teacher_assignments
from app.forms import UserForm, ClassForm, SubjectForm, ChapterForm, TopicForm, AssignmentForm
from app.utils import role_required
from sqlalchemy import or_

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
    assigns = db.session.execute(
        db.select(
            teacher_assignments.c.id.label('assignment_id'),
            User.full_name.label('teacher_name'),
            Class.name.label('class_name'),
            Section.name.label('section_name'),
            Group.name.label('group_name'),
            Subject.name.label('subject_name')
        ).select_from(User).join(teacher_assignments).join(Class).join(Subject)
        .join(Section, teacher_assignments.c.section_id == Section.id, isouter=True)
        .join(Group, teacher_assignments.c.group_id == Group.id, isouter=True)
        .order_by(Class.name, Subject.name, User.full_name)
    ).all()
    return render_template('admin/assignments.html', assignments=assigns)

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
    try:
        stmt = teacher_assignments.delete().where(teacher_assignments.c.id == id)
        db.session.execute(stmt)
        db.session.commit()
        flash('Assignment deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting assignment: {str(e)}', 'danger')
    return redirect(url_for('admin.assignments'))