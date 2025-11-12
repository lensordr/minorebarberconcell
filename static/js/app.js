// Clean JavaScript - NO AUTO REFRESH
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded - no refresh');
    
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
});