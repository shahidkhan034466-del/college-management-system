from app.models import Topic, TopicCompletion, Chapter, Subject, db
from sqlalchemy import func

def calculate_progress(entity_id, entity_type):
    if entity_type == 'subject':
        total_topics = db.session.query(func.count(Topic.id)).join(Chapter).filter(Chapter.subject_id == entity_id).scalar()
        completed_topics = db.session.query(func.count(TopicCompletion.id)).join(Topic).join(Chapter).filter(
            Chapter.subject_id == entity_id, TopicCompletion.is_completed == True
        ).scalar()
    elif entity_type == 'chapter':
        total_topics = Topic.query.filter_by(chapter_id=entity_id).count()
        completed_topics = TopicCompletion.query.join(Topic).filter(
            Topic.chapter_id == entity_id, TopicCompletion.is_completed == True
        ).count()
    else:
        return 0

    if total_topics == 0:
        return 0
    
    return round((completed_topics / total_topics) * 100)

def role_required(role):
    def decorator(f):
        from functools import wraps
        from flask_login import current_user
        from flask import abort

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                abort(403) # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator