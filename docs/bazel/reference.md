# reference



# Skyframe

The parallel evaluation and incrementality model of Bazel.

## Data model

The data model consists of the following items:

*   `SkyValue`. Also called nodes. `SkyValues` are immutable objects that
    contain all the data built over the course of the build and the inputs of
    the build. Examples are: input files, output files, targets and configured
    targets.
*   `SkyKey`. A short immutable name to reference a `SkyValue`, for example,
    `FILECONTENTS:/tmp/foo` or `PACKAGE://foo`.
*   `SkyFunction`. Builds nodes based on their keys and dependent nodes.
*   Node graph. A data structure containing the dependency relationship between
    nodes.
*   `Skyframe`. Code name for the incremental evaluation framework Bazel is
    based on.

## Evaluation

A build is achieved by evaluating the node that represents the build request.

First, Bazel finds the `SkyFunction` corresponding to the key of the top-level
`SkyKey`. The function then requests the evaluation of the nodes it needs to
evaluate the top-level node, which in turn result in other `SkyFunction` calls,
until the leaf nodes are reached. Leaf nodes are usually ones that represent
input files in the file system. Finally, Bazel ends up with the value of the
top-level `SkyValue`, some side effects (such as output files in the file
system) and a directed acyclic graph of the dependencies between the nodes
involved in the build.

A `SkyFunction` can request `SkyKeys` in multiple passes if it cannot tell in
advance all of the nodes it needs to do its job. A simple example is evaluating
an input file node that turns out to be a symlink: the function tries to read
the file, realizes that it is a symlink, and thus fetches the file system node
representing the target of the symlink. But that itself can be a symlink, in
which case the original function will need to fetch its target, too.

The functions are represented in the code by the interface `SkyFunction` and the
services provided to it by an interface called `SkyFunction.Environment`. These
are the things functions can do:

*   Request the evaluation of another node by way of calling `env.getValue`. If
    the node is available, its value is returned, otherwise, `null` is returned
    and the function itself is expected to return `null`. In the latter case,
    the dependent node is evaluated, and then the original node builder is
    invoked again, but this time the same `env.getValue` call will return a
    non-`null` value.
*   Request the evaluation of multiple other nodes by calling `env.getValues()`.
    This does essentially the same, except that the dependent nodes are
    evaluated in parallel.
*   Do computation during their invocation
*   Have side effects, for example, writing files to the file system. Care needs
    to be taken that two different functions avoid stepping on each other's
    toes. In general, write side effects (where data flows outwards from Bazel)
    are okay, read side effects (where data flows inwards into Bazel without a
    registered dependency) are not, because they are an unregistered dependency
    and as such, can cause incorrect incremental builds.

Well-behaved `SkyFunction` implementations avoid accessing data in any other way
than requesting dependencies (such as by directly reading the file system),
because that results in Bazel not registering the data dependency on the file
that was read, thus resulting in incorrect incremental builds.

Once a function has enough data to do its job, it should return a non-`null`
value indicating completion.

This evaluation strategy has a number of benefits:

*   Hermeticity. If functions only request input data by way of depending on
    other nodes, Bazel can guarantee that if the input state is the same, the
    same data is returned. If all sky functions are deterministic, this means
    that the whole build will also be deterministic.
*   Correct and perfect incrementality. If all the input data of all functions
    is recorded, Bazel can invalidate only the exact set of nodes that need to
    be invalidated when the input data changes.
*   Parallelism. Since functions can only interact with each other by way of
    requesting dependencies, functions that don't depend on each other can be
    run in parallel and Bazel can guarantee that the result is the same as if
    they were run sequentially.

## Incrementality

Since functions can only access input data by depending on other nodes, Bazel
can build up a complete data flow graph from the input files to the output
files, and use this information to only rebuild those nodes that actually need
to be rebuilt: the reverse transitive closure of the set of changed input files.

In particular, two possible incrementality strategies exist: the bottom-up one
and the top-down one. Which one is optimal depends on how the dependency graph
looks like.

*   During bottom-up invalidation, after a graph is built and the set of changed
    inputs is known, all the nodes are invalidated that transitively depend on
    changed files. This is optimal if the same top-level node will be built
    again. Note that bottom-up invalidation requires running `stat()` on all
    input files of the previous build to determine if they were changed. This
    can be improved by using `inotify` or a similar mechanism to learn about
    changed files.

*   During top-down invalidation, the transitive closure of the top-level node
    is checked and only those nodes are kept whose transitive closure is clean.
    This is better if the node graph is large, but the next build only needs a
    small subset of it: bottom-up invalidation would invalidate the larger graph
    of the first build, unlike top-down invalidation, which just walks the small
    graph of second build.

Bazel only does bottom-up invalidation.

To get further incrementality, Bazel uses _change pruning_: if a node is
invalidated, but upon rebuild, it is discovered that its new value is the same
as its old value, the nodes that were invalidated due to a change in this node
are "resurrected".

This is useful, for example, if one changes a comment in a C++ file: then the
`.o` file generated from it will be the same, thus, it is unnecessary to call
the linker again.

## Incremental Linking / Compilation

The main limitation of this model is that the invalidation of a node is an
all-or-nothing affair: when a dependency changes, the dependent node is always
rebuilt from scratch, even if a better algorithm would exist that would mutate
the old value of the node based on the changes. A few examples where this would
be useful:

*   Incremental linking
*   When a single class file changes in a JAR file, it is possible
    modify the JAR file in-place instead of building it from scratch again.

The reason why Bazel does not support these things in a principled way
is twofold:

*   There were limited performance gains.
*   Difficulty to validate that the result of the mutation is the same as that
    of a clean rebuild would be, and Google values builds that are bit-for-bit
    repeatable.

Until now, it was possible to achieve good enough performance by decomposing an
expensive build step and achieving partial re-evaluation that way. For example,
in an Android app, you can split all the classes into multiple groups and dex
them separately. This way, if classes in a group are unchanged, the dexing does
not have to be redone.

## Mapping to Bazel concepts

This is high level summary of the key `SkyFunction` and `SkyValue`
implementations Bazel uses to perform a build:

*   **FileStateValue**. The result of an `lstat()`. For existent files, the
    function also computes additional information in order to detect changes to
    the file. This is the lowest level node in the Skyframe graph and has no
    dependencies.
*   **FileValue**. Used by anything that cares about the actual contents or
    resolved path of a file. Depends on the corresponding `FileStateValue` and
    any symlinks that need to be resolved (such as the `FileValue` for `a/b`
    needs the resolved path of `a` and the resolved path of `a/b`). The
    distinction between `FileValue` and `FileStateValue` is important because
    the latter can be used in cases where the contents of the file are not
    actually needed. For example, the file contents are irrelevant when
    evaluating file system globs (such as `srcs=glob(["*/*.java"])`).
*   **DirectoryListingStateValue**. The result of `readdir()`. Like
    `FileStateValue`, this is the lowest level node and has no dependencies.
*   **DirectoryListingValue**. Used by anything that cares about the entries of
    a directory. Depends on the corresponding `DirectoryListingStateValue`, as
    well as the associated `FileValue` of the directory.
*   **PackageValue**. Represents the parsed version of a BUILD file. Depends on
    the `FileValue` of the associated `BUILD` file, and also transitively on any
    `DirectoryListingValue` that is used to resolve the globs in the package
    (the data structure representing the contents of a `BUILD` file internally).
*   **ConfiguredTargetValue**. Represents a configured target, which is a tuple
    of the set of actions generated during the analysis of a target and
    information provided to dependent configured targets. Depends on the
    `PackageValue` the corresponding target is in, the `ConfiguredTargetValues`
    of direct dependencies, and a special node representing the build
    configuration.
*   **ArtifactValue**. Represents a file in the build, be it a source or an
    output artifact. Artifacts are almost equivalent to files, and are used to
    refer to files during the actual execution of build steps. Source files
    depends on the `FileValue` of the associated node, and output artifacts
    depend on the `ActionExecutionValue` of whatever action generates the
    artifact.
*   **ActionExecutionValue**. Represents the execution of an action. Depends on
    the `ArtifactValues` of its input files. The action it executes is contained
    within its SkyKey, which is contrary to the concept that SkyKeys should be
    small. Note that `ActionExecutionValue` and `ArtifactValue` are unused if
    the execution phase does not run.

As a visual aid, this diagram shows the relationships between
SkyFunction implementations after a build of Bazel itself:

![A graph of SkyFunction implementation relationships](/reference/skyframe.png)


# Bazel Glossary

### Action

