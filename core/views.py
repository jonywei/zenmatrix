from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import render, redirect
from django.db import transaction
from django.db.models import Sum, Q, Count
from decimal import Decimal
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import datetime
from datetime import timedelta

from .models import Product, Contact, RentalContract, Transaction, CapitalAccount, CustomUser
from .serializers import ProductSerializer, ContactSerializer, RentalContractSerializer, TransactionSerializer

# --- 1. 页面路由 ---
def index_page(request): 
    if not request.user.is_authenticated: return redirect('/login/')
    return render(request, 'index.html')
def entry_page(request): return render(request, 'entry.html') if request.user.is_authenticated else redirect('/login/')
def sales_page(request): return render(request, 'sales.html') if request.user.is_authenticated else redirect('/login/')
def contact_page(request): return render(request, 'contact.html') if request.user.is_authenticated else redirect('/login/')
def inventory_page(request): return render(request, 'inventory.html') if request.user.is_authenticated else redirect('/login/')
def rental_hub_page(request): return render(request, 'rental_hub.html') if request.user.is_authenticated else redirect('/login/')
def rental_create_page(request): return render(request, 'rental_create.html') if request.user.is_authenticated else redirect('/login/')
def profit_page(request): return render(request, 'analysis_profit.html') if request.user.is_authenticated else redirect('/login/')
def finance_page(request): return render(request, 'analysis_finance.html') if request.user.is_authenticated else redirect('/login/')
def account_page(request): return render(request, 'analysis_account.html') if request.user.is_authenticated else redirect('/login/')
def profile_page(request): return render(request, 'profile.html') if request.user.is_authenticated else redirect('/login/')
def login_page(request): return redirect('/') if request.user.is_authenticated else render(request, 'login.html')

# --- 2. 认证 API ---
@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        try: data = json.loads(request.body)
        except: data = request.POST
        user = authenticate(username=data.get('username'), password=data.get('password'))
        if user:
            login(request, user)
            return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'error', 'msg': '账号或密码错误'})
    return JsonResponse({'status': 'error', 'msg': 'Method not allowed'})

def api_logout(request):
    logout(request)
    return JsonResponse({'status': 'ok'})

@csrf_exempt
def api_change_password(request):
    if not request.user.is_authenticated: return JsonResponse({'status': 'error'}, status=403)
    try:
        data = json.loads(request.body)
        request.user.set_password(data.get('password'))
        request.user.save()
        logout(request)
        return JsonResponse({'status': 'ok'})
    except: return JsonResponse({'status': 'error'})

# --- 3. 业务 API ---

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'zencode', 'note']

    def get_queryset(self):
        status = self.request.query_params.get('status')
        if status: return self.queryset.filter(status=status)
        return self.queryset

    def perform_create(self, serializer):
        user = self.request.user
        initials = getattr(user, 'initials', 'AD')
        category = self.request.data.get('category', 'ZX')
        year = str(timezone.now().year)[-2:]
        month_map = {10:'A',11:'B',12:'C'}
        month = month_map.get(timezone.now().month, str(timezone.now().month))
        day = f"{timezone.now().day:02d}"
        start = timezone.now().replace(hour=0, minute=0, second=0)
        count = Product.objects.filter(created_at__gte=start, category=category).count() + 1
        zencode = f"{year}{month}{day}{initials}{category}{count}"
        product = serializer.save(zencode=zencode)

        supplier_id = self.request.data.get('supplier_id')
        paid_amount = Decimal(str(self.request.data.get('paid_amount', 0) or 0))
        account_id = self.request.data.get('account_id')
        
        if supplier_id and str(supplier_id) != '0':
            try:
                supplier = Contact.objects.get(id=supplier_id)
                if account_id:
                    acc = CapitalAccount.objects.get(id=account_id)
                    Transaction.objects.create(contact=supplier, product=product, account=acc, amount=paid_amount, type='BUY', operator=user, remark=f"采购: {product.name}")
                    if paid_amount > 0:
                        acc.current_balance -= paid_amount
                        acc.save()
                
                debt = product.cost_price - paid_amount
                if debt != 0:
                    supplier.balance -= debt
                    supplier.save()
            except Exception: pass

    @action(detail=True, methods=['post'])
    def sell(self, request, pk=None):
        product = self.get_object()
        price = Decimal(str(request.data.get('price')))
        received_amount = Decimal(str(request.data.get('received_amount', 0) or 0))
        contact_id = request.data.get('contact_id')
        account_id = request.data.get('account_id')
        if product.status != 'IN_STOCK': return Response({'detail': '非在库商品'}, status=400)
        try:
            with transaction.atomic():
                product.status = 'SOLD'
                product.sold_price = price
                product.save()
                contact = Contact.objects.get(id=contact_id)
                
                if account_id:
                    acc = CapitalAccount.objects.get(id=account_id)
                    Transaction.objects.create(contact=contact, product=product, account=acc, amount=received_amount, type='SALE', operator=request.user, remark=f"销售: {product.name}")
                    if received_amount > 0:
                        acc.current_balance += received_amount
                        acc.save()
                else:
                    Transaction.objects.create(contact=contact, product=product, amount=0, type='SALE', operator=request.user, remark=f"销售(挂账): {product.name}")

                debt = price - received_amount
                if debt != 0:
                    contact.balance += debt
                    contact.save()
                return Response({'msg': '出库成功'})
        except Exception as e: return Response({'detail': str(e)}, status=500)

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone']

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        contact = self.get_object()
        txs = Transaction.objects.filter(contact=contact).order_by('-created_at')
        data = [{'id':t.id, 'date':t.created_at.strftime('%Y-%m-%d'), 'type':t.get_type_display(), 'amount':t.amount, 'product':t.product.name if t.product else '-', 'remark':t.remark, 'operator':t.operator.initials if t.operator else ''} for t in txs]
        return Response(data)

    @action(detail=True, methods=['post'])
    def repay(self, request, pk=None):
        contact = self.get_object()
        amount = Decimal(str(request.data.get('amount') or 0))
        acc_id = request.data.get('account_id')
        action = request.data.get('action_type')
        if amount <= 0 or not acc_id: return Response({'error': '参数错误'}, 400)
        try:
            with transaction.atomic():
                acc = CapitalAccount.objects.get(id=acc_id)
                if action == 'in':
                    Transaction.objects.create(contact=contact, account=acc, amount=amount, type='OTHER', operator=request.user, remark='收款核销')
                    acc.current_balance += amount
                    contact.balance -= amount
                else:
                    Transaction.objects.create(contact=contact, account=acc, amount=amount, type='BUY', operator=request.user, remark='付款核销')
                    acc.current_balance -= amount
                    contact.balance += amount
                acc.save()
                contact.save()
                return Response({'msg': 'ok'})
        except Exception as e: return Response({'error': str(e)}, 500)

