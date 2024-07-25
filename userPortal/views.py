from django.contrib.auth import logout
from django.db.models import Count
from django.views.static import serve
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from . import forms, models
from django.http import HttpResponseRedirect
from .smtp import send_email
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Comment, Customer, Admin, Product, Order
from .forms import ReplyForm, CommentForm
from .models import Category, Cart, CartProduct
from .forms import CategoryForm,UsernameForm, SecurityQuestionForm
from adminPortal.models import Event, EventCategory, EventRegistration
from django.core.files.storage import default_storage
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Post
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import SetNewPasswordForm
from decimal import Decimal

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

# Handles user redirection based on authentication status.
# If authenticated, they go to the customer home page. Otherwise, they go to the dashboard.
def home_view(request):
    try:
        if request.user.is_authenticated:
            return HttpResponseRedirect('customer-home')
        else:
            return HttpResponseRedirect('dashboard')
    except Exception as e:
        print(e)
        return HttpResponseRedirect('dashboard')

@login_required(login_url='login_as_customer')
def register_event(request, event_id):
    # Grab the event and current user.
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    # Check if the event is full. If it is, handle the response differently for AJAX and regular requests.
    if event.registration_count >= event.maximum_attende:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': "Event full. Unable to Register."})
        else:
            messages.error(request, "Event full. Unable to Register.")
            return redirect('events')

    # Create a registration record if it doesn't already exist.
    registration, created = EventRegistration.objects.get_or_create(event=event, user=user)
    if created:
        # Send a confirmation email and show a success message.
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            send_email(user.email, 'Event Registration Success', f'Hi {user.username},<br><br>You have successfully registered to the {event.name} event.<br><br>Regards,<br>EcoGreenSmart Team')
            return JsonResponse({'success': True, 'event_name': event.name})
        else:
            messages.success(request, f"You have successfully registered to {event.name} event.")
            send_email(user.email, 'Event Registration Success', f'Hi {user.username},<br><br>You have successfully registered to the {event.name} event.<br><br>Regards,<br>EcoGreenSmart Team')
    else:
        # Inform the user if they're already registered for the event.
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f"You are already registered to {event.name} event."})
        else:
            messages.info(request, f"You are already registered to {event.name} event.")

    return redirect('events')



@login_required
def cancel_registration(request, event_id):
    # Locate the event and the user.
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    try:
        # Try to delete the registration if it exists.
        registration = EventRegistration.objects.get(event=event, user=user)
        registration.delete()
        messages.success(request, f"You have successfully canceled your registration for {event.name} event.")
    except EventRegistration.DoesNotExist:
        # Show an error if the user wasn't registered.
        messages.error(request, "You are not registered for this event.")


# View to display events
def event_view(request):
    query = request.GET.get('query', '')  # Get the search query from the request
    category = request.GET.get('category', '')  # Get the category from the request
    events = Event.objects.all()  # Get all events
    registrations = EventRegistration.objects.filter(user=request.user) if request.user.is_authenticated else EventRegistration.objects.none()  # Get registrations for the authenticated user
    registered_event_ids = registrations.values_list('event_id', flat=True)  # Get the IDs of registered events
    event_statuses = {event.id: 'full' if event.registration_count >= event.maximum_attende else 'open' for event in events}  # Determine the status of each event
    customer_url = ''
    if request.user.is_authenticated:
        try:
            customer = models.Customer.objects.get(user_id=request.user.id)  # Get the customer associated with the authenticated user
            customer_url = customer.profile_pic.url  # Get the URL of the customer's profile picture
        except ObjectDoesNotExist:
            customer_url = ''

    if query:
        events = events.filter(name__icontains=query)  # Filter events by name if a query is provided
    if category:
        events = events.filter(category__name=category)  # Filter events by category if a category is provided

    categories = EventCategory.objects.all()  # Get all event categories

    context = {
        'events': events,
        'categories': categories,
        'customer_url': customer_url,
        'registered_event_ids': registered_event_ids,
        'event_statuses': event_statuses,
    }
    return render(request, 'ecom/v2/home/events.html', context)  # Render the events template with the context

