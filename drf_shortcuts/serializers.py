# -*- coding: utf-8 -*-
"""serializers module of DRF (Django REST Framework) shortcuts package.

Functions:

- #generate_detail_view_name: Generates detail view name for a viewset which DRF uses to expose it.

- #generate_serializer_base_name: Generates base name to be used in viewset routing via DRF router further on.

- #get_entity_pk: Gets the primary key (PK) of an entity associated with the serializer provided.

- #get_optional_field_value: Gets the value of a model field if it exists either in serializer data or in the database.

- #get_required_field_value: Gets the value of a model field either from serializer data or from the database.

- #rename_serializer_field: Renames specified field of a serializer optionally updating its label.

- #create_standard_serializer_class: Creates serializer class for the Django model specified.

Classses:

- #JsFriendlyFieldsRenamingSerializer: Renames serializer fields from snake_case into Javascript-friendly PascalCase.

- #OptimizeUrlFieldsSerializer: Removes serializer fields producing URLs from output reducing resulting output size.

- #UpdateEditorSerializer: Automatically updates serializer data with request.user if there is any in case of update.

- #InsertAuthorSerializer: Automatically adds request.user to serializer data if there is any in case of creation.
"""

from rest_framework import serializers
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.fields import empty
from django.conf import settings
import re
from inflection import dasherize, underscore


def generate_detail_view_name(base_name):
    """Generates detail view name for a viewset which DRF will use to expose it via router.
    Detail view is used to process requests against individual entities rather than lists.
    DRF registers base_name + '-detail' by default as detail view name.

    Takes #API_URL_NAMESPACE setting into account if set,
    i.e. if #API_URL_NAMESPACE is 'foo' and base name is 'bar' then detail view full name would be 'foo:bar-detail'.

    The intended usage is to provide #HyperlinkedRelatedFields with proper view name to resolve.

    Parameters:

    - base_name #str: The base name of a viewset to.

    Returns: the detail view name.

    See also:

    - [Usage of routers in DRF](https://www.django-rest-framework.org/api-guide/routers/#usage)
    - #generate_serializer_base_name
    - #rest_framework.relations.HyperlinkedRelatedField
    """
    default_detail_name = base_name + "-detail"
    if hasattr(settings, 'API_URL_NAMESPACE'):
        return "{}:{}".format(settings.API_URL_NAMESPACE, default_detail_name)
    return default_detail_name


def generate_serializer_base_name(model_cls):
    """Generates base name to be used when a viewset is exposed via DRF router further on.
    Attaching a base name to the serializer streamlines routing to detail views from related fields.

    By convention standard serializers created by DRF shortcuts package have #DEFAULT_BASE_NAME class attribute,
    which captures this function result against serializer model class for further usage.

    Parameters:

    - model_cls #django.db.models.base.ModelBase: The Model class serializer works with.

    Returns: the base name.

    See also:

    - [Usage of routers in DRF](https://www.django-rest-framework.org/api-guide/routers/#usage)
    - #generate_detail_view_name
    """
    return dasherize(underscore(model_cls.__name__))


def get_entity_pk(serializer):
    """Gets the primary key (PK) of an entity associated with the serializer provided.
    Looks up serializer context for associated view data.

    Parameters:

    - serializer #rest_framework.serializers.BaseSerializer: The serializer instance to use for PK lookup.

    Returns: the PK of the entity if present else #None.
    """
    view_kwargs = serializer.context['view'].kwargs if 'view' in serializer.context else {}
    return view_kwargs.get('pk') if 'pk' in view_kwargs else None


def get_optional_field_value(data, field_name, pk, fetch_model):
    """Gets the value of a model field if it exists either in serializer data or in the database.
    "Optional" means it's not an issue if the field value is not present.

    If there's no field in data, then model if fetched via function provided and looked up instead.
    Field can be missing in data in case of partial update (PATCH) or in case action allows that some other way.

    Parameters:

    - data #dict: The serializer's data to look up the field in first.
    - field_name #str: The name of the field to look up.
    - pk #object: The value of corresponding entity's PK to fetch model in case there's no field in data.
    - fetch_model #function: A function which is expected to return model instance if executed with its PK as argument.

    Returns: the value of the field if present else #None.
    """
    if field_name in data:
        return data.get(field_name)
    return None if pk is None else getattr(fetch_model(pk), field_name)


def get_required_field_value(data, field_name, pk, fetch_model):
    """Gets the value of a model field either from serializer data or from the database.
    "Required" means it's an issue if the field value is not present hence function will fail in such case.

    If there's no field in data, then model if fetched via function provided and looked up instead.
    Field can be missing in data in case of partial update (PATCH) or in case action allows that some other way.

    Parameters:

    - data #dict: The serializer's data to look up the field in first.
    - field_name #str: The name of the field to look up.
    - pk #object: The value of corresponding entity's PK to fetch model in case there's no field in data.
    - fetch_model #function: A function which is expected to return model instance if executed with its PK as argument.

    Returns: the value of the field if present else #None.
    """
    if field_name in data:
        return data.get(field_name)
    assert pk is not None, "Update or partial update is assumed"
    field_value = getattr(fetch_model(pk), field_name)
    assert field_value is not None, "Unexpectedly required field value is None"
    return field_value


