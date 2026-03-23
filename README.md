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

Release Clean does **not automate blindly**.
It enforces **controlled execution**, requiring explicit confirmation before any destructive operation.

---

## 🎯 Purpose

Release Clean was created to solve a common and dangerous problem in release workflows:

> **How can we guarantee that a developer’s local environment is not polluted before switching to a release branch?**

Typical risks include:

* Residual build artifacts (`ios`, `android`, `dist`)
* Untracked or partially reverted changes
* Outdated branches
* Inconsistent local state across team members

The answer is not convenience — it is **deterministic cleanup and controlled execution**.

---

## ✨ Key Features

* 🧹 Automatic cleanup of local build directories:

  * `ios`, `android`, `dist`
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

Release Clean is built around a strict principle:

> **A release environment must be deterministic.**

It ensures that:

* No residual files interfere with the build or execution
* No local changes silently affect behavior
* The correct branch is always used
* The operator is always aware of what is happening

This tool enforces **discipline before action**.

---

## ⚙️ Executed Workflow

Release Clean executes the following sequence:

```bash
rm -rf ios
rm -rf dist
rm -rf android
git checkout -- .
git checkout main
git pull
git fetch --all
git checkout release/<VERSION>
git pull origin release/<VERSION>
```

This sequence is **intentional and ordered**:

1. Clean local artifacts
2. Reset tracked changes
3. Synchronize base branch (`main`)
4. Fetch all references
5. Move to target release
6. Ensure release branch is up to date

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

### Flow

1. Prompt for version:

```text
Enter version (e.g. 2.100.1 or 2.100.1-hotfix)
```

2. Validate version format

3. Validate Git repository

4. Show execution plan

5. Ask for confirmation:

```text
Continue? [y/N]
```

6. Execute workflow

7. Stop on first failure (if any)

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

## 📊 Execution Summary

At the end, Release Clean prints:

* 🕒 Start and end time
* 📁 Repository path
* 🌿 Version and branch
* ✅ Successful actions
* ❌ Failed actions
* 📋 Full command list in execution order

This improves:

* auditability
* reproducibility
* communication with team

---

## 🛡️ Ideal Use Cases

* Preparing local environment before a release
* Avoiding “works on my machine” scenarios
* Teams working with release branches (`release/x.y.z`)
* CI/CD validation steps (manual or scripted)
* Regulated or critical systems where consistency matters

---

## 🔮 Future Enhancements

* `--dry-run` mode
* `--version` flag (non-interactive)
* `--no-color`
* `--branch-base` (support `master`)
* CI mode (`--yes`)
* Exportable summary (`.md`, `.txt`)
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

Release Clean reflects a fundamental principle in software engineering:

> **Reliability starts before execution — it starts with a clean state.**

In complex and mission-critical systems, subtle inconsistencies in local environments can lead to unpredictable behavior, hidden bugs, and costly debugging cycles.

Release Clean exists to eliminate that risk.

It is a small tool with a strong purpose:
**enforce consistency, reduce uncertainty, and protect the integrity of your release process.**
