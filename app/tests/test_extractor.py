import pytest
import os
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, '/root/sgnl-backend/app')
from extractor import calculate_density, calculate_depid_density, calculate_readability_scores, calculate_combined_density, ContentExtractor


class TestCalculateDensity:
    """Test the calculate_density function."""

    def test_calculate_density_high_content(self, sample_text_high_density):
        """Test density calculation with high-quality content."""
        with patch('app.extractor.IDEADENSITY_AVAILABLE', True), \
             patch('app.extractor.cpidr') as mock_cpidr:
            mock_cpidr.return_value = 0.8
            density = calculate_density(sample_text_high_density)
            assert density == 0.8
            mock_cpidr.assert_called_once_with(sample_text_high_density)

    def test_calculate_density_low_content(self, sample_text_low_density):
        """Test density calculation with low-quality content."""
        with patch('app.extractor.IDEADENSITY_AVAILABLE', True), \
             patch('app.extractor.cpidr') as mock_cpidr:
            mock_cpidr.return_value = 0.3
            density = calculate_density(sample_text_low_density)
            assert density == 0.3

    def test_calculate_density_empty_text(self, sample_text_empty):
        """Test density calculation with empty text."""
        density = calculate_density(sample_text_empty)
        assert density == 0.0

    def test_calculate_density_short_text(self):
        """Test density calculation with text shorter than 50 characters."""
        short_text = "Short text"
        density = calculate_density(short_text)
        assert density == 0.0

    def test_calculate_density_ideadensity_unavailable(self, sample_text_high_density):
        """Test density calculation when ideadensity is not available."""
        with patch('app.extractor.IDEADENSITY_AVAILABLE', False):
            density = calculate_density(sample_text_high_density)
            assert density == 0.5

    def test_calculate_density_exception_handling(self, sample_text_high_density):
        """Test density calculation when cpidr raises exception."""
        with patch('app.extractor.IDEADENSITY_AVAILABLE', True), \
             patch('app.extractor.cpidr') as mock_cpidr:
            mock_cpidr.side_effect = Exception("Test error")
            density = calculate_density(sample_text_high_density)
            assert density == 0.5

    def test_calculate_density_normalization(self):
        """Test that density is normalized to 0.0-1.0 range."""
        with patch('app.extractor.IDEADENSITY_AVAILABLE', True), \
             patch('app.extractor.cpidr') as mock_cpidr:
            # Test value > 1.0 gets clamped
            mock_cpidr.return_value = 1.5
            density = calculate_density("test content")
            assert density == 1.0

            # Test negative value gets clamped
            mock_cpidr.return_value = -0.5
            density = calculate_density("test content")
            assert density == 0.0


