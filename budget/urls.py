from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FamilyMemberViewSet, BudgetCategoryViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'family-members', FamilyMemberViewSet)
router.register(r'categories', BudgetCategoryViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
