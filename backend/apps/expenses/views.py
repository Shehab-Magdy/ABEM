"""Expense views – stubs to be fully implemented in Sprint 3."""
from rest_framework.viewsets import ModelViewSet
from .models import Expense, ExpenseCategory


class ExpenseCategoryViewSet(ModelViewSet):
    queryset = ExpenseCategory.objects.none()
    # TODO Sprint 3: serializer, building-scoped queryset


class ExpenseViewSet(ModelViewSet):
    queryset = Expense.objects.none()
    # TODO Sprint 3: split engine integration, file upload action, soft delete
