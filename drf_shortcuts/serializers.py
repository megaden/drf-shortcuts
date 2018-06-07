from rest_framework import serializers
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.fields import empty
from django.conf import settings
import re
from inflection import dasherize, underscore


def generate_serializer_base_name(model_cls):
    return dasherize(underscore(model_cls.__name__))


def generate_detail_view_name(base_name):
    default_detail_name = base_name + "-detail"
    if settings.API_URL_NAMESPACE:
        return "{}:{}".format(settings.API_URL_NAMESPACE, default_detail_name)
    return default_detail_name


def rename_serializer_field(serializer, source_name, target_name, display_name=None):
    field = serializer.fields.pop(source_name)
    if display_name is not None:
        field.label = display_name
    serializer.fields[target_name] = field


def get_entity_pk(serializer):
    view_kwargs = serializer.context['view'].kwargs if 'view' in serializer.context else {}
    return view_kwargs.get('pk') if 'pk' in view_kwargs else None


def get_required_field_value(data, field_name, serializer, fetch_model):
    if field_name in data:
        return data.get(field_name)
    pk = get_entity_pk(serializer)
    assert pk is not None, "Update or partial update is assumed"
    field_value = getattr(fetch_model(pk), field_name)
    assert field_value is not None, "Unexpectedly required field value is None"
    return field_value


def get_optional_field_value(data, field_name, serializer, fetch_model):
    if field_name in data:
        return data.get(field_name)
    pk = get_entity_pk(serializer)
    return None if pk is None else getattr(fetch_model(pk), field_name)


class OptimizeUrlFieldsSerializer(serializers.ModelSerializer):
    explicit_url_field_names = []

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        remove_urls = True
        if 'request' in self.context:
            query_params = self.context['request'].query_params
            if 'forceUrls' in query_params:
                remove_urls = query_params.get('forceUrls') == 'false'
            else:
                remove_urls = not isinstance(self.context['request'].accepted_renderer, BrowsableAPIRenderer)
        if remove_urls:
            field_names_to_remove = []
            for field_name in self.fields.keys():
                is_id_field = isinstance(self.fields[field_name], serializers.HyperlinkedIdentityField)
                is_related_field = isinstance(self.fields[field_name], serializers.HyperlinkedRelatedField)
                is_explicit_field = field_name in self.explicit_url_field_names
                if is_id_field or is_related_field or is_explicit_field:
                    field_names_to_remove.append(field_name)
            for field_name in field_names_to_remove:
                del self.fields[field_name]


class ValidateAndInsertAuthorSerializer(serializers.ModelSerializer):
    author_field_name = None

    _author_inserted = False

    def validate(self, data):
        author = self._get_author(data)
        if author is not None and not self._author_inserted:
            user = self.context['request'].user
            if user != author:
                raise serializers.ValidationError('Authoring for another user is not allowed')
        return data

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        if self.context is not None and 'request' in self.context and self.context['request'].method == 'POST':
            author = self._get_author(result)
            if author is None and self.context.get('request') is not None:
                user = self.context['request'].user
                if self.author_field_name:
                    result[self.author_field_name] = user
                else:
                    self.set_author_core(result, user)
                self._author_inserted = True
        return result

    def _get_author(self, data):
        if self.author_field_name:
            return data.get(self.author_field_name)
        else:
            return self.get_author_core(data)

    def get_author_core(self, data):
        raise NotImplementedError("This should be implemented")

    def set_author_core(self, data, author):
        raise NotImplementedError("This should be implemented")


class UpdateEditorSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        in_request_context = self.context is not None and 'request' in self.context
        request = self.context['request'] if in_request_context else None
        if in_request_context and request.method in ('PUT', 'PATCH') and request.user:
            self.set_editor_core(result, request.user)
        return result

    def set_editor_core(self, data, editor):
        raise NotImplementedError("This should be implemented")


class JsFriendlyFieldsRenamingSerializer(serializers.ModelSerializer):
    regex = re.compile('_(.)')

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        for field_name in [f for f in self.fields if '_' in f]:
            rename_serializer_field(self, field_name, self.regex.sub(self._process_match, field_name))

    @staticmethod
    def _process_match(match):
        return match.group(1).upper()


def create_standard_serializer_class(model_cls):
    base_name = generate_serializer_base_name(model_cls)

    class Serializer(OptimizeUrlFieldsSerializer, JsFriendlyFieldsRenamingSerializer):
        DEFAULT_BASE_NAME = base_name

        url = serializers.HyperlinkedIdentityField(view_name=generate_detail_view_name(DEFAULT_BASE_NAME))

        class Meta:
            model = model_cls
            fields = '__all__'

    Serializer.__name__ = model_cls.__name__ + 'Serializer'
    return Serializer
