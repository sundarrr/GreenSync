from django.contrib.auth import authenticate, login, logout
from datetime import timezone

from django.contrib.auth import authenticate, login, user_logged_in
from django.db.models import Count
from django.dispatch import receiver
from django.shortcuts import render, redirect, reverse
from django.views.static import serve

from . import forms, models
from django.http import HttpResponseRedirect, HttpResponse
from .smtp import send_email
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
import io
from xhtml2pdf import pisa
from django.template.loader import get_template, render_to_string
from django.template import Context
from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, Comment, Customer, Admin, Product, Orders
from .forms import CategoryForm, ReplyForm, CommentForm
from .models import Category, User, Cart, CartProduct
from .forms import CategoryForm,UsernameForm, SecurityQuestionForm, SetNewPasswordForm
from adminPortal.models import Event, EventCategory, EventRegistration

# QA Forum
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Post
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.db.models import Q

from django.http.response import (
    JsonResponse
)

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)


# def home_view(request):
#     products = Product.objects.all()
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         counter = product_ids.split('|')
#         product_count_in_cart = len(set(counter))
#     else:
#         product_count_in_cart = 0
#     if request.user.is_authenticated:
#         return HttpResponseRedirect('customer-home')
#     return render(request, 'ecom/v2/home/index.html', {'products': products, 'product_count_in_cart': product_count_in_cart})

def home_view(request):
    try:
        products = Product.objects.all()

        print(f"user {request.user.is_authenticated}")
        if request.user.is_authenticated:
            try:
                cart = get_cart(request)
                product_count_in_cart = cart['product_count_in_cart']
            except Exception as e:
                product_count_in_cart = 0
        else:
            product_count_in_cart = 0

        if request.user.is_authenticated:
            return HttpResponseRedirect('customer-home')
        else:
            return HttpResponseRedirect('dashboard')
        # return render(request, 'ecom/v2/home/index.html',
        #               {'products': products, 'product_count_in_cart': product_count_in_cart})
    except Exception as e:
        print(e)
        return HttpResponseRedirect('dashboard')


def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    if event.registration_count >= event.maximum_attende:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': "This event is full. Registration is not possible."})
        else:
            messages.error(request, "This event is full. Registration is not possible.")
            return redirect('events')

    registration, created = EventRegistration.objects.get_or_create(event=event, user=user)
    if created:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            send_email(user.email,
                       'Event Registration Successful',
                       f'Hi {user.username},<br><br>You have successfully registered for the {event.name} event.<br><br>Regards,<br>EcoGreenSmart Team')
            return JsonResponse({'success': True, 'event_name': event.name})
        else:
            messages.success(request, f"You have successfully registered for {event.name} event.")
            send_email(user.email,
                       'Event Registration Successful',
                       f'Hi {user.username},<br><br>You have successfully registered for the {event.name} event.<br><br>Regards,<br>EcoGreenSmart Team')
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f"You are already registered for {event.name} event."})
        else:
            messages.info(request, f"You are already registered for {event.name} event.")

    return redirect('events')

