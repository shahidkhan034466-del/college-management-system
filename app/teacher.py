from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from app.models import Subject, Chapter, Topic, TopicCompletion, Class, Section, Group, db, teacher_assignments
from app.utils import calculate_progress, role_required
from sqlalchemy import or_

bp = Blueprint('teacher', __name__)

@bp.route('/')
@role_required('teacher')
@login_required
def dashboard():
    # Complex query to get all subjects assigned to the current teacher
    assigned_data = db.session.execute(
        db.select(
            Subject.id, Subject.name,
            Class.id.label('class_id'), Class.name.label('class_name'),
            Section.id.label('section_id'), Section.name.label('section_name'),
            Group.id.label('group_id'), Group.name.label('group_name')
        ).select_from(Subject).join(teacher_assignments).join(Class)
        .join(Section, teacher_assignments.c.section_id == Section.id, isouter=True)
        .join(Group, teacher_assignments.c.group_id == Group.id, isouter=True)
        .where(teacher_assignments.c.teacher_id == current_user.id)
    ).all()

    subjects_with_progress = []
    for data in assigned_data:
        subject = Subject.query.get(data.id)
        progress = calculate_progress(subject.id, 'subject')
        
        chapters_with_topics = []
        for chapter in subject.chapters:
            chapter_progress = calculate_progress(chapter.id, 'chapter')
            total_topics = len(chapter.topics)
            completed_topics = TopicCompletion.query.join(Topic).filter(
                Topic.chapter_id == chapter.id, TopicCompletion.is_completed == True
            ).count()
            
            topics_data = []
            for topic in chapter.topics:
                completion = TopicCompletion.query.filter_by(topic_id=topic.id).first()
                topics_data.append({
                    'id': topic.id,
                    'name': topic.name,
                    'is_completed': completion.is_completed if completion else False,
                    'completion_date': completion.completion_date if completion else None
                })
            
            chapters_with_topics.append({
                'id': chapter.id,
                'name': chapter.name,
                'progress': chapter_progress,
                'total_topics': total_topics,
                'completed_topics': completed_topics,
                'topics': topics_data
            })

        subjects_with_progress.append({
            'id': subject.id,
            'name': subject.name,
            'class_name': data.class_name,
            'section_name': data.section_name,
            'group_name': data.group_name,
            'progress': progress,
            'chapters': chapters_with_topics
        })

    return render_template('teacher/dashboard.html', subjects=subjects_with_progress)