function toggleSidebar() {
    const body = document.body;
    const icon = document.getElementById('toggle-icon');
    
    // Check current state and toggle class on body
    if (body.classList.contains('sidebar-expanded')) {
        body.classList.remove('sidebar-expanded');
        body.classList.add('sidebar-collapsed');
        // Change icon to 'expand'
        icon.classList.remove('fa-arrow-left');
        icon.classList.add('fa-arrow-right');
    } else {
        body.classList.remove('sidebar-collapsed');
        body.classList.add('sidebar-expanded');
        // Change icon to 'collapse'
        icon.classList.remove('fa-arrow-right');
        icon.classList.add('fa-arrow-left');
    }
}