@login_required
def cancel_registration(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    try:
        registration = EventRegistration.objects.get(event=event, user=user)
        registration.delete()
        messages.success(request, f"You have successfully canceled your registration for {event.name} event.")
    except EventRegistration.DoesNotExist:
        messages.error(request, "You are not registered for this event.")

    return redirect('events')


def event_view(request):
    query = request.GET.get('query', '')
    category = request.GET.get('category', '')
    events = Event.objects.all()
    registrations = EventRegistration.objects.filter(user=request.user) if request.user.is_authenticated else []
    registered_event_ids = registrations.values_list('event_id', flat=True)
    event_statuses = {event.id: 'full' if event.registration_count >= event.maximum_attende else 'open' for event in
                      events}

    events = Event.objects.all()
    if query:
        events = events.filter(name__icontains=query)
    if category:
        events = events.filter(category__name=category)
    print("events", events)
    categories = EventCategory.objects.all()

    context = {
        'events': events,
        'categories': categories,
        'registered_event_ids': registered_event_ids,
        'event_statuses': event_statuses,
    }
    return render(request, 'ecom/v2/home/events.html', context)


def autosuggest_view(request):
    query = request.GET.get('query', '')
    suggestions = []
    events = Event.objects.filter(name__icontains=query)
    suggestions = [event.name for event in events]

    return JsonResponse(suggestions, safe=False)

def get_event_details(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
        coords = event.location if isinstance(event.location, (list, tuple)) else event.location.coords
        data = {
            'name': event.name,
            'description': event.description,
            'venue': event.venue,
            'location': coords,
            'end_date': event.end_date.strftime('%Y-%m-%d'),
            'max_attendees': event.maximum_attende,
            'image': event.category.image.url if event.category and event.category.image else ''
        }
        return JsonResponse(data)
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'})

@login_required(login_url='adminlogin')
def adminclick_view(request):
    return HttpResponseRedirect('admin-dashboard')


def customer_signup_view(request):
    userForm = forms.CustomerUserForm()
    customerForm = forms.CustomerForm()
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST)
        customerForm = forms.CustomerForm(request.POST, request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customer = customerForm.save(commit=False)
            customer.user = user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
            send_email(user.email, 'Registration Successful in EcoGreenSmart',
                       f'Hi {user.first_name}, <br><br> Thank you for registering with EcoGreenSmart. '
                       f'<br><br> Regards, <br> EcoGreenSmart Team')
        return HttpResponseRedirect('customerlogin')
    # return render(request,'ecom/customersignup.html',context=mydict)
    return render(request, 'ecom/v2/signup/customer_signup.html', context=mydict)


def forgot_password(request):
    if request.method == 'POST':
        form = UsernameForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = User.objects.get(username=username)
                customer = Customer.objects.get(user=user)
                request.session['reset_user_id'] = user.id
                return redirect('security_question')
            except (User.DoesNotExist, Customer.DoesNotExist):
                messages.error(request, 'Invalid username')
    else:
        form = UsernameForm()
    return render(request, 'ecom/v2/login/forgot_password.html', {'form': form})


def security_question(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('forgot_password')

    user = get_object_or_404(User, id=user_id)
    customer = get_object_or_404(Customer, user=user)

    if request.method == 'POST':
        form = SecurityQuestionForm(request.POST)
        if form.is_valid():
            security_answer = form.cleaned_data['security_answer']
            if security_answer == customer.security_answer:
                return redirect('set_new_password')
            else:
                messages.error(request, 'Incorrect answer')
    else:
        form = SecurityQuestionForm()

    return render(request, 'ecom/v2/login/security_question.html',
                  {'form': form, 'security_question': customer.get_security_question_display()})


from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import SetNewPasswordForm


def set_new_password(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('forgot_password')

    user = User.objects.get(id=user_id)
    print(f"User: {user.username}")

    if request.method == 'POST':
        form = SetNewPasswordForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important, to update the session with the new password
            messages.success(request, 'Your password has been successfully updated!')
            return redirect('customerlogin')
        else:
            print("Form is not valid")
    else:
        form = SetNewPasswordForm(user)

    return render(request, 'ecom/v2/login/set_new_password.html', {'form': form})

def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()


def afterlogin_view(request):
    if is_customer(request.user):
        return redirect('customer-home')
    else:
        return redirect('admin-dashboard')


def logout_view(request):
    logout(request)
    return redirect('dashboard')


def is_admin(user):
    return Admin.objects.filter(user=user).exists()


@login_required
@user_passes_test(is_admin)
def admin_portal_view(request):
    return redirect('dashboard')


@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    # for cards on dashboard
    customercount = Customer.objects.all().count()
    productcount = Product.objects.all().count()
    ordercount = Orders.objects.all().count()

    # for recent order tables
    orders = models.Orders.objects.all().order_by('-id')
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = order.products.all()
        ordered_by = Customer.objects.all().filter(id=order.customer.id)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)

    mydict = {
        'customercount': customercount,
        'productcount': productcount,
        'ordercount': ordercount,
        'data': zip(ordered_products, ordered_bys, orders),
    }
    return render(request, 'ecom/v2/admin/admin_dashboard.html', context=mydict)


# admin view the product
@login_required(login_url='adminlogin')
def admin_products_view(request):
    products = models.Product.objects.all()
    return render(request, 'ecom/v2/admin/admin_products.html', {'products': products})


# admin add product by clicking on floating button
@login_required(login_url='adminlogin')
def admin_add_product_view(request):
    productForm = forms.ProductForm()
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES)
        if productForm.is_valid():
            productForm.save()
        return HttpResponseRedirect('admin-products')
    return render(request, 'ecom/v2/admin/admin_add_products.html', {'productForm': productForm})


@login_required(login_url='adminlogin')
def delete_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    product.delete()
    return redirect('admin-products')


@login_required(login_url='adminlogin')
def update_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    productForm = forms.ProductForm(instance=product)
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES, instance=product)
        if productForm.is_valid():
            productForm.save()
            return redirect('admin-products')
    return render(request, 'ecom/v2/admin/admin_update_product.html', {'productForm': productForm})


@login_required(login_url='adminlogin')
def admin_view_booking_view(request):
    orders = Orders.objects.all()
    data = []

    for order in orders:
        ordered_products = order.products.all()
        ordered_by = Customer.objects.get(id=order.customer.id)
        data.append({
            'order': order,
            'products': ordered_products,
            'customer': ordered_by
        })

    return render(request, 'ecom/v2/admin/admin_view_booking.html', {'data': data})


@login_required(login_url='adminlogin')
def delete_order_view(request, pk):
    order = models.Orders.objects.get(id=pk)
    order.delete()
    return redirect('admin-view-booking')


def about_us(request):
    return render(request, 'ecom/v2/base/about_us.html')


def details(request):
    return render(request, 'ecom/v2/base/details.html')

def terms_and_condition(request):
    return render(request, 'ecom/v2/base/terms.html')


def privacy_policy(request):
    return render(request, 'ecom/v2/base/privacy_policy.html')


# for changing status of order (pending,delivered...)
@login_required(login_url='adminlogin')
def update_order_view(request, pk):
    order = models.Orders.objects.get(id=pk)
    orderForm = forms.OrderForm(instance=order)
    if request.method == 'POST':
        orderForm = forms.OrderForm(request.POST, instance=order)
        if orderForm.is_valid():
            orderForm.save()
            return redirect('admin-view-booking')
    return render(request, 'ecom/v2/admin/update_order.html', {'orderForm': orderForm})


def autosuggest(request):
    query = request.GET.get('query', '')
    products = models.Product.objects.filter(name__icontains=query)
    suggestions = [product.name for product in products]
    return JsonResponse(suggestions, safe=False)


def search_view(request):
    query = request.GET.get('query', "")
    category = request.GET.get('category', "")
    if len(category) > 0:
        products = models.Product.objects.filter(category__name__icontains=category)
    else:
        products = models.Product.objects.all().filter(name__icontains=query)

    categories = models.Category.objects.all()
    print(f"user {request.user.is_authenticated}")
    if request.user.is_authenticated:

        try:
            cart = get_cart(request)
            product_count_in_cart = cart['product_count_in_cart']
        except Exception as e:
            product_count_in_cart = 0
    else:
        product_count_in_cart = 0
    word = ""

    if request.user.is_authenticated:
        try:
            customer = models.Customer.objects.get(user_id=request.user.id)
            customer_url = customer.profile_pic.url
        except Exception as e:
            customer_url = 'profile_pic/default.png'
        return render(request, 'ecom/v2/home/customer_home.html',
                      {'products': products, 'word': word, 'product_count_in_cart': product_count_in_cart,
                       'categories': categories,'customer_url':customer_url})

    return render(request, 'ecom/v2/home/index.html',
                  {'products': products, 'categories': categories, 'word': word,
                   'product_count_in_cart': product_count_in_cart})


# def search_view(request):
#     # whatever user write in search box we get in query
#     query = request.GET.get('query', "")
#     category = request.GET.get('category', "")
#     if len(category) > 0:
#         products = models.Product.objects.filter(category__name__icontains=category)
#     else:
#         products = models.Product.objects.all().filter(name__icontains=query)

#     categories = models.Category.objects.all()
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         counter = product_ids.split('|')
#         product_count_in_cart = len(set(counter))
#     else:
#         product_count_in_cart = 0

#     # word variable will be shown in html when user click on search button
#     word = ""

#     if request.user.is_authenticated:
#         # return render(request,'ecom/customer_home.html',{'products':products,'word':word,'product_count_in_cart':product_count_in_cart})
#         return render(request, 'ecom/v2/home/customer_home.html',
#                       {'products': products, 'word': word, 'product_count_in_cart': product_count_in_cart,
#                        'categories': categories})
#     return render(request, 'ecom/v2/home/index.html',
#                   {'products': products, 'categories': categories, 'word': word,
#                    'product_count_in_cart': product_count_in_cart})

@login_required(login_url='customerlogin')
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    thisCustomer = models.Customer.objects.get(user_id=request.user.id)

    # Check if cart exists for the session or user
    cart, created = Cart.objects.get_or_create(customer=thisCustomer)  # Adjust based on your user handling

    # Check if product is already in the cart
    cart_product, created = CartProduct.objects.get_or_create(cart=cart, product=product)
    if not created:
        # If the product is already in the cart, increase the quantity
        cart_product.quantity += 1
        cart_product.save()
    else:
        # If the product is not in the cart, it's added with default quantity=1 (handled by get_or_create)
        pass

    # Redirect to cart view or send a success response
    return redirect('cart')


def remove_from_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    thisCustomer = models.Customer.objects.get(user_id=request.user.id)
    # Assuming the user's cart is identified by their session or user object
    cart = get_object_or_404(Cart, customer=thisCustomer)  # Adjust based on your user handling

    # Find the CartProduct instance
    cart_product = get_object_or_404(CartProduct, cart=cart, product=product)

    # Remove the product from the cart by deleting the CartProduct instance
    cart_product.delete()
    # response = render(request, 'ecom/v2/home/index.html',
    #                   {'products': products, 'product_count_in_cart': product_count_in_cart})

    # Redirect to cart view or send a success response
    return redirect('cart')  # Adjust 'cart_view' to your cart's view name or URL


def update_quantity(request, product_id, should_increase=True):
    product = get_object_or_404(Product, id=product_id)

    thisCustomer = models.Customer.objects.get(user_id=request.user.id)
    # Assuming the user's cart is identified by their session or user object
    cart = get_object_or_404(Cart, customer=thisCustomer)  # Adjust based on your user handling

    # Find the CartProduct instance
    cart_product = get_object_or_404(CartProduct, cart=cart, product=product)

    # Update the quantity of the product in the cart
    if should_increase:
        cart_product.quantity = cart_product.quantity + 1
    else:
        cart_product.quantity = cart_product.quantity - 1
    cart_product.save()


def increase_quantity(request, product_id):
    update_quantity(request, product_id, True)
    return redirect('cart')  # Adjust 'cart_view' to your cart's view name or URL


def decrease_quantity(request, product_id):
    update_quantity(request, product_id, False)
    return redirect('cart')  # Adjust 'cart_view' to your cart's view name or URL


def get_cart(request):
    thisCustomer = models.Customer.objects.get(user_id=request.user.id)
    cart = get_object_or_404(Cart, customer=thisCustomer)

    cart_products = CartProduct.objects.filter(cart=cart)

    # Calculate total and product count
    total = sum(cp.product.price * cp.quantity for cp in cart_products)
    product_count_in_cart = len(cart_products)

    # Check stock availability and collect out-of-stock products
    out_of_stock_products = []
    for cp in cart_products:
        if cp.quantity > cp.product.stock:
            out_of_stock_products.append(cp.product)

    # Pass cart details and out-of-stock products to the template
    context = {
        'products': cart_products,
        'total': total,
        'product_count_in_cart': product_count_in_cart,
        'out_of_stock_products': out_of_stock_products
    }

    return context


def cart_view(request):
    return render(request, 'ecom/v2/cart/cart.html', get_cart(request))


# # any one can add product to cart, no need of signin
# def add_to_cart_view(request, pk):
#     products = models.Product.objects.all()

#     # for cart counter, fetching products ids added by customer from cookies
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         counter = product_ids.split('|')
#         product_count_in_cart = len(set(counter))
#     else:
#         product_count_in_cart = 1

#     # response = render(request, 'ecom/index.html',{'products':products,'product_count_in_cart':product_count_in_cart})
#     response = render(request, 'ecom/v2/home/index.html',
#                       {'products': products, 'product_count_in_cart': product_count_in_cart})

#     # adding product id to cookies
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         if product_ids == "":
#             product_ids = str(pk)
#         else:
#             product_ids = product_ids + "|" + str(pk)
#         response.set_cookie('product_ids', product_ids)
#     else:
#         response.set_cookie('product_ids', pk)

#     product = models.Product.objects.get(id=pk)
#     # messages.info(request, product.name + ' added to cart successfully!')

#     return response

# # for checkout of cart
# def cart_view(request):
#     # for cart counter
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         counter = product_ids.split('|')
#         product_count_in_cart = len(set(counter))
#     else:
#         product_count_in_cart = 0

#     # fetching product details from db whose id is present in cookie
#     products = None
#     total = 0
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         if product_ids != "":
#             product_id_in_cart = product_ids.split('|')
#             products = models.Product.objects.all().filter(id__in=product_id_in_cart)

#             # for total price shown in cart
#             for p in products:
#                 total = total + p.price
#     # return render(request,'ecom/cart.html',{'products':products,'total':total,'product_count_in_cart':product_count_in_cart})
#     return render(request, 'ecom/v2/cart/cart.html',
#                   {'products': products, 'total': total, 'product_count_in_cart': product_count_in_cart})


# def remove_from_cart_view(request, pk):
#     # for counter in cart
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         counter = product_ids.split('|')
#         product_count_in_cart = len(set(counter))
#     else:
#         product_count_in_cart = 0

#     # removing product id from cookie
#     total = 0
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         product_id_in_cart = product_ids.split('|')
#         product_id_in_cart = list(set(product_id_in_cart))
#         product_id_in_cart.remove(str(pk))
#         products = models.Product.objects.all().filter(id__in=product_id_in_cart)
#         # for total price shown in cart after removing product
#         for p in products:
#             total = total + p.price

#         #  for update coookie value after removing product id in cart
#         value = ""
#         for i in range(len(product_id_in_cart)):
#             if i == 0:
#                 value = value + product_id_in_cart[0]
#             else:
#                 value = value + "|" + product_id_in_cart[i]
#         # response = render(request, 'ecom/cart.html',{'products':products,'total':total,'product_count_in_cart':product_count_in_cart})
#         response = render(request, 'ecom/v2/cart/cart.html',
#                           {'products': products, 'total': total, 'product_count_in_cart': product_count_in_cart})

#         if value == "":
#             response.delete_cookie('product_ids')
#         response.set_cookie('product_ids', value)
#         return response

@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_home_view(request):
    products = models.Product.objects.all()
    categories = models.Category.objects.all()
    try:
        cart = get_cart(request)
        product_count_in_cart = cart['product_count_in_cart']
    except Exception as e:
        product_count_in_cart = 0

    try:
        customer = models.Customer.objects.get(user_id=request.user.id)
        customer_url = customer.profile_pic.url
    except Exception as e:
        customer_url = 'profile_pic/default.png'
    # return render(request,'ecom/customer_home.html',{'products':products,'product_count_in_cart':product_count_in_cart})
    return render(request, 'ecom/v2/home/customer_home.html',
                  {'products': products,'customer_url':customer_url, 'categories': categories, 'product_count_in_cart': product_count_in_cart})


# @login_required(login_url='customerlogin')
# @user_passes_test(is_customer)
# def customer_home_view(request):
#     products = models.Product.objects.all()
#     categories = models.Category.objects.all()
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         counter = product_ids.split('|')
#         product_count_in_cart = len(set(counter))
#     else:
#         product_count_in_cart = 0
#     # return render(request,'ecom/customer_home.html',{'products':products,'product_count_in_cart':product_count_in_cart})
#     return render(request, 'ecom/v2/home/customer_home.html',
#                   {'products': products, 'categories': categories, 'product_count_in_cart': product_count_in_cart})


# # shipment address before placing order
# @login_required(login_url='customerlogin')
# def customer_address_view(request):
#     # this is for checking whether product is present in cart or not
#     # if there is no product in cart we will not show address form
#     product_in_cart = False
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         if product_ids != "":
#             product_in_cart = True
#     # for counter in cart
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         counter = product_ids.split('|')
#         product_count_in_cart = len(set(counter))
#     else:
#         product_count_in_cart = 0

#     addressForm = forms.AddressForm()
#     if request.method == 'POST':
#         addressForm = forms.AddressForm(request.POST)
#         if addressForm.is_valid():
#             # here we are taking address, email, mobile at time of order placement
#             # we are not taking it from customer account table because
#             # these thing can be changes
#             email = addressForm.cleaned_data['Email']
#             mobile = addressForm.cleaned_data['Mobile']
#             address = addressForm.cleaned_data['Address']
#             # for showing total price on payment page.....accessing id from cookies then fetching  price of product from db
#             total = 0
#             if 'product_ids' in request.COOKIES:
#                 product_ids = request.COOKIES['product_ids']
#                 if product_ids != "":
#                     product_id_in_cart = product_ids.split('|')
#                     products = models.Product.objects.all().filter(id__in=product_id_in_cart)
#                     for p in products:
#                         total = total + p.price

#             # response = render(request, 'ecom/payment.html',{'total':total})
#             response = render(request, 'ecom/v2/cart/payment.html', {'total': total})
#             response.set_cookie('email', email)
#             response.set_cookie('mobile', mobile)
#             response.set_cookie('address', address)
#             return response
#     # return render(request,'ecom/customer_address.html',{'addressForm':addressForm,'product_in_cart':product_in_cart,'product_count_in_cart':product_count_in_cart})
#     return render(request, 'ecom/v2/cart/customer_address.html',
#                   {'addressForm': addressForm, 'product_in_cart': product_in_cart,
#                    'product_count_in_cart': product_count_in_cart})


@login_required(login_url='customerlogin')
def customer_address_view(request):
    cart = get_cart(request)
    product_in_cart = cart['product_count_in_cart'] > 0
    product_count_in_cart = cart['product_count_in_cart']

    addressForm = forms.AddressForm()
    if request.method == 'POST':
        addressForm = forms.AddressForm(request.POST)
        if addressForm.is_valid():
            email = addressForm.cleaned_data['Email']
            mobile = addressForm.cleaned_data['Mobile']
            address = addressForm.cleaned_data['Address']
            total = cart['total']

            response = render(request, 'ecom/v2/cart/payment.html', {'total': total})
            response.set_cookie('email', email)
            response.set_cookie('mobile', mobile)
            response.set_cookie('address', address)
            return response
    return render(request, 'ecom/v2/cart/customer_address.html',
                  {'addressForm': addressForm, 'product_in_cart': product_in_cart,
                   'product_count_in_cart': product_count_in_cart})


@login_required(login_url='customerlogin')
def payment_success_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    cart_model_instance = get_cart(request)
    cart_products = cart_model_instance['products']
    email = request.COOKIES.get('email')
    mobile = request.COOKIES.get('mobile')
    address = request.COOKIES.get('address')

    try:
        # Create the order
        order = models.Orders.objects.create(
            customer=customer,
            email=email,
            mobile=mobile,
            address=address,
            status='Pending'
        )
        order.products.set([cp.product for cp in cart_products])
        order.save()

        # Update stock for each product in the cart
        for cp in cart_products:
            product = cp.product
            product.stock -= cp.quantity
            product.save()

        # Delete the cart products for the customer
        cart_model_instance.cartproduct_set.all().delete()

        # Delete the cart for the customer
        cart_model_instance.delete()
    except Exception as e:
        print(e)

    response = render(request, 'ecom/v2/cart/payment_success.html')
    response.delete_cookie('email')
    response.delete_cookie('mobile')
    response.delete_cookie('address')
    return response



# @login_required(login_url='customerlogin')
# def payment_success_view(request):
#     customer = models.Customer.objects.get(user_id=request.user.id)
#     products = []
#     email = None
#     mobile = None
#     address = None

#     # Retrieve products from cookies
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         if product_ids:
#             product_id_in_cart = product_ids.split('|')
#             products = models.Product.objects.filter(id__in=product_id_in_cart)
#             for product in products:
#                 print(product.name)  # Debugging statement, consider removing in production

#     # Retrieve additional customer details from cookies
#     email = request.COOKIES.get('email')
#     mobile = request.COOKIES.get('mobile')
#     address = request.COOKIES.get('address')

#     try:
#         # Create a new order
#         order = models.Orders.objects.create(
#             customer=customer,
#             email=email,
#             mobile=mobile,
#             address=address,
#             status='Pending'
#         )

#         # Add products to the order
#         order.products.set(products)
#         order.save()
#     except Exception as e:
#         print(e)  # For debugging, consider logging in production

#     # Render the payment success page and clear cookies
#     response = render(request, 'ecom/v2/cart/payment_success.html')
#     response.delete_cookie('product_ids')
#     response.delete_cookie('email')
#     response.delete_cookie('mobile')
#     response.delete_cookie('address')
#     return response


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
# def my_order_view(request):
#     customer = models.Customer.objects.get(user_id=request.user.id)
#     orders = models.Orders.objects.all().filter(customer_id=customer)
#     ordered_products = []
#     for order in orders:
#         ordered_product = models.Product.objects.all().filter(id=order.product.id)
#         ordered_products.append(ordered_product)
#     return render(request, 'ecom/v2/cart/my_order.html', {'data': zip(ordered_products, orders)})
def my_order_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    orders = models.Orders.objects.filter(customer_id=customer).order_by('-id')

    return render(request, 'ecom/v2/cart/my_order.html',
                  {'orders': orders})


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return


# @login_required(login_url='customerlogin')
# @user_passes_test(is_customer)
# def download_invoice_view(request, orderID, productID):
#     order = models.Orders.objects.get(id=orderID)
#     product = models.Product.objects.get(id=productID)
#     mydict = {
#         'orderDate': order.order_date,
#         'customerName': request.user,
#         'customerEmail': order.email,
#         'customerMobile': order.mobile,
#         'shipmentAddress': order.address,
#         'orderStatus': order.status,
#         'productName': product.name,
#         'productImage': product.product_image,
#         'productPrice': product.price,
#         'productDescription': product.description,
#     }
#     return render_to_pdf('ecom/download_invoice.html', mydict)


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def download_invoice_view(request, orderID):
    order = get_object_or_404(models.Orders, id=orderID)
    products = order.products.all()  # Assuming there's a related name `products` in the Orders model.
    print("invoice")
    for product in products:
        print(product.name)
    product_list = []
    for product in products:
        product_info = {
            'productName': product.name,
            'productImage': product.product_image,
            'productPrice': product.price,
            'productDescription': product.description,
        }
        product_list.append(product_info)

    mydict = {
        'orderDate': order.order_date,
        'customerName': request.user,
        'customerEmail': order.email,
        'customerMobile': order.mobile,
        'shipmentAddress': order.address,
        'orderStatus': order.status,
        'products': product_list,
    }

    return render_to_pdf('ecom/v2/base/download_invoice.html', mydict)


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def my_profile_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    customer_url = customer.profile_pic.url
    return render(request, 'ecom/v2/profile/my_profile.html', {'customer': customer, 'customer_url':customer_url})

@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def edit_profile_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    user = models.User.objects.get(id=customer.user_id)
    userForm = forms.CustomerUserForm(instance=user)
    customerForm = forms.CustomerForm(request.FILES, instance=customer)
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST, instance=user)
        customerForm = forms.CustomerForm(request.POST, instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return HttpResponseRedirect('my-profile')
    return render(request, 'ecom/v2/profile/edit_profile.html', context=mydict)


def dashboard(request):
    categories = models.Category.objects.all()
    top_events = Event.objects.annotate(num_registrations=Count('eventmember')).order_by('-num_registrations')[:4]
    top_threads = Post.objects.order_by('-date_posted')[:3]
    try:
        customer = models.Customer.objects.get(user_id=request.user.id)
        customer_url = customer.profile_pic.url
    except Exception as e:
        customer_url = 'profile_pic/default.png'
    context = {
        'categories': categories,
        'top_events': top_events,
        'top_threads': top_threads,
        'customer_url':customer_url
    }
    return render(request, 'ecom/v2/home/user-dashboard.html', context)


def add_category_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin-categories')
    else:
        form = CategoryForm()
    return render(request, 'ecom/v2/admin/category/add_category.html', {'form': form})


def update_category_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('admin-categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'ecom/v2/admin/category/update_category.html', {'form': form})


# admin view the product
@login_required(login_url='adminlogin')
def admin_categories_view(request):
    categories = models.Category.objects.all()
    return render(request, 'ecom/v2/admin/category/admin_categories.html', {'categories': categories})


def delete_category_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('admin-categories')
    return render(request, 'ecom/v2/admin/category/delete_category.html', {'category': category})


# view functions for QA Forum App

def home(request):
    posts = Post.objects.all()
    comments = Comment.objects.all()
    Post
    context = {
        'posts': posts,
        'comments': comments,
    }
    return render(request, 'blog/home.html', context)


class HomeView(TemplateView):
    template_name = 'home.html'


def search(request):
    template = 'blog/home.html'

    query = request.GET.get('q')

    result = Post.objects.filter(
        Q(title__icontains=query) | Q(author__user__username__icontains=query) | Q(content__icontains=query)
    )

    context = {'posts': result}
    return render(request, template, context)


def getfile(request):
    return serve(request, 'File')


class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 2


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    paginate_by = 2

    def get_queryset(self):
        # user = models.OneToOneField(User, on_delete=models.CASCADE)
        # profile_pic = models.ImageField(upload_to='profile_pic/CustomerProfilePic/', null=True, blank=True)
        # address = models.CharField(max_length=40)
        # mobile = models.CharField(max_length=20, null=False)
        print(self.kwargs.get('username'))
        user = User.objects.get(username=self.kwargs.get('username'))
        return Post.objects.filter(author__user__username=user.username)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'


# riya Created new
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/post_form.html'
    fields = ['title', 'content', 'file']

    def form_valid(self, form):
        customer = Customer.objects.get(user=self.request.user)
        form.instance.author = customer
        return super().form_valid(form)


# Riya addede new to update
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    template_name = 'blog/post_form.html'
    fields = ['title', 'content', 'file']

    def form_valid(self, form):
        customer = Customer.objects.get(user=self.request.user)
        form.instance.author = customer
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author.user


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('home')
    template_name = 'blog/post_confirm_delete.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author.user


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.filter(parent=None)  # Get only parent comments
    reply_form = ReplyForm()

    if request.method == 'POST':
        if 'comment_form' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                customer = Customer.objects.get(user=request.user)
                new_comment.post = post
                new_comment.author = customer
                new_comment.save()
                return redirect('post-detail', pk=post.pk)
        elif 'reply_form' in request.POST:
            reply_form = ReplyForm(request.POST)
            if reply_form.is_valid():
                parent_id = request.POST.get('parent_id')
                parent_comment = get_object_or_404(Comment, id=parent_id)
                new_reply = reply_form.save(commit=False)
                customer = Customer.objects.get(user=request.user)
                new_reply.post = post
                new_reply.author = customer
                new_reply.parent = parent_comment
                new_reply.save()
                return redirect('post-detail', pk=post.pk)
    else:
        comment_form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'reply_form': reply_form,
    }

    return render(request, 'blog/post_detail.html', context)
