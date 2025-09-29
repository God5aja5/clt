// Baign Mart JavaScript utilities

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Add to cart animation
function addToCartAnimation(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check"></i> Added!';
    button.classList.add('bg-green-600');
    button.classList.remove('bg-blue-600');
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.classList.add('bg-blue-600');
        button.classList.remove('bg-green-600');
    }, 2000);
}

// Quantity controls for cart
function increaseQuantity(productId) {
    const input = document.getElementById(`qty-${productId}`);
    let value = parseInt(input.value) || 0;
    input.value = value + 1;
    updateCartQuantity(productId, input.value);
}

function decreaseQuantity(productId) {
    const input = document.getElementById(`qty-${productId}`);
    let value = parseInt(input.value) || 1;
    if (value > 1) {
        input.value = value - 1;
        updateCartQuantity(productId, input.value);
    }
}

function updateCartQuantity(productId, quantity) {
    // Update quantity via AJAX to avoid page refresh
    fetch("/cart/update_quantity", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `product_id=${productId}&quantity=${quantity}`
    }).then(response => {
        if (response.ok) {
            location.reload(); // Simple approach: reload page after update
        }
    });
}

// Image carousel functionality for product detail
function initializeImageCarousel() {
    const thumbnailImages = document.querySelectorAll('.thumbnail-image');
    const mainImage = document.getElementById('mainImage');
    
    if (!mainImage) return;
    
    thumbnailImages.forEach(img => {
        img.addEventListener('click', function() {
            mainImage.src = this.getAttribute('data-full');
            
            // Remove active class from all thumbnails
            thumbnailImages.forEach(thumb => {
                thumb.classList.remove('ring-2', 'ring-blue-500');
            });
            
            // Add active class to clicked thumbnail
            this.classList.add('ring-2', 'ring-blue-500');
        });
    });
    
    // Set first thumbnail as active by default
    if (thumbnailImages.length > 0) {
        thumbnailImages[0].classList.add('ring-2', 'ring-blue-500');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeImageCarousel();
});

// Form validation
function validateCheckoutForm() {
    const phoneInput = document.querySelector('input[name="phone_number"]');
    const telegramInput = document.querySelector('input[name="telegram_username"]');
    
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            // Remove non-digit characters to validate length
            const digitsOnly = this.value.replace(/\D/g, '');
            if (digitsOnly.length < 10 || digitsOnly.length > 15) {
                this.setCustomValidity('Phone number must be 10-15 digits');
            } else {
                this.setCustomValidity('');
            }
        });
    }
    
    if (telegramInput) {
        telegramInput.addEventListener('input', function() {
            const username = this.value.trim();
            if (username && !/^[a-zA-Z][a-zA-Z0-9_]{4,31}$/.test(username.replace('@', ''))) {
                this.setCustomValidity('Invalid Telegram username format');
            } else {
                this.setCustomValidity('');
            }
        });
    }
}

// Initialize form validation when checkout form is present
document.addEventListener('DOMContentLoaded', function () {
    if (document.querySelector('form[action="/checkout"]')) {
        validateCheckoutForm();
    }
});

// Toast notifications
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-6 py-4 rounded-lg shadow-lg text-white ${
        type === 'error' ? 'bg-red-500' : 
        type === 'success' ? 'bg-green-500' : 'bg-blue-500'
    } z-50`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.transition = 'opacity 0.5s';
        toast.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 500);
    }, 3000);
}