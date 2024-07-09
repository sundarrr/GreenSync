from django.contrib import admin
from mapbox_location_field.admin import MapAdmin

from .models import (
    EventCategory,
    Event,
    # JobCategory,
    # EventJobCategoryLinking,
    EventMember,
    EventUserWishList
)

admin.site.register(EventCategory)
admin.site.register(Event, MapAdmin)
admin.site.register(EventMember)
admin.site.register(EventUserWishList)
