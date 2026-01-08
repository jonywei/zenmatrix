from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import render
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
from .models import Product, Contact, RentalContract, Transaction, CapitalAccount
from .serializers import ProductSerializer, ContactSerializer, RentalContractSerializer, TransactionSerializer
import datetime

# --- 1. 页面路由 ---
def index_page(request): return render(request, 'index.html')
def entry_page(request): return render(request, 'entry.html')
def sales_page(request): return render(request, 'sales.html')
def contact_page(request): return render(request, 'contact.html')
def inventory_page(request): return render(request, 'inventory.html')
def rental_hub_page(request): return render(request, 'rental_hub.html')
def rental_create_page(request): return render(request, 'rental_create.html')
def profit_page(request): return render(request, 'analysis_profit.html')
def finance_page(request): return render(request, 'analysis_finance.html')
def account_page(request): return render(request, 'analysis_account.html')

# --- 2. 辅助工具 ---
def generate_zencode(initials, category):
    now = timezone.now()
    year = str(now.year)[-2:]
    month_map = {10:'A', 11:'B', 12:'C'}
    month = month_map.get(now.month, str(now.month))
    day = f"{now.day:02d}"
    start = now.replace(hour=0, minute=0, second=0)
    count = Product.objects.filter(created_at__gte=start, category=category).count() + 1
    return f"{year}{month}{day}{initials}{category}{count}"

# --- 3. 核心 API ---

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'zencode', 'note']

    def get_queryset(self):
        status_param = self.request.query_params.get('status')
        if status_param:
            return self.queryset.filter(status=status_param)
        return self.queryset

    # --- 入库逻辑 ---
    def perform_create(self, serializer):
        user = self.request.user
        initials = getattr(user, 'initials', 'AD')
        data = self.request.data
        
        category = serializer.validated_data.get('category', 'ZX')
        if not serializer.validated_data.get('zencode'):
            zencode = generate_zencode(initials, category)
            product = serializer.save(zencode=zencode)
        else:
            product = serializer.save()

        supplier_id = data.get('supplier_id')
        paid_amount = Decimal(str(data.get('paid_amount', 0) or 0))
        account_id = data.get('account_id')
        cost_price = product.cost_price

        if supplier_id and str(supplier_id) != '0':
            try:
                supplier = Contact.objects.get(id=supplier_id)
                if paid_amount > 0 and account_id:
                    acc = CapitalAccount.objects.get(id=account_id)
                    Transaction.objects.create(
                        contact=supplier, product=product, account=acc,
                        amount=paid_amount, type='BUY',
                        operator=user if user.is_authenticated else None,
                        remark=f"采购实付: {product.name}"
                    )
                    acc.current_balance -= paid_amount
                    acc.save()
                
                debt = cost_price - paid_amount
                if debt != 0:
                    supplier.balance -= debt
                    supplier.save()
            except Exception as e:
                print(f"记账异常: {e}")

    # --- 出库逻辑 ---
    @action(detail=True, methods=['post'])
    def sell(self, request, pk=None):
        product = self.get_object()
        price = Decimal(str(request.data.get('price')))
        received_amount = Decimal(str(request.data.get('received_amount', 0) or 0))
        contact_id = request.data.get('contact_id')
        account_id = request.data.get('account_id')
        
        if not contact_id: return Response({'detail': '必须选择客户'}, status=400)
        if product.status != 'IN_STOCK': return Response({'detail': '商品不在库'}, status=400)

        try:
            with transaction.atomic():
                product.status = 'SOLD'
                product.sold_price = price
                product.save()
                
                contact = Contact.objects.get(id=contact_id)
                
                if received_amount > 0 and account_id:
                    acc = CapitalAccount.objects.get(id=account_id)
                    Transaction.objects.create(
                        contact=contact, product=product, account=acc,
                        amount=received_amount, type='SALE',
                        operator=request.user if request.user.is_authenticated else None,
                        remark=f"销售收款: {product.name}"
                    )
                    acc.current_balance += received_amount
                    acc.save()
                
                debt = price - received_amount
                if debt != 0:
                    contact.balance += debt
                    contact.save()
                
                return Response({'msg': '出库成功'})
        except Exception as e:
            return Response({'detail': str(e)}, status=500)

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone', 'address']

