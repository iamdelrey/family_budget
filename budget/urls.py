from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import FamilyMemberViewSet, BudgetCategoryViewSet, TransactionViewSet, RegisterView, MeView
from .views import InviteCreateView, JoinFamilyView

router = DefaultRouter()
router.register(r'familymembers', FamilyMemberViewSet)
router.register(r'categories', BudgetCategoryViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', MeView.as_view(), name='me'),
    path('invite/', InviteCreateView.as_view(), name='invite-create'),
    path('join/', JoinFamilyView.as_view(), name='join-family'),
]
