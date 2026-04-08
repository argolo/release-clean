from release_clean import (
    build_context,
    extract_version_from_branch,
    is_valid_branch,
    is_valid_version,
    planned_commands,
    supports_color,
)


def test_is_valid_version_accepts_supported_formats():
    assert is_valid_version("1.0.0") is True
    assert is_valid_version("2.100.1") is True
    assert is_valid_version("2.100.1-hotfix") is True
    assert is_valid_version("3.4.5-rc1") is True


def test_is_valid_version_rejects_invalid_formats():
    assert is_valid_version("") is False
    assert is_valid_version("1.0") is False
    assert is_valid_version("release/1.0.0") is False
    assert is_valid_version("v1.0.0") is False
    assert is_valid_version("1.0.0/") is False
    assert is_valid_version("abc") is False


def test_is_valid_branch_accepts_supported_formats():
    assert is_valid_branch("release/1.0.0") is True
    assert is_valid_branch("release/2.100.1-hotfix") is True
    assert is_valid_branch("candidate/2.1.30") is True
    assert is_valid_branch("pre-release/3.4.5-rc1") is True


def test_is_valid_branch_rejects_invalid_formats():
    assert is_valid_branch("") is False
    assert is_valid_branch("1.0.0") is False
    assert is_valid_branch("release/") is False
    assert is_valid_branch("/1.0.0") is False
    assert is_valid_branch("release/1.0") is False
    assert is_valid_branch("release/hotfix/1.0.0") is False
    assert is_valid_branch("release") is False


def test_extract_version_from_branch():
    assert extract_version_from_branch("release/2.100.1") == "2.100.1"
    assert extract_version_from_branch("release/2.100.1-hotfix") == "2.100.1-hotfix"
    assert extract_version_from_branch("candidate/2.1.30") == "2.1.30"


def test_planned_commands_has_expected_length():
    commands = planned_commands("release/2.100.1")
    assert len(commands) == 8


def test_planned_commands_starts_with_git_clean_preserving_node_modules():
    commands = planned_commands("release/2.100.1")
    assert commands[0] == "git clean -fdx -e node_modules/"


def test_planned_commands_contains_main_sync_steps_in_order():
    commands = planned_commands("release/2.100.1")

    assert commands[1] == "git checkout -- ."
    assert commands[2] == "git checkout main"
    assert commands[3] == "git pull"
    assert commands[4] == "git fetch --all"


def test_planned_commands_resets_after_release_checkout():
    release_branch = "release/2.100.1"
    commands = planned_commands(release_branch)

    release_checkout_index = commands.index(f"git checkout {release_branch}")

    assert commands[release_checkout_index] == f"git checkout {release_branch}"
    assert commands[release_checkout_index + 1] == "git checkout -- ."


def test_planned_commands_ends_with_release_pull():
    commands = planned_commands("release/2.100.1")
    assert commands[-1] == "git pull origin release/2.100.1"


def test_build_context():
    ctx = build_context("release/1.0.0", "/tmp/repo")

    assert ctx.version == "1.0.0"
    assert ctx.release_branch == "release/1.0.0"
    assert ctx.repo_root == "/tmp/repo"
    assert isinstance(ctx.color_enabled, bool)


def test_supports_color_returns_bool():
    assert isinstance(supports_color(), bool)
