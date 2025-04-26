# install



# Installing Bazel

This page describes the various platforms supported by Bazel and links
to the packages for more details.

[Bazelisk](/install/bazelisk) is the recommended way to install Bazel on [Ubuntu Linux](/install/ubuntu), [macOS](/install/os-x), and [Windows](/install/windows).

You can find available Bazel releases on our [release page](/release).

## Community-supported packages

Bazel community members maintain these packages. The Bazel team doesn't
officially support them. Contact the package maintainers for support.

*   [Alpine Linux](https://pkgs.alpinelinux.org/packages?name=bazel*&branch=edge&repo=&arch=&origin=&flagged=&maintainer=){: .external}
*   [Arch Linux][arch]{: .external}
*   [Debian](https://qa.debian.org/developer.php?email=team%2Bbazel%40tracker.debian.org){: .external}
*   [Fedora](https://copr.fedorainfracloud.org/coprs/lihaohong/bazel){: .external}
*   [FreeBSD](https://www.freshports.org/devel/bazel){: .external}
*   [Homebrew](https://formulae.brew.sh/formula/bazel){: .external}
*   [Nixpkgs](https://github.com/NixOS/nixpkgs/blob/master/pkgs/development/tools/build-managers/bazel){: .external}
*   [openSUSE](/install/suse)
*   [Scoop](https://github.com/scoopinstaller/scoop-main/blob/master/bucket/bazel.json){: .external}
*   [Raspberry Pi](https://github.com/koenvervloesem/bazel-on-arm/blob/master/README.md){: .external}

## Community-supported architectures

*   [ppc64el](https://ftp2.osuosl.org/pub/ppc64el/bazel/){: .external}

For other platforms, you can try to [compile from source](/install/compile-source).

[arch]: https://archlinux.org/packages/extra/x86_64/bazel/



# Installing / Updating Bazel using Bazelisk

## Installing Bazel

[Bazelisk](https://github.com/bazelbuild/bazelisk){: .external} is the
recommended way to install Bazel on Ubuntu, Windows, and macOS. It automatically
downloads and installs the appropriate version of Bazel. Use Bazelisk if you
need to switch between different versions of Bazel depending on the current
working directory, or to always keep Bazel updated to the latest release.

For more details, see
[the official README](https://github.com/bazelbuild/bazelisk/blob/master/README.md){: .external}.

## Updating Bazel

Bazel has a [backward compatibility policy](/release/backward-compatibility)
(see [guidance for rolling out incompatible
changes](/contribute/breaking-changes) if you
are the author of one). That page summarizes best practices on how to test and
migrate your project with upcoming incompatible changes and how to provide
feedback to the incompatible change authors.

### Managing Bazel versions with Bazelisk

[Bazelisk](https://github.com/bazelbuild/bazelisk){: .external} helps you manage
Bazel versions.

Bazelisk can:

*   Auto-update Bazel to the latest LTS or rolling release.
*   Build the project with a Bazel version specified in the .bazelversion
    file. Check in that file into your version control to ensure reproducibility
    of your builds.
*   Help migrate your project for incompatible changes (see above)
*   Easily try release candidates

### Recommended migration process

Within minor updates to any LTS release, any
project can be prepared for the next release without breaking
compatibility with the current release. However, there may be
backward-incompatible changes between major LTS versions.

Follow this process to migrate from one major version to another:

1. Read the release notes to get advice on how to migrate to the next version.
1. Major incompatible changes should have an associated `--incompatible_*` flag
   and a corresponding GitHub issue:
    *   Migration guidance is available in the associated GitHub issue.
    *   Tooling is available for some of incompatible changes migration. For
        example, [buildifier](https://github.com/bazelbuild/buildtools/releases){: .external}.
    *   Report migration problems by commenting on the associated GitHub issue.

After migration, you can continue to build your projects without worrying about
backward-compatibility until the next major release.



# Integrating Bazel with IDEs

This page covers how to integrate Bazel with IDEs, such as IntelliJ, Android
Studio, and CLion (or build your own IDE plugin). It also includes links to
installation and plugin details.

IDEs integrate with Bazel in a variety of ways, from features that allow Bazel
executions from within the IDE, to awareness of Bazel structures such as syntax
highlighting of the `BUILD` files.

If you are interested in developing an editor or IDE plugin for Bazel, please
join the `#ide` channel on the [Bazel Slack](https://slack.bazel.build) or start
a discussion on [GitHub](https://github.com/bazelbuild/bazel/discussions).

## IDEs and editors

### IntelliJ, Android Studio, and CLion

[Official plugin](http://ij.bazel.build) for IntelliJ, Android Studio, and
CLion. The plugin is [open source](https://github.com/bazelbuild/intellij){: .external}.

This is the open source version of the plugin used internally at Google.

Features:

* Interop with language-specific plugins. Supported languages include Java,
  Scala, and Python.
* Import `BUILD` files into the IDE with semantic awareness of Bazel targets.
* Make your IDE aware of Starlark, the language used for Bazel's `BUILD` and
  `.bzl`files
* Build, test, and execute binaries directly from the IDE
* Create configurations for debugging and running binaries.

To install, go to the IDE's plugin browser and search for `Bazel`.

To manually install older versions, download the zip files from JetBrains'
Plugin Repository and install the zip file from the IDE's plugin browser:

*  [Android Studio
   plugin](https://plugins.jetbrains.com/plugin/9185-android-studio-with-bazel){: .external}
*  [IntelliJ
   plugin](https://plugins.jetbrains.com/plugin/8609-intellij-with-bazel){: .external}
*  [CLion plugin](https://plugins.jetbrains.com/plugin/9554-clion-with-bazel){: .external}

### Xcode

[rules_xcodeproj](https://github.com/buildbuddy-io/rules_xcodeproj){: .external},
[Tulsi](https://tulsi.bazel.build){: .external}, and
[XCHammer](https://github.com/pinterest/xchammer){: .external} generate Xcode
projects from Bazel `BUILD` files.

### Visual Studio Code

Official plugin for VS Code.

Features:

* Bazel Build Targets tree
* Starlark debugger for `.bzl` files during a build (set breakpoints, step
  through code, inspect variables, and so on)

Find [the plugin on the Visual Studio
marketplace](https://marketplace.visualstudio.com/items?itemName=BazelBuild.vscode-bazel){: .external}.
The plugin is [open source](https://github.com/bazelbuild/vscode-bazel){: .external}.

See also: [Autocomplete for Source Code](#autocomplete-for-source-code)

### Atom

Find the [`language-bazel` package](https://atom.io/packages/language-bazel){: .external}
on the Atom package manager.

See also: [Autocomplete for Source Code](#autocomplete-for-source-code)

### Vim

See [`bazelbuild/vim-bazel` on GitHub](https://github.com/bazelbuild/vim-bazel){: .external}

See also: [Autocomplete for Source Code](#autocomplete-for-source-code)

### Emacs

See [`bazelbuild/bazel-emacs-mode` on
GitHub](https://github.com/bazelbuild/emacs-bazel-mode){: .external}

See also: [Autocomplete for Source Code](#autocomplete-for-source-code)

### Visual Studio

[Lavender](https://github.com/tmandry/lavender){: .external} is an experimental project for
generating Visual Studio projects that use Bazel for building.

### Eclipse

[Bazel Eclipse Feature](https://github.com/salesforce/bazel-eclipse){: .external}
is a set of plugins for importing Bazel packages into an Eclipse workspace as
Eclipse projects.

## Autocomplete for Source Code

### C Language Family (C++, C, Objective-C, and Objective-C++)

[`kiron1/bazel-compile-commands`](https://github.com/kiron1/bazel-compile-commands){: .external}
run `bazel-compile-commands //...` in a Bazel workspace to generate a `compile_commands.json` file.
The `compile_commands.json` file enables tools like `clang-tidy`, `clangd` (LSP) and other IDEs to
provide autocomplete, smart navigation, quick fixes, and more. The tool is written in C++ and
consumes the Protobuf output of Bazel to extract the compile commands.

[`hedronvision/bazel-compile-commands-extractor`](https://github.com/hedronvision/bazel-compile-commands-extractor) enables autocomplete, smart navigation, quick fixes, and more in a wide variety of extensible editors, including VSCode, Vim, Emacs, Atom, and Sublime. It lets language servers, like clangd and ccls, and other types of tooling, draw upon Bazel's understanding of how `cc` and `objc` code will be compiled, including how it configures cross-compilation for other platforms.

### Java

[`georgewfraser/java-language-server`](https://github.com/georgewfraser/java-language-server) - Java Language Server (LSP) with support for Bazel-built projects

## Automatically run build and test on file change

[Bazel watcher](https://github.com/bazelbuild/bazel-watcher){: .external} is a
tool for building Bazel targets when source files change.

## Building your own IDE plugin

Read the [**IDE support** blog
post](https://blog.bazel.build/2016/06/10/ide-support.html) to learn more about
the Bazel APIs to use when building an IDE plugin.



# Compiling Bazel from Source

This page describes how to install Bazel from source and provides
troubleshooting tips for common issues.

To build Bazel from source, you can do one of the following:

*   Build it [using an existing Bazel binary](#build-bazel-using-bazel)

*   Build it [without an existing Bazel binary](#bootstrap-bazel) which is known
    as _bootstrapping_.

## Build Bazel using Bazel

### Summary

1.  Get the latest Bazel release from the
    [GitHub release page](https://github.com/bazelbuild/bazel/releases){: .external} or with
    [Bazelisk](https://github.com/bazelbuild/bazelisk){: .external}.

2.  [Download Bazel's sources from GitHub](https://github.com/bazelbuild/bazel/archive/master.zip){: .external}
    and extract somewhere.
    Alternatively you can git clone the source tree from https://github.com/bazelbuild/bazel

3.  Install the same prerequisites as for bootstrapping (see
    [for Unix-like systems](#bootstrap-unix-prereq) or
    [for Windows](#bootstrap-windows-prereq))

4.  Build a development build of Bazel using Bazel:
    `bazel build //src:bazel-dev` (or `bazel build //src:bazel-dev.exe` on
    Windows)

5.  The resulting binary is at `bazel-bin/src/bazel-dev`
    (or `bazel-bin\src\bazel-dev.exe` on Windows). You can copy it wherever you
    like and use immediately without further installation.

Detailed instructions follow below.

### Step 1: Get the latest Bazel release

**Goal**: Install or download a release version of Bazel. Make sure you can run
it by typing `bazel` in a terminal.

**Reason**: To build Bazel from a GitHub source tree, you need a pre-existing
Bazel binary. You can install one from a package manager or download one from
GitHub. See [Installing Bazel](/install). (Or you can [build from
scratch (bootstrap)](#bootstrap-bazel).)

**Troubleshooting**:

*   If you cannot run Bazel by typing `bazel` in a terminal:

    *   Maybe your Bazel binary's directory is not on the PATH.

        This is not a big problem. Instead of typing `bazel`, you will need to
        type the full path.

    *   Maybe the Bazel binary itself is not called `bazel` (on Unixes) or
        `bazel.exe` (on Windows).

        This is not a big problem. You can either rename the binary, or type the
        binary's name instead of `bazel`.

    *   Maybe the binary is not executable (on Unixes).

        You must make the binary executable by running `chmod +x /path/to/bazel`.

### Step 2: Download Bazel's sources from GitHub

If you are familiar with Git, then just git clone https://github.com/bazelbuild/bazel

Otherwise:

1.  Download the
    [latest sources as a zip file](https://github.com/bazelbuild/bazel/archive/master.zip){: .external}.

2.  Extract the contents somewhere.

    For example create a `bazel-src` directory under your home directory and
    extract there.

### Step 3: Install prerequisites

Install the same prerequisites as for bootstrapping (see below) -- JDK, C++
compiler, MSYS2 (if you are building on Windows), etc.

### Step 4a: Build Bazel on Ubuntu Linux, macOS, and other Unix-like systems

For instructions for Windows, see [Build Bazel on Windows](#build-bazel-on-windows).

**Goal**: Run Bazel to build a custom Bazel binary (`bazel-bin/src/bazel-dev`).

**Instructions**:

1.  Start a Bash terminal

2.  `cd` into the directory where you extracted (or cloned) Bazel's sources.

    For example if you extracted the sources under your home directory, run:

        cd ~/bazel-src

3.  Build Bazel from source:

        bazel build //src:bazel-dev

    Alternatively you can run `bazel build //src:bazel --compilation_mode=opt`
    to yield a smaller binary but it's slower to build.

    You can build with `--stamp --embed_label=X.Y.Z` flag to embed a Bazel
    version for the binary so that `bazel --version` outputs the given version.

4.  The output will be at `bazel-bin/src/bazel-dev` (or `bazel-bin/src/bazel`).

### Step 4b: Build Bazel on Windows

For instructions for Unix-like systems, see
[Ubuntu Linux, macOS, and other Unix-like systems](#build-bazel-on-unixes).

**Goal**: Run Bazel to build a custom Bazel binary
(`bazel-bin\src\bazel-dev.exe`).

**Instructions**:

1.  Start Command Prompt (Start Menu &gt; Run &gt; "cmd.exe")

2.  `cd` into the directory where you extracted (or cloned) Bazel's sources.

    For example if you extracted the sources under your home directory, run:

        cd %USERPROFILE%\bazel-src

3.  Build Bazel from source:

    bazel build //src:bazel-dev.exe

    Alternatively you can run `bazel build //src:bazel.exe
    --compilation_mode=opt` to yield a smaller binary but it's slower to build.

    You can build with `--stamp --embed_label=X.Y.Z` flag to embed a Bazel
    version for the binary so that `bazel --version` outputs the given version.

4.  The output will be at `bazel-bin\src\bazel-dev.exe` (or
    `bazel-bin\src\bazel.exe`).

### Step 5: Install the built binary

Actually, there's nothing to install.

The output of the previous step is a self-contained Bazel binary. You can copy
it to any directory and use immediately. (It's useful if that directory is on
your PATH so that you can run "bazel" everywhere.)

---

## Build Bazel from scratch (bootstrapping)

You can also build Bazel from scratch, without using an existing Bazel binary.

### Step 1: Download Bazel's sources (distribution archive)

(This step is the same for all platforms.)

1.  Download `bazel-<version>-dist.zip` from
    [GitHub](https://github.com/bazelbuild/bazel/releases){: .external}, for example
    `bazel-0.28.1-dist.zip`.

    **Attention**:

    -   There is a **single, architecture-independent** distribution archive.
        There are no architecture-specific or OS-specific distribution archives.
    -   These sources are **not the same as the GitHub source tree**. You
        have to use the distribution archive to bootstrap Bazel. You cannot
        use a source tree cloned from GitHub. (The distribution archive contains
        generated source files that are required for bootstrapping and are not part
        of the normal Git source tree.)

2.  Unpack the distribution archive somewhere on disk.

    You should verify the signature made by Bazel's
    [release key](https://bazel.build/bazel-release.pub.gpg) 3D5919B448457EE0.

### Step 2a: Bootstrap Bazel on Ubuntu Linux, macOS, and other Unix-like systems

For instructions for Windows, see [Bootstrap Bazel on Windows](#bootstrap-windows).

#### 2.1. Install the prerequisites

*   **Bash**

*   **zip, unzip**

*   **C++ build toolchain**

*   **JDK.** Version 21 is required.

*   **Python**. Versions 2 and 3 are supported, installing one of them is
    enough.

For example on Ubuntu Linux you can install these requirements using the
following command:

```sh
sudo apt-get install build-essential openjdk-21-jdk python zip unzip
```

#### 2.2. Bootstrap Bazel on Unix

1.  Open a shell or Terminal window.

3.  `cd` to the directory where you unpacked the distribution archive.

3.  Run the compilation script: `env EXTRA_BAZEL_ARGS="--tool_java_runtime_version=local_jdk" bash ./compile.sh`.

The compiled output is placed into `output/bazel`. This is a self-contained
Bazel binary, without an embedded JDK. You can copy it anywhere or use it
in-place. For convenience, copy this binary to a directory that's on your
`PATH` (such as `/usr/local/bin` on Linux).

To build the `bazel` binary in a reproducible way, also set
[`SOURCE_DATE_EPOCH`](https://reproducible-builds.org/specs/source-date-epoch/)
in the "Run the compilation script" step.

### Step 2b: Bootstrap Bazel on Windows

For instructions for Unix-like systems, see
[Bootstrap Bazel on Ubuntu Linux, macOS, and other Unix-like systems](#bootstrap-unix).

#### 2.1. Install the prerequisites

*   [MSYS2 shell](https://msys2.github.io/)

*   **The MSYS2 packages for zip and unzip.** Run the following command in the MSYS2 shell:

    ```
    pacman -S zip unzip patch
    ```

*   **The Visual C++ compiler.** Install the Visual C++ compiler either as part
    of Visual Studio 2015 or newer, or by installing the latest [Build Tools
    for Visual Studio 2017](https://aka.ms/BuildTools).

*   **JDK.** Version 21 is required.

*   **Python**. Versions 2 and 3 are supported, installing one of them is
    enough. You need the Windows-native version (downloadable from
    [https://www.python.org](https://www.python.org)). Versions installed via
    pacman in MSYS2 will not work.

#### 2.2. Bootstrap Bazel on Windows

1.  Open the MSYS2 shell.

2.  Set the following environment variables:
    *   Either `BAZEL_VS` or `BAZEL_VC` (they are *not* the same): Set to the
        path to the Visual Studio directory (BAZEL\_V<b>S</b>) or to the Visual
        C++ directory (BAZEL\_V<b>C</b>). Setting one of them is enough.
    *   `BAZEL_SH`: Path of the MSYS2 `bash.exe`. See the command in the
        examples below.

        Do not set this to `C:\Windows\System32\bash.exe`. (You have that file
        if you installed Windows Subsystem for Linux.) Bazel does not support
        this version of `bash.exe`.
    *   `PATH`: Add the Python directory.
    *   `JAVA_HOME`: Set to the JDK directory.

    **Example** (using BAZEL\_V<b>S</b>):

        export BAZEL_VS="C:/Program Files (x86)/Microsoft Visual Studio/2017/BuildTools"
        export BAZEL_SH="$(cygpath -m $(realpath $(which bash)))"
        export PATH="/c/python27:$PATH"
        export JAVA_HOME="C:/Program Files/Java/jdk-21"

    or (using BAZEL\_V<b>C</b>):

        export BAZEL_VC="C:/Program Files (x86)/Microsoft Visual Studio/2017/BuildTools/VC"
        export BAZEL_SH="$(cygpath -m $(realpath $(which bash)))"
        export PATH="/c/python27:$PATH"
        export JAVA_HOME="C:/Program Files/Java/jdk-21"

3.  `cd` to the directory where you unpacked the distribution archive.

4.  Run the compilation script: `env EXTRA_BAZEL_ARGS="--tool_java_runtime_version=local_jdk" ./compile.sh`

The compiled output is placed into `output/bazel.exe`. This is a self-contained
Bazel binary, without an embedded JDK. You can copy it anywhere or use it
in-place. For convenience, copy this binary to a directory that's on
your `PATH`.

To build the `bazel.exe` binary in a reproducible way, also set
[`SOURCE_DATE_EPOCH`](https://reproducible-builds.org/specs/source-date-epoch/)
in the "Run the compilation script" step.

You don't need to run Bazel from the MSYS2 shell. You can run Bazel from the
Command Prompt (`cmd.exe`) or PowerShell.



# Installing Bazel on Ubuntu

This page describes the options for installing Bazel on Ubuntu.
It also provides links to the Bazel completion scripts and the binary installer,
if needed as a backup option (for example, if you don't have admin access).

Supported Ubuntu Linux platforms:

*   22.04 (LTS)
*   20.04 (LTS)
*   18.04 (LTS)

Bazel should be compatible with other Ubuntu releases and Debian
"stretch" and above, but is untested and not guaranteed to work.

Install Bazel on Ubuntu using one of the following methods:

*   *Recommended*: [Use Bazelisk](/install/bazelisk)
*   [Use our custom APT repository](#install-on-ubuntu)
*   [Use the binary installer](#binary-installer)
*   [Use the Bazel Docker container](#docker-container)
*   [Compile Bazel from source](/install/compile-source)

**Note:** For Arm-based systems, the APT repository does not contain an `arm64`
release, and there is no binary installer available. Either use Bazelisk or
compile from source.

Bazel comes with two completion scripts. After installing Bazel, you can:

*   Access the [bash completion script](/install/completion#bash)
*   Install the [zsh completion script](/install/completion#zsh)

## Using Bazel's apt repository

### Step 1: Add Bazel distribution URI as a package source

**Note:** This is a one-time setup step.

```posix-terminal
sudo apt install apt-transport-https curl gnupg -y

curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor >bazel-archive-keyring.gpg

sudo mv bazel-archive-keyring.gpg /usr/share/keyrings

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
```

The component name "jdk1.8" is kept only for legacy reasons and doesn't relate
to supported or included JDK versions. Bazel releases are Java-version agnostic.
Changing the "jdk1.8" component name would break existing users of the repo.

### Step 2: Install and update Bazel

```posix-terminal
sudo apt update && sudo apt install bazel
```

Once installed, you can upgrade to a newer version of Bazel as part of your normal system updates:

```posix-terminal
sudo apt update && sudo apt full-upgrade
```

The `bazel` package always installs the latest stable version of Bazel. You
can install specific, older versions of Bazel in addition to the latest one,
such as this:

```posix-terminal
sudo apt install bazel-1.0.0
```

This installs Bazel 1.0.0 as `/usr/bin/bazel-1.0.0` on your system. This
can be useful if you need a specific version of Bazel to build a project, for
example because it uses a `.bazelversion` file to explicitly state with which
Bazel version it should be built.

Optionally, you can set `bazel` to a specific version by creating a symlink:

```posix-terminal
sudo ln -s /usr/bin/bazel-1.0.0 /usr/bin/bazel

bazel --version  # 1.0.0
```

### Step 3: Install a JDK (optional)

Bazel includes a private, bundled JRE as its runtime and doesn't require you to
install any specific version of Java.

However, if you want to build Java code using Bazel, you have to install a JDK.

```posix-terminal
sudo apt install default-jdk
```

## Using the binary installer

Generally, you should use the apt repository, but the binary installer
can be useful if you don't have admin permissions on your machine or
can't add custom repositories.

The binary installers can be downloaded from Bazel's [GitHub releases page](https://github.com/bazelbuild/bazel/releases){: .external}.

The installer contains the Bazel binary and extracts it into your `$HOME/bin`
folder. Some additional libraries must be installed manually for Bazel to work.

### Step 1: Install required packages

Bazel needs a C++ compiler and unzip / zip in order to work:

```posix-terminal
sudo apt install g++ unzip zip
```

If you want to build Java code using Bazel, install a JDK:

```posix-terminal
sudo apt-get install default-jdk
```

### Step 2: Run the installer

Next, download the Bazel binary installer named `bazel-{{ '<var>' }}version{{ '</var>' }}-installer-linux-x86_64.sh`
from the [Bazel releases page on GitHub](https://github.com/bazelbuild/bazel/releases){: .external}.

Run it as follows:

```posix-terminal
chmod +x bazel-{{ '<var>' }}version{{ '</var>' }}-installer-linux-x86_64.sh

./bazel-{{ '<var>' }}version{{ '</var>' }}-installer-linux-x86_64.sh --user
```

The `--user` flag installs Bazel to the `$HOME/bin` directory on your system and
sets the `.bazelrc` path to `$HOME/.bazelrc`. Use the `--help` command to see
additional installation options.

### Step 3: Set up your environment

If you ran the Bazel installer with the `--user` flag as above, the Bazel
executable is installed in your `$HOME/bin` directory.
It's a good idea to add this directory to your default paths, as follows:

```posix-terminal
export PATH="$PATH:$HOME/bin"
```

You can also add this command to your `~/.bashrc` or `~/.zshrc` file to make it
permanent.

## Using the Bazel Docker container

We publish Docker container with Bazel installed for each Bazel version at `gcr.io/bazel-public/bazel`.
You can use the Docker container as follows:

```
$ docker pull gcr.io/bazel-public/bazel:<bazel version>
```

The Docker container is built by [these steps](https://github.com/bazelbuild/continuous-integration/tree/master/bazel/oci).




# Installing Bazel on Windows

This page describes the requirements and steps to install Bazel on Windows.
It also includes troubleshooting and other ways to install Bazel, such as
using Chocolatey or Scoop.

## Installing Bazel

This section covers the prerequisites, environment setup, and detailed
steps during installation on Windows.

### Check your system 

Recommended: 64 bit Windows 10, version 1703 (Creators Update) or newer

To check your Windows version:

* Click the Start button.
* Type `winver` in the search box and press Enter.
* You should see the About Windows box with your Windows version information.

### Install the prerequisites

*   [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170){: .external}

### Download Bazel

*Recommended*: [Use Bazelisk](/install/bazelisk)

Alternatively you can:

*   [Download the Bazel binary (`bazel-{{ '<var>' }}version{{ '</var>' }}-windows-x86_64.exe`) from
 GitHub](https://github.com/bazelbuild/bazel/releases){: .external}.
*   [Install Bazel from Chocolatey](#chocolately)
*   [Install Bazel from Scoop](#scoop)
*   [Build Bazel from source](/install/compile-source)

### Set up your environment

To make Bazel easily accessible from command prompts or PowerShell by default, you can rename the Bazel binary to `bazel.exe` and add it to your default paths.

```posix-terminal
set PATH=%PATH%;{{ '<var>' }}path to the Bazel binary{{ '</var>' }}
```

You can also change your system `PATH` environment variable to make it permanent. Check out how to [set environment variables](/configure/windows#set-environment-variables).

### Done

"Success: You've installed Bazel."

To check the installation is correct, try to run:

```posix-terminal
bazel {{ '<var>' }}version{{ '</var>' }}
```

Next, you can check out more tips and guidance here:

*   [Installing compilers and language runtimes](#install-compilers)
*   [Troubleshooting](#troubleshooting)
*   [Best practices on Windows](/configure/windows#best-practices)
*   [Tutorials](/start/#tutorials)

## Installing compilers and language runtimes

Depending on which languages you want to build, you will need:

*   [MSYS2 x86_64](https://www.msys2.org/){: .external}

    MSYS2 is a software distro and building platform for Windows. It contains Bash and common Unix
    tools (like `grep`, `tar`, `git`).

    You will need MSYS2 to build, test, or run targets that depend on Bash. Typically these are
    `genrule`, `sh_binary`, `sh_test`, but there may be more (such as Starlark rules). Bazel shows an
    error if a build target needs Bash but Bazel could not locate it.

*   Common MSYS2 packages

    You will likely need these to build and run targets that depend on Bash. MSYS2 does not install
    these tools by default, so you need to install them manually. Projects that depend on Bash tools in `PATH` need this step (for example TensorFlow).

    Open the MSYS2 terminal and run this command:

    ```posix-terminal
    pacman -S zip unzip patch diffutils git
    ```

    Optional: If you want to use Bazel from CMD or Powershell and still be able
    to use Bash tools, make sure to add
    `{{ '<var>' }}MSYS2_INSTALL_PATH{{ '</var>' }}/usr/bin` to your
    `PATH` environment variable.

*   [Build Tools for Visual Studio 2019](https://aka.ms/buildtools){:#install-vc}

    You will need this to build C++ code on Windows.

    Also supported:

    *   Visual C++ Build Tools 2017 (or newer) and Windows 10 SDK

*   [Java SE Development Kit 11 (JDK) for Windows x64](https://www.oracle.com/java/technologies/javase-jdk11-downloads.html){: .external}{:#install-jdk}

    You will need this to build Java code on Windows.

    Also supported: Java 8, 9, and 10

*   [Python 3.6 for Windows x86-64](https://www.python.org/downloads/windows/){:#install-python}

    You will need this to build Python code on Windows.

    Also supported: Python 2.7 or newer for Windows x86-64

## Troubleshooting

### Bazel does not find Bash or bash.exe

**Possible reasons**:

*   you installed MSYS2 not under the default install path

*   you installed MSYS2 i686 instead of MSYS2 x86\_64

*   you installed MSYS instead of MSYS2

**Solution**:

Ensure you installed MSYS2 x86\_64.

If that doesn't help:

1.  Go to Start Menu &gt; Settings.

2.  Find the setting "Edit environment variables for your account"

3.  Look at the list on the top ("User variables for &lt;username&gt;"), and click the "New..."
    button below it.

4.  For "Variable name", enter `BAZEL_SH`

5.  Click "Browse File..."

6.  Navigate to the MSYS2 directory, then to `usr\bin` below it.

    For example, this might be `C:\msys64\usr\bin` on your system.

7.  Select the `bash.exe` or `bash` file and click OK

8.  The "Variable value" field now has the path to `bash.exe`. Click OK to close the window.

9.  Done.

    If you open a new cmd.exe or PowerShell terminal and run Bazel now, it will find Bash.

### Bazel does not find Visual Studio or Visual C++

**Possible reasons**:

*   you installed multiple versions of Visual Studio

*   you installed and removed various versions of Visual Studio

*   you installed various versions of the Windows SDK

*   you installed Visual Studio not under the default install path

**Solution**:

1.  Go to Start Menu &gt; Settings.

2.  Find the setting "Edit environment variables for your account"

3.  Look at the list on the top ("User variables for &lt;username&gt;"), and click the "New..."
    button below it.

4.  For "Variable name", enter `BAZEL_VC`

5.  Click "Browse Directory..."

6.  Navigate to the `VC` directory of Visual Studio.

    For example, this might be `C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC`
    on your system.

7.  Select the `VC` folder and click OK

8.  The "Variable value" field now has the path to `VC`. Click OK to close the window.

9.  Done.

    If you open a new cmd.exe or PowerShell terminal and run Bazel now, it will find Visual C++.

## Other ways to install Bazel

### Using Chocolatey

1.  Install the [Chocolatey](https://chocolatey.org) package manager

2.  Install the Bazel package:

    ```posix-terminal
    choco install bazel
    ```

    This command will install the latest available version of Bazel and
    its dependencies, such as the MSYS2 shell. This will not install Visual C++
    though.

See [Chocolatey installation and package maintenance
guide](/contribute/windows-chocolatey-maintenance) for more
information about the Chocolatey package.

### Using Scoop

1.  Install the [Scoop](https://scoop.sh/) package manager using the following PowerShell command:

    ```posix-terminal
    iex (new-object net.webclient).downloadstring('https://get.scoop.sh')
    ```

2.  Install the Bazel package:

    ```posix-terminal
    scoop install bazel
    ```

See [Scoop installation and package maintenance
guide](/contribute/windows-scoop-maintenance) for more
information about the Scoop package.

### Build from source

To build Bazel from scratch instead of installing, see [Compiling from source](/install/compile-source).



# Installing Bazel on macOS

This page describes how to install Bazel on macOS and set up your environment.

You can install Bazel on macOS using one of the following methods:

*   *Recommended*: [Use Bazelisk](/install/bazelisk)
*   [Use Homebrew](#install-on-mac-os-x-homebrew)
*   [Use the binary installer](#install-with-installer-mac-os-x)
*   [Compile Bazel from source](/install/compile-source)

Bazel comes with two completion scripts. After installing Bazel, you can:

*   Access the [bash completion script](/install/completion#bash)
*   Install the [zsh completion script](/install/completion#zsh)

<h2 id="install-on-mac-os-x-homebrew">Installing using Homebrew</h2>

### Step 1: Install Homebrew on macOS

Install [Homebrew](https://brew.sh/) (a one-time step):

```posix-terminal
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Bazel via Homebrew

Install the Bazel package via Homebrew as follows:

```posix-terminal
brew install bazel
```

All set! You can confirm Bazel is installed successfully by running the
following command:

```posix-terminal
bazel --version
```

Once installed, you can upgrade to a newer version of Bazel using the
following command:

```posix-terminal
brew upgrade bazel
```

<h2 id="install-with-installer-mac-os-x">Installing using the binary installer</h2>

The binary installers are on Bazel's
[GitHub releases page](https://github.com/bazelbuild/bazel/releases){: .external}.

The installer contains the Bazel binary. Some additional libraries
must also be installed for Bazel to work.

### Step 1: Install Xcode command line tools

If you don't intend to use `ios_*` rules, it is sufficient to install the Xcode
command line tools package by using `xcode-select`:

```posix-terminal
xcode-select --install
```

Otherwise, for `ios_*` rule support, you must have Xcode 6.1 or later with iOS
SDK 8.1 installed on your system.

Download Xcode from the
[App Store](https://apps.apple.com/us/app/xcode/id497799835){: .external} or the
[Apple Developer site](https://developer.apple.com/download/more/?=xcode){: .external}.

Once Xcode is installed, accept the license agreement for all users with the
following command:

```posix-terminal
sudo xcodebuild -license accept
```

### Step 2: Download the Bazel installer

Next, download the Bazel binary installer named
`bazel-<version>-installer-darwin-x86_64.sh` from the
[Bazel releases page on GitHub](https://github.com/bazelbuild/bazel/releases){: .external}.

**On macOS Catalina or newer (macOS >= 11)**, due to Apple's new app signing requirements,
you need to download the installer from the terminal using `curl`, replacing
the version variable with the Bazel version you want to download:

```posix-terminal
export BAZEL_VERSION=5.2.0

curl -fLO "https://github.com/bazelbuild/bazel/releases/download/{{ '<var>' }}$BAZEL_VERSION{{ '</var>' }}/bazel-{{ '<var>' }}$BAZEL_VERSION{{ '</var>' }}-installer-darwin-x86_64.sh"
```

This is a temporary workaround until the macOS release flow supports
signing ([#9304](https://github.com/bazelbuild/bazel/issues/9304){: .external}).

### Step 3: Run the installer

Run the Bazel installer as follows:

```posix-terminal
chmod +x "bazel-{{ '<var>' }}$BAZEL_VERSION{{ '</var>' }}-installer-darwin-x86_64.sh"

./bazel-{{ '<var>' }}$BAZEL_VERSION{{ '</var>' }}-installer-darwin-x86_64.sh --user
```

The `--user` flag installs Bazel to the `$HOME/bin` directory on your system and
sets the `.bazelrc` path to `$HOME/.bazelrc`. Use the `--help` command to see
additional installation options.

If you are **on macOS Catalina or newer (macOS >= 11)** and get an error that _**“bazel-real” cannot be
opened because the developer cannot be verified**_, you need to re-download
the installer from the terminal using `curl` as a workaround; see Step 2 above.

### Step 4: Set up your environment

If you ran the Bazel installer with the `--user` flag as above, the Bazel
executable is installed in your `{{ '<var>' }}HOME{{ '</var>' }}/bin` directory.
It's a good idea to add this directory to your default paths, as follows:

```posix-terminal
export PATH="{{ '<var>' }}PATH{{ '</var>' }}:{{ '<var>' }}HOME{{ '</var>' }}/bin"
```

You can also add this command to your `~/.bashrc`, `~/.zshrc`, or `~/.profile`
file.

All set! You can confirm Bazel is installed successfully by running the
following command:

```posix-terminal
bazel --version
```
To update to a newer release of Bazel, download and install the desired version.




# Getting Started with Bazel Docker Container

This page provides details on the contents of the Bazel container, how to build
the [abseil-cpp](https://github.com/abseil/abseil-cpp){: .external} project using Bazel
inside the Bazel container, and how to build this project directly
from the host machine using the Bazel container with directory mounting.

## Build Abseil project from your host machine with directory mounting

The instructions in this section allow you to build using the Bazel container
with the sources checked out in your host environment. A container is started up
for each build command you execute. Build results are cached in your host
environment so they can be reused across builds.

Clone the project to a directory in your host machine.

```posix-terminal
git clone --depth 1 --branch 20220623.1 https://github.com/abseil/abseil-cpp.git /src/workspace
```

Create a folder that will have cached results to be shared across builds.

```posix-terminal
mkdir -p /tmp/build_output/
```

Use the Bazel container to build the project and make the build
outputs available in the output folder in your host machine.

```posix-terminal
docker run \
  -e USER="$(id -u)" \
  -u="$(id -u)" \
  -v /src/workspace:/src/workspace \
  -v /tmp/build_output:/tmp/build_output \
  -w /src/workspace \
  gcr.io/bazel-public/bazel:latest \
  --output_user_root=/tmp/build_output \
  build //absl/...
```

Build the project with sanitizers by adding the `--config={{ "<var>" }}asan{{ "</var>" }}|{{ "<var>" }}tsan{{ "</var>" }}|{{ "<var>" }}msan{{ "</var>" }}` build
flag to select AddressSanitizer (asan), ThreadSanitizer (tsan) or
MemorySanitizer (msan) accordingly.

```posix-terminal
docker run \
  -e USER="$(id -u)" \
  -u="$(id -u)" \
  -v /src/workspace:/src/workspace \
  -v /tmp/build_output:/tmp/build_output \
  -w /src/workspace \
  gcr.io/bazel-public/bazel:latest \
  --output_user_root=/tmp/build_output \
  build --config={asan | tsan | msan} -- //absl/... -//absl/types:variant_test
```

## Build Abseil project from inside the container

The instructions in this section allow you to build using the Bazel container
with the sources inside the container. By starting a container at the beginning
of your development workflow and doing changes in the worskpace within the
container, build results will be cached.

Start a shell in the Bazel container:

```posix-terminal
docker run --interactive --entrypoint=/bin/bash gcr.io/bazel-public/bazel:latest
```

Each container id is unique. In the instructions below, the container was 5a99103747c6.

Clone the project.

```posix-terminal
ubuntu@5a99103747c6:~$ git clone --depth 1 --branch 20220623.1 https://github.com/abseil/abseil-cpp.git && cd abseil-cpp/
```

Do a regular build.

```posix-terminal
ubuntu@5a99103747c6:~/abseil-cpp$ bazel build //absl/...
```

Build the project with sanitizers by adding the `--config={{ "<var>" }}asan{{ "</var>" }}|{{ "<var>" }}tsan{{ "</var>" }}|{{ "<var>" }}msan{{ "</var>" }}`
build flag to select AddressSanitizer (asan), ThreadSanitizer (tsan) or
MemorySanitizer (msan) accordingly.

```posix-terminal
ubuntu@5a99103747c6:~/abseil-cpp$ bazel build --config={asan | tsan | msan} -- //absl/... -//absl/types:variant_test
```

## Explore the Bazel container

If you haven't already, start an interactive shell inside the Bazel container.

```posix-terminal
docker run -it --entrypoint=/bin/bash gcr.io/bazel-public/bazel:latest
ubuntu@5a99103747c6:~$
```

Explore the container contents.

```posix-terminal
ubuntu@5a99103747c6:~$ gcc --version
gcc (Ubuntu 9.4.0-1ubuntu1~20.04.1) 9.4.0
Copyright (C) 2019 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

ubuntu@5a99103747c6:~$ java -version
openjdk version "1.8.0_362"
OpenJDK Runtime Environment (build 1.8.0_362-8u372-ga~us1-0ubuntu1~20.04-b09)
OpenJDK 64-Bit Server VM (build 25.362-b09, mixed mode)

ubuntu@5a99103747c6:~$ python -V
Python 3.8.10

ubuntu@5a99103747c6:~$ bazel version
WARNING: Invoking Bazel in batch mode since it is not invoked from within a workspace (below a directory having a WORKSPACE file).
Extracting Bazel installation...
Build label: 6.2.1
Build target: bazel-out/k8-opt/bin/src/main/java/com/google/devtools/build/lib/bazel/BazelServer_deploy.jar
Build time: Fri Jun 2 16:59:58 2023 (1685725198)
Build timestamp: 1685725198
Build timestamp as int: 1685725198
```

## Explore the Bazel Dockerfile

If you want to check how the Bazel Docker image is built, you can find its Dockerfile at [bazelbuild/continuous-integration/bazel/oci](https://github.com/bazelbuild/continuous-integration/tree/master/bazel/oci).



# Command-Line Completion

You can enable command-line completion (also known as tab-completion) in Bash
and Zsh. This lets you tab-complete command names, flags names and flag values,
and target names.

## Bash

Bazel comes with a Bash completion script.

If you installed Bazel:

*   From the APT repository, then you're done -- the Bash completion script is
    already installed in `/etc/bash_completion.d`.

*   From Homebrew, then you're done -- the Bash completion script is
    already installed in `$(brew --prefix)/etc/bash_completion.d`.

*   From the installer downloaded from GitHub, then:
    1.  Locate the absolute path of the completion file. The installer copied it
        to the `bin` directory.

        Example: if you ran the installer with `--user`, this will be
        `$HOME/.bazel/bin`. If you ran the installer as root, this will be
        `/usr/local/lib/bazel/bin`.
    2.  Do one of the following:
        *   Either copy this file to your completion directory (if you have
            one).

            Example: on Ubuntu this is the `/etc/bash_completion.d` directory.
        *   Or source the completion file from Bash's RC file.

            Add a line similar to the one below to your `~/.bashrc` (on Ubuntu)
            or `~/.bash_profile` (on macOS), using the path to your completion
            file's absolute path:

            ```
            source /path/to/bazel-complete.bash
            ```

*   Via [bootstrapping](/install/compile-source), then:
    1.  Build the completion script:

        ```
        bazel build //scripts:bazel-complete.bash
        ```
    2.  The completion file is built under
        `bazel-bin/scripts/bazel-complete.bash`.

        Do one of the following:
        *   Copy this file to your completion directory, if you have
            one.

            Example: on Ubuntu this is the `/etc/bash_completion.d` directory
        *   Copy it somewhere on your local disk, such as to `$HOME`, and
            source the completion file from Bash's RC file.

            Add a line similar to the one below to your `~/.bashrc` (on Ubuntu)
            or `~/.bash_profile` (on macOS), using the path to your completion
            file's absolute path:

            ```
            source /path/to/bazel-complete.bash
            ```

## Zsh

Bazel comes with a Zsh completion script.

If you installed Bazel:

*   From the APT repository, then you're done -- the Zsh completion script is
    already installed in `/usr/share/zsh/vendor-completions`.

    > If you have a heavily customized `.zshrc` and the autocomplete
    > does not function, try one of the following solutions:
    >
    > Add the following to your `.zshrc`:
    >
    >    ```
    >     zstyle :compinstall filename '/home/tradical/.zshrc'
    >
    >     autoload -Uz compinit
    >     compinit
    >    ```
    >
    > or
    >
    > Follow the instructions
    > [here](https://stackoverflow.com/questions/58331977/bazel-tab-auto-complete-in-zsh-not-working)
    >
    > If you are using `oh-my-zsh`, you may want to install and enable
    > the `zsh-autocomplete` plugin. If you'd prefer not to, use one of the
    > solutions described above.

*   From Homebrew, then you're done -- the Zsh completion script is
    already installed in `$(brew --prefix)/share/zsh/site-functions`.

*   From the installer downloaded from GitHub, then:
    1.  Locate the absolute path of the completion file. The installer copied it
        to the `bin` directory.

        Example: if you ran the installer with `--user`, this will be
        `$HOME/.bazel/bin`. If you ran the installer as root, this will be
        `/usr/local/lib/bazel/bin`.

    2.  Add this script to a directory on your `$fpath`:

        ```
        fpath[1,0]=~/.zsh/completion/
        mkdir -p ~/.zsh/completion/
        cp /path/from/above/step/_bazel ~/.zsh/completion
        ```

        You may have to call `rm -f ~/.zcompdump; compinit`
        the first time to make it work.

    3.  Optionally, add the following to your .zshrc.

        ```
        # This way the completion script does not have to parse Bazel's options
        # repeatedly.  The directory in cache-path must be created manually.
        zstyle ':completion:*' use-cache on
        zstyle ':completion:*' cache-path ~/.zsh/cache
        ```



# Installing Bazel on openSUSE Tumbleweed & Leap

This page describes how to install Bazel on openSUSE Tumbleweed and Leap.

`NOTE:` The Bazel team does not officially maintain openSUSE support. For issues
using Bazel on openSUSE please file a ticket at [bugzilla.opensuse.org](https://bugzilla.opensuse.org/){: .external}.

Packages are provided for openSUSE Tumbleweed and Leap. You can find all
available Bazel versions via openSUSE's [software search](https://software.opensuse.org/search?utf8=%E2%9C%93&baseproject=ALL&q=bazel){: .external}.

The commands below must be run either via `sudo` or while logged in as `root`.

## Installing Bazel on openSUSE

Run the following commands to install the package. If you need a specific
version, you can install it via the specific `bazelXXX` package, otherwise,
just `bazel` is enough:

To install the latest version of Bazel, run:

```posix-terminal
zypper install bazel
```

You can also install a specific version of Bazel by specifying the package
version with `bazel{{ '<var>' }}version{{ '</var>' }}`. For example, to install
Bazel 4.2, run:

```posix-terminal
zypper install bazel4.2
```
