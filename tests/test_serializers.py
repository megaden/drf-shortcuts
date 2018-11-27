from django.http.request import HttpRequest
from django.test import TestCase, override_settings
from rest_framework.serializers import Serializer, CharField, HyperlinkedIdentityField, HyperlinkedRelatedField
from rest_framework.views import APIView
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.request import Request

from drf_shortcuts.serializers import (
    generate_detail_view_name, rename_serializer_field, get_entity_pk, get_required_field_value,
    get_optional_field_value, OptimizeUrlFieldsSerializer
)


class GenerateDetailViewNameTests(TestCase):
    def test_returns_basic_name_by_default(self):
        self.assertEqual('foo-detail', generate_detail_view_name('foo'))

    @override_settings(API_URL_NAMESPACE='bar')
    def test_returns_prefixed_name_if_set(self):
        self.assertEqual('bar:foo-detail', generate_detail_view_name('foo'))


class RenameSerializerFieldTests(TestCase):
    def test_moves_field_under_new_name(self):
        serializer = Serializer()
        field = CharField()
        serializer.fields['foo'] = field
        rename_serializer_field(serializer, 'foo', 'bar')
        with self.assertRaises(KeyError):
            _ = serializer.fields['foo']
        self.assertEqual(field, serializer.fields['bar'])


class GetEntityPkTests(TestCase):
    def test_throws_for_none_serializer(self):
        with self.assertRaises(AttributeError) as excCtx:
            get_entity_pk(None)
        self.assertTrue('context' in str(excCtx.exception))

    def test_returns_none_if_pk_is_missing(self):
        serializer = Serializer()
        view = APIView()
        view.kwargs = {}
        serializer.context['view'] = view
        self.assertIsNone(get_entity_pk(serializer))

    def test_returns_pk_value_if_present(self):
        serializer = Serializer()
        view = APIView()
        view.kwargs = {'pk': 'foo'}
        serializer.context['view'] = view
        self.assertEqual('foo', get_entity_pk(serializer))


class ModelStub:
    foo = None

    def __init__(self, value=None):
        self.foo = value


class GetRequiredFieldValueTests(TestCase):
    def test_returns_value_from_data_if_present(self):
        self.assertEqual(1, get_required_field_value({'foo': 1}, 'foo', None, None))

    def test_throws_if_pk_not_available(self):
        with self.assertRaises(AssertionError) as excCtx:
            get_required_field_value({}, 'foo', None, None)
        self.assertTrue('update is assumed' in str(excCtx.exception))

    def test_throws_if_required_field_value_is_missing(self):
        with self.assertRaises(AssertionError) as excCtx:
            get_required_field_value({}, 'foo', 'bar', lambda x: ModelStub() if x == 'bar' else None)
        self.assertTrue('required field value' in str(excCtx.exception))

    def test_returns_value_from_model_if_available(self):
        value = get_required_field_value({}, 'foo', 'bar', lambda x: ModelStub('baz') if x == 'bar' else None)
        self.assertEqual('baz', value)


class GetOptionalFieldValueTests(TestCase):
    def test_returns_value_from_data_if_present(self):
        self.assertEqual(1, get_optional_field_value({'foo': 1}, 'foo', None, None))

    def test_returns_none_if_pk_not_available(self):
        self.assertIsNone(get_optional_field_value({}, 'foo', None, None))

    def test_returns_value_from_model_if_available(self):
        value = get_optional_field_value({}, 'foo', 'bar', lambda x: ModelStub('baz') if x == 'bar' else None)
        self.assertEqual('baz', value)


class SerializerWithUrlFields(OptimizeUrlFieldsSerializer):
    id_field = HyperlinkedIdentityField('foo')
    related_field = HyperlinkedRelatedField('foo', read_only=True)
    regular_field = CharField()


class OptimizeUrlFieldsSerializerTests(TestCase):
    def test_removes_url_fields_by_default(self):
        serializer = SerializerWithUrlFields()
        self.assertEqual(1, len(serializer.fields))

    def test_keeps_url_fields_if_query_param_is_set_to_true(self):
        django_request = HttpRequest()
        django_request.GET['forceUrls'] = 'true'
        serializer = SerializerWithUrlFields(context={'request': Request(django_request)})
        self.assertEqual(3, len(serializer.fields))

    def test_removes_url_fields_if_query_param_is_set_to_false(self):
        django_request = HttpRequest()
        django_request.GET['forceUrls'] = 'false'
        serializer = SerializerWithUrlFields(context={'request': Request(django_request)})
        self.assertEqual(1, len(serializer.fields))

    def test_keeps_url_fields_if_accepted_renderer_is_browsable_api(self):
        drf_request = Request(HttpRequest())
        drf_request.accepted_renderer = BrowsableAPIRenderer()
        serializer = SerializerWithUrlFields(context={'request': drf_request})
        self.assertEqual(3, len(serializer.fields))

    def test_removes_url_fields_if_accepted_renderer_is_not_browsable_api(self):
        drf_request = Request(HttpRequest())
        drf_request.accepted_renderer = JSONRenderer()
        serializer = SerializerWithUrlFields(context={'request': drf_request})
        self.assertEqual(1, len(serializer.fields))

    def test_removes_field_specified_explicitly(self):
        class SerializerWithExplicitFields(SerializerWithUrlFields):
            explicit_url_field_names = ['regular_field']

        serializer = SerializerWithExplicitFields()
        self.assertEqual(0, len(serializer.fields))
