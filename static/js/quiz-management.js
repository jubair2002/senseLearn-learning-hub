// Quiz Management JavaScript
// Handles all quiz-related UI interactions and API calls

let currentCourseId = null;
let currentModuleId = null;
let currentQuizId = null;
let quizzes = [];
let currentQuiz = null;

// Initialize quiz management for a course
function initQuizManagement(courseId, moduleId = null) {
    currentCourseId = courseId;
    currentModuleId = moduleId;
    loadQuizzes();
}

// Load all quizzes for the current course
async function loadQuizzes() {
    if (!currentCourseId) return;
    
    const listEl = document.getElementById('quizzes-list');
    if (!listEl) return;
    
    listEl.innerHTML = '<div class="text-center py-12 text-slate-400"><i class="fas fa-spinner fa-spin text-4xl mb-4"></i><p>Loading quizzes...</p></div>';
    
    try {
        const response = await fetch(`/quiz/api/courses/${currentCourseId}/quizzes`);
        const data = await response.json();
        
        if (data.success) {
            quizzes = data.quizzes || [];
            renderQuizzes(quizzes);
        } else {
            listEl.innerHTML = `<div class="text-center py-12 text-red-600"><p>Error: ${data.error || 'Failed to load quizzes'}</p></div>`;
        }
    } catch (error) {
        console.error('Error loading quizzes:', error);
        listEl.innerHTML = `<div class="text-center py-12 text-red-600"><p>Error loading quizzes. Please try again.</p></div>`;
    }
}

// Render quizzes list
function renderQuizzes(quizzesList) {
    const listEl = document.getElementById('quizzes-list');
    if (!listEl) return;
    
    if (quizzesList.length === 0) {
        listEl.innerHTML = `
            <div class="text-center py-12 text-slate-400">
                <i class="fas fa-clipboard-list text-6xl mb-4"></i>
                <p class="text-lg">No quizzes yet</p>
                <p class="text-sm mt-2">Create your first quiz to get started</p>
            </div>
        `;
        return;
    }
    
    listEl.innerHTML = quizzesList.map(quiz => `
        <div class="quiz-card">
            <div class="quiz-card-header">
                <div class="flex-1">
                    <h4 class="quiz-card-title">${escapeHtml(quiz.title)}</h4>
                    ${quiz.description ? `<p class="text-sm text-slate-600 mt-1">${escapeHtml(quiz.description)}</p>` : ''}
                    <div class="quiz-card-meta">
                        <span><i class="fas fa-question-circle mr-1"></i>${quiz.question_count || 0} questions</span>
                        <span><i class="fas fa-star mr-1"></i>${quiz.total_points || 0} points</span>
                        ${quiz.module_name ? `<span><i class="fas fa-folder mr-1"></i>${escapeHtml(quiz.module_name)}</span>` : ''}
                        <span class="badge ${quiz.is_active ? 'badge-active' : 'badge-inactive'}">
                            ${quiz.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                </div>
                <div class="quiz-card-actions">
                    <button onclick="viewQuiz(${quiz.id})" class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                        <i class="fas fa-eye mr-1"></i>View
                    </button>
                    <button onclick="deleteQuiz(${quiz.id})" class="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700">
                        <i class="fas fa-trash mr-1"></i>Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Show create quiz modal
function showCreateQuizModal() {
    const modal = document.getElementById('create-quiz-modal');
    if (!modal) return;
    
    document.getElementById('quiz-course-id').value = currentCourseId;
    document.getElementById('quiz-module-id').value = currentModuleId || '';
    document.getElementById('create-quiz-form').reset();
    modal.classList.remove('hidden');
}

// Close create quiz modal
function closeCreateQuizModal() {
    const modal = document.getElementById('create-quiz-modal');
    if (modal) modal.classList.add('hidden');
}

// Handle create quiz form submission
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('create-quiz-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = {
                title: document.getElementById('quiz-title').value.trim(),
                description: document.getElementById('quiz-description').value.trim() || null,
                instructions: document.getElementById('quiz-instructions').value.trim() || null,
                time_limit_minutes: document.getElementById('quiz-time-limit').value ? parseInt(document.getElementById('quiz-time-limit').value) : null,
                passing_score: parseFloat(document.getElementById('quiz-passing-score').value) || 60.0,
                max_attempts: parseInt(document.getElementById('quiz-max-attempts').value) || 1,
            };
            
            const moduleId = document.getElementById('quiz-module-id').value;
            if (moduleId) {
                formData.module_id = parseInt(moduleId);
            }
            
            try {
                const response = await fetch(`/quiz/api/courses/${currentCourseId}/quizzes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    closeCreateQuizModal();
                    loadQuizzes();
                    showNotification('Quiz created successfully!', 'success');
                } else {
                    showNotification(data.error || 'Failed to create quiz', 'error');
                }
            } catch (error) {
                console.error('Error creating quiz:', error);
                showNotification('Error creating quiz. Please try again.', 'error');
            }
        });
    }
});

