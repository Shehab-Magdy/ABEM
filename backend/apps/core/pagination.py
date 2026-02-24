"""Project-wide DRF pagination class."""
from rest_framework.pagination import PageNumberPagination


class ABEMPagination(PageNumberPagination):
    """
    Standard pagination for all list endpoints.

    Clients may override the page size via the ``page_size`` query param
    up to a ceiling of 200 items.  Default page size is 20.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200
