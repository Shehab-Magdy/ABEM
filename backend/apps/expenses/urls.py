from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LateFeeViewSet, ExpenseViewSet, ExpenseCategoryViewSet

router = DefaultRouter()
router.register("late-fees", LateFeeViewSet, basename="late-fee")
router.register("categories", ExpenseCategoryViewSet, basename="expense-category")
router.register("", ExpenseViewSet, basename="expense")

urlpatterns = [path("", include(router.urls))]
