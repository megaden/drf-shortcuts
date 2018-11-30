# Summary

Shortcuts for speeding up your development based on Django REST Framework (DRF).

DRF shortcuts library allows you to:

- Expose your Django model class using a one-liner `register_standard_endpoint(your_router, YourModel)`. Exposed API endpoint will support search & ordering of items for suitable fields (backed up by `SearchFilter` & `OrderingFilter` filter backends) and will be nicely documented in both Browseable API & upon issuing `OPTIONS` requests against it.
- Create `rest_framework.viewsets.ModelViewSet` based viewset class for your Django model using a one-liner `create_standard_viewset_class(YourModel)`. Viewset capabilities will be similar to the one registered using `register_standard_endpoint` shortcut.
- Create JS-based clients friendly serializer class for your Django model using a one-liner `create_standard_serializer_class(YourModel)`.
- Use library classes & helper functions to tailor your own DRF shortcuts.

# Quick Links

- [Requirements & Installation](setup.md)
- [Examples](examples.md)
- [API Reference](generated/drf_shortcuts.md)
