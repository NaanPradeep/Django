from django.urls import path, include
from .views import (
		HomeView,
		OrderSummaryView,
		ItemDetailView,
		YourOrderView,
		CheckoutView,
		PaymentView,
		AddCoupon,
		remove_coupon,
		add_to_cart,
		remove_from_cart,
		remove_single_item_from_cart,
		add_single_item_to_cart,
	)

app_name = 'cores'

urlpatterns = [
    path('', HomeView.as_view(), name='home-view'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary-view'),
    path('your-orders/', YourOrderView.as_view(), name='your-orders-view'),
    path('checkout/', CheckoutView.as_view(), name='checkout-view'),
    path('payment/<payment_choice>/', PaymentView.as_view(), name='payment-view'),
    path('products/<slug>/', ItemDetailView.as_view(), name='products-view'),
    path('add_to_cart/<slug>/', add_to_cart, name='add_to_cart'),
    path('add_coupon/', AddCoupon.as_view(), name='add_coupon'),
    path('remove_coupon/', remove_coupon, name='remove_coupon'),
    path('remove_from_cart/<slug>/', remove_from_cart, name='remove_from_cart'),
    path('remove_single_item_from_cart/<slug>/', remove_single_item_from_cart, name='remove_single_item_from_cart'),
    path('add_single_item_to_cart/<slug>/', add_single_item_to_cart, name='add_single_item_to_cart'),
] 