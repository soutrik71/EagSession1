import os
import ssl
import urllib3
import httpx
from typing import Optional

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def patch_ssl_verification():
    """
    Patch SSL verification at a global level for all HTTP clients.
    This should be called before any other imports or HTTP requests.
    """
    # Set environment variables
    os.environ["PYTHONHTTPSVERIFY"] = "0"
    os.environ["OPENAI_API_SKIP_VERIFY_SSL"] = "true"
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"

    # Clear SSL_CERT_FILE if set
    if "SSL_CERT_FILE" in os.environ:
        del os.environ["SSL_CERT_FILE"]

    # Monkey patch ssl.create_default_context
    original_create_default_context = ssl.create_default_context

    def patched_create_default_context(*args, **kwargs):
        context = original_create_default_context(*args, **kwargs)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    ssl.create_default_context = patched_create_default_context

    # Try to monkey patch httpx
    try:
        # Create a subclass of HTTPTransport with SSL verification disabled
        original_httpx_client = httpx.Client

        class InsecureClient(httpx.Client):
            def __init__(self, *args, **kwargs):
                kwargs["verify"] = False
                super().__init__(*args, **kwargs)

        httpx.Client = InsecureClient

        # Also patch AsyncClient
        original_httpx_async_client = httpx.AsyncClient

        class InsecureAsyncClient(httpx.AsyncClient):
            def __init__(self, *args, **kwargs):
                kwargs["verify"] = False
                super().__init__(*args, **kwargs)

        httpx.AsyncClient = InsecureAsyncClient
    except Exception as e:
        print(f"Warning: Failed to patch httpx: {e}")

    # Try to patch urllib3
    try:
        # Disable certificate verification in urllib3
        import urllib3.connection

        urllib3.connection.VerifiedHTTPSConnection = urllib3.connection.HTTPSConnection
        urllib3.connectionpool.VerifiedHTTPSConnection = (
            urllib3.connectionpool.HTTPSConnection
        )
    except Exception as e:
        print(f"Warning: Failed to patch urllib3: {e}")

    print("SSL verification has been disabled globally")


def create_insecure_http_client() -> httpx.Client:
    """
    Create an HTTPX client with SSL verification disabled.
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    return httpx.Client(verify=False, timeout=120.0, http2=False)


def create_insecure_async_http_client() -> httpx.AsyncClient:
    """
    Create an async HTTPX client with SSL verification disabled.
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    return httpx.AsyncClient(verify=False, timeout=120.0, http2=False)
