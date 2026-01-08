from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Contact, Product, RentalContract
from .models import CapitalAccount, Transaction

@admin.register(CapitalAccount)
class CapitalAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'initial_balance', 'current_balance')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('type', 'amount', 'contact', 'account', 'created_at')
    list_filter = ('type', 'account')

# --- 1. 用户管理 (本土化优化) ---
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # 列表页显示：账号、姓名(拼)、角色、首字母
    list_display = ('username', 'get_full_name_cn', 'role', 'initials', 'is_staff')
    
    # 定义一个符合中国人习惯的姓名显示方法
    def get_full_name_cn(self, obj):
        return f"{obj.last_name}{obj.first_name}"
    get_full_name_cn.short_description = '姓名'

    # 编辑页面：把姓和名放在一行
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': (('last_name', 'first_name'), 'email', 'initials', 'role')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
    )

# --- 2. 库存商品 (显示核心数据) ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # 列表页显示哪些列
    list_display = ('zencode', 'name', 'category', 'status', 'cost_price', 'peer_price', 'retail_price')
    # 右侧筛选器
    list_filter = ('category', 'status', 'created_at')
    # 搜索框
    search_fields = ('name', 'zencode', 'note')
    # 只读字段 (防止人工篡改流水号)
    readonly_fields = ('zencode', 'created_at')

# --- 3. 往来/客户 ---
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'address', 'balance')
    search_fields = ('name', 'phone')

# --- 4. 租赁合约 ---
@admin.register(RentalContract)
class RentalContractAdmin(admin.ModelAdmin):
    list_display = ('contact', 'product', 'start_date', 'rent_amount', 'is_active')
    list_filter = ('is_active', 'start_date')