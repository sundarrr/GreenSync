from django.db import models
from django.contrib.auth.models import User, Group
from django.urls import reverse
from adminPortal.models import Event, EventRegistrationManager


class Admin(models.Model): # This class is used to create a model for Admin
    user = models.OneToOneField(User, on_delete=models.CASCADE) # OneToOneField is used to create a one-to-one relationship between two models
    def __str__(self): # This method returns the string representation of the object 
        return self.user.username

class Customer(models.Model): # This class is used to create a model for Customer
    SECURITY_QUESTION_CHOICES = [
        ('pet', 'What was the name of your first pet?'),
        ('town', 'What is the name of the town where you were born?'),
        ('car', 'What was the model of your first car?'),
        ('book', 'What is your favorite book?')
    ] # This is a list of tuples that contains the security questions and their choices
    user = models.OneToOneField(User, on_delete=models.CASCADE) # OneToOneField is used to create a one-to-one relationship between two models
    profile_pic = models.ImageField(upload_to='images/', default='user.png', null=True, blank=True)
    address = models.CharField(max_length=40) # This field is used to store the address of the customer
    email = models.EmailField(null=False, blank=False, default='admin@ecogreenmart.in')
    mobile = models.CharField(max_length=20, null=False) # This field is used to store the mobile number of the customer
    security_question = models.CharField(max_length=255, choices=SECURITY_QUESTION_CHOICES, default='What was the name of your first pet?')
    security_answer = models.CharField(max_length=255, default='Robin') # This field is used to store the security answer of the customer

    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name

    @property
    def get_id(self):
        return self.user.id

    @property
    def get_email(self):
        return self.user.email

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        super(Customer, self).save(*args, **kwargs)
        customer_group, created = Group.objects.get_or_create(name='CUSTOMER') # This line of code is used to get or create a group named 'CUSTOMER'
        self.user.groups.add(customer_group) # This line of code is used to add the customer to the 'CUSTOMER' group

class Product(models.Model): # This class is used to create a model for Product
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=40) # This field is used to store the name of the product
    product_image = models.ImageField(upload_to='product_image/', null=True, blank=True) # This field is used to store the image of the product
    price = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    description = models.CharField(max_length=40)
    stock = models.IntegerField(default=0) # This field is used to store the stock of the product

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category_image = models.ImageField(upload_to='category_image/', null=True, blank=True) # This field is used to store the image of the category

    def __str__(self):
        return self.name

class Cart(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, null=True)
    products = models.ManyToManyField(Product, through='CartProduct', blank=True) # This field is used to store the products in the cart
    email = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=500, null=True)
    mobile = models.CharField(max_length=20, null=True)
    order_date = models.DateField(auto_now_add=True, null=True) # This field is used to store the order date of the cart

class CartProduct(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

class Item(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE) # This field is used to store the product in the cart
    quantity = models.IntegerField(default=1)

class Order(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Order Confirmed', 'Order Confirmed'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered')
    ) # This is a list of tuples that contains the status of the order and their choices
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, null=True)
    items= models.ManyToManyField(Item) # This field is used to store the items in the order
    email = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=500, null=True)
    mobile = models.CharField(max_length=20, null=True)
    order_date = models.DateField(auto_now_add=True, null=True) # This field is used to store the order date of the order
    status = models.CharField(max_length=50, null=True, choices=STATUS)

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField() # This field is used to store the content of the post
    date_posted = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Customer, on_delete=models.CASCADE) # This field is used to store the author of the post
    file = models.FileField(upload_to='files/', blank=True, null=True) # This field is used to store the file in the post

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk}) # This method returns the absolute URL of the post

class Comment(models.Model): # This class is used to create a model for Comment
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(Customer, on_delete=models.CASCADE)
    content = models.TextField() # This field is used to store the content of the comment
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True) # This field is used to store the date and time when the comment was created

    def __str__(self):
        return f'Comment by {self.author} on {self.post}'