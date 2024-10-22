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