Project: /_project.yaml
Book: /_book.yaml

# Rules

{% dynamic setvar source_file "site/en/rules/index.md" %}
{% include "_buttons.html" %}

The Bazel ecosystem has a growing and evolving set of rules to support popular
languages and packages. Much of Bazel's strength comes from the ability to
[define new rules](/extending/concepts) that can be used by others.

This page describes the recommended, native, and non-native Bazel rules.

## Recommended rules {:#recommended-rules}

Here is a selection of recommended rules:

* [Android](/docs/bazel-and-android)
* [C / C++](/docs/bazel-and-cpp)
* [Docker/OCI](https://github.com/bazel-contrib/rules_oci){: .external}
* [Go](https://github.com/bazelbuild/rules_go){: .external}
* [Haskell](https://github.com/tweag/rules_haskell){: .external}
* [Java](/docs/bazel-and-java)
* [JavaScript / NodeJS](https://github.com/bazelbuild/rules_nodejs){: .external}
* [Maven dependency management](https://github.com/bazelbuild/rules_jvm_external){: .external}
* [Objective-C](/docs/bazel-and-apple)
* [Package building](https://github.com/bazelbuild/rules_pkg){: .external}
* [Protocol Buffers](https://github.com/bazelbuild/rules_proto#protobuf-rules-for-bazel){: .external}
* [Python](https://github.com/bazelbuild/rules_python){: .external}
* [Rust](https://github.com/bazelbuild/rules_rust){: .external}
* [Scala](https://github.com/bazelbuild/rules_scala){: .external}
* [Shell](/reference/be/shell)
* [Webtesting](https://github.com/bazelbuild/rules_webtesting){: .external} (Webdriver)

The repository [Skylib](https://github.com/bazelbuild/bazel-skylib){: .external} contains
additional functions that can be useful when writing new rules and new
macros.

The rules above were reviewed and follow our
[requirements for recommended rules](/community/recommended-rules){: .external}.
Contact the respective rule set's maintainers regarding issues and feature
requests.

To find more Bazel rules, use a search engine, take a look on
[awesomebazel.com](https://awesomebazel.com/){: .external}, or search on
[GitHub](https://github.com/search?o=desc&q=bazel+rules&s=stars&type=Repositories){: .external}.

## Native rules that do not apply to a specific programming language

Native rules are shipped with the Bazel binary, they are always available in
BUILD files without a `load` statement.

* Extra actions
  - [`extra_action`](/reference/be/extra-actions#extra_action)
  - [`action_listener`](/reference/be/extra-actions#action_listener)
* General
  - [`filegroup`](/reference/be/general#filegroup)
  - [`genquery`](/reference/be/general#genquery)
  - [`test_suite`](/reference/be/general#test_suite)
  - [`alias`](/reference/be/general#alias)
  - [`config_setting`](/reference/be/general#config_setting)
  - [`genrule`](/reference/be/general#genrule)
* Platform
  - [`constraint_setting`](/reference/be/platforms-and-toolchains#constraint_setting)
  - [`constraint_value`](/reference/be/platforms-and-toolchains#constraint_value)
  - [`platform`](/reference/be/platforms-and-toolchains#platform)
  - [`toolchain`](/reference/be/platforms-and-toolchains#toolchain)
  - [`toolchain_type`](/reference/be/platforms-and-toolchains#toolchain_type)
* Workspace
  - [`bind`](/reference/be/workspace#bind)
  - [`local_repository`](/reference/be/workspace#local_repository)
  - [`new_local_repository`](/reference/be/workspace#new_local_repository)
  - [`xcode_config`](/reference/be/objective-c#xcode_config)
  - [`xcode_version`](/reference/be/objective-c#xcode_version)

## Embedded non-native rules {:#embedded-rules}

Bazel also embeds additional rules written in [Starlark](/rules/language). Those can be loaded from
the `@bazel_tools` built-in external repository.

* Repository rules
  - [`git_repository`](/rules/lib/repo/git#git_repository)
  - [`http_archive`](/rules/lib/repo/http#http_archive)
  - [`http_file`](/rules/lib/repo/http#http_archive)
  - [`http_jar`](/rules/lib/repo/http#http_jar)
  - [Utility functions on patching](/rules/lib/repo/utils)


Project: /_project.yaml
Book: /_book.yaml

# Starlark Language

{% include "_buttons.html" %}

<!-- [TOC] -->

This page is an overview of [Starlark](https://github.com/bazelbuild/starlark),
formerly known as Skylark, the language used in Bazel. For a complete list of
functions and types, see the [Bazel API reference](/rules/lib/overview).

For more information about the language, see [Starlark's GitHub repo](https://github.com/bazelbuild/starlark/).

For the authoritative specification of the Starlark syntax and
behavior, see the [Starlark Language Specification](https://github.com/bazelbuild/starlark/blob/master/spec.md).

## Syntax

Starlark's syntax is inspired by Python3. This is valid syntax in Starlark:

```python
def fizz_buzz(n):
  """Print Fizz Buzz numbers from 1 to n."""
  for i in range(1, n + 1):
    s = ""
    if i % 3 == 0:
      s += "Fizz"
    if i % 5 == 0:
      s += "Buzz"
    print(s if s else i)

fizz_buzz(20)
```

Starlark's semantics can differ from Python, but behavioral differences are
rare, except for cases where Starlark raises an error. The following Python
types are supported:

* [None](lib/globals#None)
* [bool](lib/bool)
* [dict](lib/dict)
* [tuple](lib/tuple)
* [function](lib/function)
* [int](lib/int)
* [list](lib/list)
* [string](lib/string)

## Type annotations {:#StarlarkTypes}

**Experimental**. Type annotations are an experimental feature and may change
at any time. Don't depend on it. It may be enabled in Bazel at HEAD
by using the `--experimental_starlark_types` flag.

Starlark in Bazel at HEAD is incrementally adding support for type annotations
with a syntax inspired by [PEP 484](https://peps.python.org/pep-0484/).

- Starlark type annotations are under active development. The progress is
  tracked on [issue#22935](https://github.com/bazelbuild/bazel/issues/22935).
- The specification is incrementally extended: [starlark-with-types/spec.md](https://github.com/bazelbuild/starlark/blob/starlark-with-types/spec.md)
- Initial proposal: {# disableFinding(LINK_DOCS) #}[SEP-001 Bootstrapping Starlark types](https://docs.google.com/document/d/1Sid7EAbBd_w_T7D94Li_f_bK3zMTztFbzIMvcpzo1wY/edit?tab=t.0#heading=h.5mcn15i0e1ch)

## Mutability

Starlark favors immutability. Two mutable data structures are available:
[lists](lib/list) and [dicts](lib/dict). Changes to mutable
data-structures, such as appending a value to a list or deleting an entry in a
dictionary are valid only for objects created in the current context. After a
context finishes, its values become immutable.

This is because Bazel builds use parallel execution. During a build, each `.bzl`
file and each `BUILD` file get their own execution context. Each rule is also
analyzed in its own context.

Let's go through an example with the file `foo.bzl`:

```python
# `foo.bzl`
var = [] # declare a list

def fct(): # declare a function
  var.append(5) # append a value to the list

fct() # execute the fct function
```

Bazel creates `var` when `foo.bzl` loads. `var` is thus part of `foo.bzl`'s
context. When `fct()` runs, it does so within the context of `foo.bzl`. After
evaluation for `foo.bzl` completes, the environment contains an immutable entry,
`var`, with the value `[5]`.

When another `bar.bzl` loads symbols from `foo.bzl`, loaded values remain
immutable. For this reason, the following code in `bar.bzl` is illegal:

```python
# `bar.bzl`
load(":foo.bzl", "var", "fct") # loads `var`, and `fct` from `./foo.bzl`

var.append(6)  # runtime error, the list stored in var is frozen

fct()          # runtime error, fct() attempts to modify a frozen list
```

Global variables defined in `bzl` files cannot be changed outside of the
`bzl` file that defined them. Just like the above example using `bzl` files,
values returned by rules are immutable.

## Differences between BUILD and .bzl files {:#differences-between-build-and-bzl-files}

`BUILD` files register targets via making calls to rules. `.bzl` files provide
definitions for constants, rules, macros, and functions.

[Native functions](/reference/be/functions) and [native rules](
/reference/be/overview#language-specific-native-rules) are global symbols in
`BUILD` files. `bzl` files need to load them using the [`native` module](
/rules/lib/toplevel/native).

There are two syntactic restrictions in `BUILD` files: 1) declaring functions is
illegal, and 2) `*args` and `**kwargs` arguments are not allowed.

## Differences with Python

* Global variables are immutable.

* `for` statements are not allowed at the top-level. Use them within functions
  instead. In `BUILD` files, you may use list comprehensions.

* `if` statements are not allowed at the top-level. However, `if` expressions
  can be used: `first = data[0] if len(data) > 0 else None`.

* Deterministic order for iterating through Dictionaries.

* Recursion is not allowed.

* Int type is limited to 32-bit signed integers. Overflows will throw an error.

* Modifying a collection during iteration is an error.

* Except for equality tests, comparison operators `<`, `<=`, `>=`, `>`, etc. are
not defined across value types. In short: `5 < 'foo'` will throw an error and
`5 == "5"` will return false.

* In tuples, a trailing comma is valid only when the tuple is between
  parentheses — when you write `(1,)` instead of `1,`.

* Dictionary literals cannot have duplicated keys. For example, this is an
  error: `{"a": 4, "b": 7, "a": 1}`.

* Strings are represented with double-quotes (such as when you call
  [repr](lib/globals#repr)).

* Strings aren't iterable.

The following Python features are not supported:

* implicit string concatenation (use explicit `+` operator).
* Chained comparisons (such as `1 < x < 5`).
* `class` (see [`struct`](lib/struct#struct) function).
* `import` (see [`load`](/extending/concepts#loading-an-extension) statement).
* `while`, `yield`.
* float and set types.
* generators and generator expressions.
* `is` (use `==` instead).
* `try`, `raise`, `except`, `finally` (see [`fail`](lib/globals#fail) for fatal errors).
* `global`, `nonlocal`.
* most builtin functions, most methods.


Project: /_project.yaml
Book: /_book.yaml

# .bzl style guide

{% include "_buttons.html" %}

This page covers basic style guidelines for Starlark and also includes
information on macros and rules.

[Starlark](/rules/language) is a
language that defines how software is built, and as such it is both a
programming and a configuration language.

You will use Starlark to write `BUILD` files, macros, and build rules. Macros and
rules are essentially meta-languages - they define how `BUILD` files are written.
`BUILD` files are intended to be simple and repetitive.

All software is read more often than it is written. This is especially true for
Starlark, as engineers read `BUILD` files to understand dependencies of their
targets and details of their builds. This reading will often happen in passing,
in a hurry, or in parallel to accomplishing some other task. Consequently,
simplicity and readability are very important so that users can parse and
comprehend `BUILD` files quickly.

When a user opens a `BUILD` file, they quickly want to know the list of targets in
the file; or review the list of sources of that C++ library; or remove a
dependency from that Java binary. Each time you add a layer of abstraction, you
make it harder for a user to do these tasks.

`BUILD` files are also analyzed and updated by many different tools. Tools may not
be able to edit your `BUILD` file if it uses abstractions. Keeping your `BUILD`
files simple will allow you to get better tooling. As a code base grows, it
becomes more and more frequent to do changes across many `BUILD` files in order to
update a library or do a cleanup.

Important: Do not create a variable or macro just to avoid some amount of
repetition in `BUILD` files. Your `BUILD` file should be easily readable both by
developers and tools. The
[DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself){: .external} principle doesn't
really apply here.

## General advice {:#general-advice}

*   Use [Buildifier](https://github.com/bazelbuild/buildtools/tree/master/buildifier#linter){: .external}
    as a formatter and linter.
*   Follow [testing guidelines](/rules/testing).

## Style {:#style}

### Python style {:#python-style}

When in doubt, follow the
[PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/) where possible.
In particular, use four rather than two spaces for indentation to follow the
Python convention.

Since
[Starlark is not Python](/rules/language#differences-with-python),
some aspects of Python style do not apply. For example, PEP 8 advises that
comparisons to singletons be done with `is`, which is not an operator in
Starlark.


### Docstring {:#docstring}

Document files and functions using [docstrings](https://github.com/bazelbuild/buildtools/blob/master/WARNINGS.md#function-docstring){: .external}.
Use a docstring at the top of each `.bzl` file, and a docstring for each public
function.

### Document rules and aspects {:#doc-rules-aspects}

Rules and aspects, along with their attributes, as well as providers and their
fields, should be documented using the `doc` argument.

### Naming convention {:#naming-convention}

*   Variables and function names use lowercase with words separated by
    underscores (`[a-z][a-z0-9_]*`), such as `cc_library`.
*   Top-level private values start with one underscore. Bazel enforces that
    private values cannot be used from other files. Local variables should not
    use the underscore prefix.

### Line length {:#line-length}

As in `BUILD` files, there is no strict line length limit as labels can be long.
When possible, try to use at most 79 characters per line (following Python's
style guide, [PEP 8](https://www.python.org/dev/peps/pep-0008/)). This guideline
should not be enforced strictly: editors should display more than 80 columns,
automated changes will frequently introduce longer lines, and humans shouldn't
spend time splitting lines that are already readable.

### Keyword arguments {:#keyword-arguments}

In keyword arguments, spaces around the equal sign are preferred:

```python
def fct(name, srcs):
    filtered_srcs = my_filter(source = srcs)
    native.cc_library(
        name = name,
        srcs = filtered_srcs,
        testonly = True,
    )
```

### Boolean values {:#boolean-values}

Prefer values `True` and `False` (rather than of `1` and `0`) for boolean values
(such as when using a boolean attribute in a rule).

### Use print only for debugging {:#print-for-debugging}

Do not use the `print()` function in production code; it is only intended for
debugging, and will spam all direct and indirect users of your `.bzl` file. The
only exception is that you may submit code that uses `print()` if it is disabled
by default and can only be enabled by editing the source -- for example, if all
uses of `print()` are guarded by `if DEBUG:` where `DEBUG` is hardcoded to
`False`. Be mindful of whether these statements are useful enough to justify
their impact on readability.

## Macros {:#macros}

A macro is a function which instantiates one or more rules during the loading
phase. In general, use rules whenever possible instead of macros. The build
graph seen by the user is not the same as the one used by Bazel during the
build - macros are expanded *before Bazel does any build graph analysis.*

Because of this, when something goes wrong, the user will need to understand
your macro's implementation to troubleshoot build problems. Additionally, `bazel
query` results can be hard to interpret because targets shown in the results
come from macro expansion. Finally, aspects are not aware of macros, so tooling
depending on aspects (IDEs and others) might fail.

A safe use for macros is for defining additional targets intended to be
referenced directly at the Bazel CLI or in BUILD files: In that case, only the
*end users* of those targets need to know about them, and any build problems
introduced by macros are never far from their usage.

For macros that define generated targets (implementation details of the macro
which are not supposed to be referred to at the CLI or depended on by targets
not instantiated by that macro), follow these best practices:

*   A macro should take a `name` argument and define a target with that name.
    That target becomes that macro's *main target*.
*   Generated targets, that is all other targets defined by a macro, should:
    *   Have their names prefixed by `<name>` or `_<name>`. For example, using
        `name = '%s_bar' % (name)`.
    *   Have restricted visibility (`//visibility:private`), and
    *   Have a `manual` tag to avoid expansion in wildcard targets (`:all`,
        `...`, `:*`, etc).
*   The `name` should only be used to derive names of targets defined by the
    macro, and not for anything else. For example, don't use the name to derive
    a dependency or input file that is not generated by the macro itself.
*   All the targets created in the macro should be coupled in some way to the
    main target.
*   Conventionally, `name` should be the first argument when defining a macro.
*   Keep the parameter names in the macro consistent. If a parameter is passed
    as an attribute value to the main target, keep its name the same. If a macro
    parameter serves the same purpose as a common rule attribute, such as
    `deps`, name as you would the attribute (see below).
*   When calling a macro, use only keyword arguments. This is consistent with
    rules, and greatly improves readability.

Engineers often write macros when the Starlark API of relevant rules is
insufficient for their specific use case, regardless of whether the rule is
defined within Bazel in native code, or in Starlark. If you're facing this
problem, ask the rule author if they can extend the API to accomplish your
goals.

As a rule of thumb, the more macros resemble the rules, the better.

See also [macros](/extending/macros#conventions).

## Rules {:#rules}

*   Rules, aspects, and their attributes should use lower_case names ("snake
    case").
*   Rule names are nouns that describe the main kind of artifact produced by the
    rule, from the point of view of its dependencies (or for leaf rules, the
    user). This is not necessarily a file suffix. For instance, a rule that
    produces C++ artifacts meant to be used as Python extensions might be called
    `py_extension`. For most languages, typical rules include:
    *   `*_library` - a compilation unit or "module".
    *   `*_binary` - a target producing an executable or a deployment unit.
    *   `*_test` - a test target. This can include multiple tests. Expect all
        tests in a `*_test` target to be variations on the same theme, for
        example, testing a single library.
    *   `*_import`: a target encapsulating a pre-compiled artifact, such as a
        `.jar`, or a `.dll` that is used during compilation.
*   Use consistent names and types for attributes. Some generally applicable
    attributes include:
    *   `srcs`: `label_list`, allowing files: source files, typically
        human-authored.
    *   `deps`: `label_list`, typically *not* allowing files: compilation
        dependencies.
    *   `data`: `label_list`, allowing files: data files, such as test data etc.
    *   `runtime_deps`: `label_list`: runtime dependencies that are not needed
        for compilation.
*   For any attributes with non-obvious behavior (for example, string templates
    with special substitutions, or tools that are invoked with specific
    requirements), provide documentation using the `doc` keyword argument to the
    attribute's declaration (`attr.label_list()` or similar).
*   Rule implementation functions should almost always be private functions
    (named with a leading underscore). A common style is to give the
    implementation function for `myrule` the name `_myrule_impl`.
*   Pass information between your rules using a well-defined
    [provider](/extending/rules#providers) interface. Declare and document provider
    fields.
*   Design your rule with extensibility in mind. Consider that other rules might
    want to interact with your rule, access your providers, and reuse the
    actions you create.
*   Follow [performance guidelines](/rules/performance) in your rules.


Project: /_project.yaml
Book: /_book.yaml

# Creating a Symbolic Macro

{% include "_buttons.html" %}

IMPORTANT: This tutorial is for [*symbolic macros*](/extending/macros) – the new
macro system introduced in Bazel 8. If you need to support older Bazel versions,
you will want to write a [legacy macro](/extending/legacy-macros) instead; take
a look at [Creating a Legacy Macro](../legacy-macro-tutorial).

Imagine that you need to run a tool as part of your build. For example, you
may want to generate or preprocess a source file, or compress a binary. In this
tutorial, you are going to create a symbolic macro that resizes an image.

Macros are suitable for simple tasks. If you want to do anything more
complicated, for example add support for a new programming language, consider
creating a [rule](/extending/rules). Rules give you more control and flexibility.

The easiest way to create a macro that resizes an image is to use a `genrule`:

```starlark
genrule(
    name = "logo_miniature",
    srcs = ["logo.png"],
    outs = ["small_logo.png"],
    cmd = "convert $< -resize 100x100 $@",
)

cc_binary(
    name = "my_app",
    srcs = ["my_app.cc"],
    data = [":logo_miniature"],
)
```

If you need to resize more images, you may want to reuse the code. To do that,
define an *implementation function* and a *macro declaration* in a separate
`.bzl` file, and call the file `miniature.bzl`:

```starlark
# Implementation function
def _miniature_impl(name, visibility, src, size, **kwargs):
    native.genrule(
        name = name,
        visibility = visibility,
        srcs = [src],
        outs = [name + "_small_" + src.name],
        cmd = "convert $< -resize " + size + " $@",
        **kwargs,
    )

# Macro declaration
miniature = macro(
    doc = """Create a miniature of the src image.

    The generated file name will be prefixed with `name + "_small_"`.
    """,
    implementation = _miniature_impl,
    # Inherit most of genrule's attributes (such as tags and testonly)
    inherit_attrs = native.genrule,
    attrs = {
        "src": attr.label(
            doc = "Image file",
            allow_single_file = True,
            # Non-configurable because our genrule's output filename is
            # suffixed with src's name. (We want to suffix the output file with
            # srcs's name because some tools that operate on image files expect
            # the files to have the right file extension.)
            configurable = False,
        ),
        "size": attr.string(
            doc = "Output size in WxH format",
            default = "100x100",
        ),
        # Do not allow callers of miniature() to set srcs, cmd, or outs -
        # _miniature_impl overrides their values when calling native.genrule()
        "srcs": None,
        "cmd": None,
        "outs": None,
    },
)
```

A few remarks:

  * Symbolic macro implementation functions must have `name` and `visibility`
    parameters. They should used for the macro's main target.

  * To document the behavior of a symbolic macro, use `doc` parameters for
    `macro()` and its attributes.

  * To call a `genrule`, or any other native rule, use `native.`.

  * Use `**kwargs` to forward the extra inherited arguments to the underlying
    `genrule` (it works just like in
    [Python](https://docs.python.org/3/tutorial/controlflow.html#keyword-arguments)).
    This is useful so that a user can set standard attributes like `tags` or
    `testonly`.

Now, use the macro from the `BUILD` file:

```starlark
load("//path/to:miniature.bzl", "miniature")

miniature(
    name = "logo_miniature",
    src = "image.png",
)

cc_binary(
    name = "my_app",
    srcs = ["my_app.cc"],
    data = [":logo_miniature"],
)
```


Project: /_project.yaml
Book: /_book.yaml

# Rules Tutorial

{% include "_buttons.html" %}

<!-- [TOC] -->

[Starlark](https://github.com/bazelbuild/starlark) is a Python-like
configuration language originally developed for use in Bazel and since adopted
by other tools. Bazel's `BUILD` and `.bzl` files are written in a dialect of
Starlark properly known as the "Build Language", though it is often simply
referred to as "Starlark", especially when emphasizing that a feature is
expressed in the Build Language as opposed to being a built-in or "native" part
of Bazel. Bazel augments the core language with numerous build-related functions
such as `glob`, `genrule`, `java_binary`, and so on.

See the
[Bazel](/start/) and [Starlark](/extending/concepts) documentation for
more details, and the
[Rules SIG template](https://github.com/bazel-contrib/rules-template) as a
starting point for new rulesets.

## The empty rule

To create your first rule, create the file `foo.bzl`:

```python
def _foo_binary_impl(ctx):
    pass

foo_binary = rule(
    implementation = _foo_binary_impl,
)
```

When you call the [`rule`](lib/globals#rule) function, you
must define a callback function. The logic will go there, but you
can leave the function empty for now. The [`ctx`](lib/ctx) argument
provides information about the target.

You can load the rule and use it from a `BUILD` file.

Create a `BUILD` file in the same directory:

```python
load(":foo.bzl", "foo_binary")

foo_binary(name = "bin")
```

Now, the target can be built:

```
$ bazel build bin
INFO: Analyzed target //:bin (2 packages loaded, 17 targets configured).
INFO: Found 1 target...
Target //:bin up-to-date (nothing to build)
```

Even though the rule does nothing, it already behaves like other rules: it has a
mandatory name, it supports common attributes like `visibility`, `testonly`, and
`tags`.

## Evaluation model

Before going further, it's important to understand how the code is evaluated.

Update `foo.bzl` with some print statements:

```python
def _foo_binary_impl(ctx):
    print("analyzing", ctx.label)

foo_binary = rule(
    implementation = _foo_binary_impl,
)

print("bzl file evaluation")
```

and BUILD:

```python
load(":foo.bzl", "foo_binary")

print("BUILD file")
foo_binary(name = "bin1")
foo_binary(name = "bin2")
```

[`ctx.label`](lib/ctx#label)
corresponds to the label of the target being analyzed. The `ctx` object has
many useful fields and methods; you can find an exhaustive list in the
[API reference](lib/ctx).

Query the code:

```
$ bazel query :all
DEBUG: /usr/home/bazel-codelab/foo.bzl:8:1: bzl file evaluation
DEBUG: /usr/home/bazel-codelab/BUILD:2:1: BUILD file
//:bin2
//:bin1
```

Make a few observations:

* "bzl file evaluation" is printed first. Before evaluating the `BUILD` file,
  Bazel evaluates all the files it loads. If multiple `BUILD` files are loading
  foo.bzl, you would see only one occurrence of "bzl file evaluation" because
  Bazel caches the result of the evaluation.
* The callback function `_foo_binary_impl` is not called. Bazel query loads
  `BUILD` files, but doesn't analyze targets.

To analyze the targets, use the [`cquery`](/query/cquery) ("configured
query") or the `build` command:

```
$ bazel build :all
DEBUG: /usr/home/bazel-codelab/foo.bzl:2:5: analyzing //:bin1
DEBUG: /usr/home/bazel-codelab/foo.bzl:2:5: analyzing //:bin2
INFO: Analyzed 2 targets (0 packages loaded, 0 targets configured).
INFO: Found 2 targets...
```

As you can see, `_foo_binary_impl` is now called twice - once for each target.

Notice that neither "bzl file evaluation" nor "BUILD file" are printed again,
because the evaluation of `foo.bzl` is cached after the call to `bazel query`.
Bazel only emits `print` statements when they are actually executed.

## Creating a file

To make your rule more useful, update it to generate a file. First, declare the
file and give it a name. In this example, create a file with the same name as
the target:

```python
ctx.actions.declare_file(ctx.label.name)
```

If you run `bazel build :all` now, you will get an error:

```
The following files have no generating action:
bin2
```

Whenever you declare a file, you have to tell Bazel how to generate it by
creating an action. Use [`ctx.actions.write`](lib/actions#write),
to create a file with the given content.

```python
def _foo_binary_impl(ctx):
    out = ctx.actions.declare_file(ctx.label.name)
    ctx.actions.write(
        output = out,
        content = "Hello\n",
    )
```

The code is valid, but it won't do anything:

```
$ bazel build bin1
Target //:bin1 up-to-date (nothing to build)
```

The `ctx.actions.write` function registered an action, which taught Bazel
how to generate the file. But Bazel won't create the file until it is
actually requested. So the last thing to do is tell Bazel that the file
is an output of the rule, and not a temporary file used within the rule
implementation.

```python
def _foo_binary_impl(ctx):
    out = ctx.actions.declare_file(ctx.label.name)
    ctx.actions.write(
        output = out,
        content = "Hello!\n",
    )
    return [DefaultInfo(files = depset([out]))]
```

Look at the `DefaultInfo` and `depset` functions later. For now,
assume that the last line is the way to choose the outputs of a rule.

Now, run Bazel:

```
$ bazel build bin1
INFO: Found 1 target...
Target //:bin1 up-to-date:
  bazel-bin/bin1

$ cat bazel-bin/bin1
Hello!
```

You have successfully generated a file!

## Attributes

To make the rule more useful, add new attributes using
[the `attr` module](lib/attr) and update the rule definition.

Add a string attribute called `username`:

```python
foo_binary = rule(
    implementation = _foo_binary_impl,
    attrs = {
        "username": attr.string(),
    },
)
```

Next, set it in the `BUILD` file:

```python
foo_binary(
    name = "bin",
    username = "Alice",
)
```

To access the value in the callback function, use `ctx.attr.username`. For
example:

```python
def _foo_binary_impl(ctx):
    out = ctx.actions.declare_file(ctx.label.name)
    ctx.actions.write(
        output = out,
        content = "Hello {}!\n".format(ctx.attr.username),
    )
    return [DefaultInfo(files = depset([out]))]
```

Note that you can make the attribute mandatory or set a default value. Look at
the documentation of [`attr.string`](lib/attr#string).
You may also use other types of attributes, such as [boolean](lib/attr#bool)
or [list of integers](lib/attr#int_list).

## Dependencies

Dependency attributes, such as [`attr.label`](lib/attr#label)
and [`attr.label_list`](lib/attr#label_list),
declare a dependency from the target that owns the attribute to the target whose
label appears in the attribute's value. This kind of attribute forms the basis
of the target graph.

In the `BUILD` file, the target label appears as a string object, such as
`//pkg:name`. In the implementation function, the target will be accessible as a
[`Target`](lib/Target) object. For example, view the files returned
by the target using [`Target.files`](lib/Target#modules.Target.files).

### Multiple files

By default, only targets created by rules may appear as dependencies (such as a
`foo_library()` target). If you want the attribute to accept targets that are
input files (such as source files in the repository), you can do it with
`allow_files` and specify the list of accepted file extensions (or `True` to
allow any file extension):

```python
"srcs": attr.label_list(allow_files = [".java"]),
```

The list of files can be accessed with `ctx.files.<attribute name>`. For
example, the list of files in the `srcs` attribute can be accessed through

```python
ctx.files.srcs
```

### Single file

If you need only one file, use `allow_single_file`:

```python
"src": attr.label(allow_single_file = [".java"])
```

This file is then accessible under `ctx.file.<attribute name>`:

```python
ctx.file.src
```

## Create a file with a template

You can create a rule that generates a .cc file based on a template. Also, you
can use `ctx.actions.write` to output a string constructed in the rule
implementation function, but this has two problems. First, as the template gets
bigger, it becomes more memory efficient to put it in a separate file and avoid
constructing large strings during the analysis phase. Second, using a separate
file is more convenient for the user. Instead, use
[`ctx.actions.expand_template`](lib/actions#expand_template),
which performs substitutions on a template file.

Create a `template` attribute to declare a dependency on the template
file:

```python
def _hello_world_impl(ctx):
    out = ctx.actions.declare_file(ctx.label.name + ".cc")
    ctx.actions.expand_template(
        output = out,
        template = ctx.file.template,
        substitutions = {"{NAME}": ctx.attr.username},
    )
    return [DefaultInfo(files = depset([out]))]

hello_world = rule(
    implementation = _hello_world_impl,
    attrs = {
        "username": attr.string(default = "unknown person"),
        "template": attr.label(
            allow_single_file = [".cc.tpl"],
            mandatory = True,
        ),
    },
)
```

Users can use the rule like this:

```python
hello_world(
    name = "hello",
    username = "Alice",
    template = "file.cc.tpl",
)

cc_binary(
    name = "hello_bin",
    srcs = [":hello"],
)
```

If you don't want to expose the template to the end-user and always use the
same one, you can set a default value and make the attribute private:

```python
    "_template": attr.label(
        allow_single_file = True,
        default = "file.cc.tpl",
    ),
```

Attributes that start with an underscore are private and cannot be set in a
`BUILD` file. The template is now an _implicit dependency_: Every `hello_world`
target has a dependency on this file. Don't forget to make this file visible
to other packages by updating the `BUILD` file and using
[`exports_files`](/reference/be/functions#exports_files):

```python
exports_files(["file.cc.tpl"])
```

## Going further

*   Take a look at the [reference documentation for rules](/extending/rules#contents).
*   Get familiar with [depsets](/extending/depsets).
*   Check out the [examples repository](https://github.com/bazelbuild/examples/tree/master/rules)
    which includes additional examples of rules.


Project: /_project.yaml
Book: /_book.yaml

# Challenges of Writing Rules

{% include "_buttons.html" %}

This page gives a high-level overview of the specific issues and challenges
of writing efficient Bazel rules.

## Summary Requirements {:#summary-requirements}

* Assumption: Aim for Correctness, Throughput, Ease of Use & Latency
* Assumption: Large Scale Repositories
* Assumption: BUILD-like Description Language
* Historic: Hard Separation between Loading, Analysis, and Execution is
  Outdated, but still affects the API
* Intrinsic: Remote Execution and Caching are Hard
* Intrinsic: Using Change Information for Correct and Fast Incremental Builds
  requires Unusual Coding Patterns
* Intrinsic: Avoiding Quadratic Time and Memory Consumption is Hard

## Assumptions {:#assumptions}

Here are some assumptions made about the build system, such as need for
correctness, ease of use, throughput, and large scale repositories. The
following sections address these assumptions and offer guidelines to ensure
rules are written in an effective manner.

### Aim for correctness, throughput, ease of use & latency {:#aim}

We assume that the build system needs to be first and foremost correct with
respect to incremental builds. For a given source tree, the output of the
same build should always be the same, regardless of what the output tree looks
like. In the first approximation, this means Bazel needs to know every single
input that goes into a given build step, such that it can rerun that step if any
of the inputs change. There are limits to how correct Bazel can get, as it leaks
some information such as date / time of the build, and ignores certain types of
changes such as changes to file attributes. [Sandboxing](/docs/sandboxing)
helps ensure correctness by preventing reads to undeclared input files. Besides
the intrinsic limits of the system, there are a few known correctness issues,
most of which are related to Fileset or the C++ rules, which are both hard
problems. We have long-term efforts to fix these.

The second goal of the build system is to have high throughput; we are
permanently pushing the boundaries of what can be done within the current
machine allocation for a remote execution service. If the remote execution
service gets overloaded, nobody can get work done.

Ease of use comes next. Of multiple correct approaches with the same (or
similar) footprint of the remote execution service, we choose the one that is
easier to use.

Latency denotes the time it takes from starting a build to getting the intended
result, whether that is a test log from a passing or failing test, or an error
message that a `BUILD` file has a typo.

Note that these goals often overlap; latency is as much a function of throughput
of the remote execution service as is correctness relevant for ease of use.

### Large scale repositories {:#large-repos}

The build system needs to operate at the scale of large repositories where large
scale means that it does not fit on a single hard drive, so it is impossible to
do a full checkout on virtually all developer machines. A medium-sized build
will need to read and parse tens of thousands of `BUILD` files, and evaluate
hundreds of thousands of globs. While it is theoretically possible to read all
`BUILD` files on a single machine, we have not yet been able to do so within a
reasonable amount of time and memory. As such, it is critical that `BUILD` files
can be loaded and parsed independently.

### BUILD-like description language {:#language}

In this context, we assume a configuration language that is
roughly similar to `BUILD` files in declaration of library and binary rules
and their interdependencies. `BUILD` files can be read and parsed independently,
and we avoid even looking at source files whenever we can (except for
existence).

## Historic {:#historic}

There are differences between Bazel versions that cause challenges and some
of these are outlined in the following sections.

### Hard separation between loading, analysis, and execution is outdated but still affects the API {:#loading-outdated}

Technically, it is sufficient for a rule to know the input and output files of
an action just before the action is sent to remote execution. However, the
original Bazel code base had a strict separation of loading packages, then
analyzing rules using a configuration (command-line flags, essentially), and
only then running any actions. This distinction is still part of the rules API
today, even though the core of Bazel no longer requires it (more details below).

That means that the rules API requires a declarative description of the rule
interface (what attributes it has, types of attributes). There are some
exceptions where the API allows custom code to run during the loading phase to
compute implicit names of output files and implicit values of attributes. For
example, a java_library rule named 'foo' implicitly generates an output named
'libfoo.jar', which can be referenced from other rules in the build graph.

Furthermore, the analysis of a rule cannot read any source files or inspect the
output of an action; instead, it needs to generate a partial directed bipartite
graph of build steps and output file names that is only determined from the rule
itself and its dependencies.

## Intrinsic {:#intrinsic}

There are some intrinsic properties that make writing rules challenging and
some of the most common ones are described in the following sections.

### Remote execution and caching are hard {:#remote-execution}

Remote execution and caching improve build times in large repositories by
roughly two orders of magnitude compared to running the build on a single
machine. However, the scale at which it needs to perform is staggering: Google's
remote execution service is designed to handle a huge number of requests per
second, and the protocol carefully avoids unnecessary roundtrips as well as
unnecessary work on the service side.

At this time, the protocol requires that the build system knows all inputs to a
given action ahead of time; the build system then computes a unique action
fingerprint, and asks the scheduler for a cache hit. If a cache hit is found,
the scheduler replies with the digests of the output files; the files itself are
addressed by digest later on. However, this imposes restrictions on the Bazel
rules, which need to declare all input files ahead of time.

### Using change information for correct and fast incremental builds requires unusual coding patterns {:#coding-patterns}

Above, we argued that in order to be correct, Bazel needs to know all the input
files that go into a build step in order to detect whether that build step is
still up-to-date. The same is true for package loading and rule analysis, and we
have designed [Skyframe](/reference/skyframe) to handle this
in general. Skyframe is a graph library and evaluation framework that takes a
goal node (such as 'build //foo with these options'), and breaks it down into
its constituent parts, which are then evaluated and combined to yield this
result. As part of this process, Skyframe reads packages, analyzes rules, and
executes actions.

At each node, Skyframe tracks exactly which nodes any given node used to compute
its own output, all the way from the goal node down to the input files (which
are also Skyframe nodes). Having this graph explicitly represented in memory
allows the build system to identify exactly which nodes are affected by a given
change to an input file (including creation or deletion of an input file), doing
the minimal amount of work to restore the output tree to its intended state.

As part of this, each node performs a dependency discovery process. Each
node can declare dependencies, and then use the contents of those dependencies
to declare even further dependencies. In principle, this maps well to a
thread-per-node model. However, medium-sized builds contain hundreds of
thousands of Skyframe nodes, which isn't easily possible with current Java
technology (and for historical reasons, we're currently tied to using Java, so
no lightweight threads and no continuations).

Instead, Bazel uses a fixed-size thread pool. However, that means that if a node
declares a dependency that isn't available yet, we may have to abort that
evaluation and restart it (possibly in another thread), when the dependency is
available. This, in turn, means that nodes should not do this excessively; a
node that declares N dependencies serially can potentially be restarted N times,
costing O(N^2) time. Instead, we aim for up-front bulk declaration of
dependencies, which sometimes requires reorganizing the code, or even splitting
a node into multiple nodes to limit the number of restarts.

Note that this technology isn't currently available in the rules API; instead,
the rules API is still defined using the legacy concepts of loading, analysis,
and execution phases. However, a fundamental restriction is that all accesses to
other nodes have to go through the framework so that it can track the
corresponding dependencies. Regardless of the language in which the build system
is implemented or in which the rules are written (they don't have to be the
same), rule authors must not use standard libraries or patterns that bypass
Skyframe. For Java, that means avoiding java.io.File as well as any form of
reflection, and any library that does either. Libraries that support dependency
injection of these low-level interfaces still need to be setup correctly for
Skyframe.

This strongly suggests to avoid exposing rule authors to a full language runtime
in the first place. The danger of accidental use of such APIs is just too big -
several Bazel bugs in the past were caused by rules using unsafe APIs, even
though the rules were written by the Bazel team or other domain experts.

### Avoiding quadratic time and memory consumption is hard {:#avoid}

To make matters worse, apart from the requirements imposed by Skyframe, the
historical constraints of using Java, and the outdatedness of the rules API,
accidentally introducing quadratic time or memory consumption is a fundamental
problem in any build system based on library and binary rules. There are two
very common patterns that introduce quadratic memory consumption (and therefore
quadratic time consumption).

1. Chains of Library Rules -
Consider the case of a chain of library rules A depends on B, depends on C, and
so on. Then, we want to compute some property over the transitive closure of
these rules, such as the Java runtime classpath, or the C++ linker command for
each library. Naively, we might take a standard list implementation; however,
this already introduces quadratic memory consumption: the first library
contains one entry on the classpath, the second two, the third three, and so
on, for a total of 1+2+3+...+N = O(N^2) entries.

2. Binary Rules Depending on the Same Library Rules -
Consider the case where a set of binaries that depend on the same library
rules — such as if you have a number of test rules that test the same
library code. Let's say out of N rules, half the rules are binary rules, and
the other half library rules. Now consider that each binary makes a copy of
some property computed over the transitive closure of library rules, such as
the Java runtime classpath, or the C++ linker command line. For example, it
could expand the command line string representation of the C++ link action. N/2
copies of N/2 elements is O(N^2) memory.

#### Custom collections classes to avoid quadratic complexity {:#custom-classes}

Bazel is heavily affected by both of these scenarios, so we introduced a set of
custom collection classes that effectively compress the information in memory by
avoiding the copy at each step. Almost all of these data structures have set
semantics, so we called it
[depset](/rules/lib/depset)
(also known as `NestedSet` in the internal implementation). The majority of
changes to reduce Bazel's memory consumption over the past several years were
changes to use depsets instead of whatever was previously used.

Unfortunately, usage of depsets does not automatically solve all the issues;
in particular, even just iterating over a depset in each rule re-introduces
quadratic time consumption. Internally, NestedSets also has some helper methods
to facilitate interoperability with normal collections classes; unfortunately,
accidentally passing a NestedSet to one of these methods leads to copying
behavior, and reintroduces quadratic memory consumption.


Project: /_project.yaml
Book: /_book.yaml

# Frequently Asked Questions

{% include "_buttons.html" %}

These are some common issues and questions with writing extensions.

## Why is my file not produced / my action never executed?

Bazel only executes the actions needed to produce the *requested* output files.

* If the file you want has a label, you can request it directly:
  `bazel build //pkg:myfile.txt`

* If the file is in an output group of the target, you may need to specify that
  output group on the command line:
  `bazel build //pkg:mytarget --output_groups=foo`

* If you want the file to be built automatically whenever your target is
  mentioned on the command line, add it to your rule's default outputs by
  returning a [`DefaultInfo`](lib/globals#DefaultInfo) provider.

See the [Rules page](/extending/rules#requesting-output-files) for more information.

## Why is my implementation function not executed?

Bazel analyzes only the targets that are requested for the build. You should
either name the target on the command line, or something that depends on the
target.

## A file is missing when my action or binary is executed

Make sure that 1) the file has been registered as an input to the action or
binary, and 2) the script or tool being executed is accessing the file using the
correct path.

For actions, you declare inputs by passing them to the `ctx.actions.*` function
that creates the action. The proper path for the file can be obtained using
[`File.path`](lib/File#path).

For binaries (the executable outputs run by a `bazel run` or `bazel test`
command), you declare inputs by including them in the
[runfiles](/extending/rules#runfiles). Instead of using the `path` field, use
[`File.short_path`](lib/File#short_path), which is file's path relative to
the runfiles directory in which the binary executes.

## How can I control which files are built by `bazel build //pkg:mytarget`?

Use the [`DefaultInfo`](lib/globals#DefaultInfo) provider to
[set the default outputs](/extending/rules#requesting-output-files).

## How can I run a program or do file I/O as part of my build?

A tool can be declared as a target, just like any other part of your build, and
run during the execution phase to help build other targets. To create an action
that runs a tool, use [`ctx.actions.run`](lib/actions#run) and pass in the
tool as the `executable` parameter.

During the loading and analysis phases, a tool *cannot* run, nor can you perform
file I/O. This means that tools and file contents (except the contents of BUILD
and .bzl files) cannot affect how the target and action graphs get created.

## What if I need to access the same structured data both before and during the execution phase?

You can format the structured data as a .bzl file. You can `load()` the file to
access it during the loading and analysis phases. You can pass it as an input or
runfile to actions and executables that need it during the execution phase.

## How should I document Starlark code?

For rules and rule attributes, you can pass a docstring literal (possibly
triple-quoted) to the `doc` parameter of `rule` or `attr.*()`. For helper
functions and macros, use a triple-quoted docstring literal following the format
given [here](https://github.com/bazelbuild/buildtools/blob/master/WARNINGS.md#function-docstring).
Rule implementation functions generally do not need their own docstring.

Using string literals in the expected places makes it easier for automated
tooling to extract documentation. Feel free to use standard non-string comments
wherever it may help the reader of your code.


Project: /_project.yaml
Book: /_book.yaml

# Writing Rules on Windows

{% include "_buttons.html" %}

This page focuses on writing Windows-compatible rules, common problems of
writing portable rules, and some solutions.

## Paths

Problems:

- **Length limit**: maximum path length is 259 characters.

  Though Windows also supports longer paths (up to 32767 characters), many programs are built with
  the lower limit.

  Be aware of this about programs you run in the actions.

- **Working directory**: is also limited to 259 characters.

  Processes cannot `cd` into a directory longer than 259 characters.

- **Case-sensitivity**: Windows paths are case-insensitive, Unix paths are case-sensitive.

  Be aware of this when creating command lines for actions.

- **Path separators**: are backslash (`\`), not forward slash (`/`).

  Bazel stores paths Unix-style with `/` separators. Though some Windows programs support
  Unix-style paths, others don't. Some built-in commands in cmd.exe support them, some don't.

  It's best to always use `\` separators on Windows: replace `/` with `\` when you create command
  lines and environment variables for actions.

- **Absolute paths**: don't start with slash (`/`).

  Absolute paths on Windows start with a drive letter, such as `C:\foo\bar.txt`. There's no single
  filesystem root.

  Be aware of this if your rule checks if a path is absolute. Absolute paths
  should be avoided since they are often non-portable.

Solutions:

- **Keep paths short.**

  Avoid long directory names, deeply nested directory structures, long file names, long workspace
  names, long target names.

  All of these may become path components of actions' input files, and may exhaust the path length
  limit.

- **Use a short output root.**

  Use the `--output_user_root=<path>` flag to specify a short path for Bazel outputs. A good idea
  is to have a drive (or virtual drive) just for Bazel outputs (such as `D:\`), and adding this line
  to your `.bazelrc` file:

  ```
  build --output_user_root=D:/
  ```

  or

  ```
  build --output_user_root=C:/_bzl
  ```

- **Use junctions.**

  Junctions are, loosely speaking<sup>[1]</sup>, directory symlinks. Junctions are easy to create
  and can point to directories (on the same computer) with long paths. If a build action creates a
  junction whose path is short but whose target is long, then tools with short path limit can access
  the files in the junction'ed directory.

  In `.bat` files or in cmd.exe you can create junctions like so:

  ```
  mklink /J c:\path\to\junction c:\path\to\very\long\target\path
  ```

  <sup>[1]</sup>: Strictly speaking
  [Junctions are not Symbolic Links](https://superuser.com/a/343079), but for
  the sake of build actions you may regard Junctions as Directory Symlinks.

- **Replace `/` with `\` in paths in actions / envvars.**

  When you create the command line or environment variables for an action, make the paths
  Windows-style. Example:

  ```python
  def as_path(p, is_windows):
      if is_windows:
          return p.replace("/", "\\")
      else:
          return p
  ```

## Environment variables

Problems:

- **Case-sensitivity**: Windows environment variable names are case-insensitive.

  For example, in Java `System.getenv("SystemRoot")` and `System.getenv("SYSTEMROOT")` yields the
  same result. (This applies to other languages too.)

- **Hermeticity**: actions should use as few custom environment variables as possible.

  Environment variables are part of the action's cache key. If an action uses environment variables
  that change often, or are custom to users, that makes the rule less cache-able.

Solutions:

- **Only use upper-case environment variable names.**

  This works on Windows, macOS, and Linux.

- **Minimize action environments.**

  When using `ctx.actions.run`, set the environment to `ctx.configuration.default_shell_env`. If the
  action needs more environment variables, put them all in a dictionary and pass that to the action.
  Example:

  ```python
  load("@bazel_skylib//lib:dicts.bzl", "dicts")

  def _make_env(ctx, output_file, is_windows):
      out_path = output_file.path
      if is_windows:
          out_path = out_path.replace("/", "\\")
      return dicts.add(ctx.configuration.default_shell_env, {"MY_OUTPUT": out_path})
  ```

## Actions

Problems:

- **Executable outputs**: Every executable file must have an executable extension.

  The most common extensions are `.exe` (binary files) and `.bat` (Batch scripts).

  Be aware that shell scripts (`.sh`) are NOT executable on Windows; you cannot specify them as
  `ctx.actions.run`'s `executable`. There's also no `+x` permission that files can have, so you
  can't execute arbitrary files like on Linux.

- **Bash commands**: For sake of portability, avoid running Bash commands directly in actions.

  Bash is widespread on Unix-like systems, but it's often unavailable on Windows. Bazel itself is
  relying less and less on Bash (MSYS2), so in the future users would be less likely to have MSYS2
  installed along with Bazel. To make rules easier to use on Windows, avoid running Bash commands in
  actions.

- **Line endings**: Windows uses CRLF (`\r\n`), Unix-like systems uses LF (`\n`).

  Be aware of this when comparing text files. Be mindful of your Git settings, especially of line
  endings when checking out or committing. (See Git's `core.autocrlf` setting.)

Solutions:

- **Use a Bash-less purpose-made rule.**

  `native.genrule()` is a wrapper for Bash commands, and it's often used to solve simple problems
  like copying a file or writing a text file. You can avoid relying on Bash (and reinventing the
  wheel): see if bazel-skylib has a purpose-made rule for your needs. None of them depends on Bash
  when built/tested on Windows.

  Build rule examples:

  - `copy_file()`
    ([source](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/copy_file.bzl),
    [documentation](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/copy_file_doc.md)):
    copies a file somewhere else, optionally making it executable

  - `write_file()`
    ([source](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/write_file.bzl),
    [documentation](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/write_file_doc.md)):
    writes a text file, with the desired line endings (`auto`, `unix`, or `windows`), optionally
    making it executable (if it's a script)

  - `run_binary()`
    ([source](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/run_binary.bzl),
    [documentation](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/run_binary_doc.md)):
    runs a binary (or `*_binary` rule) with given inputs and expected outputs as a build action
    (this is a build rule wrapper for `ctx.actions.run`)

  - `native_binary()`
    ([source](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/native_binary.bzl),
    [documentation](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/native_binary_doc.md#native_binary)):
    wraps a native binary in a `*_binary` rule, which you can `bazel run` or use in `run_binary()`'s
    `tool` attribute or `native.genrule()`'s `tools` attribute

  Test rule examples:

  - `diff_test()`
    ([source](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/diff_test.bzl),
    [documentation](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/diff_test_doc.md)):
    test that compares contents of two files

  - `native_test()`
    ([source](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/native_binary.bzl),
    [documentation](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/native_binary_doc.md#native_test)):
    wraps a native binary in a `*_test` rule, which you can `bazel test`

- **On Windows, consider using `.bat` scripts for trivial things.**

  Instead of `.sh` scripts, you can solve trivial tasks with `.bat` scripts.

  For example, if you need a script that does nothing, or prints a message, or exits with a fixed
  error code, then a simple `.bat` file will suffice. If your rule returns a `DefaultInfo()`
  provider, the `executable` field may refer to that `.bat` file on Windows.

  And since file extensions don't matter on macOS and Linux, you can always use `.bat` as the
  extension, even for shell scripts.

  Be aware that empty `.bat` files cannot be executed. If you need an empty script, write one space
  in it.

- **Use Bash in a principled way.**

  In Starlark build and test rules, use `ctx.actions.run_shell` to run Bash scripts and Bash
  commands as actions.

  In Starlark macros, wrap Bash scripts and commands in a `native.sh_binary()` or
  `native.genrule()`. Bazel will check if Bash is available and run the script or command through
  Bash.

  In Starlark repository rules, try avoiding Bash altogether. Bazel currently offers no way to run
  Bash commands in a principled way in repository rules.

## Deleting files

Problems:

- **Files cannot be deleted while open.**

  Open files cannot be deleted (by default), attempts result in "Access Denied"
  errors. If you cannot delete a file, maybe a running process still holds it
  open.

- **Working directory of a running process cannot be deleted.**

  Processes have an open handle to their working directory, and the directory cannot be deleted
  until the process terminates.

Solutions:

- **In your code, try to close files eagerly.**

  In Java, use `try-with-resources`. In Python, use `with open(...) as f:`. In principle, try
  closing handles as soon as possible.

<!--
TODO:
- runfiles, runfiles libraries, -nolegacy_external_runfiles
- runfiles envvars, runfiles manifest structure
- avoid using runfiles for things that could be inputs
- whether to use runfiles manifest on non-windows
- how to patch tools that expect to read from the filesystem to do a lookup through the manifest file instead (including helpers in many languages)
- how this applies in tests as well that rely on $TEST_SRCDIR
- unzip is slow
- cmd.exe has 8k command length limit
- put paths in envvars instead of args
- put cmd.exe commands in .bat files
- use ctx.resolve_tools instead of ctx.resolve_command (Bash dep)
- how to run cmd.exe actions (maybe I should write a genrule-like rule for these)

-->


Project: /_project.yaml
Book: /_book.yaml

# Testing

{% include "_buttons.html" %}

There are several different approaches to testing Starlark code in Bazel. This
page gathers the current best practices and frameworks by use case.

## Testing rules {:#testing-rules}

[Skylib](https://github.com/bazelbuild/bazel-skylib){: .external} has a test framework called
[`unittest.bzl`](https://github.com/bazelbuild/bazel-skylib/blob/main/lib/unittest.bzl){: .external}
for checking the analysis-time behavior of rules, such as their actions and
providers. Such tests are called "analysis tests" and are currently the best
option for testing the inner workings of rules.

Some caveats:

*   Test assertions occur within the build, not a separate test runner process.
    Targets that are created by the test must be named such that they do not
    collide with targets from other tests or from the build. An error that
    occurs during the test is seen by Bazel as a build breakage rather than a
    test failure.

*   It requires a fair amount of boilerplate to set up the rules under test and
    the rules containing test assertions. This boilerplate may seem daunting at
    first. It helps to [keep in mind](/extending/concepts#evaluation-model) that macros
    are evaluated and targets generated during the loading phase, while rule
    implementation functions don't run until later, during the analysis phase.

*   Analysis tests are intended to be fairly small and lightweight. Certain
    features of the analysis testing framework are restricted to verifying
    targets with a maximum number of transitive dependencies (currently 500).
    This is due to performance implications of using these features with larger
    tests.

The basic principle is to define a testing rule that depends on the
rule-under-test. This gives the testing rule access to the rule-under-test's
providers.

The testing rule's implementation function carries out assertions. If there are
any failures, these are not raised immediately by calling `fail()` (which would
trigger an analysis-time build error), but rather by storing the errors in a
generated script that fails at test execution time.

See below for a minimal toy example, followed by an example that checks actions.

### Minimal example {:#testing-rules-example}

`//mypkg/myrules.bzl`:

```python
MyInfo = provider(fields = {
    "val": "string value",
    "out": "output File",
})

def _myrule_impl(ctx):
    """Rule that just generates a file and returns a provider."""
    out = ctx.actions.declare_file(ctx.label.name + ".out")
    ctx.actions.write(out, "abc")
    return [MyInfo(val="some value", out=out)]

myrule = rule(
    implementation = _myrule_impl,
)
```

`//mypkg/myrules_test.bzl`:


```python
load("@bazel_skylib//lib:unittest.bzl", "asserts", "analysistest")
load(":myrules.bzl", "myrule", "MyInfo")

# ==== Check the provider contents ====

def _provider_contents_test_impl(ctx):
    env = analysistest.begin(ctx)

    target_under_test = analysistest.target_under_test(env)
    # If preferred, could pass these values as "expected" and "actual" keyword
    # arguments.
    asserts.equals(env, "some value", target_under_test[MyInfo].val)

    # If you forget to return end(), you will get an error about an analysis
    # test needing to return an instance of AnalysisTestResultInfo.
    return analysistest.end(env)

# Create the testing rule to wrap the test logic. This must be bound to a global
# variable, not called in a macro's body, since macros get evaluated at loading
# time but the rule gets evaluated later, at analysis time. Since this is a test
# rule, its name must end with "_test".
provider_contents_test = analysistest.make(_provider_contents_test_impl)

# Macro to setup the test.
def _test_provider_contents():
    # Rule under test. Be sure to tag 'manual', as this target should not be
    # built using `:all` except as a dependency of the test.
    myrule(name = "provider_contents_subject", tags = ["manual"])
    # Testing rule.
    provider_contents_test(name = "provider_contents_test",
                           target_under_test = ":provider_contents_subject")
    # Note the target_under_test attribute is how the test rule depends on
    # the real rule target.

# Entry point from the BUILD file; macro for running each test case's macro and
# declaring a test suite that wraps them together.
def myrules_test_suite(name):
    # Call all test functions and wrap their targets in a suite.
    _test_provider_contents()
    # ...

    native.test_suite(
        name = name,
        tests = [
            ":provider_contents_test",
            # ...
        ],
    )
```

`//mypkg/BUILD`:

```python
load(":myrules.bzl", "myrule")
load(":myrules_test.bzl", "myrules_test_suite")

# Production use of the rule.
myrule(
    name = "mytarget",
)

# Call a macro that defines targets that perform the tests at analysis time,
# and that can be executed with "bazel test" to return the result.
myrules_test_suite(name = "myrules_test")
```

The test can be run with `bazel test //mypkg:myrules_test`.

Aside from the initial `load()` statements, there are two main parts to the
file:

*   The tests themselves, each of which consists of 1) an analysis-time
    implementation function for the testing rule, 2) a declaration of the
    testing rule via `analysistest.make()`, and 3) a loading-time function
    (macro) for declaring the rule-under-test (and its dependencies) and testing
    rule. If the assertions do not change between test cases, 1) and 2) may be
    shared by multiple test cases.

*   The test suite function, which calls the loading-time functions for each
    test, and declares a `test_suite` target bundling all tests together.

For consistency, follow the recommended naming convention: Let `foo` stand for
the part of the test name that describes what the test is checking
(`provider_contents` in the above example). For example, a JUnit test method
would be named `testFoo`.

Then:

*   the macro which generates the test and target under test should should be
    named `_test_foo` (`_test_provider_contents`)

*   its test rule type should be named `foo_test` (`provider_contents_test`)

*   the label of the target of this rule type should be `foo_test`
    (`provider_contents_test`)

*   the implementation function for the testing rule should be named
    `_foo_test_impl` (`_provider_contents_test_impl`)

*   the labels of the targets of the rules under test and their dependencies
    should be prefixed with `foo_` (`provider_contents_`)

Note that the labels of all targets can conflict with other labels in the same
BUILD package, so it's helpful to use a unique name for the test.

### Failure testing {:#failure-testing}

It may be useful to verify that a rule fails given certain inputs or in certain
state. This can be done using the analysis test framework:

The test rule created with `analysistest.make` should specify `expect_failure`:

```python
failure_testing_test = analysistest.make(
    _failure_testing_test_impl,
    expect_failure = True,
)
```

The test rule implementation should make assertions on the nature of the failure
that took place (specifically, the failure message):

```python
def _failure_testing_test_impl(ctx):
    env = analysistest.begin(ctx)
    asserts.expect_failure(env, "This rule should never work")
    return analysistest.end(env)
```

Also make sure that your target under test is specifically tagged 'manual'.
Without this, building all targets in your package using `:all` will result in a
build of the intentionally-failing target and will exhibit a build failure. With
'manual', your target under test will build only if explicitly specified, or as
a dependency of a non-manual target (such as your test rule):

```python
def _test_failure():
    myrule(name = "this_should_fail", tags = ["manual"])

    failure_testing_test(name = "failure_testing_test",
                         target_under_test = ":this_should_fail")

# Then call _test_failure() in the macro which generates the test suite and add
# ":failure_testing_test" to the suite's test targets.
```

### Verifying registered actions {:#verifying-registered-actions}

You may want to write tests which make assertions about the actions that your
rule registers, for example, using `ctx.actions.run()`. This can be done in your
analysis test rule implementation function. An example:

```python
def _inspect_actions_test_impl(ctx):
    env = analysistest.begin(ctx)

    target_under_test = analysistest.target_under_test(env)
    actions = analysistest.target_actions(env)
    asserts.equals(env, 1, len(actions))
    action_output = actions[0].outputs.to_list()[0]
    asserts.equals(
        env, target_under_test.label.name + ".out", action_output.basename)
    return analysistest.end(env)
```

Note that `analysistest.target_actions(env)` returns a list of
[`Action`](lib/Action) objects which represent actions registered by the
target under test.

### Verifying rule behavior under different flags {:#verifying-rule-behavior}

You may want to verify your real rule behaves a certain way given certain build
flags. For example, your rule may behave differently if a user specifies:

```shell
bazel build //mypkg:real_target -c opt
```

versus

```shell
bazel build //mypkg:real_target -c dbg
```

At first glance, this could be done by testing the target under test using the
desired build flags:

```shell
bazel test //mypkg:myrules_test -c opt
```

But then it becomes impossible for your test suite to simultaneously contain a
test which verifies the rule behavior under `-c opt` and another test which
verifies the rule behavior under `-c dbg`. Both tests would not be able to run
in the same build!

This can be solved by specifying the desired build flags when defining the test
rule:

```python
myrule_c_opt_test = analysistest.make(
    _myrule_c_opt_test_impl,
    config_settings = {
        "//command_line_option:compilation_mode": "opt",
    },
)
```

Normally, a target under test is analyzed given the current build flags.
Specifying `config_settings` overrides the values of the specified command line
options. (Any unspecified options will retain their values from the actual
command line).

In the specified `config_settings` dictionary, command line flags must be
prefixed with a special placeholder value `//command_line_option:`, as is shown
above.


## Validating artifacts {:#validating-artifacts}

The main ways to check that your generated files are correct are:

*   You can write a test script in shell, Python, or another language, and
    create a target of the appropriate `*_test` rule type.

*   You can use a specialized rule for the kind of test you want to perform.

### Using a test target {:#using-test-target}

The most straightforward way to validate an artifact is to write a script and
add a `*_test` target to your BUILD file. The specific artifacts you want to
check should be data dependencies of this target. If your validation logic is
reusable for multiple tests, it should be a script that takes command line
arguments that are controlled by the test target's `args` attribute. Here's an
example that validates that the output of `myrule` from above is `"abc"`.

`//mypkg/myrule_validator.sh`:

```shell
if [ "$(cat $1)" = "abc" ]; then
  echo "Passed"
  exit 0
else
  echo "Failed"
  exit 1
fi
```

`//mypkg/BUILD`:

```python
...

myrule(
    name = "mytarget",
)

...

# Needed for each target whose artifacts are to be checked.
sh_test(
    name = "validate_mytarget",
    srcs = [":myrule_validator.sh"],
    args = ["$(location :mytarget.out)"],
    data = [":mytarget.out"],
)
```

### Using a custom rule {:#using-custom-rule}

A more complicated alternative is to write the shell script as a template that
gets instantiated by a new rule. This involves more indirection and Starlark
logic, but leads to cleaner BUILD files. As a side-benefit, any argument
preprocessing can be done in Starlark instead of the script, and the script is
slightly more self-documenting since it uses symbolic placeholders (for
substitutions) instead of numeric ones (for arguments).

`//mypkg/myrule_validator.sh.template`:

```shell
if [ "$(cat %TARGET%)" = "abc" ]; then
  echo "Passed"
  exit 0
else
  echo "Failed"
  exit 1
fi
```

`//mypkg/myrule_validation.bzl`:

```python
def _myrule_validation_test_impl(ctx):
  """Rule for instantiating myrule_validator.sh.template for a given target."""
  exe = ctx.outputs.executable
  target = ctx.file.target
  ctx.actions.expand_template(output = exe,
                              template = ctx.file._script,
                              is_executable = True,
                              substitutions = {
                                "%TARGET%": target.short_path,
                              })
  # This is needed to make sure the output file of myrule is visible to the
  # resulting instantiated script.
  return [DefaultInfo(runfiles=ctx.runfiles(files=[target]))]

myrule_validation_test = rule(
    implementation = _myrule_validation_test_impl,
    attrs = {"target": attr.label(allow_single_file=True),
             # You need an implicit dependency in order to access the template.
             # A target could potentially override this attribute to modify
             # the test logic.
             "_script": attr.label(allow_single_file=True,
                                   default=Label("//mypkg:myrule_validator"))},
    test = True,
)
```

`//mypkg/BUILD`:

```python
...

myrule(
    name = "mytarget",
)

...

# Needed just once, to expose the template. Could have also used export_files(),
# and made the _script attribute set allow_files=True.
filegroup(
    name = "myrule_validator",
    srcs = [":myrule_validator.sh.template"],
)

# Needed for each target whose artifacts are to be checked. Notice that you no
# longer have to specify the output file name in a data attribute, or its
# $(location) expansion in an args attribute, or the label for the script
# (unless you want to override it).
myrule_validation_test(
    name = "validate_mytarget",
    target = ":mytarget",
)
```

Alternatively, instead of using a template expansion action, you could have
inlined the template into the .bzl file as a string and expanded it during the
analysis phase using the `str.format` method or `%`-formatting.

## Testing Starlark utilities {:#testing-starlark-utilities}

[Skylib](https://github.com/bazelbuild/bazel-skylib){: .external}'s
[`unittest.bzl`](https://github.com/bazelbuild/bazel-skylib/blob/main/lib/unittest.bzl){: .external}
framework can be used to test utility functions (that is, functions that are
neither macros nor rule implementations). Instead of using `unittest.bzl`'s
`analysistest` library, `unittest` may be used. For such test suites, the
convenience function `unittest.suite()` can be used to reduce boilerplate.

`//mypkg/myhelpers.bzl`:

```python
def myhelper():
    return "abc"
```

`//mypkg/myhelpers_test.bzl`:


```python
load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":myhelpers.bzl", "myhelper")

def _myhelper_test_impl(ctx):
  env = unittest.begin(ctx)
  asserts.equals(env, "abc", myhelper())
  return unittest.end(env)

myhelper_test = unittest.make(_myhelper_test_impl)

# No need for a test_myhelper() setup function.

def myhelpers_test_suite(name):
  # unittest.suite() takes care of instantiating the testing rules and creating
  # a test_suite.
  unittest.suite(
    name,
    myhelper_test,
    # ...
  )
```

`//mypkg/BUILD`:

```python
load(":myhelpers_test.bzl", "myhelpers_test_suite")

myhelpers_test_suite(name = "myhelpers_tests")
```

For more examples, see Skylib's own [tests](https://github.com/bazelbuild/bazel-skylib/blob/main/tests/BUILD){: .external}.


Project: /_project.yaml
Book: /_book.yaml

# Optimizing Performance

{% include "_buttons.html" %}

When writing rules, the most common performance pitfall is to traverse or copy
data that is accumulated from dependencies. When aggregated over the whole
build, these operations can easily take O(N^2) time or space. To avoid this, it
is crucial to understand how to use depsets effectively.

This can be hard to get right, so Bazel also provides a memory profiler that
assists you in finding spots where you might have made a mistake. Be warned:
The cost of writing an inefficient rule may not be evident until it is in
widespread use.

## Use depsets {:#use-depsets}

Whenever you are rolling up information from rule dependencies you should use
[depsets](lib/depset). Only use plain lists or dicts to publish information
local to the current rule.

A depset represents information as a nested graph which enables sharing.

Consider the following graph:

```
C -> B -> A
D ---^
```

Each node publishes a single string. With depsets the data looks like this:

```
a = depset(direct=['a'])
b = depset(direct=['b'], transitive=[a])
c = depset(direct=['c'], transitive=[b])
d = depset(direct=['d'], transitive=[b])
```

Note that each item is only mentioned once. With lists you would get this:

```
a = ['a']
b = ['b', 'a']
c = ['c', 'b', 'a']
d = ['d', 'b', 'a']
```

Note that in this case `'a'` is mentioned four times! With larger graphs this
problem will only get worse.

Here is an example of a rule implementation that uses depsets correctly to
publish transitive information. Note that it is OK to publish rule-local
information using lists if you want since this is not O(N^2).

```
MyProvider = provider()

def _impl(ctx):
  my_things = ctx.attr.things
  all_things = depset(
      direct=my_things,
      transitive=[dep[MyProvider].all_things for dep in ctx.attr.deps]
  )
  ...
  return [MyProvider(
    my_things=my_things,  # OK, a flat list of rule-local things only
    all_things=all_things,  # OK, a depset containing dependencies
  )]
```

See the [depset overview](/extending/depsets) page for more information.

### Avoid calling `depset.to_list()` {:#avoid-depset-to-list}

You can coerce a depset to a flat list using
[`to_list()`](lib/depset#to_list), but doing so usually results in O(N^2)
cost. If at all possible, avoid any flattening of depsets except for debugging
purposes.

A common misconception is that you can freely flatten depsets if you only do it
at top-level targets, such as an `<xx>_binary` rule, since then the cost is not
accumulated over each level of the build graph. But this is *still* O(N^2) when
you build a set of targets with overlapping dependencies. This happens when
building your tests `//foo/tests/...`, or when importing an IDE project.

### Reduce the number of calls to `depset` {:#reduce-calls-depset}

Calling `depset` inside a loop is often a mistake. It can lead to depsets with
very deep nesting, which perform poorly. For example:

```python
x = depset()
for i in inputs:
    # Do not do that.
    x = depset(transitive = [x, i.deps])
```

This code can be replaced easily. First, collect the transitive depsets and
merge them all at once:

```python
transitive = []

for i in inputs:
    transitive.append(i.deps)

x = depset(transitive = transitive)
```

This can sometimes be reduced using a list comprehension:

```python
x = depset(transitive = [i.deps for i in inputs])
```

## Use ctx.actions.args() for command lines {:#ctx-actions-args}

When building command lines you should use [ctx.actions.args()](lib/Args).
This defers expansion of any depsets to the execution phase.

Apart from being strictly faster, this will reduce the memory consumption of
your rules -- sometimes by 90% or more.

Here are some tricks:

* Pass depsets and lists directly as arguments, instead of flattening them
yourself. They will get expanded by `ctx.actions.args()` for you.
If you need any transformations on the depset contents, look at
[ctx.actions.args#add](lib/Args#add) to see if anything fits the bill.

* Are you passing `File#path` as arguments? No need. Any
[File](lib/File) is automatically turned into its
[path](lib/File#path), deferred to expansion time.

* Avoid constructing strings by concatenating them together.
The best string argument is a constant as its memory will be shared between
all instances of your rule.

* If the args are too long for the command line an `ctx.actions.args()` object
can be conditionally or unconditionally written to a param file using
[`ctx.actions.args#use_param_file`](lib/Args#use_param_file). This is
done behind the scenes when the action is executed. If you need to explicitly
control the params file you can write it manually using
[`ctx.actions.write`](lib/actions#write).

Example:

```
def _impl(ctx):
  ...
  args = ctx.actions.args()
  file = ctx.declare_file(...)
  files = depset(...)

  # Bad, constructs a full string "--foo=<file path>" for each rule instance
  args.add("--foo=" + file.path)

  # Good, shares "--foo" among all rule instances, and defers file.path to later
  # It will however pass ["--foo", <file path>] to the action command line,
  # instead of ["--foo=<file_path>"]
  args.add("--foo", file)

  # Use format if you prefer ["--foo=<file path>"] to ["--foo", <file path>]
  args.add(format="--foo=%s", value=file)

  # Bad, makes a giant string of a whole depset
  args.add(" ".join(["-I%s" % file.short_path for file in files])

  # Good, only stores a reference to the depset
  args.add_all(files, format_each="-I%s", map_each=_to_short_path)

# Function passed to map_each above
def _to_short_path(f):
  return f.short_path
```

## Transitive action inputs should be depsets {:#transitive-action-inputs}

When building an action using [ctx.actions.run](lib/actions?#run), do not
forget that the `inputs` field accepts a depset. Use this whenever inputs are
collected from dependencies transitively.

```
inputs = depset(...)
ctx.actions.run(
  inputs = inputs,  # Do *not* turn inputs into a list
  ...
)
```

## Hanging {:#hanging}

If Bazel appears to be hung, you can hit <kbd>Ctrl-&#92;</kbd> or send
Bazel a `SIGQUIT` signal (`kill -3 $(bazel info server_pid)`) to get a thread
dump in the file `$(bazel info output_base)/server/jvm.out`.

Since you may not be able to run `bazel info` if bazel is hung, the
`output_base` directory is usually the parent of the `bazel-<workspace>`
symlink in your workspace directory.

## Performance profiling {:#performance-profiling}

The [JSON trace profile](/advanced/performance/json-trace-profile) can be very
useful to quickly understand what Bazel spent time on during the invocation.

The [`--experimental_command_profile`](https://bazel.build/reference/command-line-reference#flag--experimental_command_profile)
flag may be used to capture Java Flight Recorder profiles of various kinds
(cpu time, wall time, memory allocations and lock contention).

The [`--starlark_cpu_profile`](https://bazel.build/reference/command-line-reference#flag--starlark_cpu_profile)
flag may be used to write a pprof profile of CPU usage by all Starlark threads.

## Memory profiling {:#memory-profiling}

Bazel comes with a built-in memory profiler that can help you check your rule’s
memory use. If there is a problem you can dump the heap to find the
exact line of code that is causing the problem.

### Enabling memory tracking {:#enabling-memory-tracking}

You must pass these two startup flags to *every* Bazel invocation:

  ```
  STARTUP_FLAGS=\
  --host_jvm_args=-javaagent:<path to java-allocation-instrumenter-3.3.4.jar> \
  --host_jvm_args=-DRULE_MEMORY_TRACKER=1
  ```
Note: You can download the allocation instrumenter jar file from [Maven Central
Repository][allocation-instrumenter-link].

[allocation-instrumenter-link]: https://repo1.maven.org/maven2/com/google/code/java-allocation-instrumenter/java-allocation-instrumenter/3.3.4

These start the server in memory tracking mode. If you forget these for even
one Bazel invocation the server will restart and you will have to start over.

### Using the Memory Tracker {:#memory-tracker}

As an example, look at the target `foo` and see what it does. To only
run the analysis and not run the build execution phase, add the
`--nobuild` flag.

```
$ bazel $(STARTUP_FLAGS) build --nobuild //foo:foo
```

Next, see how much memory the whole Bazel instance consumes:

```
$ bazel $(STARTUP_FLAGS) info used-heap-size-after-gc
> 2594MB
```

Break it down by rule class by using `bazel dump --rules`:

```
$ bazel $(STARTUP_FLAGS) dump --rules
>

RULE                                 COUNT     ACTIONS          BYTES         EACH
genrule                             33,762      33,801    291,538,824        8,635
config_setting                      25,374           0     24,897,336          981
filegroup                           25,369      25,369     97,496,272        3,843
cc_library                           5,372      73,235    182,214,456       33,919
proto_library                        4,140     110,409    186,776,864       45,115
android_library                      2,621      36,921    218,504,848       83,366
java_library                         2,371      12,459     38,841,000       16,381
_gen_source                            719       2,157      9,195,312       12,789
_check_proto_library_deps              719         668      1,835,288        2,552
... (more output)
```

Look at where the memory is going by producing a `pprof` file
using `bazel dump --skylark_memory`:

```
$ bazel $(STARTUP_FLAGS) dump --skylark_memory=$HOME/prof.gz
> Dumping Starlark heap to: /usr/local/google/home/$USER/prof.gz
```

Use the `pprof` tool to investigate the heap. A good starting point is
getting a flame graph by using `pprof -flame $HOME/prof.gz`.

Get `pprof` from [https://github.com/google/pprof](https://github.com/google/pprof){: .external}.

Get a text dump of the hottest call sites annotated with lines:

```
$ pprof -text -lines $HOME/prof.gz
>
      flat  flat%   sum%        cum   cum%
  146.11MB 19.64% 19.64%   146.11MB 19.64%  android_library <native>:-1
  113.02MB 15.19% 34.83%   113.02MB 15.19%  genrule <native>:-1
   74.11MB  9.96% 44.80%    74.11MB  9.96%  glob <native>:-1
   55.98MB  7.53% 52.32%    55.98MB  7.53%  filegroup <native>:-1
   53.44MB  7.18% 59.51%    53.44MB  7.18%  sh_test <native>:-1
   26.55MB  3.57% 63.07%    26.55MB  3.57%  _generate_foo_files /foo/tc/tc.bzl:491
   26.01MB  3.50% 66.57%    26.01MB  3.50%  _build_foo_impl /foo/build_test.bzl:78
   22.01MB  2.96% 69.53%    22.01MB  2.96%  _build_foo_impl /foo/build_test.bzl:73
   ... (more output)
```


Project: /_project.yaml
Book: /_book.yaml

# Deploying Rules

{% include "_buttons.html" %}

This page is for rule writers who are planning to make their rules available
to others.

We recommend you start a new ruleset from the template repository:
https://github.com/bazel-contrib/rules-template
That template follows the recommendations below, and includes API documentation generation
and sets up a CI/CD pipeline to make it trivial to distribute your ruleset.

## Hosting and naming rules

New rules should go into their own GitHub repository under your organization.
Start a thread on [GitHub](https://github.com/bazelbuild/bazel/discussions)
if you feel like your rules belong in the [bazelbuild](https://github.com/bazelbuild)
organization.

Repository names for Bazel rules are standardized on the following format:
`$ORGANIZATION/rules_$NAME`.
See [examples on GitHub](https://github.com/search?q=rules+bazel&type=Repositories).
For consistency, you should follow this same format when publishing your Bazel rules.

Make sure to use a descriptive GitHub repository description and `README.md`
title, example:

* Repository name: `bazelbuild/rules_go`
* Repository description: *Go rules for Bazel*
* Repository tags: `golang`, `bazel`
* `README.md` header: *Go rules for [Bazel](https://bazel.build)*
(note the link to https://bazel.build which will guide users who are unfamiliar
with Bazel to the right place)

Rules can be grouped either by language (such as Scala), runtime platform
(such as Android), or framework (such as Spring).

## Repository content

Every rule repository should have a certain layout so that users can quickly
understand new rules.

For example, when writing new rules for the (make-believe)
`mockascript` language, the rule repository would have the following structure:

```
/
  LICENSE
  README
  MODULE.bazel
  mockascript/
    constraints/
      BUILD
    runfiles/
      BUILD
      runfiles.mocs
    BUILD
    defs.bzl
  tests/
    BUILD
    some_test.sh
    another_test.py
  examples/
    BUILD
    bin.mocs
    lib.mocs
    test.mocs
```

### MODULE.bazel

In the project's `MODULE.bazel`, you should define the name that users will use
to reference your rules. If your rules belong to the
[bazelbuild](https://github.com/bazelbuild) organization, you must use
`rules_<lang>` (such as `rules_mockascript`). Otherwise, you should name your
repository `<org>_rules_<lang>` (such as `build_stack_rules_proto`). Please
start a thread on [GitHub](https://github.com/bazelbuild/bazel/discussions)
if you feel like your rules should follow the convention for rules in the
[bazelbuild](https://github.com/bazelbuild) organization.

In the following sections, assume the repository belongs to the
[bazelbuild](https://github.com/bazelbuild) organization.

```
module(name = "rules_mockascript")
```

### README

At the top level, there should be a `README` that contains a brief description
of your ruleset, and the API users should expect.

### Rules

Often times there will be multiple rules provided by your repository. Create a
directory named by the language and provide an entry point - `defs.bzl` file
exporting all rules (also include a `BUILD` file so the directory is a package).
For `rules_mockascript` that means there will be a directory named
`mockascript`, and a `BUILD` file and a `defs.bzl` file inside:

```
/
  mockascript/
    BUILD
    defs.bzl
```

### Constraints

If your rule defines
[toolchain](/extending/toolchains) rules,
it's possible that you'll need to define custom `constraint_setting`s and/or
`constraint_value`s. Put these into a `//<LANG>/constraints` package. Your
directory structure will look like this:

```
/
  mockascript/
    constraints/
      BUILD
    BUILD
    defs.bzl
```

Please read
[github.com/bazelbuild/platforms](https://github.com/bazelbuild/platforms)
for best practices, and to see what constraints are already present, and
consider contributing your constraints there if they are language independent.
Be mindful of introducing custom constraints, all users of your rules will
use them to perform platform specific logic in their `BUILD` files (for example,
using [selects](/reference/be/functions#select)).
With custom constraints, you define a language that the whole Bazel ecosystem
will speak.

### Runfiles library

If your rule provides a standard library for accessing runfiles, it should be
in the form of a library target located at `//<LANG>/runfiles` (an abbreviation
of `//<LANG>/runfiles:runfiles`). User targets that need to access their data
dependencies will typically add this target to their `deps` attribute.

### Repository rules

#### Dependencies

Your rules might have external dependencies, which you'll need to specify in
your MODULE.bazel file.

#### Registering toolchains

Your rules might also register toolchains, which you can also specify in the
MODULE.bazel file.

Note that in order to resolve toolchains in the analysis phase Bazel needs to
analyze all `toolchain` targets that are registered. Bazel will not need to
analyze all targets referenced by `toolchain.toolchain` attribute. If in order
to register toolchains you need to perform complex computation in the
repository, consider splitting the repository with `toolchain` targets from the
repository with `<LANG>_toolchain` targets. Former will be always fetched, and
the latter will only be fetched when user actually needs to build `<LANG>` code.


#### Release snippet

In your release announcement provide a snippet that your users can copy-paste
into their `MODULE.bazel` file. This snippet in general will look as follows:

```
bazel_dep(name = "rules_<LANG>", version = "<VERSION>")
```


### Tests

There should be tests that verify that the rules are working as expected. This
can either be in the standard location for the language the rules are for or a
`tests/` directory at the top level.

### Examples (optional)

It is useful to users to have an `examples/` directory that shows users a couple
of basic ways that the rules can be used.

## CI/CD

Many rulesets use GitHub Actions. See the configuration used in the [rules-template](https://github.com/bazel-contrib/rules-template/tree/main/.github/workflows) repo, which are simplified using a "reusable workflow" hosted in the bazel-contrib
org. `ci.yaml` runs tests on each PR and `main` comit, and `release.yaml` runs anytime you push a tag to the repository.
See comments in the rules-template repo for more information.

If your repository is under the [bazelbuild organization](https://github.com/bazelbuild),
you can [ask to add](https://github.com/bazelbuild/continuous-integration/issues/new?template=adding-your-project-to-bazel-ci.md&title=Request+to+add+new+project+%5BPROJECT_NAME%5D&labels=new-project)
it to [ci.bazel.build](http://ci.bazel.build).

## Documentation

See the [Stardoc documentation](https://github.com/bazelbuild/stardoc) for
instructions on how to comment your rules so that documentation can be generated
automatically.

The [rules-template docs/ folder](https://github.com/bazel-contrib/rules-template/tree/main/docs)
shows a simple way to ensure the Markdown content in the `docs/` folder is always up-to-date
as Starlark files are updated.

## FAQs

### Why can't we add our rule to the main Bazel GitHub repository?

We want to decouple rules from Bazel releases as much as possible. It's clearer
who owns individual rules, reducing the load on Bazel developers. For our users,
decoupling makes it easier to modify, upgrade, downgrade, and replace rules.
Contributing to rules can be lighter weight than contributing to Bazel -
depending on the rules -, including full submit access to the corresponding
GitHub repository. Getting submit access to Bazel itself is a much more involved
process.

The downside is a more complicated one-time installation process for our users:
they have to add a dependency on your ruleset in their `MODULE.bazel` file.

We used to have all of the rules in the Bazel repository (under
`//tools/build_rules` or `//tools/build_defs`). We still have a couple rules
there, but we are working on moving the remaining rules out.


Project: /_project.yaml
Book: /_book.yaml

# Creating a Legacy Macro

{% include "_buttons.html" %}

IMPORTANT: This tutorial is for [*legacy macros*](/extending/legacy-macros). If
you only need to support Bazel 8 or newer, we recommend using [symbolic
macros](/extending/macros) instead; take a look at [Creating a Symbolic
Macro](../macro-tutorial).

Imagine that you need to run a tool as part of your build. For example, you
may want to generate or preprocess a source file, or compress a binary. In this
tutorial, you are going to create a legacy macro that resizes an image.

Macros are suitable for simple tasks. If you want to do anything more
complicated, for example add support for a new programming language, consider
creating a [rule](/extending/rules). Rules give you more control and flexibility.

The easiest way to create a macro that resizes an image is to use a `genrule`:

```starlark
genrule(
    name = "logo_miniature",
    srcs = ["logo.png"],
    outs = ["small_logo.png"],
    cmd = "convert $< -resize 100x100 $@",
)

cc_binary(
    name = "my_app",
    srcs = ["my_app.cc"],
    data = [":logo_miniature"],
)
```

If you need to resize more images, you may want to reuse the code. To do that,
define a function in a separate `.bzl` file, and call the file `miniature.bzl`:

```starlark
def miniature(name, src, size = "100x100", **kwargs):
    """Create a miniature of the src image.

    The generated file is prefixed with 'small_'.
    """
    native.genrule(
        name = name,
        srcs = [src],
        # Note that the line below will fail if `src` is not a filename string
        outs = ["small_" + src],
        cmd = "convert $< -resize " + size + " $@",
        **kwargs
    )
```

A few remarks:

  * By convention, legacy macros have a `name` argument, just like rules.

  * To document the behavior of a legacy macro, use
    [docstring](https://www.python.org/dev/peps/pep-0257/) like in Python.

  * To call a `genrule`, or any other native rule, prefix with `native.`.

  * Use `**kwargs` to forward the extra arguments to the underlying `genrule`
    (it works just like in
    [Python](https://docs.python.org/3/tutorial/controlflow.html#keyword-arguments)).
    This is useful, so that a user can use standard attributes like
    `visibility`, or `tags`.

Now, use the macro from the `BUILD` file:

```starlark
load("//path/to:miniature.bzl", "miniature")

miniature(
    name = "logo_miniature",
    src = "image.png",
)

cc_binary(
    name = "my_app",
    srcs = ["my_app.cc"],
    data = [":logo_miniature"],
)
```

And finally, a **warning note**: the macro assumes that `src` is a filename
string (otherwise, `outs = ["small_" + src]` will fail). So `src = "image.png"`
works; but what happens if the `BUILD` file instead used `src =
"//other/package:image.png"`, or even `src = select(...)`?

You should make sure to declare such assumptions in your macro's documentation.
Unfortunately, legacy macros, especially large ones, tend to be fragile because
it can be hard to notice and document all such assumptions in your code – and,
of course, some users of the macro won't read the documentation. We recommend,
if possible, instead using [symbolic macros](/extending/macros), which have
built\-in checks on attribute types.


Project: /_project.yaml
Book: /_book.yaml

# Using Macros to Create Custom Verbs

{% include "_buttons.html" %}

Day-to-day interaction with Bazel happens primarily through a few commands:
`build`, `test`, and `run`. At times, though, these can feel limited: you may
want to push packages to a repository, publish documentation for end-users, or
deploy an application with Kubernetes. But Bazel doesn't have a `publish` or
`deploy` command – where do these actions fit in?

## The bazel run command

Bazel's focus on hermeticity, reproducibility, and incrementality means the
`build` and `test` commands aren't helpful for the above tasks. These actions
may run in a sandbox, with limited network access, and aren't guaranteed to be
re-run with every `bazel build`.

Instead, rely on `bazel run`: the workhorse for tasks that you *want* to have
side effects. Bazel users are accustomed to rules that create executables, and
rule authors can follow a common set of patterns to extend this to
"custom verbs".

### In the wild: rules_k8s
For example, consider [`rules_k8s`](https://github.com/bazelbuild/rules_k8s),
the Kubernetes rules for Bazel. Suppose you have the following target:

```python
# BUILD file in //application/k8s
k8s_object(
    name = "staging",
    kind = "deployment",
    cluster = "testing",
    template = "deployment.yaml",
)
```

The [`k8s_object` rule](https://github.com/bazelbuild/rules_k8s#usage) builds a
standard Kubernetes YAML file when `bazel build` is used on the `staging`
target. However, the additional targets are also created by the `k8s_object`
macro with names like `staging.apply` and `:staging.delete`. These build
scripts to perform those actions, and when executed with `bazel run
staging.apply`, these behave like our own `bazel k8s-apply` or `bazel
k8s-delete` commands.

### Another example: ts_api_guardian_test

This pattern can also be seen in the Angular project. The
[`ts_api_guardian_test` macro](https://github.com/angular/angular/blob/16ac611a8410e6bcef8ffc779f488ca4fa102155/tools/ts-api-guardian/index.bzl#L22)
produces two targets. The first is a standard `nodejs_test` target which compares
some generated output against a "golden" file (that is, a file containing the
expected output). This can be built and run with a normal `bazel
test` invocation. In `angular-cli`, you can run [one such
target](https://github.com/angular/angular-cli/blob/e1269cb520871ee29b1a4eec6e6c0e4a94f0b5fc/etc/api/BUILD)
with `bazel test //etc/api:angular_devkit_core_api`.

Over time, this golden file may need to be updated for legitimate reasons.
Updating this manually is tedious and error-prone, so this macro also provides
a `nodejs_binary` target that updates the golden file, instead of comparing
against it. Effectively, the same test script can be written to run in "verify"
or "accept" mode, based on how it's invoked. This follows the same pattern
you've learned already: there is no native `bazel test-accept` command, but the
same effect can be achieved with
`bazel run //etc/api:angular_devkit_core_api.accept`.

This pattern can be quite powerful, and turns out to be quite common once you
learn to recognize it.

## Adapting your own rules

[Macros](/extending/macros) are the heart of this pattern. Macros are used like
rules, but they can create several targets. Typically, they will create a
target with the specified name which performs the primary build action: perhaps
it builds a normal binary, a Docker image, or an archive of source code. In
this pattern, additional targets are created to produce scripts performing side
effects based on the output of the primary target, like publishing the
resulting binary or updating the expected test output.

To illustrate this, wrap an imaginary rule that generates a website with
[Sphinx](https://www.sphinx-doc.org) with a macro to create an additional
target that allows the user to publish it when ready. Consider the following
existing rule for generating a website with Sphinx:

```python
_sphinx_site = rule(
     implementation = _sphinx_impl,
     attrs = {"srcs": attr.label_list(allow_files = [".rst"])},
)
```

Next, consider a rule like the following, which builds a script that, when run,
publishes the generated pages:

```python
_sphinx_publisher = rule(
    implementation = _publish_impl,
    attrs = {
        "site": attr.label(),
        "_publisher": attr.label(
            default = "//internal/sphinx:publisher",
            executable = True,
        ),
    },
    executable = True,
)
```

Finally, define the following symbolic macro (available in Bazel 8 or newer) to
create targets for both of the above rules together:

```starlark
def _sphinx_site_impl(name, visibility, srcs, **kwargs):
    # This creates the primary target, producing the Sphinx-generated HTML. We
    # set `visibility = visibility` to make it visible to callers of the
    # macro.
    _sphinx_site(name = name, visibility = visibility, srcs = srcs, **kwargs)
    # This creates the secondary target, which produces a script for publishing
    # the site generated above. We don't want it to be visible to callers of
    # our macro, so we omit visibility for it.
    _sphinx_publisher(name = "%s.publish" % name, site = name, **kwargs)

sphinx_site = macro(
    implementation = _sphinx_site_impl,
    attrs = {"srcs": attr.label_list(allow_files = [".rst"])},
    # Inherit common attributes like tags and testonly
    inherit_attrs = "common",
)
```

Or, if you need to support Bazel releases older than Bazel 8, you would instead
define a legacy macro:

```starlark
def sphinx_site(name, srcs = [], **kwargs):
    # This creates the primary target, producing the Sphinx-generated HTML.
    _sphinx_site(name = name, srcs = srcs, **kwargs)
    # This creates the secondary target, which produces a script for publishing
    # the site generated above.
    _sphinx_publisher(name = "%s.publish" % name, site = name, **kwargs)
```

In the `BUILD` files, use the macro as though it just creates the primary
target:

```python
sphinx_site(
    name = "docs",
    srcs = ["index.md", "providers.md"],
)
```

In this example, a "docs" target is created, just as though the macro were a
standard, single Bazel rule. When built, the rule generates some configuration
and runs Sphinx to produce an HTML site, ready for manual inspection. However,
an additional "docs.publish" target is also created, which builds a script for
publishing the site. Once you check the output of the primary target, you can
use `bazel run :docs.publish` to publish it for public consumption, just like
an imaginary `bazel publish` command.

It's not immediately obvious what the implementation of the `_sphinx_publisher`
rule might look like. Often, actions like this write a _launcher_ shell script.
This method typically involves using
[`ctx.actions.expand_template`](lib/actions#expand_template)
to write a very simple shell script, in this case invoking the publisher binary
with a path to the output of the primary target. This way, the publisher
implementation can remain generic, the `_sphinx_site` rule can just produce
HTML, and this small script is all that's necessary to combine the two
together.

In `rules_k8s`, this is indeed what `.apply` does:
[`expand_template`](https://github.com/bazelbuild/rules_k8s/blob/f10e7025df7651f47a76abf1db5ade1ffeb0c6ac/k8s/object.bzl#L213-L241)
writes a very simple Bash script, based on
[`apply.sh.tpl`](https://github.com/bazelbuild/rules_k8s/blob/f10e7025df7651f47a76abf1db5ade1ffeb0c6ac/k8s/apply.sh.tpl),
which runs `kubectl` with the output of the primary target. This script can
then be build and run with `bazel run :staging.apply`, effectively providing a
`k8s-apply` command for `k8s_object` targets.