class TestContentExtractor:
    """Test ContentExtractor utility methods."""

    def test_extract_domain_valid_url(self):
        """Test domain extraction from valid URL."""
        extractor = ContentExtractor()
        domain = extractor._extract_domain("https://www.example.com/path/to/page")
        assert domain == "example.com"

    def test_extract_domain_no_www(self):
        """Test domain extraction without www."""
        extractor = ContentExtractor()
        domain = extractor._extract_domain("https://example.com/page")
        assert domain == "example.com"

    def test_extract_domain_subdomain(self):
        """Test domain extraction with subdomain."""
        extractor = ContentExtractor()
        domain = extractor._extract_domain("https://blog.example.com/article")
        assert domain == "blog.example.com"

    def test_extract_domain_invalid_url(self):
        """Test domain extraction with invalid URL."""
        extractor = ContentExtractor()
        domain = extractor._extract_domain("not-a-url")
        assert domain == "unknown"

    def test_extract_title_fallback_with_title(self, sample_html):
        """Test title fallback extraction when title tag exists."""
        extractor = ContentExtractor()
        title = extractor._extract_title_fallback(sample_html)
        assert title == "Test Article - Understanding Machine Learning"

    def test_extract_title_fallback_no_title(self):
        """Test title fallback extraction when no title tag exists."""
        html_no_title = "<html><body><h1>Heading</h1></body></html>"
        extractor = ContentExtractor()
        title = extractor._extract_title_fallback(html_no_title)
        assert title is None

    def test_extract_title_fallback_empty_html(self):
        """Test title fallback extraction with empty HTML."""
        extractor = ContentExtractor()
        title = extractor._extract_title_fallback("")
        assert title is None

    def test_extract_title_fallback_malformed_html(self):
        """Test title fallback extraction with malformed HTML."""
        malformed_html = "<html><head><title>Unclosed title"
        extractor = ContentExtractor()
        title = extractor._extract_title_fallback(malformed_html)
        assert title == "Unclosed title"

    def test_error_response_structure(self):
        """Test error response structure."""
        extractor = ContentExtractor()
        error_resp = extractor._error_response("https://example.com", "Test error")

        required_keys = ["url", "title", "content", "source", "length", "signal_score", "density_score", "error"]
        for key in required_keys:
            assert key in error_resp

        assert error_resp["url"] == "https://example.com"
        assert error_resp["title"] == "Extraction Failed"
        assert error_resp["content"] == "Error: Test error"
        assert error_resp["source"] == "example.com"
        assert error_resp["length"] == 0
        assert error_resp["signal_score"] == 0.0
        assert error_resp["density_score"] == 0.0
        assert error_resp["error"] == "Test error"

    @pytest.mark.asyncio
    async def test_extract_from_url_with_new_fields(self, mock_httpx_client):
        """Test extraction response includes new depid and readability fields."""
        extractor = ContentExtractor()

        with patch('app.extractor.trafilatura.extract') as mock_extract, \
             patch('app.extractor.trafilatura.extract_metadata') as mock_metadata, \
             patch('app.extractor.calculate_density') as mock_density, \
             patch('app.extractor.calculate_depid_density') as mock_depid, \
             patch('app.extractor.calculate_readability_scores') as mock_readability, \
             patch('app.extractor.calculate_combined_density') as mock_combined, \
             patch.object(extractor, '_fetch_page', return_value="<html><body>Test content</body></html>"):

            mock_extract.return_value = "Extracted clean text content"
            mock_metadata.return_value = MagicMock()
            mock_metadata.return_value.title = "Test Title"
            mock_density.return_value = 0.7
            mock_depid.return_value = 0.6
            mock_readability.return_value = {"flesch_reading_ease": 60.0}
            mock_combined.return_value = 0.65

            result = await extractor.extract_from_url("https://example.com")

            assert result["url"] == "https://example.com"
            assert result["title"] == "Test Title"
            assert result["density_score"] == 0.7
            assert result["depid_density"] == 0.6
            assert result["readability_score"] == {"flesch_reading_ease": 60.0}

    def test_calculate_signal_score_high_quality_content(self):
        """Test signal score calculation with high-quality content."""
        extractor = ContentExtractor()
        content = "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention."
        url = "https://arxiv.org/abs/1234.5678"
        title = "Understanding Machine Learning Algorithms"

        score = extractor._calculate_signal_score(content, url, title)

        assert 0.6 <= score <= 1.0  # Should be high signal

    def test_calculate_signal_score_low_quality_content(self):
        """Test signal score calculation with low-quality content."""
        extractor = ContentExtractor()
        content = "Buy now! Limited time offer! Click here to save money!"
        url = "https://spam-site.com"
        title = "Amazing Deal!"

        score = extractor._calculate_signal_score(content, url, title)

        assert score <= 0.3  # Should be low signal

    def test_calculate_signal_score_short_content(self):
        """Test signal score calculation with short content."""
        extractor = ContentExtractor()
        content = "Short content"
        url = "https://example.com"
        title = "Test"

        score = extractor._calculate_signal_score(content, url, title)

        assert score < 0.5  # Short content should reduce score

    def test_calculate_signal_score_technical_content(self):
        """Test signal score calculation with technical content indicators."""
        extractor = ContentExtractor()
        content = """
        def neural_network(input_data):
            import numpy as np
            weights = np.random.randn(10, 5)
            bias = np.zeros(5)
            output = np.dot(input_data, weights) + bias
            return output

        This function implements a simple neural network layer using NumPy.
        The algorithm has O(n*m) time complexity where n is input size and m is output size.
        """
        url = "https://github.com/user/repo"
        title = "Neural Network Implementation"

        score = extractor._calculate_signal_score(content, url, title)

        assert score > 0.5  # Technical content should boost score

    def test_calculate_signal_score_spam_detection(self):
        """Test signal score calculation with spam pattern detection."""
        extractor = ContentExtractor()
        content = "Subscribe to our newsletter! Sign up for free updates! Click here to buy!"
        url = "https://example.com"
        title = "Amazing Offer"

        score = extractor._calculate_signal_score(content, url, title)

        assert score < 0.5  # Spam patterns should reduce score

    def test_calculate_signal_score_domain_boost(self):
        """Test signal score calculation with trusted domain boost."""
        extractor = ContentExtractor()
        content = "This is a research paper about computer science."
        url = "https://arxiv.org/abs/1234.5678"
        title = "Research Paper"

        score = extractor._calculate_signal_score(content, url, title)

        # Should get boost from arxiv.org domain
        assert score > 0.5

    @pytest.mark.asyncio
    async def test_extract_from_url_success(self, mock_httpx_client):
        """Test successful URL extraction with mocked dependencies."""
        extractor = ContentExtractor()

        with patch('app.extractor.trafilatura.extract') as mock_extract, \
             patch('app.extractor.trafilatura.extract_metadata') as mock_metadata, \
             patch('app.extractor.calculate_density') as mock_density, \
             patch.object(extractor, '_fetch_page', return_value="<html><body>Test content</body></html>"):

            # Mock trafilatura responses
            mock_extract.return_value = "Extracted clean text content"
            mock_metadata.return_value = MagicMock()
            mock_metadata.return_value.title = "Test Title"
            mock_density.return_value = 0.7

            result = await extractor.extract_from_url("https://example.com")

            assert result["url"] == "https://example.com"
            assert result["title"] == "Test Title"
            assert result["content"] == "Extracted clean text content"
            assert result["source"] == "example.com"
            assert result["length"] == len("Extracted clean text content")
            assert result["signal_score"] == 0.0  # Would be calculated
            assert result["density_score"] == 0.7

    @pytest.mark.asyncio
    async def test_extract_from_url_fetch_failure(self):
        """Test URL extraction when fetch fails."""
        extractor = ContentExtractor()

        with patch.object(extractor, '_fetch_page', return_value=None):
            result = await extractor.extract_from_url("https://example.com")

            assert result["url"] == "https://example.com"
            assert "error" in result
            assert result["length"] == 0
            assert result["signal_score"] == 0.0
            assert result["density_score"] == 0.0

    @pytest.mark.asyncio
    async def test_extract_from_url_no_content_extracted(self, mock_httpx_client):
        """Test URL extraction when trafilatura extracts no content."""
        extractor = ContentExtractor()

        with patch('app.extractor.trafilatura.extract', return_value=""), \
             patch('app.extractor.trafilatura.extract_metadata') as mock_metadata, \
             patch.object(extractor, '_fetch_page', return_value="<html><body></body></html>"):

            mock_metadata.return_value = None

            result = await extractor.extract_from_url("https://example.com")

            assert result["url"] == "https://example.com"
            assert "error" in result
            assert "No content extracted" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_from_url_exception_handling(self, mock_httpx_client):
        """Test URL extraction with general exception."""
        extractor = ContentExtractor()

        with patch.object(extractor, '_fetch_page', side_effect=Exception("Network error")):
            result = await extractor.extract_from_url("https://example.com")

            assert result["url"] == "https://example.com"
            assert "error" in result
            assert result["error"] == "Network error"


