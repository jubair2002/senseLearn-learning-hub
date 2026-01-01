"""Notification service for creating and managing notifications."""
from datetime import datetime
from src import db
from src.auth.models import Notification, User


class NotificationService:
    """Service class for managing notifications."""
    
    @staticmethod
    def create_notification(user_id: int, title: str, message: str, 
                           notification_type: str = 'info', link: str = None) -> Notification:
        """
        Create a new notification for a user.
        
        Args:
            user_id: ID of the user to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification ('info', 'success', 'warning', 'error')
            link: Optional link to related page
            
        Returns:
            Created Notification object
        """
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def notify_tutor_verified(tutor_id: int):
        """Notify tutor that their account has been verified."""
        tutor = User.query.get(tutor_id)
        if tutor and tutor.user_type == 'tutor':
            NotificationService.create_notification(
                user_id=tutor_id,
                title="Account Verified",
                message="Your tutor account has been verified by an administrator. You can now access all features.",
                notification_type='success',
                link='/tutor/dashboard'
            )
    
    @staticmethod
    def notify_tutor_registered(tutor_email: str):
        """Notify admin that a new tutor has registered."""
        # Find admin users
        admins = User.query.filter_by(user_type='admin').all()
        for admin in admins:
            NotificationService.create_notification(
                user_id=admin.id,
                title="New Tutor Registration",
                message=f"A new tutor ({tutor_email}) has registered and is pending verification.",
                notification_type='info',
                link='/admin/dashboard'
            )
    
    @staticmethod
    def notify_student_enrolled(student_id: int, course_name: str, tutor_id: int = None):
        """Notify student that they've been enrolled in a course."""
        NotificationService.create_notification(
            user_id=student_id,
            title="Course Enrollment",
            message=f"You have been enrolled in the course: {course_name}",
            notification_type='success',
            link='/student/dashboard'
        )
        
        # Also notify tutor if provided
        if tutor_id:
            NotificationService.create_notification(
                user_id=tutor_id,
                title="New Student Enrollment",
                message=f"A new student has been enrolled in your course: {course_name}",
                notification_type='info',
                link='/tutor/dashboard'
            )
    
    @staticmethod
    def notify_course_request(student_id: int, course_name: str, tutor_id: int):
        """Notify tutor that a student has requested to join a course."""
        NotificationService.create_notification(
            user_id=tutor_id,
            title="Course Enrollment Request",
            message=f"A student has requested to join your course: {course_name}",
            notification_type='info',
            link='/tutor/dashboard'
        )
    
    @staticmethod
    def notify_course_request_approved(student_id: int, course_name: str):
        """Notify student that their course request has been approved."""
        NotificationService.create_notification(
            user_id=student_id,
            title="Course Request Approved",
            message=f"Your request to join {course_name} has been approved.",
            notification_type='success',
            link='/student/dashboard'
        )
    
    @staticmethod
    def notify_course_request_rejected(student_id: int, course_name: str):
        """Notify student that their course request has been rejected."""
        NotificationService.create_notification(
            user_id=student_id,
            title="Course Request Rejected",
            message=f"Your request to join {course_name} has been rejected.",
            notification_type='warning',
            link='/student/dashboard'
        )

