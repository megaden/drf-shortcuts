from django.test import TestCase
from rest_framework.serializers import ModelSerializer
from rest_framework.views import APIView

from drf_shortcuts.serializers import get_entity_pk


class GetEntityPkTests(TestCase):
    def test_throws_for_none_serializer(self):
        with self.assertRaises(AttributeError) as excCtx:
            get_entity_pk(None)
        self.assertTrue('context' in str(excCtx.exception))

    def test_returns_none_if_pk_is_missing(self):
        serializer = ModelSerializer()
        view = APIView()
        view.kwargs = {}
        serializer.context['view'] = view
        self.assertIsNone(get_entity_pk(serializer))

    def test_returns_pk_value_if_present(self):
        serializer = ModelSerializer()
        view = APIView()
        view.kwargs = {'pk': 'foo'}
        serializer.context['view'] = view
        self.assertEqual('foo', get_entity_pk(serializer))
