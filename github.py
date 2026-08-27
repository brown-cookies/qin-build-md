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


# Add this one, for the clean request handler instead of mutating it directly to the function
RequestResult = SuccessRepo | ErrorRepo


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


def _get_response_json(response: requests.Response) -> dict | None:
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        return None


def _handle_success_fetch(response: requests.Response, owner: str, repo: str) -> RequestResult:
    data = _get_response_json(response)

    if not isinstance(data, dict):
        return ErrorRepo(
            status_code=response.status_code,
            error_type=RepoMessage.GITHUB_ERROR,
            repo=repo,
            owner=owner,
            message="Success 200 status code but body is not an instance of JSON.",
        )

    return SuccessRepo(
        status_code=response.status_code,
        repo=repo,
        owner=owner,
        description=data.get(
            "description") or "(No description.)",
        starred_count=data.get("stargazers_count", 0),
        message="Repository found.",
    )


def _handle_user_error_fetch(response: requests.Response, owner: str, repo: str) -> RequestResult:
    if response.status_code == 404:
        error_type = RepoMessage.NOT_FOUND
        message = f"'{owner}/{repo}' does not exist."
    else:
        error_type = RepoMessage.BAD_REQUEST
        data = _get_response_json(response)
        message = data.get("message", "Bad request") if isinstance(data, dict) else \
            "Bad request (response body is not an instance of JSON)."

    return ErrorRepo(
        status_code=response.status_code,
        error_type=error_type,
        repo=repo,
        owner=owner,
        message=message,
    )


def _handle_server_error_fetch(response: requests.Response, owner: str, repo: str) -> RequestResult:
    return ErrorRepo(
        status_code=response.status_code,
        error_type=RepoMessage.GITHUB_ERROR,
        repo=repo,
        owner=owner,
        message="Something went wrong on the Server!",
    )


def _handle_network_error_fetch(e: requests.exceptions.RequestException, owner: str, repo: str) -> RequestResult:
    if isinstance(e, requests.exceptions.ConnectTimeout):
        message = "Connection timed out."
    elif isinstance(e, requests.exceptions.ReadTimeout):
        message = "Response timed out."
    elif isinstance(e, requests.exceptions.SSLError):
        message = "Secure connection to GitHub failed."
    elif isinstance(e, requests.exceptions.ConnectionError):
        message = "Could not connect to GitHub."
    else:
        message = "Network request failed."

    return ErrorRepo(
        status_code=-1,
        error_type=RepoMessage.NETWORK_ERROR,
        repo=repo,
        owner=owner,
        message=message,
    )


def _handle_unmatch_status_code_fetch(response: requests.Response, owner: str, repo: str) -> RequestResult:
    return ErrorRepo(
        status_code=response.status_code,
        error_type=RepoMessage.UNMATCH_STATUS,
        repo=repo,
        owner=owner,
        message=f"Status code {response.status_code} not one Http status code outcomes for this endpoint. 200, 301, 403, 404",
    )


def _is_being_rate_limited(headers: CaseInsensitiveDict[str]):
    remaining = headers.get('X-RateLimit-Remaining')

    if remaining is None:
        return False

    return int(remaining) == 0


def _handle_rate_limited_fetch(response: requests.Response, owner: str, repo: str) -> RequestResult:
    reset = response.headers.get("X-RateLimit-Reset")
    return ErrorRepo(
        status_code=response.status_code,
        error_type=RepoMessage.RATE_LIMITED,
        repo=repo,
        owner=owner,
        message=f"Resetting at {reset}." if reset else "You hit the limit.",
    )


def classify_response(repos: list[tuple[str, str]]) -> list[RequestResult]:
    results: list[RequestResult] = []

    for (owner, repo) in repos:
        response = fetch_repo(owner, repo)

        if isinstance(response, requests.exceptions.RequestException):
            result = _handle_network_error_fetch(response, owner, repo)
            results.append(result)
            continue

        if response.status_code == 200:
            result = _handle_success_fetch(response, owner, repo)
            results.append(result)
        elif response.status_code >= 400 and response.status_code < 500:
            if response.status_code == 403 and _is_being_rate_limited(response.headers):
                result = _handle_rate_limited_fetch(response, owner, repo)
                results.append(result)
            else:
                result = _handle_user_error_fetch(response, owner, repo)
                results.append(result)

        elif response.status_code >= 500:
            result = _handle_server_error_fetch(response, owner, repo)
            results.append(result)

        else:
            result = _handle_unmatch_status_code_fetch(
                response, owner, repo)
            results.append(result)

    return results


def _print_success(success_repos: list[SuccessRepo]) -> None:
    print("SUCCESS")
    print(f"  {'STATUS':6}  {'REPO':35}  {'STARS':>6}  {'DESCRIPTION'}")
    for r in success_repos:
        print(
            f"  [{r.status_code}]  {r.owner + '/' + r.repo:35}  "
            f"{r.starred_count:6d}  "
            f"{r.description}"
        )


def _print_errors(error_repos: list[ErrorRepo]) -> None:
    print("ERROR")
    print(f"  {'STATUS':6}  {'REPO':35}  {'TYPE':12}  {'MESSAGE'}")
    for e in error_repos:
        print(
            f"  [{e.status_code}]  {e.owner + '/' + e.repo:35}  "
            f"{e.error_type.value:12}  "
            f"{e.message}"
        )


def print_results(results: list[RequestResult]) -> None:
    success_repos = [r for r in results if isinstance(r, SuccessRepo)]
    error_repos = [r for r in results if isinstance(r, ErrorRepo)]

    _print_success(success_repos)
    _print_errors(error_repos)

    print(f"  total entered: {len(results)}")
    print(f"  succeeded: {len(success_repos)}")
    print(f"  failed: {len(error_repos)}")


def main() -> None:
    """ Bootstrap the entire Build Section """
    print("Github API Link: ", GITHUB_API)

    if len(sys.argv) < 2:
        print("usage: py github.py owner/repo ...")
        sys.exit(1)

    repo_list = get_owner_repo(sys.argv[1:])

    results = classify_response(repo_list)
    print_results(results)


if __name__ == "__main__":
    main()
