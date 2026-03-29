from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("addlisting", views.addlisting, name="addlisting"),
    path("make_a_bid", views.make_a_bid, name="make_a_bid"),
    path("categories", views.categories, name="categories"),
    path("categories/<str:cat>", views.listings_by_categories, name="listings_by_categories"),
    path("wishlist", views.wishlist, name="wishlist"),
    path("add_remove_wishlist/<int:listing>", views.add_remove_wishlist, name="add_remove_wishlist"),
    path("listingdetail/<int:listing_id>", views.listing_detail, name="listing_detail"),
    path("api/postcomment", views.post_comment, name="postComment")
]
