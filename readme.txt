vaibhav is venv where packages will be installed, that's about it. The current terminal location, the Git repository location, and the Python virtual environment location do NOT have to be the same. This folder is NOT a Git repository unless it also contains a .git folder. .git folder stores git history, commits, branches, remotes whereas virtual environment (venv) stores Python interpreter and installed packages.

Important Commands
Find repository root: git rev-parse --show-toplevel
Show current Git status: git status
Find active Python interpreter: where python
Check current folder: cd

