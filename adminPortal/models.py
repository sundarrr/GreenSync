import datetime

# Importing necessary Django models and utilities
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.urls import reverse
from mapbox_location_field.models import LocationField

# Defining the EventCategory model
class EventCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Category name
    code = models.CharField(max_length=6, unique=True)  # Category code
    image = models.ImageField(upload_to='userPortal/static/event_category/')  # Category image
    created_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_user')  # User who created the category
    updated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_user')  # User who updated the category
    created_date = models.DateField(auto_now_add=True)  # Date when the category was created
    updated_date = models.DateField(auto_now_add=True)  # Date when the category was updated

    def __str__(self):
        return self.name  # Return the name of the category as its string representation


# Defining the Event model
class Event(models.Model):
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE)  # Category of the event
    name = models.CharField(max_length=255, unique=True)  # Name of the event
    uid = models.PositiveIntegerField(unique=True)  # Unique ID of the event
    description = models.TextField()  # Description of the event
    scheduled_status = models.CharField(max_length=25, choices=[
        ('yet to scheduled', 'Yet to Scheduled'),
        ('scheduled', 'Scheduled')
    ])  # Scheduled status of the event
    venue = models.CharField(max_length=255)  # Venue of the event
    start_date = models.DateField()  # Start date of the event
    end_date = models.DateField()  # End date of the event
    location = LocationField()  # Location of the event
    maximum_attende = models.PositiveIntegerField()  # Maximum number of attendees
    created_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='event_created_user')  # User who created the event
    updated_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='event_updated_user')  # User who updated the event
    created_date = models.DateField(auto_now_add=True)  # Date when the event was created
    updated_date = models.DateField(auto_now_add=True)  # Date when the event was updated
    status = models.CharField(choices=[
        ('disabled', 'Disabled'),
        ('active', 'Active'),
        ('deleted', 'Deleted'),
        ('time out', 'Time Out'),
        ('completed', 'Completed'),
        ('cancel', 'Cancel')
    ], max_length=10)  # Status of the event

    def __str__(self):
        return self.name  # Return the name of the event as its string representation

    def get_absolute_url(self):
        return reverse('event-list')  # Return the absolute URL for the event list

    def created_updated(model, request):
        obj = model.objects.latest('pk')  # Get the latest object of the model
        if obj.created_by is None:
            obj.created_by = request.user  # Set the created_by field to the request user if not set
        obj.updated_by = request.user  # Set the updated_by field to the request user
        obj.save()  # Save the object

    @property
    def registration_count(self):
        return self.eventregistrations.count()  # Return the count of event registrations


# Manager for EventRegistration to add custom query methods
class EventRegistrationManager(models.Manager):
    def registrations_last_week(self):
        last_week = datetime.datetime.now() - datetime.timedelta(days=7)  # Calculate the date a week ago
        return self.filter(registration_date__gte=last_week).count()  # Return the count of registrations in the last week

    def registration_details(self):
        return self.values('event__name', 'event__id').annotate(count=Count('id')).order_by('-count')  # Return registration details


# Defining the EventRegistration model
class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='eventregistrations')  # Event associated with the registration
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User who registered for the event
    registration_date = models.DateTimeField(auto_now_add=True)  # Date when the registration was created

    objects = EventRegistrationManager()  # Use the custom manager for EventRegistration

    class Meta:
        unique_together = ['event', 'user']  # Ensure a user can register for an event only once

    def __str__(self):
        return f"{self.user.username} - {self.event.name}"  # Return a string representation of the registration


# Defining the EventImage model
class EventImage(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE)  # Event associated with the image
    image = models.ImageField(upload_to='event_image/')  # Image for the event


# Defining the EventAgenda model
class EventAgenda(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)  # Event associated with the agenda
    session_name = models.CharField(max_length=120)  # Session name in the agenda
    speaker_name = models.CharField(max_length=120)  # Speaker name in the agenda
    start_time = models.TimeField()  # Start time of the session
    end_time = models.TimeField()  # End time of the session
    venue_name = models.CharField(max_length=255)  # Venue name for the session


# Defining the EventMember model
class EventMember(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)  # Event associated with the member
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)  # User who is a member of the event
    created_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='eventmember_created_user')  # User who created the membership
    updated_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='eventmember_updated_user')  # User who updated the membership
    created_date = models.DateField(auto_now_add=True)  # Date when the membership was created
    updated_date = models.DateField(auto_now_add=True)  # Date when the membership was updated
    status_choice = (
        ('disabled', 'Disabled'),
        ('active', 'Active'),
        ('deleted', 'Deleted'),
        ('blocked', 'Blocked'),
        ('completed', 'Completed'),
    )
    status = models.CharField(choices=status_choice, max_length=10)  # Status of the membership

    class Meta:
        unique_together = ['event', 'user']  # Ensure a user can be a member of an event only once

    def __str__(self):
        return str(self.user)  # Return a string representation of the membership

    def get_absolute_url(self):
        return reverse('join-event-list')  # Return the absolute URL for joining event list


# Defining the EventUserWishList model
class EventUserWishList(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)  # Event in the wish list
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)  # User who added the event to their wish list
    created_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='eventwishlist_created_user')  # User who created the wish list entry
    updated_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='eventwishlist_updated_user')  # User who updated the wish list entry
    created_date = models.DateField(auto_now_add=True)  # Date when the wish list entry was created
    updated_date = models.DateField(auto_now_add=True)  # Date when the wish list entry was updated
    status_choice = (
        ('disabled', 'Disabled'),
        ('active', 'Active'),
        ('deleted', 'Deleted'),
        ('blocked', 'Blocked'),
        ('completed', 'Completed'),
    )
    status = models.CharField(choices=status_choice, max_length=10)  # Status of the wish list entry

    class Meta:
        unique_together = ['event', 'user']  # Ensure a user can add an event to their wish list only once

    def __str__(self):
        return str(self.event)  # Return a string representation of the wish list entry

    def get_absolute_url(self):
        return reverse('event-wish-list')  # Return the absolute URL for the wish list


# Defining the UserCoin model
class UserCoin(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)  # User associated with the coin
    CHOICE_GAIN_TYPE = (
        ('event', 'Event'),
        ('others', 'Others'),
    )
    gain_type = models.CharField(max_length=6, choices=CHOICE_GAIN_TYPE)  # Type of gain
    gain_coin = models.PositiveIntegerField()  # Number of coins gained
    created_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='usercoin_created_user')  # User who created the coin entry
    updated_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='usercoin_updated_user')  # User who updated the coin entry
    created_date = models.DateField(auto_now_add=True)  # Date when the coin entry was created
    updated_date = models.DateField(auto_now_add=True)  # Date when the coin entry was updated
    status_choice = (
        ('disabled', 'Disabled'),
        ('active', 'Active'),
        ('deleted', 'Deleted'),
        ('blocked', 'Blocked'),
        ('completed', 'Completed'),
    )
    status = models.CharField(choices=status_choice, max_length=10)  # Status of the coin entry

    def __str__(self):
        return str(self.user)  # Return a string representation of the coin entry

    def get_absolute_url(self):
        return reverse('user-mark')  # Return the absolute URL for the user mark
