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

    print(git_integration.get_app().slug + "[bot]")

    # print("=== get repos ===")
    # for i in git_integration.get_installations():
    #    # print(i)
    #    print(i.app_id)
    #    # print(i.id)
    #    # print(i.target_id)
    #    # print(i.target_type)
    #    for repo in i.get_repos():
    #        print(repo)

    token = git_integration.get_access_token(
        git_integration.get_installation("camptocamp", "helm-custom-pod").id
    ).token
    app = Github(login_or_token=token)
    repo = app.get_repo("camptocamp/helm-custom-pod")

    def help(obj):
        attributes = [a for a in dir(obj) if not a.startswith("_")]
        print(f"{type(obj).__module__}.{type(obj).__name__}: " + ", ".join(attributes))

    (help(app_auth))
    (help(git_integration))
    (help(git_integration.get_app()))

    # Get all tags
    first = True
    for tag in repo.get_tags():
        if first:
            (help(tag))
            first = False
        print(f'{tag.name}: {tag.commit.commit.author.date}')
        # github.Commit.Commit: CHECK_AFTER_INIT_FLAG, author, comments_url, commit, committer, create_comment, create_status, etag, files, get__repr__, get_check_runs, get_check_suites, get_combined_status, get_comments, get_pulls, get_statuses, html_url, last_modified, parents, raw_data, raw_headers, setCheckAfterInitFlag, sha, stats, update, url
        # github.GitCommit.GitCommit: CHECK_AFTER_INIT_FLAG, author, committer, etag, get__repr__, html_url, last_modified, message, parents, raw_data, raw_headers, setCheckAfterInitFlag, sha, tree, update, url

    oldTag = "1.1.2"
    tag = "1.1.3"
    # get the commits between oldTag and tag
    commits = repo.compare(oldTag, tag).commits

    print(commits)
    print("=" * 20)
    (help(repo))
    (help(commits[0]))
    (help(commits[0].commit))
    (help(commits[0].commit.author))
    (help(commits[0].author))
    (help(commits[0].files[0]))
    # print((commits[0].commit.author))
    # print((commits[0].commit.author.date))
    # print((commits[0].commit.author.name))
    for file in commits[0].files:
        print(file.filename)
    print((commits[0].sha))
    print((commits[0].author.login))
    for pr in commits[0].get_pulls():
        (help(pr))
        for f in pr.get_files():
            print(f.filename)
        for c in pr.get_commits():
            print(c)
        print(pr.number) # V
        print(pr.title) # V
        print(pr.user.login) # V

    # Get the related release
    for release in repo.get_releases():
        if release.tag_name == tag:
            (help(release))
            print(release.created_at)
            print(release.author)
            print(release.title)
            print('='*10)
            print(release.body)


    sys.exit(0)

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
