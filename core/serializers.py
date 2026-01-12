from rest_framework import serializers
from .models import Product, Contact, RentalContract, Transaction, CapitalAccount
from django.utils import timezone
import datetime

class ProductSerializer(serializers.ModelSerializer):
    color_tag = serializers.SerializerMethodField()
    flow_history = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_color_tag(self, obj):
        today = timezone.now().date()
        
        # 1. 外部资产 (在租/中转) 逻辑
        if obj.status in ['RENTED', 'TRANSIT']:
            # 找当前活跃合同
            contract = RentalContract.objects.filter(product=obj, is_active=True).first()
            if not contract or not contract.end_date:
                return 'green' # 默认刚租出
            
            # 计算剩余天数
            days_left = (contract.end_date - today).days
            
            # 刚租出：起租日距离今天在7天内
            days_since_start = (today - contract.start_date).days
            
            if days_left < 7: return 'red' # 🔴 马上到期 (7天内)
            if days_since_start < 7: return 'green' # 🟢 刚租出去 (7天内)
            return 'yellow' # 🟡 中间状态

        # 2. 在库资产逻辑 (库存积压预警)
        if obj.created_at:
            entry_date = obj.created_at.date()
            stock_days = (today - entry_date).days
            
            if stock_days < 30: return 'green' # 🟢 30天内 (新鲜)
            if stock_days < 90: return 'yellow' # 🟡 30-90天 (一般)
            return 'red' # 🔴 90天以上 (积压)
        return 'green'

    def get_flow_history(self, obj):
        # 抓取所有相关流水：包括采购、租赁开单、归还、销售
        txs = Transaction.objects.filter(product=obj).order_by('-created_at')
        return [{
            'date': t.created_at.strftime('%Y-%m-%d'),
            'type': t.get_type_display(),
            'operator': t.operator.initials if t.operator else '系统',
            'desc': t.remark or '-'
        } for t in txs]

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

class RentalContractSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_zencode = serializers.CharField(source='product.zencode', read_only=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    class Meta:
        model = RentalContract
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'