from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import Topic, TopicCompletion, Subject, teacher_assignments, db
from app.utils import role_required
from datetime import date
from sqlalchemy import select

bp = Blueprint('api', __name__)

@bp.route('/topic/<int:topic_id>', methods=['POST'])
@role_required('teacher')
@login_required
def update_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    subject = topic.chapter.subject

    # Authorization check: Is the current teacher assigned to this subject/class?
    is_assigned = db.session.execute(
        select(teacher_assignments).where(
            teacher_assignments.c.teacher_id == current_user.id,
            teacher_assignments.c.class_id == subject.class_id,
            teacher_assignments.c.subject_id == subject.id
        )
    ).first() is not None

    if not is_assigned:
        return jsonify({'status': 'error', 'message': 'You are not assigned to this subject'}), 403

    data = request.get_json()
    is_completed = data.get('is_completed', False)

    completion_record = TopicCompletion.query.filter_by(topic_id=topic_id).first()
    if completion_record:
        completion_record.is_completed = is_completed
        completion_record.teacher_id = current_user.id
        completion_record.completion_date = date.today() if is_completed else None
    else:
        if is_completed:
            completion_record = TopicCompletion(
                topic_id=topic_id,
                teacher_id=current_user.id,
                completion_date=date.today(),
                is_completed=True
            )
            db.session.add(completion_record)

    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Topic updated successfully.'})