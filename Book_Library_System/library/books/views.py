from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q

from .models import Book
from .forms import BookForm, UserRegisterForm
from .mixins import UserIsOwnerMixin, UserBookMixin, SuccessMessageMixin, BookStatMixin

class UserRegisterView(CreateView):
    """
    Renders user registration form 
    
    this view Retrives data from form and creates new user
    """
    
    form_class = UserRegisterForm
    template_name = 'books/register.html'
    success_url = reverse_lazy('book_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        messages.success(self.request, f'Account created for {username}!')
        return response

class UserLoginView(TemplateView):
    """
    Renders user login form 
    
    this view Retrieves user email and password and if coorrect login user
    """
    
    template_name = 'books/login.html'
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('book_list')
        else:
            messages.error(request, 'Invalid username or password!')
            return render(request, 'books/login.html')
        
class UserProfileView(LoginRequiredMixin, TemplateView):
    """
    Renders the logged-in user's profile page
    """

    template_name = 'books/user_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['profile_user'] = user
        context['total_books'] = Book.objects.filter(created_by=user).count()
        context['available_books'] = Book.objects.filter(created_by=user, is_available=True).count()
        context['borrowed_books'] = Book.objects.filter(created_by=user, is_available=False).count()
        return context

class UserLogoutView(View):
    """
    This view logs out user
    """
    
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('book_list')

class BookListView(LoginRequiredMixin, BookStatMixin, UserBookMixin, ListView):
    """
    Renders the list of books
    
    This view fetches books data according to filter's applied
    """
    
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality for searching by title and author
        search = self.request.GET.get('search_value')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(author__icontains=search)
            )
        
        # Filter by available status
        status = self.request.GET.get('filter')
        if status:
            status = True if status == 'available' else False
            queryset = queryset.filter(is_available = status)
        
        # Filter by genre
        genre = self.request.GET.get('filter_genre')
        if genre:
            queryset = queryset.filter(genre = genre)
        
        return queryset
    
class BorrowedBooksView(LoginRequiredMixin, BookStatMixin, UserBookMixin, ListView):
    """
    This view Renders the borrowed books
    """
    
    model = Book
    template_name = 'books/book_borrowed.html'
    context_object_name = 'books'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_available = False)
        
        print(queryset)
        return queryset

class BookDetailView(LoginRequiredMixin, UserBookMixin, UserIsOwnerMixin, DetailView):
    """
    This view displays books data and 
    books with same genre
    """
    
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add related tasks
        context['related_books'] = Book.objects.filter(
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
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('book_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context

class BookUpdateView(LoginRequiredMixin, UserBookMixin, UserIsOwnerMixin, SuccessMessageMixin, UpdateView):
    """
    This view renders selected book's form, validate and updates the book details
    """
    
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('book_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context
    
    def get_success_message(self):      
        return f'{self.object.__class__.__name__} updated successfully!'

class BookDeleteView(LoginRequiredMixin, UserBookMixin, UserIsOwnerMixin, DeleteView):
    """
    This view Renders delete confirmation template and deletes book 
    """
    
    model = Book
    template_name = 'books/book_confirm_delete.html'
    success_url = reverse_lazy('book_list')

class BookToggleBorrowesView(LoginRequiredMixin, UserBookMixin, View):
    """
    This view changes status of the book to available or borrowed
    """
    
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk, created_by=request.user)
        
        book.is_available = not book.is_available
        book.save()
        
        messages.success(request, f"Book marked as {'Available' if book.is_available else 'Borrowed'}.")
        return redirect('book_list')