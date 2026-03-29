from django import forms
from .models import AuctionListing, Comment

class ListingForm(forms.ModelForm):
    class Meta:
        model = AuctionListing
        exclude = ["creator", "closed"]

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ["listing", "author"]