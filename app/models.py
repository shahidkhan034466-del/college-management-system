from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'teacher', 'principal'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sections = db.relationship('Section', backref='class_obj', lazy=True, cascade="all, delete-orphan")
    groups = db.relationship('Group', backref='class_obj', lazy=True, cascade="all, delete-orphan")
    subjects = db.relationship('Subject', backref='class_obj', lazy=True, cascade="all, delete-orphan")

class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)

# Association table for Teacher Assignments
teacher_assignments = db.Table('teacher_assignments',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
    db.Column('class_id', db.Integer, db.ForeignKey('classes.id'), nullable=False),
    db.Column('section_id', db.Integer, db.ForeignKey('sections.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id'), nullable=False),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")

class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    topics = db.relationship('Topic', backref='chapter', lazy=True, cascade="all, delete-orphan")

class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    completion = db.relationship('TopicCompletion', uselist=False, backref='topic', cascade="all, delete-orphan")

class TopicCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    completion_date = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)

class EmailReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    principal_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_date = db.Column(db.Date, nullable=False)
    report_data = db.Column(db.Text, nullable=False) # JSON string
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_data(self, data):
        self.report_data = json.dumps(data)

    def get_data(self):
        return json.loads(self.report_data)