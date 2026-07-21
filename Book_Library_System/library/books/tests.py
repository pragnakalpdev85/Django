import pytest
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Book
from .forms import BookForm, UserRegisterForm

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    """Create a basic user for testing."""
    return User.objects.create_user(username='testuser', password='testpass123')


@pytest.fixture
def other_user(db):
    """Create another user to test ownership restrictions."""
    return User.objects.create_user(username='otheruser', password='testpass123')


@pytest.fixture
def authenticated_client(client, user):
    """Return a test client logged in as the default user."""
    client.force_login(user)
    return client


@pytest.fixture
def book(user):
    """Create a sample book owned by the default user."""
    return Book.objects.create(
        title='Sample Book',
        author='Sample Author',
        isbn=1234567890,
        description='A sample description',
        genre='fiction',
        is_available=True,
        created_by=user,
    )


class TestBookModel:
    """Test the Book model's behaviour and methods."""

    def test_string_representation(self, book):
        assert str(book) == 'Sample Book'

    def test_default_availability(self, user):
        new_book = Book.objects.create(
            title='Default Book', author='Author', isbn=1111111111, created_by=user
        )
        assert new_book.is_available is True

    def test_mark_borrowed_and_available(self, book):
        book.mark_borrowed()
        assert book.is_available is False
        book.mark_available()
        assert book.is_available is True

    def test_book_genre_choices(self, user):
        science_book = Book.objects.create(
            title='Science Book', author='Author', isbn=123456789, genre='science', created_by=user
        )
        assert science_book.genre == 'science'
        assert science_book.get_genre_display() == 'Science'

    def test_ordering_by_created_at(self, user):
        first = Book.objects.create(title='First', author='A', isbn=1, created_by=user)
        second = Book.objects.create(title='Second', author='B', isbn=2, created_by=user)
        books = list(Book.objects.all())
        assert books[0] == second
        assert books[1] == first


class TestBookForm:
    """Test the BookForm validation."""

    def test_valid_book_form(self):
        form = BookForm(data={
            'title': 'Valid Book Title',
            'author': 'Valid Author',
            'isbn': 123456789,
            'description': 'A valid book description',
            'genre': 'fiction',
            'is_available': True,
        })
        assert form.is_valid()

    def test_invalid_title_too_short(self):
        form = BookForm(data={
            'title': 'AB',
            'author': 'Author',
            'isbn': 9876543210,
            'genre': 'fiction',
            'is_available': True,
        })
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_missing_required_fields(self):
        form = BookForm(data={})
        assert not form.is_valid()
        assert 'title' in form.errors
        assert 'author' in form.errors
        assert 'isbn' in form.errors


class TestUserRegisterForm:
    """Test the user registration form."""

    def test_valid_registration(self):
        form = UserRegisterForm(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
        })
        assert form.is_valid()

    def test_password_mismatch(self):
        form = UserRegisterForm(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpass123',
            'password2': 'differentpass',
        })
        assert not form.is_valid()
        assert 'password2' in form.errors


class TestUserRegisterView:
    """Test the user registration view."""

    def test_register_creates_user(self, client):
        response = client.post(reverse('register'), {
            'username': 'createduser',
            'email': 'created@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
        }, follow=False)
        assert response.status_code == 302
        assert User.objects.filter(username='createduser').exists()

    def test_register_rejects_invalid_data(self, client):
        response = client.post(reverse('register'), {
            'username': 'createduser',
            'email': 'invalid-email',
            'password1': 'complexpass123',
            'password2': 'differentpass',
        })
        assert response.status_code == 200
        assert not User.objects.filter(username='createduser').exists()


class TestUserLoginView:
    """Test the login view."""

    def test_valid_login_redirects(self, client, user):
        response = client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        }, follow=False)
        assert response.status_code == 302
        assert response.url == reverse('book_list')

    def test_invalid_login_stays_on_page(self, client):
        response = client.post(reverse('login'), {
            'username': 'nosuchuser',
            'password': 'wrongpassword',
        })
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Invalid username or password' in content


class TestUserLogoutView:
    """Test the logout view."""

    def test_logout_redirects(self, authenticated_client):
        response = authenticated_client.get(reverse('logout'), follow=False)
        assert response.status_code == 302


