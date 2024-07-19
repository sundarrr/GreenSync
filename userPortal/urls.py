from django.conf.urls.static import static
from django.contrib.auth.views import LoginView
from django.urls import path

from GreenSyncIAT import settings
from .views import (
    admin_add_product_view,
    admin_dashboard_view,
    admin_products_view,
    afterlogin_view,
    add_to_cart_view,
    cart_view,
    home_view,
    customer_address_view,
    customer_home_view,
    customer_signup_view,
    delete_order_view,
    delete_product_view,
    download_invoice_view,
    edit_profile_view,
    my_order_view,
    my_profile_view,
    payment_success_view,
    remove_from_cart_view,
    search_view,
    update_order_view,
    update_product_view,
    dashboard,
    adminclick_view,
    admin_view_booking_view,
    add_category_view,
    update_category_view,
    delete_category_view,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,
    UserPostListView,
    post_detail,
    about,
    home,
    search,
    admin_categories_view,
    autosuggest,
    event_view,
    admin_portal_view,
    register_event,
    cancel_registration,
    about_us,
    details,
    terms_and_condition,
    privacy_policy,
    logout_view,
    increase_quantity,
    decrease_quantity
)

urlpatterns = [
    path('', home_view, name=''),
    path('afterlogin', afterlogin_view, name='afterlogin'),
    path('logout/', logout_view, name='logout'),
    #path('logout', LogoutView.as_view(template_name='ecom/v2/logout/logout.html'), name='logout'),
    path('dashboard', dashboard, name='dashboard'),
    path('search', search_view, name='product-search'),
    path('autosuggest/', autosuggest, name='autosuggest'),
    path('register_event/<int:event_id>/', register_event, name='register_event'),
    path('cancel_registration/<int:event_id>/', cancel_registration, name='cancel_registration'),
    path('events/', event_view, name='events'),

    path('adminclick', adminclick_view),
    path('admin-portal/', admin_portal_view, name='admin-portal'),
    path('adminlogin', LoginView.as_view(template_name='ecom/v2/login/admin_login.html'), name='adminlogin'),
    path('admin-dashboard', admin_dashboard_view, name='admin-dashboard'),

    path('admin-products', admin_products_view, name='admin-products'),
    path('admin-add-product', admin_add_product_view, name='admin-add-product'),
    path('delete-product/<int:pk>', delete_product_view, name='delete-product'),
    path('update-product/<int:pk>', update_product_view, name='update-product'),

    path('admin-view-booking', admin_view_booking_view, name='admin-view-booking'),
    path('delete-order/<int:pk>', delete_order_view, name='delete-order'),
    path('update-order/<int:pk>', update_order_view, name='update-order'),

    path('about_us', about_us, name='about_us'),
    path('details', details, name='details'),
    path('terms_and_condition', terms_and_condition, name='terms_and_condition'),
    path('privacy_policy', privacy_policy, name='privacy_policy'),

    path('customersignup', customer_signup_view),
    path('customerlogin', LoginView.as_view(template_name='ecom/v2/login/customer_login.html'), name='customerlogin'),
    path('accounts/login/', LoginView.as_view(template_name='ecom/v2/login/customer_login.html'), name='accounts/login/'),
    path('customer-home/', customer_home_view, name='customer-home'),
    path('my-order', my_order_view, name='my-order'),
    path('my-profile', my_profile_view, name='my-profile'),
    path('edit-profile', edit_profile_view, name='edit-profile'),
    path('download-invoice/<int:orderID>', download_invoice_view, name='download-invoice'),

    path('add-to-cart/<int:product_id>', add_to_cart_view, name='add-to-cart'),
    path('cart', cart_view, name='cart'),
    path('remove-from-cart/<int:product_id>', remove_from_cart_view, name='remove-from-cart'),
    path('increase-quantity/<int:product_id>', increase_quantity, name='increase-quantity'),
    path('decrease-quantity/<int:product_id>', decrease_quantity, name='decrease-quantity'),

    
    path('customer-address', customer_address_view, name='customer-address'),
    path('payment-success', payment_success_view, name='payment-success'),

    path('admin-categories', admin_categories_view, name='admin-categories'),
    path('add-category/', add_category_view, name='add-category'),
    path('update-category/<int:pk>/', update_category_view, name='update-category'),
    path('delete-category/<int:pk>/', delete_category_view, name='delete-category'),

    path('forum', home, name='blog-home'),
    path('user/<str:username>', UserPostListView.as_view(), name='user-posts'),
    path('post/<int:pk>/', post_detail, name='post-detail'),
    path('post/new/', PostCreateView.as_view(), name='post-create'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('about/', about, name='blog-about'),
    path('search/', search, name='search'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
