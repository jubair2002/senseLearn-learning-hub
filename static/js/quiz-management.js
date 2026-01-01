// Quiz Management JavaScript
// Handles all quiz-related UI interactions and API calls

let currentCourseId = null;
let currentModuleId = null;
let currentQuizId = null;
let quizzes = [];
let currentQuiz = null;

// Initialize quiz management for a course - make it globally accessible
window.initQuizManagement = function(courseId, moduleId = null) {
    console.log('initQuizManagement called with courseId:', courseId, 'moduleId:', moduleId);
    currentCourseId = courseId;
    currentModuleId = moduleId;
    loadQuizzes();
};

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

// Refresh quiz list for a specific module (used after creating a quiz)
async function refreshQuizListForModule(courseId, moduleId) {
    console.log('Refreshing quiz list for module:', moduleId);
    const quizListEl = document.getElementById(`quizzes-list-module-${moduleId}`);
    
    if (!quizListEl) {
        console.warn('Quiz list element not found for module:', moduleId, 'Looking for: quizzes-list-module-' + moduleId);
        return;
    }
    
    try {
        // Fetch fresh quizzes with cache-busting
        const response = await fetch(`/quiz/api/courses/${courseId}/quizzes?t=${Date.now()}`);
        const data = await response.json();
        
        console.log('Quiz refresh response:', data);
        
        if (data.success && data.quizzes) {
            // Filter quizzes for this module
            const moduleQuizzes = data.quizzes.filter(q => {
                const quizModuleId = q.module_id !== null && q.module_id !== undefined ? parseInt(q.module_id) : null;
                const targetModuleId = parseInt(moduleId);
                const matches = quizModuleId === targetModuleId;
                if (matches) {
                    console.log('Quiz matches:', { id: q.id, title: q.title, module_id: quizModuleId });
                }
                return matches;
            });
            
            console.log('Found', moduleQuizzes.length, 'quizzes for module', moduleId);
            
            // Update the quiz list HTML
            if (moduleQuizzes.length > 0) {
                quizListEl.innerHTML = moduleQuizzes.map(quiz => `
                    <div class="border border-slate-200 rounded-lg p-4 hover:shadow-md transition">
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <h5 class="font-semibold text-slate-800 mb-1">${(quiz.title || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</h5>
                                ${quiz.description ? `<p class="text-sm text-slate-600 mb-2">${(quiz.description || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>` : ''}
                                <div class="flex items-center gap-4 text-xs text-slate-500">
                                    <span><i class="fas fa-question-circle mr-1"></i>${quiz.question_count || 0} questions</span>
                                    <span><i class="fas fa-star mr-1"></i>${quiz.total_points || 0} points</span>
                                    <span class="px-2 py-1 rounded ${quiz.is_active ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'}">
                                        ${quiz.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </div>
                            </div>
                            <div class="flex gap-2">
                                <button onclick="window.viewQuiz(${quiz.id})" class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                                    <i class="fas fa-eye mr-1"></i>View
                                </button>
                                <button onclick="window.deleteQuiz(${quiz.id})" class="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700">
                                    <i class="fas fa-trash mr-1"></i>Delete
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                quizListEl.innerHTML = `
                    <div class="text-center py-8 text-slate-400">
                        <i class="fas fa-clipboard-list text-4xl mb-3"></i>
                        <p class="text-sm">No quizzes for this module yet</p>
                        <button onclick="window.showCreateQuizModalForModule(${courseId}, ${moduleId})" class="mt-3 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm">
                            <i class="fas fa-plus mr-2"></i>Create Quiz
                        </button>
                    </div>
                `;
            }
        } else {
            console.error('Failed to load quizzes:', data.error);
        }
    } catch (error) {
        console.error('Error refreshing quiz list:', error);
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

// Show create quiz modal - make globally accessible
window.showCreateQuizModal = function() {
    const modal = document.getElementById('create-quiz-modal');
    if (!modal) {
        console.error('create-quiz-modal not found');
        return;
    }
    
    // Reset form first
    const form = document.getElementById('create-quiz-form');
    if (form) {
        form.reset();
    }
    
    // Then set the hidden fields (after reset so they don't get cleared)
    document.getElementById('quiz-course-id').value = currentCourseId;
    document.getElementById('quiz-module-id').value = currentModuleId || '';
    
    modal.classList.remove('hidden');
};

// Show create quiz modal for a specific module
window.showCreateQuizModalForModule = function(courseId, moduleId) {
    const modal = document.getElementById('create-quiz-modal');
    if (!modal) {
        console.error('create-quiz-modal not found');
        return;
    }
    
    currentCourseId = courseId;
    currentModuleId = moduleId;
    
    // Reset form first
    const form = document.getElementById('create-quiz-form');
    if (form) {
        form.reset();
    }
    
    // Then set the hidden fields (after reset so they don't get cleared)
    document.getElementById('quiz-course-id').value = courseId;
    document.getElementById('quiz-module-id').value = moduleId;
    
    console.log('Opening quiz modal for course:', courseId, 'module:', moduleId);
    console.log('Hidden field values - course_id:', document.getElementById('quiz-course-id').value, 'module_id:', document.getElementById('quiz-module-id').value);
    
    modal.classList.remove('hidden');
};

// Close create quiz modal - make globally accessible
window.closeCreateQuizModal = function() {
    const modal = document.getElementById('create-quiz-modal');
    if (modal) modal.classList.add('hidden');
};

// Handle create quiz form submission - use document-level event delegation
// This works even if the form is loaded dynamically via AJAX
document.addEventListener('submit', async function(e) {
    // Check if this is the create quiz form
    if (e.target && e.target.id === 'create-quiz-form') {
        e.preventDefault();
        e.stopPropagation();
        
        console.log('Create quiz form submitted');
        
        const formData = {
            title: document.getElementById('quiz-title').value.trim(),
            description: document.getElementById('quiz-description').value.trim() || null,
            instructions: document.getElementById('quiz-instructions').value.trim() || null,
            time_limit_minutes: document.getElementById('quiz-time-limit').value ? parseInt(document.getElementById('quiz-time-limit').value) : null,
            passing_score: parseFloat(document.getElementById('quiz-passing-score').value) || 60.0,
            max_attempts: parseInt(document.getElementById('quiz-max-attempts').value) || 1,
        };
        
        // Get module_id from hidden input - check both the input and the currentModuleId variable
        const moduleIdInput = document.getElementById('quiz-module-id');
        let moduleId = moduleIdInput ? moduleIdInput.value : null;
        
        // Fallback to currentModuleId if input is empty
        if (!moduleId || moduleId === '') {
            moduleId = currentModuleId;
        }
        
        console.log('Module ID input element:', moduleIdInput);
        console.log('Module ID from input (raw):', moduleIdInput ? moduleIdInput.value : 'N/A');
        console.log('Module ID from variable:', currentModuleId);
        console.log('Final module ID to use:', moduleId);
        
        if (moduleId && moduleId !== '' && moduleId !== null) {
            formData.module_id = parseInt(moduleId);
            console.log('Added module_id to formData:', formData.module_id);
        } else {
            console.warn('No module_id available - quiz will be created without module association');
        }
        
        console.log('Creating quiz with data:', formData);
        
        try {
            const response = await fetch(`/quiz/api/courses/${currentCourseId}/quizzes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            console.log('Quiz creation response:', data);
            
            if (data.success) {
                console.log('Quiz created successfully. Quiz data:', data.quiz);
                console.log('Created quiz module_id:', data.quiz ? data.quiz.module_id : 'N/A');
                closeCreateQuizModal();
                showNotification('Quiz created successfully!', 'success');
                
                // Get the module ID that was used to create the quiz
                const courseViewEl = document.querySelector('[data-course-id]');
                if (courseViewEl) {
                    const courseId = parseInt(courseViewEl.getAttribute('data-course-id'));
                    // Use the module_id from the form data (the one we just used to create the quiz)
                    let targetModuleId = null;
                    
                    if (moduleId && moduleId !== '' && moduleId !== null) {
                        targetModuleId = parseInt(moduleId);
                    } else if (data.quiz && data.quiz.module_id) {
                        targetModuleId = parseInt(data.quiz.module_id);
                    } else {
                        // Find the currently selected module (has bg-blue-50 class)
                        const moduleItem = document.querySelector('.module-item.bg-blue-50, .module-item.border-blue-300');
                        if (moduleItem) {
                            targetModuleId = parseInt(moduleItem.getAttribute('data-module-id'));
                        }
                    }
                    
                    if (!targetModuleId) {
                        // Fallback: try to find any module item
                        const anyModuleItem = document.querySelector('.module-item[data-module-id]');
                        if (anyModuleItem) {
                            targetModuleId = parseInt(anyModuleItem.getAttribute('data-module-id'));
                        }
                    }
                    
                    console.log('Refreshing quiz list after creation - courseId:', courseId, 'moduleId:', targetModuleId);
                    
                    if (!isNaN(targetModuleId) && !isNaN(courseId)) {
                        // Wait a moment for database commit, then refresh quiz list
                        setTimeout(() => {
                            refreshQuizListForModule(courseId, targetModuleId);
                        }, 800);
                        
                        // Don't reload the entire module - just refresh the quiz list
                        // This prevents the page from "vanishing"
                    } else {
                        console.warn('Invalid module or course ID for refresh');
                    }
                } else {
                    console.warn('Could not find course view element');
                }
            } else {
                showNotification(data.error || 'Failed to create quiz', 'error');
            }
        } catch (error) {
            console.error('Error creating quiz:', error);
            showNotification('Error creating quiz. Please try again.', 'error');
        }
        
        return false; // Prevent any form submission
    }
});

// View quiz details - make globally accessible
window.viewQuiz = async function(quizId) {
    currentQuizId = quizId;
    
    try {
        const response = await fetch(`/quiz/api/quizzes/${quizId}`);
        const data = await response.json();
        
        if (data.success && data.quiz) {
            currentQuiz = data.quiz;
            showQuizDetailsModal(data.quiz);
        } else {
            showNotification(data.error || 'Failed to load quiz', 'error');
        }
    } catch (error) {
        console.error('Error loading quiz:', error);
        showNotification('Error loading quiz. Please try again.', 'error');
    }
};

// Show quiz details modal - make globally accessible
window.showQuizDetailsModal = function(quiz) {
    const modal = document.getElementById('quiz-details-modal');
    if (!modal) {
        console.error('quiz-details-modal not found');
        return;
    }
    
    // Set quiz info
    document.getElementById('quiz-info-title').textContent = quiz.title;
    document.getElementById('quiz-info-description').textContent = quiz.description || 'No description';
    document.getElementById('quiz-info-time').textContent = quiz.time_limit_minutes ? `${quiz.time_limit_minutes} minutes` : 'No limit';
    document.getElementById('quiz-info-passing').textContent = quiz.passing_score ? `${quiz.passing_score}%` : 'N/A';
    document.getElementById('quiz-info-attempts').textContent = quiz.max_attempts || 'Unlimited';
    
    // Set quiz stats
    document.getElementById('quiz-stats-questions').textContent = quiz.question_count || 0;
    document.getElementById('quiz-stats-points').textContent = quiz.total_points || 0;
    
    // Store quiz ID for editing
    document.getElementById('edit-quiz-id').value = quiz.id;
    document.getElementById('edit-quiz-title').value = quiz.title;
    document.getElementById('edit-quiz-description').value = quiz.description || '';
    document.getElementById('edit-quiz-passing').value = quiz.passing_score || 60;
    const maxAttemptsInput = document.getElementById('edit-quiz-max-attempts');
    if (maxAttemptsInput) {
        maxAttemptsInput.value = quiz.max_attempts || '';
    }
    
    // Load questions
    renderQuestions(quiz.questions || []);
    
    // Load attempts
    loadQuizAttempts(quiz.id);
    
    // Hide edit form initially
    const editFormSection = document.getElementById('edit-quiz-form-section');
    if (editFormSection) {
        editFormSection.classList.add('hidden');
    }
    
    modal.classList.remove('hidden');
};

// Show edit quiz form - make globally accessible
window.showEditQuizForm = function() {
    const editFormSection = document.getElementById('edit-quiz-form-section');
    if (editFormSection) {
        editFormSection.classList.remove('hidden');
    }
};

// Cancel edit quiz - make globally accessible
window.cancelEditQuiz = function() {
    const editFormSection = document.getElementById('edit-quiz-form-section');
    if (editFormSection) {
        editFormSection.classList.add('hidden');
    }
    // Reload quiz to reset form
    if (currentQuizId) {
        viewQuiz(currentQuizId);
    }
};

// Close quiz details modal - make globally accessible
window.closeQuizDetailsModal = function() {
    const modal = document.getElementById('quiz-details-modal');
    if (modal) modal.classList.add('hidden');
};

// Show add question modal - make globally accessible
window.showAddQuestionModal = function(quizId) {
    if (!quizId) {
        quizId = currentQuizId;
    }
    if (!quizId) {
        showNotification('Quiz ID not found', 'error');
        return;
    }
    
    currentQuizId = quizId;
    const modal = document.getElementById('add-question-modal');
    if (!modal) {
        console.error('add-question-modal not found');
        return;
    }
    
    document.getElementById('question-quiz-id').value = quizId;
    const form = document.getElementById('add-question-form');
    if (form) {
        form.reset();
    }
    document.getElementById('question-type').value = '';
    
    // Clear options container
    const optionsContainer = document.getElementById('options-container');
    if (optionsContainer) {
        optionsContainer.innerHTML = '';
    }
    
    // Hide sections
    const multipleChoiceSection = document.getElementById('multiple-choice-section');
    const answerSection = document.getElementById('answer-section');
    if (multipleChoiceSection) multipleChoiceSection.classList.add('hidden');
    if (answerSection) answerSection.classList.add('hidden');
    
    handleQuestionTypeChange();
    modal.classList.remove('hidden');
};

// Close add question modal - make globally accessible
window.closeAddQuestionModal = function() {
    const modal = document.getElementById('add-question-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
    
    // Reset form to "add" mode
    const form = document.getElementById('add-question-form');
    if (form) {
        form.reset();
        delete form.dataset.editMode;
        delete form.dataset.questionId;
    }
    
    // Reset modal title and button
    const modalTitle = document.querySelector('#add-question-modal h3');
    if (modalTitle) {
        modalTitle.textContent = 'Add Question';
    }
    
    const submitBtn = document.querySelector('#add-question-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.textContent = 'Add Question';
    }
    
    // Clear options container
    const optionsContainer = document.getElementById('options-container');
    if (optionsContainer) {
        optionsContainer.innerHTML = '';
    }
    
    // Hide sections
    const multipleChoiceSection = document.getElementById('multiple-choice-section');
    const answerSection = document.getElementById('answer-section');
    if (multipleChoiceSection) multipleChoiceSection.classList.add('hidden');
    if (answerSection) answerSection.classList.add('hidden');
};

// Handle question type change
window.handleQuestionTypeChange = function() {
    const type = document.getElementById('question-type').value;
    const multipleChoiceSection = document.getElementById('multiple-choice-section');
    const answerSection = document.getElementById('answer-section');
    const optionsContainer = document.getElementById('options-container');
    
    if (multipleChoiceSection) multipleChoiceSection.classList.add('hidden');
    if (answerSection) answerSection.classList.add('hidden');
    
    if (type === 'multiple_choice') {
        if (multipleChoiceSection) {
            multipleChoiceSection.classList.remove('hidden');
            if (optionsContainer && optionsContainer.children.length === 0) {
                // Add initial 2 options
                addOptionField();
                addOptionField();
            }
        }
    } else if (type === 'short_answer' || type === 'true_false') {
        if (answerSection) answerSection.classList.remove('hidden');
    }
};

// Add option field for multiple choice
window.addOptionField = function() {
    const container = document.getElementById('options-container');
    if (!container) return;
    
    const optionCount = container.children.length;
    const optionDiv = document.createElement('div');
    optionDiv.className = 'flex items-center gap-2';
    optionDiv.setAttribute('data-option-index', optionCount);
    optionDiv.innerHTML = `
        <input type="text" name="option_text" placeholder="Option text" required
               class="flex-1 px-3 py-2 border border-slate-300 rounded-lg">
        <input type="radio" name="correct_option" value="${optionCount}" required>
        <label class="text-sm text-slate-600">Correct</label>
        <button type="button" onclick="removeOptionField(this)" class="px-2 py-1 text-red-600 hover:text-red-700">
            <i class="fas fa-times"></i>
        </button>
    `;
    container.appendChild(optionDiv);
    
    // Update all radio button values to match their index after adding
    updateRadioButtonValues();
};

// Update radio button values to match their container index
function updateRadioButtonValues() {
    const container = document.getElementById('options-container');
    if (!container) return;
    
    const options = container.children;
    for (let i = 0; i < options.length; i++) {
        const optionDiv = options[i];
        optionDiv.setAttribute('data-option-index', i);
        const radio = optionDiv.querySelector('input[type="radio"]');
        if (radio) {
            radio.value = i;
        }
    }
}

// Remove option field
window.removeOptionField = function(button) {
    const container = document.getElementById('options-container');
    if (container && container.children.length > 2) {
        button.parentElement.remove();
        // Update radio button values after removal
        updateRadioButtonValues();
    } else {
        alert('Multiple choice questions must have at least 2 options');
    }
};

// Create quiz function
async function createQuiz() {
    // This is handled by the form submit event listener above
}

// Setup edit quiz form submission
document.addEventListener('submit', async function(e) {
    if (e.target && e.target.id === 'edit-quiz-form') {
        e.preventDefault();
        e.stopPropagation();
        await window.updateQuiz();
        return false;
    }
});

// Update quiz function
window.updateQuiz = async function() {
    const quizId = document.getElementById('edit-quiz-id').value;
    if (!quizId) {
        showNotification('Quiz ID not found', 'error');
        return;
    }
    
    const maxAttemptsInput = document.getElementById('edit-quiz-max-attempts');
    const maxAttemptsValue = maxAttemptsInput ? maxAttemptsInput.value.trim() : '';
    
    const updateData = {
        title: document.getElementById('edit-quiz-title').value.trim(),
        description: document.getElementById('edit-quiz-description').value.trim() || null,
        passing_score: parseFloat(document.getElementById('edit-quiz-passing').value) || 60.0,
        max_attempts: maxAttemptsValue ? parseInt(maxAttemptsValue) : null,
    };
    
    if (!updateData.title) {
        showNotification('Quiz title is required', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/quiz/api/quizzes/${quizId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Quiz updated successfully!', 'success');
            // Hide edit form
            cancelEditQuiz();
            // Reload quiz details
            if (typeof window.viewQuiz === 'function') {
                window.viewQuiz(quizId);
            }
        } else {
            showNotification(data.error || 'Failed to update quiz', 'error');
        }
    } catch (error) {
        console.error('Error updating quiz:', error);
        showNotification('Error updating quiz. Please try again.', 'error');
    }
};

// Delete quiz - make globally accessible
window.deleteQuiz = async function(quizId) {
    if (!confirm('Are you sure you want to delete this quiz? This action cannot be undone.')) return;
    
    try {
        const response = await fetch(`/quiz/api/quizzes/${quizId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Quiz deleted successfully!', 'success');
            
            // Reload the module to refresh the quiz list
            const courseViewEl = document.querySelector('[data-course-id]');
            if (courseViewEl) {
                const courseId = parseInt(courseViewEl.getAttribute('data-course-id'));
                const moduleItem = document.querySelector('.module-item.border-blue-500, .module-item[data-module-id]');
                if (moduleItem) {
                    const moduleId = parseInt(moduleItem.getAttribute('data-module-id'));
                    if (typeof selectModule === 'function') {
                        selectModule(courseId, moduleId);
                    } else if (typeof window.selectModule === 'function') {
                        window.selectModule(courseId, moduleId);
                    }
                }
            }
            
            // Also close quiz details modal if open
            const quizModal = document.getElementById('quiz-details-modal');
            if (quizModal && !quizModal.classList.contains('hidden')) {
                closeQuizDetailsModal();
            }
        } else {
            showNotification(data.error || 'Failed to delete quiz', 'error');
        }
    } catch (error) {
        console.error('Error deleting quiz:', error);
        showNotification('Error deleting quiz. Please try again.', 'error');
    }
}

// Setup add/edit question form submission
document.addEventListener('submit', async function(e) {
    if (e.target && e.target.id === 'add-question-form') {
        e.preventDefault();
        e.stopPropagation();
        
        // Check if we're in edit mode
        if (e.target.dataset.editMode === 'true') {
            await window.updateQuestion();
        } else {
            await window.addQuestion();
        }
        
        return false;
    }
});

// Add question function
window.addQuestion = async function() {
    const form = document.getElementById('add-question-form');
    if (!form) return;
    
    const quizId = document.getElementById('question-quiz-id').value;
    if (!quizId) {
        showNotification('Quiz ID not found', 'error');
        return;
    }
    
    const type = document.getElementById('question-type').value;
    if (!type) {
        showNotification('Please select a question type', 'error');
        return;
    }
    
    const questionData = {
        question_type: type,
        question_text: document.getElementById('question-text').value.trim(),
        points: parseFloat(document.getElementById('question-points').value) || 1.0,
    };
    
    if (type === 'multiple_choice') {
        const options = [];
        const optionInputs = document.querySelectorAll('#options-container input[name="option_text"]');
        const correctOption = document.querySelector('input[name="correct_option"]:checked');
        
        // Validate that exactly one option is marked as correct
        if (!correctOption) {
            showNotification('Please select the correct answer for this multiple choice question', 'error');
            return;
        }
        
        const correctIndex = parseInt(correctOption.value);
        
        optionInputs.forEach((input, index) => {
            const optionDiv = input.closest('[data-option-index]');
            const actualIndex = optionDiv ? parseInt(optionDiv.getAttribute('data-option-index')) : index;
            
            options.push({
                option_text: input.value.trim(),
                is_correct: actualIndex === correctIndex,
                order_index: actualIndex
            });
        });
        
        // Validate that exactly one option is correct
        const correctCount = options.filter(opt => opt.is_correct).length;
        if (correctCount !== 1) {
            showNotification('Multiple choice questions must have exactly one correct answer', 'error');
            return;
        }
        
        questionData.options = options;
    } else {
        questionData.correct_answer = document.getElementById('correct-answer').value.trim();
    }
    
    try {
        const response = await fetch(`/quiz/api/quizzes/${quizId}/questions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(questionData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Question added successfully!', 'success');
            closeAddQuestionModal();
            // Reload quiz details to show new question
            if (typeof window.viewQuiz === 'function') {
                window.viewQuiz(quizId);
            }
        } else {
            showNotification(data.error || 'Failed to add question', 'error');
        }
    } catch (error) {
        console.error('Error adding question:', error);
        showNotification('Error adding question. Please try again.', 'error');
    }
};

// Edit question - make globally accessible
window.editQuestion = async function(questionId) {
    if (!questionId) {
        showNotification('Question ID not found', 'error');
        return;
    }
    
    try {
        console.log('Fetching question:', questionId);
        // Fetch question details
        const response = await fetch(`/quiz/api/questions/${questionId}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', response.status, errorText);
            let errorMessage = `Failed to load question (${response.status})`;
            try {
                const errorData = JSON.parse(errorText);
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                // Not JSON, use the text
            }
            showNotification(errorMessage, 'error');
            return;
        }
        
        const data = await response.json();
        console.log('Question data received:', data);
        
        if (!data.success || !data.question) {
            console.error('Invalid response data:', data);
            showNotification(data.error || 'Failed to load question', 'error');
            return;
        }
        
        const question = data.question;
        
        // Change modal title
        const modalTitle = document.querySelector('#add-question-modal h3');
        if (modalTitle) {
            modalTitle.textContent = 'Edit Question';
        }
        
        // Change submit button text
        const submitBtn = document.querySelector('#add-question-form button[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = 'Update Question';
        }
        
        // Set hidden field to indicate we're editing
        const form = document.getElementById('add-question-form');
        if (form) {
            form.dataset.editMode = 'true';
            form.dataset.questionId = questionId;
        }
        
        // Populate form fields
        document.getElementById('question-quiz-id').value = question.quiz_id || currentQuizId;
        document.getElementById('question-type').value = question.question_type;
        document.getElementById('question-text').value = question.question_text || '';
        document.getElementById('question-points').value = question.points || 1.0;
        
        // Clear options container
        const optionsContainer = document.getElementById('options-container');
        if (optionsContainer) {
            optionsContainer.innerHTML = '';
        }
        
        // Handle question type
        handleQuestionTypeChange();
        
        if (question.question_type === 'multiple_choice' && question.options) {
            // Populate multiple choice options
            question.options.forEach((opt, index) => {
                window.addOptionField();
            });
            
            // Now populate the values after all fields are created
            const optionInputs = document.querySelectorAll('#options-container input[name="option_text"]');
            const radioInputs = document.querySelectorAll('#options-container input[name="correct_option"]');
            
            question.options.forEach((opt, index) => {
                if (optionInputs[index]) {
                    optionInputs[index].value = opt.option_text || '';
                }
                if (radioInputs[index] && opt.is_correct) {
                    radioInputs[index].checked = true;
                }
            });
        } else if (question.question_type === 'short_answer' || question.question_type === 'true_false') {
            // Set correct answer
            document.getElementById('correct-answer').value = question.correct_answer || '';
        }
        
        // Show modal
        const modal = document.getElementById('add-question-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error loading question:', error);
        showNotification('Error loading question. Please try again.', 'error');
    }
};

// Update question function
window.updateQuestion = async function() {
    const form = document.getElementById('add-question-form');
    if (!form) return;
    
    const questionId = form.dataset.questionId;
    if (!questionId) {
        showNotification('Question ID not found', 'error');
        return;
    }
    
    const type = document.getElementById('question-type').value;
    if (!type) {
        showNotification('Please select a question type', 'error');
        return;
    }
    
    const questionData = {
        question_text: document.getElementById('question-text').value.trim(),
        points: parseFloat(document.getElementById('question-points').value) || 1.0,
    };
    
    if (type === 'multiple_choice') {
        const options = [];
        const optionInputs = document.querySelectorAll('#options-container input[name="option_text"]');
        const correctOption = document.querySelector('input[name="correct_option"]:checked');
        
        // Validate that exactly one option is marked as correct
        if (!correctOption) {
            showNotification('Please select the correct answer for this multiple choice question', 'error');
            return;
        }
        
        const correctIndex = parseInt(correctOption.value);
        
        optionInputs.forEach((input, index) => {
            const optionDiv = input.closest('[data-option-index]');
            const actualIndex = optionDiv ? parseInt(optionDiv.getAttribute('data-option-index')) : index;
            
            options.push({
                option_text: input.value.trim(),
                is_correct: actualIndex === correctIndex,
                order_index: actualIndex
            });
        });
        
        // Validate that exactly one option is correct
        const correctCount = options.filter(opt => opt.is_correct).length;
        if (correctCount !== 1) {
            showNotification('Multiple choice questions must have exactly one correct answer', 'error');
            return;
        }
        
        questionData.options = options;
    } else {
        questionData.correct_answer = document.getElementById('correct-answer').value.trim();
    }
    
    try {
        const response = await fetch(`/quiz/api/questions/${questionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(questionData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Question updated successfully!', 'success');
            closeAddQuestionModal();
            // Reload quiz details to show updated question
            const quizId = document.getElementById('question-quiz-id').value || currentQuizId;
            if (quizId && typeof window.viewQuiz === 'function') {
                window.viewQuiz(quizId);
            }
        } else {
            showNotification(data.error || 'Failed to update question', 'error');
        }
    } catch (error) {
        console.error('Error updating question:', error);
        showNotification('Error updating question. Please try again.', 'error');
    }
};

// Delete question - make globally accessible
window.deleteQuestion = async function(questionId) {
    if (!confirm('Are you sure you want to delete this question?')) return;
    
    try {
        const response = await fetch(`/quiz/api/questions/${questionId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Question deleted successfully!', 'success');
            // Reload quiz details
            if (currentQuizId) {
                viewQuiz(currentQuizId);
            }
        } else {
            showNotification(data.error || 'Failed to delete question', 'error');
        }
    } catch (error) {
        console.error('Error deleting question:', error);
        showNotification('Error deleting question. Please try again.', 'error');
    }
}

// Render questions in quiz details
function renderQuestions(questions) {
    const listEl = document.getElementById('questions-list');
    if (!listEl) return;
    
    if (questions.length === 0) {
        listEl.innerHTML = '<div class="text-center py-8 text-slate-400"><p>No questions yet. Add your first question!</p></div>';
        return;
    }
    
    listEl.innerHTML = questions.map(q => {
        let questionHtml = `
            <div class="border border-slate-200 rounded-lg p-4 mb-3">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">${q.question_type.replace('_', ' ')}</span>
                            <span class="text-sm text-slate-500">${q.points} points</span>
                        </div>
                        <p class="font-medium text-slate-800 mb-2">${escapeHtml(q.question_text)}</p>
        `;
        
        if (q.question_type === 'multiple_choice' && q.options) {
            questionHtml += '<div class="space-y-1">';
            q.options.forEach(opt => {
                questionHtml += `
                    <div class="flex items-center gap-2 text-sm">
                        <input type="radio" disabled ${opt.is_correct ? 'checked' : ''}>
                        <span class="${opt.is_correct ? 'font-semibold text-green-700' : 'text-slate-600'}">${escapeHtml(opt.option_text)}</span>
                        ${opt.is_correct ? '<i class="fas fa-check-circle text-green-600"></i>' : ''}
                    </div>
                `;
            });
            questionHtml += '</div>';
        } else {
            questionHtml += `<p class="text-sm text-slate-600"><strong>Correct Answer:</strong> ${escapeHtml(q.correct_answer || 'N/A')}</p>`;
        }
        
        questionHtml += `
                    </div>
                    <div class="flex gap-2">
                        <button onclick="editQuestion(${q.id})" class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                            <i class="fas fa-edit mr-1"></i>Edit
                        </button>
                        <button onclick="deleteQuestion(${q.id})" class="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700">
                            <i class="fas fa-trash mr-1"></i>Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        return questionHtml;
    }).join('');
}

// Load quiz attempts
async function loadQuizAttempts(quizId) {
    try {
        const response = await fetch(`/quiz/api/quizzes/${quizId}/attempts`);
        const data = await response.json();
        
        if (data.success) {
            renderQuizAttempts(data.attempts || []);
        }
    } catch (error) {
        console.error('Error loading quiz attempts:', error);
    }
}

// Render quiz attempts
function renderQuizAttempts(attempts) {
    const statsEl = document.getElementById('quiz-stats-attempts');
    if (statsEl) {
        statsEl.textContent = attempts.length;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple notification - you can enhance this
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-600' : 
        type === 'error' ? 'bg-red-600' : 
        'bg-blue-600'
    } text-white`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
