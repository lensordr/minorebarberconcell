// JavaScript with animations and refresh checking
console.log('JavaScript file loaded');

// Animation Functions
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('hide');
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

function animateRevenue(element) {
    element.classList.add('animate');
    setTimeout(() => element.classList.remove('animate'), 800);
}

function animateNewAppointment(element) {
    element.classList.add('new-appointment');
    setTimeout(() => element.classList.remove('new-appointment'), 1000);
}

function animateStatusChange(element) {
    element.classList.add('status-change');
    setTimeout(() => element.classList.remove('status-change'), 600);
}

function animateButton(button, originalText) {
    button.classList.add('loading');
    button.disabled = true;
    setTimeout(() => {
        button.classList.remove('loading');
        button.disabled = false;
        button.textContent = originalText;
    }, 1000);
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    console.log('Current path:', window.location.pathname);
    
    // Animate elements on page load
    const appointmentItems = document.querySelectorAll('.appointment-item');
    appointmentItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.1}s`;
        item.classList.add('fadeIn');
    });
    
    // Form loading states with animations
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.textContent;
                animateButton(submitBtn, originalText);
            }
        });
    });
    
    // Animate checkout buttons
    const checkoutBtns = document.querySelectorAll('.btn-checkout');
    checkoutBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const appointmentItem = this.closest('.appointment-item');
            if (appointmentItem) {
                animateStatusChange(appointmentItem);
                showNotification('Appointment completed! 💰', 'success');
                
                // Animate revenue update
                setTimeout(() => {
                    const revenueAmounts = document.querySelectorAll('.revenue-amount');
                    revenueAmounts.forEach(amount => animateRevenue(amount));
                }, 300);
            }
        });
    });
    
    // Animate cancel buttons
    const cancelBtns = document.querySelectorAll('.btn-cancel');
    cancelBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const appointmentItem = this.closest('.appointment-item');
            if (appointmentItem) {
                animateStatusChange(appointmentItem);
                showNotification('Appointment cancelled', 'error');
            }
        });
    });
    
    // Check for new bookings with animation
    if (window.location.pathname.includes('/admin/dashboard')) {
        console.log('Dashboard detected, setting up refresh checker');
        let lastCheck = Date.now() / 1000;
        console.log('Starting refresh checker, lastCheck:', lastCheck);
        
        const refreshInterval = setInterval(() => {
            fetch(`/api/check-refresh?last_check=${lastCheck}`)
                .then(response => response.json())
                .then(data => {
                    console.log('Refresh check result:', data);
                    
                    // Stop polling if outside business hours
                    if (data.business_hours === false) {
                        console.log('Outside business hours - stopping refresh checker');
                        clearInterval(refreshInterval);
                        showNotification('Dashboard inactive outside business hours', 'error');
                        return;
                    }
                    
                    if (data.refresh_needed) {
                        console.log('New booking detected, refreshing...');
                        
                        // Add loading animation
                        const dashboard = document.querySelector('.dashboard');
                        if (dashboard) {
                            dashboard.classList.add('refreshing');
                        }
                        
                        showNotification('New appointment booked! 📅', 'success');
                        
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
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
    
    // Success page animation
    if (window.location.pathname.includes('/success')) {
        const successIcon = document.querySelector('.success-icon');
        const successMessage = document.querySelector('.success-message');
        
        if (successIcon) {
            setTimeout(() => {
                successIcon.style.animation = 'checkmark 0.8s ease-in-out';
            }, 200);
        }
        
        showNotification('Appointment booked successfully! ✅', 'success');
    }
    
    // Form validation animations
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('invalid', function() {
            this.parentElement.classList.add('error');
            setTimeout(() => {
                this.parentElement.classList.remove('error');
            }, 500);
        });
        
        input.addEventListener('input', function() {
            if (this.validity.valid) {
                this.parentElement.classList.add('success');
                setTimeout(() => {
                    this.parentElement.classList.remove('success');
                }, 300);
            }
        });
    });
});