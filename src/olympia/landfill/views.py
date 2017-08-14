import os
import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from waffle.decorators import waffle_switch
from django.core.management import call_command
from django.core.cache import cache
from django.db import connection
from django.test.testcases import TransactionTestCase

from olympia import amo
from olympia.api.authentication import JWTKeyAuthentication
from olympia.api.permissions import GroupPermission

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

        cache.clear()

        return Response({}, status=201)


class DumpCurrentState(APIView):
    authentication_classes = [JWTKeyAuthentication]
    permission_classes = [
        IsAuthenticated,
        GroupPermission(amo.permissions.ACCOUNTS_SUPER_CREATE)]

    @waffle_switch('uitests-enable-landfill')
    def post(self, request):
        state = datetime.datetime.utcnow().isoformat()
        fname = '/tmp/{}.json'.format(state)
        with open(fname, 'wb') as fobj:
            fobj.write(connection.creation.serialize_db_to_string())

        return Response({'state': state}, status=200)


class RestoreCurrentState(APIView):
    authentication_classes = [JWTKeyAuthentication]
    permission_classes = [
        IsAuthenticated,
        GroupPermission(amo.permissions.ACCOUNTS_SUPER_CREATE)]

    @waffle_switch('uitests-enable-landfill')
    def post(self, request):
        state = request.data.get('state')

        fname = '/tmp/{}.json'.format(state)
        if os.path.exists('/tmp/{}.json'.format(state)):
            with open(fname, 'rb') as fobj:
                data = fobj.read()

        print('Found data to restore')

        print('Truncate...')
        # Truncate the whole database

        databases = TransactionTestCase._databases_names(include_mirrors=False)
        for db_name in databases:
            # Flush the database
            call_command('flush', verbosity=0, interactive=False,
                         database=db_name, reset_sequences=False,
                         allow_cascade=False,
                         inhibit_post_migrate=False)

        print('Restore...')
        # Restore database to previously known state
        connection.creation.deserialize_db_from_string(data)

        return Response({}, status=200)
