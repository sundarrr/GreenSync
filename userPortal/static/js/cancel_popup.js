document.addEventListener('DOMContentLoaded', function () {
    const cancelButtons = document.querySelectorAll('.cancel-registration');
    const cancelModalElement = document.getElementById('cancelModal');
    const cancelModal = new bootstrap.Modal(cancelModalElement);
    const eventNameSpan = document.getElementById('cancel-event-name');
    const confirmCancelButton = document.getElementById('confirm-cancel');

    console.log('cancelButtons:', cancelButtons);
    console.log('cancelModalElement:', cancelModalElement);
    console.log('eventNameSpan:', eventNameSpan);
    console.log('confirmCancelButton:', confirmCancelButton);

    if (!cancelButtons.length || !cancelModalElement || !eventNameSpan || !confirmCancelButton) {
        console.error('Modal elements are not correctly set.');
        return;
    }

    cancelButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            const eventName = button.getAttribute('data-event-name');
            const eventId = button.getAttribute('data-event-id');
            console.log('eventName:', eventName);
            console.log('eventId:', eventId);
            eventNameSpan.textContent = eventName;
            confirmCancelButton.href = `/cancel_registration/${eventId}/`;
            cancelModal.show();
        });
    });
});
