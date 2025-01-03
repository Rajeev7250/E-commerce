from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Status and Role choices
STATUS_CHOICES = (
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
)

ROLE_CHOICES = (
    ('Admin', 'Admin'),
    ('Customer', 'Customer'),
)


class User(AbstractUser):
    phone_number = models.PositiveBigIntegerField(blank=True, null=True)
    email = models.EmailField(max_length=223)
    bio = models.TextField(blank=True)
    date_of_b = models.DateField(null=True, blank=True)
    user_profile_image = models.ImageField(upload_to='user', blank=True)  
    address = models.TextField(blank=True) 
    pin_code = models.PositiveBigIntegerField(blank=True, null=True)  
    city = models.CharField(max_length=250)
    state = models.CharField(max_length=250)
    country = models.CharField(max_length=250)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default='Customer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Inactive')

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username  



class Product(models.Model):
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True, null=True)
    sku = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    thumbnail_img = models.ImageField(upload_to='thumbnail_img/', blank=True, null=True)
    is_in_stock = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='productimage_set', on_delete=models.CASCADE)
    file = models.ImageField(upload_to='product_images/')
    title = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.title or 'Image'}"

class ProductDetail(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    gender = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    quantity = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.product.name} - {self.size}, {self.color}"

class Category(models.Model):
    name = models.CharField(max_length=100, default='Uncategorized')  # Add a default value
    slug = models.SlugField(unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return sum(item.get_subtotal() for item in self.cartitem_set.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    
    def get_subtotal(self):
        return self.product.price * self.quantity