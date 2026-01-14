# seed_data.py
from run import app, db
from app.models import User, Class, Section, Group, Subject, Chapter, Topic, teacher_assignments
from werkzeug.security import generate_password_hash

with app.app_context():
    print("Resetting database...")
    db.drop_all()
    db.create_all()
    print("Database reset.")

    # --- Create Users ---
    print("Creating users...")
    admin = User(username='admin', email='admin@ccn.edu', full_name='Admin User', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)

    teacher = User(username='teacher1', email='teacher1@ccn.edu', full_name='Ahmed Khan', role='teacher')
    teacher.set_password('teacher123')
    db.session.add(teacher)

    principal = User(username='principal', email='principal@ccn.edu', full_name='Principal Niazi', role='principal')
    principal.set_password('principal123')
    db.session.add(principal)
    db.session.commit()
    print("Users created.")

    # --- Create Classes, Sections, Groups ---
    print("Creating academic structure...")
    class7 = Class(name='Class 7')
    class8 = Class(name='Class 8')
    class9 = Class(name='Class 9')
    class10 = Class(name='Class 10')
    class11 = Class(name='Class 11')
    class12 = Class(name='Class 12')
    db.session.add_all([class7, class8, class9, class10, class11, class12])
    db.session.commit()

    # Sections for Class 7-10
    for cls in [class7, class8, class9, class10]:
        sec_a = Section(name='A', class_id=cls.id)
        sec_b = Section(name='B', class_id=cls.id)
        db.session.add_all([sec_a, sec_b])
    
    # Groups for Class 11-12
    for cls in [class11, class12]:
        grp_med = Group(name='Medical', class_id=cls.id)
        grp_eng = Group(name='Engineering', class_id=cls.id)
        grp_ics = Group(name='ICS', class_id=cls.id)
        db.session.add_all([grp_med, grp_eng, grp_ics])
    
    db.session.commit()
    print("Academic structure created.")

    # --- Create Subjects ---
    print("Creating subjects...")
    subjects_data = {
        class7: ['English', 'Urdu', 'Science', 'Islamiyat', 'Maths', 'Computer', 'Social Studies'],
        class8: ['English', 'Urdu', 'Science', 'Islamiyat', 'Maths', 'Computer', 'Social Studies'],
        class9: ['English', 'Urdu', 'Physics', 'Biology', 'Chemistry', 'Maths', 'Islamiyat', 'Pakistan Studies'],
        class10: ['English', 'Urdu', 'Physics', 'Biology', 'Chemistry', 'Maths', 'Islamiyat', 'Pakistan Studies'],
        class11: {
            'Medical': ['English', 'Urdu', 'Biology', 'Islamiyat', 'Chemistry', 'Physics'],
            'Engineering': ['English', 'Urdu', 'Islamiyat', 'Physics', 'Maths', 'Chemistry'],
            'ICS': ['English', 'Urdu', 'Islamiyat', 'Maths', 'Computer', 'Physics']
        },
        class12: {
            'Medical': ['English', 'Urdu', 'Biology', 'Pakistan Studies', 'Chemistry', 'Physics'],
            'Engineering': ['English', 'Urdu', 'Pakistan Studies', 'Physics', 'Maths', 'Chemistry'],
            'ICS': ['English', 'Urdu', 'Pakistan Studies', 'Maths', 'Computer', 'Physics'] # Assuming similar to Class 11
        }
    }
    
    for cls, subjects_list in subjects_data.items():
        if isinstance(subjects_list, dict): # For classes with groups
            for group_name, subs in subjects_list.items():
                for sub_name in subs:
                    subject = Subject(name=sub_name, class_id=cls.id)
                    db.session.add(subject)
        else: # For classes with only sections
            for sub_name in subjects_list:
                subject = Subject(name=sub_name, class_id=cls.id)
                db.session.add(subject)
    db.session.commit()
    print("Subjects created.")

    # --- Create a sample syllabus ---
    print("Creating sample syllabus...")
    subject = Subject.query.filter_by(name='English', class_id=class7.id).first()
    if subject:
        ch1 = Chapter(name='Grammar Basics', subject_id=subject.id)
        ch2 = Chapter(name='Short Stories', subject_id=subject.id)
        db.session.add_all([ch1, ch2])
        db.session.commit()

        t1 = Topic(name='Nouns and Pronouns', chapter_id=ch1.id)
        t2 = Topic(name='Verbs and Tenses', chapter_id=ch1.id)
        t3 = Topic(name='The Little Prince', chapter_id=ch2.id)
        db.session.add_all([t1, t2, t3])
        db.session.commit()
    print("Sample syllabus created.")

    # --- Assign Teacher ---
    print("Assigning teacher...")
    english_subject_class7 = Subject.query.filter_by(name='English', class_id=class7.id).first()
    if english_subject_class7:
        stmt = teacher_assignments.insert().values(
            teacher_id=teacher.id,
            class_id=class7.id,
            section_id=Section.query.filter_by(name='A', class_id=class7.id).first().id,
            subject_id=english_subject_class7.id
        )
        db.session.execute(stmt)
        db.session.commit()
    print("Teacher assigned.")


    print("\nDatabase seeding complete!")
    print("--- Login Credentials ---")
    print("Admin:   username: admin,   password: admin123")
    print("Teacher: username: teacher1, password: teacher123")
    print("Principal: username: principal, password: principal123")
    print("-------------------------\n")
