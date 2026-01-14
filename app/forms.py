from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('teacher', 'Teacher'), ('principal', 'Principal')], validators=[DataRequired()])
    submit = SubmitField('Save User')

    def __init__(self, original_username, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class ClassForm(FlaskForm):
    name = SelectField('Class Name', choices=[('Class 7', 'Class 7'), ('Class 8', 'Class 8'), ('Class 9', 'Class 9'), ('Class 10', 'Class 10'), ('Class 11', 'Class 11'), ('Class 12', 'Class 12')], validators=[DataRequired()])
    submit = SubmitField('Save Class')

class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired()])
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Subject')

class ChapterForm(FlaskForm):
    name = StringField('Chapter Name', validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Chapter')

class TopicForm(FlaskForm):
    name = StringField('Topic Name', validators=[DataRequired()])
    chapter_id = SelectField('Chapter', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Topic')

def coerce_int_or_none(value):
    """Coerce value to int or None if empty/None"""
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

class AssignmentForm(FlaskForm):
    teacher_id = SelectField('Teacher', coerce=int, validators=[DataRequired()])
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    section_id = SelectField('Section', coerce=coerce_int_or_none)
    group_id = SelectField('Group', coerce=coerce_int_or_none)
    submit = SubmitField('Assign Teacher')