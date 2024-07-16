from django.contrib import admin
from mapbox_location_field.admin import MapAdmin

from .models import (
    EventCategory,
    Event,
    EventMember,
    EventUserWishList,
    EventRegistration
)

class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'registration_date')
    list_filter = ('event', 'user', 'registration_date')
    search_fields = ('event__name', 'user__username')

admin.site.register(EventCategory)
admin.site.register(Event, MapAdmin)
admin.site.register(EventMember)
admin.site.register(EventUserWishList)
admin.site.register(EventRegistration, EventRegistrationAdmin)