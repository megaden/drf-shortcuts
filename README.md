# DRF Shortcuts

[![Build Status](https://travis-ci.org/megaden/drf-shortcuts.svg?branch=master)](https://travis-ci.org/megaden/drf-shortcuts)
[![PyPI Version](https://img.shields.io/pypi/v/drf_shortcuts.svg)](https://img.shields.io/pypi/v/drf_shortcuts.svg)

Shortcuts for speeding up your development based on Django REST Framework (DRF).

## Overview

DRF shortcuts library allows you to:

- Expose your Django model class using a one-liner `register_standard_endpoint(your_router, YourModel)`. Exposed API endpoint will support search & ordering of items for suitable fields (backed up by `SearchFilter` & `OrderingFilter` filter backends) and will be nicely documented in both Browseable API & upon issuing `OPTIONS` requests against it.
- Create `rest_framework.viewsets.ModelViewSet` based viewset class for your Django model using a one-liner `create_standard_viewset_class(YourModel)`. Viewset capabilities will be similar to the one registered using `register_standard_endpoint` shortcut.
- Create JS-based clients friendly serializer class for your Django model using a one-liner `create_standard_serializer_class(YourModel)`.
- Use library classes & helper functions to tailor your own DRF shortcuts.

## Requirements

- Python 3.6+
- Django 2.0+
- Django REST Framework 3.8+

## Installation

Install using pip:

    pip install drf-shortcuts

## Examples

Exposing a Django model:

    # in urls.py

    from rest_framework.routers import DefaultRouter
    from drf_shortcuts.urls import register_standard_endpoint

    from my_fancy_app.models import MyModel


    router = DefaultRouter()

    register_standard_endpoint(router, MyModel)

    # ... more URL configuration code here ...

    urlpatterns = router.urls

Creating a viewset class:

    # in views.py

    from drf_shortcuts.views import create_standard_viewset_class

    from my_fancy_app.models import MyModel

    MyModelViewSet = create_standard_viewset_class(MyModel)

Creating a serializer class:

    # in serializers.py

    from drf_shortcuts.serializers import create_standard_serializer_class

    from my_fancy_app.models import MyModel

    MyModelSerializer = create_standard_serializer_class(MyModel)

Customizing a view using helpers:

    # in views.py

    from rest_framework.viewsets import ReadOnlyModelViewSet
    from drf_shortcuts.views import append_search_info_to_docstring
    from drf_shortcuts.serializers import create_standard_serializer_class

    from my_fancy_app.models import MyModel


    @append_search_info_to_docstring
    class MyModelViewSet(ReadOnlyModelViewSet):
        serializer_class = create_standard_serializer_class(MyModel)

        # ... rest of the view code ...

## Documentation

Visit [project's GitHub Pages](https://megaden.github.io/drf-shortcuts/).
