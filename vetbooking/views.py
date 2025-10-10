from datetime import date

import pet
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Appointment, Pet, Vet, Product, Order, Notification, Booking, CartItem, VetBooking
from .forms import PetForm, AppointmentForm, SignupForm, LoginForm, VetForm, ProductForm
# from django.contrib.auth.models import User

from django.shortcuts import get_object_or_404

# vet = get_object_or_404(Vet, id=vet)
# pet = get_object_or_404(Pet, id=pet, owner=user_passes_test)

# 🔒 Check if user is admin
def is_admin(user):
    return user.is_staff or user.is_superuser


# ------------------------ AUTH -----------------------------

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Signup successful! You can now login.")
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'vetbooking/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Invalid credentials.")
    else:
        form = LoginForm()
    return render(request, 'vetbooking/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ------------------------ HOME -----------------------------
def home(request):
    return render(request, 'vetbooking/home.html')


# ------------------------ PET CRUD --------------------------
@login_required(login_url='/login/')
def add_pet(request):
    if request.method == 'POST':
        form = PetForm(request.POST)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()
            messages.success(request, "Pet added successfully!")
            return redirect('my_pets')
    else:
        form = PetForm()
    return render(request, 'add_pet.html', {'form': form})


@login_required(login_url='/login/')
def my_pets(request):
    pets = Pet.objects.filter(owner=request.user)
    return render(request, 'my_pets.html', {'pets': pets})


# ------------------------ VET (ADMIN + USER) ------------------------

# ADMIN — View all vets
@user_passes_test(is_admin)
def vet_list(request):
    vets = Vet.objects.all()
    return render(request, 'vet_list.html', {'vets': vets})


# ADMIN — Add Vet
@user_passes_test(is_admin)
def add_vet(request):
    if request.method == 'POST':
        form = VetForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Vet doctor added successfully!")
            return redirect('vet_list')
    else:
        form = VetForm()
    return render(request, 'add_vet.html', {'form': form})


# ADMIN — Edit Vet
@user_passes_test(is_admin)
def edit_vet(request, vet_id):
    vet = get_object_or_404(Vet, id=vet_id)
    if request.method == 'POST':
        form = VetForm(request.POST, request.FILES, instance=vet)
        if form.is_valid():
            form.save()
            messages.success(request, "Vet details updated successfully!")
            return redirect('vet_list')
    else:
        form = VetForm(instance=vet)
    return render(request, 'edit_vet.html', {'form': form})


# ADMIN — Delete Vet
@user_passes_test(is_admin)
def delete_vet(request, vet_id):
    vet = get_object_or_404(Vet, id=vet_id)
    vet.delete()
    messages.success(request, "Vet deleted successfully!")
    return redirect('vet_list')


# USER — View available vets
@login_required(login_url='/login/')
def available_vets(request):
    vets = Vet.objects.filter(is_available=True)
    return render(request, 'available_vets.html', {'vets': vets})


# ------------------------ APPOINTMENT ------------------------
@login_required
def book_vet(request):
    user = request.user
    vets = Vet.objects.all()
    pets = Pet.objects.filter(owner=user)
    today = date.today()

    if request.method == 'POST':
        vet_id = request.POST.get('vet_id')
        pet_id = request.POST.get('pet_id')
        date_input = request.POST.get('date')
        time_input = request.POST.get('time')
        notes = request.POST.get('notes')

        # Validate date not in the past
        if date_input < str(today):
            messages.error(request, "You cannot select a past date.")
            return redirect('book_vet')

        # Get Vet and Pet objects safely
        vet = get_object_or_404(Vet, id=vet_id)
        pet = get_object_or_404(Pet, id=pet_id, owner=user)

        # Check if vet already booked at same date/time
        if VetBooking.objects.filter(vet=vet, date=date_input, time=time_input).exists():
            messages.error(request, "This vet is already booked at the selected date and time.")
            return redirect('book_vet')

        # Create booking
        VetBooking.objects.create(
            user=user,
            vet=vet,
            pet=pet,
            date=date_input,
            time=time_input,
            notes=notes,
            status='Pending'
        )

        messages.success(request, "Your appointment has been booked successfully!")
        return redirect('book_vet')

    return render(request, 'vetbooking/book_vet.html', {
        'vets': vets,
        'pets': pets,
        'today': today
    })
# ------------------------ PRODUCTS / MEDICINES ------------------------

@user_passes_test(is_admin)
def admin_products(request):
    products = Product.objects.all()
    return render(request, 'admin_products.html', {'products': products})


@user_passes_test(is_admin)
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock', 0)
        image = request.FILES.get('image')

        Product.objects.create(
            name=name,
            description=description,
            price=price,
            stock=stock,
            image=image,
            is_published=True
        )
        messages.success(request, "Product added successfully!")
        return redirect('admin_products')

    return render(request, 'add_product.html')

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

# ------------------------ ORDERS ------------------------
@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'vetbooking/notifications.html', {'notifications': notifications})

def products(request):
    products = Product.objects.all()
    return render(request, 'products.html', {'products': products})





@login_required
def buy_now(request, product_id):
    # Step 1: Get the product by id
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        # Step 2: Create a booking/order
        booking = Booking.objects.create(
            user=request.user,
            product=product,
            status='Pending'  # or any default status
        )
        # Step 3: Redirect to a success page
        return redirect('booking_success', booking_id=booking.id)

    # Step 4: If GET, render the product details page
    return render(request, 'vetbooking/buy_now.html', {'product': product})


def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'vetbooking/booking_success.html', {'booking': booking})

def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, f"Product '{product.name}' has been deleted successfully!")
    return redirect('admin_product_list')  # Redirect to your product list page



def edit_product(request, product_id):
    # Get the product or show 404
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        # Bind form with POST data and existing product instance
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('admin_product_list')  # Redirect to product list page
    else:
        # Display form with existing product data
        form = ProductForm(instance=product)

    return render(request, 'vetbooking/edit_product.html', {'form': form, 'product': product})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Check if product is already in cart
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)

    total = sum(item.total_price() for item in cart_items)

    return render(request, 'vetbooking/cart.html', {'cart_items': cart_items, 'total': total})



@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(CartItem, id=cart_id, user=request.user)
    cart_item.delete()  # Delete the item from the cart
    return redirect('cart')


def buy_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        # Create an order (simple example)
        Order.objects.create(
            user=request.user,
            product=product,
            price=product.price
        )
        messages.success(request, f"You have successfully bought {product.name}!")
        return redirect('product_list')  # Redirect to products page or anywhere

    return redirect('product_detail', product_id=product.id)