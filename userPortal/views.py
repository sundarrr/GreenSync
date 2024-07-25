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
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    if event.registration_count >= event.maximum_attende:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': "Event full. Unable to Register."})
        else:
            messages.error(request, "Event full. Unable to Register.")
            return redirect('events')

    registration, created = EventRegistration.objects.get_or_create(event=event, user=user)
    if created:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            send_email(user.email,
                       'Event Registration Success',
                       f'Hi {user.username},<br><br>You have successfully registered to the {event.name} event.<br><br>Regards,<br>EcoGreenSmart Team')
            return JsonResponse({'success': True, 'event_name': event.name})
        else:
            messages.success(request, f"You have successfully registered to {event.name} event.")
            send_email(user.email,
                       'Event Registration Success',
                       f'Hi {user.username},<br><br>You have successfully registered to the {event.name} event.<br><br>Regards,<br>EcoGreenSmart Team')
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f"You are already registered to {event.name} event."})
        else:
            messages.info(request, f"You are already registered to {event.name} event.")

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
    registrations = EventRegistration.objects.filter(user=request.user) if request.user.is_authenticated else EventRegistration.objects.none()
    registered_event_ids = registrations.values_list('event_id', flat=True)
    event_statuses = {event.id: 'full' if event.registration_count >= event.maximum_attende else 'open' for event in events}
    customer_url = ''
    if request.user.is_authenticated:
        try:
            customer = models.Customer.objects.get(user_id=request.user.id)
            customer_url = customer.profile_pic.url
        except ObjectDoesNotExist:
            customer_url = ''

    if query:
        events = events.filter(name__icontains=query)
    if category:
        events = events.filter(category__name=category)

    categories = EventCategory.objects.all()

    context = {
        'events': events,
        'categories': categories,
        'customer_url': customer_url,
        'registered_event_ids': registered_event_ids,
        'event_statuses': event_statuses,
    }
    return render(request, 'ecom/v2/home/events.html', context)

def autosuggest_view(request):
    query = request.GET.get('query', '')
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

@login_required(login_url='login_as_admin')
def admin_dashboard_view(request):
    return HttpResponseRedirect('admin-dashboard')


def customer_register_view(request):
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
        return HttpResponseRedirect('login_as_customer')
    return render(request, 'ecom/v2/signup/customer_register.html', context=mydict)


def forgot_password(request):
    if request.method == 'POST':
        form = UsernameForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = User.objects.get(username=username)
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
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been updated!')
            return redirect('login_as_customer')
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


@login_required(login_url='login_as_admin')
def admin_dashboard_view(request):
    # for cards on dashboard
    customercount = Customer.objects.all().count()
    productcount = Product.objects.all().count()
    ordercount = Order.objects.all().count()

    # for recent order tables
    orders = models.Order.objects.all().order_by('-id')
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = order.items.all()
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
@login_required(login_url='login_as_admin')
def admin_products_view(request):
    products = models.Product.objects.all()
    return render(request, 'ecom/v2/admin/admin_products.html', {'products': products})


# admin add product by clicking on floating button
@login_required(login_url='login_as_admin')
def admin_add_product_view(request):
    productForm = forms.ProductForm()
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES)
        if productForm.is_valid():
            productForm.save()
        return HttpResponseRedirect('admin-products')
    return render(request, 'ecom/v2/admin/admin_add_products.html', {'productForm': productForm})


@login_required(login_url='login_as_admin')
def delete_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    product.delete()
    return redirect('admin-products')


@login_required(login_url='login_as_admin')
def update_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    productForm = forms.ProductForm(instance=product)
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES, instance=product)
        if productForm.is_valid():
            productForm.save()
            return redirect('admin-products')
    return render(request, 'ecom/v2/admin/admin_update_product.html', {'productForm': productForm})


@login_required(login_url='login_as_admin')
def admin_view_booking_view(request):
    orders = Order.objects.all()
    data = []

    for order in orders:
        ordered_products = order.items.all()
        ordered_by = Customer.objects.get(id=order.customer.id)
        data.append({
            'order': order,
            'products': ordered_products,
            'customer': ordered_by
        })

    return render(request, 'ecom/v2/admin/admin_view_booking.html', {'data': data})


@login_required(login_url='login_as_admin')
def delete_order_view(request, pk):
    order = models.Order.objects.get(id=pk)
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
@login_required(login_url='login_as_admin')
def update_order_view(request, pk):
    order = models.Order.objects.get(id=pk)
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
                   'product_count_in_cart': product_count_in_cart, 'query': query})

