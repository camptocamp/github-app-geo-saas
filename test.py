import argparse
import subprocess
import sys

from github import Github, GithubIntegration
from github.Auth import AppAuth


def _main():
    parser = argparse.ArgumentParser(
        """
        pip install pygithub

        test with: python test.py --app-id="$(gopass show private/2fa/github/app-geo-saas-int/app-id)" --private-key="$(gopass show private/2fa/github/app-geo-saas-int/private-key)"
        """
    )
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--private-key", required=True)
    args = parser.parse_args()

    # print(args.app_id)
    # print(args.private_key)

    app_auth = AppAuth(args.app_id, args.private_key)
    git_integration = GithubIntegration(auth=app_auth)

    print(app_auth)
    print(git_integration)
    print(git_integration.get_app())
    print(git_integration.get_app().slug + "[bot]")

    print("=== get repos ===")
    for i in git_integration.get_installations():
        # print(i)
        print(i.app_id)
        # print(i.id)
        # print(i.target_id)
        # print(i.target_type)
        for repo in i.get_repos():
            print(repo)

    token = git_integration.get_access_token(
        git_integration.get_installation("sbrunner", "test-github-app").id
    ).token
    print(token)

    subprocess.run(
        ["git", "clone", f"https://x-access-token:{token}@github.com/sbrunner/test-github-app.git"],
        cwd="/tmp",
    )
    results = ["/tmp/test-github-app"]

    # Docker is not working
    # subprocess.run(
    #     ["docker", "login", "ghcr.io", "--username=x-access-token", "--password-stdin"], input=token.encode()
    # )
    # subprocess.run(["docker", "pull", "redis"])
    # subprocess.run(
    #     [
    #         "docker",
    #         "tag",
    #         "redis",
    #         "ghcr.io/camptocamp/github-app-geo-saas:test1234",
    #     ]
    # )
    # subprocess.run(["docker", "push", "ghcr.io/camptocamp/github-app-geo-saas:test1234"])
    # subprocess.run(["skopeo", "list-tags", "docker://ghcr.io/camptocamp/github-app-geo-saas"])
    # results.append("skopeo list-tags docker://ghcr.io/camptocamp/github-app-geo-saas")
    #
    # subprocess.run(
    #     [
    #         "docker",
    #         "tag",
    #         "redis",
    #         "ghcr.io/sbrunner/test-github-app:test1234",
    #     ]
    # )
    # subprocess.run(["docker", "push", "ghcr.io/sbrunner/test-github-app:test1234"])
    # subprocess.run(["skopeo", "list-tags", "docker://ghcr.io/sbrunner/test-github-app"])
    # results.append("skopeo list-tags docker://ghcr.io/sbrunner/test-github-app")

    print("\n".join(results))
    exit(0)

    app = Github(login_or_token=token)

    repo = app.get_repo("sbrunner/test-github-app")

    print("=== repo ===" * 4)
    print(repo.default_branch)
    print(repo.get_branch(repo.default_branch).commit.sha)

    file_ = repo.get_contents("README.md")
    print(file_)
    print("---")
    #    print(file_.content)
    print(file_.decoded_content)
    #    print(file_.raw_data)
    print("---")

    def list_files(path):
        for f in repo.get_contents(path):
            print(f.path)
            if f.type == "dir":
                list_files(f.path)

    list_files("/")
    print("---")

    print(list(repo.get_workflows()))

    exit(0)

    print("=== issues ===")
    open_issues = repo.get_issues(state="open")
    for issue in open_issues:
        print(issue)
        print(issue.body)
        print(dir(issue))

    issue = repo.get_issue(number=2)
    print()
    print(issue)
    print(issue.raw_data)
    print(issue.user)

    # repo.create_issue(title="This is a new issue", body="This is the body of the new issue")

    print("=== issues owned ===")
    owned_issues = repo.get_issues(creator="geo-saas-int[bot]")
    for issue in owned_issues:
        print(issue)
        print(issue.body)

        # issue.edit(body = issue.body + "\n\nThis is a test")

    branch = repo.get_branch("master")
    print(branch)
    print(branch.commit)
    print(branch.commit.sha)

    # repo.create_git_ref(ref="refs/heads/test", sha=repo.get_branch(repo.default_branch).commit.sha)
    # repo.create_file("test.txt", message="test", content="test", branch="test")

    # repo.update_file("README.md", message="test 123", content="test 123", sha=file_.sha, branch="test")

    # create pull request
    body = """
 SUMMARY
 Change HTTP library used to send requests

 TESTS
   - [x] Send 'GET' request
   - [x] Send 'POST' request with/without body
 """
    # pr = repo.create_pull(title="Use 'requests' instead of 'httplib'", body=body, head="test", base="master")
    # print(pr)


if __name__ == "__main__":
    _main()
