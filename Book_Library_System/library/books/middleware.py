import logging
from django.shortcuts import render
from django.http import Http404

logger = logging.getLogger("books")


class GlobalExceptionHandlerMiddleware:
    """
    Catch unhandled exceptions, log them for debugging, and return a
    generic, user-friendly error page. No technical details are exposed
    to the user.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        # Log warning for missing pages, but let Django render the 404 page.
        if isinstance(exception, Http404):
            logger.warning(
                "Page not found: %s %s",
                request.method,
                request.path,
                exc_info=True,
            )
            return None

        # Log full technical details for any unexpected error.
        logger.error(
            "Unhandled exception at %s %s: %s",
            request.method,
            request.path,
            str(exception),
            exc_info=True,
        )

        # Return a generic message to the user.
        return render(
            request,
            "books/error.html",
            {
                "message": (
                    "Something went wrong while processing your request. "
                    "Please try again later or contact support if the problem persists."
                )
            },
            status=500,
        )
