// JavaScript with refresh trigger checking
console.log('JavaScript file loaded');
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    console.log('Current path:', window.location.pathname);
    
    // Only form loading states
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
    
    // Check for new bookings
    if (window.location.pathname === '/admin/dashboard') {
        console.log('Dashboard detected, setting up refresh checker');
        let lastCheck = Date.now() / 1000;
        console.log('Starting refresh checker, lastCheck:', lastCheck);
        setInterval(() => {
            fetch(`/api/check-refresh?last_check=${lastCheck}`)
                .then(response => response.json())
                .then(data => {
                    console.log('Refresh check result:', data);
                    if (data.refresh_needed) {
                        console.log('New booking detected, refreshing...');
                        window.location.reload();
                    }
                    lastCheck = data.timestamp;
                })
                .catch(error => {
                    if (!error.message.includes('message channel closed')) {
                        console.log('Refresh check failed:', error);
                    }
                });
        }, 1000);
    }
});