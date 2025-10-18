from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from vetbooking import views

urlpatterns = [
    # 🏠 Home & Authentication
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # 🐾 Pet Management
    path('add-pet/', views.add_pet, name='add_pet'),
    path('my-pets/', views.my_pets, name='my_pets'),

    # 🩺 Vet Management
    path('book-vet/', views.book_vet, name='book_vet'),
    path('vets/', views.available_vets, name='available_vets'),
    path('vaccinations-home/', views.vaccination_home, name='vaccination_home'),
    path('health-tips/', views.health_tips, name='health_tips'),

    # 🛍️ Product & Cart Management
    path('products/', views.product_list, name='product_list'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/decrease/<int:product_id>/', views.decrease_cart_item, name='decrease_cart_item'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('buy/<int:product_id>/', views.add_to_cart_and_checkout, name='buy_now'),
    path('orders/', views.order_history, name='order_history'),

    # 💳 Checkout & Payment
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('payment-success/', views.success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('order-success/', views.order_success, name='order_success'),

    # 🔒 Admin Section
    path('admin-login/', views.admin_login, name='admin-login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),

    # 🔔 Notifications
    path('notifications/', views.notifications, name='notifications'),
]

# 🖼️ Serve uploaded images & static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
