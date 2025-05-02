from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    FamilyMemberViewSet,
    BudgetCategoryViewSet,
    TransactionViewSet,
    RegisterView,
    MeView,
    InviteCreateView,
    JoinFamilyView,
    CreateFamilyView,
    CurrentFamilyView,
    FamilyMembersView,
    RemoveFamilyMemberView,
    ChangeFamilyMemberRoleView
)

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
    path('family/create/', CreateFamilyView.as_view(), name='create-family'),
    path('family/me/', CurrentFamilyView.as_view(), name='family-me'),
    path('family/members/', FamilyMembersView.as_view(), name='family-members'),
    path('family/members/remove/', RemoveFamilyMemberView.as_view(), name='remove-family-member'),
    path('family/members/change-role/', ChangeFamilyMemberRoleView.as_view(), name='change-family-member-role'),

]
