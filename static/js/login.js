// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) {
        console.error('Login form not found');
        return;
    }
    
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msg = document.getElementById('login-msg');
        msg.textContent = 'Logging in...';
        msg.className = 'mt-2 text-sm text-slate-600';

        try {
            // Get API base URL - try multiple sources
            let API_BASE = window.API_BASE;
            if (!API_BASE) {
                // Try to get from script tag or use default
                API_BASE = '/api/auth';
            }
            
            const rememberMe = document.getElementById('remember') ? document.getElementById('remember').checked : false;
            
            console.log('Login attempt to:', API_BASE + '/login');
            
            const response = await fetch(API_BASE + '/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: document.getElementById('login-email').value,
                    password: document.getElementById('login-password').value,
                    remember: rememberMe
                })
            });

            // Parse JSON response, handle errors
            let data;
            try {
                const text = await response.text();
                data = text ? JSON.parse(text) : {};
            } catch (parseError) {
                console.error('Failed to parse response:', parseError);
                msg.textContent = 'Server error: Invalid response format';
                msg.className = 'mt-2 text-sm text-red-600';
                return;
            }
            
            console.log('Login response:', response.status, data);
            console.log('Failed attempts:', data.failed_attempts, 'Max:', data.max_attempts, 'Remaining:', data.remaining_attempts);
            
            if (!response.ok) {
                // Handle account lockout (423 status)
                if (response.status === 423) {
                    let lockoutMsg = '<strong>' + (data.message || 'Account is locked due to too many failed login attempts.') + '</strong>';
                    
                    // Show attempt count if available
                    if (data.failed_attempts !== undefined && data.max_attempts !== undefined) {
                        lockoutMsg += `<br><span style="color: #dc2626; font-weight: bold;">Attempt ${data.failed_attempts} of ${data.max_attempts} - Account Locked</span>`;
                    }
                    
                    msg.innerHTML = lockoutMsg;
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
                    // Show attempt count and remaining attempts - ALWAYS show if data exists
                    const failed = data.failed_attempts;
                    const max = data.max_attempts;
                    const remaining = data.remaining_attempts;
                    
                    console.log('🔍 Displaying 401 error - Failed:', failed, 'Max:', max, 'Remaining:', remaining);
                    console.log('🔍 Full data object:', JSON.stringify(data, null, 2));
                    
                    let errorMsg = '';
                    
                    // Always show the main message
                    errorMsg += `<div style="font-weight: 600; margin-bottom: 6px; color: #dc2626;">${data.message || 'Invalid email or password'}</div>`;
                    
                    // Show attempt count if available
                    if (failed !== undefined && max !== undefined && !isNaN(failed) && !isNaN(max)) {
                        errorMsg += `<div style="color: #dc2626; font-weight: bold; font-size: 15px; margin: 4px 0;">Attempt ${failed} of ${max}</div>`;
                        
                        if (remaining !== undefined && !isNaN(remaining)) {
                            if (remaining > 0) {
                                errorMsg += `<div style="color: #ea580c; font-size: 13px; margin-top: 4px;">${remaining} attempt(s) remaining before account lockout</div>`;
                            } else {
                                errorMsg += `<div style="color: #dc2626; font-weight: bold; font-size: 13px; margin-top: 4px;">No attempts remaining - account will be locked!</div>`;
                            }
                        }
                    } else if (remaining !== undefined && !isNaN(remaining)) {
                        // Fallback if only remaining_attempts is available
                        if (remaining > 0) {
                            errorMsg += `<div style="color: #ea580c; margin-top: 4px;">${remaining} attempt(s) remaining</div>`;
                        } else {
                            errorMsg += `<div style="color: #dc2626; margin-top: 4px;">No attempts remaining</div>`;
                        }
                    }
                    
                    // Ensure message is visible and styled
                    msg.innerHTML = errorMsg;
                    msg.className = 'mt-2 text-sm text-red-600';
                    msg.style.display = 'block';
                    msg.style.visibility = 'visible';
                    msg.style.opacity = '1';
                    
                    console.log('✅ Message displayed:', errorMsg);
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
            console.error('Login error:', error);
            msg.textContent = 'Network error: ' + (error.message || 'Please check your connection');
            msg.className = 'mt-2 text-sm text-red-600';
        }
    });
});
