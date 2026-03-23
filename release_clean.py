#!/usr/bin/env python3
"""
Release Clean

Interactive utility to clean local artifacts, reset tracked changes,
synchronize Git references, and switch to a target release branch.

The tool is intentionally conservative:
- it validates the current directory is a Git repository
- it validates the version before building the branch name
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
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
from typing import Sequence


VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[A-Za-z0-9._-]+)?$")


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
        Process return code, or 0 for internal file operations that succeeded.
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


def format_release_branch(version: str) -> str:
    """
    Build the target release branch name.

    Parameters
    ----------
    version:
        Release version already validated by ``is_valid_version``.

    Returns
    -------
    str
        Branch name in the form ``release/<version>``.

    Examples
    --------
    >>> format_release_branch("2.100.1")
    'release/2.100.1'
    >>> format_release_branch("2.100.1-hotfix")
    'release/2.100.1-hotfix'
    """
    return f"release/{version}"


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


def prompt_version() -> str:
    """
    Prompt the user for a version and validate it.

    Returns
    -------
    str
        A valid version string.

    Raises
    ------
    ReleaseCleanError
        If the version is empty or invalid.
    """
    version = input("Enter version (e.g. 2.100.1 or 2.100.1-hotfix): ").strip()

    if not version:
        raise ReleaseCleanError("No version was provided.")

    if not is_valid_version(version):
        raise ReleaseCleanError(
            "Invalid version format. Expected examples: "
            "1.0.0, 2.100.1, 2.100.1-hotfix."
        )

    return version


def confirm(prompt: str = "Continue? [y/N]: ") -> bool:
    """
    Ask for an explicit yes/no confirmation.

    Only the exact value ``y`` confirms execution.

    Examples
    --------
    The function is interactive and therefore not doctested directly.
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


def remove_path(path: Path, ctx: ExecutionContext) -> CommandResult:
    """
    Remove a path in a way equivalent to ``rm -rf <name>``.

    The path is removed if it exists. Missing paths are treated as a
    successful no-op.

    Parameters
    ----------
    path:
        Path to remove.
    ctx:
        Shared execution context.

    Returns
    -------
    CommandResult
        Action result.

    Raises
    ------
    ReleaseCleanError
        If removal fails.
    """
    action = f"rm -rf {path.name}"
    ctx.executed_commands.append(action)
    log_action(ctx, f"[EXEC] {action}")

    try:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            stdout = "Removed."
        else:
            stdout = "Path does not exist. Nothing to remove."
    except OSError as exc:
        raise ReleaseCleanError(f"Failed to remove '{path}': {exc}") from exc

    result = CommandResult(
        command=action,
        success=True,
        returncode=0,
        stdout=stdout,
    )
    ctx.results.append(result)

    log_action(ctx, f"[OK] {stdout}")
    return result


def print_plan(ctx: ExecutionContext) -> None:
    """
    Print the execution plan before any destructive action.
    """
    print_header("PRE-EXECUTION SUMMARY")
    print(f"Repository directory : {ctx.repo_root}")
    print(f"Provided version     : {ctx.version}")
    print(f"Target branch        : {ctx.release_branch}")

    print("\nThe utility will execute the following steps in this order:")
    for index, command in enumerate(planned_commands(ctx.release_branch), start=1):
        print(f"{index}. {command}")

    print("\nWarning: this will discard tracked local changes and remove local paths:")
    print("- ios")
    print("- dist")
    print("- android")


def planned_commands(release_branch: str) -> list[str]:
    """
    Return the ordered list of actions that define the workflow.

    Examples
    --------
    >>> planned_commands("release/2.100.1")[0]
    'rm -rf ios'
    >>> planned_commands("release/2.100.1")[-1]
    'git pull origin release/2.100.1'
    """
    return [
        "rm -rf ios",
        "rm -rf dist",
        "rm -rf android",
        "git checkout -- .",
        "git checkout main",
        "git pull",
        "git fetch --all",
        f"git checkout {release_branch}",
        f"git pull origin {release_branch}",
    ]


def print_final_summary(ctx: ExecutionContext) -> None:
    """
    Print the final execution summary and audit trail.
    """
    print_header("FINAL SUMMARY")
    print(f"Started at      : {ctx.started_at}")
    print(f"Finished at     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Repository      : {ctx.repo_root}")
    print(f"Version         : {ctx.version}")
    print(f"Final branch    : {ctx.release_branch}")

    success_count = sum(result.success for result in ctx.results)
    fail_count = len(ctx.results) - success_count

    print(f"\nSuccessful actions : {success_count}")
    print(f"Failed actions     : {fail_count}")

    print("\nExecuted commands in order:")
    for index, command in enumerate(ctx.executed_commands, start=1):
        print(f"{index}. {command}")

    print("\nStatus:")
    print(
        "Execution completed successfully. The local environment was cleaned, "
        "main was synchronized, and the requested release branch was checked out."
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
    repo_root = Path(ctx.repo_root)

    remove_path(repo_root / "ios", ctx)
    remove_path(repo_root / "dist", ctx)
    remove_path(repo_root / "android", ctx)

    run_command(["git", "checkout", "--", "."], ctx)
    run_command(["git", "checkout", "main"], ctx)
    run_command(["git", "pull"], ctx)
    run_command(["git", "fetch", "--all"], ctx)
    run_command(["git", "checkout", ctx.release_branch], ctx)
    run_command(["git", "pull", "origin", ctx.release_branch], ctx)


def build_context(version: str, repo_root: str) -> ExecutionContext:
    """
    Build the execution context from validated inputs.

    Examples
    --------
    >>> ctx = build_context("1.0.0", "/repo")
    >>> ctx.release_branch
    'release/1.0.0'
    >>> ctx.repo_root
    '/repo'
    """
    return ExecutionContext(
        version=version,
        release_branch=format_release_branch(version),
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

        version = prompt_version()
        ctx = build_context(version, repo_root)

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
