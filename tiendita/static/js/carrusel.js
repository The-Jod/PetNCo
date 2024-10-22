document.addEventListener('DOMContentLoaded', () => {
    const features = document.querySelectorAll('.feature');

    const options = {
        root: null, // Vista del viewport
        rootMargin: '0px',
        threshold: 0.1 // Al menos el 10% visible
    };

    const callback = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible'); // Agregar clase para animar
                observer.unobserve(entry.target); // Dejar de observar una vez visible
            }
        });
    };

    const observer = new IntersectionObserver(callback, options);

    features.forEach(feature => {
        observer.observe(feature); // Observar cada elemento
    });
});
