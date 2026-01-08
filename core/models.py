from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime

# 1. 用户
class CustomUser(AbstractUser):
    ROLE_CHOICES = (('ADMIN', '管理员'), ('FINANCE', '财务'), ('SALES', '销售'))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='SALES', verbose_name="角色")
    initials = models.CharField(max_length=5, default='XX', verbose_name="姓名首字母")

# 2. 资金账户 (New! 财务核心)
class CapitalAccount(models.Model):
    name = models.CharField(max_length=50, verbose_name="账户名称", help_text="如: 支付宝, 微信, 银行卡")
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="期初余额")
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="当前余额")
    
    def __str__(self): return f"{self.name} (¥{self.current_balance})"

# 3. 往来 (人)
class Contact(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="姓名")
    phone = models.CharField(max_length=20, blank=True, verbose_name="电话")
    address = models.CharField(max_length=100, blank=True, verbose_name="地址/档口")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="应收/应付") # 正数=他欠我
    def __str__(self): return self.name

# 4. 商品 (货)
class Product(models.Model):
    TYPE_CHOICES = (('ZJ', '整机'), ('SJ', '散件'), ('XS', '显示器'), ('ZX', '杂项'))
    STATUS_CHOICES = (('IN_STOCK', '在库'), ('RENTED', '在租'), ('SOLD', '已售'), ('REPAIR', '维修'))
    zencode = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=2, choices=TYPE_CHOICES)
    cpu = models.CharField(max_length=50, blank=True)
    gpu = models.CharField(max_length=50, blank=True)
    ram = models.CharField(max_length=50, blank=True)
    disk = models.CharField(max_length=50, blank=True)
    note = models.CharField(max_length=100, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peer_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sold_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='IN_STOCK')
    image = models.ImageField(upload_to='%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.category == 'ZJ' and not self.name:
            gpu_str = self.gpu if self.gpu else "核显"
            parts = [self.cpu, gpu_str, self.ram, self.disk, self.note]
            self.name = " ".join([p for p in parts if p])
        if not self.zencode:
            now = timezone.now()
            year = str(now.year)[-2:]
            month_map = {10: 'A', 11: 'B', 12: 'C'}
            month = month_map.get(now.month, str(now.month))
            day = f"{now.day:02d}"
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            count = self.__class__.objects.filter(created_at__gte=today_start, category=self.category).count() + 1
            self.zencode = f"{year}{month}{day}AD{self.category}{count}"
        super().save(*args, **kwargs)

# 5. 租赁
class RentalContract(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    initial_value = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

# 6. 交易流水 (核心升级：关联资金账户)
class Transaction(models.Model):
    TYPE_CHOICES = (('SALE', '销售收入'), ('RENT', '租金收入'), ('BUY', '采购支出'), ('OTHER', '其他'))
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey(CapitalAccount, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="资金账户")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    operator = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    remark = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)