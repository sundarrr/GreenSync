from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='images/', default='user.png',null=True, blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=False)

    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name

    @property
    def get_id(self):
        return self.user.id

    def __str__(self):
        return self.user.username


class Product(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=40)
    product_image = models.ImageField(upload_to='product_image/', null=True, blank=True)
    price = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    description = models.CharField(max_length=40)

    def __str__(self):
        return self.name
        
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category_image = models.ImageField(upload_to='category_image/', null=True, blank=True)

    def __str__(self):
        return self.name

class Orders(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Order Confirmed', 'Order Confirmed'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
    )
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, null=True)
    products = models.ManyToManyField(Product, blank=True)
    #product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True)
    email = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=500, null=True)
    mobile = models.CharField(max_length=20, null=True)
    order_date = models.DateField(auto_now_add=True, null=True)
    status = models.CharField(max_length=50, null=True, choices=STATUS)


#QA Forum models
class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Customer, on_delete=models.CASCADE)
    file = models.FileField(upload_to='files/', blank=True, null=True)

    def get_absolute_url(self):
        #return self.title
        return reverse('post-detail', kwargs={'pk': self.pk}) #Riya Updated

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(Customer, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author} on {self.post}'
