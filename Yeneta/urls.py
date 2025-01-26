from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BookView, UserView, BookCheckoutView, UserBorrowingHistoryView,
    CustomTokenObtainPairView, CustomTokenRefreshView, borrowing_history_view,
    user_list, dashboard, register, login_view, logout_view, home, book_list,
    borrow_book, return_book, check_book_status,borrowing_list
)

router = DefaultRouter()
router.register(r'books', BookView, basename='book')
router.register(r'users', UserView, basename='user')
router.register(r'bookcheckout', BookCheckoutView, basename='bookcheckout')
router.register(r'borrowings', BookCheckoutView, basename='borrowings')
urlpatterns = [
    
    path('', include(router.urls)),
    path('home/', home, name='home'),
    path('user/list/', user_list, name='user_list'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('users/borrowing_history/', UserBorrowingHistoryView.as_view({'get': 'borrowing_history'}), name='user_borrowing_history'),
    path('user/borrowing_history/', borrowing_history_view, name='user_borrowing_history'),
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register, name='register'),
    path('book/', book_list, name='book_list'),
    path('borrowings/', borrowing_list, name='borrowing_list'),
    path('borrow_book/', borrow_book, name='borrow_book'),
    path('return_book/', return_book, name='return_book'),
    path('check_book_status/', check_book_status, name='check_book_status'),
]
