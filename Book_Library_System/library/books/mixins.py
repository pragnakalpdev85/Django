from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import Http404
from .models import Book
from datetime import timezone
from django.views.generic.base import ContextMixin

class UserBookMixin:
    """Mixin to filter Books by current user"""
    
    def get_queryset(self):
        return Book.objects.filter(created_by=self.request.user)
    
    
class UserIsOwnerMixin:
    """Mixin to ensure user owns the object"""
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.created_by != self.request.user:
            raise Http404("You don't have permission to access this book.")
        return obj


class SuccessMessageMixin:
    """Mixin to add success messages"""
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message())
        return response
    
    def get_success_message(self,   ):
        if hasattr(self, 'object') and self.object:
            return f'{self.object.__class__.__name__} {"created" if self.request.method == "POST" else "updated"} successfully!'
        
        return 'Operation completed successfully!'
    
class BookStatMixin(ContextMixin):
    """Mixin to add books stats to the context"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter values for form
        context['search_query'] = self.request.GET.get('search_value', '')
        context['status_filter'] = self.request.GET.get('filter', '')
        context['genre_filter'] = self.request.GET.get('filter_genre', '') 
        
        # Add statistics
        all_books = Book.objects.filter(created_by=self.request.user)
        context['stats'] = {
            'total': all_books.count(),
            'available': all_books.filter(is_available=True).count(),
            'borrowed': all_books.filter(is_available=False).count(),
            'genre': {
                'fiction': all_books.filter(genre='fiction').count(),
                'nonfiction': all_books.filter(genre='non-fiction').count(),
                'science': all_books.filter(genre='science').count(),
                'history': all_books.filter(genre='history').count(),
                'biography': all_books.filter(genre='biography').count(),
            }
        }
        
        return context