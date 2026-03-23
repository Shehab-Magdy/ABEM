"""Project-wide DRF pagination class."""
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination


class ABEMPagination(PageNumberPagination):
    """
    Standard pagination for all list endpoints.

    Clients may override the page size via the ``page_size`` query param
    up to a ceiling of 100 items.  Default page size is 20.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                requested = int(request.query_params[self.page_size_query_param])
            except (KeyError, ValueError):
                return self.page_size
            if requested > self.max_page_size:
                raise ValidationError(
                    {self.page_size_query_param: f"Page size must not exceed {self.max_page_size}."}
                )
            if requested < 1:
                raise ValidationError(
                    {self.page_size_query_param: "Page size must be at least 1."}
                )
            return requested
        return self.page_size
