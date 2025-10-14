from devscape.ollama_ai import _extract_stream_contents, _safe_unescape

# def test_extract_stream_contents_empty_string():
#     assert _extract_stream_contents("") == ""

# def test_extract_stream_contents_simple_json_line():
#     raw = '{"message": {"content": "hello from AI"}}'
#     assert _extract_stream_contents(raw) == "hello from AI"

# def test_extract_stream_contents_top_level_content_json_line():
#     raw = '{"content": "just content"}'
#     assert _extract_stream_contents(raw) == "just content"


def test_extract_stream_contents_multiple_json_lines():
    raw = '{"message": {"content": "first part"}}\n{"message": {"content": "second part"}}'
    assert _extract_stream_contents(raw) == "first partsecond part"


def test_extract_stream_contents_escaped_newline():
    raw = '{"message": {"content": "line1\nline2"}}'
    assert _extract_stream_contents(raw) == "line1\nline2"


def test_extract_stream_contents_escaped_quote():
    raw = r'{"message": {"content": "He said \"hello\""}}'
    assert _extract_stream_contents(raw) == 'He said "hello"'


def test_extract_stream_contents_with_xa0_and_multiple_spaces():
    raw = '{"message": {"content": "  hello\xa0world   "}}'
    assert _extract_stream_contents(raw) == "hello world"


def test_extract_stream_contents_with_surrounding_single_quotes():
    raw = '\'{"message": {"content": "quoted content"}}\''
    assert _extract_stream_contents(raw) == "quoted content"


def test_extract_stream_contents_with_surrounding_double_quotes():
    raw = '"{"message": {"content": "double quoted content"}}"'
    assert _extract_stream_contents(raw) == "double quoted content"


def test_extract_stream_contents_regex_fallback_single_line():
    # This simulates a case where json.loads fails but the regex can still find content
    raw = 'some text before "content": "regex content" some text after'
    assert _extract_stream_contents(raw) == "regex content"


def test_extract_stream_contents_regex_fallback_entire_text():
    # If no JSON lines and no per-line regex match, try on the whole text
    raw = 'This is some raw text with "content": "fallback content" inside.'
    assert _extract_stream_contents(raw) == "fallback content"


def test_extract_stream_contents_no_content_found():
    raw = '{"message": {"role": "assistant"}}'  # No content field
    assert _extract_stream_contents(raw) == ""


def test_extract_stream_contents_empty_content_field():
    raw = '{"message": {"content": ""}}'
    assert _extract_stream_contents(raw) == ""


def test_extract_stream_contents_with_data_field():
    raw = '{"data": {"content": "data field content"}}'
    assert _extract_stream_contents(raw) == "data field content"


def test_extract_stream_contents_with_text_field():
    raw = '{"message": {"text": "text field"}}'
    assert _extract_stream_contents(raw) == "text field"


def test_extract_stream_contents_with_top_level_text_field():
    raw = '{"text": "top level text content"}'
    assert _extract_stream_contents(raw) == "top level text content"


def test_extract_stream_contents_with_unicode_characters():
    raw = '{"message": {"content": "你好世界"}}'
    assert _extract_stream_contents(raw) == "你好世界"


def test_extract_stream_contents_with_unicode_escape_sequences():
    raw = '{"message": {"content": "Hello\u0020World"}}'
    assert _extract_stream_contents(raw) == "Hello World"


# Tests for _safe_unescape
def test_safe_unescape_surrounding_single_quotes():
    assert _safe_unescape("'hello'") == "'hello'"


def test_safe_unescape_surrounding_double_quotes():
    assert _safe_unescape('"hello"') == '"hello"'


def test_safe_unescape_no_surrounding_quotes():
    assert _safe_unescape("hello") == "hello"


def test_safe_unescape_literal_escapes():
    assert _safe_unescape("line1\nline2") == "line1\nline2"
    assert _safe_unescape('He said "hello"') == 'He said "hello"'
    assert _safe_unescape("path\to\file") == "path\to\file"


def test_safe_unescape_unicode_escape():
    assert _safe_unescape("Hello\u0020World") == "Hello World"


def test_safe_unescape_mixed_escapes():
    assert (
        _safe_unescape("'line1\nline2\u0020with\"quotes\"'")
        == "'line1\nline2 with\"quotes\"'"
    )


def test_safe_unescape_invalid_unicode_escape():
    # Should not raise an error, but return the string as is or best effort
    assert _safe_unescape(r"invalid\uXXXXescape") == r"invalid\uXXXXescape"


def test_safe_unescape_empty_string():
    assert _safe_unescape("") == ""


def test_extract_stream_contents_non_string_content_field():
    raw = '{"message": {"content": 123}}'  # content is an int, not a string
    assert _extract_stream_contents(raw) == ""


def test_extract_stream_contents_invalid_json_raises_exception():
    raw = "{invalid json}"
    assert _extract_stream_contents(raw) == ""


def test_extract_stream_contents_no_json_no_regex_match():
    raw = "plain text without content field"
    assert _extract_stream_contents(raw) == ""


def test_safe_unescape_decode_error():
    raw_input = r"abc\x"
    assert _safe_unescape(raw_input) == raw_input
