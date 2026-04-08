#!/usr/bin/env python3
"""
Release Clean

Interactive utility to clean local ignored artifacts, reset tracked changes,
synchronize Git references, and switch to a target release branch.

The tool is intentionally conservative:
- it validates the current directory is a Git repository
- it validates the branch format before execution
- it shows a clear destructive-action summary before execution
- it requires explicit confirmation
- it stops at the first failure
- it records all executed actions for quick audit

Example
-------
Run from a Git repository root or any subdirectory inside it:

    $ release-clean

Design notes
------------
This module favors:
- small pure functions where possible
- explicit failure handling
- standard library only
- high readability
- shell-free subprocess execution for safety and predictability
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Sequence


VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[A-Za-z0-9._-]+)?$")
BRANCH_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]*/\d+\.\d+\.\d+(?:-[A-Za-z0-9._-]+)?$")


def supports_color() -> bool:
    """
    Return whether ANSI colors should be used.

    The function is intentionally conservative and only enables color
    when stdout is attached to a terminal.

    Returns
    -------
    bool
        True when ANSI coloring is likely supported.

    Examples
    --------
    >>> isinstance(supports_color(), bool)
    True
    """
    return sys.stdout.isatty()


class Style:
    """
    ANSI style helper for terminal output.

    Only operational lines are highlighted, making it easier to distinguish
    the tool's own execution flow from Git output.

    Examples
    --------
    >>> Style.wrap("hello", enabled=False)
    'hello'
    >>> "hello" in Style.wrap("hello", enabled=True)
    True
    """

    RESET = "\033[0m"
    BOLD = "\033[1m"
    MAGENTA = "\033[95m"

    @classmethod
    def wrap(cls, text: str, *, enabled: bool) -> str:
        """Wrap text with bold magenta ANSI styling when enabled."""
        if not enabled:
            return text
        return f"{cls.BOLD}{cls.MAGENTA}{text}{cls.RESET}"


@dataclass
class CommandResult:
    """
    Result of a single executed action.

    Attributes
    ----------
    command:
        Human-readable command or action description.
    success:
        Whether the action completed successfully.
    returncode:
        Process return code.
    stdout:
        Captured standard output.
    stderr:
        Captured standard error.
    """

    command: str
    success: bool
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass
class ExecutionContext:
    """
    Runtime context and audit trail for a Release Clean session.
    """

    version: str
    release_branch: str
    repo_root: str
    color_enabled: bool
    started_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    executed_commands: list[str] = field(default_factory=list)
    results: list[CommandResult] = field(default_factory=list)


class ReleaseCleanError(RuntimeError):
    """Raised when execution cannot proceed safely."""


def print_header(title: str) -> None:
    """
    Print a section header.

    Examples
    --------
    >>> print_header("TITLE")  # doctest: +ELLIPSIS
    ...
    TITLE
    ...
    """
    line = "=" * 72
    print(f"\n{line}\n{title}\n{line}")


def is_valid_version(version: str) -> bool:
    """
    Validate supported release version formats.

    Accepted examples:
    - 1.0.0
    - 2.100.1
    - 2.100.1-hotfix
    - 3.4.5-rc1

    Examples
    --------
    >>> is_valid_version("1.0.0")
    True
    >>> is_valid_version("2.100.1-hotfix")
    True
    >>> is_valid_version("1.0")
    False
    >>> is_valid_version("release/1.0.0")
    False
    >>> is_valid_version("")
    False
    """
    return bool(VERSION_PATTERN.fullmatch(version.strip()))


def is_valid_branch(branch: str) -> bool:
    """
    Validate branch format as <suffix>/<version>.

    Accepted examples:
    - release/1.0.0
    - release/2.100.1-hotfix
    - candidate/2.1.30

    Examples
    --------
    >>> is_valid_branch("release/1.0.0")
    True
    >>> is_valid_branch("candidate/2.1.30")
    True
    >>> is_valid_branch("release/hotfix/1.0.0")
    False
    >>> is_valid_branch("release/")
    False
    >>> is_valid_branch("1.0.0")
    False
    """
    return bool(BRANCH_PATTERN.fullmatch(branch.strip()))


def extract_version_from_branch(branch: str) -> str:
    """
    Extract the version portion from a valid branch string.

    Parameters
    ----------
    branch:
        Branch in the format <suffix>/<version>.

    Returns
    -------
    str
        Extracted version.

    Examples
    --------
    >>> extract_version_from_branch("release/1.0.0")
    '1.0.0'
    >>> extract_version_from_branch("candidate/2.1.30")
    '2.1.30'
    """
    _, version = branch.strip().split("/", 1)
    return version


def prompt_branch() -> str:
    """
    Prompt the user for a branch and validate it.

    Returns
    -------
    str
        A valid branch string.

    Raises
    ------
    ReleaseCleanError
        If the branch is empty or invalid.
    """
    branch = input(
        "Enter branch (e.g. release/2.100.1-hotfix or candidate/2.1.30): "
    ).strip()

    if not branch:
        raise ReleaseCleanError("No branch was provided.")

    if not is_valid_branch(branch):
        raise ReleaseCleanError(
            "Invalid branch format. Expected: <suffix>/<version>. "
            "Examples: release/1.0.0, release/2.100.1-hotfix, candidate/2.1.30."
        )

    version = extract_version_from_branch(branch)
    if not is_valid_version(version):
        raise ReleaseCleanError(
            "Invalid version format inside branch. Expected SemVer-like examples: "
            "1.0.0, 2.100.1, 2.100.1-hotfix."
        )

    return branch


def confirm(prompt: str = "Continue? [y/N]: ") -> bool:
    """
    Ask for an explicit yes/no confirmation.

    Only the exact value ``y`` confirms execution.
    """
    return input(prompt).strip().lower() == "y"


def resolve_git_repo_root() -> str:
    """
    Resolve the current Git repository root.

    Returns
    -------
    str
        Absolute path to the repository root.

    Raises
    ------
    ReleaseCleanError
        If Git is not installed or the current directory is not inside a repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ReleaseCleanError(
            "Git was not found on this system. Verify the Git installation."
        ) from exc

    if result.returncode != 0:
        raise ReleaseCleanError(
            "The current directory is not inside a valid Git repository."
        )

    repo_root = result.stdout.strip()
    if not repo_root:
        raise ReleaseCleanError("Could not determine the Git repository root.")

    return repo_root


