"""
Beauty Salon - Search & Filter Classes

Service aur Product filtering:
- Category se filter
- Price range se filter
- Featured filter
- In-stock filter
"""

import django_filters
from .models import Service, Product


class ServiceFilter(django_filters.FilterSet):
    """
    GET /api/services/?category=1&min_price=100&max_price=500&is_featured=true
    """
    min_price = django_filters.NumberFilter(field_name='original_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='original_price', lookup_expr='lte')
    has_discount = django_filters.BooleanFilter(
        field_name='discount_percent', method='filter_has_discount'
    )
    category_name = django_filters.CharFilter(
        field_name='category__name', lookup_expr='icontains'
    )

    class Meta:
        model = Service
        fields = ['category', 'is_featured', 'is_active', 'min_price', 'max_price']

    def filter_has_discount(self, queryset, name, value):
        if value:
            return queryset.filter(discount_percent__gt=0)
        return queryset.filter(discount_percent=0)


class ProductFilter(django_filters.FilterSet):
    """
    GET /api/products/?category=1&min_price=50&max_price=1000&in_stock=true&has_discount=true
    """
    min_price = django_filters.NumberFilter(field_name='original_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='original_price', lookup_expr='lte')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')
    category_name = django_filters.CharFilter(
        field_name='category__name', lookup_expr='icontains'
    )
    brand = django_filters.CharFilter(field_name='brand', lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['category', 'is_featured', 'is_active', 'min_price', 'max_price']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)

    def filter_has_discount(self, queryset, name, value):
        if value:
            return queryset.filter(discount_percent__gt=0)
        return queryset.filter(discount_percent=0)