"""
backend/middleware/exception_handler.py

Global exception handler returning standardized JSON error responses.
"""

import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("GlobalExceptionHandler")


async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url),
        },
    )
