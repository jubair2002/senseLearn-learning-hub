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
            msg.textContent = data.message || 'Login failed';
            msg.className = 'mt-2 text-sm text-red-600';
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
