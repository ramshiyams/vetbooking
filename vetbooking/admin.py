from django.contrib import admin
from django.utils.html import format_html

from .models import Pet, Vet, Appointment, Order, Notification, VetBooking
from .models import Product
# 🐾 Pet Admin
@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'pet_type', 'age', 'owner')
    search_fields = ('name', 'pet_type', 'owner__username')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_published', 'created_at')
    search_fields = ('name',)

# 🧑‍⚕️ Vet Admin
@admin.register(Vet)
class VetAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization')
    search_fields = ('name', 'specialization')

@admin.register(VetBooking)
class VetBookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'vet', 'pet', 'date', 'time', 'status')
    list_filter = ('status', 'date', 'vet')
    search_fields = ('user__username', 'vet__name', 'pet__name')



# 📅 Appointment Admin
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'vet', 'date', 'status_colored')
    list_filter = ('status',)

    def status_colored(self, obj):
        color = {
            'Pending': 'orange',
            'Approved': 'green',
            'Cancelled': 'red'
        }.get(obj.status, 'black')
        return format_html(f'<b style="color:{color}">{obj.status}</b>')
    status_colored.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.status == 'Approved':
            Notification.objects.update_or_create(
                user=obj.user,
                message=f"Your appointment with Dr. {obj.vet.name} has been approved.",
                defaults={'status': 'Approved'}
            )

# 🛍️ Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_published', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('is_published','price')
    ordering = ('-created_at',)


# 💊 Medicine Admin
# @admin.register(Medicine)
# class MedicineAdmin(admin.ModelAdmin):
#     list_display = ('name', 'price', 'stock')
#     search_fields = ('name',)
#     list_filter = ('stock',)

admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'created_at')  # <-- changed from order_date
    search_fields = ('user__username', 'product__name')
    ordering = ('-created_at',)  # <-- changed from -order_date

# 🔔 Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
    search_fields = ('user__username', 'message')
    ordering = ('-created_at',)
