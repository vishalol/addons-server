from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from waffle.decorators import waffle_switch
from django.core.management import call_command

from olympia import amo
from olympia.api.authentication import JWTKeyAuthentication
from olympia.api.permissions import GroupPermission
from olympia.addons.models import Addon, AddonUser
from olympia.users.models import UserProfile
from olympia.activity.models import ActivityLog

from .serializers import GenerateAddonsSerializer


class GenerateAddons(APIView):
    authentication_classes = [JWTKeyAuthentication]
    permission_classes = [
        IsAuthenticated,
        GroupPermission(amo.permissions.ACCOUNTS_SUPER_CREATE)]

    @waffle_switch('uitests-enable-landfill')
    def post(self, request):
        serializer = GenerateAddonsSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=422)

        serializer.create()

        return Response({}, status=201)


class Cleanup(APIView):
    authentication_classes = [JWTKeyAuthentication]
    permission_classes = [
        IsAuthenticated,
        GroupPermission(amo.permissions.ACCOUNTS_SUPER_CREATE)]

    @waffle_switch('uitests-enable-landfill')
    def post(self, request):
        # TODO: Make this configurable about what needs to be cleaned up.

        ActivityLog.objects.all().delete()
        Addon.objects.all().delete()
        AddonUser.objects.all().delete()
        UserProfile.objects.exclude(username='uitest').delete()

        return Response({}, status=200)
