from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from core.views import *

# 注册 API 路由
router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'rentals', RentalViewSet)
router.register(r'analysis', AnalysisViewSet, basename='analysis')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    # --- 核心页面 ---
    path('', index_page),          # 首页工作台
    path('entry/', entry_page),    # 极速入库
    path('sales/', sales_page),    # 销售开单
    path('contact/', contact_page),# 往来管理
    path('inventory/', inventory_page), # 库存列表
    
    # --- 租赁系统 (这里修正了) ---
    path('rental/', rental_hub_page),       # 新版租赁大厅
    path('rental/create/', rental_create_page), # 新建租赁单
    path('return/', rental_hub_page),       # 兼容旧链接 -> 指向租赁大厅
    
    # --- 经营报表 ---
    path('analysis/profit/', profit_page),
    path('analysis/finance/', finance_page),
    path('analysis/account/', account_page),
]

# 静态资源 (图片)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)