def rename_serializer_field(serializer, source_name, target_name, display_name=None):
    """Renames specified field of a serializer optionally updating its label.

    Useful to make field set of a serialized representation of an entity differ from the original one.

    Parameters:

    - serializer #rest_framework.serializers.Serializer: The serializer instance to rename field of.
    - source_name #str: The original name of the field.
    - target_name #str: The desired name of the field.
    - display_name #str: The updated label of the field (optional).

    See also:

    - [DRF Serializer Field Label](https://www.django-rest-framework.org/api-guide/fields/#label)
    """
    field = serializer.fields.pop(source_name)
    if display_name is not None:
        field.label = display_name
    serializer.fields[target_name] = field


# noinspection PyAbstractClass
class JsFriendlyFieldsRenamingSerializer(serializers.Serializer):
    """Renames serializer fields from snake_case into Javascript-friendly PascalCase.

    Looks up field names in snake_case and replaces with PascalCase names leveraging rename_serializer_field & RegExp.

    See also:

    - #rename_serializer_field
    """

    _regex = re.compile('_(.)')

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        for field_name in [f for f in self.fields if '_' in f]:
            rename_serializer_field(self, field_name, self._regex.sub(lambda m: m.group(1).upper(), field_name))


# noinspection PyAbstractClass
class OptimizeUrlFieldsSerializer(serializers.Serializer):
    """Removes serializer fields producing URLs from output reducing resulting output size.

    By default URL fields are removed for any Renderer except BrowsableAPIRenderer.
    HyperlinkedIdentityField, HyperlinkedRelatedField and any explicitly added fields are stripped out.
    Behavior can be overridden by "forceUrls" query parameter ("true" / "false").

    To explicitly add a field inheritors should set up #explicit_url_field_names class attribute.

    See also:

    - [DRF Renderers](https://www.django-rest-framework.org/api-guide/renderers/)
    """

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


# noinspection PyAbstractClass
class UpdateEditorSerializer(serializers.BaseSerializer):
    """Automatically updates serializer data with request.user if there is any in case of update.

    The intended usage is streamline update of "last modified by" kind of model fields.
    Only PUT & PATCH methods trigger such behavior.

    Inheritors must either define #editor_field_name or implement #set_editor_core method.
    """

    editor_field_name = None

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        in_request_context = self.context is not None and 'request' in self.context
        request = self.context['request'] if in_request_context else None
        if in_request_context and request.method in ('PUT', 'PATCH') and request.user:
            if self.editor_field_name:
                result[self.editor_field_name] = request.user
            else:
                self.set_editor_core(result, request.user)
        return result

    def set_editor_core(self, data, editor):
        raise NotImplementedError("This should be implemented")


# noinspection PyAbstractClass
class InsertAuthorSerializer(serializers.BaseSerializer):
    """Automatically adds request.user to serializer data if there is any in case of creation.

    The intended usage is streamline update of "created by" kind of model fields.
    Only POST methods trigger such behavior.

    Inheritors must either define #author_field_name or implement #set_author_core method.
    """

    author_field_name = None

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        in_request_context = self.context is not None and 'request' in self.context
        request = self.context['request'] if in_request_context else None
        if in_request_context and request.method == 'POST' and request.user:
            if self.author_field_name:
                result[self.author_field_name] = request.user
            else:
                self.set_author_core(result, request.user)
        return result

    def set_author_core(self, data, author):
        raise NotImplementedError("This should be implemented")


def create_standard_serializer_class(model_cls):
    """Creates serializer class for the Django model specified.

    Created serializer will declare all model fields,
    will have "url" #HyperlinkedIdentityField pointing at detail view for the entity
    and will inherit #OptimizeUrlFieldsSerializer and #JsFriendlyFieldsRenamingSerializer behaviors.

    Parameters:

    - model_cls #django.db.models.base.ModelBase: The Model class serializer should work with.

    Returns: the standardized serializer class for the model specified.
    """
    base_name = generate_serializer_base_name(model_cls)

    class Serializer(serializers.ModelSerializer, OptimizeUrlFieldsSerializer, JsFriendlyFieldsRenamingSerializer):
        DEFAULT_BASE_NAME = base_name

        url = serializers.HyperlinkedIdentityField(view_name=generate_detail_view_name(DEFAULT_BASE_NAME))

        class Meta:
            model = model_cls
            fields = '__all__'

    Serializer.__name__ = model_cls.__name__ + 'Serializer'
    return Serializer