// View quiz details
async function viewQuiz(quizId) {
    currentQuizId = quizId;
    
    try {
        const response = await fetch(`/quiz/api/quizzes/${quizId}`);
        const data = await response.json();
        
        if (data.success) {
            currentQuiz = data.quiz;
            showQuizDetailsModal(data.quiz);
        } else {
            showNotification(data.error || 'Failed to load quiz', 'error');
        }
    } catch (error) {
        console.error('Error loading quiz:', error);
        showNotification('Error loading quiz. Please try again.', 'error');
    }
}

// Show quiz details modal
function showQuizDetailsModal(quiz) {
    const modal = document.getElementById('quiz-details-modal');
    if (!modal) return;
    
    document.getElementById('quiz-details-title').textContent = quiz.title;
    document.getElementById('quiz-info-title').textContent = quiz.title;
    document.getElementById('quiz-info-description').textContent = quiz.description || 'No description';
    document.getElementById('quiz-info-time').textContent = quiz.time_limit_minutes ? `${quiz.time_limit_minutes} min` : 'No limit';
    document.getElementById('quiz-info-passing').textContent = quiz.passing_score ? `${quiz.passing_score}%` : 'N/A';
    document.getElementById('quiz-info-attempts').textContent = quiz.max_attempts || 'Unlimited';
    
    document.getElementById('quiz-stats-questions').textContent = quiz.question_count || 0;
    document.getElementById('quiz-stats-points').textContent = quiz.total_points || 0;
    
    // Store quiz ID for edit form
    document.getElementById('edit-quiz-id').value = quiz.id;
    document.getElementById('edit-quiz-title').value = quiz.title;
    document.getElementById('edit-quiz-description').value = quiz.description || '';
    document.getElementById('edit-quiz-passing').value = quiz.passing_score || 60;
    
    renderQuestions(quiz.questions || []);
    loadQuizAttempts(quiz.id);
    
    modal.classList.remove('hidden');
}

// Close quiz details modal
function closeQuizDetailsModal() {
    const modal = document.getElementById('quiz-details-modal');
    if (modal) modal.classList.add('hidden');
    currentQuizId = null;
    currentQuiz = null;
}

