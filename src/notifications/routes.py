"""Notification routes for all user types."""
from flask import jsonify, request
from flask_login import login_required, current_user
from src.notifications.service import NotificationService
from src.auth.models import Notification
from src import db


def register_notification_routes(app, admin_bp, tutor_bp, student_bp):
    """Register notification routes for all user types."""
    
    # Common route for getting notifications
    @app.route('/api/notifications', methods=['GET'])
    @login_required
    def get_notifications():
        """Get all notifications for the current user."""
        from flask import current_app
        current_app.logger.info(f"Notification API called by user {current_user.id}")
        """Get all notifications for the current user."""
        try:
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'
            limit = request.args.get('limit', type=int)
            
            query = Notification.query.filter_by(user_id=current_user.id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            query = query.order_by(Notification.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            notifications = query.all()
            
            notifications_data = [{
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat() if n.created_at else None,
                'link': n.link
            } for n in notifications]
            
            unread_count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()
            
            return jsonify({
                'success': True,
                'notifications': notifications_data,
                'unread_count': unread_count
            }), 200
            
        except Exception as e:
            from flask import current_app
            current_app.logger.exception("Error getting notifications")
            return jsonify({'success': False, 'error': 'Failed to get notifications'}), 500
    
    # Mark notification as read
    @app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
    @login_required
    def mark_notification_read(notification_id):
        """Mark a notification as read."""
        try:
            notification = Notification.query.get(notification_id)
            
            if not notification:
                return jsonify({'success': False, 'error': 'Notification not found'}), 404
            
            if notification.user_id != current_user.id:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            
            notification.mark_as_read()
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Notification marked as read'}), 200
            
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.exception("Error marking notification as read")
            return jsonify({'success': False, 'error': 'Failed to mark notification as read'}), 500
    
    # Mark all notifications as read
    @app.route('/api/notifications/read-all', methods=['POST'])
    @login_required
    def mark_all_notifications_read():
        """Mark all notifications as read for the current user."""
        try:
            notifications = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).all()
            
            for notification in notifications:
                notification.mark_as_read()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Marked {len(notifications)} notifications as read'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.exception("Error marking all notifications as read")
            return jsonify({'success': False, 'error': 'Failed to mark all notifications as read'}), 500
    
    # Delete notification
    @app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
    @login_required
    def delete_notification(notification_id):
        """Delete a notification."""
        try:
            notification = Notification.query.get(notification_id)
            
            if not notification:
                return jsonify({'success': False, 'error': 'Notification not found'}), 404
            
            if notification.user_id != current_user.id:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            
            db.session.delete(notification)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Notification deleted'}), 200
            
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.exception("Error deleting notification")
            return jsonify({'success': False, 'error': 'Failed to delete notification'}), 500

