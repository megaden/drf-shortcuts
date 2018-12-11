# -*- coding: utf-8 -*-
"""urls module of DRF (Django REST Framework) shortcuts package.

Functions:

- #register_standard_endpoint: Exposes Django model via DRF router.

See also:

- #drf_shortcuts.views.create_standard_viewset_class
"""

from inflection import dasherize, underscore

from drf_shortcuts.views import create_standard_viewset_class


def register_standard_endpoint(router, model, viewset_cls=None):
    """Exposes API endpoints for Django model via DRF router.

    Parameters:

    - router #rest_framework.routers.BaseRouter: The instance of DRF router to add viewset to.

    - model #django.db.models.base.ModelBase: The model class to expose.

    - viewset_cls #rest_framework.viewsets.GenericViewSet: The viewset to expose (optional).

        If omitted the 'standard' viewset class will be used.

        See also #drf_shortcuts.views.create_standard_viewset_class.
    """
    endpoint_name = dasherize(underscore(model.__name__))
    viewset = viewset_cls or create_standard_viewset_class(model)
    router.register(endpoint_name, viewset, base_name=viewset.serializer_class.DEFAULT_BASE_NAME)
