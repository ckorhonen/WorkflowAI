from core.domain.errors import InvalidFileError


def test_instantiate_invalid_file_error():
    error = InvalidFileError()
    assert error
