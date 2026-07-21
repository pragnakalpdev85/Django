from django.urls import path
from . import views

urlpatterns = [
    # Authentication urls
    path("register/", views.UserRegisterView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("profile/", views.UserProfileView.as_view(), name="user_profile"),
    # Books urls
    path("", views.BookListView.as_view(), name="book_list"),
    path("books/<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
    path("books/create/", views.BookCreateView.as_view(), name="book_create"),
    path("books/<int:pk>/update/", views.BookUpdateView.as_view(), name="book_update"),
    path("books/<int:pk>/delete/", views.BookDeleteView.as_view(), name="book_delete"),
    path("books/borrowed/", views.BorrowedBooksView.as_view(), name="book_borrowed"),
    path(
        "books/<int:pk>/toggle/",
        views.BookToggleBorrowesView.as_view(),
        name="book_toggle_available",
    ),
]
