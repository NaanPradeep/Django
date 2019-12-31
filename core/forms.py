from django import forms
from django_countries.fields import CountryField

PAYMENT_CHOICES = {
		('S', 'Stripe'),
		('PP','Paypal'),
}


class CheckoutForm(forms.Form):
	street_address = forms.CharField(widget=forms.TextInput(attrs={
			'class' : 'form-control',
			'placeholder': 'Doorno and Streetname'
		}))
	apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
			'class' : 'form-control',
			'placeholder': 'Apartment or suite'
		}))
	country = CountryField(blank_label='(select country)').formfield(attrs={
			'class' : 'custom-select d-block w-100 ml-0',
		})
	pincode = forms.CharField(max_length=6)
	# use_same_bill_addr = forms.BooleanField(widget=forms.CheckboxInput())
	# save_details = forms.BooleanField(widget=forms.CheckboxInput())
	payment_choice = forms.ChoiceField(widget=forms.RadioSelect(), choices=PAYMENT_CHOICES)


class CouponForm(forms.Form):
	code = forms.CharField(widget=forms.TextInput(attrs={
			'class':"form-control", 
			'placeholder' : "Promo code", 
			'aria-label' : "Recipient's username", 
			'aria-describedby' : "basic-addon2",
		}))