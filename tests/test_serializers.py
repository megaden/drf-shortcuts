from django.test import TestCase

from drf_shortcuts.serializers import get_entity_pk


class GetEntityPkTests(TestCase):
    def test_throws_for_none_serializer(self):
        with self.assertRaises(AttributeError) as excCtx:
            get_entity_pk(None)
        self.assertTrue('context' in str(excCtx.exception))
