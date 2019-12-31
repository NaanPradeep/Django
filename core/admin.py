from django.contrib import admin
from .models import Items, OrderItem, Order, PaymentRecord, CouponRecord

class OrderAdmin(admin.ModelAdmin):
	list_display = ['user', 'ordered']

admin.site.register(Items)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(PaymentRecord)
admin.site.register(CouponRecord)