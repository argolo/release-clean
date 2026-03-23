# 🧹 Release Clean — Deterministic Git cleanup and release checkout

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/argolo/release-clean)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/argolo/release-clean)](https://github.com/argolo/release-clean/commits/main)
[![Open Issues](https://img.shields.io/github/issues/argolo/release-clean)](https://github.com/argolo/release-clean/issues)

[![PyPI Version](https://img.shields.io/pypi/v/release-clean.svg)](https://pypi.org/project/release-clean/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/release-clean.svg)](https://pypi.org/project/release-clean/)
[![PyPI](https://badge.fury.io/py/release-clean.svg)](https://pypi.org/project/release-clean/)

---

**Release Clean** is a **deterministic Git utility** designed to **clean, reset, and position your local repository** into a **trusted release state** before working on a specific release branch.

Its goal is simple and critical:

> Ensure that your local environment is **clean, consistent, and aligned with the correct release version**, eliminating any hidden state that could compromise reliability.

---

## 🎯 Purpose

Release Clean was created to solve a common and dangerous problem in release workflows:

> **How can we guarantee that a developer’s local environment is not polluted before switching to a release branch?**

Typical risks include:

* Residual build artifacts
* Ignored files affecting runtime behavior
* Untracked inconsistencies between developers
* Dirty working trees
* Outdated local branches

The solution is not manual cleanup — it is **deterministic cleanup based on the repository state**.

---

## ✨ Key Features

* 🧹 Cleanup based on `.gitignore`:

  * uses `git clean -fdX`
* 🧩 Preserves `node_modules/` to improve developer experience
* 🔄 Reset of tracked changes:

  * `git checkout -- .`
* 🌿 Safe synchronization of `main`
* 🚀 Deterministic checkout of `release/<VERSION>`
* 🔁 Pull of remote release branch
* 🔍 Validation of:

  * Git repository context
  * Version format
* ⚠️ Explicit confirmation (`y/N`) before destructive actions
* 🛑 Immediate stop on first failure
* 📋 Full execution trace (audit-friendly)
* 🎨 Highlighted execution steps (bold magenta)
* 🧩 Zero external dependencies (pure Python)

---

## 🧠 Operational Philosophy

Release Clean follows a strict principle:

> **The only reliable environment is a deterministic environment.**

Instead of relying on manual cleanup or assumptions, the tool ensures that:

* Cleanup is aligned with `.gitignore`
* The working tree is fully reset
* The correct branch is used
* No hidden state leaks into the release

This ensures **consistency across machines, teams, and environments**.

---

## ⚙️ Executed Workflow

Release Clean executes the following sequence:

```bash
git clean -fdX -e node_modules/
git checkout -- .
git checkout main
git pull
git fetch --all
git checkout release/<VERSION>
git checkout -- .
git pull origin release/<VERSION>
```

---

## 🔍 Workflow Breakdown

### 1. Clean ignored files

```bash
git clean -fdX -e node_modules/
```

* Removes all files listed in `.gitignore`
* Preserves `node_modules/` to avoid unnecessary reinstalls

---

### 2. Reset tracked changes

```bash
git checkout -- .
```

* Discards all tracked local changes

---

### 3. Synchronize base branch

```bash
git checkout main
git pull
git fetch --all
```

* Ensures `main` is up to date

---

### 4. Switch to release branch

```bash
git checkout release/<VERSION>
```

---

### 5. Enforce clean state on release

```bash
git checkout -- .
```

* Guarantees no local state leaks into the release branch

---

### 6. Update release branch

```bash
git pull origin release/<VERSION>
```

---

## 🚀 Installation

### Requirements

* Python **3.9+**
* Git installed and available in PATH

---

## 🍎 macOS Installation (recommended)

### 1️⃣ Install `pipx`

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

> ⚠️ Restart your terminal after installation.

---

### 2️⃣ Navigate to project directory

```bash
cd release-clean
```

---

### 3️⃣ Install globally

```bash
pipx install .
```

Now the command is available globally:

```bash
release-clean
```

---

### ▶️ Quick Test

```bash
release-clean
```

If the interactive prompt appears, installation is successful ✅

---

### 🔍 Optional Checks

```bash
which release-clean
pipx list
```

---

### 🧹 Updating

```bash
pipx reinstall release-clean
```

---

### ❌ Uninstall

```bash
pipx uninstall release-clean
```

---

### ⚠️ Important Notes

* Do **not** use `sudo pip install`
* Do **not** install CLI tools with system Python
* Always prefer `pipx` for CLI isolation

---

### 🧠 Rule of Thumb

> Python library → `pip install`
> Python CLI tool → `pipx install`

---

## 🧾 Usage

Run inside a Git repository:

```bash
release-clean
```

---

## 🔄 Execution Flow

1. Prompt for version
2. Validate version format
3. Validate Git repository
4. Display execution plan
5. Request confirmation (`y/N`)
6. Execute workflow
7. Stop on first failure
8. Print final summary

---

## 📌 Version Format

Accepted formats:

* `1.0.0`
* `2.100.1`
* `2.100.1-hotfix`
* `3.4.5-rc1`

Invalid examples:

* `1.0`
* `release/1.0.0`
* empty values

---

## ⚠️ Important Behavior

### 🔥 Cleanup behavior

```bash
git clean -fdX -e node_modules/
```

This means:

| Type of file       | Behavior    |
| ------------------ | ----------- |
| `.gitignore` files | ❌ removed   |
| tracked files      | ❌ reset     |
| `node_modules/`    | ✅ preserved |

---

### ⚠️ Destructive actions

The tool will:

* remove ignored files
* discard tracked changes
* change branches

Execution only proceeds with explicit confirmation:

```bash
Continue? [y/N]
```

---

## 📊 Execution Summary

At the end, Release Clean prints:

* 🕒 Start and end time
* 📁 Repository path
* 🌿 Version and branch
* ✅ Successful actions
* ❌ Failed actions
* 📋 Full command list in execution order

---

## 🛡️ Ideal Use Cases

* Preparing local environment before a release
* Eliminating “works on my machine” issues
* Teams using `release/<version>` strategy
* Multi-developer environments
* Regulated or mission-critical systems

---

## 🔮 Future Enhancements

* `--dry-run` mode (preview cleanup)
* `--version` (non-interactive execution)
* `--no-color`
* `--ci` (auto-confirm)
* Configurable exclusions (`--exclude node_modules`)
* Summary export (`.md`, `.txt`)
* Integration with:

  * Slack
  * Discord
  * Jira

---

## 📜 License

MIT License.

---

## 👤 Author

**André Argôlo**
CTO • Software Architect • DevOps

* 🌐 Website: [https://argolo.dev](https://argolo.dev)
* 🐙 GitHub: [https://github.com/argolo](https://github.com/argolo)

---

## 🧭 About

Release Clean embodies a key engineering principle:

> **A clean environment is not optional — it is a prerequisite for reliability.**

In modern development, subtle local inconsistencies can lead to:

* hidden bugs
* inconsistent builds
* unreliable validations

Release Clean eliminates that risk by enforcing:

* deterministic cleanup
* explicit control
* reproducible state

It is a minimal tool with a strong purpose:

**protect the integrity of your release process.**