def log_action(ctx: ExecutionContext, text: str) -> None:
    """
    Print a highlighted operational line.

    Examples
    --------
    >>> ctx = ExecutionContext("1.0.0", "release/1.0.0", "/tmp", False)
    >>> log_action(ctx, "[EXEC] sample")  # doctest: +ELLIPSIS
    [EXEC] sample
    """
    print(Style.wrap(text, enabled=ctx.color_enabled))


def run_command(command: Sequence[str], ctx: ExecutionContext) -> CommandResult:
    """
    Execute a system command and stop on the first failure.

    Parameters
    ----------
    command:
        Command and arguments, already tokenized.
    ctx:
        Shared execution context.

    Returns
    -------
    CommandResult
        Captured execution result.

    Raises
    ------
    ReleaseCleanError
        If the command fails or cannot be executed.
    """
    command_str = " ".join(command)
    ctx.executed_commands.append(command_str)
    log_action(ctx, f"[EXEC] {command_str}")

    try:
        completed = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ReleaseCleanError(f"System command not found: {command[0]}") from exc

    result = CommandResult(
        command=command_str,
        success=completed.returncode == 0,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    ctx.results.append(result)

    if not result.success:
        raise ReleaseCleanError(
            f"Command failed: {command_str}\n"
            f"Return code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout.strip() or '-'}\n"
            f"STDERR:\n{result.stderr.strip() or '-'}"
        )

    log_action(ctx, "[OK]")
    if result.stdout.strip():
        print(result.stdout.strip())

    return result


def planned_commands(release_branch: str) -> list[str]:
    """
    Return the ordered list of actions that define the workflow.

    Examples
    --------
    >>> planned_commands("release/2.100.1")[0]
    'git clean -fdx -e node_modules/'
    >>> planned_commands("release/2.100.1")[-1]
    'git pull origin release/2.100.1'
    """
    return [
        "git clean -fdx -e node_modules/",
        "git checkout -- .",
        "git checkout main",
        "git pull",
        "git fetch --all",
        f"git checkout {release_branch}",
        "git checkout -- .",
        f"git pull origin {release_branch}",
    ]


def print_plan(ctx: ExecutionContext) -> None:
    """
    Print the execution plan before any destructive action.
    """
    print_header("PRE-EXECUTION SUMMARY")
    print(f"Repository directory : {ctx.repo_root}")
    print(f"Provided branch      : {ctx.release_branch}")
    print(f"Extracted version    : {ctx.version}")
    print(f"Target branch        : {ctx.release_branch}")

    print("\nThe utility will execute the following steps in this order:")
    for index, command in enumerate(planned_commands(ctx.release_branch), start=1):
        print(f"{index}. {command}")

    print("\nWarning: this will discard tracked changes and remove ignored files.")
    print("Preserved from cleanup:")
    print("- node_modules/")


def print_final_summary(ctx: ExecutionContext) -> None:
    """
    Print the final execution summary and audit trail.
    """
    print_header("FINAL SUMMARY")
    print(f"Started at      : {ctx.started_at}")
    print(f"Finished at     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Repository      : {ctx.repo_root}")
    print(f"Branch          : {ctx.release_branch}")
    print(f"Version         : {ctx.version}")
    print(f"Final branch    : {ctx.release_branch}")

    success_count = sum(result.success for result in ctx.results)
    fail_count = len(ctx.results) - success_count

    print(f"\nSuccessful actions : {success_count}")
    print(f"Failed actions     : {fail_count}")

    print("\nStatus:")
    print(
        "Execution completed successfully. Ignored files were cleaned "
        "(preserving node_modules/), main was synchronized, and the "
        "requested branch was checked out."
    )


def execute_workflow(ctx: ExecutionContext) -> None:
    """
    Execute the full release-clean workflow.

    Parameters
    ----------
    ctx:
        Shared execution context.

    Raises
    ------
    ReleaseCleanError
        If any step fails.
    """
    _ = Path(ctx.repo_root)

    run_command(["git", "clean", "-fdx", "-e", "node_modules/"], ctx)
    run_command(["git", "checkout", "--", "."], ctx)
    run_command(["git", "checkout", "main"], ctx)
    run_command(["git", "pull"], ctx)
    run_command(["git", "fetch", "--all"], ctx)
    run_command(["git", "checkout", ctx.release_branch], ctx)
    run_command(["git", "checkout", "--", "."], ctx)
    run_command(["git", "pull", "origin", ctx.release_branch], ctx)


def build_context(branch: str, repo_root: str) -> ExecutionContext:
    """
    Build the execution context from validated inputs.

    Examples
    --------
    >>> ctx = build_context("release/1.0.0", "/repo")
    >>> ctx.release_branch
    'release/1.0.0'
    >>> ctx.version
    '1.0.0'
    >>> ctx.repo_root
    '/repo'
    """
    return ExecutionContext(
        version=extract_version_from_branch(branch),
        release_branch=branch,
        repo_root=repo_root,
        color_enabled=supports_color(),
    )


def main() -> None:
    """
    CLI entry point for the ``release-clean`` command.
    """
    try:
        print_header("RELEASE CLEAN")

        repo_root = resolve_git_repo_root()
        os.chdir(repo_root)

        branch = prompt_branch()
        ctx = build_context(branch, repo_root)

        print_plan(ctx)

        if not confirm():
            raise ReleaseCleanError("Execution cancelled by user.")

        execute_workflow(ctx)
        print_final_summary(ctx)

    except KeyboardInterrupt:
        print_header("ERROR")
        print("Execution interrupted manually by the user.")
        raise SystemExit(1) from None
    except ReleaseCleanError as exc:
        print_header("ERROR")
        print(str(exc))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
