from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from .models import Items, OrderItem, Order, BillingAddress, PaymentRecord, CouponRecord
from django.views.generic import ListView, DetailView, View
from .forms import CheckoutForm, CouponForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY	


class HomeView(ListView):
	model = Items
	paginate_by = 1
	template_name = "home.html"


class ItemDetailView(DetailView):
	model = Items
	template_name = "product.html"


class YourOrderView(LoginRequiredMixin, View):
	def get(self, *args, **kwargs):
		try:
			order_qs = Order.objects.filter(user=self.request.user, ordered=True)
			order_item= OrderItem.objects.filter(user=self.request.user, ordered=True)
			if order_qs:
				context = {
					'object' : order_qs,
					'object_item' : order_item
				}
				return render(self.request, 'yourorders.html', context)

			else:
				messages.info(self.request, "You haven't placed any orders yet.")
				return redirect("core:home-view")

		except ObjectDoesNotExist:
			messages.info(self.request, "You haven't placed any order yet.")
			return redirect("core:home-view")



class OrderSummaryView(LoginRequiredMixin, View):
	def get(self, *args, **kwargs):
		order = Order.objects.get(user=self.request.user, ordered=False)
		context = {
			'object' : order
		}
		print(context.items)
		return render(self.request, 'order-summary.html', context)


class CheckoutView(LoginRequiredMixin, View):
	def get(self, *args, **kwargs):
		order = Order.objects.get(user=self.request.user, ordered=False)
		order_item = OrderItem.objects.all()
		if order.items:
			form = CheckoutForm()
			couponform = CouponForm()
			context = {
				'form' : form,
				'order': order,
				'couponform': couponform
			}
			return render(self.request, "checkout.html", context)
		messages.info(self.request, "There are no items in your cart")
		return redirect("core:home-view")



	def post(self, *args, **kwargs):
		form = CheckoutForm(self.request.POST)
		print(self.request.POST)
		try:
			order = Order.objects.get(user=self.request.user, ordered=False)
			if form.is_valid():
				street_address = form.cleaned_data.get('street_address')
				apartment_address = form.cleaned_data.get('apartment_address')
				country = form.cleaned_data.get('country')
				pincode = form.cleaned_data.get('pincode')
				# use_same_bill_addr = form.cleaned_data('use_same_bill_addr')
				# save_details = form.cleaned_data('save_details')
				payment_choice = form.cleaned_data.get('payment_choice')
				billing_address = BillingAddress(
							user = self.request.user,
							street_address = street_address,
							apartment_address = apartment_address,
							country = country,
							pincode = pincode
					)
				billing_address.save()
				order.billing_address = billing_address
				order.save()
				return redirect("core:payment-view", payment_choice=payment_choice)

			messages.warning(self.request, "Form is not Valid")
			return redirect("core:checkout-view")
			
		except ObjectDoesNotExist:
			messages.info(self.request, "You do not have an active order")
			return redirect("core:checkout-view")

		

class PaymentView(LoginRequiredMixin, View):


	def get(self, *args, **kwargs):
		order = Order.objects.get(user=self.request.user, ordered=False)
		context = {
			'order' : order,
		}
		return render(self.request, "payment.html", context)


	def post(self, *args, **kwargs):

		print('working')
		order = Order.objects.get(user=self.request.user, ordered=False)
		print(order)
		token = self.request.POST.get('stripeToken')
		amount = int(order.get_final_total_bill())
		print(amount)

		try:
			print('working')
			charge = stripe.Charge.create(
					  amount=amount,
					  currency="inr",
					  source=token,
					)
			print('working')
			payment = PaymentRecord()
			payment.stripe_charge_id = charge['id']
			payment.user = self.request.user
			payment.amount = order.get_final_total_bill()
			payment.save()
			print('working')

			order_item = order.items.all()
			order_item.update(ordered=True)
			for item in order_item:
				item.save()

			order.ordered = True
			order.payment = payment
			order.save()
			
			messages.success(self.request, "Order successfully placed")
			return redirect("core:home-view")

		except stripe.error.CardError as e:
			messages.error(self.request, "Something wrong")
			return redirect("core:home-view")

		except stripe.error.RateLimitError as e:
			messages.error(self.request, e.error.message)
			return redirect("/")

		except stripe.error.InvalidRequestError as e:
			messages.error(self.request, "Invalid parameters")
			return redirect("/")
		  # Invalid parameters were supplied to Stripe's API
		  
		except stripe.error.AuthenticationError as e:
			messages.error(self.request, "Authentication Failed")
			return redirect("/")
		  # Authentication with Stripe's API failed
		  # (maybe you changed API keys recently)
		  
		except stripe.error.APIConnectionError as e:
			messages.error(self.request, "Network Failed")
			return redirect("/")
		  # Network communication with Stripe failed
		  
		except stripe.error.StripeError as e:
			messages.error(self.request, "Something went wrong")
			return redirect("/")
		  # Display a very generic error to the user, and maybe send
		  # yourself an email
		  
		except Exception as e:
			messages.error(self.request, "Something went wrong")
			return redirect("/")
		  # Something else happened, completely unrelated to Stripe
	


