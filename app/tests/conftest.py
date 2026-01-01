import pytest
from fastapi.testclient import TestClient
from app.main import app
import httpx
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return '''
<html>
<head><title>Test Article</title></head>
<body>
    <h1>Test</h1>
    <p>This is a test article with content.</p>
    <pre><code>def hello_world():
    print("Hello, World!")</code></pre>
    <pre><code>function greet() {
    console.log("Hi!");
}</code></pre>
    <table><tr><td>Data 1</td><td>Data 2</td></tr></table>
    <table><tr><td>Data 3</td><td>Data 4</td></tr></table>
    <table><tr><td>Data 5</td><td>Data 6</td></tr></table>
</body>
</html>
'''


@pytest.fixture
def sample_text_high_density():
    """High density text content."""
    return "Machine learning algorithms provide computational methods for learning patterns from data without being explicitly programmed."


@pytest.fixture
def sample_text_low_density():
    """Low density text content."""
    return "Short text"


@pytest.fixture
def sample_text_empty():
    """Empty text content."""
    return ""


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for testing."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = AsyncMock()
    mock_response.text = "<html><body><h1>Test</h1></body></html>"
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '{"summary": "Test summary", "key_findings": ["Fact 1", "Fact 2"], "technical_depth_score": 75, "bias_rating": "Neutral"}'
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client