# This view handles the autosuggest functionality for events based on the query parameter.
# It filters the events based on the name containing the query and returns a JSON response with the suggestions.
def autosuggest_view(request):
    query = request.GET.get('query', '')
    events = Event.objects.filter(name__icontains=query)
    suggestions = [event.name for event in events]
    return JsonResponse(suggestions, safe=False)

# This view returns the details of an event based on the event ID.
def get_event_details(request, event_id):
    try:
        # Get the event and its coordinates
        event = Event.objects.get(pk=event_id)
        # Get the coordinates of the event location
        coords = event.location if isinstance(event.location, (list, tuple)) else event.location.coords
        data = {
            'name': event.name,
            'description': event.description,
            'venue': event.venue,
            'location': coords,
            'end_date': event.end_date.strftime('%Y-%m-%d'),
            'max_attendees': event.maximum_attende,
            'image': event.category.image.url if event.category and event.category.image else ''
        } # Create a dictionary with the event details
        return JsonResponse(data) # Return the event details as a JSON response
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}) # Return an error message if the event is not found

@login_required(login_url='login_as_admin')
def admin_dashboard_view(request): # View for the admin dashboard
    return HttpResponseRedirect('admin-dashboard') # Redirect to the admin dashboard

def customer_register_view(request): # View for customer registration
    userForm = forms.CustomerUserForm()
    customerForm = forms.CustomerForm()
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST': # If the request method is POST
        userForm = forms.CustomerUserForm(request.POST)
        customerForm = forms.CustomerForm(request.POST, request.FILES)
        if userForm.is_valid() and customerForm.is_valid(): # If both forms are valid
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customer = customerForm.save(commit=False)
            customer.user = user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER') # Get or create the CUSTOMER group
            my_customer_group[0].user_set.add(user)
            send_email(user.email, 'Registration Successful in EcoGreenSmart',
                       f'Hi {user.first_name}, <br><br> Thank you for registering with EcoGreenSmart. '
                       f'<br><br> Regards, <br> EcoGreenSmart Team') # Send a registration email
        return HttpResponseRedirect('login_as_customer') # Redirect to the customer login page
    return render(request, 'ecom/v2/signup/customer_register.html', context=mydict) # Render the customer registration template with the context


def forgot_password(request): # View for the forgot password page
    if request.method == 'POST': # If the request method is POST
        form = UsernameForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = User.objects.get(username=username)
                request.session['reset_user_id'] = user.id # Set the user ID in the session
                return redirect('security_question') # Redirect to the security question page
            except (User.DoesNotExist, Customer.DoesNotExist):
                messages.error(request, 'Invalid username')
    else:
        form = UsernameForm()
    return render(request, 'ecom/v2/login/forgot_password.html', {'form': form}) # Render the forgot password template with the form


def security_question(request): # View for the security question page
    user_id = request.session.get('reset_user_id') # Get the user ID from the session
    if not user_id:
        return redirect('forgot_password') # Redirect to the forgot password page if the user ID is not found

    user = get_object_or_404(User, id=user_id)
    customer = get_object_or_404(Customer, user=user)

    if request.method == 'POST':
        form = SecurityQuestionForm(request.POST) # Create a security question form
        if form.is_valid():
            security_answer = form.cleaned_data['security_answer']
            if security_answer == customer.security_answer:
                return redirect('set_new_password')
            else:
                messages.error(request, 'Incorrect answer')
    else:
        form = SecurityQuestionForm()

    return render(request, 'ecom/v2/login/security_question.html',
                  {'form': form, 'security_question': customer.get_security_question_display()}) # Render the security question template with the form and security question

def set_new_password(request): # View for setting a new password
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('forgot_password') # Redirect to the forgot password page if the user ID is not found

    user = User.objects.get(id=user_id)
    print(f"User: {user.username}")

    if request.method == 'POST':
        form = SetNewPasswordForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) # Update the session auth hash
            messages.success(request, 'Your password has been updated!')
            return redirect('login_as_customer') # Redirect to the customer login page
        else:
            print("Form is not valid")
    else:
        form = SetNewPasswordForm(user) # Create a set new password form

    return render(request, 'ecom/v2/login/set_new_password.html', {'form': form}) # Render the set new password template with the form

