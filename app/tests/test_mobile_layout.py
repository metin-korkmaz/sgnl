"""
Test frontend and CSS changes for mobile layout.

Tests verify:
- Marquee is hidden on mobile breakpoint
- Sections (manifesto, comparison, features) are visible on mobile
- Nav layout uses flex-direction: row on mobile
- Desktop nav links are hidden on mobile
- All features work correctly on desktop as well
"""

import pytest
import os
from pathlib import Path


class TestMobileLayoutCSS:
    """Test CSS mobile layout changes."""

    @pytest.fixture
    def css_path(self):
        """Path to main.css file."""
        return Path(__file__).parent.parent / "static" / "css" / "main.css"

    @pytest.fixture
    def css_content(self, css_path):
        """Load CSS file content."""
        with open(css_path, 'r') as f:
            return f.read()

    def test_marquee_hidden_on_mobile(self, css_content):
        """Test that marquee is hidden on mobile breakpoint (max-width: 768px)."""
        # Find all mobile media query sections
        mobile_queries = [m for m in css_content.split("@media (max-width: 768px)") if m]

        found_marquee_hidden = False

        for mobile_section in mobile_queries:
            # Find next media query to limit scope
            next_media = mobile_section.find("@media")
            section_content = mobile_section[:next_media] if next_media != -1 else mobile_section

            # Check if marquee is hidden in this section
            if ".marquee" in section_content and "display: none" in section_content:
                found_marquee_hidden = True
                break

        assert found_marquee_hidden, "Marquee should be hidden with display: none in mobile breakpoint"

    def test_sections_visible_on_mobile(self, css_content):
        """Test that manifesto, comparison, and features sections are NOT hidden on mobile."""
        # Search for section hiding patterns that should NOT exist
        assert "manifesto-section" not in css_content or "display: none" not in css_content.split("manifesto-section")[0] \
            or "manifesto-section" not in css_content.split("display: none")[0], \
            "manifesto-section should not be hidden on mobile"

        # Check that the sections don't have display: none in mobile queries
        mobile_queries = css_content.split("@media (max-width: 768px)")

        if len(mobile_queries) > 1:
            # Get the content after the first mobile query
            first_mobile = mobile_queries[1]
            # Find the next media query
            next_media = first_mobile.find("@media")
            mobile_content = first_mobile[:next_media] if next_media != -1 else first_mobile

            # Verify sections are not hidden
            assert "manifesto-section" not in mobile_content or "display: none" not in mobile_content.split("manifesto-section")[0], \
                "manifesto-section should not be hidden in mobile query"

            assert "comparison-section" not in mobile_content or "display: none" not in mobile_content.split("comparison-section")[0], \
                "comparison-section should not be hidden in mobile query"

            assert "features-section" not in mobile_content or "display: none" not in mobile_content.split("features-section")[0], \
                "features-section should not be hidden in mobile query"

    def test_nav_row_layout_on_mobile(self, css_content):
        """Test that nav uses flex-direction: row on mobile."""
        # Find mobile media queries
        mobile_queries = [m for m in css_content.split("@media (max-width: 768px)") if m]

        found_nav_row = False

        for mobile_section in mobile_queries:
            # Find next media query to limit scope
            next_media = mobile_section.find("@media")
            section_content = mobile_section[:next_media] if next_media != -1 else mobile_section

            if ".nav" in section_content and "flex-direction: row" in section_content:
                found_nav_row = True
                break

        assert found_nav_row, "Nav should use flex-direction: row in mobile breakpoint"

    def test_nav_desktop_links_hidden_on_mobile(self, css_content):
        """Test that desktop nav links are hidden on mobile."""
        # Find mobile media queries
        mobile_queries = [m for m in css_content.split("@media (max-width: 768px)") if m]

        for mobile_section in mobile_queries:
            # Find next media query to limit scope
            next_media = mobile_section.find("@media")
            section_content = mobile_section[:next_media] if next_media != -1 else mobile_section

            if ".nav-links" in section_content:
                # Verify nav-links have display: none
                assert "display: none" in section_content, \
                    "nav-links should be hidden on mobile"

    def test_mobile_github_button_visible_on_mobile(self, css_content):
        """Test that mobile GitHub button is visible on mobile."""
        # Find mobile media queries
        mobile_queries = [m for m in css_content.split("@media (max-width: 768px)") if m]

        for mobile_section in mobile_queries:
            # Find next media query to limit scope
            next_media = mobile_section.find("@media")
            section_content = mobile_section[:next_media] if next_media != -1 else mobile_section

            if ".mobile-github-link" in section_content:
                # Verify it's visible (not display: none)
                # We check that it has display: block or inline-block
                assert "display:" in section_content, \
                    "mobile-github-link should have display property"
                assert "block" in section_content or "inline-block" in section_content, \
                    "mobile-github-link should be visible on mobile"

    def test_nav_justify_space_between_on_mobile(self, css_content):
        """Test that nav uses justify-content: space-between on mobile."""
        # Find mobile media queries
        mobile_queries = [m for m in css_content.split("@media (max-width: 768px)") if m]

        for mobile_section in mobile_queries:
            # Find next media query to limit scope
            next_media = mobile_section.find("@media")
            section_content = mobile_section[:next_media] if next_media != -1 else mobile_section

            if ".nav" in section_content and "justify-content:" in section_content:
                # Verify justify-content is space-between
                assert "justify-content: space-between" in section_content, \
                    "Nav should use justify-content: space-between on mobile"

    def test_desktop_layout_not_broken(self, css_content):
        """Test that desktop layout is not broken by mobile changes."""
        # Find desktop media queries
        desktop_queries = [m for m in css_content.split("@media (min-width: 769px)") if m]

        assert len(desktop_queries) > 0, "Should have desktop media query"

        for desktop_section in desktop_queries:
            # Find next media query to limit scope
            next_media = desktop_section.find("@media")
            section_content = desktop_section[:next_media] if next_media != -1 else desktop_section

            # Verify nav-links are visible on desktop
            if ".nav-links" in section_content:
                assert "display: flex" in section_content, \
                    "nav-links should be visible on desktop"

            # Verify mobile GitHub button is hidden on desktop
            if ".mobile-github-link" in section_content:
                assert "display: none" in section_content, \
                    "mobile-github-link should be hidden on desktop"

    def test_responsive_breakpoints_exist(self, css_content):
        """Test that responsive breakpoints are defined."""
        # Check for common breakpoints
        assert "@media (max-width: 768px)" in css_content, \
            "Should have mobile breakpoint at 768px"
        assert "@media (min-width: 769px)" in css_content, \
            "Should have desktop breakpoint at 769px"


