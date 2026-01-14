from flask import Blueprint, render_template, request, send_file, make_response
from flask_login import login_required
from app.utils import role_required, calculate_progress
from app.models import Class, Subject, Chapter, Topic, TopicCompletion, User, db, EmailReport, teacher_assignments
from sqlalchemy import func
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
import pandas as pd

bp = Blueprint('principal', __name__)

@bp.route('/')
@role_required('principal')
@login_required
def dashboard():
    # Overall Progress
    total_topics = db.session.query(func.count(Topic.id)).scalar()
    completed_topics = db.session.query(func.count(TopicCompletion.id)).filter(TopicCompletion.is_completed == True).scalar()
    overall_progress = round((completed_topics / total_topics) * 100) if total_topics > 0 else 0

    # Class-wise Progress
    class_progress_data = []
    for cls in Class.query.all():
        total = db.session.query(func.count(Topic.id)).join(Chapter).join(Subject).filter(Subject.class_id == cls.id).scalar()
        completed = db.session.query(func.count(TopicCompletion.id)).join(Topic).join(Chapter).join(Subject).filter(
            Subject.class_id == cls.id, TopicCompletion.is_completed == True
        ).scalar()
        progress = round((completed / total) * 100) if total > 0 else 0
        class_progress_data.append({'name': cls.name, 'progress': progress})

    # Subject-wise Progress
    subject_progress_data = []
    for subject in Subject.query.all():
        progress = calculate_progress(subject.id, 'subject')
        subject_progress_data.append({'name': f"{subject.name} ({subject.class_obj.name})", 'progress': progress})

    return render_template('principal/dashboard.html', 
                           overall_progress=overall_progress,
                           class_progress=class_progress_data,
                           subject_progress=subject_progress_data)

@bp.route('/reports')
@role_required('principal')
@login_required
def reports():
    class_id = request.args.get('class_id', type=int)
    
    query = db.session.query(
        User.full_name.label('teacher_name'),
        Class.name.label('class_name'),
        Subject.name.label('subject_name'),
        func.count(Topic.id).label('total_topics'),
        func.sum(func.cast(TopicCompletion.is_completed, db.Integer)).label('completed_topics')
    ).select_from(User).join(teacher_assignments).join(Class).join(Subject).join(Chapter).join(Topic)\
    .join(TopicCompletion, Topic.id == TopicCompletion.topic_id, isouter=True)\
    .group_by(User.id, Class.id, Subject.id)

    if class_id:
        query = query.filter(Class.id == class_id)

    report_data = query.all()
    
    # Calculate progress for each row
    detailed_report = []
    for row in report_data:
        progress = round((row.completed_topics or 0) / row.total_topics * 100) if row.total_topics > 0 else 0
        detailed_report.append({
            'teacher_name': row.teacher_name,
            'class_name': row.class_name,
            'subject_name': row.subject_name,
            'total_topics': row.total_topics,
            'completed_topics': row.completed_topics or 0,
            'progress': progress
        })
        
    classes = Class.query.all()
    return render_template('principal/reports.html', reports=detailed_report, classes=classes, selected_class=class_id)

@bp.route('/reports/download/pdf')
@role_required('principal')
@login_required
def download_pdf():
    # This is a simplified PDF generation. A real-world scenario would need more complex layout.
    class_id = request.args.get('class_id', type=int)
    
    # Fetch data (similar to reports view)
    query = db.session.query(
        User.full_name, Class.name, Subject.name,
        func.count(Topic.id), func.sum(func.cast(TopicCompletion.is_completed, db.Integer))
    ).select_from(User).join(teacher_assignments).join(Class).join(Subject).join(Chapter).join(Topic)\
    .join(TopicCompletion, Topic.id == TopicCompletion.topic_id, isouter=True)\
    .group_by(User.id, Class.id, Subject.id)
    if class_id:
        query = query.filter(Class.id == class_id)
    
    report_data = query.all()

    # Create PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.drawString(100, height - 50, "Syllabus Progress Report")
    y_position = height - 100
    for row in report_data:
        progress = round((row[4] or 0) / row[3] * 100) if row[3] > 0 else 0
        text = f"{row[0]} | {row[1]} | {row[2]} | {row[4] or 0}/{row[3]} ({progress}%)"
        p.drawString(50, y_position, text)
        y_position -= 20
        if y_position < 50:
            p.showPage()
            y_position = height - 50

    p.save()
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=progress_report.pdf'
    return response

@bp.route('/reports/download/excel')
@role_required('principal')
@login_required
def download_excel():
    class_id = request.args.get('class_id', type=int)
    
    query = db.session.query(
        User.full_name.label('Teacher'), Class.name.label('Class'), Subject.name.label('Subject'),
        func.count(Topic.id).label('Total Topics'),
        func.sum(func.cast(TopicCompletion.is_completed, db.Integer)).label('Completed Topics')
    ).select_from(User).join(teacher_assignments).join(Class).join(Subject).join(Chapter).join(Topic)\
    .join(TopicCompletion, Topic.id == TopicCompletion.topic_id, isouter=True)\
    .group_by(User.id, Class.id, Subject.id)
    if class_id:
        query = query.filter(Class.id == class_id)

    df = pd.read_sql(query.statement, db.session.bind)
    df['Progress %'] = (df['Completed Topics'] / df['Total Topics'] * 100).round(1).astype(str) + '%'
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Progress Report')
    output.seek(0)

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=progress_report.xlsx'
    return response