def is_customer(user): # Function to check if a user is a customer
    return user.groups.filter(name='CUSTOMER').exists() # Return True if the user is in the CUSTOMER group


def afterlogin_view(request): # View for after login
    if is_customer(request.user):
        return redirect('customer-home') # Redirect to the customer home page if the user is a customer
    else:
        return redirect('admin-dashboard') # Redirect to the admin dashboard if the user is an admin


def logout_view(request):
    logout(request) # Log the user out
    return redirect('dashboard')


def is_admin(user):
    return Admin.objects.filter(user=user).exists() # Return True if the user is an admin


@login_required
@user_passes_test(is_admin)
def admin_portal_view(request): # View for the admin portal
    return redirect('dashboard')


@login_required(login_url='login_as_admin')
def admin_dashboard_view(request):
    # for cards on dashboard
    customercount = Customer.objects.all().count()
    productcount = Product.objects.all().count()
    ordercount = Order.objects.all().count()

    # for recent order tables
    orders = models.Order.objects.all().order_by('-id') # Get all orders and order them by ID
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = order.items.all()
        ordered_by = Customer.objects.all().filter(id=order.customer.id) # Get the customer who placed the order
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)

    mydict = {
        'customercount': customercount,
        'productcount': productcount,
        'ordercount': ordercount,
        'data': zip(ordered_products, ordered_bys, orders),
    } # Create a dictionary with the customer count, product count, order count, and order data
    return render(request, 'ecom/v2/admin/admin_dashboard.html', context=mydict) # Render the admin dashboard template with the context


@login_required(login_url='login_as_admin') # Require the user to be logged in as an admin
def admin_products_view(request): # View for the admin products
    products = models.Product.objects.all()
    return render(request, 'ecom/v2/admin/admin_products.html', {'products': products}) # Render the admin products template with the products

@login_required(login_url='login_as_admin')
def admin_add_product_view(request): # View for adding a product
    productForm = forms.ProductForm()
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES) # Create a product form
        if productForm.is_valid():
            productForm.save()
        return HttpResponseRedirect('admin-products')
    return render(request, 'ecom/v2/admin/admin_add_products.html', {'productForm': productForm}) # Render the add product template with the product form


@login_required(login_url='login_as_admin')
def delete_product_view(request, pk): # View for deleting a product
    product = models.Product.objects.get(id = pk) # Get the product by ID
    product.delete()
    return redirect('admin-products') # Redirect to the admin products page


@login_required(login_url='login_as_admin')
def update_product_view(request, pk): # View for updating a product
    product = models.Product.objects.get(id = pk) # Get the product by ID
    productForm = forms.ProductForm(instance=product)
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES, instance=product)
        if productForm.is_valid(): # If the form is valid
            productForm.save()
            return redirect('admin-products') # Redirect to the admin products page
    return render(request, 'ecom/v2/admin/admin_update_product.html', {'productForm': productForm})


@login_required(login_url='login_as_admin')
def admin_view_booking_view(request): # View for viewing bookings
    orders = Order.objects.all()
    data = []

    for order in orders: # For each order
        ordered_products = order.items.all()
        ordered_by = Customer.objects.get(id=order.customer.id) # Get the customer who placed the order
        data.append({
            'order': order,
            'products': ordered_products,
            'customer': ordered_by
        }) # Append the order, products, and customer to the data list

    return render(request, 'ecom/v2/admin/admin_view_booking.html', {'data': data})


@login_required(login_url='login_as_admin') # Require the user to be logged in as an admin
def delete_order_view(request, pk):
    order = models.Order.objects.get(id=pk) # Get the order by ID
    order.delete()# Delete the order
    return redirect('admin-view-booking') # Redirect to the admin view booking page


def about_us(request):
    return render(request, 'ecom/v2/base/about_us.html') # Render the about us template


def details(request):
    return render(request, 'ecom/v2/base/details.html') # Render the details template

def terms_and_condition(request):
    return render(request, 'ecom/v2/base/terms.html') # Render the terms and conditions template


def privacy_policy(request):
    return render(request, 'ecom/v2/base/privacy_policy.html') # Render the privacy policy template