class TestUserProfileView:
    """Test the user profile view."""

    def test_profile_requires_login(self, client):
        response = client.get(reverse('user_profile'), follow=False)
        assert response.status_code == 302

    def test_profile_displays_user_stats(self, authenticated_client, user):
        Book.objects.create(title='Available Book', author='A', isbn=1, created_by=user, is_available=True)
        Book.objects.create(title='Borrowed Book', author='B', isbn=2, created_by=user, is_available=False)
        response = authenticated_client.get(reverse('user_profile'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'testuser' in content
        assert response.context['total_books'] == 2
        assert response.context['available_books'] == 1
        assert response.context['borrowed_books'] == 1


class TestBookListView:
    """Test the book list view."""

    def test_redirects_when_not_logged_in(self, client):
        response = client.get(reverse('book_list'), follow=False)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_lists_only_current_user_books(self, authenticated_client, user, other_user):
        Book.objects.create(title='My Book', author='A', isbn=1, created_by=user)
        Book.objects.create(title='Not My Book', author='B', isbn=2, created_by=other_user)
        response = authenticated_client.get(reverse('book_list'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'My Book' in content
        assert 'Not My Book' not in content

    def test_search_filters_by_title(self, authenticated_client, user):
        Book.objects.create(title='Python Guide', author='A', isbn=1, created_by=user)
        Book.objects.create(title='Django Recipes', author='B', isbn=2, created_by=user)
        response = authenticated_client.get(reverse('book_list'), {'search_value': 'django'})
        content = response.content.decode()
        assert 'Django Recipes' in content
        assert 'Python Guide' not in content

    def test_filter_by_status(self, authenticated_client, user):
        available = Book.objects.create(title='Available', author='A', isbn=1, created_by=user, is_available=True)
        borrowed = Book.objects.create(title='Borrowed', author='B', isbn=2, created_by=user, is_available=False)
        response = authenticated_client.get(reverse('book_list'), {'filter': 'available'})
        books = response.context['books']
        assert available in books
        assert borrowed not in books

    def test_filter_by_genre(self, authenticated_client, user):
        history = Book.objects.create(title='History Book', author='A', isbn=1, created_by=user, genre='history')
        science = Book.objects.create(title='Science Book', author='B', isbn=2, created_by=user, genre='science')
        response = authenticated_client.get(reverse('book_list'), {'filter_genre': 'history'})
        books = response.context['books']
        assert history in books
        assert science not in books


class TestBorrowedBooksView:
    """Test the borrowed books view."""

    def test_only_borrowed_books(self, authenticated_client, user):
        available = Book.objects.create(title='Available', author='A', isbn=1, created_by=user, is_available=True)
        borrowed = Book.objects.create(title='Borrowed', author='B', isbn=2, created_by=user, is_available=False)
        response = authenticated_client.get(reverse('book_borrowed'))
        assert response.status_code == 200
        books = response.context['books']
        assert borrowed in books
        assert available not in books

    def test_requires_login(self, client):
        response = client.get(reverse('book_borrowed'), follow=False)
        assert response.status_code == 302


class TestBookDetailView:
    """Test the book detail view."""

    def test_owner_can_view_book(self, authenticated_client, book):
        response = authenticated_client.get(reverse('book_detail', kwargs={'pk': book.pk}))
        assert response.status_code == 200
        assert 'Sample Book' in response.content.decode()

    def test_non_owner_gets_404(self, authenticated_client, other_user, book):
        # The book is owned by the default user; other_user should not see it.
        authenticated_client.logout()
        authenticated_client.force_login(other_user)
        response = authenticated_client.get(reverse('book_detail', kwargs={'pk': book.pk}))
        assert response.status_code == 404

    def test_anonymous_user_redirected(self, client, book):
        response = client.get(reverse('book_detail', kwargs={'pk': book.pk}), follow=False)
        assert response.status_code == 302


class TestBookCreateView:
    """Test the book create view."""

    def test_create_book(self, authenticated_client, user):
        response = authenticated_client.post(reverse('book_create'), {
            'title': 'New Test Book',
            'author': 'Test Author',
            'isbn': 123456789,
            'description': 'Created by test',
            'genre': 'science',
            'is_available': True,
        }, follow=False)
        assert response.status_code == 302
        assert Book.objects.filter(title='New Test Book', created_by=user).exists()

    def test_create_book_invalid_form(self, authenticated_client):
        response = authenticated_client.post(reverse('book_create'), {
            'title': 'AB',  # too short
            'author': 'A',
            'isbn': 5555555555,
            'genre': 'fiction',
            'is_available': True,
        })
        assert response.status_code == 200
        assert not Book.objects.filter(title='AB').exists()

    def test_requires_login(self, client):
        response = client.get(reverse('book_create'), follow=False)
        assert response.status_code == 302


class TestBookUpdateView:
    """Test the book update view."""

    def test_update_book(self, authenticated_client, book):
        response = authenticated_client.post(reverse('book_update', kwargs={'pk': book.pk}), {
            'title': 'Updated Title',
            'author': 'Updated Author',
            'isbn': 987654321,
            'description': 'Updated description',
            'genre': 'history',
            'is_available': False,
        }, follow=False)
        assert response.status_code == 302
        book.refresh_from_db()
        assert book.title == 'Updated Title'
        assert book.author == 'Updated Author'
        assert book.is_available is False

    def test_non_owner_cannot_update(self, authenticated_client, other_user, book):
        authenticated_client.logout()
        authenticated_client.force_login(other_user)
        response = authenticated_client.get(reverse('book_update', kwargs={'pk': book.pk}))
        assert response.status_code == 404


class TestBookDeleteView:
    """Test the book delete view."""

    def test_delete_book(self, authenticated_client, book):
        response = authenticated_client.post(reverse('book_delete', kwargs={'pk': book.pk}), follow=False)
        assert response.status_code == 302
        assert not Book.objects.filter(pk=book.pk).exists()

    def test_non_owner_cannot_delete(self, authenticated_client, other_user, book):
        authenticated_client.logout()
        authenticated_client.force_login(other_user)
        response = authenticated_client.get(reverse('book_delete', kwargs={'pk': book.pk}))
        assert response.status_code == 404


class TestBookToggleBorrowedView:
    """Test the book availability toggle view."""

    def test_toggle_available_to_borrowed(self, authenticated_client, book):
        response = authenticated_client.post(
            reverse('book_toggle_available', kwargs={'pk': book.pk}), follow=False
        )
        assert response.status_code == 302
        book.refresh_from_db()
        assert book.is_available is False

    def test_toggle_borrowed_to_available(self, authenticated_client, book):
        book.is_available = False
        book.save()
        authenticated_client.post(reverse('book_toggle_available', kwargs={'pk': book.pk}))
        book.refresh_from_db()
        assert book.is_available is True

    def test_non_owner_cannot_toggle(self, authenticated_client, other_user, book):
        authenticated_client.logout()
        authenticated_client.force_login(other_user)
        response = authenticated_client.post(reverse('book_toggle_available', kwargs={'pk': book.pk}))
        assert response.status_code == 404