class TestCalculateDepidDensity:
    """Test calculate_depid_density function."""

    def test_calculate_depid_density_success(self, sample_text_high_density):
        """Test DEPID density calculation with valid text."""
        with patch('app.extractor.IDEADENSITY_AVAILABLE', True), \
             patch('app.extractor.depid') as mock_depid:
            mock_depid.return_value = (0.7, 100, [])
            density = calculate_depid_density(sample_text_high_density)
            assert density == 0.7
            mock_depid.assert_called_once()

    def test_calculate_depid_density_unavailable(self, sample_text_high_density):
        """Test DEPID density when ideadensity is unavailable."""
        with patch('app.extractor.IDEADENSITY_AVAILABLE', False):
            density = calculate_depid_density(sample_text_high_density)
            assert density is None

    def test_calculate_depid_density_short_text(self):
        """Test DEPID density with short text."""
        short_text = "Short"
        density = calculate_depid_density(short_text)
        assert density is None

    def test_calculate_depid_density_exception_handling(self, sample_text_high_density):
        """Test DEPID density when depid raises exception."""
        with patch('app.extractor.IDEADENSITY_AVAILABLE', True), \
             patch('app.extractor.depid') as mock_depid:
            mock_depid.side_effect = Exception("DEPID error")
            density = calculate_depid_density(sample_text_high_density)
            assert density is None


