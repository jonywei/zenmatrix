from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CapitalAccount, Contact, Product, RentalContract, Transaction

# 1. 用户管理
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('员工信息', {'fields': ('role', 'initials')}),
    )
    list_display = ('username', 'role', 'initials', 'is_superuser', 'is_active')
    list_filter = ('role', 'is_active')

# 2. 资金账户
@admin.register(CapitalAccount)
class CapitalAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_balance', 'initial_balance')

# 3. 客户/供应商
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'balance', 'address')
    search_fields = ('name', 'phone')

# 4. 商品库存
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('zencode', 'name', 'category', 'status', 'cost_price', 'created_at')
    list_filter = ('category', 'status')
    search_fields = ('name', 'zencode', 'note')
    readonly_fields = ('created_at',)

# 5. 租赁合同 (已修复)
@admin.register(RentalContract)
class RentalContractAdmin(admin.ModelAdmin):
    # 🟢 修复：去掉了 rent_strategy 和 initial_value
    list_display = ('id', 'contact', 'product', 'start_date', 'duration', 'rent_price', 'total_amount', 'is_active')
    # 🟢 修复：list_filter 中去掉了 rent_strategy
    list_filter = ('is_active', 'start_date') 
    search_fields = ('contact__name', 'product__zencode', 'product__name')
    autocomplete_fields = ('contact', 'product')

# 6. 资金流水
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'amount', 'contact', 'account', 'created_at', 'operator')
    list_filter = ('type', 'created_at', 'account')
    search_fields = ('remark', 'contact__name')
    readonly_fields = ('created_at',)