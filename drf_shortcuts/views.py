# -*- coding: utf-8 -*-
"""views module of DRF (Django REST Framework) shortcuts package.

Functions:

- #append_pagination_info_to_docstring: Class decorator for viewsets which adds documentation on pagination.

- #append_search_info_to_docstring: Class decorator for viewsets which adds documentation on search filtering.

- #append_ordering_info_to_docstring: Class decorator factory which creates viewset decorator adding documentation on
ordering of viewset results.

- #append_search_ordering_and_pagination_info_to_docstring: Class decorator factory which creates viewset decorator
combining other documenting decorators.

- #get_fields_suitable_for_ordering: Gets field names of a model specified which are suitable for ordering viewset
results.

- #get_fields_suitable_for_search: Gets field names of a model specified which are suitable for search viewset results.

- #create_standard_viewset_class: Creates viewset class for the Django model specified.
"""

from rest_framework.settings import api_settings
from rest_framework import viewsets
from django.db.models import TextField, CharField
from django.db.models.fields.related import ForeignObjectRel
from inflection import pluralize, humanize, underscore

from drf_shortcuts.serializers import create_standard_serializer_class


def append_pagination_info_to_docstring(cls):
    """Class decorator for viewsets which adds documentation on pagination.

    Documentation is displayed either via Browseable API or upon receiving OPTIONS request.
    """
    if cls.__doc__ is not None:
        cls.__doc__ = '{}\n' \
                      'Specify "?page=<page number>" to get particular page. ' \
                      'Page size is {}.\n'.format(cls.__doc__, api_settings.PAGE_SIZE)
    return cls


def append_search_info_to_docstring(cls):
    """Class decorator for viewsets which adds documentation on search filtering.

    Documentation is displayed either via Browseable API or upon receiving OPTIONS request.
    """
    if cls.__doc__ is not None:
        cls.__doc__ = '{}\n' \
                      'Specify "?search=<search terms here>" query parameter to search items.\n' \
                      .format(cls.__doc__)
    return cls


def append_ordering_info_to_docstring(fields):
    """Class decorator factory which creates viewset decorator adding documentation on ordering of viewset results.

    Documentation is displayed either via Browseable API or upon receiving OPTIONS request.

    Parameters:

    - fields #list: The list of field names which are available for ordering.
    """
    assert len(fields) > 0, "At least one ordering field is required"

    def _wrapped_append(cls):
        if cls.__doc__ is not None:
            appended_doc = 'Specify "?ordering=<fields to order by here>" query parameter to order results.\n\n' \
                           'You can use following fields for ordering: {}.\n\n' \
                           "To reverse ordering of a field prefix it with hyphen '-': ?ordering=-{}.\n" \
                           .format(', '.join(fields), fields[0])
            if len(fields) > 1:
                appended_doc = '{}' \
                               'You can specify multiple orderings by separating them using comma: ?ordering={}.\n' \
                               .format(appended_doc, ','.join(fields[:2]))
            cls.__doc__ = '{}\n{}'.format(cls.__doc__, appended_doc)
        return cls

    return _wrapped_append


def append_search_ordering_and_pagination_info_to_docstring(fields):
    """Class decorator factory which creates viewset decorator combining other documenting decorators.

    It's a shortcut for using the following decorators at once:

    - #append_pagination_info_to_docstring
    - #append_ordering_info_to_docstring
    - #append_search_info_to_docstring

    Documentation is displayed either via Browseable API or upon receiving OPTIONS request.

    Parameters:

    - fields #list: The list of field names which are available for ordering.
    """
    def _wrapped_append(cls):
        return append_pagination_info_to_docstring(
            append_ordering_info_to_docstring(fields)(
                append_search_info_to_docstring(cls)))

    return _wrapped_append


def get_fields_suitable_for_ordering(model):
    """Gets field names of a model specified which are suitable for ordering viewset results.

    Parameters:

    - model #django.db.models.base.ModelBase The model class to look up fields of.

    Returns: the list of field names suitable for ordering.
    """
    return [f.name for f in model._meta.get_fields()
            if not (isinstance(f, TextField) or isinstance(f, ForeignObjectRel))]


def get_fields_suitable_for_search(model):
    """Gets field names of a model specified which are suitable for search viewset results.

    Parameters:

    - model #django.db.models.base.ModelBase: The model class to look up fields of.

    Returns: the list of field names suitable for search.
    """
    return [f.name for f in model._meta.get_fields() if isinstance(f, CharField)]


def create_standard_viewset_class(model_cls, serializer_cls=None):
    """Creates viewset class for the Django model specified.

    Created viewset will either use serializer specified or a standard one,
    will have search & ordering fields specified, viewset's queryset will return all model objects ordered by PK
    and all documentation decorators will be applied to the viewset.

    Parameters:

    - model_cls #django.db.models.base.ModelBase: The Model class viewset should expose.
    - serializer_cls #type: The serializer class viewset should use (optional).

        If omitted the 'standard' serializer class will be used.

        See also #drf_shortcuts.serializers.create_standard_serializer_class.

    Returns: the standardized viewset class for the model specified.

    See also:

    - #get_fields_suitable_for_ordering
    - #get_fields_suitable_for_search
    """
    fields = get_fields_suitable_for_ordering(model_cls)

    class ViewSet(viewsets.ModelViewSet):
        serializer_class = serializer_cls or create_standard_serializer_class(model_cls)
        search_fields = get_fields_suitable_for_search(model_cls)
        ordering_fields = fields
        lookup_value_regex = '[^/]+'

        def get_queryset(self):
            return model_cls.objects.all().order_by('id')

    plural_model = pluralize(model_cls.__name__)
    ViewSet.__name__ = plural_model + 'ViewSet'
    ViewSet.__doc__ = 'This is {} API endpoint.\n'.format(humanize(underscore(plural_model)).lower())
    append_search_ordering_and_pagination_info_to_docstring(fields)(ViewSet)
    return ViewSet
