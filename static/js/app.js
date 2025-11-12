// Simple JavaScript for enhanced UX
document.addEventListener('DOMContentLoaded', function() {
    // Show last refresh time
    if (window.location.pathname === '/admin/dashboard') {
        const now = new Date().toLocaleTimeString();
        console.log('Dashboard loaded at:', now);
    }
    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.textContent = 'Loading...';
                submitBtn.disabled = true;
            }
        });
    });
    
    // Manual refresh only - no auto refresh
    if (window.location.pathname === '/admin/dashboard') {
        // Add manual refresh button functionality if needed
        console.log('Dashboard loaded - manual refresh only');
    }
});