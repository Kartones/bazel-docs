# configure



# Best Practices

This page assumes you are familiar with Bazel and provides guidelines and
advice on structuring your projects to take full advantage of Bazel's features.

The overall goals are:

- To use fine-grained dependencies to allow parallelism and incrementality.
- To keep dependencies well-encapsulated.
- To make code well-structured and testable.
- To create a build configuration that is easy to understand and maintain.

These guidelines are not requirements: few projects will be able to adhere to
all of them.  As the man page for lint says, "A special reward will be presented
to the first person to produce a real program that produces no errors with
strict checking." However, incorporating as many of these principles as possible
should make a project more readable, less error-prone, and faster to build.

This page uses the requirement levels described in
[this RFC](https://www.ietf.org/rfc/rfc2119.txt){: .external}.

## Running builds and tests

A project should always be able to run `bazel build //...` and
`bazel test //...` successfully on its stable branch. Targets that are necessary
but do not build under certain circumstances (such as,require specific build
flags, don't build on a certain platform, require license agreements) should be
tagged as specifically as possible (for example, "`requires-osx`"). This
tagging allows targets to be filtered at a more fine-grained level than the
"manual" tag and allows someone inspecting the `BUILD` file to understand what
a target's restrictions are.

## Third-party dependencies

You may declare third-party dependencies:

*   Either declare them as remote repositories in the `MODULE.bazel` file.
*   Or put them in a directory called `third_party/` under your workspace directory.

## Depending on binaries

Everything should be built from source whenever possible. Generally this means
that, instead of depending on a library `some-library.so`, you'd create a
`BUILD` file and build `some-library.so` from its sources, then depend on that
target.

Always building from source ensures that a build is not using a library that
was built with incompatible flags or a different architecture. There are also
some features like coverage, static analysis, or dynamic analysis that only
work on the source.

## Versioning

Prefer building all code from head whenever possible. When versions must be
used, avoid including the version in the target name (for example, `//guava`,
not `//guava-20.0`). This naming makes the library easier to update (only one
target needs to be updated). It's also more resilient to diamond dependency
issues: if one library depends on `guava-19.0` and one depends on `guava-20.0`,
you could end up with a library that tries to depend on two different versions.
If you created a misleading alias to point both targets to one `guava` library,
then the `BUILD` files are misleading.

## Using the `.bazelrc` file

For project-specific options, use the configuration file your
`{{ '<var>' }}workspace{{ '</var>' }}/.bazelrc` (see [bazelrc format](/run/bazelrc)).

If you want to support per-user options for your project that you **do not**
want to check into source control, include the line:

```
try-import %workspace%/user.bazelrc
```
(or any other file name) in your `{{ '<var>' }}workspace{{ '</var>' }}/.bazelrc`
and add `user.bazelrc` to your `.gitignore`.

## Packages

Every directory that contains buildable files should be a package. If a `BUILD`
file refers to files in subdirectories (such as, `srcs = ["a/b/C.java"]`) it's
a sign that a `BUILD` file should be added to that subdirectory. The longer
this structure exists, the more likely circular dependencies will be
inadvertently created, a target's scope will creep, and an increasing number
of reverse dependencies will have to be updated.



# Using Bazel on Windows

This page covers Best Practices for using Bazel on Windows. For installation
instructions, see [Install Bazel on Windows](/install/windows).

## Known issues

Windows-related Bazel issues are marked with the "area-Windows" label on GitHub.
[GitHub-Windows].

[GitHub-Windows]: https://github.com/bazelbuild/bazel/issues?q=is%3Aopen+is%3Aissue+label%3Aarea-Windows

## Best practices

### Avoid long path issues

Some tools have the [Maximum Path Length Limitation](https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file#maximum-path-length-limitation){: .external} on Windows, including the MSVC compiler.
To avoid hitting this issue, you can specify a short output directory for Bazel by the [\-\-output_user_root](/reference/command-line-reference#flag--output_user_root) flag.

For example, add the following line to your bazelrc file:

```none
startup --output_user_root=C:/tmp
```

### Enable 8.3 filename support

Bazel attempts to create a short name version for long file paths. But to do so the [8.3 filename support](https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/fsutil-8dot3name){: .external} needs to be enabled for the volume in which the file with the long path resides. You can enable 8.3 name creation in all volumes by running the following command:

```posix-terminal
fsutil 8dot3name set 0
```

### Enable symlink support

Some features require Bazel to be able to create file symlinks on Windows,
either by enabling
[Developer Mode](https://docs.microsoft.com/en-us/windows/uwp/get-started/enable-your-device-for-development){: .external}
(on Windows 10 version 1703 or newer), or by running Bazel as an administrator.
This enables the following features:

* [\-\-windows_enable_symlinks](/reference/command-line-reference#flag--windows_enable_symlinks)
* [\-\-enable_runfiles](/reference/command-line-reference#flag--enable_runfiles)

To make it easier, add the following lines to your bazelrc file:

```none
startup --windows_enable_symlinks

build --enable_runfiles
```

**Note**: Creating symlinks on Windows is an expensive operation. The `--enable_runfiles` flag can potentially create a large amount of file symlinks. Only enable this feature when you need it.

<!-- TODO(pcloudy): https://github.com/bazelbuild/bazel/issues/6402
                    Write a doc about runfiles library and add a link to it here -->

### Running Bazel: MSYS2 shell vs. command prompt vs. PowerShell

**Recommendation:** Run Bazel from the command prompt (`cmd.exe`) or from
PowerShell.

As of 2020-01-15, **do not** run Bazel from `bash` -- either
from MSYS2 shell, or Git Bash, or Cygwin, or any other Bash variant. While Bazel
may work for most use cases, some things are broken, like
[interrupting the build with Ctrl+C from MSYS2](https://github.com/bazelbuild/bazel/issues/10573){: .external}).
Also, if you choose to run under MSYS2, you need to disable MSYS2's
automatic path conversion, otherwise MSYS will convert command line arguments
that _look like_ Unix paths (such as `//foo:bar`) into Windows paths. See
[this StackOverflow answer](https://stackoverflow.com/a/49004265/7778502){: .external}
for details.

### Using Bazel without Bash (MSYS2)

#### Using bazel build without Bash

Bazel versions before 1.0 used to require Bash to build some rules.

Starting with Bazel 1.0, you can build any rule without Bash unless it is a:

- `genrule`, because genrules execute Bash commands
- `sh_binary` or `sh_test` rule, because these inherently need Bash
- Starlark rule that uses `ctx.actions.run_shell()` or `ctx.resolve_command()`

However, `genrule` is often used for simple tasks like
[copying a file](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/copy_file.bzl){: .external}
or [writing a text file](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/write_file.bzl){: .external}.
Instead of using `genrule` (and depending on Bash) you may find a suitable rule
in the
[bazel-skylib repository](https://github.com/bazelbuild/bazel-skylib/tree/main/rules){: .external}.
When built on Windows, **these rules do not require Bash**.

#### Using bazel test without Bash

Bazel versions before 1.0 used to require Bash to `bazel test` anything.

Starting with Bazel 1.0, you can test any rule without Bash, except when:

- you use `--run_under`
- the test rule itself requires Bash (because its executable is a shell script)

#### Using bazel run without Bash

Bazel versions before 1.0 used to require Bash to `bazel run` anything.

Starting with Bazel 1.0, you can run any rule without Bash, except when:

- you use `--run_under` or `--script_path`
- the test rule itself requires Bash (because its executable is a shell script)

#### Using sh\_binary and sh\_* rules, and ctx.actions.run_shell() without Bash

You need Bash to build and test `sh_*` rules, and to build and test Starlark
rules that use `ctx.actions.run_shell()` and `ctx.resolve_command()`. This
applies not only to rules in your project, but to rules in any of the external
repositories your project depends on (even transitively).

In the future, there may be an option to use Windows Subsystem for
Linux (WSL) to build these rules, but currently it is not a priority for
the Bazel-on-Windows subteam.

### Setting environment variables

Environment variables you set in the Windows Command Prompt (`cmd.exe`) are only
set in that command prompt session. If you start a new `cmd.exe`, you need to
set the variables again. To always set the variables when `cmd.exe` starts, you
can add them to the User variables or System variables in the `Control Panel >
System Properties > Advanced > Environment Variables...` dialog box.

## Build on Windows

### Build C++ with MSVC

To build C++ targets with MSVC, you need:

*   [The Visual C++ compiler](/install/windows#install-vc).

*   (Optional) The `BAZEL_VC` and `BAZEL_VC_FULL_VERSION` environment variable.

    Bazel automatically detects the Visual C++ compiler on your system.
    To tell Bazel to use a specific VC installation, you can set the
    following environment variables:

    For Visual Studio 2017 and 2019, set one of `BAZEL_VC`. Additionally you may also set `BAZEL_VC_FULL_VERSION`.

    *   `BAZEL_VC` the Visual C++ Build Tools installation directory

        ```
        set BAZEL_VC=C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\VC
        ```

    *   `BAZEL_VC_FULL_VERSION` (Optional) Only for Visual Studio 2017 and 2019, the full version
        number of your Visual C++ Build Tools. You can choose the exact Visual C++ Build Tools
        version via `BAZEL_VC_FULL_VERSION` if more than one version are installed, otherwise Bazel
        will choose the latest version.

        ```
        set BAZEL_VC_FULL_VERSION=14.16.27023
        ```

    For Visual Studio 2015 or older, set `BAZEL_VC`. (`BAZEL_VC_FULL_VERSION` is not supported.)

    *   `BAZEL_VC` the Visual C++ Build Tools installation directory

        ```
        set BAZEL_VC=C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC
        ```

*   The [Windows
    SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-10-sdk){: .external}.

    The Windows SDK contains header files and libraries you need when building
    Windows applications, including Bazel itself. By default, the latest Windows SDK installed will
    be used. You also can specify Windows SDK version by setting `BAZEL_WINSDK_FULL_VERSION`. You
    can use a full Windows 10 SDK number such as 10.0.10240.0, or specify 8.1 to use the Windows 8.1
    SDK (only one version of Windows 8.1 SDK is available). Please make sure you have the specified
    Windows SDK installed.

    **Requirement**: This is supported with VC 2017 and 2019. The standalone VC 2015 Build Tools doesn't
    support selecting Windows SDK, you'll need the full Visual Studio 2015 installation, otherwise
    `BAZEL_WINSDK_FULL_VERSION` will be ignored.

    ```
    set BAZEL_WINSDK_FULL_VERSION=10.0.10240.0
    ```

If everything is set up, you can build a C++ target now!

Try building a target from one of our [sample
projects](https://github.com/bazelbuild/bazel/tree/master/examples):

<pre class="devsite-click-to-copy">
<code class="devsite-terminal"
            data-terminal-prefix="C:\projects\bazel&gt; ">bazel build //examples/cpp:hello-world</code>
<code class="devsite-terminal"
            data-terminal-prefix="C:\projects\bazel&gt; ">bazel-bin\examples\cpp\hello-world.exe</code>
</pre>

By default, the built binaries target x64 architecture. To specify a different
target architecture, set the `--cpu` build option for your target architecture:
*  x64 (default):  `--cpu=x64_windows` or no option
*  x86: `--cpu=x64_x86_windows`
*  ARM: `--cpu=x64_arm_windows`
*  ARM64: `--cpu=arm64_windows`

Note: `--cpu=x64_arm64_windows` to target ARM64 architecture is deprecated. Please use `--cpu=arm64_windows`

For example, to build targets for ARM architecture, run:

<pre class="devsite-terminal devsite-click-to-copy"
     data-terminal-prefix="C:\projects\bazel&gt; ">
bazel build //examples/cpp:hello-world --cpu=x64_arm_windows
</pre>

To build and use Dynamically Linked Libraries (DLL files), see [this
example](https://github.com/bazelbuild/bazel/tree/master/examples/windows/dll){: .external}.

**Command Line Length Limit**: To prevent the
[Windows command line length limit issue](https://github.com/bazelbuild/bazel/issues/5163){: .external},
enable the compiler parameter file feature via `--features=compiler_param_file`.

### Build C++ with Clang

From 0.29.0, Bazel supports building with LLVM's MSVC-compatible compiler driver (`clang-cl.exe`).

**Requirement**: To build with Clang, you have to install **both**
[LLVM](http://releases.llvm.org/download.html){: .external} and Visual C++ Build tools,
because although you use `clang-cl.exe` as compiler, you still need to link to
Visual C++ libraries.

Bazel can automatically detect LLVM installation on your system, or you can explicitly tell
Bazel where LLVM is installed by `BAZEL_LLVM`.

*   `BAZEL_LLVM` the LLVM installation directory

    ```posix-terminal
    set BAZEL_LLVM=C:\Program Files\LLVM
    ```

To enable the Clang toolchain for building C++, there are several situations.

* In bazel 0.28 and older: Clang is not supported.

* Without `--incompatible_enable_cc_toolchain_resolution`:
  You can enable the Clang toolchain by a build flag `--compiler=clang-cl`.

* With `--incompatible_enable_cc_toolchain_resolution`:
  You have to add a platform target to your `BUILD file` (eg. the top level `BUILD` file):

    ```
    platform(
        name = "x64_windows-clang-cl",
        constraint_values = [
            "@platforms//cpu:x86_64",
            "@platforms//os:windows",
            "@bazel_tools//tools/cpp:clang-cl",
        ],
    )
    ```

    Then you can enable the Clang toolchain by either of the following two ways:
    * Specify the following build flags:

    ```
    --extra_toolchains=@local_config_cc//:cc-toolchain-x64_windows-clang-cl --extra_execution_platforms=//:x64_windows-clang-cl
    ```

    * Register the platform and toolchain in your `MODULE.bazel` file:

    ```
    register_execution_platforms(
        ":x64_windows-clang-cl"
    )

    register_toolchains(
        "@local_config_cc//:cc-toolchain-x64_windows-clang-cl",
    )
    ```

    The [\-\-incompatible_enable_cc_toolchain_resolution](https://github.com/bazelbuild/bazel/issues/7260){: .external}
    flag is planned to be enabled by default in future Bazel release. Therefore,
    it is recommended to enable Clang support with the second approach.

### Build Java

To build Java targets, you need:

*   [The Java SE Development Kit](/install/windows#install-jdk)

On Windows, Bazel builds two output files for `java_binary` rules:

*   a `.jar` file
*   a `.exe` file that can set up the environment for the JVM and run the binary

Try building a target from one of our [sample
projects](https://github.com/bazelbuild/bazel/tree/master/examples){: .external}:

<pre class="devsite-click-to-copy">
  <code class="devsite-terminal"
        data-terminal-prefix="C:\projects\bazel&gt; ">bazel build //examples/java-native/src/main/java/com/example/<var>myproject</var>:hello-world</code>
  <code class="devsite-terminal"
        data-terminal-prefix="C:\projects\bazel&gt; ">bazel-bin\examples\java-native\src\main\java\com\example\<var>myproject</var>\hello-world.exe</code>
</pre>

### Build Python

To build Python targets, you need:

*   The [Python interpreter](/install/windows#install-python)

On Windows, Bazel builds two output files for `py_binary` rules:

*   a self-extracting zip file
*   an executable file that can launch the Python interpreter with the
    self-extracting zip file as the argument

You can either run the executable file (it has a `.exe` extension) or you can run
Python with the self-extracting zip file as the argument.

Try building a target from one of our [sample
projects](https://github.com/bazelbuild/bazel/tree/master/examples){: .external}:

<pre class="devsite-click-to-copy">
  <code class="devsite-terminal"
        data-terminal-prefix="C:\projects\bazel&gt; ">bazel build //examples/py_native:bin</code>
  <code class="devsite-terminal"
        data-terminal-prefix="C:\projects\bazel&gt; ">bazel-bin\examples\py_native\bin.exe</code>
  <code class="devsite-terminal"
        data-terminal-prefix="C:\projects\bazel&gt; ">python bazel-bin\examples\py_native\bin.zip</code>
</pre>

If you are interested in details about how Bazel builds Python targets on
Windows, check out this [design
doc](https://github.com/bazelbuild/bazel-website/blob/master/designs/_posts/2016-09-05-build-python-on-windows.md){: .external}.



# Configurable Build Attributes

**_Configurable attributes_**, commonly known as [`select()`](
/reference/be/functions#select), is a Bazel feature that lets users toggle the values
of build rule attributes at the command line.

This can be used, for example, for a multiplatform library that automatically
chooses the appropriate implementation for the architecture, or for a
feature-configurable binary that can be customized at build time.

## Example

```python
# myapp/BUILD

cc_binary(
    name = "mybinary",
    srcs = ["main.cc"],
    deps = select({
        ":arm_build": [":arm_lib"],
        ":x86_debug_build": [":x86_dev_lib"],
        "//conditions:default": [":generic_lib"],
    }),
)

config_setting(
    name = "arm_build",
    values = {"cpu": "arm"},
)

config_setting(
    name = "x86_debug_build",
    values = {
        "cpu": "x86",
        "compilation_mode": "dbg",
    },
)
```

This declares a `cc_binary` that "chooses" its deps based on the flags at the
command line. Specifically, `deps` becomes:

<table>
  <tr style="background: #E9E9E9; font-weight: bold">
    <td>Command</td>
    <td>deps =</td>
  </tr>
  <tr>
    <td><code>bazel build //myapp:mybinary --cpu=arm</code></td>
    <td><code>[":arm_lib"]</code></td>
  </tr>
  <tr>
    <td><code>bazel build //myapp:mybinary -c dbg --cpu=x86</code></td>
    <td><code>[":x86_dev_lib"]</code></td>
  </tr>
  <tr>
    <td><code>bazel build //myapp:mybinary --cpu=ppc</code></td>
    <td><code>[":generic_lib"]</code></td>
  </tr>
  <tr>
    <td><code>bazel build //myapp:mybinary -c dbg --cpu=ppc</code></td>
    <td><code>[":generic_lib"]</code></td>
  </tr>
</table>

`select()` serves as a placeholder for a value that will be chosen based on
*configuration conditions*, which are labels referencing [`config_setting`](/reference/be/general#config_setting)
targets. By using `select()` in a configurable attribute, the attribute
effectively adopts different values when different conditions hold.

Matches must be unambiguous: if multiple conditions match then either
*  They all resolve to the same value. For example, when running on linux x86, this is unambiguous
   `{"@platforms//os:linux": "Hello", "@platforms//cpu:x86_64": "Hello"}` because both branches resolve to "hello".
*  One's `values` is a strict superset of all others'. For example, `values = {"cpu": "x86", "compilation_mode": "dbg"}`
   is an unambiguous specialization of `values = {"cpu": "x86"}`.

The built-in condition [`//conditions:default`](#default-condition) automatically matches when
nothing else does.

While this example uses `deps`, `select()` works just as well on `srcs`,
`resources`, `cmd`, and most other attributes. Only a small number of attributes
are *non-configurable*, and these are clearly annotated. For example,
`config_setting`'s own
[`values`](/reference/be/general#config_setting.values) attribute is non-configurable.

## `select()` and dependencies

Certain attributes change the build parameters for all transitive dependencies
under a target. For example, `genrule`'s `tools` changes `--cpu` to the CPU of
the machine running Bazel (which, thanks to cross-compilation, may be different
than the CPU the target is built for). This is known as a
[configuration transition](/reference/glossary#transition).

Given

```python
#myapp/BUILD

config_setting(
    name = "arm_cpu",
    values = {"cpu": "arm"},
)

config_setting(
    name = "x86_cpu",
    values = {"cpu": "x86"},
)

genrule(
    name = "my_genrule",
    srcs = select({
        ":arm_cpu": ["g_arm.src"],
        ":x86_cpu": ["g_x86.src"],
    }),
    tools = select({
        ":arm_cpu": [":tool1"],
        ":x86_cpu": [":tool2"],
    }),
)

cc_binary(
    name = "tool1",
    srcs = select({
        ":arm_cpu": ["armtool.cc"],
        ":x86_cpu": ["x86tool.cc"],
    }),
)
```

running

```sh
$ bazel build //myapp:my_genrule --cpu=arm
```

on an `x86` developer machine binds the build to `g_arm.src`, `tool1`, and
`x86tool.cc`. Both of the `select`s attached to `my_genrule` use `my_genrule`'s
build parameters, which include `--cpu=arm`. The `tools` attribute changes
`--cpu` to `x86` for `tool1` and its transitive dependencies. The `select` on
`tool1` uses `tool1`'s build parameters, which include `--cpu=x86`.

## Configuration conditions

Each key in a configurable attribute is a label reference to a
[`config_setting`](/reference/be/general#config_setting) or
[`constraint_value`](/reference/be/platforms-and-toolchains#constraint_value).

`config_setting` is just a collection of
expected command line flag settings. By encapsulating these in a target, it's
easy to maintain "standard" conditions users can reference from multiple places.

`constraint_value` provides support for [multi-platform behavior](#platforms).

### Built-in flags

Flags like `--cpu` are built into Bazel: the build tool natively understands
them for all builds in all projects. These are specified with
[`config_setting`](/reference/be/general#config_setting)'s
[`values`](/reference/be/general#config_setting.values) attribute:

```python
config_setting(
    name = "meaningful_condition_name",
    values = {
        "flag1": "value1",
        "flag2": "value2",
        ...
    },
)
```

`flagN` is a flag name (without `--`, so `"cpu"` instead of `"--cpu"`). `valueN`
is the expected value for that flag. `:meaningful_condition_name` matches if
*every* entry in `values` matches. Order is irrelevant.

`valueN` is parsed as if it was set on the command line. This means:

*  `values = { "compilation_mode": "opt" }` matches `bazel build -c opt`
*  `values = { "force_pic": "true" }` matches `bazel build --force_pic=1`
*  `values = { "force_pic": "0" }` matches `bazel build --noforce_pic`

`config_setting` only supports flags that affect target behavior. For example,
[`--show_progress`](/docs/user-manual#show-progress) isn't allowed because
it only affects how Bazel reports progress to the user. Targets can't use that
flag to construct their results. The exact set of supported flags isn't
documented. In practice, most flags that "make sense" work.

### Custom flags

You can model your own project-specific flags with
[Starlark build settings][BuildSettings]. Unlike built-in flags, these are
defined as build targets, so Bazel references them with target labels.

These are triggered with [`config_setting`](/reference/be/general#config_setting)'s
[`flag_values`](/reference/be/general#config_setting.flag_values)
attribute:

```python
config_setting(
    name = "meaningful_condition_name",
    flag_values = {
        "//myflags:flag1": "value1",
        "//myflags:flag2": "value2",
        ...
    },
)
```

Behavior is the same as for [built-in flags](#built-in-flags). See [here](https://github.com/bazelbuild/examples/tree/HEAD/configurations/select_on_build_setting){: .external}
for a working example.

[`--define`](/reference/command-line-reference#flag--define)
is an alternative legacy syntax for custom flags (for example
`--define foo=bar`). This can be expressed either in the
[values](/reference/be/general#config_setting.values) attribute
(`values = {"define": "foo=bar"}`) or the
[define_values](/reference/be/general#config_setting.define_values) attribute
(`define_values = {"foo": "bar"}`). `--define` is only supported for backwards
compatibility. Prefer Starlark build settings whenever possible.

`values`, `flag_values`, and `define_values` evaluate independently. The
`config_setting` matches if all values across all of them match.

## The default condition

The built-in condition `//conditions:default` matches when no other condition
matches.

Because of the "exactly one match" rule, a configurable attribute with no match
and no default condition emits a `"no matching conditions"` error. This can
protect against silent failures from unexpected settings:

```python
# myapp/BUILD

config_setting(
    name = "x86_cpu",
    values = {"cpu": "x86"},
)

cc_library(
    name = "x86_only_lib",
    srcs = select({
        ":x86_cpu": ["lib.cc"],
    }),
)
```

```sh
$ bazel build //myapp:x86_only_lib --cpu=arm
ERROR: Configurable attribute "srcs" doesn't match this configuration (would
a default condition help?).
Conditions checked:
  //myapp:x86_cpu
```

For even clearer errors, you can set custom messages with `select()`'s
[`no_match_error`](#custom-error-messages) attribute.

## Platforms

While the ability to specify multiple flags on the command line provides
flexibility, it can also be burdensome to individually set each one every time
you want to build a target.
   [Platforms](/extending/platforms)
let you consolidate these into simple bundles.

```python
# myapp/BUILD

sh_binary(
    name = "my_rocks",
    srcs = select({
        ":basalt": ["pyroxene.sh"],
        ":marble": ["calcite.sh"],
        "//conditions:default": ["feldspar.sh"],
    }),
)

config_setting(
    name = "basalt",
    constraint_values = [
        ":black",
        ":igneous",
    ],
)

config_setting(
    name = "marble",
    constraint_values = [
        ":white",
        ":metamorphic",
    ],
)

# constraint_setting acts as an enum type, and constraint_value as an enum value.
constraint_setting(name = "color")
constraint_value(name = "black", constraint_setting = "color")
constraint_value(name = "white", constraint_setting = "color")
constraint_setting(name = "texture")
constraint_value(name = "smooth", constraint_setting = "texture")
constraint_setting(name = "type")
constraint_value(name = "igneous", constraint_setting = "type")
constraint_value(name = "metamorphic", constraint_setting = "type")

platform(
    name = "basalt_platform",
    constraint_values = [
        ":black",
        ":igneous",
    ],
)

platform(
    name = "marble_platform",
    constraint_values = [
        ":white",
        ":smooth",
        ":metamorphic",
    ],
)
```

The platform can be specified on the command line. It activates the
`config_setting`s that contain a subset of the platform's `constraint_values`,
allowing those `config_setting`s to match in `select()` expressions.

For example, in order to set the `srcs` attribute of `my_rocks` to `calcite.sh`,
you can simply run

```sh
bazel build //my_app:my_rocks --platforms=//myapp:marble_platform
```

Without platforms, this might look something like

```sh
bazel build //my_app:my_rocks --define color=white --define texture=smooth --define type=metamorphic
```

`select()` can also directly read `constraint_value`s:

```python
constraint_setting(name = "type")
constraint_value(name = "igneous", constraint_setting = "type")
constraint_value(name = "metamorphic", constraint_setting = "type")
sh_binary(
    name = "my_rocks",
    srcs = select({
        ":igneous": ["igneous.sh"],
        ":metamorphic" ["metamorphic.sh"],
    }),
)
```

This saves the need for boilerplate `config_setting`s when you only need to
check against single values.

Platforms are still under development. See the
[documentation](/concepts/platforms) for details.

## Combining `select()`s

`select` can appear multiple times in the same attribute:

```python
sh_binary(
    name = "my_target",
    srcs = ["always_include.sh"] +
           select({
               ":armeabi_mode": ["armeabi_src.sh"],
               ":x86_mode": ["x86_src.sh"],
           }) +
           select({
               ":opt_mode": ["opt_extras.sh"],
               ":dbg_mode": ["dbg_extras.sh"],
           }),
)
```

Note: Some restrictions apply on what can be combined in the `select`s values:
 - Duplicate labels can appear in different paths of the same `select`.
 - Duplicate labels can *not* appear within the same path of a `select`.
 - Duplicate labels can *not* appear across multiple combined `select`s (no matter what path)

`select` cannot appear inside another `select`. If you need to nest `selects`
and your attribute takes other targets as values, use an intermediate target:

```python
sh_binary(
    name = "my_target",
    srcs = ["always_include.sh"],
    deps = select({
        ":armeabi_mode": [":armeabi_lib"],
        ...
    }),
)

sh_library(
    name = "armeabi_lib",
    srcs = select({
        ":opt_mode": ["armeabi_with_opt.sh"],
        ...
    }),
)
```

If you need a `select` to match when multiple conditions match, consider [AND
chaining](#and-chaining).

## OR chaining

Consider the following:

```python
sh_binary(
    name = "my_target",
    srcs = ["always_include.sh"],
    deps = select({
        ":config1": [":standard_lib"],
        ":config2": [":standard_lib"],
        ":config3": [":standard_lib"],
        ":config4": [":special_lib"],
    }),
)
```

Most conditions evaluate to the same dep. But this syntax is hard to read and
maintain. It would be nice to not have to repeat `[":standard_lib"]` multiple
times.

One option is to predefine the value as a BUILD variable:

```python
STANDARD_DEP = [":standard_lib"]

sh_binary(
    name = "my_target",
    srcs = ["always_include.sh"],
    deps = select({
        ":config1": STANDARD_DEP,
        ":config2": STANDARD_DEP,
        ":config3": STANDARD_DEP,
        ":config4": [":special_lib"],
    }),
)
```

This makes it easier to manage the dependency. But it still causes unnecessary
duplication.

For more direct support, use one of the following:

### `selects.with_or`

The
[with_or](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/selects_doc.md#selectswith_or){: .external}
macro in [Skylib](https://github.com/bazelbuild/bazel-skylib){: .external}'s
[`selects`](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/selects_doc.md){: .external}
module supports `OR`ing conditions directly inside a `select`:

```python
load("@bazel_skylib//lib:selects.bzl", "selects")
```

```python
sh_binary(
    name = "my_target",
    srcs = ["always_include.sh"],
    deps = selects.with_or({
        (":config1", ":config2", ":config3"): [":standard_lib"],
        ":config4": [":special_lib"],
    }),
)
```

### `selects.config_setting_group`

The
[config_setting_group](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/selects_doc.md#selectsconfig_setting_group){: .external}
macro in [Skylib](https://github.com/bazelbuild/bazel-skylib){: .external}'s
[`selects`](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/selects_doc.md){: .external}
module supports `OR`ing multiple `config_setting`s:

```python
load("@bazel_skylib//lib:selects.bzl", "selects")
```

```python
config_setting(
    name = "config1",
    values = {"cpu": "arm"},
)
config_setting(
    name = "config2",
    values = {"compilation_mode": "dbg"},
)
selects.config_setting_group(
    name = "config1_or_2",
    match_any = [":config1", ":config2"],
)
sh_binary(
    name = "my_target",
    srcs = ["always_include.sh"],
    deps = select({
        ":config1_or_2": [":standard_lib"],
        "//conditions:default": [":other_lib"],
    }),
)
```

Unlike `selects.with_or`, different targets can share `:config1_or_2` across
different attributes.

It's an error for multiple conditions to match unless one is an unambiguous
"specialization" of the others or they all resolve to the same value. See [here](#configurable-build-example) for details.

## AND chaining

If you need a `select` branch to match when multiple conditions match, use the
[Skylib](https://github.com/bazelbuild/bazel-skylib){: .external} macro
[config_setting_group](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/selects_doc.md#selectsconfig_setting_group){: .external}:

```python
config_setting(
    name = "config1",
    values = {"cpu": "arm"},
)
config_setting(
    name = "config2",
    values = {"compilation_mode": "dbg"},
)
selects.config_setting_group(
    name = "config1_and_2",
    match_all = [":config1", ":config2"],
)
sh_binary(
    name = "my_target",
    srcs = ["always_include.sh"],
    deps = select({
        ":config1_and_2": [":standard_lib"],
        "//conditions:default": [":other_lib"],
    }),
)
```

Unlike OR chaining, existing `config_setting`s can't be directly `AND`ed
inside a `select`. You have to explicitly wrap them in a `config_setting_group`.

## Custom error messages

By default, when no condition matches, the target the `select()` is attached to
fails with the error:

```sh
ERROR: Configurable attribute "deps" doesn't match this configuration (would
a default condition help?).
Conditions checked:
  //tools/cc_target_os:darwin
  //tools/cc_target_os:android
```

This can be customized with the [`no_match_error`](/reference/be/functions#select)
attribute:

```python
cc_library(
    name = "my_lib",
    deps = select(
        {
            "//tools/cc_target_os:android": [":android_deps"],
            "//tools/cc_target_os:windows": [":windows_deps"],
        },
        no_match_error = "Please build with an Android or Windows toolchain",
    ),
)
```

```sh
$ bazel build //myapp:my_lib
ERROR: Configurable attribute "deps" doesn't match this configuration: Please
build with an Android or Windows toolchain
```

## Rules compatibility

Rule implementations receive the *resolved values* of configurable
attributes. For example, given:

```python
# myapp/BUILD

some_rule(
    name = "my_target",
    some_attr = select({
        ":foo_mode": [":foo"],
        ":bar_mode": [":bar"],
    }),
)
```

```sh
$ bazel build //myapp/my_target --define mode=foo
```

Rule implementation code sees `ctx.attr.some_attr` as `[":foo"]`.

Macros can accept `select()` clauses and pass them through to native
rules. But *they cannot directly manipulate them*. For example, there's no way
for a macro to convert

```python
select({"foo": "val"}, ...)
```

to

```python
select({"foo": "val_with_suffix"}, ...)
```

This is for two reasons.

First, macros that need to know which path a `select` will choose *cannot work*
because macros are evaluated in Bazel's [loading phase](/run/build#loading),
which occurs before flag values are known.
This is a core Bazel design restriction that's unlikely to change any time soon.

Second, macros that just need to iterate over *all* `select` paths, while
technically feasible, lack a coherent UI. Further design is necessary to change
this.

## Bazel query and cquery

Bazel [`query`](/query/guide) operates over Bazel's
[loading phase](/reference/glossary#loading-phase).
This means it doesn't know what command line flags a target uses since those
flags aren't evaluated until later in the build (in the
[analysis phase](/reference/glossary#analysis-phase)).
So it can't determine which `select()` branches are chosen.

Bazel [`cquery`](/query/cquery) operates after Bazel's analysis phase, so it has
all this information and can accurately resolve `select()`s.

Consider:

```python
load("@bazel_skylib//rules:common_settings.bzl", "string_flag")
```
```python
# myapp/BUILD

string_flag(
    name = "dog_type",
    build_setting_default = "cat"
)

cc_library(
    name = "my_lib",
    deps = select({
        ":long": [":foo_dep"],
        ":short": [":bar_dep"],
    }),
)

config_setting(
    name = "long",
    flag_values = {":dog_type": "dachshund"},
)

config_setting(
    name = "short",
    flag_values = {":dog_type": "pug"},
)
```

`query` overapproximates `:my_lib`'s dependencies:

```sh
$ bazel query 'deps(//myapp:my_lib)'
//myapp:my_lib
//myapp:foo_dep
//myapp:bar_dep
```

while `cquery` shows its exact dependencies:

```sh
$ bazel cquery 'deps(//myapp:my_lib)' --//myapp:dog_type=pug
//myapp:my_lib
//myapp:bar_dep
```

## FAQ

### Why doesn't select() work in macros?

select() *does* work in rules! See [Rules compatibility](#rules-compatibility) for
details.

The key issue this question usually means is that select() doesn't work in
*macros*. These are different than *rules*. See the
documentation on [rules](/extending/rules) and [macros](/extending/macros)
to understand the difference.
Here's an end-to-end example:

Define a rule and macro:

```python
# myapp/defs.bzl

# Rule implementation: when an attribute is read, all select()s have already
# been resolved. So it looks like a plain old attribute just like any other.
def _impl(ctx):
    name = ctx.attr.name
    allcaps = ctx.attr.my_config_string.upper()  # This works fine on all values.
    print("My name is " + name + " with custom message: " + allcaps)

# Rule declaration:
my_custom_bazel_rule = rule(
    implementation = _impl,
    attrs = {"my_config_string": attr.string()},
)

# Macro declaration:
def my_custom_bazel_macro(name, my_config_string):
    allcaps = my_config_string.upper()  # This line won't work with select(s).
    print("My name is " + name + " with custom message: " + allcaps)
```

Instantiate the rule and macro:

```python
# myapp/BUILD

load("//myapp:defs.bzl", "my_custom_bazel_rule")
load("//myapp:defs.bzl", "my_custom_bazel_macro")

my_custom_bazel_rule(
    name = "happy_rule",
    my_config_string = select({
        "//third_party/bazel_platforms/cpu:x86_32": "first string",
        "//third_party/bazel_platforms/cpu:ppc": "second string",
    }),
)

my_custom_bazel_macro(
    name = "happy_macro",
    my_config_string = "fixed string",
)

my_custom_bazel_macro(
    name = "sad_macro",
    my_config_string = select({
        "//third_party/bazel_platforms/cpu:x86_32": "first string",
        "//third_party/bazel_platforms/cpu:ppc": "other string",
    }),
)
```

Building fails because `sad_macro` can't process the `select()`:

```sh
$ bazel build //myapp:all
ERROR: /myworkspace/myapp/BUILD:17:1: Traceback
  (most recent call last):
File "/myworkspace/myapp/BUILD", line 17
my_custom_bazel_macro(name = "sad_macro", my_config_stri..."}))
File "/myworkspace/myapp/defs.bzl", line 4, in
  my_custom_bazel_macro
my_config_string.upper()
type 'select' has no method upper().
ERROR: error loading package 'myapp': Package 'myapp' contains errors.
```

Building succeeds when you comment out `sad_macro`:

```sh
# Comment out sad_macro so it doesn't mess up the build.
$ bazel build //myapp:all
DEBUG: /myworkspace/myapp/defs.bzl:5:3: My name is happy_macro with custom message: FIXED STRING.
DEBUG: /myworkspace/myapp/hi.bzl:15:3: My name is happy_rule with custom message: FIRST STRING.
```

This is impossible to change because *by definition* macros are evaluated before
Bazel reads the build's command line flags. That means there isn't enough
information to evaluate select()s.

Macros can, however, pass `select()`s as opaque blobs to rules:

```python
# myapp/defs.bzl

def my_custom_bazel_macro(name, my_config_string):
    print("Invoking macro " + name)
    my_custom_bazel_rule(
        name = name + "_as_target",
        my_config_string = my_config_string,
    )
```

```sh
$ bazel build //myapp:sad_macro_less_sad
DEBUG: /myworkspace/myapp/defs.bzl:23:3: Invoking macro sad_macro_less_sad.
DEBUG: /myworkspace/myapp/defs.bzl:15:3: My name is sad_macro_less_sad with custom message: FIRST STRING.
```

### Why does select() always return true?

Because *macros* (but not rules) by definition
[can't evaluate `select()`s](#faq-select-macro), any attempt to do so
usually produces an error:

```sh
ERROR: /myworkspace/myapp/BUILD:17:1: Traceback
  (most recent call last):
File "/myworkspace/myapp/BUILD", line 17
my_custom_bazel_macro(name = "sad_macro", my_config_stri..."}))
File "/myworkspace/myapp/defs.bzl", line 4, in
  my_custom_bazel_macro
my_config_string.upper()
type 'select' has no method upper().
```

Booleans are a special case that fail silently, so you should be particularly
vigilant with them:

```sh
$ cat myapp/defs.bzl
def my_boolean_macro(boolval):
  print("TRUE" if boolval else "FALSE")

$ cat myapp/BUILD
load("//myapp:defs.bzl", "my_boolean_macro")
my_boolean_macro(
    boolval = select({
        "//third_party/bazel_platforms/cpu:x86_32": True,
        "//third_party/bazel_platforms/cpu:ppc": False,
    }),
)

$ bazel build //myapp:all --cpu=x86
DEBUG: /myworkspace/myapp/defs.bzl:4:3: TRUE.
$ bazel build //mypro:all --cpu=ppc
DEBUG: /myworkspace/myapp/defs.bzl:4:3: TRUE.
```

This happens because macros don't understand the contents of `select()`.
So what they're really evaluting is the `select()` object itself. According to
[Pythonic](https://docs.python.org/release/2.5.2/lib/truth.html) design
standards, all objects aside from a very small number of exceptions
automatically return true.

### Can I read select() like a dict?

Macros [can't](#faq-select-macro) evaluate select(s) because macros evaluate before
Bazel knows what the build's command line parameters are. Can they at least read
the `select()`'s dictionary to, for example, add a suffix to each value?

Conceptually this is possible, but it isn't yet a Bazel feature.
What you *can* do today is prepare a straight dictionary, then feed it into a
`select()`:

```sh
$ cat myapp/defs.bzl
def selecty_genrule(name, select_cmd):
  for key in select_cmd.keys():
    select_cmd[key] += " WITH SUFFIX"
  native.genrule(
      name = name,
      outs = [name + ".out"],
      srcs = [],
      cmd = "echo " + select(select_cmd + {"//conditions:default": "default"})
        + " > $@"
  )

$ cat myapp/BUILD
selecty_genrule(
    name = "selecty",
    select_cmd = {
        "//third_party/bazel_platforms/cpu:x86_32": "x86 mode",
    },
)

$ bazel build //testapp:selecty --cpu=x86 && cat bazel-genfiles/testapp/selecty.out
x86 mode WITH SUFFIX
```

If you'd like to support both `select()` and native types, you can do this:

```sh
$ cat myapp/defs.bzl
def selecty_genrule(name, select_cmd):
    cmd_suffix = ""
    if type(select_cmd) == "string":
        cmd_suffix = select_cmd + " WITH SUFFIX"
    elif type(select_cmd) == "dict":
        for key in select_cmd.keys():
            select_cmd[key] += " WITH SUFFIX"
        cmd_suffix = select(select_cmd + {"//conditions:default": "default"})

    native.genrule(
        name = name,
        outs = [name + ".out"],
        srcs = [],
        cmd = "echo " + cmd_suffix + "> $@",
    )
```

### Why doesn't select() work with bind()?

First of all, do not use `bind()`. It is deprecated in favor of `alias()`.

The technical answer is that [`bind()`](/reference/be/workspace#bind) is a repo
rule, not a BUILD rule.

Repo rules do not have a specific configuration, and aren't evaluated in
the same way as BUILD rules. Therefore, a `select()` in a `bind()` can't
actually evaluate to any specific branch.

Instead, you should use [`alias()`](/reference/be/general#alias), with a `select()` in
the `actual` attribute, to perform this type of run-time determination. This
works correctly, since `alias()` is a BUILD rule, and is evaluated with a
specific configuration.

```sh
$ cat WORKSPACE
workspace(name = "myapp")
bind(name = "openssl", actual = "//:ssl")
http_archive(name = "alternative", ...)
http_archive(name = "boringssl", ...)

$ cat BUILD
config_setting(
    name = "alt_ssl",
    define_values = {
        "ssl_library": "alternative",
    },
)

alias(
    name = "ssl",
    actual = select({
        "//:alt_ssl": "@alternative//:ssl",
        "//conditions:default": "@boringssl//:ssl",
    }),
)
```

With this setup, you can pass `--define ssl_library=alternative`, and any target
that depends on either `//:ssl` or `//external:ssl` will see the alternative
located at `@alternative//:ssl`.

But really, stop using `bind()`.

### Why doesn't my select() choose what I expect?

If `//myapp:foo` has a `select()` that doesn't choose the condition you expect,
use [cquery](/query/cquery) and `bazel config` to debug:

If `//myapp:foo` is the top-level target you're building, run:

```sh
$ bazel cquery //myapp:foo <desired build flags>
//myapp:foo (12e23b9a2b534a)
```

If you're building some other target `//bar` that depends on
//myapp:foo somewhere in its subgraph, run:

```sh
$ bazel cquery 'somepath(//bar, //myapp:foo)' <desired build flags>
//bar:bar   (3ag3193fee94a2)
//bar:intermediate_dep (12e23b9a2b534a)
//myapp:foo (12e23b9a2b534a)
```

The `(12e23b9a2b534a)` next to `//myapp:foo` is a *hash* of the
configuration that resolves `//myapp:foo`'s `select()`. You can inspect its
values with `bazel config`:

```sh
$ bazel config 12e23b9a2b534a
BuildConfigurationValue 12e23b9a2b534a
Fragment com.google.devtools.build.lib.analysis.config.CoreOptions {
  cpu: darwin
  compilation_mode: fastbuild
  ...
}
Fragment com.google.devtools.build.lib.rules.cpp.CppOptions {
  linkopt: [-Dfoo=bar]
  ...
}
...
```

Then compare this output against the settings expected by each `config_setting`.

`//myapp:foo` may exist in different configurations in the same build. See the
[cquery docs](/query/cquery) for guidance on using `somepath` to get the right
one.

Caution: To prevent restarting the Bazel server, invoke `bazel config` with the
same command line flags as the `bazel cquery`. The `config` command relies on
the configuration nodes from the still-running server of the previous command.

### Why doesn't `select()` work with platforms?

Bazel doesn't support configurable attributes checking whether a given platform
is the target platform because the semantics are unclear.

For example:

```py
platform(
    name = "x86_linux_platform",
    constraint_values = [
        "@platforms//cpu:x86",
        "@platforms//os:linux",
    ],
)

cc_library(
    name = "lib",
    srcs = [...],
    linkopts = select({
        ":x86_linux_platform": ["--enable_x86_optimizations"],
        "//conditions:default": [],
    }),
)
```

In this `BUILD` file, which `select()` should be used if the target platform has both the
`@platforms//cpu:x86` and `@platforms//os:linux` constraints, but is **not** the
`:x86_linux_platform` defined here? The author of the `BUILD` file and the user
who defined the separate platform may have different ideas.

#### What should I do instead?

Instead, define a `config_setting` that matches **any** platform with
these constraints:

```py
config_setting(
    name = "is_x86_linux",
    constraint_values = [
        "@platforms//cpu:x86",
        "@platforms//os:linux",
    ],
)

cc_library(
    name = "lib",
    srcs = [...],
    linkopts = select({
        ":is_x86_linux": ["--enable_x86_optimizations"],
        "//conditions:default": [],
    }),
)
```

This process defines specific semantics, making it clearer to users what
platforms meet the desired conditions.

#### What if I really, really want to `select` on the platform?

If your build requirements specifically require checking the platform, you
can flip the value of the `--platforms` flag in a `config_setting`:

```py
config_setting(
    name = "is_specific_x86_linux_platform",
    values = {
        "platforms": ["//package:x86_linux_platform"],
    },
)

cc_library(
    name = "lib",
    srcs = [...],
    linkopts = select({
        ":is_specific_x86_linux_platform": ["--enable_x86_optimizations"],
        "//conditions:default": [],
    }),
)
```

The Bazel team doesn't endorse doing this; it overly constrains your build and
confuses users when the expected condition does not match.

[BuildSettings]: /extending/config#user-defined-build-settings



# Code coverage with Bazel

Bazel features a `coverage` sub-command to produce code coverage
reports on repositories that can be tested with `bazel coverage`. Due
to the idiosyncrasies of the various language ecosystems, it is not
always trivial to make this work for a given project.

This page documents the general process for creating and viewing
coverage reports, and also features some language-specific notes for
languages whose configuration is well-known. It is best read by first
reading [the general section](#creating-a-coverage-report), and then
reading about the requirements for a specific language. Note also the
[remote execution section](#remote-execution), which requires some
additional considerations.

While a lot of customization is possible, this document focuses on
producing and consuming [`lcov`][lcov] reports, which is currently the
most well-supported route.

## Creating a coverage report

### Preparation

The basic workflow for creating coverage reports requires the
following:

- A basic repository with test targets
- A toolchain with the language-specific code coverage tools installed
- A correct "instrumentation" configuration

The former two are language-specific and mostly straightforward,
however the latter can be more difficult for complex projects.

"Instrumentation" in this case refers to the coverage tools that are
used for a specific target. Bazel allows turning this on for a
specific subset of files using the
[`--instrumentation_filter`](/reference/command-line-reference#flag--instrumentation_filter)
flag, which specifies a filter for targets that are tested with the
instrumentation enabled. To enable instrumentation for tests, the
[`--instrument_test_targets`](/reference/command-line-reference#flag--instrument_test_targets)
flag is required.

By default, bazel tries to match the target package(s), and prints the
relevant filter as an `INFO` message.

### Running coverage

To produce a coverage report, use [`bazel coverage
--combined_report=lcov
[target]`](/reference/command-line-reference#coverage). This runs the
tests for the target, generating coverage reports in the lcov format
for each file.

Once finished, bazel runs an action that collects all the produced
coverage files, and merges them into one, which is then finally
created under `$(bazel info
output_path)/_coverage/_coverage_report.dat`.

Coverage reports are also produced if tests fail, though note that
this does not extend to the failed tests - only passing tests are
reported.

### Viewing coverage

The coverage report is only output in the non-human-readable `lcov`
format. From this, we can use the `genhtml` utility (part of [the lcov
project][lcov]) to produce a report that can be viewed in a web
browser:

```console
genhtml --branch-coverage --output genhtml "$(bazel info output_path)/_coverage/_coverage_report.dat"
```

Note that `genhtml` reads the source code as well, to annotate missing
coverage in these files. For this to work, it is expected that
`genhtml` is executed in the root of the bazel project.

To view the result, simply open the `index.html` file produced in the
`genhtml` directory in any web browser.

For further help and information around the `genhtml` tool, or the
`lcov` coverage format, see [the lcov project][lcov].

## Remote execution

Running with remote test execution currently has a few caveats:

- The report combination action cannot yet run remotely. This is
  because Bazel does not consider the coverage output files as part of
  its graph (see [this issue][remote_report_issue]), and can therefore
  not correctly treat them as inputs to the combination action. To
  work around this, use `--strategy=CoverageReport=local`.
  - Note: It may be necessary to specify something like
    `--strategy=CoverageReport=local,remote` instead, if Bazel is set
    up to try `local,remote`, due to how Bazel resolves strategies.
- `--remote_download_minimal` and similar flags can also not be used
  as a consequence of the former.
- Bazel will currently fail to create coverage information if tests
  have been cached previously. To work around this,
  `--nocache_test_results` can be set specifically for coverage runs,
  although this of course incurs a heavy cost in terms of test times.
- `--experimental_split_coverage_postprocessing` and
  `--experimental_fetch_all_coverage_outputs`
  - Usually coverage is run as part of the test action, and so by
    default, we don't get all coverage back as outputs of the remote
    execution by default. These flags override the default and obtain
    the coverage data. See [this issue][split_coverage_issue] for more
    details.

## Language-specific configuration

### Java

Java should work out-of-the-box with the default configuration. The
[bazel toolchains][bazel_toolchains] contain everything necessary for
remote execution, as well, including JUnit.

### Python

See the [`rules_python` coverage docs](https://rules-python.readthedocs.io/en/latest/coverage.html)
for additional steps needed to enable coverage support in Python.

[lcov]: https://github.com/linux-test-project/lcov
[bazel_toolchains]: https://github.com/bazelbuild/bazel-toolchains
[remote_report_issue]: https://github.com/bazelbuild/bazel/issues/4685
[split_coverage_issue]: https://github.com/bazelbuild/bazel/issues/4685



# Integrating with C++ Rules

This page describes how to integrate with C++ rules on various levels.

## Accessing the C++ toolchain

You should use the helper functions available at
[`@rules_cc//cc:find_cc_toolchain.bzl`](https://github.com/bazelbuild/rules_cc/blob/main/cc/find_cc_toolchain.bzl)
to depend on a CC toolchain from a Starlark rule.

To depend on a C++ toolchain in your rule, set the `toolchains` parameter to
`use_cc_toolchain()`. Then, in the rule implementation, use
`find_cpp_toolchain(ctx)` to get the
[`CcToolchainInfo`](/rules/lib/providers/CcToolchainInfo). A complete working
example can be found [in the rules_cc
examples](https://github.com/bazelbuild/rules_cc/blob/main/examples/write_cc_toolchain_cpu/write_cc_toolchain_cpu.bzl){:
.external}.

## Generating command lines and environment variables using the C++ toolchain

Typically, you would integrate with the C++ toolchain to have the same
command line flags as C++ rules do, but without using C++ actions directly.
This is because when writing our own actions, they must behave
consistently with the C++ toolchain - for example, passing C++ command line
flags to a tool that invokes the C++ compiler behind the scenes.

C++ rules use a special way of constructing command lines based on [feature
configuration](/docs/cc-toolchain-config-reference). To construct a command line,
you need the following:

* `features` and `action_configs` - these come from the `CcToolchainConfigInfo`
  and encapsulated in `CcToolchainInfo`
* `FeatureConfiguration` - returned by [cc_common.configure_features](/rules/lib/toplevel/cc_common#configure_features)
* cc toolchain config variables - returned by
  [cc_common.create_compile_variables](/rules/lib/toplevel/cc_common#create_compile_variables)
  or
  [cc_common.create_link_variables](/rules/lib/toplevel/cc_common#create_link_variables).

There still are tool-specific getters, such as
[compiler_executable](/rules/lib/providers/CcToolchainInfo#compiler_executable).
Prefer `get_tool_for_action` over these, as tool-specific getters will
eventually be removed.

A complete working example can be found
[in the rules_cc examples](https://github.com/bazelbuild/rules_cc/blob/main/examples/my_c_compile/my_c_compile.bzl){: .external}.

## Implementing Starlark rules that depend on C++ rules and/or that C++ rules can depend on

Most C++ rules provide
[`CcInfo`](/rules/lib/providers/CcInfo),
a provider containing [`CompilationContext`](/rules/lib/builtins/CompilationContext)
and
[`LinkingContext`](/rules/lib/builtins/LinkingContext).
Through these it is possible to access information such as all transitive headers
or libraries to link. From `CcInfo` and from the `CcToolchainInfo` custom
Starlark rules should be able to get all the information they need.

If a custom Starlark rule provides `CcInfo`, it's a signal to the C++ rules that
they can also depend on it. Be careful, however - if you only need to propagate
`CcInfo` through the graph to the binary rule that then makes use of it, wrap
`CcInfo` in a different provider. For example, if `java_library` rule wanted
to propagate native dependencies up to the `java_binary`, it shouldn't provide
`CcInfo` directly (`cc_binary` depending on `java_library` doesn't make sense),
it should wrap it in, for example, `JavaCcInfo`.

A complete working example can be found
[in the rules_cc examples](https://github.com/bazelbuild/rules_cc/blob/main/examples/my_c_archive/my_c_archive.bzl){: .external}.

## Reusing logic and actions of C++ rules

_Not stable yet; This section will be updated once the API stabilizes. Follow
[#4570](https://github.com/bazelbuild/bazel/issues/4570){: .external} for up-to-date
information._
