from datetime import date, timezone
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Appointment, Pet, Vet, Notification, Booking, CartItem
from .forms import PetForm, SignupForm, LoginForm, VetForm, ProductForm
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from .models import Order, Product
import stripe
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
stripe.api_key = settings.STRIPE_SECRET_KEY
from django.views.decorators.csrf import csrf_exempt
import json

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def create_checkout_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        cart = data.get('cart', [])

        if not cart:
            return JsonResponse({'error': 'Cart is empty'})

        line_items = []
        for item in cart:
            if item['quantity'] > 0 and item['price'] > 0:
                line_items.append({
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {'name': item['name']},
                        'unit_amount': int(float(item['price']) * 100),  # ₹ → paise
                    },
                    'quantity': int(item['quantity']),
                })

        if not line_items:
            return JsonResponse({'error': 'No valid items to pay for!'})

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/payment-success/?session_id={CHECKOUT_SESSION_ID}'),
            cancel_url=request.build_absolute_uri('/checkout/')
        )

        return JsonResponse({'url': checkout_session.url})
    except Exception as e:
        return JsonResponse({'error': str(e)})

@login_required
def order_history(request):
    """
    Displays a list of all orders for the current user.
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at') # Get orders, newest first
    context = {
        'orders': orders
    }
    return render(request, 'order_history.html', context)

@login_required
def remove_from_cart(request, product_id): # <--- CRITICAL FIX: The signature must be 'product_id'
    """
    Removes a specific CartItem for the user based on the Product ID.
    """
    if request.method == 'GET':
        try:
            # Find the specific CartItem for the current user and Product ID
            cart_item = CartItem.objects.get(
                user=request.user,
                product__id=product_id # This correctly filters by the product's ID
            )
            product_name = cart_item.product.name
            cart_item.delete()
            messages.success(request, f"'{product_name}' has been removed from your cart.")

        except CartItem.DoesNotExist:
            messages.error(request, "Item not found in your cart.")

        # Redirect to the cart view
        return redirect('cart')

    return redirect('cart') # Handle unexpected method
def success(request):
    session_id = request.GET.get('session_id')
    session = None
    if session_id and session_id != "{CHECKOUT_SESSION_ID}":
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.InvalidRequestError:
            session = None
    return render(request, 'success.html', {'session': session})
def payment_cancel(request):
    return render(request, "cancel.html")

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET  # set this after creating webhook
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponseBadRequest()
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # TODO: mark order/booking as paid using session.id or session.metadata
    return HttpResponse(status=200)

def is_admin(user):
    return user.is_staff or user.is_superuser
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin-dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'admin-login.html')
@login_required(login_url='admin_login')
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')

    vets_count = Vet.objects.count()
    appointments_count = Appointment.objects.count()
    products_count = Product.objects.count()

    return render(request, 'admin_dashboard.html', {
        'vets_count': vets_count,
        'appointments_count': appointments_count,
        'products_count': products_count
    })


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

# yourapp/views.py

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

@login_required(login_url='login')
def book_vet(request):
    if request.method == 'POST':
        vet_id = request.POST.get('vet_id')
        pet_id = request.POST.get('pet_id')
        date_input = request.POST.get('date')
        time_input = request.POST.get('time')
        notes = request.POST.get('notes')

        vet = Vet.objects.get(id=vet_id)
        pet = Pet.objects.get(id=pet_id)

        booking = Appointment.objects.create(
            user=request.user,
            vet=vet,
            pet=pet,
            date=date_input,
            time=time_input,
            notes=notes,
            status='Pending'
        )

        # 🔔 Create notification
        Notification.objects.create(
            user=request.user,
            message=f"Your appointment with Dr. {vet.name} is pending approval.",
            status='Pending'
        )

        return redirect('notifications')

    vets = Vet.objects.all()
    pets = Pet.objects.filter(owner=request.user)
    return render(request, 'vetbooking/book_vet.html', {'vets': vets, 'pets': pets})

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


@login_required
def product_list(request):
    """Fetches all published products to display in the grid."""
    # Assuming 'is_published=True' means the product is live
    products = Product.objects.filter(is_published=True).order_by('-created_at')

    context = {
        'products': products
    }

    # Ensure this renders the renamed template: product_list.html
    return render(request, 'product_list.html', context)
# ------------------------ ORDERS ------------------------

@login_required(login_url='login')
def notifications(request):
    notes = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'vetbooking/notifications.html', {'notifications': notes})




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
def admin_logout(request):
    # Clear session or authentication data
    request.session.flush()
    return redirect('admin-login')

@login_required
def manage_products(request):
    products = Product.objects.all()
    return render(request, 'manage_products.html', {'products': products})
@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('manage_products')

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
# redirect to product list or same page
@csrf_exempt
def create_checkout_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        cart = data.get('cart', [])

        if not cart:
            return JsonResponse({'error': 'Cart is empty'})

        line_items = []
        for item in cart:
            if item['quantity'] > 0 and item['price'] > 0:
                line_items.append({
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {'name': item['name']},
                        'unit_amount': int(float(item['price']) * 100),
                    },
                    'quantity': int(item['quantity']),
                })

        if not line_items:
            return JsonResponse({'error': 'No valid items to pay for!'})

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/payment-success/?session_id={CHECKOUT_SESSION_ID}'),
            cancel_url=request.build_absolute_uri('/checkout/')
        )

        return JsonResponse({'url': checkout_session.url})
    except Exception as e:
        return JsonResponse({'error': str(e)})


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'vetbooking/cart.html', {'cart_items': cart_items, 'total': total})


stripe.api_key = settings.STRIPE_SECRET_KEY  # Make sure you add this in settings.py
@login_required
def checkout(request):
    product_id = request.GET.get('product_id')

    if product_id:
        # --- CASE 1: "Buy Now" (Single Product Flow) ---
        try:
            # Fetch the product being bought directly
            product = get_object_or_404(Product, id=product_id)
            quantity = 1 # Assume 'Buy Now' is always quantity 1

            # Create a temporary list structure that mimics the cart_items template format
            cart_items = [{
                'product': product,
                'quantity': quantity,
                'total_price': product.price * quantity, # Calculate total price for this item
                'is_single_item': True # Flag for template logic (optional but useful)
            }]

            total = cart_items[0]['total_price'] # Total is just the price of the single item

        except Product.DoesNotExist:
            # Handle case where product ID is invalid
            cart_items = []
            total = 0

    else:
        # --- CASE 2: Standard Cart Checkout (Multiple Items) ---
        # Fetch actual CartItem objects from the database for the user
        cart_items_queryset = CartItem.objects.filter(user=request.user)

        # We need a list of dictionaries if the template expects the total_price field directly
        # If the template uses the CartItem object's .total_price() method, this step is simpler.
        # Assuming your template is designed to handle CartItem objects:
        cart_items = list(cart_items_queryset) # Convert queryset to list
        total = sum(item.total_price() for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total': total,
        'product_id': product_id # Pass this for the place_order URL fix from the previous step
    }


    return render(request, 'checkout.html', context)

@login_required
def payment(request):
    if request.method == "POST":
        # simulate payment success
        return redirect('success')
    return redirect('checkout')




def health_tips(request):
    tips = [
        {"title": "Daily Exercise", "content": "Ensure your pet exercises daily to maintain a healthy weight and mental health."},
        {"title": "Balanced Diet", "content": "Feed your pet a balanced diet suitable for its species and age."},
        {"title": "Vaccinations", "content": "Keep all vaccinations up-to-date to prevent common diseases."},
        {"title": "Regular Checkups", "content": "Visit the vet for regular health checkups at least twice a year."},
    ]

    faqs = [
        {"question": "My dog refuses to eat. What should I do?", "answer": "Check for illness, dental problems, or stress. Consult a vet if it persists."},
        {"question": "How often should I groom my cat?", "answer": "Brush long-haired cats daily and short-haired cats weekly to reduce shedding."},
        {"question": "Can birds drink tap water?", "answer": "It's better to provide filtered or boiled water to prevent infections."},
    ]

    ai_tips = [
        "Use puzzle feeders to stimulate your pet’s mind and prevent boredom.",
        "Always keep a first aid kit ready for your pet at home.",
        "Create a calm and safe environment to reduce anxiety during thunderstorms."
    ]

    return render(request, 'health_tips.html', {"tips": tips, "faqs": faqs, "ai_tips": ai_tips})



def order_success(request):
    return render(request, 'order_success.html')

@login_required(login_url='login')
def vaccination_home(request):
    # You can show available vets and allow booking
    vets = Vet.objects.all()
    pets = Pet.objects.filter(owner=request.user)

    if request.method == "POST":
        vet_id = request.POST.get('vet_id')
        pet_id = request.POST.get('pet_id')
        date = request.POST.get('date')
        time = request.POST.get('time')
        notes = request.POST.get('notes')

        Appointment.objects.create(
            user=request.user,
            vet_id=vet_id,
            pet_id=pet_id,
            date=date,
            time=time,
            notes=notes,
            type="Vaccination"
        )
        return redirect('appointment_success')

    return render(request, 'vaccination_home.html', {"vets": vets, "pets": pets})
@login_required(login_url='login')
def appointment_success(request):
    return render(request, 'appointment_success.html')
def cart(request):
    cart = request.session.get('cart', [])
    cart_items = []
    for item in cart:
        product = Product.objects.get(id=item['id'])
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
            'total_price': item['quantity'] * product.price
        })

    total = sum(item['total_price'] for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})
@login_required
def cart_view(request):
    """Displays the user's cart contents and calculates the total."""
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    context = {
        'cart_items': cart_items,
        'total': total
    }
    return render(request, 'vetbooking/cart.html', context)
