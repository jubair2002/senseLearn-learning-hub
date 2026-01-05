/**
 * Chatbot JavaScript for student interface
 */

class Chatbot {
    constructor() {
        this.currentConversationId = null;
        this.showArchived = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadConversations();
    }

    setupEventListeners() {
        // Message form submission
        const messageForm = document.getElementById('message-form');
        if (messageForm) {
            messageForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }

        // File upload - show file info but don't upload immediately
        const fileUpload = document.getElementById('file-upload');
        if (fileUpload) {
            fileUpload.addEventListener('change', (e) => {
                if (e.target.files && e.target.files.length > 0) {
                    this.showFileSelected(e.target.files[0]);
                }
            });
        }

        // Cancel upload
        const cancelUpload = document.getElementById('cancel-upload');
        if (cancelUpload) {
            cancelUpload.addEventListener('click', () => {
                this.cancelFileUpload();
            });
        }

        // New conversation button
        const newConversationBtn = document.getElementById('new-conversation-btn');
        if (newConversationBtn) {
            newConversationBtn.addEventListener('click', () => {
                this.startNewConversation();
            });
        }

        // Filter buttons
        const showActiveBtn = document.getElementById('show-active-btn');
        const showArchivedBtn = document.getElementById('show-archived-btn');
        
        if (showActiveBtn) {
            showActiveBtn.addEventListener('click', () => {
                this.showArchived = false;
                this.updateFilterButtons();
                this.loadConversations();
            });
        }

        if (showArchivedBtn) {
            showArchivedBtn.addEventListener('click', () => {
                this.showArchived = true;
                this.updateFilterButtons();
                this.loadConversations();
            });
        }

        // Enter key to send (Shift+Enter for new line)
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }

    updateFilterButtons() {
        const showActiveBtn = document.getElementById('show-active-btn');
        const showArchivedBtn = document.getElementById('show-archived-btn');
        
        if (this.showArchived) {
            showActiveBtn.classList.remove('bg-emerald-100', 'text-emerald-700', 'font-medium');
            showActiveBtn.classList.add('text-slate-600', 'hover:bg-slate-100');
            showArchivedBtn.classList.add('bg-emerald-100', 'text-emerald-700', 'font-medium');
            showArchivedBtn.classList.remove('text-slate-600', 'hover:bg-slate-100');
        } else {
            showActiveBtn.classList.add('bg-emerald-100', 'text-emerald-700', 'font-medium');
            showActiveBtn.classList.remove('text-slate-600', 'hover:bg-slate-100');
            showArchivedBtn.classList.remove('bg-emerald-100', 'text-emerald-700', 'font-medium');
            showArchivedBtn.classList.add('text-slate-600', 'hover:bg-slate-100');
        }
    }

    async loadConversations() {
        try {
            // Force fresh data by adding timestamp to prevent caching
            const timestamp = new Date().getTime();
            const response = await fetch(`/student/chatbot/api/conversations?include_archived=${this.showArchived}&_t=${timestamp}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            if (data.success) {
                // Filter out archived conversations if showing active
                let conversations = data.conversations || [];
                if (!this.showArchived) {
                    conversations = conversations.filter(conv => !conv.is_archived);
                }
                this.renderConversations(conversations);
            } else {
                console.error('Failed to load conversations:', data.error);
                this.showError('Failed to load conversations: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.showError('Error loading conversations. Please refresh the page.');
        }
    }
    
    showError(message) {
        const messagesContainer = document.getElementById('messages-container');
        if (messagesContainer) {
            const errorHtml = `
                <div class="flex justify-center chat-message">
                    <div class="max-w-2xl w-full">
                        <div class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                            <p class="text-red-800 text-sm">
                                <i class="fas fa-exclamation-circle mr-2"></i>${this.escapeHtml(message)}
                            </p>
                        </div>
                    </div>
                </div>
            `;
            messagesContainer.insertAdjacentHTML('beforeend', errorHtml);
            this.scrollToBottom();
        }
    }

    renderConversations(conversations) {
        const conversationsList = document.getElementById('conversations-list');
        if (!conversationsList) return;

        if (conversations.length === 0) {
            conversationsList.innerHTML = `
                <div class="text-center py-8 text-slate-500">
                    <i class="fas fa-comments text-3xl mb-2"></i>
                    <p>No ${this.showArchived ? 'archived' : ''} conversations yet</p>
                </div>
            `;
            return;
        }

        conversationsList.innerHTML = conversations.map(conv => {
            const isArchived = conv.is_archived || false;
            return `
            <div class="conversation-item p-3 rounded-lg cursor-pointer hover:bg-slate-100 transition mb-2 ${
                this.currentConversationId === conv.id ? 'bg-emerald-50 border border-emerald-200' : ''
            }" data-conversation-id="${conv.id}">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                        <h3 class="font-medium text-slate-800 truncate">${this.escapeHtml(conv.title || 'New Conversation')}</h3>
                        <p class="text-xs text-slate-500 mt-1">${this.formatDate(conv.updated_at)}</p>
                    </div>
                    <div class="flex gap-1 ml-2">
                        ${!this.showArchived && !isArchived ? `
                            <button class="archive-btn p-1 text-slate-400 hover:text-slate-600" data-conv-id="${conv.id}" title="Archive">
                                <i class="fas fa-archive text-xs"></i>
                            </button>
                        ` : ''}
                        <button class="delete-btn p-1 text-slate-400 hover:text-red-600" data-conv-id="${conv.id}" title="Delete">
                            <i class="fas fa-trash text-xs"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        }).join('');