@login_required(login_url='login_as_admin')
def update_order_view(request, pk): # View for updating an order
    order = models.Order.objects.get(id = pk)
    orderForm = forms.OrderForm(instance=order)
    if request.method == 'POST': # If the request method is POST
        orderForm = forms.OrderForm(request.POST, instance=order)
        if orderForm.is_valid():
            orderForm.save()
            return redirect('admin-view-booking') # Redirect to the admin view booking page
    return render(request, 'ecom/v2/admin/update_order.html', {'orderForm': orderForm})


def autosuggest(request):
    query = request.GET.get('query', '') # Get the query from the request
    products = models.Product.objects.filter(name__icontains=query) # Filter products by name containing the query
    suggestions = [product.name for product in products]
    return JsonResponse(suggestions, safe=False) # Return the suggestions as a JSON response


def search_view(request):
    query = request.GET.get('query', "")
    category = request.GET.get('category', "")
    if len(category) > 0: # If the category is provided
        products = models.Product.objects.filter(category__name__icontains=category) # Filter products by category
    else:
        products = models.Product.objects.all().filter(name__icontains=query) # Filter products by name containing the query

    categories = models.Category.objects.all() # Get all categories
    if request.user.is_authenticated: # If the user is authenticated

        try:
            cart = get_cart(request)
            product_count_in_cart = cart['product_count_in_cart'] # Get the product count in the cart
        except Exception as e:
            product_count_in_cart = 0
    else:
        product_count_in_cart = 0
    word = ""

    if request.user.is_authenticated:
        try:
            customer = models.Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user
            customer_url = customer.profile_pic.url
        except Exception as e:
            customer_url = 'profile_pic/default.png'
        return render(request, 'ecom/v2/home/customer_home.html',
                      {'products': products, 'word': word, 'product_count_in_cart': product_count_in_cart,
                       'categories': categories,'customer_url':customer_url}) # Render the customer home template with the products, word, product count in cart, categories, and customer URL

    return render(request, 'ecom/v2/home/index.html',
                  {'products': products, 'categories': categories, 'word': word,
                   'product_count_in_cart': product_count_in_cart, 'query': query}) # Render the index template with the products, categories, word, product count in cart, and query

@login_required(login_url='login_as_customer')
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    thisCustomer = models.Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user
    cart, created = Cart.objects.get_or_create(customer=thisCustomer)
    cart_product, created = CartProduct.objects.get_or_create(cart=cart, product=product) # Get or create the cart product
    if not created:
        cart_product.quantity += 1 # Increment the quantity if the cart product already exists
        cart_product.save()
    else:
        pass
    return redirect('cart') # Redirect to the cart page


def remove_from_cart_view(request, product_id): # View for removing a product from the cart
    product = get_object_or_404(Product, id=product_id)
    thisCustomer = models.Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user
    cart = get_object_or_404(Cart, customer=thisCustomer)
    cart_product = get_object_or_404(CartProduct, cart=cart, product=product) # Get the cart product
    cart_product.delete() # Delete the cart product
    return redirect('cart')


def update_quantity(request, product_id, should_increase=True): # View for updating the quantity of a product
    product = get_object_or_404(Product, id=product_id)
    thisCustomer = models.Customer.objects.get(user_id=request.user.id)
    cart = get_object_or_404(Cart, customer=thisCustomer)
    cart_product = get_object_or_404(CartProduct, cart=cart, product=product)
    if should_increase: # If the quantity should be increased
        cart_product.quantity = cart_product.quantity + 1 # Increment the quantity
    else:
        cart_product.quantity = cart_product.quantity - 1
    cart_product.save()


def increase_quantity(request, product_id):
    update_quantity(request, product_id, True) # Update the quantity
    return redirect('cart')


def decrease_quantity(request, product_id):
    update_quantity(request, product_id, False) # Update the quantity by decreasing it by 1
    return redirect('cart')


