// API_BASE should be defined in the HTML template before this script loads
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = document.getElementById('login-msg');
    msg.textContent = 'Logging in...';
    msg.className = 'mt-2 text-sm text-slate-600';

    try {
        const API_BASE = window.API_BASE || '{{ APP_CONFIG.AUTH_API_PREFIX }}';
        const rememberMe = document.getElementById('remember').checked;
        const response = await fetch(API_BASE + '/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: document.getElementById('login-email').value,
                password: document.getElementById('login-password').value,
                remember: rememberMe
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            // Handle account lockout (423 status)
            if (response.status === 423) {
                msg.textContent = data.message || 'Account is locked due to too many failed login attempts.';
                msg.className = 'mt-2 text-sm text-red-600 font-semibold';
                
                // Disable form inputs when account is locked
                const emailInput = document.getElementById('login-email');
                const passwordInput = document.getElementById('login-password');
                const submitBtn = document.querySelector('#login-form button[type="submit"]');
                
                if (emailInput) emailInput.disabled = true;
                if (passwordInput) passwordInput.disabled = true;
                if (submitBtn) submitBtn.disabled = true;
                
                // Show lockout time if available
                if (data.remaining_minutes) {
                    const lockoutMsg = document.createElement('div');
                    lockoutMsg.id = 'lockout-timer';
                    lockoutMsg.className = 'mt-2 text-sm text-orange-600';
                    lockoutMsg.textContent = `Account will be unlocked in ${data.remaining_minutes} minute(s).`;
                    
                    // Remove existing timer if any
                    const existingTimer = document.getElementById('lockout-timer');
                    if (existingTimer) existingTimer.remove();
                    
                    msg.parentNode.insertBefore(lockoutMsg, msg.nextSibling);
                    
                    // Start countdown timer
                    let minutes = data.remaining_minutes;
                    const timerInterval = setInterval(() => {
                        minutes--;
                        if (minutes <= 0) {
                            clearInterval(timerInterval);
                            lockoutMsg.textContent = 'Account lockout has expired. You can try logging in again.';
                            lockoutMsg.className = 'mt-2 text-sm text-green-600';
                            // Re-enable form
                            if (emailInput) emailInput.disabled = false;
                            if (passwordInput) passwordInput.disabled = false;
                            if (submitBtn) submitBtn.disabled = false;
                        } else {
                            lockoutMsg.textContent = `Account will be unlocked in ${minutes} minute(s).`;
                        }
                    }, 60000); // Update every minute
                }
            } 
            // Handle rate limiting (429 status)
            else if (response.status === 429) {
                msg.textContent = data.error || data.message || 'Too many login attempts. Please try again later.';
                msg.className = 'mt-2 text-sm text-red-600 font-semibold';
                
                // Disable form temporarily
                const submitBtn = document.querySelector('#login-form button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    const retryAfter = data.retry_after || 60;
                    setTimeout(() => {
                        submitBtn.disabled = false;
                        msg.textContent = 'You can try logging in again.';
                        msg.className = 'mt-2 text-sm text-slate-600';
                    }, retryAfter * 1000);
                }
            }
            // Handle regular failed login (401 status)
            else if (response.status === 401) {
                let errorMsg = data.message || 'Invalid email or password';
                
                // Show remaining attempts if available
                if (data.remaining_attempts !== undefined) {
                    if (data.remaining_attempts > 0) {
                        errorMsg += ` (${data.remaining_attempts} attempt(s) remaining)`;
                    } else {
                        errorMsg += ' (No attempts remaining)';
                    }
                }
                
                msg.textContent = errorMsg;
                msg.className = 'mt-2 text-sm text-red-600';
            }
            // Handle other errors
            else {
                msg.textContent = data.message || 'Login failed';
                msg.className = 'mt-2 text-sm text-red-600';
            }
        } else {
            msg.textContent = 'Login successful! Redirecting...';
            msg.className = 'mt-2 text-sm text-green-600';
            
            // Store user info if needed
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Redirect to dashboard based on user type
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        }
    } catch (error) {
        msg.textContent = 'Network error';
        msg.className = 'mt-2 text-sm text-red-600';
    }
});