class RentalViewSet(viewsets.ModelViewSet):
    queryset = RentalContract.objects.all().order_by('-id')
    serializer_class = RentalContractSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active == 'true':
            return queryset.filter(is_active=True)
        elif is_active == 'false':
            return queryset.filter(is_active=False)
        return queryset
    
    @action(detail=False, methods=['post'])
    def create_lease(self, request):
        data = request.data
        try:
            with transaction.atomic():
                product = Product.objects.get(id=data['product_id'])
                contact = Contact.objects.get(id=data['contact_id'])
                deposit = Decimal(str(data.get('deposit', 0)))
                start_date = data.get('start_date', timezone.now())
                duration = data.get('duration', '1')
                
                RentalContract.objects.create(
                    contact=contact, product=product, 
                    start_date=start_date, duration=duration,
                    rent_strategy=data.get('rent_strategy', 'MONTHLY'), 
                    rent_price=Decimal(str(data.get('rent_price', 0))), 
                    deposit_amount=deposit, 
                    depreciation_monthly=Decimal(str(data.get('depreciation_monthly', 0))), 
                    initial_value=product.cost_price or 0
                )
                product.status = 'RENTED'
                product.save()
                
                acc = CapitalAccount.objects.first()
                remark_txt = f"租赁开单: {product.zencode}"
                if deposit > 0:
                    remark_txt += f" (押金¥{deposit})"
                
                Transaction.objects.create(
                    contact=contact, 
                    product=product, 
                    account=acc, 
                    amount=deposit, 
                    type='RENT', 
                    operator=request.user, 
                    remark=remark_txt
                )
                
                if deposit > 0 and acc:
                    acc.current_balance += deposit
                    acc.save()
                    
                return Response({'msg': '租赁开单成功'})
        except Exception as e: return Response({'error': str(e)}, 500)

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
                Transaction.objects.create(contact=contract.contact, product=product, amount=0, type='OTHER', operator=request.user, remark=f"租赁归还: {product.zencode}")
                return Response({'msg': '结算成功'})
        except Exception as e: return Response({'error': str(e)}, 500)

