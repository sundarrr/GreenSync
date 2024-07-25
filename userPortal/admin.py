from django.contrib import admin

from adminPortal.models import EventRegistration
from .models import Customer, Product, Order, Post, Comment, Category, Cart, CartProduct, Item

class CustomerAdmin(admin.ModelAdmin): # This class is used to create a model for CustomerAdmin
    pass

admin.site.register(Customer, CustomerAdmin)

class ProductAdmin(admin.ModelAdmin): # This class is used to create a model for ProductAdmin
    pass

admin.site.register(Product, ProductAdmin)

class OrderAdmin(admin.ModelAdmin): # This class is used to create a model for OrderAdmin
    pass

admin.site.register(Order, OrderAdmin) # Registering the Order model 
admin.site.register(Post) # Registering the Post model
admin.site.register(Comment) # Registering the Comment model
admin.site.register(Cart) # Registering the Cart model
admin.site.register(CartProduct) # Registering the CartProduct model

class CategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Category, CategoryAdmin) # Registering the Category model
admin.site.register(Item) # Registering the Item model