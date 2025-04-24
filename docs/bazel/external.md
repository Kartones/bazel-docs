


# Repository Rules

This page covers how to define repository rules and provides examples for more
details.

An [external repository](/external/overview#repository) is a directory tree,
containing source files usable in a Bazel build, which is generated on demand by
running its corresponding **repo rule**. Repos can be defined in a multitude of
ways, but ultimately, each repo is defined by invoking a repo rule, just as
build targets are defined by invoking build rules. They can be used to depend on
third-party libraries (such as Maven packaged libraries) but also to generate
`BUILD` files specific to the host Bazel is running on.

## Repository rule definition

In a `.bzl` file, use the
[repository_rule](/rules/lib/globals/bzl#repository_rule) function to define a
new repo rule and store it in a global variable. After a repo rule is defined,
it can be invoked as a function to define repos. This invocation is usually
performed from inside a [module extension](/external/extension) implementation
function.

The two major components of a repo rule definition are its attribute schema and
implementation function. The attribute schema determines the names and types of
attributes passed to a repo rule invocation, and the implementation function is
run when the repo needs to be fetched.

## Attributes

Attributes are arguments passed to the repo rule invocation. The schema of
attributes accepted by a repo rule is specified using the `attrs` argument when
the repo rule is defined with a call to `repository_rule`. An example defining
`url` and `sha256` attributes as strings:

```python
http_archive = repository_rule(
    implementation=_impl,
    attrs={
        "url": attr.string(mandatory=True),
        "sha256": attr.string(mandatory=True),
    }
)
```

To access an attribute within the implementation function, use
`repository_ctx.attr.<attribute_name>`:

```python
def _impl(repository_ctx):
    url = repository_ctx.attr.url
    checksum = repository_ctx.attr.sha256
```

All `repository_rule`s have the implicitly defined attribute `name`. This is a
string attribute that behaves somewhat magically: when specified as an input to
a repo rule invocation, it takes an apparent repo name; but when read from the
repo rule's implementation function using `repository_ctx.attr.name`, it returns
the canonical repo name.

## Implementation function

Every repo rule requires an `implementation` function. It contains the actual
logic of the rule and is executed strictly in the Loading Phase.

The function has exactly one input parameter, `repository_ctx`. The function
returns either `None` to signify that the rule is reproducible given the
specified parameters, or a dict with a set of parameters for that rule that
would turn that rule into a reproducible one generating the same repo. For
example, for a rule tracking a git repository that would mean returning a
specific commit identifier instead of a floating branch that was originally
specified.

The input parameter `repository_ctx` can be used to access attribute values, and
non-hermetic functions (finding a binary, executing a binary, creating a file in
the repository or downloading a file from the Internet). See [the API
docs](/rules/lib/builtins/repository_ctx) for more context. Example:

```python
def _impl(repository_ctx):
  repository_ctx.symlink(repository_ctx.attr.path, "")

local_repository = repository_rule(
    implementation=_impl,
    ...)
```

## When is the implementation function executed?

The implementation function of a repo rule is executed when Bazel needs a target
from that repository, for example when another target (in another repo) depends
on it or if it is mentioned on the command line. The implementation function is
then expected to create the repo in the file system. This is called "fetching"
the repo.

In contrast to regular targets, repos are not necessarily re-fetched when
something changes that would cause the repo to be different. This is because
there are things that Bazel either cannot detect changes to or it would cause
too much overhead on every build (for example, things that are fetched from the
network). Therefore, repos are re-fetched only if one of the following things
changes:

*   The attributes passed to the repo rule invocation.
*   The Starlark code comprising the implementation of the repo rule.
*   The value of any environment variable passed to `repository_ctx`'s
    `getenv()` method or declared with the `environ` attribute of the
    [`repository_rule`](/rules/lib/globals/bzl#repository_rule). The values of
    these environment variables can be hard-wired on the command line with the
    [`--repo_env`](/reference/command-line-reference#flag--repo_env) flag.
*   The existence, contents, and type of any paths being
    [`watch`ed](/rules/lib/builtins/repository_ctx#watch) in the implementation
    function of the repo rule.
    *   Certain other methods of `repository_ctx` with a `watch` parameter, such
        as `read()`, `execute()`, and `extract()`, can also cause paths to be
        watched.
    *   Similarly, [`repository_ctx.watch_tree`](/rules/lib/builtins/repository_ctx#watch_tree)
        and [`path.readdir`](/rules/lib/builtins/path#readdir) can cause paths
        to be watched in other ways.
*   When `bazel fetch --force` is executed.

There are two parameters of `repository_rule` that control when the repositories
are re-fetched:

*   If the `configure` flag is set, the repository is re-fetched on `bazel
    fetch --force --configure` (non-`configure` repositories are not
    re-fetched).
*   If the `local` flag is set, in addition to the above cases, the repo is also
    re-fetched when the Bazel server restarts.

## Forcing refetch of external repos

Sometimes, an external repo can become outdated without any change to its
definition or dependencies. For example, a repo fetching sources might follow a
particular branch of a third-party repository, and new commits are available on
that branch. In this case, you can ask bazel to refetch all external repos
unconditionally by calling `bazel fetch --force --all`.

Moreover, some repo rules inspect the local machine and might become outdated if
the local machine was upgraded. Here you can ask Bazel to only refetch those
external repos where the [`repository_rule`](/rules/lib/globals#repository_rule)
definition has the `configure` attribute set, use `bazel fetch --force
--configure`.

## Examples

-   [C++ auto-configured
    toolchain](https://cs.opensource.google/bazel/bazel/+/master:tools/cpp/cc_configure.bzl;drc=644b7d41748e09eff9e47cbab2be2263bb71f29a;l=176):
    it uses a repo rule to automatically create the C++ configuration files for
    Bazel by looking for the local C++ compiler, the environment and the flags
    the C++ compiler supports.

-   [Go repositories](https://github.com/bazelbuild/rules_go/blob/67bc217b6210a0922d76d252472b87e9a6118fdf/go/private/go_repositories.bzl#L195)
    uses several `repository_rule` to defines the list of dependencies needed to
    use the Go rules.

-   [rules_jvm_external](https://github.com/bazelbuild/rules_jvm_external)
    creates an external repository called `@maven` by default that generates
    build targets for every Maven artifact in the transitive dependency tree.


# Module extensions

Module extensions allow users to extend the module system by reading input data
from modules across the dependency graph, performing necessary logic to resolve
dependencies, and finally creating repos by calling [repo
rules](/external/repo). These extensions have capabilities similar to repo
rules, which enables them to perform file I/O, send network requests, and so on.
Among other things, they allow Bazel to interact with other package management
systems while also respecting the dependency graph built out of Bazel modules.

You can define module extensions in `.bzl` files, just like repo rules. They're
not invoked directly; rather, each module specifies pieces of data called *tags*
for extensions to read. Bazel runs module resolution before evaluating any
extensions. The extension reads all the tags belonging to it across the entire
dependency graph.

## Extension usage

Extensions are hosted in Bazel modules themselves. To use an extension in a
module, first add a `bazel_dep` on the module hosting the extension, and then
call the [`use_extension`](/rules/lib/globals/module#use_extension) built-in function
to bring it into scope. Consider the following example — a snippet from a
`MODULE.bazel` file to use the "maven" extension defined in the
[`rules_jvm_external`](https://github.com/bazelbuild/rules_jvm_external){:.external}
module:

```python
bazel_dep(name = "rules_jvm_external", version = "4.5")
maven = use_extension("@rules_jvm_external//:extensions.bzl", "maven")
```

This binds the return value of `use_extension` to a variable, which allows the
user to use dot-syntax to specify tags for the extension. The tags must follow
the schema defined by the corresponding *tag classes* specified in the
[extension definition](#extension_definition). For an example specifying some
`maven.install` and `maven.artifact` tags:

```python
maven.install(artifacts = ["org.junit:junit:4.13.2"])
maven.artifact(group = "com.google.guava",
               artifact = "guava",
               version = "27.0-jre",
               exclusions = ["com.google.j2objc:j2objc-annotations"])
```

Use the [`use_repo`](/rules/lib/globals/module#use_repo) directive to bring repos
generated by the extension into the scope of the current module.

```python
use_repo(maven, "maven")
```

Repos generated by an extension are part of its API. In this example, the
"maven" module extension promises to generate a repo called `maven`. With the
declaration above, the extension properly resolves labels such as
`@maven//:org_junit_junit` to point to the repo generated by the "maven"
extension.

Note: Module extensions are evaluated lazily. This means that an extension will
typically not be evaluated unless some module brings one of its repositories
into scope using `use_repo` and that repository is referenced in a build. While
testing a module extension, `bazel mod deps` can be useful as it
unconditionally evaluates all module extensions.

## Extension definition

You can define module extensions similarly to [repo rules](/external/repo),
using the [`module_extension`](/rules/lib/globals/bzl#module_extension)
function. However, while repo rules have a number of attributes, module
extensions have [`tag_class`es](/rules/lib/globals/bzl#tag_class), each of which
has a number of attributes. The tag classes define schemas for tags used by this
extension. For example, the "maven" extension above might be defined like this:

```python
# @rules_jvm_external//:extensions.bzl

_install = tag_class(attrs = {"artifacts": attr.string_list(), ...})
_artifact = tag_class(attrs = {"group": attr.string(), "artifact": attr.string(), ...})
maven = module_extension(
  implementation = _maven_impl,
  tag_classes = {"install": _install, "artifact": _artifact},
)
```

These declarations show that `maven.install` and `maven.artifact` tags can be
specified using the specified attribute schema.

The implementation function of module extensions are similar to those of repo
rules, except that they get a [`module_ctx`](/rules/lib/builtins/module_ctx) object,
which grants access to all modules using the extension and all pertinent tags.
The implementation function then calls repo rules to generate repos.

```python
# @rules_jvm_external//:extensions.bzl

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_file")  # a repo rule
def _maven_impl(ctx):
  # This is a fake implementation for demonstration purposes only

  # collect artifacts from across the dependency graph
  artifacts = []
  for mod in ctx.modules:
    for install in mod.tags.install:
      artifacts += install.artifacts
    artifacts += [_to_artifact(artifact) for artifact in mod.tags.artifact]

  # call out to the coursier CLI tool to resolve dependencies
  output = ctx.execute(["coursier", "resolve", artifacts])
  repo_attrs = _process_coursier_output(output)

  # call repo rules to generate repos
  for attrs in repo_attrs:
    http_file(**attrs)
  _generate_hub_repo(name = "maven", repo_attrs)
```

### Extension identity

Module extensions are identified by the name and the `.bzl` file that appears
in the call to `use_extension`. In the following example, the extension `maven`
is identified by the `.bzl` file `@rules_jvm_external//:extension.bzl` and the
name `maven`:

```python
maven = use_extension("@rules_jvm_external//:extensions.bzl", "maven")
```

Re-exporting an extension from a different `.bzl` file gives it a new identity
and if both versions of the extension are used in the transitive module graph,
then they will be evaluated separately and will only see the tags associated
with that particular identity.

As an extension author you should make sure that users will only use your
module extension from one single `.bzl` file.

## Repository names and visibility

Repos generated by extensions have canonical names in the form of `{{ "<var>"
}}module_repo_canonical_name{{ "</var>" }}+{{ "<var>" }}extension_name{{
"</var>" }}+{{ "<var>" }}repo_name{{ "</var>" }}`. Note that the canonical name
format is not an API you should depend on — it's subject to change at any time.

This naming policy means that each extension has its own "repo namespace"; two
distinct extensions can each define a repo with the same name without risking
any clashes. It also means that `repository_ctx.name` reports the canonical name
of the repo, which is *not* the same as the name specified in the repo rule
call.

Taking repos generated by module extensions into consideration, there are
several repo visibility rules:

*   A Bazel module repo can see all repos introduced in its `MODULE.bazel` file
    via [`bazel_dep`](/rules/lib/globals/module#bazel_dep) and
    [`use_repo`](/rules/lib/globals/module#use_repo).
*   A repo generated by a module extension can see all repos visible to the
    module that hosts the extension, *plus* all other repos generated by the
    same module extension (using the names specified in the repo rule calls as
    their apparent names).
    *   This might result in a conflict. If the module repo can see a repo with
        the apparent name `foo`, and the extension generates a repo with the
        specified name `foo`, then for all repos generated by that extension
        `foo` refers to the former.
*   Similarly, in a module extension's implementation function, repos created
    by the extension can refer to each other by their apparent names in
    attributes, regardless of the order in which they are created.
    *   In case of a conflict with a repository visible to the module, labels
        passed to repository rule attributes can be wrapped in a call to
        [`Label`](/rules/lib/toplevel/attr#label) to ensure that they refer to
        the repo visible to the module instead of the extension-generated repo
        of the same name.

### Overriding and injecting module extension repos

The root module can use
[`override_repo`](/rules/lib/globals/module#override_repo) and
[`inject_repo`](/rules/lib/globals/module#inject_repo) to override or inject
module extension repos.

#### Example: Replacing `rules_java`'s `java_tools` with a vendored copy

```python
# MODULE.bazel
local_repository = use_repo_rule("@bazel_tools//tools/build_defs/repo:local.bzl", "local_repository")
local_repository(
  name = "my_java_tools",
  path = "vendor/java_tools",
)

bazel_dep(name = "rules_java", version = "7.11.1")
java_toolchains = use_extension("@rules_java//java:extension.bzl", "toolchains")

override_repo(java_toolchains, remote_java_tools = "my_java_tools")
```

#### Example: Patch a Go dependency to depend on `@zlib` instead of the system zlib

```python
# MODULE.bazel
bazel_dep(name = "gazelle", version = "0.38.0")
bazel_dep(name = "zlib", version = "1.3.1.bcr.3")

go_deps = use_extension("@gazelle//:extensions.bzl", "go_deps")
go_deps.from_file(go_mod = "//:go.mod")
go_deps.module_override(
  patches = [
    "//patches:my_module_zlib.patch",
  ],
  path = "example.com/my_module",
)
use_repo(go_deps, ...)

inject_repo(go_deps, "zlib")
```

```diff
# patches/my_module_zlib.patch
--- a/BUILD.bazel
+++ b/BUILD.bazel
@@ -1,6 +1,6 @@
 go_binary(
     name = "my_module",
     importpath = "example.com/my_module",
     srcs = ["my_module.go"],
-    copts = ["-lz"],
+    cdeps = ["@zlib"],
 )
```

## Best practices

This section describes best practices when writing extensions so they are
straightforward to use, maintainable, and adapt well to changes over time.

### Put each extension in a separate file

When extensions are in a different files, it allows one extension to load
repositories generated by another extension. Even if you don't use this
functionality, it's best to put them in separate files in case you need it
later. This is because the extension's identify is based on its file, so moving
the extension into another file later changes your public API and is a backwards
incompatible change for your users.

### Specify reproducibility

If your extension always defines the same repositories given the same inputs
(extension tags, files it reads, etc.) and in particular doesn't rely on
any [downloads](/rules/lib/builtins/module_ctx#download) that aren't guarded by
a checksum, consider returning
[`extension_metadata`](/rules/lib/builtins/module_ctx#extension_metadata) with
`reproducible = True`. This allows Bazel to skip this extension when writing to
the lockfile.

### Specify the operating system and architecture

If your extension relies on the operating system or its architecture type,
ensure to indicate this in the extension definition using the `os_dependent`
and `arch_dependent` boolean attributes. This ensures that Bazel recognizes the
need for re-evaluation if there are changes to either of them.

Since this kind of dependence on the host makes it more difficult to maintain
the lockfile entry for this extension, consider
[marking the extension reproducible](#specify_reproducibility) if possible.

### Only the root module should directly affect repository names

Remember that when an extension creates repositories, they are created within
the namespace of the extension. This means collisions can occur if different
modules use the same extension and end up creating a repository with the same
name. This often manifests as a module extension's `tag_class` having a `name`
argument that is passed as a repository rule's `name` value.

For example, say the root module, `A`, depends on module `B`. Both modules
depend on module `mylang`. If both `A` and `B` call
`mylang.toolchain(name="foo")`, they will both try to create a repository named
`foo` within the `mylang` module and an error will occur.

To avoid this, either remove the ability to set the repository name directly,
or only allow the root module to do so. It's OK to allow the root module this
ability because nothing will depend on it, so it doesn't have to worry about
another module creating a conflicting name.



# External dependencies overview

Bazel supports *external dependencies*, source files (both text and binary) used
in your build that are not from your workspace. For example, they could be a
ruleset hosted in a GitHub repo, a Maven artifact, or a directory on your local
machine outside your current workspace.

This document gives an overview of the system before examining some of the
concepts in more detail.

## Overview of the system

Bazel's external dependency system works on the basis of [*Bazel
modules*](#module), each of which is a versioned Bazel project, and
[*repositories*](#repository) (or repos), which are directory trees containing
source files.

Bazel starts from the root module -- that is, the project you're working on.
Like all modules, it needs to have a `MODULE.bazel` file at its directory root,
declaring its basic metadata and direct dependencies. The following is a basic
example:

```python
module(name = "my-module", version = "1.0")

bazel_dep(name = "rules_cc", version = "0.1.1")
bazel_dep(name = "platforms", version = "0.0.11")
```

From there, Bazel looks up all transitive dependency modules in a
[*Bazel registry*](registry) — by default, the [Bazel Central
Registry](https://bcr.bazel.build/). The registry provides the
dependencies' `MODULE.bazel` files, which allows Bazel to discover the entire
transitive dependency graph before performing version resolution.

After version resolution, in which one version is selected for each module,
Bazel consults the registry again to learn how to define a repo for each module
-- that is, how the sources for each dependency module should be fetched. Most
of the time, these are just archives downloaded from the internet and extracted.

Modules can also specify customized pieces of data called *tags*, which are
consumed by [*module extensions*](extension) after module resolution
to define additional repos. These extensions can perform actions like file I/O
and sending network requests. Among other things, they allow Bazel to interact
with other package management systems while also respecting the dependency graph
built out of Bazel modules.

The three kinds of repos -- the main repo (which is the source tree you're
working in), the repos representing transitive dependency modules, and the repos
created by module extensions -- form the [*workspace*](#workspace) together.
External repos (non-main repos) are fetched on demand, for example when they're
referred to by labels (like `@repo//pkg:target`) in BUILD files.

## Benefits

Bazel's external dependency system offers a wide range of benefits.

### Automatic Dependency Resolution

-   **Deterministic Version Resolution**: Bazel adopts the deterministic
    [MVS](module#version-selection) version resolution algorithm,
    minimizing conflicts and addressing diamond dependency issues.
-   **Simplified Dependency Management**: `MODULE.bazel` declares only direct
    dependencies, while transitive dependencies are automatically resolved,
    providing a clearer overview of the project's dependencies.
-   **[Strict Dependency visibility](module#repository_names_and_strict_deps)**:
    Only direct dependencies are visible, ensuring correctness and
    predictability.

### Ecosystem Integration

-   **[Bazel Central Registry](https://registry.bazel.build/)**: A centralized
    repository for discovering and managing common dependencies as Bazel
    modules.
-   **Adoption of Non-Bazel Projects**: When a non-Bazel project (usually a C++
    library) is adapted for Bazel and made available in BCR, it streamlines its
    integration for the whole community and eliminates duplicated effort and
    conflicts of custom BUILD files.
-   **Unified Integration with Language-Specific Package Managers**: Rulesets
    streamline integration with external package managers for non-Bazel
    dependencies, including:
    *   [rules_jvm_external](https://github.com/bazel-contrib/rules_jvm_external/blob/master/docs/bzlmod.md)
        for Maven,
    *   [rules_python](https://rules-python.readthedocs.io/en/latest/pypi-dependencies.html#using-bzlmod)
        for PyPi,
    *   [bazel-gazelle](https://github.com/bazel-contrib/rules_go/blob/master/docs/go/core/bzlmod.md#external-dependencies)
        for Go Modules,
    *   [rules_rust](https://bazelbuild.github.io/rules_rust/crate_universe_bzlmod.html)
        for Cargo.

### Advanced Features

-   **[Module Extensions](extension)**: The
    [`use_repo_rule`](/rules/lib/globals/module#use_repo_rule) and module
    extension features allow flexible use of custom repository rules and
    resolution logic to introduce any non-Bazel dependencies.
-   **[`bazel mod` Command](mod-command)**: The sub-command offers
    powerful ways to inspect external dependencies. You know exactly how an
    external dependency is defined and where it comes from.
-   **[Vendor Mode](vendor)**: Pre-fetch the exact external dependencies you
    need to facilitate offline builds.
-   **[Lockfile](lockfile)**: The lockfile improves build reproducibility and
    accelerates dependency resolution.
-   **(Upcoming) [BCR Provenance
    Attestations](https://github.com/bazelbuild/bazel-central-registry/discussions/2721)**:
    Strengthen supply chain security by ensuring verified provenance of
    dependencies.

## Concepts

This section gives more detail on concepts related to external dependencies.

### Module

A Bazel project that can have multiple versions, each of which can have
dependencies on other modules.

In a local Bazel workspace, a module is represented by a repository.

For more details, see [Bazel modules](module).

### Repository

A directory tree with a boundary marker file at its root, containing source
files that can be used in a Bazel build. Often shortened to just **repo**.

A repo boundary marker file can be `MODULE.bazel` (signaling that this repo
represents a Bazel module), `REPO.bazel` (see [below](#repo.bazel)), or in
legacy contexts, `WORKSPACE` or `WORKSPACE.bazel`. Any repo boundary marker file
will signify the boundary of a repo; multiple such files can coexist in a
directory.

### Main repository

The repository in which the current Bazel command is being run.

The root of the main repository is also known as the
<span id="#workspace-root">**workspace root**</span>.

### Workspace

The environment shared by all Bazel commands run in the same main repository. It
encompasses the main repo and the set of all defined external repos.

Note that historically the concepts of "repository" and "workspace" have been
conflated; the term "workspace" has often been used to refer to the main
repository, and sometimes even used as a synonym of "repository".

### Canonical repository name

The canonical name a repository is addressable by. Within the context of a
workspace, each repository has a single canonical name. A target inside a repo
whose canonical name is `canonical_name` can be addressed by the label
`@@canonical_name//package:target` (note the double `@`).

The main repository always has the empty string as the canonical name.

### Apparent repository name

The name a repository is addressable by in the context of a certain other repo.
This can be thought of as a repo's "nickname": The repo with the canonical name
`michael` might have the apparent name `mike` in the context of the repo
`alice`, but might have the apparent name `mickey` in the context of the repo
`bob`. In this case, a target inside `michael` can be addressed by the label
`@mike//package:target` in the context of `alice` (note the single `@`).

Conversely, this can be understood as a **repository mapping**: each repo
maintains a mapping from "apparent repo name" to a "canonical repo name".

### Repository rule

A schema for repository definitions that tells Bazel how to materialize a
repository. For example, it could be "download a zip archive from a certain URL
and extract it", or "fetch a certain Maven artifact and make it available as a
`java_import` target", or simply "symlink a local directory". Every repo is
**defined** by calling a repo rule with an appropriate number of arguments.

See [Repository rules](repo) for more information about how to write
your own repository rules.

The most common repo rules by far are
[`http_archive`](/rules/lib/repo/http#http_archive), which downloads an archive
from a URL and extracts it, and
[`local_repository`](/reference/be/workspace#local_repository), which symlinks a
local directory that is already a Bazel repository.

### Fetch a repository

The action of making a repo available on local disk by running its associated
repo rule. The repos defined in a workspace are not available on local disk
before they are fetched.

Normally, Bazel only fetches a repo when it needs something from the repo,
and the repo hasn't already been fetched. If the repo has already been fetched
before, Bazel only re-fetches it if its definition has changed.

The `fetch` command can be used to initiate a pre-fetch for a repository,
target, or all necessary repositories to perform any build. This capability
enables offline builds using the `--nofetch` option.

The `--fetch` option serves to manage network access. Its default value is true.
However, when set to false (`--nofetch`), the command will utilize any cached
version of the dependency, and if none exists, the command will result in
failure.

See [fetch options](/reference/command-line-reference#fetch-options) for more
information about controlling fetch.

### Directory layout

After being fetched, the repo can be found in the subdirectory `external` in the
[output base](/remote/output-directories), under its canonical name.

You can run the following command to see the contents of the repo with the
canonical name `canonical_name`:

```posix-terminal
ls $(bazel info output_base)/external/{{ '<var>' }} canonical_name {{ '</var>' }}
```

### REPO.bazel file

The [`REPO.bazel`](/rules/lib/globals/repo) file is used to mark the topmost
boundary of the directory tree that constitutes a repo. It doesn't need to
contain anything to serve as a repo boundary file; however, it can also be used
to specify some common attributes for all build targets inside the repo.

The syntax of a `REPO.bazel` file is similar to `BUILD` files, except that no
`load` statements are supported. The `repo()` function takes the same arguments as the [`package()`
function](/reference/be/functions#package) in `BUILD` files; whereas `package()`
specifies common attributes for all build targets inside the package, `repo()`
analogously does so for all build targets inside the repo.

For example, you can specify a common license for all targets in your repo by
having the following `REPO.bazel` file:

```python
repo(
    default_package_metadata = ["//:my_license"],
)
```

## The legacy WORKSPACE system

In older Bazel versions (before 9.0), external dependencies were introduced by
defining repos in the `WORKSPACE` (or `WORKSPACE.bazel`) file. This file has a
similar syntax to `BUILD` files, employing repo rules instead of build rules.

The following snippet is an example to use the `http_archive` repo rule in the
`WORKSPACE` file:

```python
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
http_archive(
    name = "foo",
    urls = ["https://example.com/foo.zip"],
    sha256 = "c9526390a7cd420fdcec2988b4f3626fe9c5b51e2959f685e8f4d170d1a9bd96",
)
```

The snippet defines a repo whose canonical name is `foo`. In the `WORKSPACE`
system, by default, the canonical name of a repo is also its apparent name to
all other repos.

See the [full list](/rules/lib/globals/workspace) of functions available in
`WORKSPACE` files.

### Shortcomings of the `WORKSPACE` system

In the years after the `WORKSPACE` system was introduced, users reported many
pain points, including:

*   Bazel does not evaluate the `WORKSPACE` files of any dependencies, so all
    transitive dependencies must be defined in the `WORKSPACE` file of the main
    repo, in addition to direct dependencies.
*   To work around this, projects have adopted the "deps.bzl" pattern, in which
    they define a macro which in turn defines multiple repos, and ask users to
    call this macro in their `WORKSPACE` files.
    *   This has its own problems: macros cannot `load` other `.bzl` files, so
        these projects have to define their transitive dependencies in this
        "deps" macro, or work around this issue by having the user call multiple
        layered "deps" macros.
    *   Bazel evaluates the `WORKSPACE` file sequentially. Additionally,
        dependencies are specified using `http_archive` with URLs, without any
        version information. This means that there is no reliable way to perform
        version resolution in the case of diamond dependencies (`A` depends on
        `B` and `C`; `B` and `C` both depend on different versions of `D`).

Due to the shortcomings of WORKSPACE, the new module-based system (codenamed
"Bzlmod") gradually replaced the legacy WORKSPACE system between Bazel 6 and 9.
Read the [Bzlmod migration guide](migration) on how to migrate
to Bzlmod.

### External links on Bzlmod

*   [Bzlmod usage examples in bazelbuild/examples](https://github.com/bazelbuild/examples/tree/main/bzlmod)
*   [Bazel External Dependencies Overhaul](https://docs.google.com/document/d/1moQfNcEIttsk6vYanNKIy3ZuK53hQUFq1b1r0rmsYVg/edit)
    (original Bzlmod design doc)
*   [BazelCon 2021 talk on Bzlmod](https://www.youtube.com/watch?v=TxOCKtU39Fs)
*   [Bazel Community Day talk on Bzlmod](https://www.youtube.com/watch?v=MB6xxis9gWI)



# Frequently asked questions

This page answers some frequently asked questions about external dependencies in
Bazel.

## MODULE.bazel

### Why does MODULE.bazel not support `load`s?

During dependency resolution, the MODULE.bazel file of all referenced external
dependencies are fetched from registries. At this stage, the source archives of
the dependencies are not fetched yet; so if the MODULE.bazel file `load`s
another file, there is no way for Bazel to actually fetch that file without
fetching the entire source archive. Note the MODULE.bazel file itself is
special, as it's directly hosted on the registry.

There are a few use cases that people asking for `load`s in MODULE.bazel are
generally interested in, and they can be solved without `load`s:

*   Ensuring that the version listed in MODULE.bazel is consistent with build
    metadata stored elsewhere, for example in a .bzl file: This can be achieved
    by using the
    [`native.module_version`](/rules/lib/toplevel/native#module_version) method
    in a .bzl file loaded from a BUILD file.
*   Splitting up a very large MODULE.bazel file into manageable sections,
    particularly for monorepos: The root module can use the
    [`include`](/rules/lib/globals/module#include) directive to split its
    MODULE.bazel file into multiple segments. For the same reason we don't allow
    `load`s in MODULE.bazel files, `include` cannot be used in non-root modules.
*   Users of the old WORKSPACE system might remember declaring a repo, and then
    immediately `load`ing from that repo to perform complex logic. This
    capability has been replaced by [module extensions](extension).

### Can I specify a SemVer range for a `bazel_dep`?

No. Some other package managers like [npm][npm-semver] and [Cargo][cargo-semver]
support version ranges (implicitly or explicitly), and this often requires a
constraint solver (making the output harder to predict for users) and makes
version resolution nonreproducible without a lockfile.

Bazel instead uses [Minimal Version Selection](module#version-selection) like
Go, which in contrast makes the output easy to predict and guarantees
reproducibility. This is a tradeoff that matches Bazel's design goals.

Furthermore, Bazel module versions are [a superset of
SemVer](module#version-format), so what makes sense in a strict SemVer
environment doesn't always carry over to Bazel module versions.

### Can I automatically get the latest version for a `bazel_dep`?

Some users occasionally ask for the ability to specify `bazel_dep(name = "foo",
version = "latest")` to automatically get the latest version of a dep. This is
similar to [the question about SemVer
ranges](#can-i-specify-a-semver-range-for-a-bazel-dep), and the answer is also
no.

The recommended solution here is to have automation take care of this. For
example, [Renovate](https://docs.renovatebot.com/modules/manager/) supports
Bazel modules.

Sometimes, users asking this question are really looking for a way to quickly
iterate during local development. This can be achieved by using a
[`local_path_override`](/rules/lib/globals/module#local_path_override).

### Why all these `use_repo`s?

Module extension usages in MODULE.bazel files sometimes come with a big
`use_repo` directive. For example, a typical usage of the
[`go_deps` extension][go_deps] from `gazelle` might look like:

```python
go_deps = use_extension("@gazelle//:extensions.bzl", "go_deps")
go_deps.from_file(go_mod = "//:go.mod")
use_repo(
    go_deps,
    "com_github_gogo_protobuf",
    "com_github_golang_mock",
    "com_github_golang_protobuf",
    "org_golang_x_net",
    ...  # potentially dozens of lines...
)
```

The long `use_repo` directive may seem redundant, since the information is
arguably already in the referenced `go.mod` file.

The reason Bazel needs this `use_repo` directive is that it runs module
extensions lazily. That is, a module extension is only run if its result is
observed. Since a module extension's "output" is repo definitions, this means
that we only run a module extension if a repo it defines is requested (for
instance, if the target `@org_golang_x_net//:foo` is built, in the example
above). However, we don't know which repos a module extension would define until
after we run it. This is where the `use_repo` directive comes in; the user can
tell Bazel which repos they expect the extension to generate, and Bazel would
then only run the extension when these specific repos are used.

To help the maintain this `use_repo` directive, a module extension can return
an [`extension_metadata`](/rules/lib/builtins/module_ctx#extension_metadata)
object from its implementation function. The user can run the `bazel mod tidy`
command to update the `use_repo` directives for these module extensions.

## Bzlmod migration

### Which is evaluated first, MODULE.bazel or WORKSPACE?

When both `--enable_bzlmod` and `--enable_workspace` are set, it's natural to
wonder which system is consulted first. The short answer is that MODULE.bazel
(Bzlmod) is evaluated first.

The long answer is that "which evaluates first" is not the right question to
ask; rather, the right question to ask is: in the context of the repo with
[canonical name](overview#canonical-repo-name) `@@foo`, what does the [apparent
repo name](overview#apparent-repo-name) `@bar` resolve to? Alternatively, what
is the repo mapping of `@@base`?

Labels with apparent repo names (a single leading `@`) can refer to different
things based on the context they're resolved from. When you see a label
`@bar//:baz` and wonder what it actually points to, you need to first find out
what the context repo is: for example, if the label is in a BUILD file located
in the repo `@@foo`, then the context repo is `@@foo`.

Then, depending on what the context repo is, the ["repository
visibility" table](migration#repository-visibility) in the migration guide can
be used to find out which repo an apparent name actually resolves to.

*   If the context repo is the main repo (`@@`):
    1.  If `bar` is an apparent repo name introduced by the root module's
        MODULE.bazel file (through any of
        [`bazel_dep`](/rules/lib/globals/module#bazel_dep.repo_name),
        [`use_repo`](/rules/lib/globals/module#use_repo),
        [`module`](/rules/lib/globals/module#module.repo_name),
        [`use_repo_rule`](/rules/lib/globals/module#use_repo_rule)), then `@bar`
        resolves to what that MODULE.bazel file claims.
    2.  Otherwise, if `bar` is a repo defined in WORKSPACE (which means that its
        canonical name is `@@bar`), then `@bar` resolves to `@@bar`.
    3.  Otherwise, `@bar` resolves to something like
        `@@[unknown repo 'bar' requested from @@]`, and this will ultimately
        result in an error.
*   If the context repo is a Bzlmod-world repo (that is, it corresponds to a
    non-root Bazel module, or is generated by a module extension), then it
    will only ever see other Bzlmod-world repos, and no WORKSPACE-world repos.
    *   Notably, this includes any repos introduced in a `non_module_deps`-like
        module extension in the root module, or `use_repo_rule` instantiations
        in the root module.
*   If the context repo is defined in WORKSPACE:
    1.  First, check if the context repo definition has the magical
        `repo_mapping` attribute. If so, go through the mapping first (so for a
        repo defined with `repo_mapping = {"@bar": "@baz"}`, we would be looking
        at `@baz` below).
    2.  If `bar` is an apparent repo name introduced by the root module's
        MODULE.bazel file, then `@bar` resolves to what that MODULE.bazel file
        claims. (This is the same as item 1 in the main repo case.)
    3.  Otherwise, `@bar` resolves to `@@bar`. This most likely will point to a
        repo `bar` defined in WORKSPACE; if such a repo is not defined, Bazel
        will throw an error.

For a more succinct version:

*   Bzlmod-world repos (excluding the main repo) will only see Bzlmod-world
    repos.
*   WORKSPACE-world repos (including the main repo) will first see what the root
    module in the Bzlmod world defines, then fall back to seeing WORKSPACE-world
    repos.

Of note, labels in the Bazel command line (including Starlark flags, label-typed
flag values, and build/test target patterns) are treated as having the main repo
as the context repo.

## Other

### How do I prepare and run an offline build?

Use the `bazel fetch` command to prefetch repos. You can use the `--repo` flag
(like `bazel fetch --repo @foo`) to fetch only the repo `@foo` (resolved in the
context of the main repo, see [question
above](#which-is-evaluated-first-module-bazel-or-workspace)), or use a target
pattern (like `bazel fetch @foo//:bar`) to fetch all transitive dependencies of
`@foo//:bar` (this is equivalent to `bazel build --nobuild @foo//:bar`).

The make sure no fetches happen during a build, use `--nofetch`. More precisely,
this makes any attempt to run a non-local repository rule fail.

If you want to fetch repos _and_ modify them to test locally, consider using
the [`bazel vendor`](vendor) command.

### How do I use HTTP proxies?

Bazel respects the `http_proxy` and `HTTPS_PROXY` environment variables commonly
accepted by other programs, such as
[curl](https://everything.curl.dev/usingcurl/proxies/env.html).

### How do I make Bazel prefer IPv6 in dual-stack IPv4/IPv6 setups?

On IPv6-only machines, Bazel can download dependencies with no changes. However,
on dual-stack IPv4/IPv6 machines Bazel follows the same convention as Java,
preferring IPv4 if enabled. In some situations, for example when the IPv4
network cannot resolve/reach external addresses, this can cause `Network
unreachable` exceptions and build failures. In these cases, you can override
Bazel's behavior to prefer IPv6 by using the
[`java.net.preferIPv6Addresses=true` system
property](https://docs.oracle.com/javase/8/docs/api/java/net/doc-files/net-properties.html).
Specifically:

*   Use `--host_jvm_args=-Djava.net.preferIPv6Addresses=true` [startup
    option](/docs/user-manual#startup-options), for example by adding the
    following line in your [`.bazelrc` file](/run/bazelrc):

    `startup --host_jvm_args=-Djava.net.preferIPv6Addresses=true`

*   When running Java build targets that need to connect to the internet (such
    as for integration tests), use the
    `--jvmopt=-Djava.net.preferIPv6Addresses=true` [tool
    flag](/docs/user-manual#jvmopt). For example, include in your [`.bazelrc`
    file](/run/bazelrc):

    `build --jvmopt=-Djava.net.preferIPv6Addresses`

*   If you are using
    [`rules_jvm_external`](https://github.com/bazelbuild/rules_jvm_external) for
    dependency version resolution, also add
    `-Djava.net.preferIPv6Addresses=true` to the `COURSIER_OPTS` environment
    variable to [provide JVM options for
    Coursier](https://github.com/bazelbuild/rules_jvm_external#provide-jvm-options-for-coursier-with-coursier_opts).

### Can repo rules be run remotely with remote execution?

No; or at least, not yet. Users employing remote execution services to speed up
their builds may notice that repo rules are still run locally. For example, an
`http_archive` would be first downloaded onto the local machine (using any local
download cache if applicable), extracted, and then each source file would be
uploaded to the remote execution service as an input file. It's natural to ask
why the remote execution service doesn't just download and extract that archive,
saving a useless roundtrip.

Part of the reason is that repo rules (and module extensions) are akin to
"scripts" that are run by Bazel itself. A remote executor doesn't necessarily
even have a Bazel installed.

Another reason is that Bazel often needs the BUILD files in the downloaded and
extracted archives to perform loading and analysis, which _are_ performed
locally.

There are preliminary ideas to solve this problem by re-imagining repo rules as
build rules, which would naturally allow them to be run remotely, but conversely
raise new architectural concerns (for example, the `query` commands would
potentially need to run actions, complicating their design).

For more previous discussion on this topic, see [A way to support repositories
that need Bazel for being
fetched](https://github.com/bazelbuild/bazel/discussions/20464).

[npm-semver]: https://docs.npmjs.com/about-semantic-versioning
[cargo-semver]: https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#version-requirement-syntax
[go_deps]: https://github.com/bazel-contrib/rules_go/blob/master/docs/go/core/bzlmod.md#specifying-external-dependencies




# Bazel modules

A Bazel **module** is a Bazel project that can have multiple versions, each of
which publishes metadata about other modules that it depends on. This is
analogous to familiar concepts in other dependency management systems, such as a
Maven *artifact*, an npm *package*, a Go *module*, or a Cargo *crate*.

A module must have a `MODULE.bazel` file at its repo root. This file is the
module's manifest, declaring its name, version, list of direct dependencies, and
other information. For a basic example:

```python
module(name = "my-module", version = "1.0")

bazel_dep(name = "rules_cc", version = "0.0.1")
bazel_dep(name = "protobuf", version = "3.19.0")
```

See the [full list](/rules/lib/globals/module) of directives available in
`MODULE.bazel` files.

To perform module resolution, Bazel starts by reading the root module's
`MODULE.bazel` file, and then repeatedly requests any dependency's
`MODULE.bazel` file from a [Bazel registry](/external/registry) until it
discovers the entire dependency graph.

By default, Bazel then [selects](#version-selection) one version of each module
to use. Bazel represents each module with a repo, and consults the registry
again to learn how to define each of the repos.

## Version format

Bazel has a diverse ecosystem and projects use various versioning schemes. The
most popular by far is [SemVer](https://semver.org){: .external}, but there are
also prominent projects using different schemes such as
[Abseil](https://github.com/abseil/abseil-cpp/releases){: .external}, whose
versions are date-based, for example `20210324.2`).

For this reason, Bazel adopts a more relaxed version of the SemVer spec. The
differences include:

*   SemVer prescribes that the "release" part of the version must consist of 3
    segments: `MAJOR.MINOR.PATCH`. In Bazel, this requirement is loosened so
    that any number of segments is allowed.
*   In SemVer, each of the segments in the "release" part must be digits only.
    In Bazel, this is loosened to allow letters too, and the comparison
    semantics match the "identifiers" in the "prerelease" part.
*   Additionally, the semantics of major, minor, and patch version increases are
    not enforced. However, see [compatibility level](#compatibility_level) for
    details on how we denote backwards compatibility.

Any valid SemVer version is a valid Bazel module version. Additionally, two
SemVer versions `a` and `b` compare `a < b` if and only if the same holds when
they're compared as Bazel module versions.

## Version selection

Consider the diamond dependency problem, a staple in the versioned dependency
management space. Suppose you have the dependency graph:

```
       A 1.0
      /     \
   B 1.0    C 1.1
     |        |
   D 1.0    D 1.1
```

Which version of `D` should be used? To resolve this question, Bazel uses the
[Minimal Version Selection](https://research.swtch.com/vgo-mvs){: .external}
(MVS) algorithm introduced in the Go module system. MVS assumes that all new
versions of a module are backwards compatible, and so picks the highest version
specified by any dependent (`D 1.1` in our example). It's called "minimal"
because `D 1.1` is the earliest version that could satisfy our requirements —
even if `D 1.2` or newer exists, we don't select them. Using MVS creates a
version selection process that is *high-fidelity* and *reproducible*.

### Yanked versions

The registry can declare certain versions as *yanked* if they should be avoided
(such as for security vulnerabilities). Bazel throws an error when selecting a
yanked version of a module. To fix this error, either upgrade to a newer,
non-yanked version, or use the
[`--allow_yanked_versions`](/reference/command-line-reference#flag--allow_yanked_versions)
flag to explicitly allow the yanked version.

## Compatibility level

In Go, MVS's assumption about backwards compatibility works because it treats
backwards incompatible versions of a module as a separate module. In terms of
SemVer, that means `A 1.x` and `A 2.x` are considered distinct modules, and can
coexist in the resolved dependency graph. This is, in turn, made possible by
encoding the major version in the package path in Go, so there aren't any
compile-time or linking-time conflicts.

Bazel, however, cannot provide such guarantees, so it needs the "major version"
number in order to detect backwards incompatible versions. This number is called
the *compatibility level*, and is specified by each module version in its
`module()` directive. With this information, Bazel can throw an error when it
detects that versions of the same module with different compatibility levels
exist in the resolved dependency graph.

## Overrides

Specify overrides in the `MODULE.bazel` file to alter the behavior of Bazel
module resolution. Only the root module's overrides take effect — if a module is
used as a dependency, its overrides are ignored.

Each override is specified for a certain module name, affecting all of its
versions in the dependency graph. Although only the root module's overrides take
effect, they can be for transitive dependencies that the root module does not
directly depend on.

### Single-version override

The [`single_version_override`](/rules/lib/globals/module#single_version_override)
serves multiple purposes:

*   With the `version` attribute, you can pin a dependency to a specific
    version, regardless of which versions of the dependency are requested in the
    dependency graph.
*   With the `registry` attribute, you can force this dependency to come from a
    specific registry, instead of following the normal [registry
    selection](/external/registry#selecting_registries) process.
*   With the `patch*` attributes, you can specify a set of patches to apply to
    the downloaded module.

These attributes are all optional and can be mixed and matched with each other.

### Multiple-version override

A [`multiple_version_override`](/rules/lib/globals/module#multiple_version_override)
can be specified to allow multiple versions of the same module to coexist in the
resolved dependency graph.

You can specify an explicit list of allowed versions for the module, which must
all be present in the dependency graph before resolution — there must exist
*some* transitive dependency depending on each allowed version. After
resolution, only the allowed versions of the module remain, while Bazel upgrades
other versions of the module to the nearest higher allowed version at the same
compatibility level. If no higher allowed version at the same compatibility
level exists, Bazel throws an error.

For example, if versions `1.1`, `1.3`, `1.5`, `1.7`, and `2.0` exist in the
dependency graph before resolution and the major version is the compatibility
level:

*   A multiple-version override allowing `1.3`, `1.7`, and `2.0` results in
    `1.1` being upgraded to `1.3`, `1.5` being upgraded to `1.7`, and other
    versions remaining the same.
*   A multiple-version override allowing `1.5` and `2.0` results in an error, as
    `1.7` has no higher version at the same compatibility level to upgrade to.
*   A multiple-version override allowing `1.9` and `2.0` results in an error, as
    `1.9` is not present in the dependency graph before resolution.

Additionally, users can also override the registry using the `registry`
attribute, similarly to single-version overrides.

### Non-registry overrides

Non-registry overrides completely remove a module from version resolution. Bazel
does not request these `MODULE.bazel` files from a registry, but instead from
the repo itself.

Bazel supports the following non-registry overrides:

*   [`archive_override`](/rules/lib/globals/module#archive_override)
*   [`git_override`](/rules/lib/globals/module#git_override)
*   [`local_path_override`](/rules/lib/globals/module#local_path_override)

## Define repos that don't represent Bazel modules

With `bazel_dep`, you can define repos that represent other Bazel modules.
Sometimes there is a need to define a repo that does _not_ represent a Bazel
module; for example, one that contains a plain JSON file to be read as data.

In this case, you could use the [`use_repo_rule`
directive](/rules/lib/globals/module#use_repo_rule) to directly define a repo
by invoking a repo rule. This repo will only be visible to the module it's
defined in.

Under the hood, this is implemented using the same mechanism as [module
extensions](/external/extension), which lets you define repos with more
flexibility.

## Repository names and strict deps

The [apparent name](/external/overview#apparent-repo-name) of a repo backing a
module to its direct dependents defaults to its module name, unless the
`repo_name` attribute of the [`bazel_dep`](/rules/lib/globals/module#bazel_dep)
directive says otherwise. Note that this means a module can only find its direct
dependencies. This helps prevent accidental breakages due to changes in
transitive dependencies.

The [canonical name](/external/overview#canonical-repo-name) of a repo backing a
module is either `{{ "<var>" }}module_name{{ "</var>" }}+{{ "<var>" }}version{{
"</var>" }}` (for example, `bazel_skylib+1.0.3`) or `{{ "<var>" }}module_name{{
"</var>" }}+` (for example, `bazel_features+`), depending on whether there are
multiple versions of the module in the entire dependency graph (see
[`multiple_version_override`](/rules/lib/globals/module#multiple_version_override)).
Note that **the canonical name format** is not an API you should depend on and
**is subject to change at any time**. Instead of hard-coding the canonical name,
use a supported way to get it directly from Bazel:

*    In BUILD and `.bzl` files, use
     [`Label.repo_name`](/rules/lib/builtins/Label#repo_name) on a `Label` instance
     constructed from a label string given by the apparent name of the repo, e.g.,
     `Label("@bazel_skylib").repo_name`.
*    When looking up runfiles, use
     [`$(rlocationpath ...)`](https://bazel.build/reference/be/make-variables#predefined_label_variables)
     or one of the runfiles libraries in
     `@bazel_tools//tools/{bash,cpp,java}/runfiles` or, for a ruleset `rules_foo`,
     in `@rules_foo//foo/runfiles`.
*    When interacting with Bazel from an external tool such as an IDE or language
     server, use the `bazel mod dump_repo_mapping` command to get the mapping from
     apparent names to canonical names for a given set of repositories.

[Module extensions](/external/extension) can also introduce additional repos
into the visible scope of a module.



keywords: bzlmod

# Bzlmod Migration Guide

Due to the [shortcomings of
WORKSPACE](/external/overview#workspace-shortcomings), Bzlmod is replacing the
legacy WORKSPACE system. The WORKSPACE file is already disabled in Bazel 8 (late
2024) and will be removed in Bazel 9 (late 2025). This guide helps you migrate
your project to Bzlmod and drop WORKSPACE for managing external dependencies.

## Why migrate to Bzlmod?

*   There are many [advantages](overview#benefits) compared to the legacy
    WORKSPACE system, which helps to ensure a healthy growth of the Bazel
    ecosystem.

*   If your project is a dependency of other projects, migrating to Bzlmod will
    unblock their migration and make it easier for them to depend on your
    project.

*   Migration to Bzlmod is a necessary step in order to use future Bazel
    versions (mandatory in Bazel 9).

## WORKSPACE vs Bzlmod

Bazel's WORKSPACE and Bzlmod offer similar features with different syntax. This
section explains how to migrate from specific WORKSPACE functionalities to
Bzlmod.

### Define the root of a Bazel workspace

The WORKSPACE file marks the source root of a Bazel project, this responsibility
is replaced by MODULE.bazel in Bazel version 6.3 and later. With Bazel versions
prior to 6.3, there should still be a `WORKSPACE` or `WORKSPACE.bazel` file at
your workspace root, maybe with comments like:

*   **WORKSPACE**

    ```python
    # This file marks the root of the Bazel workspace.
    # See MODULE.bazel for external dependencies setup.
    ```

### Enable Bzlmod in your bazelrc

`.bazelrc` lets you set flags that apply every time your run Bazel. To enable
Bzlmod, use the `--enable_bzlmod` flag, and apply it to the `common` command so
it applies to every command:

* **.bazelrc**

    ```
    # Enable Bzlmod for every Bazel command
    common --enable_bzlmod
    ```

### Specify repository name for your workspace

*   **WORKSPACE**

    The [`workspace`](/rules/lib/globals/workspace#workspace) function is used
    to specify a repository name for your workspace. This allows a target
    `//foo:bar` in the workspace to be referenced as `@<workspace
    name>//foo:bar`. If not specified, the default repository name for your
    workspace is `__main__`.

    ```python
    ## WORKSPACE
    workspace(name = "com_foo_bar")
    ```

*   **Bzlmod**

    It's recommended to reference targets in the same workspace with the
    `//foo:bar` syntax without `@<repo name>`. But if you do need the old syntax
    , you can use the module name specified by the
    [`module`](/rules/lib/globals/module#module) function as the repository
    name. If the module name is different from the needed repository name, you
    can use `repo_name` attribute of the
    [`module`](/rules/lib/globals/module#module) function to override the
    repository name.

    ```python
    ## MODULE.bazel
    module(
        name = "bar",
        repo_name = "com_foo_bar",
    )
    ```

### Fetch external dependencies as Bazel modules

If your dependency is a Bazel project, you should be able to depend on it as a
Bazel module when it also adopts Bzlmod.

*   **WORKSPACE**

    With WORKSPACE, it's common to use the
    [`http_archive`](/rules/lib/repo/http#http_archive) or
    [`git_repository`](/rules/lib/repo/git#git_repository) repository rules to
    download the sources of the Bazel project.

    ```python
    ## WORKSPACE
    load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

    http_archive(
        name = "bazel_skylib",
        urls = ["https://github.com/bazelbuild/bazel-skylib/releases/download/1.4.2/bazel-skylib-1.4.2.tar.gz"],
        sha256 = "66ffd9315665bfaafc96b52278f57c7e2dd09f5ede279ea6d39b2be471e7e3aa",
    )
    load("@bazel_skylib//:workspace.bzl", "bazel_skylib_workspace")
    bazel_skylib_workspace()

    http_archive(
        name = "rules_java",
        urls = ["https://github.com/bazelbuild/rules_java/releases/download/6.1.1/rules_java-6.1.1.tar.gz"],
        sha256 = "76402a50ae6859d50bd7aed8c1b8ef09dae5c1035bb3ca7d276f7f3ce659818a",
    )
    load("@rules_java//java:repositories.bzl", "rules_java_dependencies", "rules_java_toolchains")
    rules_java_dependencies()
    rules_java_toolchains()
    ```

    As you can see, it's a common pattern that users need to load transitive
    dependencies from a macro of the dependency. Assume both `bazel_skylib` and
    `rules_java` depends on `platform`, the exact version of the `platform`
    dependency is determined by the order of the macros.

*   **Bzlmod**

    With Bzlmod, as long as your dependency is available in [Bazel Central
    Registry](https://registry.bazel.build) or your custom [Bazel
    registry](/external/registry), you can simply depend on it with a
    [`bazel_dep`](/rules/lib/globals/module#bazel_dep) directive.

    ```python
    ## MODULE.bazel
    bazel_dep(name = "bazel_skylib", version = "1.4.2")
    bazel_dep(name = "rules_java", version = "6.1.1")
    ```

    Bzlmod resolves Bazel module dependencies transitively using the
    [MVS](https://research.swtch.com/vgo-mvs) algorithm. Therefore, the maximal
    required version of `platform` is selected automatically.

### Override a dependency as a Bazel module{:#override-modules}

As the root module, you can override Bazel module dependencies in different
ways.

Please read the [overrides](/external/module#overrides) section for more
information.

You can find some example usages in the
[examples][override-examples]
repository.

[override-examples]: https://github.com/bazelbuild/examples/blob/main/bzlmod/02-override_bazel_module

### Fetch external dependencies with module extensions{:#fetch-deps-module-extensions}

If your dependency is not a Bazel project or not yet available in any Bazel
registry, you can introduce it using
[`use_repo_rule`](/external/module#use_repo_rule) or [module
extensions](/external/extension).

*   **WORKSPACE**

    Download a file using the [`http_file`](/rules/lib/repo/http#http_file)
    repository rule.

    ```python
    ## WORKSPACE
    load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_file")

    http_file(
        name = "data_file",
        url = "http://example.com/file",
        sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    ```

*   **Bzlmod**

    With Bzlmod, you can use the `use_repo_rule` directive in your MODULE.bazel
    file to directly instantiate repos:

    ```python
    ## MODULE.bazel
    http_file = use_repo_rule("@bazel_tools//tools/build_defs/repo:http.bzl", "http_file")
    http_file(
        name = "data_file",
        url = "http://example.com/file",
        sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    ```

    Under the hood, this is implemented using a module extension. If you need to
    perform more complex logic than simply invoking a repo rule, you could also
    implement a module extension yourself. You'll need to move the definition
    into a `.bzl` file, which also lets you share the definition between
    WORKSPACE and Bzlmod during the migration period.

    ```python
    ## repositories.bzl
    load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_file")
    def my_data_dependency():
        http_file(
            name = "data_file",
            url = "http://example.com/file",
            sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
    ```

    Implement a module extension to load the dependencies macro. You can define
    it in the same `.bzl` file of the macro, but to keep compatibility with
    older Bazel versions, it's better to define it in a separate `.bzl` file.

    ```python
    ## extensions.bzl
    load("//:repositories.bzl", "my_data_dependency")
    def _non_module_dependencies_impl(_ctx):
        my_data_dependency()

    non_module_dependencies = module_extension(
        implementation = _non_module_dependencies_impl,
    )
    ```

    To make the repository visible to the root project, you should declare the
    usages of the module extension and the repository in the MODULE.bazel file.

    ```python
    ## MODULE.bazel
    non_module_dependencies = use_extension("//:extensions.bzl", "non_module_dependencies")
    use_repo(non_module_dependencies, "data_file")
    ```

### Resolve conflict external dependencies with module extension

A project can provide a macro that introduces external repositories based on
inputs from its callers. But what if there are multiple callers in the
dependency graph and they cause a conflict?

Assume the project `foo` provides the following macro which takes `version` as
an argument.

```python
## repositories.bzl in foo
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_file")
def data_deps(version = "1.0"):
    http_file(
        name = "data_file",
        url = "http://example.com/file-%s" % version,
        # Omitting the "sha256" attribute for simplicity
    )
```

*   **WORKSPACE**

    With WORKSPACE, you can load the macro from `@foo` and specify the version
    of the data dependency you need. Assume you have another dependency `@bar`,
    which also depends on `@foo` but requires a different version of the data
    dependency.

    ```python
    ## WORKSPACE

    # Introduce @foo and @bar.
    ...

    load("@foo//:repositories.bzl", "data_deps")
    data_deps(version = "2.0")

    load("@bar//:repositories.bzl", "bar_deps")
    bar_deps() # -> which calls data_deps(version = "3.0")
    ```

    In this case, the end user must carefully adjust the order of macros in the
    WORKSPACE to get the version they need. This is one of the biggest pain
    points with WORKSPACE since it doesn't really provide a sensible way to
    resolve dependencies.

*   **Bzlmod**

    With Bzlmod, the author of project `foo` can use module extension to resolve
    conflicts. For example, let's assume it makes sense to always select the
    maximal required version of the data dependency among all Bazel modules.

    ```python
    ## extensions.bzl in foo
    load("//:repositories.bzl", "data_deps")

    data = tag_class(attrs={"version": attr.string()})

    def _data_deps_extension_impl(module_ctx):
        # Select the maximal required version in the dependency graph.
        version = "1.0"
        for mod in module_ctx.modules:
            for data in mod.tags.data:
                version = max(version, data.version)
        data_deps(version)

    data_deps_extension = module_extension(
        implementation = _data_deps_extension_impl,
        tag_classes = {"data": data},
    )
    ```

    ```python
    ## MODULE.bazel in bar
    bazel_dep(name = "foo", version = "1.0")

    foo_data_deps = use_extension("@foo//:extensions.bzl", "data_deps_extension")
    foo_data_deps.data(version = "3.0")
    use_repo(foo_data_deps, "data_file")
    ```

    ```python
    ## MODULE.bazel in root module
    bazel_dep(name = "foo", version = "1.0")
    bazel_dep(name = "bar", version = "1.0")

    foo_data_deps = use_extension("@foo//:extensions.bzl", "data_deps_extension")
    foo_data_deps.data(version = "2.0")
    use_repo(foo_data_deps, "data_file")
    ```

    In this case, the root module requires data version `2.0`, while its
    dependency `bar` requires `3.0`. The module extension in `foo` can correctly
    resolve this conflict and automatically select version `3.0` for the data
    dependency.

### Integrate third party package manager

Following the last section, since module extension provides a way to collect
information from the dependency graph, perform custom logic to resolve
dependencies and call repository rules to introduce external repositories, this
provides a great way for rules authors to enhance the rulesets that integrate
package managers for specific languages.

Please read the [module extensions](/external/extension) page to learn more
about how to use module extensions.

Here is a list of the rulesets that already adopted Bzlmod to fetch dependencies
from different package managers:

- [rules_jvm_external](https://github.com/bazelbuild/rules_jvm_external/blob/master/docs/bzlmod.md)
- [rules_go](https://github.com/bazelbuild/rules_go/blob/master/docs/go/core/bzlmod.md)
- [rules_python](https://github.com/bazelbuild/rules_python/blob/main/BZLMOD_SUPPORT.md)

A minimal example that integrates a pseudo package manager is available at the
[examples][pkg-mgr-example]
repository.

[pkg-mgr-example]: https://github.com/bazelbuild/examples/tree/main/bzlmod/05-integrate_third_party_package_manager

### Detect toolchains on the host machine

When Bazel build rules need to detect what toolchains are available on your host
machine, they use repository rules to inspect the host machine and generate
toolchain info as external repositories.

*   **WORKSPACE**

    Given the following repository rule to detect a shell toolchain.

    ```python
    ## local_config_sh.bzl
    def _sh_config_rule_impl(repository_ctx):
        sh_path = get_sh_path_from_env("SH_BIN_PATH")

        if not sh_path:
            sh_path = detect_sh_from_path()

        if not sh_path:
            sh_path = "/shell/binary/not/found"

        repository_ctx.file("BUILD", """
    load("@bazel_tools//tools/sh:sh_toolchain.bzl", "sh_toolchain")
    sh_toolchain(
        name = "local_sh",
        path = "{sh_path}",
        visibility = ["//visibility:public"],
    )
    toolchain(
        name = "local_sh_toolchain",
        toolchain = ":local_sh",
        toolchain_type = "@bazel_tools//tools/sh:toolchain_type",
    )
    """.format(sh_path = sh_path))

    sh_config_rule = repository_rule(
        environ = ["SH_BIN_PATH"],
        local = True,
        implementation = _sh_config_rule_impl,
    )
    ```

    You can load the repository rule in WORKSPACE.

    ```python
    ## WORKSPACE
    load("//:local_config_sh.bzl", "sh_config_rule")
    sh_config_rule(name = "local_config_sh")
    ```

*   **Bzlmod**

    With Bzlmod, you can introduce the same repository using a module extension,
    which is similar to introducing the `@data_file` repository in the last
    section.

    ```
    ## local_config_sh_extension.bzl
    load("//:local_config_sh.bzl", "sh_config_rule")

    sh_config_extension = module_extension(
        implementation = lambda ctx: sh_config_rule(name = "local_config_sh"),
    )
    ```

    Then use the extension in the MODULE.bazel file.

    ```python
    ## MODULE.bazel
    sh_config_ext = use_extension("//:local_config_sh_extension.bzl", "sh_config_extension")
    use_repo(sh_config_ext, "local_config_sh")
    ```

### Register toolchains & execution platforms

Following the last section, after introducing a repository hosting toolchain
information (e.g. `local_config_sh`), you probably want to register the
toolchain.

*   **WORKSPACE**

    With WORKSPACE, you can register the toolchain in the following ways.

    1.  You can register the toolchain the `.bzl` file and load the macro in the
    WORKSPACE file.

        ```python
        ## local_config_sh.bzl
        def sh_configure():
            sh_config_rule(name = "local_config_sh")
            native.register_toolchains("@local_config_sh//:local_sh_toolchain")
        ```

        ```python
        ## WORKSPACE
        load("//:local_config_sh.bzl", "sh_configure")
        sh_configure()
        ```

    2.  Or register the toolchain in the WORKSPACE file directly.

        ```python
        ## WORKSPACE
        load("//:local_config_sh.bzl", "sh_config_rule")
        sh_config_rule(name = "local_config_sh")
        register_toolchains("@local_config_sh//:local_sh_toolchain")
        ```

*   **Bzlmod**

    With Bzlmod, the
    [`register_toolchains`](/rules/lib/globals/module#register_toolchains) and
    [`register_execution_platforms`][register_execution_platforms]
    APIs are only available in the MODULE.bazel file. You cannot call
    `native.register_toolchains` in a module extension.

    ```python
    ## MODULE.bazel
    sh_config_ext = use_extension("//:local_config_sh_extension.bzl", "sh_config_extension")
    use_repo(sh_config_ext, "local_config_sh")
    register_toolchains("@local_config_sh//:local_sh_toolchain")
    ```

The toolchains and execution platforms registered in `WORKSPACE`,
`WORKSPACE.bzlmod` and each Bazel module's `MODULE.bazel` file follow this
order of precedence during toolchain selection (from highest to lowest):

1. toolchains and execution platforms registered in the root module's
   `MODULE.bazel` file.
2. toolchains and execution platforms registered in the `WORKSPACE` or
   `WORKSPACE.bzlmod` file.
3. toolchains and execution platforms registered by modules that are
   (transitive) dependencies of the root module.
4. when not using `WORKSPACE.bzlmod`: toolchains registered in the `WORKSPACE`
   [suffix](/external/migration#builtin-default-deps).

[register_execution_platforms]: /rules/lib/globals/module#register_execution_platforms

### Introduce local repositories

You may need to introduce a dependency as a local repository when you need a
local version of the dependency for debugging or you want to incorporate a
directory in your workspace as external repository.

*   **WORKSPACE**

    With WORKSPACE, this is achieved by two native repository rules,
    [`local_repository`](/reference/be/workspace#local_repository) and
    [`new_local_repository`](/reference/be/workspace#new_local_repository).

    ```python
    ## WORKSPACE
    local_repository(
        name = "rules_java",
        path = "/Users/bazel_user/workspace/rules_java",
    )
    ```

*   **Bzlmod**

    With Bzlmod, you can use
    [`local_path_override`](/rules/lib/globals/module#local_path_override) to
    override a module with a local path.

    ```python
    ## MODULE.bazel
    bazel_dep(name = "rules_java")
    local_path_override(
        module_name = "rules_java",
        path = "/Users/bazel_user/workspace/rules_java",
    )
    ```

    Note: With `local_path_override`, you can only introduce a local directory
    as a Bazel module, which means it should have a MODULE.bazel file and its
    transitive dependencies are taken into consideration during dependency
    resolution. In addition, all module override directives can only be used by
    the root module.

    It is also possible to introduce a local repository with module extension.
    However, you cannot call `native.local_repository` in module extension,
    there is ongoing effort on starlarkifying all native repository rules (check
    [#18285](https://github.com/bazelbuild/bazel/issues/18285) for progress).
    Then you can call the corresponding starlark `local_repository` in a module
    extension. It's also trivial to implement a custom version of
    `local_repository` repository rule if this is a blocking issue for you.

### Bind targets

The [`bind`](/reference/be/workspace#bind) rule in WORKSPACE is deprecated and
not supported in Bzlmod. It was introduced to give a target an alias in the
special `//external` package. All users depending on this should migrate away.

For example, if you have

```python
## WORKSPACE
bind(
    name = "openssl",
    actual = "@my-ssl//src:openssl-lib",
)
```

This allows other targets to depend on `//external:openssl`. You can migrate
away from this by:

*   Replace all usages of `//external:openssl` with
    `@my-ssl//src:openssl-lib`.

*   Or use the [`alias`](/reference/be/general#alias) build rule
    *   Define the following target in a package (e.g. `//third_party`)

        ```python
        ## third_party/BUILD
        alias(
            name = "openssl",
            actual = "@my-ssl//src:openssl-lib",
        )
        ```

    *   Replace all usages of `//external:openssl` with `//third_party:openssl`.

### Fetch versus Sync

Fetch and sync commands are used to download external repos locally and keep
them updated. Sometimes also to allow building offline using the `--nofetch`
flag after fetching all repos needed for a build.

*   **WORKSPACE**

    Sync performs a force fetch for all repositories, or for a specific
    configured set of repos, while fetch is _only_ used to fetch for a specific
    target.

*   **Bzlmod**

    The sync command is no longer applicable, but fetch offers
    [various options](/reference/command-line-reference#fetch-options).
    You can fetch a target, a repository, a set of configured repos or all
    repositories involved in your dependency resolution and module extensions.
    The fetch result is cached and to force a fetch you must include the
    `--force` option during the fetch process.

## Migration

This section provides useful information and guidance for your Bzlmod migration
process.

### Know your dependencies in WORKSPACE

The first step of migration is to understand what dependencies you have. It
could be hard to figure out what exact dependencies are introduced in the
WORKSPACE file because transitive dependencies are often loaded with `*_deps`
macros.

#### Inspect external dependency with workspace resolved file

Fortunately, the flag
[`--experimental_repository_resolved_file`][resolved_file_flag]
can help. This flag essentially generates a "lock file" of all fetched external
dependencies in your last Bazel command. You can find more details in this [blog
post](https://blog.bazel.build/2018/07/09/bazel-sync-and-resolved-file.html).

[resolved_file_flag]: /reference/command-line-reference#flag--experimental_repository_resolved_file

It can be used in two ways:

1.  To fetch info of external dependencies needed for building certain targets.

    ```shell
    bazel clean --expunge
    bazel build --nobuild --experimental_repository_resolved_file=resolved.bzl //foo:bar
    ```

2.  To fetch info of all external dependencies defined in the WORKSPACE file.

    ```shell
    bazel clean --expunge
    bazel sync --experimental_repository_resolved_file=resolved.bzl
    ```

    With the `bazel sync` command, you can fetch all dependencies defined in the
    WORKSPACE file, which include:

    *   `bind` usages
    *   `register_toolchains` & `register_execution_platforms` usages

    However, if your project is cross platforms, bazel sync may break on certain
    platforms because some repository rules may only run correctly on supported
    platforms.

After running the command, you should have information of your external
dependencies in the `resolved.bzl` file.

#### Inspect external dependency with `bazel query`

You may also know `bazel query` can be used for inspecting repository rules with

```shell
bazel query --output=build //external:<repo name>
```

While it is more convenient and much faster, [bazel query can lie about
external dependency version](https://github.com/bazelbuild/bazel/issues/12947),
so be careful using it! Querying and inspecting external
dependencies with Bzlmod is going to achieved by a [new
subcommand](https://github.com/bazelbuild/bazel/issues/15365).

#### Built-in default dependencies

If you check the file generated by `--experimental_repository_resolved_file`,
you are going to find many dependencies that are not defined in your WORKSPACE.
This is because Bazel in fact adds prefixes and suffixes to the user's WORKSPACE
file content to inject some default dependencies, which are usually required by
native rules (e.g. `@bazel_tools`, `@platforms` and `@remote_java_tools`). With
Bzlmod, those dependencies are introduced with a built-in module
[`bazel_tools`][bazel_tools] , which is a default dependency for every other
Bazel module.

[bazel_tools]: https://github.com/bazelbuild/bazel/blob/master/src/MODULE.tools

### Hybrid mode for gradual migration

Bzlmod and WORKSPACE can work side by side, which allows migrating dependencies
from the WORKSPACE file to Bzlmod to be a gradual process.

Note: In practice, loading "*_deps" macros in WORKSPACE often causes confusions
with Bzlmod dependencies, therefore we recommend starting with a
WORKSPACE.bzlmod file and avoid loading transitive dependencies with macros.

#### WORKSPACE.bzlmod

During the migration, Bazel users may need to switch between builds with and
without Bzlmod enabled. WORKSPACE.bzlmod support is implemented to make the
process smoother.

WORKSPACE.bzlmod has the exact same syntax as WORKSPACE. When Bzlmod is enabled,
if a WORKSPACE.bzlmod file also exists at the workspace root:

*   `WORKSPACE.bzlmod` takes effect and the content of `WORKSPACE` is ignored.
*   No [prefixes or suffixes](/external/migration#builtin-default-deps) are
    added to the WORKSPACE.bzlmod file.

Using the WORKSPACE.bzlmod file can make the migration easier because:

*   When Bzlmod is disabled, you fall back to fetching dependencies from the
    original WORKSPACE file.
*   When Bzlmod is enabled, you can better track what dependencies are left to
    migrate with WORKSPACE.bzlmod.

#### Repository visibility

Bzlmod is able to control which other repositories are visible from a given
repository, check [repository names and strict
deps](/external/module#repository_names_and_strict_deps) for more details.

Here is a summary of repository visibilities from different types of
repositories when also taking WORKSPACE into consideration.

| | From the main repo | From Bazel module repos | From module extension repos | From WORKSPACE repos |
|----------------|--------------------|-------------------------|---------------------------------------------------------------------------------------------------------------------|----------------------|
| The main repo  | Visible | If the root module is a direct dependency | If the root module is a direct dependency of the module hosting the module extension | Visible              |
| Bazel module repos | Direct deps | Direct deps | Direct deps of the module hosting the module extension | Direct deps of the root module |
| Module extension repos | Direct deps | Direct deps | Direct deps of the module hosting the module extension + all repos generated by the same module extension | Direct deps of the root module |
| WORKSPACE Repos | All visible | Not visible | Not visible | All visible |

Note: For the root module, if a repository `@foo` is defined in WORKSPACE and
`@foo` is also used as an [apparent repository
name](/external/overview#apparent-repo-name) in MODULE.bazel, then `@foo`
refers to the one introduced in MODULE.bazel.

Note: For a module extension generated repository `@bar`, if `@foo` is used as
an [apparent repository name](/external/overview#apparent-repo-name) of
another repository generated by the same module extension and direct
dependencies of the module hosting the module extension, then for repository
`@bar`, `@foo` refers to the latter.

### Migration process

A typical Bzlmod migration process can look like this:

1.  Understand what dependencies you have in WORKSPACE.
1.  Add an empty MODULE.bazel file at your project root.
1.  Add an empty WORKSPACE.bzlmod file to override the WORKSPACE file content.
1.  Build your targets with Bzlmod enabled and check which repository is
    missing.
1.  Check the definition of the missing repository in the resolved dependency
    file.
1.  Introduce the missing dependency as a Bazel module, through a module
    extension, or leave it in the WORKSPACE.bzlmod for later migration.
1.  Go back to 4 and repeat until all dependencies are available.

#### Migration tool

There is an interactive Bzlmod migration [helper script][migration_script] that
can get you started.

[migration_script]: https://github.com/bazelbuild/bazel-central-registry/blob/main/tools/migrate_to_bzlmod.py

The script does the following things:

*   Generate and parse the WORKSPACE resolved file.
*   Print repository info from the resolved file in a human readable way.
*   Run bazel build command, detect recognized error messages, and recommend a
    way to migrate.
*   Check if a dependency is already available in the BCR.
*   Add a dependency to MODULE.bazel file.
*   Add a dependency through a module extension.
*   Add a dependency to WORKSPACE.bzlmod file.

To use it, make sure you have the latest Bazel release installed, and run the
following command:

```shell
git clone https://github.com/bazelbuild/bazel-central-registry.git
cd bazel-central-registry
bazel build //tools:migrate_to_bzlmod
alias migrate2bzlmod=$(realpath ./bazel-bin/tools/migrate_to_bzlmod)

cd <your workspace root>
migrate2bzlmod -t <your build targets>
```

Note: The migration script is not perfect and may not be up-to-date since Bzlmod
is evolving, always double check if the recommended solution is correct.

## Publish Bazel modules

If your Bazel project is a dependency for other projects, you can publish your
project in the [Bazel Central Registry](https://registry.bazel.build/).

To be able to check in your project in the BCR, you need a source archive URL of
the project. Take note of a few things when creating the source archive:

*   **Make sure the archive is pointing to a specific version.**

    The BCR can only accept versioned source archives because Bzlmod needs to
    conduct version comparison during dependency resolution.

*   **Make sure the archive URL is stable.**

    Bazel verifies the content of the archive by a hash value, so you should
    make sure the checksum of the downloaded file never changes. If the URL is
    from GitHub, please create and upload a release archive in the release page.
    GitHub isn't going to guarantee the checksum of source archives generated on
    demand. In short, URLs in the form of
    `https://github.com/<org>/<repo>/releases/download/...` is considered stable
    while `https://github.com/<org>/<repo>/archive/...` is not. Check [GitHub
    Archive Checksum
    Outage](https://blog.bazel.build/2023/02/15/github-archive-checksum.html)
    for more context.

*   **Make sure the source tree follows the layout of the original repository.**

    In case your repository is very large and you want to create a distribution
    archive with reduced size by stripping out unnecessary sources, please make
    sure the stripped source tree is a subset of the original source tree. This
    makes it easier for end users to override the module to a non-release
    version by [`archive_override`](/rules/lib/globals/module#archive_override)
    and [`git_override`](/rules/lib/globals/module#git_override).

*   **Include a test module in a subdirectory that tests your most common
    APIs.**

    A test module is a Bazel project with its own WORKSPACE and MODULE.bazel
    file located in a subdirectory of the source archive which depends on the
    actual module to be published. It should contain examples or some
    integration tests that cover your most common APIs. Check
    [test module][test_module] to learn how to set it up.

[test_module]: https://github.com/bazelbuild/bazel-central-registry/tree/main/docs#test-module

When you have your source archive URL ready, follow the [BCR contribution
guidelines][bcr_contrib_guide] to submit your module to the BCR with a GitHub
Pull Request.

[bcr_contrib_guide]: https://github.com/bazelbuild/bazel-central-registry/tree/main/docs#contribute-a-bazel-module

It is **highly recommended** to set up the [Publish to
BCR](https://github.com/bazel-contrib/publish-to-bcr) GitHub App for your
repository to automate the process of submitting your module to the BCR.

## Best practices

This section documents a few best practices you should follow for better
managing your external dependencies.

#### Split targets into different packages to avoid fetching unnecessary dependencies.

Check [#12835](https://github.com/bazelbuild/bazel/issues/12835), where dev
dependencies for tests are forced to be fetched unnecessarily for building
targets that don't need them. This is actually not Bzlmod specific, but
following this practices makes it easier to specify dev dependencies correctly.

#### Specify dev dependencies

You can set the `dev_dependency` attribute to true for
[`bazel_dep`](/rules/lib/globals/module#bazel_dep) and
[`use_extension`](/rules/lib/globals/module#use_extension) directives so that
they don't propagate to dependent projects. As the root module, you can use the
[`--ignore_dev_dependency`][ignore_dev_dep_flag] flag to verify if your targets
still build without dev dependencies and overrides.

[ignore_dev_dep_flag]: /reference/command-line-reference#flag--ignore_dev_dependency

## Community migration progress

You can check the [Bazel Central Registry](https://registry.bazel.build) to find
out if your dependencies are already available. Otherwise feel free to join this
[GitHub discussion](https://github.com/bazelbuild/bazel/discussions/18329) to
upvote or post the dependencies that are blocking your migration.

## Report issues

Please check the [Bazel GitHub issue list][bzlmod_github_issue] for known Bzlmod
issues. Feel free to file new issues or feature requests that can help unblock
your migration!

[bzlmod_github_issue]: https://github.com/bazelbuild/bazel/issues?q=is%3Aopen+is%3Aissue+label%3Aarea-Bzlmod



keywords: product:Bazel,lockfile,Bzlmod

# Bazel Lockfile

The lockfile feature in Bazel enables the recording of specific versions or
dependencies of software libraries or packages required by a project. It
achieves this by storing the result of module resolution and extension
evaluation. The lockfile promotes reproducible builds, ensuring consistent
development environments. Additionally, it enhances build efficiency by allowing
Bazel to skip the parts of the resolution process that are unaffected by changes
in project dependencies. Furthermore, the lockfile improves stability by
preventing unexpected updates or breaking changes in external libraries, thereby
reducing the risk of introducing bugs.

## Lockfile Generation

The lockfile is generated under the workspace root with the name
`MODULE.bazel.lock`. It is created or updated during the build process,
specifically after module resolution and extension evaluation. Importantly, it
only includes dependencies that are included in the current invocation of the
build.

When changes occur in the project that affect its dependencies, the lockfile is
automatically updated to reflect the new state. This ensures that the lockfile
remains focused on the specific set of dependencies required for the current
build, providing an accurate representation of the project's resolved
dependencies.

## Lockfile Usage

The lockfile can be controlled by the flag
[`--lockfile_mode`](/reference/command-line-reference#flag--lockfile_mode) to
customize the behavior of Bazel when the project state differs from the
lockfile. The available modes are:

*   `update` (Default): Use the information that is present in the lockfile to
    skip downloads of known registry files and to avoid re-evaluating extensions
    whose results are still up-to-date. If information is missing, it will
    be added to the lockfile. In this mode, Bazel also avoids refreshing
    mutable information, such as yanked versions, for dependencies that haven't
    changed.
*   `refresh`: Like `update`, but mutable information is always refreshed when
    switching to this mode and roughly every hour while in this mode.
*   `error`: Like `update`, but if any information is missing or out-of-date,
    Bazel will fail with an error. This mode never changes the lockfile or
    performs network requests during resolution. Module extensions that marked
    themselves as `reproducible` may still perform network requests, but are
    expected to always produce the same result.
*   `off`: The lockfile is neither checked nor updated.

## Lockfile Benefits

The lockfile offers several benefits and can be utilized in various ways:

-   **Reproducible builds.** By capturing the specific versions or dependencies
    of software libraries, the lockfile ensures that builds are reproducible
    across different environments and over time. Developers can rely on
    consistent and predictable results when building their projects.

-   **Fast incremental resolutions.** The lockfile enables Bazel to avoid
    downloading registry files that were already used in a previous build.
    This significantly improves build efficiency, especially in scenarios where
    resolution can be time-consuming.

-   **Stability and risk reduction.** The lockfile helps maintain stability by
    preventing unexpected updates or breaking changes in external libraries. By
    locking the dependencies to specific versions, the risk of introducing bugs
    due to incompatible or untested updates is reduced.

## Lockfile Contents

The lockfile contains all the necessary information to determine whether the
project state has changed. It also includes the result of building the project
in the current state. The lockfile consists of two main parts:

1.   Hashes of all remote files that are inputs to module resolution.
2.   For each module extension, the lockfile includes inputs that affect it,
     represented by `bzlTransitiveDigest`, `usagesDigest` and other fields, as
     well as the output of running that extension, referred to as
     `generatedRepoSpecs`

Here is an example that demonstrates the structure of the lockfile, along with
explanations for each section:

```json
{
  "lockFileVersion": 10,
  "registryFileHashes": {
    "https://bcr.bazel.build/bazel_registry.json": "8a28e4af...5d5b3497",
    "https://bcr.bazel.build/modules/foo/1.0/MODULE.bazel": "7cd0312e...5c96ace2",
    "https://bcr.bazel.build/modules/foo/2.0/MODULE.bazel": "70390338... 9fc57589",
    "https://bcr.bazel.build/modules/foo/2.0/source.json": "7e3a9adf...170d94ad",
    "https://registry.mycorp.com/modules/foo/1.0/MODULE.bazel": "not found",
    ...
  },
  "selectedYankedVersions": {
    "foo@2.0": "Yanked for demo purposes"
  },
  "moduleExtensions": {
    "//:extension.bzl%lockfile_ext": {
      "general": {
        "bzlTransitiveDigest": "oWDzxG/aLnyY6Ubrfy....+Jp6maQvEPxn0pBM=",
        "usagesDigest": "aLmqbvowmHkkBPve05yyDNGN7oh7QE9kBADr3QIZTZs=",
        ...,
        "generatedRepoSpecs": {
          "hello": {
            "bzlFile": "@@//:extension.bzl",
            ...
          }
        }
      }
    },
    "//:extension.bzl%lockfile_ext2": {
      "os:macos": {
        "bzlTransitiveDigest": "oWDzxG/aLnyY6Ubrfy....+Jp6maQvEPxn0pBM=",
        "usagesDigest": "aLmqbvowmHkkBPve05y....yDNGN7oh7r3QIZTZs=",
        ...,
        "generatedRepoSpecs": {
          "hello": {
            "bzlFile": "@@//:extension.bzl",
            ...
          }
        }
      },
      "os:linux": {
        "bzlTransitiveDigest": "eWDzxG/aLsyY3Ubrto....+Jp4maQvEPxn0pLK=",
        "usagesDigest": "aLmqbvowmHkkBPve05y....yDNGN7oh7r3QIZTZs=",
        ...,
        "generatedRepoSpecs": {
          "hello": {
            "bzlFile": "@@//:extension.bzl",
            ...
          }
        }
      }
    }
  }
}
```

### Registry File Hashes

The `registryFileHashes` section contains the hashes of all files from
remote registries accessed during module resolution. Since the resolution
algorithm is fully deterministic when given the same inputs and all remote
inputs are hashed, this ensures a fully reproducible resolution result while
avoiding excessive duplication of remote information in the lockfile. Note that
this also requires recording when a particular registry didn't contain a certain
module, but a registry with lower precedence did (see the "not found" entry in
the example). This inherently mutable information can be updated via
`bazel mod deps --lockfile_mode=refresh`.

Bazel uses the hashes from the lockfile to look up registry files in the
repository cache before downloading them, which speeds up subsequent
resolutions.

### Selected Yanked Versions

The `selectedYankedVersions` section contains the yanked versions of modules
that were selected by module resolution. Since this usually result in an error
when trying to build, this section is only non-empty when yanked versions are
explicitly allowed via `--allow_yanked_versions` or
`BZLMOD_ALLOW_YANKED_VERSIONS`.

This field is needed since, compared to module files, yanked version information
is inherently mutable and thus can't be referenced by a hash. This information
can be updated via `bazel mod deps --lockfile_mode=refresh`.

### Module Extensions

The `moduleExtensions` section is a map that includes only the extensions used
in the current invocation or previously invoked, while excluding any extensions
that are no longer utilized. In other words, if an extension is not being used
anymore across the dependency graph, it is removed from the `moduleExtensions`
map.

If an extension is independent of the operating system or architecture type,
this section features only a single "general" entry. Otherwise, multiple
entries are included, named after the OS, architecture, or both, with each
corresponding to the result of evaluating the extension on those specifics.

Each entry in the extension map corresponds to a used extension and is
identified by its containing file and name. The corresponding value for each
entry contains the relevant information associated with that extension:

1. The `bzlTransitiveDigest` is the digest of the extension implementation
   and the .bzl files transitively loaded by it.
2. The `usagesDigest` is the digest of the _usages_ of the extension in the
   dependency graph, which includes all tags.
3. Further unspecified fields that track other inputs to the extension,
   such as contents of files or directories it reads or environment
   variables it uses.
4. The `generatedRepoSpecs` encode the repositories created by the
   extension with the current input.
5. The optional `moduleExtensionMetadata` field contains metadata provided by
   the extension such as whether certain repositories it created should be
   imported via `use_repo` by the root module. This information powers the
   `bazel mod tidy` command.

Module extensions can opt out of being included in the lockfile by setting the
returning metadata with `reproducible = True`. By doing so, they promise that
they will always create the same repositories when given the same inputs.

## Best Practices

To maximize the benefits of the lockfile feature, consider the following best
practices:

*   Regularly update the lockfile to reflect changes in project dependencies or
    configuration. This ensures that subsequent builds are based on the most
    up-to-date and accurate set of dependencies. To lock down all extensions
    at once, run `bazel mod deps --lockfile_mode=update`.

*   Include the lockfile in version control to facilitate collaboration and
    ensure that all team members have access to the same lockfile, promoting
    consistent development environments across the project.

*   Use [`bazelisk`](/install/bazelisk) to run Bazel, and include a
    `.bazelversion` file in version control that specifies the Bazel version
    corresponding to the lockfile. Because Bazel itself is a dependency of
    your build, the lockfile is specific to the Bazel version, and will
    change even between [backwards compatible](/release/backward-compatibility)
    Bazel releases. Using `bazelisk` ensures that all developers are using
    a Bazel version that matches the lockfile.

By following these best practices, you can effectively utilize the lockfile
feature in Bazel, leading to more efficient, reliable, and collaborative
software development workflows.

## Merge Conflicts

The lockfile format is designed to minimize merge conflicts, but they can still
happen.

### Automatic Resolution

Bazel provides a custom
[git merge driver](https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver)
to help resolve these conflicts automatically.

Set up the driver by adding this line to a `.gitattributes` file in the root of
your git repository:

```gitattributes
# A custom merge driver for the Bazel lockfile.
# https://bazel.build/external/lockfile#automatic-resolution
MODULE.bazel.lock merge=bazel-lockfile-merge
```

Then each developer who wants to use the driver has to register it once by
following these steps:

1. Install [jq](https://jqlang.github.io/jq/download/) (1.5 or higher).
2. Run the following commands:

```bash
jq_script=$(curl https://raw.githubusercontent.com/bazelbuild/bazel/master/scripts/bazel-lockfile-merge.jq)
printf '%s\n' "${jq_script}" | less # to optionally inspect the jq script
git config --global merge.bazel-lockfile-merge.name   "Merge driver for the Bazel lockfile (MODULE.bazel.lock)"
git config --global merge.bazel-lockfile-merge.driver "jq -s '${jq_script}' -- %O %A %B > %A.jq_tmp && mv %A.jq_tmp %A"
```

### Manual Resolution

Simple merge conflicts in the `registryFileHashes` and `selectedYankedVersions`
fields can be safely resolved by keeping all the entries from both sides of the
conflict.

Other types of merge conflicts should not be resolved manually. Instead:

1. Restore the previous state of the lockfile
   via `git reset MODULE.bazel.lock && git checkout MODULE.bazel.lock`.
2. Resolve any conflicts in the `MODULE.bazel` file.
3. Run `bazel mod deps` to update the lockfile.



keywords: product:Bazel,Bzlmod,vendor

# Vendor Mode

Vendor mode is a feature that lets you create a local copy of
external dependencies. This is useful for offline builds, or when you want to
control the source of an external dependency.

## Enable vendor mode

You can enable vendor mode by specifying `--vendor_dir` flag.

For example, by adding it to your `.bazelrc` file:

```none
# Enable vendor mode with vendor directory under <workspace>/vendor_src
common --vendor_dir=vendor_src
```

The vendor directory can be either a relative path to your workspace root or an
absolute path.

## Vendor a specific external repository

You can use the `vendor` command with the `--repo` flag to specify which repo
to vendor, it accepts both [canonical repo
name](/external/overview#canonical-repo-name) and [apparent repo
name](/external/overview#apparent-repo-name).

For example, running:

```none
bazel vendor --vendor_dir=vendor_src --repo=@rules_cc
```

or

```none
bazel vendor --vendor_dir=vendor_src --repo=@@rules_cc+
```

will both get rules_cc to be vendored under
`<workspace root>/vendor_src/rules_cc+`.

## Vendor external dependencies for given targets

To vendor all external dependencies required for building given target patterns,
you can run `bazel vendor <target patterns>`.

For example

```none
bazel vendor --vendor_dir=vendor_src //src/main:hello-world //src/test/...
```

will vendor all repos required for building the `//src/main:hello-world` target
and all targets under `//src/test/...` with the current configuration.

Under the hood, it's doing a `bazel build --nobuild` command to analyze the
target patterns, therefore build flags could be applied to this command and
affect the result.

### Build the target offline

With the external dependencies vendored, you can build the target offline by

```none
bazel build --vendor_dir=vendor_src //src/main:hello-world //src/test/...
```

The build should work in a clean build environment without network access and
repository cache.

Therefore, you should be able to check in the vendored source and build the same
targets offline on another machine.

Note: If you make changes to the targets to build, the external dependencies,
the build configuration, or the Bazel version, you may need to re-vendor to make
sure offline build still works.

## Vendor all external dependencies

To vendor all repos in your transitive external dependencies graph, you can
run:

```none
bazel vendor --vendor_dir=vendor_src
```

Note that vendoring all dependencies has a few **disadvantages**:

-   Fetching all repos, including those introduced transitively, can be time-consuming.
-   The vendor directory can become very large.
-   Some repos may fail to fetch if they are not compatible with the current platform or environment.

Therefore, consider vendoring for specific targets first.

## Configure vendor mode with VENDOR.bazel

You can control how given repos are handled with the VENDOR.bazel file located
under the vendor directory.

There are two directives available, both accepting a list of
[canonical repo names](/external/overview#canonical-repo-name) as arguments:

- `ignore()`: to completely ignore a repository from vendor mode.
- `pin()`: to pin a repository to its current vendored source as if there is a
  `--override_repository` flag for this repo. Bazel will NOT update the vendored
  source for this repo while running the vendor command unless it's unpinned.
  The user can modify and maintain the vendored source for this repo manually.

For example

```python
ignore("@@rules_cc+")
pin("@@bazel_skylib+")
```

With this configuration

-   Both repos will be excluded from subsequent vendor commands.
-   Repo `bazel_skylib` will be overridden to the source located under the
    vendor directory.
-   The user can safely modify the vendored source of `bazel_skylib`.
-   To re-vendor `bazel_skylib`, the user has to disable the pin statement
    first.

Note: Repository rules with
[`local`](/rules/lib/globals/bzl#repository_rule.local) or
[`configure`](/rules/lib/globals/bzl#repository_rule.configure) set to true are
always excluded from vendoring.

## Understand how vendor mode works

Bazel fetches external dependencies of a project under `$(bazel info
output_base)/external`. Vendoring external dependencies means moving out
relevant files and directories to the given vendor directory and use the
vendored source for later builds.

The content being vendored includes:

-   The repo directory
-   The repo marker file

During a build, if the vendored marker file is up-to-date or the repo is
pinned in the VENDOR.bazel file, then Bazel uses the vendored source by creating
a symlink to it under `$(bazel info output_base)/external` instead of actually
running the repository rule. Otherwise, a warning is printed and Bazel will
fallback to fetching the latest version of the repo.

Note: Bazel assumes the vendored source is not changed by users unless the repo
is pinned in the VENDOR.bazel file. If a user does change the vendored source
without pinning the repo, the changed vendored source will be used, but it will
be overwritten if its existing marker file is
outdated and the repo is vendored again.

### Vendor registry files

Bazel has to perform the Bazel module resolution in order to fetch external
dependencies, which may require accessing registry files through internet. To
achieve offline build, Bazel vendors all registry files fetched from
network under the `<vendor_dir>/_registries` directory.

### Vendor symlinks

External repositories may contain symlinks pointing to other files or
directories. To make sure symlinks work correctly, Bazel uses the following
strategy to rewrite symlinks in the vendored source:

-   Create a symlink `<vendor_dir>/bazel-external` that points to `$(bazel info
    output_base)/external`. It is refreshed by every Bazel command
    automatically.
-   For the vendored source, rewrite all symlinks that originally point to a
    path under `$(bazel info output_base)/external` to a relative path under
    `<vendor_dir>/bazel-external`.

For example, if the original symlink is

```none
<vendor_dir>/repo_foo+/link  =>  $(bazel info output_base)/external/repo_bar+/file
```

It will be rewritten to

```none
<vendor_dir>/repo_foo+/link  =>  ../../bazel-external/repo_bar+/file
```

where

```none
<vendor_dir>/bazel-external  =>  $(bazel info output_base)/external  # This might be new if output base is changed
```

Since `<vendor_dir>/bazel-external` is generated by Bazel automatically, it's
recommended to add it to `.gitignore` or equivalent to avoid checking it in.

With this strategy, symlinks in the vendored source should work correctly even
after the vendored source is moved to another location or the bazel output base
is changed.

Note: symlinks that point to an absolute path outside of $(bazel info
output_base)/external are not rewritten. Therefore, it could still break
cross-machine compatibility.

Note: On Windows, vendoring symlinks only works with
[`--windows_enable_symlinks`][windows_enable_symlinks]
flag enabled.

[windows_enable_symlinks]: /reference/command-line-reference#flag--windows_enable_symlinks



keywords: Bzlmod

# `mod` Command

The `mod` command provides a range of tools to help the user understand their
external dependency graph. It lets you visualize the dependency graph, find out
why a certain module or a version of a module is present in the graph, view the
repo definitions backing modules, inspect usages of module extensions and repos
they generate, among other functions.

## Syntax

```sh
bazel mod <subcommand> [<options>] [<arg> [<arg>...]]
```

The available subcommands and their respective required arguments are:

*   `graph`: Displays the full dependency graph of the project, starting from
    the root module. If one or more modules are specified in `--from`, these
    modules are shown directly under the root, and the graph is only expanded
    starting from them (see [example](#mod-example1)).

*   `deps <arg>...`: Displays the resolved direct dependencies of each of the
    specified modules, similarly to `graph`.

*   `all_paths <arg>...`: Displays all existing paths from the root to the
    specified `<arg>...`. If one or more modules are specified in `--from`,
    these modules are shown directly under the root, and the graph contains
    any existing path from the `--from` modules to the argument modules (see
    [example](#mod-example4)).

*   `path <arg>...`: Has the same semantics as `all_paths`, but only display a
    single path from one of the `--from` modules to one of the argument modules.

*   `explain <arg>...`: Shows all the places where the specified modules appear
    in the dependency graph, along with the modules that directly depend on
    them. The output of the `explain` command is essentially a pruned version of
    the `all_paths` command, containing 1) the root module; 2) the root module's
    direct dependencies that lead to the argument modules; 3) the argument
    modules' direct dependents; and
    4) the argument modules themselves (see [example](#mod-example5)).

*   `show_repo <arg>...`: Displays the definition of the specified repos (see
    [example](#mod-example6)).

*   `show_extension <extension>...`: Displays information about each of the
    specified extensions: a list of the generated repos along with the modules
    that import them using `use_repo`, and a list of the usages of that
    extension in each of the modules where it is used, containing the specified
    tags and the `use_repo` calls (see [example](#mod-example8)).

`<arg>` refers to one or more modules or repos. It can be one of:

*   The literal string `<root>`: The root module representing your current
    project.

*   `<name>@<version>`: The module `<name>` at version `<version>`. For a module
    with a non-registry override, use an underscore (`_`) as the `<version>`.

*   `<name>`: All present versions of the module `<name>`.

*   `@<repo_name>`: The repo with the given [apparent
    name](overview#apparent-repo-name) in the context of the `--base_module`.

*   `@@<repo_name>`: The repo with the given [canonical
    name](overview#canonical-repo-name).

In a context requiring specifying modules, `<arg>`s referring to repos that
correspond to modules (as opposed to extension-generated repos) can also be
used. Conversely, in a context requiring specifying repos, `<arg>`s referring to
modules can stand in for the corresponding repos.

`<extension>` must be of the form `<arg><label_to_bzl_file>%<extension_name>`.
The `<label_to_bzl_file>` part must be a repo-relative label (for example,
`//pkg/path:file.bzl`).

The following options only affect the subcommands that print graphs (`graph`,
`deps`, `all_paths`, `path`, and `explain`):

*   `--from <arg>[,<arg>[,...]]` *default: `<root>`*: The module(s) from which
    the graph is expanded in `graph`, `all_paths`, `path`, and `explain`. Check
    the subcommands' descriptions for more details.

*   `--verbose` *default: "false"*: Include in the output graph extra
    information about the version resolution of each module. If the module
    version changed during resolution, show either which version replaced it or
    what was the original version, the reason it was replaced, and which modules
    requested the new version if the reason was [Minimal Version
    Selection](module#version-selection).

*   `--include_unused` *default: "false"*: Include in the output graph the
    modules which were originally present in the dependency graph, but became
    unused after module resolution.

*   `--extension_info <mode>`: Include information about the module extension
    usages as part of the output graph (see [example](#mod-example7)). `<mode>`
    can be one of:

    *   `hidden` *(default)*: Don't show anything about extensions.

    *   `usages`: Show extensions under each module where they are used. They
        are printed in the form of `$<extension>`.

    *   `repos`: In addition to `usages`, show the repo imported using
        `use_repo` under each extension usage.

    *   `all`: In addition to `usages` and `repos`, also show
        extension-generated repos that are not imported by any module. These
        extra repos are shown under the first occurrence of their generating
        extension in the output, and are connected with a dotted edge.

*   `--extension_filter <extension>[,<extension>[,...]]`: If specified, the
    output graph only includes modules that use the specified extensions, and
    the paths that lead to those modules. Specifying an empty extension list (as
    in `--extension_filter=`) is equivalent to specifying _all_ extensions used
    by any module in the dependency graph.

*   `--depth <N>`: The depth of the output graph. A depth of 1 only displays the
    root and its direct dependencies. Defaults to 1 for `explain`, 2 for `deps`
    and infinity for the others.

*   `--cycles` *default: "false"*: Include cycle edges in the output graph.

*   `--include_builtin` *default: "false"*: Include built-in modules (such as
    `@bazel_tools`) in the output graph. This flag is disabled by default, as
    built-in modules are implicitly depended on by every other module, which
    greatly clutters the output.

*   `--charset <charset>` *default: utf8*: Specify the charset to use for text
    output. Valid values are `"utf8"` and `"ascii"`. The only significant
    difference is in the special characters used to draw the graph in the
    `"text"` output format, which don't exist in the `"ascii"` charset.
    Therefore, the `"ascii"` charset is present to also support the usage on
    legacy platforms which cannot use Unicode.

*   `--output <mode>`: Include information about the module extension usages as
    part of the output graph. `<mode`> can be one of:

    *   `text` *(default)*: A human-readable representation of the output graph
        (flattened as a tree).

    *   `json`: Outputs the graph in the form of a JSON object (flattened as a
        tree).

    *   `graph`: Outputs the graph in the Graphviz *dot* representation.

    Tip: Use the following command to pipe the output through the *dot* engine
        and export the graph representation as an SVG image.

    ```sh
    bazel mod graph --output graph | dot -Tsvg > /tmp/graph.svg
    ```

Other options include:

*   `--base_module <arg>` *default: `<root>`*: Specify a module relative to
    which apparent repo names in arguments are interpreted. Note that this
    argument itself can be in the form of `@<repo_name>`; this is always
    interpreted relative to the root module.

*   `--extension_usages <arg>[,<arg>[,...]]`: Filters `show_extension` to only
    display extension usages from the specified modules.

## Examples

Some possible usages of the `mod` command on a real Bazel project are showcased
below to give you a general idea on how you can use it to inspect your project's
external dependencies.

`MODULE.bazel` file:

```python
module(
  name = "my_project",
  version = "1.0",
)

bazel_dep(name = "bazel_skylib", version = "1.1.1", repo_name = "skylib1")
bazel_dep(name = "bazel_skylib", version = "1.2.0", repo_name = "skylib2")
multiple_version_override(module_name = "bazel_skylib", versions = ["1.1.1", "1.2.0"])

bazel_dep(name = "stardoc", version = "0.5.0")
bazel_dep(name = "rules_java", version = "5.0.0")

toolchains = use_extension("@rules_java//java:extensions.bzl", "toolchains")
use_repo(toolchains, my_jdk="remotejdk17_linux")
```

<table>
  <tr style="display: flex; flex-direction: row">
    <td style="flex: 5; display: flex; flex-direction: column">
      <figure style="height: 100%; display: flex; flex-direction: column;">
        <img src="images/mod_exampleBefore.svg" alt="Graph Before Resolution" style="object-fit: cover; max-width: 100%;">
        <figcaption style="margin-top: auto; margin-left: auto; margin-right: auto ">Graph Before Resolution</figcaption>
      </figure>
<!-- digraph mygraph {
  node [ shape=box ]
  edge [ fontsize=8 ]
  "<root>" [ label="<root> (my_project@1.0)" ]
  "<root>" -> "bazel_skylib@1.1.1" [  ]
  "<root>" -> "bazel_skylib@1.2.0" [  ]
  "<root>" -> "rules_java@5.0.0" [  ]
  "<root>" -> "stardoc@0.5.0" [  ]
  "bazel_skylib@1.1.1" -> "platforms@0.0.4" [  ]
  "bazel_skylib@1.2.0" -> "platforms@0.0.4" [  ]
  "rules_java@5.0.0" -> "platforms@0.0.4" [  ]
  "rules_java@5.0.0" -> "rules_cc@0.0.1" [  ]
  "rules_java@5.0.0" -> "rules_proto@4.0.0" [  ]
  "stardoc@0.5.0" -> "bazel_skylib@1.0.3" [  ]
  "stardoc@0.5.0" -> "rules_java@4.0.0" [  ]
  "rules_cc@0.0.1" -> "bazel_skylib@1.0.3" [  ]
  "rules_cc@0.0.1" -> "platforms@0.0.4" [  ]
  "rules_proto@4.0.0" -> "bazel_skylib@1.0.3" [  ]
  "rules_proto@4.0.0" -> "rules_cc@0.0.1" [  ]
  "bazel_skylib@1.0.3" [  ]
  "bazel_skylib@1.0.3" -> "platforms@0.0.4" [  ]
  "rules_java@4.0.0" [  ]
  "rules_java@4.0.0" -> "bazel_skylib@1.0.3" [  ]
} -->
    </td>
    <td style="flex: 3; display: flex; flex-direction: column">
      <figure style="height: 100%; display: flex; flex-direction: column;">
        <img src="images/mod_exampleResolved.svg" alt="Graph After Resolution" style="object-fit: cover; max-width: 100%;">
       <figcaption style="margin-top: auto; margin-left: auto; margin-right: auto ">Graph After Resolution</figcaption>
      </figure>
<!-- digraph mygraph {
  node [ shape=box ]
  edge [ fontsize=8 ]
  "<root>" [ label="<root> (my_project@1.0)" ]
  "<root>" -> "bazel_skylib@1.1.1" [  ]
  "<root>" -> "bazel_skylib@1.2.0" [  ]
  "<root>" -> "rules_java@5.0.0" [  ]
  "<root>" -> "stardoc@0.5.0" [  ]
  "bazel_skylib@1.1.1" -> "platforms@0.0.4" [  ]
  "bazel_skylib@1.2.0" -> "platforms@0.0.4" [  ]
  "rules_java@5.0.0" -> "platforms@0.0.4" [  ]
  "rules_java@5.0.0" -> "rules_cc@0.0.1" [  ]
  "rules_java@5.0.0" -> "rules_proto@4.0.0" [  ]
  "stardoc@0.5.0" -> "bazel_skylib@1.1.1" [  ]
  "stardoc@0.5.0" -> "rules_java@5.0.0" [  ]
  "rules_cc@0.0.1" -> "bazel_skylib@1.1.1" [  ]
  "rules_cc@0.0.1" -> "platforms@0.0.4" [  ]
  "rules_proto@4.0.0" -> "bazel_skylib@1.1.1" [  ]
  "rules_proto@4.0.0" -> "rules_cc@0.0.1" [  ]
} -->
    </td>
  </tr>
</table>

1.  <span id="mod-example1"></span>Display the whole dependency graph of your
    project.

    ```sh
    bazel mod graph
    ```

    ```none
    <root> (my_project@1.0)
    ├───bazel_skylib@1.1.1
    │   └───platforms@0.0.4
    ├───bazel_skylib@1.2.0
    │   └───platforms@0.0.4 ...
    ├───rules_java@5.0.0
    │   ├───platforms@0.0.4 ...
    │   ├───rules_cc@0.0.1
    │   │   ├───bazel_skylib@1.1.1 ...
    │   │   └───platforms@0.0.4 ...
    │   └───rules_proto@4.0.0
    │       ├───bazel_skylib@1.1.1 ...
    │       └───rules_cc@0.0.1 ...
    └───stardoc@0.5.0
        ├───bazel_skylib@1.1.1 ...
        └───rules_java@5.0.0 ...
    ```

    Note: The `...` symbol indicates that the node has already been expanded
    somewhere else and was not expanded again to reduce noise.

2.  <span id="mod-example2"></span>Display the whole dependency graph (including
    unused modules and with extra information about version resolution).

    ```sh
    bazel mod graph --include_unused --verbose
    ```

    ```none
    <root> (my_project@1.0)
    ├───bazel_skylib@1.1.1
    │   └───platforms@0.0.4
    ├───bazel_skylib@1.2.0
    │   └───platforms@0.0.4 ...
    ├───rules_java@5.0.0
    │   ├───platforms@0.0.4 ...
    │   ├───rules_cc@0.0.1
    │   │   ├───bazel_skylib@1.0.3 ... (to 1.1.1, cause multiple_version_override)
    │   │   ├───bazel_skylib@1.1.1 ... (was 1.0.3, cause multiple_version_override)
    │   │   └───platforms@0.0.4 ...
    │   └───rules_proto@4.0.0
    │       ├───bazel_skylib@1.0.3 ... (to 1.1.1, cause multiple_version_override)
    │       ├───bazel_skylib@1.1.1 ... (was 1.0.3, cause multiple_version_override)
    │       └───rules_cc@0.0.1 ...
    └───stardoc@0.5.0
        ├───bazel_skylib@1.1.1 ... (was 1.0.3, cause multiple_version_override)
        ├───rules_java@5.0.0 ... (was 4.0.0, cause <root>, bazel_tools@_)
        ├───bazel_skylib@1.0.3 (to 1.1.1, cause multiple_version_override)
        │   └───platforms@0.0.4 ...
        └───rules_java@4.0.0 (to 5.0.0, cause <root>, bazel_tools@_)
            ├───bazel_skylib@1.0.3 ... (to 1.1.1, cause multiple_version_override)
            └───bazel_skylib@1.1.1 ... (was 1.0.3, cause multiple_version_override)
    ```

3.  <span id="mod-example3"></span>Display the dependency graph expanded from
    some specific modules.

    ```sh
    bazel mod graph --from rules_java --include_unused
    ```

    ```none
    <root> (my_project@1.0)
    ├───rules_java@5.0.0
    │   ├───platforms@0.0.4
    │   ├───rules_cc@0.0.1
    │   │   ├───bazel_skylib@1.0.3 ... (unused)
    │   │   ├───bazel_skylib@1.1.1 ...
    │   │   └───platforms@0.0.4 ...
    │   └───rules_proto@4.0.0
    │       ├───bazel_skylib@1.0.3 ... (unused)
    │       ├───bazel_skylib@1.1.1 ...
    │       └───rules_cc@0.0.1 ...
    └╌╌rules_java@4.0.0 (unused)
        ├───bazel_skylib@1.0.3 (unused)
        │   └───platforms@0.0.4 ...
        └───bazel_skylib@1.1.1
            └───platforms@0.0.4 ...
    ```

    Note: The dotted line is used to indicate an *indirect* (transitive)
    dependency edge between two nodes.

4.  <span id="mod-example4"></span>Display all paths between two of your
    modules.

    ```sh
    bazel mod all_paths bazel_skylib@1.1.1 --from rules_proto
    ```

    ```none
    <root> (my_project@1.0)
    └╌╌rules_proto@4.0.0
        ├───bazel_skylib@1.1.1
        └───rules_cc@0.0.1
            └───bazel_skylib@1.1.1 ...
    ```

5.  <span id="mod-example5"></span>See why and how your project depends on some
    module(s).

    ```sh
    bazel mod explain @skylib1 --verbose --include_unused
    ```

    ```none
    <root> (my_project@1.0)
    ├───bazel_skylib@1.1.1
    ├───rules_java@5.0.0
    │   ├───rules_cc@0.0.1
    │   │   └───bazel_skylib@1.1.1 ... (was 1.0.3, cause multiple_version_override)
    │   └───rules_proto@4.0.0
    │       ├───bazel_skylib@1.1.1 ... (was 1.0.3, cause multiple_version_override)
    │       └───rules_cc@0.0.1 ...
    └───stardoc@0.5.0
        ├───bazel_skylib@1.1.1 ... (was 1.0.3, cause multiple_version_override)
        ├╌╌rules_cc@0.0.1
        │   └───bazel_skylib@1.1.1 ... (was 1.0.3, cause multiple_version_override)
        └╌╌rules_proto@4.0.0
            ├───bazel_skylib@1.1.1 ... (was 1.0.3, cause multiple_version_override)
            └───rules_cc@0.0.1 ...
    ```

6.  <span id="mod-example6"></span>See the underlying rule of some your modules'
    repos.

    ```sh
    bazel mod show_repo rules_cc stardoc
    ```

    ```none
    ## rules_cc@0.0.1:
    # <builtin>
    http_archive(
      name = "rules_cc+",
      urls = ["https://bcr.bazel.build/test-mirror/github.com/bazelbuild/rules_cc/releases/download/0.0.1/rules_cc-0.0.1.tar.gz", "https://github.com/bazelbuild/rules_cc/releases/download/0.0.1/rules_cc-0.0.1.tar.gz"],
      integrity = "sha256-Tcy/0iwN7xZMj0dFi9UODHFI89kgAs20WcKpamhJgkE=",
      strip_prefix = "",
      remote_patches = {"https://bcr.bazel.build/modules/rules_cc/0.0.1/patches/add_module_extension.patch": "sha256-g3+zmGs0YT2HKOVevZpN0Jet89Ylw90Cp9XsIAY8QqU="},
      remote_patch_strip = 1,
    )
    # Rule http_archive defined at (most recent call last):
    #   /home/user/.cache/bazel/_bazel_user/6e893e0f5a92cc4cf5909a6e4b2770f9/external/bazel_tools/tools/build_defs/repo/http.bzl:355:31 in <toplevel>

    ## stardoc:
    # <builtin>
    http_archive(
      name = "stardoc+",
      urls = ["https://bcr.bazel.build/test-mirror/github.com/bazelbuild/stardoc/releases/download/0.5.0/stardoc-0.5.0.tar.gz", "https://github.com/bazelbuild/stardoc/releases/download/0.5.0/stardoc-0.5.0.tar.gz"],
      integrity = "sha256-yXlNzIAmow/2fPfPkeviRcopSyCwcYRdEsGSr+JDrXI=",
      strip_prefix = "",
      remote_patches = {},
      remote_patch_strip = 0,
    )
    # Rule http_archive defined at (most recent call last):
    #   /home/user/.cache/bazel/_bazel_user/6e893e0f5a92cc4cf5909a6e4b2770f9/external/bazel_tools/tools/build_defs/repo/http.bzl:355:31 in <toplevel>
    ```

7.  <span id="mod-example7"></span>See what module extensions are used in your
    dependency graph.

    ```sh
    bazel mod graph --extension_info=usages --extension_filter=all
    ```

    ```none
    <root> (my_project@1.0)
    ├───$@@rules_java.5.0.0//java:extensions.bzl%toolchains
    ├───rules_java@5.0.0 #
    │   ├───$@@rules_java.5.0.0//java:extensions.bzl%toolchains
    │   ├───rules_cc@0.0.1 #
    │   │   └───$@@rules_cc.0.0.1//bzlmod:extensions.bzl%cc_configure
    │   └───rules_proto@4.0.0
    │       └───rules_cc@0.0.1 ...
    └───stardoc@0.5.0
        └───rules_java@5.0.0 ...
    ```

8.  <span id="mod-example8"></span>See what repositories are generated and
    imported from some specific extension as part of the dependency graph.

    ```sh
    bazel mod show_extension @@rules_java+5.0.0//java:extensions.bzl%toolchains
    ```

    ```none
    <root> (my_project@1.0)
    ├───$@@rules_java.5.0.0//java:extensions.bzl%toolchains
    │   ├───remotejdk17_linux
    │   ├╌╌remotejdk11_linux
    │   ├╌╌remotejdk11_linux_aarch64
    │   ├╌╌remotejdk11_linux_ppc64le
    │   ├╌╌remotejdk11_linux_s390x
    ...(some lines omitted)...
    ├───rules_java@5.0.0 #
    │   └───$@@rules_java.5.0.0//java:extensions.bzl%toolchains ...
    │       ├───local_jdk
    │       ├───remote_java_tools
    │       ├───remote_java_tools_darwin
    │       ├───remote_java_tools_linux
    │       ├───remote_java_tools_windows
    │       ├───remotejdk11_linux_aarch64_toolchain_config_repo
    │       ├───remotejdk11_linux_ppc64le_toolchain_config_repo
    ...(some lines omitted)...
    └───stardoc@0.5.0
        └───rules_java@5.0.0 ...
    ```

9.  <span id="mod-example9"></span>See the list of generated repositories of an
    extension and how that extension is used in each module.

    ```sh
    bazel mod graph --extension_info=all --extension_filter=@rules_java//java:extensions.bzl%toolchains
    ```

    ```none
    ## @@rules_java.5.0.0//java:extensions.bzl%toolchains:

    Fetched repositories:
      -   local_jdk (imported by bazel_tools@_, rules_java@5.0.0)
      -   remote_java_tools (imported by bazel_tools@_, rules_java@5.0.0)
      -   remote_java_tools_darwin (imported by bazel_tools@_, rules_java@5.0.0)
      -   remote_java_tools_linux (imported by bazel_tools@_, rules_java@5.0.0)
      -   remote_java_tools_windows (imported by bazel_tools@_, rules_java@5.0.0)
      -   remotejdk11_linux_aarch64_toolchain_config_repo (imported by rules_java@5.0.0)
      -   remotejdk11_linux_ppc64le_toolchain_config_repo (imported by rules_java@5.0.0)
    ...(some lines omitted)...
      -   remotejdk17_linux (imported by <root>)
      -   remotejdk11_linux
      -   remotejdk11_linux_aarch64
      -   remotejdk11_linux_ppc64le
      -   remotejdk11_linux_s390x
      -   remotejdk11_macos
    ...(some lines omitted)...

    # Usage in <root> at <root>/MODULE.bazel:14:27 with the specified attributes:
    use_repo(
      toolchains,
      my_jdk="remotejdk17_linux",
    )

    # Usage in bazel_tools@_ at bazel_tools@_/MODULE.bazel:23:32 with the specified attributes:
    use_repo(
      toolchains,
      "local_jdk",
      "remote_java_tools",
      "remote_java_tools_linux",
      "remote_java_tools_windows",
      "remote_java_tools_darwin",
    )

    # Usage in rules_java@5.0.0 at rules_java@5.0.0/MODULE.bazel:30:27 with the specified attributes:
    use_repo(
      toolchains,
      "remote_java_tools",
      "remote_java_tools_linux",
      "remote_java_tools_windows",
      "remote_java_tools_darwin",
      "local_jdk",
      "remotejdk11_linux_toolchain_config_repo",
      "remotejdk11_macos_toolchain_config_repo",
      "remotejdk11_macos_aarch64_toolchain_config_repo",
      ...(some lines omitted)...
    )
    ```

10.  <span id="mod-example10"></span>See the underlying rule of some
    extension-generated repositories.

    ```sh
    bazel mod show_repo --base_module=rules_java @remote_java_tools
    ```

    ```none
    ## @remote_java_tools:
    # <builtin>
    http_archive(
      name = "rules_java++toolchains+remote_java_tools",
      urls = ["https://mirror.bazel.build/bazel_java_tools/releases/java/v11.5/java_tools-v11.5.zip", "https://github.com/bazelbuild/java_tools/releases/download/java_v11.5/java_tools-v11.5.zip"],
      sha256 = "b763ee80e5754e593fd6d5be6d7343f905bc8b73d661d36d842b024ca11b6793",
    )
    # Rule http_archive defined at (most recent call last):
    #   /home/user/.cache/bazel/_bazel_user/6e893e0f5a92cc4cf5909a6e4b2770f9/external/bazel_tools/tools/build_defs/repo/http.bzl:355:31 in <toplevel>
    ```


# Bazel registries

Bazel discovers dependencies by requesting their information from Bazel
*registries*: databases of Bazel modules. Bazel only supports one type of
registries — [*index registries*](#index_registry) — local directories or static
HTTP servers following a specific format.

## Index registry

An index registry is a local directory or a static HTTP server containing
information about a list of modules — including their homepage, maintainers, the
`MODULE.bazel` file of each version, and how to fetch the source of each
version. Notably, it does *not* need to serve the source archives itself.

An index registry must have the following format:

*   [`/bazel_registry.json`](#bazel-registry-json): An optional JSON file
    containing metadata for the registry.
*   `/modules`: A directory containing a subdirectory for each module in this
    registry
*   `/modules/$MODULE`: A directory containing a subdirectory for each version
    of the module named `$MODULE`, as well as the [`metadata.json`
    file](#metadata-json) containing metadata for this module.
*   `/modules/$MODULE/$VERSION`: A directory containing the following files:
    *   `MODULE.bazel`: The `MODULE.bazel` file of this module version. Note
        that this is the `MODULE.bazel` file read during Bazel's external
        dependency resolution, _not_ the one from the source archive (unless
        there's a non-registry override).
    *   [`source.json`](#source-json): A JSON file containing information on how
        to fetch the source of this module version
    *   `patches/`: An optional directory containing patch files, only used when
        `source.json` has "archive" type
    *   `overlay/`: An optional directory containing overlay files, only used
        when `source.json` has "archive" type

### `bazel_registry.json`

`bazel_registry.json` is an optional file that specifies metadata applying to
the entire registry. It can contain the following fields:

*   `mirrors`: an array of strings, specifying the list of mirrors to use for
    source archives.
    *   The mirrored URL is a concatenation of the mirror itself, and the
        source URL of the module specified by its `source.json` file sans the
        protocol. For example, if a module's source URL is
        `https://foo.com/bar/baz`, and `mirrors` contains
        `["https://mirror1.com/", "https://example.com/mirror2/"]`, then the
        URLs Bazel will try in order are `https://mirror1.com/foo.com/bar/baz`,
        `https://example.com/mirror2/foo.com/bar/baz`, and finally the original
        source URL itself `https://foo.com/bar/baz`.
*   `module_base_path`: a string, specifying the base path for modules with
    `local_path` type in the `source.json` file

### `metadata.json`

`metadata.json` is an optional JSON file containing information about the
module, with the following fields:

*   `versions`: An array of strings, each denoting a version of the module
    available in this registry. This array should match the children of the
    module directory.
*   `yanked_versions`: A JSON object specifying the [*yanked*
    versions](/external/module#yanked_versions) of this module. The keys
    should be versions to yank, and the values should be descriptions of
    why the version is yanked, ideally containing a link to more
    information.

Note that the BCR requires more information in the `metadata.json` file.

### `source.json`

`source.json` is a required JSON file containing information about how to fetch
a specific version of a module. The schema of this file depends on its `type`
field, which defaults to `archive`.

*   If `type` is `archive` (the default), this module version is backed by an
    [`http_archive`](/rules/lib/repo/http#http_archive) repo rule; it's fetched
    by downloading an archive from a given URL and extracting its contents. It
    supports the following fields:
    *   `url`: A string, the URL of the source archive
    *   `mirror_urls`: A list of string, the mirror URLs of the source archive.
        The URLs are tried in order after `url` as backups.
    *   `integrity`: A string, the [Subresource
        Integrity][subresource-integrity] checksum of the archive
    *   `strip_prefix`: A string, the directory prefix to strip when extracting
        the source archive
    *   `overlay`: A JSON object containing overlay files to layer on top of the
        extracted archive. The patch files are located under the
        `/modules/$MODULE/$VERSION/overlay` directory. The keys are the
        overlay file names, and the values are the integrity checksum of
        the overlay files. The overlays are applied before the patch files.
    *   `patches`: A JSON object containing patch files to apply to the
        extracted archive. The patch files are located under the
        `/modules/$MODULE/$VERSION/patches` directory. The keys are the
        patch file names, and the values are the integrity checksum of
        the patch files. The patches are applied after the overlay files.
    *   `patch_strip`: A number; the same as the `--strip` argument of Unix
        `patch`.
    *   `archive_type`: A string, the archive type of the downloaded file (Same
        as [`type` on `http_archive`](/rules/lib/repo/http#http_archive-type)).
*   If `type` is `git_repository`, this module version is backed by a
    [`git_repository`](/rules/lib/repo/git#git_repository) repo rule; it's
    fetched by cloning a Git repository.
    *   The following fields are supported, and are directly forwarded to the
        underlying `git_repository` repo rule: `remote`, `commit`,
        `shallow_since`, `tag`, `init_submodules`, `verbose`, and
        `strip_prefix`.
*   If `type` is `local_path`, this module version is backed by a
    [`local_repository`](/rules/lib/repo/local#local_repository) repo rule;
    it's symlinked to a directory on local disk. It supports the following
    field:
    *   `path`: The local path to the repo, calculated as following:
        *   If `path` is an absolute path, it stays as it is
        *   If `path` is a relative path and `module_base_path` is an
            absolute path, it resolves to `<module_base_path>/<path>`
        *   If `path` and `module_base_path` are both relative paths, it
            resolves to `<registry_path>/<module_base_path>/<path>`.
            Registry must be hosted locally and used by
            `--registry=file://<registry_path>`. Otherwise, Bazel will
            throw an error

## Bazel Central Registry

The Bazel Central Registry (BCR) at <https://bcr.bazel.build/> is an index
registry with contents backed by the GitHub repo
[`bazelbuild/bazel-central-registry`][bcr-repo]. You can browse its contents
using the web frontend at <https://registry.bazel.build/>.

The Bazel community maintains the BCR, and contributors are welcome to submit
pull requests. See the [BCR contribution
guidelines][bcr-contribution-guidelines].

In addition to following the format of a normal index registry, the BCR requires
a `presubmit.yml` file for each module version
(`/modules/$MODULE/$VERSION/presubmit.yml`). This file specifies a few essential
build and test targets that you can use to check the validity of this module
version. The BCR's CI pipelines also uses this to ensure interoperability
between modules.

## Selecting registries

The repeatable Bazel flag `--registry` can be used to specify the list of
registries to request modules from, so you can set up your project to fetch
dependencies from a third-party or internal registry. Earlier registries take
precedence. For convenience, you can put a list of `--registry` flags in the
`.bazelrc` file of your project.

If your registry is hosted on GitHub (for example, as a fork of
`bazelbuild/bazel-central-registry`) then your `--registry` value needs a raw
GitHub address under `raw.githubusercontent.com`. For example, on the `main`
branch of the `my-org` fork, you would set
`--registry=https://raw.githubusercontent.com/my-org/bazel-central-registry/main/`.

Using the `--registry` flag stops the Bazel Central Registry from being used by
default, but you can add it back by adding `--registry=https://bcr.bazel.build`.

[bcr-contribution-guidelines]: https://github.com/bazelbuild/bazel-central-registry/blob/main/docs/README.md
[bcr-repo]: https://github.com/bazelbuild/bazel-central-registry
[subresource-integrity]: https://w3c.github.io/webappsec-subresource-integrity/#integrity-metadata-description
