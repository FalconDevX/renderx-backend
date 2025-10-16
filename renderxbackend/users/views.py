from django.http import response
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Users
from rest_framework import status

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