@login_required
def place_order(request):
    """Handles the POST request from the checkout form to create an Order."""
    if request.method == 'POST':
        # Retrieve billing info from the POST request
        billing_info = {
            'full_name': request.POST.get('full_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address'),
            'city': request.POST.get('city'),
            'state': request.POST.get('state'),
            'zip_code': request.POST.get('zip_code'),
        }

        # Check for single product (Buy Now) flow via query parameter
        product_id = request.GET.get('product_id')

        if product_id:
            # --- Flow 1: Buy Now (Single Product) ---
            product = get_object_or_404(Product, id=product_id)
            quantity = 1  # Buy Now is usually quantity 1

            Order.objects.create(
                user=request.user,
                product_name=product.name,
                quantity=quantity,
                price=product.price,
                total_price=product.price * quantity,
                **billing_info
            )
            messages.success(request, f"Order for '{product.name}' placed successfully. Proceeding to payment.")

        else:
            # --- Flow 2: Cart Checkout ---
            cart_items = CartItem.objects.filter(user=request.user)
            if not cart_items:
                messages.error(request, "Your cart is empty and no product was selected.")
                return redirect('product_list')

            # Create a single Order summarizing the cart (due to your model structure)
            product_list = [f"{item.product.name} (x{item.quantity})" for item in cart_items]
            total_price = sum(item.total_price() for item in cart_items)

            Order.objects.create(
                user=request.user,
                product_name="Cart Order: " + ", ".join(product_list),
                quantity=len(cart_items),
                price=0.00,  # Price is irrelevant for summary order
                total_price=total_price,
                **billing_info
            )

            # Clear the cart after successfully placing the order
            cart_items.delete()
            messages.success(request, "Your cart order has been placed successfully. Proceeding to payment.")

        # Redirect to the success/payment flow
        return redirect('order_success')  # Or redirect to create_checkout_session if using Stripe

    # If a user somehow navigates to /place-order/ with a GET request
    return redirect('checkout')
