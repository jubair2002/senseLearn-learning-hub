"""
Routes for the chatbot system.
"""
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from src import db
from src.chatbot import chatbot_bp
from src.chatbot.service import ChatbotService
from src.chatbot.models import ChatConversation, ChatMessage, ChatbotDocument
from src.chatbot.document_processor import DocumentProcessor
from src.chatbot.tts_service import TTSService
from src.config import config
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
from uuid import uuid4


@chatbot_bp.route('/')
@login_required
def chatbot_page():
    """Main chatbot page for students."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        from flask import flash, redirect, url_for
        flash('This page is only for students.', 'error')
        return redirect(url_for('student.dashboard'))
    
    return render_template('student/chatbot.html', user=current_user)


@chatbot_bp.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    """Get all conversations for the current student."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        conversations = ChatbotService.get_conversations(
            current_user.id,
            include_archived=include_archived
        )
        
        conversations_data = [conv.to_dict() for conv in conversations]
        
        return jsonify({
            'success': True,
            'conversations': conversations_data
        }), 200
    except Exception as e:
        from flask import current_app
        current_app.logger.exception("Error getting conversations")
        return jsonify({'success': False, 'error': 'Failed to load conversations'}), 500


@chatbot_bp.route('/api/conversations', methods=['POST'])
@login_required
def create_conversation():
    """Create a new conversation."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json() or {}
        first_message = data.get('first_message', '').strip()
        
        if not first_message:
            return jsonify({'success': False, 'error': 'First message is required'}), 400
        
        # Create conversation
        conversation = ChatbotService.create_conversation(current_user.id, first_message)
        
        # Add user message
        user_message = ChatbotService.add_message(
            conversation.id,
            'user',
            first_message
        )
        
        # Generate response
        response_data = ChatbotService.generate_response(
            first_message,
            current_user.id,
            conversation.id
        )
        
        # Add assistant response
        assistant_message = ChatbotService.add_message(
            conversation.id,
            'assistant',
            response_data['content'],
            json.dumps(response_data.get('metadata', {})) if response_data.get('metadata') else None
        )
        
        # Ensure conversation is not archived and updated_at is current
        conversation.updated_at = datetime.utcnow()
        if conversation.is_archived:
            conversation.is_archived = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation': conversation.to_dict(),
            'messages': [
                user_message.to_dict(),
                assistant_message.to_dict()
            ]
        }), 201
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception("Error creating conversation")
        return jsonify({'success': False, 'error': 'Failed to create conversation'}), 500


@chatbot_bp.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
@login_required
def get_messages(conversation_id):
    """Get all messages for a conversation."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        messages = ChatbotService.get_conversation_messages(conversation_id, current_user.id)
        
        if messages is None:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        messages_data = [msg.to_dict() for msg in messages]
        
        return jsonify({
            'success': True,
            'messages': messages_data
        }), 200
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error getting messages for conversation {conversation_id}")
        return jsonify({'success': False, 'error': 'Failed to load messages'}), 500


@chatbot_bp.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
@login_required
def send_message(conversation_id):
    """Send a message in an existing conversation."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json() or {}
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return jsonify({'success': False, 'error': 'Message content is required'}), 400
        
        # Verify conversation exists and belongs to student
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation or conversation.student_id != current_user.id:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        # Add user message
        user_message = ChatbotService.add_message(
            conversation_id,
            'user',
            message_content
        )
        
        # Generate response
        response_data = ChatbotService.generate_response(
            message_content,
            current_user.id,
            conversation_id
        )
        
        # Add assistant response
        assistant_message = ChatbotService.add_message(
            conversation_id,
            'assistant',
            response_data['content'],
            json.dumps(response_data.get('metadata', {})) if response_data.get('metadata') else None
        )
        
        # Ensure conversation is not archived and updated_at is current
        conversation.updated_at = datetime.utcnow()
        if conversation.is_archived:
            conversation.is_archived = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'messages': [
                user_message.to_dict(),
                assistant_message.to_dict()
            ]
        }), 201
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception(f"Error sending message to conversation {conversation_id}")
        return jsonify({'success': False, 'error': 'Failed to send message'}), 500


@chatbot_bp.route('/api/conversations/<int:conversation_id>/archive', methods=['POST'])
@login_required
def archive_conversation(conversation_id):
    """Archive a conversation."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        success = ChatbotService.archive_conversation(conversation_id, current_user.id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Conversation archived'
        }), 200
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error archiving conversation {conversation_id}")
        return jsonify({'success': False, 'error': 'Failed to archive conversation'}), 500