def get_cart(request):
    thisCustomer = models.Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user if the user is authenticated
    cart = get_object_or_404(Cart, customer=thisCustomer)
    cart_products = CartProduct.objects.filter(cart=cart)
    total = sum(cp.product.price * cp.quantity for cp in cart_products) # Calculate the total price of the products in the cart using a list comprehension
    total = Decimal(total) # Multiply using Decimal
    tax_rate = Decimal('0.13')  # Use a string to initialize the Decimal
    tax_amount = total * tax_rate
    total = total + tax_amount # Add the tax amount to the total
    total = total.quantize(Decimal('0.00')) # Round the total to 2 decimal places
    product_count_in_cart = len(cart_products) # Get the number of products in the cart
    out_of_stock_products = []
    for cp in cart_products:
        if cp.quantity > cp.product.stock:
            out_of_stock_products.append(cp.product)
    context = {
        'products': cart_products,
        'tax_amount': tax_amount,
        'total': total,
        'product_count_in_cart': product_count_in_cart,
        'out_of_stock_products': out_of_stock_products
    } # Create a context dictionary with the products, tax amount, total, product count in cart, and out of stock products
    return context


def cart_view(request): # View for the cart page if the user is authenticated
    user = User.objects.get(id=request.user.id)
    customer = Customer.objects.get(user=user)
    customer_url = customer.profile_pic.url
    cart_context = get_cart(request)
    cart_context['customer_url'] = customer_url # Add the customer URL to the cart context
    return render(request, 'ecom/v2/cart/cart.html', cart_context)  # Render the cart template with the cart context

@login_required(login_url='login_as_customer')
@user_passes_test(is_customer)
def customer_home_view(request): # View for the customer home page if the user is a customer and is authenticated
    products = models.Product.objects.all()
    categories = models.Category.objects.all()
    try:
        cart = get_cart(request) # Get the cart context if the user is authenticated and is a customer using the get_cart function
        product_count_in_cart = cart['product_count_in_cart'] # Get the product count in the cart
    except Exception as e:
        product_count_in_cart = 0

    try:
        customer = models.Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user
        customer_url = customer.profile_pic.url
    except Exception as e:
        customer_url = 'profile_pic/default.png'
    return render(request, 'ecom/v2/home/customer_home.html',
                  {'products': products,'customer_url':customer_url, 'categories': categories, 'product_count_in_cart': product_count_in_cart}) # Render the customer home template with the products, categories, customer URL, and product count in cart

@login_required(login_url='login_as_customer')
def customer_address_view(request): # View for the customer address if the user is authenticated
    cart = get_cart(request)
    product_in_cart = cart['product_count_in_cart'] > 0
    product_count_in_cart = cart['product_count_in_cart']
    customer = Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user
    customer_url = customer.profile_pic.url
    addressForm = forms.AddressForm() # Create an address form
    if request.method == 'POST':
        addressForm = forms.AddressForm(request.POST) # Create an address form with the POST data
        if addressForm.is_valid():
            email = addressForm.cleaned_data['Email']
            mobile = addressForm.cleaned_data['Mobile'] 
            address = addressForm.cleaned_data['Address'] # Get the email, mobile, and address from the form
            cart_details = Cart.objects.get(customer=customer) # Get the cart details
            cart_details.email = email
            # Update the cart details with the mobile
            cart_details.mobile = mobile
            # Update the cart details with the address
            cart_details.address= address
            cart_details.save() # Save the cart details
            total = cart['total'] # Get the total from the cart
            response = render(request, 'ecom/v2/cart/payment.html', {'total': total,'customer_url':customer_url})   # Render the payment template with the total and customer URL
            response.set_cookie('email', email)
            # Set the email in a cookie
            response.set_cookie('mobile', mobile)
            # Set the mobile in a cookie
            response.set_cookie('address', address)
            # Set the address in a cookie
            return response # Return the response
    return render(request, 'ecom/v2/cart/customer_address.html',
                  {'addressForm': addressForm, 'product_in_cart': product_in_cart,
                   'product_count_in_cart': product_count_in_cart, 'customer_url':customer_url}) # Render the customer address template with the address form, product in cart, product count in cart, and customer URL