class RentalViewSet(viewsets.ModelViewSet):
    queryset = RentalContract.objects.all().order_by('-id')
    serializer_class = RentalContractSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['product__zencode', 'contact__name'] 
    
    @action(detail=False, methods=['post'])
    def create_lease(self, request):
        data = request.data
        try:
            with transaction.atomic():
                product = Product.objects.get(id=data['product_id'])
                contact = Contact.objects.get(id=data['contact_id'])
                deposit = Decimal(str(data.get('deposit', 0)))
                
                if product.status != 'IN_STOCK':
                    return Response({'error': '该商品不在库'}, status=400)

                RentalContract.objects.create(
                    contact=contact, product=product,
                    start_date=data.get('start_date', timezone.now()),
                    rent_strategy=data.get('rent_strategy', 'MONTHLY'),
                    rent_price=Decimal(str(data.get('rent_price', 0))),
                    deposit_amount=deposit,
                    depreciation_monthly=Decimal(str(data.get('depreciation_monthly', 0))),
                    initial_value=product.cost_price or 0
                )

                product.status = 'RENTED'
                product.save()

                if deposit > 0:
                    acc = CapitalAccount.objects.first()
                    if acc:
                        Transaction.objects.create(
                            contact=contact, product=product, account=acc,
                            amount=deposit, type='RENT',
                            remark=f"租赁押金: {product.zencode}"
                        )
                        acc.current_balance += deposit
                        acc.save()
                
                return Response({'msg': '租赁开单成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def settle(self, request, pk=None):
        contract = self.get_object()
        end_value = request.data.get('end_value')
        if not end_value: return Response({'error': '必须填写回库评估价'}, status=400)
        
        try:
            with transaction.atomic():
                product = contract.product
                product.cost_price = Decimal(str(end_value))
                product.status = 'IN_STOCK'
                product.save()
                
                contract.is_active = False
                contract.save()
                
                return Response({'msg': '结算成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class AnalysisViewSet(viewsets.ViewSet):
    
    @action(detail=False)
    def profit(self, request):
        period = request.query_params.get('period', 'all')
        query = Product.objects.filter(status='SOLD')
        
        now = timezone.now()
        if period == 'month':
            query = query.filter(created_at__month=now.month, created_at__year=now.year)
        elif period == 'year':
            query = query.filter(created_at__year=now.year)
            
        total_sales = sum([p.sold_price for p in query if p.sold_price]) or 0
        total_cost = sum([p.cost_price for p in query if p.cost_price]) or 0
        gross_profit = total_sales - total_cost
        
        return Response({
            'total_sales': total_sales,
            'total_cost': total_cost,
            'gross_profit': gross_profit,
            'count': query.count()
        })
        
    @action(detail=False)
    def profit_detail(self, request):
        period = request.query_params.get('period', 'all')
        query = Product.objects.filter(status='SOLD').order_by('-created_at')
        
        now = timezone.now()
        if period == 'month':
            query = query.filter(created_at__month=now.month, created_at__year=now.year)
        elif period == 'year':
            query = query.filter(created_at__year=now.year)
            
        details = []
        sales_sum = 0
        cost_sum = 0
        
        for p in query:
            s = p.sold_price or 0
            c = p.cost_price or 0
            sales_sum += s
            cost_sum += c
            details.append({
                'zencode': p.zencode,
                'name': p.name,
                'date': p.created_at.strftime('%Y-%m-%d'),
                'price': s,
                'profit': s - c
            })
            
        return Response({
            'summary': {
                'sales': sales_sum, 
                'cost': cost_sum, 
                'profit': sales_sum - cost_sum,
                'count': len(details)
            },
            'list': details
        })

    @action(detail=False)
    def accounting(self, request):
        accounts = CapitalAccount.objects.all()
        total_cash = sum([a.current_balance for a in accounts]) or 0
        stock_value = Product.objects.filter(status='IN_STOCK').aggregate(Sum('cost_price'))['cost_price__sum'] or 0
        receivable = Contact.objects.filter(balance__gt=0).aggregate(Sum('balance'))['balance__sum'] or 0
        payable = Contact.objects.filter(balance__lt=0).aggregate(Sum('balance'))['balance__sum'] or 0
        net_worth = total_cash + stock_value + receivable - abs(payable)
        
        return Response({
            'cash': total_cash, 
            'stock': stock_value, 
            'receivable': receivable, 
            'payable': payable, 
            'net_worth': net_worth,
            'accounts': [{'id': a.id, 'name': a.name, 'balance': a.current_balance} for a in accounts]
        })