// Render questions list
function renderQuestions(questions) {
    const listEl = document.getElementById('questions-list');
    if (!listEl) return;
    
    if (questions.length === 0) {
        listEl.innerHTML = `
            <div class="text-center py-8 text-slate-400">
                <i class="fas fa-question-circle text-4xl mb-2"></i>
                <p class="text-sm">No questions yet. Add your first question!</p>
            </div>
        `;
        return;
    }
    
    listEl.innerHTML = questions.map((q, index) => `
        <div class="question-item">
            <div class="question-header">
                <div class="flex-1">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="question-type-badge question-type-${q.question_type}">
                            ${q.question_type.replace('_', ' ').toUpperCase()}
                        </span>
                        <span class="text-sm text-slate-500">${q.points} points</span>
                    </div>
                    <p class="question-text">${escapeHtml(q.question_text)}</p>
                    ${q.question_type === 'multiple_choice' && q.options ? `
                        <div class="mt-3 space-y-1">
                            ${q.options.map(opt => `
                                <div class="option-item ${opt.is_correct ? 'correct' : ''}">
                                    <i class="fas fa-${opt.is_correct ? 'check-circle text-green-600' : 'circle text-slate-400'}"></i>
                                    <span class="${opt.is_correct ? 'font-semibold text-green-700' : 'text-slate-700'}">${escapeHtml(opt.option_text)}</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    ${q.question_type !== 'multiple_choice' ? `
                        <div class="mt-2 text-sm">
                            <span class="text-slate-500">Correct Answer:</span>
                            <span class="ml-2 font-medium text-green-700">${escapeHtml(q.correct_answer || 'N/A')}</span>
                        </div>
                    ` : ''}
                </div>
                <div class="flex gap-2">
                    <button onclick="deleteQuestion(${q.id})" class="px-2 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Show add question modal
function showAddQuestionModal() {
    const modal = document.getElementById('add-question-modal');
    if (!modal) return;
    
    document.getElementById('question-quiz-id').value = currentQuizId;
    document.getElementById('add-question-form').reset();
    document.getElementById('multiple-choice-section').classList.add('hidden');
    document.getElementById('answer-section').classList.add('hidden');
    document.getElementById('options-container').innerHTML = '';
    
    modal.classList.remove('hidden');
}

// Close add question modal
function closeAddQuestionModal() {
    const modal = document.getElementById('add-question-modal');
    if (modal) modal.classList.add('hidden');
}

// Handle question type change
function handleQuestionTypeChange() {
    const type = document.getElementById('question-type').value;
    const mcSection = document.getElementById('multiple-choice-section');
    const answerSection = document.getElementById('answer-section');
    
    mcSection.classList.add('hidden');
    answerSection.classList.add('hidden');
    
    if (type === 'multiple_choice') {
        mcSection.classList.remove('hidden');
        if (document.getElementById('options-container').children.length === 0) {
            addOption();
            addOption();
        }
    } else if (type === 'short_answer' || type === 'true_false') {
        answerSection.classList.remove('hidden');
        if (type === 'true_false') {
            document.getElementById('correct-answer').placeholder = 'Enter "true" or "false"';
        } else {
            document.getElementById('correct-answer').placeholder = 'Enter the correct answer';
        }
    }
}

// Add option for multiple choice
function addOption() {
    const container = document.getElementById('options-container');
    const optionCount = container.children.length;
    
    const optionDiv = document.createElement('div');
    optionDiv.className = 'option-input-group';
    optionDiv.innerHTML = `
        <input type="text" class="option-input" placeholder="Option ${optionCount + 1}" required>
        <label class="flex items-center gap-2">
            <input type="radio" name="correct_option" value="${optionCount}" class="option-checkbox" required>
            <span class="text-sm text-slate-600">Correct</span>
        </label>
        <button type="button" onclick="removeOption(this)" class="option-remove-btn">
            <i class="fas fa-times"></i>
        </button>
    `;
    container.appendChild(optionDiv);
}

// Remove option
function removeOption(btn) {
    const container = document.getElementById('options-container');
    if (container.children.length > 2) {
        btn.closest('.option-input-group').remove();
    } else {
        showNotification('At least 2 options are required', 'error');
    }
}

// Handle add question form submission
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('add-question-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const type = document.getElementById('question-type').value;
            const questionData = {
                question_type: type,
                question_text: document.getElementById('question-text').value.trim(),
                points: parseFloat(document.getElementById('question-points').value) || 1.0,
            };
            
            if (type === 'multiple_choice') {
                const options = [];
                const optionInputs = document.querySelectorAll('#options-container .option-input');
                const correctRadio = document.querySelector('input[name="correct_option"]:checked');
                
                if (!correctRadio) {
                    showNotification('Please select a correct option', 'error');
                    return;
                }
                
                optionInputs.forEach((input, index) => {
                    if (input.value.trim()) {
                        options.push({
                            option_text: input.value.trim(),
                            is_correct: index === parseInt(correctRadio.value),
                            order_index: index
                        });
                    }
                });
                
                if (options.length < 2) {
                    showNotification('At least 2 options are required', 'error');
                    return;
                }
                
                questionData.options = options;
            } else {
                questionData.correct_answer = document.getElementById('correct-answer').value.trim();
                if (!questionData.correct_answer) {
                    showNotification('Please enter a correct answer', 'error');
                    return;
                }
            }
            
            try {
                const response = await fetch(`/quiz/api/quizzes/${currentQuizId}/questions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(questionData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    closeAddQuestionModal();
                    viewQuiz(currentQuizId); // Reload quiz to show new question
                    showNotification('Question added successfully!', 'success');
                } else {
                    showNotification(data.error || 'Failed to add question', 'error');
                }
            } catch (error) {
                console.error('Error adding question:', error);
                showNotification('Error adding question. Please try again.', 'error');
            }
        });
    }
});

