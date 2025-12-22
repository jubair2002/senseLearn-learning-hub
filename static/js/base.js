// User dropdown toggle
document.getElementById('user-menu-button')?.addEventListener('click', function() {
    const dropdown = document.getElementById('user-dropdown');
    dropdown.classList.toggle('hidden');
});

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('user-dropdown');
    const button = document.getElementById('user-menu-button');
    
    if (dropdown && !dropdown.contains(event.target) && button && !button.contains(event.target)) {
        dropdown.classList.add('hidden');
    }
});
