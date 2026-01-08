from rest_framework import serializers
from .models import Product, Contact, RentalContract, CustomUser, Transaction

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'role', 'initials']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    display_status = serializers.CharField(source='get_status_display', read_only=True)
    class Meta:
        model = Product
        fields = '__all__'

class RentalContractSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    class Meta:
        model = RentalContract
        fields = '__all__'

# [Day 3 新增] 交易流水序列化
class TransactionSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    operator_name = serializers.CharField(source='operator.initials', read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'