class AnalysisViewSet(viewsets.ViewSet):
    
    @action(detail=False)
    def dashboard(self, request):
        today = timezone.localtime(timezone.now()).date()
        
        stock_val = Product.objects.filter(status='IN_STOCK').aggregate(Sum('cost_price'))['cost_price__sum'] or 0
        stock_count = Product.objects.filter(status='IN_STOCK').count()
        today_entry = Product.objects.filter(created_at__date=today).count()
        today_sale = Transaction.objects.filter(
            Q(type='SALE') | Q(type='RENT'), 
            created_at__date=today
        ).count()
        
        total_sales_amount = Transaction.objects.filter(Q(type='SALE') | Q(type='RENT')).aggregate(Sum('amount'))['amount__sum'] or 0

        # 图表数据：近7天
        days = []
        sales_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_sum = Transaction.objects.filter(
                Q(type='SALE') | Q(type='RENT'), 
                created_at__date=day
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            days.append(day.strftime('%m-%d'))
            sales_data.append(float(day_sum))

        # 图表数据：分类占比
        cat_map = {'ZJ': '整机', 'SJ': '配件', 'XS': '显示器', 'ZX': '杂项'}
        category_stats = Product.objects.filter(status='SOLD').values('category').annotate(total=Count('id'))
        pie_labels = []
        pie_data = []
        for item in category_stats:
            label = cat_map.get(item['category'], item['category'])
            pie_labels.append(label)
            pie_data.append(item['total'])

        receivable = Contact.objects.filter(balance__gt=0).aggregate(Sum('balance'))['balance__sum'] or 0
        payable = Contact.objects.filter(balance__lt=0).aggregate(Sum('balance'))['balance__sum'] or 0
        total_cash = CapitalAccount.objects.aggregate(Sum('current_balance'))['current_balance__sum'] or 0

        recent_txs = Transaction.objects.all().select_related('product').order_by('-created_at')[:8]
        recent_list = []
        for t in recent_txs:
            is_income = t.type in ['SALE', 'RENT', 'OTHER'] and t.amount > 0
            product_name = t.product.name if t.product else (t.remark or '-')
            desc = f"{t.get_type_display()} - {product_name}"
            recent_list.append({
                'id': t.id, 'desc': desc, 'change_message': desc, 'action_flag': t.type,
                'action_type': t.get_type_display(),
                'amount': t.amount, 'is_income': is_income, 'time': timezone.localtime(t.created_at).strftime('%m-%d %H:%M')
            })

        return Response({
            'stock_value': stock_val, 'stock_count': stock_count,
            'today_entry': today_entry, 'today_sale': today_sale, 'today_sale_count': today_sale,
            'cards': {
                'stock_val': stock_val,
                'total_sales_amount': total_sales_amount,
                'receivable': receivable,
                'payable': abs(payable),
                'cash': total_cash
            },
            'charts': {
                'trend': {'labels': days, 'data': sales_data},
                'category': {'labels': pie_labels, 'data': pie_data}
            },
            'recent_list': recent_list
        })

    @action(detail=False)
    def profit_dashboard(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        staff_id = request.query_params.get('staff_id')

        query = Product.objects.filter(status='SOLD').order_by('-created_at')
        if start_date and end_date:
            query = query.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
        
        if staff_id:
            p_ids = Transaction.objects.filter(operator_id=staff_id, type='SALE').values_list('product_id', flat=True)
            query = query.filter(id__in=p_ids)

        details = []
        sales_sum = 0
        cost_sum = 0
        for p in query:
            s = p.sold_price or 0
            c = p.cost_price or 0
            profit = s - c
            sales_sum += s
            cost_sum += c
            
            sale_tx = Transaction.objects.filter(product=p, type='SALE').last()
            staff_name = '-'
            customer_name = '-'
            if sale_tx:
                if sale_tx.operator:
                    staff_name = f"{sale_tx.operator.last_name}{sale_tx.operator.first_name}".strip() or sale_tx.operator.username
                if sale_tx.contact:
                    customer_name = sale_tx.contact.name

            details.append({
                'id': p.id, 'date': p.created_at.strftime('%Y-%m-%d'), 'zencode': p.zencode, 
                'product_name': p.name, 'customer': customer_name, 'staff': staff_name, 
                'sales': s, 'cost': c, 'profit': profit
            })
        
        raw_users = CustomUser.objects.values('id', 'username', 'last_name', 'first_name')
        staff_list = []
        for u in raw_users:
            real_name = f"{u['last_name']}{u['first_name']}".strip()
            staff_list.append({'id': u['id'], 'name': real_name if real_name else u['username']})
        
        return Response({
            'summary': {'sales': sales_sum, 'cost': cost_sum, 'profit': sales_sum - cost_sum, 'count': len(details)}, 
            'list': details, 'options': {'staff': staff_list}
        })

    @action(detail=False)
    def accounting(self, request):
        accounts = CapitalAccount.objects.all()
        total_cash = sum([a.current_balance for a in accounts]) or 0
        stock_value = Product.objects.filter(status='IN_STOCK').aggregate(Sum('cost_price'))['cost_price__sum'] or 0
        receivable = Contact.objects.filter(balance__gt=0).aggregate(Sum('balance'))['balance__sum'] or 0
        payable = Contact.objects.filter(balance__lt=0).aggregate(Sum('balance'))['balance__sum'] or 0
        net_worth = total_cash + stock_value + receivable + payable 
        return Response({
            'cash': total_cash, 'stock': stock_value, 'receivable': receivable, 'payable': payable, 'net_worth': net_worth,
            'accounts': [{'id': a.id, 'name': a.name, 'balance': a.current_balance} for a in accounts]
        })
    
    @action(detail=False)
    def account_history(self, request):
        acc_id = request.query_params.get('id')
        txs = Transaction.objects.filter(account_id=acc_id).order_by('-created_at')
        data = []
        for t in txs:
            sign = '+' if t.type in ['SALE', 'RENT', 'OTHER'] else '-'
            color = 'text-red-500' if sign == '+' else 'text-green-500'
            target = t.contact.name if t.contact else (t.product.name if t.product else '-')
            data.append({'id':t.id, 'date':t.created_at.strftime('%Y-%m-%d'), 'type':t.get_type_display(), 'amount':t.amount, 'sign':sign, 'color':color, 'target':target, 'remark':t.remark})
        return Response(data)