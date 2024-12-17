# views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Category, Supplier, Product, Order,OrderItem
from .serializers import (
    CategorySerializer, 
    SupplierSerializer, 
    ProductSerializer, 
    OrderSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'category__name', 'supplier__name']

    @action(detail=False, methods=['GET'])
    def low_stock(self, request):
        """Récupérer les produits avec un stock inférieur au stock minimum"""
        low_stock_products = Product.objects.filter(stock__lt=F('min_stock'))
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def update_stock(self, request, pk=None):
        """Mettre à jour le stock d'un produit"""
        product = self.get_object()
        new_stock = request.data.get('stock')
        
        if new_stock is not None:
            product.stock = new_stock
            product.save()
            return Response({
                'status': 'stock updated', 
                'stock': product.stock
            })
        
        return Response(
            {'error': 'Stock value not provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Utilisateurs ne voient que leurs propres commandes"""
        return Order.objects.filter(user=self.request.user)

    @transaction.atomic
    def create(self, request):
        """
        Création d'une commande avec gestion avancée du stock
        """
        try:
            # Validation des données de la commande
            cart_items = request.data.get('items', [])
            
            if not cart_items:
                return Response(
                    {'error': 'Aucun article dans le panier'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Vérification préalable du stock
            stock_errors = []
            for item in cart_items:
                product = Product.objects.get(id=item['product_id'])
                if not product.check_stock_availability(item['quantity']):
                    stock_errors.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'available_stock': product.stock,
                        'requested_quantity': item['quantity']
                    })

            # Si des erreurs de stock sont détectées, retourner les détails
            if stock_errors:
                return Response(
                    {
                        'error': 'Stocks insuffisants',
                        'stock_issues': stock_errors
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calcul du montant total
            total_amount = sum(
                item['quantity'] * item['unit_price'] 
                for item in cart_items
            )

            # Création de la commande
            order = Order.objects.create(
                user=request.user,
                total_amount=total_amount,
                status='pending'
            )

            # Création des items de commande et réduction du stock
            order_items = []
            for item in cart_items:
                product = Product.objects.get(id=item['product_id'])
                
                # Réduire le stock
                product.reduce_stock(item['quantity'])

                # Créer l'item de commande
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item['quantity'],
                    unit_price=item['unit_price']
                )
                order_items.append(order_item)

            # Sérialisation et réponse
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            # Gestion des erreurs de validation (stock insuffisant)
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Product.DoesNotExist:
            return Response(
                {'error': 'Produit non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['POST'])
    def cancel(self, request, pk=None):
        """
        Action personnalisée pour annuler une commande
        """
        order = self.get_object()
        
        # Vérifier si la commande peut être annulée
        if order.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cette commande ne peut pas être annulée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Annuler la commande
        order.cancel_order()
        
        return Response(
            {'message': 'Commande annulée avec succès'},
            status=status.HTTP_200_OK
        )