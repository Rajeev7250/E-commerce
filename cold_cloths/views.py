from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from cold_cloths.models import User
from .forms import UserLoginForm, UserSignUpForm, ProfileEditForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product, Category, ProductDetail, ProductImage
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from .models import Cart, CartItem
from django.http import JsonResponse
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.core.paginator import Paginator




def home(request):
    return render(request, 'cold_cloths/home.html')
    


def is_admin(user):
    return user.role == 'Admin'

@login_required
@user_passes_test(is_admin)
def add_product(request):
    if request.method == 'POST':
        try:
            # Create Product
            product = Product.objects.create(
                title=request.POST['title'],
                sku =request.POST['sku'],
                name=request.POST['name'],
                description=request.POST['description'],
                price=request.POST['price'],
                stock=request.POST['stock'],
                category_id=request.POST['category'],
                thumbnail_img=request.FILES.get('thumbnail_img')
            )
            
            # Create Product Detail
            ProductDetail.objects.create(
                product=product,
                size=request.POST['size'],
                color=request.POST['color'],
                gender=request.POST['gender'],
                type=request.POST['type']
            )
            
            # Handle multiple product images
            image_files = request.FILES.getlist('product_images[]')
            image_titles = request.POST.getlist('image_titles[]')
            
            for file, title in zip(image_files, image_titles):
                if file and title:
                    ProductImage.objects.create(
                        product=product,
                        title=title,
                        file=file
                    )
            
            messages.success(request, 'Product added successfully!')
            return redirect('product_list')
            
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
    
    categories = Category.objects.all()
    return render(request, 'cold_cloths/add_product.html', {'categories': categories})

    
def product_list(request):
    products = Product.objects.all().select_related('category')

    if request.user.is_authenticated:
        # Assuming the user has a cart; modify according to your model setup
        cart = Cart.objects.filter(user=request.user).first()
        cart_items = CartItem.objects.filter(cart=cart).select_related('product') if cart else []
    else:
        cart_items = []

    cart_product_ids = [item.product.id for item in cart_items]

    return render(request, 'cold_cloths/product_list.html', {
        'products': products,
        'cart_product_ids': cart_product_ids
    })


@login_required
@user_passes_test(is_admin)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        try:
            # Update product fields
            product.title = request.POST['title']
            product.sku = request.POST['sku']
            product.name = request.POST['name']
            product.description = request.POST['description']
            product.price = request.POST['price']
            product.stock = request.POST['stock']
            product.category_id = request.POST['category']
            
            if 'thumbnail_img' in request.FILES:
                product.thumbnail_img = request.FILES['thumbnail_img']
            
            product.save()
            
            # Update product detail
            product_detail = product.productdetail_set.first()
            if product_detail:
                product_detail.size = request.POST['size']
                product_detail.color = request.POST['color']
                product_detail.gender = request.POST['gender']
                product_detail.type = request.POST['type']
                product_detail.save()
            
            messages.success(request, 'Product updated successfully!')
            return redirect('product_list')
            
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    categories = Category.objects.all()
    return render(request, 'cold_cloths/edit_product.html', {
        'product': product,
        'categories': categories
    })

@login_required
@user_passes_test(is_admin)
def delete_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        messages.success(request, 'Product deleted successfully!')
    return redirect('product_list')


def product_detail(request, pk):
    # Get the product with its related details
    product = get_object_or_404(Product, id=pk)
    
    # Get product details
    try:
        product_details = product.productdetail_set.first()
        
        # Get additional images for the product
        additional_images = product.productimage_set.all()
        
        context = {
            'product': product,
            'product_details': product_details,
            'additional_images': additional_images
        }
        
        return render(request, 'cold_cloths/product_detail.html', context)
    except Exception as e:
        messages.error(request, f'Error fetching product details: {str(e)}')
        return redirect('product_list')



