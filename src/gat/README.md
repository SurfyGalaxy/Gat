# GAT
<sub> idk what this name means but it's like gat so :3 </sub>

## Features:

- It doesn't crash instantly
- Files seem to load
- Hasn't blown up my hard drive yet
- Minorly speedy for python
- <s>Won't sell your data to AI unlike *some* VCS</s>

## Usage:

simply run:
```bash
pip install gat_vcs
```

## Commands:

### Init

Initialises the gat folder and JSON required for gat to function.
Only needed to be ran once.

syntax:
```bash
gat init
```

### Commit

Create a new commit.

- `<branch>`    What branch to commit it to
- `<files>`     List of files to add to the commit
- `-n <name>`   Name of the commit
- `-m <message>`The message to be displayed with the commit

syntax:
```bash
gat commit <branch> <files> -n <name> -m <message>
```

e.g.:
```bash
gat commit Main main.py README.md -n Test -m "A test commit"
```

### Merge

Merge a branch's most recent commit into main.

syntax:
```bash
gat merge <branch>
```

e.g.:
```bash
gat merge features
```

### Change

Reverts all the files to the commit with the hash of `<hash>`

syntax:
```bash
gat change <hash>
```
e.g.:
```bash
gat change cd326bab41e0b8aa0f6e5422e264bf32
```

### Goto

Reverts all the files to the commit named `<name>` from branch `<branch>`

syntax:
```bash
gat goto <branch> <name>
```
e.g.:
```bash
gat goto Main "Initial commit"
```

### Log

Shows data on every commit in branch `<branch>`

syntax:
```bash
gat log <branch>
```

e.g.:
```bash
gat log Main
```

### Status

Create a diff between the latest commit in branch `<branch>` and the file `<file>`

syntax:
```bash
gat status <branch> <file>
```

e.g.:
```bash
gat status feature main.py
```

### List-branches

Lists every branch gat can find

syntax:
```bash
gat list-branches
```

### List-commits

Lists every commit on branch `name`. Oftenimes you'll want `log` instead, since this only shows name and hash

syntax:
```bash
gat list-commits <name>
```

e.g.:
```bash
gat list-commits Main
```

## AI Disclaimer

Like every other project, this project uses no AI at all