from app.core.api_keys import generate_api_key, extract_key_prefix, hash_api_key


def test_generate_api_key_has_expected_format():
    api_key, prefix = generate_api_key()

    assert api_key.startswith("sp_live_")
    assert prefix == api_key[:16]
    assert len(api_key) > 30


def test_hash_api_key_is_deterministic():
    key = "sp_live_test_key_123"

    first_hash = hash_api_key(key)
    second_hash = hash_api_key(key)

    assert first_hash == second_hash
    assert first_hash != key
    assert len(first_hash) == 64


def test_different_keys_have_different_hashes():
    first_hash = hash_api_key("sp_live_key_one")
    second_hash = hash_api_key("sp_live_key_two")

    assert first_hash != second_hash


def test_extract_key_prefix():
    key = "sp_live_abcdefghijklmnopqrstuvwxyz"

    prefix = extract_key_prefix(key)

    assert prefix == key[:16]