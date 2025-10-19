from django.contrib import admin
from django.urls import path
from users import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("register/", views.register_user, name="register_user"),
    path("login/", views.login_user, name="login_user"),
    path("refresh/", views.refresh_token, name="refresh_token"),
    path("products/", views.ProductSearchView.as_view(), name="products_search"),
    path("product/", views.ProductManagementView.as_view(), name="product_managment")
]
