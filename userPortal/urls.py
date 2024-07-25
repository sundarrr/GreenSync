from django.conf.urls.static import static
from django.contrib.auth.views import LoginView
from django.urls import path
from GreenSyncIAT import settings # Importing settings from GreenSyncIAT
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
    customer_register_view,
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
    admin_dashboard_view,
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
    decrease_quantity,
    forgot_password,
    set_new_password,
    security_question,
    decrease_quantity, get_event_details
) # Importing views from views.py

urlpatterns = [
    path('', home_view, name=''), # Home page
    path('afterlogin', afterlogin_view, name='afterlogin'), # After login page 
    path('logout/', logout_view, name='logout'), # Logout page
    path('dashboard', dashboard, name='dashboard'), # Dashboard page
    path('search', search_view, name='product-search'), # Search page
    path('autosuggest/', autosuggest, name='autosuggest'), # Autosuggest page
    path('register_event/<int:event_id>/', register_event, name='register_event'), # Register event page
    path('cancel_registration/<int:event_id>/', cancel_registration, name='cancel_registration'), # Cancel registration page
    path('events/', event_view, name='events'), # Events page
    path('get_event_details/<int:event_id>/', get_event_details, name='get_event_details'), # Get event details page
    path('admin_dashboard', admin_dashboard_view), # Admin dashboard page
    path('admin-portal/', admin_portal_view, name='admin-portal'), # Admin portal page
    path('login_as_admin', LoginView.as_view(template_name='ecom/v2/login/admin_login.html'), name='login_as_admin'), # Admin login page
    path('admin-dashboard', admin_dashboard_view, name='admin-dashboard'), # Admin dashboard page
    path('admin-products', admin_products_view, name='admin-products'), # Admin products page
    path('admin-add-product', admin_add_product_view, name='admin-add-product'), # Admin add product page
    path('delete-product/<int:pk>', delete_product_view, name='delete-product'), # Delete product page
    path('update-product/<int:pk>', update_product_view, name='update-product'), # Update product page
    path('admin-view-booking', admin_view_booking_view, name='admin-view-booking'), # Admin view booking page
    path('delete-order/<int:pk>', delete_order_view, name='delete-order'), # Delete order page
    path('update-order/<int:pk>', update_order_view, name='update-order'), # Update order page
    path('about_us', about_us, name='about_us'), # About us page
    path('details', details, name='details'), # Details page
    path('terms_and_condition', terms_and_condition, name='terms_and_condition'), # Terms and condition page
    path('privacy_policy', privacy_policy, name='privacy_policy'), # Privacy policy
    path('register_as_customer', customer_register_view), # Register as customer page
    path('login_as_customer', LoginView.as_view(template_name='ecom/v2/login/customer_login.html'), name='login_as_customer'),
    path('forgot-password/', forgot_password, name='forgot_password'), # Forgot password page
    path('security-question/', security_question, name='security_question'), # Security question page
    path('set-new-password/', set_new_password, name='set_new_password'), # Set new password page  
    path('accounts/login/', LoginView.as_view(template_name='ecom/v2/login/customer_login.html'), name='accounts/login/'),
    path('customer-home/', customer_home_view, name='customer-home'), # Customer home page
    path('my-order', my_order_view, name='my-order'), # My order page
    path('my-profile', my_profile_view, name='my-profile'), # My profile page
    path('edit-profile', edit_profile_view, name='edit-profile'), # Edit profile page
    path('download-invoice/<int:orderID>', download_invoice_view, name='download-invoice'), # Download invoice page
    path('add-to-cart/<int:product_id>', add_to_cart_view, name='add-to-cart'), # Add to cart page
    path('cart', cart_view, name='cart'), # Cart page
    path('remove-from-cart/<int:product_id>', remove_from_cart_view, name='remove-from-cart'), # Remove from cart page
    path('increase-quantity/<int:product_id>', increase_quantity, name='increase-quantity'), # Increase quantity page
    path('decrease-quantity/<int:product_id>', decrease_quantity, name='decrease-quantity'), # Decrease quantity page
    path('customer-address', customer_address_view, name='customer-address'), # Customer address page
    path('payment-success', payment_success_view, name='payment-success'), # Payment success page
    path('admin-categories', admin_categories_view, name='admin-categories'), # Admin categories page
    path('add-category/', add_category_view, name='add-category'), # Add category page
    path('update-category/<int:pk>/', update_category_view, name='update-category'), # Update category page
    path('delete-category/<int:pk>/', delete_category_view, name='delete-category'), # Delete category page
    path('forum', home, name='blog-home'), # Forum page
    path('user/<str:username>', UserPostListView.as_view(), name='user-posts'), # User posts page
    path('post/<int:pk>/', post_detail, name='post-detail'), # Post detail page
    path('post/new/', PostCreateView.as_view(), name='post-create'), # Post create page
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'), # Post update page
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'), # Post delete page
    path('about/', about, name='blog-about'), # About page
    path('search/', search, name='search'), # Search page
]

if settings.DEBUG: # This is used to serve media files in development environment
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # This is used to serve media files in development environment
