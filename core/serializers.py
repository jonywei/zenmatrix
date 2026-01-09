from rest_framework import serializers
from .models import Product, Contact, RentalContract, Transaction, CapitalAccount

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

class RentalContractSerializer(serializers.ModelSerializer):
    # 增加关联字段显示，方便前端取名字
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_zencode = serializers.CharField(source='product.zencode', read_only=True)
    
    class Meta:
        model = RentalContract
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class CapitalAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapitalAccount
        fields = '__all__'