@login_required(login_url='login_as_customer')
def payment_success_view(request): # View for the payment success if the user is authenticated
    customer = models.Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user
    cart_model_instance = get_cart(request) # Get the cart model instance
    cart_products = cart_model_instance['products'] # Get the products in the cart
    email = request.COOKIES.get('email') # Get the email from the cookies
    mobile = request.COOKIES.get('mobile') # Get the mobile from the cookies
    address = request.COOKIES.get('address') # Get the address from the cookies
    customer = Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user
    customer_url = customer.profile_pic.url # Get the customer URL
    try:
        # Create the order
        order = models.Order.objects.create(
            customer=customer,
            email=email,
            mobile=mobile,
            address=address,
            status='Pending'
        )
        for cart_product in cart_products: # For each product in the cart
            item = models.Item.objects.create(
                product=cart_product.product,
                quantity=cart_product.quantity
            ) # Create an item with the product and quantity
            order.items.add(item) # Add the item to the order
            product = cart_product.product # Get the product
            product.stock -= cart_product.quantity # Subtract the quantity from the stock
            product.save()

        order.save()
        cart_model_instance.cartproduct_set.all().delete() # Delete all cart products in the cart model instance
        cart_model_instance.delete() # Delete the cart model instance
    except Exception as e:
        print(e)

    response = render(request, 'ecom/v2/cart/payment_success.html',{'customer_url':customer_url}) # Render the payment success template with the customer URL
    response.delete_cookie('email') # Delete the email cookie
    response.delete_cookie('mobile') # Delete the mobile cookie
    response.delete_cookie('address')
    return response # Return the response

def my_order_view(request): # View for the customer's order if the user is authenticated
    customer = models.Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user
    orders = models.Order.objects.filter(customer_id=customer).order_by('-id') # Get the orders for the customer and order them by ID
    customer_url = customer.profile_pic.url # Get the customer
    return render(request, 'ecom/v2/cart/my_order.html',
                  {'orders': orders,'customer_url':customer_url}) # Render the my order template with the orders and customer URL

def render_to_pdf(template_src, context_dict): # Function to render a template to a PDF
    template = get_template(template_src) # Get the template
    html = template.render(context_dict) # Render the template
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result) # Create a PDF from the HTML content using pisa
    if not pdf.err: # If there are no errors
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return

@login_required(login_url='login_as_customer')
@user_passes_test(is_customer) # Require the user to be a customer
def download_invoice_view(request, orderID): # View for downloading an invoice
    order = get_object_or_404(models.Order, id=orderID) # Get the order by ID
    items = order.items.all() # Get the items in the order using the items attribute
    for product in items: # For each product in the items
        print(product.product.name)
    product_list = []
    site_domain = request.build_absolute_uri('/').strip('/') # Get the site domain from the request
    total=0
    sub_total=0
    tax_amount=0
    for item in items: # For each item in the items
        product_info = {
            'productName': item.product.name,
            'productImage':  site_domain + item.product.product_image.url, # Get the product image URL
            'productPrice': item.product.price,
            'productDescription': item.product.description,
            'productQuantity': item.quantity,
        }
        product_list.append(product_info) # Append the product info to the product list
        sub_total += item.product.price * item.quantity # Calculate the sub total
        total = Decimal(sub_total) # Multiply using Decimal and assign to total variable
        tax_rate = Decimal('0.13')  
        tax_amount = total * tax_rate # Calculate the tax amount using the total and tax rate 
        tax_amount = tax_amount.quantize(Decimal('0.00')) # Round the tax amount to 2 decimal places
        total = total.quantize(Decimal('0.00')) # Round the total to 2 decimal places

    mydict = {
        'OrderID': order.id,
        'orderDate': order.order_date,
        'customerName': request.user,
        'customerEmail': order.email,
        'customerMobile': order.mobile,
        'shipmentAddress': order.address,
        'orderStatus': order.status,
        'products': product_list,
        'subTotal': sub_total,
        'taxAmount': tax_amount,
        'total': total,
    } # Create a dictionary with the order ID, order date, customer name, customer email, 
    # customer mobile, shipment address, order status, products, sub total, tax amount, and total

    return render_to_pdf('ecom/v2/base/download_invoice.html', mydict) # Render the download invoice template as a PDF with the dictionary


