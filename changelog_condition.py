import argparse
from typing import NamedTuple, Optional, Union
import subprocess
import tempfile
import os
import yaml
import github
from github import Github, GithubIntegration
from github.Auth import AppAuth

import re


class ChangelogItem(NamedTuple):
    object: Union[github.PullRequest.PullRequest, github.Commit.Commit]
    ref: str
    title: str
    author: str
    authors: set[str]
    branch: Optional[str]
    files: set[str]
    labels: set[str]

    def __hash__(self) -> int:
        return hash(self.ref)


def match(pr: ChangelogItem, condition: dict) -> bool:
    match_functions = {
        "and": match_and,
        "or": match_or,
        "not": match_not,
        "const": match_const,
        "title": match_title,
        "files": match_files,
        "label": match_label,
        "branch": match_branch,
        "author": match_author,
    }
    if condition["type"] not in match_functions:
        return False
    return match_functions[condition["type"]](pr, condition)


def match_and(pr: ChangelogItem, condition: dict) -> bool:
    for c in condition["conditions"]:
        if not match(pr, c):
            return False
    return True


def match_or(pr: ChangelogItem, condition: dict) -> bool:
    for c in condition["conditions"]:
        if match(pr, c):
            return True
    return False


def match_not(pr: ChangelogItem, condition: dict) -> bool:
    return not match(pr, condition["condition"])


def match_const(pr: ChangelogItem, condition: dict) -> bool:
    return condition["value"]


def match_title(pr: ChangelogItem, condition: dict) -> bool:
    return re.match(condition["regex"], pr.title) is not None


def match_files(pr: ChangelogItem, condition: dict) -> bool:
    file_re = re.compile("|".join(condition["regex"]))
    for f in pr.files:
        if file_re.match(f) is None:
            return False
    return True


def match_label(pr: ChangelogItem, condition: dict) -> bool:
    return condition["value"] in pr.labels


def match_branch(pr: ChangelogItem, condition: dict) -> bool:
    return re.match(condition["regex"], pr.branch) is not None


def match_author(pr: ChangelogItem, condition: dict) -> bool:
    return condition["value"] == pr.author


def get_group(pr: ChangelogItem, config: dict) -> list:
    group = config["default-group"]
    for group_condition in config["groups-conditions"]:
        if match(pr, group_condition["condition"]):
            group = group_condition["group-name"]
            if not group_condition.get("continue", False):
                return group
    return group


def _help(obj):
    attributes = [a for a in dir(obj) if not a.startswith("_")]
    print(f"{type(obj).__module__}.{type(obj).__name__}: " + ", ".join(attributes))


class Tag:
    TAG_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")
    TAG2_RE = re.compile(r"release_?(\d+)")

    def __init__(self, tag_str: Optional[str] = None, tag: Optional[github.Tag.Tag] = None):
        if tag_str is None:
            tag_str = tag.name
        self.tag_str = tag_str
        self.tag = tag
        tag_match = self.TAG_RE.match(tag_str)
        if tag_match is None:
            tag_match = self.TAG2_RE.match(tag_str)
            if tag_match is None:
                raise ValueError(f"Invalid tag: {tag_str}")
            self.major = tag_match.group(1)
            self.minor = 0
            self.patch = 0
        else:
            self.major, self.minor, self.patch = (int(e) for e in tag_match.groups())

    def __eq__(self, other: "Tag") -> bool:
        return self.major == other.major and self.minor == other.minor and self.patch == other.patch

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))

    def __lt__(self, other: "Tag") -> bool:
        if self.major < other.major:
            return True
        if self.major > other.major:
            return False
        if self.minor < other.minor:
            return True
        if self.minor > other.minor:
            return False
        return self.patch < other.patch

    def __gt__(self, other: "Tag") -> bool:
        if self.major > other.major:
            return True
        if self.major < other.major:
            return False
        if self.minor > other.minor:
            return True
        if self.minor < other.minor:
            return False
        return self.patch > other.patch

    def __cmp__(self, other: "Tag") -> int:
        if self < other:
            return -1
        if self > other:
            return 1
        return 0


def _previous_tag(tag: Tag, tags: dict[Tag, Tag]) -> Optional[Tag]:
    if tag.patch != 0:
        test_tag = Tag(".".join(str(e) for e in (tag.major, tag.minor, tag.patch - 1)))
        if test_tag in tags:
            return tags[test_tag]
        return _previous_tag(test_tag, tags)
    if tag.minor != 0:
        test_tag = Tag(".".join(str(e) for e in (tag.major, tag.minor - 1, 0)))
        if test_tag in tags:
            return tags[test_tag]
        return _previous_tag(test_tag, tags)
    if tag.major != 0:
        test_tag = Tag(".".join(str(e) for e in (tag.major - 1, 0, 0)))
        if test_tag in tags:
            return tags[test_tag]
        return _previous_tag(test_tag, tags)
    return None


def get_labels(config: dict) -> set[str]:
    if config["type"] in ("and", "or"):
        labels = set()
        for c in config["conditions"]:
            labels.update(get_labels(c))
        return labels
    if config["type"] == "not":
        return get_labels(config["condition"])
    if config["type"] == "label":
        return {config["value"]}
    return set()


def get_sections(config: dict) -> list[str]:
    sections = [config["default-group"]]

    for c in config["groups-conditions"]:
        group_name = c["group-name"]
        if group_name not in sections:
            sections.append(group_name)
    return sections


def get_release(tag: github.Tag.Tag) -> Optional[github.GitRelease.GitRelease]:
    for release in tag.get_repo().get_releases():
        if release.tag_name == tag.name:
            return release
    return None


