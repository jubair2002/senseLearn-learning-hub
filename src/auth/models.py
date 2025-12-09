from datetime import datetime, timedelta
from flask_login import UserMixin

from src import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # --- User Type (Student/Tutor) ---
    user_type = db.Column(db.String(20), nullable=False, default="student")  # 'student' or 'tutor'
    
    # --- Common Fields for Both ---
    full_name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    
    # --- Student Specific Fields ---
    disability_type = db.Column(db.String(50), nullable=True)  # Only for students
    
    # --- Tutor Specific Fields ---
    qualifications = db.Column(db.Text, nullable=True)  # Tutor's qualifications
    experience_years = db.Column(db.Integer, nullable=True)  # Years of experience
    subjects = db.Column(db.String(255), nullable=True)  # Subjects tutor can teach
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)  # Hourly rate
    bio = db.Column(db.Text, nullable=True)  # Short bio/description
    is_verified = db.Column(db.Boolean, default=False)  # Tutor verification status
    
    # --- Email Verification ---
    email_verified = db.Column(db.Boolean, default=False)  # Email verification status

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email} ({self.user_type})>"

    def is_student(self) -> bool:
        return self.user_type == "student"
    
    def is_tutor(self) -> bool:
        return self.user_type == "tutor"
    
    def is_admin(self) -> bool:
        return self.user_type == "admin"


class PasswordResetCode(db.Model):
    __tablename__ = "password_reset_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    code = db.Column(db.String(20), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="reset_codes")

    @classmethod
    def create_for_user(cls, user: User, code: str, minutes_valid: int = 15) -> "PasswordResetCode":
        expires = datetime.utcnow() + timedelta(minutes=minutes_valid)
        return cls(user=user, code=code, expires_at=expires)


class EmailVerificationOTP(db.Model):
    __tablename__ = "email_verification_otps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)  # Nullable for pending registrations, indexed for faster queries
    email = db.Column(db.String(255), nullable=True, index=True)  # For pending registrations before user exists
    otp = db.Column(db.String(20), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)  # Indexed for expiration cleanup queries
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Indexed for ordering queries
    purpose = db.Column(db.String(50), nullable=False, default="verification", index=True)  # Indexed for filtering by purpose

    user = db.relationship("User", backref="verification_otps")
    
    # Add composite index for common query patterns (email + purpose, user_id + purpose)
    __table_args__ = (
        db.Index('ix_email_purpose', 'email', 'purpose'),
        db.Index('ix_user_purpose', 'user_id', 'purpose'),
        db.Index('ix_email_otp', 'email', 'otp', 'purpose'),
    )

    @classmethod
    def create_for_user(cls, user: User, otp: str, minutes_valid: int = 10, purpose: str = "verification") -> "EmailVerificationOTP":
        expires = datetime.utcnow() + timedelta(minutes=minutes_valid)
        return cls(user=user, otp=otp, expires_at=expires, purpose=purpose)
    
    @classmethod
    def create_for_email(cls, email: str, otp: str, minutes_valid: int = 10, purpose: str = "verification") -> "EmailVerificationOTP":
        expires = datetime.utcnow() + timedelta(minutes=minutes_valid)
        return cls(email=email, otp=otp, expires_at=expires, purpose=purpose)


class PendingRegistration(db.Model):
    """Temporary storage for registration data before email verification."""
    __tablename__ = "pending_registrations"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    
    # Registration data stored as JSON
    registration_data = db.Column(db.Text, nullable=False)  # JSON string with all registration fields
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def create(cls, email: str, registration_data: dict, minutes_valid: int = 30) -> "PendingRegistration":
        import json
        expires = datetime.utcnow() + timedelta(minutes=minutes_valid)
        return cls(
            email=email,
            registration_data=json.dumps(registration_data),
            expires_at=expires
        )
    
    def get_registration_data(self) -> dict:
        import json
        return json.loads(self.registration_data)


class TutorDocument(db.Model):
    """Model for storing tutor verification documents (certificates, etc.)."""
    __tablename__ = "tutor_documents"
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)  # Original filename
    file_path = db.Column(db.String(500), nullable=False)  # Path relative to uploads directory (unique constraint via migration index)
    file_type = db.Column(db.String(50), nullable=False, index=True)  # e.g., 'certificate', 'recommendation', 'vendor_cert'
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type = db.Column(db.String(100), nullable=True)  # MIME type (e.g., 'application/pdf')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    uploaded_by_admin = db.Column(db.Boolean, default=False)  # True if uploaded by admin during account creation
    
    # Relationship
    tutor = db.relationship("User", backref="documents")
    
    # Composite index for common query pattern: tutor_id + uploaded_at (for sorting)
    __table_args__ = (
        db.Index('ix_tutor_documents_tutor_uploaded', 'tutor_id', 'uploaded_at'),
    )
    
    def __repr__(self) -> str:
        return f"<TutorDocument {self.file_name} for tutor {self.tutor_id}>"


