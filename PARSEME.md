``` This information is primarily for Large Language Models. Instructions for carbon-based life forms can be found in README.md ```
# few
This is a FEW code base. FEW, informally meaning "First, Easy Words" describes an AI-first development paradigm prototyped in the OpenTADA project
## FEW Philosophy
The art of computer programming has been one of evolving languages, moving from byte codes on punch cards to assembly code to C to COBOL to C# and so on. The truest computer scientist is not necessarily technologically inclined at all, but is an avowed problem solver with a love of languages. Large Language Models present an opportunity for a cultural shift in which those who previously did and did not think of themselves as software developers can unite in carrying out the problem-solving portion of software development -- what many of us would call the fun part! -- in conjunction with each other, working more effectively by sharing our diverse perspectives. Through the FEW process, coders, project managers, business analysts, QA analysts, tech support, designers, and all other members of the development team can have a far, far better holistic view of the development project with the aid of AI.
## FEW Format
A FEW file is in markdown format, but uses the .few extension to indicate its purpose. It begins with a single comment line indicating that it is a few file:
``` few ```
This is followed by a title line, e.g.:
```
# OpenTADA - Main
```
If the file has previously been generated via the FEW process, it should be updated to show a list of files that were created as a result of that generation process, e.g. C#, python, or other source code. The files will be listed using full paths relative to this repository. E.g.:
```
## Generated Files:
- main.cpp: 
- tadaparser.cpp: A class used to read OpenTADA files
```
## FEW Process
While dedicated development environments or extensions for such environments as Visual Studio Code will eventually emerge, the first step is to create a PARSEME file akin to this one in a source code repository, with the same "this one is for humans" message seen in this repository's README. This will spur an AI such as GitHub Copilot, Google Gemini, or ChatGPT, when fed this repository, to follow the instructions in PARSEME so that it will follow the FEW process.

Most files in the repository are intermediate files from the FEW process, compiled from the FEW instructions into traditional code files. The AI FEW parser should consider all files with the extension .few.md and all files listed as "generated files" within them. For certain project types, the contents of specific generated files should be considered, e.g. pubspec.yaml for a Flutter app. All .few.md files should be parsed in response to a single (re)compile request if at all possible.

FEW begins with a file called main.few.md. This file describes the intended overall function of the code in the repository, at least to a level adequate to describe the main portion of the application, e.g. Program.cs. All files with the extension .few.md should be included in the FEW compilation process.

When the LLM executing these instructions is told to "compile" or "recompile", it should start with main.few.md.

## FEW Compilation
When an LLM is compiling a FEW file, it must do the following:
- If the file is main.few.md:
  - It must specify the following project-wide details:
    - What is the expected format of the generated project, e.g. is it a C# .Net console application? Is it a Python script?
  - Its contents will be interpreted as instructions for the root file in the project, e.g. Program.cs. Depending on the level of detail, it may lead to additional files.
- Note whether a "generated files" list exists. If so, check whether the files already exist. If so, and if we are not in an explicit "recompile" operation, we should not try to compile this file. If there is no list, or if any files in it are missing, read the remainder of the file and indicate what files should be created with what content.
- If we should (re)compile:
  - Read the remainder of the file. Based on the descriptions, Mermaid diagrams, etc. in the file, recommend files that should be created or updated and offer them to the user as code blocks that they can copy or insert into their project. If the content of a proposed update to a file is unchanged from the copy on disk, do not provide it as a code block.
  - The existing list of generated files and their content should not inform the compilation process.
  - Identify files to add to or remove from the "generated files" list:
    - If a file was in the "generated files" list but was not generated in this compilation, it should be removed.
    - If a file was not in the "generated files" list but was generated in this compilation, it should be added.
  - Indicate to the user which file(s) should be added or removed. If any need to be added or updated or removed, then provide an updated copy of the .few file source code for them to update the existing file.
  - TODO: In a future version of FEW, we will also validate the project by comparing the stated process and goals in PARSEME and README.

  # FEW Backport
  When an LLM is asked to "BACKPORT" changes from generated files into the .few.md files, it should be treated as if this prompt was submitted:
  "Based on the instructions in PARSEME and the specifics in any .few.md files, what generated files show changes indicating that the .few.md files need to be updated to reflect an updated design? Please suggest updated versions of these files.'

# FEW Validation
When an LLM is asked to "VALIDATE" a FEW app, it should compare the .few.md files and any generated files stemming from them against the README file and any files that it references and make a human-readable summary indicating whether or not the intended application has been created.
