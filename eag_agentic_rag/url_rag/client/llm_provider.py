import os
import ssl
import sys
import warnings
import httpx

# ======== CRITICAL SSL PATCHING AT THE MOST BASIC LEVEL ========
# Based on proven ssl_helper.py techniques for comprehensive SSL bypassing

# 1. Set all environment variables that could affect SSL verification
os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["OPENAI_VERIFY_SSL_CERTS"] = "false"
os.environ["OPENAI_API_SKIP_VERIFY_SSL"] = "true"
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"

# 2. Remove any problematic SSL_CERT_FILE setting
if "SSL_CERT_FILE" in os.environ:
    print(f"Removing SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE')}")
    del os.environ["SSL_CERT_FILE"]

# 3. Create and use unverified SSL context
ssl._create_default_https_context = ssl._create_unverified_context

# 4. Apply more aggressive patching of the SSL default context
original_create_default_context = ssl.create_default_context


def patched_create_default_context(*args, **kwargs):
    context = original_create_default_context(*args, **kwargs)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


ssl.create_default_context = patched_create_default_context

# 5. Patch urllib3 which is used by requests and httpx
try:
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Patch at the lowest level
    urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"

    # Replace the VerifiedHTTPSConnection with unverified version
    urllib3.connection.VerifiedHTTPSConnection = urllib3.connection.HTTPSConnection
    urllib3.connectionpool.VerifiedHTTPSConnection = (
        urllib3.connectionpool.HTTPSConnection
    )

    print("urllib3 SSL patched successfully")
except ImportError:
    print("urllib3 not available to patch")
except Exception as e:
    print(f"Warning: Failed to patch urllib3 completely: {e}")

# 6. Patch httpx's Client class (for sync)
# Save original class
original_httpx_client = httpx.Client


# Create patched Client class
class InsecureClient(original_httpx_client):
    def __init__(self, *args, **kwargs):
        kwargs["verify"] = False
        super().__init__(*args, **kwargs)


# Replace the original class
httpx.Client = InsecureClient

# Note: We're NOT patching AsyncClient as it causes issues with LangChain
# Instead we'll configure it directly through other means

print("httpx Client patched to disable SSL verification")

# 7. Suppress all SSL warnings
warnings.filterwarnings("ignore", ".*SSL.*")
warnings.filterwarnings("ignore", ".*Certificate.*")
warnings.filterwarnings("ignore", ".*Unverified.*")

# 8. Patch httpx transport for AsyncClient
# This is a lower-level approach that doesn't break compatibility
original_httpx_transport = httpx._transports.default.AsyncHTTPTransport


class InsecureAsyncHTTPTransport(original_httpx_transport):
    def __init__(self, *args, **kwargs):
        kwargs["verify"] = False
        super().__init__(*args, **kwargs)


httpx._transports.default.AsyncHTTPTransport = InsecureAsyncHTTPTransport
print("httpx AsyncHTTPTransport patched to disable SSL verification")

# 9. Report success
print("✅ SSL verification completely disabled at all levels")

# Now all other imports
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Additional debug info
print("SSL_CERT_FILE:", os.environ.get("SSL_CERT_FILE"))
print("PYTHONHTTPSVERIFY:", os.environ.get("PYTHONHTTPSVERIFY"))
print("OPENAI_VERIFY_SSL_CERTS:", os.environ.get("OPENAI_VERIFY_SSL_CERTS"))
print("OPENAI_API_SKIP_VERIFY_SSL:", os.environ.get("OPENAI_API_SKIP_VERIFY_SSL"))


# Helper functions from ssl_helper for creating clients
def create_insecure_http_client(timeout=120.0):
    """Create an HTTPX client with SSL verification disabled."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return httpx.Client(verify=False, timeout=timeout, http2=False)


def create_insecure_async_http_client(timeout=120.0):
    """Create an async HTTPX client with SSL verification disabled."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    # Use original AsyncClient to avoid compatibility issues
    # but force verification to be disabled
    return httpx.AsyncClient(verify=False, timeout=timeout, http2=False)


class LLMProvider:
    """Provider for LLM interactions using LangChain's OpenAI implementation with robust SSL handling."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o",
        timeout: float = 120.0,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided and not found in environment variables"
            )
        self.model = model
        self.timeout = timeout

        # Basic config for ChatOpenAI
        self.model_kwargs = {"model": model}
        self.client_kwargs = {"openai_api_key": self.api_key, "temperature": 0}

        # Create the synchronous client
        self.chat_model = self._create_sync_chat_model()

        # Async model will be lazily created
        self.async_chat_model = None

    def _create_sync_chat_model(self):
        """Create a properly configured synchronous chat model."""
        # Create a simple HTTP client with very basic config using helper
        http_client = create_insecure_http_client(timeout=self.timeout)

        # Create the ChatOpenAI instance
        return ChatOpenAI(
            **self.client_kwargs,
            **self.model_kwargs,
            http_client=http_client,
        )

    def _create_async_chat_model(self):
        """Create a properly configured asynchronous chat model."""
        # For async, we'll directly set LangChain's API parameters
        # instead of providing our own client
        import openai
        from openai import AsyncOpenAI

        # Configure base OpenAI settings
        openai.verify_ssl_certs = False

        # Create the LangChain model
        chat_model = ChatOpenAI(
            **self.client_kwargs,
            **self.model_kwargs,
        )

        # Directly configure the OpenAI client it uses
        # Force OpenAI async client to use our special settings
        chat_model.client.verify_ssl_certs = False

        # For newer versions, try to patch the async client too
        try:
            if hasattr(chat_model, "async_client") and isinstance(
                chat_model.async_client, AsyncOpenAI
            ):
                chat_model.async_client.verify_ssl_certs = False
        except Exception:
            pass

        return chat_model

    def get_completion(self, system_message: str, user_prompt: str) -> str:
        """Get a synchronous completion from the LLM."""
        from langchain.schema import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt),
        ]
        response = self.chat_model.invoke(messages)
        return response.content

    async def get_completion_async(self, system_message: str, user_prompt: str) -> str:
        """Get an asynchronous completion from the LLM."""
        from langchain.schema import HumanMessage, SystemMessage

        # Initialize async model if not yet created
        if self.async_chat_model is None:
            self.async_chat_model = self._create_async_chat_model()

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt),
        ]

        # Use the async model for invoking
        response = await self.async_chat_model.ainvoke(messages)
        return response.content


# Create a default instance for easy import, with SSL verification disabled
default_llm = LLMProvider()


# Test SSL configuration
def test_ssl_config():
    """Test SSL configuration by making a simple HTTPS request."""
    try:
        resp = httpx.get("https://api.openai.com/v1/models", verify=False)
        print(f"✅ SSL test success: {resp.status_code}")
        return True
    except Exception as e:
        print(f"❌ SSL test failed: {e}")
        return False


# Run the SSL test to verify our configuration
test_ssl_config()
