from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CapitalAccount, Contact, Product, RentalContract, Transaction

# 1. 员工/用户管理
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'role', 'initials', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('员工信息', {'fields': ('role', 'initials')}),
    )

# 2. 资金账户管理
@admin.register(CapitalAccount)
class CapitalAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_balance', 'initial_balance')

# 3. 客户/供应商档案
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'balance', 'address')
    search_fields = ('name', 'phone')

# 4. 商品库存管理
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('zencode', 'name', 'category', 'status', 'cost_price', 'retail_price', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('name', 'zencode', 'note')

# 5. 租赁合同管理 (核心修复点)
@admin.register(RentalContract)
class RentalContractAdmin(admin.ModelAdmin):
    # 修复：这里原来写的是 rent_amount，现在改成了 rent_price
    list_display = ('contact', 'product', 'start_date', 'rent_price', 'deposit_amount', 'is_active')
    list_filter = ('is_active', 'rent_strategy')
    search_fields = ('contact__name', 'product__zencode')

# 6. 资金/交易流水
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('type', 'amount', 'contact', 'account', 'created_at', 'operator')
    list_filter = ('type', 'account', 'created_at')
    search_fields = ('contact__name', 'remark')
# ... (保留上面的代码)

# 隐藏系统自带的 "组" (Groups)，让后台更干净
from django.contrib.auth.models import Group
admin.site.unregister(Group)

# 修改后台顶部的标题，看着更正规
admin.site.site_header = 'ZenMatrix 经营管理后台'
admin.site.site_title = 'ZenMatrix'
admin.site.index_title = '企业数据中心'