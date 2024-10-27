// JavaScript para manejar el comportamiento de los modales
document.addEventListener('DOMContentLoaded', function () {
    const productButtons = document.querySelectorAll('[data-bs-toggle="modal"]');

    productButtons.forEach(button => {
        button.addEventListener('click', function () {
            // Aquí puedes agregar lógica para cargar datos del producto en el modal
            const productCard = button.closest('.product-card');
            const productTitle = productCard.querySelector('.card-title').innerText;
            const productPrice = productCard.querySelector('.text-success').innerText;
            const productDescription = productCard.querySelector('.card-text').innerText;

            // Aquí puedes usar Bootstrap para actualizar el modal
            const modalTitle = document.querySelector('#productModal .modal-title');
            const modalBody = document.querySelector('#productModal .modal-body');

            modalTitle.innerText = productTitle;
            modalBody.innerHTML = `
                <p>${productDescription}</p>
                <h5>Precio: ${productPrice}</h5>
            `;
        });
    });
});
