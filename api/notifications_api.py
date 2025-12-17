from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from __init__ import db
from model.notifications import Message, Notification, MessageLink
from model.user import User

# Flask Blueprint for notification system routes.

notifications_api = Blueprint('notifications', __name__, url_prefix='/api')

# POST /messages - Create new message and generate notifications for all users
@notifications_api.route('/messages', methods=['POST'])
def create_message():
    try:
        data = request.get_json()
        if not data or not data.get('title') or not data.get('content'):
            return jsonify({'error': 'title and content are required'}), 400
        
        message = Message(title=data['title'], content=data['content'])
        db.session.add(message)
        db.session.flush()
        
        # Add links if provided
        if 'links' in data:
            for link in data['links']:
                msg_link = MessageLink(message_id=message.id, url=link.get('url'), label=link.get('label'))
                db.session.add(msg_link)
        
        db.session.commit()
        
        # Generate notifications for all users
        users = User.query.all()
        for user in users:
            notification = Notification(user_id=user.id, message_id=message.id)
            db.session.add(notification)
        db.session.commit()
        
        return jsonify({'message_id': message.id, 'title': message.title}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# PUT /messages/<id> - Edit existing message
@notifications_api.route('/messages/<int:msg_id>', methods=['PUT'])
def update_message(msg_id):
    try:
        message = Message.query.get(msg_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        data = request.get_json()
        if 'title' in data:
            message.title = data['title']
        if 'content' in data:
            message.content = data['content']
        
        if 'links' in data:
            MessageLink.query.filter_by(message_id=msg_id).delete()
            for link in data['links']:
                msg_link = MessageLink(message_id=msg_id, url=link.get('url'), label=link.get('label'))
                db.session.add(msg_link)
        
        db.session.commit()
        return jsonify({'message': 'Message updated'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# DELETE /messages/<id> - Delete message (cascade delete links and notifications)
@notifications_api.route('/messages/<int:msg_id>', methods=['DELETE'])
def delete_message(msg_id):
    try:
        message = Message.query.get(msg_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        Notification.query.filter_by(message_id=msg_id).delete()
        MessageLink.query.filter_by(message_id=msg_id).delete()
        db.session.delete(message)
        db.session.commit()
        return jsonify({'message': 'Message deleted'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# GET /notifications/<user_id> - Get all notifications for user
@notifications_api.route('/notifications/<int:user_id>', methods=['GET'])
def get_user_notifications(user_id):
    try:
        notifications = Notification.query.filter_by(user_id=user_id).all()
        if not notifications:
            return jsonify([]), 200
        
        result = []
        for notif in notifications:
            message = Message.query.get(notif.message_id)
            links = MessageLink.query.filter_by(message_id=notif.message_id).all()
            result.append({
                'notification_id': notif.id,
                'message_id': notif.message_id,
                'title': message.title,
                'content': message.content,
                'links': [{'url': link.url, 'label': link.label} for link in links],
                'is_read': notif.is_read,
                'is_dismissed': notif.is_dismissed,
                'read_at': notif.read_at,
                'dismissed_at': notif.dismissed_at
            })
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

# POST /notifications/<id>/read - Mark notification as read
@notifications_api.route('/notifications/<int:notif_id>/read', methods=['POST'])
def mark_as_read(notif_id):
    try:
        notification = Notification.query.get(notif_id)
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Notification marked as read'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# POST /notifications/<id>/dismiss - Mark notification as dismissed
@notifications_api.route('/notifications/<int:notif_id>/dismiss', methods=['POST'])
def mark_as_dismissed(notif_id):
    try:
        notification = Notification.query.get(notif_id)
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        notification.is_dismissed = True
        notification.dismissed_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Notification marked as dismissed'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# GET /notifications - Admin reporting route
@notifications_api.route('/notifications', methods=['GET'])
def get_message_report():
    try:
        message_id = request.args.get('message_id')
        if not message_id:
            return jsonify({'error': 'message_id parameter required'}), 400
        
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        notifications = Notification.query.filter_by(message_id=message_id).all()
        result = [{
            'user_id': n.user_id,
            'is_read': n.is_read,
            'is_dismissed': n.is_dismissed,
            'read_at': n.read_at,
            'dismissed_at': n.dismissed_at
        } for n in notifications]
        
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500