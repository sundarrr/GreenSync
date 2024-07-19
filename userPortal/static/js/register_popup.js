document.addEventListener('DOMContentLoaded', function () {
    const registerButtons = document.querySelectorAll('.register-event');
    const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
    const eventNameSpan = document.getElementById('register-event-name');
    const confirmRegisterButton = document.getElementById('confirm-register');

    registerButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            const eventName = button.getAttribute('data-event-name');
            const eventId = button.getAttribute('data-event-id');
            eventNameSpan.textContent = eventName;
            confirmRegisterButton.href = `/register_event/${eventId}/`;
            registerModal.show();
        });
    });
});