@chatbot_bp.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """Delete a conversation."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        success = ChatbotService.delete_conversation(conversation_id, current_user.id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Conversation deleted'
        }), 200
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error deleting conversation {conversation_id}")
        return jsonify({'success': False, 'error': 'Failed to delete conversation'}), 500


@chatbot_bp.route('/api/documents/upload', methods=['POST'])
@login_required
def upload_document():
    """Upload a document for text-to-speech processing."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        conversation_id = request.form.get('conversation_id', type=int)  # Optional
        
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type (only allow text-extractable formats)
        allowed_extensions = {'pdf', 'docx', 'doc', 'txt'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False, 
                'error': f'Unsupported file type. Allowed: {", ".join(allowed_extensions)}'
            }), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > config.MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': 'File too large'}), 400
        
        # Generate unique filename
        unique_id = str(uuid4())[:8]
        secure_name = secure_filename(file.filename.rsplit('.', 1)[0])
        unique_filename = f"chatbot_{current_user.id}_{secure_name}_{unique_id}.{file_ext}"
        
        # Create upload directory structure: uploads/chatbot/students/{student_id}/
        upload_base = config.UPLOAD_DIR
        student_dir = os.path.join(upload_base, "chatbot", "students", str(current_user.id))
        os.makedirs(student_dir, exist_ok=True)
        
        full_path = os.path.join(student_dir, unique_filename)
        relative_path = os.path.join("chatbot", "students", str(current_user.id), unique_filename).replace("\\", "/")
        
        # Save file
        file.save(full_path)
        mime_type = file.content_type or 'application/octet-stream'
        
        # Extract text from document
        extracted_text = None
        extraction_error = None
        try:
            extracted_text = DocumentProcessor.extract_text(full_path, file_ext)
            if not extracted_text:
                extraction_error = "No text could be extracted from the document. The file may be image-based (scanned PDF), encrypted, or corrupted."
        except Exception as e:
            from flask import current_app
            current_app.logger.exception(f"Exception during text extraction: {str(e)}")
            extraction_error = f"Error extracting text: {str(e)}"
        
        # Create document record
        document = ChatbotDocument(
            conversation_id=conversation_id,
            student_id=current_user.id,
            original_filename=file.filename,
            file_path=relative_path,
            file_type=file_ext,
            file_size=file_size,
            extracted_text=extracted_text,
            uploaded_at=datetime.utcnow()
        )
        db.session.add(document)
        db.session.flush()  # Get the ID
        
        # Generate audio if text was extracted
        audio_path = None
        message_content = None
        if extracted_text:
            # Limit text length for TTS (e.g., first 5000 characters to avoid very long audio)
            text_for_audio = extracted_text[:5000] if len(extracted_text) > 5000 else extracted_text
            if len(extracted_text) > 5000:
                text_for_audio += "\n\n[Note: Document was truncated for audio generation. Full text is available in the chat.]"
            
            # Create audio directory
            audio_dir = os.path.join(upload_base, "chatbot", "audio", str(current_user.id))
            os.makedirs(audio_dir, exist_ok=True)
            
            audio_filename = f"audio_{document.id}.mp3"
            audio_full_path = os.path.join(audio_dir, audio_filename)
            audio_relative_path = os.path.join("chatbot", "audio", str(current_user.id), audio_filename).replace("\\", "/")
            
            # Generate audio
            try:
                audio_generated = TTSService.text_to_speech(text_for_audio, audio_full_path)
                if audio_generated:
                    document.audio_path = audio_relative_path
                    db.session.flush()
                    from flask import current_app
                    current_app.logger.info(f"Audio generated successfully for document {document.id}: {audio_relative_path}")
                else:
                    from flask import current_app
                    current_app.logger.warning(f"Audio generation failed for document {document.id}")
            except Exception as e:
                from flask import current_app
                current_app.logger.exception(f"Exception during audio generation: {str(e)}")
            
            # Truncate text for display (show first 500 chars)
            preview_text = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
            message_content = f"📄 I've processed your document **{file.filename}**!\n\n"
            message_content += f"**Extracted Text Preview:**\n{preview_text}\n\n"
            
            if document.audio_path:
                message_content += "🔊 **Audio Available!** Click the play button below to listen to the document.\n\n"
            else:
                message_content += "⚠️ Audio generation is not available. The text has been extracted and is ready for reading.\n\n"
            
            message_content += f"**Full text length:** {len(extracted_text)} characters"
            
            # Add message to conversation if conversation_id provided
            if conversation_id:
                assistant_message = ChatbotService.add_message(
                    conversation_id,
                    'assistant',
                    message_content,
                    json.dumps({
                        'type': 'document_processed',
                        'document_id': document.id,
                        'has_audio': document.audio_path is not None
                    })
                )
                # Update conversation timestamp
                conversation = ChatConversation.query.get(conversation_id)
                if conversation:
                    conversation.updated_at = datetime.utcnow()
                    if conversation.is_archived:
                        conversation.is_archived = False
                db.session.commit()
            else:
                db.session.commit()
        else:
            db.session.commit()
            # Provide more helpful error message
            if extraction_error:
                message_content = f"⚠️ I couldn't extract text from **{file.filename}**.\n\n**Reason:** {extraction_error}\n\n**Suggestions:**\n"
                if file_ext == 'pdf':
                    message_content += "- If this is a scanned PDF (image-based), you may need OCR software to extract text.\n"
                    message_content += "- If the PDF is encrypted, please provide an unencrypted version.\n"
                    message_content += "- Try converting the PDF to a text file or DOCX format.\n"
                else:
                    message_content += "- The file may be corrupted or in an unsupported format.\n"
                    message_content += "- Try saving the file in a different format (PDF, DOCX, or TXT).\n"
            else:
                message_content = f"⚠️ I couldn't extract text from **{file.filename}**. The file may be corrupted or in an unsupported format."
        
        return jsonify({
            'success': True,
            'message': 'Document uploaded and processed successfully',
            'document': document.to_dict(),
            'extracted_text_length': len(extracted_text) if extracted_text else 0,
            'has_audio': document.audio_path is not None,
            'audio_url': TTSService.get_audio_url(document.audio_path) if document.audio_path else None,
            'assistant_message': message_content
        }), 201
        
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception("Error uploading document")
        return jsonify({'success': False, 'error': f'Failed to process document: {str(e)}'}), 500


@chatbot_bp.route('/api/documents/<int:document_id>/audio', methods=['GET'])
@login_required
def serve_audio_file(document_id):
    """Serve audio file directly."""
    from flask import send_from_directory, abort
    
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        abort(403)
    
    try:
        document = ChatbotDocument.query.get(document_id)
        if not document or document.student_id != current_user.id:
            abort(404)
        
        if not document.audio_path:
            abort(404)
        
        # Get full path to audio file
        audio_full_path = os.path.join(config.UPLOAD_DIR, document.audio_path)
        
        if not os.path.exists(audio_full_path):
            abort(404)
        
        # Extract directory and filename
        audio_dir = os.path.dirname(audio_full_path)
        audio_filename = os.path.basename(audio_full_path)
        
        return send_from_directory(audio_dir, audio_filename, mimetype='audio/mpeg')
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error serving audio for document {document_id}")
        abort(500)

