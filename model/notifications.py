from datetime import datetime
from __init__ import db

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    links = db.relationship('MessageLink', backref='message', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='message', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at,
            'links': [link.to_dict() for link in self.links]
        }


class MessageLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    url = db.Column(db.String(255))
    label = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'label': self.label
        }


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    is_dismissed = db.Column(db.Boolean, default=False)
    dismissed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message_id': self.message_id,
            'is_read': self.is_read,
            'is_dismissed': self.is_dismissed,
            'read_at': self.read_at,
            'dismissed_at': self.dismissed_at,
            'created_at': self.created_at
        }