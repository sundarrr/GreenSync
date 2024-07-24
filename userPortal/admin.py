from django.contrib import admin

from adminPortal.models import EventRegistration
from .models import Customer, Product, Order, Post, Comment, Category, Cart, CartProduct, Item

class CustomerAdmin(admin.ModelAdmin):
    pass


admin.site.register(Customer, CustomerAdmin)


class ProductAdmin(admin.ModelAdmin):
    pass


admin.site.register(Product, ProductAdmin)


class OrderAdmin(admin.ModelAdmin):
    pass


admin.site.register(Order, OrderAdmin)


admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Cart)
admin.site.register(CartProduct)

class CategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Category, CategoryAdmin)
admin.site.register(Item)