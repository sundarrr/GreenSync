document.addEventListener('DOMContentLoaded', function () {
    const cancelButtons = document.querySelectorAll('.cancel-registration');
    const cancelModal = new bootstrap.Modal(document.getElementById('cancelModal'));
    const eventNameSpan = document.getElementById('event-name');
    const confirmCancelButton = document.getElementById('confirm-cancel');

    cancelButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            const eventName = button.getAttribute('data-event-name');
            const eventId = button.getAttribute('data-event-id');
            eventNameSpan.textContent = eventName;
            confirmCancelButton.href = `/cancel_registration/${eventId}/`;
            cancelModal.show();
        });
    });
});
