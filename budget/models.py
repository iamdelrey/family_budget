from django.contrib.auth.models import User
from django.db import models
import uuid


class BudgetCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class FamilyMember(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    relation = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    TRANSACTION_TYPE_CHOICES = [
        (INCOME, 'Доход'),
        (EXPENSE, 'Расход'),
    ]

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    category = models.ForeignKey('BudgetCategory', on_delete=models.CASCADE)
    member = models.ForeignKey('FamilyMembership', on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, default=EXPENSE)

    def __str__(self):
        return f"{self.amount} - {self.category.name}"


class Family(models.Model):
    name = models.CharField(max_length=255)
    created_by = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='owned_family'
    )

    def __str__(self):
        return self.name


class FamilyMembership(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('member', 'Member'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')

    def __str__(self):
        return f'{self.user.username} in {self.family.name}'


class InviteCode(models.Model):
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return str(self.code)