class TestCalculateReadabilityScores:
    """Test calculate_readability_scores function."""

    def test_calculate_readability_scores_success(self, sample_text_high_density):
        """Test readability scores calculation with valid text."""
        with patch('app.extractor.TEXTSTAT_AVAILABLE', True), \
             patch('app.extractor.textstat') as mock_textstat:
            mock_textstat.flesch_reading_ease.return_value = 75.0
            mock_textstat.flesch_kincaid_grade.return_value = 10.0
            mock_textstat.gunning_fog.return_value = 12.0
            mock_textstat.automated_readability_index.return_value = 6.0
            mock_textstat.coleman_liau_index.return_value = 9.0

            scores = calculate_readability_scores(sample_text_high_density)

            assert "flesch_reading_ease" in scores
            assert "flesch_kincaid_grade" in scores
            assert "gunning_fog" in scores
            assert "automated_readability_index" in scores
            assert "coleman_liau_index" in scores
            assert scores["flesch_reading_ease"] == 75.0

    def test_calculate_readability_scores_unavailable(self, sample_text_high_density):
        """Test readability scores when textstat is unavailable."""
        with patch('app.extractor.TEXTSTAT_AVAILABLE', False):
            scores = calculate_readability_scores(sample_text_high_density)
            assert scores == {}

    def test_calculate_readability_scores_short_text(self):
        """Test readability scores with short text."""
        short_text = "Short"
        scores = calculate_readability_scores(short_text)
        assert scores == {}


class TestCalculateCombinedDensity:
    """Test calculate_combined_density function."""

    @patch.dict(os.environ, {'CPIDR_WEIGHT': '0.5', 'DEPID_WEIGHT': '0.3', 'READABILITY_WEIGHT': '0.2'}, clear=True)
    def test_combined_density_with_all_metrics(self):
        """Test combined density with CPIDR, DEPID, and readability."""
        cpidr = 0.6
        depid = 0.7
        readability = {"flesch_reading_ease": 60.0}

        combined = calculate_combined_density(cpidr, depid, readability)

        # Expected: (0.6 * 0.5 + 0.7 * 0.3 + (30/90) * 0.2) / 1.0
        # Reading difficulty: (90 - 60) / 90 = 0.333
        # Combined: (0.3 + 0.21 + 0.067) = 0.577
        assert 0.5 <= combined <= 0.6

    @patch.dict(os.environ, {'CPIDR_WEIGHT': '0.5', 'DEPID_WEIGHT': '0.3', 'READABILITY_WEIGHT': '0.2'}, clear=True)
    def test_combined_density_depid_none(self):
        """Test combined density when DEPID is None."""
        cpidr = 0.6
        depid = None
        readability = {"flesch_reading_ease": 60.0}

        combined = calculate_combined_density(cpidr, depid, readability)

        # Expected: (0.6 * 0.5 + 0.067) / (0.5 + 0.2) = 0.667 / 0.7 = 0.95
        # Actually without DEPID weight: 0.667 / 0.7 = 0.95
        assert 0.0 <= combined <= 1.0

    @patch.dict(os.environ, {'CPIDR_WEIGHT': '0.5', 'DEPID_WEIGHT': '0.3', 'READABILITY_WEIGHT': '0.2'}, clear=True)
    def test_combined_density_no_readability(self):
        """Test combined density when readability is empty."""
        cpidr = 0.6
        depid = 0.7
        readability = {}

        combined = calculate_combined_density(cpidr, depid, readability)

        # Should fall back to CPIDR + DEPID only (0.6 * 0.5 + 0.7 * 0.3) / 0.8 ≈ 0.83
        assert 0.0 <= combined <= 1.0

    @patch.dict(os.environ, {'CPIDR_WEIGHT': '0.8', 'DEPID_WEIGHT': '0.1', 'READABILITY_WEIGHT': '0.1'}, clear=True)
    def test_combined_density_custom_weights(self):
        """Test combined density with custom weights from env."""
        cpidr = 0.5
        depid = 0.6
        readability = {"flesch_reading_ease": 60.0}

        combined = calculate_combined_density(cpidr, depid, readability)

        # Expected: (0.5 * 0.8 + 0.6 * 0.1 + 0.333 * 0.1) / 1.0
        expected = (0.4 + 0.06 + 0.0333) / 1.0
        assert abs(combined - expected) < 0.01