@login_required(login_url='login')
def buy_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        # Step 1: Create a Booking/Order
        order = Order.objects.create(
            user=request.user,
            product=product,
            created_at=timezone.now()
        )
        # Step 2: Redirect to a bill page
        return redirect('order_bill', order_id=order.id)

    return render(request, 'vetbooking/buy_product.html', {'product': product})
@login_required
def order_bill(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'vetbooking/order_bill.html', {'order': order})


def payment_cancel(request):
    return render(request, 'payment_cancel.html')

@login_required
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == "POST":
        # Here you would integrate a payment gateway like Razorpay, Stripe, etc.
        # For now, we mark the order as “Paid”
        order.status = "Paid"
        order.save()
        messages.success(request, f"Payment successful for {order.product.name}!")
        return redirect('home')
    return render(request, 'vetbooking/payment_page.html', {'order': order})

@login_required
def add_to_cart(request, product_id):
    """Adds a product to the user's cart or increments quantity if it exists."""
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"'{product.name}' added to your cart!")
    return redirect('cart')


@login_required(login_url='login')
def add_to_cart_and_checkout(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # ✅ Use CartItem instead of Cart
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('checkout')


@login_required
def decrease_cart_item(request, product_id):
    """Decreases the quantity of a product in the user's database cart."""
    try:
        cart_item = CartItem.objects.get(user=request.user, product__id=product_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except CartItem.DoesNotExist:
        messages.error(request, "Item not found in your cart.")
    return redirect('cart')


@login_required
def remove_from_cart(request, product_id):
    """Removes an entire item from the cart, regardless of quantity."""
    try:
        cart_item = CartItem.objects.get(user=request.user, product__id=product_id)
        cart_item.delete()
        messages.success(request, f"'{cart_item.product.name}' was removed from your cart.")
    except CartItem.DoesNotExist:
        messages.error(request, "Item not found in your cart.")
    return redirect('cart')
