"""
Database models for the chatbot system.
"""
from datetime import datetime
from flask_login import current_user
from src import db


class ChatConversation(db.Model):
    """Model for storing chatbot conversations."""
    __tablename__ = "chat_conversations"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=True)  # Auto-generated from first message
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Relationships
    student = db.relationship("User", foreign_keys=[student_id], backref="chat_conversations")
    messages = db.relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    
    __table_args__ = (
        db.Index('ix_chat_conversations_student_updated', 'student_id', 'updated_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatConversation {self.id} for student {self.student_id}>"
    
    def to_dict(self):
        """Convert conversation to dictionary."""
        return {
            'id': self.id,
            'title': self.title or 'New Conversation',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_archived': self.is_archived,
            'message_count': len(self.messages)
        }


class ChatMessage(db.Model):
    """Model for storing individual chat messages."""
    __tablename__ = "chat_messages"
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("chat_conversations.id", ondelete='CASCADE'), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, index=True)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Optional: Store metadata about the response (e.g., sources, confidence)
    message_metadata = db.Column(db.Text, nullable=True)  # JSON string for additional data
    
    # Relationships
    conversation = db.relationship("ChatConversation", back_populates="messages")
    
    __table_args__ = (
        db.Index('ix_chat_messages_conversation_created', 'conversation_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatMessage {self.id} ({self.role}) in conversation {self.conversation_id}>"
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.message_metadata
        }


class ChatbotDocument(db.Model):
    """Model for storing documents uploaded to chatbot for text-to-speech."""
    __tablename__ = "chatbot_documents"
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("chat_conversations.id", ondelete='CASCADE'), nullable=True, index=True)  # Optional - can be uploaded without conversation
    student_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)  # Path to uploaded document
    file_type = db.Column(db.String(50), nullable=False)  # pdf, docx, txt, etc.
    file_size = db.Column(db.Integer, nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)  # Extracted text from document
    audio_path = db.Column(db.String(500), nullable=True)  # Path to generated audio file
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    conversation = db.relationship("ChatConversation", backref="documents")
    student = db.relationship("User", foreign_keys=[student_id], backref="chatbot_documents")
    
    __table_args__ = (
        db.Index('ix_chatbot_documents_student_uploaded', 'student_id', 'uploaded_at'),
        db.Index('ix_chatbot_documents_conversation', 'conversation_id'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatbotDocument {self.original_filename} for student {self.student_id}>"
    
    def to_dict(self):
        """Convert document to dictionary."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'has_text': self.extracted_text is not None,
            'has_audio': self.audio_path is not None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }

