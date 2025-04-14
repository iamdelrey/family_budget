from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FamilyMemberViewSet, BudgetCategoryViewSet, TransactionViewSet, RegisterView

router = DefaultRouter()
router.register(r'familymembers', FamilyMemberViewSet)
router.register(r'categories', BudgetCategoryViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
]