@login_required(login_url='login_as_customer')
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    thisCustomer = models.Customer.objects.get(user_id=request.user.id)
    cart, created = Cart.objects.get_or_create(customer=thisCustomer)
    cart_product, created = CartProduct.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_product.quantity += 1
        cart_product.save()
    else:
        pass
    return redirect('cart')


def remove_from_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    thisCustomer = models.Customer.objects.get(user_id=request.user.id)
    cart = get_object_or_404(Cart, customer=thisCustomer)
    cart_product = get_object_or_404(CartProduct, cart=cart, product=product)
    cart_product.delete()
    return redirect('cart')


def update_quantity(request, product_id, should_increase=True):
    product = get_object_or_404(Product, id=product_id)
    thisCustomer = models.Customer.objects.get(user_id=request.user.id)
    cart = get_object_or_404(Cart, customer=thisCustomer)
    cart_product = get_object_or_404(CartProduct, cart=cart, product=product)
    if should_increase:
        cart_product.quantity = cart_product.quantity + 1
    else:
        cart_product.quantity = cart_product.quantity - 1
    cart_product.save()


def increase_quantity(request, product_id):
    update_quantity(request, product_id, True)
    return redirect('cart')


def decrease_quantity(request, product_id):
    update_quantity(request, product_id, False)
    return redirect('cart')


def get_cart(request):
    thisCustomer = models.Customer.objects.get(user_id=request.user.id)
    cart = get_object_or_404(Cart, customer=thisCustomer)
    cart_products = CartProduct.objects.filter(cart=cart)
    total = sum(cp.product.price * cp.quantity for cp in cart_products)
    total = Decimal(total) # Multiply using Decimal
    tax_rate = Decimal('0.13')  # Use a string to initialize the Decimal
    tax_amount = total * tax_rate
    total = total + tax_amount
    total = total.quantize(Decimal('0.00'))
    product_count_in_cart = len(cart_products)
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
    }
    return context


def cart_view(request):
    user = User.objects.get(id=request.user.id)
    customer = Customer.objects.get(user=user)
    customer_url = customer.profile_pic.url
    cart_context = get_cart(request)
    cart_context['customer_url'] = customer_url
    return render(request, 'ecom/v2/cart/cart.html', cart_context)

@login_required(login_url='login_as_customer')
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
    return render(request, 'ecom/v2/home/customer_home.html',
                  {'products': products,'customer_url':customer_url, 'categories': categories, 'product_count_in_cart': product_count_in_cart})

@login_required(login_url='login_as_customer')
def customer_address_view(request):
    cart = get_cart(request)
    product_in_cart = cart['product_count_in_cart'] > 0
    product_count_in_cart = cart['product_count_in_cart']
    customer = Customer.objects.get(user_id=request.user.id)
    customer_url = customer.profile_pic.url
    addressForm = forms.AddressForm()
    if request.method == 'POST':
        addressForm = forms.AddressForm(request.POST)
        if addressForm.is_valid():
            email = addressForm.cleaned_data['Email']
            mobile = addressForm.cleaned_data['Mobile']
            address = addressForm.cleaned_data['Address']
            cart_details = Cart.objects.get(customer=customer)
            cart_details.email = email
            cart_details.mobile = mobile
            cart_details.address= address
            cart_details.save()
            total = cart['total']
            response = render(request, 'ecom/v2/cart/payment.html', {'total': total,'customer_url':customer_url})
            response.set_cookie('email', email)
            response.set_cookie('mobile', mobile)
            response.set_cookie('address', address)
            return response
    return render(request, 'ecom/v2/cart/customer_address.html',
                  {'addressForm': addressForm, 'product_in_cart': product_in_cart,
                   'product_count_in_cart': product_count_in_cart, 'customer_url':customer_url})


@login_required(login_url='login_as_customer')
def payment_success_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    cart_model_instance = get_cart(request)
    cart_products = cart_model_instance['products']
    email = request.COOKIES.get('email')
    mobile = request.COOKIES.get('mobile')
    address = request.COOKIES.get('address')
    customer = Customer.objects.get(user_id=request.user.id)
    customer_url = customer.profile_pic.url
    try:
        # Create the order
        order = models.Order.objects.create(
            customer=customer,
            email=email,
            mobile=mobile,
            address=address,
            status='Pending'
        )
        for cart_product in cart_products:
            item = models.Item.objects.create(
                product=cart_product.product,
                quantity=cart_product.quantity
            )
            order.items.add(item)
            product = cart_product.product
            product.stock -= cart_product.quantity
            product.save()

        order.save()
        cart_model_instance.cartproduct_set.all().delete()
        cart_model_instance.delete()
    except Exception as e:
        print(e)

    response = render(request, 'ecom/v2/cart/payment_success.html',{'customer_url':customer_url})
    response.delete_cookie('email')
    response.delete_cookie('mobile')
    response.delete_cookie('address')
    return response

