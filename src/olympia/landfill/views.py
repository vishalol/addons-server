from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from waffle.decorators import waffle_switch

from olympia import amo
from olympia.amo.tests import user_factory, addon_factory
from olympia.api.authentication import JWTKeyAuthentication
from olympia.api.permissions import GroupPermission
from olympia.addons.models import AddonUser


class AddonUserCreate(APIView):
    authentication_classes = [JWTKeyAuthentication]
    permission_classes = [
        IsAuthenticated,
        GroupPermission(amo.permissions.ACCOUNTS_SUPER_CREATE)]

    @waffle_switch('super-create-accounts')
    def post(self, request):
        count = request.data.get('count', 1)

        for idx in range(count):
            AddonUser.objects.create(user=user_factory(), addon=addon_factory())

        return Response(status=201)
