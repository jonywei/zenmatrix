from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from core.views import *

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'rentals', RentalViewSet)
router.register(r'analysis', AnalysisViewSet, basename='analysis')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    # 核心页面
    path('', index_page),
    path('entry/', entry_page),
    path('sales/', sales_page),
    path('contact/', contact_page),
    path('inventory/', inventory_page),
    
    # 租赁
    path('rental/', rental_hub_page),
    path('rental/create/', rental_create_page),
    path('return/', rental_hub_page),
    
    # 报表
    path('analysis/profit/', profit_page),
    path('analysis/finance/', finance_page),
    path('analysis/account/', account_page),
    
    # 登录与用户 (Day 6 新增)
    path('login/', login_page),
    path('profile/', profile_page),
    
    # Auth API
    path('api/login/', api_login),
    path('api/logout/', api_logout),
    path('api/change_password/', api_change_password),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)