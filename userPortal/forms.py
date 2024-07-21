from django import forms
from django.contrib.auth.models import User
from . import models
from .models import Product, Category, Comment, Customer
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm


class CustomerUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'email','last_name', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput(),
            'email': forms.EmailInput()
        }


class CustomerForm(forms.ModelForm):
    security_question = forms.ChoiceField(choices=Customer.SECURITY_QUESTION_CHOICES)
    security_answer = forms.CharField(max_length=255, widget=forms.TextInput())
    class Meta:
        model = models.Customer
        fields = ['address', 'email','mobile', 'profile_pic', 'security_question', 'security_answer', ]
        widgets = {
            'email': forms.EmailInput()
        }

class UsernameForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
class SecurityQuestionForm(forms.Form):
    security_answer = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Answer'}))

class SetNewPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(max_length=128, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}))
    new_password2 = forms.CharField(max_length=128, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}))

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'product_image', 'category', 'stock']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()

# address of shipment
class AddressForm(forms.Form):
    Email = forms.EmailField()
    Mobile = forms.IntegerField()
    Address = forms.CharField(max_length=500)


# for updating status of order
class OrderForm(forms.ModelForm):
    class Meta:
        model = models.Order
        fields = ['status']


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'category_image']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,  # Adjust the number of rows
                'cols': 50,  # Adjust the number of columns
                'style': 'resize:none; width: 300px;',  # Set a specific width
                'class': 'form-control'  # Add Bootstrap class for styling
            })}

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,  # Adjust the number of rows
                'cols': 50,  # Adjust the number of columns
                'style': 'resize:none; width: 300px;',  # Set a specific width
                'class': 'form-control'  # Add Bootstrap class for styling
            })}