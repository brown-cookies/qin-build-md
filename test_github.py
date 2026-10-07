from github import (
    RepoMessage,
    arg_to_owner_repo,
    get_owner_repo,
    _is_being_rate_limited,
)
from requests.structures import CaseInsensitiveDict
import pytest


def test_arg_to_owner_repo():
    owner, repo = arg_to_owner_repo("octocat/Hello-World")

    assert owner == "octocat"
    assert repo == "Hello-World"


def test_arg_to_owner_repo_should_raise_value_error():
    with pytest.raises(ValueError):
        arg_to_owner_repo("facebook")


def test_get_owner_repo():
    repos, errors = get_owner_repo([
        "octocat/Hello-World",
        "torvalds/linux",
        "microsoft/vscode",
        "facebook/react",
        "python/cpython",
    ])

    assert repos == [
        ("octocat", "Hello-World"),
        ("torvalds", "linux"),
        ("microsoft", "vscode"),
        ("facebook", "react"),
        ("python", "cpython"),
    ]
    assert len(errors) == 0


def test_is_being_rate_limited():
    headers = CaseInsensitiveDict({
        "X-RateLimit-Remaining": "0"
    })

    assert _is_being_rate_limited(headers) is True