@require_POST
def add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login first'}, status=401)
    
    data = json.loads(request.body)
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    size = data.get('size')
    color = data.get('color')
    
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Check if item already exists in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=size,
        color=color,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    cart_count = cart.cartitem_set.count()
    total_price = cart.get_total_price()
    
    return JsonResponse({
        'message': 'Product added to cart',
        'cart_count': cart_count,
        'total_price': str(total_price)
    })

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.select_related('product').all()
    
    context = {
        'cart_items': cart_items,
        'total_price': cart.get_total_price()
    }
    return render(request, 'cold_cloths/cart.html', context)

@require_POST
def update_cart_item(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login first'}, status=401)
    
    data = json.loads(request.body)
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))
    
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.quantity = quantity
    cart_item.save()
    
    cart = cart_item.cart
    return JsonResponse({
        'subtotal': str(cart_item.get_subtotal()),
        'total_price': str(cart.get_total_price())
    })

@require_POST
def remove_from_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login first'}, status=401)
    
    data = json.loads(request.body)
    item_id = data.get('item_id')
    
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart = cart_item.cart
    cart_item.delete()
    
    return JsonResponse({
        'message': 'Item removed from cart',
        'total_price': str(cart.get_total_price())
    })
    


class ProductDataTableView(APIView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        # DataTables parameters
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Sorting parameters
        order_column = request.GET.get('order[0][column]', '')
        order_dir = request.GET.get('order[0][dir]', 'asc')
        
        # Columns for sorting and searching
        columns = [
            'id', 'sku', 'thumbnail_img', 'name', 'title', 
            'price', 'is_in_stock', 'stock', 'category__name', 
            'description', 'created_at', 'updated_at'
        ]
        
        # Base queryset with category relationship
        queryset = Product.objects.select_related('category')
        
        # Global search across multiple fields
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) | 
                Q(sku__icontains=search_value) | 
                Q(title__icontains=search_value) |
                Q(category__name__icontains=search_value)
            )
        
        # Sorting
        if order_column and 0 <= int(order_column) < len(columns):
            sort_column = columns[int(order_column)]
            if order_dir == 'desc':
                sort_column = f'-{sort_column}'
            queryset = queryset.order_by(sort_column)
        
        # Total records
        total_records = queryset.count()
        
        # Paginate
        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page_obj = paginator.get_page(page_number)
        
        # Prepare data for DataTables
        data = []
        for product in page_obj:
            data.append({
                'DT_RowId': product.id,
                'actions': f'''
                    <div class="btn-group" role="group">
                        <a href="/product/edit/{product.id}/" class="btn btn-sm btn-primary">Edit</a>
                        <button class="btn btn-sm btn-danger delete-product" data-id="{product.id}" data-name="{product.name}">Delete</button>
                    </div>
                ''',
                'sku': product.sku,
                'thumbnail': f'<img src="{product.thumbnail_img.url if product.thumbnail_img else ""}" style="max-width:50px; max-height:50px;" />' if product.thumbnail_img else 'No Image',
                'name': product.name,
                'title': product.title,
                'price': f'₹{product.price:.2f}',
                'stock_status': 'In Stock' if product.stock > 0 else 'Out of Stock',
                'stock': product.stock,
                'category': product.category.name if product.category else 'No Category',
                'description': product.description,
                'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': product.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # DataTables response format
        response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        }
        
        return Response(response)
        
def signup_view(request):
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            # Create user but don't save yet
            user = form.save(commit=False)
            # Hash the password properly
            raw_password = form.cleaned_data.get('password')
            user.password = make_password(raw_password)
            user.save()
            
            # Authenticate and login the user
            auth_user = authenticate(username=user.username, password=raw_password)
            if auth_user:
                login(request, auth_user)
                messages.success(request, "Account created successfully!")
                return redirect('home')
            else:
                messages.error(request, "Error during authentication!")
    else:
        form = UserSignUpForm()
    return render(request, 'cold_cloths/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, "Successfully logged in!")
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password!")
    else:
        form = UserLoginForm()
    
    return render(request, 'cold_cloths/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('product_list')


@login_required
def profile_view(request):
    return render(request, 'cold_cloths/profile.html', {
        'user': request.user
    })

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(
            request.POST, 
            request.FILES, 
            instance=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'cold_cloths/profile_edit.html', {
        'form': form
    })
    
