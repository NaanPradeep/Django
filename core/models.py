from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django_countries.fields import CountryField


CATEGORY_CHOICES = (
		("Shirt" , "S"),
		("ShortWear" , "SW"),
		("Out Wear" , "OW"),
	)

LABEL_CHOICES = (
		("P" , "primary"),
		("S" , "secondary"),
		("D" , "danger"),
	)


class Items(models.Model):
	title = models.CharField(max_length=100)
	category = models.CharField(choices=CATEGORY_CHOICES, max_length=50)
	label = models.CharField(choices=LABEL_CHOICES, max_length=1)
	price = models.FloatField()
	discounted_price = models.FloatField()
	image = models.ImageField(default='default.jpg', upload_to='card_pics')
	slug = models.SlugField()


	def __str__(self):
		return self.title


	def get_absolute_url(self):
		return reverse('core:products-view', kwargs={
					'slug' : self.slug
			})


	def get_add_to_cart_url(self):
		return reverse('core:add_to_cart', kwargs={
					'slug' : self.slug
			})


	def get_remove_from_cart_url(self):
		return reverse('core:remove_from_cart', kwargs={
					'slug' : self.slug
			})

class OrderItem(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	ordered =  models.BooleanField(default=False)	
	item = models.ForeignKey(Items, on_delete=models.CASCADE)
	quantity = models.IntegerField(default=1)


	def __str__(self):
		return f"{self.quantity} of {self.item.title}"

	def get_total_item_price(self):
		return self.quantity * self.item.price

	def get_total_discounted_item_price(self):
		return self.quantity * self.item.discounted_price

	def get_total_savings(self):
		return self.get_total_item_price() - self.get_total_discounted_item_price()

	def get_final_price(self):
		if self.item.discounted_price:
			return self.get_total_discounted_item_price()
		return self.get_total_item_price()


class Order(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	items = models.ManyToManyField(OrderItem)
	start_date = models.DateTimeField(auto_now_add=True)
	ordered_date = models.DateTimeField()	
	ordered =  models.BooleanField(default=False)	
	billing_address = models.ForeignKey('BillingAddress', on_delete=models.SET_NULL, blank=True, null=True)
	payment = models.ForeignKey('PaymentRecord', on_delete=models.SET_NULL, blank=True, null=True)
	coupon = models.ForeignKey('CouponRecord', on_delete=models.SET_NULL, blank=True, null=True)
	being_delivered = models.BooleanField(default=False)
	delivered = models.BooleanField(default=False)
	refund_requested = models.BooleanField(default=False)


	def __str__(self):
		return self.user.username

	def get_final_total_bill(self):
		total = 0
		for orders in self.items.all():
			total += orders.get_final_price()

		return total

	def promo_applied_or_not_bill(self):
		total = 0
		for orders in self.items.all():
			total += orders.get_final_price()
		if self.coupon:
			total -= self.coupon.amount
		return total

	def get_final_total_savings(self):
		total_savings = 0
		for orders in self.items.all():
			total_savings += orders.get_total_savings()
		return total_savings


class BillingAddress(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	street_address = models.CharField(max_length=100)
	apartment_address = models.CharField(max_length=100)
	country = CountryField(multiple=True)
	pincode = models.CharField(max_length=6)



	def __str__(self):
		return self.user.username


class PaymentRecord(models.Model):
	stripe_charge_id = models.CharField(max_length=60)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
	amount = models.FloatField()
	timestamp = models.DateTimeField(auto_now_add=True)


	def __str__(self):
		return self.user.username


class CouponRecord(models.Model):
	code = models.CharField(max_length=20)
	amount = models.FloatField()


	def __str__(self):
		return self.code

	def get_remove_coupon_url(self):
		return reverse("core:remove_coupon")