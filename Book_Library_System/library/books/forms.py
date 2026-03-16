from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Book

class BookForm(forms.ModelForm):
    """
    BookForm class represents form fields details of books
    """
    
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'description', 'genre', 'is_available']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter book title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter author name'}),
            'isbn': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter ISBN number'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter book description'}),
            'genre': forms.Select(attrs={'class': 'form-control'}),
            'is_available': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters long")
        return title
    

class UserRegisterForm(UserCreationForm):
    """
    UserForm class represents form field details of User
    """
    
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})