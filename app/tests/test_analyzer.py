import pytest
from app.services.analyzer import HeuristicAnalyzer
from bs4 import BeautifulSoup
from unittest.mock import patch


class TestHeuristicAnalyzer:
    """Test HeuristicAnalyzer class methods."""

    def test_init(self):
        """Test analyzer initialization and regex compilation."""
        analyzer = HeuristicAnalyzer()
        assert analyzer.affiliate_regex is not None
        assert analyzer.hype_regex is not None

        # Test regex patterns
        assert analyzer.affiliate_regex.search("amzn.to/link")
        assert analyzer.hype_regex.search("shocking news")

    def test_calculate_structure_score_valid_html(self, sample_html):
        """Test structure score calculation with valid HTML."""
        analyzer = HeuristicAnalyzer()
        result = analyzer.calculate_structure_score(sample_html, "machine learning")

        assert isinstance(result, dict)
        assert "score" in result
        assert "reason" in result
        assert "adjustments" in result
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100

    def test_calculate_structure_score_empty_html(self):
        """Test structure score calculation with empty HTML."""
        analyzer = HeuristicAnalyzer()
        result = analyzer.calculate_structure_score("", "test")

        assert result["score"] == 0
        assert "Empty or too short content" in result["reason"]

    def test_calculate_structure_score_short_html(self):
        """Test structure score calculation with short HTML."""
        short_html = "<html><body>Short</body></html>"
        analyzer = HeuristicAnalyzer()
        result = analyzer.calculate_structure_score(short_html, "test")

        assert result["score"] == 0
        assert "Empty or too short content" in result["reason"]

    def test_calculate_structure_score_parse_error(self):
        """Test structure score calculation with malformed HTML."""
        # Use a valid HTML string (≥100 chars) to pass length check
        # Mock BeautifulSoup to raise an exception during parsing
        long_html = "<html><body>" + "This is longer content " * 20 + "</body></html>"

        with patch('app.services.analyzer.BeautifulSoup', side_effect=Exception("Parse error")):
            analyzer = HeuristicAnalyzer()
            result = analyzer.calculate_structure_score(long_html, "test")

        assert result["score"] == 30
        assert "Failed to parse HTML" in result["reason"]

    def test_analyze_code_density_with_code(self, sample_html):
        """Test code density analysis with HTML containing code."""
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(sample_html, "lxml")
        score, reason = analyzer._analyze_code_density(soup, "python tutorial")

        assert score > 0
        assert "code" in reason.lower()

    def test_analyze_code_density_no_code(self):
        """Test code density analysis with HTML containing no code."""
        html_no_code = "<html><body><p>This is just plain text content.</p></body></html>"
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(html_no_code, "lxml")
        score, reason = analyzer._analyze_code_density(soup, "plain text")

        assert score == 0
        assert reason == ""

    def test_analyze_data_density_with_tables(self, sample_html):
        """Test data density analysis with HTML containing tables."""
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(sample_html, "lxml")
        score, reason = analyzer._analyze_data_density(soup)

        assert score > 0
        assert "table" in reason.lower()

    def test_analyze_data_density_no_tables(self):
        """Test data density analysis with HTML containing no tables."""
        html_no_tables = "<html><body><p>No tables here.</p></body></html>"
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(html_no_tables, "lxml")
        score, reason = analyzer._analyze_data_density(soup)

        assert score == 0
        assert reason == ""

    def test_detect_slop_high_ratio(self):
        """Test slop detection with high HTML-to-text ratio."""
        # Create HTML with lots of markup and very little text (ratio > 20)
        # Each div has many attributes and nested tags, creating high bloat
        bloated_div = '<div class="container wrapper main" id="div1" data-test="value" style="display:block"><span class="label" data-attr="val"><em class="italic" style="color:red"><strong class="bold"><a href="#" class="link" id="link1" data-track="yes" target="_blank" rel="nofollow">click</a></strong></em></span></div>'
        bloated_html = bloated_div * 50
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(bloated_html, "lxml")
        score, reason = analyzer._detect_slop(bloated_html, soup)

        assert score < 0
        assert "bloated" in reason.lower() or "ratio" in reason.lower()

    def test_detect_slop_clean_content(self):
        """Test slop detection with clean, text-focused content."""
        # Long text with minimal markup should get positive score
        clean_html = "<html><body><p>" + "This is clean text content. " * 20 + "</p></body></html>"
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(clean_html, "lxml")
        score, reason = analyzer._detect_slop(clean_html, soup)

        assert score >= 0

    def test_detect_slop_no_text(self):
        """Test slop detection with HTML containing no readable text."""
        no_text_html = "<html><body>" + "<img src='test.jpg'>" * 10 + "<script>alert('test');</script></body></html>"
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(no_text_html, "lxml")
        score, reason = analyzer._detect_slop(no_text_html, soup)

        assert score < 0
        assert "readable text" in reason.lower()

    def test_detect_affiliates_with_affiliate_links(self):
        """Test affiliate detection with affiliate links."""
        html_with_affiliates = """
        <html><body>
        <a href="amzn.to/test">Buy now</a>
        <a href="shareasale.com/aff">Affiliate link</a>
        <a href="example.com/normal">Normal link</a>
        </body></html>
        """
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(html_with_affiliates, "lxml")
        score, reason = analyzer._detect_affiliates(soup)

        assert score < 0
        assert "affiliate" in reason.lower()

    def test_detect_affiliates_no_affiliate_links(self, sample_html):
        """Test affiliate detection with no affiliate links."""
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(sample_html, "lxml")
        score, reason = analyzer._detect_affiliates(soup)

        assert score == 0
        assert reason == ""

    def test_detect_hype_with_hype_title(self):
        """Test hype detection with clickbait title."""
        html_hype = "<html><head><title>You won't believe this shocking secret!</title></head><body></body></html>"
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(html_hype, "lxml")
        score, reason = analyzer._detect_hype(soup)

        assert score < 0
        assert "clickbait" in reason.lower() or "hype" in reason.lower()

    def test_detect_hype_with_hype_h1(self):
        """Test hype detection with clickbait H1."""
        html_hype = "<html><body><h1>Mind-blowing revolutionary breakthrough!</h1></body></html>"
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(html_hype, "lxml")
        score, reason = analyzer._detect_hype(soup)

        assert score < 0
        assert "headline" in reason.lower() or "hype" in reason.lower()

    def test_detect_hype_no_hype(self, sample_html):
        """Test hype detection with normal title."""
        analyzer = HeuristicAnalyzer()
        soup = BeautifulSoup(sample_html, "lxml")
        score, reason = analyzer._detect_hype(soup)

        assert score == 0
        assert reason == ""

    def test_calculate_structure_score_adjustments(self, sample_html):
        """Test that adjustments are properly tracked."""
        analyzer = HeuristicAnalyzer()
        result = analyzer.calculate_structure_score(sample_html, "machine learning")

        assert "adjustments" in result
        assert isinstance(result["adjustments"], list)

        # Each adjustment should be a tuple of (score_change, reason)
        for adjustment in result["adjustments"]:
            assert isinstance(adjustment, tuple)
            assert len(adjustment) == 2
            assert isinstance(adjustment[0], int)
