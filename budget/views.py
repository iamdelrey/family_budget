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
from rest_framework import serializers
from .models import FamilyMembership


class FamilyMemberViewSet(viewsets.ModelViewSet):
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer

    def get_queryset(self):
        return FamilyMember.objects.all().order_by('id')


class FamilyMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = FamilyMembership.objects.filter(user=request.user).select_related('family').first()
        if not membership:
            return Response({'detail': 'User is not part of any family'}, status=404)

        members = FamilyMembership.objects.filter(family=membership.family).select_related('user')
        serializer = FamilyMemberDetailSerializer(members, many=True)
        return Response(serializer.data)


class FamilyMemberDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = FamilyMembership
        fields = ['id', 'username', 'email', 'role']


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
        membership = FamilyMembership.objects.filter(
            user=request.user,
            role='owner'
        ).select_related('family').first()

        if not membership:
            return Response(
                {'detail': 'Только владелец (owner) семьи может генерировать приглашения'},
                status=status.HTTP_403_FORBIDDEN
            )

        family = membership.family

        invite = InviteCode.objects.create(family=family)
        return Response({'code': str(invite.code)}, status=status.HTTP_201_CREATED)


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
        serializer = CreateFamilySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            family = serializer.save()
            FamilyMembership.objects.create(user=request.user, family=family, role='owner')
            return Response({"detail": "Family created", "family_id": family.id}, status=201)
        return Response(serializer.errors, status=400)


class CurrentFamilyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiResponse(description="Current family info")},
    )
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

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': 'New family name'},
                },
                'required': ['name'],
            }
        },
        responses={200: OpenApiResponse(description="Family renamed")},
    )
    def patch(self, request):
        membership = FamilyMembership.objects.filter(user=request.user).select_related('family').first()
        if not membership:
            return Response({'detail': 'User is not part of any family'}, status=404)

        if membership.role != 'owner':
            return Response({'detail': 'Only the head can update family'}, status=403)

        new_name = request.data.get('name')
        if not new_name:
            return Response({'detail': 'New name is required'}, status=400)

        membership.family.name = new_name
        membership.family.save()
        return Response({'detail': 'Family updated', 'name': new_name})


class RemoveFamilyMemberView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'integer', 'description': 'ID of user to remove'},
                },
                'required': ['user_id'],
            }
        },
        responses={
            200: OpenApiResponse(description="Member removed"),
            403: OpenApiResponse(description="Not allowed"),
            404: OpenApiResponse(description="User not found or not in family"),
        }
    )
    def post(self, request):
        current_user = request.user
        user_id = request.data.get('user_id')

        if user_id is None:
            return Response({'detail': 'user_id is required'}, status=400)

        try:
            current_membership = FamilyMembership.objects.get(user=current_user)
        except FamilyMembership.DoesNotExist:
            return Response({'detail': 'You are not part of any family'}, status=404)

        if current_membership.role != 'owner':
            return Response({'detail': 'Only head of family can remove members'}, status=403)

        if user_id == current_user.id:
            return Response({'detail': 'You cannot remove yourself'}, status=400)

        try:
            membership_to_remove = FamilyMembership.objects.get(
                pk=user_id,
                family=current_membership.family
            )
        except FamilyMembership.DoesNotExist:
            return Response({'detail': 'User not found in your family'}, status=404)

        membership_to_remove.delete()
        return Response({'detail': 'Member removed successfully'})


class ChangeFamilyMemberRoleView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'integer', 'description': 'ID of user to update'},
                    'new_role': {'type': 'string', 'enum': ['member', 'owner']},
                },
                'required': ['user_id', 'new_role'],
            }
        },
        responses={
            200: OpenApiResponse(description="Role updated"),
            403: OpenApiResponse(description="Not allowed"),
            404: OpenApiResponse(description="User not found or not in family"),
        }
    )
    def post(self, request):
        current_user = request.user
        user_id = request.data.get('user_id')
        new_role = request.data.get('new_role')

        if not user_id or not new_role:
            return Response({'detail': 'user_id and new_role are required'}, status=400)

        if new_role not in ['member', 'owner']:
            return Response({'detail': 'Invalid role'}, status=400)

        try:
            current_membership = FamilyMembership.objects.get(user=current_user)
        except FamilyMembership.DoesNotExist:
            return Response({'detail': 'You are not part of any family'}, status=404)

        if current_membership.role != 'owner':
            return Response({'detail': 'Only the head can change roles'}, status=403)

        if user_id == current_user.id:
            return Response({'detail': 'You cannot change your own role'}, status=400)

        try:
            target_membership = FamilyMembership.objects.get(
                pk=user_id,
                family=current_membership.family
            )
        except FamilyMembership.DoesNotExist:
            return Response({'detail': 'User not found in your family'}, status=404)

        if new_role == 'owner':
            current_membership.role = 'member'
            current_membership.save()

        target_membership.role = new_role
        target_membership.save()
        return Response({'detail': 'Role updated'})


class LeaveFamilyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Left the family successfully"),
            403: OpenApiResponse(description="Head cannot leave without assigning new head"),
            404: OpenApiResponse(description="User not in family"),
        }
    )
    def post(self, request):
        user = request.user

        membership = FamilyMembership.objects.filter(user=user).first()
        if not membership:
            return Response({'detail': 'You are not in any family'}, status=404)

        if membership.role == 'owner':
            return Response({'detail': 'Head of family cannot leave. Assign new head first.'}, status=403)

        membership.delete()
        return Response({'detail': 'You have left the family'}, status=200)


class DeleteFamilyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Family deleted"),
            403: OpenApiResponse(description="Only head can delete the family"),
            404: OpenApiResponse(description="User not in a family"),
        }
    )
    def delete(self, request):
        user = request.user

        membership = FamilyMembership.objects.filter(user=user).select_related('family').first()
        if not membership:
            return Response({'detail': 'You are not in any family'}, status=404)

        if membership.role != 'owner':
            return Response({'detail': 'Only the head can delete the family'}, status=403)

        membership.family.delete()
        return Response({'detail': 'Family deleted'}, status=200)


class AssignHeadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'integer', 'description': 'ID нового главы семьи'},
                },
                'required': ['user_id'],
            }
        },
        responses={
            200: OpenApiResponse(description="New head assigned"),
            403: OpenApiResponse(description="Only head can assign a new head"),
            404: OpenApiResponse(description="User or membership not found"),
        }
    )
    def post(self, request):
        current_user = request.user
        new_head_id = request.data.get('user_id')

        current_membership = FamilyMembership.objects.filter(user=current_user).select_related('family').first()
        if not current_membership or current_membership.role != 'owner':
            return Response({'detail': 'Only the head can assign a new head'}, status=403)

        try:
            new_head_membership = FamilyMembership.objects.get(user_id=new_head_id, family=current_membership.family)
        except FamilyMembership.DoesNotExist:
            return Response({'detail': 'User not found in your family'}, status=404)

        current_membership.role = 'member'
        current_membership.save()

        new_head_membership.role = 'owner'
        new_head_membership.save()

        return Response({'detail': f'User {new_head_membership.user.username} is now the head'})
