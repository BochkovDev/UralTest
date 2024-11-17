from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import Category, Material


class MaterialSerializer(serializers.ModelSerializer):
    ''' Сериализатор для материалов '''
    class Meta:
        model = Material
        fields = ['id', 'category', 'code', 'name', 'cost']

class CategorySerializer(serializers.ModelSerializer):
    materials = MaterialSerializer(many=True, read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'parent', 'code', 'name', 'materials']

class CategoryTreeSerializer(serializers.ModelSerializer):
    materials = MaterialSerializer(many=True, read_only=True)
    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'code', 'materials', 'children']

    def get_children(self, obj):
        """
        Рекурсивно сериализует дочерние категории.
        """
        if hasattr(obj, 'child_list'):
            return CategoryTreeSerializer(obj.child_list, many=True).data
        return []
CategoryTreeSerializer.get_children = extend_schema_field(
    CategoryTreeSerializer(many=True)
)(
    CategoryTreeSerializer.get_children
)