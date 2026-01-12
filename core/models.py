from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# 1. 用户
class CustomUser(AbstractUser):
    ROLE_CHOICES = (('ADMIN', '管理员'), ('FINANCE', '财务'), ('SALES', '销售'))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='SALES', verbose_name="角色")
    initials = models.CharField(max_length=5, default='XX', verbose_name="姓名首字母")
    class Meta: verbose_name = "员工账号"; verbose_name_plural = verbose_name

# 2. 资金账户
class CapitalAccount(models.Model):
    name = models.CharField(max_length=50, verbose_name="账户名称")
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="期初余额")
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="当前余额")
    def __str__(self): return f"{self.name} (¥{self.current_balance})"
    class Meta: verbose_name = "资金账户"; verbose_name_plural = verbose_name

# 3. 客户/供应商
class Contact(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="姓名/昵称")
    phone = models.CharField(max_length=20, blank=True, verbose_name="电话")
    address = models.CharField(max_length=100, blank=True, verbose_name="地址/档口")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="应收/应付余额")
    def __str__(self): return self.name
    class Meta: verbose_name = "客户/供应商"; verbose_name_plural = verbose_name

# 4. 商品
class Product(models.Model):
    TYPE_CHOICES = (('ZJ', '整机'), ('SJ', '散件'), ('XS', '显示器'), ('ZX', '杂项'))
    STATUS_CHOICES = (('IN_STOCK', '在库'), ('RENTED', '在租'), ('TRANSIT', '中转/外借'), ('SOLD', '已售'), ('REPAIR', '维修'))
    
    zencode = models.CharField(max_length=20, unique=True, blank=True, verbose_name="ZenCode编码")
    name = models.CharField(max_length=200, blank=True, verbose_name="商品名称")
    category = models.CharField(max_length=2, choices=TYPE_CHOICES, verbose_name="分类")
    
    cpu = models.CharField(max_length=50, blank=True, verbose_name="CPU")
    gpu = models.CharField(max_length=50, blank=True, verbose_name="显卡")
    ram = models.CharField(max_length=50, blank=True, verbose_name="内存")
    disk = models.CharField(max_length=50, blank=True, verbose_name="硬盘")
    note = models.CharField(max_length=100, blank=True, verbose_name="备注")
    
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="入库成本")
    peer_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="同行底价")
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="零售指导")
    sold_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="实际成交价")
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='IN_STOCK', verbose_name="当前状态")
    image = models.ImageField(upload_to='%Y/%m/', blank=True, null=True, verbose_name="图片")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="入库时间")
    class Meta: verbose_name = "库存商品"; verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        if self.category == 'ZJ' and not self.name:
            parts = []
            if self.cpu: parts.append(self.cpu)
            if self.ram: parts.append(self.ram)
            if self.disk: parts.append(self.disk)
            if self.gpu and self.gpu not in ["核显", "核显主机"]:
                parts.append(self.gpu)
                if self.note: parts.append(self.note)
            else:
                if self.note: parts.append(self.note)
                if self.cpu: parts.append("核显主机")
            self.name = " ".join([p for p in parts if p])
        super().save(*args, **kwargs)

# 5. 租赁合约 (精简版)
class RentalContract(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, verbose_name="客户")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="设备")
    operator = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, verbose_name="经手人")
    
    start_date = models.DateField(default=timezone.now, verbose_name="起租日")
    duration = models.IntegerField(default=1, verbose_name="租期(月)")
    end_date = models.DateField(null=True, blank=True, verbose_name="归还日")
    
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="实收押金")
    # ❌ 删除了 rent_strategy (Web已写死，小程序逻辑重复)
    rent_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="租金单价")
    # ❌ 删除了 initial_value (重复数据)
    depreciation_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="月折旧估算")
    
    # 财务核心字段 (保留)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="合同总额")
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="已付租金")
    expected_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="预估毛利")
    
    is_active = models.BooleanField(default=True, verbose_name="租赁中")
    class Meta: verbose_name = "租赁合同"; verbose_name_plural = verbose_name

# 6. 资金流水
class Transaction(models.Model):
    TYPE_CHOICES = (('SALE', '销售收入'), ('RENT', '租金/押金'), ('BUY', '采购支出'), ('OTHER', '其他'))
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, verbose_name="关联方")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联商品")
    account = models.ForeignKey(CapitalAccount, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="资金账户")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="金额")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="类型")
    operator = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, verbose_name="经手人")
    remark = models.CharField(max_length=200, blank=True, verbose_name="摘要")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="时间")
    class Meta: verbose_name = "财务流水"; verbose_name_plural = verbose_name