def my_order_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    orders = models.Order.objects.filter(customer_id=customer).order_by('-id')
    customer_url = customer.profile_pic.url
    return render(request, 'ecom/v2/cart/my_order.html',
                  {'orders': orders,'customer_url':customer_url})

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return

@login_required(login_url='login_as_customer')
@user_passes_test(is_customer)
def download_invoice_view(request, orderID):
    order = get_object_or_404(models.Order, id=orderID)
    items = order.items.all()  # Assuming there's a related name `products` in the Orders model.
    print("invoice")
    for product in items:
        print(product.product.name)
    product_list = []
    site_domain = request.build_absolute_uri('/').strip('/')
    total=0
    sub_total=0
    tax_amount=0
    for item in items:
        product_info = {
            'productName': item.product.name,
            'productImage':  site_domain + item.product.product_image.url,
            'productPrice': item.product.price,
            'productDescription': item.product.description,
            'productQuantity': item.quantity,
        }
        product_list.append(product_info)
        sub_total += item.product.price * item.quantity
        total = Decimal(sub_total)  # Multiply using Decimal
        tax_rate = Decimal('0.13')  # Use a string to initialize the Decimal
        tax_amount = total * tax_rate
        tax_amount = tax_amount.quantize(Decimal('0.00'))
        total = total.quantize(Decimal('0.00'))

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
    }

    return render_to_pdf('ecom/v2/base/download_invoice.html', mydict)


@login_required(login_url='login_as_customer')
@user_passes_test(is_customer)
def my_profile_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    customer_url = customer.profile_pic.url
    return render(request, 'ecom/v2/profile/my_profile.html', {'customer': customer, 'customer_url':customer_url})

@login_required(login_url='login_as_customer')
@user_passes_test(is_customer)
def edit_profile_view(request):
    print("Starting edit_profile_view")
    customer = get_object_or_404(Customer, user_id=request.user.id)
    user = get_object_or_404(User, id=customer.user_id)
    print(f"Fetched customer: {customer}, user: {user}")
    customer_url = customer.profile_pic.url if customer.profile_pic else None
    print(f"Customer profile pic URL: {customer_url}")

    if request.method == 'POST':
        print("POST request received")
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')
        security_question = request.POST.get('security_question')
        security_answer = request.POST.get('security_answer')
        profile_pic = request.FILES.get('profile_pic')

        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email

        customer.mobile = mobile
        customer.address = address
        customer.security_question = security_question
        customer.security_answer = security_answer
        if profile_pic:
            if customer.profile_pic:
                default_storage.delete(customer.profile_pic.path)
            customer.profile_pic = profile_pic

        try:
            user.save()
            customer.save()
            print("User and customer information updated successfully")
            messages.success(request, 'Profile updated successfully')
            return redirect('my-profile')
        except ValidationError as e:
            print(f"Error updating profile: {e}")
            messages.error(request, f"Error updating profile: {e}")

    else:
        print("GET request received")

    mydict = {'user': user, 'customer': customer, 'customer_url': customer_url}
    print(f"Rendering template with context: {mydict}")
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
    category = models.Category.objects.get(id=pk)
    categoryForm = forms.CategoryForm(instance=category)
    if request.method == 'POST':
        categoryForm = CategoryForm(request.POST,request.FILES, instance=category)
        if categoryForm.is_valid():
            categoryForm.save()
            return redirect('admin-categories')
    return render(request, 'ecom/v2/admin/category/update_category.html', {'form': categoryForm})

# admin view the product
@login_required(login_url='login_as_admin')
def admin_categories_view(request):
    categories = models.Category.objects.all()
    return render(request, 'ecom/v2/admin/category/admin_categories.html', {'categories': categories})


def delete_category_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('admin-categories')
    return render(request, 'ecom/v2/admin/category/delete_category.html', {'category': category})

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
        user = User.objects.get(username=self.kwargs.get('username'))
        return Post.objects.filter(author__user__username=user.username)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/post_form.html'
    fields = ['title', 'content', 'file']

    def form_valid(self, form):
        customer = Customer.objects.get(user=self.request.user)
        form.instance.author = customer
        return super().form_valid(form)

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
    success_url = reverse_lazy('blog-home')
    template_name = 'blog/post_confirm_delete.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author.user


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.filter(parent=None)
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
