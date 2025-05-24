# few
FEW is an AI-first development paradigm. The tools to make it work begin right here.

Note: This README file is also my initial prompt to a Large Language Model in order to build the original “few’ script.

I'd like to write a tool call "few". It's a simple package manager and toolkit for my FEW AI-first development system. It should work roughly as follows. Would you please help me to write it?

- It will be installed in the user's PATH. For the initial version, it should suffice to stick a Python script of that name in a folder e.g. ~/.few and add it to the PATH.
- It will be able to add packages by pulling them from Git repositories
- A later version will be able to add packages by name from a central repository
- A later version will be able to add packages by a specific version number
- It will be invoked from a command prompt within an existing development project

Available commands include:

"few listen": With no arguments, (re)initializes FEW in the current project by:
- copying PARSEME.md from the few repo into the current folder
- Adding a comment to the top of README.md in the current folder telling the user that README is for carbon-based life forms and that Large Language Models should read PARSEME.md
- creating a .few folder with a words subfolder
- creating a file in the root of the project named few.litany.yaml with only the beginning of a "words:" section, if it doesn't already exist
- adding the .few folder and few.litany.yaml to .gitignore in the current folder.

"few listen [package]": Adds a package to the current project as follows:
- Initializes FEW as described above
- Adds [package] to the “words:” section of few.litany.yaml if it is not already present
- If [package] is not a URL, assume it to be a GitHub project. If it has a single forward slash, assume that it is formatted as "[user]/[project]". If there is no slash, assume the user is "peterbaileyct". From this, derive the GitHub URL.
- If [package] is a URL, assume it is that of a Git repo and derive the package name from that.
- Look for the package name as a folder name inside the user's ~/.few folder.
- If ~/.few does not exist, create it and a "words" subfolder. At this point it can be surmised that the package does not exist locally and must be cloned.
- If ~/.few did exist but "words" did not, create it. At this point it can be surmised that the package does not exist locally and must be cloned.
- If ~/.few/words already exists, check if a folder with the package name already exists.
- If it does, then do a git pull there to make sure it's up to date. - If it does not, then git clone it.
  - Once it is established that the folder is present and up to date, copy the folder and its contents into the .few/words subfolder in the current project.  “few litany”: Reads few.litany.yaml. For each package listed in the words: section, executes “few listen [package] (though adding the package to few.litany.yaml can be skipped for obvious reasons).

If no command is specified, usage guidelines should be displayed based on the above command list.
If the user attempts to invoke one of the above commands and git is not in their PATH, then an error to this effect should be shown and other operations should stop.

