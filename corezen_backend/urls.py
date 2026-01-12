from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core import views

# 注册 API 路由
router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'contacts', views.ContactViewSet)
router.register(r'rentals', views.RentalViewSet)
router.register(r'analysis', views.AnalysisViewSet, basename='analysis')

urlpatterns = [
    # 🟢 1. 找回后台管理入口
    path('admin/', admin.site.urls),

    # 🟢 2. 业务页面路由
    path('', views.index_page, name='index'),
    path('login/', views.login_page, name='login'),
    path('entry/', views.entry_page, name='entry'),
    path('sales/', views.sales_page, name='sales'),
    path('contact/', views.contact_page, name='contact'),
    path('inventory/', views.inventory_page, name='inventory'),
    path('rental/', views.rental_hub_page, name='rental_hub'),
    path('rental/create/', views.rental_create_page, name='rental_create'),
    
    # 财务与报表页面
    path('analysis/profit/', views.profit_page, name='profit'),
    path('analysis/finance/', views.finance_page, name='finance'),
    path('analysis/account/', views.account_page, name='account'),
    path('profile/', views.profile_page, name='profile'),

    # 🟢 3. API 接口
    path('api/login/', views.api_login),
    path('api/logout/', views.api_logout),
    path('api/change_password/', views.api_change_password),
    
    # 自动生成的 REST API
    path('api/', include(router.urls)),
]