A command to run during the build, for example, a call to a compiler that takes
[artifacts](#artifact) as inputs and produces other artifacts as outputs.
Includes metadata like the command line arguments, action key, environment
variables, and declared input/output artifacts.

**See also:** [Rules documentation](/extending/rules#actions)

### Action cache

An on-disk cache that stores a mapping of executed [actions](#action) to the
outputs they created. The cache key is known as the [action key](#action-key). A
core component for Bazel's incrementality model. The cache is stored in the
output base directory and thus survives Bazel server restarts.

### Action graph

An in-memory graph of [actions](#action) and the [artifacts](#artifact) that
these actions read and generate. The graph might include artifacts that exist as
source files (for example, in the file system) as well as generated
intermediate/final artifacts that are not mentioned in `BUILD` files. Produced
during the [analysis phase](#analysis-phase) and used during the [execution
phase](#execution-phase).

### Action graph query (aquery)

A [query](#query-concept) tool that can query over build [actions](#action).
This provides the ability to analyze how [build rules](#rule) translate into the
actual work builds do.

### Action key

The cache key of an [action](#action). Computed based on action metadata, which
might include the command to be executed in the action, compiler flags, library
locations, or system headers, depending on the action. Enables Bazel to cache or
invalidate individual actions deterministically.

### Analysis phase

The second phase of a build. Processes the [target graph](#target-graph)
specified in [`BUILD` files](#build-file) to produce an in-memory [action
graph](#action-graph) that determines the order of actions to run during the
[execution phase](#execution-phase). This is the phase in which rule
implementations are evaluated.

### Artifact

A source file or a generated file. Can also be a directory of files, known as
[tree artifacts](#tree-artifact).

An artifact may be an input to multiple actions, but must only be generated by
at most one action.

An artifact that corresponds to a [file target](#target) can be addressed by a
label.

### Aspect

A mechanism for rules to create additional [actions](#action) in their
dependencies. For example, if target A depends on B, one can apply an aspect on
A that traverses *up* a dependency edge to B, and runs additional actions in B
to generate and collect additional output files. These additional actions are
cached and reused between targets requiring the same aspect. Created with the
`aspect()` Starlark Build API function. Can be used, for example, to generate
metadata for IDEs, and create actions for linting.

**See also:** [Aspects documentation](/extending/aspects)

### Aspect-on-aspect

A composition mechanism whereby aspects can be applied to the results
of other aspects. For example, an aspect that generates information for use by
IDEs can be applied on top of an aspect that generates `.java` files from a
proto.

For an aspect `A` to apply on top of aspect `B`, the [providers](#provider) that
`B` advertises in its [`provides`](/rules/lib/globals#aspect.provides) attribute
must match what `A` declares it wants in its [`required_aspect_providers`](/rules/lib/globals#aspect.required_aspect_providers)
attribute.

### Attribute

A parameter to a [rule](#rule), used to express per-target build information.
Examples include `srcs`, `deps`, and `copts`, which respectively declare a
target's source files, dependencies, and custom compiler options. The particular
attributes available for a given target depend on its rule type.

### .bazelrc

Bazel’s configuration file used to change the default values for [startup
flags](#startup-flags) and [command flags](#command-flags), and to define common
groups of options that can then be set together on the Bazel command line using
a `--config` flag. Bazel can combine settings from multiple bazelrc files
(systemwide, per-workspace, per-user, or from a custom location), and a
`bazelrc` file may also import settings from other `bazelrc` files.

### Blaze

The Google-internal version of Bazel. Google’s main build system for its
mono-repository.

### BUILD File

A `BUILD` file is the main configuration file that tells Bazel what software
outputs to build, what their dependencies are, and how to build them. Bazel
takes a `BUILD` file as input and uses the file to create a graph of dependencies
and to derive the actions that must be completed to build intermediate and final
software outputs. A `BUILD` file marks a directory and any sub-directories not
containing a `BUILD` file as a [package](#package), and can contain
[targets](#target) created by [rules](#rule). The file can also be named
`BUILD.bazel`.

### BUILD.bazel File

See [`BUILD` File](#build-file). Takes precedence over a `BUILD` file in the same
directory.

### .bzl File

A file that defines rules, [macros](#macro), and constants written in
[Starlark](#starlark). These can then be imported into [`BUILD`
files](#build-file) using the `load()` function.

<!-- TODO: ### Build event protocol -->

<!-- TODO: ### Build flag -->

### Build graph

The dependency graph that Bazel constructs and traverses to perform a build.
Includes nodes like [targets](#target), [configured
targets](#configured-target), [actions](#action), and [artifacts](#artifact). A
build is considered complete when all [artifacts](#artifact) on which a set of
requested targets depend are verified as up-to-date.

### Build setting

A Starlark-defined piece of [configuration](#configuration).
[Transitions](#transition) can set build settings to change a subgraph's
configuration. If exposed to the user as a [command-line flag](#command-flags),
also known as a build flag.

### Clean build

A build that doesn't use the results of earlier builds. This is generally slower
than an [incremental build](#incremental-build) but commonly considered to be
more [correct](#correctness). Bazel guarantees both clean and incremental builds
are always correct.

### Client-server model

The `bazel` command-line client automatically starts a background server on the
local machine to execute Bazel [commands](#command). The server persists across
commands but automatically stops after a period of inactivity (or explicitly via
bazel shutdown). Splitting Bazel into a server and client helps amortize JVM
startup time and supports faster [incremental builds](#incremental-build)
because the [action graph](#action-graph) remains in memory across commands.

### Command

Used on the command line to invoke different Bazel functions, like `bazel
build`, `bazel test`, `bazel run`, and `bazel query`.

### Command flags

A set of flags specific to a [command](#command). Command flags are specified
*after* the command (`bazel build <command flags>`). Flags can be applicable to
one or more commands. For example, `--configure` is a flag exclusively for the
`bazel sync` command, but `--keep_going` is applicable to `sync`, `build`,
`test` and more. Flags are often used for [configuration](#configuration)
purposes, so changes in flag values can cause Bazel to invalidate in-memory
graphs and restart the [analysis phase](#analysis-phase).

### Configuration

Information outside of [rule](#rule) definitions that impacts how rules generate
[actions](#action). Every build has at least one configuration specifying the
target platform, action environment variables, and command-line [build
flags](#command-flags). [Transitions](#transition) may create additional
configurations, such as for host tools or cross-compilation.

**See also:** [Configurations](/extending/rules#configurations)

<!-- TODO: ### Configuration fragment -->

### Configuration trimming

The process of only including the pieces of [configuration](#configuration) a
target actually needs. For example, if you build Java binary `//:j` with C++
dependency `//:c`, it's wasteful to include the value of `--javacopt` in the
configuration of `//:c` because changing `--javacopt` unnecessarily breaks C++
build cacheability.

### Configured query (cquery)

A [query](#query-concept) tool that queries over [configured
targets](#configured-target) (after the [analysis phase](#analysis-phase)
completes). This means `select()` and [build flags](#command-flags) (such as
`--platforms`) are accurately reflected in the results.

**See also:** [cquery documentation](/query/cquery)

### Configured target

The result of evaluating a [target](#target) with a
[configuration](#configuration). The [analysis phase](#analysis-phase) produces
this by combining the build's options with the targets that need to be built.
For example, if `//:foo` builds for two different architectures in the same
build, it has two configured targets: `<//:foo, x86>` and `<//:foo, arm>`.

### Correctness

A build is correct when its output faithfully reflects the state of its
transitive inputs. To achieve correct builds, Bazel strives to be
[hermetic](#hermeticity), reproducible, and making [build
analysis](#analysis-phase) and [action execution](#execution-phase)
deterministic.

### Dependency

A directed edge between two [targets](#target). A target `//:foo` has a *target
dependency* on target `//:bar` if `//:foo`'s attribute values contain a
reference to `//:bar`. `//:foo` has an *action dependency* on `//:bar` if an
action in `//:foo` depends on an input [artifact](#artifact) created by an
action in `//:bar`.

In certain contexts, it could also refer to an _external dependency_; see
[modules](#module).

### Depset

A data structure for collecting data on transitive dependencies. Optimized so
that merging depsets is time and space efficient, because it’s common to have
very large depsets (hundreds of thousands of files). Implemented to
recursively refer to other depsets for space efficiency reasons. [Rule](#rule)
implementations should not "flatten" depsets by converting them to lists unless
the rule is at the top level of the build graph. Flattening large depsets incurs
huge memory consumption. Also known as *nested sets* in Bazel's internal
implementation.

**See also:** [Depset documentation](/extending/depsets)

### Disk cache

A local on-disk blob store for the remote caching feature. Can be used in
conjunction with an actual remote blob store.

### Distdir

A read-only directory containing files that Bazel would otherwise fetch from the
internet using repository rules. Enables builds to run fully offline.

### Dynamic execution

An execution strategy that selects between local and remote execution based on
various heuristics, and uses the execution results of the faster successful
method. Certain [actions](#action) are executed faster locally (for example,
linking) and others are faster remotely (for example, highly parallelizable
compilation). A dynamic execution strategy can provide the best possible
incremental and clean build times.

### Execution phase

The third phase of a build. Executes the [actions](#action) in the [action
graph](#action-graph) created during the [analysis phase](#analysis-phase).
These actions invoke executables (compilers, scripts) to read and write
[artifacts](#artifact). *Spawn strategies* control how these actions are
executed: locally, remotely, dynamically, sandboxed, docker, and so on.

### Execution root

A directory in the [workspace](#workspace)’s [output base](#output-base)
directory where local [actions](#action) are executed in
non-[sandboxed](#sandboxing) builds. The directory contents are mostly symlinks
of input [artifacts](#artifact) from the workspace. The execution root also
contains symlinks to external repositories as other inputs and the `bazel-out`
directory to store outputs. Prepared during the [loading phase](#loading-phase)
by creating a *symlink forest* of the directories that represent the transitive
closure of packages on which a build depends. Accessible with `bazel info
execution_root` on the command line.

### File

See [Artifact](#artifact).

### Hermeticity

A build is hermetic if there are no external influences on its build and test
operations, which helps to make sure that results are deterministic and
[correct](#correctness). For example, hermetic builds typically disallow network
access to actions, restrict access to declared inputs, use fixed timestamps and
timezones, restrict access to environment variables, and use fixed seeds for
random number generators

### Incremental build

An incremental build reuses the results of earlier builds to reduce build time
and resource usage. Dependency checking and caching aim to produce correct
results for this type of build. An incremental build is the opposite of a clean
build.

<!-- TODO: ### Install base -->

### Label

An identifier for a [target](#target). Generally has the form
`@repo//path/to/package:target`, where `repo` is the (apparent) name of the
[repository](#repository) containing the target, `path/to/package` is the path
to the directory that contains the [`BUILD` file](#build-file) declaring the
target (this directory is also known as the [package](#package)), and `target`
is the name of the target itself. Depending on the situation, parts of this
syntax may be omitted.

**See also**: [Labels](/concepts/labels)

### Loading phase

The first phase of a build where Bazel executes [`BUILD` files](#build-file) to
create [packages](#package). [Macros](#macro) and certain functions like
`glob()` are evaluated in this phase. Interleaved with the second phase of the
build, the [analysis phase](#analysis-phase), to build up a [target
graph](#target-graph).

### Legacy macro

A flavor of [macro](#macro) which is declared as an ordinary
[Starlark](#starlark) function, and which runs as a side effect of executing a
`BUILD` file.

Legacy macros can do anything a function can. This means they can be convenient,
but they can also be harder to read, write, and use. A legacy macro might
unexpectedly mutate its arguments or fail when given a `select()` or ill-typed
argument.

Contrast with [symbolic macros](#symbolic-macro).

**See also:** [Legacy macro documentation](/extending/legacy-macros)

### Macro

A mechanism to compose multiple [rule](#rule) target declarations together under
a single [Starlark](#starlark) callable. Enables reusing common rule declaration
patterns across `BUILD` files. Expanded to the underlying rule target
declarations during the [loading phase](#loading-phase).

Comes in two flavors: [symbolic macros](#symbolic-macro) (since Bazel 8) and
[legacy macros](#legacy-macro).

### Mnemonic

A short, human-readable string selected by a rule author to quickly understand
what an [action](#action) in the rule is doing. Mnemonics can be used as
identifiers for *spawn strategy* selections. Some examples of action mnemonics
are `Javac` from Java rules, `CppCompile` from C++ rules, and
`AndroidManifestMerger` from Android rules.

### Module

A Bazel project that can have multiple versions, each of which can have
dependencies on other modules. This is analogous to familiar concepts in other
dependency management systems, such as a Maven _artifact_, an npm _package_, a
Go _module_, or a Cargo _crate_. Modules form the backbone of Bazel's external
dependency management system.

Each module is backed by a [repo](#repository) with a `MODULE.bazel` file at its
root. This file contains metadata about the module itself (such as its name and
version), its direct dependencies, and various other data including toolchain
registrations and [module extension](#module-extension) input.

Module metadata is hosted in Bazel registries.

**See also:** [Bazel modules](/external/module)

### Module Extension

A piece of logic that can be run to generate [repos](#repository) by reading
inputs from across the [module](#module) dependency graph and invoking [repo
rules](#repository-rule). Module extensions have capabilities similar to repo
rules, allowing them to access the internet, perform file I/O, and so on.

**See also:** [Module extensions](/external/extension)

### Native rules

[Rules](#rule) that are built into Bazel and implemented in Java. Such rules
appear in [`.bzl` files](#bzl-file) as functions in the native module (for
example, `native.cc_library` or `native.java_library`). User-defined rules
(non-native) are created using [Starlark](#starlark).

### Output base

A [workspace](#workspace)-specific directory to store Bazel output files. Used
to separate outputs from the *workspace*'s source tree (the [main
repo](#repository)). Located in the [output user root](#output-user-root).

### Output groups

A group of files that is expected to be built when Bazel finishes building a
target. [Rules](#rule) put their usual outputs in the "default output group"
(e.g the `.jar` file of a `java_library`, `.a` and `.so` for `cc_library`
targets). The default output group is the output group whose
[artifacts](#artifact) are built when a target is requested on the command line.
Rules can define more named output groups that can be explicitly specified in
[`BUILD` files](#build-file) (`filegroup` rule) or the command line
(`--output_groups` flag).

### Output user root

A user-specific directory to store Bazel's outputs. The directory name is
derived from the user's system username. Prevents output file collisions if
multiple users are building the same project on the system at the same time.
Contains subdirectories corresponding to build outputs of individual workspaces,
also known as [output bases](#output-base).

### Package

The set of [targets](#target) defined by a [`BUILD` file](#build-file). A
package's name is the `BUILD` file's path relative to the [repo](#repository)
root. A package can contain subpackages, or subdirectories containing `BUILD`
files, thus forming a package hierarchy.

### Package group

A [target](#target) representing a set of packages. Often used in `visibility`
attribute values.

### Platform

A "machine type" involved in a build. This includes the machine Bazel runs on
(the "host" platform), the machines build tools execute on ("exec" platforms),
and the machines targets are built for ("target platforms").

### Provider

A schema describing a unit of information to pass between
[rule targets](#rule-target) along dependency relationships. Typically this
contains information like compiler options, transitive source or output files,
and build metadata. Frequently used in conjunction with [depsets](#depset) to
efficiently store accumulated transitive data. An example of a built-in provider
is `DefaultInfo`.

Note: The object holding specific data for a given rule target is
referred to as a "provider instance", although sometimes this is conflated with
"provider".

**See also:** [Provider documentation](/extending/rules#providers)

### Query (concept)

The process of analyzing a [build graph](#build-graph) to understand
[target](#target) properties and dependency structures. Bazel supports three
query variants: [query](#query-command), [cquery](#configured-query), and
[aquery](#action-graph-query).

### query (command)

A [query](#query-concept) tool that operates over the build's post-[loading
phase](#loading-phase) [target graph](#target-graph). This is relatively fast,
but can't analyze the effects of `select()`, [build flags](#command-flags),
[artifacts](#artifact), or build [actions](#action).

**See also:** [Query how-to](/query/guide), [Query reference](/query/language)

### Repository

A directory tree with a boundary marker file at its root, containing source
files that can be used in a Bazel build. Often shortened to just **repo**.

A repo boundary marker file can be `MODULE.bazel` (signaling that this repo
represents a Bazel module), `REPO.bazel`, or in legacy contexts, `WORKSPACE` or
`WORKSPACE.bazel`. Any repo boundary marker file will signify the boundary of a
repo; multiple such files can coexist in a directory.

The *main repo* is the repo in which the current Bazel command is being run.

*External repos* are defined by specifying [modules](#module) in `MODULE.bazel`
files, or invoking [repo rules](#repository-rule) in [module
extensions](#module-extension). They can be fetched on demand to a predetermined
"magical" location on disk.

Each repo has a unique, constant *canonical* name, and potentially different
*apparent* names when viewed from other repos.

**See also**: [External dependencies overview](/external/overview)

### Repository cache

A shared content-addressable cache of files downloaded by Bazel for builds,
shareable across [workspaces](#workspace). Enables offline builds after the
initial download. Commonly used to cache files downloaded through [repository
rules](#repository-rule) like `http_archive` and repository rule APIs like
`repository_ctx.download`. Files are cached only if their SHA-256 checksums are
specified for the download.

### Repository rule

A schema for repository definitions that tells Bazel how to materialize (or
"fetch") a [repository](#repository). Often shortened to just **repo rule**.
Repo rules are invoked by Bazel internally to define repos backed by
[modules](#module), or can be invoked by [module extensions](#module-extension).
Repo rules can access the internet or perform file I/O; the most common repo
rule is `http_archive` to download an archive containing source files from the
internet.

**See also:** [Repo rule documentation](/external/repo)

### Reproducibility

The property of a build or test that a set of inputs to the build or test will
always produce the same set of outputs every time, regardless of time, method,
or environment. Note that this does not necessarily imply that the outputs are
[correct](#correctness) or the desired outputs.

### Rule

A schema for defining [rule targets](#rule-target) in a `BUILD` file, such as
`cc_library`. From the perspective of a `BUILD` file author, a rule consists of
a set of [attributes](#attributes) and black box logic. The logic tells the
rule target how to produce output [artifacts](#artifact) and pass information to
other rule targets. From the perspective of `.bzl` authors, rules are the
primary way to extend Bazel to support new programming languages and
environments.

Rules are instantiated to produce rule targets in the
[loading phase](#loading-phase). In the [analysis phase](#analysis-phase) rule
targets communicate information to their downstream dependencies in the form of
[providers](#provider), and register [actions](#action) describing how to
generate their output artifacts. These actions are run in the [execution
phase](#execution-phase).

Note: Historically the term "rule" has been used to refer to a rule target.
This usage was inherited from tools like Make, but causes confusion and should
be avoided for Bazel.

**See also:** [Rules documentation](/extending/rules)

### Rule target

A [target](#target) that is an instance of a rule. Contrasts with file targets
and package groups. Not to be confused with [rule](#rule).

### Runfiles

The runtime dependencies of an executable [target](#target). Most commonly, the
executable is the executable output of a test rule, and the runfiles are runtime
data dependencies of the test. Before the invocation of the executable (during
bazel test), Bazel prepares the tree of runfiles alongside the test executable
according to their source directory structure.

**See also:** [Runfiles documentation](/extending/rules#runfiles)

### Sandboxing

A technique to isolate a running [action](#action) inside a restricted and
temporary [execution root](#execution-root), helping to ensure that it doesn’t
read undeclared inputs or write undeclared outputs. Sandboxing greatly improves
[hermeticity](#hermeticity), but usually has a performance cost, and requires
support from the operating system. The performance cost depends on the platform.
On Linux, it's not significant, but on macOS it can make sandboxing unusable.

### Skyframe

[Skyframe](/reference/skyframe) is the core parallel, functional, and incremental evaluation framework of Bazel.

<!-- TODO: ### Spawn strategy -->

### Stamping

A feature to embed additional information into Bazel-built
[artifacts](#artifact). For example, this can be used for source control, build
time and other workspace or environment-related information for release builds.
Enable through the `--workspace_status_command` flag and [rules](/extending/rules) that
support the stamp attribute.

### Starlark

The extension language for writing [rules](/extending/rules) and [macros](#macro). A
restricted subset of Python (syntactically and grammatically) aimed for the
purpose of configuration, and for better performance. Uses the [`.bzl`
file](#bzl-file) extension. [`BUILD` files](#build-file) use an even more
restricted version of Starlark (such as no `def` function definitions), formerly
known as Skylark.

**See also:** [Starlark language documentation](/rules/language)

<!-- TODO: ### Starlark rules -->

<!-- TODO: ### Starlark rule sandwich -->

### Startup flags

The set of flags specified between `bazel` and the [command](#query-command),
for example, bazel `--host_jvm_debug` build. These flags modify the
[configuration](#configuration) of the Bazel server, so any modification to
startup flags causes a server restart. Startup flags are not specific to any
command.

### Symbolic macro

A flavor of [macro](#macro) which is declared with a [rule](#rule)-like
[attribute](#attribute) schema, allows hiding internal declared
[targets](#target) from their own package, and enforces a predictable naming
pattern on the targets that the macro declares. Designed to avoid some of the
problems seen in large [legacy macro](#legacy-macro) codebases.

**See also:** [Symbolic macro documentation](/extending/macros)

### Target

An object that is defined in a [`BUILD` file](#build-file) and identified by a
[label](#label). Targets represent the buildable units of a workspace from
the perspective of the end user.

A target that is declared by instantiating a [rule](#rule) is called a [rule
target](#rule-target). Depending on the rule, these may be runnable (like
`cc_binary`) or testable (like `cc_test`). Rule targets typically depend on
other targets via their [attributes](#attribute) (such as `deps`); these
dependencies form the basis of the [target graph](#target-graph).

Aside from rule targets, there are also file targets and [package group](#package-group)
targets. File targets correspond to [artifacts](#artifact) that are referenced
within a `BUILD` file. As a special case, the `BUILD` file of any package is
always considered a source file target in that package.

Targets are discovered during the [loading phase](#loading-phase). During the
[analysis phase](#analysis-phase), targets are associated with [build
configurations](#configuration) to form [configured
targets](#configured-target).

### Target graph

An in-memory graph of [targets](#target) and their dependencies. Produced during
the [loading phase](#loading-phase) and used as an input to the [analysis
phase](#analysis-phase).

### Target pattern

A way to specify a group of [targets](#target) on the command line. Commonly
used patterns are `:all` (all rule targets), `:*` (all rule + file targets),
`...` (current [package](#package) and all subpackages recursively). Can be used
in combination, for example, `//...:*` means all rule and file targets in all
packages recursively from the root of the [workspace](#workspace).

### Tests

Rule [targets](#target) instantiated from test rules, and therefore contains a
test executable. A return code of zero from the completion of the executable
indicates test success. The exact contract between Bazel and tests (such as test
environment variables, test result collection methods) is specified in the [Test
Encyclopedia](/reference/test-encyclopedia).

### Toolchain

A set of tools to build outputs for a language. Typically, a toolchain includes
compilers, linkers, interpreters or/and linters. A toolchain can also vary by
platform, that is, a Unix compiler toolchain's components may differ for the
Windows variant, even though the toolchain is for the same language. Selecting
the right toolchain for the platform is known as toolchain resolution.

### Top-level target

A build [target](#target) is top-level if it’s requested on the Bazel command
line. For example, if `//:foo` depends on `//:bar`, and `bazel build //:foo` is
called, then for this build, `//:foo` is top-level, and `//:bar` isn’t
top-level, although both targets will need to be built. An important difference
between top-level and non-top-level targets is that [command
flags](#command-flags) set on the Bazel command line (or via
[.bazelrc](#bazelrc)) will set the [configuration](#configuration) for top-level
targets, but might be modified by a [transition](#transition) for non-top-level
targets.

### Transition

A mapping of [configuration](#configuration) state from one value to another.
Enables [targets](#target) in the [build graph](#build-graph) to have different
configurations, even if they were instantiated from the same [rule](#rule). A
common usage of transitions is with *split* transitions, where certain parts of
the [target graph](#target-graph) is forked with distinct configurations for
each fork. For example, one can build an Android APK with native binaries
compiled for ARM and x86 using split transitions in a single build.

**See also:** [User-defined transitions](/extending/config#user-defined-transitions)

### Tree artifact

An [artifact](#artifact) that represents a collection of files. Since these
files are not themselves artifacts, an [action](#action) operating on them must
instead register the tree artifact as its input or output.

### Visibility

One of two mechanisms for preventing unwanted dependencies in the build system:
*target visibility* for controlling whether a [target](#target) can be depended
upon by other targets; and *load visibility* for controlling whether a `BUILD`
or `.bzl` file may load a given `.bzl` file. Without context, usually
"visibility" refers to target visibility.

**See also:** [Visibility documentation](/concepts/visibility)

### Workspace

The environment shared by all Bazel commands run from the same [main
repository](#repository).

Note that historically the concepts of "repository" and "workspace" have been
conflated; the term "workspace" has often been used to refer to the main
repository, and sometimes even used as a synonym of "repository". Such usage
should be avoided for clarity.

<html devsite>
<head>
  <meta name="project_path" value="/_project.yaml">
  <meta name="book_path" value="/_book.yaml">
</head>
<body>

# Bazel flag cheat sheet

Navigating Bazel's extensive list of command line flags can be a challenge.
This page focuses on the most crucial flags you'll need to know.

<style>

table {
  width: 100%;
}
.flag {
  width: 28%'
  align: left;
}
.description {
  width: 72%;
  align:left;
}

</style>

<aside class="tip">
  <b>Tip:</b> Select the flag name in table to navigate to its entry in the
  command line reference.
</aside>

## Useful general options

The following flags are meant to be set explicitly on the command line.

<table>
  <tr>
    <th class="flag" >Flag</th>
    <th class="description" >Description</th>
  </tr>

  <tr>
    <td>
      <h3 id="flag-config" data-text="config"><code><a href="https://bazel.build/reference/command-line-reference#flag--config">--config</a></code></h3>
    </td>
    <td>

You can organize flags in a <strong>.bazelrc</strong> file into configurations,
like ones for debugging or release builds. Additional configuration groups can
be selected with <code>--config=<strong>&lt;group&gt;</strong></code>.

</td>

  </tr>

  <tr>
    <td>
      <h3 id="flag-keep-going" data-text="keep_going"><code><a href="https://bazel.build/reference/command-line-reference#flag--keep_going">--keep_going</a></code></h3>
    </td>
    <td>

Bazel should try as much as possible to continue with build and test execution.
By default, Bazel fails eagerly.

    </td>
  </tr>

  <tr>
    <td>
      <h3 id="flag-remote-download-outputs" data-text="remote_download_outputs"><code><a href="https://bazel.build/reference/command-line-reference#flag--remote_download_outputs">--remote_download_outputs</a></code></h3>
    </td>
    <td>

When using remote execution or caching (both disk and remote), you can signal to
Bazel that you
want to download <strong>all</strong> (intermediate) build artifacts as follows:

<pre class="prettyprint lang-sh">
--remote_download_outputs=<strong>all</strong>
</pre>

By default, Bazel only downloads top-level artifacts, such as the final binary,
and intermediate artifacts that are necessary for local actions.

</td>

  </tr>

  <tr>
    <td>
      <h3 id="flag-stamp" data-text="stamp"><code><a href="https://bazel.build/reference/command-line-reference#flag--stamp">--stamp</a></code></h3>
    </td>
    <td>

Adds build info (user, timestamp) to binaries.

<aside class="note">
  <b>Note:</b> Because this increases build time, it's only intended for release
  builds.
</aside>

</td>
</tr>
</table>

## Uncover Build & Test Issues

The following flags can help you better understand Bazel build or test errors.

<table>
  <tr>
    <th class="flag" >Flag</th>
    <th class="description" >Description</th>
  </tr>

  <tr>
    <td>
       <h3 id="flag-announce-rc" data-text="announce_rc"><code><a href="https://bazel.build/reference/command-line-reference#flag--announce_rc">--announce_rc</a></code></h3>
    </td>
    <td>

Shows which flags are implicitly set through user-defined,
machine-defined, or project-defined <strong>.bazelrc</strong> files.

</td>

  </tr>

  <tr>
    <td>
      <h3 id="flag-auto-output-filter" data-text="auto_output_filter"><code><a href="https://bazel.build/reference/command-line-reference#flag--auto_output_filter">--auto_output_filter</a></code></h3>
    </td>
    <td>

By default, Bazel tries to prevent log spam and does only print compiler
warnings and Starlark debug output for packages and subpackages requested on the
command line. To disable all filtering, set
<code>--auto_output_filter=<strong>none</strong></code>.

</td>

  </tr>

  <tr>
    <td>
      <h3 id="flag-sandbox-debug" data-text="sandbox_debug"><code><a href="https://bazel.build/reference/command-line-reference#flag--sandbox_debug">--sandbox_debug</a></code></h3>
    </td>
    <td>

Lets you drill into sandboxing errors. For details on why Bazel sandboxes
builds by default and what gets sandboxed, see our
<a href="https://bazel.build/docs/sandboxing">sandboxing documentation</a>.

<aside class="tip">
  <b>Tip:</b> If you think the error might be caused by sandboxing,
  try turning sandboxing off temporarily.

  <p>To do this, add <code>--spawn_strategy=<strong>standalone</strong></code>
  to your command.</p>

</aside>

</td>

  </tr>

  <tr>
    <td>
      <h3 id="flag-subcommands" data-text="subcommands"><code><a href="https://bazel.build/reference/command-line-reference#flag--subcommands">--subcommands (-s)</a></code></h3>
    </td>
    <td>

Displays a comprehensive list of every command that Bazel runs during a build,
regardless of whether it succeeds or fails

</td>
 </tr>
 </table>

## Startup

Caution: Startup flags need to be passed before the command and cause
a server restart. Toggle these flags with caution.

<table>
  <tr>
    <th class="flag" >Flag</th>
    <th class="description" >Description</th>
  </tr>

  <tr>
    <td>
       <h3 id="flag-bazelrc" data-text="bazelrc"><code><a href="https://bazel.build/reference/command-line-reference#flag--bazelrc">--bazelrc</a></code></h3>
    </td>
    <td>

You can specify default Bazel options in <strong>.bazelrc</strong> files. If
multiple <strong>.bazelrc</strong> files exist, you can select which
<strong>.bazelrc</strong> file is used by adding <code>--bazelrc=<strong>&lt;path to
the .bazelrc file&gt;</strong></code>.

<aside class="tip">
  <b>Tip:</b> <code>--bazelrc=<strong>dev/null</strong></code> disables the
  search for <strong>.bazelrc</strong> files.

  <p>This is ideal for scenarios where you want to ensure a clean build
  environment, such as release builds, and prevent any unintended configuration
  changes from <strong>.bazelrc</strong> files</p>

</aside>
</td>
</tr>

  <tr>
    <td>
    <h3 id="flag-host-jvm-args" data-text="host_jvm_args"><code><a href="https://bazel.build/docs/user-manual#host-jvm-args">--host_jvm_args</a></code></h3>
    </td>
    <td>

Limits the amount of RAM the Bazel server uses.

For example, the following limits the Bazel heap size to <strong>3</strong>GB:

<pre class="prettyprint lang-sh">
--host_jvm_args=<strong>-Xmx3g</strong>
</pre>

<aside class="note">
  <b>Note:</b> <code>-Xmx</code> is used to set the maximum heap size for the
  Java Virtual Machine (JVM). The heap is the area of memory where objects are
  allocated. The correct format for this option is <code>-Xmx&lt;size&gt;</code>
  , where <code>&lt;size&gt;</code> is the maximum heap size, specified with a
  unit such as:

<ul>
  <li>m for megabytes</li>
  <li>g for gigabytes</li>
  <li>k for kilobytes</li>
</ul>

</aside>

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-output-base" data-text="output_base"><code><a href="https://bazel.build/reference/command-line-reference#flag--output_base">--output_base</a></code></h3>
    </td>
    <td>

Controls Bazel's output tree. Bazel doesn't store build outputs, including logs,
within the source tree itself. Instead, it uses a distinct output tree for this
purpose.

<aside class="tip">
  <b>Tip:</b> Using multiple output bases in one Bazel workspace lets you run
multiple Bazel servers concurrently. This can be useful when trying to avoid
analysis thrashing. For more information,
see <a href="https://bazel.build/run/scripts#output-base-option">Choosing the output base</a>.
</aside>

</td>

  </tr>
 </table>

## Bazel tests

The following flags are related to Bazel test

<table>
  <tr>
    <th class="flag" >Flag</th>
    <th class="description" >Description</th>
  </tr>

  <tr>
    <td>
       <h3 id="flag-java-debug" data-text="java_debug"><code><a href="https://bazel.build/reference/command-line-reference#flag--java_debug">--java_debug</a></code></h3>
    </td>
    <td>

Causes Java tests to wait for a debugger connection before being executed.

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-runs-per-test" data-text="runs_per_test"><code><a href="https://bazel.build/reference/command-line-reference#flag--runs_per_test">--runs_per_test</a></code></h3>
    </td>
    <td>

The number of times to run tests. For example, to run tests N times, add
<code>--runs_per_test=<strong>N</strong></code>. This can be useful to debug
flaky tests and see whether a fix causes a test to pass consistently.

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-test-filter" data-text="test_filter"><code><a href="https://bazel.build/reference/command-line-reference#flag--test_filter">--test_filter</a></code></h3>
    </td>
    <td>

This flag is particularly useful when iterating on a single test method, such as
when a change you made breaks a test. Instead of re-running
all the test methods in the test suite, you can focus solely on the specific
test(s) that failed. This allows for faster feedback and more efficient
debugging. This flag is often used in conjunction with
<code>--test_output=<strong>streamed</strong></code> for real-time test output.

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-test-output" data-text="test_output"><code><a href="https://bazel.build/reference/command-line-reference#flag--test_output">--test_output</a></code></h3>
    </td>
    <td>

Specifies the output mode. By default, Bazel captures test output in
local log files. When iterating on a broken test, you typically want to use
<code>--test_output=<strong>streamed</strong></code> to see the test output in
real time.

</td>

  </tr>
 </table>

## Bazel run

The following flags are related to Bazel run.

<table>
  <tr>
    <th class="flag" >Flag</th>
    <th class="description" >Description</th>
  </tr>

  <tr>
    <td>
        <h3 id="flag-run-under" data-text="run_under"><code><a href="https://bazel.build/reference/command-line-reference#flag--run_under">--run_under</a></code></h3>
    </td>
    <td>

Changes how executables are invoked. For example <code>--run_under=<strong>"strace -c"</strong></code> is
commonly used for debugging.

</td>

  </tr>

 </table>

## User-specific bazelrc options

The following flags are related to user-specific **.bazelrc**
options.

<table>
  <tr>
    <th class="flag" >Flag</th>
    <th class="description" >Description</th>
  </tr>

  <tr>
    <td>
       <h3 id="flag-disk-cache" data-text="disk_cache"><code><a href="https://bazel.build/reference/command-line-reference#flag--disk_cache">--disk_cache</a></code></h3>
    </td>
    <td>

A path to a directory where Bazel can read and write actions and action outputs.
If the directory doesn't exist, it will be created.

You can share build artifacts between multiple branches or workspaces and speed
up Bazel builds by adding
<code>--disk_cache=<strong>&lt;path&gt;</strong></code> to your command.

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-jobs" data-text="jobs"><code><a href="https://bazel.build/reference/command-line-reference#flag--jobs">--jobs</a></code></h3>
    </td>
    <td>

The number of concurrent jobs to run.

This is typically only required when using remote execution where a remote build
cluster executes more jobs than you have cores locally.

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-local-resources" data-text="local_resources"><code><a href="https://bazel.build/reference/command-line-reference#flag--local_resources">--local_resources</a></code></h3>
    </td>
    <td>

Limits how much CPU or RAM is consumed by locally running actions.

<aside class="note">
  <b>Note:</b> This has no impact on the amount of CPU or RAM that the Bazel
  server itself consumes for tasks like analysis and build orchestration.
</aside>

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-sandbox-base" data-text="sandbox_base"><code><a href="https://bazel.build/reference/command-line-reference#flag--sandbox_base">--sandbox_base</a></code></h3>
    </td>
    <td>

Lets the sandbox create its sandbox directories underneath this path. By
default, Bazel executes local actions sandboxed which adds some overhead to the
build.

<aside class="tip">
  <b>Tip:</b> Specify a path on tmpfs, for example <code>/run/shm</code>, to
  possibly improve performance a lot when your build or tests have many input
  files.
</aside>

</td>
  </tr>
 </table>

## Project-specific bazelrc options

The following flags are related to project-specific <strong>.bazelrc</strong>
options.

<table>
  <tr>
    <th class="flag" >Flag</th>
    <th class="description" >Description</th>
  </tr>

  <tr>
    <td>
       <h3 id="flag-flaky-test-attempts" data-text="flaky_test_attempts"><code><a href="https://bazel.build/reference/command-line-reference#flag--flaky_test_attempts">--flaky_test_attempts</a></code></h3>
    </td>
    <td>

Retry each test up to the specified number of times in case of any
test failure. This is especially useful on Continuous Integration. Tests that
require more than one attempt to pass are marked as <strong>FLAKY</strong> in
the test summary.

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-remote-cache" data-text="remote_cache"><code><a href="https://bazel.build/reference/command-line-reference#flag--remote_cache">--remote_cache</a></code></h3>
    </td>
    <td>

A URI of a caching endpoint. Setting up remote caching can be a great way to
speed up Bazel builds. It can be combined with a local disk cache.

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-remote-download-regex" data-text="remote_download_regex"><code><a href="https://bazel.build/reference/command-line-reference#flag--remote_download_regex">--remote_download_regex</a></code></h3>
    </td>
    <td>

Force remote build outputs whose path matches this pattern to be downloaded,
irrespective of the <code>--remote_download_outputs</code> setting. Multiple
patterns may be specified by repeating this flag.

</td>

  </tr>

  <tr>
    <td>
     <h3 id="flag-remote-executor" data-text="remote_executor"><code><a href="https://bazel.build/reference/command-line-reference#flag--remote_executor">--remote_executor</a></code></h3>
    </td>
    <td>

<code>HOST</code> or <code>HOST:PORT</code> of a remote execution endpoint. Pass this if you are using
a remote execution service. You'll often need to Add
<code>--remote_instance_name=<strong>&lt;name&gt;</strong></code>.

</td>

  </tr>

  <tr>
    <td>
     <h3 id="flag-remote-instance-name" data-text="remote_instance_name"><code><a href="https://bazel.build/reference/command-line-reference#flag--remote_instance_name">--remote_instance_name</a></code></h3>
    </td>
    <td>

The value to pass as <code>instance_name</code> in the remote execution API.

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-show-timestamps" data-text="show-timestamps"><code><a href="https://bazel.build/docs/user-manual#show-timestamps">--show-timestamps</a></code></h3>
    </td>
    <td>

If specified, a timestamp is added to each message generated by Bazel specifying
the time at which the message was displayed. This is useful on CI systems to
quickly understand what step took how long.

</td>

  </tr>

  <tr>
    <td>
    <h3 id="flag-spawn-strategy" data-text="spawn_strategy"><code><a href="https://bazel.build/reference/command-line-reference#flag--spawn_strategy">--spawn_strategy</a></code></h3>
    </td>
    <td>

Even with remote execution, running some build actions locally might be faster.
This depends on factors like your build cluster's capacity, network speed, and
network delays.

<aside class="tip">
  <b>Tip:</b> To run actions both locally and remotely and accept
the faster result add <code>--spawn_strategy=<strong>dynamic</strong></code>
to your build command.
</aside>

</td>

  </tr>

 </table>
</body>
</html>


# Test encyclopedia

An exhaustive specification of the test execution environment.

## Background

The Bazel BUILD language includes rules which can be used to define automated
test programs in many languages.

Tests are run using [`bazel test`](/docs/user-manual#test).

Users may also execute test binaries directly. This is allowed but not endorsed,
as such an invocation will not adhere to the mandates described below.

Tests should be *hermetic*: that is, they ought to access only those resources
on which they have a declared dependency. If tests are not properly hermetic
then they do not give historically reproducible results. This could be a
significant problem for culprit finding (determining which change broke a test),
release engineering auditability, and resource isolation of tests (automated
testing frameworks ought not DDOS a server because some tests happen to talk to
it).

## Objective

The goal of this page is to formally establish the runtime environment for and
expected behavior of Bazel tests. It will also impose requirements on the test
runner and the build system.

The test environment specification helps test authors avoid relying on
unspecified behavior, and thus gives the testing infrastructure more freedom to
make implementation changes. The specification tightens up some holes that
currently allow many tests to pass despite not being properly hermetic,
deterministic, and reentrant.

This page is intended to be both normative and authoritative. If this
specification and the implemented behavior of test runner disagree, the
specification takes precedence.

## Proposed Specification

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" are to be interpreted as
described in IETF RFC 2119.

## Purpose of tests

The purpose of Bazel tests is to confirm some property of the source files
checked into the repository. (On this page, "source files" includes test data,
golden outputs, and anything else kept under version control.) One user writes a
test to assert an invariant which they expect to be maintained. Other users
execute the test later to check whether the invariant has been broken. If the
test depends on any variables other than source files (non-hermetic), its value
is diminished, because the later users cannot be sure their changes are at fault
when the test stops passing.

Therefore the outcome of a test must depend only on:

*   source files on which the test has a declared dependency
*   products of the build system on which the test has a declared dependency
*   resources whose behavior is guaranteed by the test runner to remain constant

Currently, such behavior is not enforced. However, test runners reserve the
right to add such enforcement in the future.

## Role of the build system

Test rules are analogous to binary rules in that each must yield an executable
program. For some languages, this is a stub program which combines a
language-specific harness with the test code. Test rules must produce other
outputs as well. In addition to the primary test executable, the test runner
will need a manifest of **runfiles**, input files which should be made available
to the test at runtime, and it may need information about the type, size, and
tags of a test.

The build system may use the runfiles to deliver code as well as data. (This
might be used as an optimization to make each test binary smaller by sharing
files across tests, such as through the use of dynamic linking.) The build system
should ensure that the generated executable loads these files via the runfiles
image provided by the test runner, rather than hardcoded references to absolute
locations in the source or output tree.

## Role of the test runner

From the point of view of the test runner, each test is a program which can be
invoked with `execve()`. There may be other ways to execute tests; for example,
an IDE might allow the execution of Java tests in-process. However, the result
of running the test as a standalone process must be considered authoritative. If
a test process runs to completion and terminates normally with an exit code of
zero, the test has passed. Any other result is considered a test failure. In
particular, writing any of the strings `PASS` or `FAIL` to stdout has no
significance to the test runner.

If a test takes too long to execute, exceeds some resource limit, or the test
runner otherwise detects prohibited behavior, it may choose to kill the test and
treat the run as a failure. The runner must not report the test as passing after
sending a signal to the test process or any children thereof.

The whole test target (not individual methods or tests) is given a limited
amount of time to run to completion. The time limit for a test is based on its
[`timeout`](/reference/be/common-definitions#test.timeout) attribute according
to the following table:

<table>
  <tr>
    <th>timeout</th>
    <th>Time Limit (sec.)</th>
  </tr>
  <tr>
    <td>short</td>
    <td>60</td>
  </tr>
  <tr>
    <td>moderate</td>
    <td>300</td>
  </tr>
  <tr>
    <td>long</td>
    <td>900</td>
  </tr>
  <tr>
    <td>eternal</td>
    <td>3600</td>
  </tr>
</table>

Tests which do not explicitly specify a timeout have one implied based on the
test's [`size`](/reference/be/common-definitions#test.size) as follows:

<table>
  <tr>
    <th>size</th>
    <th>Implied timeout label</th>
  </tr>
  <tr>
    <td>small</td>
    <td>short</td>
  </tr>
  <tr>
    <td>medium</td>
    <td>moderate</td>
  </tr>
  <tr>
    <td>large</td>
    <td>long</td>
  </tr>
  <tr>
    <td>enormous</td>
    <td>eternal</td>
  </tr>
</table>

A "large" test with no explicit timeout setting will be allotted 900
seconds to run. A "medium" test with a timeout of "short" will be allotted 60
seconds.

Unlike `timeout`, the `size` additionally determines the assumed peak usage of
other resources (like RAM) when running the test locally, as described in
[Common definitions](/reference/be/common-definitions#common-attributes-tests).

All combinations of `size` and `timeout` labels are legal, so an "enormous" test
may be declared to have a timeout of "short". Presumably it would do some really
horrible things very quickly.

Tests may return arbitrarily fast regardless of timeout. A test is not penalized
for an overgenerous timeout, although a warning may be issued: you should
generally set your timeout as tight as you can without incurring any flakiness.

The test timeout can be overridden with the `--test_timeout` bazel flag when
manually running under conditions that are known to be slow. The
`--test_timeout` values are in seconds. For example, `--test_timeout=120`
sets the test timeout to two minutes.

There is also a recommended lower bound for test timeouts as follows:

<table>
  <tr>
    <th>timeout</th>
    <th>Time minimum (sec.)</th>
  </tr>
  <tr>
    <td>short</td>
    <td>0</td>
  </tr>
  <tr>
    <td>moderate</td>
    <td>30</td>
  </tr>
  <tr>
    <td>long</td>
    <td>300</td>
  </tr>
  <tr>
    <td>eternal</td>
    <td>900</td>
  </tr>
</table>

For example, if a "moderate" test completes in 5.5s, consider setting `timeout =
"short"` or `size = "small"`. Using the bazel `--test_verbose_timeout_warnings`
command line option will show the tests whose specified size is too big.

Test sizes and timeouts are specified in the BUILD file according to the
specification [here](/reference/be/common-definitions#common-attributes-tests). If
unspecified, a test's size will default to "medium".

If the main process of a test exits, but some of its children are still running,
the test runner should consider the run complete and count it as a success or
failure based on the exit code observed from the main process. The test runner
may kill any stray processes. Tests should not leak processes in this fashion.

## Test sharding

Tests can be parallelized via test sharding. See
[`--test_sharding_strategy`](/reference/command-line-reference#flag--test_sharding_strategy)
and [`shard_count`](/reference/be/common-definitions#common-attributes-tests) to
enable test sharding. When sharding is enabled, the test runner is launched once
per shard. The environment variable [`TEST_TOTAL_SHARDS`](#initial-conditions)
is the number of shards, and [`TEST_SHARD_INDEX`](#initial-conditions) is the
shard index, beginning at 0. Runners use this information to select which tests
to run - for example, using a round-robin strategy. Not all test runners support
sharding. If a runner supports sharding, it must create or update the last
modified date of the file specified by
[`TEST_SHARD_STATUS_FILE`](#initial-conditions). Otherwise, if
[`--incompatible_check_sharding_support`](/reference/command-line-reference#flag--incompatible_check_sharding_support)
is enabled, Bazel will fail the test if it is sharded.

## Initial conditions

When executing a test, the test runner must establish certain initial
conditions.

The test runner must invoke each test with the path to the test executable in
`argv[0]`. This path must be relative and beneath the test's current directory
(which is in the runfiles tree, see below). The test runner should not pass any
other arguments to a test unless the user explicitly requests it.

The initial environment block shall be composed as follows:

<table>
  <tr>
    <th>Variable</th>
    <th>Value</th>
    <th>Status</th>
  </tr>
  <tr>
    <td><code>HOME</code></td>
    <td>value of <code>$TEST_TMPDIR</code></td>
    <td>recommended</td>
  </tr>
  <tr>
    <td><code>LANG</code></td>
    <td><em>unset</em></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>LANGUAGE</code></td>
    <td><em>unset</em></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>LC_ALL</code></td>
    <td><em>unset</em></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>LC_COLLATE</code></td>
    <td><em>unset</em></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>LC_CTYPE</code></td>
    <td><em>unset</em></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>LC_MESSAGES</code></td>
    <td><em>unset</em></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>LC_MONETARY</code></td>
    <td><em>unset</em></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>LC_NUMERIC</code></td>
    <td><em>unset</em></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>LC_TIME</code></td>
    <td><em>unset</em></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>LD_LIBRARY_PATH</code></td>
    <td>colon-separated list of directories containing shared libraries</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>JAVA_RUNFILES</code></td>
    <td>value of <code>$TEST_SRCDIR</code></td>
    <td>deprecated</td>
  </tr>
  <tr>
    <td><code>LOGNAME</code></td>
    <td>value of <code>$USER</code></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>PATH</code></td>
    <td><code>/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin:.</code></td>
    <td>recommended</td>
  </tr>
  <tr>
    <td><code>PWD</code></td>
    <td><code>$TEST_SRCDIR/<var>workspace-name</var></code></td>
    <td>recommended</td>
  </tr>
  <tr>
    <td><code>SHLVL</code></td>
    <td><code>2</code></td>
    <td>recommended</td>
  </tr>
  <tr>
    <td><code>TEST_INFRASTRUCTURE_FAILURE_FILE</code></td>
    <td>absolute path to a private file in a writable directory (This file
      should only be used to report failures originating from the testing
      infrastructure, not as a general mechanism for reporting flaky failures
      of tests. In this context, testing infrastructure is defined as systems
      or libraries that are not test-specific, but can cause test failures by
      malfunctioning. The first line is the name of the testing infrastructure
      component that caused the failure, the second one a human-readable
      description of the failure. Additional lines are ignored.)</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_LOGSPLITTER_OUTPUT_FILE</code></td>
    <td>absolute path to a private file in a writable directory (used to write
      Logsplitter protobuffer log)</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_PREMATURE_EXIT_FILE</code></td>
    <td>absolute path to a private file in a writable directory (used for
      catching calls to <code>exit()</code>)</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_RANDOM_SEED</code></td>
    <td>If the <code>--runs_per_test</code> option is used,
      <code>TEST_RANDOM_SEED</code> is set to the <var>run number</var>
      (starting with 1) for each individual test run.</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_RUN_NUMBER</code></td>
    <td>If the <code>--runs_per_test</code> option is used,
      <code>TEST_RUN_NUMBER</code> is set to the <var>run number</var>
      (starting with 1) for each individual test run.</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_TARGET</code></td>
    <td>The name of the target being tested</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_SIZE</code></td>
    <td>The test <a href="#size"><code>size</code></a></td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_TIMEOUT</code></td>
    <td>The test <a href="#timeout"><code>timeout</code></a> in seconds</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_SHARD_INDEX</code></td>
    <td>shard index, if <a href="#test-sharding"><code>sharding</code></a> is used</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_SHARD_STATUS_FILE</code></td>
    <td>path to file to touch to indicate support for <a href="#test-sharding"><code>sharding</code></a></td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_SRCDIR</code></td>
    <td>absolute path to the base of the runfiles tree</td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>TEST_TOTAL_SHARDS</code></td>
    <td>total
      <a href="/reference/be/common-definitions#test.shard_count"><code>shard count</code></a>,
      if <a href="#test-sharding"><code>sharding</code></a> is used</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_TMPDIR</code></td>
    <td>absolute path to a private writable directory</td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>TEST_WORKSPACE</code></td>
    <td>the local repository's workspace name</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_UNDECLARED_OUTPUTS_DIR</code></td>
    <td>absolute path to a private writable directory (used to write undeclared
      test outputs). Any files written to the
      <code>TEST_UNDECLARED_OUTPUTS_DIR</code> directory will be zipped up and
      added to an <code>outputs.zip</code> file under
      <code>bazel-testlogs</code>.</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TEST_UNDECLARED_OUTPUTS_ANNOTATIONS_DIR</code></td>
    <td>absolute path to a private writable directory (used to write undeclared
      test output annotation <code>.part</code> and <code>.pb</code> files).</td>
    <td>optional</td>
  </tr>

  <tr>
    <td><code>TEST_WARNINGS_OUTPUT_FILE</code></td>
    <td>absolute path to a private file in a writable directory (used to write
      test target warnings)</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TESTBRIDGE_TEST_ONLY</code></td>
    <td>value of
      <a href="/docs/user-manual#flag--test_filter"><code>--test_filter</code></a>,
      if specified</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>TZ</code></td>
    <td><code>UTC</code></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>USER</code></td>
    <td>value of <code>getpwuid(getuid())-&gt;pw_name</code></td>
    <td>required</td>
  </tr>
  <tr>
    <td><code>XML_OUTPUT_FILE</code></td>
    <td>
      Location to which test actions should write a test result XML output file.
      Otherwise, Bazel generates a default XML output file wrapping the test log
      as part of the test action. The XML schema is based on the
      <a href="https://windyroad.com.au/dl/Open%20Source/JUnit.xsd"
        class="external">JUnit test result schema</a>.</td>
    <td>optional</td>
  </tr>
  <tr>
    <td><code>BAZEL_TEST</code></td>
    <td>Signifies test executable is being driven by <code>bazel test</code></td>
    <td>required</td>
  </tr>
</table>

The environment may contain additional entries. Tests should not depend on the
presence, absence, or value of any environment variable not listed above.

The initial working directory shall be `$TEST_SRCDIR/$TEST_WORKSPACE`.

The current process id, process group id, session id, and parent process id are
unspecified. The process may or may not be a process group leader or a session
leader. The process may or may not have a controlling terminal. The process may
have zero or more running or unreaped child processes. The process should not
have multiple threads when the test code gains control.

File descriptor 0 (`stdin`) shall be open for reading, but what it is attached to
is unspecified. Tests must not read from it. File descriptors 1 (`stdout`) and 2
(`stderr`) shall be open for writing, but what they are attached to is
unspecified. It could be a terminal, a pipe, a regular file, or anything else to
which characters can be written. They may share an entry in the open file table
(meaning that they cannot seek independently). Tests should not inherit any
other open file descriptors.

The initial umask shall be `022` or `027`.

No alarm or interval timer shall be pending.

The initial mask of blocked signals shall be empty. All signals shall be set to
their default action.

The initial resource limits, both soft and hard, should be set as follows:

<table>
  <tr>
    <th>Resource</th>
    <th>Limit</th>
  </tr>
  <tr>
    <td><code>RLIMIT_AS</code></td>
    <td>unlimited</td>
  </tr>
  <tr>
    <td><code>RLIMIT_CORE</code></td>
    <td>unspecified</td>
  </tr>
  <tr>
    <td><code>RLIMIT_CPU</code></td>
    <td>unlimited</td>
  </tr>
  <tr>
    <td><code>RLIMIT_DATA</code></td>
    <td>unlimited</td>
  </tr>
  <tr>
    <td><code>RLIMIT_FSIZE</code></td>
    <td>unlimited</td>
  </tr>
  <tr>
    <td><code>RLIMIT_LOCKS</code></td>
    <td>unlimited</td>
  </tr>
  <tr>
    <td><code>RLIMIT_MEMLOCK</code></td>
    <td>unlimited</td>
  </tr>
  <tr>
    <td><code>RLIMIT_MSGQUEUE</code></td>
    <td>unspecified</td>
  </tr>
  <tr>
    <td><code>RLIMIT_NICE</code></td>
    <td>unspecified</td>
  </tr>
  <tr>
    <td><code>RLIMIT_NOFILE</code></td>
    <td>at least 1024</td>
  </tr>
  <tr>
    <td><code>RLIMIT_NPROC</code></td>
    <td>unspecified</td>
  </tr>
  <tr>
    <td><code>RLIMIT_RSS</code></td>
    <td>unlimited</td>
  </tr>
  <tr>
    <td><code>RLIMIT_RTPRIO</code></td>
    <td>unspecified</td>
  </tr>
  <tr>
    <td><code>RLIMIT_SIGPENDING</code></td>
    <td>unspecified</td>
  </tr>
  <tr>
    <td><code>RLIMIT_STACK</code></td>
    <td>unlimited, or 2044KB &lt;= rlim &lt;= 8192KB</td>
  </tr>
</table>

The initial process times (as returned by `times()`) and resource utilization
(as returned by `getrusage()`) are unspecified.

The initial scheduling policy and priority are unspecified.

## Role of the host system

In addition to the aspects of user context under direct control of the test
runner, the operating system on which tests execute must satisfy certain
properties for a test run to be valid.

#### Filesystem

The root directory observed by a test may or may not be the real root directory.

`/proc` shall be mounted.

All build tools shall be present at the absolute paths under `/usr` used by a
local installation.

Paths starting with `/home` may not be available. Tests should not access any
such paths.

`/tmp` shall be writable, but tests should avoid using these paths.

Tests must not assume that any constant path is available for their exclusive
use.

Tests must not assume that atimes are enabled for any mounted filesystem.

#### Users and groups

The users root, nobody, and unittest must exist. The groups root, nobody, and
eng must exist.

Tests must be executed as a non-root user. The real and effective user ids must
be equal; likewise for group ids. Beyond this, the current user id, group id,
user name, and group name are unspecified. The set of supplementary group ids is
unspecified.

The current user id and group id must have corresponding names which can be
retrieved with `getpwuid()` and `getgrgid()`. The same may not be true for
supplementary group ids.

The current user must have a home directory. It may not be writable. Tests must
not attempt to write to it.

#### Networking

The hostname is unspecified. It may or may not contain a dot. Resolving the
hostname must give an IP address of the current host. Resolving the hostname cut
after the first dot must also work. The hostname localhost must resolve.

#### Other resources

Tests are granted at least one CPU core. Others may be available but this is not
guaranteed. Other performance aspects of this core are not specified. You can
increase the reservation to a higher number of CPU cores by adding the tag
"cpu:n" (where n is a positive number) to a test rule. If a machine has less
total CPU cores than requested, Bazel will still run the test. If a test uses
[sharding](#test-sharding), each individual shard will reserve the number of CPU
cores specified here.

Tests may create subprocesses, but not process groups or sessions.

There is a limit on the number of input files a test may consume. This limit is
subject to change, but is currently in the range of tens of thousands of inputs.

#### Time and date

The current time and date are unspecified. The system timezone is unspecified.

X Windows may or may not be available. Tests that need an X server should start
Xvfb.

## Test interaction with the filesystem

All file paths specified in test environment variables point to somewhere on the
local filesystem, unless otherwise specified.

Tests should create files only within the directories specified by
`$TEST_TMPDIR` and `$TEST_UNDECLARED_OUTPUTS_DIR` (if set).

These directories will be initially empty.

Tests must not attempt to remove, chmod, or otherwise alter these directories.

These directories may be a symbolic links.

The filesystem type of `$TEST_TMPDIR/.` remains unspecified.

Tests may also write .part files to the
`$TEST_UNDECLARED_OUTPUTS_ANNOTATIONS_DIR` to annotate undeclared output files.

In rare cases, a test may be forced to create files in `/tmp`. For example,
[path length limits for Unix domain sockets](https://serverfault.com/questions/641347){: .external}
typically require creating the socket under `/tmp`. Bazel will be unable to
track such files; the test itself must take care to be hermetic, to use unique
paths to avoid colliding with other, simultaneously running tests and non-test
processes, and to clean up the files it creates in `/tmp`.

Some popular testing frameworks, such as
[JUnit4 `TemporaryFolder`](https://junit.org/junit4/javadoc/latest/org/junit/rules/TemporaryFolder.html){: .external}
or [Go `TempDir`](https://golang.org/pkg/testing/#T.TempDir){: .external}, have
their own ways to create a temporary directory under `/tmp`. These testing
frameworks include functionality that cleans up files in `/tmp`, so you may use
them even though they create files outside of `TEST_TMPDIR`.

Tests must access inputs through the **runfiles** mechanism, or other parts of
the execution environment which are specifically intended to make input files
available.

Tests must not access other outputs of the build system at paths inferred from
the location of their own executable.

It is unspecified whether the runfiles tree contains regular files, symbolic
links, or a mixture. The runfiles tree may contain symlinks to directories.
Tests should avoid using paths containing `..` components within the runfiles
tree.

No directory, file, or symlink within the runfiles tree (including paths which
traverse symlinks) should be writable. (It follows that the initial working
directory should not be writable.) Tests must not assume that any part of the
runfiles is writable, or owned by the current user (for example, `chmod` and `chgrp` may
fail).

The runfiles tree (including paths which traverse symlinks) must not change
during test execution. Parent directories and filesystem mounts must not change
in any way which affects the result of resolving a path within the runfiles
tree.

In order to catch early exit, a test may create a file at the path specified by
`TEST_PREMATURE_EXIT_FILE` upon start and remove it upon exit. If Bazel sees the
file when the test finishes, it will assume that the test exited prematurely and
mark it as having failed.

## Execution platform

The [execution platform](/extending/platforms) for a test action is determined
via [toolchain resolution](/extending/toolchains#toolchain-resolution), just
like for any other action. Each test rule has an implicitly defined [
`test` exec group](/extending/exec-groups#exec-groups-for-native-rules) that,
unless overridden, has a mandatory toolchain requirement on
`@bazel_tools//tools/test:default_test_toolchain_type`. Toolchains of this type
do not carry any data in the form of providers, but can be used to influence the
execution platform of the test action. By default, Bazel registers two such
toolchains:

* If `--@bazel_tools//tools/test:incompatible_use_default_test_toolchain` is
  disabled (the current default), the active test toolchain is
  `@bazel_tools//tools/test:legacy_test_toolchain`. This toolchain does not
  impose any constraints and thus test actions without manually specified exec
  constraints are configured for the first registered execution platform. This
  is often not the intended behavior in multi-platform builds as it can result
  in e.g. a test binary built for Linux on a Windows machine to be executed on
  Windows.
* If `--@bazel_tools//tools/test:incompatible_use_default_test_toolchain` is
  enabled, the active test toolchain is
  `@bazel_tools//tools/test:default_test_toolchain`. This toolchain requires an
  execution platform to match all the constraints of the test rule's target
  platform. In particular, the target platform is compatible with this toolchain
  if it is also registered as an execution platform. If no such platform is
  found, the test rule fails with a toolchain resolution error.

Users can register additional toolchains for this type to influence this
behavior and their toolchains will take precedence over the default ones.
Test rule authors can define their own test toolchain type and also register
a default toolchain for it.

## Tag conventions

Some tags in the test rules have a special meaning. See also the
[Bazel Build Encyclopedia on the `tags` attribute](/reference/be/common-definitions#common.tags).

<table>
  <tr>
    <th>Tag</th>
    <th>Meaning</th>
  </tr>
  <tr>
    <th><code>exclusive</code></th>
      <td>run no other test at the same time</td>
    </tr>
    <tr>
      <td><code>external</code></td>
      <td>test has an external dependency; disable test caching</td>
    </tr>
    <tr>
      <td><code>large</code></td>
      <td><code>test_suite</code> convention; suite of large tests</td>
    </tr>
    <tr>
      <td><code>manual *</code></td>
      <td>don't include test target in wildcard target patterns like
        <code>:...</code>, <code>:*</code>, or <code>:all</code></td>
    </tr>
    <tr>
      <td><code>medium</code></td>
      <td><code>test_suite</code> convention; suite of medium tests</td>
    </tr>
    <tr>
      <td><code>small</code></td>
      <td><code>test_suite</code> convention; suite of small tests</td>
    </tr>
    <tr>
      <td><code>smoke</code></td>
      <td><code>test_suite</code> convention; means it should be run before
        committing code changes into the version control system</td>
    </tr>
</table>

Note: bazel `query` does not respect the manual tag.

## Runfiles

In the following, assume there is a *_binary() rule labeled
`//foo/bar:unittest`, with a run-time dependency on the rule labeled
`//deps/server:server`.

#### Location

The runfiles directory for a target `//foo/bar:unittest` is the directory
`$(WORKSPACE)/$(BINDIR)/foo/bar/unittest.runfiles`. This path is referred to as
the `runfiles_dir`.

#### Dependencies

The runfiles directory is declared as a compile-time dependency of the
`*_binary()` rule. The runfiles directory itself depends on the set of BUILD
files that affect the `*_binary()` rule or any of its compile-time or run-time
dependencies. Modifying source files does not affect the structure of the
runfiles directory, and thus does not trigger any rebuilding.

#### Contents

The runfiles directory contains the following:

*   **Symlinks to run-time dependencies**: each OutputFile and CommandRule that
    is a run-time dependency of the `*_binary()` rule is represented by one
    symlink in the runfiles directory. The name of the symlink is
    `$(WORKSPACE)/package_name/rule_name`. For example, the symlink for server
    would be named `$(WORKSPACE)/deps/server/server`, and the full path would be
    `$(WORKSPACE)/foo/bar/unittest.runfiles/$(WORKSPACE)/deps/server/server`.
    The destination of the symlink is the OutputFileName() of the OutputFile or
    CommandRule, expressed as an absolute path. Thus, the destination of the
    symlink might be `$(WORKSPACE)/linux-dbg/deps/server/42/server`.
