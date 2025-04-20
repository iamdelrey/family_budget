from uuid import UUID

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import FamilyMember, BudgetCategory, Transaction
from .models import InviteCode, Family, FamilyMembership
from .permissions import IsOwnerOrReadOnly
from .serializers import FamilyMemberSerializer, BudgetCategorySerializer, TransactionSerializer
from .serializers_register import RegisterSerializer
from .serializers_family import CreateFamilySerializer


class FamilyMemberViewSet(viewsets.ModelViewSet):
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer

    def get_queryset(self):
        return FamilyMember.objects.all().order_by('id')


class BudgetCategoryViewSet(viewsets.ModelViewSet):
    queryset = BudgetCategory.objects.all()
    serializer_class = BudgetCategorySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name']

    def get_queryset(self):
        return BudgetCategory.objects.filter(user=self.request.user).order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['amount', 'date', 'category', 'member']
    search_fields = ['description']
    ordering_fields = ['amount', 'date']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RegisterView(APIView):

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description="Tokens successfully created"),
            400: OpenApiResponse(description="Validation error")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
        })

    def patch(self, request):
        user = request.user
        data = request.data
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        user.save()
        return Response({
            "message": "User updated successfully",
            "username": user.username,
            "email": user.email,
        })

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({"message": "User deleted"}, status=status.HTTP_204_NO_CONTENT)


class InviteCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Invite code successfully created"),
            403: OpenApiResponse(description="User is not the head of a family"),
        }
    )
    def post(self, request):
        user = request.user
        try:
            family = Family.objects.get(created_by=user)
        except Family.DoesNotExist:
            return Response({'detail': 'You are not the head of a family'}, status=403)

        invite = InviteCode.objects.create(family=family)
        return Response({'code': str(invite.code)})


class JoinFamilyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'detail': 'Invite code is required'}, status=400)

        try:
            invite = InviteCode.objects.get(code=UUID(code), is_used=False)
        except InviteCode.DoesNotExist:
            return Response({'detail': 'Invalid or used code'}, status=400)

        # Check if user already in family
        if FamilyMembership.objects.filter(user=request.user, family=invite.family).exists():
            return Response({'detail': 'Already a member of this family'}, status=400)

        FamilyMembership.objects.create(
            user=request.user,
            family=invite.family,
            role='member'
        )
        invite.is_used = True
        invite.save()

        return Response({'detail': 'Successfully joined the family!'})


class CreateFamilyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CreateFamilySerializer,
        responses={201: OpenApiResponse(description="Family created")},
    )
    def post(self, request):
        serializer = CreateFamilySerializer(data=request.data, context={'request': request})  # 💥 тут
        if serializer.is_valid():
            family = serializer.save()
            FamilyMembership.objects.create(user=request.user, family=family, role='head')
            return Response({"detail": "Family created", "family_id": family.id}, status=201)
        return Response(serializer.errors, status=400)


class MyFamilyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            membership = FamilyMembership.objects.select_related('family').get(user=request.user)
            family = membership.family
            return Response({
                "id": family.id,
                "name": family.name,
                "created_by": family.created_by.username,
                "role": membership.role,
            })
        except FamilyMembership.DoesNotExist:
            return Response({"detail": "You are not a member of any family"}, status=404)


class CurrentFamilyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = FamilyMembership.objects.filter(user=request.user).select_related('family').first()

        if not membership:
            return Response({'detail': 'User is not part of any family'}, status=404)

        return Response({
            'id': membership.family.id,
            'name': membership.family.name,
            'created_by': membership.family.created_by.username,
            'role': membership.role,
        })
