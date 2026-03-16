from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Book(models.Model):
    """Book model"""
    
    #Genre choices
    GENRE_CHOICES = [
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('science', 'Science'),
        ('history', 'History'),
        ('biography', 'Biography')
    ]
    
    #Status choices
    STATUS_CHOICE = [
        (True, 'Available'),
        (False, 'Borrowed')
    ]
    
    # Basic fields
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField(max_length=200, null=True, blank=True)
    isbn = models.IntegerField()
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES, default='fiction')
    is_available = models.BooleanField(default=True, choices=STATUS_CHOICE)
    
    # Relationships
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    #Meta informations about model
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        db_table = 'books'
        indexes = [
            models.Index(fields=['created_by']),
            models.Index(fields=['genre', 'is_available']),
        ]
    
    def __str__(self):
        return self.title
    
    def mark_available(self):
        """Mark Book as available"""
        self.is_available = True
        self.save()
    
    def mark_borrowed(self):
        """Mark book as borrowed"""
        self.is_available = False
        self.save()