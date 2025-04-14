from django.db import models
from django.contrib.auth.models import User


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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.amount} - {self.category.name}"