@login_required(login_url='login_as_customer')
@user_passes_test(is_customer)
def my_profile_view(request): # View for the customer's profile if the user is authenticated and is a customer
    customer = models.Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user
    customer_url = customer.profile_pic.url
    return render(request, 'ecom/v2/profile/my_profile.html', {'customer': customer, 'customer_url':customer_url}) # Render the my profile template with the customer and customer URL

@login_required(login_url='login_as_customer')
@user_passes_test(is_customer)
def edit_profile_view(request): # View for editing the customer's profile if the user is authenticated and is a customer 
    customer = get_object_or_404(Customer, user_id=request.user.id) # Get the customer by the user ID
    user = get_object_or_404(User, id=customer.user_id)
    customer_url = customer.profile_pic.url if customer.profile_pic else None # Get the customer's profile picture URL if it exists
    if request.method == 'POST':
        first_name = request.POST.get('first_name') # Get the first name from the request
        last_name = request.POST.get('last_name') # Get the last name from the request
        username = request.POST.get('username')
        email = request.POST.get('email') # Get the email from the request
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')
        security_question = request.POST.get('security_question') # Get the security question from the request
        security_answer = request.POST.get('security_answer')
        profile_pic = request.FILES.get('profile_pic') # Get the profile picture from the request
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email
        customer.mobile = mobile
        customer.address = address
        customer.security_question = security_question
        customer.security_answer = security_answer
        if profile_pic: # If a profile picture is provided
            if customer.profile_pic:
                default_storage.delete(customer.profile_pic.path) # Delete the existing profile picture
            customer.profile_pic = profile_pic
        try: # Try to save the user and customer
            user.save()
            customer.save()
            messages.success(request, 'Profile updated successfully')   # Show a success message if the profile is updated successfully
            return redirect('my-profile') # Redirect to the my profile page
        except ValidationError as e:
            messages.error(request, f"Error: {e}") # Show an error message if there is an error
    else:
        print("Invalid request") # Print an error message if the request is invalid
    mydict = {'user': user, 'customer': customer, 'customer_url': customer_url} # Create a dictionary with the user, customer, and customer URL
    return render(request, 'ecom/v2/profile/edit_profile.html', context=mydict) # Render the edit profile template with the context


def dashboard(request): # View for the dashboard
    categories = models.Category.objects.all() # Get all categories
    top_events = Event.objects.annotate(num_registrations=Count('eventmember')).order_by('-num_registrations')[:4] # Get the top events by the number of registrations
    top_threads = Post.objects.order_by('-date_posted')[:3] # Get the top threads by the date posted
    try:
        customer = models.Customer.objects.get(user_id=request.user.id) # Get the customer associated with the authenticated user
        customer_url = customer.profile_pic.url # Get the customer URL
    except Exception as e: 
        customer_url = 'profile_pic/default.png'
    context = {
        'categories': categories,
        'top_events': top_events,
        'top_threads': top_threads,
        'customer_url':customer_url
    } # Create a context dictionary with the categories, top events, top threads, and customer URL
    return render(request, 'ecom/v2/home/user-dashboard.html', context) # Render the user dashboard template with the context


def add_category_view(request): # View for adding a category
    if request.method == 'POST': 
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin-categories') # Redirect to the admin categories page
    else:
        form = CategoryForm()
    return render(request, 'ecom/v2/admin/category/add_category.html', {'form': form}) # Render the add category template with the form


def update_category_view(request, pk): # View for updating a category
    category = models.Category.objects.get(id = pk) # Get the category by ID   
    categoryForm = forms.CategoryForm(instance=category)
    if request.method == 'POST':
        categoryForm = CategoryForm(request.POST,request.FILES, instance=category) # Create a category form with the POST data and instance
        if categoryForm.is_valid():
            categoryForm.save()
            return redirect('admin-categories') # Redirect to the admin categories page
    return render(request, 'ecom/v2/admin/category/update_category.html', {'form': categoryForm}) # Render the update category template with the form

@login_required(login_url='login_as_admin')
def admin_categories_view(request): # View for the admin categories
    categories = models.Category.objects.all() # Get all categories 
    return render(request, 'ecom/v2/admin/category/admin_categories.html', {'categories': categories}) # Render the admin categories template with the categories


