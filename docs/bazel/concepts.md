

Project: /_project.yaml
Book: /_book.yaml

# Visibility

{% include "_buttons.html" %}

This page covers Bazel's two visibility systems:
[target visibility](#target-visibility) and [load visibility](#load-visibility).

Both types of visibility help other developers distinguish between your
library's public API and its implementation details, and help enforce structure
as your workspace grows. You can also use visibility when deprecating a public
API to allow current users while denying new ones.

## Target visibility {:#target-visibility}

**Target visibility** controls who may depend on your target — that is, who may
use your target's label inside an attribute such as `deps`. A target will fail
to build during the [analysis](/reference/glossary#analysis-phase) phase if it
violates the visibility of one of its dependencies.

Generally, a target `A` is visible to a target `B` if they are in the same
location, or if `A` grants visibility to `B`'s location. In the absence of
[symbolic macros](/extending/macros), the term "location" can be simplified
to just "package"; see [below](#symbolic-macros) for more on symbolic macros.

Visibility is specified by listing allowed packages. Allowing a package does not
necessarily mean that its subpackages are also allowed. For more details on
packages and subpackages, see [Concepts and terminology](/concepts/build-ref).

For prototyping, you can disable target visibility enforcement by setting the
flag `--check_visibility=false`. This shouldn't be done for production usage in
submitted code.

The primary way to control visibility is with a rule's
[`visibility`](/reference/be/common-definitions#common.visibility) attribute.
The following subsections describe the attribute's format, how to apply it to
various kinds of targets, and the interaction between the visibility system and
symbolic macros.

### Visibility specifications {:#visibility-specifications}

All rule targets have a `visibility` attribute that takes a list of labels. Each
label has one of the following forms. With the exception of the last form, these
are just syntactic placeholders that don't correspond to any actual target.

*   `"//visibility:public"`: Grants access to all packages.

*   `"//visibility:private"`: Does not grant any additional access; only targets
    in this location's package can use this target.

*   `"//foo/bar:__pkg__"`: Grants access to `//foo/bar` (but not its
    subpackages).

*   `"//foo/bar:__subpackages__"`: Grants access to `//foo/bar` and all of its
    direct and indirect subpackages.

*   `"//some_pkg:my_package_group"`: Grants access to all of the packages that
    are part of the given [`package_group`](/reference/be/functions#package_group).

    *   Package groups use a
        [different syntax](/reference/be/functions#package_group.packages) for
        specifying packages. Within a package group, the forms
        `"//foo/bar:__pkg__"` and `"//foo/bar:__subpackages__"` are respectively
        replaced by `"//foo/bar"` and `"//foo/bar/..."`. Likewise,
        `"//visibility:public"` and `"//visibility:private"` are just `"public"`
        and `"private"`.

For example, if `//some/package:mytarget` has its `visibility` set to
`[":__subpackages__", "//tests:__pkg__"]`, then it could be used by any target
that is part of the `//some/package/...` source tree, as well as targets
declared in `//tests/BUILD`, but not by targets defined in
`//tests/integration/BUILD`.

**Best practice:** To make several targets visible to the same set
of packages, use a `package_group` instead of repeating the list in each
target's `visibility` attribute. This increases readability and prevents the
lists from getting out of sync.

**Best practice:** When granting visibility to another team's project, prefer
`__subpackages__` over `__pkg__` to avoid needless visibility churn as that
project evolves and adds new subpackages.

Note: The `visibility` attribute may not specify non-`package_group` targets.
Doing so triggers a "Label does not refer to a package group" or "Cycle in
dependency graph" error.

### Rule target visibility {:#rule-target-visibility}

A rule target's visibility is determined by taking its `visibility` attribute
-- or a suitable default if not given -- and appending the location where the
target was declared. For targets not declared in a symbolic macro, if the
package specifies a [`default_visibility`](/reference/be/functions#package.default_visibility),
this default is used; for all other packages and for targets declared in a
symbolic macro, the default is just `["//visibility:private"]`.

```starlark
# //mypkg/BUILD

package(default_visibility = ["//friend:__pkg__"])

cc_library(
    name = "t1",
    ...
    # No visibility explicitly specified.
    # Effective visibility is ["//friend:__pkg__", "//mypkg:__pkg__"].
    # If no default_visibility were given in package(...), the visibility would
    # instead default to ["//visibility:private"], and the effective visibility
    # would be ["//mypkg:__pkg__"].
)

cc_library(
    name = "t2",
    ...
    visibility = [":clients"],
    # Effective visibility is ["//mypkg:clients, "//mypkg:__pkg__"], which will
    # expand to ["//another_friend:__subpackages__", "//mypkg:__pkg__"].
)

cc_library(
    name = "t3",
    ...
    visibility = ["//visibility:private"],
    # Effective visibility is ["//mypkg:__pkg__"]
)

package_group(
    name = "clients",
    packages = ["//another_friend/..."],
)
```

**Best practice:** Avoid setting `default_visibility` to public. It may be
convenient for prototyping or in small codebases, but the risk of inadvertently
creating public targets increases as the codebase grows. It's better to be
explicit about which targets are part of a package's public interface.

### Generated file target visibility {:#generated-file-target-visibility}

A generated file target has the same visibility as the rule target that
generates it.

```starlark
# //mypkg/BUILD

java_binary(
    name = "foo",
    ...
    visibility = ["//friend:__pkg__"],
)
```

```starlark
# //friend/BUILD

some_rule(
    name = "bar",
    deps = [
        # Allowed directly by visibility of foo.
        "//mypkg:foo",
        # Also allowed. The java_binary's "_deploy.jar" implicit output file
        # target the same visibility as the rule target itself.
        "//mypkg:foo_deploy.jar",
    ]
    ...
)
```

### Source file target visibility {:#source-file-target-visibility}

Source file targets can either be explicitly declared using
[`exports_files`](/reference/be/functions#exports_files), or implicitly created
by referring to their filename in a label attribute of a rule (outside of a
symbolic macro). As with rule targets, the location of the call to
`exports_files`, or the BUILD file that referred to the input file, is always
automatically appended to the file's visibility.

Files declared by `exports_files` can have their visibility set by the
`visibility` parameter to that function. If this parameter is not given, the visibility is public.

Note: `exports_files` may not be used to override the visibility of a generated
file.

For files that do not appear in a call to `exports_files`, the visibility
depends on the value of the flag
[`--incompatible_no_implicit_file_export`](https://github.com/bazelbuild/bazel/issues/10225){: .external}:

*   If the flag is true, the visibility is private.

*   Else, the legacy behavior applies: The visibility is the same as the
    `BUILD` file's `default_visibility`, or private if a default visibility is
    not specified.

Avoid relying on the legacy behavior. Always write an `exports_files`
declaration whenever a source file target needs non-private visibility.

**Best practice:** When possible, prefer to expose a rule target rather than a
source file. For example, instead of calling `exports_files` on a `.java` file,
wrap the file in a non-private `java_library` target. Generally, rule targets
should only directly reference source files that live in the same package.

#### Example {:#source-file-visibility-example}

File `//frobber/data/BUILD`:

```starlark
exports_files(["readme.txt"])
```

File `//frobber/bin/BUILD`:

```starlark
cc_binary(
  name = "my-program",
  data = ["//frobber/data:readme.txt"],
)
```

### Config setting visibility {:#config-setting-visibility}

Historically, Bazel has not enforced visibility for
[`config_setting`](/reference/be/general#config_setting) targets that are
referenced in the keys of a [`select()`](/reference/be/functions#select). There
are two flags to remove this legacy behavior:

*   [`--incompatible_enforce_config_setting_visibility`](https://github.com/bazelbuild/bazel/issues/12932){: .external}
    enables visibility checking for these targets. To assist with migration, it
    also causes any `config_setting` that does not specify a `visibility` to be
    considered public (regardless of package-level `default_visibility`).

*   [`--incompatible_config_setting_private_default_visibility`](https://github.com/bazelbuild/bazel/issues/12933){: .external}
    causes `config_setting`s that do not specify a `visibility` to respect the
    package's `default_visibility` and to fallback on private visibility, just
    like any other rule target. It is a no-op if
    `--incompatible_enforce_config_setting_visibility` is not set.

Avoid relying on the legacy behavior. Any `config_setting` that is intended to
be used outside the current package should have an explicit `visibility`, if the
package does not already specify a suitable `default_visibility`.

### Package group target visibility {:#package-group-target-visibility}

`package_group` targets do not have a `visibility` attribute. They are always
publicly visible.

### Visibility of implicit dependencies {:#visibility-implicit-dependencies}

Some rules have [implicit dependencies](/extending/rules#private_attributes_and_implicit_dependencies) —
dependencies that are not spelled out in a `BUILD` file but are inherent to
every instance of that rule. For example, a `cc_library` rule might create an
implicit dependency from each of its rule targets to an executable target
representing a C++ compiler.

The visibility of such an implicit dependency is checked with respect to the
package containing the `.bzl` file in which the rule (or aspect) is defined. In
our example, the C++ compiler could be private so long as it lives in the same
package as the definition of the `cc_library` rule. As a fallback, if the
implicit dependency is not visible from the definition, it is checked with
respect to the `cc_library` target.

If you want to restrict the usage of a rule to certain packages, use
[load visibility](#load-visibility) instead.

### Visibility and symbolic macros {:#symbolic-macros}

This section describes how the visibility system interacts with
[symbolic macros](/extending/macros).

#### Locations within symbolic macros {:#locations-within-symbolic-macros}

A key detail of the visibility system is how we determine the location of a
declaration. For targets that are not declared in a symbolic macro, the location
is just the package where the target lives -- the package of the `BUILD` file.
But for targets created in a symbolic macro, the location is the package
containing the `.bzl` file where the macro's definition (the
`my_macro = macro(...)` statement) appears. When a target is created inside
multiple nested targets, it is always the innermost symbolic macro's definition
that is used.

The same system is used to determine what location to check against a given
dependency's visibility. If the consuming target was created inside a macro, we
look at the innermost macro's definition rather than the package the consuming
target lives in.

This means that all macros whose code is defined in the same package are
automatically "friends" with one another. Any target directly created by a macro
defined in `//lib:defs.bzl` can be seen from any other macro defined in `//lib`,
regardless of what packages the macros are actually instantiated in. Likewise,
they can see, and can be seen by, targets declared directly in `//lib/BUILD` and
its legacy macros. Conversely, targets that live in the same package cannot
necessarily see one another if at least one of them is created by a symbolic
macro.

Within a symbolic macro's implementation function, the `visibility` parameter
has the effective value of the macro's `visibility` attribute after appending
the location where the macro was called. The standard way for a macro to export
one of its targets to its caller is to forward this value along to the target's
declaration, as in `some_rule(..., visibility = visibility)`. Targets that omit
this attribute won't be visible to the caller of the macro unless the caller
happens to be in the same package as the macro definition. This behavior
composes, in the sense that a chain of nested calls to submacros may each pass
`visibility = visibility`, re-exporting the inner macro's exported targets to
the caller at each level, without exposing any of the macros' implementation
details.

#### Delegating privileges to a submacro {:#delegating-privileges-to-a-submacro}

The visibility model has a special feature to allow a macro to delegate its
permissions to a submacro. This is important for factoring and composing macros.

Suppose you have a macro `my_macro` that creates a dependency edge using a rule
`some_library` from another package:

```starlark
# //macro/defs.bzl
load("//lib:defs.bzl", "some_library")

def _impl(name, visibility, ...):
    ...
    native.genrule(
        name = name + "_dependency"
        ...
    )
    some_library(
        name = name + "_consumer",
        deps = [name + "_dependency"],
        ...
    )

my_macro = macro(implementation = _impl, ...)
```

```starlark
# //pkg/BUILD

load("//macro:defs.bzl", "my_macro")

my_macro(name = "foo", ...)
```

The `//pkg:foo_dependency` target has no `visibility` specified, so it is only
visible within `//macro`, which works fine for the consuming target. Now, what
happens if the author of `//lib` refactors `some_library` to instead be
implemented using a macro?

```starlark
# //lib:defs.bzl

def _impl(name, visibility, deps, ...):
    some_rule(
        # Main target, exported.
        name = name,
        visibility = visibility,
        deps = deps,
        ...)

some_library = macro(implementation = _impl, ...)
```

With this change, `//pkg:foo_consumer`'s location is now `//lib` rather than
`//macro`, so its usage of `//pkg:foo_dependency` violates the dependency's
visibility. The author of `my_macro` can't be expected to pass
`visibility = ["//lib"]` to the declaration of the dependency just to work
around this implementation detail.

For this reason, when a dependency of a target is also an attribute value of the
macro that declared the target, we check the dependency's visibility against the
location of the macro instead of the location of the consuming target.

In this example, to validate whether `//pkg:foo_consumer` can see
`//pkg:foo_dependency`, we see that `//pkg:foo_dependency` was also passed as an
input to the call to `some_library` inside of `my_macro`, and instead check the
dependency's visibility against the location of this call, `//macro`.

This process can repeat recursively, as long as a target or macro declaration is
inside of another symbolic macro taking the dependency's label in one of its
label-typed attributes.

Note: Visibility delegation does not work for labels that were not passed into
the macro, such as labels derived by string manipulation.

#### Finalizers {:#finalizers}

Targets declared in a rule finalizer (a symbolic macro with `finalizer = True`),
in addition to seeing targets following the usual symbolic macro visibility
rules, can *also* see all targets which are visible to the finalizer target's
package.

In other words, if you migrate a `native.existing_rules()`-based legacy macro to
a finalizer, the targets declared by the finalizer will still be able to see
their old dependencies.

It is possible to define targets that a finalizer can introspect using
`native.existing_rules()`, but which it cannot use as dependencies under the
visibility system. For example, if a macro-defined target is not visible to its
own package or to the finalizer macro's definition, and is not delegated to the
finalizer, the finalizer cannot see such a target. Note, however, that a
`native.existing_rules()`-based legacy macro will also be unable to see such a
target.

## Load visibility {:#load-visibility}

**Load visibility** controls whether a `.bzl` file may be loaded from other
`BUILD` or `.bzl` files outside the current package.

In the same way that target visibility protects source code that is encapsulated
by targets, load visibility protects build logic that is encapsulated by `.bzl`
files. For instance, a `BUILD` file author might wish to factor some repetitive
target declarations into a macro in a `.bzl` file. Without the protection of
load visibility, they might find their macro reused by other collaborators in
the same workspace, so that modifying the macro breaks other teams' builds.

Note that a `.bzl` file may or may not have a corresponding source file target.
If it does, there is no guarantee that the load visibility and the target
visibility coincide. That is, the same `BUILD` file might be able to load the
`.bzl` file but not list it in the `srcs` of a [`filegroup`](/reference/be/general#filegroup),
or vice versa. This can sometimes cause problems for rules that wish to consume
`.bzl` files as source code, such as for documentation generation or testing.

For prototyping, you may disable load visibility enforcement by setting
`--check_bzl_visibility=false`. As with `--check_visibility=false`, this should
not be done for submitted code.

Load visibility is available as of Bazel 6.0.

### Declaring load visibility {:#declaring-load-visibility}

To set the load visibility of a `.bzl` file, call the
[`visibility()`](/rules/lib/globals/bzl#visibility) function from within the file.
The argument to `visibility()` is a list of package specifications, just like
the [`packages`](/reference/be/functions#package_group.packages) attribute of
`package_group`. However, `visibility()` does not accept negative package
specifications.

The call to `visibility()` must only occur once per file, at the top level (not
inside a function), and ideally immediately following the `load()` statements.

Unlike target visibility, the default load visibility is always public. Files
that do not call `visibility()` are always loadable from anywhere in the
workspace. It is a good idea to add `visibility("private")` to the top of any
new `.bzl` file that is not specifically intended for use outside the package.

### Example {:#load-visibility-example}

```starlark
# //mylib/internal_defs.bzl

# Available to subpackages and to mylib's tests.
visibility(["//mylib/...", "//tests/mylib/..."])

def helper(...):
    ...
```

```starlark
# //mylib/rules.bzl

load(":internal_defs.bzl", "helper")
# Set visibility explicitly, even though public is the default.
# Note the [] can be omitted when there's only one entry.
visibility("public")

myrule = rule(
    ...
)
```

```starlark
# //someclient/BUILD

load("//mylib:rules.bzl", "myrule")          # ok
load("//mylib:internal_defs.bzl", "helper")  # error

...
```

### Load visibility practices {:#load-visibility-practices}

This section describes tips for managing load visibility declarations.

#### Factoring visibilities {:#factoring-visibilities}

When multiple `.bzl` files should have the same visibility, it can be helpful to
factor their package specifications into a common list. For example:

```starlark
# //mylib/internal_defs.bzl

visibility("private")

clients = [
    "//foo",
    "//bar/baz/...",
    ...
]
```

```starlark
# //mylib/feature_A.bzl

load(":internal_defs.bzl", "clients")
visibility(clients)

...
```

```starlark
# //mylib/feature_B.bzl

load(":internal_defs.bzl", "clients")
visibility(clients)

...
```

This helps prevent accidental skew between the various `.bzl` files'
visibilities. It also is more readable when the `clients` list is large.

#### Composing visibilities {:#composing-visibilities}

Sometimes a `.bzl` file might need to be visible to an allowlist that is
composed of multiple smaller allowlists. This is analogous to how a
`package_group` can incorporate other `package_group`s via its
[`includes`](/reference/be/functions#package_group.includes) attribute.

Suppose you are deprecating a widely used macro. You want it to be visible only
to existing users and to the packages owned by your own team. You might write:

```starlark
# //mylib/macros.bzl

load(":internal_defs.bzl", "our_packages")
load("//some_big_client:defs.bzl", "their_remaining_uses")

# List concatenation. Duplicates are fine.
visibility(our_packages + their_remaining_uses)
```

#### Deduplicating with package groups {:#deduplicating-with-package-groups}

Unlike target visibility, you cannot define a load visibility in terms of a
`package_group`. If you want to reuse the same allowlist for both target
visibility and load visibility, it's best to move the list of package
specifications into a .bzl file, where both kinds of declarations may refer to
it. Building off the example in [Factoring visibilities](#factoring-visibilities)
above, you might write:

```starlark
# //mylib/BUILD

load(":internal_defs", "clients")

package_group(
    name = "my_pkg_grp",
    packages = clients,
)
```

This only works if the list does not contain any negative package
specifications.

#### Protecting individual symbols {:#protecting-individual-symbols}

Any Starlark symbol whose name begins with an underscore cannot be loaded from
another file. This makes it easy to create private symbols, but does not allow
you to share these symbols with a limited set of trusted files. On the other
hand, load visibility gives you control over what other packages may see your
`.bzl file`, but does not allow you to prevent any non-underscored symbol from
being loaded.

Luckily, you can combine these two features to get fine-grained control.

```starlark
# //mylib/internal_defs.bzl

# Can't be public, because internal_helper shouldn't be exposed to the world.
visibility("private")

# Can't be underscore-prefixed, because this is
# needed by other .bzl files in mylib.
def internal_helper(...):
    ...

def public_util(...):
    ...
```

```starlark
# //mylib/defs.bzl

load(":internal_defs", "internal_helper", _public_util="public_util")
visibility("public")

# internal_helper, as a loaded symbol, is available for use in this file but
# can't be imported by clients who load this file.
...

# Re-export public_util from this file by assigning it to a global variable.
# We needed to import it under a different name ("_public_util") in order for
# this assignment to be legal.
public_util = _public_util
```

#### bzl-visibility Buildifier lint {:#bzl-visibility-buildifier-lint}

There is a [Buildifier lint](https://github.com/bazelbuild/buildtools/blob/master/WARNINGS.md#bzl-visibility)
that provides a warning if users load a file from a directory named `internal`
or `private`, when the user's file is not itself underneath the parent of that
directory. This lint predates the load visibility feature and is unnecessary in
workspaces where `.bzl` files declare visibilities.


Project: /_project.yaml
Book: /_book.yaml

# BUILD files

{% include "_buttons.html" %}

The previous sections described packages, targets and labels, and the
build dependency graph abstractly. This section describes the concrete syntax
used to define a package.

By definition, every package contains a `BUILD` file, which is a short
program.

Note: The `BUILD` file can be named either `BUILD` or `BUILD.bazel`. If both
files exist, `BUILD.bazel` takes precedence over `BUILD`.
For simplicity's sake, the documentation refers to these files simply as `BUILD`
files.

`BUILD` files are evaluated using an imperative language,
[Starlark](https://github.com/bazelbuild/starlark/){: .external}.

They are interpreted as a sequential list of statements.

In general, order does matter: variables must be defined before they are
used, for example. However, most `BUILD` files consist only of declarations of
build rules, and the relative order of these statements is immaterial; all
that matters is _which_ rules were declared, and with what values, by the
time package evaluation completes.

When a build rule function, such as `cc_library`, is executed, it creates a
new target in the graph. This target can later be referred using a label.

In simple `BUILD` files, rule declarations can be re-ordered freely without
changing the behavior.

To encourage a clean separation between code and data, `BUILD` files cannot
contain function definitions, `for` statements or `if` statements (but list
comprehensions and `if` expressions are allowed). Functions can be declared in
`.bzl` files instead. Additionally, `*args` and `**kwargs` arguments are not
allowed in `BUILD` files; instead list all the arguments explicitly.

Crucially, programs in Starlark can't perform arbitrary I/O. This invariant
makes the interpretation of `BUILD` files hermetic — dependent only on a known
set of inputs, which is essential for ensuring that builds are reproducible.
For more details, see [Hermeticity](/basics/hermeticity).

Because `BUILD` files need to be updated whenever the dependencies of the
underlying code change, they are typically maintained by multiple people on a
team. `BUILD` file authors should comment liberally to document the role
of each build target, whether or not it is intended for public use, and to
document the role of the package itself.

## Loading an extension {:#load}

Bazel extensions are files ending in `.bzl`. Use the `load` statement to import
a symbol from an extension.

```
load("//foo/bar:file.bzl", "some_library")
```

This code loads the file `foo/bar/file.bzl` and adds the `some_library` symbol
to the environment. This can be used to load new rules, functions, or constants
(for example, a string or a list). Multiple symbols can be imported by using
additional arguments to the call to `load`. Arguments must be string literals
(no variable) and `load` statements must appear at top-level — they cannot be
in a function body.

The first argument of `load` is a [label](/concepts/labels) identifying a
`.bzl` file. If it's a relative label, it is resolved with respect to the
package (not directory) containing the current `bzl` file. Relative labels in
`load` statements should use a leading `:`.

`load` also supports aliases, therefore, you can assign different names to the
imported symbols.

```
load("//foo/bar:file.bzl", library_alias = "some_library")
```

You can define multiple aliases within one `load` statement. Moreover, the
argument list can contain both aliases and regular symbol names. The following
example is perfectly legal (please note when to use quotation marks).

```
load(":my_rules.bzl", "some_rule", nice_alias = "some_other_rule")
```

In a `.bzl` file, symbols starting with `_` are not exported and cannot be
loaded from another file.

You can use [load visibility](/concepts/visibility#load-visibility) to restrict
who may load a `.bzl` file.

## Types of build rules {:#types-of-build-rules}

The majority of build rules come in families, grouped together by
language. For example, `cc_binary`, `cc_library`
and `cc_test` are the build rules for C++ binaries,
libraries, and tests, respectively. Other languages use the same
naming scheme, with a different prefix, such as `java_*` for
Java. Some of these functions are documented in the
[Build Encyclopedia](/reference/be/overview), but it is possible
for anyone to create new rules.

* `*_binary` rules build executable programs in a given language. After a
  build, the executable will reside in the build tool's binary
  output tree at the corresponding name for the rule's label,
  so `//my:program` would appear at (for example) `$(BINDIR)/my/program`.

  In some languages, such rules also create a runfiles directory
  containing all the files mentioned in a `data`
  attribute belonging to the rule, or any rule in its transitive
  closure of dependencies; this set of files is gathered together in
  one place for ease of deployment to production.

* `*_test` rules are a specialization of a `*_binary` rule, used for automated
  testing. Tests are simply programs that return zero on success.

  Like binaries, tests also have runfiles trees, and the files
  beneath it are the only files that a test may legitimately open
  at runtime. For example, a program `cc_test(name='x',
  data=['//foo:bar'])` may open and read `$TEST_SRCDIR/workspace/foo/bar` during execution.
  (Each programming language has its own utility function for
  accessing the value of `$TEST_SRCDIR`, but they are all
  equivalent to using the environment variable directly.)
  Failure to observe the rule will cause the test to fail when it is
  executed on a remote testing host.

* `*_library` rules specify separately-compiled modules in the given
    programming language. Libraries can depend on other libraries,
    and binaries and tests can depend on libraries, with the expected
    separate-compilation behavior.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/labels">
        <span class="material-icons" aria-hidden="true">arrow_back</span>Labels</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/dependencies">
        Dependencies<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>

## File encoding

`BUILD` and `.bzl` files should be encoded in UTF-8, of which ASCII is a valid
subset. Arbitrary byte sequences are currently allowed, but may stop being
supported in the future.


Project: /_project.yaml
Book: /_book.yaml

# Dependencies

{% include "_buttons.html" %}

A target `A` _depends upon_ a target `B` if `B` is needed by `A` at build or
execution time. The _depends upon_ relation induces a
[Directed Acyclic Graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph){: .external}
(DAG) over targets, and it is called a _dependency graph_.

A target's _direct_ dependencies are those other targets reachable by a path
of length 1 in the dependency graph. A target's _transitive_ dependencies are
those targets upon which it depends via a path of any length through the graph.

In fact, in the context of builds, there are two dependency graphs, the graph
of _actual dependencies_ and the graph of _declared dependencies_. Most of the
time, the two graphs are so similar that this distinction need not be made, but
it is useful for the discussion below.

## Actual and declared dependencies {:#actual-and-declared-dependencies}

A target `X` is _actually dependent_ on target `Y` if `Y` must be present,
built, and up-to-date in order for `X` to be built correctly. _Built_ could
mean generated, processed, compiled, linked, archived, compressed, executed, or
any of the other kinds of tasks that routinely occur during a build.

A target `X` has a _declared dependency_ on target `Y` if there is a dependency
edge from `X` to `Y` in the package of `X`.

For correct builds, the graph of actual dependencies _A_ must be a subgraph of
the graph of declared dependencies _D_. That is, every pair of
directly-connected nodes `x --> y` in _A_ must also be directly connected in
_D_. It can be said that _D_ is an _overapproximation_ of _A_.

Important: _D_ should not be too much of an overapproximation of _A_ because
redundant declared dependencies can make builds slower and binaries larger.

`BUILD` file writers must explicitly declare all of the actual direct
dependencies for every rule to the build system, and no more.

Failure to observe this principle causes undefined behavior: the build may fail,
but worse, the build may depend on some prior operations, or upon transitive
declared dependencies the target happens to have. Bazel checks for missing
dependencies and report errors, but it's not possible for this checking to be
complete in all cases.

You need not (and should not) attempt to list everything indirectly imported,
even if it is _needed_ by `A` at execution time.

During a build of target `X`, the build tool inspects the entire transitive
closure of dependencies of `X` to ensure that any changes in those targets are
reflected in the final result, rebuilding intermediates as needed.

The transitive nature of dependencies leads to a common mistake. Sometimes,
code in one file may use code provided by an _indirect_ dependency — a
transitive but not direct edge in the declared dependency graph. Indirect
dependencies don't appear in the `BUILD` file. Because the rule doesn't
directly depend on the provider, there is no way to track changes, as shown in
the following example timeline:

### 1. Declared dependencies match actual dependencies {:#this-is-fine}

At first, everything works. The code in package `a` uses code in package `b`.
The code in package `b` uses code in package `c`, and thus `a` transitively
depends on `c`.

<table class="cyan">
  <tr>
    <th><code>a/BUILD</code></th>
    <th><code><strong>b</strong>/BUILD</code></th>
  </tr>
  <tr>
    <td>
      <pre>rule(
    name = "a",
    srcs = "a.in",
    deps = "//b:b",
)
      </pre>
    </td>
    <td>
      <pre>
rule(
    name = "b",
    srcs = "b.in",
    deps = "//c:c",
)
      </pre>
    </td>
  </tr>
  <tr class="alt">
    <td><code>a / a.in</code></td>
    <td><code>b / b.in</code></td>
  </tr>
  <tr>
    <td><pre>
import b;
b.foo();
    </pre>
    </td>
    <td>
      <pre>
import c;
function foo() {
  c.bar();
}
      </pre>
    </td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Declared dependency graph with arrows connecting a, b, and c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Actual dependency graph that matches the declared dependency
                  graph with arrows connecting a, b, and c">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependencies overapproximate the actual dependencies. All is well.

### 2. Adding an undeclared dependency {:#undeclared-dependency}

A latent hazard is introduced when someone adds code to `a` that creates a
direct _actual_ dependency on `c`, but forgets to declare it in the build file
`a/BUILD`.

<table class="cyan">
  <tr>
    <th><code>a / a.in</code></th>
    <th>&nbsp;</th>
  </tr>
  <tr>
    <td>
      <pre>
        import b;
        import c;
        b.foo();
        c.garply();
      </pre>
    </td>
    <td>&nbsp;</td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Declared dependency graph with arrows connecting a, b, and c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_c_ac.svg"
             alt="Actual dependency graph with arrows connecting a, b, and c. An
                  arrow now connects A to C as well. This does not match the
                  declared dependency graph">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependencies no longer overapproximate the actual dependencies.
This may build ok, because the transitive closures of the two graphs are equal,
but masks a problem: `a` has an actual but undeclared dependency on `c`.

### 3. Divergence between declared and actual dependency graphs {:#divergence}

The hazard is revealed when someone refactors `b` so that it no longer depends on
`c`, inadvertently breaking `a` through no
fault of their own.

<table class="cyan">
  <tr>
    <th>&nbsp;</th>
    <th><code><strong>b</strong>/BUILD</code></th>
  </tr>
  <tr>
    <td>&nbsp;</td>
    <td>
      <pre>rule(
    name = "b",
    srcs = "b.in",
    <strong>deps = "//d:d",</strong>
)
      </pre>
    </td>
  </tr>
  <tr class="alt">
    <td>&nbsp;</td>
    <td><code>b / b.in</code></td>
  </tr>
  <tr>
    <td>&nbsp;</td>
    <td>
      <pre>
      import d;
      function foo() {
        d.baz();
      }
      </pre>
    </td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/ab_c.svg"
             alt="Declared dependency graph with arrows connecting a and b.
                  b no longer connects to c, which breaks a's connection to c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_a_c.svg"
             alt="Actual dependency graph that shows a connecting to b and c,
                  but b no longer connects to c">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependency graph is now an underapproximation of the actual
dependencies, even when transitively closed; the build is likely to fail.

The problem could have been averted by ensuring that the actual dependency from
`a` to `c` introduced in Step 2 was properly declared in the `BUILD` file.

## Types of dependencies {:#types-of-dependencies}

Most build rules have three attributes for specifying different kinds of
generic dependencies: `srcs`, `deps` and `data`. These are explained below. For
more details, see
[Attributes common to all rules](/reference/be/common-definitions).

Many rules also have additional attributes for rule-specific kinds of
dependencies, for example, `compiler` or `resources`. These are detailed in the
[Build Encyclopedia](/reference/be/).

### `srcs` dependencies {:#srcs-dependencies}

Files consumed directly by the rule or rules that output source files.

### `deps` dependencies {:#deps-dependencies}

Rule pointing to separately-compiled modules providing header files,
symbols, libraries, data, etc.

### `data` dependencies {:#data-dependencies}

A build target might need some data files to run correctly. These data files
aren't source code: they don't affect how the target is built. For example, a
unit test might compare a function's output to the contents of a file. When you
build the unit test you don't need the file, but you do need it when you run
the test. The same applies to tools that are launched during execution.

The build system runs tests in an isolated directory where only files listed as
`data` are available. Thus, if a binary/library/test needs some files to run,
specify them (or a build rule containing them) in `data`. For example:

```
# I need a config file from a directory named env:
java_binary(
    name = "setenv",
    ...
    data = [":env/default_env.txt"],
)

# I need test data from another directory
sh_test(
    name = "regtest",
    srcs = ["regtest.sh"],
    data = [
        "//data:file1.txt",
        "//data:file2.txt",
        ...
    ],
)
```

These files are available using the relative path `path/to/data/file`. In tests,
you can refer to these files by joining the paths of the test's source
directory and the workspace-relative path, for example,
`${TEST_SRCDIR}/workspace/path/to/data/file`.

## Using labels to reference directories {:#using-labels-reference-directories}

As you look over our `BUILD` files, you might notice that some `data` labels
refer to directories. These labels end with `/.` or `/` like these examples,
which you should not use:

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["//data/regression:unittest/."]</code>
</p>

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["testdata/."]</code>
</p>

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["testdata/"]</code>
</p>


This seems convenient, particularly for tests because it allows a test to
use all the data files in the directory.

But try not to do this. In order to ensure correct incremental rebuilds (and
re-execution of tests) after a change, the build system must be aware of the
complete set of files that are inputs to the build (or test). When you specify
a directory, the build system performs a rebuild only when the directory itself
changes (due to addition or deletion of files), but won't be able to detect
edits to individual files as those changes don't affect the enclosing directory.
Rather than specifying directories as inputs to the build system, you should
enumerate the set of files contained within them, either explicitly or using the
[`glob()`](/reference/be/functions#glob) function. (Use `**` to force the
`glob()` to be recursive.)


<p><span class="compare-better">Recommended</span> —
  <code>data = glob(["testdata/**"])</code>
</p>

Unfortunately, there are some scenarios where directory labels must be used.
For example, if the `testdata` directory contains files whose names don't
conform to the [label syntax](/concepts/labels#labels-lexical-specification),
then explicit enumeration of files, or use of the
[`glob()`](/reference/be/functions#glob) function produces an invalid labels
error. You must use directory labels in this case, but beware of the
associated risk of incorrect rebuilds described above.

If you must use directory labels, keep in mind that you can't refer to the
parent package with a relative `../` path; instead, use an absolute path like
`//data/regression:unittest/.`.

Note: Directory labels are only valid for data dependencies. If you try to use
a directory as a label in an argument other than `data`, it will fail and you
will get a (probably cryptic) error message.

Any external rule, such as a test, that needs to use multiple files must
explicitly declare its dependence on all of them. You can use `filegroup()` to
group files together in the `BUILD` file:

```
filegroup(
        name = 'my_data',
        srcs = glob(['my_unittest_data/*'])
)
```

You can then reference the label `my_data` as the data dependency in your test.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-files">
        <span class="material-icons" aria-hidden="true">arrow_back</span>BUILD files</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/visibility">
        Visibility<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>



Project: /_project.yaml
Book: /_book.yaml

# Repositories, workspaces, packages, and targets

{% include "_buttons.html" %}

Bazel builds software from source code organized in directory trees called
repositories. A defined set of repositories comprises the workspace. Source
files in repositories are organized in a nested hierarchy of packages, where
each package is a directory that contains a set of related source files and one
`BUILD` file. The `BUILD` file specifies what software outputs can be built from
the source.

### Repositories {:#repositories}

Source files used in a Bazel build are organized in _repositories_ (often
shortened to _repos_). A repo is a directory tree with a boundary marker file at
its root; such a boundary marker file could be `MODULE.bazel`, `REPO.bazel`, or
in legacy contexts, `WORKSPACE` or `WORKSPACE.bazel`.

The repo in which the current Bazel command is being run is called the _main
repo_. Other, (external) repos are defined by _repo rules_; see [external
dependencies overview](/external/overview) for more information.

## Workspace {:#workspace}

A _workspace_ is the environment shared by all Bazel commands run from the same
main repo. It encompasses the main repo and the set of all defined external
repos.

Note that historically the concepts of "repository" and "workspace" have been
conflated; the term "workspace" has often been used to refer to the main
repository, and sometimes even used as a synonym of "repository".

## Packages {:#packages}

The primary unit of code organization in a repository is the _package_. A
package is a collection of related files and a specification of how they can be
used to produce output artifacts.

A package is defined as a directory containing a
[`BUILD` file](/concepts/build-files) named either `BUILD` or `BUILD.bazel`. A
package includes all files in its directory, plus all subdirectories beneath it,
except those which themselves contain a `BUILD` file. From this definition, no
file or directory may be a part of two different packages.

For example, in the following directory tree there are two packages, `my/app`,
and the subpackage `my/app/tests`. Note that `my/app/data` is not a package, but
a directory belonging to package `my/app`.

```
src/my/app/BUILD
src/my/app/app.cc
src/my/app/data/input.txt
src/my/app/tests/BUILD
src/my/app/tests/test.cc
```

## Targets {:#targets}

A package is a container of _targets_, which are defined in the package's
`BUILD` file. Most targets are one of two principal kinds, _files_ and _rules_.

Files are further divided into two kinds. _Source files_ are usually written by
the efforts of people, and checked in to the repository. _Generated files_,
sometimes called derived files or output files, are not checked in, but are
generated from source files.

The second kind of target is declared with a _rule_. Each rule instance
specifies the relationship between a set of input and a set of output files. The
inputs to a rule may be source files, but they also may be the outputs of other
rules.

Whether the input to a rule is a source file or a generated file is in most
cases immaterial; what matters is only the contents of that file. This fact
makes it easy to replace a complex source file with a generated file produced by
a rule, such as happens when the burden of manually maintaining a highly
structured file becomes too tiresome, and someone writes a program to derive it.
No change is required to the consumers of that file. Conversely, a generated
file may easily be replaced by a source file with only local changes.

The inputs to a rule may also include _other rules_. The precise meaning of such
relationships is often quite complex and language- or rule-dependent, but
intuitively it is simple: a C++ library rule A might have another C++ library
rule B for an input. The effect of this dependency is that B's header files are
available to A during compilation, B's symbols are available to A during
linking, and B's runtime data is available to A during execution.

An invariant of all rules is that the files generated by a rule always belong to
the same package as the rule itself; it is not possible to generate files into
another package. It is not uncommon for a rule's inputs to come from another
package, though.

Package groups are sets of packages whose purpose is to limit accessibility of
certain rules. Package groups are defined by the `package_group` function. They
have three properties: the list of packages they contain, their name, and other
package groups they include. The only allowed ways to refer to them are from the
`visibility` attribute of rules or from the `default_visibility` attribute of
the `package` function; they do not generate or consume files. For more
information, refer to the [`package_group`
documentation](/reference/be/functions#package_group).

<a class="button button-with-icon button-primary" href="/concepts/labels">
  Labels<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span>
</a>

Project: /_project.yaml
Book: /_book.yaml

# Migrating to Platforms

{% include "_buttons.html" %}

Bazel has sophisticated [support](#background) for modeling
[platforms][Platforms] and [toolchains][Toolchains] for multi-architecture and
cross-compiled builds.

This page summarizes the state of this support.

Key Point: Bazel's platform and toolchain APIs are available today. Not all
languages support them. Use these APIs with your project if you can. Bazel is
migrating all major languages so eventually all builds will be platform-based.

See also:

* [Platforms][Platforms]
* [Toolchains][Toolchains]
* [Background][Background]

## Status {:#status}

### C++ {:#cxx}

C++ rules use platforms to select toolchains when
`--incompatible_enable_cc_toolchain_resolution` is set.

This means you can configure a C++ project with:

```posix-terminal
bazel build //:my_cpp_project --platforms=//:myplatform
```

instead of the legacy:

```posix-terminal
bazel build //:my_cpp_project` --cpu=... --crosstool_top=...  --compiler=...
```

This will be enabled by default in Bazel 7.0 ([#7260](https://github.com/bazelbuild/bazel/issues/7260){: .external}).

To test your C++ project with platforms, see
[Migrating Your Project](#migrating-your-project) and
[Configuring C++ toolchains].

### Java {:#java}

Java rules use platforms to select toolchains.

This replaces legacy flags `--java_toolchain`, `--host_java_toolchain`,
`--javabase`, and `--host_javabase`.

See [Java and Bazel](/docs/bazel-and-java) for details.

### Android {:#android}

Android rules use platforms to select toolchains when
`--incompatible_enable_android_toolchain_resolution` is set.

This means you can configure an Android project with:

```posix-terminal
bazel build //:my_android_project --android_platforms=//:my_android_platform
```

instead of with legacy flags like  `--android_crosstool_top`, `--android_cpu`,
and `--fat_apk_cpu`.

This will be enabled by default in Bazel 7.0 ([#16285](https://github.com/bazelbuild/bazel/issues/16285){: .external}).

To test your Android project with platforms, see
[Migrating Your Project](#migrating-your-project).

### Apple {:#apple}

[Apple rules]{: .external} do not support platforms and are not yet scheduled
for support.

You can still use platform APIs with Apple builds (for example, when building
with a mixture of Apple rules and pure C++) with [platform
mappings](#platform-mappings).

### Other languages {:#other-languages}

* [Go rules]{: .external} fully support platforms
* [Rust rules]{: .external} fully support platforms.

If you own a language rule set, see [Migrating your rule set] for adding
support.

## Background {:#background}

*Platforms* and *toolchains* were introduced to standardize how software
projects target different architectures and cross-compile.

This was
[inspired][Inspiration]{: .external}
by the observation that language maintainers were already doing this in ad
hoc, incompatible ways. For example, C++ rules used `--cpu` and
 `--crosstool_top` to declare a target CPU and toolchain. Neither of these
correctly models a "platform". This produced awkward and incorrect builds.

Java, Android, and other languages evolved their own flags for similar purposes,
none of which interoperated with each other. This made cross-language builds
confusing and complicated.

Bazel is intended for large, multi-language, multi-platform projects. This
demands more principled support for these concepts, including a clear
standard API.

### Need for migration {:#migration}

Upgrading to the new API requires two efforts: releasing the API and upgrading
rule logic to use it.

The first is done but the second is ongoing. This consists of ensuring
language-specific platforms and toolchains are defined, language logic reads
toolchains through the new API instead of old flags like `--crosstool_top`, and
`config_setting`s select on the new API instead of old flags.

This work is straightforward but requires a distinct effort for each language,
plus fair warning for project owners to test against upcoming changes.

This is why this is an ongoing migration.

### Goal {:#goal}

This migration is complete when all projects build with the form:

```posix-terminal
bazel build //:myproject --platforms=//:myplatform
```

This implies:

1. Your project's rules choose the right toolchains for `//:myplatform`.
1. Your project's dependencies choose the right toolchains for `//:myplatform`.
1. `//:myplatform` references
[common declarations][Common Platform Declarations]{: .external}
of `CPU`, `OS`, and other generic, language-independent properties
1. All relevant [`select()`s][select()] properly match `//:myplatform`.
1. `//:myplatform` is defined in a clear, accessible place: in your project's
repo if the platform is unique to your project, or some common place all
consuming projects can find it

Old flags like `--cpu`, `--crosstool_top`, and `--fat_apk_cpu` will be
deprecated and removed as soon as it's safe to do so.

Ultimately, this will be the *sole* way to configure architectures.


## Migrating your project {:#migrating-your-project}

If you build with languages that support platforms, your build should already
work with an invocation like:

```posix-terminal
bazel build //:myproject --platforms=//:myplatform
```

See [Status](#status) and your language's documentation for precise details.

If a language requires a flag to enable platform support, you also need to set
that flag. See [Status](#status) for details.

For your project to build, you need to check the following:

1. `//:myplatform` must exist. It's generally the project owner's responsibility
   to define platforms because different projects target different machines.
   See [Default platforms](#default-platforms).

1. The toolchains you want to use must exist. If using stock toolchains, the
   language owners should include instructions for how to register them. If
   writing your own custom toolchains, you need to [register](https://bazel.build/extending/toolchains#registering-building-toolchains) them in your
   `MODULE.bazel` file or with [`--extra_toolchains`](https://bazel.build/reference/command-line-reference#flag--extra_toolchains).

1. `select()`s and [configuration transitions][Starlark transitions] must
  resolve properly. See [select()](#select) and [Transitions](#transitions).

1. If your build mixes languages that do and don't support platforms, you may
   need platform mappings to help the legacy languages work with the new API.
   See [Platform mappings](#platform-mappings) for details.

If you still have problems, [reach out](#questions) for support.

### Default platforms {:#default-platforms}

Project owners should define explicit
[platforms][Defining Constraints and Platforms] to describe the architectures
they want to build for. These are then triggered with `--platforms`.

When `--platforms` isn't set, Bazel defaults to a `platform` representing the
local build machine. This is auto-generated at `@platforms//host` (aliased as
`@bazel_tools//tools:host_platform`)
so there's no need to explicitly define it. It maps the local machine's `OS`
and `CPU` with `constraint_value`s declared in
[`@platforms`](https://github.com/bazelbuild/platforms){: .external}.

### `select()` {:#select}

Projects can [`select()`][select()] on
[`constraint_value` targets][constraint_value Rule] but not complete
platforms. This is intentional so `select()` supports as wide a variety of
machines as possible. A library with `ARM`-specific sources should support *all*
`ARM`-powered machines unless there's reason to be more specific.

To select on one or more `constraint_value`s, use:

```python
config_setting(
    name = "is_arm",
    constraint_values = [
        "@platforms//cpu:arm",
    ],
)
```

This is equivalent to traditionally selecting on `--cpu`:

```python
config_setting(
    name = "is_arm",
    values = {
        "cpu": "arm",
    },
)
```

More details [here][select() Platforms].

`select`s on `--cpu`, `--crosstool_top`, etc. don't understand `--platforms`.
When migrating your project to platforms, you must either convert them to
`constraint_values` or use [platform mappings](#platform-mappings) to support
both styles during migration.

### Transitions {:#transitions}

[Starlark transitions][Starlark transitions] change
flags down parts of your build graph. If your project uses a transition that
sets `--cpu`, `--crossstool_top`, or other legacy flags, rules that read
`--platforms` won't see these changes.

When migrating your project to platforms, you must either convert changes like
`return { "//command_line_option:cpu": "arm" }` to `return {
"//command_line_option:platforms": "//:my_arm_platform" }` or use [platform
mappings](#platform-mappings) to support both styles during migration.
window.

## Migrating your rule set  {:#migrating-your-rule-set}

If you own a rule set and want to support platforms, you need to:

1. Have rule logic resolve toolchains with the toolchain API. See
   [toolchain API][Toolchains] (`ctx.toolchains`).

1. Optional: define an `--incompatible_enable_platforms_for_my_language` flag so
   rule logic alternately resolves toolchains through the new API or old flags
   like `--crosstool_top` during migration testing.

1. Define the relevant properties that make up platform components. See
   [Common platform properties](#common-platform-properties)

1. Define standard toolchains and make them accessible to users through your
   rule's registration instructions ([details](https://bazel.build/extending/toolchains#registering-building-toolchains))

1. Ensure [`select()`s](#select) and
   [configuration transitions](#transitions) support platforms. This is the
   biggest challenge. It's particularly challenging for multi-language projects
   (which may fail if *all* languages can't read `--platforms`).

If you need to mix with rules that don't support platforms, you may need
[platform mappings](#platform-mappings) to bridge the gap.

### Common platform properties {:#common-platform-properties}

Common, cross-language platform properties like `OS` and `CPU` should be
declared in [`@platforms`](https://github.com/bazelbuild/platforms){: .external}.
This encourages sharing, standardization, and cross-language compatibility.

Properties unique to your rules should be declared in your rule's repo. This
lets you maintain clear ownership over the specific concepts your rules are
responsible for.

If your rules use custom-purpose OSes or CPUs, these should be declared in your
rule's repo vs.
[`@platforms`](https://github.com/bazelbuild/platforms){: .external}.

## Platform mappings {:#platform-mappings}

*Platform mappings* is a temporary API that lets platform-aware logic mix with
legacy logic in the same build. This is a blunt tool that's only intended to
smooth incompatibilities with different migration timeframes.

Caution: Only use this if necessary, and expect to eventually  eliminate it.

A platform mapping is a map of either a `platform()` to a
corresponding set of legacy flags or the reverse. For example:

```python
platforms:
  # Maps "--platforms=//platforms:ios" to "--ios_multi_cpus=x86_64 --apple_platform_type=ios".
  //platforms:ios
    --ios_multi_cpus=x86_64
    --apple_platform_type=ios

flags:
  # Maps "--ios_multi_cpus=x86_64 --apple_platform_type=ios" to "--platforms=//platforms:ios".
  --ios_multi_cpus=x86_64
  --apple_platform_type=ios
    //platforms:ios

  # Maps "--cpu=darwin_x86_64 --apple_platform_type=macos" to "//platform:macos".
  --cpu=darwin_x86_64
  --apple_platform_type=macos
    //platforms:macos
```

Bazel uses this to guarantee all settings, both platform-based and
legacy, are consistently applied throughout the build, including through
[transitions](#transitions).

By default Bazel reads mappings from the `platform_mappings` file in your
workspace root. You can also set
`--platform_mappings=//:my_custom_mapping`.

See the [platform mappings design]{: .external} for details.

## API review {:#api-review}

A [`platform`][platform Rule] is a collection of
[`constraint_value` targets][constraint_value Rule]:

```python
platform(
    name = "myplatform",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:arm",
    ],
)
```

A [`constraint_value`][constraint_value Rule] is a machine
property. Values of the same "kind" are grouped under a common
[`constraint_setting`][constraint_setting Rule]:

```python
constraint_setting(name = "os")
constraint_value(
    name = "linux",
    constraint_setting = ":os",
)
constraint_value(
    name = "mac",
    constraint_setting = ":os",
)
```

A [`toolchain`][Toolchains] is a [Starlark rule][Starlark rule]. Its
attributes declare a language's tools (like `compiler =
"//mytoolchain:custom_gcc"`). Its [providers][Starlark Provider] pass
this information to rules that need to build with these tools.

Toolchains declare the `constraint_value`s of machines they can
[target][target_compatible_with Attribute]
(`target_compatible_with = ["@platforms//os:linux"]`) and machines their tools can
[run on][exec_compatible_with Attribute]
(`exec_compatible_with = ["@platforms//os:mac"]`).

When building `$ bazel build //:myproject --platforms=//:myplatform`, Bazel
automatically selects a toolchain that can run on the build machine and
build binaries for `//:myplatform`. This is known as *toolchain resolution*.

The set of available toolchains can be registered in the `MODULE.bazel` file
with [`register_toolchains`][register_toolchains Function] or at the
command line with [`--extra_toolchains`][extra_toolchains Flag].

For more information see [here][Toolchains].

## Questions {:#questions}

For general support and questions about the migration timeline, contact
[bazel-discuss]{: .external} or the owners of the appropriate rules.

For discussions on the design and evolution of the platform/toolchain APIs,
contact [bazel-dev]{: .external}.

## See also {:#see-also}

* [Configurable Builds - Part 1]{: .external}
* [Platforms]
* [Toolchains]
* [Bazel Platforms Cookbook]{: .external}
* [Platforms examples]{: .external}
* [Example C++ toolchain]{: .external}

[Android Rules]: /docs/bazel-and-android
[Apple Rules]: https://github.com/bazelbuild/rules_apple
[Background]: #background
[Bazel platforms Cookbook]: https://docs.google.com/document/d/1UZaVcL08wePB41ATZHcxQV4Pu1YfA1RvvWm8FbZHuW8/
[bazel-dev]: https://groups.google.com/forum/#!forum/bazel-dev
[bazel-discuss]: https://groups.google.com/forum/#!forum/bazel-discuss
[Common Platform Declarations]: https://github.com/bazelbuild/platforms
[constraint_setting Rule]: /reference/be/platforms-and-toolchains#constraint_setting
[constraint_value Rule]: /reference/be/platforms-and-toolchains#constraint_value
[Configurable Builds - Part 1]: https://blog.bazel.build/2019/02/11/configurable-builds-part-1.html
[Configuring C++ toolchains]: /tutorials/ccp-toolchain-config
[Defining Constraints and Platforms]: /extending/platforms#constraints-platforms
[Example C++ toolchain]: https://github.com/gregestren/snippets/tree/master/custom_cc_toolchain_with_platforms
[exec_compatible_with Attribute]: /reference/be/platforms-and-toolchains#toolchain.exec_compatible_with
[extra_toolchains Flag]: /reference/command-line-reference#flag--extra_toolchains
[Go Rules]: https://github.com/bazelbuild/rules_go
[Inspiration]: https://blog.bazel.build/2019/02/11/configurable-builds-part-1.html
[Migrating your rule set]: #migrating-your-rule-set
[Platforms]: /extending/platforms
[Platforms examples]: https://github.com/hlopko/bazel_platforms_examples
[platform mappings design]: https://docs.google.com/document/d/1Vg_tPgiZbSrvXcJ403vZVAGlsWhH9BUDrAxMOYnO0Ls/edit
[platform Rule]: /reference/be/platforms-and-toolchains#platform
[register_toolchains Function]: /rules/lib/globals/module#register_toolchains
[Rust rules]: https://github.com/bazelbuild/rules_rust
[select()]: /docs/configurable-attributes
[select() Platforms]: /docs/configurable-attributes#platforms
[Starlark provider]: /extending/rules#providers
[Starlark rule]: /extending/rules
[Starlark transitions]: /extending/config#user-defined-transitions
[target_compatible_with Attribute]: /reference/be/platforms-and-toolchains#toolchain.target_compatible_with
[Toolchains]: /extending/toolchains


Project: /_project.yaml
Book: /_book.yaml

# Labels

{% include "_buttons.html" %}

A **label** is an identifier for a target. A typical label in its full canonical
form looks like:

```none
@@myrepo//my/app/main:app_binary
```

The first part of the label is the repository name, `@@myrepo`. The double-`@`
syntax signifies that this is a [*canonical* repo
name](/external/overview#canonical-repo-name), which is unique within
the workspace. Labels with canonical repo names unambiguously identify a target
no matter which context they appear in.

Often the canonical repo name is an arcane string that looks like
`@@rules_java++toolchains+local_jdk`. What is much more commonly seen is
labels with an [*apparent* repo name](/external/overview#apparent-repo-name),
which looks like:

```
@myrepo//my/app/main:app_binary
```

The only difference is the repo name being prefixed with one `@` instead of two.
This refers to a repo with the apparent name `myrepo`, which could be different
based on the context this label appears in.

In the typical case that a label refers to the same repository from which
it is used, the repo name part may be omitted.  So, inside `@@myrepo` the first
label is usually written as

```
//my/app/main:app_binary
```

The second part of the label is the un-qualified package name
`my/app/main`, the path to the package
relative to the repository root.  Together, the repository name and the
un-qualified package name form the fully-qualified package name
`@@myrepo//my/app/main`. When the label refers to the same
package it is used in, the package name (and optionally, the colon)
may be omitted.  So, inside `@@myrepo//my/app/main`,
this label may be written either of the following ways:

```
app_binary
:app_binary
```

It is a matter of convention that the colon is omitted for files,
but retained for rules, but it is not otherwise significant.

The part of the label after the colon, `app_binary` is the un-qualified target
name. When it matches the last component of the package path, it, and the
colon, may be omitted.  So, these two labels are equivalent:

```
//my/app/lib
//my/app/lib:lib
```

The name of a file target in a subdirectory of the package is the file's path
relative to the package root (the directory containing the `BUILD` file). So,
this file is in the `my/app/main/testdata` subdirectory of the repository:

```
//my/app/main:testdata/input.txt
```

Strings like `//my/app` and `@@some_repo//my/app` have two meanings depending on
the context in which they are used: when Bazel expects a label, they mean
`//my/app:app` and `@@some_repo//my/app:app`, respectively. But, when Bazel
expects a package (e.g. in `package_group` specifications), they reference the
package that contains that label.

A common mistake in `BUILD` files is using `//my/app` to refer to a package, or
to *all* targets in a package--it does not.  Remember, it is
equivalent to `//my/app:app`, so it names the `app` target in the `my/app`
package of the current repository.

However, the use of `//my/app` to refer to a package is encouraged in the
specification of a `package_group` or in `.bzl` files, because it clearly
communicates that the package name is absolute and rooted in the top-level
directory of the workspace.

Relative labels cannot be used to refer to targets in other packages; the
repository identifier and package name must always be specified in this case.
For example, if the source tree contains both the package `my/app` and the
package `my/app/testdata` (each of these two directories has its own
`BUILD` file), the latter package contains a file named `testdepot.zip`. Here
are two ways (one wrong, one correct) to refer to this file within
`//my/app:BUILD`:

<p><span class="compare-worse">Wrong</span> — <code>testdata</code> is a different package, so you can't use a relative path</p>
<pre class="prettyprint">testdata/testdepot.zip</pre>

<p><span class="compare-better">Correct</span> — refer to <code>testdata</code> with its full path</p>

<pre class="prettyprint">//my/app/testdata:testdepot.zip</pre>



Labels starting with `@@//` are references to the main
repository, which will still work even from external repositories.
Therefore `@@//a/b/c` is different from
`//a/b/c` when referenced from an external repository.
The former refers back to the main repository, while the latter
looks for `//a/b/c` in the external repository itself.
This is especially relevant when writing rules in the main
repository that refer to targets in the main repository, and will be
used from external repositories.

For information about the different ways you can refer to targets, see
[target patterns](/run/build#specifying-build-targets).

### Lexical specification of a label {:#labels-lexical-specification}

Label syntax discourages use of metacharacters that have special meaning to the
shell. This helps to avoid inadvertent quoting problems, and makes it easier to
construct tools and scripts that manipulate labels, such as the
[Bazel Query Language](/query/language).

The precise details of allowed target names are below.

### Target names — `{{ "<var>" }}package-name{{ "</var>" }}:target-name` {:#target-names}

`target-name` is the name of the target within the package. The name of a rule
is the value of the `name` attribute in the rule's declaration in a `BUILD`
file; the name of a file is its pathname relative to the directory containing
the `BUILD` file.

Target names must be composed entirely of characters drawn from the set `a`–`z`,
`A`–`Z`, `0`–`9`, and the punctuation symbols `!%-@^_"#$&'()*-+,;<=>?[]{|}~/.`.

Filenames must be relative pathnames in normal form, which means they must
neither start nor end with a slash (for example, `/foo` and `foo/` are
forbidden) nor contain multiple consecutive slashes as path separators
(for example, `foo//bar`). Similarly, up-level references (`..`) and
current-directory references (`./`) are forbidden.

<p><span class="compare-worse">Wrong</span> — Do not use <code>..</code> to refer to files in other packages</p>

<p><span class="compare-better">Correct</span> — Use
  <code>//{{ "<var>" }}package-name{{ "</var>" }}:{{ "<var>" }}filename{{ "</var>" }}</code></p>


While it is common to use `/` in the name of a file target, avoid the use of
`/` in the names of rules. Especially when the shorthand form of a label is
used, it may confuse the reader. The label `//foo/bar/wiz` is always a shorthand
for `//foo/bar/wiz:wiz`, even if there is no such package `foo/bar/wiz`; it
never refers to `//foo:bar/wiz`, even if that target exists.

However, there are some situations where use of a slash is convenient, or
sometimes even necessary. For example, the name of certain rules must match
their principal source file, which may reside in a subdirectory of the package.

### Package names — `//package-name:{{ "<var>" }}target-name{{ "</var>" }}` {:#package-names}

The name of a package is the name of the directory containing its `BUILD` file,
relative to the top-level directory of the containing repository.
For example: `my/app`.

On a technical level, Bazel enforces the following:

* Allowed characters in package names are the lowercase letters `a` through `z`,
  the uppercase letters `A` through `Z`, the digits `0` through `9`, the
  characters ``! \"#$%&'()*+,-.;<=>?@[]^_`{|}`` (yes, there's a space character
  in there!), and of course forward slash `/` (since it's the directory
  separator).
* Package names may not start or end with a forward slash character `/`.
* Package names may not contain the substring `//`. This wouldn't make
  sense---what would the corresponding directory path be?
* Package names may not contain the substring `/./` or `/../` or `/.../` etc.
  This enforcement is done to avoid confusion when translating between a logical
  package name and a physical directory name, given the semantic meaning of the
  dot character in path strings.

On a practical level:

* For a language with a directory structure that is significant to its module
  system (for example, Java), it's important to choose directory names that are
  valid identifiers in the language. For example, don't start with a leading
  digit and avoid special characters, especially underscores and hyphens.
* Although Bazel supports targets in the workspace's root package (for example,
  `//:foo`), it's best to leave that package empty so all meaningful packages
  have descriptive names.

## Rules {:#rules}

A rule specifies the relationship between inputs and outputs, and the
steps to build the outputs. Rules can be of one of many different
kinds (sometimes called the _rule class_), which produce compiled
executables and libraries, test executables and other supported
outputs as described in the [Build Encyclopedia](/reference/be/overview).

`BUILD` files declare _targets_ by invoking _rules_.

In the example below, we see the declaration of the target `my_app`
using the `cc_binary` rule.

```python
cc_binary(
    name = "my_app",
    srcs = ["my_app.cc"],
    deps = [
        "//absl/base",
        "//absl/strings",
    ],
)
```

Every rule invocation has a `name` attribute (which must be a valid
[target name](#target-names)), that declares a target within the package
of the `BUILD` file.

Every rule has a set of _attributes_; the applicable attributes for a given
rule, and the significance and semantics of each attribute are a function of
the rule's kind; see the [Build Encyclopedia](/reference/be/overview) for a
list of rules and their corresponding attributes. Each attribute has a name and
a type. Some of the common types an attribute can have are integer, label, list
of labels, string, list of strings, output label, list of output labels. Not
all attributes need to be specified in every rule. Attributes thus form a
dictionary from keys (names) to optional, typed values.

The `srcs` attribute present in many rules has type "list of labels"; its
value, if present, is a list of labels, each being the name of a target that is
an input to this rule.

In some cases, the name of the rule kind is somewhat arbitrary, and more
interesting are the names of the files generated by the rule, and this is true
of genrules. For more information, see
[General Rules: genrule](/reference/be/general#genrule).

In other cases, the name is significant: for `*_binary` and `*_test` rules,
for example, the rule name determines the name of the executable produced by
the build.

This directed acyclic graph over targets is called the _target graph_ or
_build dependency graph_, and is the domain over which the
[Bazel Query tool](/query/guide) operates.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-ref">
        <span class="material-icons" aria-hidden="true">arrow_back</span>Targets</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-files">
        BUILD files<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>


Project: /_project.yaml
Book: /_book.yaml

# Visibility

{% include "_buttons.html" %}

This page covers Bazel's two visibility systems:
[target visibility](#target-visibility) and [load visibility](#load-visibility).

Both types of visibility help other developers distinguish between your
library's public API and its implementation details, and help enforce structure
as your workspace grows. You can also use visibility when deprecating a public
API to allow current users while denying new ones.

## Target visibility {:#target-visibility}

**Target visibility** controls who may depend on your target — that is, who may
use your target's label inside an attribute such as `deps`. A target will fail
to build during the [analysis](/reference/glossary#analysis-phase) phase if it
violates the visibility of one of its dependencies.

Generally, a target `A` is visible to a target `B` if they are in the same
location, or if `A` grants visibility to `B`'s location. In the absence of
[symbolic macros](/extending/macros), the term "location" can be simplified
to just "package"; see [below](#symbolic-macros) for more on symbolic macros.

Visibility is specified by listing allowed packages. Allowing a package does not
necessarily mean that its subpackages are also allowed. For more details on
packages and subpackages, see [Concepts and terminology](/concepts/build-ref).

For prototyping, you can disable target visibility enforcement by setting the
flag `--check_visibility=false`. This shouldn't be done for production usage in
submitted code.

The primary way to control visibility is with a rule's
[`visibility`](/reference/be/common-definitions#common.visibility) attribute.
The following subsections describe the attribute's format, how to apply it to
various kinds of targets, and the interaction between the visibility system and
symbolic macros.

### Visibility specifications {:#visibility-specifications}

All rule targets have a `visibility` attribute that takes a list of labels. Each
label has one of the following forms. With the exception of the last form, these
are just syntactic placeholders that don't correspond to any actual target.

*   `"//visibility:public"`: Grants access to all packages.

*   `"//visibility:private"`: Does not grant any additional access; only targets
    in this location's package can use this target.

*   `"//foo/bar:__pkg__"`: Grants access to `//foo/bar` (but not its
    subpackages).

*   `"//foo/bar:__subpackages__"`: Grants access to `//foo/bar` and all of its
    direct and indirect subpackages.

*   `"//some_pkg:my_package_group"`: Grants access to all of the packages that
    are part of the given [`package_group`](/reference/be/functions#package_group).

    *   Package groups use a
        [different syntax](/reference/be/functions#package_group.packages) for
        specifying packages. Within a package group, the forms
        `"//foo/bar:__pkg__"` and `"//foo/bar:__subpackages__"` are respectively
        replaced by `"//foo/bar"` and `"//foo/bar/..."`. Likewise,
        `"//visibility:public"` and `"//visibility:private"` are just `"public"`
        and `"private"`.

For example, if `//some/package:mytarget` has its `visibility` set to
`[":__subpackages__", "//tests:__pkg__"]`, then it could be used by any target
that is part of the `//some/package/...` source tree, as well as targets
declared in `//tests/BUILD`, but not by targets defined in
`//tests/integration/BUILD`.

**Best practice:** To make several targets visible to the same set
of packages, use a `package_group` instead of repeating the list in each
target's `visibility` attribute. This increases readability and prevents the
lists from getting out of sync.

**Best practice:** When granting visibility to another team's project, prefer
`__subpackages__` over `__pkg__` to avoid needless visibility churn as that
project evolves and adds new subpackages.

Note: The `visibility` attribute may not specify non-`package_group` targets.
Doing so triggers a "Label does not refer to a package group" or "Cycle in
dependency graph" error.

### Rule target visibility {:#rule-target-visibility}

A rule target's visibility is determined by taking its `visibility` attribute
-- or a suitable default if not given -- and appending the location where the
target was declared. For targets not declared in a symbolic macro, if the
package specifies a [`default_visibility`](/reference/be/functions#package.default_visibility),
this default is used; for all other packages and for targets declared in a
symbolic macro, the default is just `["//visibility:private"]`.

```starlark
# //mypkg/BUILD

package(default_visibility = ["//friend:__pkg__"])

cc_library(
    name = "t1",
    ...
    # No visibility explicitly specified.
    # Effective visibility is ["//friend:__pkg__", "//mypkg:__pkg__"].
    # If no default_visibility were given in package(...), the visibility would
    # instead default to ["//visibility:private"], and the effective visibility
    # would be ["//mypkg:__pkg__"].
)

cc_library(
    name = "t2",
    ...
    visibility = [":clients"],
    # Effective visibility is ["//mypkg:clients, "//mypkg:__pkg__"], which will
    # expand to ["//another_friend:__subpackages__", "//mypkg:__pkg__"].
)

cc_library(
    name = "t3",
    ...
    visibility = ["//visibility:private"],
    # Effective visibility is ["//mypkg:__pkg__"]
)

package_group(
    name = "clients",
    packages = ["//another_friend/..."],
)
```

**Best practice:** Avoid setting `default_visibility` to public. It may be
convenient for prototyping or in small codebases, but the risk of inadvertently
creating public targets increases as the codebase grows. It's better to be
explicit about which targets are part of a package's public interface.

### Generated file target visibility {:#generated-file-target-visibility}

A generated file target has the same visibility as the rule target that
generates it.

```starlark
# //mypkg/BUILD

java_binary(
    name = "foo",
    ...
    visibility = ["//friend:__pkg__"],
)
```

```starlark
# //friend/BUILD

some_rule(
    name = "bar",
    deps = [
        # Allowed directly by visibility of foo.
        "//mypkg:foo",
        # Also allowed. The java_binary's "_deploy.jar" implicit output file
        # target the same visibility as the rule target itself.
        "//mypkg:foo_deploy.jar",
    ]
    ...
)
```

### Source file target visibility {:#source-file-target-visibility}

Source file targets can either be explicitly declared using
[`exports_files`](/reference/be/functions#exports_files), or implicitly created
by referring to their filename in a label attribute of a rule (outside of a
symbolic macro). As with rule targets, the location of the call to
`exports_files`, or the BUILD file that referred to the input file, is always
automatically appended to the file's visibility.

Files declared by `exports_files` can have their visibility set by the
`visibility` parameter to that function. If this parameter is not given, the visibility is public.

Note: `exports_files` may not be used to override the visibility of a generated
file.

For files that do not appear in a call to `exports_files`, the visibility
depends on the value of the flag
[`--incompatible_no_implicit_file_export`](https://github.com/bazelbuild/bazel/issues/10225){: .external}:

*   If the flag is true, the visibility is private.

*   Else, the legacy behavior applies: The visibility is the same as the
    `BUILD` file's `default_visibility`, or private if a default visibility is
    not specified.

Avoid relying on the legacy behavior. Always write an `exports_files`
declaration whenever a source file target needs non-private visibility.

**Best practice:** When possible, prefer to expose a rule target rather than a
source file. For example, instead of calling `exports_files` on a `.java` file,
wrap the file in a non-private `java_library` target. Generally, rule targets
should only directly reference source files that live in the same package.

#### Example {:#source-file-visibility-example}

File `//frobber/data/BUILD`:

```starlark
exports_files(["readme.txt"])
```

File `//frobber/bin/BUILD`:

```starlark
cc_binary(
  name = "my-program",
  data = ["//frobber/data:readme.txt"],
)
```

### Config setting visibility {:#config-setting-visibility}

Historically, Bazel has not enforced visibility for
[`config_setting`](/reference/be/general#config_setting) targets that are
referenced in the keys of a [`select()`](/reference/be/functions#select). There
are two flags to remove this legacy behavior:

*   [`--incompatible_enforce_config_setting_visibility`](https://github.com/bazelbuild/bazel/issues/12932){: .external}
    enables visibility checking for these targets. To assist with migration, it
    also causes any `config_setting` that does not specify a `visibility` to be
    considered public (regardless of package-level `default_visibility`).

*   [`--incompatible_config_setting_private_default_visibility`](https://github.com/bazelbuild/bazel/issues/12933){: .external}
    causes `config_setting`s that do not specify a `visibility` to respect the
    package's `default_visibility` and to fallback on private visibility, just
    like any other rule target. It is a no-op if
    `--incompatible_enforce_config_setting_visibility` is not set.

Avoid relying on the legacy behavior. Any `config_setting` that is intended to
be used outside the current package should have an explicit `visibility`, if the
package does not already specify a suitable `default_visibility`.

### Package group target visibility {:#package-group-target-visibility}

`package_group` targets do not have a `visibility` attribute. They are always
publicly visible.

### Visibility of implicit dependencies {:#visibility-implicit-dependencies}

Some rules have [implicit dependencies](/extending/rules#private_attributes_and_implicit_dependencies) —
dependencies that are not spelled out in a `BUILD` file but are inherent to
every instance of that rule. For example, a `cc_library` rule might create an
implicit dependency from each of its rule targets to an executable target
representing a C++ compiler.

The visibility of such an implicit dependency is checked with respect to the
package containing the `.bzl` file in which the rule (or aspect) is defined. In
our example, the C++ compiler could be private so long as it lives in the same
package as the definition of the `cc_library` rule. As a fallback, if the
implicit dependency is not visible from the definition, it is checked with
respect to the `cc_library` target.

If you want to restrict the usage of a rule to certain packages, use
[load visibility](#load-visibility) instead.

### Visibility and symbolic macros {:#symbolic-macros}

This section describes how the visibility system interacts with
[symbolic macros](/extending/macros).

#### Locations within symbolic macros {:#locations-within-symbolic-macros}

A key detail of the visibility system is how we determine the location of a
declaration. For targets that are not declared in a symbolic macro, the location
is just the package where the target lives -- the package of the `BUILD` file.
But for targets created in a symbolic macro, the location is the package
containing the `.bzl` file where the macro's definition (the
`my_macro = macro(...)` statement) appears. When a target is created inside
multiple nested targets, it is always the innermost symbolic macro's definition
that is used.

The same system is used to determine what location to check against a given
dependency's visibility. If the consuming target was created inside a macro, we
look at the innermost macro's definition rather than the package the consuming
target lives in.

This means that all macros whose code is defined in the same package are
automatically "friends" with one another. Any target directly created by a macro
defined in `//lib:defs.bzl` can be seen from any other macro defined in `//lib`,
regardless of what packages the macros are actually instantiated in. Likewise,
they can see, and can be seen by, targets declared directly in `//lib/BUILD` and
its legacy macros. Conversely, targets that live in the same package cannot
necessarily see one another if at least one of them is created by a symbolic
macro.

Within a symbolic macro's implementation function, the `visibility` parameter
has the effective value of the macro's `visibility` attribute after appending
the location where the macro was called. The standard way for a macro to export
one of its targets to its caller is to forward this value along to the target's
declaration, as in `some_rule(..., visibility = visibility)`. Targets that omit
this attribute won't be visible to the caller of the macro unless the caller
happens to be in the same package as the macro definition. This behavior
composes, in the sense that a chain of nested calls to submacros may each pass
`visibility = visibility`, re-exporting the inner macro's exported targets to
the caller at each level, without exposing any of the macros' implementation
details.

#### Delegating privileges to a submacro {:#delegating-privileges-to-a-submacro}

The visibility model has a special feature to allow a macro to delegate its
permissions to a submacro. This is important for factoring and composing macros.

Suppose you have a macro `my_macro` that creates a dependency edge using a rule
`some_library` from another package:

```starlark
# //macro/defs.bzl
load("//lib:defs.bzl", "some_library")

def _impl(name, visibility, ...):
    ...
    native.genrule(
        name = name + "_dependency"
        ...
    )
    some_library(
        name = name + "_consumer",
        deps = [name + "_dependency"],
        ...
    )

my_macro = macro(implementation = _impl, ...)
```

```starlark
# //pkg/BUILD

load("//macro:defs.bzl", "my_macro")

my_macro(name = "foo", ...)
```

The `//pkg:foo_dependency` target has no `visibility` specified, so it is only
visible within `//macro`, which works fine for the consuming target. Now, what
happens if the author of `//lib` refactors `some_library` to instead be
implemented using a macro?

```starlark
# //lib:defs.bzl

def _impl(name, visibility, deps, ...):
    some_rule(
        # Main target, exported.
        name = name,
        visibility = visibility,
        deps = deps,
        ...)

some_library = macro(implementation = _impl, ...)
```

With this change, `//pkg:foo_consumer`'s location is now `//lib` rather than
`//macro`, so its usage of `//pkg:foo_dependency` violates the dependency's
visibility. The author of `my_macro` can't be expected to pass
`visibility = ["//lib"]` to the declaration of the dependency just to work
around this implementation detail.

For this reason, when a dependency of a target is also an attribute value of the
macro that declared the target, we check the dependency's visibility against the
location of the macro instead of the location of the consuming target.

In this example, to validate whether `//pkg:foo_consumer` can see
`//pkg:foo_dependency`, we see that `//pkg:foo_dependency` was also passed as an
input to the call to `some_library` inside of `my_macro`, and instead check the
dependency's visibility against the location of this call, `//macro`.

This process can repeat recursively, as long as a target or macro declaration is
inside of another symbolic macro taking the dependency's label in one of its
label-typed attributes.

Note: Visibility delegation does not work for labels that were not passed into
the macro, such as labels derived by string manipulation.

#### Finalizers {:#finalizers}

Targets declared in a rule finalizer (a symbolic macro with `finalizer = True`),
in addition to seeing targets following the usual symbolic macro visibility
rules, can *also* see all targets which are visible to the finalizer target's
package.

In other words, if you migrate a `native.existing_rules()`-based legacy macro to
a finalizer, the targets declared by the finalizer will still be able to see
their old dependencies.

It is possible to define targets that a finalizer can introspect using
`native.existing_rules()`, but which it cannot use as dependencies under the
visibility system. For example, if a macro-defined target is not visible to its
own package or to the finalizer macro's definition, and is not delegated to the
finalizer, the finalizer cannot see such a target. Note, however, that a
`native.existing_rules()`-based legacy macro will also be unable to see such a
target.

## Load visibility {:#load-visibility}

**Load visibility** controls whether a `.bzl` file may be loaded from other
`BUILD` or `.bzl` files outside the current package.

In the same way that target visibility protects source code that is encapsulated
by targets, load visibility protects build logic that is encapsulated by `.bzl`
files. For instance, a `BUILD` file author might wish to factor some repetitive
target declarations into a macro in a `.bzl` file. Without the protection of
load visibility, they might find their macro reused by other collaborators in
the same workspace, so that modifying the macro breaks other teams' builds.

Note that a `.bzl` file may or may not have a corresponding source file target.
If it does, there is no guarantee that the load visibility and the target
visibility coincide. That is, the same `BUILD` file might be able to load the
`.bzl` file but not list it in the `srcs` of a [`filegroup`](/reference/be/general#filegroup),
or vice versa. This can sometimes cause problems for rules that wish to consume
`.bzl` files as source code, such as for documentation generation or testing.

For prototyping, you may disable load visibility enforcement by setting
`--check_bzl_visibility=false`. As with `--check_visibility=false`, this should
not be done for submitted code.

Load visibility is available as of Bazel 6.0.

### Declaring load visibility {:#declaring-load-visibility}

To set the load visibility of a `.bzl` file, call the
[`visibility()`](/rules/lib/globals/bzl#visibility) function from within the file.
The argument to `visibility()` is a list of package specifications, just like
the [`packages`](/reference/be/functions#package_group.packages) attribute of
`package_group`. However, `visibility()` does not accept negative package
specifications.

The call to `visibility()` must only occur once per file, at the top level (not
inside a function), and ideally immediately following the `load()` statements.

Unlike target visibility, the default load visibility is always public. Files
that do not call `visibility()` are always loadable from anywhere in the
workspace. It is a good idea to add `visibility("private")` to the top of any
new `.bzl` file that is not specifically intended for use outside the package.

### Example {:#load-visibility-example}

```starlark
# //mylib/internal_defs.bzl

# Available to subpackages and to mylib's tests.
visibility(["//mylib/...", "//tests/mylib/..."])

def helper(...):
    ...
```

```starlark
# //mylib/rules.bzl

load(":internal_defs.bzl", "helper")
# Set visibility explicitly, even though public is the default.
# Note the [] can be omitted when there's only one entry.
visibility("public")

myrule = rule(
    ...
)
```

```starlark
# //someclient/BUILD

load("//mylib:rules.bzl", "myrule")          # ok
load("//mylib:internal_defs.bzl", "helper")  # error

...
```

### Load visibility practices {:#load-visibility-practices}

This section describes tips for managing load visibility declarations.

#### Factoring visibilities {:#factoring-visibilities}

When multiple `.bzl` files should have the same visibility, it can be helpful to
factor their package specifications into a common list. For example:

```starlark
# //mylib/internal_defs.bzl

visibility("private")

clients = [
    "//foo",
    "//bar/baz/...",
    ...
]
```

```starlark
# //mylib/feature_A.bzl

load(":internal_defs.bzl", "clients")
visibility(clients)

...
```

```starlark
# //mylib/feature_B.bzl

load(":internal_defs.bzl", "clients")
visibility(clients)

...
```

This helps prevent accidental skew between the various `.bzl` files'
visibilities. It also is more readable when the `clients` list is large.

#### Composing visibilities {:#composing-visibilities}

Sometimes a `.bzl` file might need to be visible to an allowlist that is
composed of multiple smaller allowlists. This is analogous to how a
`package_group` can incorporate other `package_group`s via its
[`includes`](/reference/be/functions#package_group.includes) attribute.

Suppose you are deprecating a widely used macro. You want it to be visible only
to existing users and to the packages owned by your own team. You might write:

```starlark
# //mylib/macros.bzl

load(":internal_defs.bzl", "our_packages")
load("//some_big_client:defs.bzl", "their_remaining_uses")

# List concatenation. Duplicates are fine.
visibility(our_packages + their_remaining_uses)
```

#### Deduplicating with package groups {:#deduplicating-with-package-groups}

Unlike target visibility, you cannot define a load visibility in terms of a
`package_group`. If you want to reuse the same allowlist for both target
visibility and load visibility, it's best to move the list of package
specifications into a .bzl file, where both kinds of declarations may refer to
it. Building off the example in [Factoring visibilities](#factoring-visibilities)
above, you might write:

```starlark
# //mylib/BUILD

load(":internal_defs", "clients")

package_group(
    name = "my_pkg_grp",
    packages = clients,
)
```

This only works if the list does not contain any negative package
specifications.

#### Protecting individual symbols {:#protecting-individual-symbols}

Any Starlark symbol whose name begins with an underscore cannot be loaded from
another file. This makes it easy to create private symbols, but does not allow
you to share these symbols with a limited set of trusted files. On the other
hand, load visibility gives you control over what other packages may see your
`.bzl file`, but does not allow you to prevent any non-underscored symbol from
being loaded.

Luckily, you can combine these two features to get fine-grained control.

```starlark
# //mylib/internal_defs.bzl

# Can't be public, because internal_helper shouldn't be exposed to the world.
visibility("private")

# Can't be underscore-prefixed, because this is
# needed by other .bzl files in mylib.
def internal_helper(...):
    ...

def public_util(...):
    ...
```

```starlark
# //mylib/defs.bzl

load(":internal_defs", "internal_helper", _public_util="public_util")
visibility("public")

# internal_helper, as a loaded symbol, is available for use in this file but
# can't be imported by clients who load this file.
...

# Re-export public_util from this file by assigning it to a global variable.
# We needed to import it under a different name ("_public_util") in order for
# this assignment to be legal.
public_util = _public_util
```

#### bzl-visibility Buildifier lint {:#bzl-visibility-buildifier-lint}

There is a [Buildifier lint](https://github.com/bazelbuild/buildtools/blob/master/WARNINGS.md#bzl-visibility)
that provides a warning if users load a file from a directory named `internal`
or `private`, when the user's file is not itself underneath the parent of that
directory. This lint predates the load visibility feature and is unnecessary in
workspaces where `.bzl` files declare visibilities.


Project: /_project.yaml
Book: /_book.yaml

# BUILD files

{% include "_buttons.html" %}

The previous sections described packages, targets and labels, and the
build dependency graph abstractly. This section describes the concrete syntax
used to define a package.

By definition, every package contains a `BUILD` file, which is a short
program.

Note: The `BUILD` file can be named either `BUILD` or `BUILD.bazel`. If both
files exist, `BUILD.bazel` takes precedence over `BUILD`.
For simplicity's sake, the documentation refers to these files simply as `BUILD`
files.

`BUILD` files are evaluated using an imperative language,
[Starlark](https://github.com/bazelbuild/starlark/){: .external}.

They are interpreted as a sequential list of statements.

In general, order does matter: variables must be defined before they are
used, for example. However, most `BUILD` files consist only of declarations of
build rules, and the relative order of these statements is immaterial; all
that matters is _which_ rules were declared, and with what values, by the
time package evaluation completes.

When a build rule function, such as `cc_library`, is executed, it creates a
new target in the graph. This target can later be referred using a label.

In simple `BUILD` files, rule declarations can be re-ordered freely without
changing the behavior.

To encourage a clean separation between code and data, `BUILD` files cannot
contain function definitions, `for` statements or `if` statements (but list
comprehensions and `if` expressions are allowed). Functions can be declared in
`.bzl` files instead. Additionally, `*args` and `**kwargs` arguments are not
allowed in `BUILD` files; instead list all the arguments explicitly.

Crucially, programs in Starlark can't perform arbitrary I/O. This invariant
makes the interpretation of `BUILD` files hermetic — dependent only on a known
set of inputs, which is essential for ensuring that builds are reproducible.
For more details, see [Hermeticity](/basics/hermeticity).

Because `BUILD` files need to be updated whenever the dependencies of the
underlying code change, they are typically maintained by multiple people on a
team. `BUILD` file authors should comment liberally to document the role
of each build target, whether or not it is intended for public use, and to
document the role of the package itself.

## Loading an extension {:#load}

Bazel extensions are files ending in `.bzl`. Use the `load` statement to import
a symbol from an extension.

```
load("//foo/bar:file.bzl", "some_library")
```

This code loads the file `foo/bar/file.bzl` and adds the `some_library` symbol
to the environment. This can be used to load new rules, functions, or constants
(for example, a string or a list). Multiple symbols can be imported by using
additional arguments to the call to `load`. Arguments must be string literals
(no variable) and `load` statements must appear at top-level — they cannot be
in a function body.

The first argument of `load` is a [label](/concepts/labels) identifying a
`.bzl` file. If it's a relative label, it is resolved with respect to the
package (not directory) containing the current `bzl` file. Relative labels in
`load` statements should use a leading `:`.

`load` also supports aliases, therefore, you can assign different names to the
imported symbols.

```
load("//foo/bar:file.bzl", library_alias = "some_library")
```

You can define multiple aliases within one `load` statement. Moreover, the
argument list can contain both aliases and regular symbol names. The following
example is perfectly legal (please note when to use quotation marks).

```
load(":my_rules.bzl", "some_rule", nice_alias = "some_other_rule")
```

In a `.bzl` file, symbols starting with `_` are not exported and cannot be
loaded from another file.

You can use [load visibility](/concepts/visibility#load-visibility) to restrict
who may load a `.bzl` file.

## Types of build rules {:#types-of-build-rules}

The majority of build rules come in families, grouped together by
language. For example, `cc_binary`, `cc_library`
and `cc_test` are the build rules for C++ binaries,
libraries, and tests, respectively. Other languages use the same
naming scheme, with a different prefix, such as `java_*` for
Java. Some of these functions are documented in the
[Build Encyclopedia](/reference/be/overview), but it is possible
for anyone to create new rules.

* `*_binary` rules build executable programs in a given language. After a
  build, the executable will reside in the build tool's binary
  output tree at the corresponding name for the rule's label,
  so `//my:program` would appear at (for example) `$(BINDIR)/my/program`.

  In some languages, such rules also create a runfiles directory
  containing all the files mentioned in a `data`
  attribute belonging to the rule, or any rule in its transitive
  closure of dependencies; this set of files is gathered together in
  one place for ease of deployment to production.

* `*_test` rules are a specialization of a `*_binary` rule, used for automated
  testing. Tests are simply programs that return zero on success.

  Like binaries, tests also have runfiles trees, and the files
  beneath it are the only files that a test may legitimately open
  at runtime. For example, a program `cc_test(name='x',
  data=['//foo:bar'])` may open and read `$TEST_SRCDIR/workspace/foo/bar` during execution.
  (Each programming language has its own utility function for
  accessing the value of `$TEST_SRCDIR`, but they are all
  equivalent to using the environment variable directly.)
  Failure to observe the rule will cause the test to fail when it is
  executed on a remote testing host.

* `*_library` rules specify separately-compiled modules in the given
    programming language. Libraries can depend on other libraries,
    and binaries and tests can depend on libraries, with the expected
    separate-compilation behavior.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/labels">
        <span class="material-icons" aria-hidden="true">arrow_back</span>Labels</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/dependencies">
        Dependencies<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>

## File encoding

`BUILD` and `.bzl` files should be encoded in UTF-8, of which ASCII is a valid
subset. Arbitrary byte sequences are currently allowed, but may stop being
supported in the future.


Project: /_project.yaml
Book: /_book.yaml

# Dependencies

{% include "_buttons.html" %}

A target `A` _depends upon_ a target `B` if `B` is needed by `A` at build or
execution time. The _depends upon_ relation induces a
[Directed Acyclic Graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph){: .external}
(DAG) over targets, and it is called a _dependency graph_.

A target's _direct_ dependencies are those other targets reachable by a path
of length 1 in the dependency graph. A target's _transitive_ dependencies are
those targets upon which it depends via a path of any length through the graph.

In fact, in the context of builds, there are two dependency graphs, the graph
of _actual dependencies_ and the graph of _declared dependencies_. Most of the
time, the two graphs are so similar that this distinction need not be made, but
it is useful for the discussion below.

## Actual and declared dependencies {:#actual-and-declared-dependencies}

A target `X` is _actually dependent_ on target `Y` if `Y` must be present,
built, and up-to-date in order for `X` to be built correctly. _Built_ could
mean generated, processed, compiled, linked, archived, compressed, executed, or
any of the other kinds of tasks that routinely occur during a build.

A target `X` has a _declared dependency_ on target `Y` if there is a dependency
edge from `X` to `Y` in the package of `X`.

For correct builds, the graph of actual dependencies _A_ must be a subgraph of
the graph of declared dependencies _D_. That is, every pair of
directly-connected nodes `x --> y` in _A_ must also be directly connected in
_D_. It can be said that _D_ is an _overapproximation_ of _A_.

Important: _D_ should not be too much of an overapproximation of _A_ because
redundant declared dependencies can make builds slower and binaries larger.

`BUILD` file writers must explicitly declare all of the actual direct
dependencies for every rule to the build system, and no more.

Failure to observe this principle causes undefined behavior: the build may fail,
but worse, the build may depend on some prior operations, or upon transitive
declared dependencies the target happens to have. Bazel checks for missing
dependencies and report errors, but it's not possible for this checking to be
complete in all cases.

You need not (and should not) attempt to list everything indirectly imported,
even if it is _needed_ by `A` at execution time.

During a build of target `X`, the build tool inspects the entire transitive
closure of dependencies of `X` to ensure that any changes in those targets are
reflected in the final result, rebuilding intermediates as needed.

The transitive nature of dependencies leads to a common mistake. Sometimes,
code in one file may use code provided by an _indirect_ dependency — a
transitive but not direct edge in the declared dependency graph. Indirect
dependencies don't appear in the `BUILD` file. Because the rule doesn't
directly depend on the provider, there is no way to track changes, as shown in
the following example timeline:

### 1. Declared dependencies match actual dependencies {:#this-is-fine}

At first, everything works. The code in package `a` uses code in package `b`.
The code in package `b` uses code in package `c`, and thus `a` transitively
depends on `c`.

<table class="cyan">
  <tr>
    <th><code>a/BUILD</code></th>
    <th><code><strong>b</strong>/BUILD</code></th>
  </tr>
  <tr>
    <td>
      <pre>rule(
    name = "a",
    srcs = "a.in",
    deps = "//b:b",
)
      </pre>
    </td>
    <td>
      <pre>
rule(
    name = "b",
    srcs = "b.in",
    deps = "//c:c",
)
      </pre>
    </td>
  </tr>
  <tr class="alt">
    <td><code>a / a.in</code></td>
    <td><code>b / b.in</code></td>
  </tr>
  <tr>
    <td><pre>
import b;
b.foo();
    </pre>
    </td>
    <td>
      <pre>
import c;
function foo() {
  c.bar();
}
      </pre>
    </td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Declared dependency graph with arrows connecting a, b, and c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Actual dependency graph that matches the declared dependency
                  graph with arrows connecting a, b, and c">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependencies overapproximate the actual dependencies. All is well.

### 2. Adding an undeclared dependency {:#undeclared-dependency}

A latent hazard is introduced when someone adds code to `a` that creates a
direct _actual_ dependency on `c`, but forgets to declare it in the build file
`a/BUILD`.

<table class="cyan">
  <tr>
    <th><code>a / a.in</code></th>
    <th>&nbsp;</th>
  </tr>
  <tr>
    <td>
      <pre>
        import b;
        import c;
        b.foo();
        c.garply();
      </pre>
    </td>
    <td>&nbsp;</td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Declared dependency graph with arrows connecting a, b, and c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_c_ac.svg"
             alt="Actual dependency graph with arrows connecting a, b, and c. An
                  arrow now connects A to C as well. This does not match the
                  declared dependency graph">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependencies no longer overapproximate the actual dependencies.
This may build ok, because the transitive closures of the two graphs are equal,
but masks a problem: `a` has an actual but undeclared dependency on `c`.

### 3. Divergence between declared and actual dependency graphs {:#divergence}

The hazard is revealed when someone refactors `b` so that it no longer depends on
`c`, inadvertently breaking `a` through no
fault of their own.

<table class="cyan">
  <tr>
    <th>&nbsp;</th>
    <th><code><strong>b</strong>/BUILD</code></th>
  </tr>
  <tr>
    <td>&nbsp;</td>
    <td>
      <pre>rule(
    name = "b",
    srcs = "b.in",
    <strong>deps = "//d:d",</strong>
)
      </pre>
    </td>
  </tr>
  <tr class="alt">
    <td>&nbsp;</td>
    <td><code>b / b.in</code></td>
  </tr>
  <tr>
    <td>&nbsp;</td>
    <td>
      <pre>
      import d;
      function foo() {
        d.baz();
      }
      </pre>
    </td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/ab_c.svg"
             alt="Declared dependency graph with arrows connecting a and b.
                  b no longer connects to c, which breaks a's connection to c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_a_c.svg"
             alt="Actual dependency graph that shows a connecting to b and c,
                  but b no longer connects to c">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependency graph is now an underapproximation of the actual
dependencies, even when transitively closed; the build is likely to fail.

The problem could have been averted by ensuring that the actual dependency from
`a` to `c` introduced in Step 2 was properly declared in the `BUILD` file.

## Types of dependencies {:#types-of-dependencies}

Most build rules have three attributes for specifying different kinds of
generic dependencies: `srcs`, `deps` and `data`. These are explained below. For
more details, see
[Attributes common to all rules](/reference/be/common-definitions).

Many rules also have additional attributes for rule-specific kinds of
dependencies, for example, `compiler` or `resources`. These are detailed in the
[Build Encyclopedia](/reference/be/).

### `srcs` dependencies {:#srcs-dependencies}

Files consumed directly by the rule or rules that output source files.

### `deps` dependencies {:#deps-dependencies}

Rule pointing to separately-compiled modules providing header files,
symbols, libraries, data, etc.

### `data` dependencies {:#data-dependencies}

A build target might need some data files to run correctly. These data files
aren't source code: they don't affect how the target is built. For example, a
unit test might compare a function's output to the contents of a file. When you
build the unit test you don't need the file, but you do need it when you run
the test. The same applies to tools that are launched during execution.

The build system runs tests in an isolated directory where only files listed as
`data` are available. Thus, if a binary/library/test needs some files to run,
specify them (or a build rule containing them) in `data`. For example:

```
# I need a config file from a directory named env:
java_binary(
    name = "setenv",
    ...
    data = [":env/default_env.txt"],
)

# I need test data from another directory
sh_test(
    name = "regtest",
    srcs = ["regtest.sh"],
    data = [
        "//data:file1.txt",
        "//data:file2.txt",
        ...
    ],
)
```

These files are available using the relative path `path/to/data/file`. In tests,
you can refer to these files by joining the paths of the test's source
directory and the workspace-relative path, for example,
`${TEST_SRCDIR}/workspace/path/to/data/file`.

## Using labels to reference directories {:#using-labels-reference-directories}

As you look over our `BUILD` files, you might notice that some `data` labels
refer to directories. These labels end with `/.` or `/` like these examples,
which you should not use:

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["//data/regression:unittest/."]</code>
</p>

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["testdata/."]</code>
</p>

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["testdata/"]</code>
</p>


This seems convenient, particularly for tests because it allows a test to
use all the data files in the directory.

But try not to do this. In order to ensure correct incremental rebuilds (and
re-execution of tests) after a change, the build system must be aware of the
complete set of files that are inputs to the build (or test). When you specify
a directory, the build system performs a rebuild only when the directory itself
changes (due to addition or deletion of files), but won't be able to detect
edits to individual files as those changes don't affect the enclosing directory.
Rather than specifying directories as inputs to the build system, you should
enumerate the set of files contained within them, either explicitly or using the
[`glob()`](/reference/be/functions#glob) function. (Use `**` to force the
`glob()` to be recursive.)


<p><span class="compare-better">Recommended</span> —
  <code>data = glob(["testdata/**"])</code>
</p>

Unfortunately, there are some scenarios where directory labels must be used.
For example, if the `testdata` directory contains files whose names don't
conform to the [label syntax](/concepts/labels#labels-lexical-specification),
then explicit enumeration of files, or use of the
[`glob()`](/reference/be/functions#glob) function produces an invalid labels
error. You must use directory labels in this case, but beware of the
associated risk of incorrect rebuilds described above.

If you must use directory labels, keep in mind that you can't refer to the
parent package with a relative `../` path; instead, use an absolute path like
`//data/regression:unittest/.`.

Note: Directory labels are only valid for data dependencies. If you try to use
a directory as a label in an argument other than `data`, it will fail and you
will get a (probably cryptic) error message.

Any external rule, such as a test, that needs to use multiple files must
explicitly declare its dependence on all of them. You can use `filegroup()` to
group files together in the `BUILD` file:

```
filegroup(
        name = 'my_data',
        srcs = glob(['my_unittest_data/*'])
)
```

You can then reference the label `my_data` as the data dependency in your test.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-files">
        <span class="material-icons" aria-hidden="true">arrow_back</span>BUILD files</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/visibility">
        Visibility<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>



Project: /_project.yaml
Book: /_book.yaml

# Repositories, workspaces, packages, and targets

{% include "_buttons.html" %}

Bazel builds software from source code organized in directory trees called
repositories. A defined set of repositories comprises the workspace. Source
files in repositories are organized in a nested hierarchy of packages, where
each package is a directory that contains a set of related source files and one
`BUILD` file. The `BUILD` file specifies what software outputs can be built from
the source.

### Repositories {:#repositories}

Source files used in a Bazel build are organized in _repositories_ (often
shortened to _repos_). A repo is a directory tree with a boundary marker file at
its root; such a boundary marker file could be `MODULE.bazel`, `REPO.bazel`, or
in legacy contexts, `WORKSPACE` or `WORKSPACE.bazel`.

The repo in which the current Bazel command is being run is called the _main
repo_. Other, (external) repos are defined by _repo rules_; see [external
dependencies overview](/external/overview) for more information.

## Workspace {:#workspace}

A _workspace_ is the environment shared by all Bazel commands run from the same
main repo. It encompasses the main repo and the set of all defined external
repos.

Note that historically the concepts of "repository" and "workspace" have been
conflated; the term "workspace" has often been used to refer to the main
repository, and sometimes even used as a synonym of "repository".

## Packages {:#packages}

The primary unit of code organization in a repository is the _package_. A
package is a collection of related files and a specification of how they can be
used to produce output artifacts.

A package is defined as a directory containing a
[`BUILD` file](/concepts/build-files) named either `BUILD` or `BUILD.bazel`. A
package includes all files in its directory, plus all subdirectories beneath it,
except those which themselves contain a `BUILD` file. From this definition, no
file or directory may be a part of two different packages.

For example, in the following directory tree there are two packages, `my/app`,
and the subpackage `my/app/tests`. Note that `my/app/data` is not a package, but
a directory belonging to package `my/app`.

```
src/my/app/BUILD
src/my/app/app.cc
src/my/app/data/input.txt
src/my/app/tests/BUILD
src/my/app/tests/test.cc
```

## Targets {:#targets}

A package is a container of _targets_, which are defined in the package's
`BUILD` file. Most targets are one of two principal kinds, _files_ and _rules_.

Files are further divided into two kinds. _Source files_ are usually written by
the efforts of people, and checked in to the repository. _Generated files_,
sometimes called derived files or output files, are not checked in, but are
generated from source files.

The second kind of target is declared with a _rule_. Each rule instance
specifies the relationship between a set of input and a set of output files. The
inputs to a rule may be source files, but they also may be the outputs of other
rules.

Whether the input to a rule is a source file or a generated file is in most
cases immaterial; what matters is only the contents of that file. This fact
makes it easy to replace a complex source file with a generated file produced by
a rule, such as happens when the burden of manually maintaining a highly
structured file becomes too tiresome, and someone writes a program to derive it.
No change is required to the consumers of that file. Conversely, a generated
file may easily be replaced by a source file with only local changes.

The inputs to a rule may also include _other rules_. The precise meaning of such
relationships is often quite complex and language- or rule-dependent, but
intuitively it is simple: a C++ library rule A might have another C++ library
rule B for an input. The effect of this dependency is that B's header files are
available to A during compilation, B's symbols are available to A during
linking, and B's runtime data is available to A during execution.

An invariant of all rules is that the files generated by a rule always belong to
the same package as the rule itself; it is not possible to generate files into
another package. It is not uncommon for a rule's inputs to come from another
package, though.

Package groups are sets of packages whose purpose is to limit accessibility of
certain rules. Package groups are defined by the `package_group` function. They
have three properties: the list of packages they contain, their name, and other
package groups they include. The only allowed ways to refer to them are from the
`visibility` attribute of rules or from the `default_visibility` attribute of
the `package` function; they do not generate or consume files. For more
information, refer to the [`package_group`
documentation](/reference/be/functions#package_group).

<a class="button button-with-icon button-primary" href="/concepts/labels">
  Labels<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span>
</a>

Project: /_project.yaml
Book: /_book.yaml

# Migrating to Platforms

{% include "_buttons.html" %}

Bazel has sophisticated [support](#background) for modeling
[platforms][Platforms] and [toolchains][Toolchains] for multi-architecture and
cross-compiled builds.

This page summarizes the state of this support.

Key Point: Bazel's platform and toolchain APIs are available today. Not all
languages support them. Use these APIs with your project if you can. Bazel is
migrating all major languages so eventually all builds will be platform-based.

See also:

* [Platforms][Platforms]
* [Toolchains][Toolchains]
* [Background][Background]

## Status {:#status}

### C++ {:#cxx}

C++ rules use platforms to select toolchains when
`--incompatible_enable_cc_toolchain_resolution` is set.

This means you can configure a C++ project with:

```posix-terminal
bazel build //:my_cpp_project --platforms=//:myplatform
```

instead of the legacy:

```posix-terminal
bazel build //:my_cpp_project` --cpu=... --crosstool_top=...  --compiler=...
```

This will be enabled by default in Bazel 7.0 ([#7260](https://github.com/bazelbuild/bazel/issues/7260){: .external}).

To test your C++ project with platforms, see
[Migrating Your Project](#migrating-your-project) and
[Configuring C++ toolchains].

### Java {:#java}

Java rules use platforms to select toolchains.

This replaces legacy flags `--java_toolchain`, `--host_java_toolchain`,
`--javabase`, and `--host_javabase`.

See [Java and Bazel](/docs/bazel-and-java) for details.

### Android {:#android}

Android rules use platforms to select toolchains when
`--incompatible_enable_android_toolchain_resolution` is set.

This means you can configure an Android project with:

```posix-terminal
bazel build //:my_android_project --android_platforms=//:my_android_platform
```

instead of with legacy flags like  `--android_crosstool_top`, `--android_cpu`,
and `--fat_apk_cpu`.

This will be enabled by default in Bazel 7.0 ([#16285](https://github.com/bazelbuild/bazel/issues/16285){: .external}).

To test your Android project with platforms, see
[Migrating Your Project](#migrating-your-project).

### Apple {:#apple}

[Apple rules]{: .external} do not support platforms and are not yet scheduled
for support.

You can still use platform APIs with Apple builds (for example, when building
with a mixture of Apple rules and pure C++) with [platform
mappings](#platform-mappings).

### Other languages {:#other-languages}

* [Go rules]{: .external} fully support platforms
* [Rust rules]{: .external} fully support platforms.

If you own a language rule set, see [Migrating your rule set] for adding
support.

## Background {:#background}

*Platforms* and *toolchains* were introduced to standardize how software
projects target different architectures and cross-compile.

This was
[inspired][Inspiration]{: .external}
by the observation that language maintainers were already doing this in ad
hoc, incompatible ways. For example, C++ rules used `--cpu` and
 `--crosstool_top` to declare a target CPU and toolchain. Neither of these
correctly models a "platform". This produced awkward and incorrect builds.

Java, Android, and other languages evolved their own flags for similar purposes,
none of which interoperated with each other. This made cross-language builds
confusing and complicated.

Bazel is intended for large, multi-language, multi-platform projects. This
demands more principled support for these concepts, including a clear
standard API.

### Need for migration {:#migration}

Upgrading to the new API requires two efforts: releasing the API and upgrading
rule logic to use it.

The first is done but the second is ongoing. This consists of ensuring
language-specific platforms and toolchains are defined, language logic reads
toolchains through the new API instead of old flags like `--crosstool_top`, and
`config_setting`s select on the new API instead of old flags.

This work is straightforward but requires a distinct effort for each language,
plus fair warning for project owners to test against upcoming changes.

This is why this is an ongoing migration.

### Goal {:#goal}

This migration is complete when all projects build with the form:

```posix-terminal
bazel build //:myproject --platforms=//:myplatform
```

This implies:

1. Your project's rules choose the right toolchains for `//:myplatform`.
1. Your project's dependencies choose the right toolchains for `//:myplatform`.
1. `//:myplatform` references
[common declarations][Common Platform Declarations]{: .external}
of `CPU`, `OS`, and other generic, language-independent properties
1. All relevant [`select()`s][select()] properly match `//:myplatform`.
1. `//:myplatform` is defined in a clear, accessible place: in your project's
repo if the platform is unique to your project, or some common place all
consuming projects can find it

Old flags like `--cpu`, `--crosstool_top`, and `--fat_apk_cpu` will be
deprecated and removed as soon as it's safe to do so.

Ultimately, this will be the *sole* way to configure architectures.


## Migrating your project {:#migrating-your-project}

If you build with languages that support platforms, your build should already
work with an invocation like:

```posix-terminal
bazel build //:myproject --platforms=//:myplatform
```

See [Status](#status) and your language's documentation for precise details.

If a language requires a flag to enable platform support, you also need to set
that flag. See [Status](#status) for details.

For your project to build, you need to check the following:

1. `//:myplatform` must exist. It's generally the project owner's responsibility
   to define platforms because different projects target different machines.
   See [Default platforms](#default-platforms).

1. The toolchains you want to use must exist. If using stock toolchains, the
   language owners should include instructions for how to register them. If
   writing your own custom toolchains, you need to [register](https://bazel.build/extending/toolchains#registering-building-toolchains) them in your
   `MODULE.bazel` file or with [`--extra_toolchains`](https://bazel.build/reference/command-line-reference#flag--extra_toolchains).

1. `select()`s and [configuration transitions][Starlark transitions] must
  resolve properly. See [select()](#select) and [Transitions](#transitions).

1. If your build mixes languages that do and don't support platforms, you may
   need platform mappings to help the legacy languages work with the new API.
   See [Platform mappings](#platform-mappings) for details.

If you still have problems, [reach out](#questions) for support.

### Default platforms {:#default-platforms}

Project owners should define explicit
[platforms][Defining Constraints and Platforms] to describe the architectures
they want to build for. These are then triggered with `--platforms`.

When `--platforms` isn't set, Bazel defaults to a `platform` representing the
local build machine. This is auto-generated at `@platforms//host` (aliased as
`@bazel_tools//tools:host_platform`)
so there's no need to explicitly define it. It maps the local machine's `OS`
and `CPU` with `constraint_value`s declared in
[`@platforms`](https://github.com/bazelbuild/platforms){: .external}.

### `select()` {:#select}

Projects can [`select()`][select()] on
[`constraint_value` targets][constraint_value Rule] but not complete
platforms. This is intentional so `select()` supports as wide a variety of
machines as possible. A library with `ARM`-specific sources should support *all*
`ARM`-powered machines unless there's reason to be more specific.

To select on one or more `constraint_value`s, use:

```python
config_setting(
    name = "is_arm",
    constraint_values = [
        "@platforms//cpu:arm",
    ],
)
```

This is equivalent to traditionally selecting on `--cpu`:

```python
config_setting(
    name = "is_arm",
    values = {
        "cpu": "arm",
    },
)
```

More details [here][select() Platforms].

`select`s on `--cpu`, `--crosstool_top`, etc. don't understand `--platforms`.
When migrating your project to platforms, you must either convert them to
`constraint_values` or use [platform mappings](#platform-mappings) to support
both styles during migration.

### Transitions {:#transitions}

[Starlark transitions][Starlark transitions] change
flags down parts of your build graph. If your project uses a transition that
sets `--cpu`, `--crossstool_top`, or other legacy flags, rules that read
`--platforms` won't see these changes.

When migrating your project to platforms, you must either convert changes like
`return { "//command_line_option:cpu": "arm" }` to `return {
"//command_line_option:platforms": "//:my_arm_platform" }` or use [platform
mappings](#platform-mappings) to support both styles during migration.
window.

## Migrating your rule set  {:#migrating-your-rule-set}

If you own a rule set and want to support platforms, you need to:

1. Have rule logic resolve toolchains with the toolchain API. See
   [toolchain API][Toolchains] (`ctx.toolchains`).

1. Optional: define an `--incompatible_enable_platforms_for_my_language` flag so
   rule logic alternately resolves toolchains through the new API or old flags
   like `--crosstool_top` during migration testing.

1. Define the relevant properties that make up platform components. See
   [Common platform properties](#common-platform-properties)

1. Define standard toolchains and make them accessible to users through your
   rule's registration instructions ([details](https://bazel.build/extending/toolchains#registering-building-toolchains))

1. Ensure [`select()`s](#select) and
   [configuration transitions](#transitions) support platforms. This is the
   biggest challenge. It's particularly challenging for multi-language projects
   (which may fail if *all* languages can't read `--platforms`).

If you need to mix with rules that don't support platforms, you may need
[platform mappings](#platform-mappings) to bridge the gap.

### Common platform properties {:#common-platform-properties}

Common, cross-language platform properties like `OS` and `CPU` should be
declared in [`@platforms`](https://github.com/bazelbuild/platforms){: .external}.
This encourages sharing, standardization, and cross-language compatibility.

Properties unique to your rules should be declared in your rule's repo. This
lets you maintain clear ownership over the specific concepts your rules are
responsible for.

If your rules use custom-purpose OSes or CPUs, these should be declared in your
rule's repo vs.
[`@platforms`](https://github.com/bazelbuild/platforms){: .external}.

## Platform mappings {:#platform-mappings}

*Platform mappings* is a temporary API that lets platform-aware logic mix with
legacy logic in the same build. This is a blunt tool that's only intended to
smooth incompatibilities with different migration timeframes.

Caution: Only use this if necessary, and expect to eventually  eliminate it.

A platform mapping is a map of either a `platform()` to a
corresponding set of legacy flags or the reverse. For example:

```python
platforms:
  # Maps "--platforms=//platforms:ios" to "--ios_multi_cpus=x86_64 --apple_platform_type=ios".
  //platforms:ios
    --ios_multi_cpus=x86_64
    --apple_platform_type=ios

flags:
  # Maps "--ios_multi_cpus=x86_64 --apple_platform_type=ios" to "--platforms=//platforms:ios".
  --ios_multi_cpus=x86_64
  --apple_platform_type=ios
    //platforms:ios

  # Maps "--cpu=darwin_x86_64 --apple_platform_type=macos" to "//platform:macos".
  --cpu=darwin_x86_64
  --apple_platform_type=macos
    //platforms:macos
```

Bazel uses this to guarantee all settings, both platform-based and
legacy, are consistently applied throughout the build, including through
[transitions](#transitions).

By default Bazel reads mappings from the `platform_mappings` file in your
workspace root. You can also set
`--platform_mappings=//:my_custom_mapping`.

See the [platform mappings design]{: .external} for details.

## API review {:#api-review}

A [`platform`][platform Rule] is a collection of
[`constraint_value` targets][constraint_value Rule]:

```python
platform(
    name = "myplatform",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:arm",
    ],
)
```

A [`constraint_value`][constraint_value Rule] is a machine
property. Values of the same "kind" are grouped under a common
[`constraint_setting`][constraint_setting Rule]:

```python
constraint_setting(name = "os")
constraint_value(
    name = "linux",
    constraint_setting = ":os",
)
constraint_value(
    name = "mac",
    constraint_setting = ":os",
)
```

A [`toolchain`][Toolchains] is a [Starlark rule][Starlark rule]. Its
attributes declare a language's tools (like `compiler =
"//mytoolchain:custom_gcc"`). Its [providers][Starlark Provider] pass
this information to rules that need to build with these tools.

Toolchains declare the `constraint_value`s of machines they can
[target][target_compatible_with Attribute]
(`target_compatible_with = ["@platforms//os:linux"]`) and machines their tools can
[run on][exec_compatible_with Attribute]
(`exec_compatible_with = ["@platforms//os:mac"]`).

When building `$ bazel build //:myproject --platforms=//:myplatform`, Bazel
automatically selects a toolchain that can run on the build machine and
build binaries for `//:myplatform`. This is known as *toolchain resolution*.

The set of available toolchains can be registered in the `MODULE.bazel` file
with [`register_toolchains`][register_toolchains Function] or at the
command line with [`--extra_toolchains`][extra_toolchains Flag].

For more information see [here][Toolchains].

## Questions {:#questions}

For general support and questions about the migration timeline, contact
[bazel-discuss]{: .external} or the owners of the appropriate rules.

For discussions on the design and evolution of the platform/toolchain APIs,
contact [bazel-dev]{: .external}.

## See also {:#see-also}

* [Configurable Builds - Part 1]{: .external}
* [Platforms]
* [Toolchains]
* [Bazel Platforms Cookbook]{: .external}
* [Platforms examples]{: .external}
* [Example C++ toolchain]{: .external}

[Android Rules]: /docs/bazel-and-android
[Apple Rules]: https://github.com/bazelbuild/rules_apple
[Background]: #background
[Bazel platforms Cookbook]: https://docs.google.com/document/d/1UZaVcL08wePB41ATZHcxQV4Pu1YfA1RvvWm8FbZHuW8/
[bazel-dev]: https://groups.google.com/forum/#!forum/bazel-dev
[bazel-discuss]: https://groups.google.com/forum/#!forum/bazel-discuss
[Common Platform Declarations]: https://github.com/bazelbuild/platforms
[constraint_setting Rule]: /reference/be/platforms-and-toolchains#constraint_setting
[constraint_value Rule]: /reference/be/platforms-and-toolchains#constraint_value
[Configurable Builds - Part 1]: https://blog.bazel.build/2019/02/11/configurable-builds-part-1.html
[Configuring C++ toolchains]: /tutorials/ccp-toolchain-config
[Defining Constraints and Platforms]: /extending/platforms#constraints-platforms
[Example C++ toolchain]: https://github.com/gregestren/snippets/tree/master/custom_cc_toolchain_with_platforms
[exec_compatible_with Attribute]: /reference/be/platforms-and-toolchains#toolchain.exec_compatible_with
[extra_toolchains Flag]: /reference/command-line-reference#flag--extra_toolchains
[Go Rules]: https://github.com/bazelbuild/rules_go
[Inspiration]: https://blog.bazel.build/2019/02/11/configurable-builds-part-1.html
[Migrating your rule set]: #migrating-your-rule-set
[Platforms]: /extending/platforms
[Platforms examples]: https://github.com/hlopko/bazel_platforms_examples
[platform mappings design]: https://docs.google.com/document/d/1Vg_tPgiZbSrvXcJ403vZVAGlsWhH9BUDrAxMOYnO0Ls/edit
[platform Rule]: /reference/be/platforms-and-toolchains#platform
[register_toolchains Function]: /rules/lib/globals/module#register_toolchains
[Rust rules]: https://github.com/bazelbuild/rules_rust
[select()]: /docs/configurable-attributes
[select() Platforms]: /docs/configurable-attributes#platforms
[Starlark provider]: /extending/rules#providers
[Starlark rule]: /extending/rules
[Starlark transitions]: /extending/config#user-defined-transitions
[target_compatible_with Attribute]: /reference/be/platforms-and-toolchains#toolchain.target_compatible_with
[Toolchains]: /extending/toolchains


Project: /_project.yaml
Book: /_book.yaml

# Labels

{% include "_buttons.html" %}

A **label** is an identifier for a target. A typical label in its full canonical
form looks like:

```none
@@myrepo//my/app/main:app_binary
```

The first part of the label is the repository name, `@@myrepo`. The double-`@`
syntax signifies that this is a [*canonical* repo
name](/external/overview#canonical-repo-name), which is unique within
the workspace. Labels with canonical repo names unambiguously identify a target
no matter which context they appear in.

Often the canonical repo name is an arcane string that looks like
`@@rules_java++toolchains+local_jdk`. What is much more commonly seen is
labels with an [*apparent* repo name](/external/overview#apparent-repo-name),
which looks like:

```
@myrepo//my/app/main:app_binary
```

The only difference is the repo name being prefixed with one `@` instead of two.
This refers to a repo with the apparent name `myrepo`, which could be different
based on the context this label appears in.

In the typical case that a label refers to the same repository from which
it is used, the repo name part may be omitted.  So, inside `@@myrepo` the first
label is usually written as

```
//my/app/main:app_binary
```

The second part of the label is the un-qualified package name
`my/app/main`, the path to the package
relative to the repository root.  Together, the repository name and the
un-qualified package name form the fully-qualified package name
`@@myrepo//my/app/main`. When the label refers to the same
package it is used in, the package name (and optionally, the colon)
may be omitted.  So, inside `@@myrepo//my/app/main`,
this label may be written either of the following ways:

```
app_binary
:app_binary
```

It is a matter of convention that the colon is omitted for files,
but retained for rules, but it is not otherwise significant.

The part of the label after the colon, `app_binary` is the un-qualified target
name. When it matches the last component of the package path, it, and the
colon, may be omitted.  So, these two labels are equivalent:

```
//my/app/lib
//my/app/lib:lib
```

The name of a file target in a subdirectory of the package is the file's path
relative to the package root (the directory containing the `BUILD` file). So,
this file is in the `my/app/main/testdata` subdirectory of the repository:

```
//my/app/main:testdata/input.txt
```

Strings like `//my/app` and `@@some_repo//my/app` have two meanings depending on
the context in which they are used: when Bazel expects a label, they mean
`//my/app:app` and `@@some_repo//my/app:app`, respectively. But, when Bazel
expects a package (e.g. in `package_group` specifications), they reference the
package that contains that label.

A common mistake in `BUILD` files is using `//my/app` to refer to a package, or
to *all* targets in a package--it does not.  Remember, it is
equivalent to `//my/app:app`, so it names the `app` target in the `my/app`
package of the current repository.

However, the use of `//my/app` to refer to a package is encouraged in the
specification of a `package_group` or in `.bzl` files, because it clearly
communicates that the package name is absolute and rooted in the top-level
directory of the workspace.

Relative labels cannot be used to refer to targets in other packages; the
repository identifier and package name must always be specified in this case.
For example, if the source tree contains both the package `my/app` and the
package `my/app/testdata` (each of these two directories has its own
`BUILD` file), the latter package contains a file named `testdepot.zip`. Here
are two ways (one wrong, one correct) to refer to this file within
`//my/app:BUILD`:

<p><span class="compare-worse">Wrong</span> — <code>testdata</code> is a different package, so you can't use a relative path</p>
<pre class="prettyprint">testdata/testdepot.zip</pre>

<p><span class="compare-better">Correct</span> — refer to <code>testdata</code> with its full path</p>

<pre class="prettyprint">//my/app/testdata:testdepot.zip</pre>



Labels starting with `@@//` are references to the main
repository, which will still work even from external repositories.
Therefore `@@//a/b/c` is different from
`//a/b/c` when referenced from an external repository.
The former refers back to the main repository, while the latter
looks for `//a/b/c` in the external repository itself.
This is especially relevant when writing rules in the main
repository that refer to targets in the main repository, and will be
used from external repositories.

For information about the different ways you can refer to targets, see
[target patterns](/run/build#specifying-build-targets).

### Lexical specification of a label {:#labels-lexical-specification}

Label syntax discourages use of metacharacters that have special meaning to the
shell. This helps to avoid inadvertent quoting problems, and makes it easier to
construct tools and scripts that manipulate labels, such as the
[Bazel Query Language](/query/language).

The precise details of allowed target names are below.

### Target names — `{{ "<var>" }}package-name{{ "</var>" }}:target-name` {:#target-names}

`target-name` is the name of the target within the package. The name of a rule
is the value of the `name` attribute in the rule's declaration in a `BUILD`
file; the name of a file is its pathname relative to the directory containing
the `BUILD` file.

Target names must be composed entirely of characters drawn from the set `a`–`z`,
`A`–`Z`, `0`–`9`, and the punctuation symbols `!%-@^_"#$&'()*-+,;<=>?[]{|}~/.`.

Filenames must be relative pathnames in normal form, which means they must
neither start nor end with a slash (for example, `/foo` and `foo/` are
forbidden) nor contain multiple consecutive slashes as path separators
(for example, `foo//bar`). Similarly, up-level references (`..`) and
current-directory references (`./`) are forbidden.

<p><span class="compare-worse">Wrong</span> — Do not use <code>..</code> to refer to files in other packages</p>

<p><span class="compare-better">Correct</span> — Use
  <code>//{{ "<var>" }}package-name{{ "</var>" }}:{{ "<var>" }}filename{{ "</var>" }}</code></p>


While it is common to use `/` in the name of a file target, avoid the use of
`/` in the names of rules. Especially when the shorthand form of a label is
used, it may confuse the reader. The label `//foo/bar/wiz` is always a shorthand
for `//foo/bar/wiz:wiz`, even if there is no such package `foo/bar/wiz`; it
never refers to `//foo:bar/wiz`, even if that target exists.

However, there are some situations where use of a slash is convenient, or
sometimes even necessary. For example, the name of certain rules must match
their principal source file, which may reside in a subdirectory of the package.

### Package names — `//package-name:{{ "<var>" }}target-name{{ "</var>" }}` {:#package-names}

The name of a package is the name of the directory containing its `BUILD` file,
relative to the top-level directory of the containing repository.
For example: `my/app`.

On a technical level, Bazel enforces the following:

* Allowed characters in package names are the lowercase letters `a` through `z`,
  the uppercase letters `A` through `Z`, the digits `0` through `9`, the
  characters ``! \"#$%&'()*+,-.;<=>?@[]^_`{|}`` (yes, there's a space character
  in there!), and of course forward slash `/` (since it's the directory
  separator).
* Package names may not start or end with a forward slash character `/`.
* Package names may not contain the substring `//`. This wouldn't make
  sense---what would the corresponding directory path be?
* Package names may not contain the substring `/./` or `/../` or `/.../` etc.
  This enforcement is done to avoid confusion when translating between a logical
  package name and a physical directory name, given the semantic meaning of the
  dot character in path strings.

On a practical level:

* For a language with a directory structure that is significant to its module
  system (for example, Java), it's important to choose directory names that are
  valid identifiers in the language. For example, don't start with a leading
  digit and avoid special characters, especially underscores and hyphens.
* Although Bazel supports targets in the workspace's root package (for example,
  `//:foo`), it's best to leave that package empty so all meaningful packages
  have descriptive names.

## Rules {:#rules}

A rule specifies the relationship between inputs and outputs, and the
steps to build the outputs. Rules can be of one of many different
kinds (sometimes called the _rule class_), which produce compiled
executables and libraries, test executables and other supported
outputs as described in the [Build Encyclopedia](/reference/be/overview).

`BUILD` files declare _targets_ by invoking _rules_.

In the example below, we see the declaration of the target `my_app`
using the `cc_binary` rule.

```python
cc_binary(
    name = "my_app",
    srcs = ["my_app.cc"],
    deps = [
        "//absl/base",
        "//absl/strings",
    ],
)
```

Every rule invocation has a `name` attribute (which must be a valid
[target name](#target-names)), that declares a target within the package
of the `BUILD` file.

Every rule has a set of _attributes_; the applicable attributes for a given
rule, and the significance and semantics of each attribute are a function of
the rule's kind; see the [Build Encyclopedia](/reference/be/overview) for a
list of rules and their corresponding attributes. Each attribute has a name and
a type. Some of the common types an attribute can have are integer, label, list
of labels, string, list of strings, output label, list of output labels. Not
all attributes need to be specified in every rule. Attributes thus form a
dictionary from keys (names) to optional, typed values.

The `srcs` attribute present in many rules has type "list of labels"; its
value, if present, is a list of labels, each being the name of a target that is
an input to this rule.

In some cases, the name of the rule kind is somewhat arbitrary, and more
interesting are the names of the files generated by the rule, and this is true
of genrules. For more information, see
[General Rules: genrule](/reference/be/general#genrule).

In other cases, the name is significant: for `*_binary` and `*_test` rules,
for example, the rule name determines the name of the executable produced by
the build.

This directed acyclic graph over targets is called the _target graph_ or
_build dependency graph_, and is the domain over which the
[Bazel Query tool](/query/guide) operates.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-ref">
        <span class="material-icons" aria-hidden="true">arrow_back</span>Targets</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-files">
        BUILD files<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>


Project: /_project.yaml
Book: /_book.yaml

# Visibility

{% include "_buttons.html" %}

This page covers Bazel's two visibility systems:
[target visibility](#target-visibility) and [load visibility](#load-visibility).

Both types of visibility help other developers distinguish between your
library's public API and its implementation details, and help enforce structure
as your workspace grows. You can also use visibility when deprecating a public
API to allow current users while denying new ones.

## Target visibility {:#target-visibility}

**Target visibility** controls who may depend on your target — that is, who may
use your target's label inside an attribute such as `deps`. A target will fail
to build during the [analysis](/reference/glossary#analysis-phase) phase if it
violates the visibility of one of its dependencies.

Generally, a target `A` is visible to a target `B` if they are in the same
location, or if `A` grants visibility to `B`'s location. In the absence of
[symbolic macros](/extending/macros), the term "location" can be simplified
to just "package"; see [below](#symbolic-macros) for more on symbolic macros.

Visibility is specified by listing allowed packages. Allowing a package does not
necessarily mean that its subpackages are also allowed. For more details on
packages and subpackages, see [Concepts and terminology](/concepts/build-ref).

For prototyping, you can disable target visibility enforcement by setting the
flag `--check_visibility=false`. This shouldn't be done for production usage in
submitted code.

The primary way to control visibility is with a rule's
[`visibility`](/reference/be/common-definitions#common.visibility) attribute.
The following subsections describe the attribute's format, how to apply it to
various kinds of targets, and the interaction between the visibility system and
symbolic macros.

### Visibility specifications {:#visibility-specifications}

All rule targets have a `visibility` attribute that takes a list of labels. Each
label has one of the following forms. With the exception of the last form, these
are just syntactic placeholders that don't correspond to any actual target.

*   `"//visibility:public"`: Grants access to all packages.

*   `"//visibility:private"`: Does not grant any additional access; only targets
    in this location's package can use this target.

*   `"//foo/bar:__pkg__"`: Grants access to `//foo/bar` (but not its
    subpackages).

*   `"//foo/bar:__subpackages__"`: Grants access to `//foo/bar` and all of its
    direct and indirect subpackages.

*   `"//some_pkg:my_package_group"`: Grants access to all of the packages that
    are part of the given [`package_group`](/reference/be/functions#package_group).

    *   Package groups use a
        [different syntax](/reference/be/functions#package_group.packages) for
        specifying packages. Within a package group, the forms
        `"//foo/bar:__pkg__"` and `"//foo/bar:__subpackages__"` are respectively
        replaced by `"//foo/bar"` and `"//foo/bar/..."`. Likewise,
        `"//visibility:public"` and `"//visibility:private"` are just `"public"`
        and `"private"`.

For example, if `//some/package:mytarget` has its `visibility` set to
`[":__subpackages__", "//tests:__pkg__"]`, then it could be used by any target
that is part of the `//some/package/...` source tree, as well as targets
declared in `//tests/BUILD`, but not by targets defined in
`//tests/integration/BUILD`.

**Best practice:** To make several targets visible to the same set
of packages, use a `package_group` instead of repeating the list in each
target's `visibility` attribute. This increases readability and prevents the
lists from getting out of sync.

**Best practice:** When granting visibility to another team's project, prefer
`__subpackages__` over `__pkg__` to avoid needless visibility churn as that
project evolves and adds new subpackages.

Note: The `visibility` attribute may not specify non-`package_group` targets.
Doing so triggers a "Label does not refer to a package group" or "Cycle in
dependency graph" error.

### Rule target visibility {:#rule-target-visibility}

A rule target's visibility is determined by taking its `visibility` attribute
-- or a suitable default if not given -- and appending the location where the
target was declared. For targets not declared in a symbolic macro, if the
package specifies a [`default_visibility`](/reference/be/functions#package.default_visibility),
this default is used; for all other packages and for targets declared in a
symbolic macro, the default is just `["//visibility:private"]`.

```starlark
# //mypkg/BUILD

package(default_visibility = ["//friend:__pkg__"])

cc_library(
    name = "t1",
    ...
    # No visibility explicitly specified.
    # Effective visibility is ["//friend:__pkg__", "//mypkg:__pkg__"].
    # If no default_visibility were given in package(...), the visibility would
    # instead default to ["//visibility:private"], and the effective visibility
    # would be ["//mypkg:__pkg__"].
)

cc_library(
    name = "t2",
    ...
    visibility = [":clients"],
    # Effective visibility is ["//mypkg:clients, "//mypkg:__pkg__"], which will
    # expand to ["//another_friend:__subpackages__", "//mypkg:__pkg__"].
)

cc_library(
    name = "t3",
    ...
    visibility = ["//visibility:private"],
    # Effective visibility is ["//mypkg:__pkg__"]
)

package_group(
    name = "clients",
    packages = ["//another_friend/..."],
)
```

**Best practice:** Avoid setting `default_visibility` to public. It may be
convenient for prototyping or in small codebases, but the risk of inadvertently
creating public targets increases as the codebase grows. It's better to be
explicit about which targets are part of a package's public interface.

### Generated file target visibility {:#generated-file-target-visibility}

A generated file target has the same visibility as the rule target that
generates it.

```starlark
# //mypkg/BUILD

java_binary(
    name = "foo",
    ...
    visibility = ["//friend:__pkg__"],
)
```

```starlark
# //friend/BUILD

some_rule(
    name = "bar",
    deps = [
        # Allowed directly by visibility of foo.
        "//mypkg:foo",
        # Also allowed. The java_binary's "_deploy.jar" implicit output file
        # target the same visibility as the rule target itself.
        "//mypkg:foo_deploy.jar",
    ]
    ...
)
```

### Source file target visibility {:#source-file-target-visibility}

Source file targets can either be explicitly declared using
[`exports_files`](/reference/be/functions#exports_files), or implicitly created
by referring to their filename in a label attribute of a rule (outside of a
symbolic macro). As with rule targets, the location of the call to
`exports_files`, or the BUILD file that referred to the input file, is always
automatically appended to the file's visibility.

Files declared by `exports_files` can have their visibility set by the
`visibility` parameter to that function. If this parameter is not given, the visibility is public.

Note: `exports_files` may not be used to override the visibility of a generated
file.

For files that do not appear in a call to `exports_files`, the visibility
depends on the value of the flag
[`--incompatible_no_implicit_file_export`](https://github.com/bazelbuild/bazel/issues/10225){: .external}:

*   If the flag is true, the visibility is private.

*   Else, the legacy behavior applies: The visibility is the same as the
    `BUILD` file's `default_visibility`, or private if a default visibility is
    not specified.

Avoid relying on the legacy behavior. Always write an `exports_files`
declaration whenever a source file target needs non-private visibility.

**Best practice:** When possible, prefer to expose a rule target rather than a
source file. For example, instead of calling `exports_files` on a `.java` file,
wrap the file in a non-private `java_library` target. Generally, rule targets
should only directly reference source files that live in the same package.

#### Example {:#source-file-visibility-example}

File `//frobber/data/BUILD`:

```starlark
exports_files(["readme.txt"])
```

File `//frobber/bin/BUILD`:

```starlark
cc_binary(
  name = "my-program",
  data = ["//frobber/data:readme.txt"],
)
```

### Config setting visibility {:#config-setting-visibility}

Historically, Bazel has not enforced visibility for
[`config_setting`](/reference/be/general#config_setting) targets that are
referenced in the keys of a [`select()`](/reference/be/functions#select). There
are two flags to remove this legacy behavior:

*   [`--incompatible_enforce_config_setting_visibility`](https://github.com/bazelbuild/bazel/issues/12932){: .external}
    enables visibility checking for these targets. To assist with migration, it
    also causes any `config_setting` that does not specify a `visibility` to be
    considered public (regardless of package-level `default_visibility`).

*   [`--incompatible_config_setting_private_default_visibility`](https://github.com/bazelbuild/bazel/issues/12933){: .external}
    causes `config_setting`s that do not specify a `visibility` to respect the
    package's `default_visibility` and to fallback on private visibility, just
    like any other rule target. It is a no-op if
    `--incompatible_enforce_config_setting_visibility` is not set.

Avoid relying on the legacy behavior. Any `config_setting` that is intended to
be used outside the current package should have an explicit `visibility`, if the
package does not already specify a suitable `default_visibility`.

### Package group target visibility {:#package-group-target-visibility}

`package_group` targets do not have a `visibility` attribute. They are always
publicly visible.

### Visibility of implicit dependencies {:#visibility-implicit-dependencies}

Some rules have [implicit dependencies](/extending/rules#private_attributes_and_implicit_dependencies) —
dependencies that are not spelled out in a `BUILD` file but are inherent to
every instance of that rule. For example, a `cc_library` rule might create an
implicit dependency from each of its rule targets to an executable target
representing a C++ compiler.

The visibility of such an implicit dependency is checked with respect to the
package containing the `.bzl` file in which the rule (or aspect) is defined. In
our example, the C++ compiler could be private so long as it lives in the same
package as the definition of the `cc_library` rule. As a fallback, if the
implicit dependency is not visible from the definition, it is checked with
respect to the `cc_library` target.

If you want to restrict the usage of a rule to certain packages, use
[load visibility](#load-visibility) instead.

### Visibility and symbolic macros {:#symbolic-macros}

This section describes how the visibility system interacts with
[symbolic macros](/extending/macros).

#### Locations within symbolic macros {:#locations-within-symbolic-macros}

A key detail of the visibility system is how we determine the location of a
declaration. For targets that are not declared in a symbolic macro, the location
is just the package where the target lives -- the package of the `BUILD` file.
But for targets created in a symbolic macro, the location is the package
containing the `.bzl` file where the macro's definition (the
`my_macro = macro(...)` statement) appears. When a target is created inside
multiple nested targets, it is always the innermost symbolic macro's definition
that is used.

The same system is used to determine what location to check against a given
dependency's visibility. If the consuming target was created inside a macro, we
look at the innermost macro's definition rather than the package the consuming
target lives in.

This means that all macros whose code is defined in the same package are
automatically "friends" with one another. Any target directly created by a macro
defined in `//lib:defs.bzl` can be seen from any other macro defined in `//lib`,
regardless of what packages the macros are actually instantiated in. Likewise,
they can see, and can be seen by, targets declared directly in `//lib/BUILD` and
its legacy macros. Conversely, targets that live in the same package cannot
necessarily see one another if at least one of them is created by a symbolic
macro.

Within a symbolic macro's implementation function, the `visibility` parameter
has the effective value of the macro's `visibility` attribute after appending
the location where the macro was called. The standard way for a macro to export
one of its targets to its caller is to forward this value along to the target's
declaration, as in `some_rule(..., visibility = visibility)`. Targets that omit
this attribute won't be visible to the caller of the macro unless the caller
happens to be in the same package as the macro definition. This behavior
composes, in the sense that a chain of nested calls to submacros may each pass
`visibility = visibility`, re-exporting the inner macro's exported targets to
the caller at each level, without exposing any of the macros' implementation
details.

#### Delegating privileges to a submacro {:#delegating-privileges-to-a-submacro}

The visibility model has a special feature to allow a macro to delegate its
permissions to a submacro. This is important for factoring and composing macros.

Suppose you have a macro `my_macro` that creates a dependency edge using a rule
`some_library` from another package:

```starlark
# //macro/defs.bzl
load("//lib:defs.bzl", "some_library")

def _impl(name, visibility, ...):
    ...
    native.genrule(
        name = name + "_dependency"
        ...
    )
    some_library(
        name = name + "_consumer",
        deps = [name + "_dependency"],
        ...
    )

my_macro = macro(implementation = _impl, ...)
```

```starlark
# //pkg/BUILD

load("//macro:defs.bzl", "my_macro")

my_macro(name = "foo", ...)
```

The `//pkg:foo_dependency` target has no `visibility` specified, so it is only
visible within `//macro`, which works fine for the consuming target. Now, what
happens if the author of `//lib` refactors `some_library` to instead be
implemented using a macro?

```starlark
# //lib:defs.bzl

def _impl(name, visibility, deps, ...):
    some_rule(
        # Main target, exported.
        name = name,
        visibility = visibility,
        deps = deps,
        ...)

some_library = macro(implementation = _impl, ...)
```

With this change, `//pkg:foo_consumer`'s location is now `//lib` rather than
`//macro`, so its usage of `//pkg:foo_dependency` violates the dependency's
visibility. The author of `my_macro` can't be expected to pass
`visibility = ["//lib"]` to the declaration of the dependency just to work
around this implementation detail.

For this reason, when a dependency of a target is also an attribute value of the
macro that declared the target, we check the dependency's visibility against the
location of the macro instead of the location of the consuming target.

In this example, to validate whether `//pkg:foo_consumer` can see
`//pkg:foo_dependency`, we see that `//pkg:foo_dependency` was also passed as an
input to the call to `some_library` inside of `my_macro`, and instead check the
dependency's visibility against the location of this call, `//macro`.

This process can repeat recursively, as long as a target or macro declaration is
inside of another symbolic macro taking the dependency's label in one of its
label-typed attributes.

Note: Visibility delegation does not work for labels that were not passed into
the macro, such as labels derived by string manipulation.

#### Finalizers {:#finalizers}

Targets declared in a rule finalizer (a symbolic macro with `finalizer = True`),
in addition to seeing targets following the usual symbolic macro visibility
rules, can *also* see all targets which are visible to the finalizer target's
package.

In other words, if you migrate a `native.existing_rules()`-based legacy macro to
a finalizer, the targets declared by the finalizer will still be able to see
their old dependencies.

It is possible to define targets that a finalizer can introspect using
`native.existing_rules()`, but which it cannot use as dependencies under the
visibility system. For example, if a macro-defined target is not visible to its
own package or to the finalizer macro's definition, and is not delegated to the
finalizer, the finalizer cannot see such a target. Note, however, that a
`native.existing_rules()`-based legacy macro will also be unable to see such a
target.

## Load visibility {:#load-visibility}

**Load visibility** controls whether a `.bzl` file may be loaded from other
`BUILD` or `.bzl` files outside the current package.

In the same way that target visibility protects source code that is encapsulated
by targets, load visibility protects build logic that is encapsulated by `.bzl`
files. For instance, a `BUILD` file author might wish to factor some repetitive
target declarations into a macro in a `.bzl` file. Without the protection of
load visibility, they might find their macro reused by other collaborators in
the same workspace, so that modifying the macro breaks other teams' builds.

Note that a `.bzl` file may or may not have a corresponding source file target.
If it does, there is no guarantee that the load visibility and the target
visibility coincide. That is, the same `BUILD` file might be able to load the
`.bzl` file but not list it in the `srcs` of a [`filegroup`](/reference/be/general#filegroup),
or vice versa. This can sometimes cause problems for rules that wish to consume
`.bzl` files as source code, such as for documentation generation or testing.

For prototyping, you may disable load visibility enforcement by setting
`--check_bzl_visibility=false`. As with `--check_visibility=false`, this should
not be done for submitted code.

Load visibility is available as of Bazel 6.0.

### Declaring load visibility {:#declaring-load-visibility}

To set the load visibility of a `.bzl` file, call the
[`visibility()`](/rules/lib/globals/bzl#visibility) function from within the file.
The argument to `visibility()` is a list of package specifications, just like
the [`packages`](/reference/be/functions#package_group.packages) attribute of
`package_group`. However, `visibility()` does not accept negative package
specifications.

The call to `visibility()` must only occur once per file, at the top level (not
inside a function), and ideally immediately following the `load()` statements.

Unlike target visibility, the default load visibility is always public. Files
that do not call `visibility()` are always loadable from anywhere in the
workspace. It is a good idea to add `visibility("private")` to the top of any
new `.bzl` file that is not specifically intended for use outside the package.

### Example {:#load-visibility-example}

```starlark
# //mylib/internal_defs.bzl

# Available to subpackages and to mylib's tests.
visibility(["//mylib/...", "//tests/mylib/..."])

def helper(...):
    ...
```

```starlark
# //mylib/rules.bzl

load(":internal_defs.bzl", "helper")
# Set visibility explicitly, even though public is the default.
# Note the [] can be omitted when there's only one entry.
visibility("public")

myrule = rule(
    ...
)
```

```starlark
# //someclient/BUILD

load("//mylib:rules.bzl", "myrule")          # ok
load("//mylib:internal_defs.bzl", "helper")  # error

...
```

### Load visibility practices {:#load-visibility-practices}

This section describes tips for managing load visibility declarations.

#### Factoring visibilities {:#factoring-visibilities}

When multiple `.bzl` files should have the same visibility, it can be helpful to
factor their package specifications into a common list. For example:

```starlark
# //mylib/internal_defs.bzl

visibility("private")

clients = [
    "//foo",
    "//bar/baz/...",
    ...
]
```

```starlark
# //mylib/feature_A.bzl

load(":internal_defs.bzl", "clients")
visibility(clients)

...
```

```starlark
# //mylib/feature_B.bzl

load(":internal_defs.bzl", "clients")
visibility(clients)

...
```

This helps prevent accidental skew between the various `.bzl` files'
visibilities. It also is more readable when the `clients` list is large.

#### Composing visibilities {:#composing-visibilities}

Sometimes a `.bzl` file might need to be visible to an allowlist that is
composed of multiple smaller allowlists. This is analogous to how a
`package_group` can incorporate other `package_group`s via its
[`includes`](/reference/be/functions#package_group.includes) attribute.

Suppose you are deprecating a widely used macro. You want it to be visible only
to existing users and to the packages owned by your own team. You might write:

```starlark
# //mylib/macros.bzl

load(":internal_defs.bzl", "our_packages")
load("//some_big_client:defs.bzl", "their_remaining_uses")

# List concatenation. Duplicates are fine.
visibility(our_packages + their_remaining_uses)
```

#### Deduplicating with package groups {:#deduplicating-with-package-groups}

Unlike target visibility, you cannot define a load visibility in terms of a
`package_group`. If you want to reuse the same allowlist for both target
visibility and load visibility, it's best to move the list of package
specifications into a .bzl file, where both kinds of declarations may refer to
it. Building off the example in [Factoring visibilities](#factoring-visibilities)
above, you might write:

```starlark
# //mylib/BUILD

load(":internal_defs", "clients")

package_group(
    name = "my_pkg_grp",
    packages = clients,
)
```

This only works if the list does not contain any negative package
specifications.

#### Protecting individual symbols {:#protecting-individual-symbols}

Any Starlark symbol whose name begins with an underscore cannot be loaded from
another file. This makes it easy to create private symbols, but does not allow
you to share these symbols with a limited set of trusted files. On the other
hand, load visibility gives you control over what other packages may see your
`.bzl file`, but does not allow you to prevent any non-underscored symbol from
being loaded.

Luckily, you can combine these two features to get fine-grained control.

```starlark
# //mylib/internal_defs.bzl

# Can't be public, because internal_helper shouldn't be exposed to the world.
visibility("private")

# Can't be underscore-prefixed, because this is
# needed by other .bzl files in mylib.
def internal_helper(...):
    ...

def public_util(...):
    ...
```

```starlark
# //mylib/defs.bzl

load(":internal_defs", "internal_helper", _public_util="public_util")
visibility("public")

# internal_helper, as a loaded symbol, is available for use in this file but
# can't be imported by clients who load this file.
...

# Re-export public_util from this file by assigning it to a global variable.
# We needed to import it under a different name ("_public_util") in order for
# this assignment to be legal.
public_util = _public_util
```

#### bzl-visibility Buildifier lint {:#bzl-visibility-buildifier-lint}

There is a [Buildifier lint](https://github.com/bazelbuild/buildtools/blob/master/WARNINGS.md#bzl-visibility)
that provides a warning if users load a file from a directory named `internal`
or `private`, when the user's file is not itself underneath the parent of that
directory. This lint predates the load visibility feature and is unnecessary in
workspaces where `.bzl` files declare visibilities.


Project: /_project.yaml
Book: /_book.yaml

# BUILD files

{% include "_buttons.html" %}

The previous sections described packages, targets and labels, and the
build dependency graph abstractly. This section describes the concrete syntax
used to define a package.

By definition, every package contains a `BUILD` file, which is a short
program.

Note: The `BUILD` file can be named either `BUILD` or `BUILD.bazel`. If both
files exist, `BUILD.bazel` takes precedence over `BUILD`.
For simplicity's sake, the documentation refers to these files simply as `BUILD`
files.

`BUILD` files are evaluated using an imperative language,
[Starlark](https://github.com/bazelbuild/starlark/){: .external}.

They are interpreted as a sequential list of statements.

In general, order does matter: variables must be defined before they are
used, for example. However, most `BUILD` files consist only of declarations of
build rules, and the relative order of these statements is immaterial; all
that matters is _which_ rules were declared, and with what values, by the
time package evaluation completes.

When a build rule function, such as `cc_library`, is executed, it creates a
new target in the graph. This target can later be referred using a label.

In simple `BUILD` files, rule declarations can be re-ordered freely without
changing the behavior.

To encourage a clean separation between code and data, `BUILD` files cannot
contain function definitions, `for` statements or `if` statements (but list
comprehensions and `if` expressions are allowed). Functions can be declared in
`.bzl` files instead. Additionally, `*args` and `**kwargs` arguments are not
allowed in `BUILD` files; instead list all the arguments explicitly.

Crucially, programs in Starlark can't perform arbitrary I/O. This invariant
makes the interpretation of `BUILD` files hermetic — dependent only on a known
set of inputs, which is essential for ensuring that builds are reproducible.
For more details, see [Hermeticity](/basics/hermeticity).

Because `BUILD` files need to be updated whenever the dependencies of the
underlying code change, they are typically maintained by multiple people on a
team. `BUILD` file authors should comment liberally to document the role
of each build target, whether or not it is intended for public use, and to
document the role of the package itself.

## Loading an extension {:#load}

Bazel extensions are files ending in `.bzl`. Use the `load` statement to import
a symbol from an extension.

```
load("//foo/bar:file.bzl", "some_library")
```

This code loads the file `foo/bar/file.bzl` and adds the `some_library` symbol
to the environment. This can be used to load new rules, functions, or constants
(for example, a string or a list). Multiple symbols can be imported by using
additional arguments to the call to `load`. Arguments must be string literals
(no variable) and `load` statements must appear at top-level — they cannot be
in a function body.

The first argument of `load` is a [label](/concepts/labels) identifying a
`.bzl` file. If it's a relative label, it is resolved with respect to the
package (not directory) containing the current `bzl` file. Relative labels in
`load` statements should use a leading `:`.

`load` also supports aliases, therefore, you can assign different names to the
imported symbols.

```
load("//foo/bar:file.bzl", library_alias = "some_library")
```

You can define multiple aliases within one `load` statement. Moreover, the
argument list can contain both aliases and regular symbol names. The following
example is perfectly legal (please note when to use quotation marks).

```
load(":my_rules.bzl", "some_rule", nice_alias = "some_other_rule")
```

In a `.bzl` file, symbols starting with `_` are not exported and cannot be
loaded from another file.

You can use [load visibility](/concepts/visibility#load-visibility) to restrict
who may load a `.bzl` file.

## Types of build rules {:#types-of-build-rules}

The majority of build rules come in families, grouped together by
language. For example, `cc_binary`, `cc_library`
and `cc_test` are the build rules for C++ binaries,
libraries, and tests, respectively. Other languages use the same
naming scheme, with a different prefix, such as `java_*` for
Java. Some of these functions are documented in the
[Build Encyclopedia](/reference/be/overview), but it is possible
for anyone to create new rules.

* `*_binary` rules build executable programs in a given language. After a
  build, the executable will reside in the build tool's binary
  output tree at the corresponding name for the rule's label,
  so `//my:program` would appear at (for example) `$(BINDIR)/my/program`.

  In some languages, such rules also create a runfiles directory
  containing all the files mentioned in a `data`
  attribute belonging to the rule, or any rule in its transitive
  closure of dependencies; this set of files is gathered together in
  one place for ease of deployment to production.

* `*_test` rules are a specialization of a `*_binary` rule, used for automated
  testing. Tests are simply programs that return zero on success.

  Like binaries, tests also have runfiles trees, and the files
  beneath it are the only files that a test may legitimately open
  at runtime. For example, a program `cc_test(name='x',
  data=['//foo:bar'])` may open and read `$TEST_SRCDIR/workspace/foo/bar` during execution.
  (Each programming language has its own utility function for
  accessing the value of `$TEST_SRCDIR`, but they are all
  equivalent to using the environment variable directly.)
  Failure to observe the rule will cause the test to fail when it is
  executed on a remote testing host.

* `*_library` rules specify separately-compiled modules in the given
    programming language. Libraries can depend on other libraries,
    and binaries and tests can depend on libraries, with the expected
    separate-compilation behavior.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/labels">
        <span class="material-icons" aria-hidden="true">arrow_back</span>Labels</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/dependencies">
        Dependencies<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>

## File encoding

`BUILD` and `.bzl` files should be encoded in UTF-8, of which ASCII is a valid
subset. Arbitrary byte sequences are currently allowed, but may stop being
supported in the future.


Project: /_project.yaml
Book: /_book.yaml

# Dependencies

{% include "_buttons.html" %}

A target `A` _depends upon_ a target `B` if `B` is needed by `A` at build or
execution time. The _depends upon_ relation induces a
[Directed Acyclic Graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph){: .external}
(DAG) over targets, and it is called a _dependency graph_.

A target's _direct_ dependencies are those other targets reachable by a path
of length 1 in the dependency graph. A target's _transitive_ dependencies are
those targets upon which it depends via a path of any length through the graph.

In fact, in the context of builds, there are two dependency graphs, the graph
of _actual dependencies_ and the graph of _declared dependencies_. Most of the
time, the two graphs are so similar that this distinction need not be made, but
it is useful for the discussion below.

## Actual and declared dependencies {:#actual-and-declared-dependencies}

A target `X` is _actually dependent_ on target `Y` if `Y` must be present,
built, and up-to-date in order for `X` to be built correctly. _Built_ could
mean generated, processed, compiled, linked, archived, compressed, executed, or
any of the other kinds of tasks that routinely occur during a build.

A target `X` has a _declared dependency_ on target `Y` if there is a dependency
edge from `X` to `Y` in the package of `X`.

For correct builds, the graph of actual dependencies _A_ must be a subgraph of
the graph of declared dependencies _D_. That is, every pair of
directly-connected nodes `x --> y` in _A_ must also be directly connected in
_D_. It can be said that _D_ is an _overapproximation_ of _A_.

Important: _D_ should not be too much of an overapproximation of _A_ because
redundant declared dependencies can make builds slower and binaries larger.

`BUILD` file writers must explicitly declare all of the actual direct
dependencies for every rule to the build system, and no more.

Failure to observe this principle causes undefined behavior: the build may fail,
but worse, the build may depend on some prior operations, or upon transitive
declared dependencies the target happens to have. Bazel checks for missing
dependencies and report errors, but it's not possible for this checking to be
complete in all cases.

You need not (and should not) attempt to list everything indirectly imported,
even if it is _needed_ by `A` at execution time.

During a build of target `X`, the build tool inspects the entire transitive
closure of dependencies of `X` to ensure that any changes in those targets are
reflected in the final result, rebuilding intermediates as needed.

The transitive nature of dependencies leads to a common mistake. Sometimes,
code in one file may use code provided by an _indirect_ dependency — a
transitive but not direct edge in the declared dependency graph. Indirect
dependencies don't appear in the `BUILD` file. Because the rule doesn't
directly depend on the provider, there is no way to track changes, as shown in
the following example timeline:

### 1. Declared dependencies match actual dependencies {:#this-is-fine}

At first, everything works. The code in package `a` uses code in package `b`.
The code in package `b` uses code in package `c`, and thus `a` transitively
depends on `c`.

<table class="cyan">
  <tr>
    <th><code>a/BUILD</code></th>
    <th><code><strong>b</strong>/BUILD</code></th>
  </tr>
  <tr>
    <td>
      <pre>rule(
    name = "a",
    srcs = "a.in",
    deps = "//b:b",
)
      </pre>
    </td>
    <td>
      <pre>
rule(
    name = "b",
    srcs = "b.in",
    deps = "//c:c",
)
      </pre>
    </td>
  </tr>
  <tr class="alt">
    <td><code>a / a.in</code></td>
    <td><code>b / b.in</code></td>
  </tr>
  <tr>
    <td><pre>
import b;
b.foo();
    </pre>
    </td>
    <td>
      <pre>
import c;
function foo() {
  c.bar();
}
      </pre>
    </td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Declared dependency graph with arrows connecting a, b, and c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Actual dependency graph that matches the declared dependency
                  graph with arrows connecting a, b, and c">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependencies overapproximate the actual dependencies. All is well.

### 2. Adding an undeclared dependency {:#undeclared-dependency}

A latent hazard is introduced when someone adds code to `a` that creates a
direct _actual_ dependency on `c`, but forgets to declare it in the build file
`a/BUILD`.

<table class="cyan">
  <tr>
    <th><code>a / a.in</code></th>
    <th>&nbsp;</th>
  </tr>
  <tr>
    <td>
      <pre>
        import b;
        import c;
        b.foo();
        c.garply();
      </pre>
    </td>
    <td>&nbsp;</td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Declared dependency graph with arrows connecting a, b, and c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_c_ac.svg"
             alt="Actual dependency graph with arrows connecting a, b, and c. An
                  arrow now connects A to C as well. This does not match the
                  declared dependency graph">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependencies no longer overapproximate the actual dependencies.
This may build ok, because the transitive closures of the two graphs are equal,
but masks a problem: `a` has an actual but undeclared dependency on `c`.

### 3. Divergence between declared and actual dependency graphs {:#divergence}

The hazard is revealed when someone refactors `b` so that it no longer depends on
`c`, inadvertently breaking `a` through no
fault of their own.

<table class="cyan">
  <tr>
    <th>&nbsp;</th>
    <th><code><strong>b</strong>/BUILD</code></th>
  </tr>
  <tr>
    <td>&nbsp;</td>
    <td>
      <pre>rule(
    name = "b",
    srcs = "b.in",
    <strong>deps = "//d:d",</strong>
)
      </pre>
    </td>
  </tr>
  <tr class="alt">
    <td>&nbsp;</td>
    <td><code>b / b.in</code></td>
  </tr>
  <tr>
    <td>&nbsp;</td>
    <td>
      <pre>
      import d;
      function foo() {
        d.baz();
      }
      </pre>
    </td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/ab_c.svg"
             alt="Declared dependency graph with arrows connecting a and b.
                  b no longer connects to c, which breaks a's connection to c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_a_c.svg"
             alt="Actual dependency graph that shows a connecting to b and c,
                  but b no longer connects to c">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependency graph is now an underapproximation of the actual
dependencies, even when transitively closed; the build is likely to fail.

The problem could have been averted by ensuring that the actual dependency from
`a` to `c` introduced in Step 2 was properly declared in the `BUILD` file.

## Types of dependencies {:#types-of-dependencies}

Most build rules have three attributes for specifying different kinds of
generic dependencies: `srcs`, `deps` and `data`. These are explained below. For
more details, see
[Attributes common to all rules](/reference/be/common-definitions).

Many rules also have additional attributes for rule-specific kinds of
dependencies, for example, `compiler` or `resources`. These are detailed in the
[Build Encyclopedia](/reference/be/).

### `srcs` dependencies {:#srcs-dependencies}

Files consumed directly by the rule or rules that output source files.

### `deps` dependencies {:#deps-dependencies}

Rule pointing to separately-compiled modules providing header files,
symbols, libraries, data, etc.

### `data` dependencies {:#data-dependencies}

A build target might need some data files to run correctly. These data files
aren't source code: they don't affect how the target is built. For example, a
unit test might compare a function's output to the contents of a file. When you
build the unit test you don't need the file, but you do need it when you run
the test. The same applies to tools that are launched during execution.

The build system runs tests in an isolated directory where only files listed as
`data` are available. Thus, if a binary/library/test needs some files to run,
specify them (or a build rule containing them) in `data`. For example:

```
# I need a config file from a directory named env:
java_binary(
    name = "setenv",
    ...
    data = [":env/default_env.txt"],
)

# I need test data from another directory
sh_test(
    name = "regtest",
    srcs = ["regtest.sh"],
    data = [
        "//data:file1.txt",
        "//data:file2.txt",
        ...
    ],
)
```

These files are available using the relative path `path/to/data/file`. In tests,
you can refer to these files by joining the paths of the test's source
directory and the workspace-relative path, for example,
`${TEST_SRCDIR}/workspace/path/to/data/file`.

## Using labels to reference directories {:#using-labels-reference-directories}

As you look over our `BUILD` files, you might notice that some `data` labels
refer to directories. These labels end with `/.` or `/` like these examples,
which you should not use:

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["//data/regression:unittest/."]</code>
</p>

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["testdata/."]</code>
</p>

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["testdata/"]</code>
</p>


This seems convenient, particularly for tests because it allows a test to
use all the data files in the directory.

But try not to do this. In order to ensure correct incremental rebuilds (and
re-execution of tests) after a change, the build system must be aware of the
complete set of files that are inputs to the build (or test). When you specify
a directory, the build system performs a rebuild only when the directory itself
changes (due to addition or deletion of files), but won't be able to detect
edits to individual files as those changes don't affect the enclosing directory.
Rather than specifying directories as inputs to the build system, you should
enumerate the set of files contained within them, either explicitly or using the
[`glob()`](/reference/be/functions#glob) function. (Use `**` to force the
`glob()` to be recursive.)


<p><span class="compare-better">Recommended</span> —
  <code>data = glob(["testdata/**"])</code>
</p>

Unfortunately, there are some scenarios where directory labels must be used.
For example, if the `testdata` directory contains files whose names don't
conform to the [label syntax](/concepts/labels#labels-lexical-specification),
then explicit enumeration of files, or use of the
[`glob()`](/reference/be/functions#glob) function produces an invalid labels
error. You must use directory labels in this case, but beware of the
associated risk of incorrect rebuilds described above.

If you must use directory labels, keep in mind that you can't refer to the
parent package with a relative `../` path; instead, use an absolute path like
`//data/regression:unittest/.`.

Note: Directory labels are only valid for data dependencies. If you try to use
a directory as a label in an argument other than `data`, it will fail and you
will get a (probably cryptic) error message.

Any external rule, such as a test, that needs to use multiple files must
explicitly declare its dependence on all of them. You can use `filegroup()` to
group files together in the `BUILD` file:

```
filegroup(
        name = 'my_data',
        srcs = glob(['my_unittest_data/*'])
)
```

You can then reference the label `my_data` as the data dependency in your test.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-files">
        <span class="material-icons" aria-hidden="true">arrow_back</span>BUILD files</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/visibility">
        Visibility<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>



Project: /_project.yaml
Book: /_book.yaml

# Repositories, workspaces, packages, and targets

{% include "_buttons.html" %}

Bazel builds software from source code organized in directory trees called
repositories. A defined set of repositories comprises the workspace. Source
files in repositories are organized in a nested hierarchy of packages, where
each package is a directory that contains a set of related source files and one
`BUILD` file. The `BUILD` file specifies what software outputs can be built from
the source.

### Repositories {:#repositories}

Source files used in a Bazel build are organized in _repositories_ (often
shortened to _repos_). A repo is a directory tree with a boundary marker file at
its root; such a boundary marker file could be `MODULE.bazel`, `REPO.bazel`, or
in legacy contexts, `WORKSPACE` or `WORKSPACE.bazel`.

The repo in which the current Bazel command is being run is called the _main
repo_. Other, (external) repos are defined by _repo rules_; see [external
dependencies overview](/external/overview) for more information.

## Workspace {:#workspace}

A _workspace_ is the environment shared by all Bazel commands run from the same
main repo. It encompasses the main repo and the set of all defined external
repos.

Note that historically the concepts of "repository" and "workspace" have been
conflated; the term "workspace" has often been used to refer to the main
repository, and sometimes even used as a synonym of "repository".

## Packages {:#packages}

The primary unit of code organization in a repository is the _package_. A
package is a collection of related files and a specification of how they can be
used to produce output artifacts.

A package is defined as a directory containing a
[`BUILD` file](/concepts/build-files) named either `BUILD` or `BUILD.bazel`. A
package includes all files in its directory, plus all subdirectories beneath it,
except those which themselves contain a `BUILD` file. From this definition, no
file or directory may be a part of two different packages.

For example, in the following directory tree there are two packages, `my/app`,
and the subpackage `my/app/tests`. Note that `my/app/data` is not a package, but
a directory belonging to package `my/app`.

```
src/my/app/BUILD
src/my/app/app.cc
src/my/app/data/input.txt
src/my/app/tests/BUILD
src/my/app/tests/test.cc
```

## Targets {:#targets}

A package is a container of _targets_, which are defined in the package's
`BUILD` file. Most targets are one of two principal kinds, _files_ and _rules_.

Files are further divided into two kinds. _Source files_ are usually written by
the efforts of people, and checked in to the repository. _Generated files_,
sometimes called derived files or output files, are not checked in, but are
generated from source files.

The second kind of target is declared with a _rule_. Each rule instance
specifies the relationship between a set of input and a set of output files. The
inputs to a rule may be source files, but they also may be the outputs of other
rules.

Whether the input to a rule is a source file or a generated file is in most
cases immaterial; what matters is only the contents of that file. This fact
makes it easy to replace a complex source file with a generated file produced by
a rule, such as happens when the burden of manually maintaining a highly
structured file becomes too tiresome, and someone writes a program to derive it.
No change is required to the consumers of that file. Conversely, a generated
file may easily be replaced by a source file with only local changes.

The inputs to a rule may also include _other rules_. The precise meaning of such
relationships is often quite complex and language- or rule-dependent, but
intuitively it is simple: a C++ library rule A might have another C++ library
rule B for an input. The effect of this dependency is that B's header files are
available to A during compilation, B's symbols are available to A during
linking, and B's runtime data is available to A during execution.

An invariant of all rules is that the files generated by a rule always belong to
the same package as the rule itself; it is not possible to generate files into
another package. It is not uncommon for a rule's inputs to come from another
package, though.

Package groups are sets of packages whose purpose is to limit accessibility of
certain rules. Package groups are defined by the `package_group` function. They
have three properties: the list of packages they contain, their name, and other
package groups they include. The only allowed ways to refer to them are from the
`visibility` attribute of rules or from the `default_visibility` attribute of
the `package` function; they do not generate or consume files. For more
information, refer to the [`package_group`
documentation](/reference/be/functions#package_group).

<a class="button button-with-icon button-primary" href="/concepts/labels">
  Labels<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span>
</a>

Project: /_project.yaml
Book: /_book.yaml

# Migrating to Platforms

{% include "_buttons.html" %}

Bazel has sophisticated [support](#background) for modeling
[platforms][Platforms] and [toolchains][Toolchains] for multi-architecture and
cross-compiled builds.

This page summarizes the state of this support.

Key Point: Bazel's platform and toolchain APIs are available today. Not all
languages support them. Use these APIs with your project if you can. Bazel is
migrating all major languages so eventually all builds will be platform-based.

See also:

* [Platforms][Platforms]
* [Toolchains][Toolchains]
* [Background][Background]

## Status {:#status}

### C++ {:#cxx}

C++ rules use platforms to select toolchains when
`--incompatible_enable_cc_toolchain_resolution` is set.

This means you can configure a C++ project with:

```posix-terminal
bazel build //:my_cpp_project --platforms=//:myplatform
```

instead of the legacy:

```posix-terminal
bazel build //:my_cpp_project` --cpu=... --crosstool_top=...  --compiler=...
```

This will be enabled by default in Bazel 7.0 ([#7260](https://github.com/bazelbuild/bazel/issues/7260){: .external}).

To test your C++ project with platforms, see
[Migrating Your Project](#migrating-your-project) and
[Configuring C++ toolchains].

### Java {:#java}

Java rules use platforms to select toolchains.

This replaces legacy flags `--java_toolchain`, `--host_java_toolchain`,
`--javabase`, and `--host_javabase`.

See [Java and Bazel](/docs/bazel-and-java) for details.

### Android {:#android}

Android rules use platforms to select toolchains when
`--incompatible_enable_android_toolchain_resolution` is set.

This means you can configure an Android project with:

```posix-terminal
bazel build //:my_android_project --android_platforms=//:my_android_platform
```

instead of with legacy flags like  `--android_crosstool_top`, `--android_cpu`,
and `--fat_apk_cpu`.

This will be enabled by default in Bazel 7.0 ([#16285](https://github.com/bazelbuild/bazel/issues/16285){: .external}).

To test your Android project with platforms, see
[Migrating Your Project](#migrating-your-project).

### Apple {:#apple}

[Apple rules]{: .external} do not support platforms and are not yet scheduled
for support.

You can still use platform APIs with Apple builds (for example, when building
with a mixture of Apple rules and pure C++) with [platform
mappings](#platform-mappings).

### Other languages {:#other-languages}

* [Go rules]{: .external} fully support platforms
* [Rust rules]{: .external} fully support platforms.

If you own a language rule set, see [Migrating your rule set] for adding
support.

## Background {:#background}

*Platforms* and *toolchains* were introduced to standardize how software
projects target different architectures and cross-compile.

This was
[inspired][Inspiration]{: .external}
by the observation that language maintainers were already doing this in ad
hoc, incompatible ways. For example, C++ rules used `--cpu` and
 `--crosstool_top` to declare a target CPU and toolchain. Neither of these
correctly models a "platform". This produced awkward and incorrect builds.

Java, Android, and other languages evolved their own flags for similar purposes,
none of which interoperated with each other. This made cross-language builds
confusing and complicated.

Bazel is intended for large, multi-language, multi-platform projects. This
demands more principled support for these concepts, including a clear
standard API.

### Need for migration {:#migration}

Upgrading to the new API requires two efforts: releasing the API and upgrading
rule logic to use it.

The first is done but the second is ongoing. This consists of ensuring
language-specific platforms and toolchains are defined, language logic reads
toolchains through the new API instead of old flags like `--crosstool_top`, and
`config_setting`s select on the new API instead of old flags.

This work is straightforward but requires a distinct effort for each language,
plus fair warning for project owners to test against upcoming changes.

This is why this is an ongoing migration.

### Goal {:#goal}

This migration is complete when all projects build with the form:

```posix-terminal
bazel build //:myproject --platforms=//:myplatform
```

This implies:

1. Your project's rules choose the right toolchains for `//:myplatform`.
1. Your project's dependencies choose the right toolchains for `//:myplatform`.
1. `//:myplatform` references
[common declarations][Common Platform Declarations]{: .external}
of `CPU`, `OS`, and other generic, language-independent properties
1. All relevant [`select()`s][select()] properly match `//:myplatform`.
1. `//:myplatform` is defined in a clear, accessible place: in your project's
repo if the platform is unique to your project, or some common place all
consuming projects can find it

Old flags like `--cpu`, `--crosstool_top`, and `--fat_apk_cpu` will be
deprecated and removed as soon as it's safe to do so.

Ultimately, this will be the *sole* way to configure architectures.


## Migrating your project {:#migrating-your-project}

If you build with languages that support platforms, your build should already
work with an invocation like:

```posix-terminal
bazel build //:myproject --platforms=//:myplatform
```

See [Status](#status) and your language's documentation for precise details.

If a language requires a flag to enable platform support, you also need to set
that flag. See [Status](#status) for details.

For your project to build, you need to check the following:

1. `//:myplatform` must exist. It's generally the project owner's responsibility
   to define platforms because different projects target different machines.
   See [Default platforms](#default-platforms).

1. The toolchains you want to use must exist. If using stock toolchains, the
   language owners should include instructions for how to register them. If
   writing your own custom toolchains, you need to [register](https://bazel.build/extending/toolchains#registering-building-toolchains) them in your
   `MODULE.bazel` file or with [`--extra_toolchains`](https://bazel.build/reference/command-line-reference#flag--extra_toolchains).

1. `select()`s and [configuration transitions][Starlark transitions] must
  resolve properly. See [select()](#select) and [Transitions](#transitions).

1. If your build mixes languages that do and don't support platforms, you may
   need platform mappings to help the legacy languages work with the new API.
   See [Platform mappings](#platform-mappings) for details.

If you still have problems, [reach out](#questions) for support.

### Default platforms {:#default-platforms}

Project owners should define explicit
[platforms][Defining Constraints and Platforms] to describe the architectures
they want to build for. These are then triggered with `--platforms`.

When `--platforms` isn't set, Bazel defaults to a `platform` representing the
local build machine. This is auto-generated at `@platforms//host` (aliased as
`@bazel_tools//tools:host_platform`)
so there's no need to explicitly define it. It maps the local machine's `OS`
and `CPU` with `constraint_value`s declared in
[`@platforms`](https://github.com/bazelbuild/platforms){: .external}.

### `select()` {:#select}

Projects can [`select()`][select()] on
[`constraint_value` targets][constraint_value Rule] but not complete
platforms. This is intentional so `select()` supports as wide a variety of
machines as possible. A library with `ARM`-specific sources should support *all*
`ARM`-powered machines unless there's reason to be more specific.

To select on one or more `constraint_value`s, use:

```python
config_setting(
    name = "is_arm",
    constraint_values = [
        "@platforms//cpu:arm",
    ],
)
```

This is equivalent to traditionally selecting on `--cpu`:

```python
config_setting(
    name = "is_arm",
    values = {
        "cpu": "arm",
    },
)
```

More details [here][select() Platforms].

`select`s on `--cpu`, `--crosstool_top`, etc. don't understand `--platforms`.
When migrating your project to platforms, you must either convert them to
`constraint_values` or use [platform mappings](#platform-mappings) to support
both styles during migration.

### Transitions {:#transitions}

[Starlark transitions][Starlark transitions] change
flags down parts of your build graph. If your project uses a transition that
sets `--cpu`, `--crossstool_top`, or other legacy flags, rules that read
`--platforms` won't see these changes.

When migrating your project to platforms, you must either convert changes like
`return { "//command_line_option:cpu": "arm" }` to `return {
"//command_line_option:platforms": "//:my_arm_platform" }` or use [platform
mappings](#platform-mappings) to support both styles during migration.
window.

## Migrating your rule set  {:#migrating-your-rule-set}

If you own a rule set and want to support platforms, you need to:

1. Have rule logic resolve toolchains with the toolchain API. See
   [toolchain API][Toolchains] (`ctx.toolchains`).

1. Optional: define an `--incompatible_enable_platforms_for_my_language` flag so
   rule logic alternately resolves toolchains through the new API or old flags
   like `--crosstool_top` during migration testing.

1. Define the relevant properties that make up platform components. See
   [Common platform properties](#common-platform-properties)

1. Define standard toolchains and make them accessible to users through your
   rule's registration instructions ([details](https://bazel.build/extending/toolchains#registering-building-toolchains))

1. Ensure [`select()`s](#select) and
   [configuration transitions](#transitions) support platforms. This is the
   biggest challenge. It's particularly challenging for multi-language projects
   (which may fail if *all* languages can't read `--platforms`).

If you need to mix with rules that don't support platforms, you may need
[platform mappings](#platform-mappings) to bridge the gap.

### Common platform properties {:#common-platform-properties}

Common, cross-language platform properties like `OS` and `CPU` should be
declared in [`@platforms`](https://github.com/bazelbuild/platforms){: .external}.
This encourages sharing, standardization, and cross-language compatibility.

Properties unique to your rules should be declared in your rule's repo. This
lets you maintain clear ownership over the specific concepts your rules are
responsible for.

If your rules use custom-purpose OSes or CPUs, these should be declared in your
rule's repo vs.
[`@platforms`](https://github.com/bazelbuild/platforms){: .external}.

## Platform mappings {:#platform-mappings}

*Platform mappings* is a temporary API that lets platform-aware logic mix with
legacy logic in the same build. This is a blunt tool that's only intended to
smooth incompatibilities with different migration timeframes.

Caution: Only use this if necessary, and expect to eventually  eliminate it.

A platform mapping is a map of either a `platform()` to a
corresponding set of legacy flags or the reverse. For example:

```python
platforms:
  # Maps "--platforms=//platforms:ios" to "--ios_multi_cpus=x86_64 --apple_platform_type=ios".
  //platforms:ios
    --ios_multi_cpus=x86_64
    --apple_platform_type=ios

flags:
  # Maps "--ios_multi_cpus=x86_64 --apple_platform_type=ios" to "--platforms=//platforms:ios".
  --ios_multi_cpus=x86_64
  --apple_platform_type=ios
    //platforms:ios

  # Maps "--cpu=darwin_x86_64 --apple_platform_type=macos" to "//platform:macos".
  --cpu=darwin_x86_64
  --apple_platform_type=macos
    //platforms:macos
```

Bazel uses this to guarantee all settings, both platform-based and
legacy, are consistently applied throughout the build, including through
[transitions](#transitions).

By default Bazel reads mappings from the `platform_mappings` file in your
workspace root. You can also set
`--platform_mappings=//:my_custom_mapping`.

See the [platform mappings design]{: .external} for details.

## API review {:#api-review}

A [`platform`][platform Rule] is a collection of
[`constraint_value` targets][constraint_value Rule]:

```python
platform(
    name = "myplatform",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:arm",
    ],
)
```

A [`constraint_value`][constraint_value Rule] is a machine
property. Values of the same "kind" are grouped under a common
[`constraint_setting`][constraint_setting Rule]:

```python
constraint_setting(name = "os")
constraint_value(
    name = "linux",
    constraint_setting = ":os",
)
constraint_value(
    name = "mac",
    constraint_setting = ":os",
)
```

A [`toolchain`][Toolchains] is a [Starlark rule][Starlark rule]. Its
attributes declare a language's tools (like `compiler =
"//mytoolchain:custom_gcc"`). Its [providers][Starlark Provider] pass
this information to rules that need to build with these tools.

Toolchains declare the `constraint_value`s of machines they can
[target][target_compatible_with Attribute]
(`target_compatible_with = ["@platforms//os:linux"]`) and machines their tools can
[run on][exec_compatible_with Attribute]
(`exec_compatible_with = ["@platforms//os:mac"]`).

When building `$ bazel build //:myproject --platforms=//:myplatform`, Bazel
automatically selects a toolchain that can run on the build machine and
build binaries for `//:myplatform`. This is known as *toolchain resolution*.

The set of available toolchains can be registered in the `MODULE.bazel` file
with [`register_toolchains`][register_toolchains Function] or at the
command line with [`--extra_toolchains`][extra_toolchains Flag].

For more information see [here][Toolchains].

## Questions {:#questions}

For general support and questions about the migration timeline, contact
[bazel-discuss]{: .external} or the owners of the appropriate rules.

For discussions on the design and evolution of the platform/toolchain APIs,
contact [bazel-dev]{: .external}.

## See also {:#see-also}

* [Configurable Builds - Part 1]{: .external}
* [Platforms]
* [Toolchains]
* [Bazel Platforms Cookbook]{: .external}
* [Platforms examples]{: .external}
* [Example C++ toolchain]{: .external}

[Android Rules]: /docs/bazel-and-android
[Apple Rules]: https://github.com/bazelbuild/rules_apple
[Background]: #background
[Bazel platforms Cookbook]: https://docs.google.com/document/d/1UZaVcL08wePB41ATZHcxQV4Pu1YfA1RvvWm8FbZHuW8/
[bazel-dev]: https://groups.google.com/forum/#!forum/bazel-dev
[bazel-discuss]: https://groups.google.com/forum/#!forum/bazel-discuss
[Common Platform Declarations]: https://github.com/bazelbuild/platforms
[constraint_setting Rule]: /reference/be/platforms-and-toolchains#constraint_setting
[constraint_value Rule]: /reference/be/platforms-and-toolchains#constraint_value
[Configurable Builds - Part 1]: https://blog.bazel.build/2019/02/11/configurable-builds-part-1.html
[Configuring C++ toolchains]: /tutorials/ccp-toolchain-config
[Defining Constraints and Platforms]: /extending/platforms#constraints-platforms
[Example C++ toolchain]: https://github.com/gregestren/snippets/tree/master/custom_cc_toolchain_with_platforms
[exec_compatible_with Attribute]: /reference/be/platforms-and-toolchains#toolchain.exec_compatible_with
[extra_toolchains Flag]: /reference/command-line-reference#flag--extra_toolchains
[Go Rules]: https://github.com/bazelbuild/rules_go
[Inspiration]: https://blog.bazel.build/2019/02/11/configurable-builds-part-1.html
[Migrating your rule set]: #migrating-your-rule-set
[Platforms]: /extending/platforms
[Platforms examples]: https://github.com/hlopko/bazel_platforms_examples
[platform mappings design]: https://docs.google.com/document/d/1Vg_tPgiZbSrvXcJ403vZVAGlsWhH9BUDrAxMOYnO0Ls/edit
[platform Rule]: /reference/be/platforms-and-toolchains#platform
[register_toolchains Function]: /rules/lib/globals/module#register_toolchains
[Rust rules]: https://github.com/bazelbuild/rules_rust
[select()]: /docs/configurable-attributes
[select() Platforms]: /docs/configurable-attributes#platforms
[Starlark provider]: /extending/rules#providers
[Starlark rule]: /extending/rules
[Starlark transitions]: /extending/config#user-defined-transitions
[target_compatible_with Attribute]: /reference/be/platforms-and-toolchains#toolchain.target_compatible_with
[Toolchains]: /extending/toolchains


Project: /_project.yaml
Book: /_book.yaml

# Labels

{% include "_buttons.html" %}

A **label** is an identifier for a target. A typical label in its full canonical
form looks like:

```none
@@myrepo//my/app/main:app_binary
```

The first part of the label is the repository name, `@@myrepo`. The double-`@`
syntax signifies that this is a [*canonical* repo
name](/external/overview#canonical-repo-name), which is unique within
the workspace. Labels with canonical repo names unambiguously identify a target
no matter which context they appear in.

Often the canonical repo name is an arcane string that looks like
`@@rules_java++toolchains+local_jdk`. What is much more commonly seen is
labels with an [*apparent* repo name](/external/overview#apparent-repo-name),
which looks like:

```
@myrepo//my/app/main:app_binary
```

The only difference is the repo name being prefixed with one `@` instead of two.
This refers to a repo with the apparent name `myrepo`, which could be different
based on the context this label appears in.

In the typical case that a label refers to the same repository from which
it is used, the repo name part may be omitted.  So, inside `@@myrepo` the first
label is usually written as

```
//my/app/main:app_binary
```

The second part of the label is the un-qualified package name
`my/app/main`, the path to the package
relative to the repository root.  Together, the repository name and the
un-qualified package name form the fully-qualified package name
`@@myrepo//my/app/main`. When the label refers to the same
package it is used in, the package name (and optionally, the colon)
may be omitted.  So, inside `@@myrepo//my/app/main`,
this label may be written either of the following ways:

```
app_binary
:app_binary
```

It is a matter of convention that the colon is omitted for files,
but retained for rules, but it is not otherwise significant.

The part of the label after the colon, `app_binary` is the un-qualified target
name. When it matches the last component of the package path, it, and the
colon, may be omitted.  So, these two labels are equivalent:

```
//my/app/lib
//my/app/lib:lib
```

The name of a file target in a subdirectory of the package is the file's path
relative to the package root (the directory containing the `BUILD` file). So,
this file is in the `my/app/main/testdata` subdirectory of the repository:

```
//my/app/main:testdata/input.txt
```

Strings like `//my/app` and `@@some_repo//my/app` have two meanings depending on
the context in which they are used: when Bazel expects a label, they mean
`//my/app:app` and `@@some_repo//my/app:app`, respectively. But, when Bazel
expects a package (e.g. in `package_group` specifications), they reference the
package that contains that label.

A common mistake in `BUILD` files is using `//my/app` to refer to a package, or
to *all* targets in a package--it does not.  Remember, it is
equivalent to `//my/app:app`, so it names the `app` target in the `my/app`
package of the current repository.

However, the use of `//my/app` to refer to a package is encouraged in the
specification of a `package_group` or in `.bzl` files, because it clearly
communicates that the package name is absolute and rooted in the top-level
directory of the workspace.

Relative labels cannot be used to refer to targets in other packages; the
repository identifier and package name must always be specified in this case.
For example, if the source tree contains both the package `my/app` and the
package `my/app/testdata` (each of these two directories has its own
`BUILD` file), the latter package contains a file named `testdepot.zip`. Here
are two ways (one wrong, one correct) to refer to this file within
`//my/app:BUILD`:

<p><span class="compare-worse">Wrong</span> — <code>testdata</code> is a different package, so you can't use a relative path</p>
<pre class="prettyprint">testdata/testdepot.zip</pre>

<p><span class="compare-better">Correct</span> — refer to <code>testdata</code> with its full path</p>

<pre class="prettyprint">//my/app/testdata:testdepot.zip</pre>



Labels starting with `@@//` are references to the main
repository, which will still work even from external repositories.
Therefore `@@//a/b/c` is different from
`//a/b/c` when referenced from an external repository.
The former refers back to the main repository, while the latter
looks for `//a/b/c` in the external repository itself.
This is especially relevant when writing rules in the main
repository that refer to targets in the main repository, and will be
used from external repositories.

For information about the different ways you can refer to targets, see
[target patterns](/run/build#specifying-build-targets).

### Lexical specification of a label {:#labels-lexical-specification}

Label syntax discourages use of metacharacters that have special meaning to the
shell. This helps to avoid inadvertent quoting problems, and makes it easier to
construct tools and scripts that manipulate labels, such as the
[Bazel Query Language](/query/language).

The precise details of allowed target names are below.

### Target names — `{{ "<var>" }}package-name{{ "</var>" }}:target-name` {:#target-names}

`target-name` is the name of the target within the package. The name of a rule
is the value of the `name` attribute in the rule's declaration in a `BUILD`
file; the name of a file is its pathname relative to the directory containing
the `BUILD` file.

Target names must be composed entirely of characters drawn from the set `a`–`z`,
`A`–`Z`, `0`–`9`, and the punctuation symbols `!%-@^_"#$&'()*-+,;<=>?[]{|}~/.`.

Filenames must be relative pathnames in normal form, which means they must
neither start nor end with a slash (for example, `/foo` and `foo/` are
forbidden) nor contain multiple consecutive slashes as path separators
(for example, `foo//bar`). Similarly, up-level references (`..`) and
current-directory references (`./`) are forbidden.

<p><span class="compare-worse">Wrong</span> — Do not use <code>..</code> to refer to files in other packages</p>

<p><span class="compare-better">Correct</span> — Use
  <code>//{{ "<var>" }}package-name{{ "</var>" }}:{{ "<var>" }}filename{{ "</var>" }}</code></p>


While it is common to use `/` in the name of a file target, avoid the use of
`/` in the names of rules. Especially when the shorthand form of a label is
used, it may confuse the reader. The label `//foo/bar/wiz` is always a shorthand
for `//foo/bar/wiz:wiz`, even if there is no such package `foo/bar/wiz`; it
never refers to `//foo:bar/wiz`, even if that target exists.

However, there are some situations where use of a slash is convenient, or
sometimes even necessary. For example, the name of certain rules must match
their principal source file, which may reside in a subdirectory of the package.

### Package names — `//package-name:{{ "<var>" }}target-name{{ "</var>" }}` {:#package-names}

The name of a package is the name of the directory containing its `BUILD` file,
relative to the top-level directory of the containing repository.
For example: `my/app`.

On a technical level, Bazel enforces the following:

* Allowed characters in package names are the lowercase letters `a` through `z`,
  the uppercase letters `A` through `Z`, the digits `0` through `9`, the
  characters ``! \"#$%&'()*+,-.;<=>?@[]^_`{|}`` (yes, there's a space character
  in there!), and of course forward slash `/` (since it's the directory
  separator).
* Package names may not start or end with a forward slash character `/`.
* Package names may not contain the substring `//`. This wouldn't make
  sense---what would the corresponding directory path be?
* Package names may not contain the substring `/./` or `/../` or `/.../` etc.
  This enforcement is done to avoid confusion when translating between a logical
  package name and a physical directory name, given the semantic meaning of the
  dot character in path strings.

On a practical level:

* For a language with a directory structure that is significant to its module
  system (for example, Java), it's important to choose directory names that are
  valid identifiers in the language. For example, don't start with a leading
  digit and avoid special characters, especially underscores and hyphens.
* Although Bazel supports targets in the workspace's root package (for example,
  `//:foo`), it's best to leave that package empty so all meaningful packages
  have descriptive names.

## Rules {:#rules}

A rule specifies the relationship between inputs and outputs, and the
steps to build the outputs. Rules can be of one of many different
kinds (sometimes called the _rule class_), which produce compiled
executables and libraries, test executables and other supported
outputs as described in the [Build Encyclopedia](/reference/be/overview).

`BUILD` files declare _targets_ by invoking _rules_.

In the example below, we see the declaration of the target `my_app`
using the `cc_binary` rule.

```python
cc_binary(
    name = "my_app",
    srcs = ["my_app.cc"],
    deps = [
        "//absl/base",
        "//absl/strings",
    ],
)
```

Every rule invocation has a `name` attribute (which must be a valid
[target name](#target-names)), that declares a target within the package
of the `BUILD` file.

Every rule has a set of _attributes_; the applicable attributes for a given
rule, and the significance and semantics of each attribute are a function of
the rule's kind; see the [Build Encyclopedia](/reference/be/overview) for a
list of rules and their corresponding attributes. Each attribute has a name and
a type. Some of the common types an attribute can have are integer, label, list
of labels, string, list of strings, output label, list of output labels. Not
all attributes need to be specified in every rule. Attributes thus form a
dictionary from keys (names) to optional, typed values.

The `srcs` attribute present in many rules has type "list of labels"; its
value, if present, is a list of labels, each being the name of a target that is
an input to this rule.

In some cases, the name of the rule kind is somewhat arbitrary, and more
interesting are the names of the files generated by the rule, and this is true
of genrules. For more information, see
[General Rules: genrule](/reference/be/general#genrule).

In other cases, the name is significant: for `*_binary` and `*_test` rules,
for example, the rule name determines the name of the executable produced by
the build.

This directed acyclic graph over targets is called the _target graph_ or
_build dependency graph_, and is the domain over which the
[Bazel Query tool](/query/guide) operates.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-ref">
        <span class="material-icons" aria-hidden="true">arrow_back</span>Targets</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-files">
        BUILD files<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>


Project: /_project.yaml
Book: /_book.yaml

# Visibility

{% include "_buttons.html" %}

This page covers Bazel's two visibility systems:
[target visibility](#target-visibility) and [load visibility](#load-visibility).

Both types of visibility help other developers distinguish between your
library's public API and its implementation details, and help enforce structure
as your workspace grows. You can also use visibility when deprecating a public
API to allow current users while denying new ones.

## Target visibility {:#target-visibility}

**Target visibility** controls who may depend on your target — that is, who may
use your target's label inside an attribute such as `deps`. A target will fail
to build during the [analysis](/reference/glossary#analysis-phase) phase if it
violates the visibility of one of its dependencies.

Generally, a target `A` is visible to a target `B` if they are in the same
location, or if `A` grants visibility to `B`'s location. In the absence of
[symbolic macros](/extending/macros), the term "location" can be simplified
to just "package"; see [below](#symbolic-macros) for more on symbolic macros.

Visibility is specified by listing allowed packages. Allowing a package does not
necessarily mean that its subpackages are also allowed. For more details on
packages and subpackages, see [Concepts and terminology](/concepts/build-ref).

For prototyping, you can disable target visibility enforcement by setting the
flag `--check_visibility=false`. This shouldn't be done for production usage in
submitted code.

The primary way to control visibility is with a rule's
[`visibility`](/reference/be/common-definitions#common.visibility) attribute.
The following subsections describe the attribute's format, how to apply it to
various kinds of targets, and the interaction between the visibility system and
symbolic macros.

### Visibility specifications {:#visibility-specifications}

All rule targets have a `visibility` attribute that takes a list of labels. Each
label has one of the following forms. With the exception of the last form, these
are just syntactic placeholders that don't correspond to any actual target.

*   `"//visibility:public"`: Grants access to all packages.

*   `"//visibility:private"`: Does not grant any additional access; only targets
    in this location's package can use this target.

*   `"//foo/bar:__pkg__"`: Grants access to `//foo/bar` (but not its
    subpackages).

*   `"//foo/bar:__subpackages__"`: Grants access to `//foo/bar` and all of its
    direct and indirect subpackages.

*   `"//some_pkg:my_package_group"`: Grants access to all of the packages that
    are part of the given [`package_group`](/reference/be/functions#package_group).

    *   Package groups use a
        [different syntax](/reference/be/functions#package_group.packages) for
        specifying packages. Within a package group, the forms
        `"//foo/bar:__pkg__"` and `"//foo/bar:__subpackages__"` are respectively
        replaced by `"//foo/bar"` and `"//foo/bar/..."`. Likewise,
        `"//visibility:public"` and `"//visibility:private"` are just `"public"`
        and `"private"`.

For example, if `//some/package:mytarget` has its `visibility` set to
`[":__subpackages__", "//tests:__pkg__"]`, then it could be used by any target
that is part of the `//some/package/...` source tree, as well as targets
declared in `//tests/BUILD`, but not by targets defined in
`//tests/integration/BUILD`.

**Best practice:** To make several targets visible to the same set
of packages, use a `package_group` instead of repeating the list in each
target's `visibility` attribute. This increases readability and prevents the
lists from getting out of sync.

**Best practice:** When granting visibility to another team's project, prefer
`__subpackages__` over `__pkg__` to avoid needless visibility churn as that
project evolves and adds new subpackages.

Note: The `visibility` attribute may not specify non-`package_group` targets.
Doing so triggers a "Label does not refer to a package group" or "Cycle in
dependency graph" error.

### Rule target visibility {:#rule-target-visibility}

A rule target's visibility is determined by taking its `visibility` attribute
-- or a suitable default if not given -- and appending the location where the
target was declared. For targets not declared in a symbolic macro, if the
package specifies a [`default_visibility`](/reference/be/functions#package.default_visibility),
this default is used; for all other packages and for targets declared in a
symbolic macro, the default is just `["//visibility:private"]`.

```starlark
# //mypkg/BUILD

package(default_visibility = ["//friend:__pkg__"])

cc_library(
    name = "t1",
    ...
    # No visibility explicitly specified.
    # Effective visibility is ["//friend:__pkg__", "//mypkg:__pkg__"].
    # If no default_visibility were given in package(...), the visibility would
    # instead default to ["//visibility:private"], and the effective visibility
    # would be ["//mypkg:__pkg__"].
)

cc_library(
    name = "t2",
    ...
    visibility = [":clients"],
    # Effective visibility is ["//mypkg:clients, "//mypkg:__pkg__"], which will
    # expand to ["//another_friend:__subpackages__", "//mypkg:__pkg__"].
)

cc_library(
    name = "t3",
    ...
    visibility = ["//visibility:private"],
    # Effective visibility is ["//mypkg:__pkg__"]
)

package_group(
    name = "clients",
    packages = ["//another_friend/..."],
)
```

**Best practice:** Avoid setting `default_visibility` to public. It may be
convenient for prototyping or in small codebases, but the risk of inadvertently
creating public targets increases as the codebase grows. It's better to be
explicit about which targets are part of a package's public interface.

### Generated file target visibility {:#generated-file-target-visibility}

A generated file target has the same visibility as the rule target that
generates it.

```starlark
# //mypkg/BUILD

java_binary(
    name = "foo",
    ...
    visibility = ["//friend:__pkg__"],
)
```

```starlark
# //friend/BUILD

some_rule(
    name = "bar",
    deps = [
        # Allowed directly by visibility of foo.
        "//mypkg:foo",
        # Also allowed. The java_binary's "_deploy.jar" implicit output file
        # target the same visibility as the rule target itself.
        "//mypkg:foo_deploy.jar",
    ]
    ...
)
```

### Source file target visibility {:#source-file-target-visibility}

Source file targets can either be explicitly declared using
[`exports_files`](/reference/be/functions#exports_files), or implicitly created
by referring to their filename in a label attribute of a rule (outside of a
symbolic macro). As with rule targets, the location of the call to
`exports_files`, or the BUILD file that referred to the input file, is always
automatically appended to the file's visibility.

Files declared by `exports_files` can have their visibility set by the
`visibility` parameter to that function. If this parameter is not given, the visibility is public.

Note: `exports_files` may not be used to override the visibility of a generated
file.

For files that do not appear in a call to `exports_files`, the visibility
depends on the value of the flag
[`--incompatible_no_implicit_file_export`](https://github.com/bazelbuild/bazel/issues/10225){: .external}:

*   If the flag is true, the visibility is private.

*   Else, the legacy behavior applies: The visibility is the same as the
    `BUILD` file's `default_visibility`, or private if a default visibility is
    not specified.

Avoid relying on the legacy behavior. Always write an `exports_files`
declaration whenever a source file target needs non-private visibility.

**Best practice:** When possible, prefer to expose a rule target rather than a
source file. For example, instead of calling `exports_files` on a `.java` file,
wrap the file in a non-private `java_library` target. Generally, rule targets
should only directly reference source files that live in the same package.

#### Example {:#source-file-visibility-example}

File `//frobber/data/BUILD`:

```starlark
exports_files(["readme.txt"])
```

File `//frobber/bin/BUILD`:

```starlark
cc_binary(
  name = "my-program",
  data = ["//frobber/data:readme.txt"],
)
```

### Config setting visibility {:#config-setting-visibility}

Historically, Bazel has not enforced visibility for
[`config_setting`](/reference/be/general#config_setting) targets that are
referenced in the keys of a [`select()`](/reference/be/functions#select). There
are two flags to remove this legacy behavior:

*   [`--incompatible_enforce_config_setting_visibility`](https://github.com/bazelbuild/bazel/issues/12932){: .external}
    enables visibility checking for these targets. To assist with migration, it
    also causes any `config_setting` that does not specify a `visibility` to be
    considered public (regardless of package-level `default_visibility`).

*   [`--incompatible_config_setting_private_default_visibility`](https://github.com/bazelbuild/bazel/issues/12933){: .external}
    causes `config_setting`s that do not specify a `visibility` to respect the
    package's `default_visibility` and to fallback on private visibility, just
    like any other rule target. It is a no-op if
    `--incompatible_enforce_config_setting_visibility` is not set.

Avoid relying on the legacy behavior. Any `config_setting` that is intended to
be used outside the current package should have an explicit `visibility`, if the
package does not already specify a suitable `default_visibility`.

### Package group target visibility {:#package-group-target-visibility}

`package_group` targets do not have a `visibility` attribute. They are always
publicly visible.

### Visibility of implicit dependencies {:#visibility-implicit-dependencies}

Some rules have [implicit dependencies](/extending/rules#private_attributes_and_implicit_dependencies) —
dependencies that are not spelled out in a `BUILD` file but are inherent to
every instance of that rule. For example, a `cc_library` rule might create an
implicit dependency from each of its rule targets to an executable target
representing a C++ compiler.

The visibility of such an implicit dependency is checked with respect to the
package containing the `.bzl` file in which the rule (or aspect) is defined. In
our example, the C++ compiler could be private so long as it lives in the same
package as the definition of the `cc_library` rule. As a fallback, if the
implicit dependency is not visible from the definition, it is checked with
respect to the `cc_library` target.

If you want to restrict the usage of a rule to certain packages, use
[load visibility](#load-visibility) instead.

### Visibility and symbolic macros {:#symbolic-macros}

This section describes how the visibility system interacts with
[symbolic macros](/extending/macros).

#### Locations within symbolic macros {:#locations-within-symbolic-macros}

A key detail of the visibility system is how we determine the location of a
declaration. For targets that are not declared in a symbolic macro, the location
is just the package where the target lives -- the package of the `BUILD` file.
But for targets created in a symbolic macro, the location is the package
containing the `.bzl` file where the macro's definition (the
`my_macro = macro(...)` statement) appears. When a target is created inside
multiple nested targets, it is always the innermost symbolic macro's definition
that is used.

The same system is used to determine what location to check against a given
dependency's visibility. If the consuming target was created inside a macro, we
look at the innermost macro's definition rather than the package the consuming
target lives in.

This means that all macros whose code is defined in the same package are
automatically "friends" with one another. Any target directly created by a macro
defined in `//lib:defs.bzl` can be seen from any other macro defined in `//lib`,
regardless of what packages the macros are actually instantiated in. Likewise,
they can see, and can be seen by, targets declared directly in `//lib/BUILD` and
its legacy macros. Conversely, targets that live in the same package cannot
necessarily see one another if at least one of them is created by a symbolic
macro.

Within a symbolic macro's implementation function, the `visibility` parameter
has the effective value of the macro's `visibility` attribute after appending
the location where the macro was called. The standard way for a macro to export
one of its targets to its caller is to forward this value along to the target's
declaration, as in `some_rule(..., visibility = visibility)`. Targets that omit
this attribute won't be visible to the caller of the macro unless the caller
happens to be in the same package as the macro definition. This behavior
composes, in the sense that a chain of nested calls to submacros may each pass
`visibility = visibility`, re-exporting the inner macro's exported targets to
the caller at each level, without exposing any of the macros' implementation
details.

#### Delegating privileges to a submacro {:#delegating-privileges-to-a-submacro}

The visibility model has a special feature to allow a macro to delegate its
permissions to a submacro. This is important for factoring and composing macros.

Suppose you have a macro `my_macro` that creates a dependency edge using a rule
`some_library` from another package:

```starlark
# //macro/defs.bzl
load("//lib:defs.bzl", "some_library")

def _impl(name, visibility, ...):
    ...
    native.genrule(
        name = name + "_dependency"
        ...
    )
    some_library(
        name = name + "_consumer",
        deps = [name + "_dependency"],
        ...
    )

my_macro = macro(implementation = _impl, ...)
```

```starlark
# //pkg/BUILD

load("//macro:defs.bzl", "my_macro")

my_macro(name = "foo", ...)
```

The `//pkg:foo_dependency` target has no `visibility` specified, so it is only
visible within `//macro`, which works fine for the consuming target. Now, what
happens if the author of `//lib` refactors `some_library` to instead be
implemented using a macro?

```starlark
# //lib:defs.bzl

def _impl(name, visibility, deps, ...):
    some_rule(
        # Main target, exported.
        name = name,
        visibility = visibility,
        deps = deps,
        ...)

some_library = macro(implementation = _impl, ...)
```

With this change, `//pkg:foo_consumer`'s location is now `//lib` rather than
`//macro`, so its usage of `//pkg:foo_dependency` violates the dependency's
visibility. The author of `my_macro` can't be expected to pass
`visibility = ["//lib"]` to the declaration of the dependency just to work
around this implementation detail.

For this reason, when a dependency of a target is also an attribute value of the
macro that declared the target, we check the dependency's visibility against the
location of the macro instead of the location of the consuming target.

In this example, to validate whether `//pkg:foo_consumer` can see
`//pkg:foo_dependency`, we see that `//pkg:foo_dependency` was also passed as an
input to the call to `some_library` inside of `my_macro`, and instead check the
dependency's visibility against the location of this call, `//macro`.

This process can repeat recursively, as long as a target or macro declaration is
inside of another symbolic macro taking the dependency's label in one of its
label-typed attributes.

Note: Visibility delegation does not work for labels that were not passed into
the macro, such as labels derived by string manipulation.

#### Finalizers {:#finalizers}

Targets declared in a rule finalizer (a symbolic macro with `finalizer = True`),
in addition to seeing targets following the usual symbolic macro visibility
rules, can *also* see all targets which are visible to the finalizer target's
package.

In other words, if you migrate a `native.existing_rules()`-based legacy macro to
a finalizer, the targets declared by the finalizer will still be able to see
their old dependencies.

It is possible to define targets that a finalizer can introspect using
`native.existing_rules()`, but which it cannot use as dependencies under the
visibility system. For example, if a macro-defined target is not visible to its
own package or to the finalizer macro's definition, and is not delegated to the
finalizer, the finalizer cannot see such a target. Note, however, that a
`native.existing_rules()`-based legacy macro will also be unable to see such a
target.

## Load visibility {:#load-visibility}

**Load visibility** controls whether a `.bzl` file may be loaded from other
`BUILD` or `.bzl` files outside the current package.

In the same way that target visibility protects source code that is encapsulated
by targets, load visibility protects build logic that is encapsulated by `.bzl`
files. For instance, a `BUILD` file author might wish to factor some repetitive
target declarations into a macro in a `.bzl` file. Without the protection of
load visibility, they might find their macro reused by other collaborators in
the same workspace, so that modifying the macro breaks other teams' builds.

Note that a `.bzl` file may or may not have a corresponding source file target.
If it does, there is no guarantee that the load visibility and the target
visibility coincide. That is, the same `BUILD` file might be able to load the
`.bzl` file but not list it in the `srcs` of a [`filegroup`](/reference/be/general#filegroup),
or vice versa. This can sometimes cause problems for rules that wish to consume
`.bzl` files as source code, such as for documentation generation or testing.

For prototyping, you may disable load visibility enforcement by setting
`--check_bzl_visibility=false`. As with `--check_visibility=false`, this should
not be done for submitted code.

Load visibility is available as of Bazel 6.0.

### Declaring load visibility {:#declaring-load-visibility}

To set the load visibility of a `.bzl` file, call the
[`visibility()`](/rules/lib/globals/bzl#visibility) function from within the file.
The argument to `visibility()` is a list of package specifications, just like
the [`packages`](/reference/be/functions#package_group.packages) attribute of
`package_group`. However, `visibility()` does not accept negative package
specifications.

The call to `visibility()` must only occur once per file, at the top level (not
inside a function), and ideally immediately following the `load()` statements.

Unlike target visibility, the default load visibility is always public. Files
that do not call `visibility()` are always loadable from anywhere in the
workspace. It is a good idea to add `visibility("private")` to the top of any
new `.bzl` file that is not specifically intended for use outside the package.

### Example {:#load-visibility-example}

```starlark
# //mylib/internal_defs.bzl

# Available to subpackages and to mylib's tests.
visibility(["//mylib/...", "//tests/mylib/..."])

def helper(...):
    ...
```

```starlark
# //mylib/rules.bzl

load(":internal_defs.bzl", "helper")
# Set visibility explicitly, even though public is the default.
# Note the [] can be omitted when there's only one entry.
visibility("public")

myrule = rule(
    ...
)
```

```starlark
# //someclient/BUILD

load("//mylib:rules.bzl", "myrule")          # ok
load("//mylib:internal_defs.bzl", "helper")  # error

...
```

### Load visibility practices {:#load-visibility-practices}

This section describes tips for managing load visibility declarations.

#### Factoring visibilities {:#factoring-visibilities}

When multiple `.bzl` files should have the same visibility, it can be helpful to
factor their package specifications into a common list. For example:

```starlark
# //mylib/internal_defs.bzl

visibility("private")

clients = [
    "//foo",
    "//bar/baz/...",
    ...
]
```

```starlark
# //mylib/feature_A.bzl

load(":internal_defs.bzl", "clients")
visibility(clients)

...
```

```starlark
# //mylib/feature_B.bzl

load(":internal_defs.bzl", "clients")
visibility(clients)

...
```

This helps prevent accidental skew between the various `.bzl` files'
visibilities. It also is more readable when the `clients` list is large.

#### Composing visibilities {:#composing-visibilities}

Sometimes a `.bzl` file might need to be visible to an allowlist that is
composed of multiple smaller allowlists. This is analogous to how a
`package_group` can incorporate other `package_group`s via its
[`includes`](/reference/be/functions#package_group.includes) attribute.

Suppose you are deprecating a widely used macro. You want it to be visible only
to existing users and to the packages owned by your own team. You might write:

```starlark
# //mylib/macros.bzl

load(":internal_defs.bzl", "our_packages")
load("//some_big_client:defs.bzl", "their_remaining_uses")

# List concatenation. Duplicates are fine.
visibility(our_packages + their_remaining_uses)
```

#### Deduplicating with package groups {:#deduplicating-with-package-groups}

Unlike target visibility, you cannot define a load visibility in terms of a
`package_group`. If you want to reuse the same allowlist for both target
visibility and load visibility, it's best to move the list of package
specifications into a .bzl file, where both kinds of declarations may refer to
it. Building off the example in [Factoring visibilities](#factoring-visibilities)
above, you might write:

```starlark
# //mylib/BUILD

load(":internal_defs", "clients")

package_group(
    name = "my_pkg_grp",
    packages = clients,
)
```

This only works if the list does not contain any negative package
specifications.

#### Protecting individual symbols {:#protecting-individual-symbols}

Any Starlark symbol whose name begins with an underscore cannot be loaded from
another file. This makes it easy to create private symbols, but does not allow
you to share these symbols with a limited set of trusted files. On the other
hand, load visibility gives you control over what other packages may see your
`.bzl file`, but does not allow you to prevent any non-underscored symbol from
being loaded.

Luckily, you can combine these two features to get fine-grained control.

```starlark
# //mylib/internal_defs.bzl

# Can't be public, because internal_helper shouldn't be exposed to the world.
visibility("private")

# Can't be underscore-prefixed, because this is
# needed by other .bzl files in mylib.
def internal_helper(...):
    ...

def public_util(...):
    ...
```

```starlark
# //mylib/defs.bzl

load(":internal_defs", "internal_helper", _public_util="public_util")
visibility("public")

# internal_helper, as a loaded symbol, is available for use in this file but
# can't be imported by clients who load this file.
...

# Re-export public_util from this file by assigning it to a global variable.
# We needed to import it under a different name ("_public_util") in order for
# this assignment to be legal.
public_util = _public_util
```

#### bzl-visibility Buildifier lint {:#bzl-visibility-buildifier-lint}

There is a [Buildifier lint](https://github.com/bazelbuild/buildtools/blob/master/WARNINGS.md#bzl-visibility)
that provides a warning if users load a file from a directory named `internal`
or `private`, when the user's file is not itself underneath the parent of that
directory. This lint predates the load visibility feature and is unnecessary in
workspaces where `.bzl` files declare visibilities.


Project: /_project.yaml
Book: /_book.yaml

# BUILD files

{% include "_buttons.html" %}

The previous sections described packages, targets and labels, and the
build dependency graph abstractly. This section describes the concrete syntax
used to define a package.

By definition, every package contains a `BUILD` file, which is a short
program.

Note: The `BUILD` file can be named either `BUILD` or `BUILD.bazel`. If both
files exist, `BUILD.bazel` takes precedence over `BUILD`.
For simplicity's sake, the documentation refers to these files simply as `BUILD`
files.

`BUILD` files are evaluated using an imperative language,
[Starlark](https://github.com/bazelbuild/starlark/){: .external}.

They are interpreted as a sequential list of statements.

In general, order does matter: variables must be defined before they are
used, for example. However, most `BUILD` files consist only of declarations of
build rules, and the relative order of these statements is immaterial; all
that matters is _which_ rules were declared, and with what values, by the
time package evaluation completes.

When a build rule function, such as `cc_library`, is executed, it creates a
new target in the graph. This target can later be referred using a label.

In simple `BUILD` files, rule declarations can be re-ordered freely without
changing the behavior.

To encourage a clean separation between code and data, `BUILD` files cannot
contain function definitions, `for` statements or `if` statements (but list
comprehensions and `if` expressions are allowed). Functions can be declared in
`.bzl` files instead. Additionally, `*args` and `**kwargs` arguments are not
allowed in `BUILD` files; instead list all the arguments explicitly.

Crucially, programs in Starlark can't perform arbitrary I/O. This invariant
makes the interpretation of `BUILD` files hermetic — dependent only on a known
set of inputs, which is essential for ensuring that builds are reproducible.
For more details, see [Hermeticity](/basics/hermeticity).

Because `BUILD` files need to be updated whenever the dependencies of the
underlying code change, they are typically maintained by multiple people on a
team. `BUILD` file authors should comment liberally to document the role
of each build target, whether or not it is intended for public use, and to
document the role of the package itself.

## Loading an extension {:#load}

Bazel extensions are files ending in `.bzl`. Use the `load` statement to import
a symbol from an extension.

```
load("//foo/bar:file.bzl", "some_library")
```

This code loads the file `foo/bar/file.bzl` and adds the `some_library` symbol
to the environment. This can be used to load new rules, functions, or constants
(for example, a string or a list). Multiple symbols can be imported by using
additional arguments to the call to `load`. Arguments must be string literals
(no variable) and `load` statements must appear at top-level — they cannot be
in a function body.

The first argument of `load` is a [label](/concepts/labels) identifying a
`.bzl` file. If it's a relative label, it is resolved with respect to the
package (not directory) containing the current `bzl` file. Relative labels in
`load` statements should use a leading `:`.

`load` also supports aliases, therefore, you can assign different names to the
imported symbols.

```
load("//foo/bar:file.bzl", library_alias = "some_library")
```

You can define multiple aliases within one `load` statement. Moreover, the
argument list can contain both aliases and regular symbol names. The following
example is perfectly legal (please note when to use quotation marks).

```
load(":my_rules.bzl", "some_rule", nice_alias = "some_other_rule")
```

In a `.bzl` file, symbols starting with `_` are not exported and cannot be
loaded from another file.

You can use [load visibility](/concepts/visibility#load-visibility) to restrict
who may load a `.bzl` file.

## Types of build rules {:#types-of-build-rules}

The majority of build rules come in families, grouped together by
language. For example, `cc_binary`, `cc_library`
and `cc_test` are the build rules for C++ binaries,
libraries, and tests, respectively. Other languages use the same
naming scheme, with a different prefix, such as `java_*` for
Java. Some of these functions are documented in the
[Build Encyclopedia](/reference/be/overview), but it is possible
for anyone to create new rules.

* `*_binary` rules build executable programs in a given language. After a
  build, the executable will reside in the build tool's binary
  output tree at the corresponding name for the rule's label,
  so `//my:program` would appear at (for example) `$(BINDIR)/my/program`.

  In some languages, such rules also create a runfiles directory
  containing all the files mentioned in a `data`
  attribute belonging to the rule, or any rule in its transitive
  closure of dependencies; this set of files is gathered together in
  one place for ease of deployment to production.

* `*_test` rules are a specialization of a `*_binary` rule, used for automated
  testing. Tests are simply programs that return zero on success.

  Like binaries, tests also have runfiles trees, and the files
  beneath it are the only files that a test may legitimately open
  at runtime. For example, a program `cc_test(name='x',
  data=['//foo:bar'])` may open and read `$TEST_SRCDIR/workspace/foo/bar` during execution.
  (Each programming language has its own utility function for
  accessing the value of `$TEST_SRCDIR`, but they are all
  equivalent to using the environment variable directly.)
  Failure to observe the rule will cause the test to fail when it is
  executed on a remote testing host.

* `*_library` rules specify separately-compiled modules in the given
    programming language. Libraries can depend on other libraries,
    and binaries and tests can depend on libraries, with the expected
    separate-compilation behavior.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/labels">
        <span class="material-icons" aria-hidden="true">arrow_back</span>Labels</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/dependencies">
        Dependencies<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>

## File encoding

`BUILD` and `.bzl` files should be encoded in UTF-8, of which ASCII is a valid
subset. Arbitrary byte sequences are currently allowed, but may stop being
supported in the future.


Project: /_project.yaml
Book: /_book.yaml

# Dependencies

{% include "_buttons.html" %}

A target `A` _depends upon_ a target `B` if `B` is needed by `A` at build or
execution time. The _depends upon_ relation induces a
[Directed Acyclic Graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph){: .external}
(DAG) over targets, and it is called a _dependency graph_.

A target's _direct_ dependencies are those other targets reachable by a path
of length 1 in the dependency graph. A target's _transitive_ dependencies are
those targets upon which it depends via a path of any length through the graph.

In fact, in the context of builds, there are two dependency graphs, the graph
of _actual dependencies_ and the graph of _declared dependencies_. Most of the
time, the two graphs are so similar that this distinction need not be made, but
it is useful for the discussion below.

## Actual and declared dependencies {:#actual-and-declared-dependencies}

A target `X` is _actually dependent_ on target `Y` if `Y` must be present,
built, and up-to-date in order for `X` to be built correctly. _Built_ could
mean generated, processed, compiled, linked, archived, compressed, executed, or
any of the other kinds of tasks that routinely occur during a build.

A target `X` has a _declared dependency_ on target `Y` if there is a dependency
edge from `X` to `Y` in the package of `X`.

For correct builds, the graph of actual dependencies _A_ must be a subgraph of
the graph of declared dependencies _D_. That is, every pair of
directly-connected nodes `x --> y` in _A_ must also be directly connected in
_D_. It can be said that _D_ is an _overapproximation_ of _A_.

Important: _D_ should not be too much of an overapproximation of _A_ because
redundant declared dependencies can make builds slower and binaries larger.

`BUILD` file writers must explicitly declare all of the actual direct
dependencies for every rule to the build system, and no more.

Failure to observe this principle causes undefined behavior: the build may fail,
but worse, the build may depend on some prior operations, or upon transitive
declared dependencies the target happens to have. Bazel checks for missing
dependencies and report errors, but it's not possible for this checking to be
complete in all cases.

You need not (and should not) attempt to list everything indirectly imported,
even if it is _needed_ by `A` at execution time.

During a build of target `X`, the build tool inspects the entire transitive
closure of dependencies of `X` to ensure that any changes in those targets are
reflected in the final result, rebuilding intermediates as needed.

The transitive nature of dependencies leads to a common mistake. Sometimes,
code in one file may use code provided by an _indirect_ dependency — a
transitive but not direct edge in the declared dependency graph. Indirect
dependencies don't appear in the `BUILD` file. Because the rule doesn't
directly depend on the provider, there is no way to track changes, as shown in
the following example timeline:

### 1. Declared dependencies match actual dependencies {:#this-is-fine}

At first, everything works. The code in package `a` uses code in package `b`.
The code in package `b` uses code in package `c`, and thus `a` transitively
depends on `c`.

<table class="cyan">
  <tr>
    <th><code>a/BUILD</code></th>
    <th><code><strong>b</strong>/BUILD</code></th>
  </tr>
  <tr>
    <td>
      <pre>rule(
    name = "a",
    srcs = "a.in",
    deps = "//b:b",
)
      </pre>
    </td>
    <td>
      <pre>
rule(
    name = "b",
    srcs = "b.in",
    deps = "//c:c",
)
      </pre>
    </td>
  </tr>
  <tr class="alt">
    <td><code>a / a.in</code></td>
    <td><code>b / b.in</code></td>
  </tr>
  <tr>
    <td><pre>
import b;
b.foo();
    </pre>
    </td>
    <td>
      <pre>
import c;
function foo() {
  c.bar();
}
      </pre>
    </td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Declared dependency graph with arrows connecting a, b, and c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Actual dependency graph that matches the declared dependency
                  graph with arrows connecting a, b, and c">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependencies overapproximate the actual dependencies. All is well.

### 2. Adding an undeclared dependency {:#undeclared-dependency}

A latent hazard is introduced when someone adds code to `a` that creates a
direct _actual_ dependency on `c`, but forgets to declare it in the build file
`a/BUILD`.

<table class="cyan">
  <tr>
    <th><code>a / a.in</code></th>
    <th>&nbsp;</th>
  </tr>
  <tr>
    <td>
      <pre>
        import b;
        import c;
        b.foo();
        c.garply();
      </pre>
    </td>
    <td>&nbsp;</td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/a_b_c.svg"
             alt="Declared dependency graph with arrows connecting a, b, and c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_c_ac.svg"
             alt="Actual dependency graph with arrows connecting a, b, and c. An
                  arrow now connects A to C as well. This does not match the
                  declared dependency graph">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependencies no longer overapproximate the actual dependencies.
This may build ok, because the transitive closures of the two graphs are equal,
but masks a problem: `a` has an actual but undeclared dependency on `c`.

### 3. Divergence between declared and actual dependency graphs {:#divergence}

The hazard is revealed when someone refactors `b` so that it no longer depends on
`c`, inadvertently breaking `a` through no
fault of their own.

<table class="cyan">
  <tr>
    <th>&nbsp;</th>
    <th><code><strong>b</strong>/BUILD</code></th>
  </tr>
  <tr>
    <td>&nbsp;</td>
    <td>
      <pre>rule(
    name = "b",
    srcs = "b.in",
    <strong>deps = "//d:d",</strong>
)
      </pre>
    </td>
  </tr>
  <tr class="alt">
    <td>&nbsp;</td>
    <td><code>b / b.in</code></td>
  </tr>
  <tr>
    <td>&nbsp;</td>
    <td>
      <pre>
      import d;
      function foo() {
        d.baz();
      }
      </pre>
    </td>
  </tr>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/ab_c.svg"
             alt="Declared dependency graph with arrows connecting a and b.
                  b no longer connects to c, which breaks a's connection to c">
        <figcaption><b>Declared</b> dependency graph</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="/docs/images/a_b_a_c.svg"
             alt="Actual dependency graph that shows a connecting to b and c,
                  but b no longer connects to c">
        <figcaption><b>Actual</b> dependency graph</figcaption>
      </figure>
    </td>
  </tr>
</table>

The declared dependency graph is now an underapproximation of the actual
dependencies, even when transitively closed; the build is likely to fail.

The problem could have been averted by ensuring that the actual dependency from
`a` to `c` introduced in Step 2 was properly declared in the `BUILD` file.

## Types of dependencies {:#types-of-dependencies}

Most build rules have three attributes for specifying different kinds of
generic dependencies: `srcs`, `deps` and `data`. These are explained below. For
more details, see
[Attributes common to all rules](/reference/be/common-definitions).

Many rules also have additional attributes for rule-specific kinds of
dependencies, for example, `compiler` or `resources`. These are detailed in the
[Build Encyclopedia](/reference/be/).

### `srcs` dependencies {:#srcs-dependencies}

Files consumed directly by the rule or rules that output source files.

### `deps` dependencies {:#deps-dependencies}

Rule pointing to separately-compiled modules providing header files,
symbols, libraries, data, etc.

### `data` dependencies {:#data-dependencies}

A build target might need some data files to run correctly. These data files
aren't source code: they don't affect how the target is built. For example, a
unit test might compare a function's output to the contents of a file. When you
build the unit test you don't need the file, but you do need it when you run
the test. The same applies to tools that are launched during execution.

The build system runs tests in an isolated directory where only files listed as
`data` are available. Thus, if a binary/library/test needs some files to run,
specify them (or a build rule containing them) in `data`. For example:

```
# I need a config file from a directory named env:
java_binary(
    name = "setenv",
    ...
    data = [":env/default_env.txt"],
)

# I need test data from another directory
sh_test(
    name = "regtest",
    srcs = ["regtest.sh"],
    data = [
        "//data:file1.txt",
        "//data:file2.txt",
        ...
    ],
)
```

These files are available using the relative path `path/to/data/file`. In tests,
you can refer to these files by joining the paths of the test's source
directory and the workspace-relative path, for example,
`${TEST_SRCDIR}/workspace/path/to/data/file`.

## Using labels to reference directories {:#using-labels-reference-directories}

As you look over our `BUILD` files, you might notice that some `data` labels
refer to directories. These labels end with `/.` or `/` like these examples,
which you should not use:

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["//data/regression:unittest/."]</code>
</p>

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["testdata/."]</code>
</p>

<p><span class="compare-worse">Not recommended</span> —
  <code>data = ["testdata/"]</code>
</p>


This seems convenient, particularly for tests because it allows a test to
use all the data files in the directory.

But try not to do this. In order to ensure correct incremental rebuilds (and
re-execution of tests) after a change, the build system must be aware of the
complete set of files that are inputs to the build (or test). When you specify
a directory, the build system performs a rebuild only when the directory itself
changes (due to addition or deletion of files), but won't be able to detect
edits to individual files as those changes don't affect the enclosing directory.
Rather than specifying directories as inputs to the build system, you should
enumerate the set of files contained within them, either explicitly or using the
[`glob()`](/reference/be/functions#glob) function. (Use `**` to force the
`glob()` to be recursive.)


<p><span class="compare-better">Recommended</span> —
  <code>data = glob(["testdata/**"])</code>
</p>

Unfortunately, there are some scenarios where directory labels must be used.
For example, if the `testdata` directory contains files whose names don't
conform to the [label syntax](/concepts/labels#labels-lexical-specification),
then explicit enumeration of files, or use of the
[`glob()`](/reference/be/functions#glob) function produces an invalid labels
error. You must use directory labels in this case, but beware of the
associated risk of incorrect rebuilds described above.

If you must use directory labels, keep in mind that you can't refer to the
parent package with a relative `../` path; instead, use an absolute path like
`//data/regression:unittest/.`.

Note: Directory labels are only valid for data dependencies. If you try to use
a directory as a label in an argument other than `data`, it will fail and you
will get a (probably cryptic) error message.

Any external rule, such as a test, that needs to use multiple files must
explicitly declare its dependence on all of them. You can use `filegroup()` to
group files together in the `BUILD` file:

```
filegroup(
        name = 'my_data',
        srcs = glob(['my_unittest_data/*'])
)
```

You can then reference the label `my_data` as the data dependency in your test.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-files">
        <span class="material-icons" aria-hidden="true">arrow_back</span>BUILD files</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/visibility">
        Visibility<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>



Project: /_project.yaml
Book: /_book.yaml

# Repositories, workspaces, packages, and targets

{% include "_buttons.html" %}

Bazel builds software from source code organized in directory trees called
repositories. A defined set of repositories comprises the workspace. Source
files in repositories are organized in a nested hierarchy of packages, where
each package is a directory that contains a set of related source files and one
`BUILD` file. The `BUILD` file specifies what software outputs can be built from
the source.

### Repositories {:#repositories}

Source files used in a Bazel build are organized in _repositories_ (often
shortened to _repos_). A repo is a directory tree with a boundary marker file at
its root; such a boundary marker file could be `MODULE.bazel`, `REPO.bazel`, or
in legacy contexts, `WORKSPACE` or `WORKSPACE.bazel`.

The repo in which the current Bazel command is being run is called the _main
repo_. Other, (external) repos are defined by _repo rules_; see [external
dependencies overview](/external/overview) for more information.

## Workspace {:#workspace}

A _workspace_ is the environment shared by all Bazel commands run from the same
main repo. It encompasses the main repo and the set of all defined external
repos.

Note that historically the concepts of "repository" and "workspace" have been
conflated; the term "workspace" has often been used to refer to the main
repository, and sometimes even used as a synonym of "repository".

## Packages {:#packages}

The primary unit of code organization in a repository is the _package_. A
package is a collection of related files and a specification of how they can be
used to produce output artifacts.

A package is defined as a directory containing a
[`BUILD` file](/concepts/build-files) named either `BUILD` or `BUILD.bazel`. A
package includes all files in its directory, plus all subdirectories beneath it,
except those which themselves contain a `BUILD` file. From this definition, no
file or directory may be a part of two different packages.

For example, in the following directory tree there are two packages, `my/app`,
and the subpackage `my/app/tests`. Note that `my/app/data` is not a package, but
a directory belonging to package `my/app`.

```
src/my/app/BUILD
src/my/app/app.cc
src/my/app/data/input.txt
src/my/app/tests/BUILD
src/my/app/tests/test.cc
```

## Targets {:#targets}

A package is a container of _targets_, which are defined in the package's
`BUILD` file. Most targets are one of two principal kinds, _files_ and _rules_.

Files are further divided into two kinds. _Source files_ are usually written by
the efforts of people, and checked in to the repository. _Generated files_,
sometimes called derived files or output files, are not checked in, but are
generated from source files.

The second kind of target is declared with a _rule_. Each rule instance
specifies the relationship between a set of input and a set of output files. The
inputs to a rule may be source files, but they also may be the outputs of other
rules.

Whether the input to a rule is a source file or a generated file is in most
cases immaterial; what matters is only the contents of that file. This fact
makes it easy to replace a complex source file with a generated file produced by
a rule, such as happens when the burden of manually maintaining a highly
structured file becomes too tiresome, and someone writes a program to derive it.
No change is required to the consumers of that file. Conversely, a generated
file may easily be replaced by a source file with only local changes.

The inputs to a rule may also include _other rules_. The precise meaning of such
relationships is often quite complex and language- or rule-dependent, but
intuitively it is simple: a C++ library rule A might have another C++ library
rule B for an input. The effect of this dependency is that B's header files are
available to A during compilation, B's symbols are available to A during
linking, and B's runtime data is available to A during execution.

An invariant of all rules is that the files generated by a rule always belong to
the same package as the rule itself; it is not possible to generate files into
another package. It is not uncommon for a rule's inputs to come from another
package, though.

Package groups are sets of packages whose purpose is to limit accessibility of
certain rules. Package groups are defined by the `package_group` function. They
have three properties: the list of packages they contain, their name, and other
package groups they include. The only allowed ways to refer to them are from the
`visibility` attribute of rules or from the `default_visibility` attribute of
the `package` function; they do not generate or consume files. For more
information, refer to the [`package_group`
documentation](/reference/be/functions#package_group).

<a class="button button-with-icon button-primary" href="/concepts/labels">
  Labels<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span>
</a>

Project: /_project.yaml
Book: /_book.yaml

# Migrating to Platforms

{% include "_buttons.html" %}

Bazel has sophisticated [support](#background) for modeling
[platforms][Platforms] and [toolchains][Toolchains] for multi-architecture and
cross-compiled builds.

This page summarizes the state of this support.

Key Point: Bazel's platform and toolchain APIs are available today. Not all
languages support them. Use these APIs with your project if you can. Bazel is
migrating all major languages so eventually all builds will be platform-based.

See also:

* [Platforms][Platforms]
* [Toolchains][Toolchains]
* [Background][Background]

## Status {:#status}

### C++ {:#cxx}

C++ rules use platforms to select toolchains when
`--incompatible_enable_cc_toolchain_resolution` is set.

This means you can configure a C++ project with:

```posix-terminal
bazel build //:my_cpp_project --platforms=//:myplatform
```

instead of the legacy:

```posix-terminal
bazel build //:my_cpp_project` --cpu=... --crosstool_top=...  --compiler=...
```

This will be enabled by default in Bazel 7.0 ([#7260](https://github.com/bazelbuild/bazel/issues/7260){: .external}).

To test your C++ project with platforms, see
[Migrating Your Project](#migrating-your-project) and
[Configuring C++ toolchains].

### Java {:#java}

Java rules use platforms to select toolchains.

This replaces legacy flags `--java_toolchain`, `--host_java_toolchain`,
`--javabase`, and `--host_javabase`.

See [Java and Bazel](/docs/bazel-and-java) for details.

### Android {:#android}

Android rules use platforms to select toolchains when
`--incompatible_enable_android_toolchain_resolution` is set.

This means you can configure an Android project with:

```posix-terminal
bazel build //:my_android_project --android_platforms=//:my_android_platform
```

instead of with legacy flags like  `--android_crosstool_top`, `--android_cpu`,
and `--fat_apk_cpu`.

This will be enabled by default in Bazel 7.0 ([#16285](https://github.com/bazelbuild/bazel/issues/16285){: .external}).

To test your Android project with platforms, see
[Migrating Your Project](#migrating-your-project).

### Apple {:#apple}

[Apple rules]{: .external} do not support platforms and are not yet scheduled
for support.

You can still use platform APIs with Apple builds (for example, when building
with a mixture of Apple rules and pure C++) with [platform
mappings](#platform-mappings).

### Other languages {:#other-languages}

* [Go rules]{: .external} fully support platforms
* [Rust rules]{: .external} fully support platforms.

If you own a language rule set, see [Migrating your rule set] for adding
support.

## Background {:#background}

*Platforms* and *toolchains* were introduced to standardize how software
projects target different architectures and cross-compile.

This was
[inspired][Inspiration]{: .external}
by the observation that language maintainers were already doing this in ad
hoc, incompatible ways. For example, C++ rules used `--cpu` and
 `--crosstool_top` to declare a target CPU and toolchain. Neither of these
correctly models a "platform". This produced awkward and incorrect builds.

Java, Android, and other languages evolved their own flags for similar purposes,
none of which interoperated with each other. This made cross-language builds
confusing and complicated.

Bazel is intended for large, multi-language, multi-platform projects. This
demands more principled support for these concepts, including a clear
standard API.

### Need for migration {:#migration}

Upgrading to the new API requires two efforts: releasing the API and upgrading
rule logic to use it.

The first is done but the second is ongoing. This consists of ensuring
language-specific platforms and toolchains are defined, language logic reads
toolchains through the new API instead of old flags like `--crosstool_top`, and
`config_setting`s select on the new API instead of old flags.

This work is straightforward but requires a distinct effort for each language,
plus fair warning for project owners to test against upcoming changes.

This is why this is an ongoing migration.

### Goal {:#goal}

This migration is complete when all projects build with the form:

```posix-terminal
bazel build //:myproject --platforms=//:myplatform
```

This implies:

1. Your project's rules choose the right toolchains for `//:myplatform`.
1. Your project's dependencies choose the right toolchains for `//:myplatform`.
1. `//:myplatform` references
[common declarations][Common Platform Declarations]{: .external}
of `CPU`, `OS`, and other generic, language-independent properties
1. All relevant [`select()`s][select()] properly match `//:myplatform`.
1. `//:myplatform` is defined in a clear, accessible place: in your project's
repo if the platform is unique to your project, or some common place all
consuming projects can find it

Old flags like `--cpu`, `--crosstool_top`, and `--fat_apk_cpu` will be
deprecated and removed as soon as it's safe to do so.

Ultimately, this will be the *sole* way to configure architectures.


## Migrating your project {:#migrating-your-project}

If you build with languages that support platforms, your build should already
work with an invocation like:

```posix-terminal
bazel build //:myproject --platforms=//:myplatform
```

See [Status](#status) and your language's documentation for precise details.

If a language requires a flag to enable platform support, you also need to set
that flag. See [Status](#status) for details.

For your project to build, you need to check the following:

1. `//:myplatform` must exist. It's generally the project owner's responsibility
   to define platforms because different projects target different machines.
   See [Default platforms](#default-platforms).

1. The toolchains you want to use must exist. If using stock toolchains, the
   language owners should include instructions for how to register them. If
   writing your own custom toolchains, you need to [register](https://bazel.build/extending/toolchains#registering-building-toolchains) them in your
   `MODULE.bazel` file or with [`--extra_toolchains`](https://bazel.build/reference/command-line-reference#flag--extra_toolchains).

1. `select()`s and [configuration transitions][Starlark transitions] must
  resolve properly. See [select()](#select) and [Transitions](#transitions).

1. If your build mixes languages that do and don't support platforms, you may
   need platform mappings to help the legacy languages work with the new API.
   See [Platform mappings](#platform-mappings) for details.

If you still have problems, [reach out](#questions) for support.

### Default platforms {:#default-platforms}

Project owners should define explicit
[platforms][Defining Constraints and Platforms] to describe the architectures
they want to build for. These are then triggered with `--platforms`.

When `--platforms` isn't set, Bazel defaults to a `platform` representing the
local build machine. This is auto-generated at `@platforms//host` (aliased as
`@bazel_tools//tools:host_platform`)
so there's no need to explicitly define it. It maps the local machine's `OS`
and `CPU` with `constraint_value`s declared in
[`@platforms`](https://github.com/bazelbuild/platforms){: .external}.

### `select()` {:#select}

Projects can [`select()`][select()] on
[`constraint_value` targets][constraint_value Rule] but not complete
platforms. This is intentional so `select()` supports as wide a variety of
machines as possible. A library with `ARM`-specific sources should support *all*
`ARM`-powered machines unless there's reason to be more specific.

To select on one or more `constraint_value`s, use:

```python
config_setting(
    name = "is_arm",
    constraint_values = [
        "@platforms//cpu:arm",
    ],
)
```

This is equivalent to traditionally selecting on `--cpu`:

```python
config_setting(
    name = "is_arm",
    values = {
        "cpu": "arm",
    },
)
```

More details [here][select() Platforms].

`select`s on `--cpu`, `--crosstool_top`, etc. don't understand `--platforms`.
When migrating your project to platforms, you must either convert them to
`constraint_values` or use [platform mappings](#platform-mappings) to support
both styles during migration.

### Transitions {:#transitions}

[Starlark transitions][Starlark transitions] change
flags down parts of your build graph. If your project uses a transition that
sets `--cpu`, `--crossstool_top`, or other legacy flags, rules that read
`--platforms` won't see these changes.

When migrating your project to platforms, you must either convert changes like
`return { "//command_line_option:cpu": "arm" }` to `return {
"//command_line_option:platforms": "//:my_arm_platform" }` or use [platform
mappings](#platform-mappings) to support both styles during migration.
window.

## Migrating your rule set  {:#migrating-your-rule-set}

If you own a rule set and want to support platforms, you need to:

1. Have rule logic resolve toolchains with the toolchain API. See
   [toolchain API][Toolchains] (`ctx.toolchains`).

1. Optional: define an `--incompatible_enable_platforms_for_my_language` flag so
   rule logic alternately resolves toolchains through the new API or old flags
   like `--crosstool_top` during migration testing.

1. Define the relevant properties that make up platform components. See
   [Common platform properties](#common-platform-properties)

1. Define standard toolchains and make them accessible to users through your
   rule's registration instructions ([details](https://bazel.build/extending/toolchains#registering-building-toolchains))

1. Ensure [`select()`s](#select) and
   [configuration transitions](#transitions) support platforms. This is the
   biggest challenge. It's particularly challenging for multi-language projects
   (which may fail if *all* languages can't read `--platforms`).

If you need to mix with rules that don't support platforms, you may need
[platform mappings](#platform-mappings) to bridge the gap.

### Common platform properties {:#common-platform-properties}

Common, cross-language platform properties like `OS` and `CPU` should be
declared in [`@platforms`](https://github.com/bazelbuild/platforms){: .external}.
This encourages sharing, standardization, and cross-language compatibility.

Properties unique to your rules should be declared in your rule's repo. This
lets you maintain clear ownership over the specific concepts your rules are
responsible for.

If your rules use custom-purpose OSes or CPUs, these should be declared in your
rule's repo vs.
[`@platforms`](https://github.com/bazelbuild/platforms){: .external}.

## Platform mappings {:#platform-mappings}

*Platform mappings* is a temporary API that lets platform-aware logic mix with
legacy logic in the same build. This is a blunt tool that's only intended to
smooth incompatibilities with different migration timeframes.

Caution: Only use this if necessary, and expect to eventually  eliminate it.

A platform mapping is a map of either a `platform()` to a
corresponding set of legacy flags or the reverse. For example:

```python
platforms:
  # Maps "--platforms=//platforms:ios" to "--ios_multi_cpus=x86_64 --apple_platform_type=ios".
  //platforms:ios
    --ios_multi_cpus=x86_64
    --apple_platform_type=ios

flags:
  # Maps "--ios_multi_cpus=x86_64 --apple_platform_type=ios" to "--platforms=//platforms:ios".
  --ios_multi_cpus=x86_64
  --apple_platform_type=ios
    //platforms:ios

  # Maps "--cpu=darwin_x86_64 --apple_platform_type=macos" to "//platform:macos".
  --cpu=darwin_x86_64
  --apple_platform_type=macos
    //platforms:macos
```

Bazel uses this to guarantee all settings, both platform-based and
legacy, are consistently applied throughout the build, including through
[transitions](#transitions).

By default Bazel reads mappings from the `platform_mappings` file in your
workspace root. You can also set
`--platform_mappings=//:my_custom_mapping`.

See the [platform mappings design]{: .external} for details.

## API review {:#api-review}

A [`platform`][platform Rule] is a collection of
[`constraint_value` targets][constraint_value Rule]:

```python
platform(
    name = "myplatform",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:arm",
    ],
)
```

A [`constraint_value`][constraint_value Rule] is a machine
property. Values of the same "kind" are grouped under a common
[`constraint_setting`][constraint_setting Rule]:

```python
constraint_setting(name = "os")
constraint_value(
    name = "linux",
    constraint_setting = ":os",
)
constraint_value(
    name = "mac",
    constraint_setting = ":os",
)
```

A [`toolchain`][Toolchains] is a [Starlark rule][Starlark rule]. Its
attributes declare a language's tools (like `compiler =
"//mytoolchain:custom_gcc"`). Its [providers][Starlark Provider] pass
this information to rules that need to build with these tools.

Toolchains declare the `constraint_value`s of machines they can
[target][target_compatible_with Attribute]
(`target_compatible_with = ["@platforms//os:linux"]`) and machines their tools can
[run on][exec_compatible_with Attribute]
(`exec_compatible_with = ["@platforms//os:mac"]`).

When building `$ bazel build //:myproject --platforms=//:myplatform`, Bazel
automatically selects a toolchain that can run on the build machine and
build binaries for `//:myplatform`. This is known as *toolchain resolution*.

The set of available toolchains can be registered in the `MODULE.bazel` file
with [`register_toolchains`][register_toolchains Function] or at the
command line with [`--extra_toolchains`][extra_toolchains Flag].

For more information see [here][Toolchains].

## Questions {:#questions}

For general support and questions about the migration timeline, contact
[bazel-discuss]{: .external} or the owners of the appropriate rules.

For discussions on the design and evolution of the platform/toolchain APIs,
contact [bazel-dev]{: .external}.

## See also {:#see-also}

* [Configurable Builds - Part 1]{: .external}
* [Platforms]
* [Toolchains]
* [Bazel Platforms Cookbook]{: .external}
* [Platforms examples]{: .external}
* [Example C++ toolchain]{: .external}

[Android Rules]: /docs/bazel-and-android
[Apple Rules]: https://github.com/bazelbuild/rules_apple
[Background]: #background
[Bazel platforms Cookbook]: https://docs.google.com/document/d/1UZaVcL08wePB41ATZHcxQV4Pu1YfA1RvvWm8FbZHuW8/
[bazel-dev]: https://groups.google.com/forum/#!forum/bazel-dev
[bazel-discuss]: https://groups.google.com/forum/#!forum/bazel-discuss
[Common Platform Declarations]: https://github.com/bazelbuild/platforms
[constraint_setting Rule]: /reference/be/platforms-and-toolchains#constraint_setting
[constraint_value Rule]: /reference/be/platforms-and-toolchains#constraint_value
[Configurable Builds - Part 1]: https://blog.bazel.build/2019/02/11/configurable-builds-part-1.html
[Configuring C++ toolchains]: /tutorials/ccp-toolchain-config
[Defining Constraints and Platforms]: /extending/platforms#constraints-platforms
[Example C++ toolchain]: https://github.com/gregestren/snippets/tree/master/custom_cc_toolchain_with_platforms
[exec_compatible_with Attribute]: /reference/be/platforms-and-toolchains#toolchain.exec_compatible_with
[extra_toolchains Flag]: /reference/command-line-reference#flag--extra_toolchains
[Go Rules]: https://github.com/bazelbuild/rules_go
[Inspiration]: https://blog.bazel.build/2019/02/11/configurable-builds-part-1.html
[Migrating your rule set]: #migrating-your-rule-set
[Platforms]: /extending/platforms
[Platforms examples]: https://github.com/hlopko/bazel_platforms_examples
[platform mappings design]: https://docs.google.com/document/d/1Vg_tPgiZbSrvXcJ403vZVAGlsWhH9BUDrAxMOYnO0Ls/edit
[platform Rule]: /reference/be/platforms-and-toolchains#platform
[register_toolchains Function]: /rules/lib/globals/module#register_toolchains
[Rust rules]: https://github.com/bazelbuild/rules_rust
[select()]: /docs/configurable-attributes
[select() Platforms]: /docs/configurable-attributes#platforms
[Starlark provider]: /extending/rules#providers
[Starlark rule]: /extending/rules
[Starlark transitions]: /extending/config#user-defined-transitions
[target_compatible_with Attribute]: /reference/be/platforms-and-toolchains#toolchain.target_compatible_with
[Toolchains]: /extending/toolchains


Project: /_project.yaml
Book: /_book.yaml

# Labels

{% include "_buttons.html" %}

A **label** is an identifier for a target. A typical label in its full canonical
form looks like:

```none
@@myrepo//my/app/main:app_binary
```

The first part of the label is the repository name, `@@myrepo`. The double-`@`
syntax signifies that this is a [*canonical* repo
name](/external/overview#canonical-repo-name), which is unique within
the workspace. Labels with canonical repo names unambiguously identify a target
no matter which context they appear in.

Often the canonical repo name is an arcane string that looks like
`@@rules_java++toolchains+local_jdk`. What is much more commonly seen is
labels with an [*apparent* repo name](/external/overview#apparent-repo-name),
which looks like:

```
@myrepo//my/app/main:app_binary
```

The only difference is the repo name being prefixed with one `@` instead of two.
This refers to a repo with the apparent name `myrepo`, which could be different
based on the context this label appears in.

In the typical case that a label refers to the same repository from which
it is used, the repo name part may be omitted.  So, inside `@@myrepo` the first
label is usually written as

```
//my/app/main:app_binary
```

The second part of the label is the un-qualified package name
`my/app/main`, the path to the package
relative to the repository root.  Together, the repository name and the
un-qualified package name form the fully-qualified package name
`@@myrepo//my/app/main`. When the label refers to the same
package it is used in, the package name (and optionally, the colon)
may be omitted.  So, inside `@@myrepo//my/app/main`,
this label may be written either of the following ways:

```
app_binary
:app_binary
```

It is a matter of convention that the colon is omitted for files,
but retained for rules, but it is not otherwise significant.

The part of the label after the colon, `app_binary` is the un-qualified target
name. When it matches the last component of the package path, it, and the
colon, may be omitted.  So, these two labels are equivalent:

```
//my/app/lib
//my/app/lib:lib
```

The name of a file target in a subdirectory of the package is the file's path
relative to the package root (the directory containing the `BUILD` file). So,
this file is in the `my/app/main/testdata` subdirectory of the repository:

```
//my/app/main:testdata/input.txt
```

Strings like `//my/app` and `@@some_repo//my/app` have two meanings depending on
the context in which they are used: when Bazel expects a label, they mean
`//my/app:app` and `@@some_repo//my/app:app`, respectively. But, when Bazel
expects a package (e.g. in `package_group` specifications), they reference the
package that contains that label.

A common mistake in `BUILD` files is using `//my/app` to refer to a package, or
to *all* targets in a package--it does not.  Remember, it is
equivalent to `//my/app:app`, so it names the `app` target in the `my/app`
package of the current repository.

However, the use of `//my/app` to refer to a package is encouraged in the
specification of a `package_group` or in `.bzl` files, because it clearly
communicates that the package name is absolute and rooted in the top-level
directory of the workspace.

Relative labels cannot be used to refer to targets in other packages; the
repository identifier and package name must always be specified in this case.
For example, if the source tree contains both the package `my/app` and the
package `my/app/testdata` (each of these two directories has its own
`BUILD` file), the latter package contains a file named `testdepot.zip`. Here
are two ways (one wrong, one correct) to refer to this file within
`//my/app:BUILD`:

<p><span class="compare-worse">Wrong</span> — <code>testdata</code> is a different package, so you can't use a relative path</p>
<pre class="prettyprint">testdata/testdepot.zip</pre>

<p><span class="compare-better">Correct</span> — refer to <code>testdata</code> with its full path</p>

<pre class="prettyprint">//my/app/testdata:testdepot.zip</pre>



Labels starting with `@@//` are references to the main
repository, which will still work even from external repositories.
Therefore `@@//a/b/c` is different from
`//a/b/c` when referenced from an external repository.
The former refers back to the main repository, while the latter
looks for `//a/b/c` in the external repository itself.
This is especially relevant when writing rules in the main
repository that refer to targets in the main repository, and will be
used from external repositories.

For information about the different ways you can refer to targets, see
[target patterns](/run/build#specifying-build-targets).

### Lexical specification of a label {:#labels-lexical-specification}

Label syntax discourages use of metacharacters that have special meaning to the
shell. This helps to avoid inadvertent quoting problems, and makes it easier to
construct tools and scripts that manipulate labels, such as the
[Bazel Query Language](/query/language).

The precise details of allowed target names are below.

### Target names — `{{ "<var>" }}package-name{{ "</var>" }}:target-name` {:#target-names}

`target-name` is the name of the target within the package. The name of a rule
is the value of the `name` attribute in the rule's declaration in a `BUILD`
file; the name of a file is its pathname relative to the directory containing
the `BUILD` file.

Target names must be composed entirely of characters drawn from the set `a`–`z`,
`A`–`Z`, `0`–`9`, and the punctuation symbols `!%-@^_"#$&'()*-+,;<=>?[]{|}~/.`.

Filenames must be relative pathnames in normal form, which means they must
neither start nor end with a slash (for example, `/foo` and `foo/` are
forbidden) nor contain multiple consecutive slashes as path separators
(for example, `foo//bar`). Similarly, up-level references (`..`) and
current-directory references (`./`) are forbidden.

<p><span class="compare-worse">Wrong</span> — Do not use <code>..</code> to refer to files in other packages</p>

<p><span class="compare-better">Correct</span> — Use
  <code>//{{ "<var>" }}package-name{{ "</var>" }}:{{ "<var>" }}filename{{ "</var>" }}</code></p>


While it is common to use `/` in the name of a file target, avoid the use of
`/` in the names of rules. Especially when the shorthand form of a label is
used, it may confuse the reader. The label `//foo/bar/wiz` is always a shorthand
for `//foo/bar/wiz:wiz`, even if there is no such package `foo/bar/wiz`; it
never refers to `//foo:bar/wiz`, even if that target exists.

However, there are some situations where use of a slash is convenient, or
sometimes even necessary. For example, the name of certain rules must match
their principal source file, which may reside in a subdirectory of the package.

### Package names — `//package-name:{{ "<var>" }}target-name{{ "</var>" }}` {:#package-names}

The name of a package is the name of the directory containing its `BUILD` file,
relative to the top-level directory of the containing repository.
For example: `my/app`.

On a technical level, Bazel enforces the following:

* Allowed characters in package names are the lowercase letters `a` through `z`,
  the uppercase letters `A` through `Z`, the digits `0` through `9`, the
  characters ``! \"#$%&'()*+,-.;<=>?@[]^_`{|}`` (yes, there's a space character
  in there!), and of course forward slash `/` (since it's the directory
  separator).
* Package names may not start or end with a forward slash character `/`.
* Package names may not contain the substring `//`. This wouldn't make
  sense---what would the corresponding directory path be?
* Package names may not contain the substring `/./` or `/../` or `/.../` etc.
  This enforcement is done to avoid confusion when translating between a logical
  package name and a physical directory name, given the semantic meaning of the
  dot character in path strings.

On a practical level:

* For a language with a directory structure that is significant to its module
  system (for example, Java), it's important to choose directory names that are
  valid identifiers in the language. For example, don't start with a leading
  digit and avoid special characters, especially underscores and hyphens.
* Although Bazel supports targets in the workspace's root package (for example,
  `//:foo`), it's best to leave that package empty so all meaningful packages
  have descriptive names.

## Rules {:#rules}

A rule specifies the relationship between inputs and outputs, and the
steps to build the outputs. Rules can be of one of many different
kinds (sometimes called the _rule class_), which produce compiled
executables and libraries, test executables and other supported
outputs as described in the [Build Encyclopedia](/reference/be/overview).

`BUILD` files declare _targets_ by invoking _rules_.

In the example below, we see the declaration of the target `my_app`
using the `cc_binary` rule.

```python
cc_binary(
    name = "my_app",
    srcs = ["my_app.cc"],
    deps = [
        "//absl/base",
        "//absl/strings",
    ],
)
```

Every rule invocation has a `name` attribute (which must be a valid
[target name](#target-names)), that declares a target within the package
of the `BUILD` file.

Every rule has a set of _attributes_; the applicable attributes for a given
rule, and the significance and semantics of each attribute are a function of
the rule's kind; see the [Build Encyclopedia](/reference/be/overview) for a
list of rules and their corresponding attributes. Each attribute has a name and
a type. Some of the common types an attribute can have are integer, label, list
of labels, string, list of strings, output label, list of output labels. Not
all attributes need to be specified in every rule. Attributes thus form a
dictionary from keys (names) to optional, typed values.

The `srcs` attribute present in many rules has type "list of labels"; its
value, if present, is a list of labels, each being the name of a target that is
an input to this rule.

In some cases, the name of the rule kind is somewhat arbitrary, and more
interesting are the names of the files generated by the rule, and this is true
of genrules. For more information, see
[General Rules: genrule](/reference/be/general#genrule).

In other cases, the name is significant: for `*_binary` and `*_test` rules,
for example, the rule name determines the name of the executable produced by
the build.

This directed acyclic graph over targets is called the _target graph_ or
_build dependency graph_, and is the domain over which the
[Bazel Query tool](/query/guide) operates.

<table class="columns">
  <tr>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-ref">
        <span class="material-icons" aria-hidden="true">arrow_back</span>Targets</a>
    </td>
    <td><a class="button button-with-icon button-primary"
           href="/concepts/build-files">
        BUILD files<span class="material-icons icon-after" aria-hidden="true">arrow_forward</span></a>
    </td>
  </tr>
</table>
