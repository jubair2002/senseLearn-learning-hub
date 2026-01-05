"""
Chatbot service for generating responses to student queries.
"""
from typing import Optional, List, Dict
from src import db
from src.chatbot.models import ChatConversation, ChatMessage
from src.auth.models import User, Course, CourseStudent, CourseModule, ModuleFile
from datetime import datetime


class ChatbotService:
    """Service class for handling chatbot logic."""
    
    @staticmethod
    def generate_response(user_message: str, student_id: int, conversation_id: Optional[int] = None) -> Dict:
        """
        Generate a response to the user's message.
        
        Args:
            user_message: The message from the student
            student_id: ID of the student
            conversation_id: Optional conversation ID for context
            
        Returns:
            Dictionary with response content and metadata
        """
        user_message_lower = user_message.lower().strip()
        
        # Get conversation history if available
        context_messages = []
        if conversation_id:
            conversation = ChatConversation.query.get(conversation_id)
            if conversation and conversation.student_id == student_id:
                # Get last 5 messages for context
                recent_messages = ChatMessage.query.filter_by(
                    conversation_id=conversation_id
                ).order_by(ChatMessage.created_at.desc()).limit(5).all()
                context_messages = [msg.to_dict() for msg in reversed(recent_messages)]
        
        # Get student's enrolled courses for context
        student = User.query.get(student_id)
        enrolled_courses = []
        if student:
            enrollments = CourseStudent.query.filter_by(
                student_id=student_id,
                status='enrolled'
            ).all()
            enrolled_courses = [enrollment.course for enrollment in enrollments]
        
        # Simple rule-based responses (can be enhanced with AI/ML later)
        response = ChatbotService._generate_rule_based_response(
            user_message_lower,
            student,
            enrolled_courses,
            context_messages
        )
        
        return {
            'content': response['content'],
            'metadata': response.get('metadata', {})
        }
    
    @staticmethod
    def _generate_rule_based_response(
        message: str,
        student: Optional[User],
        enrolled_courses: List[Course],
        context_messages: List[Dict]
    ) -> Dict:
        """Generate response using rule-based logic with enhanced accuracy and context awareness."""
        
        message_lower = message.lower().strip()
        
        # Use context from previous messages for better understanding
        recent_user_messages = [msg for msg in context_messages if msg.get('role') == 'user'][-3:]
        conversation_context = ' '.join([msg.get('content', '').lower() for msg in recent_user_messages])
        
        # Greetings - Use strict matching to avoid false positives (e.g., "aaaa" shouldn't match "hi")
        # Check for exact greeting words or at start of message
        greeting_words = ['hello', 'hi', 'hey', 'greetings']
        greeting_phrases = ['good morning', 'good afternoon', 'good evening']
        
        # Check if message starts with a greeting word (with optional punctuation/whitespace)
        message_starts_with_greeting = any(
            message_lower.startswith(word) or 
            message_lower.startswith(word + ' ') or
            message_lower.startswith(word + '!') or
            message_lower.startswith(word + '?')
            for word in greeting_words
        )
        # Check if message contains a greeting phrase
        message_has_greeting_phrase = any(phrase in message_lower for phrase in greeting_phrases)
        # Check if message is just a greeting word (exact match or with punctuation)
        message_stripped = message_lower.strip().rstrip('!?.,')
        message_is_greeting = message_stripped in greeting_words
        
        is_greeting = message_starts_with_greeting or message_has_greeting_phrase or message_is_greeting
        
        if is_greeting:
            name = student.full_name if student and student.full_name else "there"
            return {
                'content': f"Hello {name}! 👋 I'm your Learning Assistant. I'm here to help you with:\n\n"
                          f"📚 Your courses and learning materials\n"
                          f"📊 Your progress and achievements\n"
                          f"📝 Quizzes and assessments\n"
                          f"❓ Any questions about the platform\n\n"
                          f"How can I assist you today?",
                'metadata': {'type': 'greeting'}
            }
        
        # Help/Support
        help_words = ['help', 'support', 'assist', 'guide', 'how', 'what can you', 'what do you']
        if any(word in message_lower for word in help_words):
            return {
                'content': "I'm here to help! Here's what I can assist you with:\n\n"
                          "📚 **Courses**: Information about your enrolled courses, course details, and how to access materials\n"
                          "📁 **Materials**: Help finding course files, videos, PDFs, and other learning resources\n"
                          "📊 **Progress**: Check your learning progress, completed files, and quiz scores\n"
                          "📝 **Quizzes**: Information about quizzes, how to take them, and view results\n"
                          "🎯 **Navigation**: Help finding features in your dashboard\n"
                          "❓ **General**: Answer questions about how the platform works\n\n"
                          "Just ask me anything! For example:\n"
                          "• \"What courses am I enrolled in?\"\n"
                          "• \"How do I view my progress?\"\n"
                          "• \"Where can I find course materials?\"",
                'metadata': {'type': 'help'}
            }
        
        # Course-related queries - Enhanced
        course_words = ['course', 'courses', 'class', 'classes', 'subject', 'subjects', 'enrolled', 'enrollment']
        if any(word in message_lower for word in course_words):
            if enrolled_courses:
                course_names = [course.name for course in enrolled_courses[:10]]
                courses_list = "\n".join([f"• {name}" for name in course_names])
                if len(enrolled_courses) > 10:
                    courses_list += f"\n• ... and {len(enrolled_courses) - 10} more courses"
                
                return {
                    'content': f"Great! You are currently enrolled in **{len(enrolled_courses)} course(s)**:\n\n{courses_list}\n\n"
                              f"To view a course:\n"
                              f"1. Go to 'My Courses' in your dashboard\n"
                              f"2. Click on any course to see its modules and materials\n"
                              f"3. You can access files, videos, and quizzes from there\n\n"
                              f"Would you like to know more about any specific course?",
                    'metadata': {'type': 'courses_list', 'courses': [c.id for c in enrolled_courses]}
                }
            else:
                return {
                    'content': "You're not currently enrolled in any courses yet.\n\n"
                              "Here's how to get started:\n"
                              "1. Go to 'My Courses' in your dashboard\n"
                              "2. Browse available courses\n"
                              "3. Click 'Request to Join' on courses you're interested in\n"
                              "4. Wait for approval from course tutors\n\n"
                              "Once approved, you'll have access to all course materials!",
                    'metadata': {'type': 'no_courses'}
                }
        
        # Progress-related queries - Enhanced
        progress_words = ['progress', 'completed', 'finished', 'done', 'how much', 'how many', 'percentage', 'score']
        if any(word in message_lower for word in progress_words):
            return {
                'content': "To view your learning progress:\n\n"
                          "📊 **Dashboard Progress Section**:\n"
                          "   • Go to 'Progress' in your dashboard sidebar\n"
                          "   • See overall progress across all courses\n"
                          "   • View progress per course with percentages\n\n"
                          "📁 **File Progress**:\n"
                          "   • Track which files you've viewed\n"
                          "   • See how many files you've completed per module\n\n"
                          "📝 **Quiz Progress**:\n"
                          "   • View your quiz scores and attempts\n"
                          "   • See which quizzes you've completed\n\n"
                          "Would you like specific information about your progress in a particular course?",
                'metadata': {'type': 'progress_info'}
            }
        
        # Quiz-related queries - Enhanced
        quiz_words = ['quiz', 'quizzes', 'test', 'tests', 'exam', 'exams', 'assessment', 'assessments', 'question', 'questions']
        if any(word in message_lower for word in quiz_words):
            return {
                'content': "Here's everything about quizzes:\n\n"
                          "📍 **Finding Quizzes**:\n"
                          "   • Quizzes are located within course modules\n"
                          "   • Go to 'My Courses' → Select a course → Open a module\n"
                          "   • Quizzes appear alongside course materials\n\n"
                          "⏱️ **Taking Quizzes**:\n"
                          "   • Each quiz has a time limit (shown before starting)\n"
                          "   • You have a maximum number of attempts (varies by quiz)\n"
                          "   • Answer all questions and click 'Submit'\n\n"
                          "📊 **Results**:\n"
                          "   • Scores are calculated automatically\n"
                          "   • You'll see your score immediately after submission\n"
                          "   • View past attempts in the course view\n\n"
                          "Need help with a specific quiz?",
                'metadata': {'type': 'quiz_info'}
            }
        
        # Materials/Files queries - Enhanced
        material_words = ['material', 'materials', 'file', 'files', 'document', 'documents', 'video', 'videos', 'pdf', 'download', 'view']
        if any(word in message_lower for word in material_words):
            return {
                'content': "Here's how to access course materials:\n\n"
                          "📁 **Finding Materials**:\n"
                          "   1. Go to 'My Courses' in your dashboard\n"
                          "   2. Click on the course you want\n"
                          "   3. Open a module to see all files\n\n"
                          "📄 **File Types Available**:\n"
                          "   • PDF documents\n"
                          "   • Videos (MP4, WebM, etc.)\n"
                          "   • Presentations (PPT, PPTX)\n"
                          "   • Word documents (DOC, DOCX)\n"
                          "   • Images (JPG, PNG)\n"
                          "   • Text files\n\n"
                          "▶️ **Viewing Files**:\n"
                          "   • Click on any file to view it\n"
                          "   • Videos can be streamed directly\n"
                          "   • PDFs open in the browser\n\n"
                          "Your progress is automatically tracked when you view files!",
                'metadata': {'type': 'materials_info'}
            }
        
        # Dashboard/Navigation queries
        nav_words = ['dashboard', 'navigate', 'where', 'how to', 'how do i', 'menu', 'sidebar']
        if any(word in message_lower for word in nav_words):
            return {
                'content': "Here's your dashboard navigation guide:\n\n"
                          "📋 **Main Sections**:\n"
                          "   • **Dashboard**: Overview and statistics\n"
                          "   • **Profile**: Update your personal information\n"
                          "   • **My Courses**: View and manage your enrolled courses\n"
                          "   • **Tutors**: See tutors assigned to your courses\n"
                          "   • **Sessions**: View scheduled learning sessions\n"
                          "   • **Progress**: Track your learning progress\n"
                          "   • **Settings**: Account settings\n"
                          "   • **Chatbot**: Get help (you're here!)\n\n"
                          "Use the sidebar on the left to navigate between sections.",
                'metadata': {'type': 'navigation'}
            }
        
        # Goodbye
        goodbye_words = ['bye', 'goodbye', 'thanks', 'thank you', 'exit', 'see you', 'later']
        if any(word in message_lower for word in goodbye_words):
            return {
                'content': "You're very welcome! 😊\n\n"
                          "Feel free to come back anytime if you need help. I'm always here to assist you with your learning journey.\n\n"
                          "Good luck with your studies! 🎓✨",
                'metadata': {'type': 'goodbye'}
            }
        
        # Complex question handling - analyze intent and provide contextual help
        # Check for question words and provide intelligent responses
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can i', 'should i', 'do i need']
        is_question = any(message_lower.startswith(word) or f' {word} ' in message_lower for word in question_words)
        
        # Check for specific course mentions
        course_mentioned = False
        if enrolled_courses:
            for course in enrolled_courses:
                if course.name.lower() in message_lower:
                    course_mentioned = True
                    return {
                        'content': f"Great question about **{course.name}**! 📚\n\n"
                                  f"Here's what you can do:\n\n"
                                  f"1. **View Course Details**:\n"
                                  f"   • Go to 'My Courses' in your dashboard\n"
                                  f"   • Click on '{course.name}'\n"
                                  f"   • You'll see all modules, files, and quizzes\n\n"
                                  f"2. **Access Materials**:\n"
                                  f"   • Open any module to view files and videos\n"
                                  f"   • Your progress is tracked automatically\n\n"
                                  f"3. **Take Quizzes**:\n"
                                  f"   • Quizzes are available within course modules\n"
                                  f"   • Check time limits and attempt limits before starting\n\n"
                                  f"Is there something specific about this course you'd like help with?",
                        'metadata': {'type': 'course_specific', 'course_id': course.id}
                    }
        
        # Handle complex multi-part questions
        if is_question and len(message_lower.split()) > 5:
            # Complex question - provide comprehensive help
            return {
                'content': "I understand you have a detailed question. Let me help you! 🤔\n\n"
                          "Based on your question, here's what I can assist with:\n\n"
                          "📚 **Course-Related Questions**:\n"
                          "   • Course enrollment and access\n"
                          "   • Finding specific course materials\n"
                          "   • Understanding course structure\n"
                          "   • Course progress and completion\n\n"
                          "📝 **Quiz and Assessment Questions**:\n"
                          "   • How to take quizzes\n"
                          "   • Understanding quiz results\n"
                          "   • Quiz retake policies\n"
                          "   • Time limits and scoring\n\n"
                          "📊 **Progress and Tracking**:\n"
                          "   • Viewing your learning progress\n"
                          "   • Understanding completion percentages\n"
                          "   • Tracking file views\n\n"
                          "💡 **Tips**:\n"
                          "   • Be specific about what you need (e.g., \"How do I find videos in my course?\")\n"
                          "   • Mention the course name if asking about a specific course\n"
                          "   • Ask step-by-step if you need detailed instructions\n\n"
                          "Could you rephrase your question more specifically? I'm here to help!",
                'metadata': {'type': 'complex_question'}
            }
        
        # Handle follow-up questions using context
        if context_messages and len(context_messages) > 2:
            last_assistant = next((msg for msg in reversed(context_messages) if msg.get('role') == 'assistant'), None)
            if last_assistant:
                last_response = last_assistant.get('content', '').lower()
                # If user is asking about something mentioned in previous response
                if any(word in message_lower for word in ['more', 'tell me more', 'explain', 'details', 'elaborate']):
                    return {
                        'content': "I'd be happy to provide more details! 📖\n\n"
                                  "Could you be more specific about what you'd like to know more about?\n\n"
                                  "For example:\n"
                                  "• \"Tell me more about how to access course materials\"\n"
                                  "• \"Explain how quiz scoring works\"\n"
                                  "• \"More details about tracking my progress\"\n\n"
                                  "The more specific your question, the better I can help you!",
                        'metadata': {'type': 'follow_up'}
                    }
        
        # Default response - More helpful with suggestions
        return {
            'content': "I'm here to help! I can assist you with:\n\n"
                      "📚 **Courses**: Information about your enrolled courses\n"
                      "📁 **Materials**: Finding and accessing course files\n"
                      "📊 **Progress**: Checking your learning progress\n"
                      "📝 **Quizzes**: Information about quizzes and assessments\n"
                      "🗺️ **Navigation**: Help using the dashboard\n\n"
                      "**Try asking me specific questions like:**\n"
                      "• \"What courses am I enrolled in?\"\n"
                      "• \"How do I view my progress?\"\n"
                      "• \"Where can I find course materials?\"\n"
                      "• \"How do I take a quiz?\"\n"
                      "• \"What files are in [course name]?\"\n"
                      "• \"How do I track my learning progress?\"\n\n"
                      "Feel free to ask me anything about your learning journey! I'm here to help. 😊",
            'metadata': {'type': 'default'}
        }
    
    @staticmethod
    def create_conversation(student_id: int, first_message: str) -> ChatConversation:
        """Create a new conversation."""
        # Generate title from first message (first 50 chars)
        title = first_message[:50] + "..." if len(first_message) > 50 else first_message
        
        conversation = ChatConversation(
            student_id=student_id,
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(conversation)
        db.session.flush()  # Get the ID
        
        return conversation
    
    @staticmethod
    def add_message(conversation_id: int, role: str, content: str, metadata: Optional[str] = None) -> ChatMessage:
        """Add a message to a conversation."""
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.utcnow(),
            message_metadata=metadata
        )
        db.session.add(message)
        
        # Update conversation's updated_at timestamp and ensure it's not archived
        conversation = ChatConversation.query.get(conversation_id)
        if conversation:
            conversation.updated_at = datetime.utcnow()
            # Ensure conversation is not archived when new message is added
            if conversation.is_archived:
                conversation.is_archived = False
        
        return message
    
    @staticmethod
    def get_conversations(student_id: int, include_archived: bool = False) -> List[ChatConversation]:
        """Get all conversations for a student."""
        query = ChatConversation.query.filter_by(student_id=student_id)
        if not include_archived:
            # Use explicit == False to ensure archived conversations are excluded
            query = query.filter(ChatConversation.is_archived == False)
        # Order by updated_at descending to show most recent first
        return query.order_by(ChatConversation.updated_at.desc()).all()
    
    @staticmethod
    def get_conversation_messages(conversation_id: int, student_id: int) -> List[ChatMessage]:
        """Get all messages for a conversation, verifying student ownership."""
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation or conversation.student_id != student_id:
            return []
        
        return ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(ChatMessage.created_at.asc()).all()
    
    @staticmethod
    def archive_conversation(conversation_id: int, student_id: int) -> bool:
        """Archive a conversation."""
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation or conversation.student_id != student_id:
            return False
        
        conversation.is_archived = True
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    @staticmethod
    def delete_conversation(conversation_id: int, student_id: int) -> bool:
        """Delete a conversation."""
        conversation = ChatConversation.query.get(conversation_id)
        if not conversation or conversation.student_id != student_id:
            return False
        
        db.session.delete(conversation)
        db.session.commit()
        return True

