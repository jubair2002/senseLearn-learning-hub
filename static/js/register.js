// API_BASE should be defined in the HTML template before this script loads

// Function to update fields based on user type
function updateFieldsForUserType(userType) {
    const isStudent = userType === 'student';
    
    // Toggle visibility
    document.getElementById('student-fields').classList.toggle('hidden', !isStudent);
    document.getElementById('tutor-fields').classList.toggle('hidden', isStudent);
    
    // Toggle required for student fields
    const disabilityField = document.getElementById('register-disability-type');
    if (isStudent) {
        disabilityField.setAttribute('required', 'required');
    } else {
        disabilityField.removeAttribute('required');
    }
    
    // Toggle required for tutor fields
    const tutorFields = [
        'register-qualifications',
        'register-experience-years',
        'register-hourly-rate',
        'register-subjects',
        'register-bio'
    ];
    
    tutorFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!isStudent) {
            field.setAttribute('required', 'required');
        } else {
            field.removeAttribute('required');
        }
    });
}

// Initialize on page load
updateFieldsForUserType('student');

// Toggle between student and tutor fields
document.querySelectorAll('input[name="user_type"]').forEach(radio => {
    radio.addEventListener('change', function() {
        updateFieldsForUserType(this.value);
    });
});

// Document preview handler
document.getElementById('register-documents').addEventListener('change', function(e) {
    const preview = document.getElementById('document-preview');
    preview.innerHTML = '';
    const files = Array.from(e.target.files);
    
    files.forEach((file, index) => {
        const div = document.createElement('div');
        div.className = 'text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded';
        div.textContent = `${index + 1}. ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
        preview.appendChild(div);
    });
});

// Form submission
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = document.getElementById('register-msg');
    msg.textContent = 'Loading...';
    msg.className = 'mt-1 text-sm text-slate-600';

    try {
        const userType = document.querySelector('input[name="user_type"]:checked').value;
        const isStudent = userType === 'student';
        
        // Validate required fields based on user type
        if (isStudent) {
            const disabilityType = document.getElementById('register-disability-type').value;
            if (!disabilityType) {
                msg.textContent = 'Disability type is required for students';
                msg.className = 'mt-1 text-sm text-red-600';
                return;
            }
        } else {
            const qualifications = document.getElementById('register-qualifications').value;
            const experienceYears = document.getElementById('register-experience-years').value;
            const subjects = document.getElementById('register-subjects').value;
            const hourlyRate = document.getElementById('register-hourly-rate').value;
            const bio = document.getElementById('register-bio').value;
            const documents = document.getElementById('register-documents').files;
            
            if (!qualifications || !experienceYears || !subjects || !hourlyRate || !bio) {
                msg.textContent = 'All tutor information fields are required';
                msg.className = 'mt-1 text-sm text-red-600';
                return;
            }
            
            if (!documents || documents.length === 0) {
                msg.textContent = 'At least one document is required for tutor registration';
                msg.className = 'mt-1 text-sm text-red-600';
                return;
            }
        }

        // Prepare form data (for file uploads)
        const formData = new FormData();
        formData.append('email', document.getElementById('register-email').value);
        formData.append('password', document.getElementById('register-password').value);
        formData.append('full_name', document.getElementById('register-full-name').value);
        formData.append('username', document.getElementById('register-username').value);
        formData.append('phone_number', document.getElementById('register-phone-number').value);
        formData.append('user_type', userType);
        
        if (isStudent) {
            formData.append('disability_type', document.getElementById('register-disability-type').value);
            const studentNeeds = document.getElementById('register-student-needs').value;
            if (studentNeeds) formData.append('student_needs', studentNeeds);
        } else {
            formData.append('qualifications', document.getElementById('register-qualifications').value);
            formData.append('experience_years', document.getElementById('register-experience-years').value);
            formData.append('subjects', document.getElementById('register-subjects').value);
            formData.append('hourly_rate', document.getElementById('register-hourly-rate').value);
            formData.append('bio', document.getElementById('register-bio').value);
            
            // Add files
            const files = document.getElementById('register-documents').files;
            for (let i = 0; i < files.length; i++) {
                formData.append('documents[]', files[i]);
                formData.append(`file_type_${i}`, 'certificate'); // Default type
            }
        }

        const res = await fetch(API_BASE + '/register', {
            method: 'POST',
            body: formData,
            // Don't set Content-Type header - browser will set it automatically with boundary
        });
        const responseData = await res.json();
        if (!res.ok) {
            let text = responseData.message || 'Registration failed';
            if (responseData.detail) {
                text += ' (' + responseData.detail + ')';
            }
            msg.textContent = text;
            msg.className = 'mt-1 text-sm text-red-600';
        } else {
            // Registration submitted, show OTP verification step
            if (responseData.email_verification_required) {
                msg.textContent = responseData.message || 'Please check your email for the OTP code.';
                msg.className = 'mt-1 text-sm text-emerald-600';
                
                // Hide registration form and show OTP verification
                const registerForm = document.getElementById('register-form');
                const otpSection = document.getElementById('otp-verification-section');
                // Get email from form input or response
                const registerEmail = responseData.email || document.getElementById('register-email').value;
                
                if (registerForm && otpSection) {
                    registerForm.style.display = 'none';
                    otpSection.classList.remove('hidden');
                    document.getElementById('otp-email').value = registerEmail;
                }
            } else {
                // Old flow - redirect
                msg.textContent = responseData.message || 'Registration successful!';
                msg.className = 'mt-1 text-sm text-emerald-600';
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            }
        }
    } catch (err) {
        msg.textContent = 'Network error: ' + err.message;
        msg.className = 'mt-1 text-sm text-red-600';
    }
});

// OTP Verification Form
document.getElementById('otp-verify-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const otpMsg = document.getElementById('otp-msg');
    const btn = document.querySelector('#otp-verify-form button[type="submit"]');
    const email = document.getElementById('otp-email').value;
    const otp = document.getElementById('otp-code').value.trim();

    btn.disabled = true;
    btn.textContent = 'Verifying...';
    otpMsg.textContent = 'Verifying OTP...';
    otpMsg.className = 'mt-1 text-sm text-slate-600';

    try {
        const res = await fetch(API_BASE + '/verify-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, otp: otp }),
        });

        const responseData = await res.json();
        
        if (!res.ok) {
            otpMsg.textContent = responseData.message || 'Invalid OTP. Please try again.';
            otpMsg.className = 'mt-1 text-sm text-red-600';
            btn.disabled = false;
            btn.textContent = 'Verify & Complete Registration';
        } else {
            otpMsg.textContent = responseData.message || 'Registration completed successfully!';
            otpMsg.className = 'mt-1 text-sm text-emerald-600';
            
            // Redirect to dashboard/home after successful registration
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        }
    } catch (err) {
        otpMsg.textContent = 'Network error: ' + err.message;
        otpMsg.className = 'mt-1 text-sm text-red-600';
        btn.disabled = false;
        btn.textContent = 'Verify & Complete Registration';
    }
});

// Resend OTP
document.getElementById('resend-otp-btn').addEventListener('click', async () => {
    const otpMsg = document.getElementById('otp-msg');
    const email = document.getElementById('otp-email').value;

    otpMsg.textContent = 'Sending OTP...';
    otpMsg.className = 'mt-1 text-sm text-slate-600';

    try {
        const res = await fetch(API_BASE + '/resend-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, purpose: 'verification' }),
        });

        const responseData = await res.json();
        
        if (!res.ok) {
            otpMsg.textContent = responseData.message || 'Failed to resend OTP.';
            otpMsg.className = 'mt-1 text-sm text-red-600';
        } else {
            otpMsg.textContent = responseData.message || 'OTP has been resent to your email.';
            otpMsg.className = 'mt-1 text-sm text-emerald-600';
        }
    } catch (err) {
        otpMsg.textContent = 'Network error: ' + err.message;
        otpMsg.className = 'mt-1 text-sm text-red-600';
    }
});
