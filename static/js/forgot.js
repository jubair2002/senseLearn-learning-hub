// API_BASE should be defined in the HTML template before this script loads

// Step 1: Request Reset Code
document.getElementById('forgot-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = document.getElementById('forgot-msg');
    const btn = document.getElementById('forgot-btn');
    const emailInput = document.getElementById('forgot-email');
    const email = emailInput.value.trim().toLowerCase();
    
    if (!email) {
        msg.textContent = 'Please enter your email address';
        msg.className = 'mt-1 text-sm text-red-600';
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Sending...';
    msg.textContent = 'Sending reset code...';
    msg.className = 'mt-1 text-sm text-slate-600';

    try {
        const res = await fetch(API_BASE + '/forgot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email }),
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            msg.textContent = data.message || 'Failed to send reset code';
            msg.className = 'mt-1 text-sm text-red-600';
            btn.disabled = false;
            btn.textContent = 'Send OTP to Email';
        } else {
            // Show success message - OTP sent via email
            msg.textContent = data.message || 'Password reset OTP has been sent to your email. Please check your inbox.';
            msg.className = 'mt-1 text-sm text-emerald-600 font-medium';
            
            // Auto-fill email in reset form and show step 2 with animation
            document.getElementById('reset-email').value = email;
            const step2 = document.getElementById('step2');
            step2.classList.remove('hidden');
            step2.style.opacity = '0';
            setTimeout(() => {
                step2.style.opacity = '1';
                step2.style.transition = 'opacity 0.3s ease-in';
            }, 10);
            
            // Focus on reset code input
            setTimeout(() => {
                document.getElementById('reset-code').focus();
            }, 100);
            
            btn.disabled = false;
            btn.textContent = 'Send OTP to Email';
        }
    } catch (err) {
        msg.textContent = 'Network error. Please check your connection and try again.';
        msg.className = 'mt-1 text-sm text-red-600';
        btn.disabled = false;
        btn.textContent = 'Send Reset Code';
    }
});

// Step 2: Reset Password
document.getElementById('reset-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = document.getElementById('reset-msg');
    const btn = document.getElementById('reset-btn');
    const email = document.getElementById('reset-email').value.trim().toLowerCase();
    const code = document.getElementById('reset-code').value.trim();
    const password = document.getElementById('reset-password').value;
    const passwordConfirm = document.getElementById('reset-password-confirm').value;

    // Validate passwords match
    if (password !== passwordConfirm) {
        msg.textContent = 'Passwords do not match. Please try again.';
        msg.className = 'mt-1 text-sm text-red-600';
        document.getElementById('reset-password-confirm').focus();
        return;
    }

    if (password.length < 8) {
        msg.textContent = 'Password must be at least 8 characters long';
        msg.className = 'mt-1 text-sm text-red-600';
        document.getElementById('reset-password').focus();
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Resetting...';
    msg.textContent = 'Resetting your password...';
    msg.className = 'mt-1 text-sm text-slate-600';

    try {
        const res = await fetch(API_BASE + '/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                otp: code,  // Using 'otp' for consistency with backend
                new_password: password,
            }),
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            msg.textContent = data.message || 'Failed to reset password';
            msg.className = 'mt-1 text-sm text-red-600';
            btn.disabled = false;
            btn.textContent = 'Reset Password';
        } else {
            // Success - hide forms and show success message with animation
            const step1 = document.getElementById('step1');
            const step2 = document.getElementById('step2');
            const success = document.getElementById('success-message');
            
            step1.style.opacity = '0';
            step2.style.opacity = '0';
            setTimeout(() => {
                step1.classList.add('hidden');
                step2.classList.add('hidden');
                success.classList.remove('hidden');
                success.style.opacity = '0';
                setTimeout(() => {
                    success.style.opacity = '1';
                    success.style.transition = 'opacity 0.5s ease-in';
                }, 10);
            }, 300);
        }
    } catch (err) {
        msg.textContent = 'Network error. Please check your connection and try again.';
        msg.className = 'mt-1 text-sm text-red-600';
        btn.disabled = false;
        btn.textContent = 'Reset Password';
    }
});

// Real-time password match validation
const passwordInput = document.getElementById('reset-password');
const passwordConfirmInput = document.getElementById('reset-password-confirm');
const resetMsg = document.getElementById('reset-msg');

function validatePasswords() {
    if (passwordConfirmInput.value && passwordInput.value) {
        if (passwordInput.value !== passwordConfirmInput.value) {
            passwordConfirmInput.classList.add('border-red-500');
            passwordConfirmInput.classList.remove('border-slate-300');
        } else {
            passwordConfirmInput.classList.remove('border-red-500');
            passwordConfirmInput.classList.add('border-slate-300');
            if (resetMsg.textContent.includes('Passwords do not match')) {
                resetMsg.textContent = '';
            }
        }
    }
}

passwordInput.addEventListener('input', validatePasswords);
passwordConfirmInput.addEventListener('input', validatePasswords);