        // Add click handlers
        conversationsList.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.archive-btn') || e.target.closest('.delete-btn')) {
                    return; // Don't load conversation if clicking action buttons
                }
                const convId = parseInt(item.dataset.conversationId);
                this.loadConversation(convId);
            });
        });

        // Archive button handlers
        conversationsList.querySelectorAll('.archive-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const convId = parseInt(btn.dataset.convId);
                await this.archiveConversation(convId);
            });
        });

        // Delete button handlers
        conversationsList.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const convId = parseInt(btn.dataset.convId);
                if (confirm('Are you sure you want to delete this conversation?')) {
                    await this.deleteConversation(convId);
                }
            });
        });
    }

    async loadConversation(conversationId) {
        this.currentConversationId = conversationId;
        this.renderConversations(await this.getConversationsList());

        try {
            const response = await fetch(`/student/chatbot/api/conversations/${conversationId}/messages`);
            const data = await response.json();

            if (data.success) {
                this.renderMessages(data.messages);
                this.hideWelcomeMessage();
            } else {
                console.error('Failed to load messages:', data.error);
                alert('Failed to load conversation');
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
            alert('Error loading conversation');
        }
    }

    renderMessages(messages) {
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) return;

        this.hideWelcomeMessage();

        messagesContainer.innerHTML = messages.map(msg => this.renderMessage(msg)).join('');
        this.scrollToBottom();
    }

    renderMessage(message) {
        const isUser = message.role === 'user';
        const alignment = isUser ? 'justify-end' : 'justify-start';
        const bgColor = isUser ? 'bg-emerald-600 text-white' : 'bg-white border border-slate-200 text-slate-800';
        const icon = isUser ? 'fa-user' : 'fa-robot';

        // Parse metadata if available
        let metadata = null;
        if (message.metadata) {
            try {
                metadata = typeof message.metadata === 'string' ? JSON.parse(message.metadata) : message.metadata;
            } catch (e) {
                console.warn('Failed to parse message metadata:', e);
            }
        }

        // Check if this is a document processing message
        const hasAudio = metadata && metadata.type === 'document_processed' && metadata.has_audio;
        const documentId = metadata && metadata.document_id;

        // Convert markdown-style formatting to HTML (simple conversion)
        let content = this.escapeHtml(message.content);
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        content = content.replace(/\n/g, '<br>');

        let audioPlayer = '';
        if (hasAudio && documentId) {
            audioPlayer = `
                <div class="mt-3 pt-3 border-t border-slate-200">
                    <audio id="audio-${documentId}" controls class="w-full">
                        <source src="/student/chatbot/api/documents/${documentId}/audio" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                </div>
            `;
        }

        return `
            <div class="flex ${alignment} chat-message">
                <div class="max-w-2xl ${isUser ? 'order-2' : 'order-1'}">
                    <div class="flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}">
                        <div class="w-8 h-8 rounded-full ${isUser ? 'bg-emerald-600' : 'bg-slate-200'} flex items-center justify-center flex-shrink-0">
                            <i class="fas ${icon} text-sm ${isUser ? 'text-white' : 'text-slate-600'}"></i>
                        </div>
                        <div class="flex-1">
                            <div class="${bgColor} rounded-lg px-4 py-3 shadow-sm">
                                <div class="whitespace-pre-wrap">${content}</div>
                                ${audioPlayer}
                            </div>
                            <p class="text-xs text-slate-500 mt-1 ${isUser ? 'text-right' : 'text-left'}">
                                ${this.formatDateTime(message.created_at)}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const fileUpload = document.getElementById('file-upload');
        
        if (!messageInput) {
            console.error('Message input not found');
            return;
        }

        const message = messageInput.value.trim();
        
        // Check if there's a file selected but not yet uploaded
        const selectedFile = fileUpload && fileUpload.files && fileUpload.files.length > 0 ? fileUpload.files[0] : null;
        
        // If file is selected, upload it first (or along with message)
        if (selectedFile) {
            // Upload file first, then send message if there is one
            await this.handleFileUpload(selectedFile);
            // Clear file input after upload
            if (fileUpload) {
                fileUpload.value = '';
            }
        }
        
        // If no message and no file, return
        if (!message && !selectedFile) {
            return;
        }

        // If there's a message, send it
        if (message) {
            // Disable input while sending
            messageInput.disabled = true;
            sendBtn.disabled = true;

            let success = false;
            try {
                if (!this.currentConversationId) {
                    // Create new conversation
                    await this.createConversation(message);
                } else {
                    // Send message to existing conversation
                    await this.sendMessageToConversation(message);
                }
                success = true;
            } catch (error) {
                console.error('Error sending message:', error);
                this.showError('Failed to send message. Please try again.');
            } finally {
                // Always re-enable input and button
                messageInput.disabled = false;
                sendBtn.disabled = false;
                
                // Only clear input if message was sent successfully
                if (success) {
                    messageInput.value = '';
                    messageInput.focus();
                    await this.loadConversations(); // Refresh conversations list to update timestamps
                }
            }
        } else {
            // Just uploaded file, refresh conversations
            await this.loadConversations();
        }
    }

    async createConversation(firstMessage) {
        try {
            const response = await fetch('/student/chatbot/api/conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    first_message: firstMessage
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.currentConversationId = data.conversation.id;
                this.renderMessages(data.messages);
                this.hideWelcomeMessage();
                // Reload conversations to update timestamps - use small delay to ensure DB is updated
                setTimeout(() => this.loadConversations(), 100);
            } else {
                throw new Error(data.error || 'Failed to create conversation');
            }
        } catch (error) {
            console.error('Error creating conversation:', error);
            this.showError('Failed to create conversation: ' + error.message);
            throw error;
        }
    }

    async sendMessageToConversation(message) {
        // Show user message immediately
        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: message,
            created_at: new Date().toISOString()
        };
        this.appendMessage(userMessage);

        // Show typing indicator
        const typingId = this.showTypingIndicator();

        try {
            const response = await fetch(`/student/chatbot/api/conversations/${this.currentConversationId}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Remove typing indicator
            this.hideTypingIndicator(typingId);

            if (data.success) {
                // Append assistant response
                if (data.messages && data.messages.length > 0) {
                    const assistantMessage = data.messages.find(m => m.role === 'assistant');
                    if (assistantMessage) {
                        this.appendMessage(assistantMessage);
                        // Reload conversations to update timestamps - use small delay to ensure DB is updated
                        setTimeout(() => this.loadConversations(), 100);
                    } else {
                        throw new Error('No assistant response received');
                    }
                } else {
                    throw new Error('Empty response from server');
                }
            } else {
                throw new Error(data.error || 'Failed to send message');
            }
        } catch (error) {
            this.hideTypingIndicator(typingId);
            console.error('Error sending message:', error);
            this.showError('Failed to send message: ' + error.message);
            throw error;
        }
    }

    appendMessage(message) {
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) return;

        this.hideWelcomeMessage();
        const messageHtml = this.renderMessage(message);
        messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) return null;

        this.hideWelcomeMessage();
        const typingId = `typing-${Date.now()}`;
        const typingHtml = `
            <div class="flex justify-start chat-message" id="${typingId}">
                <div class="max-w-2xl">
                    <div class="flex items-start gap-3">
                        <div class="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0">
                            <i class="fas fa-robot text-sm text-slate-600"></i>
                        </div>
                        <div class="flex-1">
                            <div class="bg-white border border-slate-200 rounded-lg px-4 py-3 shadow-sm">
                                <div class="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', typingHtml);
        this.scrollToBottom();
        return typingId;
    }

    hideTypingIndicator(typingId) {
        if (!typingId) return;
        const typingElement = document.getElementById(typingId);
        if (typingElement) {
            typingElement.remove();
        }
    }

    hideWelcomeMessage() {
        const welcomeMessage = document.getElementById('welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
    }

    startNewConversation() {
        this.currentConversationId = null;
        const messagesContainer = document.getElementById('messages-container');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
            const welcomeMessage = document.getElementById('welcome-message');
            if (welcomeMessage) {
                welcomeMessage.style.display = 'block';
            }
        }
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.focus();
        }
    }

    async archiveConversation(conversationId) {
        try {
            const response = await fetch(`/student/chatbot/api/conversations/${conversationId}/archive`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                if (this.currentConversationId === conversationId) {
                    this.startNewConversation();
                }
                await this.loadConversations();
            } else {
                alert('Failed to archive conversation: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error archiving conversation:', error);
            alert('Error archiving conversation');
        }
    }

    async deleteConversation(conversationId) {
        try {
            const response = await fetch(`/student/chatbot/api/conversations/${conversationId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                if (this.currentConversationId === conversationId) {
                    this.startNewConversation();
                }
                await this.loadConversations();
            } else {
                alert('Failed to delete conversation: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error deleting conversation:', error);
            alert('Error deleting conversation');
        }
    }

    async getConversationsList() {
        try {
            const response = await fetch(`/student/chatbot/api/conversations?include_archived=${this.showArchived}`);
            const data = await response.json();
            return data.success ? data.conversations : [];
        } catch (error) {
            console.error('Error loading conversations:', error);
            return [];
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('messages-container');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        if (!dateString) return 'Just now';
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
        
        return date.toLocaleDateString();
    }

    formatDateTime(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    async handleFileUpload(file) {
        // Validate file type
        const allowedExtensions = ['pdf', 'docx', 'doc', 'txt'];
        const fileExt = file.name.split('.').pop().toLowerCase();
        
        if (!allowedExtensions.includes(fileExt)) {
            this.showError('Unsupported file type. Please upload PDF, DOCX, DOC, or TXT files.');
            this.cancelFileUpload();
            return;
        }

        // Show upload info with uploading status
        const uploadInfo = document.getElementById('upload-info');
        const uploadFilename = document.getElementById('upload-filename');
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        
        if (uploadInfo && uploadFilename) {
            uploadInfo.classList.remove('hidden');
            uploadFilename.textContent = `Uploading: ${file.name}`;
        }
        
        // Disable inputs during upload
        if (messageInput) {
            messageInput.disabled = true;
        }
        if (sendBtn) {
            sendBtn.disabled = true;
        }

        // Create FormData
        const formData = new FormData();
        formData.append('file', file);
        if (this.currentConversationId) {
            formData.append('conversation_id', this.currentConversationId);
        }

        try {
            const response = await fetch('/student/chatbot/api/documents/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // Hide upload info
                if (uploadInfo) {
                    uploadInfo.classList.add('hidden');
                }

                // Re-enable inputs
                if (messageInput) {
                    messageInput.disabled = false;
                    messageInput.focus();
                }
                if (sendBtn) {
                    sendBtn.disabled = false;
                }

                // If there's an assistant message, display it
                if (data.assistant_message) {
                    const assistantMessage = {
                        id: Date.now(),
                        role: 'assistant',
                        content: data.assistant_message,
                        created_at: new Date().toISOString(),
                        metadata: JSON.stringify({
                            type: 'document_processed',
                            document_id: data.document.id,
                            has_audio: data.has_audio
                        })
                    };
                    this.appendMessage(assistantMessage);
                    
                    // If audio is available, load it
                    if (data.has_audio) {
                        // Audio player will be rendered in the message
                        setTimeout(() => {
                            const audioElement = document.getElementById(`audio-${data.document.id}`);
                            if (audioElement) {
                                audioElement.src = `/student/chatbot/api/documents/${data.document.id}/audio`;
                            }
                        }, 100);
                    }
                }

                // Reload conversations to update timestamps
                await this.loadConversations();
            } else {
                throw new Error(data.error || 'Failed to upload document');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            this.showError('Failed to upload document: ' + error.message);
            
            // Hide upload info on error
            const uploadInfo = document.getElementById('upload-info');
            if (uploadInfo) {
                uploadInfo.classList.add('hidden');
            }
            
            // Re-enable inputs on error
            const messageInput = document.getElementById('message-input');
            const sendBtn = document.getElementById('send-btn');
            if (messageInput) {
                messageInput.disabled = false;
            }
            if (sendBtn) {
                sendBtn.disabled = false;
            }
        }
    }

    showFileSelected(file) {
        // Show upload info but don't upload yet
        const uploadInfo = document.getElementById('upload-info');
        const uploadFilename = document.getElementById('upload-filename');
        if (uploadInfo && uploadFilename) {
            uploadInfo.classList.remove('hidden');
            uploadFilename.textContent = `Selected: ${file.name}`;
        }
        
        // Enable message input and send button (they should already be enabled, but just in case)
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        if (messageInput) {
            messageInput.disabled = false;
            messageInput.focus();
        }
        if (sendBtn) {
            sendBtn.disabled = false;
        }
    }

    cancelFileUpload() {
        const fileUpload = document.getElementById('file-upload');
        const uploadInfo = document.getElementById('upload-info');
        
        if (fileUpload) {
            fileUpload.value = '';
        }
        if (uploadInfo) {
            uploadInfo.classList.add('hidden');
        }
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('Initializing chatbot...');
        const chatbot = new Chatbot();
        console.log('Chatbot initialized successfully');
    } catch (error) {
        console.error('Error initializing chatbot:', error);
        alert('Error loading chatbot. Please refresh the page.');
    }
});

