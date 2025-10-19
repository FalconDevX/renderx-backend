from itertools import product
from unicodedata import category
from django.http import response
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Users
from rest_framework import status
from .serializers import ProductSerializer
from .models import Products

@api_view(['POST'])
def register_user(request):
    data = request.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)
    
    if Users.objects.filter(username=username).exists():
        return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    password_hash = make_password(password)
    user = Users.objects.create(username=username, email=email, password_hash=password_hash)

    return Response({"message": f"User {user.username} created successfully!"}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login_user(request):
    data = request.data
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

    user = Users.objects.filter(email=email).first()

    if not user:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if not check_password(password, user.password_hash):
        return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)

    #generatiing JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    #httpOnly cookie for refresh token
    response = Response({
        "access": access_token,
        "user": {"username": user.username, "email": user.email}
    })

    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        httponly=True,
        secure=False,  
        samesite='Lax',
        max_age=7 * 24 * 60 * 60,
    )

    return response

@api_view(['POST'])
def refresh_token(request):
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return Response({"error": "Refresh token not found"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        refresh = RefreshToken(refresh_token)
        new_access_token = str(refresh.access_token)
        return Response({
            "access": new_access_token,
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProductSearchView(APIView):
    def get(self, request):
        name = request.GET.get('name','').strip()
        category = request.GET.get('category','').strip()
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')

        products = Products.objects.all()

        if name: 
            products = products.filter(name__icontains=name)
        if category:
            products = products.filter(category__iexact=category)
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProductManagementView(APIView):
    def get(self, request):
        product_id = request.GET.get('id')
        if not product_id:
            return Response(
                {"error": "Product ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            product = Products.objects.get(pk=product_id)
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Products.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
    def post(self, request):
        data = request.data
        name = data.get("name")
        description = data.get("description")
        category = data.get("category")
        brand = data.get("brand")
        price = data.get("price")
        stock = data.get("stock")
        image_url = data.get("image_url")
        is_available = data.get("is_available", True)

        

        if not name or not description or not category or not brand or not price or not stock:
            return Response({"error": "missing fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            return Response({"error": "Invalid price or stock value"}, status=status.HTTP_400_BAD_REQUEST)


        if Products.objects.filter(name=name).exists():
            return Response({"error": "Product already exists"}, status=status.HTTP_400_BAD_REQUEST)

        product = Products.objects.create(name=name, description=description, category=category, brand=brand, price=price, stock=stock, image_url=image_url, is_available=is_available)
        return Response({"message": f"Product {product.name} created successfully!"}, status=status.HTTP_201_CREATED)
    
    def put(self,request):
        data = request.data
        product_id = data.get("id")
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Products.objects.get(pk=product_id)
            price = data.get("price")
            stock = data.get("stock")

            if price is not None:
                try:
                    product.price = float(price)
                except ValueError:
                    return Response({"error": "Invalid price value"}, status=status.HTTP_400_BAD_REQUEST)
            if stock is not None:
                try:
                    product.stock = int(stock)
                except ValueError:
                    return Response({"error": "Invalid stock value"}, status=status.HTTP_400_BAD_REQUEST)

            name = data.get("name")
            description = data.get("description")
            category = data.get("category")
            brand = data.get("brand")
            image_url = data.get("image_url")
            is_available = data.get("is_available", True)

            if name:
                product.name = name
            if description:
                product.description = description
            if category:
                product.category = category
            if brand:
                product.brand = brand
            if price:
                product.price = price
            if stock:
                product.stock = stock
            if image_url:
                product.image_url = image_url
            if is_available is not None:
                product.is_available = is_available
            product.save()
            return Response({"message": f"Product {product.name} updated successfully!"}, status=status.HTTP_200_OK)
        except Products.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self,request):
        data = request.data
        product_id = data.get("id")
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Products.objects.get(pk=product_id)
            product.delete()
            return Response({"message": f"Product {product.name} deleted successfully!"}, status=status.HTTP_200_OK)
        except Products.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)