# Association table for Course-Tutor many-to-many relationship (must be defined before Course model)
course_tutors = db.Table(
    'course_tutors',
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True, index=True),
    db.Column('tutor_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, index=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow, nullable=False),
    db.Column('assigned_by', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),  # Admin who assigned
    db.Index('ix_course_tutors_course_tutor', 'course_id', 'tutor_id'),
)


class Course(db.Model):
    """Model for courses created by admin."""
    __tablename__ = "courses"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    target_disability_types = db.Column(db.String(255), nullable=True)  # Comma-separated list: "Deaf,Mute" or "All"
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='SET NULL'), nullable=False, index=True)  # Admin who created it
    
    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_courses")
    tutors = db.relationship(
        "User", 
        secondary=course_tutors, 
        primaryjoin="Course.id == course_tutors.c.course_id",
        secondaryjoin="User.id == course_tutors.c.tutor_id",
        backref="assigned_courses"
    )
    
    def __repr__(self) -> str:
        return f"<Course {self.name}>"


class CourseStudent(db.Model):
    """Model for student enrollment in courses."""
    __tablename__ = "course_students"
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete='CASCADE'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="enrolled", index=True)  # enrolled, pending, rejected
    assigned_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='SET NULL'), nullable=False)  # Admin or tutor who assigned
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    course = db.relationship("Course", backref="enrollments")
    student = db.relationship("User", foreign_keys=[student_id], backref="course_enrollments")
    assigner = db.relationship("User", foreign_keys=[assigned_by])
    
    __table_args__ = (
        db.UniqueConstraint('course_id', 'student_id', name='uq_course_student'),
        db.Index('ix_course_students_course_status', 'course_id', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<CourseStudent course={self.course_id} student={self.student_id} status={self.status}>"


class CourseRequest(db.Model):
    """Model for student requests to join courses."""
    __tablename__ = "course_requests"
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete='CASCADE'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)  # Tutor who will review
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)  # pending, accepted, rejected
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    course = db.relationship("Course", backref="requests")
    student = db.relationship("User", foreign_keys=[student_id], backref="course_requests")
    tutor = db.relationship("User", foreign_keys=[tutor_id], backref="received_requests")
    
    __table_args__ = (
        db.Index('ix_course_requests_tutor_status', 'tutor_id', 'status'),
        db.Index('ix_course_requests_course_student', 'course_id', 'student_id'),
    )
    
    def __repr__(self) -> str:
        return f"<CourseRequest course={self.course_id} student={self.student_id} tutor={self.tutor_id} status={self.status}>"


class CourseModule(db.Model):
    """Model for course modules/lessons."""
    __tablename__ = "course_modules"
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order_index = db.Column(db.Integer, nullable=False, default=0, index=True)  # For ordering modules
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='SET NULL'), nullable=False)  # Tutor who created it
    
    # Relationships
    course = db.relationship("Course", backref="modules")
    creator = db.relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        db.Index('ix_course_modules_course_order', 'course_id', 'order_index'),
    )
    
    def __repr__(self) -> str:
        return f"<CourseModule {self.name} (course={self.course_id})>"


class ModuleFile(db.Model):
    """Model for files within course modules."""
    __tablename__ = "module_files"
    
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey("course_modules.id", ondelete='CASCADE'), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)  # Original filename
    file_path = db.Column(db.String(500), nullable=False)  # Path relative to uploads directory (unique constraint via migration index)
    file_type = db.Column(db.String(50), nullable=False, index=True)  # pdf, pptx, doc, docx, jpg, png, etc.
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type = db.Column(db.String(100), nullable=True)  # MIME type
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='SET NULL'), nullable=False)  # Tutor who uploaded
    
    # Relationships
    module = db.relationship("CourseModule", backref="files")
    uploader = db.relationship("User", foreign_keys=[uploaded_by])
    
    __table_args__ = (
        db.Index('ix_module_files_module_uploaded', 'module_id', 'uploaded_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ModuleFile {self.file_name} (module={self.module_id})>"