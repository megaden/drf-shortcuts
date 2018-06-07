from inflection import dasherize, underscore

from drf_shortcuts.views import create_standard_viewset_class


def register_standard_endpoint(router, model):
    endpoint_name = dasherize(underscore(model.__name__))
    viewset = create_standard_viewset_class(model)
    router.register(endpoint_name, viewset, base_name=viewset.serializer_class.DEFAULT_BASE_NAME)