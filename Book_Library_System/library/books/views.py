import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from .forms import BookForm, UserRegisterForm
from .mixins import BookStatMixin, SuccessMessageMixin, UserBookMixin, UserIsOwnerMixin
from .models import Book

logger = logging.getLogger("books")


class UserRegisterView(CreateView):
    """
    Renders user registration form

    this view Retrives data from form and creates new user
    """

    form_class = UserRegisterForm
    template_name = "books/register.html"
    success_url = reverse_lazy("book_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get("username")
        messages.success(self.request, f"Account created for {username}!")
        logger.info("New user registered: %s", username)
        return response


class UserLoginView(TemplateView):
    """
    Renders user login form

    this view Retrieves user email and password and if coorrect login user
    """

    template_name = "books/login.html"

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Login successful!")
            logger.info("User logged in: %s", username)
            return redirect("book_list")
        else:
            messages.error(request, "Invalid username or password!")
            logger.warning("Failed login attempt for username: %s", username)
            return render(request, "books/login.html")


class UserProfileView(LoginRequiredMixin, TemplateView):
    """
    Renders the logged-in user's profile page
    """

    template_name = "books/user_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        logger.info("User profile viewed: %s", user.username)
        context["profile_user"] = user
        context["total_books"] = Book.objects.filter(created_by=user).count()
        context["available_books"] = Book.objects.filter(
            created_by=user, is_available=True
        ).count()
        context["borrowed_books"] = Book.objects.filter(
            created_by=user, is_available=False
        ).count()
        return context


class UserLogoutView(View):
    """
    This view logs out user
    """

    def get(self, request):
        if request.user.is_authenticated:
            logger.info("User logged out: %s", request.user.username)
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect("book_list")


class BookListView(LoginRequiredMixin, BookStatMixin, UserBookMixin, ListView):
    """
    Renders the list of books

    This view fetches books data according to filter's applied
    """

    model = Book
    template_name = "books/book_list.html"
    context_object_name = "books"
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Search functionality for searching by title and author
        search = self.request.GET.get("search_value")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(author__icontains=search)
            )
            logger.info("User %s searched books with query: %s", user.username, search)

        # Filter by available status
        status = self.request.GET.get("filter")
        if status:
            status = True if status == "available" else False
            queryset = queryset.filter(is_available=status)
            logger.info("User %s filtered books by status: %s", user.username, status)

        # Filter by genre
        genre = self.request.GET.get("filter_genre")
        if genre:
            queryset = queryset.filter(genre=genre)
            logger.info("User %s filtered books by genre: %s", user.username, genre)

        logger.info(
            "User %s retrieved %d book(s) from the list",
            user.username,
            queryset.count(),
        )
        return queryset


class BorrowedBooksView(LoginRequiredMixin, BookStatMixin, UserBookMixin, ListView):
    """
    This view Renders the borrowed books
    """

    model = Book
    template_name = "books/book_borrowed.html"
    context_object_name = "books"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_available=False)

        print(queryset)
        return queryset


class BookDetailView(LoginRequiredMixin, UserBookMixin, UserIsOwnerMixin, DetailView):
    """
    This view displays books data and
    books with same genre
    """

    model = Book
    template_name = "books/book_detail.html"
    context_object_name = "book"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add related tasks
        context["related_books"] = Book.objects.filter(
            created_by=self.request.user,
            genre=self.object.genre,
        ).exclude(pk=self.object.pk)[:6]

        return context


class BookCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """
    This view Renders book form, validate and retrieved data from the form and creates new book
    """

    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"
    success_url = reverse_lazy("book_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        logger.info(
            "User %s created a new book: %s",
            self.request.user.username,
            form.instance.title,
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create"
        return context


class BookUpdateView(
    LoginRequiredMixin, UserBookMixin, UserIsOwnerMixin, SuccessMessageMixin, UpdateView
):
    """
    This view renders selected book's form, validate and updates the book details
    """

    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"
    success_url = reverse_lazy("book_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Update"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            "User %s updated book '%s' (id: %s)",
            self.request.user.username,
            self.object.title,
            self.object.pk,
        )
        return response

    def get_success_message(self):
        return f"{self.object.__class__.__name__} updated successfully!"


class BookDeleteView(LoginRequiredMixin, UserBookMixin, UserIsOwnerMixin, DeleteView):
    """
    This view Renders delete confirmation template and deletes book
    """

    model = Book
    template_name = "books/book_confirm_delete.html"
    success_url = reverse_lazy("book_list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        logger.info(
            "User %s deleted book '%s' (id: %s)",
            request.user.username,
            self.object.title,
            self.object.pk,
        )
        return super().delete(request, *args, **kwargs)


class BookToggleBorrowesView(LoginRequiredMixin, UserBookMixin, View):
    """
    This view changes status of the book to available or borrowed
    """

    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk, created_by=request.user)

        book.is_available = not book.is_available
        book.save()

        status = "Available" if book.is_available else "Borrowed"
        messages.success(request, f"Book marked as {status}.")
        logger.info(
            "User %s toggled book '%s' (id: %s) availability to: %s",
            request.user.username,
            book.title,
            book.pk,
            status,
        )
        return redirect("book_list")