@login_required
def add_to_cart(request, slug):
	item = get_object_or_404(Items, slug=slug) 
	print("Item is: ", item)
	order_item, ordered = OrderItem.objects.get_or_create(
					item=item,
					user=request.user,
					ordered=False,
	)
	print("Order_item is: ", order_item, ordered)
	order_qs = Order.objects.filter(user=request.user, ordered=False)
	print("Order_qs is: ", order_qs)
	if order_qs.exists():
		order = order_qs[0]
		print("Order is: ", order)
		if order.items.filter(item__slug=item.slug).exists():
			order_item.quantity += 1
			order_item.save()
			messages.info(request, "Item successfully added to your cart")
			return redirect("core:products-view", slug=slug)
		else:
			order.items.add(order_item)
			messages.info(request, "Item successfully added to your cart")
			return redirect("core:products-view", slug=slug)

	else:
		ordered_date = timezone.now()
		order = Order.objects.create(user=request.user, ordered_date=ordered_date)
		order.items.add(order_item)
		messages.info(request, "Item successfully added to your cart")
	return redirect("core:products-view", slug=slug)

@login_required
def remove_from_cart(request, slug):
	item = get_object_or_404(Items, slug=slug)
	print("Item is: ", item)
	order_qs = Order.objects.filter(user=request.user, ordered=False)
	print("Order_qs is: ", order_qs)
	if order_qs.exists():
		order = order_qs[0]
		print("Order is: ", order)
		if order.items.filter(item__slug=item.slug).exists():
			order_item = OrderItem.objects.filter(
					item=item,
					user=request.user,
					ordered=False,
		)[0]
			print("Order_item is: ", order_item)
			order.items.remove(order_item)
			messages.info(request, "Item successfully removed from your cart")
			return redirect("core:products-view", slug=slug)
		else:
			messages.info(request, "No such item in you cart")
			return redirect("core:products-view", slug=slug)
	else:
		messages.info(request, "Your cart is empty")
		return redirect("core:products-view", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
	item = get_object_or_404(Items, slug=slug)
	print("Item is: ", item)
	order_qs = Order.objects.filter(user=request.user, ordered=False)
	print("Order_qs is: ", order_qs)
	if order_qs.exists():
		order = order_qs[0]
		print("Order is: ", order)
		if order.items.filter(item__slug=item.slug).exists():
			order_item = OrderItem.objects.filter(
					item=item,
					user=request.user,
					ordered=False,
		)[0]
			print("Order_item is: ", order_item)
			if order_item.quantity > 1:
				order_item.quantity -= 1
				order_item.save()
				messages.info(request, "Item successfully removed from your cart")
				return redirect("core:order-summary-view")
			else:
				order.items.remove(order_item)
				messages.info(request, "Item quantity is zero")
				return redirect("core:order-summary-view")
		else:
			messages.info(request, "No such item in you cart")
			return redirect("core:order-summary-view")
	else:
		messages.info(request, "Your cart is empty")
		return redirect("core:order-summary-view")


@login_required
def add_single_item_to_cart(request, slug):
	item = get_object_or_404(Items, slug=slug) 
	print("Item is: ", item)
	order_item, ordered = OrderItem.objects.get_or_create(
					item=item,
					user=request.user,
					ordered=False,
	)
	print("Order_item is: ", order_item, ordered)
	order_qs = Order.objects.filter(user=request.user, ordered=False)
	print("Order_qs is: ", order_qs)
	if order_qs.exists():
		order = order_qs[0]
		print("Order is: ", order)
		if order.items.filter(item__slug=item.slug).exists():
			order_item.quantity += 1
			order_item.save()
			messages.info(request, "Item successfully added to your cart")
			return redirect("core:order-summary-view")
		else:
			order.items.add(order_item)
			messages.info(request, "Item successfully added to your cart")
			return redirect("core:order-summary-view")

	else:
		ordered_date = timezone.now()
		order = Order.objects.create(user=request.user, ordered_date=ordered_date)
		order.items.add(order_item)
		messages.info(request, "Item successfully added to your cart")
	return redirect("core:order-summary-view")


def get_coupon(request, code):
	try:
		coupons = CouponRecord.objects.get(code=code)
		return coupons
	except ObjectDoesNotExist:
		messages.info(request, "Coupon not Valid")
		return redirect("core:order-summary-view")



class AddCoupon(View):
		
	def post(self, *args, **kwargs):
		print('working')
		form = CouponForm(self.request.POST or None)
		print(form)
		if form.is_valid():
			try:
				code = form.cleaned_data.get('code')
				print(code)
				order = Order.objects.get(user=self.request.user, ordered=False)
				print(order)
				order.coupon = get_coupon(self.request, code)
				print(order.coupon)
				order.save()

				messages.success(self.request, "Coupon successfully applied")
				return redirect("core:checkout-view")

			except ObjectDoesNotExist:
				messages.success(self.request, "You do not have an active order")
				return redirect("core:checkout-view")

		messages.warning(self.request, "Please enter coupon in a valid format")
		return redirect("core:checkout-view")


@login_required
def remove_coupon(request):
	order_qs = Order.objects.filter(user=request.user, ordered=False)
	if order_qs.exists():
		order = order_qs[0]
		coupon = CouponRecord.objects.get(code='None')
		print(coupon)
		order.coupon = coupon
		order.save()
		messages.warning(request, "Promo cancelled")
		return redirect("core:checkout-view")

	messages.warning(request, "No such order exists")
	return redirect("core:checkout-view")
	