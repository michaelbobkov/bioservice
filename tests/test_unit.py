import pytest
from pydantic import ValidationError

from app.main import ALPHABET, LinkIn, make_code


def test_make_code_length_and_alphabet():
    code = make_code()
    assert len(code) == 7 and set(code) <= set(ALPHABET)


def test_codes_differ():
    assert len({make_code() for _ in range(100)}) == 100


def test_url_validation():
    LinkIn(url="https://example.com/x")
    with pytest.raises(ValidationError):
        LinkIn(url="javascript:alert(1)")
