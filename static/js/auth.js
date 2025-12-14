// Simple tab/view switching
const tabs = {
    login: document.getElementById('tab-login'),
    register: document.getElementById('tab-register'),
    forgot: document.getElementById('tab-forgot'),
};
const views = {
    login: document.getElementById('view-login'),
    register: document.getElementById('view-register'),
    forgot: document.getElementById('view-forgot'),
};

function setActiveTab(name) {
    Object.keys(views).forEach((key) => {
        views[key].classList.toggle('hidden', key !== name);
    });
    Object.keys(tabs).forEach((key) => {
        const isActive = key === name;
        tabs[key].classList.toggle('text-slate-900', isActive);
        tabs[key].classList.toggle('text-slate-500', !isActive);
        tabs[key].classList.toggle('border-emerald-500', isActive);
        tabs[key].classList.toggle('border-transparent', !isActive);
    });
}

tabs.login.addEventListener('click', () => setActiveTab('login'));
tabs.register.addEventListener('click', () => setActiveTab('register'));
tabs.forgot.addEventListener('click', () => setActiveTab('forgot'));

document.getElementById('link-to-register').addEventListener('click', () => setActiveTab('register'));
document.getElementById('link-to-login').addEventListener('click', () => setActiveTab('login'));
document.getElementById('link-to-login-from-forgot').addEventListener('click', () => setActiveTab('login'));

// Default: show login
setActiveTab('login');

// Use relative path so it works in any environment (k8s, different domains, etc.)
const API_BASE = '/api/auth';

async function handleForm(formId, url, method, bodyBuilder, msgId) {
    const form = document.getElementById(formId);
    const msg = document.getElementById(msgId);
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        msg.textContent = 'Loading...';
        msg.className = 'mt-2 text-sm text-slate-600';
        try {
            const res = await fetch(API_BASE + url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bodyBuilder()),
            });
            const data = await res.json();
            if (!res.ok) {
                msg.textContent = data.message || 'Request failed';
                msg.className = 'mt-2 text-sm text-red-600';
            } else {
                msg.textContent = data.message || 'Success';
                msg.className = 'mt-2 text-sm text-emerald-600';
                // OTP is sent via email, not displayed in UI
            }
        } catch (err) {
            msg.textContent = 'Network error';
            msg.className = 'mt-2 text-sm text-red-600';
        }
    });
}

handleForm('login-form', '/login', 'POST', () => ({
    email: document.getElementById('login-email').value,
    password: document.getElementById('login-password').value,
}), 'login-msg');

// FIXED: Using new unique IDs for the registration form in the tabbed view
handleForm('tab-register-form', '/register', 'POST', () => ({
    email: document.getElementById('tab-register-email').value,
    password: document.getElementById('tab-register-password').value,
}), 'tab-register-msg');

handleForm('forgot-form', '/forgot', 'POST', () => ({
    email: document.getElementById('forgot-email').value,
}), 'forgot-msg');

handleForm('reset-form', '/reset', 'POST', () => ({
    email: document.getElementById('reset-email').value,
    otp: document.getElementById('reset-code').value,  // Using 'otp' for consistency with backend
    new_password: document.getElementById('reset-password').value,
}), 'reset-msg');