// Delete question
async function deleteQuestion(questionId) {
    if (!confirm('Are you sure you want to delete this question?')) return;
    
    try {
        const response = await fetch(`/quiz/api/questions/${questionId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            viewQuiz(currentQuizId); // Reload quiz
            showNotification('Question deleted successfully!', 'success');
        } else {
            showNotification(data.error || 'Failed to delete question', 'error');
        }
    } catch (error) {
        console.error('Error deleting question:', error);
        showNotification('Error deleting question. Please try again.', 'error');
    }
}

// Delete quiz
async function deleteQuiz(quizId) {
    if (!confirm('Are you sure you want to delete this quiz? This action cannot be undone.')) return;
    
    try {
        const response = await fetch(`/quiz/api/quizzes/${quizId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadQuizzes();
            showNotification('Quiz deleted successfully!', 'success');
        } else {
            showNotification(data.error || 'Failed to delete quiz', 'error');
        }
    } catch (error) {
        console.error('Error deleting quiz:', error);
        showNotification('Error deleting quiz. Please try again.', 'error');
    }
}

// Show edit quiz form
function showEditQuizForm() {
    document.getElementById('quiz-info-section').classList.add('hidden');
    document.getElementById('edit-quiz-form-section').classList.remove('hidden');
}

// Cancel edit quiz
function cancelEditQuiz() {
    document.getElementById('quiz-info-section').classList.remove('hidden');
    document.getElementById('edit-quiz-form-section').classList.add('hidden');
}

// Handle edit quiz form
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('edit-quiz-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const quizId = document.getElementById('edit-quiz-id').value;
            const updateData = {
                title: document.getElementById('edit-quiz-title').value.trim(),
                description: document.getElementById('edit-quiz-description').value.trim() || null,
                passing_score: parseFloat(document.getElementById('edit-quiz-passing').value) || 60.0,
            };
            
            try {
                const response = await fetch(`/quiz/api/quizzes/${quizId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updateData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    viewQuiz(quizId); // Reload quiz
                    cancelEditQuiz();
                    showNotification('Quiz updated successfully!', 'success');
                } else {
                    showNotification(data.error || 'Failed to update quiz', 'error');
                }
            } catch (error) {
                console.error('Error updating quiz:', error);
                showNotification('Error updating quiz. Please try again.', 'error');
            }
        });
    }
});

// Load quiz attempts
async function loadQuizAttempts(quizId) {
    try {
        const response = await fetch(`/quiz/api/quizzes/${quizId}/attempts`);
        const data = await response.json();
        
        if (data.success) {
            const attempts = data.attempts || [];
            document.getElementById('quiz-stats-attempts').textContent = attempts.length;
        }
    } catch (error) {
        console.error('Error loading quiz attempts:', error);
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    // Simple notification - you can enhance this
    const bgColor = type === 'success' ? 'bg-green-600' : type === 'error' ? 'bg-red-600' : 'bg-blue-600';
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

