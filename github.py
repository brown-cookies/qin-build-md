import sys
from dataclasses import dataclass
from enum import Enum
from typing import Final

import requests
from requests.structures import CaseInsensitiveDict

""" Testing 5 repos
# Working Repo
octocat/Hello-World
torvalds/linux
microsoft/vscode
facebook/react
python/cpython

# Non-existant Repo
octocat/this-repo-definitely-does-not-exist-123456789
this-user-definitely-does-not-exist-987654321/fake-repo

Invalid Format
facebook
microsoft\vscode
"""


GITHUB_API: Final[str] = "https://api.github.com/repos"
REQUEST_TIMEOUT: Final[int] = 10


class RepoMessage(Enum):
    SUCCESS = "SUCCESS"
    NOT_FOUND = "NOT FOUND"
    BAD_REQUEST = "BAD REQUEST"
    GITHUB_ERROR = "GITHUB ERROR"
    RATE_LIMITED = "RATE LIMITED"
    NETWORK_ERROR = "NETWORK ERROR"
    UNMATCH_STATUS = "UNMATCH STATUS"


@dataclass
class ErrorRepo:
    # Status code of the response, return -1 if network error
    status_code: int
    error_type: RepoMessage
    repo: str
    owner: str
    message: str


@dataclass
class SuccessRepo:
    status_code: int
    repo: str
    owner: str
    description: str
    starred_count: int
    message: str


def arg_to_owner_repo(arg: str) -> tuple[str, str]:
    """Converts the list input into readable variable."""
    if "/" not in arg:
        raise ValueError(f"Wrong format: '{arg}' — use owner/repo.")
    owner, name = arg.split("/", 1)
    if not owner or not name:
        raise ValueError(f"Wrong format: '{arg}' — use owner/repo.")
    return owner, name


def get_owner_repo(argv: list[str]) -> list[tuple[str, str]]:
    repo_list: list[tuple[str, str]] = []
    for arg in argv:
        owner, repo = arg_to_owner_repo(arg)
        repo_list.append((owner, repo))
    return repo_list


