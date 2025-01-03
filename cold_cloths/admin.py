from django.contrib import admin
from .models import User, Product, ProductDetail, ProductImage, Category,Cart,CartItem




class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # Number of empty image upload slots

class ProductDetailInline(admin.StackedInline):
    model = ProductDetail
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline, ProductDetailInline]
    list_display = ('name','sku', 'price', 'category', 'is_in_stock', 'stock')
    list_filter = ('category', 'is_in_stock')
    search_fields = ('name', 'description')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(ProductImage)
admin.site.register(ProductDetail)
admin.site.register(User)