def delete_category_view(request, pk): # View for deleting a category
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete() # Delete the category
        return redirect('admin-categories')
    return render(request, 'ecom/v2/admin/category/delete_category.html', {'category': category}) # Render the delete category template with the category

def home(request): # View for the home page
    posts = Post.objects.all()
    comments = Comment.objects.all() # Get all comments
    context = {
        'posts': posts,
        'comments': comments,
    } # Create a context dictionary with the posts and comments
    return render(request, 'blog/home.html', context) # Render the home template with the context


class HomeView(TemplateView): # View for the home page
    template_name = 'home.html'


def search(request):
    template = 'blog/home.html'
    query = request.GET.get('q') # Get the query from the request
    result = Post.objects.filter(
        Q(title__icontains=query) | Q(author__user__username__icontains=query) | Q(content__icontains=query)
    ) # Filter posts by title, author username, and content containing the query

    context = {'posts': result} # Create a context dictionary with the result
    return render(request, template, context) # Render the template with the context


def getfile(request): # View for getting a file
    return serve(request, 'File')


class PostListView(ListView): # View for the post list
    model = Post
    template_name = 'blog/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    ordering = ['-date_posted'] # Order by date posted 
    paginate_by = 2

class UserPostListView(ListView): # View for the user post list
    model = Post
    template_name = 'blog/user_posts.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    paginate_by = 2 # Paginate by 2 posts

    def get_queryset(self):
        user = User.objects.get(username=self.kwargs.get('username')) # Get the user by the username
        return Post.objects.filter(author__user__username=user.username) # Filter posts by the author's username 


class PostDetailView(DetailView): # View for the post detail page
    model = Post
    template_name = 'blog/post_detail.html' # Template for the post detail page

class PostCreateView(LoginRequiredMixin, CreateView):  # View for creating a post
    model = Post
    template_name = 'blog/post_form.html'
    fields = ['title', 'content', 'file']

    def form_valid(self, form):
        customer = Customer.objects.get(user=self.request.user) # Get the customer associated with the authenticated user
        form.instance.author = customer
        return super().form_valid(form) # Call the parent class's form_valid method

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView): 
    model = Post
    template_name = 'blog/post_form.html' # <app>/<model>_form.html
    fields = ['title', 'content', 'file'] # Fields to display in the form

    def form_valid(self, form): # If the form is valid
        customer = Customer.objects.get(user=self.request.user)
        form.instance.author = customer # Set the author of the post to the customer
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author.user


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog-home') # Redirect to the home page after deleting a post
    template_name = 'blog/post_confirm_delete.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author.user


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})


def post_detail(request, pk):  # View for the post detail page
    post = get_object_or_404(Post, pk=pk) # Get the post by ID using get_object_or_404
    comments = post.comments.filter(parent=None) # Get the comments for the post
    reply_form = ReplyForm()

    if request.method == 'POST':
        if 'comment_form' in request.POST: # If the comment form is in the POST request
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid(): # If the comment form is valid
                new_comment = comment_form.save(commit=False)
                customer = Customer.objects.get(user=request.user) # Get the customer associated with the authenticated user
                new_comment.post = post
                new_comment.author = customer
                new_comment.save() # Save the new comment to the database
                return redirect('post-detail', pk=post.pk) # Redirect to the post detail page
        elif 'reply_form' in request.POST: # If the reply form is in the POST request
            reply_form = ReplyForm(request.POST)
            if reply_form.is_valid(): # If the reply form is valid
                parent_id = request.POST.get('parent_id') # Get the parent ID from the POST request
                parent_comment = get_object_or_404(Comment, id=parent_id)
                new_reply = reply_form.save(commit=False)
                customer = Customer.objects.get(user=request.user) # Get the customer associated with the authenticated user
                new_reply.post = post
                new_reply.author = customer
                new_reply.parent = parent_comment
                new_reply.save() # Save the new reply to the database 
                return redirect('post-detail', pk=post.pk) # Redirect to the post detail page
    else:
        comment_form = CommentForm() # Create a comment form

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'reply_form': reply_form,
    } # Create a context dictionary with the post, comments, comment form, and reply form

    return render(request, 'blog/post_detail.html', context) # Render the post detail template with the context
