from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 🏠 Home & Auth
    path('', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # 🐾 PET MANAGEMENT
    path('add-pet/', views.add_pet, name='add_pet'),
    path('my-pets/', views.my_pets, name='my_pets'),

    # 🩺 VET MANAGEMENT
    path('book-vet/', views.book_vet, name='book_vet'),
    path('vets/', views.available_vets, name='available_vets'),  # for users

    # 👨‍⚕️ ADMIN — Vet Management
    path('admin/vets/', views.vet_list, name='vet_list'),
    path('admin/vets/add/', views.add_vet, name='add_vet'),
    path('admin/vets/edit/<int:vet_id>/', views.edit_vet, name='edit_vet'),
    path('admin/vets/delete/<int:vet_id>/', views.delete_vet, name='delete_vet'),

    # 🛍️ PRODUCT (MEDICINE) MANAGEMENT
    # path('products/', views.products, name='products'),
    path('buy/<int:product_id>/', views.buy_now, name='buy_now'),


    path('products/', views.products, name='products'),
    path('products/', views.product_list, name='product_list'),
    path('admin/products/', views.admin_products, name='admin_products'),


    # 👨‍⚕️ ADMIN — Product Management
    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin/products/add/', views.add_product, name='add_product'),
    path('admin/products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('admin/products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('buy/<int:product_id>/', views.buy_product, name='buy_product'),
    # 🧾 CART & NOTIFICATIONS
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='cart'),
    path('notifications/', views.notifications, name='notifications'),
]

# 🖼️ Serve uploaded images during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