CONFIG = yaml.safe_load(
    """
enabled: true
default-group: New feature
create-labels: true
groups-conditions:
# Label
  - group-name: Breaking changes
    condition:
        type: label
        value: Breaking changes
  - group-name: New feature
    condition:
        type: label
        value: New feature
  - group-name: Fixed bugs
    condition:
        type: label
        value: Fixed bugs
  - group-name: Documentation
    condition:
        type: label
        value: Documentation
  - group-name: Tests
    condition:
        type: label
        value: Tests
  - group-name: Chore
    condition:
        type: label
        value: Chore
  - group-name: Security fixes
    condition:
        type: label
        value: Security fixes
  - group-name: Dependency update
    condition:
        type: label
        value: Dependency update
  # Other
  - group-name: Documentation
    condition:
        type: files
        regex:
            - .*\.rst$
            - .*\.md$
            - .*\.rst\.[a-z0-9]{2,6}$
            - .*\.md\.[a-z0-9]{2,6}$
            - ^docs?/.*
  - group-name: Chore
    condition:
        type: files
        regex:
            - ^\.github/.*
            - ^ci/.*
  - group-name: Chore
    condition:
        type: title
        regex: ^CI updates$
  - group-name: Security fixes
    condition:
        type: branch
        regex: ^audit-.*
  - group-name: Security fixes
    condition:
        type: and
        conditions:
            - type: branch
              regex: ^dpkg-update/.*
            - type: author
              value: c2c-gid-bot-ci
  - group-name: Security fixes
    condition:
        type: branch
        regex: ^snyk-fix/.*
  - group-name: Dependency update
    condition:
        type: author
        value: renovate[bot]"""
)


def get_pull_request_tags(
    repo: github.Repository.Repository, pull_request_number: int, tags: Optional[dict[Tag, Tag]] = None
) -> Optional[Tag]:
    """
    Get the tags that contains the merge commit of the pull request
    """
    pr = repo.get_pull(pull_request_number)
    # created temporary directory
    with tempfile.TemporaryDirectory() as tmp_directory_name:
        os.chdir(tmp_directory_name)
        subprocess.run(["git", "clone", repo.clone_url], check=True)
        os.chdir(os.path.join(tmp_directory_name, repo.name))
        tags_str = (
            subprocess.run(
                ["git", "tag", "--contains", pr.merge_commit_sha], stdout=subprocess.PIPE, check=True
            )
            .stdout.decode()
            .split("\n")
        )
        found_tags = []
        for tag in tags_str:
            if tag:
                try:
                    found_tags.append(Tag(tag))
                except ValueError:
                    pass

    if not found_tags:
        return None
    found_tags.sort()
    found_tag = found_tags[0]
    if tags and found_tag in tags:
        return tags[found_tag]
    return found_tag


def _main():
    parser = argparse.ArgumentParser(
        """
        pip install pygithub

        test with: python changelog_condition.py --app-id="$(gopass show private/2fa/github/app-geo-saas-int/app-id)" --private-key="$(gopass show private/2fa/github/app-geo-saas-int/private-key)"
        """
    )
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--private-key", required=True)
    args = parser.parse_args()

    labels = set()
    for c in CONFIG["groups-conditions"]:
        labels.update(get_labels(c["condition"]))
    print(labels)
    print(get_sections(CONFIG))

    app_auth = AppAuth(args.app_id, args.private_key)
    git_integration = GithubIntegration(auth=app_auth)

    token = git_integration.get_access_token(
        git_integration.get_installation("camptocamp", "helm-custom-pod").id
    ).token
    app = Github(login_or_token=token)
    repo = app.get_repo("camptocamp/helm-custom-pod")

    tags: dict[Tag, Tag] = {}
    for tag in repo.get_tags():
        try:
            tag = Tag(tag=tag)
            tags[tag] = tag
        except ValueError:
            print(f"Invalid tag: {tag.name}")
            continue

    tag = Tag("1.1.3")
    if tag not in tags:
        print(f"Tag {tag} not found")
        return
    tag = tags[tag]
    old_tag = _previous_tag(tag, tags)
    if old_tag is None:
        print("No previous tag")
        return

    changelog_items: set[ChangelogItem] = set()

    # get the commits between oldTag and tag
    for commit in repo.compare(old_tag.tag.name, tag.tag.name).commits:
        has_pr = False
        for pr in commit.get_pulls():
            has_pr = True
            authors = {pr.user.login}
            for c in pr.get_commits():
                authors.add(c.author.login)
            changelog_items.add(
                ChangelogItem(
                    object=pr,
                    ref=f"#{pr.number}",
                    title=pr.title,
                    author=pr.user.login,
                    authors=authors,
                    branch=pr.base.ref,
                    files={f.filename for f in pr.get_files()},
                    labels={l.name for l in pr.get_labels()},
                )
            )
        if not has_pr:
            changelog_items.add(
                ChangelogItem(
                    object=commit,
                    ref=commit.sha,
                    title=commit.commit.message.split("\n")[0],
                    author=commit.author.login,
                    authors={commit.author.login},
                    branch=commit.committer.login,
                    files={f.filename for f in commit.files},
                    labels=set(),
                )
            )

    groups = {}
    for item in changelog_items:
        group = get_group(item, CONFIG)
        groups.setdefault(group, []).append(item)

    print("Title:")
    created = tag.tag.commit.commit.author.date
    print(f"{tag.major}.{tag.minor}.{tag.patch} ({created:%Y-%m-%d})")
    print()
    for group in get_sections(CONFIG):
        if group not in groups:
            continue
        print(f"## {group}")
        for item in groups[group]:
            authors = [item.author]
            authors.extend(a for a in item.authors if a != item.author)
            authors = [f"@{a}" for a in authors]
            print(f"- {item.ref} **{item.title}** ({', '.join(authors)})")
        print()


if __name__ == "__main__":
    _main()
