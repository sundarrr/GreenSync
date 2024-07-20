document.addEventListener('DOMContentLoaded', function () {
    const infoButtons = document.querySelectorAll('.fa-info-circle');
    const eventDetailsModal = new bootstrap.Modal(document.getElementById('eventDetailsModal'));
    const eventImage = document.getElementById('event-image');
    const eventNameSpan = document.getElementById('event-name');
    const eventDescription = document.getElementById('event-description');
    const eventVenue = document.getElementById('event-venue');
    const eventEndDate = document.getElementById('event-end-date');
    const eventMaxAttendees = document.getElementById('event-max-attendees');
    const eventMap = document.getElementById('event-map');
    let map;

    infoButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            const eventId = button.getAttribute('data-event-id');
            fetch(`/get_event_details/${eventId}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error(data.error);
                        return;
                    }
                    eventImage.src = data.image || '/path/to/default/image.jpg';
                    eventNameSpan.textContent = data.name;
                    eventDescription.innerHTML = data.description;
                    eventVenue.textContent = data.venue;
                    eventEndDate.textContent = data.end_date;
                    eventMaxAttendees.textContent = data.max_attendees;

                    // Initialize or update the map
                    if (map) {
                        map.remove();
                    }
                    const coords = data.location; // [lat, lng]
                    map = L.map(eventMap).setView([coords[0], coords[1]], 13);
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    }).addTo(map);
                    L.marker([coords[0], coords[1]]).addTo(map)
                        .bindPopup(data.name)
                        .openPopup();

                    eventDetailsModal.show();
                })
                .catch(error => console.error('Error fetching event details:', error));
        });
    });

    const registerButtons = document.querySelectorAll('.register-event');
    const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
    const registerEventNameSpan = document.getElementById('register-event-name');
    const confirmRegisterButton = document.getElementById('confirm-register');

    registerButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            const eventName = button.getAttribute('data-event-name');
            const eventId = button.getAttribute('data-event-id');
            registerEventNameSpan.textContent = eventName;
            confirmRegisterButton.href = `/register_event/${eventId}/`;
            registerModal.show();
        });
    });
});
