from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import User
from .permissions import IsAdmin
from .serializers import UserPublicSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserPublicSerializer
        return UserSerializer
