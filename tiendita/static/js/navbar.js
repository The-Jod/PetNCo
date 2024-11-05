// Inicialización de AOS
AOS.init({
    duration: 800,
    once: true
});

// Clase para manejar la navegación
class NavigationHandler {
    constructor() {
        this.navbar = document.getElementById('mainNav');
        this.lastScroll = 0;
        this.init();
    }

    init() {
        this.setupScrollListener();
        this.setupMobileMenu();
        this.setupNavLinks();
    }

    setupScrollListener() {
        window.addEventListener('scroll', () => {
            this.handleScroll();
        });
    }

    handleScroll() {
        const currentScroll = window.pageYOffset;

        // Ocultar/mostrar navbar al hacer scroll
        if (currentScroll > this.lastScroll && currentScroll > 100) {
            // Scrolling down
            this.navbar.style.transform = 'translateY(-100%)';
        } else {
            // Scrolling up
            this.navbar.style.transform = 'translateY(0)';
        }

        this.lastScroll = currentScroll;
    }

    setupMobileMenu() {
        const toggler = document.querySelector('.navbar-toggler');
        const menu = document.querySelector('.navbar-collapse');

        if (toggler && menu) {
            toggler.addEventListener('click', () => {
                menu.classList.contains('show')
                    ? this.closeMobileMenu(menu)
                    : this.openMobileMenu(menu);
            });
        }
    }

    openMobileMenu(menu) {
        menu.style.opacity = '0';
        menu.classList.add('show');
        setTimeout(() => {
            menu.style.opacity = '1';
        }, 10);
    }

    closeMobileMenu(menu) {
        menu.style.opacity = '0';
        setTimeout(() => {
            menu.classList.remove('show');
        }, 300);
    }

    setupNavLinks() {
        const links = document.querySelectorAll('.nav-link');

        links.forEach(link => {


            link.addEventListener('mouseleave', (e) => {
                const icon = e.currentTarget.querySelector('.nav-icon');
                if (icon) {
                    icon.style.transform = 'translateY(0) scale(1)';
                }
                link.style.background = 'transparent'; // Vuelve a fondo transparente
            });

            // Efecto click
            link.addEventListener('click', this.handleNavClick.bind(this));
        });
    }

    handleNavClick(e) {
        const icon = e.currentTarget.querySelector('.nav-icon');
        if (icon) {
            icon.classList.add('click-animation');
            setTimeout(() => {
                icon.classList.remove('click-animation');
            }, 500);
        }
    }
}

// Inicializar el manejador de navegación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    const navigation = new NavigationHandler();
});


document.addEventListener('DOMContentLoaded', () => {
    // Animación de elementos al hacer scroll
    const animatedElements = document.querySelectorAll('.feature, .card, .promotion-card, .category-item');

    const animationOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const animationCallback = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    };

    const animationObserver = new IntersectionObserver(animationCallback, animationOptions);

    animatedElements.forEach(element => {
        animationObserver.observe(element);
    });

    // Carrusel automático
    const carousel = document.querySelector('#heroCarousel');
    if (carousel) {
        const carouselInstance = new bootstrap.Carousel(carousel, {
            interval: 5000,
            pause: 'hover'
        });
    }

    // Lazy loading de imágenes
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    const lazyImageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('loading');
                lazyImageObserver.unobserve(img);
            }
        });
    });

    lazyImages.forEach(img => {
        lazyImageObserver.observe(img);
    });
});
