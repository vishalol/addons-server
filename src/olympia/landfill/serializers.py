from rest_framework import serializers

from olympia.addons.models import AddonUser
from olympia.amo.tests import user_factory, addon_factory


class GenerateAddonsSerializer(serializers.Serializer):
    count = serializers.IntegerField(default=10)

    def create(self):
        for _ in range(self.validated_data['count']):
            AddonUser.objects.create(
                user=user_factory(),
                addon=addon_factory())
