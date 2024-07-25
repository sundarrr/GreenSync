from django import forms
from django.contrib.auth.models import User
from . import models
from .models import Product, Category, Comment, Customer
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

class CustomerUserForm(forms.ModelForm):  # This class is used to create a form for CustomerUser
    class Meta: 
        model = User
        fields = ['first_name', 'email','last_name', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput(),
            'email': forms.EmailInput()
        }  # This is a dictionary that contains the widgets for the form fields


class CustomerForm(forms.ModelForm): # This class is used to create a form for Customer
    security_question = forms.ChoiceField(choices=Customer.SECURITY_QUESTION_CHOICES)
    security_answer = forms.CharField(max_length=255, widget=forms.TextInput())
    class Meta: # This class is used to create a form for Customer
        model = models.Customer
        fields = ['address', 'email','mobile', 'profile_pic', 'security_question', 'security_answer', ]
        widgets = {
            'email': forms.EmailInput()
        } # This is a dictionary that contains the widgets for the form fields

class UsernameForm(forms.Form): # create a form for Username
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))

class SecurityQuestionForm(forms.Form): # create a form for SecurityQuestion
    security_answer = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Answer'}))

class SetNewPasswordForm(SetPasswordForm): # This class is used to create a form for SetNewPassword
    new_password1 = forms.CharField(max_length=128, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}))
    new_password2 = forms.CharField(max_length=128, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}))

class ProductForm(forms.ModelForm): # This class is used to create a form for Product
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'product_image', 'category', 'stock']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all() # This line of code is used to get all the categories

class AddressForm(forms.Form): # This class is used to create a form for Address
    Email = forms.EmailField()
    Mobile = forms.IntegerField()
    Address = forms.CharField(max_length=500)

class OrderForm(forms.ModelForm):
    class Meta: # This class is used to create a form for Order
        model = models.Order
        fields = ['status']

class CategoryForm(forms.ModelForm):
    class Meta: # This class is used to create a form for Category
        model = Category
        fields = ['name', 'description', 'category_image']

class CommentForm(forms.ModelForm):
    class Meta: # This class is used to create a form for Comment
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4, 
                'cols': 50,
                'style': 'resize:none; width: 300px;',  
                'class': 'form-control'
            })} # This is a dictionary that contains the widgets for the form fields

class ReplyForm(forms.ModelForm):
    class Meta: # This class is used to create a form for Reply
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'cols': 50,
                'style': 'resize:none; width: 300px;',
                'class': 'form-control'
            })} # This is a dictionary that contains the widgets for the form fields