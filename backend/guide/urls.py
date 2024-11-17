from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MaterialListView,
    MaterialDetailView,
    CategoryViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('materials/', MaterialListView.as_view(), name='material-list'),
    path('materials/<int:id>/', MaterialDetailView.as_view(), name='material-detail'),
]