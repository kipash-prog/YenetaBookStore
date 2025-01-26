from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from .serializers import BookSerializer, UserSerializer, TransactionSerializer
from .models import Book, User, Transactions
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework import filters
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.pagination import PageNumberPagination
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import IntegrityError

# Create your views here.
class BookPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class BookView(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['Title', 'Author', 'ISBN']
    ordering_fields = ['Title', 'Author', 'ISBN']
    ordering = ['Title']
    authentication_classes = [JWTAuthentication]
    pagination_class = BookPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        available = self.request.query_params.get('available', None)
        if available is not None:
            if available.lower() == 'true':
                queryset = queryset.filter(Number_of_copies_Available__gt=0)
            elif available.lower() == 'false':
                queryset = queryset.filter(Number_of_copies_Available__lte=0)
        return queryset

class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

class BookCheckoutView(viewsets.ModelViewSet):
    queryset = Transactions.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def create(self, request, *args, **kwargs):
        user = request.user
        book_id = request.data.get('book')
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        if book.Number_of_copies_Available < 1:
            return Response({"error": "No copies available"}, status=status.HTTP_400_BAD_REQUEST)

        if Transactions.objects.filter(user=user, book=book).exists():
            return Response({"error": "You have already checked out this book"}, status=status.HTTP_400_BAD_REQUEST)

        book.Number_of_copies_Available -= 1
        book.save()

        checkout = Transactions.objects.create(user=user, book=book)
        serializer = self.get_serializer(checkout)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='return')
    def return_book(self, request):
        user = request.user
        book_id = request.data.get('book')
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        checkout = Transactions.objects.filter(user=user, book=book, return_date__isnull=True).first()

        if not checkout:
            return Response({"error": "You have not checked out this book"}, status=status.HTTP_400_BAD_REQUEST)

        checkout.return_date = timezone.now().date()

        if checkout.return_date > checkout.due_date:
            overdue_days = (checkout.return_date - checkout.due_date).days
            checkout.penalty = overdue_days * 1.00  # Example penalty calculation
            send_mail(
                'Overdue Book Return',
                f'Dear {user.username}, you have returned the book "{book.Title}" {overdue_days} days late. Your penalty is ${checkout.penalty}.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        checkout.save()

        book.Number_of_copies_Available += 1
        book.save()

        serializer = self.get_serializer(checkout)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='is-returned')
    def is_returned(self, request):
        user = request.user
        book_id = request.query_params.get('book')
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        checkout = Transactions.objects.filter(user=user, book=book).first()

        if not checkout:
            return Response({"error": "You have not checked out this book"}, status=status.HTTP_400_BAD_REQUEST)

        if checkout.return_date is not None:
            return Response({"message": "Book has been returned"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Book has not been returned"}, status=status.HTTP_200_OK)

class UserBorrowingHistoryView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='borrowing-history')
    def borrowing_history(self, request):
        user = request.user
        borrowings = Transactions.objects.filter(user=user)
        serializer = TransactionSerializer(borrowings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@login_required
def borrowing_history_view(request):
    user = request.user
    borrowings = Transactions.objects.filter(user=user)
    paginator = Paginator(borrowings, 10)  # Show 10 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'borrowing_history.html', {'transactions': borrowings})

class CustomTokenObtainPairView(TokenObtainPairView):
    pass

class CustomTokenRefreshView(TokenRefreshView):
    pass

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all()
    return render(request, 'users.html', {'users': users})

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'register.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'register.html')
        user = User.objects.create_user(email=email, username=username, password=password)
        messages.success(request, 'Registration successful. Please login.')
        return redirect('login')
    else:
        return render(request, 'register.html')
    
def login_view(request):
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('borrow_book')  # Redirect to the borrow book page after successful login
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('login')  # Redirect to login page with error message
    else:
        return render(request, 'login.html')

@login_required   
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def home(request):
    return render(request, 'home.html')

@login_required  
def book_list(request):
    books = Book.objects.all()
    return render(request, 'books.html', {'books': books})

@login_required
def book_detail(request, book_id):
    book = Book.objects.get(id=book_id)
    return render(request, 'book.html', {'book': book})

@login_required
def user_detail(request, user_id):
    user = User.objects.get(id=user_id)
    return render(request, 'user.html', {'user': user})

@login_required
def borrowing_history(request, user_id):
    user = User.objects.get(id=user_id)
    borrowings = Transactions.objects.filter(user=user)
    return render(request, 'borrowings.html', {'borrowings': borrowings})

@login_required
def borrowing_detail(request, borrowing_id):
    borrowing = Transactions.objects.get(id=borrowing_id)
    return render(request, 'borrowing.html', {'borrowing': borrowing})

@login_required
def borrowing_return(request, borrowing_id):
    borrowing = Transactions.objects.get(id=borrowing_id)
    borrowing.return_date = timezone.now().date()
    borrowing.save()
    return render(request, 'borrowing.html', {'borrowing': borrowing})

@login_required
def borrowing_penalty(request, borrowing_id):
    borrowing = Transactions.objects.get(id=borrowing_id)
    overdue_days = (timezone.now().date() - borrowing.due_date).days
    borrowing.penalty = overdue_days * 1.00  # Example penalty calculation
    borrowing.save()
    return render(request, 'borrowing.html', {'borrowing': borrowing})

@login_required
def borrowing_email(request, borrowing_id):
    borrowing = Transactions.objects.get(id=borrowing_id)
    send_mail(
        'Overdue Book Return',
        f'Dear {borrowing.user.username}, you have returned the book "{borrowing.book.Title}" {borrowing.penalty} days late. Your penalty is ${borrowing.penalty}.',
        settings.DEFAULT_FROM_EMAIL,
        [borrowing.user.email],
        fail_silently=False,
    )
    return render(request, 'borrowing.html', {'borrowing': borrowing})

@login_required
def borrowing_is_returned(request, borrowing_id):
    borrowing = Transactions.objects.get(id=borrowing_id)
    if borrowing.return_date is not None:
        return render(request, 'borrowing.html', {'borrowing': borrowing, 'message': 'Book has been returned'})
    else:
        return render(request, 'borrowing.html', {'borrowing': borrowing, 'message': 'Book has not been returned'})

@login_required
def borrowing_list(request):
    borrowings = Transactions.objects.all()
    return render(request, 'borrowings.html', {'borrowings': borrowings})

@login_required
def borrow_book(request):
    user = request.user
    books = Book.objects.all()
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            messages.error(request, 'Book not found')
            return render(request, 'borrow_book.html', {'books': books})

        if book.Number_of_copies_Available < 1:
            messages.error(request, 'No copies available')
            return render(request, 'borrow_book.html', {'books': books})

        if Transactions.objects.filter(user=user, book=book, return_date__isnull=True).exists():
            messages.error(request, 'You have already borrowed this book and have not returned it yet. You cannot borrow it twice.')
            return render(request, 'borrow_book.html', {'books': books})

        book.Number_of_copies_Available -= 1
        book.save()
        
        try:
            Transactions.objects.create(user=user, book=book)
            messages.success(request, 'Book borrowed successfully')
        except IntegrityError:
            messages.error(request, 'You have already borrowed this book and have not returned it yet. You cannot borrow it twice.')
        return render(request, 'borrow_book.html', {'books': books})
    else:
        return render(request, 'borrow_book.html', {'books': books})

@login_required
def return_book(request):
    user = request.user
    books = Book.objects.all()
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            messages.error(request, 'Book not found')
            return render(request, 'borrow_book.html', {'books': books})

        checkout = Transactions.objects.filter(user=user, book=book, return_date__isnull=True).first()

        if not checkout:
            messages.error(request, 'You have not checked out this book')
            return render(request, 'borrow_book.html', {'books': books})

        checkout.return_date = timezone.now().date()
        
        if checkout.return_date > checkout.due_date:
            overdue_days = (checkout.return_date - checkout.due_date).days
            checkout.penalty = overdue_days * 1.00  # Example penalty calculation
            send_mail(
                'Overdue Book Return',
                f'Dear {user.username}, you have returned the book "{book.Title}" {overdue_days} days late. Your penalty is ${checkout.penalty}.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        checkout.save()

        book.Number_of_copies_Available += 1
        book.save()

        messages.success(request, 'Book returned successfully')
        return render(request, 'borrow_book.html', {'books': books})
    else:
        return render(request, 'borrow_book.html', {'books': books})
        
@login_required
def check_book_status(request):
    user = request.user
    books = Book.objects.all()
    if request.method == 'GET':
        book_id = request.GET.get('book_id')
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            messages.error(request, 'Book not found')
            return render(request, 'borrow_book.html', {'books': books})

        checkout = Transactions.objects.filter(user=user, book=book).first()

        if not checkout:
            messages.error(request, 'You have not checked out this book')
            return render(request, 'borrow_book.html', {'books': books})

        if checkout.return_date is not None:
            messages.success(request, 'Book has been returned')
            
        else:
            messages.info(request, 'Book has not been returned')
        return render(request, 'borrow_book.html', {'books': books})
    else:
        return render(request, 'borrow_book.html', {'books': books})          
