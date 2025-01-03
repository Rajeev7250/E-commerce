from rest_framework import serializers
from .models import Product, Category

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    thumbnail_img = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'title', 'price', 
            'is_in_stock', 'stock', 'category_name', 
            'description', 'created_at', 'updated_at', 
            'thumbnail_img'
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_thumbnail_img(self, obj):
        return obj.thumbnail_img.url if obj.thumbnail_img else None