class TestHTMLStructure:
    """Test HTML structure for mobile layout."""

    @pytest.fixture
    def html_path(self):
        """Path to index.html file."""
        return Path(__file__).parent.parent / "templates" / "index.html"

    @pytest.fixture
    def html_content(self, html_path):
        """Load HTML file content."""
        with open(html_path, 'r') as f:
            return f.read()

    def test_marquee_element_exists(self, html_content):
        """Test that marquee element exists in HTML."""
        assert '<div class="marquee">' in html_content, \
            "Marquee element should exist in HTML"

    def test_nav_has_logo_and_github_button(self, html_content):
        """Test that nav has both logo and GitHub button elements."""
        assert '<div class="logo">SGNL</div>' in html_content, \
            "Nav should have SGNL logo"

        assert 'class="mobile-github-link"' in html_content, \
            "Nav should have mobile GitHub button"

    def test_nav_has_desktop_links(self, html_content):
        """Test that nav has desktop navigation links."""
        assert '<div class="nav-links">' in html_content, \
            "Nav should have desktop nav-links container"
        assert 'href="#search">Scan</a>' in html_content, \
            "Should have Scan link"
        assert 'href="#manifesto">Manifesto</a>' in html_content, \
            "Should have Manifesto link"
        assert 'href="#comparison">Compare</a>' in html_content, \
            "Should have Compare link"

    def test_sections_exist(self, html_content):
        """Test that all sections exist in HTML."""
        assert 'id="search"' in html_content, \
            "Search section should exist"
        assert 'id="manifesto"' in html_content, \
            "Manifesto section should exist"
        assert 'id="comparison"' in html_content, \
            "Comparison section should exist"
        assert 'id="features"' in html_content, \
            "Features section should exist"

    def test_results_section_exists(self, html_content):
        """Test that results section exists."""
        assert 'id="results-section"' in html_content, \
            "Results section should exist"
        assert 'results-section' in html_content, \
            "Results section should have results-section class (can be combined with modifiers)"

    def test_ai_analysis_section_exists(self, html_content):
        """Test that AI analysis section exists."""
        assert 'id="ai-analysis"' in html_content, \
            "AI analysis section should exist"

    def test_mobile_github_link_has_correct_attributes(self, html_content):
        """Test that mobile GitHub link has correct attributes."""
        assert 'class="mobile-github-link"' in html_content, \
            "Mobile GitHub link should have correct class"
        assert 'target="_blank"' in html_content, \
            "Mobile GitHub link should open in new tab"
        assert 'rel="noopener"' in html_content, \
            "Mobile GitHub link should have noopener rel"


class TestCSSIntegration:
    """Test CSS integration with HTML."""

    def test_css_file_exists(self):
        """Test that CSS file exists."""
        css_path = Path(__file__).parent.parent / "static" / "css" / "main.css"
        assert css_path.exists(), "CSS file should exist"

    def test_css_file_readable(self):
        """Test that CSS file is readable."""
        css_path = Path(__file__).parent.parent / "static" / "css" / "main.css"
        with open(css_path, 'r') as f:
            content = f.read()
        assert len(content) > 0, "CSS file should have content"

    def test_html_file_exists(self):
        """Test that HTML file exists."""
        html_path = Path(__file__).parent.parent / "templates" / "index.html"
        assert html_path.exists(), "HTML file should exist"

    def test_html_links_css(self):
        """Test that HTML correctly links to CSS file."""
        html_path = Path(__file__).parent.parent / "templates" / "index.html"
        with open(html_path, 'r') as f:
            content = f.read()
        assert 'href="/static/css/main.css' in content, \
            "HTML should link to main.css"
