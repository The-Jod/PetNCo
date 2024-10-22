$(document).ready(function () {
    const products = [
        { name: "PX Formula Adultos", price: 25000, category: "perros", image: "dog-food-1.jpg", discount: 10 },
        { name: "Tasty Gato Adulto", price: 20000, category: "gatos", image: "cat-food-1.jpg", discount: 5 },
        { name: "Collar para perro", price: 8000, category: "perros", image: "dog-collar.jpg", discount: 0 },
        { name: "Correa para perro", price: 9000, category: "perros", image: "dog-leash.jpg", discount: 0 },
        { name: "Juguete para gato", price: 5000, category: "gatos", image: "cat-toy.jpg", discount: 15 },
        { name: "Juguete para perro", price: 7000, category: "perros", image: "dog-toy.jpg", discount: 0 },
        { name: "Cama para gato", price: 25000, category: "gatos", image: "cat-bed.jpg", discount: 20 },
        { name: "Rascador para gato", price: 30000, category: "gatos", image: "cat-scratcher.jpg", discount: 0 }
    ];

    function renderProducts(filter = 'all') {
        const container = $('#products-container');
        container.empty();

        products.forEach(product => {
            if (filter === 'all' || product.category === filter) {
                const discountedPrice = product.price * (1 - product.discount / 100);
                const card = `
                    <div class="col-md-3 mb-4">
                        <div class="card product-card">
                            <img src="${product.image}" class="card-img-top" alt="${product.name}">
                            <div class="card-body">
                                <h5 class="card-title">${product.name}</h5>
                                <p class="card-text">
                                    ${product.discount > 0 ? `<del>$${product.price.toLocaleString()}</del> ` : ''}
                                    <strong>$${discountedPrice.toLocaleString()}</strong>
                                </p>
                                ${product.discount > 0 ? `<span class="badge bg-danger">-${product.discount}%</span>` : ''}
                                <button class="btn btn-primary mt-2">Agregar al carrito</button>
                            </div>
                        </div>
                    </div>
                `;
                container.append(card);
            }
        });
    }

    renderProducts();

    $('.filter-btn').click(function () {
        $('.filter-btn').removeClass('active');
        $(this).addClass('active');
        const filter = $(this).data('filter');
        renderProducts(filter);
    });

    $('.category-card').click(function () {
        const category = $(this).data('category');
        $(`button[data-filter="${category}"]`).click();
    });
});