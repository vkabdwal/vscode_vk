# VS Code, Python Virtual Environments, and Git Notes

These notes are a practical reference for working with Python projects in VS Code and pushing the right files to GitHub. They are based on my local setup and the common mistakes that came up while using `D:\Github`, `D:\Github\vaibhav`, and the FeederIQ project folder.

## Index

- [Quick Mental Model](#quick-mental-model)
- [My Example Setup](#my-example-setup)
- [Working In The Right Folder](#working-in-the-right-folder)
  - [Check Where You Are](#check-where-you-are)
  - [Check The Git Repository Root](#check-the-git-repository-root)
  - [Check The Git Remote](#check-the-git-remote)
- [Python And VS Code Setup](#python-and-vs-code-setup)
  - [Python Virtual Environment Basics](#python-virtual-environment-basics)
  - [Activate The Virtual Environment](#activate-the-virtual-environment)
  - [Install Packages In The Active Environment](#install-packages-in-the-active-environment)
  - [Select The Right Python In VS Code](#select-the-right-python-in-vs-code)
- [Adding The Right Files To GitHub](#adding-the-right-files-to-github)
  - [Push Only One Folder To GitHub](#push-only-one-folder-to-github)
  - [What Happened When I Ran `git add .`](#what-happened-when-i-ran-git-add-)
  - [Add Specific Files Or Folders Only](#add-specific-files-or-folders-only)
  - [Undo Accidental `git add .`](#undo-accidental-git-add-)
  - [Remove A Folder From GitHub But Keep It Locally](#remove-a-folder-from-github-but-keep-it-locally)
  - [Stop A Folder From Being Added Again](#stop-a-folder-from-being-added-again)
  - [Embedded Git Repository Warning](#embedded-git-repository-warning)
- [Common Git Problems](#common-git-problems)
  - [Push Rejected: Fetch First](#push-rejected-fetch-first)
  - [Branch Has No Upstream](#branch-has-no-upstream)
  - [Line Ending Warning On Windows](#line-ending-warning-on-windows)
- [Project Folder Placement](#project-folder-placement)
  - [Copy A Project Folder Into The Existing Git Repo](#copy-a-project-folder-into-the-existing-git-repo)
  - [Do Not Copy Into An Ignored Folder](#do-not-copy-into-an-ignored-folder)
- [Daily Use](#daily-use)
  - [Recommended Daily Workflow](#recommended-daily-workflow)
  - [Safety Checklist Before Committing](#safety-checklist-before-committing)
  - [Useful Commands](#useful-commands)
  - [Best Rule To Remember](#best-rule-to-remember)

## Quick Mental Model

There are three different things that are easy to mix up:

| Thing | What it means | Example |
|---|---|---|
| Project folder | The folder containing the code you are editing | `G:\My Drive\Analytics\Projects\feederiq_hackathon26-main\FeederIQ` |
| Git repository root | The folder that contains `.git` | `D:\Github` |
| Python virtual environment | The folder containing Python packages for one environment | `D:\Github\vaibhav` |

A Python virtual environment is not automatically the same thing as your Git repository. A VS Code folder is also not automatically the same thing as your Git repository.

## My Example Setup

```text
D:\Github
|-- .git
|-- .gitignore
|-- FeederIQ
|-- Resources
|-- config
|-- utils
|-- readme.txt
|-- readme_vscode.docx
|-- README_GIT_Notes.md
`-- vaibhav
    |-- Scripts
    |-- Lib
    |-- Include
    `-- pyvenv.cfg
```

In this setup:

- `D:\Github` is the Git repo root.
- `D:\Github\vaibhav` is a Python virtual environment.
- `D:\Github\FeederIQ` is the project folder copied into the Git repo.

## Working In The Right Folder

### Check Where You Are

In PowerShell:

```powershell
pwd
```

In cmd:

```cmd
cd
```

To move folders in PowerShell:

```powershell
cd "D:\Github"
cd "G:\My Drive\Analytics\Projects\feederiq_hackathon26-main\FeederIQ"
```

To move folders in cmd, especially when changing drives:

```cmd
cd /d D:\Github\vaibhav
```

### Check The Git Repository Root

Run this from any folder inside a Git repo:

```powershell
git rev-parse --show-toplevel
```

Example output:

```text
D:/Github
```

That means Git considers `D:\Github` the repo root. If you run `git add .` from `D:\Github`, Git will try to add everything under `D:\Github`.

### Check The Git Remote

```powershell
git remote -v
```

Example:

```text
origin  https://github.com/vkabdwal/vscode_vk.git (fetch)
origin  https://github.com/vkabdwal/vscode_vk.git (push)
```

This means commits from the local repo will push to:

```text
https://github.com/vkabdwal/vscode_vk.git
```

## Python And VS Code Setup

### Python Virtual Environment Basics

Create a virtual environment:

```powershell
python -m venv vaibhav
```

Create a virtual environment in a specific location:

```powershell
python -m venv D:\PythonEnvs\vaibhav_exact
```

A virtual environment usually contains:

```text
Scripts
Lib
Include
pyvenv.cfg
```

### Activate The Virtual Environment

For cmd:

```cmd
D:\Github\vaibhav\Scripts\activate
```

or:

```cmd
D:\Github\vaibhav\Scripts\activate.bat
```

For PowerShell:

```powershell
& "D:\Github\vaibhav\Scripts\Activate.ps1"
```

PowerShell needs `Activate.ps1`. The cmd activation script is different.

If PowerShell blocks the script, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then open a new PowerShell window and activate again.

Deactivate the environment:

```powershell
deactivate
```

### Install Packages In The Active Environment

After activation, install packages:

```powershell
pip install pandas numpy matplotlib
```

Check installed packages:

```powershell
pip list
```

Check which Python is being used:

```powershell
python -c "import sys; print(sys.executable)"
```

You want to see something like:

```text
D:\Github\vaibhav\Scripts\python.exe
```

### Select The Right Python In VS Code

Activating a venv in the terminal is useful, but VS Code may still use another Python interpreter when running or debugging code.

In VS Code:

1. Press `Ctrl + Shift + P`.
2. Search for `Python: Select Interpreter`.
3. Select the interpreter from the venv, for example:

```text
D:\Github\vaibhav\Scripts\python.exe
```

If you skip this step, these problems can happen:

- Imports work in terminal but fail when using the VS Code Run button.
- IntelliSense shows missing packages.
- Debugging uses a different Python.
- Linting and code navigation behave strangely.

## Adding The Right Files To GitHub

### Push Only One Folder To GitHub

If the repo root is `D:\Github` and you only want to add `FeederIQ`, do this:

```powershell
cd "D:\Github"

git status
git add FeederIQ
git status
git commit -m "Update FeederIQ"
git push
```

Do not use `git add .` unless you truly want to add everything in the current folder.

### What Happened When I Ran `git add .`

If you run this from `D:\Github`:

```powershell
git add .
```

Git tries to stage everything under `D:\Github`, including folders you did not intend to upload.

That is why `Complete-Python-Bootcamp` appeared on GitHub. It was inside `D:\Github`, so Git saw it when `git add .` was used.

### Add Specific Files Or Folders Only

Add one folder:

```powershell
git add FeederIQ
```

Add one file:

```powershell
git add FeederIQ/README.md
```

Add multiple specific paths:

```powershell
git add FeederIQ Resources readme.txt
```

Always check before committing:

```powershell
git status
```

### Undo Accidental `git add .`

If you staged too much but have not committed yet:

```powershell
git restore --staged .
```

Then add only what you want:

```powershell
git add FeederIQ
```

### Remove A Folder From GitHub But Keep It Locally

If `Complete-Python-Bootcamp` was added by mistake, remove it from Git tracking only:

```powershell
cd "D:\Github"

git rm --cached -r Complete-Python-Bootcamp
git commit -m "Remove Complete Python Bootcamp from repo"
git push
```

The `--cached` flag is important. It removes the folder from GitHub and Git tracking, but keeps the local folder on the computer.

### Stop A Folder From Being Added Again

Add it to `.gitignore`:

```powershell
Add-Content .gitignore "`nComplete-Python-Bootcamp/"

git add .gitignore
git commit -m "Ignore Complete Python Bootcamp folder"
git push
```

After this, Git should ignore that folder.

### Embedded Git Repository Warning

Warning example:

```text
warning: adding embedded git repository: Complete-Python-Bootcamp
```

Meaning:

```text
D:\Github\Complete-Python-Bootcamp
```

has its own `.git` folder inside it. Git is warning that you are trying to add one Git repo inside another Git repo.

Usually, this is a mistake.

Fix:

```powershell
git rm --cached -r Complete-Python-Bootcamp
```

Then commit and push:

```powershell
git commit -m "Remove embedded Python bootcamp repo"
git push
```

## Common Git Problems

### Push Rejected: Fetch First

Error:

```text
! [rejected] main -> main (fetch first)
error: failed to push some refs
```

Meaning: GitHub has commits that your local repo does not have yet.

Fix:

```powershell
cd "D:\Github"

git pull origin main --rebase
git push --set-upstream origin main
```

If conflicts appear, stop and resolve them before pushing.

### Branch Has No Upstream

Error:

```text
fatal: The current branch main has no upstream branch
```

Fix:

```powershell
git push --set-upstream origin main
```

After that, normal `git push` should work from the same branch.

### Line Ending Warning On Windows

Warning:

```text
LF will be replaced by CRLF the next time Git touches it
```

Meaning: Git is warning about line endings. Linux/macOS often use `LF`; Windows often uses `CRLF`.

Usually this is not a blocker. Your commit can still succeed.

Optional setting for Windows:

```powershell
git config --global core.autocrlf true
```

## Project Folder Placement

### Copy A Project Folder Into The Existing Git Repo

If your current VS Code folder is here:

```text
G:\My Drive\Analytics\Projects\feederiq_hackathon26-main\FeederIQ
```

and your Git repo is here:

```text
D:\Github
```

copy the project into the Git repo:

```powershell
Copy-Item -Recurse -Force "G:\My Drive\Analytics\Projects\feederiq_hackathon26-main\FeederIQ" "D:\Github\FeederIQ"
```

Then commit only that folder:

```powershell
cd "D:\Github"

git add FeederIQ
git commit -m "Add FeederIQ project"
git push --set-upstream origin main
```

### Do Not Copy Into An Ignored Folder

This caused trouble:

```text
D:\Github\vaibhav\FeederIQ
```

because `vaibhav` was ignored by `.gitignore`. Git refused to add files inside it.

Better:

```text
D:\Github\FeederIQ
```

## Daily Use

### Recommended Daily Workflow

When updating FeederIQ:

```powershell
cd "D:\Github"

git pull origin main --rebase
git status
git add FeederIQ
git status
git commit -m "Update FeederIQ"
git push
```

If `git status` shows files you did not intend to upload, do not commit yet.

### Safety Checklist Before Committing

Before `git commit`, ask:

- Am I in the correct repo root?
- Did I run `git status`?
- Am I using `git add FeederIQ` instead of `git add .`?
- Is `Complete-Python-Bootcamp` absent from staged changes?
- Are virtual environment folders like `vaibhav`, `.venv`, or `venv` ignored?
- Did I avoid committing secrets, tokens, `.env`, or generated files?

### Useful Commands

Show current folder:

```powershell
pwd
```

Show Git repo root:

```powershell
git rev-parse --show-toplevel
```

Show remote GitHub repo:

```powershell
git remote -v
```

Show changed files:

```powershell
git status
```

Show staged files only:

```powershell
git diff --cached --name-only
```

Unstage everything:

```powershell
git restore --staged .
```

Commit staged files:

```powershell
git commit -m "Message here"
```

Push current branch:

```powershell
git push
```

Push and set upstream:

```powershell
git push --set-upstream origin main
```

### Best Rule To Remember

If you only want to upload one folder, name that folder explicitly:

```powershell
git add FeederIQ
```

Avoid this from a broad repo root:

```powershell
git add .
```
