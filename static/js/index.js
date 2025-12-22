// 1. Mobile Menu Toggle
function toggleMenu() {
    const menu = document.getElementById('mobile-menu');
    menu.classList.toggle('hidden');
}

// 2. Accessibility: Font Resizer
let currentScale = 1;
function resizeText(multiplier) {
    currentScale += multiplier;
    if (currentScale < 0.8) currentScale = 0.8;
    if (currentScale > 1.4) currentScale = 1.4;
    document.documentElement.style.setProperty('--text-scale', currentScale);
    
    // Add visual feedback
    const btn = event.target;
    btn.classList.add('scale-125');
    setTimeout(() => {
        btn.classList.remove('scale-125');
    }, 300);
}

// 3. Accessibility: High Contrast Mode
function toggleContrast() {
    document.body.classList.toggle('high-contrast');
    const dot = document.getElementById('contrast-dot');
    const btn = document.getElementById('contrast-toggle');
    
    if (document.body.classList.contains('high-contrast')) {
        dot.style.transform = 'translateX(16px)';
        btn.classList.remove('bg-gray-200');
        btn.classList.add('bg-brand-primary');
    } else {
        dot.style.transform = 'translateX(0)';
        btn.classList.add('bg-gray-200');
        btn.classList.remove('bg-brand-primary');
    }
}

// 4. Accessibility: Toggle Menu
function toggleAccessMenu() {
    const panel = document.getElementById('access-panel');
    if(panel.classList.contains('hidden')) {
        panel.classList.remove('hidden');
        setTimeout(() => {
            panel.classList.remove('opacity-0', 'scale-95');
        }, 10);
    } else {
        panel.classList.add('opacity-0', 'scale-95');
        setTimeout(() => {
            panel.classList.add('hidden');
        }, 300);
    }
}

// 5. Accordion Functionality
function toggleAccordion(id) {
    const content = document.getElementById(`content-${id}`);
    const icon = document.getElementById(`icon-${id}`);
    
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        icon.innerText = '-';
        icon.classList.add('rotate-180');
    } else {
        content.classList.add('hidden');
        icon.innerText = '+';
        icon.classList.remove('rotate-180');
    }
}

// 6. Intersection Observer for Animations
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('active');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.reveal').forEach(el => {
    observer.observe(el);
});

// 7. Navbar scroll effect
window.addEventListener('scroll', function() {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('shadow-lg', 'bg-white/95');
        navbar.classList.remove('bg-transparent');
    } else {
        navbar.classList.remove('shadow-lg', 'bg-white/95');
    }
});

// 8. Add hover sound effects (optional)
document.querySelectorAll('a, button').forEach(element => {
    element.addEventListener('mouseenter', function() {
        // Could add subtle sound effect here for accessibility
    });
});

// 9. Animate stats on scroll
const stats = document.querySelectorAll('.reveal .text-4xl, .reveal .text-5xl');
stats.forEach(stat => {
    const originalText = stat.textContent;
    const targetNumber = parseInt(originalText.replace(/[^0-9]/g, ''));
    
    if (!isNaN(targetNumber)) {
        stat.textContent = '0';
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    let current = 0;
                    const increment = targetNumber / 50;
                    const timer = setInterval(() => {
                        current += increment;
                        if (current >= targetNumber) {
                            clearInterval(timer);
                            stat.textContent = originalText;
                        } else {
                            stat.textContent = Math.floor(current).toString();
                        }
                    }, 30);
                    observer.unobserve(stat);
                }
            });
        });
        
        observer.observe(stat);
    }
});
