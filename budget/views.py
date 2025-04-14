from rest_framework import viewsets
from .models import FamilyMember, BudgetCategory, Transaction
from .serializers import FamilyMemberSerializer, BudgetCategorySerializer, TransactionSerializer
from rest_framework.permissions import IsAuthenticated


class FamilyMemberViewSet(viewsets.ModelViewSet):
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer


class BudgetCategoryViewSet(viewsets.ModelViewSet):
    queryset = BudgetCategory.objects.all()
    serializer_class = BudgetCategorySerializer
    permission_classes = [IsAuthenticated]


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