def fetch_repo(owner: str, repo: str) -> requests.Response | requests.exceptions.RequestException:
    """"""
    query = f"{GITHUB_API}/{owner}/{repo}"

    try:
        return requests.get(
            query,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException as e:
        return e


def _handle_success_fetch(response: requests.Response, owner: str, repo: str, SUCCESS_REPO_LIST: list[SuccessRepo]):
    data = response.json()
    SUCCESS_REPO_LIST.append(
        SuccessRepo(
            status_code=response.status_code,
            repo=repo,
            owner=owner,
            description=data.get(
                "description") or "(This retard is rather lazy and didn't provide description.)",
            starred_count=data.get("stargazers_count", 0),
            message="Repository found.",
        )
    )


def _handle_user_error_fetch(response: requests.Response, owner: str, repo: str, ERROR_REPO_LIST: list[ErrorRepo]):
    if response.status_code == 404:
        error_type = RepoMessage.NOT_FOUND
        message = f"'Bro, {owner}/{repo}' is does not exist, or Private? we don't know."
    else:
        error_type = RepoMessage.BAD_REQUEST
        message = response.json().get("message", "Bad request")

    ERROR_REPO_LIST.append(
        ErrorRepo(
            status_code=response.status_code,
            error_type=error_type,
            repo=repo,
            owner=owner,
            message=message,
        )
    )


def _handle_server_error_fetch(response: requests.Response, owner: str, repo: str, ERROR_REPO_LIST: list[ErrorRepo]):
    ERROR_REPO_LIST.append(
        ErrorRepo(
            status_code=response.status_code,
            error_type=RepoMessage.GITHUB_ERROR,
            repo=repo,
            owner=owner,
            message="Mwehehe, This Tech giant github had an internal error handling this request.",
        )
    )


def _handle_network_error_fetch(e: requests.exceptions.RequestException, owner: str, repo: str, ERROR_REPO_LIST: list[ErrorRepo]):
    ERROR_REPO_LIST.append(
        ErrorRepo(
            status_code=-1,
            error_type=RepoMessage.NETWORK_ERROR,
            repo=repo,
            owner=owner,
            message=f"{type(e).__name__}: {e}"
        )
    )


def _handle_unmatch_status_code_fetch(response: requests.Response, owner: str, repo: str, ERROR_REPO_LIST: list[ErrorRepo]):
    ERROR_REPO_LIST.append(
        ErrorRepo(
            status_code=response.status_code,
            error_type=RepoMessage.UNMATCH_STATUS,
            repo=repo,
            owner=owner,
            message=f"Status code {response.status_code} not one Http status code outcomes for this endpoint. 200, 301, 403, 404",
        )
    )


def _is_being_rate_limited(headers: CaseInsensitiveDict[str]):
    remaining = headers.get('X-RateLimit-Remaining')

    if remaining is None:
        return False

    return int(remaining) == 0


def _handle_rate_limited_fetch(response: requests.Response, owner: str, repo: str, ERROR_REPO_LIST: list[ErrorRepo]):
    reset = response.headers.get("X-RateLimit-Reset")
    ERROR_REPO_LIST.append(
        ErrorRepo(
            status_code=response.status_code,
            error_type=RepoMessage.RATE_LIMITED,
            repo=repo,
            owner=owner,
            message=f"Resetting at {reset}." if reset else "Bro hit the rate.",
        )
    )


def classify_response(repos: list[tuple[str, str]], SUCCESS_REPO_LIST: list[SuccessRepo], ERROR_REPO_LIST: list[ErrorRepo]):

    for (owner, repo) in repos:
        response = fetch_repo(owner, repo)

        if isinstance(response, requests.exceptions.RequestException):
            _handle_network_error_fetch(response, owner, repo, ERROR_REPO_LIST)
            continue

        if response.status_code == 200:
            _handle_success_fetch(response, owner, repo, SUCCESS_REPO_LIST)
        elif response.status_code >= 400 and response.status_code < 500:
            if response.status_code == 403 and _is_being_rate_limited(response.headers):
                _handle_rate_limited_fetch(
                    response, owner, repo, ERROR_REPO_LIST)
            else:
                _handle_user_error_fetch(
                    response, owner, repo, ERROR_REPO_LIST)
        elif response.status_code >= 500:
            _handle_server_error_fetch(response, owner, repo, ERROR_REPO_LIST)
        else:
            _handle_unmatch_status_code_fetch(
                response, owner, repo, ERROR_REPO_LIST)


def _print_success(SUCCESS_REPO_LIST: list[SuccessRepo]) -> None:
    print("SUCCESS")
    print(f"  {'STATUS':6}  {'REPO':35}  {'STARS':>6}  {'DESCRIPTION'}")
    for r in SUCCESS_REPO_LIST:
        print(
            f"  [{r.status_code}]  {r.owner + '/' + r.repo:35}  "
            f"{r.starred_count:6d}  "
            f"{r.description}"
        )


def _print_errors(ERROR_REPO_LIST: list[ErrorRepo]) -> None:
    print("ERRORS")
    print(f"  {'STATUS':6}  {'REPO':35}  {'TYPE':12}  {'MESSAGE'}")
    for e in ERROR_REPO_LIST:
        print(
            f"  [{e.status_code}]  {e.owner + '/' + e.repo:35}  "
            f"{e.error_type.value:12}  "
            f"{e.message}"
        )


def print_result(SUCCESS_REPO_LIST: list[SuccessRepo], ERROR_REPO_LIST: list[ErrorRepo]) -> None:
    _print_success(SUCCESS_REPO_LIST)
    _print_errors(ERROR_REPO_LIST)

    print(f"  total entered: {len(SUCCESS_REPO_LIST) + len(ERROR_REPO_LIST)}")
    print(f"  succeeded: {len(SUCCESS_REPO_LIST)}")
    print(f"  failed: {len(ERROR_REPO_LIST)}")


def main() -> None:
    """ Bootstrap the entire Build Section """
    print("Github API Link: ", GITHUB_API)

    if len(sys.argv) < 2:
        print("usage: py github.py owner/repo ...")
        sys.exit(1)

    repo_list = get_owner_repo(sys.argv[1:])

    SUCCESS_REPO_LIST: list[SuccessRepo] = []
    ERROR_REPO_LIST: list[ErrorRepo] = []

    classify_response(repo_list, SUCCESS_REPO_LIST, ERROR_REPO_LIST)
    print_result(SUCCESS_REPO_LIST, ERROR_REPO_LIST)


if __name__ == "__main__":
    main()
