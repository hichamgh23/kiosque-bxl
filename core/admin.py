from django.contrib import admin
from .models import Category, Product, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'slug', 'order')
    exclude       = ('icon',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ('emoji', 'name', 'category', 'price', 'in_stock', 'featured')
    list_filter   = ('category', 'in_stock', 'featured')
    list_editable = ('price', 'in_stock', 'featured')
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model  = OrderItem
    extra  = 0
    readonly_fields = ('product_name', 'unit_price', 'quantity', 'subtotal')

    def subtotal(self, obj):
        return f"{obj.subtotal:.2f} €"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('id', 'client_name', 'phone', 'payment_method', 'status', 'created_at')
    list_filter   = ('status', 'payment_method')
    list_editable = ('status',)
    search_fields = ('client_name', 'phone', 'address')
    inlines       = [OrderItemInline]
    readonly_fields = ('created_at',)
