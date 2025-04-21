

Project: /_project.yaml
Book: /_book.yaml
{# disableFinding("Currently") #}
{# disableFinding(TODO) #}

# Macros

{% include "_buttons.html" %}

This page covers the basics of using macros and includes typical use cases,
debugging, and conventions.

A macro is a function called from the `BUILD` file that can instantiate rules.
Macros are mainly used for encapsulation and code reuse of existing rules and
other macros.

Macros come in two flavors: symbolic macros, which are described on this page,
and [legacy macros](legacy-macros.md). Where possible, we recommend using
symbolic macros for code clarity.

Symbolic macros offer typed arguments (string to label conversion, relative to
where the macro was called) and the ability to restrict and specify the
visibility of targets created. They are designed to be amenable to lazy
evaluation (which will be added in a future Bazel release). Symbolic macros are
available by default in Bazel 8. Where this document mentions `macros`, it's
referring to **symbolic macros**.

An executable example of symbolic macros can be found in the
[examples repository](https://github.com/bazelbuild/examples/tree/main/macros).

## Usage {:#usage}

Macros are defined in `.bzl` files by calling the
[`macro()`](https://bazel.build/rules/lib/globals/bzl.html#macro) function with
two required parameters: `attrs` and `implementation`.

### Attributes {:#attributes}

`attrs` accepts a dictionary of attribute name to [attribute
types](https://bazel.build/rules/lib/toplevel/attr#members), which represents
the arguments to the macro. Two common attributes – `name` and `visibility` –
are implicitly added to all macros and are not included in the dictionary passed
to `attrs`.

```starlark
# macro/macro.bzl
my_macro = macro(
    attrs = {
        "deps": attr.label_list(mandatory = True, doc = "The dependencies passed to the inner cc_binary and cc_test targets"),
        "create_test": attr.bool(default = False, configurable = False, doc = "If true, creates a test target"),
    },
    implementation = _my_macro_impl,
)
```

Attribute type declarations accept the
[parameters](https://bazel.build/rules/lib/toplevel/attr#parameters),
`mandatory`, `default`, and `doc`. Most attribute types also accept the
`configurable` parameter, which determines wheher the attribute accepts
`select`s. If an attribute is `configurable`, it will parse non-`select` values
as an unconfigurable `select` – `"foo"` will become
`select({"//conditions:default": "foo"})`. Learn more in [selects](#selects).

#### Attribute inheritance {:#attribute-inheritance}

Macros are often intended to wrap a rule (or another macro), and the macro's
author often wants to forward the bulk of the wrapped symbol's attributes
unchanged, using `**kwargs`, to the macro's main target (or main inner macro).

To support this pattern, a macro can *inherit attributes* from a rule or another
macro by passing the [rule](https://bazel.build/rules/lib/builtins/rule) or
[macro symbol](https://bazel.build/rules/lib/builtins/macro) to `macro()`'s
`inherit_attrs` argument. (You can also use the special string `"common"`
instead of a rule or macro symbol to inherit the [common attributes defined for
all Starlark build
rules](https://bazel.build/reference/be/common-definitions#common-attributes).)
Only public attributes get inherited, and the attributes in the macro's own
`attrs` dictionary override inherited attributes with the same name. You can
also *remove* inherited attributes by using `None` as a value in the `attrs`
dictionary:

```starlark
# macro/macro.bzl
my_macro = macro(
    inherit_attrs = native.cc_library,
    attrs = {
        # override native.cc_library's `local_defines` attribute
        "local_defines": attr.string_list(default = ["FOO"]),
        # do not inherit native.cc_library's `defines` attribute
        "defines": None,
    },
    ...
)
```

The default value of non-mandatory inherited attributes is always overridden to
be `None`, regardless of the original attribute definition's default value. If
you need to examine or modify an inherited non-mandatory attribute – for
example, if you want to add a tag to an inherited `tags` attribute – you must
make sure to handle the `None` case in your macro's implementation function:

```starlark
# macro/macro.bzl
_my_macro_implementation(name, visibility, tags, **kwargs):
    # Append a tag; tags attr is an inherited non-mandatory attribute, and
    # therefore is None unless explicitly set by the caller of our macro.
    my_tags = (tags or []) + ["another_tag"]
    native.cc_library(
        ...
        tags = my_tags,
        **kwargs,
    )
    ...
```

### Implementation {:#implementation}

`implementation` accepts a function which contains the logic of the macro.
Implementation functions often create targets by calling one or more rules, and
they are usually private (named with a leading underscore). Conventionally,
they are named the same as their macro, but prefixed with `_` and suffixed with
`_impl`.

Unlike rule implementation functions, which take a single argument (`ctx`) that
contains a reference to the attributes, macro implementation functions accept a
parameter for each argument.

```starlark
# macro/macro.bzl
def _my_macro_impl(name, visibility, deps, create_test):
    cc_library(
        name = name + "_cc_lib",
        deps = deps,
    )

    if create_test:
        cc_test(
            name = name + "_test",
            srcs = ["my_test.cc"],
            deps = deps,
        )
```

If a macro inherits attributes, its implementation function *must* have a
`**kwargs` residual keyword parameter, which can be forwarded to the call that
invokes the inherited rule or submacro. (This helps ensure that your macro won't
be broken if the rule or macro which from which you are inheriting adds a new
attribute.)

### Declaration {:#declaration}

Macros are declared by loading and calling their definition in a `BUILD` file.

```starlark

# pkg/BUILD

my_macro(
    name = "macro_instance",
    deps = ["src.cc"] + select(
        {
            "//config_setting:special": ["special_source.cc"],
            "//conditions:default": [],
        },
    ),
    create_tests = True,
)
```

This would create targets
`//pkg:macro_instance_cc_lib` and`//pkg:macro_instance_test`.

Just like in rule calls, if an attribute value in a macro call is set to `None`,
that attribute is treated as if it was omitted by the macro's caller. For
example, the following two macro calls are equivalent:

```starlark
# pkg/BUILD
my_macro(name = "abc", srcs = ["src.cc"], deps = None)
my_macro(name = "abc", srcs = ["src.cc"])
```

This is generally not useful in `BUILD` files, but is helpful when
programmatically wrapping a macro inside another macro.

## Details {:#usage-details}

### Naming conventions for targets created {:#naming}

The names of any targets or submacros created by a symbolic macro must
either match the macro's `name` parameter or must be prefixed by `name` followed
by `_` (preferred), `.` or `-`. For example, `my_macro(name = "foo")` may only
create files or targets named `foo`, or prefixed by `foo_`, `foo-` or `foo.`,
for example, `foo_bar`.

Targets or files that violate macro naming convention can be declared, but
cannot be built and cannot be used as dependencies.

Non-macro files and targets within the same package as a macro instance should
*not* have names that conflict with potential macro target names, though this
exclusivity is not enforced. We are in the progress of implementing
[lazy evaluation](#laziness) as a performance improvement for Symbolic macros,
which will be impaired in packages that violate the naming schema.

### Restrictions {:#restrictions}

Symbolic macros have some additional restrictions compared to legacy macros.

Symbolic macros

*   must take a `name` argument and a `visibility` argument
*   must have an `implementation` function
*   may not return values
*   may not mutate their arguments
*   may not call `native.existing_rules()` unless they are special `finalizer`
    macros
*   may not call `native.package()`
*   may not call `glob()`
*   may not call `native.environment_group()`
*   must create targets whose names adhere to the [naming schema](#naming)
*   can't refer to input files that weren't declared or passed in as an argument
*   can't refer to private targets of their callers (see
    [visibility and macros](#visibility) for more details).

### Visibility and macros {:#visibility}

The [visibility](/concepts/visibility) system helps protect the implementation
details of both (symbolic) macros and their callers.

By default, targets created in a symbolic macro are visible within the macro
itself, but not necessarily to the macro's caller. The macro can "export" a
target as a public API by forwarding the value of its own `visibility`
attribute, as in `some_rule(..., visibility = visibility)`.

The key ideas of macro visibility are:

1. Visibility is checked based on what macro declared the target, not what
   package called the macro.

   * In other words, being in the same package does not by itself make one
     target visible to another. This protects the macro's internal targets
     from becoming dependencies of other macros or top-level targets in the
     package.

1. All `visibility` attributes, on both rules and macros, automatically
   include the place where the rule or macro was called.

   * Thus, a target is unconditionally visible to other targets declared in the
     same macro (or the `BUILD` file, if not in a macro).

In practice, this means that when a macro declares a target without setting its
`visibility`, the target defaults to being internal to the macro. (The package's
[default visibility](/reference/be/functions#package.default_visibility) does
not apply within a macro.) Exporting the target means that the target is visible
to whatever the macro's caller specified in the macro's `visibility` attribute,
plus the package of the macro's caller itself, as well as the macro's own code.
Another way of thinking of it is that the visibility of a macro determines who
(aside from the macro itself) can see the macro's exported targets.

```starlark
# tool/BUILD
...
some_rule(
    name = "some_tool",
    visibility = ["//macro:__pkg__"],
)
```

```starlark
# macro/macro.bzl

def _impl(name, visibility):
    cc_library(
        name = name + "_helper",
        ...
        # No visibility passed in. Same as passing `visibility = None` or
        # `visibility = ["//visibility:private"]`. Visible to the //macro
        # package only.
    )
    cc_binary(
        name = name + "_exported",
        deps = [
            # Allowed because we're also in //macro. (Targets in any other
            # instance of this macro, or any other macro in //macro, can see it
            # too.)
            name + "_helper",
            # Allowed by some_tool's visibility, regardless of what BUILD file
            # we're called from.
            "//tool:some_tool",
        ],
        ...
        visibility = visibility,
    )

my_macro = macro(implementation = _impl, ...)
```

```starlark
# pkg/BUILD
load("//macro:macro.bzl", "my_macro")
...

my_macro(
    name = "foo",
    ...
)

some_rule(
    ...
    deps = [
        # Allowed, its visibility is ["//pkg:__pkg__", "//macro:__pkg__"].
        ":foo_exported",
        # Disallowed, its visibility is ["//macro:__pkg__"] and
        # we are not in //macro.
        ":foo_helper",
    ]
)
```

If `my_macro` were called with `visibility = ["//other_pkg:__pkg__"]`, or if
the `//pkg` package had set its `default_visibility` to that value, then
`//pkg:foo_exported` could also be used within `//other_pkg/BUILD` or within a
macro defined in `//other_pkg:defs.bzl`, but `//pkg:foo_helper` would remain
protected.

A macro can declare that a target is visible to a friend package by passing
`visibility = ["//some_friend:__pkg__"]` (for an internal target) or
`visibility = visibility + ["//some_friend:__pkg__"]` (for an exported one).
Note that it is an antipattern for a macro to declare a target with public
visibility (`visibility = ["//visibility:public"]`). This is because it makes
the target unconditionally visible to every package, even if the caller
specified a more restricted visibility.

All visibility checking is done with respect to the innermost currently running
symbolic macro. However, there is a visibility delegation mechanism: If a macro
passes a label as an attribute value to an inner macro, any usages of the label
in the inner macro are checked with respect to the outer macro. See the
[visibility page](/concepts/visibility#symbolic-macros) for more details.

Remember that legacy macros are entirely transparent to the visibility system,
and behave as though their location is whatever BUILD file or symbolic macro
they were called from.

#### Finalizers and visibility {:#finalizers-and-visibility}

Targets declared in a rule finalizer, in addition to seeing targets following
the usual symbolic macro visibility rules, can *also* see all targets which are
visible to the finalizer target's package.

This means that if you migrate a `native.existing_rules()`-based legacy macro to
a finalizer, the targets declared by the finalizer will still be able to see
their old dependencies.

However, note that it's possible to declare a target in a symbolic macro such
that a finalizer's targets cannot see it under the visibility system – even
though the finalizer can *introspect* its attributes using
`native.existing_rules()`.

### Selects {:#selects}

If an attribute is `configurable` (the default) and its value is not `None`,
then the macro implementation function will see the attribute value as wrapped
in a trivial `select`. This makes it easier for the macro author to catch bugs
where they did not anticipate that the attribute value could be a `select`.

For example, consider the following macro:

```starlark
my_macro = macro(
    attrs = {"deps": attr.label_list()},  # configurable unless specified otherwise
    implementation = _my_macro_impl,
)
```

If `my_macro` is invoked with `deps = ["//a"]`, that will cause `_my_macro_impl`
to be invoked with its `deps` parameter set to `select({"//conditions:default":
["//a"]})`. If this causes the implementation function to fail (say, because the
code tried to index into the value as in `deps[0]`, which is not allowed for
`select`s), the macro author can then make a choice: either they can rewrite
their macro to only use operations compatible with `select`, or they can mark
the attribute as nonconfigurable (`attr.label_list(configurable = False)`). The
latter ensures that users are not permitted to pass a `select` value in.

Rule targets reverse this transformation, and store trivial `select`s as their
unconditional values; in the above example, if `_my_macro_impl` declares a rule
target `my_rule(..., deps = deps)`, that rule target's `deps` will be stored as
`["//a"]`. This ensures that `select`-wrapping does not cause trivial `select`
values to be stored in all targets instantiated by macros.

If the value of a configurable attribute is `None`, it does not get wrapped in a
`select`. This ensures that tests like `my_attr == None` still work, and that
when the attribute is forwarded to a rule with a computed default, the rule
behaves properly (that is, as if the attribute were not passed in at all). It is
not always possible for an attribute to take on a `None` value, but it can
happen for the `attr.label()` type, and for any inherited non-mandatory
attribute.

## Finalizers {:#finalizers}

A rule finalizer is a special symbolic macro which – regardless of its lexical
position in a BUILD file – is evaluated in the final stage of loading a package,
after all non-finalizer targets have been defined. Unlike ordinary symbolic
macros, a finalizer can call `native.existing_rules()`, where it behaves
slightly differently than in legacy macros: it only returns the set of
non-finalizer rule targets. The finalizer may assert on the state of that set or
define new targets.

To declare a finalizer, call `macro()` with `finalizer = True`:

```starlark
def _my_finalizer_impl(name, visibility, tags_filter):
    for r in native.existing_rules().values():
        for tag in r.get("tags", []):
            if tag in tags_filter:
                my_test(
                    name = name + "_" + r["name"] + "_finalizer_test",
                    deps = [r["name"]],
                    data = r["srcs"],
                    ...
                )
                continue

my_finalizer = macro(
    attrs = {"tags_filter": attr.string_list(configurable = False)},
    implementation = _impl,
    finalizer = True,
)
```

## Laziness {:#laziness}

IMPORTANT: We are in the process of implementing lazy macro expansion and
evaluation. This feature is not available yet.

Currently, all macros are evaluated as soon as the BUILD file is loaded, which
can negatively impact performance for targets in packages that also have costly
unrelated macros. In the future, non-finalizer symbolic macros will only be
evaluated if they're required for the build. The prefix naming schema helps
Bazel determine which macro to expand given a requested target.

## Migration troubleshooting {:#troubleshooting}

Here are some common migration headaches and how to fix them.

*   Legacy macro calls `glob()`

Move the `glob()` call to your BUILD file (or to a legacy macro called from the
BUILD file), and pass the `glob()` value to the symbolic macro using a
label-list attribute:

```starlark
# BUILD file
my_macro(
    ...,
    deps = glob(...),
)
```

*   Legacy macro has a parameter that isn't a valid starlark `attr` type.

Pull as much logic as possible into a nested symbolic macro, but keep the
top level macro a legacy macro.

*  Legacy macro calls a rule that creates a target that breaks the naming schema

That's okay, just don't depend on the "offending" target. The naming check will
be quietly ignored.



Project: /_project.yaml
Book: /_book.yaml

# Depsets

{% include "_buttons.html" %}

[Depsets](/rules/lib/builtins/depset) are a specialized data structure for efficiently
collecting data across a target’s transitive dependencies. They are an essential
element of rule processing.

The defining feature of depset is its time- and space-efficient union operation.
The depset constructor accepts a list of elements ("direct") and a list of other
depsets ("transitive"), and returns a depset representing a set containing all the
direct elements and the union of all the transitive sets. Conceptually, the
constructor creates a new graph node that has the direct and transitive nodes
as its successors. Depsets have a well-defined ordering semantics, based on
traversal of this graph.

Example uses of depsets include:

*   Storing the paths of all object files for a program’s libraries, which can
    then be passed to a linker action through a provider.

*   For an interpreted language, storing the transitive source files that are
    included in an executable's runfiles.

## Description and operations

Conceptually, a depset is a directed acyclic graph (DAG) that typically looks
similar to the target graph. It is constructed from the leaves up to the root.
Each target in a dependency chain can add its own contents on top of the
previous without having to read or copy them.

Each node in the DAG holds a list of direct elements and a list of child nodes.
The contents of the depset are the transitive elements, such as the direct elements
of all the nodes. A new depset can be created using the
[depset](/rules/lib/globals/bzl#depset) constructor: it accepts a list of direct
elements and another list of child nodes.

```python
s = depset(["a", "b", "c"])
t = depset(["d", "e"], transitive = [s])

print(s)    # depset(["a", "b", "c"])
print(t)    # depset(["d", "e", "a", "b", "c"])
```

To retrieve the contents of a depset, use the
[to_list()](/rules/lib/builtins/depset#to_list) method. It returns a list of all transitive
elements, not including duplicates. There is no way to directly inspect the
precise structure of the DAG, although this structure does affect the order in
which the elements are returned.

```python
s = depset(["a", "b", "c"])

print("c" in s.to_list())              # True
print(s.to_list() == ["a", "b", "c"])  # True
```

The allowed items in a depset are restricted, just as the allowed keys in
dictionaries are restricted. In particular, depset contents may not be mutable.

Depsets use reference equality: a depset is equal to itself, but unequal to any
other depset, even if they have the same contents and same internal structure.

```python
s = depset(["a", "b", "c"])
t = s
print(s == t)  # True

t = depset(["a", "b", "c"])
print(s == t)  # False

d = {}
d[s] = None
d[t] = None
print(len(d))  # 2
```

To compare depsets by their contents, convert them to sorted lists.

```python
s = depset(["a", "b", "c"])
t = depset(["c", "b", "a"])
print(sorted(s.to_list()) == sorted(t.to_list()))  # True
```

There is no ability to remove elements from a depset. If this is needed, you
must read out the entire contents of the depset, filter the elements you want to
remove, and reconstruct a new depset. This is not particularly efficient.

```python
s = depset(["a", "b", "c"])
t = depset(["b", "c"])

# Compute set difference s - t. Precompute t.to_list() so it's not done
# in a loop, and convert it to a dictionary for fast membership tests.
t_items = {e: None for e in t.to_list()}
diff_items = [x for x in s.to_list() if x not in t_items]
# Convert back to depset if it's still going to be used for union operations.
s = depset(diff_items)
print(s)  # depset(["a"])
```

### Order

The `to_list` operation performs a traversal over the DAG. The kind of traversal
depends on the *order* that was specified at the time the depset was
constructed. It is useful for Bazel to support multiple orders because sometimes
tools care about the order of their inputs. For example, a linker action may
need to ensure that if `B` depends on `A`, then `A.o` comes before `B.o` on the
linker’s command line. Other tools might have the opposite requirement.

Three traversal orders are supported: `postorder`, `preorder`, and
`topological`. The first two work exactly like [tree
traversals](https://en.wikipedia.org/wiki/Tree_traversal#Depth-first_search)
except that they operate on DAGs and skip already visited nodes. The third order
works as a topological sort from root to leaves, essentially the same as
preorder except that shared children are listed only after all of their parents.
Preorder and postorder operate as left-to-right traversals, but note that within
each node direct elements have no order relative to children. For topological
order, there is no left-to-right guarantee, and even the
all-parents-before-child guarantee does not apply in the case that there are
duplicate elements in different nodes of the DAG.

```python
# This demonstrates different traversal orders.

def create(order):
  cd = depset(["c", "d"], order = order)
  gh = depset(["g", "h"], order = order)
  return depset(["a", "b", "e", "f"], transitive = [cd, gh], order = order)

print(create("postorder").to_list())  # ["c", "d", "g", "h", "a", "b", "e", "f"]
print(create("preorder").to_list())   # ["a", "b", "e", "f", "c", "d", "g", "h"]
```

```python
# This demonstrates different orders on a diamond graph.

def create(order):
  a = depset(["a"], order=order)
  b = depset(["b"], transitive = [a], order = order)
  c = depset(["c"], transitive = [a], order = order)
  d = depset(["d"], transitive = [b, c], order = order)
  return d

print(create("postorder").to_list())    # ["a", "b", "c", "d"]
print(create("preorder").to_list())     # ["d", "b", "a", "c"]
print(create("topological").to_list())  # ["d", "b", "c", "a"]
```

Due to how traversals are implemented, the order must be specified at the time
the depset is created with the constructor’s `order` keyword argument. If this
argument is omitted, the depset has the special `default` order, in which case
there are no guarantees about the order of any of its elements (except that it
is deterministic).

## Full example

This example is available at
[https://github.com/bazelbuild/examples/tree/main/rules/depsets](https://github.com/bazelbuild/examples/tree/main/rules/depsets).

Suppose there is a hypothetical interpreted language Foo. In order to build
each `foo_binary` you need to know all the `*.foo` files that it directly or
indirectly depends on.

```python
# //depsets:BUILD

load(":foo.bzl", "foo_library", "foo_binary")

# Our hypothetical Foo compiler.
py_binary(
    name = "foocc",
    srcs = ["foocc.py"],
)

foo_library(
    name = "a",
    srcs = ["a.foo", "a_impl.foo"],
)

foo_library(
    name = "b",
    srcs = ["b.foo", "b_impl.foo"],
    deps = [":a"],
)

foo_library(
    name = "c",
    srcs = ["c.foo", "c_impl.foo"],
    deps = [":a"],
)

foo_binary(
    name = "d",
    srcs = ["d.foo"],
    deps = [":b", ":c"],
)
```

```python
# //depsets:foocc.py

# "Foo compiler" that just concatenates its inputs to form its output.
import sys

if __name__ == "__main__":
  assert len(sys.argv) >= 1
  output = open(sys.argv[1], "wt")
  for path in sys.argv[2:]:
    input = open(path, "rt")
    output.write(input.read())
```

Here, the transitive sources of the binary `d` are all of the `*.foo` files in
the `srcs` fields of `a`, `b`, `c`, and `d`. In order for the `foo_binary`
target to know about any file besides `d.foo`, the `foo_library` targets need to
pass them along in a provider. Each library receives the providers from its own
dependencies, adds its own immediate sources, and passes on a new provider with
the augmented contents. The `foo_binary` rule does the same, except that instead
of returning a provider, it uses the complete list of sources to construct a
command line for an action.

Here’s a complete implementation of the `foo_library` and `foo_binary` rules.

```python
# //depsets/foo.bzl

# A provider with one field, transitive_sources.
FooFiles = provider(fields = ["transitive_sources"])

def get_transitive_srcs(srcs, deps):
  """Obtain the source files for a target and its transitive dependencies.

  Args:
    srcs: a list of source files
    deps: a list of targets that are direct dependencies
  Returns:
    a collection of the transitive sources
  """
  return depset(
        srcs,
        transitive = [dep[FooFiles].transitive_sources for dep in deps])

def _foo_library_impl(ctx):
  trans_srcs = get_transitive_srcs(ctx.files.srcs, ctx.attr.deps)
  return [FooFiles(transitive_sources=trans_srcs)]

foo_library = rule(
    implementation = _foo_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files=True),
        "deps": attr.label_list(),
    },
)

def _foo_binary_impl(ctx):
  foocc = ctx.executable._foocc
  out = ctx.outputs.out
  trans_srcs = get_transitive_srcs(ctx.files.srcs, ctx.attr.deps)
  srcs_list = trans_srcs.to_list()
  ctx.actions.run(executable = foocc,
                  arguments = [out.path] + [src.path for src in srcs_list],
                  inputs = srcs_list + [foocc],
                  outputs = [out])

foo_binary = rule(
    implementation = _foo_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files=True),
        "deps": attr.label_list(),
        "_foocc": attr.label(default=Label("//depsets:foocc"),
                             allow_files=True, executable=True, cfg="host")
    },
    outputs = {"out": "%{name}.out"},
)
```

You can test this by copying these files into a fresh package, renaming the
labels appropriately, creating the source `*.foo` files with dummy content, and
building the `d` target.


## Performance

To see the motivation for using depsets, consider what would happen if
`get_transitive_srcs()` collected its sources in a list.

```python
def get_transitive_srcs(srcs, deps):
  trans_srcs = []
  for dep in deps:
    trans_srcs += dep[FooFiles].transitive_sources
  trans_srcs += srcs
  return trans_srcs
```

This does not take into account duplicates, so the source files for `a`
will appear twice on the command line and twice in the contents of the output
file.

An alternative is using a general set, which can be simulated by a
dictionary where the keys are the elements and all the keys map to `True`.

```python
def get_transitive_srcs(srcs, deps):
  trans_srcs = {}
  for dep in deps:
    for file in dep[FooFiles].transitive_sources:
      trans_srcs[file] = True
  for file in srcs:
    trans_srcs[file] = True
  return trans_srcs
```

This gets rid of the duplicates, but it makes the order of the command line
arguments (and therefore the contents of the files) unspecified, although still
deterministic.

Moreover, both approaches are asymptotically worse than the depset-based
approach. Consider the case where there is a long chain of dependencies on
Foo libraries. Processing every rule requires copying all of the transitive
sources that came before it into a new data structure. This means that the
time and space cost for analyzing an individual library or binary target
is proportional to its own height in the chain. For a chain of length n,
foolib_1 ← foolib_2 ← … ← foolib_n, the overall cost is effectively O(n^2).

Generally speaking, depsets should be used whenever you are accumulating
information through your transitive dependencies. This helps ensure that
your build scales well as your target graph grows deeper.

Finally, it’s important to not retrieve the contents of the depset
unnecessarily in rule implementations. One call to `to_list()`
at the end in a binary rule is fine, since the overall cost is just O(n). It’s
when many non-terminal targets try to call `to_list()` that quadratic behavior
occurs.

For more information about using depsets efficiently, see the [performance](/rules/performance) page.

## API Reference

Please see [here](/rules/lib/builtins/depset) for more details.



Project: /_project.yaml
Book: /_book.yaml

# Automatic Execution Groups (AEGs)

{% include "_buttons.html" %}

Automatic execution groups select an [execution platform][exec_platform]
for each toolchain type. In other words, one target can have multiple
execution platforms without defining execution groups.

## Quick summary {:#quick-summary}

Automatic execution groups are closely connected to toolchains. If you are using
toolchains, you need to set them on the affected actions (actions which use an
executable or a tool from a toolchain) by adding `toolchain` parameter. For
example:

```python
ctx.actions.run(
    ...,
    executable = ctx.toolchain['@bazel_tools//tools/jdk:toolchain_type'].tool,
    ...,
    toolchain = '@bazel_tools//tools/jdk:toolchain_type',
)
```
If the action does not use a tool or executable from a toolchain, and Blaze
doesn't detect that ([the error](#first-error-message) is raised), you can set
`toolchain = None`.

If you need to use multiple toolchains on a single execution platform (an action
uses executable or tools from two or more toolchains), you need to manually
define [exec_groups][exec_groups] (check
[When should I use a custom exec_group?][multiple_toolchains_exec_groups]
section).

## History {:#history}

Before AEGs, the execution platform was selected on a rule level. For example:

```python
my_rule = rule(
    _impl,
    toolchains = ['//tools:toolchain_type_1', '//tools:toolchain_type_2'],
)
```

Rule `my_rule` registers two toolchain types. This means that the [Toolchain
Resolution](https://bazel.build/extending/toolchains#toolchain-resolution) used
to find an execution platform which supports both toolchain types. The selected
execution platform was used for each registered action inside the rule, unless
specified differently with [exec_groups][exec_groups].
In other words, all actions inside the rule used to have a single execution
platform even if they used tools from different toolchains (execution platform
is selected for each target). This resulted in failures when there was no
execution platform supporting all toolchains.

## Current state {:#current-state}

With AEGs, the execution platform is selected for each toolchain type. The
implementation function of the earlier example, `my_rule`, would look like:

```python
def _impl(ctx):
    ctx.actions.run(
      mnemonic = "First action",
      executable = ctx.toolchain['//tools:toolchain_type_1'].tool,
      toolchain = '//tools:toolchain_type_1',
    )

    ctx.actions.run(
      mnemonic = "Second action",
      executable = ctx.toolchain['//tools:toolchain_type_2'].tool,
      toolchain = '//tools:toolchain_type_2',
    )
```

This rule creates two actions, the `First action` which uses executable from a
`//tools:toolchain_type_1` and the `Second action` which uses executable from a
`//tools:toolchain_type_2`. Before AEGs, both of these actions would be executed
on a single execution platform which supports both toolchain types. With AEGs,
by adding the `toolchain` parameter inside the actions, each action executes on
the execution platform that provides the toolchain. The actions may be executed
on different execution platforms.

The same is effective with [ctx.actions.run_shell][run_shell] where `toolchain`
parameter should be added when `tools` are from a toolchain.

## Difference between custom exec groups and automatic exec groups {:#difference-custom}

As the name suggests, AEGs are exec groups created automatically for each
toolchain type registered on a rule. There is no need to manually specify them,
unlike the "classic" exec groups.

### When should I use a custom exec_group? {:#when-should-use-exec-groups}

Custom exec_groups are needed only in case where multiple toolchains need to
execute on a single execution platform. In all other cases there's no need to
define custom exec_groups. For example:

```python
def _impl(ctx):
    ctx.actions.run(
      ...,
      executable = ctx.toolchain['//tools:toolchain_type_1'].tool,
      tools = [ctx.toolchain['//tools:toolchain_type_2'].tool],
      exec_group = 'two_toolchains',
    )
```

```python
my_rule = rule(
    _impl,
    exec_groups = {
        "two_toolchains": exec_group(
            toolchains = ['//tools:toolchain_type_1', '//tools:toolchain_type_2'],
        ),
    }
)
```

## Migration of AEGs {:#migration-aegs}

Internally in google3, Blaze is already using AEGs.
Externally for Bazel, migration is in the process. Some rules are already using
this feature (e.g. Java and C++ rules).

### Which Bazel versions support this migration? {:#which-bazel}

AEGs are fully supported from Bazel 7.

### How to enable AEGs? {:#how-enable}

Set `--incompatible_auto_exec_groups` to true. More information about the flag
on [the GitHub issue][github_flag].

### How to enable AEGs inside a particular rule? {:#how-enable-particular-rule}

Set the `_use_auto_exec_groups` attribute on a rule.

```python
my_rule = rule(
    _impl,
    attrs = {
      "_use_auto_exec_groups": attr.bool(default = True),
    }
)
```
This enables AEGs only in `my_rule` and its actions start using the new logic
when selecting the execution platform. Incompatible flag is overridden with this
attribute.

### How to disable AEGs in case of an error? {:#how-disable}

Set `--incompatible_auto_exec_groups` to false to completely disable AEGs in
your project ([flag's GitHub issue][github_flag]), or disable a particular rule
by setting `_use_auto_exec_groups` attribute to `False`
([more details about the attribute](#how-enable-particular-rule)).

### Error messages while migrating to AEGs {:#potential-problems}

#### Couldn't identify if tools are from implicit dependencies or a toolchain. Please set the toolchain parameter. If you're not using a toolchain, set it to 'None'. {:#first-error-message}
  * In this case you get a stack of calls before the error happened and you can
    clearly see which exact action needs the toolchain parameter. Check which
    toolchain is used for the action and set it with the toolchain param. If no
    toolchain is used inside the action for tools or executable, set it to
    `None`.

#### Action declared for non-existent toolchain '[toolchain_type]'.
  * This means that you've set the toolchain parameter on the action but didn't
register it on the rule. Register the toolchain or set `None` inside the action.

## Additional material {:#additional-material}

For more information, check design document:
[Automatic exec groups for toolchains][aegs_design_doc].

[exec_platform]: https://bazel.build/extending/platforms#:~:text=Execution%20%2D%20a%20platform%20on%20which%20build%20tools%20execute%20build%20actions%20to%20produce%20intermediate%20and%20final%20outputs.
[exec_groups]: https://bazel.build/extending/exec-groups
[github_flag]: https://github.com/bazelbuild/bazel/issues/17134
[aegs_design_doc]: https://docs.google.com/document/d/1-rbP_hmKs9D639YWw5F_JyxPxL2bi6dSmmvj_WXak9M/edit#heading=h.5mcn15i0e1ch
[run_shell]: https://bazel.build/rules/lib/builtins/actions#run_shell
[multiple_toolchains_exec_groups]: /extending/auto-exec-groups#when-should-use-exec-groups

Project: /_project.yaml
Book: /_book.yaml

# Extension Overview

{% include "_buttons.html" %}

<!-- [TOC] -->

This page describes how to extend the BUILD language using macros
and rules.

Bazel extensions are files ending in `.bzl`. Use a
[load statement](/concepts/build-files#load) to import a symbol from an extension.

Before learning the more advanced concepts, first:

* Read about the [Starlark language](/rules/language), used in both the
  `BUILD` and `.bzl` files.

* Learn how you can [share variables](/build/share-variables)
  between two `BUILD` files.

## Macros and rules {:#macros-and-rules}

A macro is a function that instantiates rules. Macros come in two flavors:
[symbolic macros](/extending/macros) (new in Bazel 8) and [legacy
macros](/extending/legacy-macros). The two flavors of macros are defined
differently, but behave almost the same from the point of view of a user. A
macro is useful when a `BUILD` file is getting too repetitive or too complex, as
it lets you reuse some code. The function is evaluated as soon as the `BUILD`
file is read. After the evaluation of the `BUILD` file, Bazel has little
information about macros. If your macro generates a `genrule`, Bazel will
behave *almost* as if you declared that `genrule` in the `BUILD` file. (The one
exception is that targets declared in a symbolic macro have [special visibility
semantics](/extending/macros#visibility): a symbolic macro can hide its internal
targets from the rest of the package.)

A [rule](/extending/rules) is more powerful than a macro. It can access Bazel
internals and have full control over what is going on. It may for example pass
information to other rules.

If you want to reuse simple logic, start with a macro; we recommend a symbolic
macro, unless you need to support older Bazel versions. If a macro becomes
complex, it is often a good idea to make it a rule. Support for a new language
is typically done with a rule. Rules are for advanced users, and most users will
never have to write one; they will only load and call existing rules.

## Evaluation model {:#evaluation-model}

A build consists of three phases.

* **Loading phase**. First, load and evaluate all extensions and all `BUILD`
  files that are needed for the build. The execution of the `BUILD` files simply
  instantiates rules (each time a rule is called, it gets added to a graph).
  This is where macros are evaluated.

* **Analysis phase**. The code of the rules is executed (their `implementation`
  function), and actions are instantiated. An action describes how to generate
  a set of outputs from a set of inputs, such as "run gcc on hello.c and get
  hello.o". You must list explicitly which files will be generated before
  executing the actual commands. In other words, the analysis phase takes
  the graph generated by the loading phase and generates an action graph.

* **Execution phase**. Actions are executed, when at least one of their outputs is
  required. If a file is missing or if a command fails to generate one output,
  the build fails. Tests are also run during this phase.

Bazel uses parallelism to read, parse and evaluate the `.bzl` files and `BUILD`
files. A file is read at most once per build and the result of the evaluation is
cached and reused. A file is evaluated only once all its dependencies (`load()`
statements) have been resolved. By design, loading a `.bzl` file has no visible
side-effect, it only defines values and functions.

Bazel tries to be clever: it uses dependency analysis to know which files must
be loaded, which rules must be analyzed, and which actions must be executed. For
example, if a rule generates actions that you don't need for the current build,
they will not be executed.

## Creating extensions

* [Create your first macro](/rules/macro-tutorial) in order to reuse some code.
  Then [learn more about macros](/extending/macros) and [using them to create
  "custom verbs"](/rules/verbs-tutorial).

* [Follow the rules tutorial](/rules/rules-tutorial) to get started with rules.
  Next, you can read more about the [rules concepts](/extending/rules).

The two links below will be very useful when writing your own extensions. Keep
them within reach:

* The [API reference](/rules/lib)

* [Examples](https://github.com/bazelbuild/examples/tree/master/rules)

## Going further

In addition to [macros](/extending/macros) and [rules](/extending/rules), you
may want to write [aspects](/extending/aspects) and [repository
rules](/external/repo).

* Use [Buildifier](https://github.com/bazelbuild/buildtools){: .external}
  consistently to format and lint your code.

* Follow the [`.bzl` style guide](/rules/bzl-style).

* [Test](/rules/testing) your code.

* [Generate documentation](https://skydoc.bazel.build/) to help your users.

* [Optimize the performance](/rules/performance) of your code.

* [Deploy](/rules/deploying) your extensions to other people.


Project: /_project.yaml
Book: /_book.yaml

# Aspects

{% include "_buttons.html" %}

This page explains the basics and benefits of using
[aspects](/rules/lib/globals/bzl#aspect) and provides simple and advanced
examples.

Aspects allow augmenting build dependency graphs with additional information
and actions. Some typical scenarios when aspects can be useful:

*   IDEs that integrate Bazel can use aspects to collect information about the
    project.
*   Code generation tools can leverage aspects to execute on their inputs in
    *target-agnostic* manner. As an example, `BUILD` files can specify a hierarchy
    of [protobuf](https://developers.google.com/protocol-buffers/) library
    definitions, and language-specific rules can use aspects to attach
    actions generating protobuf support code for a particular language.

## Aspect basics

`BUILD` files provide a description of a project’s source code: what source
files are part of the project, what artifacts (_targets_) should be built from
those files, what the dependencies between those files are, etc. Bazel uses
this information to perform a build, that is, it figures out the set of actions
needed to produce the artifacts (such as running compiler or linker) and
executes those actions. Bazel accomplishes this by constructing a _dependency
graph_ between targets and visiting this graph to collect those actions.

Consider the following `BUILD` file:

```python
java_library(name = 'W', ...)
java_library(name = 'Y', deps = [':W'], ...)
java_library(name = 'Z', deps = [':W'], ...)
java_library(name = 'Q', ...)
java_library(name = 'T', deps = [':Q'], ...)
java_library(name = 'X', deps = [':Y',':Z'], runtime_deps = [':T'], ...)
```

This `BUILD` file defines a dependency graph shown in the following figure:

![Build graph](/rules/build-graph.png "Build graph")

**Figure 1.** `BUILD` file dependency graph.

Bazel analyzes this dependency graph by calling an implementation function of
the corresponding [rule](/extending/rules) (in this case "java_library") for every
target in the above example. Rule implementation functions generate actions that
build artifacts, such as `.jar` files, and pass information, such as locations
and names of those artifacts, to the reverse dependencies of those targets in
[providers](/extending/rules#providers).

Aspects are similar to rules in that they have an implementation function that
generates actions and returns providers. However, their power comes from
the way the dependency graph is built for them. An aspect has an implementation
and a list of all attributes it propagates along. Consider an aspect A that
propagates along attributes named "deps". This aspect can be applied to
a target X, yielding an aspect application node A(X). During its application,
aspect A is applied recursively to all targets that X refers to in its "deps"
attribute (all attributes in A's propagation list).

Thus a single act of applying aspect A to a target X yields a "shadow graph" of
the original dependency graph of targets shown in the following figure:

![Build Graph with Aspect](/rules/build-graph-aspects.png "Build graph with aspects")

**Figure 2.** Build graph with aspects.

The only edges that are shadowed are the edges along the attributes in
the propagation set, thus the `runtime_deps` edge is not shadowed in this
example. An aspect implementation function is then invoked on all nodes in
the shadow graph similar to how rule implementations are invoked on the nodes
of the original graph.

## Simple example

This example demonstrates how to recursively print the source files for a
rule and all of its dependencies that have a `deps` attribute. It shows
an aspect implementation, an aspect definition, and how to invoke the aspect
from the Bazel command line.

```python
def _print_aspect_impl(target, ctx):
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the files that make up the sources and
        # print their paths.
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                print(f.path)
    return []

print_aspect = aspect(
    implementation = _print_aspect_impl,
    attr_aspects = ['deps'],
    required_providers = [CcInfo],
)
```

Let's break the example up into its parts and examine each one individually.

### Aspect definition

```python
print_aspect = aspect(
    implementation = _print_aspect_impl,
    attr_aspects = ['deps'],
    required_providers = [CcInfo],
)
```
Aspect definitions are similar to rule definitions, and defined using
the [`aspect`](/rules/lib/globals/bzl#aspect) function.

Just like a rule, an aspect has an implementation function which in this case is
``_print_aspect_impl``.

``attr_aspects`` is a list of rule attributes along which the aspect propagates.
In this case, the aspect will propagate along the ``deps`` attribute of the
rules that it is applied to.

Another common argument for `attr_aspects` is `['*']` which would propagate the
aspect to all attributes of a rule.

``required_providers`` is a list of providers that allows the aspect to limit
its propagation to only the targets whose rules advertise its required
providers. For more details consult
[the documentation of the aspect function](/rules/lib/globals/bzl#aspect).
In this case, the aspect will only apply on targets that declare `CcInfo`
provider.

### Aspect implementation

```python
def _print_aspect_impl(target, ctx):
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the files that make up the sources and
        # print their paths.
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                print(f.path)
    return []
```

Aspect implementation functions are similar to the rule implementation
functions. They return [providers](/extending/rules#providers), can generate
[actions](/extending/rules#actions), and take two arguments:

*  `target`: the [target](/rules/lib/builtins/Target) the aspect is being applied to.
*   `ctx`: [`ctx`](/rules/lib/builtins/ctx) object that can be used to access attributes
    and generate outputs and actions.

The implementation function can access the attributes of the target rule via
[`ctx.rule.attr`](/rules/lib/builtins/ctx#rule). It can examine providers that are
provided by the target to which it is applied (via the `target` argument).

Aspects are required to return a list of providers. In this example, the aspect
does not provide anything, so it returns an empty list.

### Invoking the aspect using the command line

The simplest way to apply an aspect is from the command line using the
[`--aspects`](/reference/command-line-reference#flag--aspects)
argument. Assuming the aspect above were defined in a file named `print.bzl`
this:

```bash
bazel build //MyExample:example --aspects print.bzl%print_aspect
```

would apply the `print_aspect` to the target `example` and all of the
target rules that are accessible recursively via the `deps` attribute.

The `--aspects` flag takes one argument, which is a specification of the aspect
in the format `<extension file label>%<aspect top-level name>`.

## Advanced example

The following example demonstrates using an aspect from a target rule
that counts files in targets, potentially filtering them by extension.
It shows how to use a provider to return values, how to use parameters to pass
an argument into an aspect implementation, and how to invoke an aspect from a rule.

Note: Aspects added in rules' attributes are called *rule-propagated aspects* as
opposed to *command-line aspects* that are specified using the ``--aspects``
flag.

`file_count.bzl` file:

```python
FileCountInfo = provider(
    fields = {
        'count' : 'number of files'
    }
)

def _file_count_aspect_impl(target, ctx):
    count = 0
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the sources counting files
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                if ctx.attr.extension == '*' or ctx.attr.extension == f.extension:
                    count = count + 1
    # Get the counts from our dependencies.
    for dep in ctx.rule.attr.deps:
        count = count + dep[FileCountInfo].count
    return [FileCountInfo(count = count)]

file_count_aspect = aspect(
    implementation = _file_count_aspect_impl,
    attr_aspects = ['deps'],
    attrs = {
        'extension' : attr.string(values = ['*', 'h', 'cc']),
    }
)

def _file_count_rule_impl(ctx):
    for dep in ctx.attr.deps:
        print(dep[FileCountInfo].count)

file_count_rule = rule(
    implementation = _file_count_rule_impl,
    attrs = {
        'deps' : attr.label_list(aspects = [file_count_aspect]),
        'extension' : attr.string(default = '*'),
    },
)
```

`BUILD.bazel` file:

```python
load('//:file_count.bzl', 'file_count_rule')

cc_library(
    name = 'lib',
    srcs = [
        'lib.h',
        'lib.cc',
    ],
)

cc_binary(
    name = 'app',
    srcs = [
        'app.h',
        'app.cc',
        'main.cc',
    ],
    deps = ['lib'],
)

file_count_rule(
    name = 'file_count',
    deps = ['app'],
    extension = 'h',
)
```

### Aspect definition

```python
file_count_aspect = aspect(
    implementation = _file_count_aspect_impl,
    attr_aspects = ['deps'],
    attrs = {
        'extension' : attr.string(values = ['*', 'h', 'cc']),
    }
)
```

This example shows how the aspect propagates through the ``deps`` attribute.

``attrs`` defines a set of attributes for an aspect. Public aspect attributes
define parameters and can only be of types ``bool``, ``int`` or ``string``.
For rule-propagated aspects, ``int`` and ``string`` parameters must have
``values`` specified on them. This example has a parameter called ``extension``
that is allowed to have '``*``', '``h``', or '``cc``' as a value.

For rule-propagated aspects, parameter values are taken from the rule requesting
the aspect, using the attribute of the rule that has the same name and type.
(see the definition of ``file_count_rule``).

For command-line aspects, the parameters values can be passed using
[``--aspects_parameters``](/reference/command-line-reference#flag--aspects_parameters)
flag. The ``values`` restriction of ``int`` and ``string`` parameters may be
omitted.

Aspects are also allowed to have private attributes of types ``label`` or
``label_list``. Private label attributes can be used to specify dependencies on
tools or libraries that are needed for actions generated by aspects. There is not
a private attribute defined in this example, but the following code snippet
demonstrates how you could pass in a tool to an aspect:

```python
...
    attrs = {
        '_protoc' : attr.label(
            default = Label('//tools:protoc'),
            executable = True,
            cfg = "exec"
        )
    }
...
```

### Aspect implementation

```python
FileCountInfo = provider(
    fields = {
        'count' : 'number of files'
    }
)

def _file_count_aspect_impl(target, ctx):
    count = 0
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the sources counting files
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                if ctx.attr.extension == '*' or ctx.attr.extension == f.extension:
                    count = count + 1
    # Get the counts from our dependencies.
    for dep in ctx.rule.attr.deps:
        count = count + dep[FileCountInfo].count
    return [FileCountInfo(count = count)]
```

Just like a rule implementation function, an aspect implementation function
returns a struct of providers that are accessible to its dependencies.

In this example, the ``FileCountInfo`` is defined as a provider that has one
field ``count``. It is best practice to explicitly define the fields of a
provider using the ``fields`` attribute.

The set of providers for an aspect application A(X) is the union of providers
that come from the implementation of a rule for target X and from the
implementation of aspect A. The providers that a rule implementation propagates
are created and frozen before aspects are applied and cannot be modified from an
aspect. It is an error if a target and an aspect that is applied to it each
provide a provider with the same type, with the exceptions of
[`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo)
(which is merged, so long as the
rule and aspect specify different output groups) and
[`InstrumentedFilesInfo`](/rules/lib/providers/InstrumentedFilesInfo)
(which is taken from the aspect). This means that aspect implementations may
never return [`DefaultInfo`](/rules/lib/providers/DefaultInfo).

The parameters and private attributes are passed in the attributes of the
``ctx``. This example references the ``extension`` parameter and determines
what files to count.

For returning providers, the values of attributes along which
the aspect is propagated (from the `attr_aspects` list) are replaced with
the results of an application of the aspect to them. For example, if target
X has Y and Z in its deps, `ctx.rule.attr.deps` for A(X) will be [A(Y), A(Z)].
In this example, ``ctx.rule.attr.deps`` are Target objects that are the
results of applying the aspect to the 'deps' of the original target to which
the aspect has been applied.

In the example, the aspect accesses the ``FileCountInfo`` provider from the
target's dependencies to accumulate the total transitive number of files.

### Invoking the aspect from a rule

```python
def _file_count_rule_impl(ctx):
    for dep in ctx.attr.deps:
        print(dep[FileCountInfo].count)

file_count_rule = rule(
    implementation = _file_count_rule_impl,
    attrs = {
        'deps' : attr.label_list(aspects = [file_count_aspect]),
        'extension' : attr.string(default = '*'),
    },
)
```

The rule implementation demonstrates how to access the ``FileCountInfo``
via the ``ctx.attr.deps``.

The rule definition demonstrates how to define a parameter (``extension``)
and give it a default value (``*``). Note that having a default value that
was not one of '``cc``', '``h``', or '``*``' would be an error due to the
restrictions placed on the parameter in the aspect definition.

### Invoking an aspect through a target rule

```python
load('//:file_count.bzl', 'file_count_rule')

cc_binary(
    name = 'app',
...
)

file_count_rule(
    name = 'file_count',
    deps = ['app'],
    extension = 'h',
)
```

This demonstrates how to pass the ``extension`` parameter into the aspect
via the rule. Since the ``extension`` parameter has a default value in the
rule implementation, ``extension`` would be considered an optional parameter.

When the ``file_count`` target is built, our aspect will be evaluated for
itself, and all of the targets accessible recursively via ``deps``.

## References

* [`aspect` API reference](/rules/lib/globals/bzl#aspect)


Project: /_project.yaml
Book: /_book.yaml

# Configurations

<devsite-mathjax config="TeX-AMS-MML_SVG"></devsite-mathjax>

{% include "_buttons.html" %}

This page covers the benefits and basic usage of Starlark configurations,
Bazel's API for customizing how your project builds. It includes how to define
build settings and provides examples.

This makes it possible to:

*   define custom flags for your project, obsoleting the need for
     [`--define`](/docs/configurable-attributes#custom-keys)
*   write
    [transitions](/rules/lib/builtins/transition#transition) to configure deps in
    different configurations than their parents
    (such as `--compilation_mode=opt` or `--cpu=arm`)
*   bake better defaults into rules (such as automatically build `//my:android_app`
    with a specified SDK)

and more, all completely from .bzl files (no Bazel release required). See the
`bazelbuild/examples` repo for
[examples](https://github.com/bazelbuild/examples/tree/HEAD/configurations){: .external}.

## User-defined build settings {:#user-defined-build-settings}

A build setting is a single piece of
[configuration](/extending/rules#configurations)
information. Think of a configuration as a key/value map. Setting `--cpu=ppc`
and `--copt="-DFoo"` produces a configuration that looks like
`{cpu: ppc, copt: "-DFoo"}`. Each entry is a build setting.

Traditional flags like `cpu` and `copt` are native settings —
their keys are defined and their values are set inside native bazel java code.
Bazel users can only read and write them via the command line
and other APIs maintained natively. Changing native flags, and the APIs
that expose them, requires a bazel release. User-defined build
settings are defined in `.bzl` files (and thus, don't need a bazel release to
register changes). They also can be set via the command line
(if they're designated as `flags`, see more below), but can also be
set via [user-defined transitions](#user-defined-transitions).

### Defining build settings {:#defining-build-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/basic_build_setting){: .external}

#### The `build_setting` `rule()` parameter {:#rule-parameter}

Build settings are rules like any other rule and are differentiated using the
Starlark `rule()` function's `build_setting`
[attribute](/rules/lib/globals/bzl#rule.build_setting).

```python
# example/buildsettings/build_settings.bzl
string_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

The `build_setting` attribute takes a function that designates the type of the
build setting. The type is limited to a set of basic Starlark types like
`bool` and `string`. See the `config` module
[documentation](/rules/lib/toplevel/config)  for details. More complicated typing can be
done in the rule's implementation function. More on this below.

The `config` module's functions takes an optional boolean parameter, `flag`,
which is set to false by default. if `flag` is set to true, the build setting
can be set on the command line by users as well as internally by rule writers
via default values and [transitions](/rules/lib/builtins/transition#transition).
Not all settings should be settable by users. For example, if you as a rule
writer have some debug mode that you'd like to turn on inside test rules,
you don't want to give users the ability to indiscriminately turn on that
feature inside other non-test rules.

#### Using ctx.build_setting_value {:#ctx-build-setting-value}

Like all rules, build setting rules have [implementation functions](/extending/rules#implementation-function).
The basic Starlark-type value of the build settings can be accessed via the
`ctx.build_setting_value` method. This method is only available to
[`ctx`](/rules/lib/builtins/ctx) objects of build setting rules. These implementation
methods can directly forward the build settings value or do additional work on
it, like type checking or more complex struct creation. Here's how you would
implement an `enum`-typed build setting:

```python
# example/buildsettings/build_settings.bzl
TemperatureProvider = provider(fields = ['type'])

temperatures = ["HOT", "LUKEWARM", "ICED"]

def _impl(ctx):
    raw_temperature = ctx.build_setting_value
    if raw_temperature not in temperatures:
        fail(str(ctx.label) + " build setting allowed to take values {"
             + ", ".join(temperatures) + "} but was set to unallowed value "
             + raw_temperature)
    return TemperatureProvider(type = raw_temperature)

temperature = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

Note: if a rule depends on a build setting, it will receive whatever providers
the build setting implementation function returns, like any other dependency.
But all other references to the value of the build setting (such as in transitions)
will see its basic Starlark-typed value, not this post implementation function
value.

#### Defining multi-set string flags {:#multi-set-string-flags}

String settings have an additional `allow_multiple` parameter which allows the
flag to be set multiple times on the command line or in bazelrcs. Their default
value is still set with a string-typed attribute:

```python
# example/buildsettings/build_settings.bzl
allow_multiple_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True, allow_multiple = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "allow_multiple_flag")
allow_multiple_flag(
    name = "roasts",
    build_setting_default = "medium"
)
```

Each setting of the flag is treated as a single value:

```shell
$ bazel build //my/target --//example:roasts=blonde \
    --//example:roasts=medium,dark
```

The above is parsed to `{"//example:roasts": ["blonde", "medium,dark"]}` and
`ctx.build_setting_value` returns the list `["blonde", "medium,dark"]`.

#### Instantiating build settings {:#instantiating-build-settings}

Rules defined with the `build_setting` parameter have an implicit mandatory
`build_setting_default` attribute. This attribute takes on the same type as
declared by the `build_setting` param.

```python
# example/buildsettings/build_settings.bzl
FlavorProvider = provider(fields = ['type'])

def _impl(ctx):
    return FlavorProvider(type = ctx.build_setting_value)

flavor = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "flavor")
flavor(
    name = "favorite_flavor",
    build_setting_default = "APPLE"
)
```

### Predefined settings {:#predefined-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/use_skylib_build_setting){: .external}

The
[Skylib](https://github.com/bazelbuild/bazel-skylib){: .external}
library includes a set of predefined settings you can instantiate without having
to write custom Starlark.

For example, to define a setting that accepts a limited set of string values:

```python
# example/BUILD
load("@bazel_skylib//rules:common_settings.bzl", "string_flag")
string_flag(
    name = "myflag",
    values = ["a", "b", "c"],
    build_setting_default = "a",
)
```

For a complete list, see
[Common build setting rules](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/common_settings.bzl){: .external}.

### Using build settings {:#using-build-settings}

#### Depending on build settings {:#depending-on-build-settings}

If a target would like to read a piece of configuration information, it can
directly depend on the build setting via a regular attribute dependency.

```python
# example/rules.bzl
load("//example/buildsettings:build_settings.bzl", "FlavorProvider")
def _rule_impl(ctx):
    if ctx.attr.flavor[FlavorProvider].type == "ORANGE":
        ...

drink_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "flavor": attr.label()
    }
)
```

```python
# example/BUILD
load("//example:rules.bzl", "drink_rule")
load("//example/buildsettings:build_settings.bzl", "flavor")
flavor(
    name = "favorite_flavor",
    build_setting_default = "APPLE"
)
drink_rule(
    name = "my_drink",
    flavor = ":favorite_flavor",
)
```

Languages may wish to create a canonical set of build settings which all rules
for that language depend on. Though the native concept of `fragments` no longer
exists as a hardcoded object in Starlark configuration world, one way to
translate this concept would be to use sets of common implicit attributes. For
example:

```python
# kotlin/rules.bzl
_KOTLIN_CONFIG = {
    "_compiler": attr.label(default = "//kotlin/config:compiler-flag"),
    "_mode": attr.label(default = "//kotlin/config:mode-flag"),
    ...
}

...

kotlin_library = rule(
    implementation = _rule_impl,
    attrs = dicts.add({
        "library-attr": attr.string()
    }, _KOTLIN_CONFIG)
)

kotlin_binary = rule(
    implementation = _binary_impl,
    attrs = dicts.add({
        "binary-attr": attr.label()
    }, _KOTLIN_CONFIG)

```

#### Using build settings on the command line {:#build-settings-command-line}

Similar to most native flags, you can use the command line to set build settings
[that are marked as flags](#rule-parameter). The build
setting's name is its full target path using `name=value` syntax:

```shell
$ bazel build //my/target --//example:string_flag=some-value # allowed
$ bazel build //my/target --//example:string_flag some-value # not allowed
```

Special boolean syntax is supported:

```shell
$ bazel build //my/target --//example:boolean_flag
$ bazel build //my/target --no//example:boolean_flag
```

#### Using build setting aliases {:#using-build-setting-aliases}

You can set an alias for your build setting target path to make it easier to read
on the command line. Aliases function similarly to native flags and also make use
of the double-dash option syntax.

Set an alias by adding `--flag_alias=ALIAS_NAME=TARGET_PATH`
to your `.bazelrc` . For example, to set an alias to `coffee`:

```shell
# .bazelrc
build --flag_alias=coffee=//experimental/user/starlark_configurations/basic_build_setting:coffee-temp
```

Best Practice: Setting an alias multiple times results in the most recent
one taking precedence. Use unique alias names to avoid unintended parsing results.

To make use of the alias, type it in place of the build setting target path.
With the above example of `coffee` set in the user's `.bazelrc`:

```shell
$ bazel build //my/target --coffee=ICED
```

instead of

```shell
$ bazel build //my/target --//experimental/user/starlark_configurations/basic_build_setting:coffee-temp=ICED
```
Best Practice: While it possible to set aliases on the command line, leaving them
in a `.bazelrc` reduces command line clutter.

### Label-typed build settings {:#label-typed-build-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/label_typed_build_setting){: .external}

Unlike other build settings, label-typed settings cannot be defined using the
`build_setting` rule parameter. Instead, bazel has two built-in rules:
`label_flag` and `label_setting`. These rules forward the providers of the
actual target to which the build setting is set. `label_flag` and
`label_setting` can be read/written by transitions and `label_flag` can be set
by the user like other `build_setting` rules can. Their only difference is they
can't customely defined.

Label-typed settings will eventually replace the functionality of late-bound
defaults. Late-bound default attributes are Label-typed attributes whose
final values can be affected by configuration. In Starlark, this will replace
the [`configuration_field`](/rules/lib/globals/bzl#configuration_field)
 API.

```python
# example/rules.bzl
MyProvider = provider(fields = ["my_field"])

def _dep_impl(ctx):
    return MyProvider(my_field = "yeehaw")

dep_rule = rule(
    implementation = _dep_impl
)

def _parent_impl(ctx):
    if ctx.attr.my_field_provider[MyProvider].my_field == "cowabunga":
        ...

parent_rule = rule(
    implementation = _parent_impl,
    attrs = { "my_field_provider": attr.label() }
)

```

```python
# example/BUILD
load("//example:rules.bzl", "dep_rule", "parent_rule")

dep_rule(name = "dep")

parent_rule(name = "parent", my_field_provider = ":my_field_provider")

label_flag(
    name = "my_field_provider",
    build_setting_default = ":dep"
)
```

### Build settings and select() {:#build-settings-and-select}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/select_on_build_setting){: .external}

Users can configure attributes on build settings by using
 [`select()`](/reference/be/functions#select). Build setting targets can be passed to the `flag_values` attribute of
`config_setting`. The value to match to the configuration is passed as a
`String` then parsed to the type of the build setting for matching.

```python
config_setting(
    name = "my_config",
    flag_values = {
        "//example:favorite_flavor": "MANGO"
    }
)
```

## User-defined transitions {:#user-defined-transitions}

A configuration
[transition](/rules/lib/builtins/transition#transition)
maps the transformation from one configured target to another within the
build graph.

Important: Transitions have [memory and performance impact](#memory-performance-considerations).

### Defining {:#defining}

Transitions define configuration changes between rules. For example, a request
like "compile my dependency for a different CPU than its parent" is handled by a
transition.

Formally, a transition is a function from an input configuration to one or more
output configurations. Most transitions are 1:1 such as "override the input
configuration with `--cpu=ppc`". 1:2+ transitions can also exist but come
with special restrictions.

In Starlark, transitions are defined much like rules, with a defining
`transition()`
[function](/rules/lib/builtins/transition#transition)
and an implementation function.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {"//example:favorite_flavor" : "MINT"}

hot_chocolate_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)
```
The `transition()` function takes in an implementation function, a set of
build settings to read(`inputs`), and a set of build settings to write
(`outputs`). The implementation function has two parameters, `settings` and
`attr`. `settings` is a dictionary {`String`:`Object`} of all settings declared
in the `inputs` parameter to `transition()`.

`attr` is a dictionary of attributes and values of the rule to which the
transition is attached. When attached as an
[outgoing edge transition](#outgoing-edge-transitions), the values of these
attributes are all configured post-select() resolution. When attached as
an [incoming edge transition](#incoming-edge-transitions), `attr` does not
include any attributes that use a selector to resolve their value. If an
incoming edge transition on `--foo` reads attribute `bar` and then also
selects on `--foo` to set attribute `bar`, then there's a chance for the
incoming edge transition to read the wrong value of `bar` in the transition.

Note: Since transitions are attached to rule definitions and `select()`s are
attached to rule instantiations (such as targets), errors related to `select()`s on
read attributes will pop up when users create targets rather than when rules are
written. It may be worth taking extra care to communicate to rule users which
attributes they should be wary of selecting on or taking other precautions.

The implementation function must return a dictionary (or list of
dictionaries, in the case of
transitions with multiple output configurations)
of new build settings values to apply. The returned dictionary keyset(s) must
contain exactly the set of build settings passed to the `outputs`
parameter of the transition function. This is true even if a build setting is
not actually changed over the course of the transition - its original value must
be explicitly passed through in the returned dictionary.

### Defining 1:2+ transitions {:#defining-1-2-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/multi_arch_binary){: .external}

[Outgoing edge transition](#outgoing-edge-transitions) can map a single input
configuration to two or more output configurations. This is useful for defining
rules that bundle multi-architecture code.

1:2+ transitions are defined by returning a list of dictionaries in the
transition implementation function.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return [
        {"//example:favorite_flavor" : "LATTE"},
        {"//example:favorite_flavor" : "MOCHA"},
    ]

coffee_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)
```
They can also set custom keys that the rule implementation function can use to
read individual dependencies:

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {
        "Apple deps": {"//command_line_option:cpu": "ppc"},
        "Linux deps": {"//command_line_option:cpu": "x86"},
    }

multi_arch_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
)
```

### Attaching transitions {:#attaching-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/attaching_transitions_to_rules){: .external}

Transitions can be attached in two places: incoming edges and outgoing edges.
Effectively this means rules can transition their own configuration (incoming
edge transition) and transition their dependencies' configurations (outgoing
edge transition).

NOTE: There is currently no way to attach Starlark transitions to native rules.
If you need to do this, contact
bazel-discuss@googlegroups.com
for help with figuring out workarounds.

### Incoming edge transitions {:#incoming-edge-transitions}

Incoming edge transitions are activated by attaching a `transition` object
(created by `transition()`) to `rule()`'s `cfg` parameter:

```python
# example/rules.bzl
load("example/transitions:transitions.bzl", "hot_chocolate_transition")
drink_rule = rule(
    implementation = _impl,
    cfg = hot_chocolate_transition,
    ...
```

Incoming edge transitions must be 1:1 transitions.

### Outgoing edge transitions {:#outgoing-edge-transitions}

Outgoing edge transitions are activated by attaching a `transition` object
(created by `transition()`) to an attribute's `cfg` parameter:

```python
# example/rules.bzl
load("example/transitions:transitions.bzl", "coffee_transition")
drink_rule = rule(
    implementation = _impl,
    attrs = { "dep": attr.label(cfg = coffee_transition)}
    ...
```
Outgoing edge transitions can be 1:1 or 1:2+.

See [Accessing attributes with transitions](#accessing-attributes-with-transitions)
for how to read these keys.

### Transitions on native options {:#transitions-native-options}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/transition_on_native_flag){: .external}

Starlark transitions can also declare reads and writes on native build
configuration options via a special prefix to the option name.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {"//command_line_option:cpu": "k8"}

cpu_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
```

#### Unsupported native options {:#unsupported-native-options}

Bazel doesn't support transitioning on `--define` with
`"//command_line_option:define"`. Instead, use a custom
[build setting](#user-defined-build-settings). In general, new usages of
`--define` are discouraged in favor of build settings.

Bazel doesn't support transitioning on `--config`. This is because `--config` is
an "expansion" flag that expands to other flags.

Crucially, `--config` may include flags that don't affect build configuration,
such as
[`--spawn_strategy`](/docs/user-manual#spawn-strategy)
. Bazel, by design, can't bind such flags to individual targets. This means
there's no coherent way to apply them in transitions.

As a workaround, you can explicitly itemize the flags that *are* part of
the configuration in your transition. This requires maintaining the `--config`'s
expansion in two places, which is a known UI blemish.

### Transitions on allow multiple build settings {:#transitions-multiple-build-settings}

When setting build settings that
[allow multiple values](#defining-multi-set-string-flags), the value of the
setting must be set with a list.

```python
# example/buildsettings/build_settings.bzl
string_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True, allow_multiple = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "string_flag")
string_flag(name = "roasts", build_setting_default = "medium")
```

```python
# example/transitions/rules.bzl
def _transition_impl(settings, attr):
    # Using a value of just "dark" here will throw an error
    return {"//example:roasts" : ["dark"]},

coffee_transition = transition(
    implementation = _transition_impl,
    inputs = [],
    outputs = ["//example:roasts"]
)
```

### No-op transitions {:#no-op-transitions}

If a transition returns `{}`, `[]`, or `None`, this is shorthand for keeping all
settings at their original values. This can be more convenient than explicitly
setting each output to itself.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (attr)
    if settings["//example:already_chosen"] is True:
      return {}
    return {
      "//example:favorite_flavor": "dark chocolate",
      "//example:include_marshmallows": "yes",
      "//example:desired_temperature": "38C",
    }

hot_chocolate_transition = transition(
    implementation = _impl,
    inputs = ["//example:already_chosen"],
    outputs = [
        "//example:favorite_flavor",
        "//example:include_marshmallows",
        "//example:desired_temperature",
    ]
)
```

### Accessing attributes with transitions {:#accessing-attributes-with-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/read_attr_in_transition){: .external}

When [attaching a transition to an outgoing edge](#outgoing-edge-transitions)
(regardless of whether the transition is a 1:1 or 1:2+ transition), `ctx.attr` is forced to be a list
if it isn't already. The order of elements in this list is unspecified.


```python
# example/transitions/rules.bzl
def _transition_impl(settings, attr):
    return {"//example:favorite_flavor" : "LATTE"},

coffee_transition = transition(
    implementation = _transition_impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)

def _rule_impl(ctx):
    # Note: List access even though "dep" is not declared as list
    transitioned_dep = ctx.attr.dep[0]

    # Note: Access doesn't change, other_deps was already a list
    for other_dep in ctx.attr.other_deps:
      # ...


coffee_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "dep": attr.label(cfg = coffee_transition)
        "other_deps": attr.label_list(cfg = coffee_transition)
    })
```

If the transition is `1:2+` and sets custom keys, `ctx.split_attr` can be used
to read individual deps for each key:

```python
# example/transitions/rules.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {
        "Apple deps": {"//command_line_option:cpu": "ppc"},
        "Linux deps": {"//command_line_option:cpu": "x86"},
    }

multi_arch_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
)

def _rule_impl(ctx):
    apple_dep = ctx.split_attr.dep["Apple deps"]
    linux_dep = ctx.split_attr.dep["Linux deps"]
    # ctx.attr has a list of all deps for all keys. Order is not guaranteed.
    all_deps = ctx.attr.dep

multi_arch_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "dep": attr.label(cfg = multi_arch_transition)
    })
```

See [complete example](https://github.com/bazelbuild/examples/tree/main/configurations/multi_arch_binary)
here.

## Integration with platforms and toolchains {:#integration-platforms-toolchains}

Many native flags today, like `--cpu` and `--crosstool_top` are related to
toolchain resolution. In the future, explicit transitions on these types of
flags will likely be replaced by transitioning on the
[target platform](/extending/platforms).

## Memory and performance considerations {:#memory-performance-considerations}

Adding transitions, and therefore new configurations, to your build comes at a
cost: larger build graphs, less comprehensible build graphs, and slower
builds. It's worth considering these costs when considering
using transitions in your build rules. Below is an example of how a transition
might create exponential growth of your build graph.

### Badly behaved builds: a case study {:#badly-behaved-builds}

![Scalability graph](/rules/scalability-graph.png "Scalability graph")

**Figure 1.** Scalability graph showing a top level target and its dependencies.

This graph shows a top level target, `//pkg:app`, which depends on two targets, a
`//pkg:1_0` and `//pkg:1_1`. Both these targets depend on two targets, `//pkg:2_0` and
`//pkg:2_1`. Both these targets depend on two targets, `//pkg:3_0` and `//pkg:3_1`.
This continues on until `//pkg:n_0` and `//pkg:n_1`, which both depend on a single
target, `//pkg:dep`.

Building `//pkg:app` requires \\(2n+2\\) targets:

* `//pkg:app`
* `//pkg:dep`
* `//pkg:i_0` and `//pkg:i_1` for \\(i\\) in \\([1..n]\\)

Imagine you [implement](#user-defined-build-settings) a flag
`--//foo:owner=<STRING>` and `//pkg:i_b` applies

    depConfig = myConfig + depConfig.owner="$(myConfig.owner)$(b)"

In other words, `//pkg:i_b` appends `b` to the old value of `--owner` for all
its deps.

This produces the following [configured targets](/reference/glossary#configured-target):

```
//pkg:app                              //foo:owner=""
//pkg:1_0                              //foo:owner=""
//pkg:1_1                              //foo:owner=""
//pkg:2_0 (via //pkg:1_0)              //foo:owner="0"
//pkg:2_0 (via //pkg:1_1)              //foo:owner="1"
//pkg:2_1 (via //pkg:1_0)              //foo:owner="0"
//pkg:2_1 (via //pkg:1_1)              //foo:owner="1"
//pkg:3_0 (via //pkg:1_0 → //pkg:2_0)  //foo:owner="00"
//pkg:3_0 (via //pkg:1_0 → //pkg:2_1)  //foo:owner="01"
//pkg:3_0 (via //pkg:1_1 → //pkg:2_0)  //foo:owner="10"
//pkg:3_0 (via //pkg:1_1 → //pkg:2_1)  //foo:owner="11"
...
```

`//pkg:dep` produces \\(2^n\\) configured targets: `config.owner=`
"\\(b_0b_1...b_n\\)" for all \\(b_i\\) in \\(\{0,1\}\\).

This makes the build graph exponentially larger than the target graph, with
corresponding memory and performance consequences.

TODO: Add strategies for measurement and mitigation of these issues.

## Further reading {:#further-reading}

For more details on modifying build configurations, see:

 * [Starlark Build Configuration](https://docs.google.com/document/d/1vc8v-kXjvgZOdQdnxPTaV0rrLxtP2XwnD2tAZlYJOqw/edit?usp=sharing){: .external}
 * [Bazel Configurability Roadmap](https://bazel.build/community/roadmaps-configurability){: .external}
 * Full [set](https://github.com/bazelbuild/examples/tree/HEAD/configurations){: .external} of end to end examples


Project: /_project.yaml
Book: /_book.yaml

# Platforms

{% include "_buttons.html" %}

Bazel can build and test code on a variety of hardware, operating systems, and
system configurations, using many different versions of build tools such as
linkers and compilers. To help manage this complexity, Bazel has a concept of
*constraints* and *platforms*. A constraint is a dimension in which build or
production environments may differ, such as CPU architecture, the presence or
absence of a GPU, or the version of a system-installed compiler. A platform is a
named collection of choices for these constraints, representing the particular
resources that are available in some environment.

Modeling the environment as a platform helps Bazel to automatically select the
appropriate
[toolchains](/extending/toolchains)
for build actions. Platforms can also be used in combination with the
[config_setting](/reference/be/general#config_setting)
rule to write [configurable attributes](/docs/configurable-attributes).

Bazel recognizes three roles that a platform may serve:

*  **Host** - the platform on which Bazel itself runs.
*  **Execution** - a platform on which build tools execute build actions to
   produce intermediate and final outputs.
*  **Target** - a platform on which a final output resides and executes.

Bazel supports the following build scenarios regarding platforms:

*  **Single-platform builds** (default) - host, execution, and target platforms
   are the same. For example, building a Linux executable on Ubuntu running on
   an Intel x64 CPU.

*  **Cross-compilation builds** - host and execution platforms are the same, but
   the target platform is different. For example, building an iOS app on macOS
   running on a MacBook Pro.

*  **Multi-platform builds** - host, execution, and target platforms are all
   different.

Tip: for detailed instructions on migrating your project to platforms, see
[Migrating to Platforms](/concepts/platforms).

## Defining constraints and platforms {:#constraints-platforms}

The space of possible choices for platforms is defined by using the
[`constraint_setting`][constraint_setting] and
[`constraint_value`][constraint_value] rules within `BUILD` files.
`constraint_setting` creates a new dimension, while
`constraint_value` creates a new value for a given dimension; together they
effectively define an enum and its possible values. For example, the following
snippet of a `BUILD` file introduces a constraint for the system's glibc version
with two possible values.

[constraint_setting]: /reference/be/platforms-and-toolchains#constraint_setting
[constraint_value]: /reference/be/platforms-and-toolchains#constraint_value

```python
constraint_setting(name = "glibc_version")

constraint_value(
    name = "glibc_2_25",
    constraint_setting = ":glibc_version",
)

constraint_value(
    name = "glibc_2_26",
    constraint_setting = ":glibc_version",
)
```

Constraints and their values may be defined across different packages in the
workspace. They are referenced by label and subject to the usual visibility
controls. If visibility allows, you can extend an existing constraint setting by
defining your own value for it.

The [`platform`](/reference/be/platforms-and-toolchains#platform) rule introduces a new platform with
certain choices of constraint values. The
following creates a platform named `linux_x86`, and says that it describes any
environment that runs a Linux operating system on an x86_64 architecture with a
glibc version of 2.25. (See below for more on Bazel's built-in constraints.)

```python
platform(
    name = "linux_x86",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
        ":glibc_2_25",
    ],
)
```

Note: It is an error for a platform to specify more than one value of the
same constraint setting, such as `@platforms//cpu:x86_64` and
`@platforms//cpu:arm` for `@platforms//cpu:cpu`.

## Generally useful constraints and platforms {:#useful-constraints-platforms}

To keep the ecosystem consistent, Bazel team maintains a repository with
constraint definitions for the most popular CPU architectures and operating
systems. These are all located in
[https://github.com/bazelbuild/platforms](https://github.com/bazelbuild/platforms){: .external}.

Bazel ships with the following special platform definition:
`@platforms//host` (aliased as `@bazel_tools//tools:host_platform`). This is the
autodetected host platform value -
represents autodetected platform for the system Bazel is running on.

## Specifying a platform for a build {:#specifying-build-platform}

You can specify the host and target platforms for a build using the following
command-line flags:

*  `--host_platform` - defaults to `@bazel_tools//tools:host_platform`
   *  This target is aliased to `@platforms//host`, which is backed by a repo
      rule that detects the host OS and CPU and writes the platform target.
   *  There's also `@platforms//host:constraints.bzl`, which exposes
      an array called `HOST_CONSTRAINTS`, which can be used in other BUILD and
      Starlark files.
*  `--platforms` - defaults to the host platform
   *  This means that when no other flags are set,
      `@platforms//host` is the target platform.
   *  If `--host_platform` is set and not `--platforms`, the value of
      `--host_platform` is both the host and target platform.

## Skipping incompatible targets {:#skipping-incompatible-targets}

When building for a specific target platform it is often desirable to skip
targets that will never work on that platform. For example, your Windows device
driver is likely going to generate lots of compiler errors when building on a
Linux machine with `//...`. Use the
[`target_compatible_with`](/reference/be/common-definitions#common.target_compatible_with)
attribute to tell Bazel what target platform constraints your code has.

The simplest use of this attribute restricts a target to a single platform.
The target will not be built for any platform that doesn't satisfy all of the
constraints. The following example restricts `win_driver_lib.cc` to 64-bit
Windows.

```python
cc_library(
    name = "win_driver_lib",
    srcs = ["win_driver_lib.cc"],
    target_compatible_with = [
        "@platforms//cpu:x86_64",
        "@platforms//os:windows",
    ],
)
```

`:win_driver_lib` is *only* compatible for building with 64-bit Windows and
incompatible with all else. Incompatibility is transitive. Any targets
that transitively depend on an incompatible target are themselves considered
incompatible.

### When are targets skipped? {:#when-targets-skipped}

Targets are skipped when they are considered incompatible and included in the
build as part of a target pattern expansion. For example, the following two
invocations skip any incompatible targets found in a target pattern expansion.

```console
$ bazel build --platforms=//:myplatform //...
```

```console
$ bazel build --platforms=//:myplatform //:all
```

Incompatible tests in a [`test_suite`](/reference/be/general#test_suite) are
similarly skipped if the `test_suite` is specified on the command line with
[`--expand_test_suites`](/reference/command-line-reference#flag--expand_test_suites).
In other words, `test_suite` targets on the command line behave like `:all` and
`...`. Using `--noexpand_test_suites` prevents expansion and causes
`test_suite` targets with incompatible tests to also be incompatible.

Explicitly specifying an incompatible target on the command line results in an
error message and a failed build.

```console
$ bazel build --platforms=//:myplatform //:target_incompatible_with_myplatform
...
ERROR: Target //:target_incompatible_with_myplatform is incompatible and cannot be built, but was explicitly requested.
...
FAILED: Build did NOT complete successfully
```

Incompatible explicit targets are silently skipped if
`--skip_incompatible_explicit_targets` is enabled.

### More expressive constraints {:#expressive-constraints}

For more flexibility in expressing constraints, use the
`@platforms//:incompatible`
[`constraint_value`](/reference/be/platforms-and-toolchains#constraint_value)
that no platform satisfies.

Use [`select()`](/reference/be/functions#select) in combination with
`@platforms//:incompatible` to express more complicated restrictions. For
example, use it to implement basic OR logic. The following marks a library
compatible with macOS and Linux, but no other platforms.

Note: An empty constraints list is equivalent to "compatible with everything".

```python
cc_library(
    name = "unixish_lib",
    srcs = ["unixish_lib.cc"],
    target_compatible_with = select({
        "@platforms//os:osx": [],
        "@platforms//os:linux": [],
        "//conditions:default": ["@platforms//:incompatible"],
    }),
)
```

The above can be interpreted as follows:

1. When targeting macOS, the target has no constraints.
2. When targeting Linux, the target has no constraints.
3. Otherwise, the target has the `@platforms//:incompatible` constraint. Because
   `@platforms//:incompatible` is not part of any platform, the target is
   deemed incompatible.

To make your constraints more readable, use
[skylib](https://github.com/bazelbuild/bazel-skylib){: .external}'s
[`selects.with_or()`](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/selects_doc.md#selectswith_or){: .external}.

You can express inverse compatibility in a similar way. The following example
describes a library that is compatible with everything _except_ for ARM.

```python
cc_library(
    name = "non_arm_lib",
    srcs = ["non_arm_lib.cc"],
    target_compatible_with = select({
        "@platforms//cpu:arm": ["@platforms//:incompatible"],
        "//conditions:default": [],
    }),
)
```

### Detecting incompatible targets using `bazel cquery` {:#cquery-incompatible-target-detection}

You can use the
[`IncompatiblePlatformProvider`](/rules/lib/providers/IncompatiblePlatformProvider)
in `bazel cquery`'s [Starlark output
format](/query/cquery#output-format-definition) to distinguish
incompatible targets from compatible ones.

This can be used to filter out incompatible targets. The example below will
only print the labels for targets that are compatible. Incompatible targets are
not printed.

```console
$ cat example.cquery

def format(target):
  if "IncompatiblePlatformProvider" not in providers(target):
    return target.label
  return ""


$ bazel cquery //... --output=starlark --starlark:file=example.cquery
```

### Known Issues

Incompatible targets [ignore visibility
restrictions](https://github.com/bazelbuild/bazel/issues/16044).


Project: /_project.yaml
Book: /_book.yaml

# Execution Groups

{% include "_buttons.html" %}

Execution groups allow for multiple execution platforms within a single target.
Each execution group has its own [toolchain](/extending/toolchains) dependencies and
performs its own [toolchain resolution](/extending/toolchains#toolchain-resolution).

## Current status {:#current-status}

Execution groups for certain natively declared actions, like `CppLink`, can be
used inside `exec_properties` to set per-action, per-target execution
requirements. For more details, see the
[Default execution groups](#exec-groups-for-native-rules) section.

## Background {:#background}

Execution groups allow the rule author to define sets of actions, each with a
potentially different execution platform. Multiple execution platforms can allow
actions to execution differently, for example compiling an iOS app on a remote
(linux) worker and then linking/code signing on a local mac worker.

Being able to define groups of actions also helps alleviate the usage of action
mnemonics as a proxy for specifying actions. Mnemonics are not guaranteed to be
unique and can only reference a single action. This is especially helpful in
allocating extra resources to specific memory and processing intensive actions
like linking in C++ builds without over-allocating to less demanding tasks.

## Defining execution groups {:#defining-exec-groups}

During rule definition, rule authors can
[declare](/rules/lib/globals/bzl#exec_group)
a set of execution groups. On each execution group, the rule author can specify
everything needed to select an execution platform for that execution group,
namely any constraints via `exec_compatible_with` and toolchain types via
`toolchain`.

```python
# foo.bzl
my_rule = rule(
    _impl,
    exec_groups = {
        "link": exec_group(
            exec_compatible_with = ["@platforms//os:linux"],
            toolchains = ["//foo:toolchain_type"],
        ),
        "test": exec_group(
            toolchains = ["//foo_tools:toolchain_type"],
        ),
    },
    attrs = {
        "_compiler": attr.label(cfg = config.exec("link"))
    },
)
```

In the code snippet above, you can see that tool dependencies can also specify
transition for an exec group using the
[`cfg`](/rules/lib/toplevel/attr#label)
attribute param and the
[`config`](/rules/lib/toplevel/config)
module. The module exposes an `exec` function which takes a single string
parameter which is the name of the exec group for which the dependency should be
built.

As on native rules, the `test` execution group is present by default on Starlark
test rules.

## Accessing execution groups {:#accessing-exec-groups}

In the rule implementation, you can declare that actions should be run on the
execution platform of an execution group. You can do this by using the `exec_group`
param of action generating methods, specifically [`ctx.actions.run`]
(/rules/lib/builtins/actions#run) and
[`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell).

```python
# foo.bzl
def _impl(ctx):
  ctx.actions.run(
     inputs = [ctx.attr._some_tool, ctx.srcs[0]]
     exec_group = "compile",
     # ...
  )
```

Rule authors will also be able to access the [resolved toolchains](/extending/toolchains#toolchain-resolution)
of execution groups, similarly to how you
can access the resolved toolchain of a target:

```python
# foo.bzl
def _impl(ctx):
  foo_info = ctx.exec_groups["link"].toolchains["//foo:toolchain_type"].fooinfo
  ctx.actions.run(
     inputs = [foo_info, ctx.srcs[0]]
     exec_group = "link",
     # ...
  )
```

Note: If an action uses a toolchain from an execution group, but doesn't specify
that execution group in the action declaration, that may potentially cause
issues. A mismatch like this may not immediately cause failures, but is a latent
problem.

### Default execution groups {:#exec-groups-for-native-rules}

The following execution groups are predefined:

* `test`: Test runner actions (for more details, see
  the [execution platform section of the Test Encylopedia](/reference/test-encyclopedia#execution-platform)).
* `cpp_link`: C++ linking actions.

## Using execution groups to set execution properties {:#using-exec-groups-for-exec-properties}

Execution groups are integrated with the
[`exec_properties`](/reference/be/common-definitions#common-attributes)
attribute that exists on every rule and allows the target writer to specify a
string dict of properties that is then passed to the execution machinery. For
example, if you wanted to set some property, say memory, for the target and give
certain actions a higher memory allocation, you would write an `exec_properties`
entry with an execution-group-augmented key, such as:

```python
# BUILD
my_rule(
    name = 'my_target',
    exec_properties = {
        'mem': '12g',
        'link.mem': '16g'
    }
    …
)
```

All actions with `exec_group = "link"` would see the exec properties
dictionary as `{"mem": "16g"}`. As you see here, execution-group-level
settings override target-level settings.

## Using execution groups to set platform constraints {:#using-exec-groups-for-platform-constraints}

Execution groups are also integrated with the
[`exec_compatible_with`](/reference/be/common-definitions#common-attributes) and
[`exec_group_compatible_with`](/reference/be/common-definitions#common-attributes)
attributes that exist on every rule and allow the target writer to specify
additional constraints that must be satisfied by the execution platforms
selected for the target's actions.

For example, if the rule `my_test` defines the `link` execution group in
addition to the default and the `test` execution group, then the following
usage of these attributes would run actions in the default execution group on
a platform with a high number of CPUs, the test action on Linux, and the link
action on the default execution platform:

```python
# BUILD
constraint_setting(name = "cpu")
constraint_value(name = "high_cpu", constraint_setting = ":cpu")

platform(
  name = "high_cpu_platform",
  constraint_values = [":high_cpu"],
  exec_properties = {
    "cpu": "256",
  },
)

my_test(
  name = "my_test",
  exec_compatible_with = ["//constraints:high_cpu"],
  exec_group_compatible_with = {
    "test": ["@platforms//os:linux"],
  },
  ...
)
```

### Execution groups for native rules {:#execution-groups-for-native-rules}

The following execution groups are available for actions defined by native
rules:

* `test`: Test runner actions.
* `cpp_link`: C++ linking actions.

### Execution groups and platform execution properties {:#platform-execution-properties}

It is possible to define `exec_properties` for arbitrary execution groups on
platform targets (unlike `exec_properties` set directly on a target, where
properties for unknown execution groups are rejected). Targets then inherit the
execution platform's `exec_properties` that affect the default execution group
and any other relevant execution groups.

For example, suppose running tests on the exec platform requires some resource
to be available, but it isn't required for compiling and linking; this can be
modelled as follows:

```python
constraint_setting(name = "resource")
constraint_value(name = "has_resource", constraint_setting = ":resource")

platform(
    name = "platform_with_resource",
    constraint_values = [":has_resource"],
    exec_properties = {
        "test.resource": "...",
    },
)

cc_test(
    name = "my_test",
    srcs = ["my_test.cc"],
    exec_compatible_with = [":has_resource"],
)
```

`exec_properties` defined directly on targets take precedence over those that
are inherited from the execution platform.


Project: /_project.yaml
Book: /_book.yaml

# Rules

{% include "_buttons.html" %}

A **rule** defines a series of [**actions**](#actions) that Bazel performs on
inputs to produce a set of outputs, which are referenced in
[**providers**](#providers) returned by the rule's
[**implementation function**](#implementation_function). For example, a C++
binary rule might:

1.  Take a set of `.cpp` source files (inputs).
2.  Run `g++` on the source files (action).
3.  Return the `DefaultInfo` provider with the executable output and other files
    to make available at runtime.
4.  Return the `CcInfo` provider with C++-specific information gathered from the
    target and its dependencies.

From Bazel's perspective, `g++` and the standard C++ libraries are also inputs
to this rule. As a rule writer, you must consider not only the user-provided
inputs to a rule, but also all of the tools and libraries required to execute
the actions.

Before creating or modifying any rule, ensure you are familiar with Bazel's
[build phases](/extending/concepts). It is important to understand the three
phases of a build (loading, analysis, and execution). It is also useful to
learn about [macros](/extending/macros) to understand the difference between rules and
macros. To get started, first review the [Rules Tutorial](/rules/rules-tutorial).
Then, use this page as a reference.

A few rules are built into Bazel itself. These *native rules*, such as
`genrule` and `filegroup`, provide some core support.
By defining your own rules, you can add support for languages and tools
that Bazel doesn't support natively.

Bazel provides an extensibility model for writing rules using the
[Starlark](/rules/language) language. These rules are written in `.bzl` files, which
can be loaded directly from `BUILD` files.

When defining your own rule, you get to decide what attributes it supports and
how it generates its outputs.

The rule's `implementation` function defines its exact behavior during the
[analysis phase](/extending/concepts#evaluation-model). This function doesn't run any
external commands. Rather, it registers [actions](#actions) that will be used
later during the execution phase to build the rule's outputs, if they are
needed.

## Rule creation

In a `.bzl` file, use the [rule](/rules/lib/globals/bzl#rule) function to define a new
rule, and store the result in a global variable. The call to `rule` specifies
[attributes](#attributes) and an
[implementation function](#implementation_function):

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        "deps": attr.label_list(),
        ...
    },
)
```

This defines a [rule kind](/query/language#kind) named `example_library`.

The call to `rule` also must specify if the rule creates an
[executable](#executable-rules) output (with `executable = True`), or specifically
a test executable (with `test = True`). If the latter, the rule is a *test rule*,
and the name of the rule must end in `_test`.

## Target instantiation

Rules can be [loaded](/concepts/build-files#load) and called in `BUILD` files:

```python
load('//some/pkg:rules.bzl', 'example_library')

example_library(
    name = "example_target",
    deps = [":another_target"],
    ...
)
```

Each call to a build rule returns no value, but has the side effect of defining
a target. This is called *instantiating* the rule. This specifies a name for the
new target and values for the target's [attributes](#attributes).

Rules can also be called from Starlark functions and loaded in `.bzl` files.
Starlark functions that call rules are called [Starlark macros](/extending/macros).
Starlark macros must ultimately be called from `BUILD` files, and can only be
called during the [loading phase](/extending/concepts#evaluation-model), when `BUILD`
files are evaluated to instantiate targets.

## Attributes

An *attribute* is a rule argument. Attributes can provide specific values to a
target's [implementation](#implementation_function), or they can refer to other
targets, creating a graph of dependencies.

Rule-specific attributes, such as `srcs` or `deps`, are defined by passing a map
from attribute names to schemas (created using the [`attr`](/rules/lib/toplevel/attr)
module) to the `attrs` parameter of `rule`.
[Common attributes](/reference/be/common-definitions#common-attributes), such as
`name` and `visibility`, are implicitly added to all rules. Additional
attributes are implicitly added to
[executable and test rules](#executable-rules) specifically. Attributes which
are implicitly added to a rule can't be included in the dictionary passed to
`attrs`.

### Dependency attributes

Rules that process source code usually define the following attributes to handle
various [types of dependencies](/concepts/dependencies#types_of_dependencies):

*   `srcs` specifies source files processed by a target's actions. Often, the
    attribute schema specifies which file extensions are expected for the sort
    of source file the rule processes. Rules for languages with header files
    generally specify a separate `hdrs` attribute for headers processed by a
    target and its consumers.
*   `deps` specifies code dependencies for a target. The attribute schema should
    specify which [providers](#providers) those dependencies must provide. (For
    example, `cc_library` provides `CcInfo`.)
*   `data` specifies files to be made available at runtime to any executable
    which depends on a target. That should allow arbitrary files to be
    specified.

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = [".example"]),
        "hdrs": attr.label_list(allow_files = [".header"]),
        "deps": attr.label_list(providers = [ExampleInfo]),
        "data": attr.label_list(allow_files = True),
        ...
    },
)
```

These are examples of *dependency attributes*. Any attribute that specifies
an input label (those defined with
[`attr.label_list`](/rules/lib/toplevel/attr#label_list),
[`attr.label`](/rules/lib/toplevel/attr#label), or
[`attr.label_keyed_string_dict`](/rules/lib/toplevel/attr#label_keyed_string_dict))
specifies dependencies of a certain type
between a target and the targets whose labels (or the corresponding
[`Label`](/rules/lib/builtins/Label) objects) are listed in that attribute when the target
is defined. The repository, and possibly the path, for these labels is resolved
relative to the defined target.

```python
example_library(
    name = "my_target",
    deps = [":other_target"],
)

example_library(
    name = "other_target",
    ...
)
```

In this example, `other_target` is a dependency of `my_target`, and therefore
`other_target` is analyzed first. It is an error if there is a cycle in the
dependency graph of targets.

<a name="private-attributes"></a>

### Private attributes and implicit dependencies {:#private_attributes_and_implicit_dependencies}

A dependency attribute with a default value creates an *implicit dependency*. It
is implicit because it's a part of the target graph that the user doesn't
specify it in a `BUILD` file. Implicit dependencies are useful for hard-coding a
relationship between a rule and a *tool* (a build-time dependency, such as a
compiler), since most of the time a user is not interested in specifying what
tool the rule uses. Inside the rule's implementation function, this is treated
the same as other dependencies.

If you want to provide an implicit dependency without allowing the user to
override that value, you can make the attribute *private* by giving it a name
that begins with an underscore (`_`). Private attributes must have default
values. It generally only makes sense to use private attributes for implicit
dependencies.

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        ...
        "_compiler": attr.label(
            default = Label("//tools:example_compiler"),
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
    },
)
```

In this example, every target of type `example_library` has an implicit
dependency on the compiler `//tools:example_compiler`. This allows
`example_library`'s implementation function to generate actions that invoke the
compiler, even though the user did not pass its label as an input. Since
`_compiler` is a private attribute, it follows that `ctx.attr._compiler`
will always point to `//tools:example_compiler` in all targets of this rule
type. Alternatively, you can name the attribute `compiler` without the
underscore and keep the default value. This allows users to substitute a
different compiler if necessary, but it requires no awareness of the compiler's
label.

Implicit dependencies are generally used for tools that reside in the same
repository as the rule implementation. If the tool comes from the
[execution platform](/extending/platforms) or a different repository instead, the
rule should obtain that tool from a [toolchain](/extending/toolchains).

### Output attributes

*Output attributes*, such as [`attr.output`](/rules/lib/toplevel/attr#output) and
[`attr.output_list`](/rules/lib/toplevel/attr#output_list), declare an output file that the
target generates. These differ from dependency attributes in two ways:

*   They define output file targets instead of referring to targets defined
    elsewhere.
*   The output file targets depend on the instantiated rule target, instead of
    the other way around.

Typically, output attributes are only used when a rule needs to create outputs
with user-defined names which can't be based on the target name. If a rule has
one output attribute, it is typically named `out` or `outs`.

Output attributes are the preferred way of creating *predeclared outputs*, which
can be specifically depended upon or
[requested at the command line](#requesting_output_files).

## Implementation function

Every rule requires an `implementation` function. These functions are executed
strictly in the [analysis phase](/extending/concepts#evaluation-model) and transform the
graph of targets generated in the loading phase into a graph of
[actions](#actions) to be performed during the execution phase. As such,
implementation functions can't actually read or write files.

Rule implementation functions are usually private (named with a leading
underscore). Conventionally, they are named the same as their rule, but suffixed
with `_impl`.

Implementation functions take exactly one parameter: a
[rule context](/rules/lib/builtins/ctx), conventionally named `ctx`. They return a list of
[providers](#providers).

### Targets

Dependencies are represented at analysis time as [`Target`](/rules/lib/builtins/Target)
objects. These objects contain the [providers](#providers) generated when the
target's implementation function was executed.

[`ctx.attr`](/rules/lib/builtins/ctx#attr) has fields corresponding to the names of each
dependency attribute, containing `Target` objects representing each direct
dependency using that attribute. For `label_list` attributes, this is a list of
`Targets`. For `label` attributes, this is a single `Target` or `None`.

A list of provider objects are returned by a target's implementation function:

```python
return [ExampleInfo(headers = depset(...))]
```

Those can be accessed using index notation (`[]`), with the type of provider as
a key. These can be [custom providers](#custom_providers) defined in Starlark or
[providers for native rules](/rules/lib/providers) available as Starlark
global variables.

For example, if a rule takes header files using a `hdrs` attribute and provides
them to the compilation actions of the target and its consumers, it could
collect them like so:

```python
def _example_library_impl(ctx):
    ...
    transitive_headers = [hdr[ExampleInfo].headers for hdr in ctx.attr.hdrs]
```

There's a legacy struct style, which is strongly discouraged and rules should be
[migrated away from it](#migrating_from_legacy_providers).

### Files

Files are represented by [`File`](/rules/lib/builtins/File) objects. Since Bazel doesn't
perform file I/O during the analysis phase, these objects can't be used to
directly read or write file content. Rather, they are passed to action-emitting
functions (see [`ctx.actions`](/rules/lib/builtins/actions)) to construct pieces of the
action graph.

A `File` can either be a source file or a generated file. Each generated file
must be an output of exactly one action. Source files can't be the output of
any action.

For each dependency attribute, the corresponding field of
[`ctx.files`](/rules/lib/builtins/ctx#files) contains a list of the default outputs of all
dependencies using that attribute:

```python
def _example_library_impl(ctx):
    ...
    headers = depset(ctx.files.hdrs, transitive = transitive_headers)
    srcs = ctx.files.srcs
    ...
```

[`ctx.file`](/rules/lib/builtins/ctx#file) contains a single `File` or `None` for
dependency attributes whose specs set `allow_single_file = True`.
[`ctx.executable`](/rules/lib/builtins/ctx#executable) behaves the same as `ctx.file`, but only
contains fields for dependency attributes whose specs set `executable = True`.

### Declaring outputs

During the analysis phase, a rule's implementation function can create outputs.
Since all labels have to be known during the loading phase, these additional
outputs have no labels. `File` objects for outputs can be created using
[`ctx.actions.declare_file`](/rules/lib/builtins/actions#declare_file) and
[`ctx.actions.declare_directory`](/rules/lib/builtins/actions#declare_directory).
Often, the names of outputs are based on the target's name,
[`ctx.label.name`](/rules/lib/builtins/ctx#label):

```python
def _example_library_impl(ctx):
  ...
  output_file = ctx.actions.declare_file(ctx.label.name + ".output")
  ...
```

For *predeclared outputs*, like those created for
[output attributes](#output_attributes), `File` objects instead can be retrieved
from the corresponding fields of [`ctx.outputs`](/rules/lib/builtins/ctx#outputs).

### Actions

An action describes how to generate a set of outputs from a set of inputs, for
example "run gcc on hello.c and get hello.o". When an action is created, Bazel
doesn't run the command immediately. It registers it in a graph of dependencies,
because an action can depend on the output of another action. For example, in C,
the linker must be called after the compiler.

General-purpose functions that create actions are defined in
[`ctx.actions`](/rules/lib/builtins/actions):

*   [`ctx.actions.run`](/rules/lib/builtins/actions#run), to run an executable.
*   [`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell), to run a shell
    command.
*   [`ctx.actions.write`](/rules/lib/builtins/actions#write), to write a string to a file.
*   [`ctx.actions.expand_template`](/rules/lib/builtins/actions#expand_template), to
    generate a file from a template.

[`ctx.actions.args`](/rules/lib/builtins/actions#args) can be used to efficiently
accumulate the arguments for actions. It avoids flattening depsets until
execution time:

```python
def _example_library_impl(ctx):
    ...

    transitive_headers = [dep[ExampleInfo].headers for dep in ctx.attr.deps]
    headers = depset(ctx.files.hdrs, transitive = transitive_headers)
    srcs = ctx.files.srcs
    inputs = depset(srcs, transitive = [headers])
    output_file = ctx.actions.declare_file(ctx.label.name + ".output")

    args = ctx.actions.args()
    args.add_joined("-h", headers, join_with = ",")
    args.add_joined("-s", srcs, join_with = ",")
    args.add("-o", output_file)

    ctx.actions.run(
        mnemonic = "ExampleCompile",
        executable = ctx.executable._compiler,
        arguments = [args],
        inputs = inputs,
        outputs = [output_file],
    )
    ...
```

Actions take a list or depset of input files and generate a (non-empty) list of
output files. The set of input and output files must be known during the
[analysis phase](/extending/concepts#evaluation-model). It might depend on the value of
attributes, including providers from dependencies, but it can't depend on the
result of the execution. For example, if your action runs the unzip command, you
must specify which files you expect to be inflated (before running unzip).
Actions which create a variable number of files internally can wrap those in a
single file (such as a zip, tar, or other archive format).

Actions must list all of their inputs. Listing inputs that are not used is
permitted, but inefficient.

Actions must create all of their outputs. They may write other files, but
anything not in outputs won't be available to consumers. All declared outputs
must be written by some action.

Actions are comparable to pure functions: They should depend only on the
provided inputs, and avoid accessing computer information, username, clock,
network, or I/O devices (except for reading inputs and writing outputs). This is
important because the output will be cached and reused.

Dependencies are resolved by Bazel, which decides which actions to
execute. It is an error if there is a cycle in the dependency graph. Creating
an action doesn't guarantee that it will be executed, that depends on whether
its outputs are needed for the build.

### Providers

Providers are pieces of information that a rule exposes to other rules that
depend on it. This data can include output files, libraries, parameters to pass
on a tool's command line, or anything else a target's consumers should know
about.

Since a rule's implementation function can only read providers from the
instantiated target's immediate dependencies, rules need to forward any
information from a target's dependencies that needs to be known by a target's
consumers, generally by accumulating that into a [`depset`](/rules/lib/builtins/depset).

A target's providers are specified by a list of provider objects returned by
the implementation function.

Old implementation functions can also be written in a legacy style where the
implementation function returns a [`struct`](/rules/lib/builtins/struct) instead of list of
provider objects. This style is strongly discouraged and rules should be
[migrated away from it](#migrating_from_legacy_providers).

#### Default outputs

A target's *default outputs* are the outputs that are requested by default when
the target is requested for build at the command line. For example, a
`java_library` target `//pkg:foo` has `foo.jar` as a default output, so that
will be built by the command `bazel build //pkg:foo`.

Default outputs are specified by the `files` parameter of
[`DefaultInfo`](/rules/lib/providers/DefaultInfo):

```python
def _example_library_impl(ctx):
    ...
    return [
        DefaultInfo(files = depset([output_file]), ...),
        ...
    ]
```

If `DefaultInfo` is not returned by a rule implementation or the `files`
parameter is not specified, `DefaultInfo.files` defaults to all
*predeclared outputs* (generally, those created by [output
attributes](#output_attributes)).

Rules that perform actions should provide default outputs, even if those outputs
are not expected to be directly used. Actions that are not in the graph of the
requested outputs are pruned. If an output is only used by a target's consumers,
those actions won't be performed when the target is built in isolation. This
makes debugging more difficult because rebuilding just the failing target won't
reproduce the failure.

#### Runfiles

Runfiles are a set of files used by a target at runtime (as opposed to build
time). During the [execution phase](/extending/concepts#evaluation-model), Bazel creates
a directory tree containing symlinks pointing to the runfiles. This stages the
environment for the binary so it can access the runfiles during runtime.

Runfiles can be added manually during rule creation.
[`runfiles`](/rules/lib/builtins/runfiles) objects can be created by the `runfiles` method
on the rule context, [`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles) and passed to the
`runfiles` parameter on `DefaultInfo`. The executable output of
[executable rules](#executable-rules) is implicitly added to the runfiles.

Some rules specify attributes, generally named
[`data`](/reference/be/common-definitions#common.data), whose outputs are added to
a targets' runfiles. Runfiles should also be merged in from `data`, as well as
from any attributes which might provide code for eventual execution, generally
`srcs` (which might contain `filegroup` targets with associated `data`) and
`deps`.

```python
def _example_library_impl(ctx):
    ...
    runfiles = ctx.runfiles(files = ctx.files.data)
    transitive_runfiles = []
    for runfiles_attr in (
        ctx.attr.srcs,
        ctx.attr.hdrs,
        ctx.attr.deps,
        ctx.attr.data,
    ):
        for target in runfiles_attr:
            transitive_runfiles.append(target[DefaultInfo].default_runfiles)
    runfiles = runfiles.merge_all(transitive_runfiles)
    return [
        DefaultInfo(..., runfiles = runfiles),
        ...
    ]
```

#### Custom providers

Providers can be defined using the [`provider`](/rules/lib/globals/bzl#provider)
function to convey rule-specific information:

```python
ExampleInfo = provider(
    "Info needed to compile/link Example code.",
    fields = {
        "headers": "depset of header Files from transitive dependencies.",
        "files_to_link": "depset of Files from compilation.",
    },
)
```

Rule implementation functions can then construct and return provider instances:

```python
def _example_library_impl(ctx):
  ...
  return [
      ...
      ExampleInfo(
          headers = headers,
          files_to_link = depset(
              [output_file],
              transitive = [
                  dep[ExampleInfo].files_to_link for dep in ctx.attr.deps
              ],
          ),
      )
  ]
```

##### Custom initialization of providers

It's possible to guard the instantiation of a provider with custom
preprocessing and validation logic. This can be used to ensure that all
provider instances satisfy certain invariants, or to give users a cleaner API for
obtaining an instance.

This is done by passing an `init` callback to the
[`provider`](/rules/lib/globals/bzl.html#provider) function. If this callback is given, the
return type of `provider()` changes to be a tuple of two values: the provider
symbol that is the ordinary return value when `init` is not used, and a "raw
constructor".

In this case, when the provider symbol is called, instead of directly returning
a new instance, it will forward the arguments along to the `init` callback. The
callback's return value must be a dict mapping field names (strings) to values;
this is used to initialize the fields of the new instance. Note that the
callback may have any signature, and if the arguments don't match the signature
an error is reported as if the callback were invoked directly.

The raw constructor, by contrast, will bypass the `init` callback.

The following example uses `init` to preprocess and validate its arguments:

```python
# //pkg:exampleinfo.bzl

_core_headers = [...]  # private constant representing standard library files

# Keyword-only arguments are preferred.
def _exampleinfo_init(*, files_to_link, headers = None, allow_empty_files_to_link = False):
    if not files_to_link and not allow_empty_files_to_link:
        fail("files_to_link may not be empty")
    all_headers = depset(_core_headers, transitive = headers)
    return {"files_to_link": files_to_link, "headers": all_headers}

ExampleInfo, _new_exampleinfo = provider(
    fields = ["files_to_link", "headers"],
    init = _exampleinfo_init,
)
```

A rule implementation may then instantiate the provider as follows:

```python
ExampleInfo(
    files_to_link = my_files_to_link,  # may not be empty
    headers = my_headers,  # will automatically include the core headers
)
```

The raw constructor can be used to define alternative public factory functions
that don't go through the `init` logic. For example, exampleinfo.bzl
could define:

```python
def make_barebones_exampleinfo(headers):
    """Returns an ExampleInfo with no files_to_link and only the specified headers."""
    return _new_exampleinfo(files_to_link = depset(), headers = all_headers)
```

Typically, the raw constructor is bound to a variable whose name begins with an
underscore (`_new_exampleinfo` above), so that user code can't load it and
generate arbitrary provider instances.

Another use for `init` is to prevent the user from calling the provider
symbol altogether, and force them to use a factory function instead:

```python
def _exampleinfo_init_banned(*args, **kwargs):
    fail("Do not call ExampleInfo(). Use make_exampleinfo() instead.")

ExampleInfo, _new_exampleinfo = provider(
    ...
    init = _exampleinfo_init_banned)

def make_exampleinfo(...):
    ...
    return _new_exampleinfo(...)
```

<a name="executable-rules"></a>

## Executable rules and test rules

Executable rules define targets that can be invoked by a `bazel run` command.
Test rules are a special kind of executable rule whose targets can also be
invoked by a `bazel test` command. Executable and test rules are created by
setting the respective [`executable`](/rules/lib/globals/bzl#rule.executable) or
[`test`](/rules/lib/globals/bzl#rule.test) argument to `True` in the call to `rule`:

```python
example_binary = rule(
   implementation = _example_binary_impl,
   executable = True,
   ...
)

example_test = rule(
   implementation = _example_binary_impl,
   test = True,
   ...
)
```

Test rules must have names that end in `_test`. (Test *target* names also often
end in `_test` by convention, but this is not required.) Non-test rules must not
have this suffix.

Both kinds of rules must produce an executable output file (which may or may not
be predeclared) that will be invoked by the `run` or `test` commands. To tell
Bazel which of a rule's outputs to use as this executable, pass it as the
`executable` argument of a returned [`DefaultInfo`](/rules/lib/providers/DefaultInfo)
provider. That `executable` is added to the default outputs of the rule (so you
don't need to pass that to both `executable` and `files`). It's also implicitly
added to the [runfiles](#runfiles):

```python
def _example_binary_impl(ctx):
    executable = ctx.actions.declare_file(ctx.label.name)
    ...
    return [
        DefaultInfo(executable = executable, ...),
        ...
    ]
```

The action that generates this file must set the executable bit on the file. For
a [`ctx.actions.run`](/rules/lib/builtins/actions#run) or
[`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell) action this should be done
by the underlying tool that is invoked by the action. For a
[`ctx.actions.write`](/rules/lib/builtins/actions#write) action, pass `is_executable = True`.

As [legacy behavior](#deprecated_predeclared_outputs), executable rules have a
special `ctx.outputs.executable` predeclared output. This file serves as the
default executable if you don't specify one using `DefaultInfo`; it must not be
used otherwise. This output mechanism is deprecated because it doesn't support
customizing the executable file's name at analysis time.

See examples of an
[executable rule](https://github.com/bazelbuild/examples/blob/main/rules/executable/fortune.bzl){: .external}
and a
[test rule](https://github.com/bazelbuild/examples/blob/main/rules/test_rule/line_length.bzl){: .external}.

[Executable rules](/reference/be/common-definitions#common-attributes-binaries) and
[test rules](/reference/be/common-definitions#common-attributes-tests) have additional
attributes implicitly defined, in addition to those added for
[all rules](/reference/be/common-definitions#common-attributes). The defaults of
implicitly-added attributes can't be changed, though this can be worked around
by wrapping a private rule in a [Starlark macro](/extending/macros) which alters the
default:

```python
def example_test(size = "small", **kwargs):
  _example_test(size = size, **kwargs)

_example_test = rule(
 ...
)
```

### Runfiles location

When an executable target is run with `bazel run` (or `test`), the root of the
runfiles directory is adjacent to the executable. The paths relate as follows:

```python
# Given launcher_path and runfile_file:
runfiles_root = launcher_path.path + ".runfiles"
workspace_name = ctx.workspace_name
runfile_path = runfile_file.short_path
execution_root_relative_path = "%s/%s/%s" % (
    runfiles_root, workspace_name, runfile_path)
```

The path to a `File` under the runfiles directory corresponds to
[`File.short_path`](/rules/lib/builtins/File#short_path).

The binary executed directly by `bazel` is adjacent to the root of the
`runfiles` directory. However, binaries called *from* the runfiles can't make
the same assumption. To mitigate this, each binary should provide a way to
accept its runfiles root as a parameter using an environment, or command line
argument or flag. This allows binaries to pass the correct canonical runfiles root
to the binaries it calls. If that's not set, a binary can guess that it was the
first binary called and look for an adjacent runfiles directory.

## Advanced topics

### Requesting output files

A single target can have several output files. When a `bazel build` command is
run, some of the outputs of the targets given to the command are considered to
be *requested*. Bazel only builds these requested files and the files that they
directly or indirectly depend on. (In terms of the action graph, Bazel only
executes the actions that are reachable as transitive dependencies of the
requested files.)

In addition to [default outputs](#default_outputs), any *predeclared output* can
be explicitly requested on the command line. Rules can specify predeclared
outputs using [output attributes](#output_attributes). In that case, the user
explicitly chooses labels for outputs when they instantiate the rule. To obtain
[`File`](/rules/lib/builtins/File) objects for output attributes, use the corresponding
attribute of [`ctx.outputs`](/rules/lib/builtins/ctx#outputs). Rules can
[implicitly define predeclared outputs](#deprecated_predeclared_outputs) based
on the target name as well, but this feature is deprecated.

In addition to default outputs, there are *output groups*, which are collections
of output files that may be requested together. These can be requested with
[`--output_groups`](/reference/command-line-reference#flag--output_groups). For
example, if a target `//pkg:mytarget` is of a rule type that has a `debug_files`
output group, these files can be built by running `bazel build //pkg:mytarget
--output_groups=debug_files`. Since non-predeclared outputs don't have labels,
they can only be requested by appearing in the default outputs or an output
group.

Output groups can be specified with the
[`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo) provider. Note that unlike many
built-in providers, `OutputGroupInfo` can take parameters with arbitrary names
to define output groups with that name:

```python
def _example_library_impl(ctx):
    ...
    debug_file = ctx.actions.declare_file(name + ".pdb")
    ...
    return [
        DefaultInfo(files = depset([output_file]), ...),
        OutputGroupInfo(
            debug_files = depset([debug_file]),
            all_files = depset([output_file, debug_file]),
        ),
        ...
    ]
```

Also unlike most providers, `OutputGroupInfo` can be returned by both an
[aspect](/extending/aspects) and the rule target to which that aspect is applied, as
long as they don't define the same output groups. In that case, the resulting
providers are merged.

Note that `OutputGroupInfo` generally shouldn't be used to convey specific sorts
of files from a target to the actions of its consumers. Define
[rule-specific providers](#custom_providers) for that instead.

### Configurations

Imagine that you want to build a C++ binary for a different architecture. The
build can be complex and involve multiple steps. Some of the intermediate
binaries, like compilers and code generators, have to run on
[the execution platform](/extending/platforms#overview) (which could be your host,
or a remote executor). Some binaries like the final output must be built for the
target architecture.

For this reason, Bazel has a concept of "configurations" and transitions. The
topmost targets (the ones requested on the command line) are built-in the
"target" configuration, while tools that should run on the execution platform
are built-in an "exec" configuration. Rules may generate different actions based
on the configuration, for instance to change the cpu architecture that is passed
to the compiler. In some cases, the same library may be needed for different
configurations. If this happens, it will be analyzed and potentially built
multiple times.

By default, Bazel builds a target's dependencies in the same configuration as
the target itself, in other words without transitions. When a dependency is a
tool that's needed to help build the target, the corresponding attribute should
specify a transition to an exec configuration. This causes the tool and all its
dependencies to build for the execution platform.

For each dependency attribute, you can use `cfg` to decide if dependencies
should build in the same configuration or transition to an exec configuration.
If a dependency attribute has the flag `executable = True`, `cfg` must be set
explicitly. This is to guard against accidentally building a tool for the wrong
configuration.
[See example](https://github.com/bazelbuild/examples/blob/main/rules/actions_run/execute.bzl){: .external}

In general, sources, dependent libraries, and executables that will be needed at
runtime can use the same configuration.

Tools that are executed as part of the build (such as compilers or code generators)
should be built for an exec configuration. In this case, specify `cfg = "exec"` in
the attribute.

Otherwise, executables that are used at runtime (such as as part of a test) should
be built for the target configuration. In this case, specify `cfg = "target"` in
the attribute.

`cfg = "target"` doesn't actually do anything: it's purely a convenience value to
help rule designers be explicit about their intentions. When `executable = False`,
which means `cfg` is optional, only set this when it truly helps readability.

You can also use `cfg = my_transition` to use
[user-defined transitions](/extending/config#user-defined-transitions), which allow
rule authors a great deal of flexibility in changing configurations, with the
drawback of
[making the build graph larger and less comprehensible](/extending/config#memory-and-performance-considerations).

**Note**: Historically, Bazel didn't have the concept of execution platforms,
and instead all build actions were considered to run on the host machine. Bazel
versions before 6.0 created a distinct "host" configuration to represent this.
If you see references to "host" in code or old documentation, that's what this
refers to. We recommend using Bazel 6.0 or newer to avoid this extra conceptual
overhead.

<a name="fragments"></a>

### Configuration fragments

Rules may access
[configuration fragments](/rules/lib/fragments) such as
`cpp` and `java`. However, all required fragments must be declared in
order to avoid access errors:

```python
def _impl(ctx):
    # Using ctx.fragments.cpp leads to an error since it was not declared.
    x = ctx.fragments.java
    ...

my_rule = rule(
    implementation = _impl,
    fragments = ["java"],      # Required fragments of the target configuration
    ...
)
```

### Runfiles symlinks

Normally, the relative path of a file in the runfiles tree is the same as the
relative path of that file in the source tree or generated output tree. If these
need to be different for some reason, you can specify the `root_symlinks` or
`symlinks` arguments. The `root_symlinks` is a dictionary mapping paths to
files, where the paths are relative to the root of the runfiles directory. The
`symlinks` dictionary is the same, but paths are implicitly prefixed with the
name of the main workspace (*not* the name of the repository containing the
current target).

```python
    ...
    runfiles = ctx.runfiles(
        root_symlinks = {"some/path/here.foo": ctx.file.some_data_file2}
        symlinks = {"some/path/here.bar": ctx.file.some_data_file3}
    )
    # Creates something like:
    # sometarget.runfiles/
    #     some/
    #         path/
    #             here.foo -> some_data_file2
    #     <workspace_name>/
    #         some/
    #             path/
    #                 here.bar -> some_data_file3
```

If `symlinks` or `root_symlinks` is used, be careful not to map two different
files to the same path in the runfiles tree. This will cause the build to fail
with an error describing the conflict. To fix, you will need to modify your
`ctx.runfiles` arguments to remove the collision. This checking will be done for
any targets using your rule, as well as targets of any kind that depend on those
targets. This is especially risky if your tool is likely to be used transitively
by another tool; symlink names must be unique across the runfiles of a tool and
all of its dependencies.

### Code coverage

When the [`coverage`](/reference/command-line-reference#coverage) command is run,
the build may need to add coverage instrumentation for certain targets. The
build also gathers the list of source files that are instrumented. The subset of
targets that are considered is controlled by the flag
[`--instrumentation_filter`](/reference/command-line-reference#flag--instrumentation_filter).
Test targets are excluded, unless
[`--instrument_test_targets`](/reference/command-line-reference#flag--instrument_test_targets)
is specified.

If a rule implementation adds coverage instrumentation at build time, it needs
to account for that in its implementation function.
[ctx.coverage_instrumented](/rules/lib/builtins/ctx#coverage_instrumented) returns
`True` in coverage mode if a target's sources should be instrumented:

```python
# Are this rule's sources instrumented?
if ctx.coverage_instrumented():
  # Do something to turn on coverage for this compile action
```

Logic that always needs to be on in coverage mode (whether a target's sources
specifically are instrumented or not) can be conditioned on
[ctx.configuration.coverage_enabled](/rules/lib/builtins/configuration#coverage_enabled).

If the rule directly includes sources from its dependencies before compilation
(such as header files), it may also need to turn on compile-time instrumentation if
the dependencies' sources should be instrumented:

```python
# Are this rule's sources or any of the sources for its direct dependencies
# in deps instrumented?
if (ctx.configuration.coverage_enabled and
    (ctx.coverage_instrumented() or
     any([ctx.coverage_instrumented(dep) for dep in ctx.attr.deps]))):
    # Do something to turn on coverage for this compile action
```

Rules also should provide information about which attributes are relevant for
coverage with the `InstrumentedFilesInfo` provider, constructed using
[`coverage_common.instrumented_files_info`](/rules/lib/toplevel/coverage_common#instrumented_files_info).
The `dependency_attributes` parameter of `instrumented_files_info` should list
all runtime dependency attributes, including code dependencies like `deps` and
data dependencies like `data`. The `source_attributes` parameter should list the
rule's source files attributes if coverage instrumentation might be added:

```python
def _example_library_impl(ctx):
    ...
    return [
        ...
        coverage_common.instrumented_files_info(
            ctx,
            dependency_attributes = ["deps", "data"],
            # Omitted if coverage is not supported for this rule:
            source_attributes = ["srcs", "hdrs"],
        )
        ...
    ]
```

If `InstrumentedFilesInfo` is not returned, a default one is created with each
non-tool [dependency attribute](#dependency_attributes) that doesn't set
[`cfg`](#configuration) to `"exec"` in the attribute schema. in
`dependency_attributes`. (This isn't ideal behavior, since it puts attributes
like `srcs` in `dependency_attributes` instead of `source_attributes`, but it
avoids the need for explicit coverage configuration for all rules in the
dependency chain.)

### Validation Actions

Sometimes you need to validate something about the build, and the
information required to do that validation is available only in artifacts
(source files or generated files). Because this information is in artifacts,
rules can't do this validation at analysis time because rules can't read
files. Instead, actions must do this validation at execution time. When
validation fails, the action will fail, and hence so will the build.

Examples of validations that might be run are static analysis, linting,
dependency and consistency checks, and style checks.

Validation actions can also help to improve build performance by moving parts
of actions that are not required for building artifacts into separate actions.
For example, if a single action that does compilation and linting can be
separated into a compilation action and a linting action, then the linting
action can be run as a validation action and run in parallel with other actions.

These "validation actions" often don't produce anything that is used elsewhere
in the build, since they only need to assert things about their inputs. This
presents a problem though: If a validation action doesn't produce anything that
is used elsewhere in the build, how does a rule get the action to run?
Historically, the approach was to have the validation action output an empty
file, and artificially add that output to the inputs of some other important
action in the build:

<img src="/rules/validation_action_historical.svg" width="35%" />

This works, because Bazel will always run the validation action when the compile
action is run, but this has significant drawbacks:

1. The validation action is in the critical path of the build. Because Bazel
thinks the empty output is required to run the compile action, it will run the
validation action first, even though the compile action will ignore the input.
This reduces parallelism and slows down builds.

2. If other actions in the build might run instead of the
compile action, then the empty outputs of validation actions need to be added to
those actions as well (`java_library`'s source jar output, for example). This is
also a problem if new actions that might run instead of the compile action are
added later, and the empty validation output is accidentally left off.

The solution to these problems is to use the Validations Output Group.

#### Validations Output Group

The Validations Output Group is an output group designed to hold the otherwise
unused outputs of validation actions, so that they don't need to be artificially
added to the inputs of other actions.

This group is special in that its outputs are always requested, regardless of
the value of the `--output_groups` flag, and regardless of how the target is
depended upon (for example, on the command line, as a dependency, or through
implicit outputs of the target). Note that normal caching and incrementality
still apply: if the inputs to the validation action have not changed and the
validation action previously succeeded, then the validation action won't be
run.

<img src="/rules/validation_action.svg" width="35%" />

Using this output group still requires that validation actions output some file,
even an empty one. This might require wrapping some tools that normally don't
create outputs so that a file is created.

A target's validation actions are not run in three cases:

*    When the target is depended upon as a tool
*    When the target is depended upon as an implicit dependency (for example, an
     attribute that starts with "_")
*    When the target is built in the exec configuration.

It is assumed that these targets have their own
separate builds and tests that would uncover any validation failures.

#### Using the Validations Output Group

The Validations Output Group is named `_validation` and is used like any other
output group:

```python
def _rule_with_validation_impl(ctx):

  ctx.actions.write(ctx.outputs.main, "main output\n")
  ctx.actions.write(ctx.outputs.implicit, "implicit output\n")

  validation_output = ctx.actions.declare_file(ctx.attr.name + ".validation")
  ctx.actions.run(
    outputs = [validation_output],
    executable = ctx.executable._validation_tool,
    arguments = [validation_output.path],
  )

  return [
    DefaultInfo(files = depset([ctx.outputs.main])),
    OutputGroupInfo(_validation = depset([validation_output])),
  ]


rule_with_validation = rule(
  implementation = _rule_with_validation_impl,
  outputs = {
    "main": "%{name}.main",
    "implicit": "%{name}.implicit",
  },
  attrs = {
    "_validation_tool": attr.label(
        default = Label("//validation_actions:validation_tool"),
        executable = True,
        cfg = "exec"
    ),
  }
)
```

Notice that the validation output file is not added to the `DefaultInfo` or the
inputs to any other action. The validation action for a target of this rule kind
will still run if the target is depended upon by label, or any of the target's
implicit outputs are directly or indirectly depended upon.

It is usually important that the outputs of validation actions only go into the
validation output group, and are not added to the inputs of other actions, as
this could defeat parallelism gains. Note however that Bazel doesn't
have any special checking to enforce this. Therefore, you should test
that validation action outputs are not added to the inputs of any actions in the
tests for Starlark rules. For example:

```python
load("@bazel_skylib//lib:unittest.bzl", "analysistest")

def _validation_outputs_test_impl(ctx):
  env = analysistest.begin(ctx)

  actions = analysistest.target_actions(env)
  target = analysistest.target_under_test(env)
  validation_outputs = target.output_groups._validation.to_list()
  for action in actions:
    for validation_output in validation_outputs:
      if validation_output in action.inputs.to_list():
        analysistest.fail(env,
            "%s is a validation action output, but is an input to action %s" % (
                validation_output, action))

  return analysistest.end(env)

validation_outputs_test = analysistest.make(_validation_outputs_test_impl)
```

#### Validation Actions Flag

Running validation actions is controlled by the `--run_validations` command line
flag, which defaults to true.

## Deprecated features

### Deprecated predeclared outputs

There are two **deprecated** ways of using predeclared outputs:

*   The [`outputs`](/rules/lib/globals/bzl#rule.outputs) parameter of `rule` specifies
    a mapping between output attribute names and string templates for generating
    predeclared output labels. Prefer using non-predeclared outputs and
    explicitly adding outputs to `DefaultInfo.files`. Use the rule target's
    label as input for rules which consume the output instead of a predeclared
    output's label.

*   For [executable rules](#executable-rules), `ctx.outputs.executable` refers
    to a predeclared executable output with the same name as the rule target.
    Prefer declaring the output explicitly, for example with
    `ctx.actions.declare_file(ctx.label.name)`, and ensure that the command that
    generates the executable sets its permissions to allow execution. Explicitly
    pass the executable output to the `executable` parameter of `DefaultInfo`.

### Runfiles features to avoid

[`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles) and the [`runfiles`](/rules/lib/builtins/runfiles)
type have a complex set of features, many of which are kept for legacy reasons.
The following recommendations help reduce complexity:

*   **Avoid** use of the `collect_data` and `collect_default` modes of
    [`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles). These modes implicitly collect
    runfiles across certain hardcoded dependency edges in confusing ways.
    Instead, add files using the `files` or `transitive_files` parameters of
    `ctx.runfiles`, or by merging in runfiles from dependencies with
    `runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)`.

*   **Avoid** use of the `data_runfiles` and `default_runfiles` of the
    `DefaultInfo` constructor. Specify `DefaultInfo(runfiles = ...)` instead.
    The distinction between "default" and "data" runfiles is maintained for
    legacy reasons. For example, some rules put their default outputs in
    `data_runfiles`, but not `default_runfiles`. Instead of using
    `data_runfiles`, rules should *both* include default outputs and merge in
    `default_runfiles` from attributes which provide runfiles (often
    [`data`](/reference/be/common-definitions#common-attributes.data)).

*   When retrieving `runfiles` from `DefaultInfo` (generally only for merging
    runfiles between the current rule and its dependencies), use
    `DefaultInfo.default_runfiles`, **not** `DefaultInfo.data_runfiles`.

### Migrating from legacy providers

Historically, Bazel providers were simple fields on the `Target` object. They
were accessed using the dot operator, and they were created by putting the field
in a [`struct`](/rules/lib/builtins/struct) returned by the rule's
implementation function instead of a list of provider objects:

```python
return struct(example_info = struct(headers = depset(...)))
```

Such providers can be retrieved from the corresponding field of the `Target` object:

```python
transitive_headers = [hdr.example_info.headers for hdr in ctx.attr.hdrs]
```

*This style is deprecated and should not be used in new code;* see following for
information that may help you migrate. The new provider mechanism avoids name
clashes. It also supports data hiding, by requiring any code accessing a
provider instance to retrieve it using the provider symbol.

For the moment, legacy providers are still supported. A rule can return both
legacy and modern providers as follows:

```python
def _old_rule_impl(ctx):
  ...
  legacy_data = struct(x = "foo", ...)
  modern_data = MyInfo(y = "bar", ...)
  # When any legacy providers are returned, the top-level returned value is a
  # struct.
  return struct(
      # One key = value entry for each legacy provider.
      legacy_info = legacy_data,
      ...
      # Additional modern providers:
      providers = [modern_data, ...])
```

If `dep` is the resulting `Target` object for an instance of this rule, the
providers and their contents can be retrieved as `dep.legacy_info.x` and
`dep[MyInfo].y`.

In addition to `providers`, the returned struct can also take several other
fields that have special meaning (and thus don't create a corresponding legacy
provider):

*   The fields `files`, `runfiles`, `data_runfiles`, `default_runfiles`, and
    `executable` correspond to the same-named fields of
    [`DefaultInfo`](/rules/lib/providers/DefaultInfo). It is not allowed to specify any of
    these fields while also returning a `DefaultInfo` provider.

*   The field `output_groups` takes a struct value and corresponds to an
    [`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo).

In [`provides`](/rules/lib/globals/bzl#rule.provides) declarations of rules, and in
[`providers`](/rules/lib/toplevel/attr#label_list.providers) declarations of dependency
attributes, legacy providers are passed in as strings and modern providers are
passed in by their `Info` symbol. Be sure to change from strings to symbols
when migrating. For complex or large rule sets where it is difficult to update
all rules atomically, you may have an easier time if you follow this sequence of
steps:

1.  Modify the rules that produce the legacy provider to produce both the legacy
    and modern providers, using the preceding syntax. For rules that declare they
    return the legacy provider, update that declaration to include both the
    legacy and modern providers.

2.  Modify the rules that consume the legacy provider to instead consume the
    modern provider. If any attribute declarations require the legacy provider,
    also update them to instead require the modern provider. Optionally, you can
    interleave this work with step 1 by having consumers accept or require either
    provider: Test for the presence of the legacy provider using
    `hasattr(target, 'foo')`, or the new provider using `FooInfo in target`.

3.  Fully remove the legacy provider from all rules.


Project: /_project.yaml
Book: /_book.yaml

# Toolchains

{% include "_buttons.html" %}

This page describes the toolchain framework, which is a way for rule authors to
decouple their rule logic from platform-based selection of tools. It is
recommended to read the [rules](/extending/rules) and [platforms](/extending/platforms)
pages before continuing. This page covers why toolchains are needed, how to
define and use them, and how Bazel selects an appropriate toolchain based on
platform constraints.

## Motivation {:#motivation}

Let's first look at the problem toolchains are designed to solve. Suppose you
are writing rules to support the "bar" programming language. Your `bar_binary`
rule would compile `*.bar` files using the `barc` compiler, a tool that itself
is built as another target in your workspace. Since users who write `bar_binary`
targets shouldn't have to specify a dependency on the compiler, you make it an
implicit dependency by adding it to the rule definition as a private attribute.

```python
bar_binary = rule(
    implementation = _bar_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        ...
        "_compiler": attr.label(
            default = "//bar_tools:barc_linux",  # the compiler running on linux
            providers = [BarcInfo],
        ),
    },
)
```

`//bar_tools:barc_linux` is now a dependency of every `bar_binary` target, so
it'll be built before any `bar_binary` target. It can be accessed by the rule's
implementation function just like any other attribute:

```python
BarcInfo = provider(
    doc = "Information about how to invoke the barc compiler.",
    # In the real world, compiler_path and system_lib might hold File objects,
    # but for simplicity they are strings for this example. arch_flags is a list
    # of strings.
    fields = ["compiler_path", "system_lib", "arch_flags"],
)

def _bar_binary_impl(ctx):
    ...
    info = ctx.attr._compiler[BarcInfo]
    command = "%s -l %s %s" % (
        info.compiler_path,
        info.system_lib,
        " ".join(info.arch_flags),
    )
    ...
```

The issue here is that the compiler's label is hardcoded into `bar_binary`, yet
different targets may need different compilers depending on what platform they
are being built for and what platform they are being built on -- called the
*target platform* and *execution platform*, respectively. Furthermore, the rule
author does not necessarily even know all the available tools and platforms, so
it is not feasible to hardcode them in the rule's definition.

A less-than-ideal solution would be to shift the burden onto users, by making
the `_compiler` attribute non-private. Then individual targets could be
hardcoded to build for one platform or another.

```python
bar_binary(
    name = "myprog_on_linux",
    srcs = ["mysrc.bar"],
    compiler = "//bar_tools:barc_linux",
)

bar_binary(
    name = "myprog_on_windows",
    srcs = ["mysrc.bar"],
    compiler = "//bar_tools:barc_windows",
)
```

You can improve on this solution by using `select` to choose the `compiler`
[based on the platform](/docs/configurable-attributes):

```python
config_setting(
    name = "on_linux",
    constraint_values = [
        "@platforms//os:linux",
    ],
)

config_setting(
    name = "on_windows",
    constraint_values = [
        "@platforms//os:windows",
    ],
)

bar_binary(
    name = "myprog",
    srcs = ["mysrc.bar"],
    compiler = select({
        ":on_linux": "//bar_tools:barc_linux",
        ":on_windows": "//bar_tools:barc_windows",
    }),
)
```

But this is tedious and a bit much to ask of every single `bar_binary` user.
If this style is not used consistently throughout the workspace, it leads to
builds that work fine on a single platform but fail when extended to
multi-platform scenarios. It also does not address the problem of adding support
for new platforms and compilers without modifying existing rules or targets.

The toolchain framework solves this problem by adding an extra level of
indirection. Essentially, you declare that your rule has an abstract dependency
on *some* member of a family of targets (a toolchain type), and Bazel
automatically resolves this to a particular target (a toolchain) based on the
applicable platform constraints. Neither the rule author nor the target author
need know the complete set of available platforms and toolchains.

## Writing rules that use toolchains {:#writing-rules-toolchains}

Under the toolchain framework, instead of having rules depend directly on tools,
they instead depend on *toolchain types*. A toolchain type is a simple target
that represents a class of tools that serve the same role for different
platforms. For instance, you can declare a type that represents the bar
compiler:

```python
# By convention, toolchain_type targets are named "toolchain_type" and
# distinguished by their package path. So the full path for this would be
# //bar_tools:toolchain_type.
toolchain_type(name = "toolchain_type")
```

The rule definition in the previous section is modified so that instead of
taking in the compiler as an attribute, it declares that it consumes a
`//bar_tools:toolchain_type` toolchain.

```python
bar_binary = rule(
    implementation = _bar_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        ...
        # No `_compiler` attribute anymore.
    },
    toolchains = ["//bar_tools:toolchain_type"],
)
```

The implementation function now accesses this dependency under `ctx.toolchains`
instead of `ctx.attr`, using the toolchain type as the key.

```python
def _bar_binary_impl(ctx):
    ...
    info = ctx.toolchains["//bar_tools:toolchain_type"].barcinfo
    # The rest is unchanged.
    command = "%s -l %s %s" % (
        info.compiler_path,
        info.system_lib,
        " ".join(info.arch_flags),
    )
    ...
```

`ctx.toolchains["//bar_tools:toolchain_type"]` returns the
[`ToolchainInfo` provider](/rules/lib/toplevel/platform_common#ToolchainInfo)
of whatever target Bazel resolved the toolchain dependency to. The fields of the
`ToolchainInfo` object are set by the underlying tool's rule; in the next
section, this rule is defined such that there is a `barcinfo` field that wraps
a `BarcInfo` object.

Bazel's procedure for resolving toolchains to targets is described
[below](#toolchain-resolution). Only the resolved toolchain target is actually
made a dependency of the `bar_binary` target, not the whole space of candidate
toolchains.

### Mandatory and Optional Toolchains {:#optional-toolchains}

By default, when a rule expresses a toolchain type dependency using a bare label
(as shown above), the toolchain type is considered to be **mandatory**. If Bazel
is unable to find a matching toolchain (see
[Toolchain resolution](#toolchain-resolution) below) for a mandatory toolchain
type, this is an error and analysis halts.

It is possible instead to declare an **optional** toolchain type dependency, as
follows:

```python
bar_binary = rule(
    ...
    toolchains = [
        config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False),
    ],
)
```

When an optional toolchain type cannot be resolved, analysis continues, and the
result of `ctx.toolchains["//bar_tools:toolchain_type"]` is `None`.

The [`config_common.toolchain_type`](/rules/lib/toplevel/config_common#toolchain_type)
function defaults to mandatory.

The following forms can be used:

-  Mandatory toolchain types:
   -  `toolchains = ["//bar_tools:toolchain_type"]`
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type")]`
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = True)]`
- Optional toolchain types:
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False)]`

```python
bar_binary = rule(
    ...
    toolchains = [
        "//foo_tools:toolchain_type",
        config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False),
    ],
)
```

You can mix and match forms in the same rule, also. However, if the same
toolchain type is listed multiple times, it will take the most strict version,
where mandatory is more strict than optional.

### Writing aspects that use toolchains {:#writing-aspects-toolchains}

Aspects have access to the same toolchain API as rules: you can define required
toolchain types, access toolchains via the context, and use them to generate new
actions using the toolchain.

```py
bar_aspect = aspect(
    implementation = _bar_aspect_impl,
    attrs = {},
    toolchains = ['//bar_tools:toolchain_type'],
)

def _bar_aspect_impl(target, ctx):
  toolchain = ctx.toolchains['//bar_tools:toolchain_type']
  # Use the toolchain provider like in a rule.
  return []
```

## Defining toolchains {:#toolchain-definitions}

To define some toolchains for a given toolchain type, you need three things:

1. A language-specific rule representing the kind of tool or tool suite. By
   convention this rule's name is suffixed with "\_toolchain".

    1.  **Note:** The `\_toolchain` rule cannot create any build actions.
        Rather, it collects artifacts from other rules and forwards them to the
        rule that uses the toolchain. That rule is responsible for creating all
        build actions.

2. Several targets of this rule type, representing versions of the tool or tool
   suite for different platforms.

3. For each such target, an associated target of the generic
  [`toolchain`](/reference/be/platforms-and-toolchains#toolchain)
   rule, to provide metadata used by the toolchain framework. This `toolchain`
   target also refers to the `toolchain_type` associated with this toolchain.
   This means that a given `_toolchain` rule could be associated with any
   `toolchain_type`, and that only in a `toolchain` instance that uses
   this `_toolchain` rule that the rule is associated with a `toolchain_type`.

For our running example, here's a definition for a `bar_toolchain` rule. Our
example has only a compiler, but other tools such as a linker could also be
grouped underneath it.

```python
def _bar_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        barcinfo = BarcInfo(
            compiler_path = ctx.attr.compiler_path,
            system_lib = ctx.attr.system_lib,
            arch_flags = ctx.attr.arch_flags,
        ),
    )
    return [toolchain_info]

bar_toolchain = rule(
    implementation = _bar_toolchain_impl,
    attrs = {
        "compiler_path": attr.string(),
        "system_lib": attr.string(),
        "arch_flags": attr.string_list(),
    },
)
```

The rule must return a `ToolchainInfo` provider, which becomes the object that
the consuming rule retrieves using `ctx.toolchains` and the label of the
toolchain type. `ToolchainInfo`, like `struct`, can hold arbitrary field-value
pairs. The specification of exactly what fields are added to the `ToolchainInfo`
should be clearly documented at the toolchain type. In this example, the values
return wrapped in a `BarcInfo` object to reuse the schema defined above; this
style may be useful for validation and code reuse.

Now you can define targets for specific `barc` compilers.

```python
bar_toolchain(
    name = "barc_linux",
    arch_flags = [
        "--arch=Linux",
        "--debug_everything",
    ],
    compiler_path = "/path/to/barc/on/linux",
    system_lib = "/usr/lib/libbarc.so",
)

bar_toolchain(
    name = "barc_windows",
    arch_flags = [
        "--arch=Windows",
        # Different flags, no debug support on windows.
    ],
    compiler_path = "C:\\path\\on\\windows\\barc.exe",
    system_lib = "C:\\path\\on\\windows\\barclib.dll",
)
```

Finally, you create `toolchain` definitions for the two `bar_toolchain` targets.
These definitions link the language-specific targets to the toolchain type and
provide the constraint information that tells Bazel when the toolchain is
appropriate for a given platform.

```python
toolchain(
    name = "barc_linux_toolchain",
    exec_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":barc_linux",
    toolchain_type = ":toolchain_type",
)

toolchain(
    name = "barc_windows_toolchain",
    exec_compatible_with = [
        "@platforms//os:windows",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:windows",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":barc_windows",
    toolchain_type = ":toolchain_type",
)
```

The use of relative path syntax above suggests these definitions are all in the
same package, but there's no reason the toolchain type, language-specific
toolchain targets, and `toolchain` definition targets can't all be in separate
packages.

See the [`go_toolchain`](https://github.com/bazelbuild/rules_go/blob/master/go/private/go_toolchain.bzl){: .external}
for a real-world example.

### Toolchains and configurations

An important question for rule authors is, when a `bar_toolchain` target is
analyzed, what [configuration](/reference/glossary#configuration) does it see, and what transitions
should be used for dependencies? The example above uses string attributes, but
what would happen for a more complicated toolchain that depends on other targets
in the Bazel repository?

Let's see a more complex version of `bar_toolchain`:

```python
def _bar_toolchain_impl(ctx):
    # The implementation is mostly the same as above, so skipping.
    pass

bar_toolchain = rule(
    implementation = _bar_toolchain_impl,
    attrs = {
        "compiler": attr.label(
            executable = True,
            mandatory = True,
            cfg = "exec",
        ),
        "system_lib": attr.label(
            mandatory = True,
            cfg = "target",
        ),
        "arch_flags": attr.string_list(),
    },
)
```

The use of [`attr.label`](/rules/lib/toplevel/attr#label) is the same as for a standard rule,
but the meaning of the `cfg` parameter is slightly different.

The dependency from a target (called the "parent") to a toolchain via toolchain
resolution uses a special configuration transition called the "toolchain
transition". The toolchain transition keeps the configuration the same, except
that it forces the execution platform to be the same for the toolchain as for
the parent (otherwise, toolchain resolution for the toolchain could pick any
execution platform, and wouldn't necessarily be the same as for parent). This
allows any `exec` dependencies of the toolchain to also be executable for the
parent's build actions. Any of the toolchain's dependencies which use `cfg =
"target"` (or which don't specify `cfg`, since "target" is the default) are
built for the same target platform as the parent. This allows toolchain rules to
contribute both libraries (the `system_lib` attribute above) and tools (the
`compiler` attribute) to the build rules which need them. The system libraries
are linked into the final artifact, and so need to be built for the same
platform, whereas the compiler is a tool invoked during the build, and needs to
be able to run on the execution platform.

## Registering and building with toolchains {:#registering-building-toolchains}

At this point all the building blocks are assembled, and you just need to make
the toolchains available to Bazel's resolution procedure. This is done by
registering the toolchain, either in a `MODULE.bazel` file using
`register_toolchains()`, or by passing the toolchains' labels on the command
line using the `--extra_toolchains` flag.

```python
register_toolchains(
    "//bar_tools:barc_linux_toolchain",
    "//bar_tools:barc_windows_toolchain",
    # Target patterns are also permitted, so you could have also written:
    # "//bar_tools:all",
    # or even
    # "//bar_tools/...",
)
```

When using target patterns to register toolchains, the order in which the
individual toolchains are registered is determined by the following rules:

* The toolchains defined in a subpackage of a package are registered before the
  toolchains defined in the package itself.
* Within a package, toolchains are registered in the lexicographical order of
  their names.

Now when you build a target that depends on a toolchain type, an appropriate
toolchain will be selected based on the target and execution platforms.

```python
# my_pkg/BUILD

platform(
    name = "my_target_platform",
    constraint_values = [
        "@platforms//os:linux",
    ],
)

bar_binary(
    name = "my_bar_binary",
    ...
)
```

```sh
bazel build //my_pkg:my_bar_binary --platforms=//my_pkg:my_target_platform
```

Bazel will see that `//my_pkg:my_bar_binary` is being built with a platform that
has `@platforms//os:linux` and therefore resolve the
`//bar_tools:toolchain_type` reference to `//bar_tools:barc_linux_toolchain`.
This will end up building `//bar_tools:barc_linux` but not
`//bar_tools:barc_windows`.

## Toolchain resolution {:#toolchain-resolution}

Note: [Some Bazel rules](/concepts/platforms#status) do not yet support
toolchain resolution.

For each target that uses toolchains, Bazel's toolchain resolution procedure
determines the target's concrete toolchain dependencies. The procedure takes as
input a set of required toolchain types, the target platform, the list of
available execution platforms, and the list of available toolchains. Its outputs
are a selected toolchain for each toolchain type as well as a selected execution
platform for the current target.

The available execution platforms and toolchains are gathered from the
external dependency graph via
[`register_execution_platforms`](/rules/lib/globals/module#register_execution_platforms)
and
[`register_toolchains`](/rules/lib/globals/module#register_toolchains) calls in
`MODULE.bazel` files.
Additional execution platforms and toolchains may also be specified on the
command line via
[`--extra_execution_platforms`](/reference/command-line-reference#flag--extra_execution_platforms)
and
[`--extra_toolchains`](/reference/command-line-reference#flag--extra_toolchains).
The host platform is automatically included as an available execution platform.
Available platforms and toolchains are tracked as ordered lists for determinism,
with preference given to earlier items in the list.

The set of available toolchains, in priority order, is created from
`--extra_toolchains` and `register_toolchains`:

1. Toolchains registered using `--extra_toolchains` are added first. (Within
   these, the **last** toolchain has highest priority.)
2. Toolchains registered using `register_toolchains` in the transitive external
   dependency graph, in the following order: (Within these, the **first**
   mentioned toolchain has highest priority.)
  1. Toolchains registered by the root module (as in, the `MODULE.bazel` at the
     workspace root);
  2. Toolchains registered in the user's `WORKSPACE` file, including in any
     macros invoked from there;
  3. Toolchains registered by non-root modules (as in, dependencies specified by
     the root module, and their dependencies, and so forth);
  4. Toolchains registered in the "WORKSPACE suffix"; this is only used by
     certain native rules bundled with the Bazel installation.

**NOTE:** [Pseudo-targets like `:all`, `:*`, and
`/...`](/run/build#specifying-build-targets) are ordered by Bazel's package
loading mechanism, which uses a lexicographic ordering.

The resolution steps are as follows.

1. A `target_compatible_with` or `exec_compatible_with` clause *matches* a
   platform if, for each `constraint_value` in its list, the platform also has
   that `constraint_value` (either explicitly or as a default).

   If the platform has `constraint_value`s from `constraint_setting`s not
   referenced by the clause, these do not affect matching.

1. If the target being built specifies the
   [`exec_compatible_with` attribute](/reference/be/common-definitions#common.exec_compatible_with)
   (or its rule definition specifies the
   [`exec_compatible_with` argument](/rules/lib/globals/bzl#rule.exec_compatible_with)),
   the list of available execution platforms is filtered to remove
   any that do not match the execution constraints.

1. The list of available toolchains is filtered to remove any toolchains
   specifying `target_settings` that don't match the current configuration.

1. For each available execution platform, you associate each toolchain type with
   the first available toolchain, if any, that is compatible with this execution
   platform and the target platform.

1. Any execution platform that failed to find a compatible mandatory toolchain
   for one of its toolchain types is ruled out. Of the remaining platforms, the
   first one becomes the current target's execution platform, and its associated
   toolchains (if any) become dependencies of the target.

The chosen execution platform is used to run all actions that the target
generates.

In cases where the same target can be built in multiple configurations (such as
for different CPUs) within the same build, the resolution procedure is applied
independently to each version of the target.

If the rule uses [execution groups](/extending/exec-groups), each execution
group performs toolchain resolution separately, and each has its own execution
platform and toolchains.

## Debugging toolchains {:#debugging-toolchains}

If you are adding toolchain support to an existing rule, use the
`--toolchain_resolution_debug=regex` flag. During toolchain resolution, the flag
provides verbose output for toolchain types or target names that match the regex variable. You
can use `.*` to output all information. Bazel will output names of toolchains it
checks and skips during the resolution process.

If you'd like to see which [`cquery`](/query/cquery) dependencies are from toolchain
resolution, use `cquery`'s [`--transitions`](/query/cquery#transitions) flag:

```
# Find all direct dependencies of //cc:my_cc_lib. This includes explicitly
# declared dependencies, implicit dependencies, and toolchain dependencies.
$ bazel cquery 'deps(//cc:my_cc_lib, 1)'
//cc:my_cc_lib (96d6638)
@bazel_tools//tools/cpp:toolchain (96d6638)
@bazel_tools//tools/def_parser:def_parser (HOST)
//cc:my_cc_dep (96d6638)
@local_config_platform//:host (96d6638)
@bazel_tools//tools/cpp:toolchain_type (96d6638)
//:default_host_platform (96d6638)
@local_config_cc//:cc-compiler-k8 (HOST)
//cc:my_cc_lib.cc (null)
@bazel_tools//tools/cpp:grep-includes (HOST)

# Which of these are from toolchain resolution?
$ bazel cquery 'deps(//cc:my_cc_lib, 1)' --transitions=lite | grep "toolchain dependency"
  [toolchain dependency]#@local_config_cc//:cc-compiler-k8#HostTransition -> b6df211
```


Project: /_project.yaml
Book: /_book.yaml
{# disableFinding("native") #}
{# disableFinding("Native") #}
{# disableFinding(LINE_OVER_80_LINK) #}

# Legacy Macros

{% include "_buttons.html" %}

Legacy macros are unstructured functions called from `BUILD` files that can
create targets. By the end of the
[loading phase](/extending/concepts#evaluation-model), legacy macros don't exist
anymore, and Bazel sees only the concrete set of instantiated rules.

## Why you shouldn't use legacy macros (and should use Symbolic macros instead) {:#no-legacy-macros}

Where possible you should use [symbolic macros](macros.md#macros).

Symbolic macros

*   Prevent action at a distance
*   Make it possible to hide implementation details through granular visibility
*   Take typed attributes, which in turn means automatic label and select
    conversion.
*   Are more readable
*   Will soon have [lazy evaluation](macros.md/laziness)

## Usage {:#usage}

The typical use case for a macro is when you want to reuse a rule.

For example, genrule in a `BUILD` file generates a file using `//:generator`
with a `some_arg` argument hardcoded in the command:

```python
genrule(
    name = "file",
    outs = ["file.txt"],
    cmd = "$(location //:generator) some_arg > $@",
    tools = ["//:generator"],
)
```

Note: `$@` is a
[Make variable](/reference/be/make-variables#predefined_genrule_variables) that
refers to the execution-time locations of the files in the `outs` attribute
list. It is equivalent to `$(locations :file.txt)`.

If you want to generate more files with different arguments, you may want to
extract this code to a macro function. To create a macro called
`file_generator`, which has `name` and `arg` parameters, we can replace the
genrule with the following:

```python
load("//path:generator.bzl", "file_generator")

file_generator(
    name = "file",
    arg = "some_arg",
)

file_generator(
    name = "file-two",
    arg = "some_arg_two",
)

file_generator(
    name = "file-three",
    arg = "some_arg_three",
)
```

Here, you load the `file_generator` symbol from a `.bzl` file located in the
`//path` package. By putting macro function definitions in a separate `.bzl`
file, you keep your `BUILD` files clean and declarative, The `.bzl` file can be
loaded from any package in the workspace.

Finally, in `path/generator.bzl`, write the definition of the macro to
encapsulate and parameterize the original genrule definition:

```python
def file_generator(name, arg, visibility=None):
  native.genrule(
    name = name,
    outs = [name + ".txt"],
    cmd = "$(location //:generator) %s > $@" % arg,
    tools = ["//:generator"],
    visibility = visibility,
  )
```

You can also use macros to chain rules together. This example shows chained
genrules, where a genrule uses the outputs of a previous genrule as inputs:

```python
def chained_genrules(name, visibility=None):
  native.genrule(
    name = name + "-one",
    outs = [name + ".one"],
    cmd = "$(location :tool-one) $@",
    tools = [":tool-one"],
    visibility = ["//visibility:private"],
  )

  native.genrule(
    name = name + "-two",
    srcs = [name + ".one"],
    outs = [name + ".two"],
    cmd = "$(location :tool-two) $< $@",
    tools = [":tool-two"],
    visibility = visibility,
  )
```

The example only assigns a visibility value to the second genrule. This allows
macro authors to hide the outputs of intermediate rules from being depended upon
by other targets in the workspace.

Note: Similar to `$@` for outputs, `$<` expands to the locations of files in the
`srcs` attribute list.

## Expanding macros {:#expanding-macros}

When you want to investigate what a macro does, use the `query` command with
`--output=build` to see the expanded form:

```none
$ bazel query --output=build :file
# /absolute/path/test/ext.bzl:42:3
genrule(
  name = "file",
  tools = ["//:generator"],
  outs = ["//test:file.txt"],
  cmd = "$(location //:generator) some_arg > $@",
)
```

## Instantiating native rules {:#instantiating-native-rules}

Native rules (rules that don't need a `load()` statement) can be instantiated
from the [native](/rules/lib/toplevel/native) module:

```python
def my_macro(name, visibility=None):
  native.cc_library(
    name = name,
    srcs = ["main.cc"],
    visibility = visibility,
  )
```

If you need to know the package name (for example, which `BUILD` file is calling
the macro), use the function
[native.package_name()](/rules/lib/toplevel/native#package_name). Note that
`native` can only be used in `.bzl` files, and not in `BUILD` files.

## Label resolution in macros {:#label-resolution}

Since legacy macros are evaluated in the
[loading phase](concepts.md#evaluation-model), label strings such as
`"//foo:bar"` that occur in a legacy macro are interpreted relative to the
`BUILD` file in which the macro is used rather than relative to the `.bzl` file
in which it is defined. This behavior is generally undesirable for macros that
are meant to be used in other repositories, such as because they are part of a
published Starlark ruleset.

To get the same behavior as for Starlark rules, wrap the label strings with the
[`Label`](/rules/lib/builtins/Label#Label) constructor:

```python
# @my_ruleset//rules:defs.bzl
def my_cc_wrapper(name, deps = [], **kwargs):
  native.cc_library(
    name = name,
    deps = deps + select({
      # Due to the use of Label, this label is resolved within @my_ruleset,
      # regardless of its site of use.
      Label("//config:needs_foo"): [
        # Due to the use of Label, this label will resolve to the correct target
        # even if the canonical name of @dep_of_my_ruleset should be different
        # in the main repo, such as due to repo mappings.
        Label("@dep_of_my_ruleset//tools:foo"),
      ],
      "//conditions:default": [],
    }),
    **kwargs,
  )
```

## Debugging {:#debugging}

*   `bazel query --output=build //my/path:all` will show you how the `BUILD`
    file looks after evaluation. All legacy macros, globs, loops are expanded.
    Known limitation: `select` expressions are not shown in the output.

*   You may filter the output based on `generator_function` (which function
    generated the rules) or `generator_name` (the name attribute of the macro):
    `bash $ bazel query --output=build 'attr(generator_function, my_macro,
    //my/path:all)'`

*   To find out where exactly the rule `foo` is generated in a `BUILD` file, you
    can try the following trick. Insert this line near the top of the `BUILD`
    file: `cc_library(name = "foo")`. Run Bazel. You will get an exception when
    the rule `foo` is created (due to a name conflict), which will show you the
    full stack trace.

*   You can also use [print](/rules/lib/globals/all#print) for debugging. It
    displays the message as a `DEBUG` log line during the loading phase. Except
    in rare cases, either remove `print` calls, or make them conditional under a
    `debugging` parameter that defaults to `False` before submitting the code to
    the depot.

## Errors {:#errors}

If you want to throw an error, use the [fail](/rules/lib/globals/all#fail)
function. Explain clearly to the user what went wrong and how to fix their
`BUILD` file. It is not possible to catch an error.

```python
def my_macro(name, deps, visibility=None):
  if len(deps) < 2:
    fail("Expected at least two values in deps")
  # ...
```

## Conventions {:#conventions}

*   All public functions (functions that don't start with underscore) that
    instantiate rules must have a `name` argument. This argument should not be
    optional (don't give a default value).

*   Public functions should use a docstring following
    [Python conventions](https://www.python.org/dev/peps/pep-0257/#one-line-docstrings).

*   In `BUILD` files, the `name` argument of the macros must be a keyword
    argument (not a positional argument).

*   The `name` attribute of rules generated by a macro should include the name
    argument as a prefix. For example, `macro(name = "foo")` can generate a
    `cc_library` `foo` and a genrule `foo_gen`.

*   In most cases, optional parameters should have a default value of `None`.
    `None` can be passed directly to native rules, which treat it the same as if
    you had not passed in any argument. Thus, there is no need to replace it
    with `0`, `False`, or `[]` for this purpose. Instead, the macro should defer
    to the rules it creates, as their defaults may be complex or may change over
    time. Additionally, a parameter that is explicitly set to its default value
    looks different than one that is never set (or set to `None`) when accessed
    through the query language or build-system internals.

*   Macros should have an optional `visibility` argument.


Project: /_project.yaml
Book: /_book.yaml
{# disableFinding("Currently") #}
{# disableFinding(TODO) #}

# Macros

{% include "_buttons.html" %}

This page covers the basics of using macros and includes typical use cases,
debugging, and conventions.

A macro is a function called from the `BUILD` file that can instantiate rules.
Macros are mainly used for encapsulation and code reuse of existing rules and
other macros.

Macros come in two flavors: symbolic macros, which are described on this page,
and [legacy macros](legacy-macros.md). Where possible, we recommend using
symbolic macros for code clarity.

Symbolic macros offer typed arguments (string to label conversion, relative to
where the macro was called) and the ability to restrict and specify the
visibility of targets created. They are designed to be amenable to lazy
evaluation (which will be added in a future Bazel release). Symbolic macros are
available by default in Bazel 8. Where this document mentions `macros`, it's
referring to **symbolic macros**.

An executable example of symbolic macros can be found in the
[examples repository](https://github.com/bazelbuild/examples/tree/main/macros).

## Usage {:#usage}

Macros are defined in `.bzl` files by calling the
[`macro()`](https://bazel.build/rules/lib/globals/bzl.html#macro) function with
two required parameters: `attrs` and `implementation`.

### Attributes {:#attributes}

`attrs` accepts a dictionary of attribute name to [attribute
types](https://bazel.build/rules/lib/toplevel/attr#members), which represents
the arguments to the macro. Two common attributes – `name` and `visibility` –
are implicitly added to all macros and are not included in the dictionary passed
to `attrs`.

```starlark
# macro/macro.bzl
my_macro = macro(
    attrs = {
        "deps": attr.label_list(mandatory = True, doc = "The dependencies passed to the inner cc_binary and cc_test targets"),
        "create_test": attr.bool(default = False, configurable = False, doc = "If true, creates a test target"),
    },
    implementation = _my_macro_impl,
)
```

Attribute type declarations accept the
[parameters](https://bazel.build/rules/lib/toplevel/attr#parameters),
`mandatory`, `default`, and `doc`. Most attribute types also accept the
`configurable` parameter, which determines wheher the attribute accepts
`select`s. If an attribute is `configurable`, it will parse non-`select` values
as an unconfigurable `select` – `"foo"` will become
`select({"//conditions:default": "foo"})`. Learn more in [selects](#selects).

#### Attribute inheritance {:#attribute-inheritance}

Macros are often intended to wrap a rule (or another macro), and the macro's
author often wants to forward the bulk of the wrapped symbol's attributes
unchanged, using `**kwargs`, to the macro's main target (or main inner macro).

To support this pattern, a macro can *inherit attributes* from a rule or another
macro by passing the [rule](https://bazel.build/rules/lib/builtins/rule) or
[macro symbol](https://bazel.build/rules/lib/builtins/macro) to `macro()`'s
`inherit_attrs` argument. (You can also use the special string `"common"`
instead of a rule or macro symbol to inherit the [common attributes defined for
all Starlark build
rules](https://bazel.build/reference/be/common-definitions#common-attributes).)
Only public attributes get inherited, and the attributes in the macro's own
`attrs` dictionary override inherited attributes with the same name. You can
also *remove* inherited attributes by using `None` as a value in the `attrs`
dictionary:

```starlark
# macro/macro.bzl
my_macro = macro(
    inherit_attrs = native.cc_library,
    attrs = {
        # override native.cc_library's `local_defines` attribute
        "local_defines": attr.string_list(default = ["FOO"]),
        # do not inherit native.cc_library's `defines` attribute
        "defines": None,
    },
    ...
)
```

The default value of non-mandatory inherited attributes is always overridden to
be `None`, regardless of the original attribute definition's default value. If
you need to examine or modify an inherited non-mandatory attribute – for
example, if you want to add a tag to an inherited `tags` attribute – you must
make sure to handle the `None` case in your macro's implementation function:

```starlark
# macro/macro.bzl
_my_macro_implementation(name, visibility, tags, **kwargs):
    # Append a tag; tags attr is an inherited non-mandatory attribute, and
    # therefore is None unless explicitly set by the caller of our macro.
    my_tags = (tags or []) + ["another_tag"]
    native.cc_library(
        ...
        tags = my_tags,
        **kwargs,
    )
    ...
```

### Implementation {:#implementation}

`implementation` accepts a function which contains the logic of the macro.
Implementation functions often create targets by calling one or more rules, and
they are usually private (named with a leading underscore). Conventionally,
they are named the same as their macro, but prefixed with `_` and suffixed with
`_impl`.

Unlike rule implementation functions, which take a single argument (`ctx`) that
contains a reference to the attributes, macro implementation functions accept a
parameter for each argument.

```starlark
# macro/macro.bzl
def _my_macro_impl(name, visibility, deps, create_test):
    cc_library(
        name = name + "_cc_lib",
        deps = deps,
    )

    if create_test:
        cc_test(
            name = name + "_test",
            srcs = ["my_test.cc"],
            deps = deps,
        )
```

If a macro inherits attributes, its implementation function *must* have a
`**kwargs` residual keyword parameter, which can be forwarded to the call that
invokes the inherited rule or submacro. (This helps ensure that your macro won't
be broken if the rule or macro which from which you are inheriting adds a new
attribute.)

### Declaration {:#declaration}

Macros are declared by loading and calling their definition in a `BUILD` file.

```starlark

# pkg/BUILD

my_macro(
    name = "macro_instance",
    deps = ["src.cc"] + select(
        {
            "//config_setting:special": ["special_source.cc"],
            "//conditions:default": [],
        },
    ),
    create_tests = True,
)
```

This would create targets
`//pkg:macro_instance_cc_lib` and`//pkg:macro_instance_test`.

Just like in rule calls, if an attribute value in a macro call is set to `None`,
that attribute is treated as if it was omitted by the macro's caller. For
example, the following two macro calls are equivalent:

```starlark
# pkg/BUILD
my_macro(name = "abc", srcs = ["src.cc"], deps = None)
my_macro(name = "abc", srcs = ["src.cc"])
```

This is generally not useful in `BUILD` files, but is helpful when
programmatically wrapping a macro inside another macro.

## Details {:#usage-details}

### Naming conventions for targets created {:#naming}

The names of any targets or submacros created by a symbolic macro must
either match the macro's `name` parameter or must be prefixed by `name` followed
by `_` (preferred), `.` or `-`. For example, `my_macro(name = "foo")` may only
create files or targets named `foo`, or prefixed by `foo_`, `foo-` or `foo.`,
for example, `foo_bar`.

Targets or files that violate macro naming convention can be declared, but
cannot be built and cannot be used as dependencies.

Non-macro files and targets within the same package as a macro instance should
*not* have names that conflict with potential macro target names, though this
exclusivity is not enforced. We are in the progress of implementing
[lazy evaluation](#laziness) as a performance improvement for Symbolic macros,
which will be impaired in packages that violate the naming schema.

### Restrictions {:#restrictions}

Symbolic macros have some additional restrictions compared to legacy macros.

Symbolic macros

*   must take a `name` argument and a `visibility` argument
*   must have an `implementation` function
*   may not return values
*   may not mutate their arguments
*   may not call `native.existing_rules()` unless they are special `finalizer`
    macros
*   may not call `native.package()`
*   may not call `glob()`
*   may not call `native.environment_group()`
*   must create targets whose names adhere to the [naming schema](#naming)
*   can't refer to input files that weren't declared or passed in as an argument
*   can't refer to private targets of their callers (see
    [visibility and macros](#visibility) for more details).

### Visibility and macros {:#visibility}

The [visibility](/concepts/visibility) system helps protect the implementation
details of both (symbolic) macros and their callers.

By default, targets created in a symbolic macro are visible within the macro
itself, but not necessarily to the macro's caller. The macro can "export" a
target as a public API by forwarding the value of its own `visibility`
attribute, as in `some_rule(..., visibility = visibility)`.

The key ideas of macro visibility are:

1. Visibility is checked based on what macro declared the target, not what
   package called the macro.

   * In other words, being in the same package does not by itself make one
     target visible to another. This protects the macro's internal targets
     from becoming dependencies of other macros or top-level targets in the
     package.

1. All `visibility` attributes, on both rules and macros, automatically
   include the place where the rule or macro was called.

   * Thus, a target is unconditionally visible to other targets declared in the
     same macro (or the `BUILD` file, if not in a macro).

In practice, this means that when a macro declares a target without setting its
`visibility`, the target defaults to being internal to the macro. (The package's
[default visibility](/reference/be/functions#package.default_visibility) does
not apply within a macro.) Exporting the target means that the target is visible
to whatever the macro's caller specified in the macro's `visibility` attribute,
plus the package of the macro's caller itself, as well as the macro's own code.
Another way of thinking of it is that the visibility of a macro determines who
(aside from the macro itself) can see the macro's exported targets.

```starlark
# tool/BUILD
...
some_rule(
    name = "some_tool",
    visibility = ["//macro:__pkg__"],
)
```

```starlark
# macro/macro.bzl

def _impl(name, visibility):
    cc_library(
        name = name + "_helper",
        ...
        # No visibility passed in. Same as passing `visibility = None` or
        # `visibility = ["//visibility:private"]`. Visible to the //macro
        # package only.
    )
    cc_binary(
        name = name + "_exported",
        deps = [
            # Allowed because we're also in //macro. (Targets in any other
            # instance of this macro, or any other macro in //macro, can see it
            # too.)
            name + "_helper",
            # Allowed by some_tool's visibility, regardless of what BUILD file
            # we're called from.
            "//tool:some_tool",
        ],
        ...
        visibility = visibility,
    )

my_macro = macro(implementation = _impl, ...)
```

```starlark
# pkg/BUILD
load("//macro:macro.bzl", "my_macro")
...

my_macro(
    name = "foo",
    ...
)

some_rule(
    ...
    deps = [
        # Allowed, its visibility is ["//pkg:__pkg__", "//macro:__pkg__"].
        ":foo_exported",
        # Disallowed, its visibility is ["//macro:__pkg__"] and
        # we are not in //macro.
        ":foo_helper",
    ]
)
```

If `my_macro` were called with `visibility = ["//other_pkg:__pkg__"]`, or if
the `//pkg` package had set its `default_visibility` to that value, then
`//pkg:foo_exported` could also be used within `//other_pkg/BUILD` or within a
macro defined in `//other_pkg:defs.bzl`, but `//pkg:foo_helper` would remain
protected.

A macro can declare that a target is visible to a friend package by passing
`visibility = ["//some_friend:__pkg__"]` (for an internal target) or
`visibility = visibility + ["//some_friend:__pkg__"]` (for an exported one).
Note that it is an antipattern for a macro to declare a target with public
visibility (`visibility = ["//visibility:public"]`). This is because it makes
the target unconditionally visible to every package, even if the caller
specified a more restricted visibility.

All visibility checking is done with respect to the innermost currently running
symbolic macro. However, there is a visibility delegation mechanism: If a macro
passes a label as an attribute value to an inner macro, any usages of the label
in the inner macro are checked with respect to the outer macro. See the
[visibility page](/concepts/visibility#symbolic-macros) for more details.

Remember that legacy macros are entirely transparent to the visibility system,
and behave as though their location is whatever BUILD file or symbolic macro
they were called from.

#### Finalizers and visibility {:#finalizers-and-visibility}

Targets declared in a rule finalizer, in addition to seeing targets following
the usual symbolic macro visibility rules, can *also* see all targets which are
visible to the finalizer target's package.

This means that if you migrate a `native.existing_rules()`-based legacy macro to
a finalizer, the targets declared by the finalizer will still be able to see
their old dependencies.

However, note that it's possible to declare a target in a symbolic macro such
that a finalizer's targets cannot see it under the visibility system – even
though the finalizer can *introspect* its attributes using
`native.existing_rules()`.

### Selects {:#selects}

If an attribute is `configurable` (the default) and its value is not `None`,
then the macro implementation function will see the attribute value as wrapped
in a trivial `select`. This makes it easier for the macro author to catch bugs
where they did not anticipate that the attribute value could be a `select`.

For example, consider the following macro:

```starlark
my_macro = macro(
    attrs = {"deps": attr.label_list()},  # configurable unless specified otherwise
    implementation = _my_macro_impl,
)
```

If `my_macro` is invoked with `deps = ["//a"]`, that will cause `_my_macro_impl`
to be invoked with its `deps` parameter set to `select({"//conditions:default":
["//a"]})`. If this causes the implementation function to fail (say, because the
code tried to index into the value as in `deps[0]`, which is not allowed for
`select`s), the macro author can then make a choice: either they can rewrite
their macro to only use operations compatible with `select`, or they can mark
the attribute as nonconfigurable (`attr.label_list(configurable = False)`). The
latter ensures that users are not permitted to pass a `select` value in.

Rule targets reverse this transformation, and store trivial `select`s as their
unconditional values; in the above example, if `_my_macro_impl` declares a rule
target `my_rule(..., deps = deps)`, that rule target's `deps` will be stored as
`["//a"]`. This ensures that `select`-wrapping does not cause trivial `select`
values to be stored in all targets instantiated by macros.

If the value of a configurable attribute is `None`, it does not get wrapped in a
`select`. This ensures that tests like `my_attr == None` still work, and that
when the attribute is forwarded to a rule with a computed default, the rule
behaves properly (that is, as if the attribute were not passed in at all). It is
not always possible for an attribute to take on a `None` value, but it can
happen for the `attr.label()` type, and for any inherited non-mandatory
attribute.

## Finalizers {:#finalizers}

A rule finalizer is a special symbolic macro which – regardless of its lexical
position in a BUILD file – is evaluated in the final stage of loading a package,
after all non-finalizer targets have been defined. Unlike ordinary symbolic
macros, a finalizer can call `native.existing_rules()`, where it behaves
slightly differently than in legacy macros: it only returns the set of
non-finalizer rule targets. The finalizer may assert on the state of that set or
define new targets.

To declare a finalizer, call `macro()` with `finalizer = True`:

```starlark
def _my_finalizer_impl(name, visibility, tags_filter):
    for r in native.existing_rules().values():
        for tag in r.get("tags", []):
            if tag in tags_filter:
                my_test(
                    name = name + "_" + r["name"] + "_finalizer_test",
                    deps = [r["name"]],
                    data = r["srcs"],
                    ...
                )
                continue

my_finalizer = macro(
    attrs = {"tags_filter": attr.string_list(configurable = False)},
    implementation = _impl,
    finalizer = True,
)
```

## Laziness {:#laziness}

IMPORTANT: We are in the process of implementing lazy macro expansion and
evaluation. This feature is not available yet.

Currently, all macros are evaluated as soon as the BUILD file is loaded, which
can negatively impact performance for targets in packages that also have costly
unrelated macros. In the future, non-finalizer symbolic macros will only be
evaluated if they're required for the build. The prefix naming schema helps
Bazel determine which macro to expand given a requested target.

## Migration troubleshooting {:#troubleshooting}

Here are some common migration headaches and how to fix them.

*   Legacy macro calls `glob()`

Move the `glob()` call to your BUILD file (or to a legacy macro called from the
BUILD file), and pass the `glob()` value to the symbolic macro using a
label-list attribute:

```starlark
# BUILD file
my_macro(
    ...,
    deps = glob(...),
)
```

*   Legacy macro has a parameter that isn't a valid starlark `attr` type.

Pull as much logic as possible into a nested symbolic macro, but keep the
top level macro a legacy macro.

*  Legacy macro calls a rule that creates a target that breaks the naming schema

That's okay, just don't depend on the "offending" target. The naming check will
be quietly ignored.



Project: /_project.yaml
Book: /_book.yaml

# Depsets

{% include "_buttons.html" %}

[Depsets](/rules/lib/builtins/depset) are a specialized data structure for efficiently
collecting data across a target’s transitive dependencies. They are an essential
element of rule processing.

The defining feature of depset is its time- and space-efficient union operation.
The depset constructor accepts a list of elements ("direct") and a list of other
depsets ("transitive"), and returns a depset representing a set containing all the
direct elements and the union of all the transitive sets. Conceptually, the
constructor creates a new graph node that has the direct and transitive nodes
as its successors. Depsets have a well-defined ordering semantics, based on
traversal of this graph.

Example uses of depsets include:

*   Storing the paths of all object files for a program’s libraries, which can
    then be passed to a linker action through a provider.

*   For an interpreted language, storing the transitive source files that are
    included in an executable's runfiles.

## Description and operations

Conceptually, a depset is a directed acyclic graph (DAG) that typically looks
similar to the target graph. It is constructed from the leaves up to the root.
Each target in a dependency chain can add its own contents on top of the
previous without having to read or copy them.

Each node in the DAG holds a list of direct elements and a list of child nodes.
The contents of the depset are the transitive elements, such as the direct elements
of all the nodes. A new depset can be created using the
[depset](/rules/lib/globals/bzl#depset) constructor: it accepts a list of direct
elements and another list of child nodes.

```python
s = depset(["a", "b", "c"])
t = depset(["d", "e"], transitive = [s])

print(s)    # depset(["a", "b", "c"])
print(t)    # depset(["d", "e", "a", "b", "c"])
```

To retrieve the contents of a depset, use the
[to_list()](/rules/lib/builtins/depset#to_list) method. It returns a list of all transitive
elements, not including duplicates. There is no way to directly inspect the
precise structure of the DAG, although this structure does affect the order in
which the elements are returned.

```python
s = depset(["a", "b", "c"])

print("c" in s.to_list())              # True
print(s.to_list() == ["a", "b", "c"])  # True
```

The allowed items in a depset are restricted, just as the allowed keys in
dictionaries are restricted. In particular, depset contents may not be mutable.

Depsets use reference equality: a depset is equal to itself, but unequal to any
other depset, even if they have the same contents and same internal structure.

```python
s = depset(["a", "b", "c"])
t = s
print(s == t)  # True

t = depset(["a", "b", "c"])
print(s == t)  # False

d = {}
d[s] = None
d[t] = None
print(len(d))  # 2
```

To compare depsets by their contents, convert them to sorted lists.

```python
s = depset(["a", "b", "c"])
t = depset(["c", "b", "a"])
print(sorted(s.to_list()) == sorted(t.to_list()))  # True
```

There is no ability to remove elements from a depset. If this is needed, you
must read out the entire contents of the depset, filter the elements you want to
remove, and reconstruct a new depset. This is not particularly efficient.

```python
s = depset(["a", "b", "c"])
t = depset(["b", "c"])

# Compute set difference s - t. Precompute t.to_list() so it's not done
# in a loop, and convert it to a dictionary for fast membership tests.
t_items = {e: None for e in t.to_list()}
diff_items = [x for x in s.to_list() if x not in t_items]
# Convert back to depset if it's still going to be used for union operations.
s = depset(diff_items)
print(s)  # depset(["a"])
```

### Order

The `to_list` operation performs a traversal over the DAG. The kind of traversal
depends on the *order* that was specified at the time the depset was
constructed. It is useful for Bazel to support multiple orders because sometimes
tools care about the order of their inputs. For example, a linker action may
need to ensure that if `B` depends on `A`, then `A.o` comes before `B.o` on the
linker’s command line. Other tools might have the opposite requirement.

Three traversal orders are supported: `postorder`, `preorder`, and
`topological`. The first two work exactly like [tree
traversals](https://en.wikipedia.org/wiki/Tree_traversal#Depth-first_search)
except that they operate on DAGs and skip already visited nodes. The third order
works as a topological sort from root to leaves, essentially the same as
preorder except that shared children are listed only after all of their parents.
Preorder and postorder operate as left-to-right traversals, but note that within
each node direct elements have no order relative to children. For topological
order, there is no left-to-right guarantee, and even the
all-parents-before-child guarantee does not apply in the case that there are
duplicate elements in different nodes of the DAG.

```python
# This demonstrates different traversal orders.

def create(order):
  cd = depset(["c", "d"], order = order)
  gh = depset(["g", "h"], order = order)
  return depset(["a", "b", "e", "f"], transitive = [cd, gh], order = order)

print(create("postorder").to_list())  # ["c", "d", "g", "h", "a", "b", "e", "f"]
print(create("preorder").to_list())   # ["a", "b", "e", "f", "c", "d", "g", "h"]
```

```python
# This demonstrates different orders on a diamond graph.

def create(order):
  a = depset(["a"], order=order)
  b = depset(["b"], transitive = [a], order = order)
  c = depset(["c"], transitive = [a], order = order)
  d = depset(["d"], transitive = [b, c], order = order)
  return d

print(create("postorder").to_list())    # ["a", "b", "c", "d"]
print(create("preorder").to_list())     # ["d", "b", "a", "c"]
print(create("topological").to_list())  # ["d", "b", "c", "a"]
```

Due to how traversals are implemented, the order must be specified at the time
the depset is created with the constructor’s `order` keyword argument. If this
argument is omitted, the depset has the special `default` order, in which case
there are no guarantees about the order of any of its elements (except that it
is deterministic).

## Full example

This example is available at
[https://github.com/bazelbuild/examples/tree/main/rules/depsets](https://github.com/bazelbuild/examples/tree/main/rules/depsets).

Suppose there is a hypothetical interpreted language Foo. In order to build
each `foo_binary` you need to know all the `*.foo` files that it directly or
indirectly depends on.

```python
# //depsets:BUILD

load(":foo.bzl", "foo_library", "foo_binary")

# Our hypothetical Foo compiler.
py_binary(
    name = "foocc",
    srcs = ["foocc.py"],
)

foo_library(
    name = "a",
    srcs = ["a.foo", "a_impl.foo"],
)

foo_library(
    name = "b",
    srcs = ["b.foo", "b_impl.foo"],
    deps = [":a"],
)

foo_library(
    name = "c",
    srcs = ["c.foo", "c_impl.foo"],
    deps = [":a"],
)

foo_binary(
    name = "d",
    srcs = ["d.foo"],
    deps = [":b", ":c"],
)
```

```python
# //depsets:foocc.py

# "Foo compiler" that just concatenates its inputs to form its output.
import sys

if __name__ == "__main__":
  assert len(sys.argv) >= 1
  output = open(sys.argv[1], "wt")
  for path in sys.argv[2:]:
    input = open(path, "rt")
    output.write(input.read())
```

Here, the transitive sources of the binary `d` are all of the `*.foo` files in
the `srcs` fields of `a`, `b`, `c`, and `d`. In order for the `foo_binary`
target to know about any file besides `d.foo`, the `foo_library` targets need to
pass them along in a provider. Each library receives the providers from its own
dependencies, adds its own immediate sources, and passes on a new provider with
the augmented contents. The `foo_binary` rule does the same, except that instead
of returning a provider, it uses the complete list of sources to construct a
command line for an action.

Here’s a complete implementation of the `foo_library` and `foo_binary` rules.

```python
# //depsets/foo.bzl

# A provider with one field, transitive_sources.
FooFiles = provider(fields = ["transitive_sources"])

def get_transitive_srcs(srcs, deps):
  """Obtain the source files for a target and its transitive dependencies.

  Args:
    srcs: a list of source files
    deps: a list of targets that are direct dependencies
  Returns:
    a collection of the transitive sources
  """
  return depset(
        srcs,
        transitive = [dep[FooFiles].transitive_sources for dep in deps])

def _foo_library_impl(ctx):
  trans_srcs = get_transitive_srcs(ctx.files.srcs, ctx.attr.deps)
  return [FooFiles(transitive_sources=trans_srcs)]

foo_library = rule(
    implementation = _foo_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files=True),
        "deps": attr.label_list(),
    },
)

def _foo_binary_impl(ctx):
  foocc = ctx.executable._foocc
  out = ctx.outputs.out
  trans_srcs = get_transitive_srcs(ctx.files.srcs, ctx.attr.deps)
  srcs_list = trans_srcs.to_list()
  ctx.actions.run(executable = foocc,
                  arguments = [out.path] + [src.path for src in srcs_list],
                  inputs = srcs_list + [foocc],
                  outputs = [out])

foo_binary = rule(
    implementation = _foo_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files=True),
        "deps": attr.label_list(),
        "_foocc": attr.label(default=Label("//depsets:foocc"),
                             allow_files=True, executable=True, cfg="host")
    },
    outputs = {"out": "%{name}.out"},
)
```

You can test this by copying these files into a fresh package, renaming the
labels appropriately, creating the source `*.foo` files with dummy content, and
building the `d` target.


## Performance

To see the motivation for using depsets, consider what would happen if
`get_transitive_srcs()` collected its sources in a list.

```python
def get_transitive_srcs(srcs, deps):
  trans_srcs = []
  for dep in deps:
    trans_srcs += dep[FooFiles].transitive_sources
  trans_srcs += srcs
  return trans_srcs
```

This does not take into account duplicates, so the source files for `a`
will appear twice on the command line and twice in the contents of the output
file.

An alternative is using a general set, which can be simulated by a
dictionary where the keys are the elements and all the keys map to `True`.

```python
def get_transitive_srcs(srcs, deps):
  trans_srcs = {}
  for dep in deps:
    for file in dep[FooFiles].transitive_sources:
      trans_srcs[file] = True
  for file in srcs:
    trans_srcs[file] = True
  return trans_srcs
```

This gets rid of the duplicates, but it makes the order of the command line
arguments (and therefore the contents of the files) unspecified, although still
deterministic.

Moreover, both approaches are asymptotically worse than the depset-based
approach. Consider the case where there is a long chain of dependencies on
Foo libraries. Processing every rule requires copying all of the transitive
sources that came before it into a new data structure. This means that the
time and space cost for analyzing an individual library or binary target
is proportional to its own height in the chain. For a chain of length n,
foolib_1 ← foolib_2 ← … ← foolib_n, the overall cost is effectively O(n^2).

Generally speaking, depsets should be used whenever you are accumulating
information through your transitive dependencies. This helps ensure that
your build scales well as your target graph grows deeper.

Finally, it’s important to not retrieve the contents of the depset
unnecessarily in rule implementations. One call to `to_list()`
at the end in a binary rule is fine, since the overall cost is just O(n). It’s
when many non-terminal targets try to call `to_list()` that quadratic behavior
occurs.

For more information about using depsets efficiently, see the [performance](/rules/performance) page.

## API Reference

Please see [here](/rules/lib/builtins/depset) for more details.



Project: /_project.yaml
Book: /_book.yaml

# Automatic Execution Groups (AEGs)

{% include "_buttons.html" %}

Automatic execution groups select an [execution platform][exec_platform]
for each toolchain type. In other words, one target can have multiple
execution platforms without defining execution groups.

## Quick summary {:#quick-summary}

Automatic execution groups are closely connected to toolchains. If you are using
toolchains, you need to set them on the affected actions (actions which use an
executable or a tool from a toolchain) by adding `toolchain` parameter. For
example:

```python
ctx.actions.run(
    ...,
    executable = ctx.toolchain['@bazel_tools//tools/jdk:toolchain_type'].tool,
    ...,
    toolchain = '@bazel_tools//tools/jdk:toolchain_type',
)
```
If the action does not use a tool or executable from a toolchain, and Blaze
doesn't detect that ([the error](#first-error-message) is raised), you can set
`toolchain = None`.

If you need to use multiple toolchains on a single execution platform (an action
uses executable or tools from two or more toolchains), you need to manually
define [exec_groups][exec_groups] (check
[When should I use a custom exec_group?][multiple_toolchains_exec_groups]
section).

## History {:#history}

Before AEGs, the execution platform was selected on a rule level. For example:

```python
my_rule = rule(
    _impl,
    toolchains = ['//tools:toolchain_type_1', '//tools:toolchain_type_2'],
)
```

Rule `my_rule` registers two toolchain types. This means that the [Toolchain
Resolution](https://bazel.build/extending/toolchains#toolchain-resolution) used
to find an execution platform which supports both toolchain types. The selected
execution platform was used for each registered action inside the rule, unless
specified differently with [exec_groups][exec_groups].
In other words, all actions inside the rule used to have a single execution
platform even if they used tools from different toolchains (execution platform
is selected for each target). This resulted in failures when there was no
execution platform supporting all toolchains.

## Current state {:#current-state}

With AEGs, the execution platform is selected for each toolchain type. The
implementation function of the earlier example, `my_rule`, would look like:

```python
def _impl(ctx):
    ctx.actions.run(
      mnemonic = "First action",
      executable = ctx.toolchain['//tools:toolchain_type_1'].tool,
      toolchain = '//tools:toolchain_type_1',
    )

    ctx.actions.run(
      mnemonic = "Second action",
      executable = ctx.toolchain['//tools:toolchain_type_2'].tool,
      toolchain = '//tools:toolchain_type_2',
    )
```

This rule creates two actions, the `First action` which uses executable from a
`//tools:toolchain_type_1` and the `Second action` which uses executable from a
`//tools:toolchain_type_2`. Before AEGs, both of these actions would be executed
on a single execution platform which supports both toolchain types. With AEGs,
by adding the `toolchain` parameter inside the actions, each action executes on
the execution platform that provides the toolchain. The actions may be executed
on different execution platforms.

The same is effective with [ctx.actions.run_shell][run_shell] where `toolchain`
parameter should be added when `tools` are from a toolchain.

## Difference between custom exec groups and automatic exec groups {:#difference-custom}

As the name suggests, AEGs are exec groups created automatically for each
toolchain type registered on a rule. There is no need to manually specify them,
unlike the "classic" exec groups.

### When should I use a custom exec_group? {:#when-should-use-exec-groups}

Custom exec_groups are needed only in case where multiple toolchains need to
execute on a single execution platform. In all other cases there's no need to
define custom exec_groups. For example:

```python
def _impl(ctx):
    ctx.actions.run(
      ...,
      executable = ctx.toolchain['//tools:toolchain_type_1'].tool,
      tools = [ctx.toolchain['//tools:toolchain_type_2'].tool],
      exec_group = 'two_toolchains',
    )
```

```python
my_rule = rule(
    _impl,
    exec_groups = {
        "two_toolchains": exec_group(
            toolchains = ['//tools:toolchain_type_1', '//tools:toolchain_type_2'],
        ),
    }
)
```

## Migration of AEGs {:#migration-aegs}

Internally in google3, Blaze is already using AEGs.
Externally for Bazel, migration is in the process. Some rules are already using
this feature (e.g. Java and C++ rules).

### Which Bazel versions support this migration? {:#which-bazel}

AEGs are fully supported from Bazel 7.

### How to enable AEGs? {:#how-enable}

Set `--incompatible_auto_exec_groups` to true. More information about the flag
on [the GitHub issue][github_flag].

### How to enable AEGs inside a particular rule? {:#how-enable-particular-rule}

Set the `_use_auto_exec_groups` attribute on a rule.

```python
my_rule = rule(
    _impl,
    attrs = {
      "_use_auto_exec_groups": attr.bool(default = True),
    }
)
```
This enables AEGs only in `my_rule` and its actions start using the new logic
when selecting the execution platform. Incompatible flag is overridden with this
attribute.

### How to disable AEGs in case of an error? {:#how-disable}

Set `--incompatible_auto_exec_groups` to false to completely disable AEGs in
your project ([flag's GitHub issue][github_flag]), or disable a particular rule
by setting `_use_auto_exec_groups` attribute to `False`
([more details about the attribute](#how-enable-particular-rule)).

### Error messages while migrating to AEGs {:#potential-problems}

#### Couldn't identify if tools are from implicit dependencies or a toolchain. Please set the toolchain parameter. If you're not using a toolchain, set it to 'None'. {:#first-error-message}
  * In this case you get a stack of calls before the error happened and you can
    clearly see which exact action needs the toolchain parameter. Check which
    toolchain is used for the action and set it with the toolchain param. If no
    toolchain is used inside the action for tools or executable, set it to
    `None`.

#### Action declared for non-existent toolchain '[toolchain_type]'.
  * This means that you've set the toolchain parameter on the action but didn't
register it on the rule. Register the toolchain or set `None` inside the action.

## Additional material {:#additional-material}

For more information, check design document:
[Automatic exec groups for toolchains][aegs_design_doc].

[exec_platform]: https://bazel.build/extending/platforms#:~:text=Execution%20%2D%20a%20platform%20on%20which%20build%20tools%20execute%20build%20actions%20to%20produce%20intermediate%20and%20final%20outputs.
[exec_groups]: https://bazel.build/extending/exec-groups
[github_flag]: https://github.com/bazelbuild/bazel/issues/17134
[aegs_design_doc]: https://docs.google.com/document/d/1-rbP_hmKs9D639YWw5F_JyxPxL2bi6dSmmvj_WXak9M/edit#heading=h.5mcn15i0e1ch
[run_shell]: https://bazel.build/rules/lib/builtins/actions#run_shell
[multiple_toolchains_exec_groups]: /extending/auto-exec-groups#when-should-use-exec-groups

Project: /_project.yaml
Book: /_book.yaml

# Extension Overview

{% include "_buttons.html" %}

<!-- [TOC] -->

This page describes how to extend the BUILD language using macros
and rules.

Bazel extensions are files ending in `.bzl`. Use a
[load statement](/concepts/build-files#load) to import a symbol from an extension.

Before learning the more advanced concepts, first:

* Read about the [Starlark language](/rules/language), used in both the
  `BUILD` and `.bzl` files.

* Learn how you can [share variables](/build/share-variables)
  between two `BUILD` files.

## Macros and rules {:#macros-and-rules}

A macro is a function that instantiates rules. Macros come in two flavors:
[symbolic macros](/extending/macros) (new in Bazel 8) and [legacy
macros](/extending/legacy-macros). The two flavors of macros are defined
differently, but behave almost the same from the point of view of a user. A
macro is useful when a `BUILD` file is getting too repetitive or too complex, as
it lets you reuse some code. The function is evaluated as soon as the `BUILD`
file is read. After the evaluation of the `BUILD` file, Bazel has little
information about macros. If your macro generates a `genrule`, Bazel will
behave *almost* as if you declared that `genrule` in the `BUILD` file. (The one
exception is that targets declared in a symbolic macro have [special visibility
semantics](/extending/macros#visibility): a symbolic macro can hide its internal
targets from the rest of the package.)

A [rule](/extending/rules) is more powerful than a macro. It can access Bazel
internals and have full control over what is going on. It may for example pass
information to other rules.

If you want to reuse simple logic, start with a macro; we recommend a symbolic
macro, unless you need to support older Bazel versions. If a macro becomes
complex, it is often a good idea to make it a rule. Support for a new language
is typically done with a rule. Rules are for advanced users, and most users will
never have to write one; they will only load and call existing rules.

## Evaluation model {:#evaluation-model}

A build consists of three phases.

* **Loading phase**. First, load and evaluate all extensions and all `BUILD`
  files that are needed for the build. The execution of the `BUILD` files simply
  instantiates rules (each time a rule is called, it gets added to a graph).
  This is where macros are evaluated.

* **Analysis phase**. The code of the rules is executed (their `implementation`
  function), and actions are instantiated. An action describes how to generate
  a set of outputs from a set of inputs, such as "run gcc on hello.c and get
  hello.o". You must list explicitly which files will be generated before
  executing the actual commands. In other words, the analysis phase takes
  the graph generated by the loading phase and generates an action graph.

* **Execution phase**. Actions are executed, when at least one of their outputs is
  required. If a file is missing or if a command fails to generate one output,
  the build fails. Tests are also run during this phase.

Bazel uses parallelism to read, parse and evaluate the `.bzl` files and `BUILD`
files. A file is read at most once per build and the result of the evaluation is
cached and reused. A file is evaluated only once all its dependencies (`load()`
statements) have been resolved. By design, loading a `.bzl` file has no visible
side-effect, it only defines values and functions.

Bazel tries to be clever: it uses dependency analysis to know which files must
be loaded, which rules must be analyzed, and which actions must be executed. For
example, if a rule generates actions that you don't need for the current build,
they will not be executed.

## Creating extensions

* [Create your first macro](/rules/macro-tutorial) in order to reuse some code.
  Then [learn more about macros](/extending/macros) and [using them to create
  "custom verbs"](/rules/verbs-tutorial).

* [Follow the rules tutorial](/rules/rules-tutorial) to get started with rules.
  Next, you can read more about the [rules concepts](/extending/rules).

The two links below will be very useful when writing your own extensions. Keep
them within reach:

* The [API reference](/rules/lib)

* [Examples](https://github.com/bazelbuild/examples/tree/master/rules)

## Going further

In addition to [macros](/extending/macros) and [rules](/extending/rules), you
may want to write [aspects](/extending/aspects) and [repository
rules](/external/repo).

* Use [Buildifier](https://github.com/bazelbuild/buildtools){: .external}
  consistently to format and lint your code.

* Follow the [`.bzl` style guide](/rules/bzl-style).

* [Test](/rules/testing) your code.

* [Generate documentation](https://skydoc.bazel.build/) to help your users.

* [Optimize the performance](/rules/performance) of your code.

* [Deploy](/rules/deploying) your extensions to other people.


Project: /_project.yaml
Book: /_book.yaml

# Aspects

{% include "_buttons.html" %}

This page explains the basics and benefits of using
[aspects](/rules/lib/globals/bzl#aspect) and provides simple and advanced
examples.

Aspects allow augmenting build dependency graphs with additional information
and actions. Some typical scenarios when aspects can be useful:

*   IDEs that integrate Bazel can use aspects to collect information about the
    project.
*   Code generation tools can leverage aspects to execute on their inputs in
    *target-agnostic* manner. As an example, `BUILD` files can specify a hierarchy
    of [protobuf](https://developers.google.com/protocol-buffers/) library
    definitions, and language-specific rules can use aspects to attach
    actions generating protobuf support code for a particular language.

## Aspect basics

`BUILD` files provide a description of a project’s source code: what source
files are part of the project, what artifacts (_targets_) should be built from
those files, what the dependencies between those files are, etc. Bazel uses
this information to perform a build, that is, it figures out the set of actions
needed to produce the artifacts (such as running compiler or linker) and
executes those actions. Bazel accomplishes this by constructing a _dependency
graph_ between targets and visiting this graph to collect those actions.

Consider the following `BUILD` file:

```python
java_library(name = 'W', ...)
java_library(name = 'Y', deps = [':W'], ...)
java_library(name = 'Z', deps = [':W'], ...)
java_library(name = 'Q', ...)
java_library(name = 'T', deps = [':Q'], ...)
java_library(name = 'X', deps = [':Y',':Z'], runtime_deps = [':T'], ...)
```

This `BUILD` file defines a dependency graph shown in the following figure:

![Build graph](/rules/build-graph.png "Build graph")

**Figure 1.** `BUILD` file dependency graph.

Bazel analyzes this dependency graph by calling an implementation function of
the corresponding [rule](/extending/rules) (in this case "java_library") for every
target in the above example. Rule implementation functions generate actions that
build artifacts, such as `.jar` files, and pass information, such as locations
and names of those artifacts, to the reverse dependencies of those targets in
[providers](/extending/rules#providers).

Aspects are similar to rules in that they have an implementation function that
generates actions and returns providers. However, their power comes from
the way the dependency graph is built for them. An aspect has an implementation
and a list of all attributes it propagates along. Consider an aspect A that
propagates along attributes named "deps". This aspect can be applied to
a target X, yielding an aspect application node A(X). During its application,
aspect A is applied recursively to all targets that X refers to in its "deps"
attribute (all attributes in A's propagation list).

Thus a single act of applying aspect A to a target X yields a "shadow graph" of
the original dependency graph of targets shown in the following figure:

![Build Graph with Aspect](/rules/build-graph-aspects.png "Build graph with aspects")

**Figure 2.** Build graph with aspects.

The only edges that are shadowed are the edges along the attributes in
the propagation set, thus the `runtime_deps` edge is not shadowed in this
example. An aspect implementation function is then invoked on all nodes in
the shadow graph similar to how rule implementations are invoked on the nodes
of the original graph.

## Simple example

This example demonstrates how to recursively print the source files for a
rule and all of its dependencies that have a `deps` attribute. It shows
an aspect implementation, an aspect definition, and how to invoke the aspect
from the Bazel command line.

```python
def _print_aspect_impl(target, ctx):
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the files that make up the sources and
        # print their paths.
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                print(f.path)
    return []

print_aspect = aspect(
    implementation = _print_aspect_impl,
    attr_aspects = ['deps'],
    required_providers = [CcInfo],
)
```

Let's break the example up into its parts and examine each one individually.

### Aspect definition

```python
print_aspect = aspect(
    implementation = _print_aspect_impl,
    attr_aspects = ['deps'],
    required_providers = [CcInfo],
)
```
Aspect definitions are similar to rule definitions, and defined using
the [`aspect`](/rules/lib/globals/bzl#aspect) function.

Just like a rule, an aspect has an implementation function which in this case is
``_print_aspect_impl``.

``attr_aspects`` is a list of rule attributes along which the aspect propagates.
In this case, the aspect will propagate along the ``deps`` attribute of the
rules that it is applied to.

Another common argument for `attr_aspects` is `['*']` which would propagate the
aspect to all attributes of a rule.

``required_providers`` is a list of providers that allows the aspect to limit
its propagation to only the targets whose rules advertise its required
providers. For more details consult
[the documentation of the aspect function](/rules/lib/globals/bzl#aspect).
In this case, the aspect will only apply on targets that declare `CcInfo`
provider.

### Aspect implementation

```python
def _print_aspect_impl(target, ctx):
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the files that make up the sources and
        # print their paths.
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                print(f.path)
    return []
```

Aspect implementation functions are similar to the rule implementation
functions. They return [providers](/extending/rules#providers), can generate
[actions](/extending/rules#actions), and take two arguments:

*  `target`: the [target](/rules/lib/builtins/Target) the aspect is being applied to.
*   `ctx`: [`ctx`](/rules/lib/builtins/ctx) object that can be used to access attributes
    and generate outputs and actions.

The implementation function can access the attributes of the target rule via
[`ctx.rule.attr`](/rules/lib/builtins/ctx#rule). It can examine providers that are
provided by the target to which it is applied (via the `target` argument).

Aspects are required to return a list of providers. In this example, the aspect
does not provide anything, so it returns an empty list.

### Invoking the aspect using the command line

The simplest way to apply an aspect is from the command line using the
[`--aspects`](/reference/command-line-reference#flag--aspects)
argument. Assuming the aspect above were defined in a file named `print.bzl`
this:

```bash
bazel build //MyExample:example --aspects print.bzl%print_aspect
```

would apply the `print_aspect` to the target `example` and all of the
target rules that are accessible recursively via the `deps` attribute.

The `--aspects` flag takes one argument, which is a specification of the aspect
in the format `<extension file label>%<aspect top-level name>`.

## Advanced example

The following example demonstrates using an aspect from a target rule
that counts files in targets, potentially filtering them by extension.
It shows how to use a provider to return values, how to use parameters to pass
an argument into an aspect implementation, and how to invoke an aspect from a rule.

Note: Aspects added in rules' attributes are called *rule-propagated aspects* as
opposed to *command-line aspects* that are specified using the ``--aspects``
flag.

`file_count.bzl` file:

```python
FileCountInfo = provider(
    fields = {
        'count' : 'number of files'
    }
)

def _file_count_aspect_impl(target, ctx):
    count = 0
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the sources counting files
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                if ctx.attr.extension == '*' or ctx.attr.extension == f.extension:
                    count = count + 1
    # Get the counts from our dependencies.
    for dep in ctx.rule.attr.deps:
        count = count + dep[FileCountInfo].count
    return [FileCountInfo(count = count)]

file_count_aspect = aspect(
    implementation = _file_count_aspect_impl,
    attr_aspects = ['deps'],
    attrs = {
        'extension' : attr.string(values = ['*', 'h', 'cc']),
    }
)

def _file_count_rule_impl(ctx):
    for dep in ctx.attr.deps:
        print(dep[FileCountInfo].count)

file_count_rule = rule(
    implementation = _file_count_rule_impl,
    attrs = {
        'deps' : attr.label_list(aspects = [file_count_aspect]),
        'extension' : attr.string(default = '*'),
    },
)
```

`BUILD.bazel` file:

```python
load('//:file_count.bzl', 'file_count_rule')

cc_library(
    name = 'lib',
    srcs = [
        'lib.h',
        'lib.cc',
    ],
)

cc_binary(
    name = 'app',
    srcs = [
        'app.h',
        'app.cc',
        'main.cc',
    ],
    deps = ['lib'],
)

file_count_rule(
    name = 'file_count',
    deps = ['app'],
    extension = 'h',
)
```

### Aspect definition

```python
file_count_aspect = aspect(
    implementation = _file_count_aspect_impl,
    attr_aspects = ['deps'],
    attrs = {
        'extension' : attr.string(values = ['*', 'h', 'cc']),
    }
)
```

This example shows how the aspect propagates through the ``deps`` attribute.

``attrs`` defines a set of attributes for an aspect. Public aspect attributes
define parameters and can only be of types ``bool``, ``int`` or ``string``.
For rule-propagated aspects, ``int`` and ``string`` parameters must have
``values`` specified on them. This example has a parameter called ``extension``
that is allowed to have '``*``', '``h``', or '``cc``' as a value.

For rule-propagated aspects, parameter values are taken from the rule requesting
the aspect, using the attribute of the rule that has the same name and type.
(see the definition of ``file_count_rule``).

For command-line aspects, the parameters values can be passed using
[``--aspects_parameters``](/reference/command-line-reference#flag--aspects_parameters)
flag. The ``values`` restriction of ``int`` and ``string`` parameters may be
omitted.

Aspects are also allowed to have private attributes of types ``label`` or
``label_list``. Private label attributes can be used to specify dependencies on
tools or libraries that are needed for actions generated by aspects. There is not
a private attribute defined in this example, but the following code snippet
demonstrates how you could pass in a tool to an aspect:

```python
...
    attrs = {
        '_protoc' : attr.label(
            default = Label('//tools:protoc'),
            executable = True,
            cfg = "exec"
        )
    }
...
```

### Aspect implementation

```python
FileCountInfo = provider(
    fields = {
        'count' : 'number of files'
    }
)

def _file_count_aspect_impl(target, ctx):
    count = 0
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the sources counting files
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                if ctx.attr.extension == '*' or ctx.attr.extension == f.extension:
                    count = count + 1
    # Get the counts from our dependencies.
    for dep in ctx.rule.attr.deps:
        count = count + dep[FileCountInfo].count
    return [FileCountInfo(count = count)]
```

Just like a rule implementation function, an aspect implementation function
returns a struct of providers that are accessible to its dependencies.

In this example, the ``FileCountInfo`` is defined as a provider that has one
field ``count``. It is best practice to explicitly define the fields of a
provider using the ``fields`` attribute.

The set of providers for an aspect application A(X) is the union of providers
that come from the implementation of a rule for target X and from the
implementation of aspect A. The providers that a rule implementation propagates
are created and frozen before aspects are applied and cannot be modified from an
aspect. It is an error if a target and an aspect that is applied to it each
provide a provider with the same type, with the exceptions of
[`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo)
(which is merged, so long as the
rule and aspect specify different output groups) and
[`InstrumentedFilesInfo`](/rules/lib/providers/InstrumentedFilesInfo)
(which is taken from the aspect). This means that aspect implementations may
never return [`DefaultInfo`](/rules/lib/providers/DefaultInfo).

The parameters and private attributes are passed in the attributes of the
``ctx``. This example references the ``extension`` parameter and determines
what files to count.

For returning providers, the values of attributes along which
the aspect is propagated (from the `attr_aspects` list) are replaced with
the results of an application of the aspect to them. For example, if target
X has Y and Z in its deps, `ctx.rule.attr.deps` for A(X) will be [A(Y), A(Z)].
In this example, ``ctx.rule.attr.deps`` are Target objects that are the
results of applying the aspect to the 'deps' of the original target to which
the aspect has been applied.

In the example, the aspect accesses the ``FileCountInfo`` provider from the
target's dependencies to accumulate the total transitive number of files.

### Invoking the aspect from a rule

```python
def _file_count_rule_impl(ctx):
    for dep in ctx.attr.deps:
        print(dep[FileCountInfo].count)

file_count_rule = rule(
    implementation = _file_count_rule_impl,
    attrs = {
        'deps' : attr.label_list(aspects = [file_count_aspect]),
        'extension' : attr.string(default = '*'),
    },
)
```

The rule implementation demonstrates how to access the ``FileCountInfo``
via the ``ctx.attr.deps``.

The rule definition demonstrates how to define a parameter (``extension``)
and give it a default value (``*``). Note that having a default value that
was not one of '``cc``', '``h``', or '``*``' would be an error due to the
restrictions placed on the parameter in the aspect definition.

### Invoking an aspect through a target rule

```python
load('//:file_count.bzl', 'file_count_rule')

cc_binary(
    name = 'app',
...
)

file_count_rule(
    name = 'file_count',
    deps = ['app'],
    extension = 'h',
)
```

This demonstrates how to pass the ``extension`` parameter into the aspect
via the rule. Since the ``extension`` parameter has a default value in the
rule implementation, ``extension`` would be considered an optional parameter.

When the ``file_count`` target is built, our aspect will be evaluated for
itself, and all of the targets accessible recursively via ``deps``.

## References

* [`aspect` API reference](/rules/lib/globals/bzl#aspect)


Project: /_project.yaml
Book: /_book.yaml

# Configurations

<devsite-mathjax config="TeX-AMS-MML_SVG"></devsite-mathjax>

{% include "_buttons.html" %}

This page covers the benefits and basic usage of Starlark configurations,
Bazel's API for customizing how your project builds. It includes how to define
build settings and provides examples.

This makes it possible to:

*   define custom flags for your project, obsoleting the need for
     [`--define`](/docs/configurable-attributes#custom-keys)
*   write
    [transitions](/rules/lib/builtins/transition#transition) to configure deps in
    different configurations than their parents
    (such as `--compilation_mode=opt` or `--cpu=arm`)
*   bake better defaults into rules (such as automatically build `//my:android_app`
    with a specified SDK)

and more, all completely from .bzl files (no Bazel release required). See the
`bazelbuild/examples` repo for
[examples](https://github.com/bazelbuild/examples/tree/HEAD/configurations){: .external}.

## User-defined build settings {:#user-defined-build-settings}

A build setting is a single piece of
[configuration](/extending/rules#configurations)
information. Think of a configuration as a key/value map. Setting `--cpu=ppc`
and `--copt="-DFoo"` produces a configuration that looks like
`{cpu: ppc, copt: "-DFoo"}`. Each entry is a build setting.

Traditional flags like `cpu` and `copt` are native settings —
their keys are defined and their values are set inside native bazel java code.
Bazel users can only read and write them via the command line
and other APIs maintained natively. Changing native flags, and the APIs
that expose them, requires a bazel release. User-defined build
settings are defined in `.bzl` files (and thus, don't need a bazel release to
register changes). They also can be set via the command line
(if they're designated as `flags`, see more below), but can also be
set via [user-defined transitions](#user-defined-transitions).

### Defining build settings {:#defining-build-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/basic_build_setting){: .external}

#### The `build_setting` `rule()` parameter {:#rule-parameter}

Build settings are rules like any other rule and are differentiated using the
Starlark `rule()` function's `build_setting`
[attribute](/rules/lib/globals/bzl#rule.build_setting).

```python
# example/buildsettings/build_settings.bzl
string_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

The `build_setting` attribute takes a function that designates the type of the
build setting. The type is limited to a set of basic Starlark types like
`bool` and `string`. See the `config` module
[documentation](/rules/lib/toplevel/config)  for details. More complicated typing can be
done in the rule's implementation function. More on this below.

The `config` module's functions takes an optional boolean parameter, `flag`,
which is set to false by default. if `flag` is set to true, the build setting
can be set on the command line by users as well as internally by rule writers
via default values and [transitions](/rules/lib/builtins/transition#transition).
Not all settings should be settable by users. For example, if you as a rule
writer have some debug mode that you'd like to turn on inside test rules,
you don't want to give users the ability to indiscriminately turn on that
feature inside other non-test rules.

#### Using ctx.build_setting_value {:#ctx-build-setting-value}

Like all rules, build setting rules have [implementation functions](/extending/rules#implementation-function).
The basic Starlark-type value of the build settings can be accessed via the
`ctx.build_setting_value` method. This method is only available to
[`ctx`](/rules/lib/builtins/ctx) objects of build setting rules. These implementation
methods can directly forward the build settings value or do additional work on
it, like type checking or more complex struct creation. Here's how you would
implement an `enum`-typed build setting:

```python
# example/buildsettings/build_settings.bzl
TemperatureProvider = provider(fields = ['type'])

temperatures = ["HOT", "LUKEWARM", "ICED"]

def _impl(ctx):
    raw_temperature = ctx.build_setting_value
    if raw_temperature not in temperatures:
        fail(str(ctx.label) + " build setting allowed to take values {"
             + ", ".join(temperatures) + "} but was set to unallowed value "
             + raw_temperature)
    return TemperatureProvider(type = raw_temperature)

temperature = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

Note: if a rule depends on a build setting, it will receive whatever providers
the build setting implementation function returns, like any other dependency.
But all other references to the value of the build setting (such as in transitions)
will see its basic Starlark-typed value, not this post implementation function
value.

#### Defining multi-set string flags {:#multi-set-string-flags}

String settings have an additional `allow_multiple` parameter which allows the
flag to be set multiple times on the command line or in bazelrcs. Their default
value is still set with a string-typed attribute:

```python
# example/buildsettings/build_settings.bzl
allow_multiple_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True, allow_multiple = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "allow_multiple_flag")
allow_multiple_flag(
    name = "roasts",
    build_setting_default = "medium"
)
```

Each setting of the flag is treated as a single value:

```shell
$ bazel build //my/target --//example:roasts=blonde \
    --//example:roasts=medium,dark
```

The above is parsed to `{"//example:roasts": ["blonde", "medium,dark"]}` and
`ctx.build_setting_value` returns the list `["blonde", "medium,dark"]`.

#### Instantiating build settings {:#instantiating-build-settings}

Rules defined with the `build_setting` parameter have an implicit mandatory
`build_setting_default` attribute. This attribute takes on the same type as
declared by the `build_setting` param.

```python
# example/buildsettings/build_settings.bzl
FlavorProvider = provider(fields = ['type'])

def _impl(ctx):
    return FlavorProvider(type = ctx.build_setting_value)

flavor = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "flavor")
flavor(
    name = "favorite_flavor",
    build_setting_default = "APPLE"
)
```

### Predefined settings {:#predefined-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/use_skylib_build_setting){: .external}

The
[Skylib](https://github.com/bazelbuild/bazel-skylib){: .external}
library includes a set of predefined settings you can instantiate without having
to write custom Starlark.

For example, to define a setting that accepts a limited set of string values:

```python
# example/BUILD
load("@bazel_skylib//rules:common_settings.bzl", "string_flag")
string_flag(
    name = "myflag",
    values = ["a", "b", "c"],
    build_setting_default = "a",
)
```

For a complete list, see
[Common build setting rules](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/common_settings.bzl){: .external}.

### Using build settings {:#using-build-settings}

#### Depending on build settings {:#depending-on-build-settings}

If a target would like to read a piece of configuration information, it can
directly depend on the build setting via a regular attribute dependency.

```python
# example/rules.bzl
load("//example/buildsettings:build_settings.bzl", "FlavorProvider")
def _rule_impl(ctx):
    if ctx.attr.flavor[FlavorProvider].type == "ORANGE":
        ...

drink_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "flavor": attr.label()
    }
)
```

```python
# example/BUILD
load("//example:rules.bzl", "drink_rule")
load("//example/buildsettings:build_settings.bzl", "flavor")
flavor(
    name = "favorite_flavor",
    build_setting_default = "APPLE"
)
drink_rule(
    name = "my_drink",
    flavor = ":favorite_flavor",
)
```

Languages may wish to create a canonical set of build settings which all rules
for that language depend on. Though the native concept of `fragments` no longer
exists as a hardcoded object in Starlark configuration world, one way to
translate this concept would be to use sets of common implicit attributes. For
example:

```python
# kotlin/rules.bzl
_KOTLIN_CONFIG = {
    "_compiler": attr.label(default = "//kotlin/config:compiler-flag"),
    "_mode": attr.label(default = "//kotlin/config:mode-flag"),
    ...
}

...

kotlin_library = rule(
    implementation = _rule_impl,
    attrs = dicts.add({
        "library-attr": attr.string()
    }, _KOTLIN_CONFIG)
)

kotlin_binary = rule(
    implementation = _binary_impl,
    attrs = dicts.add({
        "binary-attr": attr.label()
    }, _KOTLIN_CONFIG)

```

#### Using build settings on the command line {:#build-settings-command-line}

Similar to most native flags, you can use the command line to set build settings
[that are marked as flags](#rule-parameter). The build
setting's name is its full target path using `name=value` syntax:

```shell
$ bazel build //my/target --//example:string_flag=some-value # allowed
$ bazel build //my/target --//example:string_flag some-value # not allowed
```

Special boolean syntax is supported:

```shell
$ bazel build //my/target --//example:boolean_flag
$ bazel build //my/target --no//example:boolean_flag
```

#### Using build setting aliases {:#using-build-setting-aliases}

You can set an alias for your build setting target path to make it easier to read
on the command line. Aliases function similarly to native flags and also make use
of the double-dash option syntax.

Set an alias by adding `--flag_alias=ALIAS_NAME=TARGET_PATH`
to your `.bazelrc` . For example, to set an alias to `coffee`:

```shell
# .bazelrc
build --flag_alias=coffee=//experimental/user/starlark_configurations/basic_build_setting:coffee-temp
```

Best Practice: Setting an alias multiple times results in the most recent
one taking precedence. Use unique alias names to avoid unintended parsing results.

To make use of the alias, type it in place of the build setting target path.
With the above example of `coffee` set in the user's `.bazelrc`:

```shell
$ bazel build //my/target --coffee=ICED
```

instead of

```shell
$ bazel build //my/target --//experimental/user/starlark_configurations/basic_build_setting:coffee-temp=ICED
```
Best Practice: While it possible to set aliases on the command line, leaving them
in a `.bazelrc` reduces command line clutter.

### Label-typed build settings {:#label-typed-build-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/label_typed_build_setting){: .external}

Unlike other build settings, label-typed settings cannot be defined using the
`build_setting` rule parameter. Instead, bazel has two built-in rules:
`label_flag` and `label_setting`. These rules forward the providers of the
actual target to which the build setting is set. `label_flag` and
`label_setting` can be read/written by transitions and `label_flag` can be set
by the user like other `build_setting` rules can. Their only difference is they
can't customely defined.

Label-typed settings will eventually replace the functionality of late-bound
defaults. Late-bound default attributes are Label-typed attributes whose
final values can be affected by configuration. In Starlark, this will replace
the [`configuration_field`](/rules/lib/globals/bzl#configuration_field)
 API.

```python
# example/rules.bzl
MyProvider = provider(fields = ["my_field"])

def _dep_impl(ctx):
    return MyProvider(my_field = "yeehaw")

dep_rule = rule(
    implementation = _dep_impl
)

def _parent_impl(ctx):
    if ctx.attr.my_field_provider[MyProvider].my_field == "cowabunga":
        ...

parent_rule = rule(
    implementation = _parent_impl,
    attrs = { "my_field_provider": attr.label() }
)

```

```python
# example/BUILD
load("//example:rules.bzl", "dep_rule", "parent_rule")

dep_rule(name = "dep")

parent_rule(name = "parent", my_field_provider = ":my_field_provider")

label_flag(
    name = "my_field_provider",
    build_setting_default = ":dep"
)
```

### Build settings and select() {:#build-settings-and-select}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/select_on_build_setting){: .external}

Users can configure attributes on build settings by using
 [`select()`](/reference/be/functions#select). Build setting targets can be passed to the `flag_values` attribute of
`config_setting`. The value to match to the configuration is passed as a
`String` then parsed to the type of the build setting for matching.

```python
config_setting(
    name = "my_config",
    flag_values = {
        "//example:favorite_flavor": "MANGO"
    }
)
```

## User-defined transitions {:#user-defined-transitions}

A configuration
[transition](/rules/lib/builtins/transition#transition)
maps the transformation from one configured target to another within the
build graph.

Important: Transitions have [memory and performance impact](#memory-performance-considerations).

### Defining {:#defining}

Transitions define configuration changes between rules. For example, a request
like "compile my dependency for a different CPU than its parent" is handled by a
transition.

Formally, a transition is a function from an input configuration to one or more
output configurations. Most transitions are 1:1 such as "override the input
configuration with `--cpu=ppc`". 1:2+ transitions can also exist but come
with special restrictions.

In Starlark, transitions are defined much like rules, with a defining
`transition()`
[function](/rules/lib/builtins/transition#transition)
and an implementation function.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {"//example:favorite_flavor" : "MINT"}

hot_chocolate_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)
```
The `transition()` function takes in an implementation function, a set of
build settings to read(`inputs`), and a set of build settings to write
(`outputs`). The implementation function has two parameters, `settings` and
`attr`. `settings` is a dictionary {`String`:`Object`} of all settings declared
in the `inputs` parameter to `transition()`.

`attr` is a dictionary of attributes and values of the rule to which the
transition is attached. When attached as an
[outgoing edge transition](#outgoing-edge-transitions), the values of these
attributes are all configured post-select() resolution. When attached as
an [incoming edge transition](#incoming-edge-transitions), `attr` does not
include any attributes that use a selector to resolve their value. If an
incoming edge transition on `--foo` reads attribute `bar` and then also
selects on `--foo` to set attribute `bar`, then there's a chance for the
incoming edge transition to read the wrong value of `bar` in the transition.

Note: Since transitions are attached to rule definitions and `select()`s are
attached to rule instantiations (such as targets), errors related to `select()`s on
read attributes will pop up when users create targets rather than when rules are
written. It may be worth taking extra care to communicate to rule users which
attributes they should be wary of selecting on or taking other precautions.

The implementation function must return a dictionary (or list of
dictionaries, in the case of
transitions with multiple output configurations)
of new build settings values to apply. The returned dictionary keyset(s) must
contain exactly the set of build settings passed to the `outputs`
parameter of the transition function. This is true even if a build setting is
not actually changed over the course of the transition - its original value must
be explicitly passed through in the returned dictionary.

### Defining 1:2+ transitions {:#defining-1-2-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/multi_arch_binary){: .external}

[Outgoing edge transition](#outgoing-edge-transitions) can map a single input
configuration to two or more output configurations. This is useful for defining
rules that bundle multi-architecture code.

1:2+ transitions are defined by returning a list of dictionaries in the
transition implementation function.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return [
        {"//example:favorite_flavor" : "LATTE"},
        {"//example:favorite_flavor" : "MOCHA"},
    ]

coffee_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)
```
They can also set custom keys that the rule implementation function can use to
read individual dependencies:

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {
        "Apple deps": {"//command_line_option:cpu": "ppc"},
        "Linux deps": {"//command_line_option:cpu": "x86"},
    }

multi_arch_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
)
```

### Attaching transitions {:#attaching-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/attaching_transitions_to_rules){: .external}

Transitions can be attached in two places: incoming edges and outgoing edges.
Effectively this means rules can transition their own configuration (incoming
edge transition) and transition their dependencies' configurations (outgoing
edge transition).

NOTE: There is currently no way to attach Starlark transitions to native rules.
If you need to do this, contact
bazel-discuss@googlegroups.com
for help with figuring out workarounds.

### Incoming edge transitions {:#incoming-edge-transitions}

Incoming edge transitions are activated by attaching a `transition` object
(created by `transition()`) to `rule()`'s `cfg` parameter:

```python
# example/rules.bzl
load("example/transitions:transitions.bzl", "hot_chocolate_transition")
drink_rule = rule(
    implementation = _impl,
    cfg = hot_chocolate_transition,
    ...
```

Incoming edge transitions must be 1:1 transitions.

### Outgoing edge transitions {:#outgoing-edge-transitions}

Outgoing edge transitions are activated by attaching a `transition` object
(created by `transition()`) to an attribute's `cfg` parameter:

```python
# example/rules.bzl
load("example/transitions:transitions.bzl", "coffee_transition")
drink_rule = rule(
    implementation = _impl,
    attrs = { "dep": attr.label(cfg = coffee_transition)}
    ...
```
Outgoing edge transitions can be 1:1 or 1:2+.

See [Accessing attributes with transitions](#accessing-attributes-with-transitions)
for how to read these keys.

### Transitions on native options {:#transitions-native-options}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/transition_on_native_flag){: .external}

Starlark transitions can also declare reads and writes on native build
configuration options via a special prefix to the option name.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {"//command_line_option:cpu": "k8"}

cpu_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
```

#### Unsupported native options {:#unsupported-native-options}

Bazel doesn't support transitioning on `--define` with
`"//command_line_option:define"`. Instead, use a custom
[build setting](#user-defined-build-settings). In general, new usages of
`--define` are discouraged in favor of build settings.

Bazel doesn't support transitioning on `--config`. This is because `--config` is
an "expansion" flag that expands to other flags.

Crucially, `--config` may include flags that don't affect build configuration,
such as
[`--spawn_strategy`](/docs/user-manual#spawn-strategy)
. Bazel, by design, can't bind such flags to individual targets. This means
there's no coherent way to apply them in transitions.

As a workaround, you can explicitly itemize the flags that *are* part of
the configuration in your transition. This requires maintaining the `--config`'s
expansion in two places, which is a known UI blemish.

### Transitions on allow multiple build settings {:#transitions-multiple-build-settings}

When setting build settings that
[allow multiple values](#defining-multi-set-string-flags), the value of the
setting must be set with a list.

```python
# example/buildsettings/build_settings.bzl
string_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True, allow_multiple = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "string_flag")
string_flag(name = "roasts", build_setting_default = "medium")
```

```python
# example/transitions/rules.bzl
def _transition_impl(settings, attr):
    # Using a value of just "dark" here will throw an error
    return {"//example:roasts" : ["dark"]},

coffee_transition = transition(
    implementation = _transition_impl,
    inputs = [],
    outputs = ["//example:roasts"]
)
```

### No-op transitions {:#no-op-transitions}

If a transition returns `{}`, `[]`, or `None`, this is shorthand for keeping all
settings at their original values. This can be more convenient than explicitly
setting each output to itself.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (attr)
    if settings["//example:already_chosen"] is True:
      return {}
    return {
      "//example:favorite_flavor": "dark chocolate",
      "//example:include_marshmallows": "yes",
      "//example:desired_temperature": "38C",
    }

hot_chocolate_transition = transition(
    implementation = _impl,
    inputs = ["//example:already_chosen"],
    outputs = [
        "//example:favorite_flavor",
        "//example:include_marshmallows",
        "//example:desired_temperature",
    ]
)
```

### Accessing attributes with transitions {:#accessing-attributes-with-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/read_attr_in_transition){: .external}

When [attaching a transition to an outgoing edge](#outgoing-edge-transitions)
(regardless of whether the transition is a 1:1 or 1:2+ transition), `ctx.attr` is forced to be a list
if it isn't already. The order of elements in this list is unspecified.


```python
# example/transitions/rules.bzl
def _transition_impl(settings, attr):
    return {"//example:favorite_flavor" : "LATTE"},

coffee_transition = transition(
    implementation = _transition_impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)

def _rule_impl(ctx):
    # Note: List access even though "dep" is not declared as list
    transitioned_dep = ctx.attr.dep[0]

    # Note: Access doesn't change, other_deps was already a list
    for other_dep in ctx.attr.other_deps:
      # ...


coffee_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "dep": attr.label(cfg = coffee_transition)
        "other_deps": attr.label_list(cfg = coffee_transition)
    })
```

If the transition is `1:2+` and sets custom keys, `ctx.split_attr` can be used
to read individual deps for each key:

```python
# example/transitions/rules.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {
        "Apple deps": {"//command_line_option:cpu": "ppc"},
        "Linux deps": {"//command_line_option:cpu": "x86"},
    }

multi_arch_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
)

def _rule_impl(ctx):
    apple_dep = ctx.split_attr.dep["Apple deps"]
    linux_dep = ctx.split_attr.dep["Linux deps"]
    # ctx.attr has a list of all deps for all keys. Order is not guaranteed.
    all_deps = ctx.attr.dep

multi_arch_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "dep": attr.label(cfg = multi_arch_transition)
    })
```

See [complete example](https://github.com/bazelbuild/examples/tree/main/configurations/multi_arch_binary)
here.

## Integration with platforms and toolchains {:#integration-platforms-toolchains}

Many native flags today, like `--cpu` and `--crosstool_top` are related to
toolchain resolution. In the future, explicit transitions on these types of
flags will likely be replaced by transitioning on the
[target platform](/extending/platforms).

## Memory and performance considerations {:#memory-performance-considerations}

Adding transitions, and therefore new configurations, to your build comes at a
cost: larger build graphs, less comprehensible build graphs, and slower
builds. It's worth considering these costs when considering
using transitions in your build rules. Below is an example of how a transition
might create exponential growth of your build graph.

### Badly behaved builds: a case study {:#badly-behaved-builds}

![Scalability graph](/rules/scalability-graph.png "Scalability graph")

**Figure 1.** Scalability graph showing a top level target and its dependencies.

This graph shows a top level target, `//pkg:app`, which depends on two targets, a
`//pkg:1_0` and `//pkg:1_1`. Both these targets depend on two targets, `//pkg:2_0` and
`//pkg:2_1`. Both these targets depend on two targets, `//pkg:3_0` and `//pkg:3_1`.
This continues on until `//pkg:n_0` and `//pkg:n_1`, which both depend on a single
target, `//pkg:dep`.

Building `//pkg:app` requires \\(2n+2\\) targets:

* `//pkg:app`
* `//pkg:dep`
* `//pkg:i_0` and `//pkg:i_1` for \\(i\\) in \\([1..n]\\)

Imagine you [implement](#user-defined-build-settings) a flag
`--//foo:owner=<STRING>` and `//pkg:i_b` applies

    depConfig = myConfig + depConfig.owner="$(myConfig.owner)$(b)"

In other words, `//pkg:i_b` appends `b` to the old value of `--owner` for all
its deps.

This produces the following [configured targets](/reference/glossary#configured-target):

```
//pkg:app                              //foo:owner=""
//pkg:1_0                              //foo:owner=""
//pkg:1_1                              //foo:owner=""
//pkg:2_0 (via //pkg:1_0)              //foo:owner="0"
//pkg:2_0 (via //pkg:1_1)              //foo:owner="1"
//pkg:2_1 (via //pkg:1_0)              //foo:owner="0"
//pkg:2_1 (via //pkg:1_1)              //foo:owner="1"
//pkg:3_0 (via //pkg:1_0 → //pkg:2_0)  //foo:owner="00"
//pkg:3_0 (via //pkg:1_0 → //pkg:2_1)  //foo:owner="01"
//pkg:3_0 (via //pkg:1_1 → //pkg:2_0)  //foo:owner="10"
//pkg:3_0 (via //pkg:1_1 → //pkg:2_1)  //foo:owner="11"
...
```

`//pkg:dep` produces \\(2^n\\) configured targets: `config.owner=`
"\\(b_0b_1...b_n\\)" for all \\(b_i\\) in \\(\{0,1\}\\).

This makes the build graph exponentially larger than the target graph, with
corresponding memory and performance consequences.

TODO: Add strategies for measurement and mitigation of these issues.

## Further reading {:#further-reading}

For more details on modifying build configurations, see:

 * [Starlark Build Configuration](https://docs.google.com/document/d/1vc8v-kXjvgZOdQdnxPTaV0rrLxtP2XwnD2tAZlYJOqw/edit?usp=sharing){: .external}
 * [Bazel Configurability Roadmap](https://bazel.build/community/roadmaps-configurability){: .external}
 * Full [set](https://github.com/bazelbuild/examples/tree/HEAD/configurations){: .external} of end to end examples


Project: /_project.yaml
Book: /_book.yaml

# Platforms

{% include "_buttons.html" %}

Bazel can build and test code on a variety of hardware, operating systems, and
system configurations, using many different versions of build tools such as
linkers and compilers. To help manage this complexity, Bazel has a concept of
*constraints* and *platforms*. A constraint is a dimension in which build or
production environments may differ, such as CPU architecture, the presence or
absence of a GPU, or the version of a system-installed compiler. A platform is a
named collection of choices for these constraints, representing the particular
resources that are available in some environment.

Modeling the environment as a platform helps Bazel to automatically select the
appropriate
[toolchains](/extending/toolchains)
for build actions. Platforms can also be used in combination with the
[config_setting](/reference/be/general#config_setting)
rule to write [configurable attributes](/docs/configurable-attributes).

Bazel recognizes three roles that a platform may serve:

*  **Host** - the platform on which Bazel itself runs.
*  **Execution** - a platform on which build tools execute build actions to
   produce intermediate and final outputs.
*  **Target** - a platform on which a final output resides and executes.

Bazel supports the following build scenarios regarding platforms:

*  **Single-platform builds** (default) - host, execution, and target platforms
   are the same. For example, building a Linux executable on Ubuntu running on
   an Intel x64 CPU.

*  **Cross-compilation builds** - host and execution platforms are the same, but
   the target platform is different. For example, building an iOS app on macOS
   running on a MacBook Pro.

*  **Multi-platform builds** - host, execution, and target platforms are all
   different.

Tip: for detailed instructions on migrating your project to platforms, see
[Migrating to Platforms](/concepts/platforms).

## Defining constraints and platforms {:#constraints-platforms}

The space of possible choices for platforms is defined by using the
[`constraint_setting`][constraint_setting] and
[`constraint_value`][constraint_value] rules within `BUILD` files.
`constraint_setting` creates a new dimension, while
`constraint_value` creates a new value for a given dimension; together they
effectively define an enum and its possible values. For example, the following
snippet of a `BUILD` file introduces a constraint for the system's glibc version
with two possible values.

[constraint_setting]: /reference/be/platforms-and-toolchains#constraint_setting
[constraint_value]: /reference/be/platforms-and-toolchains#constraint_value

```python
constraint_setting(name = "glibc_version")

constraint_value(
    name = "glibc_2_25",
    constraint_setting = ":glibc_version",
)

constraint_value(
    name = "glibc_2_26",
    constraint_setting = ":glibc_version",
)
```

Constraints and their values may be defined across different packages in the
workspace. They are referenced by label and subject to the usual visibility
controls. If visibility allows, you can extend an existing constraint setting by
defining your own value for it.

The [`platform`](/reference/be/platforms-and-toolchains#platform) rule introduces a new platform with
certain choices of constraint values. The
following creates a platform named `linux_x86`, and says that it describes any
environment that runs a Linux operating system on an x86_64 architecture with a
glibc version of 2.25. (See below for more on Bazel's built-in constraints.)

```python
platform(
    name = "linux_x86",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
        ":glibc_2_25",
    ],
)
```

Note: It is an error for a platform to specify more than one value of the
same constraint setting, such as `@platforms//cpu:x86_64` and
`@platforms//cpu:arm` for `@platforms//cpu:cpu`.

## Generally useful constraints and platforms {:#useful-constraints-platforms}

To keep the ecosystem consistent, Bazel team maintains a repository with
constraint definitions for the most popular CPU architectures and operating
systems. These are all located in
[https://github.com/bazelbuild/platforms](https://github.com/bazelbuild/platforms){: .external}.

Bazel ships with the following special platform definition:
`@platforms//host` (aliased as `@bazel_tools//tools:host_platform`). This is the
autodetected host platform value -
represents autodetected platform for the system Bazel is running on.

## Specifying a platform for a build {:#specifying-build-platform}

You can specify the host and target platforms for a build using the following
command-line flags:

*  `--host_platform` - defaults to `@bazel_tools//tools:host_platform`
   *  This target is aliased to `@platforms//host`, which is backed by a repo
      rule that detects the host OS and CPU and writes the platform target.
   *  There's also `@platforms//host:constraints.bzl`, which exposes
      an array called `HOST_CONSTRAINTS`, which can be used in other BUILD and
      Starlark files.
*  `--platforms` - defaults to the host platform
   *  This means that when no other flags are set,
      `@platforms//host` is the target platform.
   *  If `--host_platform` is set and not `--platforms`, the value of
      `--host_platform` is both the host and target platform.

## Skipping incompatible targets {:#skipping-incompatible-targets}

When building for a specific target platform it is often desirable to skip
targets that will never work on that platform. For example, your Windows device
driver is likely going to generate lots of compiler errors when building on a
Linux machine with `//...`. Use the
[`target_compatible_with`](/reference/be/common-definitions#common.target_compatible_with)
attribute to tell Bazel what target platform constraints your code has.

The simplest use of this attribute restricts a target to a single platform.
The target will not be built for any platform that doesn't satisfy all of the
constraints. The following example restricts `win_driver_lib.cc` to 64-bit
Windows.

```python
cc_library(
    name = "win_driver_lib",
    srcs = ["win_driver_lib.cc"],
    target_compatible_with = [
        "@platforms//cpu:x86_64",
        "@platforms//os:windows",
    ],
)
```

`:win_driver_lib` is *only* compatible for building with 64-bit Windows and
incompatible with all else. Incompatibility is transitive. Any targets
that transitively depend on an incompatible target are themselves considered
incompatible.

### When are targets skipped? {:#when-targets-skipped}

Targets are skipped when they are considered incompatible and included in the
build as part of a target pattern expansion. For example, the following two
invocations skip any incompatible targets found in a target pattern expansion.

```console
$ bazel build --platforms=//:myplatform //...
```

```console
$ bazel build --platforms=//:myplatform //:all
```

Incompatible tests in a [`test_suite`](/reference/be/general#test_suite) are
similarly skipped if the `test_suite` is specified on the command line with
[`--expand_test_suites`](/reference/command-line-reference#flag--expand_test_suites).
In other words, `test_suite` targets on the command line behave like `:all` and
`...`. Using `--noexpand_test_suites` prevents expansion and causes
`test_suite` targets with incompatible tests to also be incompatible.

Explicitly specifying an incompatible target on the command line results in an
error message and a failed build.

```console
$ bazel build --platforms=//:myplatform //:target_incompatible_with_myplatform
...
ERROR: Target //:target_incompatible_with_myplatform is incompatible and cannot be built, but was explicitly requested.
...
FAILED: Build did NOT complete successfully
```

Incompatible explicit targets are silently skipped if
`--skip_incompatible_explicit_targets` is enabled.

### More expressive constraints {:#expressive-constraints}

For more flexibility in expressing constraints, use the
`@platforms//:incompatible`
[`constraint_value`](/reference/be/platforms-and-toolchains#constraint_value)
that no platform satisfies.

Use [`select()`](/reference/be/functions#select) in combination with
`@platforms//:incompatible` to express more complicated restrictions. For
example, use it to implement basic OR logic. The following marks a library
compatible with macOS and Linux, but no other platforms.

Note: An empty constraints list is equivalent to "compatible with everything".

```python
cc_library(
    name = "unixish_lib",
    srcs = ["unixish_lib.cc"],
    target_compatible_with = select({
        "@platforms//os:osx": [],
        "@platforms//os:linux": [],
        "//conditions:default": ["@platforms//:incompatible"],
    }),
)
```

The above can be interpreted as follows:

1. When targeting macOS, the target has no constraints.
2. When targeting Linux, the target has no constraints.
3. Otherwise, the target has the `@platforms//:incompatible` constraint. Because
   `@platforms//:incompatible` is not part of any platform, the target is
   deemed incompatible.

To make your constraints more readable, use
[skylib](https://github.com/bazelbuild/bazel-skylib){: .external}'s
[`selects.with_or()`](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/selects_doc.md#selectswith_or){: .external}.

You can express inverse compatibility in a similar way. The following example
describes a library that is compatible with everything _except_ for ARM.

```python
cc_library(
    name = "non_arm_lib",
    srcs = ["non_arm_lib.cc"],
    target_compatible_with = select({
        "@platforms//cpu:arm": ["@platforms//:incompatible"],
        "//conditions:default": [],
    }),
)
```

### Detecting incompatible targets using `bazel cquery` {:#cquery-incompatible-target-detection}

You can use the
[`IncompatiblePlatformProvider`](/rules/lib/providers/IncompatiblePlatformProvider)
in `bazel cquery`'s [Starlark output
format](/query/cquery#output-format-definition) to distinguish
incompatible targets from compatible ones.

This can be used to filter out incompatible targets. The example below will
only print the labels for targets that are compatible. Incompatible targets are
not printed.

```console
$ cat example.cquery

def format(target):
  if "IncompatiblePlatformProvider" not in providers(target):
    return target.label
  return ""


$ bazel cquery //... --output=starlark --starlark:file=example.cquery
```

### Known Issues

Incompatible targets [ignore visibility
restrictions](https://github.com/bazelbuild/bazel/issues/16044).


Project: /_project.yaml
Book: /_book.yaml

# Execution Groups

{% include "_buttons.html" %}

Execution groups allow for multiple execution platforms within a single target.
Each execution group has its own [toolchain](/extending/toolchains) dependencies and
performs its own [toolchain resolution](/extending/toolchains#toolchain-resolution).

## Current status {:#current-status}

Execution groups for certain natively declared actions, like `CppLink`, can be
used inside `exec_properties` to set per-action, per-target execution
requirements. For more details, see the
[Default execution groups](#exec-groups-for-native-rules) section.

## Background {:#background}

Execution groups allow the rule author to define sets of actions, each with a
potentially different execution platform. Multiple execution platforms can allow
actions to execution differently, for example compiling an iOS app on a remote
(linux) worker and then linking/code signing on a local mac worker.

Being able to define groups of actions also helps alleviate the usage of action
mnemonics as a proxy for specifying actions. Mnemonics are not guaranteed to be
unique and can only reference a single action. This is especially helpful in
allocating extra resources to specific memory and processing intensive actions
like linking in C++ builds without over-allocating to less demanding tasks.

## Defining execution groups {:#defining-exec-groups}

During rule definition, rule authors can
[declare](/rules/lib/globals/bzl#exec_group)
a set of execution groups. On each execution group, the rule author can specify
everything needed to select an execution platform for that execution group,
namely any constraints via `exec_compatible_with` and toolchain types via
`toolchain`.

```python
# foo.bzl
my_rule = rule(
    _impl,
    exec_groups = {
        "link": exec_group(
            exec_compatible_with = ["@platforms//os:linux"],
            toolchains = ["//foo:toolchain_type"],
        ),
        "test": exec_group(
            toolchains = ["//foo_tools:toolchain_type"],
        ),
    },
    attrs = {
        "_compiler": attr.label(cfg = config.exec("link"))
    },
)
```

In the code snippet above, you can see that tool dependencies can also specify
transition for an exec group using the
[`cfg`](/rules/lib/toplevel/attr#label)
attribute param and the
[`config`](/rules/lib/toplevel/config)
module. The module exposes an `exec` function which takes a single string
parameter which is the name of the exec group for which the dependency should be
built.

As on native rules, the `test` execution group is present by default on Starlark
test rules.

## Accessing execution groups {:#accessing-exec-groups}

In the rule implementation, you can declare that actions should be run on the
execution platform of an execution group. You can do this by using the `exec_group`
param of action generating methods, specifically [`ctx.actions.run`]
(/rules/lib/builtins/actions#run) and
[`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell).

```python
# foo.bzl
def _impl(ctx):
  ctx.actions.run(
     inputs = [ctx.attr._some_tool, ctx.srcs[0]]
     exec_group = "compile",
     # ...
  )
```

Rule authors will also be able to access the [resolved toolchains](/extending/toolchains#toolchain-resolution)
of execution groups, similarly to how you
can access the resolved toolchain of a target:

```python
# foo.bzl
def _impl(ctx):
  foo_info = ctx.exec_groups["link"].toolchains["//foo:toolchain_type"].fooinfo
  ctx.actions.run(
     inputs = [foo_info, ctx.srcs[0]]
     exec_group = "link",
     # ...
  )
```

Note: If an action uses a toolchain from an execution group, but doesn't specify
that execution group in the action declaration, that may potentially cause
issues. A mismatch like this may not immediately cause failures, but is a latent
problem.

### Default execution groups {:#exec-groups-for-native-rules}

The following execution groups are predefined:

* `test`: Test runner actions (for more details, see
  the [execution platform section of the Test Encylopedia](/reference/test-encyclopedia#execution-platform)).
* `cpp_link`: C++ linking actions.

## Using execution groups to set execution properties {:#using-exec-groups-for-exec-properties}

Execution groups are integrated with the
[`exec_properties`](/reference/be/common-definitions#common-attributes)
attribute that exists on every rule and allows the target writer to specify a
string dict of properties that is then passed to the execution machinery. For
example, if you wanted to set some property, say memory, for the target and give
certain actions a higher memory allocation, you would write an `exec_properties`
entry with an execution-group-augmented key, such as:

```python
# BUILD
my_rule(
    name = 'my_target',
    exec_properties = {
        'mem': '12g',
        'link.mem': '16g'
    }
    …
)
```

All actions with `exec_group = "link"` would see the exec properties
dictionary as `{"mem": "16g"}`. As you see here, execution-group-level
settings override target-level settings.

## Using execution groups to set platform constraints {:#using-exec-groups-for-platform-constraints}

Execution groups are also integrated with the
[`exec_compatible_with`](/reference/be/common-definitions#common-attributes) and
[`exec_group_compatible_with`](/reference/be/common-definitions#common-attributes)
attributes that exist on every rule and allow the target writer to specify
additional constraints that must be satisfied by the execution platforms
selected for the target's actions.

For example, if the rule `my_test` defines the `link` execution group in
addition to the default and the `test` execution group, then the following
usage of these attributes would run actions in the default execution group on
a platform with a high number of CPUs, the test action on Linux, and the link
action on the default execution platform:

```python
# BUILD
constraint_setting(name = "cpu")
constraint_value(name = "high_cpu", constraint_setting = ":cpu")

platform(
  name = "high_cpu_platform",
  constraint_values = [":high_cpu"],
  exec_properties = {
    "cpu": "256",
  },
)

my_test(
  name = "my_test",
  exec_compatible_with = ["//constraints:high_cpu"],
  exec_group_compatible_with = {
    "test": ["@platforms//os:linux"],
  },
  ...
)
```

### Execution groups for native rules {:#execution-groups-for-native-rules}

The following execution groups are available for actions defined by native
rules:

* `test`: Test runner actions.
* `cpp_link`: C++ linking actions.

### Execution groups and platform execution properties {:#platform-execution-properties}

It is possible to define `exec_properties` for arbitrary execution groups on
platform targets (unlike `exec_properties` set directly on a target, where
properties for unknown execution groups are rejected). Targets then inherit the
execution platform's `exec_properties` that affect the default execution group
and any other relevant execution groups.

For example, suppose running tests on the exec platform requires some resource
to be available, but it isn't required for compiling and linking; this can be
modelled as follows:

```python
constraint_setting(name = "resource")
constraint_value(name = "has_resource", constraint_setting = ":resource")

platform(
    name = "platform_with_resource",
    constraint_values = [":has_resource"],
    exec_properties = {
        "test.resource": "...",
    },
)

cc_test(
    name = "my_test",
    srcs = ["my_test.cc"],
    exec_compatible_with = [":has_resource"],
)
```

`exec_properties` defined directly on targets take precedence over those that
are inherited from the execution platform.


Project: /_project.yaml
Book: /_book.yaml

# Rules

{% include "_buttons.html" %}

A **rule** defines a series of [**actions**](#actions) that Bazel performs on
inputs to produce a set of outputs, which are referenced in
[**providers**](#providers) returned by the rule's
[**implementation function**](#implementation_function). For example, a C++
binary rule might:

1.  Take a set of `.cpp` source files (inputs).
2.  Run `g++` on the source files (action).
3.  Return the `DefaultInfo` provider with the executable output and other files
    to make available at runtime.
4.  Return the `CcInfo` provider with C++-specific information gathered from the
    target and its dependencies.

From Bazel's perspective, `g++` and the standard C++ libraries are also inputs
to this rule. As a rule writer, you must consider not only the user-provided
inputs to a rule, but also all of the tools and libraries required to execute
the actions.

Before creating or modifying any rule, ensure you are familiar with Bazel's
[build phases](/extending/concepts). It is important to understand the three
phases of a build (loading, analysis, and execution). It is also useful to
learn about [macros](/extending/macros) to understand the difference between rules and
macros. To get started, first review the [Rules Tutorial](/rules/rules-tutorial).
Then, use this page as a reference.

A few rules are built into Bazel itself. These *native rules*, such as
`genrule` and `filegroup`, provide some core support.
By defining your own rules, you can add support for languages and tools
that Bazel doesn't support natively.

Bazel provides an extensibility model for writing rules using the
[Starlark](/rules/language) language. These rules are written in `.bzl` files, which
can be loaded directly from `BUILD` files.

When defining your own rule, you get to decide what attributes it supports and
how it generates its outputs.

The rule's `implementation` function defines its exact behavior during the
[analysis phase](/extending/concepts#evaluation-model). This function doesn't run any
external commands. Rather, it registers [actions](#actions) that will be used
later during the execution phase to build the rule's outputs, if they are
needed.

## Rule creation

In a `.bzl` file, use the [rule](/rules/lib/globals/bzl#rule) function to define a new
rule, and store the result in a global variable. The call to `rule` specifies
[attributes](#attributes) and an
[implementation function](#implementation_function):

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        "deps": attr.label_list(),
        ...
    },
)
```

This defines a [rule kind](/query/language#kind) named `example_library`.

The call to `rule` also must specify if the rule creates an
[executable](#executable-rules) output (with `executable = True`), or specifically
a test executable (with `test = True`). If the latter, the rule is a *test rule*,
and the name of the rule must end in `_test`.

## Target instantiation

Rules can be [loaded](/concepts/build-files#load) and called in `BUILD` files:

```python
load('//some/pkg:rules.bzl', 'example_library')

example_library(
    name = "example_target",
    deps = [":another_target"],
    ...
)
```

Each call to a build rule returns no value, but has the side effect of defining
a target. This is called *instantiating* the rule. This specifies a name for the
new target and values for the target's [attributes](#attributes).

Rules can also be called from Starlark functions and loaded in `.bzl` files.
Starlark functions that call rules are called [Starlark macros](/extending/macros).
Starlark macros must ultimately be called from `BUILD` files, and can only be
called during the [loading phase](/extending/concepts#evaluation-model), when `BUILD`
files are evaluated to instantiate targets.

## Attributes

An *attribute* is a rule argument. Attributes can provide specific values to a
target's [implementation](#implementation_function), or they can refer to other
targets, creating a graph of dependencies.

Rule-specific attributes, such as `srcs` or `deps`, are defined by passing a map
from attribute names to schemas (created using the [`attr`](/rules/lib/toplevel/attr)
module) to the `attrs` parameter of `rule`.
[Common attributes](/reference/be/common-definitions#common-attributes), such as
`name` and `visibility`, are implicitly added to all rules. Additional
attributes are implicitly added to
[executable and test rules](#executable-rules) specifically. Attributes which
are implicitly added to a rule can't be included in the dictionary passed to
`attrs`.

### Dependency attributes

Rules that process source code usually define the following attributes to handle
various [types of dependencies](/concepts/dependencies#types_of_dependencies):

*   `srcs` specifies source files processed by a target's actions. Often, the
    attribute schema specifies which file extensions are expected for the sort
    of source file the rule processes. Rules for languages with header files
    generally specify a separate `hdrs` attribute for headers processed by a
    target and its consumers.
*   `deps` specifies code dependencies for a target. The attribute schema should
    specify which [providers](#providers) those dependencies must provide. (For
    example, `cc_library` provides `CcInfo`.)
*   `data` specifies files to be made available at runtime to any executable
    which depends on a target. That should allow arbitrary files to be
    specified.

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = [".example"]),
        "hdrs": attr.label_list(allow_files = [".header"]),
        "deps": attr.label_list(providers = [ExampleInfo]),
        "data": attr.label_list(allow_files = True),
        ...
    },
)
```

These are examples of *dependency attributes*. Any attribute that specifies
an input label (those defined with
[`attr.label_list`](/rules/lib/toplevel/attr#label_list),
[`attr.label`](/rules/lib/toplevel/attr#label), or
[`attr.label_keyed_string_dict`](/rules/lib/toplevel/attr#label_keyed_string_dict))
specifies dependencies of a certain type
between a target and the targets whose labels (or the corresponding
[`Label`](/rules/lib/builtins/Label) objects) are listed in that attribute when the target
is defined. The repository, and possibly the path, for these labels is resolved
relative to the defined target.

```python
example_library(
    name = "my_target",
    deps = [":other_target"],
)

example_library(
    name = "other_target",
    ...
)
```

In this example, `other_target` is a dependency of `my_target`, and therefore
`other_target` is analyzed first. It is an error if there is a cycle in the
dependency graph of targets.

<a name="private-attributes"></a>

### Private attributes and implicit dependencies {:#private_attributes_and_implicit_dependencies}

A dependency attribute with a default value creates an *implicit dependency*. It
is implicit because it's a part of the target graph that the user doesn't
specify it in a `BUILD` file. Implicit dependencies are useful for hard-coding a
relationship between a rule and a *tool* (a build-time dependency, such as a
compiler), since most of the time a user is not interested in specifying what
tool the rule uses. Inside the rule's implementation function, this is treated
the same as other dependencies.

If you want to provide an implicit dependency without allowing the user to
override that value, you can make the attribute *private* by giving it a name
that begins with an underscore (`_`). Private attributes must have default
values. It generally only makes sense to use private attributes for implicit
dependencies.

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        ...
        "_compiler": attr.label(
            default = Label("//tools:example_compiler"),
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
    },
)
```

In this example, every target of type `example_library` has an implicit
dependency on the compiler `//tools:example_compiler`. This allows
`example_library`'s implementation function to generate actions that invoke the
compiler, even though the user did not pass its label as an input. Since
`_compiler` is a private attribute, it follows that `ctx.attr._compiler`
will always point to `//tools:example_compiler` in all targets of this rule
type. Alternatively, you can name the attribute `compiler` without the
underscore and keep the default value. This allows users to substitute a
different compiler if necessary, but it requires no awareness of the compiler's
label.

Implicit dependencies are generally used for tools that reside in the same
repository as the rule implementation. If the tool comes from the
[execution platform](/extending/platforms) or a different repository instead, the
rule should obtain that tool from a [toolchain](/extending/toolchains).

### Output attributes

*Output attributes*, such as [`attr.output`](/rules/lib/toplevel/attr#output) and
[`attr.output_list`](/rules/lib/toplevel/attr#output_list), declare an output file that the
target generates. These differ from dependency attributes in two ways:

*   They define output file targets instead of referring to targets defined
    elsewhere.
*   The output file targets depend on the instantiated rule target, instead of
    the other way around.

Typically, output attributes are only used when a rule needs to create outputs
with user-defined names which can't be based on the target name. If a rule has
one output attribute, it is typically named `out` or `outs`.

Output attributes are the preferred way of creating *predeclared outputs*, which
can be specifically depended upon or
[requested at the command line](#requesting_output_files).

## Implementation function

Every rule requires an `implementation` function. These functions are executed
strictly in the [analysis phase](/extending/concepts#evaluation-model) and transform the
graph of targets generated in the loading phase into a graph of
[actions](#actions) to be performed during the execution phase. As such,
implementation functions can't actually read or write files.

Rule implementation functions are usually private (named with a leading
underscore). Conventionally, they are named the same as their rule, but suffixed
with `_impl`.

Implementation functions take exactly one parameter: a
[rule context](/rules/lib/builtins/ctx), conventionally named `ctx`. They return a list of
[providers](#providers).

### Targets

Dependencies are represented at analysis time as [`Target`](/rules/lib/builtins/Target)
objects. These objects contain the [providers](#providers) generated when the
target's implementation function was executed.

[`ctx.attr`](/rules/lib/builtins/ctx#attr) has fields corresponding to the names of each
dependency attribute, containing `Target` objects representing each direct
dependency using that attribute. For `label_list` attributes, this is a list of
`Targets`. For `label` attributes, this is a single `Target` or `None`.

A list of provider objects are returned by a target's implementation function:

```python
return [ExampleInfo(headers = depset(...))]
```

Those can be accessed using index notation (`[]`), with the type of provider as
a key. These can be [custom providers](#custom_providers) defined in Starlark or
[providers for native rules](/rules/lib/providers) available as Starlark
global variables.

For example, if a rule takes header files using a `hdrs` attribute and provides
them to the compilation actions of the target and its consumers, it could
collect them like so:

```python
def _example_library_impl(ctx):
    ...
    transitive_headers = [hdr[ExampleInfo].headers for hdr in ctx.attr.hdrs]
```

There's a legacy struct style, which is strongly discouraged and rules should be
[migrated away from it](#migrating_from_legacy_providers).

### Files

Files are represented by [`File`](/rules/lib/builtins/File) objects. Since Bazel doesn't
perform file I/O during the analysis phase, these objects can't be used to
directly read or write file content. Rather, they are passed to action-emitting
functions (see [`ctx.actions`](/rules/lib/builtins/actions)) to construct pieces of the
action graph.

A `File` can either be a source file or a generated file. Each generated file
must be an output of exactly one action. Source files can't be the output of
any action.

For each dependency attribute, the corresponding field of
[`ctx.files`](/rules/lib/builtins/ctx#files) contains a list of the default outputs of all
dependencies using that attribute:

```python
def _example_library_impl(ctx):
    ...
    headers = depset(ctx.files.hdrs, transitive = transitive_headers)
    srcs = ctx.files.srcs
    ...
```

[`ctx.file`](/rules/lib/builtins/ctx#file) contains a single `File` or `None` for
dependency attributes whose specs set `allow_single_file = True`.
[`ctx.executable`](/rules/lib/builtins/ctx#executable) behaves the same as `ctx.file`, but only
contains fields for dependency attributes whose specs set `executable = True`.

### Declaring outputs

During the analysis phase, a rule's implementation function can create outputs.
Since all labels have to be known during the loading phase, these additional
outputs have no labels. `File` objects for outputs can be created using
[`ctx.actions.declare_file`](/rules/lib/builtins/actions#declare_file) and
[`ctx.actions.declare_directory`](/rules/lib/builtins/actions#declare_directory).
Often, the names of outputs are based on the target's name,
[`ctx.label.name`](/rules/lib/builtins/ctx#label):

```python
def _example_library_impl(ctx):
  ...
  output_file = ctx.actions.declare_file(ctx.label.name + ".output")
  ...
```

For *predeclared outputs*, like those created for
[output attributes](#output_attributes), `File` objects instead can be retrieved
from the corresponding fields of [`ctx.outputs`](/rules/lib/builtins/ctx#outputs).

### Actions

An action describes how to generate a set of outputs from a set of inputs, for
example "run gcc on hello.c and get hello.o". When an action is created, Bazel
doesn't run the command immediately. It registers it in a graph of dependencies,
because an action can depend on the output of another action. For example, in C,
the linker must be called after the compiler.

General-purpose functions that create actions are defined in
[`ctx.actions`](/rules/lib/builtins/actions):

*   [`ctx.actions.run`](/rules/lib/builtins/actions#run), to run an executable.
*   [`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell), to run a shell
    command.
*   [`ctx.actions.write`](/rules/lib/builtins/actions#write), to write a string to a file.
*   [`ctx.actions.expand_template`](/rules/lib/builtins/actions#expand_template), to
    generate a file from a template.

[`ctx.actions.args`](/rules/lib/builtins/actions#args) can be used to efficiently
accumulate the arguments for actions. It avoids flattening depsets until
execution time:

```python
def _example_library_impl(ctx):
    ...

    transitive_headers = [dep[ExampleInfo].headers for dep in ctx.attr.deps]
    headers = depset(ctx.files.hdrs, transitive = transitive_headers)
    srcs = ctx.files.srcs
    inputs = depset(srcs, transitive = [headers])
    output_file = ctx.actions.declare_file(ctx.label.name + ".output")

    args = ctx.actions.args()
    args.add_joined("-h", headers, join_with = ",")
    args.add_joined("-s", srcs, join_with = ",")
    args.add("-o", output_file)

    ctx.actions.run(
        mnemonic = "ExampleCompile",
        executable = ctx.executable._compiler,
        arguments = [args],
        inputs = inputs,
        outputs = [output_file],
    )
    ...
```

Actions take a list or depset of input files and generate a (non-empty) list of
output files. The set of input and output files must be known during the
[analysis phase](/extending/concepts#evaluation-model). It might depend on the value of
attributes, including providers from dependencies, but it can't depend on the
result of the execution. For example, if your action runs the unzip command, you
must specify which files you expect to be inflated (before running unzip).
Actions which create a variable number of files internally can wrap those in a
single file (such as a zip, tar, or other archive format).

Actions must list all of their inputs. Listing inputs that are not used is
permitted, but inefficient.

Actions must create all of their outputs. They may write other files, but
anything not in outputs won't be available to consumers. All declared outputs
must be written by some action.

Actions are comparable to pure functions: They should depend only on the
provided inputs, and avoid accessing computer information, username, clock,
network, or I/O devices (except for reading inputs and writing outputs). This is
important because the output will be cached and reused.

Dependencies are resolved by Bazel, which decides which actions to
execute. It is an error if there is a cycle in the dependency graph. Creating
an action doesn't guarantee that it will be executed, that depends on whether
its outputs are needed for the build.

### Providers

Providers are pieces of information that a rule exposes to other rules that
depend on it. This data can include output files, libraries, parameters to pass
on a tool's command line, or anything else a target's consumers should know
about.

Since a rule's implementation function can only read providers from the
instantiated target's immediate dependencies, rules need to forward any
information from a target's dependencies that needs to be known by a target's
consumers, generally by accumulating that into a [`depset`](/rules/lib/builtins/depset).

A target's providers are specified by a list of provider objects returned by
the implementation function.

Old implementation functions can also be written in a legacy style where the
implementation function returns a [`struct`](/rules/lib/builtins/struct) instead of list of
provider objects. This style is strongly discouraged and rules should be
[migrated away from it](#migrating_from_legacy_providers).

#### Default outputs

A target's *default outputs* are the outputs that are requested by default when
the target is requested for build at the command line. For example, a
`java_library` target `//pkg:foo` has `foo.jar` as a default output, so that
will be built by the command `bazel build //pkg:foo`.

Default outputs are specified by the `files` parameter of
[`DefaultInfo`](/rules/lib/providers/DefaultInfo):

```python
def _example_library_impl(ctx):
    ...
    return [
        DefaultInfo(files = depset([output_file]), ...),
        ...
    ]
```

If `DefaultInfo` is not returned by a rule implementation or the `files`
parameter is not specified, `DefaultInfo.files` defaults to all
*predeclared outputs* (generally, those created by [output
attributes](#output_attributes)).

Rules that perform actions should provide default outputs, even if those outputs
are not expected to be directly used. Actions that are not in the graph of the
requested outputs are pruned. If an output is only used by a target's consumers,
those actions won't be performed when the target is built in isolation. This
makes debugging more difficult because rebuilding just the failing target won't
reproduce the failure.

#### Runfiles

Runfiles are a set of files used by a target at runtime (as opposed to build
time). During the [execution phase](/extending/concepts#evaluation-model), Bazel creates
a directory tree containing symlinks pointing to the runfiles. This stages the
environment for the binary so it can access the runfiles during runtime.

Runfiles can be added manually during rule creation.
[`runfiles`](/rules/lib/builtins/runfiles) objects can be created by the `runfiles` method
on the rule context, [`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles) and passed to the
`runfiles` parameter on `DefaultInfo`. The executable output of
[executable rules](#executable-rules) is implicitly added to the runfiles.

Some rules specify attributes, generally named
[`data`](/reference/be/common-definitions#common.data), whose outputs are added to
a targets' runfiles. Runfiles should also be merged in from `data`, as well as
from any attributes which might provide code for eventual execution, generally
`srcs` (which might contain `filegroup` targets with associated `data`) and
`deps`.

```python
def _example_library_impl(ctx):
    ...
    runfiles = ctx.runfiles(files = ctx.files.data)
    transitive_runfiles = []
    for runfiles_attr in (
        ctx.attr.srcs,
        ctx.attr.hdrs,
        ctx.attr.deps,
        ctx.attr.data,
    ):
        for target in runfiles_attr:
            transitive_runfiles.append(target[DefaultInfo].default_runfiles)
    runfiles = runfiles.merge_all(transitive_runfiles)
    return [
        DefaultInfo(..., runfiles = runfiles),
        ...
    ]
```

#### Custom providers

Providers can be defined using the [`provider`](/rules/lib/globals/bzl#provider)
function to convey rule-specific information:

```python
ExampleInfo = provider(
    "Info needed to compile/link Example code.",
    fields = {
        "headers": "depset of header Files from transitive dependencies.",
        "files_to_link": "depset of Files from compilation.",
    },
)
```

Rule implementation functions can then construct and return provider instances:

```python
def _example_library_impl(ctx):
  ...
  return [
      ...
      ExampleInfo(
          headers = headers,
          files_to_link = depset(
              [output_file],
              transitive = [
                  dep[ExampleInfo].files_to_link for dep in ctx.attr.deps
              ],
          ),
      )
  ]
```

##### Custom initialization of providers

It's possible to guard the instantiation of a provider with custom
preprocessing and validation logic. This can be used to ensure that all
provider instances satisfy certain invariants, or to give users a cleaner API for
obtaining an instance.

This is done by passing an `init` callback to the
[`provider`](/rules/lib/globals/bzl.html#provider) function. If this callback is given, the
return type of `provider()` changes to be a tuple of two values: the provider
symbol that is the ordinary return value when `init` is not used, and a "raw
constructor".

In this case, when the provider symbol is called, instead of directly returning
a new instance, it will forward the arguments along to the `init` callback. The
callback's return value must be a dict mapping field names (strings) to values;
this is used to initialize the fields of the new instance. Note that the
callback may have any signature, and if the arguments don't match the signature
an error is reported as if the callback were invoked directly.

The raw constructor, by contrast, will bypass the `init` callback.

The following example uses `init` to preprocess and validate its arguments:

```python
# //pkg:exampleinfo.bzl

_core_headers = [...]  # private constant representing standard library files

# Keyword-only arguments are preferred.
def _exampleinfo_init(*, files_to_link, headers = None, allow_empty_files_to_link = False):
    if not files_to_link and not allow_empty_files_to_link:
        fail("files_to_link may not be empty")
    all_headers = depset(_core_headers, transitive = headers)
    return {"files_to_link": files_to_link, "headers": all_headers}

ExampleInfo, _new_exampleinfo = provider(
    fields = ["files_to_link", "headers"],
    init = _exampleinfo_init,
)
```

A rule implementation may then instantiate the provider as follows:

```python
ExampleInfo(
    files_to_link = my_files_to_link,  # may not be empty
    headers = my_headers,  # will automatically include the core headers
)
```

The raw constructor can be used to define alternative public factory functions
that don't go through the `init` logic. For example, exampleinfo.bzl
could define:

```python
def make_barebones_exampleinfo(headers):
    """Returns an ExampleInfo with no files_to_link and only the specified headers."""
    return _new_exampleinfo(files_to_link = depset(), headers = all_headers)
```

Typically, the raw constructor is bound to a variable whose name begins with an
underscore (`_new_exampleinfo` above), so that user code can't load it and
generate arbitrary provider instances.

Another use for `init` is to prevent the user from calling the provider
symbol altogether, and force them to use a factory function instead:

```python
def _exampleinfo_init_banned(*args, **kwargs):
    fail("Do not call ExampleInfo(). Use make_exampleinfo() instead.")

ExampleInfo, _new_exampleinfo = provider(
    ...
    init = _exampleinfo_init_banned)

def make_exampleinfo(...):
    ...
    return _new_exampleinfo(...)
```

<a name="executable-rules"></a>

## Executable rules and test rules

Executable rules define targets that can be invoked by a `bazel run` command.
Test rules are a special kind of executable rule whose targets can also be
invoked by a `bazel test` command. Executable and test rules are created by
setting the respective [`executable`](/rules/lib/globals/bzl#rule.executable) or
[`test`](/rules/lib/globals/bzl#rule.test) argument to `True` in the call to `rule`:

```python
example_binary = rule(
   implementation = _example_binary_impl,
   executable = True,
   ...
)

example_test = rule(
   implementation = _example_binary_impl,
   test = True,
   ...
)
```

Test rules must have names that end in `_test`. (Test *target* names also often
end in `_test` by convention, but this is not required.) Non-test rules must not
have this suffix.

Both kinds of rules must produce an executable output file (which may or may not
be predeclared) that will be invoked by the `run` or `test` commands. To tell
Bazel which of a rule's outputs to use as this executable, pass it as the
`executable` argument of a returned [`DefaultInfo`](/rules/lib/providers/DefaultInfo)
provider. That `executable` is added to the default outputs of the rule (so you
don't need to pass that to both `executable` and `files`). It's also implicitly
added to the [runfiles](#runfiles):

```python
def _example_binary_impl(ctx):
    executable = ctx.actions.declare_file(ctx.label.name)
    ...
    return [
        DefaultInfo(executable = executable, ...),
        ...
    ]
```

The action that generates this file must set the executable bit on the file. For
a [`ctx.actions.run`](/rules/lib/builtins/actions#run) or
[`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell) action this should be done
by the underlying tool that is invoked by the action. For a
[`ctx.actions.write`](/rules/lib/builtins/actions#write) action, pass `is_executable = True`.

As [legacy behavior](#deprecated_predeclared_outputs), executable rules have a
special `ctx.outputs.executable` predeclared output. This file serves as the
default executable if you don't specify one using `DefaultInfo`; it must not be
used otherwise. This output mechanism is deprecated because it doesn't support
customizing the executable file's name at analysis time.

See examples of an
[executable rule](https://github.com/bazelbuild/examples/blob/main/rules/executable/fortune.bzl){: .external}
and a
[test rule](https://github.com/bazelbuild/examples/blob/main/rules/test_rule/line_length.bzl){: .external}.

[Executable rules](/reference/be/common-definitions#common-attributes-binaries) and
[test rules](/reference/be/common-definitions#common-attributes-tests) have additional
attributes implicitly defined, in addition to those added for
[all rules](/reference/be/common-definitions#common-attributes). The defaults of
implicitly-added attributes can't be changed, though this can be worked around
by wrapping a private rule in a [Starlark macro](/extending/macros) which alters the
default:

```python
def example_test(size = "small", **kwargs):
  _example_test(size = size, **kwargs)

_example_test = rule(
 ...
)
```

### Runfiles location

When an executable target is run with `bazel run` (or `test`), the root of the
runfiles directory is adjacent to the executable. The paths relate as follows:

```python
# Given launcher_path and runfile_file:
runfiles_root = launcher_path.path + ".runfiles"
workspace_name = ctx.workspace_name
runfile_path = runfile_file.short_path
execution_root_relative_path = "%s/%s/%s" % (
    runfiles_root, workspace_name, runfile_path)
```

The path to a `File` under the runfiles directory corresponds to
[`File.short_path`](/rules/lib/builtins/File#short_path).

The binary executed directly by `bazel` is adjacent to the root of the
`runfiles` directory. However, binaries called *from* the runfiles can't make
the same assumption. To mitigate this, each binary should provide a way to
accept its runfiles root as a parameter using an environment, or command line
argument or flag. This allows binaries to pass the correct canonical runfiles root
to the binaries it calls. If that's not set, a binary can guess that it was the
first binary called and look for an adjacent runfiles directory.

## Advanced topics

### Requesting output files

A single target can have several output files. When a `bazel build` command is
run, some of the outputs of the targets given to the command are considered to
be *requested*. Bazel only builds these requested files and the files that they
directly or indirectly depend on. (In terms of the action graph, Bazel only
executes the actions that are reachable as transitive dependencies of the
requested files.)

In addition to [default outputs](#default_outputs), any *predeclared output* can
be explicitly requested on the command line. Rules can specify predeclared
outputs using [output attributes](#output_attributes). In that case, the user
explicitly chooses labels for outputs when they instantiate the rule. To obtain
[`File`](/rules/lib/builtins/File) objects for output attributes, use the corresponding
attribute of [`ctx.outputs`](/rules/lib/builtins/ctx#outputs). Rules can
[implicitly define predeclared outputs](#deprecated_predeclared_outputs) based
on the target name as well, but this feature is deprecated.

In addition to default outputs, there are *output groups*, which are collections
of output files that may be requested together. These can be requested with
[`--output_groups`](/reference/command-line-reference#flag--output_groups). For
example, if a target `//pkg:mytarget` is of a rule type that has a `debug_files`
output group, these files can be built by running `bazel build //pkg:mytarget
--output_groups=debug_files`. Since non-predeclared outputs don't have labels,
they can only be requested by appearing in the default outputs or an output
group.

Output groups can be specified with the
[`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo) provider. Note that unlike many
built-in providers, `OutputGroupInfo` can take parameters with arbitrary names
to define output groups with that name:

```python
def _example_library_impl(ctx):
    ...
    debug_file = ctx.actions.declare_file(name + ".pdb")
    ...
    return [
        DefaultInfo(files = depset([output_file]), ...),
        OutputGroupInfo(
            debug_files = depset([debug_file]),
            all_files = depset([output_file, debug_file]),
        ),
        ...
    ]
```

Also unlike most providers, `OutputGroupInfo` can be returned by both an
[aspect](/extending/aspects) and the rule target to which that aspect is applied, as
long as they don't define the same output groups. In that case, the resulting
providers are merged.

Note that `OutputGroupInfo` generally shouldn't be used to convey specific sorts
of files from a target to the actions of its consumers. Define
[rule-specific providers](#custom_providers) for that instead.

### Configurations

Imagine that you want to build a C++ binary for a different architecture. The
build can be complex and involve multiple steps. Some of the intermediate
binaries, like compilers and code generators, have to run on
[the execution platform](/extending/platforms#overview) (which could be your host,
or a remote executor). Some binaries like the final output must be built for the
target architecture.

For this reason, Bazel has a concept of "configurations" and transitions. The
topmost targets (the ones requested on the command line) are built-in the
"target" configuration, while tools that should run on the execution platform
are built-in an "exec" configuration. Rules may generate different actions based
on the configuration, for instance to change the cpu architecture that is passed
to the compiler. In some cases, the same library may be needed for different
configurations. If this happens, it will be analyzed and potentially built
multiple times.

By default, Bazel builds a target's dependencies in the same configuration as
the target itself, in other words without transitions. When a dependency is a
tool that's needed to help build the target, the corresponding attribute should
specify a transition to an exec configuration. This causes the tool and all its
dependencies to build for the execution platform.

For each dependency attribute, you can use `cfg` to decide if dependencies
should build in the same configuration or transition to an exec configuration.
If a dependency attribute has the flag `executable = True`, `cfg` must be set
explicitly. This is to guard against accidentally building a tool for the wrong
configuration.
[See example](https://github.com/bazelbuild/examples/blob/main/rules/actions_run/execute.bzl){: .external}

In general, sources, dependent libraries, and executables that will be needed at
runtime can use the same configuration.

Tools that are executed as part of the build (such as compilers or code generators)
should be built for an exec configuration. In this case, specify `cfg = "exec"` in
the attribute.

Otherwise, executables that are used at runtime (such as as part of a test) should
be built for the target configuration. In this case, specify `cfg = "target"` in
the attribute.

`cfg = "target"` doesn't actually do anything: it's purely a convenience value to
help rule designers be explicit about their intentions. When `executable = False`,
which means `cfg` is optional, only set this when it truly helps readability.

You can also use `cfg = my_transition` to use
[user-defined transitions](/extending/config#user-defined-transitions), which allow
rule authors a great deal of flexibility in changing configurations, with the
drawback of
[making the build graph larger and less comprehensible](/extending/config#memory-and-performance-considerations).

**Note**: Historically, Bazel didn't have the concept of execution platforms,
and instead all build actions were considered to run on the host machine. Bazel
versions before 6.0 created a distinct "host" configuration to represent this.
If you see references to "host" in code or old documentation, that's what this
refers to. We recommend using Bazel 6.0 or newer to avoid this extra conceptual
overhead.

<a name="fragments"></a>

### Configuration fragments

Rules may access
[configuration fragments](/rules/lib/fragments) such as
`cpp` and `java`. However, all required fragments must be declared in
order to avoid access errors:

```python
def _impl(ctx):
    # Using ctx.fragments.cpp leads to an error since it was not declared.
    x = ctx.fragments.java
    ...

my_rule = rule(
    implementation = _impl,
    fragments = ["java"],      # Required fragments of the target configuration
    ...
)
```

### Runfiles symlinks

Normally, the relative path of a file in the runfiles tree is the same as the
relative path of that file in the source tree or generated output tree. If these
need to be different for some reason, you can specify the `root_symlinks` or
`symlinks` arguments. The `root_symlinks` is a dictionary mapping paths to
files, where the paths are relative to the root of the runfiles directory. The
`symlinks` dictionary is the same, but paths are implicitly prefixed with the
name of the main workspace (*not* the name of the repository containing the
current target).

```python
    ...
    runfiles = ctx.runfiles(
        root_symlinks = {"some/path/here.foo": ctx.file.some_data_file2}
        symlinks = {"some/path/here.bar": ctx.file.some_data_file3}
    )
    # Creates something like:
    # sometarget.runfiles/
    #     some/
    #         path/
    #             here.foo -> some_data_file2
    #     <workspace_name>/
    #         some/
    #             path/
    #                 here.bar -> some_data_file3
```

If `symlinks` or `root_symlinks` is used, be careful not to map two different
files to the same path in the runfiles tree. This will cause the build to fail
with an error describing the conflict. To fix, you will need to modify your
`ctx.runfiles` arguments to remove the collision. This checking will be done for
any targets using your rule, as well as targets of any kind that depend on those
targets. This is especially risky if your tool is likely to be used transitively
by another tool; symlink names must be unique across the runfiles of a tool and
all of its dependencies.

### Code coverage

When the [`coverage`](/reference/command-line-reference#coverage) command is run,
the build may need to add coverage instrumentation for certain targets. The
build also gathers the list of source files that are instrumented. The subset of
targets that are considered is controlled by the flag
[`--instrumentation_filter`](/reference/command-line-reference#flag--instrumentation_filter).
Test targets are excluded, unless
[`--instrument_test_targets`](/reference/command-line-reference#flag--instrument_test_targets)
is specified.

If a rule implementation adds coverage instrumentation at build time, it needs
to account for that in its implementation function.
[ctx.coverage_instrumented](/rules/lib/builtins/ctx#coverage_instrumented) returns
`True` in coverage mode if a target's sources should be instrumented:

```python
# Are this rule's sources instrumented?
if ctx.coverage_instrumented():
  # Do something to turn on coverage for this compile action
```

Logic that always needs to be on in coverage mode (whether a target's sources
specifically are instrumented or not) can be conditioned on
[ctx.configuration.coverage_enabled](/rules/lib/builtins/configuration#coverage_enabled).

If the rule directly includes sources from its dependencies before compilation
(such as header files), it may also need to turn on compile-time instrumentation if
the dependencies' sources should be instrumented:

```python
# Are this rule's sources or any of the sources for its direct dependencies
# in deps instrumented?
if (ctx.configuration.coverage_enabled and
    (ctx.coverage_instrumented() or
     any([ctx.coverage_instrumented(dep) for dep in ctx.attr.deps]))):
    # Do something to turn on coverage for this compile action
```

Rules also should provide information about which attributes are relevant for
coverage with the `InstrumentedFilesInfo` provider, constructed using
[`coverage_common.instrumented_files_info`](/rules/lib/toplevel/coverage_common#instrumented_files_info).
The `dependency_attributes` parameter of `instrumented_files_info` should list
all runtime dependency attributes, including code dependencies like `deps` and
data dependencies like `data`. The `source_attributes` parameter should list the
rule's source files attributes if coverage instrumentation might be added:

```python
def _example_library_impl(ctx):
    ...
    return [
        ...
        coverage_common.instrumented_files_info(
            ctx,
            dependency_attributes = ["deps", "data"],
            # Omitted if coverage is not supported for this rule:
            source_attributes = ["srcs", "hdrs"],
        )
        ...
    ]
```

If `InstrumentedFilesInfo` is not returned, a default one is created with each
non-tool [dependency attribute](#dependency_attributes) that doesn't set
[`cfg`](#configuration) to `"exec"` in the attribute schema. in
`dependency_attributes`. (This isn't ideal behavior, since it puts attributes
like `srcs` in `dependency_attributes` instead of `source_attributes`, but it
avoids the need for explicit coverage configuration for all rules in the
dependency chain.)

### Validation Actions

Sometimes you need to validate something about the build, and the
information required to do that validation is available only in artifacts
(source files or generated files). Because this information is in artifacts,
rules can't do this validation at analysis time because rules can't read
files. Instead, actions must do this validation at execution time. When
validation fails, the action will fail, and hence so will the build.

Examples of validations that might be run are static analysis, linting,
dependency and consistency checks, and style checks.

Validation actions can also help to improve build performance by moving parts
of actions that are not required for building artifacts into separate actions.
For example, if a single action that does compilation and linting can be
separated into a compilation action and a linting action, then the linting
action can be run as a validation action and run in parallel with other actions.

These "validation actions" often don't produce anything that is used elsewhere
in the build, since they only need to assert things about their inputs. This
presents a problem though: If a validation action doesn't produce anything that
is used elsewhere in the build, how does a rule get the action to run?
Historically, the approach was to have the validation action output an empty
file, and artificially add that output to the inputs of some other important
action in the build:

<img src="/rules/validation_action_historical.svg" width="35%" />

This works, because Bazel will always run the validation action when the compile
action is run, but this has significant drawbacks:

1. The validation action is in the critical path of the build. Because Bazel
thinks the empty output is required to run the compile action, it will run the
validation action first, even though the compile action will ignore the input.
This reduces parallelism and slows down builds.

2. If other actions in the build might run instead of the
compile action, then the empty outputs of validation actions need to be added to
those actions as well (`java_library`'s source jar output, for example). This is
also a problem if new actions that might run instead of the compile action are
added later, and the empty validation output is accidentally left off.

The solution to these problems is to use the Validations Output Group.

#### Validations Output Group

The Validations Output Group is an output group designed to hold the otherwise
unused outputs of validation actions, so that they don't need to be artificially
added to the inputs of other actions.

This group is special in that its outputs are always requested, regardless of
the value of the `--output_groups` flag, and regardless of how the target is
depended upon (for example, on the command line, as a dependency, or through
implicit outputs of the target). Note that normal caching and incrementality
still apply: if the inputs to the validation action have not changed and the
validation action previously succeeded, then the validation action won't be
run.

<img src="/rules/validation_action.svg" width="35%" />

Using this output group still requires that validation actions output some file,
even an empty one. This might require wrapping some tools that normally don't
create outputs so that a file is created.

A target's validation actions are not run in three cases:

*    When the target is depended upon as a tool
*    When the target is depended upon as an implicit dependency (for example, an
     attribute that starts with "_")
*    When the target is built in the exec configuration.

It is assumed that these targets have their own
separate builds and tests that would uncover any validation failures.

#### Using the Validations Output Group

The Validations Output Group is named `_validation` and is used like any other
output group:

```python
def _rule_with_validation_impl(ctx):

  ctx.actions.write(ctx.outputs.main, "main output\n")
  ctx.actions.write(ctx.outputs.implicit, "implicit output\n")

  validation_output = ctx.actions.declare_file(ctx.attr.name + ".validation")
  ctx.actions.run(
    outputs = [validation_output],
    executable = ctx.executable._validation_tool,
    arguments = [validation_output.path],
  )

  return [
    DefaultInfo(files = depset([ctx.outputs.main])),
    OutputGroupInfo(_validation = depset([validation_output])),
  ]


rule_with_validation = rule(
  implementation = _rule_with_validation_impl,
  outputs = {
    "main": "%{name}.main",
    "implicit": "%{name}.implicit",
  },
  attrs = {
    "_validation_tool": attr.label(
        default = Label("//validation_actions:validation_tool"),
        executable = True,
        cfg = "exec"
    ),
  }
)
```

Notice that the validation output file is not added to the `DefaultInfo` or the
inputs to any other action. The validation action for a target of this rule kind
will still run if the target is depended upon by label, or any of the target's
implicit outputs are directly or indirectly depended upon.

It is usually important that the outputs of validation actions only go into the
validation output group, and are not added to the inputs of other actions, as
this could defeat parallelism gains. Note however that Bazel doesn't
have any special checking to enforce this. Therefore, you should test
that validation action outputs are not added to the inputs of any actions in the
tests for Starlark rules. For example:

```python
load("@bazel_skylib//lib:unittest.bzl", "analysistest")

def _validation_outputs_test_impl(ctx):
  env = analysistest.begin(ctx)

  actions = analysistest.target_actions(env)
  target = analysistest.target_under_test(env)
  validation_outputs = target.output_groups._validation.to_list()
  for action in actions:
    for validation_output in validation_outputs:
      if validation_output in action.inputs.to_list():
        analysistest.fail(env,
            "%s is a validation action output, but is an input to action %s" % (
                validation_output, action))

  return analysistest.end(env)

validation_outputs_test = analysistest.make(_validation_outputs_test_impl)
```

#### Validation Actions Flag

Running validation actions is controlled by the `--run_validations` command line
flag, which defaults to true.

## Deprecated features

### Deprecated predeclared outputs

There are two **deprecated** ways of using predeclared outputs:

*   The [`outputs`](/rules/lib/globals/bzl#rule.outputs) parameter of `rule` specifies
    a mapping between output attribute names and string templates for generating
    predeclared output labels. Prefer using non-predeclared outputs and
    explicitly adding outputs to `DefaultInfo.files`. Use the rule target's
    label as input for rules which consume the output instead of a predeclared
    output's label.

*   For [executable rules](#executable-rules), `ctx.outputs.executable` refers
    to a predeclared executable output with the same name as the rule target.
    Prefer declaring the output explicitly, for example with
    `ctx.actions.declare_file(ctx.label.name)`, and ensure that the command that
    generates the executable sets its permissions to allow execution. Explicitly
    pass the executable output to the `executable` parameter of `DefaultInfo`.

### Runfiles features to avoid

[`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles) and the [`runfiles`](/rules/lib/builtins/runfiles)
type have a complex set of features, many of which are kept for legacy reasons.
The following recommendations help reduce complexity:

*   **Avoid** use of the `collect_data` and `collect_default` modes of
    [`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles). These modes implicitly collect
    runfiles across certain hardcoded dependency edges in confusing ways.
    Instead, add files using the `files` or `transitive_files` parameters of
    `ctx.runfiles`, or by merging in runfiles from dependencies with
    `runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)`.

*   **Avoid** use of the `data_runfiles` and `default_runfiles` of the
    `DefaultInfo` constructor. Specify `DefaultInfo(runfiles = ...)` instead.
    The distinction between "default" and "data" runfiles is maintained for
    legacy reasons. For example, some rules put their default outputs in
    `data_runfiles`, but not `default_runfiles`. Instead of using
    `data_runfiles`, rules should *both* include default outputs and merge in
    `default_runfiles` from attributes which provide runfiles (often
    [`data`](/reference/be/common-definitions#common-attributes.data)).

*   When retrieving `runfiles` from `DefaultInfo` (generally only for merging
    runfiles between the current rule and its dependencies), use
    `DefaultInfo.default_runfiles`, **not** `DefaultInfo.data_runfiles`.

### Migrating from legacy providers

Historically, Bazel providers were simple fields on the `Target` object. They
were accessed using the dot operator, and they were created by putting the field
in a [`struct`](/rules/lib/builtins/struct) returned by the rule's
implementation function instead of a list of provider objects:

```python
return struct(example_info = struct(headers = depset(...)))
```

Such providers can be retrieved from the corresponding field of the `Target` object:

```python
transitive_headers = [hdr.example_info.headers for hdr in ctx.attr.hdrs]
```

*This style is deprecated and should not be used in new code;* see following for
information that may help you migrate. The new provider mechanism avoids name
clashes. It also supports data hiding, by requiring any code accessing a
provider instance to retrieve it using the provider symbol.

For the moment, legacy providers are still supported. A rule can return both
legacy and modern providers as follows:

```python
def _old_rule_impl(ctx):
  ...
  legacy_data = struct(x = "foo", ...)
  modern_data = MyInfo(y = "bar", ...)
  # When any legacy providers are returned, the top-level returned value is a
  # struct.
  return struct(
      # One key = value entry for each legacy provider.
      legacy_info = legacy_data,
      ...
      # Additional modern providers:
      providers = [modern_data, ...])
```

If `dep` is the resulting `Target` object for an instance of this rule, the
providers and their contents can be retrieved as `dep.legacy_info.x` and
`dep[MyInfo].y`.

In addition to `providers`, the returned struct can also take several other
fields that have special meaning (and thus don't create a corresponding legacy
provider):

*   The fields `files`, `runfiles`, `data_runfiles`, `default_runfiles`, and
    `executable` correspond to the same-named fields of
    [`DefaultInfo`](/rules/lib/providers/DefaultInfo). It is not allowed to specify any of
    these fields while also returning a `DefaultInfo` provider.

*   The field `output_groups` takes a struct value and corresponds to an
    [`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo).

In [`provides`](/rules/lib/globals/bzl#rule.provides) declarations of rules, and in
[`providers`](/rules/lib/toplevel/attr#label_list.providers) declarations of dependency
attributes, legacy providers are passed in as strings and modern providers are
passed in by their `Info` symbol. Be sure to change from strings to symbols
when migrating. For complex or large rule sets where it is difficult to update
all rules atomically, you may have an easier time if you follow this sequence of
steps:

1.  Modify the rules that produce the legacy provider to produce both the legacy
    and modern providers, using the preceding syntax. For rules that declare they
    return the legacy provider, update that declaration to include both the
    legacy and modern providers.

2.  Modify the rules that consume the legacy provider to instead consume the
    modern provider. If any attribute declarations require the legacy provider,
    also update them to instead require the modern provider. Optionally, you can
    interleave this work with step 1 by having consumers accept or require either
    provider: Test for the presence of the legacy provider using
    `hasattr(target, 'foo')`, or the new provider using `FooInfo in target`.

3.  Fully remove the legacy provider from all rules.


Project: /_project.yaml
Book: /_book.yaml

# Toolchains

{% include "_buttons.html" %}

This page describes the toolchain framework, which is a way for rule authors to
decouple their rule logic from platform-based selection of tools. It is
recommended to read the [rules](/extending/rules) and [platforms](/extending/platforms)
pages before continuing. This page covers why toolchains are needed, how to
define and use them, and how Bazel selects an appropriate toolchain based on
platform constraints.

## Motivation {:#motivation}

Let's first look at the problem toolchains are designed to solve. Suppose you
are writing rules to support the "bar" programming language. Your `bar_binary`
rule would compile `*.bar` files using the `barc` compiler, a tool that itself
is built as another target in your workspace. Since users who write `bar_binary`
targets shouldn't have to specify a dependency on the compiler, you make it an
implicit dependency by adding it to the rule definition as a private attribute.

```python
bar_binary = rule(
    implementation = _bar_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        ...
        "_compiler": attr.label(
            default = "//bar_tools:barc_linux",  # the compiler running on linux
            providers = [BarcInfo],
        ),
    },
)
```

`//bar_tools:barc_linux` is now a dependency of every `bar_binary` target, so
it'll be built before any `bar_binary` target. It can be accessed by the rule's
implementation function just like any other attribute:

```python
BarcInfo = provider(
    doc = "Information about how to invoke the barc compiler.",
    # In the real world, compiler_path and system_lib might hold File objects,
    # but for simplicity they are strings for this example. arch_flags is a list
    # of strings.
    fields = ["compiler_path", "system_lib", "arch_flags"],
)

def _bar_binary_impl(ctx):
    ...
    info = ctx.attr._compiler[BarcInfo]
    command = "%s -l %s %s" % (
        info.compiler_path,
        info.system_lib,
        " ".join(info.arch_flags),
    )
    ...
```

The issue here is that the compiler's label is hardcoded into `bar_binary`, yet
different targets may need different compilers depending on what platform they
are being built for and what platform they are being built on -- called the
*target platform* and *execution platform*, respectively. Furthermore, the rule
author does not necessarily even know all the available tools and platforms, so
it is not feasible to hardcode them in the rule's definition.

A less-than-ideal solution would be to shift the burden onto users, by making
the `_compiler` attribute non-private. Then individual targets could be
hardcoded to build for one platform or another.

```python
bar_binary(
    name = "myprog_on_linux",
    srcs = ["mysrc.bar"],
    compiler = "//bar_tools:barc_linux",
)

bar_binary(
    name = "myprog_on_windows",
    srcs = ["mysrc.bar"],
    compiler = "//bar_tools:barc_windows",
)
```

You can improve on this solution by using `select` to choose the `compiler`
[based on the platform](/docs/configurable-attributes):

```python
config_setting(
    name = "on_linux",
    constraint_values = [
        "@platforms//os:linux",
    ],
)

config_setting(
    name = "on_windows",
    constraint_values = [
        "@platforms//os:windows",
    ],
)

bar_binary(
    name = "myprog",
    srcs = ["mysrc.bar"],
    compiler = select({
        ":on_linux": "//bar_tools:barc_linux",
        ":on_windows": "//bar_tools:barc_windows",
    }),
)
```

But this is tedious and a bit much to ask of every single `bar_binary` user.
If this style is not used consistently throughout the workspace, it leads to
builds that work fine on a single platform but fail when extended to
multi-platform scenarios. It also does not address the problem of adding support
for new platforms and compilers without modifying existing rules or targets.

The toolchain framework solves this problem by adding an extra level of
indirection. Essentially, you declare that your rule has an abstract dependency
on *some* member of a family of targets (a toolchain type), and Bazel
automatically resolves this to a particular target (a toolchain) based on the
applicable platform constraints. Neither the rule author nor the target author
need know the complete set of available platforms and toolchains.

## Writing rules that use toolchains {:#writing-rules-toolchains}

Under the toolchain framework, instead of having rules depend directly on tools,
they instead depend on *toolchain types*. A toolchain type is a simple target
that represents a class of tools that serve the same role for different
platforms. For instance, you can declare a type that represents the bar
compiler:

```python
# By convention, toolchain_type targets are named "toolchain_type" and
# distinguished by their package path. So the full path for this would be
# //bar_tools:toolchain_type.
toolchain_type(name = "toolchain_type")
```

The rule definition in the previous section is modified so that instead of
taking in the compiler as an attribute, it declares that it consumes a
`//bar_tools:toolchain_type` toolchain.

```python
bar_binary = rule(
    implementation = _bar_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        ...
        # No `_compiler` attribute anymore.
    },
    toolchains = ["//bar_tools:toolchain_type"],
)
```

The implementation function now accesses this dependency under `ctx.toolchains`
instead of `ctx.attr`, using the toolchain type as the key.

```python
def _bar_binary_impl(ctx):
    ...
    info = ctx.toolchains["//bar_tools:toolchain_type"].barcinfo
    # The rest is unchanged.
    command = "%s -l %s %s" % (
        info.compiler_path,
        info.system_lib,
        " ".join(info.arch_flags),
    )
    ...
```

`ctx.toolchains["//bar_tools:toolchain_type"]` returns the
[`ToolchainInfo` provider](/rules/lib/toplevel/platform_common#ToolchainInfo)
of whatever target Bazel resolved the toolchain dependency to. The fields of the
`ToolchainInfo` object are set by the underlying tool's rule; in the next
section, this rule is defined such that there is a `barcinfo` field that wraps
a `BarcInfo` object.

Bazel's procedure for resolving toolchains to targets is described
[below](#toolchain-resolution). Only the resolved toolchain target is actually
made a dependency of the `bar_binary` target, not the whole space of candidate
toolchains.

### Mandatory and Optional Toolchains {:#optional-toolchains}

By default, when a rule expresses a toolchain type dependency using a bare label
(as shown above), the toolchain type is considered to be **mandatory**. If Bazel
is unable to find a matching toolchain (see
[Toolchain resolution](#toolchain-resolution) below) for a mandatory toolchain
type, this is an error and analysis halts.

It is possible instead to declare an **optional** toolchain type dependency, as
follows:

```python
bar_binary = rule(
    ...
    toolchains = [
        config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False),
    ],
)
```

When an optional toolchain type cannot be resolved, analysis continues, and the
result of `ctx.toolchains["//bar_tools:toolchain_type"]` is `None`.

The [`config_common.toolchain_type`](/rules/lib/toplevel/config_common#toolchain_type)
function defaults to mandatory.

The following forms can be used:

-  Mandatory toolchain types:
   -  `toolchains = ["//bar_tools:toolchain_type"]`
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type")]`
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = True)]`
- Optional toolchain types:
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False)]`

```python
bar_binary = rule(
    ...
    toolchains = [
        "//foo_tools:toolchain_type",
        config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False),
    ],
)
```

You can mix and match forms in the same rule, also. However, if the same
toolchain type is listed multiple times, it will take the most strict version,
where mandatory is more strict than optional.

### Writing aspects that use toolchains {:#writing-aspects-toolchains}

Aspects have access to the same toolchain API as rules: you can define required
toolchain types, access toolchains via the context, and use them to generate new
actions using the toolchain.

```py
bar_aspect = aspect(
    implementation = _bar_aspect_impl,
    attrs = {},
    toolchains = ['//bar_tools:toolchain_type'],
)

def _bar_aspect_impl(target, ctx):
  toolchain = ctx.toolchains['//bar_tools:toolchain_type']
  # Use the toolchain provider like in a rule.
  return []
```

## Defining toolchains {:#toolchain-definitions}

To define some toolchains for a given toolchain type, you need three things:

1. A language-specific rule representing the kind of tool or tool suite. By
   convention this rule's name is suffixed with "\_toolchain".

    1.  **Note:** The `\_toolchain` rule cannot create any build actions.
        Rather, it collects artifacts from other rules and forwards them to the
        rule that uses the toolchain. That rule is responsible for creating all
        build actions.

2. Several targets of this rule type, representing versions of the tool or tool
   suite for different platforms.

3. For each such target, an associated target of the generic
  [`toolchain`](/reference/be/platforms-and-toolchains#toolchain)
   rule, to provide metadata used by the toolchain framework. This `toolchain`
   target also refers to the `toolchain_type` associated with this toolchain.
   This means that a given `_toolchain` rule could be associated with any
   `toolchain_type`, and that only in a `toolchain` instance that uses
   this `_toolchain` rule that the rule is associated with a `toolchain_type`.

For our running example, here's a definition for a `bar_toolchain` rule. Our
example has only a compiler, but other tools such as a linker could also be
grouped underneath it.

```python
def _bar_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        barcinfo = BarcInfo(
            compiler_path = ctx.attr.compiler_path,
            system_lib = ctx.attr.system_lib,
            arch_flags = ctx.attr.arch_flags,
        ),
    )
    return [toolchain_info]

bar_toolchain = rule(
    implementation = _bar_toolchain_impl,
    attrs = {
        "compiler_path": attr.string(),
        "system_lib": attr.string(),
        "arch_flags": attr.string_list(),
    },
)
```

The rule must return a `ToolchainInfo` provider, which becomes the object that
the consuming rule retrieves using `ctx.toolchains` and the label of the
toolchain type. `ToolchainInfo`, like `struct`, can hold arbitrary field-value
pairs. The specification of exactly what fields are added to the `ToolchainInfo`
should be clearly documented at the toolchain type. In this example, the values
return wrapped in a `BarcInfo` object to reuse the schema defined above; this
style may be useful for validation and code reuse.

Now you can define targets for specific `barc` compilers.

```python
bar_toolchain(
    name = "barc_linux",
    arch_flags = [
        "--arch=Linux",
        "--debug_everything",
    ],
    compiler_path = "/path/to/barc/on/linux",
    system_lib = "/usr/lib/libbarc.so",
)

bar_toolchain(
    name = "barc_windows",
    arch_flags = [
        "--arch=Windows",
        # Different flags, no debug support on windows.
    ],
    compiler_path = "C:\\path\\on\\windows\\barc.exe",
    system_lib = "C:\\path\\on\\windows\\barclib.dll",
)
```

Finally, you create `toolchain` definitions for the two `bar_toolchain` targets.
These definitions link the language-specific targets to the toolchain type and
provide the constraint information that tells Bazel when the toolchain is
appropriate for a given platform.

```python
toolchain(
    name = "barc_linux_toolchain",
    exec_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":barc_linux",
    toolchain_type = ":toolchain_type",
)

toolchain(
    name = "barc_windows_toolchain",
    exec_compatible_with = [
        "@platforms//os:windows",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:windows",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":barc_windows",
    toolchain_type = ":toolchain_type",
)
```

The use of relative path syntax above suggests these definitions are all in the
same package, but there's no reason the toolchain type, language-specific
toolchain targets, and `toolchain` definition targets can't all be in separate
packages.

See the [`go_toolchain`](https://github.com/bazelbuild/rules_go/blob/master/go/private/go_toolchain.bzl){: .external}
for a real-world example.

### Toolchains and configurations

An important question for rule authors is, when a `bar_toolchain` target is
analyzed, what [configuration](/reference/glossary#configuration) does it see, and what transitions
should be used for dependencies? The example above uses string attributes, but
what would happen for a more complicated toolchain that depends on other targets
in the Bazel repository?

Let's see a more complex version of `bar_toolchain`:

```python
def _bar_toolchain_impl(ctx):
    # The implementation is mostly the same as above, so skipping.
    pass

bar_toolchain = rule(
    implementation = _bar_toolchain_impl,
    attrs = {
        "compiler": attr.label(
            executable = True,
            mandatory = True,
            cfg = "exec",
        ),
        "system_lib": attr.label(
            mandatory = True,
            cfg = "target",
        ),
        "arch_flags": attr.string_list(),
    },
)
```

The use of [`attr.label`](/rules/lib/toplevel/attr#label) is the same as for a standard rule,
but the meaning of the `cfg` parameter is slightly different.

The dependency from a target (called the "parent") to a toolchain via toolchain
resolution uses a special configuration transition called the "toolchain
transition". The toolchain transition keeps the configuration the same, except
that it forces the execution platform to be the same for the toolchain as for
the parent (otherwise, toolchain resolution for the toolchain could pick any
execution platform, and wouldn't necessarily be the same as for parent). This
allows any `exec` dependencies of the toolchain to also be executable for the
parent's build actions. Any of the toolchain's dependencies which use `cfg =
"target"` (or which don't specify `cfg`, since "target" is the default) are
built for the same target platform as the parent. This allows toolchain rules to
contribute both libraries (the `system_lib` attribute above) and tools (the
`compiler` attribute) to the build rules which need them. The system libraries
are linked into the final artifact, and so need to be built for the same
platform, whereas the compiler is a tool invoked during the build, and needs to
be able to run on the execution platform.

## Registering and building with toolchains {:#registering-building-toolchains}

At this point all the building blocks are assembled, and you just need to make
the toolchains available to Bazel's resolution procedure. This is done by
registering the toolchain, either in a `MODULE.bazel` file using
`register_toolchains()`, or by passing the toolchains' labels on the command
line using the `--extra_toolchains` flag.

```python
register_toolchains(
    "//bar_tools:barc_linux_toolchain",
    "//bar_tools:barc_windows_toolchain",
    # Target patterns are also permitted, so you could have also written:
    # "//bar_tools:all",
    # or even
    # "//bar_tools/...",
)
```

When using target patterns to register toolchains, the order in which the
individual toolchains are registered is determined by the following rules:

* The toolchains defined in a subpackage of a package are registered before the
  toolchains defined in the package itself.
* Within a package, toolchains are registered in the lexicographical order of
  their names.

Now when you build a target that depends on a toolchain type, an appropriate
toolchain will be selected based on the target and execution platforms.

```python
# my_pkg/BUILD

platform(
    name = "my_target_platform",
    constraint_values = [
        "@platforms//os:linux",
    ],
)

bar_binary(
    name = "my_bar_binary",
    ...
)
```

```sh
bazel build //my_pkg:my_bar_binary --platforms=//my_pkg:my_target_platform
```

Bazel will see that `//my_pkg:my_bar_binary` is being built with a platform that
has `@platforms//os:linux` and therefore resolve the
`//bar_tools:toolchain_type` reference to `//bar_tools:barc_linux_toolchain`.
This will end up building `//bar_tools:barc_linux` but not
`//bar_tools:barc_windows`.

## Toolchain resolution {:#toolchain-resolution}

Note: [Some Bazel rules](/concepts/platforms#status) do not yet support
toolchain resolution.

For each target that uses toolchains, Bazel's toolchain resolution procedure
determines the target's concrete toolchain dependencies. The procedure takes as
input a set of required toolchain types, the target platform, the list of
available execution platforms, and the list of available toolchains. Its outputs
are a selected toolchain for each toolchain type as well as a selected execution
platform for the current target.

The available execution platforms and toolchains are gathered from the
external dependency graph via
[`register_execution_platforms`](/rules/lib/globals/module#register_execution_platforms)
and
[`register_toolchains`](/rules/lib/globals/module#register_toolchains) calls in
`MODULE.bazel` files.
Additional execution platforms and toolchains may also be specified on the
command line via
[`--extra_execution_platforms`](/reference/command-line-reference#flag--extra_execution_platforms)
and
[`--extra_toolchains`](/reference/command-line-reference#flag--extra_toolchains).
The host platform is automatically included as an available execution platform.
Available platforms and toolchains are tracked as ordered lists for determinism,
with preference given to earlier items in the list.

The set of available toolchains, in priority order, is created from
`--extra_toolchains` and `register_toolchains`:

1. Toolchains registered using `--extra_toolchains` are added first. (Within
   these, the **last** toolchain has highest priority.)
2. Toolchains registered using `register_toolchains` in the transitive external
   dependency graph, in the following order: (Within these, the **first**
   mentioned toolchain has highest priority.)
  1. Toolchains registered by the root module (as in, the `MODULE.bazel` at the
     workspace root);
  2. Toolchains registered in the user's `WORKSPACE` file, including in any
     macros invoked from there;
  3. Toolchains registered by non-root modules (as in, dependencies specified by
     the root module, and their dependencies, and so forth);
  4. Toolchains registered in the "WORKSPACE suffix"; this is only used by
     certain native rules bundled with the Bazel installation.

**NOTE:** [Pseudo-targets like `:all`, `:*`, and
`/...`](/run/build#specifying-build-targets) are ordered by Bazel's package
loading mechanism, which uses a lexicographic ordering.

The resolution steps are as follows.

1. A `target_compatible_with` or `exec_compatible_with` clause *matches* a
   platform if, for each `constraint_value` in its list, the platform also has
   that `constraint_value` (either explicitly or as a default).

   If the platform has `constraint_value`s from `constraint_setting`s not
   referenced by the clause, these do not affect matching.

1. If the target being built specifies the
   [`exec_compatible_with` attribute](/reference/be/common-definitions#common.exec_compatible_with)
   (or its rule definition specifies the
   [`exec_compatible_with` argument](/rules/lib/globals/bzl#rule.exec_compatible_with)),
   the list of available execution platforms is filtered to remove
   any that do not match the execution constraints.

1. The list of available toolchains is filtered to remove any toolchains
   specifying `target_settings` that don't match the current configuration.

1. For each available execution platform, you associate each toolchain type with
   the first available toolchain, if any, that is compatible with this execution
   platform and the target platform.

1. Any execution platform that failed to find a compatible mandatory toolchain
   for one of its toolchain types is ruled out. Of the remaining platforms, the
   first one becomes the current target's execution platform, and its associated
   toolchains (if any) become dependencies of the target.

The chosen execution platform is used to run all actions that the target
generates.

In cases where the same target can be built in multiple configurations (such as
for different CPUs) within the same build, the resolution procedure is applied
independently to each version of the target.

If the rule uses [execution groups](/extending/exec-groups), each execution
group performs toolchain resolution separately, and each has its own execution
platform and toolchains.

## Debugging toolchains {:#debugging-toolchains}

If you are adding toolchain support to an existing rule, use the
`--toolchain_resolution_debug=regex` flag. During toolchain resolution, the flag
provides verbose output for toolchain types or target names that match the regex variable. You
can use `.*` to output all information. Bazel will output names of toolchains it
checks and skips during the resolution process.

If you'd like to see which [`cquery`](/query/cquery) dependencies are from toolchain
resolution, use `cquery`'s [`--transitions`](/query/cquery#transitions) flag:

```
# Find all direct dependencies of //cc:my_cc_lib. This includes explicitly
# declared dependencies, implicit dependencies, and toolchain dependencies.
$ bazel cquery 'deps(//cc:my_cc_lib, 1)'
//cc:my_cc_lib (96d6638)
@bazel_tools//tools/cpp:toolchain (96d6638)
@bazel_tools//tools/def_parser:def_parser (HOST)
//cc:my_cc_dep (96d6638)
@local_config_platform//:host (96d6638)
@bazel_tools//tools/cpp:toolchain_type (96d6638)
//:default_host_platform (96d6638)
@local_config_cc//:cc-compiler-k8 (HOST)
//cc:my_cc_lib.cc (null)
@bazel_tools//tools/cpp:grep-includes (HOST)

# Which of these are from toolchain resolution?
$ bazel cquery 'deps(//cc:my_cc_lib, 1)' --transitions=lite | grep "toolchain dependency"
  [toolchain dependency]#@local_config_cc//:cc-compiler-k8#HostTransition -> b6df211
```


Project: /_project.yaml
Book: /_book.yaml
{# disableFinding("native") #}
{# disableFinding("Native") #}
{# disableFinding(LINE_OVER_80_LINK) #}

# Legacy Macros

{% include "_buttons.html" %}

Legacy macros are unstructured functions called from `BUILD` files that can
create targets. By the end of the
[loading phase](/extending/concepts#evaluation-model), legacy macros don't exist
anymore, and Bazel sees only the concrete set of instantiated rules.

## Why you shouldn't use legacy macros (and should use Symbolic macros instead) {:#no-legacy-macros}

Where possible you should use [symbolic macros](macros.md#macros).

Symbolic macros

*   Prevent action at a distance
*   Make it possible to hide implementation details through granular visibility
*   Take typed attributes, which in turn means automatic label and select
    conversion.
*   Are more readable
*   Will soon have [lazy evaluation](macros.md/laziness)

## Usage {:#usage}

The typical use case for a macro is when you want to reuse a rule.

For example, genrule in a `BUILD` file generates a file using `//:generator`
with a `some_arg` argument hardcoded in the command:

```python
genrule(
    name = "file",
    outs = ["file.txt"],
    cmd = "$(location //:generator) some_arg > $@",
    tools = ["//:generator"],
)
```

Note: `$@` is a
[Make variable](/reference/be/make-variables#predefined_genrule_variables) that
refers to the execution-time locations of the files in the `outs` attribute
list. It is equivalent to `$(locations :file.txt)`.

If you want to generate more files with different arguments, you may want to
extract this code to a macro function. To create a macro called
`file_generator`, which has `name` and `arg` parameters, we can replace the
genrule with the following:

```python
load("//path:generator.bzl", "file_generator")

file_generator(
    name = "file",
    arg = "some_arg",
)

file_generator(
    name = "file-two",
    arg = "some_arg_two",
)

file_generator(
    name = "file-three",
    arg = "some_arg_three",
)
```

Here, you load the `file_generator` symbol from a `.bzl` file located in the
`//path` package. By putting macro function definitions in a separate `.bzl`
file, you keep your `BUILD` files clean and declarative, The `.bzl` file can be
loaded from any package in the workspace.

Finally, in `path/generator.bzl`, write the definition of the macro to
encapsulate and parameterize the original genrule definition:

```python
def file_generator(name, arg, visibility=None):
  native.genrule(
    name = name,
    outs = [name + ".txt"],
    cmd = "$(location //:generator) %s > $@" % arg,
    tools = ["//:generator"],
    visibility = visibility,
  )
```

You can also use macros to chain rules together. This example shows chained
genrules, where a genrule uses the outputs of a previous genrule as inputs:

```python
def chained_genrules(name, visibility=None):
  native.genrule(
    name = name + "-one",
    outs = [name + ".one"],
    cmd = "$(location :tool-one) $@",
    tools = [":tool-one"],
    visibility = ["//visibility:private"],
  )

  native.genrule(
    name = name + "-two",
    srcs = [name + ".one"],
    outs = [name + ".two"],
    cmd = "$(location :tool-two) $< $@",
    tools = [":tool-two"],
    visibility = visibility,
  )
```

The example only assigns a visibility value to the second genrule. This allows
macro authors to hide the outputs of intermediate rules from being depended upon
by other targets in the workspace.

Note: Similar to `$@` for outputs, `$<` expands to the locations of files in the
`srcs` attribute list.

## Expanding macros {:#expanding-macros}

When you want to investigate what a macro does, use the `query` command with
`--output=build` to see the expanded form:

```none
$ bazel query --output=build :file
# /absolute/path/test/ext.bzl:42:3
genrule(
  name = "file",
  tools = ["//:generator"],
  outs = ["//test:file.txt"],
  cmd = "$(location //:generator) some_arg > $@",
)
```

## Instantiating native rules {:#instantiating-native-rules}

Native rules (rules that don't need a `load()` statement) can be instantiated
from the [native](/rules/lib/toplevel/native) module:

```python
def my_macro(name, visibility=None):
  native.cc_library(
    name = name,
    srcs = ["main.cc"],
    visibility = visibility,
  )
```

If you need to know the package name (for example, which `BUILD` file is calling
the macro), use the function
[native.package_name()](/rules/lib/toplevel/native#package_name). Note that
`native` can only be used in `.bzl` files, and not in `BUILD` files.

## Label resolution in macros {:#label-resolution}

Since legacy macros are evaluated in the
[loading phase](concepts.md#evaluation-model), label strings such as
`"//foo:bar"` that occur in a legacy macro are interpreted relative to the
`BUILD` file in which the macro is used rather than relative to the `.bzl` file
in which it is defined. This behavior is generally undesirable for macros that
are meant to be used in other repositories, such as because they are part of a
published Starlark ruleset.

To get the same behavior as for Starlark rules, wrap the label strings with the
[`Label`](/rules/lib/builtins/Label#Label) constructor:

```python
# @my_ruleset//rules:defs.bzl
def my_cc_wrapper(name, deps = [], **kwargs):
  native.cc_library(
    name = name,
    deps = deps + select({
      # Due to the use of Label, this label is resolved within @my_ruleset,
      # regardless of its site of use.
      Label("//config:needs_foo"): [
        # Due to the use of Label, this label will resolve to the correct target
        # even if the canonical name of @dep_of_my_ruleset should be different
        # in the main repo, such as due to repo mappings.
        Label("@dep_of_my_ruleset//tools:foo"),
      ],
      "//conditions:default": [],
    }),
    **kwargs,
  )
```

## Debugging {:#debugging}

*   `bazel query --output=build //my/path:all` will show you how the `BUILD`
    file looks after evaluation. All legacy macros, globs, loops are expanded.
    Known limitation: `select` expressions are not shown in the output.

*   You may filter the output based on `generator_function` (which function
    generated the rules) or `generator_name` (the name attribute of the macro):
    `bash $ bazel query --output=build 'attr(generator_function, my_macro,
    //my/path:all)'`

*   To find out where exactly the rule `foo` is generated in a `BUILD` file, you
    can try the following trick. Insert this line near the top of the `BUILD`
    file: `cc_library(name = "foo")`. Run Bazel. You will get an exception when
    the rule `foo` is created (due to a name conflict), which will show you the
    full stack trace.

*   You can also use [print](/rules/lib/globals/all#print) for debugging. It
    displays the message as a `DEBUG` log line during the loading phase. Except
    in rare cases, either remove `print` calls, or make them conditional under a
    `debugging` parameter that defaults to `False` before submitting the code to
    the depot.

## Errors {:#errors}

If you want to throw an error, use the [fail](/rules/lib/globals/all#fail)
function. Explain clearly to the user what went wrong and how to fix their
`BUILD` file. It is not possible to catch an error.

```python
def my_macro(name, deps, visibility=None):
  if len(deps) < 2:
    fail("Expected at least two values in deps")
  # ...
```

## Conventions {:#conventions}

*   All public functions (functions that don't start with underscore) that
    instantiate rules must have a `name` argument. This argument should not be
    optional (don't give a default value).

*   Public functions should use a docstring following
    [Python conventions](https://www.python.org/dev/peps/pep-0257/#one-line-docstrings).

*   In `BUILD` files, the `name` argument of the macros must be a keyword
    argument (not a positional argument).

*   The `name` attribute of rules generated by a macro should include the name
    argument as a prefix. For example, `macro(name = "foo")` can generate a
    `cc_library` `foo` and a genrule `foo_gen`.

*   In most cases, optional parameters should have a default value of `None`.
    `None` can be passed directly to native rules, which treat it the same as if
    you had not passed in any argument. Thus, there is no need to replace it
    with `0`, `False`, or `[]` for this purpose. Instead, the macro should defer
    to the rules it creates, as their defaults may be complex or may change over
    time. Additionally, a parameter that is explicitly set to its default value
    looks different than one that is never set (or set to `None`) when accessed
    through the query language or build-system internals.

*   Macros should have an optional `visibility` argument.


Project: /_project.yaml
Book: /_book.yaml
{# disableFinding("Currently") #}
{# disableFinding(TODO) #}

# Macros

{% include "_buttons.html" %}

This page covers the basics of using macros and includes typical use cases,
debugging, and conventions.

A macro is a function called from the `BUILD` file that can instantiate rules.
Macros are mainly used for encapsulation and code reuse of existing rules and
other macros.

Macros come in two flavors: symbolic macros, which are described on this page,
and [legacy macros](legacy-macros.md). Where possible, we recommend using
symbolic macros for code clarity.

Symbolic macros offer typed arguments (string to label conversion, relative to
where the macro was called) and the ability to restrict and specify the
visibility of targets created. They are designed to be amenable to lazy
evaluation (which will be added in a future Bazel release). Symbolic macros are
available by default in Bazel 8. Where this document mentions `macros`, it's
referring to **symbolic macros**.

An executable example of symbolic macros can be found in the
[examples repository](https://github.com/bazelbuild/examples/tree/main/macros).

## Usage {:#usage}

Macros are defined in `.bzl` files by calling the
[`macro()`](https://bazel.build/rules/lib/globals/bzl.html#macro) function with
two required parameters: `attrs` and `implementation`.

### Attributes {:#attributes}

`attrs` accepts a dictionary of attribute name to [attribute
types](https://bazel.build/rules/lib/toplevel/attr#members), which represents
the arguments to the macro. Two common attributes – `name` and `visibility` –
are implicitly added to all macros and are not included in the dictionary passed
to `attrs`.

```starlark
# macro/macro.bzl
my_macro = macro(
    attrs = {
        "deps": attr.label_list(mandatory = True, doc = "The dependencies passed to the inner cc_binary and cc_test targets"),
        "create_test": attr.bool(default = False, configurable = False, doc = "If true, creates a test target"),
    },
    implementation = _my_macro_impl,
)
```

Attribute type declarations accept the
[parameters](https://bazel.build/rules/lib/toplevel/attr#parameters),
`mandatory`, `default`, and `doc`. Most attribute types also accept the
`configurable` parameter, which determines wheher the attribute accepts
`select`s. If an attribute is `configurable`, it will parse non-`select` values
as an unconfigurable `select` – `"foo"` will become
`select({"//conditions:default": "foo"})`. Learn more in [selects](#selects).

#### Attribute inheritance {:#attribute-inheritance}

Macros are often intended to wrap a rule (or another macro), and the macro's
author often wants to forward the bulk of the wrapped symbol's attributes
unchanged, using `**kwargs`, to the macro's main target (or main inner macro).

To support this pattern, a macro can *inherit attributes* from a rule or another
macro by passing the [rule](https://bazel.build/rules/lib/builtins/rule) or
[macro symbol](https://bazel.build/rules/lib/builtins/macro) to `macro()`'s
`inherit_attrs` argument. (You can also use the special string `"common"`
instead of a rule or macro symbol to inherit the [common attributes defined for
all Starlark build
rules](https://bazel.build/reference/be/common-definitions#common-attributes).)
Only public attributes get inherited, and the attributes in the macro's own
`attrs` dictionary override inherited attributes with the same name. You can
also *remove* inherited attributes by using `None` as a value in the `attrs`
dictionary:

```starlark
# macro/macro.bzl
my_macro = macro(
    inherit_attrs = native.cc_library,
    attrs = {
        # override native.cc_library's `local_defines` attribute
        "local_defines": attr.string_list(default = ["FOO"]),
        # do not inherit native.cc_library's `defines` attribute
        "defines": None,
    },
    ...
)
```

The default value of non-mandatory inherited attributes is always overridden to
be `None`, regardless of the original attribute definition's default value. If
you need to examine or modify an inherited non-mandatory attribute – for
example, if you want to add a tag to an inherited `tags` attribute – you must
make sure to handle the `None` case in your macro's implementation function:

```starlark
# macro/macro.bzl
_my_macro_implementation(name, visibility, tags, **kwargs):
    # Append a tag; tags attr is an inherited non-mandatory attribute, and
    # therefore is None unless explicitly set by the caller of our macro.
    my_tags = (tags or []) + ["another_tag"]
    native.cc_library(
        ...
        tags = my_tags,
        **kwargs,
    )
    ...
```

### Implementation {:#implementation}

`implementation` accepts a function which contains the logic of the macro.
Implementation functions often create targets by calling one or more rules, and
they are usually private (named with a leading underscore). Conventionally,
they are named the same as their macro, but prefixed with `_` and suffixed with
`_impl`.

Unlike rule implementation functions, which take a single argument (`ctx`) that
contains a reference to the attributes, macro implementation functions accept a
parameter for each argument.

```starlark
# macro/macro.bzl
def _my_macro_impl(name, visibility, deps, create_test):
    cc_library(
        name = name + "_cc_lib",
        deps = deps,
    )

    if create_test:
        cc_test(
            name = name + "_test",
            srcs = ["my_test.cc"],
            deps = deps,
        )
```

If a macro inherits attributes, its implementation function *must* have a
`**kwargs` residual keyword parameter, which can be forwarded to the call that
invokes the inherited rule or submacro. (This helps ensure that your macro won't
be broken if the rule or macro which from which you are inheriting adds a new
attribute.)

### Declaration {:#declaration}

Macros are declared by loading and calling their definition in a `BUILD` file.

```starlark

# pkg/BUILD

my_macro(
    name = "macro_instance",
    deps = ["src.cc"] + select(
        {
            "//config_setting:special": ["special_source.cc"],
            "//conditions:default": [],
        },
    ),
    create_tests = True,
)
```

This would create targets
`//pkg:macro_instance_cc_lib` and`//pkg:macro_instance_test`.

Just like in rule calls, if an attribute value in a macro call is set to `None`,
that attribute is treated as if it was omitted by the macro's caller. For
example, the following two macro calls are equivalent:

```starlark
# pkg/BUILD
my_macro(name = "abc", srcs = ["src.cc"], deps = None)
my_macro(name = "abc", srcs = ["src.cc"])
```

This is generally not useful in `BUILD` files, but is helpful when
programmatically wrapping a macro inside another macro.

## Details {:#usage-details}

### Naming conventions for targets created {:#naming}

The names of any targets or submacros created by a symbolic macro must
either match the macro's `name` parameter or must be prefixed by `name` followed
by `_` (preferred), `.` or `-`. For example, `my_macro(name = "foo")` may only
create files or targets named `foo`, or prefixed by `foo_`, `foo-` or `foo.`,
for example, `foo_bar`.

Targets or files that violate macro naming convention can be declared, but
cannot be built and cannot be used as dependencies.

Non-macro files and targets within the same package as a macro instance should
*not* have names that conflict with potential macro target names, though this
exclusivity is not enforced. We are in the progress of implementing
[lazy evaluation](#laziness) as a performance improvement for Symbolic macros,
which will be impaired in packages that violate the naming schema.

### Restrictions {:#restrictions}

Symbolic macros have some additional restrictions compared to legacy macros.

Symbolic macros

*   must take a `name` argument and a `visibility` argument
*   must have an `implementation` function
*   may not return values
*   may not mutate their arguments
*   may not call `native.existing_rules()` unless they are special `finalizer`
    macros
*   may not call `native.package()`
*   may not call `glob()`
*   may not call `native.environment_group()`
*   must create targets whose names adhere to the [naming schema](#naming)
*   can't refer to input files that weren't declared or passed in as an argument
*   can't refer to private targets of their callers (see
    [visibility and macros](#visibility) for more details).

### Visibility and macros {:#visibility}

The [visibility](/concepts/visibility) system helps protect the implementation
details of both (symbolic) macros and their callers.

By default, targets created in a symbolic macro are visible within the macro
itself, but not necessarily to the macro's caller. The macro can "export" a
target as a public API by forwarding the value of its own `visibility`
attribute, as in `some_rule(..., visibility = visibility)`.

The key ideas of macro visibility are:

1. Visibility is checked based on what macro declared the target, not what
   package called the macro.

   * In other words, being in the same package does not by itself make one
     target visible to another. This protects the macro's internal targets
     from becoming dependencies of other macros or top-level targets in the
     package.

1. All `visibility` attributes, on both rules and macros, automatically
   include the place where the rule or macro was called.

   * Thus, a target is unconditionally visible to other targets declared in the
     same macro (or the `BUILD` file, if not in a macro).

In practice, this means that when a macro declares a target without setting its
`visibility`, the target defaults to being internal to the macro. (The package's
[default visibility](/reference/be/functions#package.default_visibility) does
not apply within a macro.) Exporting the target means that the target is visible
to whatever the macro's caller specified in the macro's `visibility` attribute,
plus the package of the macro's caller itself, as well as the macro's own code.
Another way of thinking of it is that the visibility of a macro determines who
(aside from the macro itself) can see the macro's exported targets.

```starlark
# tool/BUILD
...
some_rule(
    name = "some_tool",
    visibility = ["//macro:__pkg__"],
)
```

```starlark
# macro/macro.bzl

def _impl(name, visibility):
    cc_library(
        name = name + "_helper",
        ...
        # No visibility passed in. Same as passing `visibility = None` or
        # `visibility = ["//visibility:private"]`. Visible to the //macro
        # package only.
    )
    cc_binary(
        name = name + "_exported",
        deps = [
            # Allowed because we're also in //macro. (Targets in any other
            # instance of this macro, or any other macro in //macro, can see it
            # too.)
            name + "_helper",
            # Allowed by some_tool's visibility, regardless of what BUILD file
            # we're called from.
            "//tool:some_tool",
        ],
        ...
        visibility = visibility,
    )

my_macro = macro(implementation = _impl, ...)
```

```starlark
# pkg/BUILD
load("//macro:macro.bzl", "my_macro")
...

my_macro(
    name = "foo",
    ...
)

some_rule(
    ...
    deps = [
        # Allowed, its visibility is ["//pkg:__pkg__", "//macro:__pkg__"].
        ":foo_exported",
        # Disallowed, its visibility is ["//macro:__pkg__"] and
        # we are not in //macro.
        ":foo_helper",
    ]
)
```

If `my_macro` were called with `visibility = ["//other_pkg:__pkg__"]`, or if
the `//pkg` package had set its `default_visibility` to that value, then
`//pkg:foo_exported` could also be used within `//other_pkg/BUILD` or within a
macro defined in `//other_pkg:defs.bzl`, but `//pkg:foo_helper` would remain
protected.

A macro can declare that a target is visible to a friend package by passing
`visibility = ["//some_friend:__pkg__"]` (for an internal target) or
`visibility = visibility + ["//some_friend:__pkg__"]` (for an exported one).
Note that it is an antipattern for a macro to declare a target with public
visibility (`visibility = ["//visibility:public"]`). This is because it makes
the target unconditionally visible to every package, even if the caller
specified a more restricted visibility.

All visibility checking is done with respect to the innermost currently running
symbolic macro. However, there is a visibility delegation mechanism: If a macro
passes a label as an attribute value to an inner macro, any usages of the label
in the inner macro are checked with respect to the outer macro. See the
[visibility page](/concepts/visibility#symbolic-macros) for more details.

Remember that legacy macros are entirely transparent to the visibility system,
and behave as though their location is whatever BUILD file or symbolic macro
they were called from.

#### Finalizers and visibility {:#finalizers-and-visibility}

Targets declared in a rule finalizer, in addition to seeing targets following
the usual symbolic macro visibility rules, can *also* see all targets which are
visible to the finalizer target's package.

This means that if you migrate a `native.existing_rules()`-based legacy macro to
a finalizer, the targets declared by the finalizer will still be able to see
their old dependencies.

However, note that it's possible to declare a target in a symbolic macro such
that a finalizer's targets cannot see it under the visibility system – even
though the finalizer can *introspect* its attributes using
`native.existing_rules()`.

### Selects {:#selects}

If an attribute is `configurable` (the default) and its value is not `None`,
then the macro implementation function will see the attribute value as wrapped
in a trivial `select`. This makes it easier for the macro author to catch bugs
where they did not anticipate that the attribute value could be a `select`.

For example, consider the following macro:

```starlark
my_macro = macro(
    attrs = {"deps": attr.label_list()},  # configurable unless specified otherwise
    implementation = _my_macro_impl,
)
```

If `my_macro` is invoked with `deps = ["//a"]`, that will cause `_my_macro_impl`
to be invoked with its `deps` parameter set to `select({"//conditions:default":
["//a"]})`. If this causes the implementation function to fail (say, because the
code tried to index into the value as in `deps[0]`, which is not allowed for
`select`s), the macro author can then make a choice: either they can rewrite
their macro to only use operations compatible with `select`, or they can mark
the attribute as nonconfigurable (`attr.label_list(configurable = False)`). The
latter ensures that users are not permitted to pass a `select` value in.

Rule targets reverse this transformation, and store trivial `select`s as their
unconditional values; in the above example, if `_my_macro_impl` declares a rule
target `my_rule(..., deps = deps)`, that rule target's `deps` will be stored as
`["//a"]`. This ensures that `select`-wrapping does not cause trivial `select`
values to be stored in all targets instantiated by macros.

If the value of a configurable attribute is `None`, it does not get wrapped in a
`select`. This ensures that tests like `my_attr == None` still work, and that
when the attribute is forwarded to a rule with a computed default, the rule
behaves properly (that is, as if the attribute were not passed in at all). It is
not always possible for an attribute to take on a `None` value, but it can
happen for the `attr.label()` type, and for any inherited non-mandatory
attribute.

## Finalizers {:#finalizers}

A rule finalizer is a special symbolic macro which – regardless of its lexical
position in a BUILD file – is evaluated in the final stage of loading a package,
after all non-finalizer targets have been defined. Unlike ordinary symbolic
macros, a finalizer can call `native.existing_rules()`, where it behaves
slightly differently than in legacy macros: it only returns the set of
non-finalizer rule targets. The finalizer may assert on the state of that set or
define new targets.

To declare a finalizer, call `macro()` with `finalizer = True`:

```starlark
def _my_finalizer_impl(name, visibility, tags_filter):
    for r in native.existing_rules().values():
        for tag in r.get("tags", []):
            if tag in tags_filter:
                my_test(
                    name = name + "_" + r["name"] + "_finalizer_test",
                    deps = [r["name"]],
                    data = r["srcs"],
                    ...
                )
                continue

my_finalizer = macro(
    attrs = {"tags_filter": attr.string_list(configurable = False)},
    implementation = _impl,
    finalizer = True,
)
```

## Laziness {:#laziness}

IMPORTANT: We are in the process of implementing lazy macro expansion and
evaluation. This feature is not available yet.

Currently, all macros are evaluated as soon as the BUILD file is loaded, which
can negatively impact performance for targets in packages that also have costly
unrelated macros. In the future, non-finalizer symbolic macros will only be
evaluated if they're required for the build. The prefix naming schema helps
Bazel determine which macro to expand given a requested target.

## Migration troubleshooting {:#troubleshooting}

Here are some common migration headaches and how to fix them.

*   Legacy macro calls `glob()`

Move the `glob()` call to your BUILD file (or to a legacy macro called from the
BUILD file), and pass the `glob()` value to the symbolic macro using a
label-list attribute:

```starlark
# BUILD file
my_macro(
    ...,
    deps = glob(...),
)
```

*   Legacy macro has a parameter that isn't a valid starlark `attr` type.

Pull as much logic as possible into a nested symbolic macro, but keep the
top level macro a legacy macro.

*  Legacy macro calls a rule that creates a target that breaks the naming schema

That's okay, just don't depend on the "offending" target. The naming check will
be quietly ignored.



Project: /_project.yaml
Book: /_book.yaml

# Depsets

{% include "_buttons.html" %}

[Depsets](/rules/lib/builtins/depset) are a specialized data structure for efficiently
collecting data across a target’s transitive dependencies. They are an essential
element of rule processing.

The defining feature of depset is its time- and space-efficient union operation.
The depset constructor accepts a list of elements ("direct") and a list of other
depsets ("transitive"), and returns a depset representing a set containing all the
direct elements and the union of all the transitive sets. Conceptually, the
constructor creates a new graph node that has the direct and transitive nodes
as its successors. Depsets have a well-defined ordering semantics, based on
traversal of this graph.

Example uses of depsets include:

*   Storing the paths of all object files for a program’s libraries, which can
    then be passed to a linker action through a provider.

*   For an interpreted language, storing the transitive source files that are
    included in an executable's runfiles.

## Description and operations

Conceptually, a depset is a directed acyclic graph (DAG) that typically looks
similar to the target graph. It is constructed from the leaves up to the root.
Each target in a dependency chain can add its own contents on top of the
previous without having to read or copy them.

Each node in the DAG holds a list of direct elements and a list of child nodes.
The contents of the depset are the transitive elements, such as the direct elements
of all the nodes. A new depset can be created using the
[depset](/rules/lib/globals/bzl#depset) constructor: it accepts a list of direct
elements and another list of child nodes.

```python
s = depset(["a", "b", "c"])
t = depset(["d", "e"], transitive = [s])

print(s)    # depset(["a", "b", "c"])
print(t)    # depset(["d", "e", "a", "b", "c"])
```

To retrieve the contents of a depset, use the
[to_list()](/rules/lib/builtins/depset#to_list) method. It returns a list of all transitive
elements, not including duplicates. There is no way to directly inspect the
precise structure of the DAG, although this structure does affect the order in
which the elements are returned.

```python
s = depset(["a", "b", "c"])

print("c" in s.to_list())              # True
print(s.to_list() == ["a", "b", "c"])  # True
```

The allowed items in a depset are restricted, just as the allowed keys in
dictionaries are restricted. In particular, depset contents may not be mutable.

Depsets use reference equality: a depset is equal to itself, but unequal to any
other depset, even if they have the same contents and same internal structure.

```python
s = depset(["a", "b", "c"])
t = s
print(s == t)  # True

t = depset(["a", "b", "c"])
print(s == t)  # False

d = {}
d[s] = None
d[t] = None
print(len(d))  # 2
```

To compare depsets by their contents, convert them to sorted lists.

```python
s = depset(["a", "b", "c"])
t = depset(["c", "b", "a"])
print(sorted(s.to_list()) == sorted(t.to_list()))  # True
```

There is no ability to remove elements from a depset. If this is needed, you
must read out the entire contents of the depset, filter the elements you want to
remove, and reconstruct a new depset. This is not particularly efficient.

```python
s = depset(["a", "b", "c"])
t = depset(["b", "c"])

# Compute set difference s - t. Precompute t.to_list() so it's not done
# in a loop, and convert it to a dictionary for fast membership tests.
t_items = {e: None for e in t.to_list()}
diff_items = [x for x in s.to_list() if x not in t_items]
# Convert back to depset if it's still going to be used for union operations.
s = depset(diff_items)
print(s)  # depset(["a"])
```

### Order

The `to_list` operation performs a traversal over the DAG. The kind of traversal
depends on the *order* that was specified at the time the depset was
constructed. It is useful for Bazel to support multiple orders because sometimes
tools care about the order of their inputs. For example, a linker action may
need to ensure that if `B` depends on `A`, then `A.o` comes before `B.o` on the
linker’s command line. Other tools might have the opposite requirement.

Three traversal orders are supported: `postorder`, `preorder`, and
`topological`. The first two work exactly like [tree
traversals](https://en.wikipedia.org/wiki/Tree_traversal#Depth-first_search)
except that they operate on DAGs and skip already visited nodes. The third order
works as a topological sort from root to leaves, essentially the same as
preorder except that shared children are listed only after all of their parents.
Preorder and postorder operate as left-to-right traversals, but note that within
each node direct elements have no order relative to children. For topological
order, there is no left-to-right guarantee, and even the
all-parents-before-child guarantee does not apply in the case that there are
duplicate elements in different nodes of the DAG.

```python
# This demonstrates different traversal orders.

def create(order):
  cd = depset(["c", "d"], order = order)
  gh = depset(["g", "h"], order = order)
  return depset(["a", "b", "e", "f"], transitive = [cd, gh], order = order)

print(create("postorder").to_list())  # ["c", "d", "g", "h", "a", "b", "e", "f"]
print(create("preorder").to_list())   # ["a", "b", "e", "f", "c", "d", "g", "h"]
```

```python
# This demonstrates different orders on a diamond graph.

def create(order):
  a = depset(["a"], order=order)
  b = depset(["b"], transitive = [a], order = order)
  c = depset(["c"], transitive = [a], order = order)
  d = depset(["d"], transitive = [b, c], order = order)
  return d

print(create("postorder").to_list())    # ["a", "b", "c", "d"]
print(create("preorder").to_list())     # ["d", "b", "a", "c"]
print(create("topological").to_list())  # ["d", "b", "c", "a"]
```

Due to how traversals are implemented, the order must be specified at the time
the depset is created with the constructor’s `order` keyword argument. If this
argument is omitted, the depset has the special `default` order, in which case
there are no guarantees about the order of any of its elements (except that it
is deterministic).

## Full example

This example is available at
[https://github.com/bazelbuild/examples/tree/main/rules/depsets](https://github.com/bazelbuild/examples/tree/main/rules/depsets).

Suppose there is a hypothetical interpreted language Foo. In order to build
each `foo_binary` you need to know all the `*.foo` files that it directly or
indirectly depends on.

```python
# //depsets:BUILD

load(":foo.bzl", "foo_library", "foo_binary")

# Our hypothetical Foo compiler.
py_binary(
    name = "foocc",
    srcs = ["foocc.py"],
)

foo_library(
    name = "a",
    srcs = ["a.foo", "a_impl.foo"],
)

foo_library(
    name = "b",
    srcs = ["b.foo", "b_impl.foo"],
    deps = [":a"],
)

foo_library(
    name = "c",
    srcs = ["c.foo", "c_impl.foo"],
    deps = [":a"],
)

foo_binary(
    name = "d",
    srcs = ["d.foo"],
    deps = [":b", ":c"],
)
```

```python
# //depsets:foocc.py

# "Foo compiler" that just concatenates its inputs to form its output.
import sys

if __name__ == "__main__":
  assert len(sys.argv) >= 1
  output = open(sys.argv[1], "wt")
  for path in sys.argv[2:]:
    input = open(path, "rt")
    output.write(input.read())
```

Here, the transitive sources of the binary `d` are all of the `*.foo` files in
the `srcs` fields of `a`, `b`, `c`, and `d`. In order for the `foo_binary`
target to know about any file besides `d.foo`, the `foo_library` targets need to
pass them along in a provider. Each library receives the providers from its own
dependencies, adds its own immediate sources, and passes on a new provider with
the augmented contents. The `foo_binary` rule does the same, except that instead
of returning a provider, it uses the complete list of sources to construct a
command line for an action.

Here’s a complete implementation of the `foo_library` and `foo_binary` rules.

```python
# //depsets/foo.bzl

# A provider with one field, transitive_sources.
FooFiles = provider(fields = ["transitive_sources"])

def get_transitive_srcs(srcs, deps):
  """Obtain the source files for a target and its transitive dependencies.

  Args:
    srcs: a list of source files
    deps: a list of targets that are direct dependencies
  Returns:
    a collection of the transitive sources
  """
  return depset(
        srcs,
        transitive = [dep[FooFiles].transitive_sources for dep in deps])

def _foo_library_impl(ctx):
  trans_srcs = get_transitive_srcs(ctx.files.srcs, ctx.attr.deps)
  return [FooFiles(transitive_sources=trans_srcs)]

foo_library = rule(
    implementation = _foo_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files=True),
        "deps": attr.label_list(),
    },
)

def _foo_binary_impl(ctx):
  foocc = ctx.executable._foocc
  out = ctx.outputs.out
  trans_srcs = get_transitive_srcs(ctx.files.srcs, ctx.attr.deps)
  srcs_list = trans_srcs.to_list()
  ctx.actions.run(executable = foocc,
                  arguments = [out.path] + [src.path for src in srcs_list],
                  inputs = srcs_list + [foocc],
                  outputs = [out])

foo_binary = rule(
    implementation = _foo_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files=True),
        "deps": attr.label_list(),
        "_foocc": attr.label(default=Label("//depsets:foocc"),
                             allow_files=True, executable=True, cfg="host")
    },
    outputs = {"out": "%{name}.out"},
)
```

You can test this by copying these files into a fresh package, renaming the
labels appropriately, creating the source `*.foo` files with dummy content, and
building the `d` target.


## Performance

To see the motivation for using depsets, consider what would happen if
`get_transitive_srcs()` collected its sources in a list.

```python
def get_transitive_srcs(srcs, deps):
  trans_srcs = []
  for dep in deps:
    trans_srcs += dep[FooFiles].transitive_sources
  trans_srcs += srcs
  return trans_srcs
```

This does not take into account duplicates, so the source files for `a`
will appear twice on the command line and twice in the contents of the output
file.

An alternative is using a general set, which can be simulated by a
dictionary where the keys are the elements and all the keys map to `True`.

```python
def get_transitive_srcs(srcs, deps):
  trans_srcs = {}
  for dep in deps:
    for file in dep[FooFiles].transitive_sources:
      trans_srcs[file] = True
  for file in srcs:
    trans_srcs[file] = True
  return trans_srcs
```

This gets rid of the duplicates, but it makes the order of the command line
arguments (and therefore the contents of the files) unspecified, although still
deterministic.

Moreover, both approaches are asymptotically worse than the depset-based
approach. Consider the case where there is a long chain of dependencies on
Foo libraries. Processing every rule requires copying all of the transitive
sources that came before it into a new data structure. This means that the
time and space cost for analyzing an individual library or binary target
is proportional to its own height in the chain. For a chain of length n,
foolib_1 ← foolib_2 ← … ← foolib_n, the overall cost is effectively O(n^2).

Generally speaking, depsets should be used whenever you are accumulating
information through your transitive dependencies. This helps ensure that
your build scales well as your target graph grows deeper.

Finally, it’s important to not retrieve the contents of the depset
unnecessarily in rule implementations. One call to `to_list()`
at the end in a binary rule is fine, since the overall cost is just O(n). It’s
when many non-terminal targets try to call `to_list()` that quadratic behavior
occurs.

For more information about using depsets efficiently, see the [performance](/rules/performance) page.

## API Reference

Please see [here](/rules/lib/builtins/depset) for more details.



Project: /_project.yaml
Book: /_book.yaml

# Automatic Execution Groups (AEGs)

{% include "_buttons.html" %}

Automatic execution groups select an [execution platform][exec_platform]
for each toolchain type. In other words, one target can have multiple
execution platforms without defining execution groups.

## Quick summary {:#quick-summary}

Automatic execution groups are closely connected to toolchains. If you are using
toolchains, you need to set them on the affected actions (actions which use an
executable or a tool from a toolchain) by adding `toolchain` parameter. For
example:

```python
ctx.actions.run(
    ...,
    executable = ctx.toolchain['@bazel_tools//tools/jdk:toolchain_type'].tool,
    ...,
    toolchain = '@bazel_tools//tools/jdk:toolchain_type',
)
```
If the action does not use a tool or executable from a toolchain, and Blaze
doesn't detect that ([the error](#first-error-message) is raised), you can set
`toolchain = None`.

If you need to use multiple toolchains on a single execution platform (an action
uses executable or tools from two or more toolchains), you need to manually
define [exec_groups][exec_groups] (check
[When should I use a custom exec_group?][multiple_toolchains_exec_groups]
section).

## History {:#history}

Before AEGs, the execution platform was selected on a rule level. For example:

```python
my_rule = rule(
    _impl,
    toolchains = ['//tools:toolchain_type_1', '//tools:toolchain_type_2'],
)
```

Rule `my_rule` registers two toolchain types. This means that the [Toolchain
Resolution](https://bazel.build/extending/toolchains#toolchain-resolution) used
to find an execution platform which supports both toolchain types. The selected
execution platform was used for each registered action inside the rule, unless
specified differently with [exec_groups][exec_groups].
In other words, all actions inside the rule used to have a single execution
platform even if they used tools from different toolchains (execution platform
is selected for each target). This resulted in failures when there was no
execution platform supporting all toolchains.

## Current state {:#current-state}

With AEGs, the execution platform is selected for each toolchain type. The
implementation function of the earlier example, `my_rule`, would look like:

```python
def _impl(ctx):
    ctx.actions.run(
      mnemonic = "First action",
      executable = ctx.toolchain['//tools:toolchain_type_1'].tool,
      toolchain = '//tools:toolchain_type_1',
    )

    ctx.actions.run(
      mnemonic = "Second action",
      executable = ctx.toolchain['//tools:toolchain_type_2'].tool,
      toolchain = '//tools:toolchain_type_2',
    )
```

This rule creates two actions, the `First action` which uses executable from a
`//tools:toolchain_type_1` and the `Second action` which uses executable from a
`//tools:toolchain_type_2`. Before AEGs, both of these actions would be executed
on a single execution platform which supports both toolchain types. With AEGs,
by adding the `toolchain` parameter inside the actions, each action executes on
the execution platform that provides the toolchain. The actions may be executed
on different execution platforms.

The same is effective with [ctx.actions.run_shell][run_shell] where `toolchain`
parameter should be added when `tools` are from a toolchain.

## Difference between custom exec groups and automatic exec groups {:#difference-custom}

As the name suggests, AEGs are exec groups created automatically for each
toolchain type registered on a rule. There is no need to manually specify them,
unlike the "classic" exec groups.

### When should I use a custom exec_group? {:#when-should-use-exec-groups}

Custom exec_groups are needed only in case where multiple toolchains need to
execute on a single execution platform. In all other cases there's no need to
define custom exec_groups. For example:

```python
def _impl(ctx):
    ctx.actions.run(
      ...,
      executable = ctx.toolchain['//tools:toolchain_type_1'].tool,
      tools = [ctx.toolchain['//tools:toolchain_type_2'].tool],
      exec_group = 'two_toolchains',
    )
```

```python
my_rule = rule(
    _impl,
    exec_groups = {
        "two_toolchains": exec_group(
            toolchains = ['//tools:toolchain_type_1', '//tools:toolchain_type_2'],
        ),
    }
)
```

## Migration of AEGs {:#migration-aegs}

Internally in google3, Blaze is already using AEGs.
Externally for Bazel, migration is in the process. Some rules are already using
this feature (e.g. Java and C++ rules).

### Which Bazel versions support this migration? {:#which-bazel}

AEGs are fully supported from Bazel 7.

### How to enable AEGs? {:#how-enable}

Set `--incompatible_auto_exec_groups` to true. More information about the flag
on [the GitHub issue][github_flag].

### How to enable AEGs inside a particular rule? {:#how-enable-particular-rule}

Set the `_use_auto_exec_groups` attribute on a rule.

```python
my_rule = rule(
    _impl,
    attrs = {
      "_use_auto_exec_groups": attr.bool(default = True),
    }
)
```
This enables AEGs only in `my_rule` and its actions start using the new logic
when selecting the execution platform. Incompatible flag is overridden with this
attribute.

### How to disable AEGs in case of an error? {:#how-disable}

Set `--incompatible_auto_exec_groups` to false to completely disable AEGs in
your project ([flag's GitHub issue][github_flag]), or disable a particular rule
by setting `_use_auto_exec_groups` attribute to `False`
([more details about the attribute](#how-enable-particular-rule)).

### Error messages while migrating to AEGs {:#potential-problems}

#### Couldn't identify if tools are from implicit dependencies or a toolchain. Please set the toolchain parameter. If you're not using a toolchain, set it to 'None'. {:#first-error-message}
  * In this case you get a stack of calls before the error happened and you can
    clearly see which exact action needs the toolchain parameter. Check which
    toolchain is used for the action and set it with the toolchain param. If no
    toolchain is used inside the action for tools or executable, set it to
    `None`.

#### Action declared for non-existent toolchain '[toolchain_type]'.
  * This means that you've set the toolchain parameter on the action but didn't
register it on the rule. Register the toolchain or set `None` inside the action.

## Additional material {:#additional-material}

For more information, check design document:
[Automatic exec groups for toolchains][aegs_design_doc].

[exec_platform]: https://bazel.build/extending/platforms#:~:text=Execution%20%2D%20a%20platform%20on%20which%20build%20tools%20execute%20build%20actions%20to%20produce%20intermediate%20and%20final%20outputs.
[exec_groups]: https://bazel.build/extending/exec-groups
[github_flag]: https://github.com/bazelbuild/bazel/issues/17134
[aegs_design_doc]: https://docs.google.com/document/d/1-rbP_hmKs9D639YWw5F_JyxPxL2bi6dSmmvj_WXak9M/edit#heading=h.5mcn15i0e1ch
[run_shell]: https://bazel.build/rules/lib/builtins/actions#run_shell
[multiple_toolchains_exec_groups]: /extending/auto-exec-groups#when-should-use-exec-groups

Project: /_project.yaml
Book: /_book.yaml

# Extension Overview

{% include "_buttons.html" %}

<!-- [TOC] -->

This page describes how to extend the BUILD language using macros
and rules.

Bazel extensions are files ending in `.bzl`. Use a
[load statement](/concepts/build-files#load) to import a symbol from an extension.

Before learning the more advanced concepts, first:

* Read about the [Starlark language](/rules/language), used in both the
  `BUILD` and `.bzl` files.

* Learn how you can [share variables](/build/share-variables)
  between two `BUILD` files.

## Macros and rules {:#macros-and-rules}

A macro is a function that instantiates rules. Macros come in two flavors:
[symbolic macros](/extending/macros) (new in Bazel 8) and [legacy
macros](/extending/legacy-macros). The two flavors of macros are defined
differently, but behave almost the same from the point of view of a user. A
macro is useful when a `BUILD` file is getting too repetitive or too complex, as
it lets you reuse some code. The function is evaluated as soon as the `BUILD`
file is read. After the evaluation of the `BUILD` file, Bazel has little
information about macros. If your macro generates a `genrule`, Bazel will
behave *almost* as if you declared that `genrule` in the `BUILD` file. (The one
exception is that targets declared in a symbolic macro have [special visibility
semantics](/extending/macros#visibility): a symbolic macro can hide its internal
targets from the rest of the package.)

A [rule](/extending/rules) is more powerful than a macro. It can access Bazel
internals and have full control over what is going on. It may for example pass
information to other rules.

If you want to reuse simple logic, start with a macro; we recommend a symbolic
macro, unless you need to support older Bazel versions. If a macro becomes
complex, it is often a good idea to make it a rule. Support for a new language
is typically done with a rule. Rules are for advanced users, and most users will
never have to write one; they will only load and call existing rules.

## Evaluation model {:#evaluation-model}

A build consists of three phases.

* **Loading phase**. First, load and evaluate all extensions and all `BUILD`
  files that are needed for the build. The execution of the `BUILD` files simply
  instantiates rules (each time a rule is called, it gets added to a graph).
  This is where macros are evaluated.

* **Analysis phase**. The code of the rules is executed (their `implementation`
  function), and actions are instantiated. An action describes how to generate
  a set of outputs from a set of inputs, such as "run gcc on hello.c and get
  hello.o". You must list explicitly which files will be generated before
  executing the actual commands. In other words, the analysis phase takes
  the graph generated by the loading phase and generates an action graph.

* **Execution phase**. Actions are executed, when at least one of their outputs is
  required. If a file is missing or if a command fails to generate one output,
  the build fails. Tests are also run during this phase.

Bazel uses parallelism to read, parse and evaluate the `.bzl` files and `BUILD`
files. A file is read at most once per build and the result of the evaluation is
cached and reused. A file is evaluated only once all its dependencies (`load()`
statements) have been resolved. By design, loading a `.bzl` file has no visible
side-effect, it only defines values and functions.

Bazel tries to be clever: it uses dependency analysis to know which files must
be loaded, which rules must be analyzed, and which actions must be executed. For
example, if a rule generates actions that you don't need for the current build,
they will not be executed.

## Creating extensions

* [Create your first macro](/rules/macro-tutorial) in order to reuse some code.
  Then [learn more about macros](/extending/macros) and [using them to create
  "custom verbs"](/rules/verbs-tutorial).

* [Follow the rules tutorial](/rules/rules-tutorial) to get started with rules.
  Next, you can read more about the [rules concepts](/extending/rules).

The two links below will be very useful when writing your own extensions. Keep
them within reach:

* The [API reference](/rules/lib)

* [Examples](https://github.com/bazelbuild/examples/tree/master/rules)

## Going further

In addition to [macros](/extending/macros) and [rules](/extending/rules), you
may want to write [aspects](/extending/aspects) and [repository
rules](/external/repo).

* Use [Buildifier](https://github.com/bazelbuild/buildtools){: .external}
  consistently to format and lint your code.

* Follow the [`.bzl` style guide](/rules/bzl-style).

* [Test](/rules/testing) your code.

* [Generate documentation](https://skydoc.bazel.build/) to help your users.

* [Optimize the performance](/rules/performance) of your code.

* [Deploy](/rules/deploying) your extensions to other people.


Project: /_project.yaml
Book: /_book.yaml

# Aspects

{% include "_buttons.html" %}

This page explains the basics and benefits of using
[aspects](/rules/lib/globals/bzl#aspect) and provides simple and advanced
examples.

Aspects allow augmenting build dependency graphs with additional information
and actions. Some typical scenarios when aspects can be useful:

*   IDEs that integrate Bazel can use aspects to collect information about the
    project.
*   Code generation tools can leverage aspects to execute on their inputs in
    *target-agnostic* manner. As an example, `BUILD` files can specify a hierarchy
    of [protobuf](https://developers.google.com/protocol-buffers/) library
    definitions, and language-specific rules can use aspects to attach
    actions generating protobuf support code for a particular language.

## Aspect basics

`BUILD` files provide a description of a project’s source code: what source
files are part of the project, what artifacts (_targets_) should be built from
those files, what the dependencies between those files are, etc. Bazel uses
this information to perform a build, that is, it figures out the set of actions
needed to produce the artifacts (such as running compiler or linker) and
executes those actions. Bazel accomplishes this by constructing a _dependency
graph_ between targets and visiting this graph to collect those actions.

Consider the following `BUILD` file:

```python
java_library(name = 'W', ...)
java_library(name = 'Y', deps = [':W'], ...)
java_library(name = 'Z', deps = [':W'], ...)
java_library(name = 'Q', ...)
java_library(name = 'T', deps = [':Q'], ...)
java_library(name = 'X', deps = [':Y',':Z'], runtime_deps = [':T'], ...)
```

This `BUILD` file defines a dependency graph shown in the following figure:

![Build graph](/rules/build-graph.png "Build graph")

**Figure 1.** `BUILD` file dependency graph.

Bazel analyzes this dependency graph by calling an implementation function of
the corresponding [rule](/extending/rules) (in this case "java_library") for every
target in the above example. Rule implementation functions generate actions that
build artifacts, such as `.jar` files, and pass information, such as locations
and names of those artifacts, to the reverse dependencies of those targets in
[providers](/extending/rules#providers).

Aspects are similar to rules in that they have an implementation function that
generates actions and returns providers. However, their power comes from
the way the dependency graph is built for them. An aspect has an implementation
and a list of all attributes it propagates along. Consider an aspect A that
propagates along attributes named "deps". This aspect can be applied to
a target X, yielding an aspect application node A(X). During its application,
aspect A is applied recursively to all targets that X refers to in its "deps"
attribute (all attributes in A's propagation list).

Thus a single act of applying aspect A to a target X yields a "shadow graph" of
the original dependency graph of targets shown in the following figure:

![Build Graph with Aspect](/rules/build-graph-aspects.png "Build graph with aspects")

**Figure 2.** Build graph with aspects.

The only edges that are shadowed are the edges along the attributes in
the propagation set, thus the `runtime_deps` edge is not shadowed in this
example. An aspect implementation function is then invoked on all nodes in
the shadow graph similar to how rule implementations are invoked on the nodes
of the original graph.

## Simple example

This example demonstrates how to recursively print the source files for a
rule and all of its dependencies that have a `deps` attribute. It shows
an aspect implementation, an aspect definition, and how to invoke the aspect
from the Bazel command line.

```python
def _print_aspect_impl(target, ctx):
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the files that make up the sources and
        # print their paths.
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                print(f.path)
    return []

print_aspect = aspect(
    implementation = _print_aspect_impl,
    attr_aspects = ['deps'],
    required_providers = [CcInfo],
)
```

Let's break the example up into its parts and examine each one individually.

### Aspect definition

```python
print_aspect = aspect(
    implementation = _print_aspect_impl,
    attr_aspects = ['deps'],
    required_providers = [CcInfo],
)
```
Aspect definitions are similar to rule definitions, and defined using
the [`aspect`](/rules/lib/globals/bzl#aspect) function.

Just like a rule, an aspect has an implementation function which in this case is
``_print_aspect_impl``.

``attr_aspects`` is a list of rule attributes along which the aspect propagates.
In this case, the aspect will propagate along the ``deps`` attribute of the
rules that it is applied to.

Another common argument for `attr_aspects` is `['*']` which would propagate the
aspect to all attributes of a rule.

``required_providers`` is a list of providers that allows the aspect to limit
its propagation to only the targets whose rules advertise its required
providers. For more details consult
[the documentation of the aspect function](/rules/lib/globals/bzl#aspect).
In this case, the aspect will only apply on targets that declare `CcInfo`
provider.

### Aspect implementation

```python
def _print_aspect_impl(target, ctx):
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the files that make up the sources and
        # print their paths.
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                print(f.path)
    return []
```

Aspect implementation functions are similar to the rule implementation
functions. They return [providers](/extending/rules#providers), can generate
[actions](/extending/rules#actions), and take two arguments:

*  `target`: the [target](/rules/lib/builtins/Target) the aspect is being applied to.
*   `ctx`: [`ctx`](/rules/lib/builtins/ctx) object that can be used to access attributes
    and generate outputs and actions.

The implementation function can access the attributes of the target rule via
[`ctx.rule.attr`](/rules/lib/builtins/ctx#rule). It can examine providers that are
provided by the target to which it is applied (via the `target` argument).

Aspects are required to return a list of providers. In this example, the aspect
does not provide anything, so it returns an empty list.

### Invoking the aspect using the command line

The simplest way to apply an aspect is from the command line using the
[`--aspects`](/reference/command-line-reference#flag--aspects)
argument. Assuming the aspect above were defined in a file named `print.bzl`
this:

```bash
bazel build //MyExample:example --aspects print.bzl%print_aspect
```

would apply the `print_aspect` to the target `example` and all of the
target rules that are accessible recursively via the `deps` attribute.

The `--aspects` flag takes one argument, which is a specification of the aspect
in the format `<extension file label>%<aspect top-level name>`.

## Advanced example

The following example demonstrates using an aspect from a target rule
that counts files in targets, potentially filtering them by extension.
It shows how to use a provider to return values, how to use parameters to pass
an argument into an aspect implementation, and how to invoke an aspect from a rule.

Note: Aspects added in rules' attributes are called *rule-propagated aspects* as
opposed to *command-line aspects* that are specified using the ``--aspects``
flag.

`file_count.bzl` file:

```python
FileCountInfo = provider(
    fields = {
        'count' : 'number of files'
    }
)

def _file_count_aspect_impl(target, ctx):
    count = 0
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the sources counting files
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                if ctx.attr.extension == '*' or ctx.attr.extension == f.extension:
                    count = count + 1
    # Get the counts from our dependencies.
    for dep in ctx.rule.attr.deps:
        count = count + dep[FileCountInfo].count
    return [FileCountInfo(count = count)]

file_count_aspect = aspect(
    implementation = _file_count_aspect_impl,
    attr_aspects = ['deps'],
    attrs = {
        'extension' : attr.string(values = ['*', 'h', 'cc']),
    }
)

def _file_count_rule_impl(ctx):
    for dep in ctx.attr.deps:
        print(dep[FileCountInfo].count)

file_count_rule = rule(
    implementation = _file_count_rule_impl,
    attrs = {
        'deps' : attr.label_list(aspects = [file_count_aspect]),
        'extension' : attr.string(default = '*'),
    },
)
```

`BUILD.bazel` file:

```python
load('//:file_count.bzl', 'file_count_rule')

cc_library(
    name = 'lib',
    srcs = [
        'lib.h',
        'lib.cc',
    ],
)

cc_binary(
    name = 'app',
    srcs = [
        'app.h',
        'app.cc',
        'main.cc',
    ],
    deps = ['lib'],
)

file_count_rule(
    name = 'file_count',
    deps = ['app'],
    extension = 'h',
)
```

### Aspect definition

```python
file_count_aspect = aspect(
    implementation = _file_count_aspect_impl,
    attr_aspects = ['deps'],
    attrs = {
        'extension' : attr.string(values = ['*', 'h', 'cc']),
    }
)
```

This example shows how the aspect propagates through the ``deps`` attribute.

``attrs`` defines a set of attributes for an aspect. Public aspect attributes
define parameters and can only be of types ``bool``, ``int`` or ``string``.
For rule-propagated aspects, ``int`` and ``string`` parameters must have
``values`` specified on them. This example has a parameter called ``extension``
that is allowed to have '``*``', '``h``', or '``cc``' as a value.

For rule-propagated aspects, parameter values are taken from the rule requesting
the aspect, using the attribute of the rule that has the same name and type.
(see the definition of ``file_count_rule``).

For command-line aspects, the parameters values can be passed using
[``--aspects_parameters``](/reference/command-line-reference#flag--aspects_parameters)
flag. The ``values`` restriction of ``int`` and ``string`` parameters may be
omitted.

Aspects are also allowed to have private attributes of types ``label`` or
``label_list``. Private label attributes can be used to specify dependencies on
tools or libraries that are needed for actions generated by aspects. There is not
a private attribute defined in this example, but the following code snippet
demonstrates how you could pass in a tool to an aspect:

```python
...
    attrs = {
        '_protoc' : attr.label(
            default = Label('//tools:protoc'),
            executable = True,
            cfg = "exec"
        )
    }
...
```

### Aspect implementation

```python
FileCountInfo = provider(
    fields = {
        'count' : 'number of files'
    }
)

def _file_count_aspect_impl(target, ctx):
    count = 0
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the sources counting files
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                if ctx.attr.extension == '*' or ctx.attr.extension == f.extension:
                    count = count + 1
    # Get the counts from our dependencies.
    for dep in ctx.rule.attr.deps:
        count = count + dep[FileCountInfo].count
    return [FileCountInfo(count = count)]
```

Just like a rule implementation function, an aspect implementation function
returns a struct of providers that are accessible to its dependencies.

In this example, the ``FileCountInfo`` is defined as a provider that has one
field ``count``. It is best practice to explicitly define the fields of a
provider using the ``fields`` attribute.

The set of providers for an aspect application A(X) is the union of providers
that come from the implementation of a rule for target X and from the
implementation of aspect A. The providers that a rule implementation propagates
are created and frozen before aspects are applied and cannot be modified from an
aspect. It is an error if a target and an aspect that is applied to it each
provide a provider with the same type, with the exceptions of
[`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo)
(which is merged, so long as the
rule and aspect specify different output groups) and
[`InstrumentedFilesInfo`](/rules/lib/providers/InstrumentedFilesInfo)
(which is taken from the aspect). This means that aspect implementations may
never return [`DefaultInfo`](/rules/lib/providers/DefaultInfo).

The parameters and private attributes are passed in the attributes of the
``ctx``. This example references the ``extension`` parameter and determines
what files to count.

For returning providers, the values of attributes along which
the aspect is propagated (from the `attr_aspects` list) are replaced with
the results of an application of the aspect to them. For example, if target
X has Y and Z in its deps, `ctx.rule.attr.deps` for A(X) will be [A(Y), A(Z)].
In this example, ``ctx.rule.attr.deps`` are Target objects that are the
results of applying the aspect to the 'deps' of the original target to which
the aspect has been applied.

In the example, the aspect accesses the ``FileCountInfo`` provider from the
target's dependencies to accumulate the total transitive number of files.

### Invoking the aspect from a rule

```python
def _file_count_rule_impl(ctx):
    for dep in ctx.attr.deps:
        print(dep[FileCountInfo].count)

file_count_rule = rule(
    implementation = _file_count_rule_impl,
    attrs = {
        'deps' : attr.label_list(aspects = [file_count_aspect]),
        'extension' : attr.string(default = '*'),
    },
)
```

The rule implementation demonstrates how to access the ``FileCountInfo``
via the ``ctx.attr.deps``.

The rule definition demonstrates how to define a parameter (``extension``)
and give it a default value (``*``). Note that having a default value that
was not one of '``cc``', '``h``', or '``*``' would be an error due to the
restrictions placed on the parameter in the aspect definition.

### Invoking an aspect through a target rule

```python
load('//:file_count.bzl', 'file_count_rule')

cc_binary(
    name = 'app',
...
)

file_count_rule(
    name = 'file_count',
    deps = ['app'],
    extension = 'h',
)
```

This demonstrates how to pass the ``extension`` parameter into the aspect
via the rule. Since the ``extension`` parameter has a default value in the
rule implementation, ``extension`` would be considered an optional parameter.

When the ``file_count`` target is built, our aspect will be evaluated for
itself, and all of the targets accessible recursively via ``deps``.

## References

* [`aspect` API reference](/rules/lib/globals/bzl#aspect)


Project: /_project.yaml
Book: /_book.yaml

# Configurations

<devsite-mathjax config="TeX-AMS-MML_SVG"></devsite-mathjax>

{% include "_buttons.html" %}

This page covers the benefits and basic usage of Starlark configurations,
Bazel's API for customizing how your project builds. It includes how to define
build settings and provides examples.

This makes it possible to:

*   define custom flags for your project, obsoleting the need for
     [`--define`](/docs/configurable-attributes#custom-keys)
*   write
    [transitions](/rules/lib/builtins/transition#transition) to configure deps in
    different configurations than their parents
    (such as `--compilation_mode=opt` or `--cpu=arm`)
*   bake better defaults into rules (such as automatically build `//my:android_app`
    with a specified SDK)

and more, all completely from .bzl files (no Bazel release required). See the
`bazelbuild/examples` repo for
[examples](https://github.com/bazelbuild/examples/tree/HEAD/configurations){: .external}.

## User-defined build settings {:#user-defined-build-settings}

A build setting is a single piece of
[configuration](/extending/rules#configurations)
information. Think of a configuration as a key/value map. Setting `--cpu=ppc`
and `--copt="-DFoo"` produces a configuration that looks like
`{cpu: ppc, copt: "-DFoo"}`. Each entry is a build setting.

Traditional flags like `cpu` and `copt` are native settings —
their keys are defined and their values are set inside native bazel java code.
Bazel users can only read and write them via the command line
and other APIs maintained natively. Changing native flags, and the APIs
that expose them, requires a bazel release. User-defined build
settings are defined in `.bzl` files (and thus, don't need a bazel release to
register changes). They also can be set via the command line
(if they're designated as `flags`, see more below), but can also be
set via [user-defined transitions](#user-defined-transitions).

### Defining build settings {:#defining-build-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/basic_build_setting){: .external}

#### The `build_setting` `rule()` parameter {:#rule-parameter}

Build settings are rules like any other rule and are differentiated using the
Starlark `rule()` function's `build_setting`
[attribute](/rules/lib/globals/bzl#rule.build_setting).

```python
# example/buildsettings/build_settings.bzl
string_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

The `build_setting` attribute takes a function that designates the type of the
build setting. The type is limited to a set of basic Starlark types like
`bool` and `string`. See the `config` module
[documentation](/rules/lib/toplevel/config)  for details. More complicated typing can be
done in the rule's implementation function. More on this below.

The `config` module's functions takes an optional boolean parameter, `flag`,
which is set to false by default. if `flag` is set to true, the build setting
can be set on the command line by users as well as internally by rule writers
via default values and [transitions](/rules/lib/builtins/transition#transition).
Not all settings should be settable by users. For example, if you as a rule
writer have some debug mode that you'd like to turn on inside test rules,
you don't want to give users the ability to indiscriminately turn on that
feature inside other non-test rules.

#### Using ctx.build_setting_value {:#ctx-build-setting-value}

Like all rules, build setting rules have [implementation functions](/extending/rules#implementation-function).
The basic Starlark-type value of the build settings can be accessed via the
`ctx.build_setting_value` method. This method is only available to
[`ctx`](/rules/lib/builtins/ctx) objects of build setting rules. These implementation
methods can directly forward the build settings value or do additional work on
it, like type checking or more complex struct creation. Here's how you would
implement an `enum`-typed build setting:

```python
# example/buildsettings/build_settings.bzl
TemperatureProvider = provider(fields = ['type'])

temperatures = ["HOT", "LUKEWARM", "ICED"]

def _impl(ctx):
    raw_temperature = ctx.build_setting_value
    if raw_temperature not in temperatures:
        fail(str(ctx.label) + " build setting allowed to take values {"
             + ", ".join(temperatures) + "} but was set to unallowed value "
             + raw_temperature)
    return TemperatureProvider(type = raw_temperature)

temperature = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

Note: if a rule depends on a build setting, it will receive whatever providers
the build setting implementation function returns, like any other dependency.
But all other references to the value of the build setting (such as in transitions)
will see its basic Starlark-typed value, not this post implementation function
value.

#### Defining multi-set string flags {:#multi-set-string-flags}

String settings have an additional `allow_multiple` parameter which allows the
flag to be set multiple times on the command line or in bazelrcs. Their default
value is still set with a string-typed attribute:

```python
# example/buildsettings/build_settings.bzl
allow_multiple_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True, allow_multiple = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "allow_multiple_flag")
allow_multiple_flag(
    name = "roasts",
    build_setting_default = "medium"
)
```

Each setting of the flag is treated as a single value:

```shell
$ bazel build //my/target --//example:roasts=blonde \
    --//example:roasts=medium,dark
```

The above is parsed to `{"//example:roasts": ["blonde", "medium,dark"]}` and
`ctx.build_setting_value` returns the list `["blonde", "medium,dark"]`.

#### Instantiating build settings {:#instantiating-build-settings}

Rules defined with the `build_setting` parameter have an implicit mandatory
`build_setting_default` attribute. This attribute takes on the same type as
declared by the `build_setting` param.

```python
# example/buildsettings/build_settings.bzl
FlavorProvider = provider(fields = ['type'])

def _impl(ctx):
    return FlavorProvider(type = ctx.build_setting_value)

flavor = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "flavor")
flavor(
    name = "favorite_flavor",
    build_setting_default = "APPLE"
)
```

### Predefined settings {:#predefined-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/use_skylib_build_setting){: .external}

The
[Skylib](https://github.com/bazelbuild/bazel-skylib){: .external}
library includes a set of predefined settings you can instantiate without having
to write custom Starlark.

For example, to define a setting that accepts a limited set of string values:

```python
# example/BUILD
load("@bazel_skylib//rules:common_settings.bzl", "string_flag")
string_flag(
    name = "myflag",
    values = ["a", "b", "c"],
    build_setting_default = "a",
)
```

For a complete list, see
[Common build setting rules](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/common_settings.bzl){: .external}.

### Using build settings {:#using-build-settings}

#### Depending on build settings {:#depending-on-build-settings}

If a target would like to read a piece of configuration information, it can
directly depend on the build setting via a regular attribute dependency.

```python
# example/rules.bzl
load("//example/buildsettings:build_settings.bzl", "FlavorProvider")
def _rule_impl(ctx):
    if ctx.attr.flavor[FlavorProvider].type == "ORANGE":
        ...

drink_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "flavor": attr.label()
    }
)
```

```python
# example/BUILD
load("//example:rules.bzl", "drink_rule")
load("//example/buildsettings:build_settings.bzl", "flavor")
flavor(
    name = "favorite_flavor",
    build_setting_default = "APPLE"
)
drink_rule(
    name = "my_drink",
    flavor = ":favorite_flavor",
)
```

Languages may wish to create a canonical set of build settings which all rules
for that language depend on. Though the native concept of `fragments` no longer
exists as a hardcoded object in Starlark configuration world, one way to
translate this concept would be to use sets of common implicit attributes. For
example:

```python
# kotlin/rules.bzl
_KOTLIN_CONFIG = {
    "_compiler": attr.label(default = "//kotlin/config:compiler-flag"),
    "_mode": attr.label(default = "//kotlin/config:mode-flag"),
    ...
}

...

kotlin_library = rule(
    implementation = _rule_impl,
    attrs = dicts.add({
        "library-attr": attr.string()
    }, _KOTLIN_CONFIG)
)

kotlin_binary = rule(
    implementation = _binary_impl,
    attrs = dicts.add({
        "binary-attr": attr.label()
    }, _KOTLIN_CONFIG)

```

#### Using build settings on the command line {:#build-settings-command-line}

Similar to most native flags, you can use the command line to set build settings
[that are marked as flags](#rule-parameter). The build
setting's name is its full target path using `name=value` syntax:

```shell
$ bazel build //my/target --//example:string_flag=some-value # allowed
$ bazel build //my/target --//example:string_flag some-value # not allowed
```

Special boolean syntax is supported:

```shell
$ bazel build //my/target --//example:boolean_flag
$ bazel build //my/target --no//example:boolean_flag
```

#### Using build setting aliases {:#using-build-setting-aliases}

You can set an alias for your build setting target path to make it easier to read
on the command line. Aliases function similarly to native flags and also make use
of the double-dash option syntax.

Set an alias by adding `--flag_alias=ALIAS_NAME=TARGET_PATH`
to your `.bazelrc` . For example, to set an alias to `coffee`:

```shell
# .bazelrc
build --flag_alias=coffee=//experimental/user/starlark_configurations/basic_build_setting:coffee-temp
```

Best Practice: Setting an alias multiple times results in the most recent
one taking precedence. Use unique alias names to avoid unintended parsing results.

To make use of the alias, type it in place of the build setting target path.
With the above example of `coffee` set in the user's `.bazelrc`:

```shell
$ bazel build //my/target --coffee=ICED
```

instead of

```shell
$ bazel build //my/target --//experimental/user/starlark_configurations/basic_build_setting:coffee-temp=ICED
```
Best Practice: While it possible to set aliases on the command line, leaving them
in a `.bazelrc` reduces command line clutter.

### Label-typed build settings {:#label-typed-build-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/label_typed_build_setting){: .external}

Unlike other build settings, label-typed settings cannot be defined using the
`build_setting` rule parameter. Instead, bazel has two built-in rules:
`label_flag` and `label_setting`. These rules forward the providers of the
actual target to which the build setting is set. `label_flag` and
`label_setting` can be read/written by transitions and `label_flag` can be set
by the user like other `build_setting` rules can. Their only difference is they
can't customely defined.

Label-typed settings will eventually replace the functionality of late-bound
defaults. Late-bound default attributes are Label-typed attributes whose
final values can be affected by configuration. In Starlark, this will replace
the [`configuration_field`](/rules/lib/globals/bzl#configuration_field)
 API.

```python
# example/rules.bzl
MyProvider = provider(fields = ["my_field"])

def _dep_impl(ctx):
    return MyProvider(my_field = "yeehaw")

dep_rule = rule(
    implementation = _dep_impl
)

def _parent_impl(ctx):
    if ctx.attr.my_field_provider[MyProvider].my_field == "cowabunga":
        ...

parent_rule = rule(
    implementation = _parent_impl,
    attrs = { "my_field_provider": attr.label() }
)

```

```python
# example/BUILD
load("//example:rules.bzl", "dep_rule", "parent_rule")

dep_rule(name = "dep")

parent_rule(name = "parent", my_field_provider = ":my_field_provider")

label_flag(
    name = "my_field_provider",
    build_setting_default = ":dep"
)
```

### Build settings and select() {:#build-settings-and-select}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/select_on_build_setting){: .external}

Users can configure attributes on build settings by using
 [`select()`](/reference/be/functions#select). Build setting targets can be passed to the `flag_values` attribute of
`config_setting`. The value to match to the configuration is passed as a
`String` then parsed to the type of the build setting for matching.

```python
config_setting(
    name = "my_config",
    flag_values = {
        "//example:favorite_flavor": "MANGO"
    }
)
```

## User-defined transitions {:#user-defined-transitions}

A configuration
[transition](/rules/lib/builtins/transition#transition)
maps the transformation from one configured target to another within the
build graph.

Important: Transitions have [memory and performance impact](#memory-performance-considerations).

### Defining {:#defining}

Transitions define configuration changes between rules. For example, a request
like "compile my dependency for a different CPU than its parent" is handled by a
transition.

Formally, a transition is a function from an input configuration to one or more
output configurations. Most transitions are 1:1 such as "override the input
configuration with `--cpu=ppc`". 1:2+ transitions can also exist but come
with special restrictions.

In Starlark, transitions are defined much like rules, with a defining
`transition()`
[function](/rules/lib/builtins/transition#transition)
and an implementation function.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {"//example:favorite_flavor" : "MINT"}

hot_chocolate_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)
```
The `transition()` function takes in an implementation function, a set of
build settings to read(`inputs`), and a set of build settings to write
(`outputs`). The implementation function has two parameters, `settings` and
`attr`. `settings` is a dictionary {`String`:`Object`} of all settings declared
in the `inputs` parameter to `transition()`.

`attr` is a dictionary of attributes and values of the rule to which the
transition is attached. When attached as an
[outgoing edge transition](#outgoing-edge-transitions), the values of these
attributes are all configured post-select() resolution. When attached as
an [incoming edge transition](#incoming-edge-transitions), `attr` does not
include any attributes that use a selector to resolve their value. If an
incoming edge transition on `--foo` reads attribute `bar` and then also
selects on `--foo` to set attribute `bar`, then there's a chance for the
incoming edge transition to read the wrong value of `bar` in the transition.

Note: Since transitions are attached to rule definitions and `select()`s are
attached to rule instantiations (such as targets), errors related to `select()`s on
read attributes will pop up when users create targets rather than when rules are
written. It may be worth taking extra care to communicate to rule users which
attributes they should be wary of selecting on or taking other precautions.

The implementation function must return a dictionary (or list of
dictionaries, in the case of
transitions with multiple output configurations)
of new build settings values to apply. The returned dictionary keyset(s) must
contain exactly the set of build settings passed to the `outputs`
parameter of the transition function. This is true even if a build setting is
not actually changed over the course of the transition - its original value must
be explicitly passed through in the returned dictionary.

### Defining 1:2+ transitions {:#defining-1-2-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/multi_arch_binary){: .external}

[Outgoing edge transition](#outgoing-edge-transitions) can map a single input
configuration to two or more output configurations. This is useful for defining
rules that bundle multi-architecture code.

1:2+ transitions are defined by returning a list of dictionaries in the
transition implementation function.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return [
        {"//example:favorite_flavor" : "LATTE"},
        {"//example:favorite_flavor" : "MOCHA"},
    ]

coffee_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)
```
They can also set custom keys that the rule implementation function can use to
read individual dependencies:

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {
        "Apple deps": {"//command_line_option:cpu": "ppc"},
        "Linux deps": {"//command_line_option:cpu": "x86"},
    }

multi_arch_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
)
```

### Attaching transitions {:#attaching-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/attaching_transitions_to_rules){: .external}

Transitions can be attached in two places: incoming edges and outgoing edges.
Effectively this means rules can transition their own configuration (incoming
edge transition) and transition their dependencies' configurations (outgoing
edge transition).

NOTE: There is currently no way to attach Starlark transitions to native rules.
If you need to do this, contact
bazel-discuss@googlegroups.com
for help with figuring out workarounds.

### Incoming edge transitions {:#incoming-edge-transitions}

Incoming edge transitions are activated by attaching a `transition` object
(created by `transition()`) to `rule()`'s `cfg` parameter:

```python
# example/rules.bzl
load("example/transitions:transitions.bzl", "hot_chocolate_transition")
drink_rule = rule(
    implementation = _impl,
    cfg = hot_chocolate_transition,
    ...
```

Incoming edge transitions must be 1:1 transitions.

### Outgoing edge transitions {:#outgoing-edge-transitions}

Outgoing edge transitions are activated by attaching a `transition` object
(created by `transition()`) to an attribute's `cfg` parameter:

```python
# example/rules.bzl
load("example/transitions:transitions.bzl", "coffee_transition")
drink_rule = rule(
    implementation = _impl,
    attrs = { "dep": attr.label(cfg = coffee_transition)}
    ...
```
Outgoing edge transitions can be 1:1 or 1:2+.

See [Accessing attributes with transitions](#accessing-attributes-with-transitions)
for how to read these keys.

### Transitions on native options {:#transitions-native-options}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/transition_on_native_flag){: .external}

Starlark transitions can also declare reads and writes on native build
configuration options via a special prefix to the option name.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {"//command_line_option:cpu": "k8"}

cpu_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
```

#### Unsupported native options {:#unsupported-native-options}

Bazel doesn't support transitioning on `--define` with
`"//command_line_option:define"`. Instead, use a custom
[build setting](#user-defined-build-settings). In general, new usages of
`--define` are discouraged in favor of build settings.

Bazel doesn't support transitioning on `--config`. This is because `--config` is
an "expansion" flag that expands to other flags.

Crucially, `--config` may include flags that don't affect build configuration,
such as
[`--spawn_strategy`](/docs/user-manual#spawn-strategy)
. Bazel, by design, can't bind such flags to individual targets. This means
there's no coherent way to apply them in transitions.

As a workaround, you can explicitly itemize the flags that *are* part of
the configuration in your transition. This requires maintaining the `--config`'s
expansion in two places, which is a known UI blemish.

### Transitions on allow multiple build settings {:#transitions-multiple-build-settings}

When setting build settings that
[allow multiple values](#defining-multi-set-string-flags), the value of the
setting must be set with a list.

```python
# example/buildsettings/build_settings.bzl
string_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True, allow_multiple = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "string_flag")
string_flag(name = "roasts", build_setting_default = "medium")
```

```python
# example/transitions/rules.bzl
def _transition_impl(settings, attr):
    # Using a value of just "dark" here will throw an error
    return {"//example:roasts" : ["dark"]},

coffee_transition = transition(
    implementation = _transition_impl,
    inputs = [],
    outputs = ["//example:roasts"]
)
```

### No-op transitions {:#no-op-transitions}

If a transition returns `{}`, `[]`, or `None`, this is shorthand for keeping all
settings at their original values. This can be more convenient than explicitly
setting each output to itself.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (attr)
    if settings["//example:already_chosen"] is True:
      return {}
    return {
      "//example:favorite_flavor": "dark chocolate",
      "//example:include_marshmallows": "yes",
      "//example:desired_temperature": "38C",
    }

hot_chocolate_transition = transition(
    implementation = _impl,
    inputs = ["//example:already_chosen"],
    outputs = [
        "//example:favorite_flavor",
        "//example:include_marshmallows",
        "//example:desired_temperature",
    ]
)
```

### Accessing attributes with transitions {:#accessing-attributes-with-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/read_attr_in_transition){: .external}

When [attaching a transition to an outgoing edge](#outgoing-edge-transitions)
(regardless of whether the transition is a 1:1 or 1:2+ transition), `ctx.attr` is forced to be a list
if it isn't already. The order of elements in this list is unspecified.


```python
# example/transitions/rules.bzl
def _transition_impl(settings, attr):
    return {"//example:favorite_flavor" : "LATTE"},

coffee_transition = transition(
    implementation = _transition_impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)

def _rule_impl(ctx):
    # Note: List access even though "dep" is not declared as list
    transitioned_dep = ctx.attr.dep[0]

    # Note: Access doesn't change, other_deps was already a list
    for other_dep in ctx.attr.other_deps:
      # ...


coffee_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "dep": attr.label(cfg = coffee_transition)
        "other_deps": attr.label_list(cfg = coffee_transition)
    })
```

If the transition is `1:2+` and sets custom keys, `ctx.split_attr` can be used
to read individual deps for each key:

```python
# example/transitions/rules.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {
        "Apple deps": {"//command_line_option:cpu": "ppc"},
        "Linux deps": {"//command_line_option:cpu": "x86"},
    }

multi_arch_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
)

def _rule_impl(ctx):
    apple_dep = ctx.split_attr.dep["Apple deps"]
    linux_dep = ctx.split_attr.dep["Linux deps"]
    # ctx.attr has a list of all deps for all keys. Order is not guaranteed.
    all_deps = ctx.attr.dep

multi_arch_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "dep": attr.label(cfg = multi_arch_transition)
    })
```

See [complete example](https://github.com/bazelbuild/examples/tree/main/configurations/multi_arch_binary)
here.

## Integration with platforms and toolchains {:#integration-platforms-toolchains}

Many native flags today, like `--cpu` and `--crosstool_top` are related to
toolchain resolution. In the future, explicit transitions on these types of
flags will likely be replaced by transitioning on the
[target platform](/extending/platforms).

## Memory and performance considerations {:#memory-performance-considerations}

Adding transitions, and therefore new configurations, to your build comes at a
cost: larger build graphs, less comprehensible build graphs, and slower
builds. It's worth considering these costs when considering
using transitions in your build rules. Below is an example of how a transition
might create exponential growth of your build graph.

### Badly behaved builds: a case study {:#badly-behaved-builds}

![Scalability graph](/rules/scalability-graph.png "Scalability graph")

**Figure 1.** Scalability graph showing a top level target and its dependencies.

This graph shows a top level target, `//pkg:app`, which depends on two targets, a
`//pkg:1_0` and `//pkg:1_1`. Both these targets depend on two targets, `//pkg:2_0` and
`//pkg:2_1`. Both these targets depend on two targets, `//pkg:3_0` and `//pkg:3_1`.
This continues on until `//pkg:n_0` and `//pkg:n_1`, which both depend on a single
target, `//pkg:dep`.

Building `//pkg:app` requires \\(2n+2\\) targets:

* `//pkg:app`
* `//pkg:dep`
* `//pkg:i_0` and `//pkg:i_1` for \\(i\\) in \\([1..n]\\)

Imagine you [implement](#user-defined-build-settings) a flag
`--//foo:owner=<STRING>` and `//pkg:i_b` applies

    depConfig = myConfig + depConfig.owner="$(myConfig.owner)$(b)"

In other words, `//pkg:i_b` appends `b` to the old value of `--owner` for all
its deps.

This produces the following [configured targets](/reference/glossary#configured-target):

```
//pkg:app                              //foo:owner=""
//pkg:1_0                              //foo:owner=""
//pkg:1_1                              //foo:owner=""
//pkg:2_0 (via //pkg:1_0)              //foo:owner="0"
//pkg:2_0 (via //pkg:1_1)              //foo:owner="1"
//pkg:2_1 (via //pkg:1_0)              //foo:owner="0"
//pkg:2_1 (via //pkg:1_1)              //foo:owner="1"
//pkg:3_0 (via //pkg:1_0 → //pkg:2_0)  //foo:owner="00"
//pkg:3_0 (via //pkg:1_0 → //pkg:2_1)  //foo:owner="01"
//pkg:3_0 (via //pkg:1_1 → //pkg:2_0)  //foo:owner="10"
//pkg:3_0 (via //pkg:1_1 → //pkg:2_1)  //foo:owner="11"
...
```

`//pkg:dep` produces \\(2^n\\) configured targets: `config.owner=`
"\\(b_0b_1...b_n\\)" for all \\(b_i\\) in \\(\{0,1\}\\).

This makes the build graph exponentially larger than the target graph, with
corresponding memory and performance consequences.

TODO: Add strategies for measurement and mitigation of these issues.

## Further reading {:#further-reading}

For more details on modifying build configurations, see:

 * [Starlark Build Configuration](https://docs.google.com/document/d/1vc8v-kXjvgZOdQdnxPTaV0rrLxtP2XwnD2tAZlYJOqw/edit?usp=sharing){: .external}
 * [Bazel Configurability Roadmap](https://bazel.build/community/roadmaps-configurability){: .external}
 * Full [set](https://github.com/bazelbuild/examples/tree/HEAD/configurations){: .external} of end to end examples


Project: /_project.yaml
Book: /_book.yaml

# Platforms

{% include "_buttons.html" %}

Bazel can build and test code on a variety of hardware, operating systems, and
system configurations, using many different versions of build tools such as
linkers and compilers. To help manage this complexity, Bazel has a concept of
*constraints* and *platforms*. A constraint is a dimension in which build or
production environments may differ, such as CPU architecture, the presence or
absence of a GPU, or the version of a system-installed compiler. A platform is a
named collection of choices for these constraints, representing the particular
resources that are available in some environment.

Modeling the environment as a platform helps Bazel to automatically select the
appropriate
[toolchains](/extending/toolchains)
for build actions. Platforms can also be used in combination with the
[config_setting](/reference/be/general#config_setting)
rule to write [configurable attributes](/docs/configurable-attributes).

Bazel recognizes three roles that a platform may serve:

*  **Host** - the platform on which Bazel itself runs.
*  **Execution** - a platform on which build tools execute build actions to
   produce intermediate and final outputs.
*  **Target** - a platform on which a final output resides and executes.

Bazel supports the following build scenarios regarding platforms:

*  **Single-platform builds** (default) - host, execution, and target platforms
   are the same. For example, building a Linux executable on Ubuntu running on
   an Intel x64 CPU.

*  **Cross-compilation builds** - host and execution platforms are the same, but
   the target platform is different. For example, building an iOS app on macOS
   running on a MacBook Pro.

*  **Multi-platform builds** - host, execution, and target platforms are all
   different.

Tip: for detailed instructions on migrating your project to platforms, see
[Migrating to Platforms](/concepts/platforms).

## Defining constraints and platforms {:#constraints-platforms}

The space of possible choices for platforms is defined by using the
[`constraint_setting`][constraint_setting] and
[`constraint_value`][constraint_value] rules within `BUILD` files.
`constraint_setting` creates a new dimension, while
`constraint_value` creates a new value for a given dimension; together they
effectively define an enum and its possible values. For example, the following
snippet of a `BUILD` file introduces a constraint for the system's glibc version
with two possible values.

[constraint_setting]: /reference/be/platforms-and-toolchains#constraint_setting
[constraint_value]: /reference/be/platforms-and-toolchains#constraint_value

```python
constraint_setting(name = "glibc_version")

constraint_value(
    name = "glibc_2_25",
    constraint_setting = ":glibc_version",
)

constraint_value(
    name = "glibc_2_26",
    constraint_setting = ":glibc_version",
)
```

Constraints and their values may be defined across different packages in the
workspace. They are referenced by label and subject to the usual visibility
controls. If visibility allows, you can extend an existing constraint setting by
defining your own value for it.

The [`platform`](/reference/be/platforms-and-toolchains#platform) rule introduces a new platform with
certain choices of constraint values. The
following creates a platform named `linux_x86`, and says that it describes any
environment that runs a Linux operating system on an x86_64 architecture with a
glibc version of 2.25. (See below for more on Bazel's built-in constraints.)

```python
platform(
    name = "linux_x86",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
        ":glibc_2_25",
    ],
)
```

Note: It is an error for a platform to specify more than one value of the
same constraint setting, such as `@platforms//cpu:x86_64` and
`@platforms//cpu:arm` for `@platforms//cpu:cpu`.

## Generally useful constraints and platforms {:#useful-constraints-platforms}

To keep the ecosystem consistent, Bazel team maintains a repository with
constraint definitions for the most popular CPU architectures and operating
systems. These are all located in
[https://github.com/bazelbuild/platforms](https://github.com/bazelbuild/platforms){: .external}.

Bazel ships with the following special platform definition:
`@platforms//host` (aliased as `@bazel_tools//tools:host_platform`). This is the
autodetected host platform value -
represents autodetected platform for the system Bazel is running on.

## Specifying a platform for a build {:#specifying-build-platform}

You can specify the host and target platforms for a build using the following
command-line flags:

*  `--host_platform` - defaults to `@bazel_tools//tools:host_platform`
   *  This target is aliased to `@platforms//host`, which is backed by a repo
      rule that detects the host OS and CPU and writes the platform target.
   *  There's also `@platforms//host:constraints.bzl`, which exposes
      an array called `HOST_CONSTRAINTS`, which can be used in other BUILD and
      Starlark files.
*  `--platforms` - defaults to the host platform
   *  This means that when no other flags are set,
      `@platforms//host` is the target platform.
   *  If `--host_platform` is set and not `--platforms`, the value of
      `--host_platform` is both the host and target platform.

## Skipping incompatible targets {:#skipping-incompatible-targets}

When building for a specific target platform it is often desirable to skip
targets that will never work on that platform. For example, your Windows device
driver is likely going to generate lots of compiler errors when building on a
Linux machine with `//...`. Use the
[`target_compatible_with`](/reference/be/common-definitions#common.target_compatible_with)
attribute to tell Bazel what target platform constraints your code has.

The simplest use of this attribute restricts a target to a single platform.
The target will not be built for any platform that doesn't satisfy all of the
constraints. The following example restricts `win_driver_lib.cc` to 64-bit
Windows.

```python
cc_library(
    name = "win_driver_lib",
    srcs = ["win_driver_lib.cc"],
    target_compatible_with = [
        "@platforms//cpu:x86_64",
        "@platforms//os:windows",
    ],
)
```

`:win_driver_lib` is *only* compatible for building with 64-bit Windows and
incompatible with all else. Incompatibility is transitive. Any targets
that transitively depend on an incompatible target are themselves considered
incompatible.

### When are targets skipped? {:#when-targets-skipped}

Targets are skipped when they are considered incompatible and included in the
build as part of a target pattern expansion. For example, the following two
invocations skip any incompatible targets found in a target pattern expansion.

```console
$ bazel build --platforms=//:myplatform //...
```

```console
$ bazel build --platforms=//:myplatform //:all
```

Incompatible tests in a [`test_suite`](/reference/be/general#test_suite) are
similarly skipped if the `test_suite` is specified on the command line with
[`--expand_test_suites`](/reference/command-line-reference#flag--expand_test_suites).
In other words, `test_suite` targets on the command line behave like `:all` and
`...`. Using `--noexpand_test_suites` prevents expansion and causes
`test_suite` targets with incompatible tests to also be incompatible.

Explicitly specifying an incompatible target on the command line results in an
error message and a failed build.

```console
$ bazel build --platforms=//:myplatform //:target_incompatible_with_myplatform
...
ERROR: Target //:target_incompatible_with_myplatform is incompatible and cannot be built, but was explicitly requested.
...
FAILED: Build did NOT complete successfully
```

Incompatible explicit targets are silently skipped if
`--skip_incompatible_explicit_targets` is enabled.

### More expressive constraints {:#expressive-constraints}

For more flexibility in expressing constraints, use the
`@platforms//:incompatible`
[`constraint_value`](/reference/be/platforms-and-toolchains#constraint_value)
that no platform satisfies.

Use [`select()`](/reference/be/functions#select) in combination with
`@platforms//:incompatible` to express more complicated restrictions. For
example, use it to implement basic OR logic. The following marks a library
compatible with macOS and Linux, but no other platforms.

Note: An empty constraints list is equivalent to "compatible with everything".

```python
cc_library(
    name = "unixish_lib",
    srcs = ["unixish_lib.cc"],
    target_compatible_with = select({
        "@platforms//os:osx": [],
        "@platforms//os:linux": [],
        "//conditions:default": ["@platforms//:incompatible"],
    }),
)
```

The above can be interpreted as follows:

1. When targeting macOS, the target has no constraints.
2. When targeting Linux, the target has no constraints.
3. Otherwise, the target has the `@platforms//:incompatible` constraint. Because
   `@platforms//:incompatible` is not part of any platform, the target is
   deemed incompatible.

To make your constraints more readable, use
[skylib](https://github.com/bazelbuild/bazel-skylib){: .external}'s
[`selects.with_or()`](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/selects_doc.md#selectswith_or){: .external}.

You can express inverse compatibility in a similar way. The following example
describes a library that is compatible with everything _except_ for ARM.

```python
cc_library(
    name = "non_arm_lib",
    srcs = ["non_arm_lib.cc"],
    target_compatible_with = select({
        "@platforms//cpu:arm": ["@platforms//:incompatible"],
        "//conditions:default": [],
    }),
)
```

### Detecting incompatible targets using `bazel cquery` {:#cquery-incompatible-target-detection}

You can use the
[`IncompatiblePlatformProvider`](/rules/lib/providers/IncompatiblePlatformProvider)
in `bazel cquery`'s [Starlark output
format](/query/cquery#output-format-definition) to distinguish
incompatible targets from compatible ones.

This can be used to filter out incompatible targets. The example below will
only print the labels for targets that are compatible. Incompatible targets are
not printed.

```console
$ cat example.cquery

def format(target):
  if "IncompatiblePlatformProvider" not in providers(target):
    return target.label
  return ""


$ bazel cquery //... --output=starlark --starlark:file=example.cquery
```

### Known Issues

Incompatible targets [ignore visibility
restrictions](https://github.com/bazelbuild/bazel/issues/16044).


Project: /_project.yaml
Book: /_book.yaml

# Execution Groups

{% include "_buttons.html" %}

Execution groups allow for multiple execution platforms within a single target.
Each execution group has its own [toolchain](/extending/toolchains) dependencies and
performs its own [toolchain resolution](/extending/toolchains#toolchain-resolution).

## Current status {:#current-status}

Execution groups for certain natively declared actions, like `CppLink`, can be
used inside `exec_properties` to set per-action, per-target execution
requirements. For more details, see the
[Default execution groups](#exec-groups-for-native-rules) section.

## Background {:#background}

Execution groups allow the rule author to define sets of actions, each with a
potentially different execution platform. Multiple execution platforms can allow
actions to execution differently, for example compiling an iOS app on a remote
(linux) worker and then linking/code signing on a local mac worker.

Being able to define groups of actions also helps alleviate the usage of action
mnemonics as a proxy for specifying actions. Mnemonics are not guaranteed to be
unique and can only reference a single action. This is especially helpful in
allocating extra resources to specific memory and processing intensive actions
like linking in C++ builds without over-allocating to less demanding tasks.

## Defining execution groups {:#defining-exec-groups}

During rule definition, rule authors can
[declare](/rules/lib/globals/bzl#exec_group)
a set of execution groups. On each execution group, the rule author can specify
everything needed to select an execution platform for that execution group,
namely any constraints via `exec_compatible_with` and toolchain types via
`toolchain`.

```python
# foo.bzl
my_rule = rule(
    _impl,
    exec_groups = {
        "link": exec_group(
            exec_compatible_with = ["@platforms//os:linux"],
            toolchains = ["//foo:toolchain_type"],
        ),
        "test": exec_group(
            toolchains = ["//foo_tools:toolchain_type"],
        ),
    },
    attrs = {
        "_compiler": attr.label(cfg = config.exec("link"))
    },
)
```

In the code snippet above, you can see that tool dependencies can also specify
transition for an exec group using the
[`cfg`](/rules/lib/toplevel/attr#label)
attribute param and the
[`config`](/rules/lib/toplevel/config)
module. The module exposes an `exec` function which takes a single string
parameter which is the name of the exec group for which the dependency should be
built.

As on native rules, the `test` execution group is present by default on Starlark
test rules.

## Accessing execution groups {:#accessing-exec-groups}

In the rule implementation, you can declare that actions should be run on the
execution platform of an execution group. You can do this by using the `exec_group`
param of action generating methods, specifically [`ctx.actions.run`]
(/rules/lib/builtins/actions#run) and
[`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell).

```python
# foo.bzl
def _impl(ctx):
  ctx.actions.run(
     inputs = [ctx.attr._some_tool, ctx.srcs[0]]
     exec_group = "compile",
     # ...
  )
```

Rule authors will also be able to access the [resolved toolchains](/extending/toolchains#toolchain-resolution)
of execution groups, similarly to how you
can access the resolved toolchain of a target:

```python
# foo.bzl
def _impl(ctx):
  foo_info = ctx.exec_groups["link"].toolchains["//foo:toolchain_type"].fooinfo
  ctx.actions.run(
     inputs = [foo_info, ctx.srcs[0]]
     exec_group = "link",
     # ...
  )
```

Note: If an action uses a toolchain from an execution group, but doesn't specify
that execution group in the action declaration, that may potentially cause
issues. A mismatch like this may not immediately cause failures, but is a latent
problem.

### Default execution groups {:#exec-groups-for-native-rules}

The following execution groups are predefined:

* `test`: Test runner actions (for more details, see
  the [execution platform section of the Test Encylopedia](/reference/test-encyclopedia#execution-platform)).
* `cpp_link`: C++ linking actions.

## Using execution groups to set execution properties {:#using-exec-groups-for-exec-properties}

Execution groups are integrated with the
[`exec_properties`](/reference/be/common-definitions#common-attributes)
attribute that exists on every rule and allows the target writer to specify a
string dict of properties that is then passed to the execution machinery. For
example, if you wanted to set some property, say memory, for the target and give
certain actions a higher memory allocation, you would write an `exec_properties`
entry with an execution-group-augmented key, such as:

```python
# BUILD
my_rule(
    name = 'my_target',
    exec_properties = {
        'mem': '12g',
        'link.mem': '16g'
    }
    …
)
```

All actions with `exec_group = "link"` would see the exec properties
dictionary as `{"mem": "16g"}`. As you see here, execution-group-level
settings override target-level settings.

## Using execution groups to set platform constraints {:#using-exec-groups-for-platform-constraints}

Execution groups are also integrated with the
[`exec_compatible_with`](/reference/be/common-definitions#common-attributes) and
[`exec_group_compatible_with`](/reference/be/common-definitions#common-attributes)
attributes that exist on every rule and allow the target writer to specify
additional constraints that must be satisfied by the execution platforms
selected for the target's actions.

For example, if the rule `my_test` defines the `link` execution group in
addition to the default and the `test` execution group, then the following
usage of these attributes would run actions in the default execution group on
a platform with a high number of CPUs, the test action on Linux, and the link
action on the default execution platform:

```python
# BUILD
constraint_setting(name = "cpu")
constraint_value(name = "high_cpu", constraint_setting = ":cpu")

platform(
  name = "high_cpu_platform",
  constraint_values = [":high_cpu"],
  exec_properties = {
    "cpu": "256",
  },
)

my_test(
  name = "my_test",
  exec_compatible_with = ["//constraints:high_cpu"],
  exec_group_compatible_with = {
    "test": ["@platforms//os:linux"],
  },
  ...
)
```

### Execution groups for native rules {:#execution-groups-for-native-rules}

The following execution groups are available for actions defined by native
rules:

* `test`: Test runner actions.
* `cpp_link`: C++ linking actions.

### Execution groups and platform execution properties {:#platform-execution-properties}

It is possible to define `exec_properties` for arbitrary execution groups on
platform targets (unlike `exec_properties` set directly on a target, where
properties for unknown execution groups are rejected). Targets then inherit the
execution platform's `exec_properties` that affect the default execution group
and any other relevant execution groups.

For example, suppose running tests on the exec platform requires some resource
to be available, but it isn't required for compiling and linking; this can be
modelled as follows:

```python
constraint_setting(name = "resource")
constraint_value(name = "has_resource", constraint_setting = ":resource")

platform(
    name = "platform_with_resource",
    constraint_values = [":has_resource"],
    exec_properties = {
        "test.resource": "...",
    },
)

cc_test(
    name = "my_test",
    srcs = ["my_test.cc"],
    exec_compatible_with = [":has_resource"],
)
```

`exec_properties` defined directly on targets take precedence over those that
are inherited from the execution platform.


Project: /_project.yaml
Book: /_book.yaml

# Rules

{% include "_buttons.html" %}

A **rule** defines a series of [**actions**](#actions) that Bazel performs on
inputs to produce a set of outputs, which are referenced in
[**providers**](#providers) returned by the rule's
[**implementation function**](#implementation_function). For example, a C++
binary rule might:

1.  Take a set of `.cpp` source files (inputs).
2.  Run `g++` on the source files (action).
3.  Return the `DefaultInfo` provider with the executable output and other files
    to make available at runtime.
4.  Return the `CcInfo` provider with C++-specific information gathered from the
    target and its dependencies.

From Bazel's perspective, `g++` and the standard C++ libraries are also inputs
to this rule. As a rule writer, you must consider not only the user-provided
inputs to a rule, but also all of the tools and libraries required to execute
the actions.

Before creating or modifying any rule, ensure you are familiar with Bazel's
[build phases](/extending/concepts). It is important to understand the three
phases of a build (loading, analysis, and execution). It is also useful to
learn about [macros](/extending/macros) to understand the difference between rules and
macros. To get started, first review the [Rules Tutorial](/rules/rules-tutorial).
Then, use this page as a reference.

A few rules are built into Bazel itself. These *native rules*, such as
`genrule` and `filegroup`, provide some core support.
By defining your own rules, you can add support for languages and tools
that Bazel doesn't support natively.

Bazel provides an extensibility model for writing rules using the
[Starlark](/rules/language) language. These rules are written in `.bzl` files, which
can be loaded directly from `BUILD` files.

When defining your own rule, you get to decide what attributes it supports and
how it generates its outputs.

The rule's `implementation` function defines its exact behavior during the
[analysis phase](/extending/concepts#evaluation-model). This function doesn't run any
external commands. Rather, it registers [actions](#actions) that will be used
later during the execution phase to build the rule's outputs, if they are
needed.

## Rule creation

In a `.bzl` file, use the [rule](/rules/lib/globals/bzl#rule) function to define a new
rule, and store the result in a global variable. The call to `rule` specifies
[attributes](#attributes) and an
[implementation function](#implementation_function):

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        "deps": attr.label_list(),
        ...
    },
)
```

This defines a [rule kind](/query/language#kind) named `example_library`.

The call to `rule` also must specify if the rule creates an
[executable](#executable-rules) output (with `executable = True`), or specifically
a test executable (with `test = True`). If the latter, the rule is a *test rule*,
and the name of the rule must end in `_test`.

## Target instantiation

Rules can be [loaded](/concepts/build-files#load) and called in `BUILD` files:

```python
load('//some/pkg:rules.bzl', 'example_library')

example_library(
    name = "example_target",
    deps = [":another_target"],
    ...
)
```

Each call to a build rule returns no value, but has the side effect of defining
a target. This is called *instantiating* the rule. This specifies a name for the
new target and values for the target's [attributes](#attributes).

Rules can also be called from Starlark functions and loaded in `.bzl` files.
Starlark functions that call rules are called [Starlark macros](/extending/macros).
Starlark macros must ultimately be called from `BUILD` files, and can only be
called during the [loading phase](/extending/concepts#evaluation-model), when `BUILD`
files are evaluated to instantiate targets.

## Attributes

An *attribute* is a rule argument. Attributes can provide specific values to a
target's [implementation](#implementation_function), or they can refer to other
targets, creating a graph of dependencies.

Rule-specific attributes, such as `srcs` or `deps`, are defined by passing a map
from attribute names to schemas (created using the [`attr`](/rules/lib/toplevel/attr)
module) to the `attrs` parameter of `rule`.
[Common attributes](/reference/be/common-definitions#common-attributes), such as
`name` and `visibility`, are implicitly added to all rules. Additional
attributes are implicitly added to
[executable and test rules](#executable-rules) specifically. Attributes which
are implicitly added to a rule can't be included in the dictionary passed to
`attrs`.

### Dependency attributes

Rules that process source code usually define the following attributes to handle
various [types of dependencies](/concepts/dependencies#types_of_dependencies):

*   `srcs` specifies source files processed by a target's actions. Often, the
    attribute schema specifies which file extensions are expected for the sort
    of source file the rule processes. Rules for languages with header files
    generally specify a separate `hdrs` attribute for headers processed by a
    target and its consumers.
*   `deps` specifies code dependencies for a target. The attribute schema should
    specify which [providers](#providers) those dependencies must provide. (For
    example, `cc_library` provides `CcInfo`.)
*   `data` specifies files to be made available at runtime to any executable
    which depends on a target. That should allow arbitrary files to be
    specified.

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = [".example"]),
        "hdrs": attr.label_list(allow_files = [".header"]),
        "deps": attr.label_list(providers = [ExampleInfo]),
        "data": attr.label_list(allow_files = True),
        ...
    },
)
```

These are examples of *dependency attributes*. Any attribute that specifies
an input label (those defined with
[`attr.label_list`](/rules/lib/toplevel/attr#label_list),
[`attr.label`](/rules/lib/toplevel/attr#label), or
[`attr.label_keyed_string_dict`](/rules/lib/toplevel/attr#label_keyed_string_dict))
specifies dependencies of a certain type
between a target and the targets whose labels (or the corresponding
[`Label`](/rules/lib/builtins/Label) objects) are listed in that attribute when the target
is defined. The repository, and possibly the path, for these labels is resolved
relative to the defined target.

```python
example_library(
    name = "my_target",
    deps = [":other_target"],
)

example_library(
    name = "other_target",
    ...
)
```

In this example, `other_target` is a dependency of `my_target`, and therefore
`other_target` is analyzed first. It is an error if there is a cycle in the
dependency graph of targets.

<a name="private-attributes"></a>

### Private attributes and implicit dependencies {:#private_attributes_and_implicit_dependencies}

A dependency attribute with a default value creates an *implicit dependency*. It
is implicit because it's a part of the target graph that the user doesn't
specify it in a `BUILD` file. Implicit dependencies are useful for hard-coding a
relationship between a rule and a *tool* (a build-time dependency, such as a
compiler), since most of the time a user is not interested in specifying what
tool the rule uses. Inside the rule's implementation function, this is treated
the same as other dependencies.

If you want to provide an implicit dependency without allowing the user to
override that value, you can make the attribute *private* by giving it a name
that begins with an underscore (`_`). Private attributes must have default
values. It generally only makes sense to use private attributes for implicit
dependencies.

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        ...
        "_compiler": attr.label(
            default = Label("//tools:example_compiler"),
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
    },
)
```

In this example, every target of type `example_library` has an implicit
dependency on the compiler `//tools:example_compiler`. This allows
`example_library`'s implementation function to generate actions that invoke the
compiler, even though the user did not pass its label as an input. Since
`_compiler` is a private attribute, it follows that `ctx.attr._compiler`
will always point to `//tools:example_compiler` in all targets of this rule
type. Alternatively, you can name the attribute `compiler` without the
underscore and keep the default value. This allows users to substitute a
different compiler if necessary, but it requires no awareness of the compiler's
label.

Implicit dependencies are generally used for tools that reside in the same
repository as the rule implementation. If the tool comes from the
[execution platform](/extending/platforms) or a different repository instead, the
rule should obtain that tool from a [toolchain](/extending/toolchains).

### Output attributes

*Output attributes*, such as [`attr.output`](/rules/lib/toplevel/attr#output) and
[`attr.output_list`](/rules/lib/toplevel/attr#output_list), declare an output file that the
target generates. These differ from dependency attributes in two ways:

*   They define output file targets instead of referring to targets defined
    elsewhere.
*   The output file targets depend on the instantiated rule target, instead of
    the other way around.

Typically, output attributes are only used when a rule needs to create outputs
with user-defined names which can't be based on the target name. If a rule has
one output attribute, it is typically named `out` or `outs`.

Output attributes are the preferred way of creating *predeclared outputs*, which
can be specifically depended upon or
[requested at the command line](#requesting_output_files).

## Implementation function

Every rule requires an `implementation` function. These functions are executed
strictly in the [analysis phase](/extending/concepts#evaluation-model) and transform the
graph of targets generated in the loading phase into a graph of
[actions](#actions) to be performed during the execution phase. As such,
implementation functions can't actually read or write files.

Rule implementation functions are usually private (named with a leading
underscore). Conventionally, they are named the same as their rule, but suffixed
with `_impl`.

Implementation functions take exactly one parameter: a
[rule context](/rules/lib/builtins/ctx), conventionally named `ctx`. They return a list of
[providers](#providers).

### Targets

Dependencies are represented at analysis time as [`Target`](/rules/lib/builtins/Target)
objects. These objects contain the [providers](#providers) generated when the
target's implementation function was executed.

[`ctx.attr`](/rules/lib/builtins/ctx#attr) has fields corresponding to the names of each
dependency attribute, containing `Target` objects representing each direct
dependency using that attribute. For `label_list` attributes, this is a list of
`Targets`. For `label` attributes, this is a single `Target` or `None`.

A list of provider objects are returned by a target's implementation function:

```python
return [ExampleInfo(headers = depset(...))]
```

Those can be accessed using index notation (`[]`), with the type of provider as
a key. These can be [custom providers](#custom_providers) defined in Starlark or
[providers for native rules](/rules/lib/providers) available as Starlark
global variables.

For example, if a rule takes header files using a `hdrs` attribute and provides
them to the compilation actions of the target and its consumers, it could
collect them like so:

```python
def _example_library_impl(ctx):
    ...
    transitive_headers = [hdr[ExampleInfo].headers for hdr in ctx.attr.hdrs]
```

There's a legacy struct style, which is strongly discouraged and rules should be
[migrated away from it](#migrating_from_legacy_providers).

### Files

Files are represented by [`File`](/rules/lib/builtins/File) objects. Since Bazel doesn't
perform file I/O during the analysis phase, these objects can't be used to
directly read or write file content. Rather, they are passed to action-emitting
functions (see [`ctx.actions`](/rules/lib/builtins/actions)) to construct pieces of the
action graph.

A `File` can either be a source file or a generated file. Each generated file
must be an output of exactly one action. Source files can't be the output of
any action.

For each dependency attribute, the corresponding field of
[`ctx.files`](/rules/lib/builtins/ctx#files) contains a list of the default outputs of all
dependencies using that attribute:

```python
def _example_library_impl(ctx):
    ...
    headers = depset(ctx.files.hdrs, transitive = transitive_headers)
    srcs = ctx.files.srcs
    ...
```

[`ctx.file`](/rules/lib/builtins/ctx#file) contains a single `File` or `None` for
dependency attributes whose specs set `allow_single_file = True`.
[`ctx.executable`](/rules/lib/builtins/ctx#executable) behaves the same as `ctx.file`, but only
contains fields for dependency attributes whose specs set `executable = True`.

### Declaring outputs

During the analysis phase, a rule's implementation function can create outputs.
Since all labels have to be known during the loading phase, these additional
outputs have no labels. `File` objects for outputs can be created using
[`ctx.actions.declare_file`](/rules/lib/builtins/actions#declare_file) and
[`ctx.actions.declare_directory`](/rules/lib/builtins/actions#declare_directory).
Often, the names of outputs are based on the target's name,
[`ctx.label.name`](/rules/lib/builtins/ctx#label):

```python
def _example_library_impl(ctx):
  ...
  output_file = ctx.actions.declare_file(ctx.label.name + ".output")
  ...
```

For *predeclared outputs*, like those created for
[output attributes](#output_attributes), `File` objects instead can be retrieved
from the corresponding fields of [`ctx.outputs`](/rules/lib/builtins/ctx#outputs).

### Actions

An action describes how to generate a set of outputs from a set of inputs, for
example "run gcc on hello.c and get hello.o". When an action is created, Bazel
doesn't run the command immediately. It registers it in a graph of dependencies,
because an action can depend on the output of another action. For example, in C,
the linker must be called after the compiler.

General-purpose functions that create actions are defined in
[`ctx.actions`](/rules/lib/builtins/actions):

*   [`ctx.actions.run`](/rules/lib/builtins/actions#run), to run an executable.
*   [`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell), to run a shell
    command.
*   [`ctx.actions.write`](/rules/lib/builtins/actions#write), to write a string to a file.
*   [`ctx.actions.expand_template`](/rules/lib/builtins/actions#expand_template), to
    generate a file from a template.

[`ctx.actions.args`](/rules/lib/builtins/actions#args) can be used to efficiently
accumulate the arguments for actions. It avoids flattening depsets until
execution time:

```python
def _example_library_impl(ctx):
    ...

    transitive_headers = [dep[ExampleInfo].headers for dep in ctx.attr.deps]
    headers = depset(ctx.files.hdrs, transitive = transitive_headers)
    srcs = ctx.files.srcs
    inputs = depset(srcs, transitive = [headers])
    output_file = ctx.actions.declare_file(ctx.label.name + ".output")

    args = ctx.actions.args()
    args.add_joined("-h", headers, join_with = ",")
    args.add_joined("-s", srcs, join_with = ",")
    args.add("-o", output_file)

    ctx.actions.run(
        mnemonic = "ExampleCompile",
        executable = ctx.executable._compiler,
        arguments = [args],
        inputs = inputs,
        outputs = [output_file],
    )
    ...
```

Actions take a list or depset of input files and generate a (non-empty) list of
output files. The set of input and output files must be known during the
[analysis phase](/extending/concepts#evaluation-model). It might depend on the value of
attributes, including providers from dependencies, but it can't depend on the
result of the execution. For example, if your action runs the unzip command, you
must specify which files you expect to be inflated (before running unzip).
Actions which create a variable number of files internally can wrap those in a
single file (such as a zip, tar, or other archive format).

Actions must list all of their inputs. Listing inputs that are not used is
permitted, but inefficient.

Actions must create all of their outputs. They may write other files, but
anything not in outputs won't be available to consumers. All declared outputs
must be written by some action.

Actions are comparable to pure functions: They should depend only on the
provided inputs, and avoid accessing computer information, username, clock,
network, or I/O devices (except for reading inputs and writing outputs). This is
important because the output will be cached and reused.

Dependencies are resolved by Bazel, which decides which actions to
execute. It is an error if there is a cycle in the dependency graph. Creating
an action doesn't guarantee that it will be executed, that depends on whether
its outputs are needed for the build.

### Providers

Providers are pieces of information that a rule exposes to other rules that
depend on it. This data can include output files, libraries, parameters to pass
on a tool's command line, or anything else a target's consumers should know
about.

Since a rule's implementation function can only read providers from the
instantiated target's immediate dependencies, rules need to forward any
information from a target's dependencies that needs to be known by a target's
consumers, generally by accumulating that into a [`depset`](/rules/lib/builtins/depset).

A target's providers are specified by a list of provider objects returned by
the implementation function.

Old implementation functions can also be written in a legacy style where the
implementation function returns a [`struct`](/rules/lib/builtins/struct) instead of list of
provider objects. This style is strongly discouraged and rules should be
[migrated away from it](#migrating_from_legacy_providers).

#### Default outputs

A target's *default outputs* are the outputs that are requested by default when
the target is requested for build at the command line. For example, a
`java_library` target `//pkg:foo` has `foo.jar` as a default output, so that
will be built by the command `bazel build //pkg:foo`.

Default outputs are specified by the `files` parameter of
[`DefaultInfo`](/rules/lib/providers/DefaultInfo):

```python
def _example_library_impl(ctx):
    ...
    return [
        DefaultInfo(files = depset([output_file]), ...),
        ...
    ]
```

If `DefaultInfo` is not returned by a rule implementation or the `files`
parameter is not specified, `DefaultInfo.files` defaults to all
*predeclared outputs* (generally, those created by [output
attributes](#output_attributes)).

Rules that perform actions should provide default outputs, even if those outputs
are not expected to be directly used. Actions that are not in the graph of the
requested outputs are pruned. If an output is only used by a target's consumers,
those actions won't be performed when the target is built in isolation. This
makes debugging more difficult because rebuilding just the failing target won't
reproduce the failure.

#### Runfiles

Runfiles are a set of files used by a target at runtime (as opposed to build
time). During the [execution phase](/extending/concepts#evaluation-model), Bazel creates
a directory tree containing symlinks pointing to the runfiles. This stages the
environment for the binary so it can access the runfiles during runtime.

Runfiles can be added manually during rule creation.
[`runfiles`](/rules/lib/builtins/runfiles) objects can be created by the `runfiles` method
on the rule context, [`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles) and passed to the
`runfiles` parameter on `DefaultInfo`. The executable output of
[executable rules](#executable-rules) is implicitly added to the runfiles.

Some rules specify attributes, generally named
[`data`](/reference/be/common-definitions#common.data), whose outputs are added to
a targets' runfiles. Runfiles should also be merged in from `data`, as well as
from any attributes which might provide code for eventual execution, generally
`srcs` (which might contain `filegroup` targets with associated `data`) and
`deps`.

```python
def _example_library_impl(ctx):
    ...
    runfiles = ctx.runfiles(files = ctx.files.data)
    transitive_runfiles = []
    for runfiles_attr in (
        ctx.attr.srcs,
        ctx.attr.hdrs,
        ctx.attr.deps,
        ctx.attr.data,
    ):
        for target in runfiles_attr:
            transitive_runfiles.append(target[DefaultInfo].default_runfiles)
    runfiles = runfiles.merge_all(transitive_runfiles)
    return [
        DefaultInfo(..., runfiles = runfiles),
        ...
    ]
```

#### Custom providers

Providers can be defined using the [`provider`](/rules/lib/globals/bzl#provider)
function to convey rule-specific information:

```python
ExampleInfo = provider(
    "Info needed to compile/link Example code.",
    fields = {
        "headers": "depset of header Files from transitive dependencies.",
        "files_to_link": "depset of Files from compilation.",
    },
)
```

Rule implementation functions can then construct and return provider instances:

```python
def _example_library_impl(ctx):
  ...
  return [
      ...
      ExampleInfo(
          headers = headers,
          files_to_link = depset(
              [output_file],
              transitive = [
                  dep[ExampleInfo].files_to_link for dep in ctx.attr.deps
              ],
          ),
      )
  ]
```

##### Custom initialization of providers

It's possible to guard the instantiation of a provider with custom
preprocessing and validation logic. This can be used to ensure that all
provider instances satisfy certain invariants, or to give users a cleaner API for
obtaining an instance.

This is done by passing an `init` callback to the
[`provider`](/rules/lib/globals/bzl.html#provider) function. If this callback is given, the
return type of `provider()` changes to be a tuple of two values: the provider
symbol that is the ordinary return value when `init` is not used, and a "raw
constructor".

In this case, when the provider symbol is called, instead of directly returning
a new instance, it will forward the arguments along to the `init` callback. The
callback's return value must be a dict mapping field names (strings) to values;
this is used to initialize the fields of the new instance. Note that the
callback may have any signature, and if the arguments don't match the signature
an error is reported as if the callback were invoked directly.

The raw constructor, by contrast, will bypass the `init` callback.

The following example uses `init` to preprocess and validate its arguments:

```python
# //pkg:exampleinfo.bzl

_core_headers = [...]  # private constant representing standard library files

# Keyword-only arguments are preferred.
def _exampleinfo_init(*, files_to_link, headers = None, allow_empty_files_to_link = False):
    if not files_to_link and not allow_empty_files_to_link:
        fail("files_to_link may not be empty")
    all_headers = depset(_core_headers, transitive = headers)
    return {"files_to_link": files_to_link, "headers": all_headers}

ExampleInfo, _new_exampleinfo = provider(
    fields = ["files_to_link", "headers"],
    init = _exampleinfo_init,
)
```

A rule implementation may then instantiate the provider as follows:

```python
ExampleInfo(
    files_to_link = my_files_to_link,  # may not be empty
    headers = my_headers,  # will automatically include the core headers
)
```

The raw constructor can be used to define alternative public factory functions
that don't go through the `init` logic. For example, exampleinfo.bzl
could define:

```python
def make_barebones_exampleinfo(headers):
    """Returns an ExampleInfo with no files_to_link and only the specified headers."""
    return _new_exampleinfo(files_to_link = depset(), headers = all_headers)
```

Typically, the raw constructor is bound to a variable whose name begins with an
underscore (`_new_exampleinfo` above), so that user code can't load it and
generate arbitrary provider instances.

Another use for `init` is to prevent the user from calling the provider
symbol altogether, and force them to use a factory function instead:

```python
def _exampleinfo_init_banned(*args, **kwargs):
    fail("Do not call ExampleInfo(). Use make_exampleinfo() instead.")

ExampleInfo, _new_exampleinfo = provider(
    ...
    init = _exampleinfo_init_banned)

def make_exampleinfo(...):
    ...
    return _new_exampleinfo(...)
```

<a name="executable-rules"></a>

## Executable rules and test rules

Executable rules define targets that can be invoked by a `bazel run` command.
Test rules are a special kind of executable rule whose targets can also be
invoked by a `bazel test` command. Executable and test rules are created by
setting the respective [`executable`](/rules/lib/globals/bzl#rule.executable) or
[`test`](/rules/lib/globals/bzl#rule.test) argument to `True` in the call to `rule`:

```python
example_binary = rule(
   implementation = _example_binary_impl,
   executable = True,
   ...
)

example_test = rule(
   implementation = _example_binary_impl,
   test = True,
   ...
)
```

Test rules must have names that end in `_test`. (Test *target* names also often
end in `_test` by convention, but this is not required.) Non-test rules must not
have this suffix.

Both kinds of rules must produce an executable output file (which may or may not
be predeclared) that will be invoked by the `run` or `test` commands. To tell
Bazel which of a rule's outputs to use as this executable, pass it as the
`executable` argument of a returned [`DefaultInfo`](/rules/lib/providers/DefaultInfo)
provider. That `executable` is added to the default outputs of the rule (so you
don't need to pass that to both `executable` and `files`). It's also implicitly
added to the [runfiles](#runfiles):

```python
def _example_binary_impl(ctx):
    executable = ctx.actions.declare_file(ctx.label.name)
    ...
    return [
        DefaultInfo(executable = executable, ...),
        ...
    ]
```

The action that generates this file must set the executable bit on the file. For
a [`ctx.actions.run`](/rules/lib/builtins/actions#run) or
[`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell) action this should be done
by the underlying tool that is invoked by the action. For a
[`ctx.actions.write`](/rules/lib/builtins/actions#write) action, pass `is_executable = True`.

As [legacy behavior](#deprecated_predeclared_outputs), executable rules have a
special `ctx.outputs.executable` predeclared output. This file serves as the
default executable if you don't specify one using `DefaultInfo`; it must not be
used otherwise. This output mechanism is deprecated because it doesn't support
customizing the executable file's name at analysis time.

See examples of an
[executable rule](https://github.com/bazelbuild/examples/blob/main/rules/executable/fortune.bzl){: .external}
and a
[test rule](https://github.com/bazelbuild/examples/blob/main/rules/test_rule/line_length.bzl){: .external}.

[Executable rules](/reference/be/common-definitions#common-attributes-binaries) and
[test rules](/reference/be/common-definitions#common-attributes-tests) have additional
attributes implicitly defined, in addition to those added for
[all rules](/reference/be/common-definitions#common-attributes). The defaults of
implicitly-added attributes can't be changed, though this can be worked around
by wrapping a private rule in a [Starlark macro](/extending/macros) which alters the
default:

```python
def example_test(size = "small", **kwargs):
  _example_test(size = size, **kwargs)

_example_test = rule(
 ...
)
```

### Runfiles location

When an executable target is run with `bazel run` (or `test`), the root of the
runfiles directory is adjacent to the executable. The paths relate as follows:

```python
# Given launcher_path and runfile_file:
runfiles_root = launcher_path.path + ".runfiles"
workspace_name = ctx.workspace_name
runfile_path = runfile_file.short_path
execution_root_relative_path = "%s/%s/%s" % (
    runfiles_root, workspace_name, runfile_path)
```

The path to a `File` under the runfiles directory corresponds to
[`File.short_path`](/rules/lib/builtins/File#short_path).

The binary executed directly by `bazel` is adjacent to the root of the
`runfiles` directory. However, binaries called *from* the runfiles can't make
the same assumption. To mitigate this, each binary should provide a way to
accept its runfiles root as a parameter using an environment, or command line
argument or flag. This allows binaries to pass the correct canonical runfiles root
to the binaries it calls. If that's not set, a binary can guess that it was the
first binary called and look for an adjacent runfiles directory.

## Advanced topics

### Requesting output files

A single target can have several output files. When a `bazel build` command is
run, some of the outputs of the targets given to the command are considered to
be *requested*. Bazel only builds these requested files and the files that they
directly or indirectly depend on. (In terms of the action graph, Bazel only
executes the actions that are reachable as transitive dependencies of the
requested files.)

In addition to [default outputs](#default_outputs), any *predeclared output* can
be explicitly requested on the command line. Rules can specify predeclared
outputs using [output attributes](#output_attributes). In that case, the user
explicitly chooses labels for outputs when they instantiate the rule. To obtain
[`File`](/rules/lib/builtins/File) objects for output attributes, use the corresponding
attribute of [`ctx.outputs`](/rules/lib/builtins/ctx#outputs). Rules can
[implicitly define predeclared outputs](#deprecated_predeclared_outputs) based
on the target name as well, but this feature is deprecated.

In addition to default outputs, there are *output groups*, which are collections
of output files that may be requested together. These can be requested with
[`--output_groups`](/reference/command-line-reference#flag--output_groups). For
example, if a target `//pkg:mytarget` is of a rule type that has a `debug_files`
output group, these files can be built by running `bazel build //pkg:mytarget
--output_groups=debug_files`. Since non-predeclared outputs don't have labels,
they can only be requested by appearing in the default outputs or an output
group.

Output groups can be specified with the
[`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo) provider. Note that unlike many
built-in providers, `OutputGroupInfo` can take parameters with arbitrary names
to define output groups with that name:

```python
def _example_library_impl(ctx):
    ...
    debug_file = ctx.actions.declare_file(name + ".pdb")
    ...
    return [
        DefaultInfo(files = depset([output_file]), ...),
        OutputGroupInfo(
            debug_files = depset([debug_file]),
            all_files = depset([output_file, debug_file]),
        ),
        ...
    ]
```

Also unlike most providers, `OutputGroupInfo` can be returned by both an
[aspect](/extending/aspects) and the rule target to which that aspect is applied, as
long as they don't define the same output groups. In that case, the resulting
providers are merged.

Note that `OutputGroupInfo` generally shouldn't be used to convey specific sorts
of files from a target to the actions of its consumers. Define
[rule-specific providers](#custom_providers) for that instead.

### Configurations

Imagine that you want to build a C++ binary for a different architecture. The
build can be complex and involve multiple steps. Some of the intermediate
binaries, like compilers and code generators, have to run on
[the execution platform](/extending/platforms#overview) (which could be your host,
or a remote executor). Some binaries like the final output must be built for the
target architecture.

For this reason, Bazel has a concept of "configurations" and transitions. The
topmost targets (the ones requested on the command line) are built-in the
"target" configuration, while tools that should run on the execution platform
are built-in an "exec" configuration. Rules may generate different actions based
on the configuration, for instance to change the cpu architecture that is passed
to the compiler. In some cases, the same library may be needed for different
configurations. If this happens, it will be analyzed and potentially built
multiple times.

By default, Bazel builds a target's dependencies in the same configuration as
the target itself, in other words without transitions. When a dependency is a
tool that's needed to help build the target, the corresponding attribute should
specify a transition to an exec configuration. This causes the tool and all its
dependencies to build for the execution platform.

For each dependency attribute, you can use `cfg` to decide if dependencies
should build in the same configuration or transition to an exec configuration.
If a dependency attribute has the flag `executable = True`, `cfg` must be set
explicitly. This is to guard against accidentally building a tool for the wrong
configuration.
[See example](https://github.com/bazelbuild/examples/blob/main/rules/actions_run/execute.bzl){: .external}

In general, sources, dependent libraries, and executables that will be needed at
runtime can use the same configuration.

Tools that are executed as part of the build (such as compilers or code generators)
should be built for an exec configuration. In this case, specify `cfg = "exec"` in
the attribute.

Otherwise, executables that are used at runtime (such as as part of a test) should
be built for the target configuration. In this case, specify `cfg = "target"` in
the attribute.

`cfg = "target"` doesn't actually do anything: it's purely a convenience value to
help rule designers be explicit about their intentions. When `executable = False`,
which means `cfg` is optional, only set this when it truly helps readability.

You can also use `cfg = my_transition` to use
[user-defined transitions](/extending/config#user-defined-transitions), which allow
rule authors a great deal of flexibility in changing configurations, with the
drawback of
[making the build graph larger and less comprehensible](/extending/config#memory-and-performance-considerations).

**Note**: Historically, Bazel didn't have the concept of execution platforms,
and instead all build actions were considered to run on the host machine. Bazel
versions before 6.0 created a distinct "host" configuration to represent this.
If you see references to "host" in code or old documentation, that's what this
refers to. We recommend using Bazel 6.0 or newer to avoid this extra conceptual
overhead.

<a name="fragments"></a>

### Configuration fragments

Rules may access
[configuration fragments](/rules/lib/fragments) such as
`cpp` and `java`. However, all required fragments must be declared in
order to avoid access errors:

```python
def _impl(ctx):
    # Using ctx.fragments.cpp leads to an error since it was not declared.
    x = ctx.fragments.java
    ...

my_rule = rule(
    implementation = _impl,
    fragments = ["java"],      # Required fragments of the target configuration
    ...
)
```

### Runfiles symlinks

Normally, the relative path of a file in the runfiles tree is the same as the
relative path of that file in the source tree or generated output tree. If these
need to be different for some reason, you can specify the `root_symlinks` or
`symlinks` arguments. The `root_symlinks` is a dictionary mapping paths to
files, where the paths are relative to the root of the runfiles directory. The
`symlinks` dictionary is the same, but paths are implicitly prefixed with the
name of the main workspace (*not* the name of the repository containing the
current target).

```python
    ...
    runfiles = ctx.runfiles(
        root_symlinks = {"some/path/here.foo": ctx.file.some_data_file2}
        symlinks = {"some/path/here.bar": ctx.file.some_data_file3}
    )
    # Creates something like:
    # sometarget.runfiles/
    #     some/
    #         path/
    #             here.foo -> some_data_file2
    #     <workspace_name>/
    #         some/
    #             path/
    #                 here.bar -> some_data_file3
```

If `symlinks` or `root_symlinks` is used, be careful not to map two different
files to the same path in the runfiles tree. This will cause the build to fail
with an error describing the conflict. To fix, you will need to modify your
`ctx.runfiles` arguments to remove the collision. This checking will be done for
any targets using your rule, as well as targets of any kind that depend on those
targets. This is especially risky if your tool is likely to be used transitively
by another tool; symlink names must be unique across the runfiles of a tool and
all of its dependencies.

### Code coverage

When the [`coverage`](/reference/command-line-reference#coverage) command is run,
the build may need to add coverage instrumentation for certain targets. The
build also gathers the list of source files that are instrumented. The subset of
targets that are considered is controlled by the flag
[`--instrumentation_filter`](/reference/command-line-reference#flag--instrumentation_filter).
Test targets are excluded, unless
[`--instrument_test_targets`](/reference/command-line-reference#flag--instrument_test_targets)
is specified.

If a rule implementation adds coverage instrumentation at build time, it needs
to account for that in its implementation function.
[ctx.coverage_instrumented](/rules/lib/builtins/ctx#coverage_instrumented) returns
`True` in coverage mode if a target's sources should be instrumented:

```python
# Are this rule's sources instrumented?
if ctx.coverage_instrumented():
  # Do something to turn on coverage for this compile action
```

Logic that always needs to be on in coverage mode (whether a target's sources
specifically are instrumented or not) can be conditioned on
[ctx.configuration.coverage_enabled](/rules/lib/builtins/configuration#coverage_enabled).

If the rule directly includes sources from its dependencies before compilation
(such as header files), it may also need to turn on compile-time instrumentation if
the dependencies' sources should be instrumented:

```python
# Are this rule's sources or any of the sources for its direct dependencies
# in deps instrumented?
if (ctx.configuration.coverage_enabled and
    (ctx.coverage_instrumented() or
     any([ctx.coverage_instrumented(dep) for dep in ctx.attr.deps]))):
    # Do something to turn on coverage for this compile action
```

Rules also should provide information about which attributes are relevant for
coverage with the `InstrumentedFilesInfo` provider, constructed using
[`coverage_common.instrumented_files_info`](/rules/lib/toplevel/coverage_common#instrumented_files_info).
The `dependency_attributes` parameter of `instrumented_files_info` should list
all runtime dependency attributes, including code dependencies like `deps` and
data dependencies like `data`. The `source_attributes` parameter should list the
rule's source files attributes if coverage instrumentation might be added:

```python
def _example_library_impl(ctx):
    ...
    return [
        ...
        coverage_common.instrumented_files_info(
            ctx,
            dependency_attributes = ["deps", "data"],
            # Omitted if coverage is not supported for this rule:
            source_attributes = ["srcs", "hdrs"],
        )
        ...
    ]
```

If `InstrumentedFilesInfo` is not returned, a default one is created with each
non-tool [dependency attribute](#dependency_attributes) that doesn't set
[`cfg`](#configuration) to `"exec"` in the attribute schema. in
`dependency_attributes`. (This isn't ideal behavior, since it puts attributes
like `srcs` in `dependency_attributes` instead of `source_attributes`, but it
avoids the need for explicit coverage configuration for all rules in the
dependency chain.)

### Validation Actions

Sometimes you need to validate something about the build, and the
information required to do that validation is available only in artifacts
(source files or generated files). Because this information is in artifacts,
rules can't do this validation at analysis time because rules can't read
files. Instead, actions must do this validation at execution time. When
validation fails, the action will fail, and hence so will the build.

Examples of validations that might be run are static analysis, linting,
dependency and consistency checks, and style checks.

Validation actions can also help to improve build performance by moving parts
of actions that are not required for building artifacts into separate actions.
For example, if a single action that does compilation and linting can be
separated into a compilation action and a linting action, then the linting
action can be run as a validation action and run in parallel with other actions.

These "validation actions" often don't produce anything that is used elsewhere
in the build, since they only need to assert things about their inputs. This
presents a problem though: If a validation action doesn't produce anything that
is used elsewhere in the build, how does a rule get the action to run?
Historically, the approach was to have the validation action output an empty
file, and artificially add that output to the inputs of some other important
action in the build:

<img src="/rules/validation_action_historical.svg" width="35%" />

This works, because Bazel will always run the validation action when the compile
action is run, but this has significant drawbacks:

1. The validation action is in the critical path of the build. Because Bazel
thinks the empty output is required to run the compile action, it will run the
validation action first, even though the compile action will ignore the input.
This reduces parallelism and slows down builds.

2. If other actions in the build might run instead of the
compile action, then the empty outputs of validation actions need to be added to
those actions as well (`java_library`'s source jar output, for example). This is
also a problem if new actions that might run instead of the compile action are
added later, and the empty validation output is accidentally left off.

The solution to these problems is to use the Validations Output Group.

#### Validations Output Group

The Validations Output Group is an output group designed to hold the otherwise
unused outputs of validation actions, so that they don't need to be artificially
added to the inputs of other actions.

This group is special in that its outputs are always requested, regardless of
the value of the `--output_groups` flag, and regardless of how the target is
depended upon (for example, on the command line, as a dependency, or through
implicit outputs of the target). Note that normal caching and incrementality
still apply: if the inputs to the validation action have not changed and the
validation action previously succeeded, then the validation action won't be
run.

<img src="/rules/validation_action.svg" width="35%" />

Using this output group still requires that validation actions output some file,
even an empty one. This might require wrapping some tools that normally don't
create outputs so that a file is created.

A target's validation actions are not run in three cases:

*    When the target is depended upon as a tool
*    When the target is depended upon as an implicit dependency (for example, an
     attribute that starts with "_")
*    When the target is built in the exec configuration.

It is assumed that these targets have their own
separate builds and tests that would uncover any validation failures.

#### Using the Validations Output Group

The Validations Output Group is named `_validation` and is used like any other
output group:

```python
def _rule_with_validation_impl(ctx):

  ctx.actions.write(ctx.outputs.main, "main output\n")
  ctx.actions.write(ctx.outputs.implicit, "implicit output\n")

  validation_output = ctx.actions.declare_file(ctx.attr.name + ".validation")
  ctx.actions.run(
    outputs = [validation_output],
    executable = ctx.executable._validation_tool,
    arguments = [validation_output.path],
  )

  return [
    DefaultInfo(files = depset([ctx.outputs.main])),
    OutputGroupInfo(_validation = depset([validation_output])),
  ]


rule_with_validation = rule(
  implementation = _rule_with_validation_impl,
  outputs = {
    "main": "%{name}.main",
    "implicit": "%{name}.implicit",
  },
  attrs = {
    "_validation_tool": attr.label(
        default = Label("//validation_actions:validation_tool"),
        executable = True,
        cfg = "exec"
    ),
  }
)
```

Notice that the validation output file is not added to the `DefaultInfo` or the
inputs to any other action. The validation action for a target of this rule kind
will still run if the target is depended upon by label, or any of the target's
implicit outputs are directly or indirectly depended upon.

It is usually important that the outputs of validation actions only go into the
validation output group, and are not added to the inputs of other actions, as
this could defeat parallelism gains. Note however that Bazel doesn't
have any special checking to enforce this. Therefore, you should test
that validation action outputs are not added to the inputs of any actions in the
tests for Starlark rules. For example:

```python
load("@bazel_skylib//lib:unittest.bzl", "analysistest")

def _validation_outputs_test_impl(ctx):
  env = analysistest.begin(ctx)

  actions = analysistest.target_actions(env)
  target = analysistest.target_under_test(env)
  validation_outputs = target.output_groups._validation.to_list()
  for action in actions:
    for validation_output in validation_outputs:
      if validation_output in action.inputs.to_list():
        analysistest.fail(env,
            "%s is a validation action output, but is an input to action %s" % (
                validation_output, action))

  return analysistest.end(env)

validation_outputs_test = analysistest.make(_validation_outputs_test_impl)
```

#### Validation Actions Flag

Running validation actions is controlled by the `--run_validations` command line
flag, which defaults to true.

## Deprecated features

### Deprecated predeclared outputs

There are two **deprecated** ways of using predeclared outputs:

*   The [`outputs`](/rules/lib/globals/bzl#rule.outputs) parameter of `rule` specifies
    a mapping between output attribute names and string templates for generating
    predeclared output labels. Prefer using non-predeclared outputs and
    explicitly adding outputs to `DefaultInfo.files`. Use the rule target's
    label as input for rules which consume the output instead of a predeclared
    output's label.

*   For [executable rules](#executable-rules), `ctx.outputs.executable` refers
    to a predeclared executable output with the same name as the rule target.
    Prefer declaring the output explicitly, for example with
    `ctx.actions.declare_file(ctx.label.name)`, and ensure that the command that
    generates the executable sets its permissions to allow execution. Explicitly
    pass the executable output to the `executable` parameter of `DefaultInfo`.

### Runfiles features to avoid

[`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles) and the [`runfiles`](/rules/lib/builtins/runfiles)
type have a complex set of features, many of which are kept for legacy reasons.
The following recommendations help reduce complexity:

*   **Avoid** use of the `collect_data` and `collect_default` modes of
    [`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles). These modes implicitly collect
    runfiles across certain hardcoded dependency edges in confusing ways.
    Instead, add files using the `files` or `transitive_files` parameters of
    `ctx.runfiles`, or by merging in runfiles from dependencies with
    `runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)`.

*   **Avoid** use of the `data_runfiles` and `default_runfiles` of the
    `DefaultInfo` constructor. Specify `DefaultInfo(runfiles = ...)` instead.
    The distinction between "default" and "data" runfiles is maintained for
    legacy reasons. For example, some rules put their default outputs in
    `data_runfiles`, but not `default_runfiles`. Instead of using
    `data_runfiles`, rules should *both* include default outputs and merge in
    `default_runfiles` from attributes which provide runfiles (often
    [`data`](/reference/be/common-definitions#common-attributes.data)).

*   When retrieving `runfiles` from `DefaultInfo` (generally only for merging
    runfiles between the current rule and its dependencies), use
    `DefaultInfo.default_runfiles`, **not** `DefaultInfo.data_runfiles`.

### Migrating from legacy providers

Historically, Bazel providers were simple fields on the `Target` object. They
were accessed using the dot operator, and they were created by putting the field
in a [`struct`](/rules/lib/builtins/struct) returned by the rule's
implementation function instead of a list of provider objects:

```python
return struct(example_info = struct(headers = depset(...)))
```

Such providers can be retrieved from the corresponding field of the `Target` object:

```python
transitive_headers = [hdr.example_info.headers for hdr in ctx.attr.hdrs]
```

*This style is deprecated and should not be used in new code;* see following for
information that may help you migrate. The new provider mechanism avoids name
clashes. It also supports data hiding, by requiring any code accessing a
provider instance to retrieve it using the provider symbol.

For the moment, legacy providers are still supported. A rule can return both
legacy and modern providers as follows:

```python
def _old_rule_impl(ctx):
  ...
  legacy_data = struct(x = "foo", ...)
  modern_data = MyInfo(y = "bar", ...)
  # When any legacy providers are returned, the top-level returned value is a
  # struct.
  return struct(
      # One key = value entry for each legacy provider.
      legacy_info = legacy_data,
      ...
      # Additional modern providers:
      providers = [modern_data, ...])
```

If `dep` is the resulting `Target` object for an instance of this rule, the
providers and their contents can be retrieved as `dep.legacy_info.x` and
`dep[MyInfo].y`.

In addition to `providers`, the returned struct can also take several other
fields that have special meaning (and thus don't create a corresponding legacy
provider):

*   The fields `files`, `runfiles`, `data_runfiles`, `default_runfiles`, and
    `executable` correspond to the same-named fields of
    [`DefaultInfo`](/rules/lib/providers/DefaultInfo). It is not allowed to specify any of
    these fields while also returning a `DefaultInfo` provider.

*   The field `output_groups` takes a struct value and corresponds to an
    [`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo).

In [`provides`](/rules/lib/globals/bzl#rule.provides) declarations of rules, and in
[`providers`](/rules/lib/toplevel/attr#label_list.providers) declarations of dependency
attributes, legacy providers are passed in as strings and modern providers are
passed in by their `Info` symbol. Be sure to change from strings to symbols
when migrating. For complex or large rule sets where it is difficult to update
all rules atomically, you may have an easier time if you follow this sequence of
steps:

1.  Modify the rules that produce the legacy provider to produce both the legacy
    and modern providers, using the preceding syntax. For rules that declare they
    return the legacy provider, update that declaration to include both the
    legacy and modern providers.

2.  Modify the rules that consume the legacy provider to instead consume the
    modern provider. If any attribute declarations require the legacy provider,
    also update them to instead require the modern provider. Optionally, you can
    interleave this work with step 1 by having consumers accept or require either
    provider: Test for the presence of the legacy provider using
    `hasattr(target, 'foo')`, or the new provider using `FooInfo in target`.

3.  Fully remove the legacy provider from all rules.


Project: /_project.yaml
Book: /_book.yaml

# Toolchains

{% include "_buttons.html" %}

This page describes the toolchain framework, which is a way for rule authors to
decouple their rule logic from platform-based selection of tools. It is
recommended to read the [rules](/extending/rules) and [platforms](/extending/platforms)
pages before continuing. This page covers why toolchains are needed, how to
define and use them, and how Bazel selects an appropriate toolchain based on
platform constraints.

## Motivation {:#motivation}

Let's first look at the problem toolchains are designed to solve. Suppose you
are writing rules to support the "bar" programming language. Your `bar_binary`
rule would compile `*.bar` files using the `barc` compiler, a tool that itself
is built as another target in your workspace. Since users who write `bar_binary`
targets shouldn't have to specify a dependency on the compiler, you make it an
implicit dependency by adding it to the rule definition as a private attribute.

```python
bar_binary = rule(
    implementation = _bar_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        ...
        "_compiler": attr.label(
            default = "//bar_tools:barc_linux",  # the compiler running on linux
            providers = [BarcInfo],
        ),
    },
)
```

`//bar_tools:barc_linux` is now a dependency of every `bar_binary` target, so
it'll be built before any `bar_binary` target. It can be accessed by the rule's
implementation function just like any other attribute:

```python
BarcInfo = provider(
    doc = "Information about how to invoke the barc compiler.",
    # In the real world, compiler_path and system_lib might hold File objects,
    # but for simplicity they are strings for this example. arch_flags is a list
    # of strings.
    fields = ["compiler_path", "system_lib", "arch_flags"],
)

def _bar_binary_impl(ctx):
    ...
    info = ctx.attr._compiler[BarcInfo]
    command = "%s -l %s %s" % (
        info.compiler_path,
        info.system_lib,
        " ".join(info.arch_flags),
    )
    ...
```

The issue here is that the compiler's label is hardcoded into `bar_binary`, yet
different targets may need different compilers depending on what platform they
are being built for and what platform they are being built on -- called the
*target platform* and *execution platform*, respectively. Furthermore, the rule
author does not necessarily even know all the available tools and platforms, so
it is not feasible to hardcode them in the rule's definition.

A less-than-ideal solution would be to shift the burden onto users, by making
the `_compiler` attribute non-private. Then individual targets could be
hardcoded to build for one platform or another.

```python
bar_binary(
    name = "myprog_on_linux",
    srcs = ["mysrc.bar"],
    compiler = "//bar_tools:barc_linux",
)

bar_binary(
    name = "myprog_on_windows",
    srcs = ["mysrc.bar"],
    compiler = "//bar_tools:barc_windows",
)
```

You can improve on this solution by using `select` to choose the `compiler`
[based on the platform](/docs/configurable-attributes):

```python
config_setting(
    name = "on_linux",
    constraint_values = [
        "@platforms//os:linux",
    ],
)

config_setting(
    name = "on_windows",
    constraint_values = [
        "@platforms//os:windows",
    ],
)

bar_binary(
    name = "myprog",
    srcs = ["mysrc.bar"],
    compiler = select({
        ":on_linux": "//bar_tools:barc_linux",
        ":on_windows": "//bar_tools:barc_windows",
    }),
)
```

But this is tedious and a bit much to ask of every single `bar_binary` user.
If this style is not used consistently throughout the workspace, it leads to
builds that work fine on a single platform but fail when extended to
multi-platform scenarios. It also does not address the problem of adding support
for new platforms and compilers without modifying existing rules or targets.

The toolchain framework solves this problem by adding an extra level of
indirection. Essentially, you declare that your rule has an abstract dependency
on *some* member of a family of targets (a toolchain type), and Bazel
automatically resolves this to a particular target (a toolchain) based on the
applicable platform constraints. Neither the rule author nor the target author
need know the complete set of available platforms and toolchains.

## Writing rules that use toolchains {:#writing-rules-toolchains}

Under the toolchain framework, instead of having rules depend directly on tools,
they instead depend on *toolchain types*. A toolchain type is a simple target
that represents a class of tools that serve the same role for different
platforms. For instance, you can declare a type that represents the bar
compiler:

```python
# By convention, toolchain_type targets are named "toolchain_type" and
# distinguished by their package path. So the full path for this would be
# //bar_tools:toolchain_type.
toolchain_type(name = "toolchain_type")
```

The rule definition in the previous section is modified so that instead of
taking in the compiler as an attribute, it declares that it consumes a
`//bar_tools:toolchain_type` toolchain.

```python
bar_binary = rule(
    implementation = _bar_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        ...
        # No `_compiler` attribute anymore.
    },
    toolchains = ["//bar_tools:toolchain_type"],
)
```

The implementation function now accesses this dependency under `ctx.toolchains`
instead of `ctx.attr`, using the toolchain type as the key.

```python
def _bar_binary_impl(ctx):
    ...
    info = ctx.toolchains["//bar_tools:toolchain_type"].barcinfo
    # The rest is unchanged.
    command = "%s -l %s %s" % (
        info.compiler_path,
        info.system_lib,
        " ".join(info.arch_flags),
    )
    ...
```

`ctx.toolchains["//bar_tools:toolchain_type"]` returns the
[`ToolchainInfo` provider](/rules/lib/toplevel/platform_common#ToolchainInfo)
of whatever target Bazel resolved the toolchain dependency to. The fields of the
`ToolchainInfo` object are set by the underlying tool's rule; in the next
section, this rule is defined such that there is a `barcinfo` field that wraps
a `BarcInfo` object.

Bazel's procedure for resolving toolchains to targets is described
[below](#toolchain-resolution). Only the resolved toolchain target is actually
made a dependency of the `bar_binary` target, not the whole space of candidate
toolchains.

### Mandatory and Optional Toolchains {:#optional-toolchains}

By default, when a rule expresses a toolchain type dependency using a bare label
(as shown above), the toolchain type is considered to be **mandatory**. If Bazel
is unable to find a matching toolchain (see
[Toolchain resolution](#toolchain-resolution) below) for a mandatory toolchain
type, this is an error and analysis halts.

It is possible instead to declare an **optional** toolchain type dependency, as
follows:

```python
bar_binary = rule(
    ...
    toolchains = [
        config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False),
    ],
)
```

When an optional toolchain type cannot be resolved, analysis continues, and the
result of `ctx.toolchains["//bar_tools:toolchain_type"]` is `None`.

The [`config_common.toolchain_type`](/rules/lib/toplevel/config_common#toolchain_type)
function defaults to mandatory.

The following forms can be used:

-  Mandatory toolchain types:
   -  `toolchains = ["//bar_tools:toolchain_type"]`
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type")]`
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = True)]`
- Optional toolchain types:
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False)]`

```python
bar_binary = rule(
    ...
    toolchains = [
        "//foo_tools:toolchain_type",
        config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False),
    ],
)
```

You can mix and match forms in the same rule, also. However, if the same
toolchain type is listed multiple times, it will take the most strict version,
where mandatory is more strict than optional.

### Writing aspects that use toolchains {:#writing-aspects-toolchains}

Aspects have access to the same toolchain API as rules: you can define required
toolchain types, access toolchains via the context, and use them to generate new
actions using the toolchain.

```py
bar_aspect = aspect(
    implementation = _bar_aspect_impl,
    attrs = {},
    toolchains = ['//bar_tools:toolchain_type'],
)

def _bar_aspect_impl(target, ctx):
  toolchain = ctx.toolchains['//bar_tools:toolchain_type']
  # Use the toolchain provider like in a rule.
  return []
```

## Defining toolchains {:#toolchain-definitions}

To define some toolchains for a given toolchain type, you need three things:

1. A language-specific rule representing the kind of tool or tool suite. By
   convention this rule's name is suffixed with "\_toolchain".

    1.  **Note:** The `\_toolchain` rule cannot create any build actions.
        Rather, it collects artifacts from other rules and forwards them to the
        rule that uses the toolchain. That rule is responsible for creating all
        build actions.

2. Several targets of this rule type, representing versions of the tool or tool
   suite for different platforms.

3. For each such target, an associated target of the generic
  [`toolchain`](/reference/be/platforms-and-toolchains#toolchain)
   rule, to provide metadata used by the toolchain framework. This `toolchain`
   target also refers to the `toolchain_type` associated with this toolchain.
   This means that a given `_toolchain` rule could be associated with any
   `toolchain_type`, and that only in a `toolchain` instance that uses
   this `_toolchain` rule that the rule is associated with a `toolchain_type`.

For our running example, here's a definition for a `bar_toolchain` rule. Our
example has only a compiler, but other tools such as a linker could also be
grouped underneath it.

```python
def _bar_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        barcinfo = BarcInfo(
            compiler_path = ctx.attr.compiler_path,
            system_lib = ctx.attr.system_lib,
            arch_flags = ctx.attr.arch_flags,
        ),
    )
    return [toolchain_info]

bar_toolchain = rule(
    implementation = _bar_toolchain_impl,
    attrs = {
        "compiler_path": attr.string(),
        "system_lib": attr.string(),
        "arch_flags": attr.string_list(),
    },
)
```

The rule must return a `ToolchainInfo` provider, which becomes the object that
the consuming rule retrieves using `ctx.toolchains` and the label of the
toolchain type. `ToolchainInfo`, like `struct`, can hold arbitrary field-value
pairs. The specification of exactly what fields are added to the `ToolchainInfo`
should be clearly documented at the toolchain type. In this example, the values
return wrapped in a `BarcInfo` object to reuse the schema defined above; this
style may be useful for validation and code reuse.

Now you can define targets for specific `barc` compilers.

```python
bar_toolchain(
    name = "barc_linux",
    arch_flags = [
        "--arch=Linux",
        "--debug_everything",
    ],
    compiler_path = "/path/to/barc/on/linux",
    system_lib = "/usr/lib/libbarc.so",
)

bar_toolchain(
    name = "barc_windows",
    arch_flags = [
        "--arch=Windows",
        # Different flags, no debug support on windows.
    ],
    compiler_path = "C:\\path\\on\\windows\\barc.exe",
    system_lib = "C:\\path\\on\\windows\\barclib.dll",
)
```

Finally, you create `toolchain` definitions for the two `bar_toolchain` targets.
These definitions link the language-specific targets to the toolchain type and
provide the constraint information that tells Bazel when the toolchain is
appropriate for a given platform.

```python
toolchain(
    name = "barc_linux_toolchain",
    exec_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":barc_linux",
    toolchain_type = ":toolchain_type",
)

toolchain(
    name = "barc_windows_toolchain",
    exec_compatible_with = [
        "@platforms//os:windows",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:windows",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":barc_windows",
    toolchain_type = ":toolchain_type",
)
```

The use of relative path syntax above suggests these definitions are all in the
same package, but there's no reason the toolchain type, language-specific
toolchain targets, and `toolchain` definition targets can't all be in separate
packages.

See the [`go_toolchain`](https://github.com/bazelbuild/rules_go/blob/master/go/private/go_toolchain.bzl){: .external}
for a real-world example.

### Toolchains and configurations

An important question for rule authors is, when a `bar_toolchain` target is
analyzed, what [configuration](/reference/glossary#configuration) does it see, and what transitions
should be used for dependencies? The example above uses string attributes, but
what would happen for a more complicated toolchain that depends on other targets
in the Bazel repository?

Let's see a more complex version of `bar_toolchain`:

```python
def _bar_toolchain_impl(ctx):
    # The implementation is mostly the same as above, so skipping.
    pass

bar_toolchain = rule(
    implementation = _bar_toolchain_impl,
    attrs = {
        "compiler": attr.label(
            executable = True,
            mandatory = True,
            cfg = "exec",
        ),
        "system_lib": attr.label(
            mandatory = True,
            cfg = "target",
        ),
        "arch_flags": attr.string_list(),
    },
)
```

The use of [`attr.label`](/rules/lib/toplevel/attr#label) is the same as for a standard rule,
but the meaning of the `cfg` parameter is slightly different.

The dependency from a target (called the "parent") to a toolchain via toolchain
resolution uses a special configuration transition called the "toolchain
transition". The toolchain transition keeps the configuration the same, except
that it forces the execution platform to be the same for the toolchain as for
the parent (otherwise, toolchain resolution for the toolchain could pick any
execution platform, and wouldn't necessarily be the same as for parent). This
allows any `exec` dependencies of the toolchain to also be executable for the
parent's build actions. Any of the toolchain's dependencies which use `cfg =
"target"` (or which don't specify `cfg`, since "target" is the default) are
built for the same target platform as the parent. This allows toolchain rules to
contribute both libraries (the `system_lib` attribute above) and tools (the
`compiler` attribute) to the build rules which need them. The system libraries
are linked into the final artifact, and so need to be built for the same
platform, whereas the compiler is a tool invoked during the build, and needs to
be able to run on the execution platform.

## Registering and building with toolchains {:#registering-building-toolchains}

At this point all the building blocks are assembled, and you just need to make
the toolchains available to Bazel's resolution procedure. This is done by
registering the toolchain, either in a `MODULE.bazel` file using
`register_toolchains()`, or by passing the toolchains' labels on the command
line using the `--extra_toolchains` flag.

```python
register_toolchains(
    "//bar_tools:barc_linux_toolchain",
    "//bar_tools:barc_windows_toolchain",
    # Target patterns are also permitted, so you could have also written:
    # "//bar_tools:all",
    # or even
    # "//bar_tools/...",
)
```

When using target patterns to register toolchains, the order in which the
individual toolchains are registered is determined by the following rules:

* The toolchains defined in a subpackage of a package are registered before the
  toolchains defined in the package itself.
* Within a package, toolchains are registered in the lexicographical order of
  their names.

Now when you build a target that depends on a toolchain type, an appropriate
toolchain will be selected based on the target and execution platforms.

```python
# my_pkg/BUILD

platform(
    name = "my_target_platform",
    constraint_values = [
        "@platforms//os:linux",
    ],
)

bar_binary(
    name = "my_bar_binary",
    ...
)
```

```sh
bazel build //my_pkg:my_bar_binary --platforms=//my_pkg:my_target_platform
```

Bazel will see that `//my_pkg:my_bar_binary` is being built with a platform that
has `@platforms//os:linux` and therefore resolve the
`//bar_tools:toolchain_type` reference to `//bar_tools:barc_linux_toolchain`.
This will end up building `//bar_tools:barc_linux` but not
`//bar_tools:barc_windows`.

## Toolchain resolution {:#toolchain-resolution}

Note: [Some Bazel rules](/concepts/platforms#status) do not yet support
toolchain resolution.

For each target that uses toolchains, Bazel's toolchain resolution procedure
determines the target's concrete toolchain dependencies. The procedure takes as
input a set of required toolchain types, the target platform, the list of
available execution platforms, and the list of available toolchains. Its outputs
are a selected toolchain for each toolchain type as well as a selected execution
platform for the current target.

The available execution platforms and toolchains are gathered from the
external dependency graph via
[`register_execution_platforms`](/rules/lib/globals/module#register_execution_platforms)
and
[`register_toolchains`](/rules/lib/globals/module#register_toolchains) calls in
`MODULE.bazel` files.
Additional execution platforms and toolchains may also be specified on the
command line via
[`--extra_execution_platforms`](/reference/command-line-reference#flag--extra_execution_platforms)
and
[`--extra_toolchains`](/reference/command-line-reference#flag--extra_toolchains).
The host platform is automatically included as an available execution platform.
Available platforms and toolchains are tracked as ordered lists for determinism,
with preference given to earlier items in the list.

The set of available toolchains, in priority order, is created from
`--extra_toolchains` and `register_toolchains`:

1. Toolchains registered using `--extra_toolchains` are added first. (Within
   these, the **last** toolchain has highest priority.)
2. Toolchains registered using `register_toolchains` in the transitive external
   dependency graph, in the following order: (Within these, the **first**
   mentioned toolchain has highest priority.)
  1. Toolchains registered by the root module (as in, the `MODULE.bazel` at the
     workspace root);
  2. Toolchains registered in the user's `WORKSPACE` file, including in any
     macros invoked from there;
  3. Toolchains registered by non-root modules (as in, dependencies specified by
     the root module, and their dependencies, and so forth);
  4. Toolchains registered in the "WORKSPACE suffix"; this is only used by
     certain native rules bundled with the Bazel installation.

**NOTE:** [Pseudo-targets like `:all`, `:*`, and
`/...`](/run/build#specifying-build-targets) are ordered by Bazel's package
loading mechanism, which uses a lexicographic ordering.

The resolution steps are as follows.

1. A `target_compatible_with` or `exec_compatible_with` clause *matches* a
   platform if, for each `constraint_value` in its list, the platform also has
   that `constraint_value` (either explicitly or as a default).

   If the platform has `constraint_value`s from `constraint_setting`s not
   referenced by the clause, these do not affect matching.

1. If the target being built specifies the
   [`exec_compatible_with` attribute](/reference/be/common-definitions#common.exec_compatible_with)
   (or its rule definition specifies the
   [`exec_compatible_with` argument](/rules/lib/globals/bzl#rule.exec_compatible_with)),
   the list of available execution platforms is filtered to remove
   any that do not match the execution constraints.

1. The list of available toolchains is filtered to remove any toolchains
   specifying `target_settings` that don't match the current configuration.

1. For each available execution platform, you associate each toolchain type with
   the first available toolchain, if any, that is compatible with this execution
   platform and the target platform.

1. Any execution platform that failed to find a compatible mandatory toolchain
   for one of its toolchain types is ruled out. Of the remaining platforms, the
   first one becomes the current target's execution platform, and its associated
   toolchains (if any) become dependencies of the target.

The chosen execution platform is used to run all actions that the target
generates.

In cases where the same target can be built in multiple configurations (such as
for different CPUs) within the same build, the resolution procedure is applied
independently to each version of the target.

If the rule uses [execution groups](/extending/exec-groups), each execution
group performs toolchain resolution separately, and each has its own execution
platform and toolchains.

## Debugging toolchains {:#debugging-toolchains}

If you are adding toolchain support to an existing rule, use the
`--toolchain_resolution_debug=regex` flag. During toolchain resolution, the flag
provides verbose output for toolchain types or target names that match the regex variable. You
can use `.*` to output all information. Bazel will output names of toolchains it
checks and skips during the resolution process.

If you'd like to see which [`cquery`](/query/cquery) dependencies are from toolchain
resolution, use `cquery`'s [`--transitions`](/query/cquery#transitions) flag:

```
# Find all direct dependencies of //cc:my_cc_lib. This includes explicitly
# declared dependencies, implicit dependencies, and toolchain dependencies.
$ bazel cquery 'deps(//cc:my_cc_lib, 1)'
//cc:my_cc_lib (96d6638)
@bazel_tools//tools/cpp:toolchain (96d6638)
@bazel_tools//tools/def_parser:def_parser (HOST)
//cc:my_cc_dep (96d6638)
@local_config_platform//:host (96d6638)
@bazel_tools//tools/cpp:toolchain_type (96d6638)
//:default_host_platform (96d6638)
@local_config_cc//:cc-compiler-k8 (HOST)
//cc:my_cc_lib.cc (null)
@bazel_tools//tools/cpp:grep-includes (HOST)

# Which of these are from toolchain resolution?
$ bazel cquery 'deps(//cc:my_cc_lib, 1)' --transitions=lite | grep "toolchain dependency"
  [toolchain dependency]#@local_config_cc//:cc-compiler-k8#HostTransition -> b6df211
```


Project: /_project.yaml
Book: /_book.yaml
{# disableFinding("native") #}
{# disableFinding("Native") #}
{# disableFinding(LINE_OVER_80_LINK) #}

# Legacy Macros

{% include "_buttons.html" %}

Legacy macros are unstructured functions called from `BUILD` files that can
create targets. By the end of the
[loading phase](/extending/concepts#evaluation-model), legacy macros don't exist
anymore, and Bazel sees only the concrete set of instantiated rules.

## Why you shouldn't use legacy macros (and should use Symbolic macros instead) {:#no-legacy-macros}

Where possible you should use [symbolic macros](macros.md#macros).

Symbolic macros

*   Prevent action at a distance
*   Make it possible to hide implementation details through granular visibility
*   Take typed attributes, which in turn means automatic label and select
    conversion.
*   Are more readable
*   Will soon have [lazy evaluation](macros.md/laziness)

## Usage {:#usage}

The typical use case for a macro is when you want to reuse a rule.

For example, genrule in a `BUILD` file generates a file using `//:generator`
with a `some_arg` argument hardcoded in the command:

```python
genrule(
    name = "file",
    outs = ["file.txt"],
    cmd = "$(location //:generator) some_arg > $@",
    tools = ["//:generator"],
)
```

Note: `$@` is a
[Make variable](/reference/be/make-variables#predefined_genrule_variables) that
refers to the execution-time locations of the files in the `outs` attribute
list. It is equivalent to `$(locations :file.txt)`.

If you want to generate more files with different arguments, you may want to
extract this code to a macro function. To create a macro called
`file_generator`, which has `name` and `arg` parameters, we can replace the
genrule with the following:

```python
load("//path:generator.bzl", "file_generator")

file_generator(
    name = "file",
    arg = "some_arg",
)

file_generator(
    name = "file-two",
    arg = "some_arg_two",
)

file_generator(
    name = "file-three",
    arg = "some_arg_three",
)
```

Here, you load the `file_generator` symbol from a `.bzl` file located in the
`//path` package. By putting macro function definitions in a separate `.bzl`
file, you keep your `BUILD` files clean and declarative, The `.bzl` file can be
loaded from any package in the workspace.

Finally, in `path/generator.bzl`, write the definition of the macro to
encapsulate and parameterize the original genrule definition:

```python
def file_generator(name, arg, visibility=None):
  native.genrule(
    name = name,
    outs = [name + ".txt"],
    cmd = "$(location //:generator) %s > $@" % arg,
    tools = ["//:generator"],
    visibility = visibility,
  )
```

You can also use macros to chain rules together. This example shows chained
genrules, where a genrule uses the outputs of a previous genrule as inputs:

```python
def chained_genrules(name, visibility=None):
  native.genrule(
    name = name + "-one",
    outs = [name + ".one"],
    cmd = "$(location :tool-one) $@",
    tools = [":tool-one"],
    visibility = ["//visibility:private"],
  )

  native.genrule(
    name = name + "-two",
    srcs = [name + ".one"],
    outs = [name + ".two"],
    cmd = "$(location :tool-two) $< $@",
    tools = [":tool-two"],
    visibility = visibility,
  )
```

The example only assigns a visibility value to the second genrule. This allows
macro authors to hide the outputs of intermediate rules from being depended upon
by other targets in the workspace.

Note: Similar to `$@` for outputs, `$<` expands to the locations of files in the
`srcs` attribute list.

## Expanding macros {:#expanding-macros}

When you want to investigate what a macro does, use the `query` command with
`--output=build` to see the expanded form:

```none
$ bazel query --output=build :file
# /absolute/path/test/ext.bzl:42:3
genrule(
  name = "file",
  tools = ["//:generator"],
  outs = ["//test:file.txt"],
  cmd = "$(location //:generator) some_arg > $@",
)
```

## Instantiating native rules {:#instantiating-native-rules}

Native rules (rules that don't need a `load()` statement) can be instantiated
from the [native](/rules/lib/toplevel/native) module:

```python
def my_macro(name, visibility=None):
  native.cc_library(
    name = name,
    srcs = ["main.cc"],
    visibility = visibility,
  )
```

If you need to know the package name (for example, which `BUILD` file is calling
the macro), use the function
[native.package_name()](/rules/lib/toplevel/native#package_name). Note that
`native` can only be used in `.bzl` files, and not in `BUILD` files.

## Label resolution in macros {:#label-resolution}

Since legacy macros are evaluated in the
[loading phase](concepts.md#evaluation-model), label strings such as
`"//foo:bar"` that occur in a legacy macro are interpreted relative to the
`BUILD` file in which the macro is used rather than relative to the `.bzl` file
in which it is defined. This behavior is generally undesirable for macros that
are meant to be used in other repositories, such as because they are part of a
published Starlark ruleset.

To get the same behavior as for Starlark rules, wrap the label strings with the
[`Label`](/rules/lib/builtins/Label#Label) constructor:

```python
# @my_ruleset//rules:defs.bzl
def my_cc_wrapper(name, deps = [], **kwargs):
  native.cc_library(
    name = name,
    deps = deps + select({
      # Due to the use of Label, this label is resolved within @my_ruleset,
      # regardless of its site of use.
      Label("//config:needs_foo"): [
        # Due to the use of Label, this label will resolve to the correct target
        # even if the canonical name of @dep_of_my_ruleset should be different
        # in the main repo, such as due to repo mappings.
        Label("@dep_of_my_ruleset//tools:foo"),
      ],
      "//conditions:default": [],
    }),
    **kwargs,
  )
```

## Debugging {:#debugging}

*   `bazel query --output=build //my/path:all` will show you how the `BUILD`
    file looks after evaluation. All legacy macros, globs, loops are expanded.
    Known limitation: `select` expressions are not shown in the output.

*   You may filter the output based on `generator_function` (which function
    generated the rules) or `generator_name` (the name attribute of the macro):
    `bash $ bazel query --output=build 'attr(generator_function, my_macro,
    //my/path:all)'`

*   To find out where exactly the rule `foo` is generated in a `BUILD` file, you
    can try the following trick. Insert this line near the top of the `BUILD`
    file: `cc_library(name = "foo")`. Run Bazel. You will get an exception when
    the rule `foo` is created (due to a name conflict), which will show you the
    full stack trace.

*   You can also use [print](/rules/lib/globals/all#print) for debugging. It
    displays the message as a `DEBUG` log line during the loading phase. Except
    in rare cases, either remove `print` calls, or make them conditional under a
    `debugging` parameter that defaults to `False` before submitting the code to
    the depot.

## Errors {:#errors}

If you want to throw an error, use the [fail](/rules/lib/globals/all#fail)
function. Explain clearly to the user what went wrong and how to fix their
`BUILD` file. It is not possible to catch an error.

```python
def my_macro(name, deps, visibility=None):
  if len(deps) < 2:
    fail("Expected at least two values in deps")
  # ...
```

## Conventions {:#conventions}

*   All public functions (functions that don't start with underscore) that
    instantiate rules must have a `name` argument. This argument should not be
    optional (don't give a default value).

*   Public functions should use a docstring following
    [Python conventions](https://www.python.org/dev/peps/pep-0257/#one-line-docstrings).

*   In `BUILD` files, the `name` argument of the macros must be a keyword
    argument (not a positional argument).

*   The `name` attribute of rules generated by a macro should include the name
    argument as a prefix. For example, `macro(name = "foo")` can generate a
    `cc_library` `foo` and a genrule `foo_gen`.

*   In most cases, optional parameters should have a default value of `None`.
    `None` can be passed directly to native rules, which treat it the same as if
    you had not passed in any argument. Thus, there is no need to replace it
    with `0`, `False`, or `[]` for this purpose. Instead, the macro should defer
    to the rules it creates, as their defaults may be complex or may change over
    time. Additionally, a parameter that is explicitly set to its default value
    looks different than one that is never set (or set to `None`) when accessed
    through the query language or build-system internals.

*   Macros should have an optional `visibility` argument.


Project: /_project.yaml
Book: /_book.yaml
{# disableFinding("Currently") #}
{# disableFinding(TODO) #}

# Macros

{% include "_buttons.html" %}

This page covers the basics of using macros and includes typical use cases,
debugging, and conventions.

A macro is a function called from the `BUILD` file that can instantiate rules.
Macros are mainly used for encapsulation and code reuse of existing rules and
other macros.

Macros come in two flavors: symbolic macros, which are described on this page,
and [legacy macros](legacy-macros.md). Where possible, we recommend using
symbolic macros for code clarity.

Symbolic macros offer typed arguments (string to label conversion, relative to
where the macro was called) and the ability to restrict and specify the
visibility of targets created. They are designed to be amenable to lazy
evaluation (which will be added in a future Bazel release). Symbolic macros are
available by default in Bazel 8. Where this document mentions `macros`, it's
referring to **symbolic macros**.

An executable example of symbolic macros can be found in the
[examples repository](https://github.com/bazelbuild/examples/tree/main/macros).

## Usage {:#usage}

Macros are defined in `.bzl` files by calling the
[`macro()`](https://bazel.build/rules/lib/globals/bzl.html#macro) function with
two required parameters: `attrs` and `implementation`.

### Attributes {:#attributes}

`attrs` accepts a dictionary of attribute name to [attribute
types](https://bazel.build/rules/lib/toplevel/attr#members), which represents
the arguments to the macro. Two common attributes – `name` and `visibility` –
are implicitly added to all macros and are not included in the dictionary passed
to `attrs`.

```starlark
# macro/macro.bzl
my_macro = macro(
    attrs = {
        "deps": attr.label_list(mandatory = True, doc = "The dependencies passed to the inner cc_binary and cc_test targets"),
        "create_test": attr.bool(default = False, configurable = False, doc = "If true, creates a test target"),
    },
    implementation = _my_macro_impl,
)
```

Attribute type declarations accept the
[parameters](https://bazel.build/rules/lib/toplevel/attr#parameters),
`mandatory`, `default`, and `doc`. Most attribute types also accept the
`configurable` parameter, which determines wheher the attribute accepts
`select`s. If an attribute is `configurable`, it will parse non-`select` values
as an unconfigurable `select` – `"foo"` will become
`select({"//conditions:default": "foo"})`. Learn more in [selects](#selects).

#### Attribute inheritance {:#attribute-inheritance}

Macros are often intended to wrap a rule (or another macro), and the macro's
author often wants to forward the bulk of the wrapped symbol's attributes
unchanged, using `**kwargs`, to the macro's main target (or main inner macro).

To support this pattern, a macro can *inherit attributes* from a rule or another
macro by passing the [rule](https://bazel.build/rules/lib/builtins/rule) or
[macro symbol](https://bazel.build/rules/lib/builtins/macro) to `macro()`'s
`inherit_attrs` argument. (You can also use the special string `"common"`
instead of a rule or macro symbol to inherit the [common attributes defined for
all Starlark build
rules](https://bazel.build/reference/be/common-definitions#common-attributes).)
Only public attributes get inherited, and the attributes in the macro's own
`attrs` dictionary override inherited attributes with the same name. You can
also *remove* inherited attributes by using `None` as a value in the `attrs`
dictionary:

```starlark
# macro/macro.bzl
my_macro = macro(
    inherit_attrs = native.cc_library,
    attrs = {
        # override native.cc_library's `local_defines` attribute
        "local_defines": attr.string_list(default = ["FOO"]),
        # do not inherit native.cc_library's `defines` attribute
        "defines": None,
    },
    ...
)
```

The default value of non-mandatory inherited attributes is always overridden to
be `None`, regardless of the original attribute definition's default value. If
you need to examine or modify an inherited non-mandatory attribute – for
example, if you want to add a tag to an inherited `tags` attribute – you must
make sure to handle the `None` case in your macro's implementation function:

```starlark
# macro/macro.bzl
_my_macro_implementation(name, visibility, tags, **kwargs):
    # Append a tag; tags attr is an inherited non-mandatory attribute, and
    # therefore is None unless explicitly set by the caller of our macro.
    my_tags = (tags or []) + ["another_tag"]
    native.cc_library(
        ...
        tags = my_tags,
        **kwargs,
    )
    ...
```

### Implementation {:#implementation}

`implementation` accepts a function which contains the logic of the macro.
Implementation functions often create targets by calling one or more rules, and
they are usually private (named with a leading underscore). Conventionally,
they are named the same as their macro, but prefixed with `_` and suffixed with
`_impl`.

Unlike rule implementation functions, which take a single argument (`ctx`) that
contains a reference to the attributes, macro implementation functions accept a
parameter for each argument.

```starlark
# macro/macro.bzl
def _my_macro_impl(name, visibility, deps, create_test):
    cc_library(
        name = name + "_cc_lib",
        deps = deps,
    )

    if create_test:
        cc_test(
            name = name + "_test",
            srcs = ["my_test.cc"],
            deps = deps,
        )
```

If a macro inherits attributes, its implementation function *must* have a
`**kwargs` residual keyword parameter, which can be forwarded to the call that
invokes the inherited rule or submacro. (This helps ensure that your macro won't
be broken if the rule or macro which from which you are inheriting adds a new
attribute.)

### Declaration {:#declaration}

Macros are declared by loading and calling their definition in a `BUILD` file.

```starlark

# pkg/BUILD

my_macro(
    name = "macro_instance",
    deps = ["src.cc"] + select(
        {
            "//config_setting:special": ["special_source.cc"],
            "//conditions:default": [],
        },
    ),
    create_tests = True,
)
```

This would create targets
`//pkg:macro_instance_cc_lib` and`//pkg:macro_instance_test`.

Just like in rule calls, if an attribute value in a macro call is set to `None`,
that attribute is treated as if it was omitted by the macro's caller. For
example, the following two macro calls are equivalent:

```starlark
# pkg/BUILD
my_macro(name = "abc", srcs = ["src.cc"], deps = None)
my_macro(name = "abc", srcs = ["src.cc"])
```

This is generally not useful in `BUILD` files, but is helpful when
programmatically wrapping a macro inside another macro.

## Details {:#usage-details}

### Naming conventions for targets created {:#naming}

The names of any targets or submacros created by a symbolic macro must
either match the macro's `name` parameter or must be prefixed by `name` followed
by `_` (preferred), `.` or `-`. For example, `my_macro(name = "foo")` may only
create files or targets named `foo`, or prefixed by `foo_`, `foo-` or `foo.`,
for example, `foo_bar`.

Targets or files that violate macro naming convention can be declared, but
cannot be built and cannot be used as dependencies.

Non-macro files and targets within the same package as a macro instance should
*not* have names that conflict with potential macro target names, though this
exclusivity is not enforced. We are in the progress of implementing
[lazy evaluation](#laziness) as a performance improvement for Symbolic macros,
which will be impaired in packages that violate the naming schema.

### Restrictions {:#restrictions}

Symbolic macros have some additional restrictions compared to legacy macros.

Symbolic macros

*   must take a `name` argument and a `visibility` argument
*   must have an `implementation` function
*   may not return values
*   may not mutate their arguments
*   may not call `native.existing_rules()` unless they are special `finalizer`
    macros
*   may not call `native.package()`
*   may not call `glob()`
*   may not call `native.environment_group()`
*   must create targets whose names adhere to the [naming schema](#naming)
*   can't refer to input files that weren't declared or passed in as an argument
*   can't refer to private targets of their callers (see
    [visibility and macros](#visibility) for more details).

### Visibility and macros {:#visibility}

The [visibility](/concepts/visibility) system helps protect the implementation
details of both (symbolic) macros and their callers.

By default, targets created in a symbolic macro are visible within the macro
itself, but not necessarily to the macro's caller. The macro can "export" a
target as a public API by forwarding the value of its own `visibility`
attribute, as in `some_rule(..., visibility = visibility)`.

The key ideas of macro visibility are:

1. Visibility is checked based on what macro declared the target, not what
   package called the macro.

   * In other words, being in the same package does not by itself make one
     target visible to another. This protects the macro's internal targets
     from becoming dependencies of other macros or top-level targets in the
     package.

1. All `visibility` attributes, on both rules and macros, automatically
   include the place where the rule or macro was called.

   * Thus, a target is unconditionally visible to other targets declared in the
     same macro (or the `BUILD` file, if not in a macro).

In practice, this means that when a macro declares a target without setting its
`visibility`, the target defaults to being internal to the macro. (The package's
[default visibility](/reference/be/functions#package.default_visibility) does
not apply within a macro.) Exporting the target means that the target is visible
to whatever the macro's caller specified in the macro's `visibility` attribute,
plus the package of the macro's caller itself, as well as the macro's own code.
Another way of thinking of it is that the visibility of a macro determines who
(aside from the macro itself) can see the macro's exported targets.

```starlark
# tool/BUILD
...
some_rule(
    name = "some_tool",
    visibility = ["//macro:__pkg__"],
)
```

```starlark
# macro/macro.bzl

def _impl(name, visibility):
    cc_library(
        name = name + "_helper",
        ...
        # No visibility passed in. Same as passing `visibility = None` or
        # `visibility = ["//visibility:private"]`. Visible to the //macro
        # package only.
    )
    cc_binary(
        name = name + "_exported",
        deps = [
            # Allowed because we're also in //macro. (Targets in any other
            # instance of this macro, or any other macro in //macro, can see it
            # too.)
            name + "_helper",
            # Allowed by some_tool's visibility, regardless of what BUILD file
            # we're called from.
            "//tool:some_tool",
        ],
        ...
        visibility = visibility,
    )

my_macro = macro(implementation = _impl, ...)
```

```starlark
# pkg/BUILD
load("//macro:macro.bzl", "my_macro")
...

my_macro(
    name = "foo",
    ...
)

some_rule(
    ...
    deps = [
        # Allowed, its visibility is ["//pkg:__pkg__", "//macro:__pkg__"].
        ":foo_exported",
        # Disallowed, its visibility is ["//macro:__pkg__"] and
        # we are not in //macro.
        ":foo_helper",
    ]
)
```

If `my_macro` were called with `visibility = ["//other_pkg:__pkg__"]`, or if
the `//pkg` package had set its `default_visibility` to that value, then
`//pkg:foo_exported` could also be used within `//other_pkg/BUILD` or within a
macro defined in `//other_pkg:defs.bzl`, but `//pkg:foo_helper` would remain
protected.

A macro can declare that a target is visible to a friend package by passing
`visibility = ["//some_friend:__pkg__"]` (for an internal target) or
`visibility = visibility + ["//some_friend:__pkg__"]` (for an exported one).
Note that it is an antipattern for a macro to declare a target with public
visibility (`visibility = ["//visibility:public"]`). This is because it makes
the target unconditionally visible to every package, even if the caller
specified a more restricted visibility.

All visibility checking is done with respect to the innermost currently running
symbolic macro. However, there is a visibility delegation mechanism: If a macro
passes a label as an attribute value to an inner macro, any usages of the label
in the inner macro are checked with respect to the outer macro. See the
[visibility page](/concepts/visibility#symbolic-macros) for more details.

Remember that legacy macros are entirely transparent to the visibility system,
and behave as though their location is whatever BUILD file or symbolic macro
they were called from.

#### Finalizers and visibility {:#finalizers-and-visibility}

Targets declared in a rule finalizer, in addition to seeing targets following
the usual symbolic macro visibility rules, can *also* see all targets which are
visible to the finalizer target's package.

This means that if you migrate a `native.existing_rules()`-based legacy macro to
a finalizer, the targets declared by the finalizer will still be able to see
their old dependencies.

However, note that it's possible to declare a target in a symbolic macro such
that a finalizer's targets cannot see it under the visibility system – even
though the finalizer can *introspect* its attributes using
`native.existing_rules()`.

### Selects {:#selects}

If an attribute is `configurable` (the default) and its value is not `None`,
then the macro implementation function will see the attribute value as wrapped
in a trivial `select`. This makes it easier for the macro author to catch bugs
where they did not anticipate that the attribute value could be a `select`.

For example, consider the following macro:

```starlark
my_macro = macro(
    attrs = {"deps": attr.label_list()},  # configurable unless specified otherwise
    implementation = _my_macro_impl,
)
```

If `my_macro` is invoked with `deps = ["//a"]`, that will cause `_my_macro_impl`
to be invoked with its `deps` parameter set to `select({"//conditions:default":
["//a"]})`. If this causes the implementation function to fail (say, because the
code tried to index into the value as in `deps[0]`, which is not allowed for
`select`s), the macro author can then make a choice: either they can rewrite
their macro to only use operations compatible with `select`, or they can mark
the attribute as nonconfigurable (`attr.label_list(configurable = False)`). The
latter ensures that users are not permitted to pass a `select` value in.

Rule targets reverse this transformation, and store trivial `select`s as their
unconditional values; in the above example, if `_my_macro_impl` declares a rule
target `my_rule(..., deps = deps)`, that rule target's `deps` will be stored as
`["//a"]`. This ensures that `select`-wrapping does not cause trivial `select`
values to be stored in all targets instantiated by macros.

If the value of a configurable attribute is `None`, it does not get wrapped in a
`select`. This ensures that tests like `my_attr == None` still work, and that
when the attribute is forwarded to a rule with a computed default, the rule
behaves properly (that is, as if the attribute were not passed in at all). It is
not always possible for an attribute to take on a `None` value, but it can
happen for the `attr.label()` type, and for any inherited non-mandatory
attribute.

## Finalizers {:#finalizers}

A rule finalizer is a special symbolic macro which – regardless of its lexical
position in a BUILD file – is evaluated in the final stage of loading a package,
after all non-finalizer targets have been defined. Unlike ordinary symbolic
macros, a finalizer can call `native.existing_rules()`, where it behaves
slightly differently than in legacy macros: it only returns the set of
non-finalizer rule targets. The finalizer may assert on the state of that set or
define new targets.

To declare a finalizer, call `macro()` with `finalizer = True`:

```starlark
def _my_finalizer_impl(name, visibility, tags_filter):
    for r in native.existing_rules().values():
        for tag in r.get("tags", []):
            if tag in tags_filter:
                my_test(
                    name = name + "_" + r["name"] + "_finalizer_test",
                    deps = [r["name"]],
                    data = r["srcs"],
                    ...
                )
                continue

my_finalizer = macro(
    attrs = {"tags_filter": attr.string_list(configurable = False)},
    implementation = _impl,
    finalizer = True,
)
```

## Laziness {:#laziness}

IMPORTANT: We are in the process of implementing lazy macro expansion and
evaluation. This feature is not available yet.

Currently, all macros are evaluated as soon as the BUILD file is loaded, which
can negatively impact performance for targets in packages that also have costly
unrelated macros. In the future, non-finalizer symbolic macros will only be
evaluated if they're required for the build. The prefix naming schema helps
Bazel determine which macro to expand given a requested target.

## Migration troubleshooting {:#troubleshooting}

Here are some common migration headaches and how to fix them.

*   Legacy macro calls `glob()`

Move the `glob()` call to your BUILD file (or to a legacy macro called from the
BUILD file), and pass the `glob()` value to the symbolic macro using a
label-list attribute:

```starlark
# BUILD file
my_macro(
    ...,
    deps = glob(...),
)
```

*   Legacy macro has a parameter that isn't a valid starlark `attr` type.

Pull as much logic as possible into a nested symbolic macro, but keep the
top level macro a legacy macro.

*  Legacy macro calls a rule that creates a target that breaks the naming schema

That's okay, just don't depend on the "offending" target. The naming check will
be quietly ignored.



Project: /_project.yaml
Book: /_book.yaml

# Depsets

{% include "_buttons.html" %}

[Depsets](/rules/lib/builtins/depset) are a specialized data structure for efficiently
collecting data across a target’s transitive dependencies. They are an essential
element of rule processing.

The defining feature of depset is its time- and space-efficient union operation.
The depset constructor accepts a list of elements ("direct") and a list of other
depsets ("transitive"), and returns a depset representing a set containing all the
direct elements and the union of all the transitive sets. Conceptually, the
constructor creates a new graph node that has the direct and transitive nodes
as its successors. Depsets have a well-defined ordering semantics, based on
traversal of this graph.

Example uses of depsets include:

*   Storing the paths of all object files for a program’s libraries, which can
    then be passed to a linker action through a provider.

*   For an interpreted language, storing the transitive source files that are
    included in an executable's runfiles.

## Description and operations

Conceptually, a depset is a directed acyclic graph (DAG) that typically looks
similar to the target graph. It is constructed from the leaves up to the root.
Each target in a dependency chain can add its own contents on top of the
previous without having to read or copy them.

Each node in the DAG holds a list of direct elements and a list of child nodes.
The contents of the depset are the transitive elements, such as the direct elements
of all the nodes. A new depset can be created using the
[depset](/rules/lib/globals/bzl#depset) constructor: it accepts a list of direct
elements and another list of child nodes.

```python
s = depset(["a", "b", "c"])
t = depset(["d", "e"], transitive = [s])

print(s)    # depset(["a", "b", "c"])
print(t)    # depset(["d", "e", "a", "b", "c"])
```

To retrieve the contents of a depset, use the
[to_list()](/rules/lib/builtins/depset#to_list) method. It returns a list of all transitive
elements, not including duplicates. There is no way to directly inspect the
precise structure of the DAG, although this structure does affect the order in
which the elements are returned.

```python
s = depset(["a", "b", "c"])

print("c" in s.to_list())              # True
print(s.to_list() == ["a", "b", "c"])  # True
```

The allowed items in a depset are restricted, just as the allowed keys in
dictionaries are restricted. In particular, depset contents may not be mutable.

Depsets use reference equality: a depset is equal to itself, but unequal to any
other depset, even if they have the same contents and same internal structure.

```python
s = depset(["a", "b", "c"])
t = s
print(s == t)  # True

t = depset(["a", "b", "c"])
print(s == t)  # False

d = {}
d[s] = None
d[t] = None
print(len(d))  # 2
```

To compare depsets by their contents, convert them to sorted lists.

```python
s = depset(["a", "b", "c"])
t = depset(["c", "b", "a"])
print(sorted(s.to_list()) == sorted(t.to_list()))  # True
```

There is no ability to remove elements from a depset. If this is needed, you
must read out the entire contents of the depset, filter the elements you want to
remove, and reconstruct a new depset. This is not particularly efficient.

```python
s = depset(["a", "b", "c"])
t = depset(["b", "c"])

# Compute set difference s - t. Precompute t.to_list() so it's not done
# in a loop, and convert it to a dictionary for fast membership tests.
t_items = {e: None for e in t.to_list()}
diff_items = [x for x in s.to_list() if x not in t_items]
# Convert back to depset if it's still going to be used for union operations.
s = depset(diff_items)
print(s)  # depset(["a"])
```

### Order

The `to_list` operation performs a traversal over the DAG. The kind of traversal
depends on the *order* that was specified at the time the depset was
constructed. It is useful for Bazel to support multiple orders because sometimes
tools care about the order of their inputs. For example, a linker action may
need to ensure that if `B` depends on `A`, then `A.o` comes before `B.o` on the
linker’s command line. Other tools might have the opposite requirement.

Three traversal orders are supported: `postorder`, `preorder`, and
`topological`. The first two work exactly like [tree
traversals](https://en.wikipedia.org/wiki/Tree_traversal#Depth-first_search)
except that they operate on DAGs and skip already visited nodes. The third order
works as a topological sort from root to leaves, essentially the same as
preorder except that shared children are listed only after all of their parents.
Preorder and postorder operate as left-to-right traversals, but note that within
each node direct elements have no order relative to children. For topological
order, there is no left-to-right guarantee, and even the
all-parents-before-child guarantee does not apply in the case that there are
duplicate elements in different nodes of the DAG.

```python
# This demonstrates different traversal orders.

def create(order):
  cd = depset(["c", "d"], order = order)
  gh = depset(["g", "h"], order = order)
  return depset(["a", "b", "e", "f"], transitive = [cd, gh], order = order)

print(create("postorder").to_list())  # ["c", "d", "g", "h", "a", "b", "e", "f"]
print(create("preorder").to_list())   # ["a", "b", "e", "f", "c", "d", "g", "h"]
```

```python
# This demonstrates different orders on a diamond graph.

def create(order):
  a = depset(["a"], order=order)
  b = depset(["b"], transitive = [a], order = order)
  c = depset(["c"], transitive = [a], order = order)
  d = depset(["d"], transitive = [b, c], order = order)
  return d

print(create("postorder").to_list())    # ["a", "b", "c", "d"]
print(create("preorder").to_list())     # ["d", "b", "a", "c"]
print(create("topological").to_list())  # ["d", "b", "c", "a"]
```

Due to how traversals are implemented, the order must be specified at the time
the depset is created with the constructor’s `order` keyword argument. If this
argument is omitted, the depset has the special `default` order, in which case
there are no guarantees about the order of any of its elements (except that it
is deterministic).

## Full example

This example is available at
[https://github.com/bazelbuild/examples/tree/main/rules/depsets](https://github.com/bazelbuild/examples/tree/main/rules/depsets).

Suppose there is a hypothetical interpreted language Foo. In order to build
each `foo_binary` you need to know all the `*.foo` files that it directly or
indirectly depends on.

```python
# //depsets:BUILD

load(":foo.bzl", "foo_library", "foo_binary")

# Our hypothetical Foo compiler.
py_binary(
    name = "foocc",
    srcs = ["foocc.py"],
)

foo_library(
    name = "a",
    srcs = ["a.foo", "a_impl.foo"],
)

foo_library(
    name = "b",
    srcs = ["b.foo", "b_impl.foo"],
    deps = [":a"],
)

foo_library(
    name = "c",
    srcs = ["c.foo", "c_impl.foo"],
    deps = [":a"],
)

foo_binary(
    name = "d",
    srcs = ["d.foo"],
    deps = [":b", ":c"],
)
```

```python
# //depsets:foocc.py

# "Foo compiler" that just concatenates its inputs to form its output.
import sys

if __name__ == "__main__":
  assert len(sys.argv) >= 1
  output = open(sys.argv[1], "wt")
  for path in sys.argv[2:]:
    input = open(path, "rt")
    output.write(input.read())
```

Here, the transitive sources of the binary `d` are all of the `*.foo` files in
the `srcs` fields of `a`, `b`, `c`, and `d`. In order for the `foo_binary`
target to know about any file besides `d.foo`, the `foo_library` targets need to
pass them along in a provider. Each library receives the providers from its own
dependencies, adds its own immediate sources, and passes on a new provider with
the augmented contents. The `foo_binary` rule does the same, except that instead
of returning a provider, it uses the complete list of sources to construct a
command line for an action.

Here’s a complete implementation of the `foo_library` and `foo_binary` rules.

```python
# //depsets/foo.bzl

# A provider with one field, transitive_sources.
FooFiles = provider(fields = ["transitive_sources"])

def get_transitive_srcs(srcs, deps):
  """Obtain the source files for a target and its transitive dependencies.

  Args:
    srcs: a list of source files
    deps: a list of targets that are direct dependencies
  Returns:
    a collection of the transitive sources
  """
  return depset(
        srcs,
        transitive = [dep[FooFiles].transitive_sources for dep in deps])

def _foo_library_impl(ctx):
  trans_srcs = get_transitive_srcs(ctx.files.srcs, ctx.attr.deps)
  return [FooFiles(transitive_sources=trans_srcs)]

foo_library = rule(
    implementation = _foo_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files=True),
        "deps": attr.label_list(),
    },
)

def _foo_binary_impl(ctx):
  foocc = ctx.executable._foocc
  out = ctx.outputs.out
  trans_srcs = get_transitive_srcs(ctx.files.srcs, ctx.attr.deps)
  srcs_list = trans_srcs.to_list()
  ctx.actions.run(executable = foocc,
                  arguments = [out.path] + [src.path for src in srcs_list],
                  inputs = srcs_list + [foocc],
                  outputs = [out])

foo_binary = rule(
    implementation = _foo_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files=True),
        "deps": attr.label_list(),
        "_foocc": attr.label(default=Label("//depsets:foocc"),
                             allow_files=True, executable=True, cfg="host")
    },
    outputs = {"out": "%{name}.out"},
)
```

You can test this by copying these files into a fresh package, renaming the
labels appropriately, creating the source `*.foo` files with dummy content, and
building the `d` target.


## Performance

To see the motivation for using depsets, consider what would happen if
`get_transitive_srcs()` collected its sources in a list.

```python
def get_transitive_srcs(srcs, deps):
  trans_srcs = []
  for dep in deps:
    trans_srcs += dep[FooFiles].transitive_sources
  trans_srcs += srcs
  return trans_srcs
```

This does not take into account duplicates, so the source files for `a`
will appear twice on the command line and twice in the contents of the output
file.

An alternative is using a general set, which can be simulated by a
dictionary where the keys are the elements and all the keys map to `True`.

```python
def get_transitive_srcs(srcs, deps):
  trans_srcs = {}
  for dep in deps:
    for file in dep[FooFiles].transitive_sources:
      trans_srcs[file] = True
  for file in srcs:
    trans_srcs[file] = True
  return trans_srcs
```

This gets rid of the duplicates, but it makes the order of the command line
arguments (and therefore the contents of the files) unspecified, although still
deterministic.

Moreover, both approaches are asymptotically worse than the depset-based
approach. Consider the case where there is a long chain of dependencies on
Foo libraries. Processing every rule requires copying all of the transitive
sources that came before it into a new data structure. This means that the
time and space cost for analyzing an individual library or binary target
is proportional to its own height in the chain. For a chain of length n,
foolib_1 ← foolib_2 ← … ← foolib_n, the overall cost is effectively O(n^2).

Generally speaking, depsets should be used whenever you are accumulating
information through your transitive dependencies. This helps ensure that
your build scales well as your target graph grows deeper.

Finally, it’s important to not retrieve the contents of the depset
unnecessarily in rule implementations. One call to `to_list()`
at the end in a binary rule is fine, since the overall cost is just O(n). It’s
when many non-terminal targets try to call `to_list()` that quadratic behavior
occurs.

For more information about using depsets efficiently, see the [performance](/rules/performance) page.

## API Reference

Please see [here](/rules/lib/builtins/depset) for more details.



Project: /_project.yaml
Book: /_book.yaml

# Automatic Execution Groups (AEGs)

{% include "_buttons.html" %}

Automatic execution groups select an [execution platform][exec_platform]
for each toolchain type. In other words, one target can have multiple
execution platforms without defining execution groups.

## Quick summary {:#quick-summary}

Automatic execution groups are closely connected to toolchains. If you are using
toolchains, you need to set them on the affected actions (actions which use an
executable or a tool from a toolchain) by adding `toolchain` parameter. For
example:

```python
ctx.actions.run(
    ...,
    executable = ctx.toolchain['@bazel_tools//tools/jdk:toolchain_type'].tool,
    ...,
    toolchain = '@bazel_tools//tools/jdk:toolchain_type',
)
```
If the action does not use a tool or executable from a toolchain, and Blaze
doesn't detect that ([the error](#first-error-message) is raised), you can set
`toolchain = None`.

If you need to use multiple toolchains on a single execution platform (an action
uses executable or tools from two or more toolchains), you need to manually
define [exec_groups][exec_groups] (check
[When should I use a custom exec_group?][multiple_toolchains_exec_groups]
section).

## History {:#history}

Before AEGs, the execution platform was selected on a rule level. For example:

```python
my_rule = rule(
    _impl,
    toolchains = ['//tools:toolchain_type_1', '//tools:toolchain_type_2'],
)
```

Rule `my_rule` registers two toolchain types. This means that the [Toolchain
Resolution](https://bazel.build/extending/toolchains#toolchain-resolution) used
to find an execution platform which supports both toolchain types. The selected
execution platform was used for each registered action inside the rule, unless
specified differently with [exec_groups][exec_groups].
In other words, all actions inside the rule used to have a single execution
platform even if they used tools from different toolchains (execution platform
is selected for each target). This resulted in failures when there was no
execution platform supporting all toolchains.

## Current state {:#current-state}

With AEGs, the execution platform is selected for each toolchain type. The
implementation function of the earlier example, `my_rule`, would look like:

```python
def _impl(ctx):
    ctx.actions.run(
      mnemonic = "First action",
      executable = ctx.toolchain['//tools:toolchain_type_1'].tool,
      toolchain = '//tools:toolchain_type_1',
    )

    ctx.actions.run(
      mnemonic = "Second action",
      executable = ctx.toolchain['//tools:toolchain_type_2'].tool,
      toolchain = '//tools:toolchain_type_2',
    )
```

This rule creates two actions, the `First action` which uses executable from a
`//tools:toolchain_type_1` and the `Second action` which uses executable from a
`//tools:toolchain_type_2`. Before AEGs, both of these actions would be executed
on a single execution platform which supports both toolchain types. With AEGs,
by adding the `toolchain` parameter inside the actions, each action executes on
the execution platform that provides the toolchain. The actions may be executed
on different execution platforms.

The same is effective with [ctx.actions.run_shell][run_shell] where `toolchain`
parameter should be added when `tools` are from a toolchain.

## Difference between custom exec groups and automatic exec groups {:#difference-custom}

As the name suggests, AEGs are exec groups created automatically for each
toolchain type registered on a rule. There is no need to manually specify them,
unlike the "classic" exec groups.

### When should I use a custom exec_group? {:#when-should-use-exec-groups}

Custom exec_groups are needed only in case where multiple toolchains need to
execute on a single execution platform. In all other cases there's no need to
define custom exec_groups. For example:

```python
def _impl(ctx):
    ctx.actions.run(
      ...,
      executable = ctx.toolchain['//tools:toolchain_type_1'].tool,
      tools = [ctx.toolchain['//tools:toolchain_type_2'].tool],
      exec_group = 'two_toolchains',
    )
```

```python
my_rule = rule(
    _impl,
    exec_groups = {
        "two_toolchains": exec_group(
            toolchains = ['//tools:toolchain_type_1', '//tools:toolchain_type_2'],
        ),
    }
)
```

## Migration of AEGs {:#migration-aegs}

Internally in google3, Blaze is already using AEGs.
Externally for Bazel, migration is in the process. Some rules are already using
this feature (e.g. Java and C++ rules).

### Which Bazel versions support this migration? {:#which-bazel}

AEGs are fully supported from Bazel 7.

### How to enable AEGs? {:#how-enable}

Set `--incompatible_auto_exec_groups` to true. More information about the flag
on [the GitHub issue][github_flag].

### How to enable AEGs inside a particular rule? {:#how-enable-particular-rule}

Set the `_use_auto_exec_groups` attribute on a rule.

```python
my_rule = rule(
    _impl,
    attrs = {
      "_use_auto_exec_groups": attr.bool(default = True),
    }
)
```
This enables AEGs only in `my_rule` and its actions start using the new logic
when selecting the execution platform. Incompatible flag is overridden with this
attribute.

### How to disable AEGs in case of an error? {:#how-disable}

Set `--incompatible_auto_exec_groups` to false to completely disable AEGs in
your project ([flag's GitHub issue][github_flag]), or disable a particular rule
by setting `_use_auto_exec_groups` attribute to `False`
([more details about the attribute](#how-enable-particular-rule)).

### Error messages while migrating to AEGs {:#potential-problems}

#### Couldn't identify if tools are from implicit dependencies or a toolchain. Please set the toolchain parameter. If you're not using a toolchain, set it to 'None'. {:#first-error-message}
  * In this case you get a stack of calls before the error happened and you can
    clearly see which exact action needs the toolchain parameter. Check which
    toolchain is used for the action and set it with the toolchain param. If no
    toolchain is used inside the action for tools or executable, set it to
    `None`.

#### Action declared for non-existent toolchain '[toolchain_type]'.
  * This means that you've set the toolchain parameter on the action but didn't
register it on the rule. Register the toolchain or set `None` inside the action.

## Additional material {:#additional-material}

For more information, check design document:
[Automatic exec groups for toolchains][aegs_design_doc].

[exec_platform]: https://bazel.build/extending/platforms#:~:text=Execution%20%2D%20a%20platform%20on%20which%20build%20tools%20execute%20build%20actions%20to%20produce%20intermediate%20and%20final%20outputs.
[exec_groups]: https://bazel.build/extending/exec-groups
[github_flag]: https://github.com/bazelbuild/bazel/issues/17134
[aegs_design_doc]: https://docs.google.com/document/d/1-rbP_hmKs9D639YWw5F_JyxPxL2bi6dSmmvj_WXak9M/edit#heading=h.5mcn15i0e1ch
[run_shell]: https://bazel.build/rules/lib/builtins/actions#run_shell
[multiple_toolchains_exec_groups]: /extending/auto-exec-groups#when-should-use-exec-groups

Project: /_project.yaml
Book: /_book.yaml

# Extension Overview

{% include "_buttons.html" %}

<!-- [TOC] -->

This page describes how to extend the BUILD language using macros
and rules.

Bazel extensions are files ending in `.bzl`. Use a
[load statement](/concepts/build-files#load) to import a symbol from an extension.

Before learning the more advanced concepts, first:

* Read about the [Starlark language](/rules/language), used in both the
  `BUILD` and `.bzl` files.

* Learn how you can [share variables](/build/share-variables)
  between two `BUILD` files.

## Macros and rules {:#macros-and-rules}

A macro is a function that instantiates rules. Macros come in two flavors:
[symbolic macros](/extending/macros) (new in Bazel 8) and [legacy
macros](/extending/legacy-macros). The two flavors of macros are defined
differently, but behave almost the same from the point of view of a user. A
macro is useful when a `BUILD` file is getting too repetitive or too complex, as
it lets you reuse some code. The function is evaluated as soon as the `BUILD`
file is read. After the evaluation of the `BUILD` file, Bazel has little
information about macros. If your macro generates a `genrule`, Bazel will
behave *almost* as if you declared that `genrule` in the `BUILD` file. (The one
exception is that targets declared in a symbolic macro have [special visibility
semantics](/extending/macros#visibility): a symbolic macro can hide its internal
targets from the rest of the package.)

A [rule](/extending/rules) is more powerful than a macro. It can access Bazel
internals and have full control over what is going on. It may for example pass
information to other rules.

If you want to reuse simple logic, start with a macro; we recommend a symbolic
macro, unless you need to support older Bazel versions. If a macro becomes
complex, it is often a good idea to make it a rule. Support for a new language
is typically done with a rule. Rules are for advanced users, and most users will
never have to write one; they will only load and call existing rules.

## Evaluation model {:#evaluation-model}

A build consists of three phases.

* **Loading phase**. First, load and evaluate all extensions and all `BUILD`
  files that are needed for the build. The execution of the `BUILD` files simply
  instantiates rules (each time a rule is called, it gets added to a graph).
  This is where macros are evaluated.

* **Analysis phase**. The code of the rules is executed (their `implementation`
  function), and actions are instantiated. An action describes how to generate
  a set of outputs from a set of inputs, such as "run gcc on hello.c and get
  hello.o". You must list explicitly which files will be generated before
  executing the actual commands. In other words, the analysis phase takes
  the graph generated by the loading phase and generates an action graph.

* **Execution phase**. Actions are executed, when at least one of their outputs is
  required. If a file is missing or if a command fails to generate one output,
  the build fails. Tests are also run during this phase.

Bazel uses parallelism to read, parse and evaluate the `.bzl` files and `BUILD`
files. A file is read at most once per build and the result of the evaluation is
cached and reused. A file is evaluated only once all its dependencies (`load()`
statements) have been resolved. By design, loading a `.bzl` file has no visible
side-effect, it only defines values and functions.

Bazel tries to be clever: it uses dependency analysis to know which files must
be loaded, which rules must be analyzed, and which actions must be executed. For
example, if a rule generates actions that you don't need for the current build,
they will not be executed.

## Creating extensions

* [Create your first macro](/rules/macro-tutorial) in order to reuse some code.
  Then [learn more about macros](/extending/macros) and [using them to create
  "custom verbs"](/rules/verbs-tutorial).

* [Follow the rules tutorial](/rules/rules-tutorial) to get started with rules.
  Next, you can read more about the [rules concepts](/extending/rules).

The two links below will be very useful when writing your own extensions. Keep
them within reach:

* The [API reference](/rules/lib)

* [Examples](https://github.com/bazelbuild/examples/tree/master/rules)

## Going further

In addition to [macros](/extending/macros) and [rules](/extending/rules), you
may want to write [aspects](/extending/aspects) and [repository
rules](/external/repo).

* Use [Buildifier](https://github.com/bazelbuild/buildtools){: .external}
  consistently to format and lint your code.

* Follow the [`.bzl` style guide](/rules/bzl-style).

* [Test](/rules/testing) your code.

* [Generate documentation](https://skydoc.bazel.build/) to help your users.

* [Optimize the performance](/rules/performance) of your code.

* [Deploy](/rules/deploying) your extensions to other people.


Project: /_project.yaml
Book: /_book.yaml

# Aspects

{% include "_buttons.html" %}

This page explains the basics and benefits of using
[aspects](/rules/lib/globals/bzl#aspect) and provides simple and advanced
examples.

Aspects allow augmenting build dependency graphs with additional information
and actions. Some typical scenarios when aspects can be useful:

*   IDEs that integrate Bazel can use aspects to collect information about the
    project.
*   Code generation tools can leverage aspects to execute on their inputs in
    *target-agnostic* manner. As an example, `BUILD` files can specify a hierarchy
    of [protobuf](https://developers.google.com/protocol-buffers/) library
    definitions, and language-specific rules can use aspects to attach
    actions generating protobuf support code for a particular language.

## Aspect basics

`BUILD` files provide a description of a project’s source code: what source
files are part of the project, what artifacts (_targets_) should be built from
those files, what the dependencies between those files are, etc. Bazel uses
this information to perform a build, that is, it figures out the set of actions
needed to produce the artifacts (such as running compiler or linker) and
executes those actions. Bazel accomplishes this by constructing a _dependency
graph_ between targets and visiting this graph to collect those actions.

Consider the following `BUILD` file:

```python
java_library(name = 'W', ...)
java_library(name = 'Y', deps = [':W'], ...)
java_library(name = 'Z', deps = [':W'], ...)
java_library(name = 'Q', ...)
java_library(name = 'T', deps = [':Q'], ...)
java_library(name = 'X', deps = [':Y',':Z'], runtime_deps = [':T'], ...)
```

This `BUILD` file defines a dependency graph shown in the following figure:

![Build graph](/rules/build-graph.png "Build graph")

**Figure 1.** `BUILD` file dependency graph.

Bazel analyzes this dependency graph by calling an implementation function of
the corresponding [rule](/extending/rules) (in this case "java_library") for every
target in the above example. Rule implementation functions generate actions that
build artifacts, such as `.jar` files, and pass information, such as locations
and names of those artifacts, to the reverse dependencies of those targets in
[providers](/extending/rules#providers).

Aspects are similar to rules in that they have an implementation function that
generates actions and returns providers. However, their power comes from
the way the dependency graph is built for them. An aspect has an implementation
and a list of all attributes it propagates along. Consider an aspect A that
propagates along attributes named "deps". This aspect can be applied to
a target X, yielding an aspect application node A(X). During its application,
aspect A is applied recursively to all targets that X refers to in its "deps"
attribute (all attributes in A's propagation list).

Thus a single act of applying aspect A to a target X yields a "shadow graph" of
the original dependency graph of targets shown in the following figure:

![Build Graph with Aspect](/rules/build-graph-aspects.png "Build graph with aspects")

**Figure 2.** Build graph with aspects.

The only edges that are shadowed are the edges along the attributes in
the propagation set, thus the `runtime_deps` edge is not shadowed in this
example. An aspect implementation function is then invoked on all nodes in
the shadow graph similar to how rule implementations are invoked on the nodes
of the original graph.

## Simple example

This example demonstrates how to recursively print the source files for a
rule and all of its dependencies that have a `deps` attribute. It shows
an aspect implementation, an aspect definition, and how to invoke the aspect
from the Bazel command line.

```python
def _print_aspect_impl(target, ctx):
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the files that make up the sources and
        # print their paths.
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                print(f.path)
    return []

print_aspect = aspect(
    implementation = _print_aspect_impl,
    attr_aspects = ['deps'],
    required_providers = [CcInfo],
)
```

Let's break the example up into its parts and examine each one individually.

### Aspect definition

```python
print_aspect = aspect(
    implementation = _print_aspect_impl,
    attr_aspects = ['deps'],
    required_providers = [CcInfo],
)
```
Aspect definitions are similar to rule definitions, and defined using
the [`aspect`](/rules/lib/globals/bzl#aspect) function.

Just like a rule, an aspect has an implementation function which in this case is
``_print_aspect_impl``.

``attr_aspects`` is a list of rule attributes along which the aspect propagates.
In this case, the aspect will propagate along the ``deps`` attribute of the
rules that it is applied to.

Another common argument for `attr_aspects` is `['*']` which would propagate the
aspect to all attributes of a rule.

``required_providers`` is a list of providers that allows the aspect to limit
its propagation to only the targets whose rules advertise its required
providers. For more details consult
[the documentation of the aspect function](/rules/lib/globals/bzl#aspect).
In this case, the aspect will only apply on targets that declare `CcInfo`
provider.

### Aspect implementation

```python
def _print_aspect_impl(target, ctx):
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the files that make up the sources and
        # print their paths.
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                print(f.path)
    return []
```

Aspect implementation functions are similar to the rule implementation
functions. They return [providers](/extending/rules#providers), can generate
[actions](/extending/rules#actions), and take two arguments:

*  `target`: the [target](/rules/lib/builtins/Target) the aspect is being applied to.
*   `ctx`: [`ctx`](/rules/lib/builtins/ctx) object that can be used to access attributes
    and generate outputs and actions.

The implementation function can access the attributes of the target rule via
[`ctx.rule.attr`](/rules/lib/builtins/ctx#rule). It can examine providers that are
provided by the target to which it is applied (via the `target` argument).

Aspects are required to return a list of providers. In this example, the aspect
does not provide anything, so it returns an empty list.

### Invoking the aspect using the command line

The simplest way to apply an aspect is from the command line using the
[`--aspects`](/reference/command-line-reference#flag--aspects)
argument. Assuming the aspect above were defined in a file named `print.bzl`
this:

```bash
bazel build //MyExample:example --aspects print.bzl%print_aspect
```

would apply the `print_aspect` to the target `example` and all of the
target rules that are accessible recursively via the `deps` attribute.

The `--aspects` flag takes one argument, which is a specification of the aspect
in the format `<extension file label>%<aspect top-level name>`.

## Advanced example

The following example demonstrates using an aspect from a target rule
that counts files in targets, potentially filtering them by extension.
It shows how to use a provider to return values, how to use parameters to pass
an argument into an aspect implementation, and how to invoke an aspect from a rule.

Note: Aspects added in rules' attributes are called *rule-propagated aspects* as
opposed to *command-line aspects* that are specified using the ``--aspects``
flag.

`file_count.bzl` file:

```python
FileCountInfo = provider(
    fields = {
        'count' : 'number of files'
    }
)

def _file_count_aspect_impl(target, ctx):
    count = 0
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the sources counting files
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                if ctx.attr.extension == '*' or ctx.attr.extension == f.extension:
                    count = count + 1
    # Get the counts from our dependencies.
    for dep in ctx.rule.attr.deps:
        count = count + dep[FileCountInfo].count
    return [FileCountInfo(count = count)]

file_count_aspect = aspect(
    implementation = _file_count_aspect_impl,
    attr_aspects = ['deps'],
    attrs = {
        'extension' : attr.string(values = ['*', 'h', 'cc']),
    }
)

def _file_count_rule_impl(ctx):
    for dep in ctx.attr.deps:
        print(dep[FileCountInfo].count)

file_count_rule = rule(
    implementation = _file_count_rule_impl,
    attrs = {
        'deps' : attr.label_list(aspects = [file_count_aspect]),
        'extension' : attr.string(default = '*'),
    },
)
```

`BUILD.bazel` file:

```python
load('//:file_count.bzl', 'file_count_rule')

cc_library(
    name = 'lib',
    srcs = [
        'lib.h',
        'lib.cc',
    ],
)

cc_binary(
    name = 'app',
    srcs = [
        'app.h',
        'app.cc',
        'main.cc',
    ],
    deps = ['lib'],
)

file_count_rule(
    name = 'file_count',
    deps = ['app'],
    extension = 'h',
)
```

### Aspect definition

```python
file_count_aspect = aspect(
    implementation = _file_count_aspect_impl,
    attr_aspects = ['deps'],
    attrs = {
        'extension' : attr.string(values = ['*', 'h', 'cc']),
    }
)
```

This example shows how the aspect propagates through the ``deps`` attribute.

``attrs`` defines a set of attributes for an aspect. Public aspect attributes
define parameters and can only be of types ``bool``, ``int`` or ``string``.
For rule-propagated aspects, ``int`` and ``string`` parameters must have
``values`` specified on them. This example has a parameter called ``extension``
that is allowed to have '``*``', '``h``', or '``cc``' as a value.

For rule-propagated aspects, parameter values are taken from the rule requesting
the aspect, using the attribute of the rule that has the same name and type.
(see the definition of ``file_count_rule``).

For command-line aspects, the parameters values can be passed using
[``--aspects_parameters``](/reference/command-line-reference#flag--aspects_parameters)
flag. The ``values`` restriction of ``int`` and ``string`` parameters may be
omitted.

Aspects are also allowed to have private attributes of types ``label`` or
``label_list``. Private label attributes can be used to specify dependencies on
tools or libraries that are needed for actions generated by aspects. There is not
a private attribute defined in this example, but the following code snippet
demonstrates how you could pass in a tool to an aspect:

```python
...
    attrs = {
        '_protoc' : attr.label(
            default = Label('//tools:protoc'),
            executable = True,
            cfg = "exec"
        )
    }
...
```

### Aspect implementation

```python
FileCountInfo = provider(
    fields = {
        'count' : 'number of files'
    }
)

def _file_count_aspect_impl(target, ctx):
    count = 0
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the sources counting files
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                if ctx.attr.extension == '*' or ctx.attr.extension == f.extension:
                    count = count + 1
    # Get the counts from our dependencies.
    for dep in ctx.rule.attr.deps:
        count = count + dep[FileCountInfo].count
    return [FileCountInfo(count = count)]
```

Just like a rule implementation function, an aspect implementation function
returns a struct of providers that are accessible to its dependencies.

In this example, the ``FileCountInfo`` is defined as a provider that has one
field ``count``. It is best practice to explicitly define the fields of a
provider using the ``fields`` attribute.

The set of providers for an aspect application A(X) is the union of providers
that come from the implementation of a rule for target X and from the
implementation of aspect A. The providers that a rule implementation propagates
are created and frozen before aspects are applied and cannot be modified from an
aspect. It is an error if a target and an aspect that is applied to it each
provide a provider with the same type, with the exceptions of
[`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo)
(which is merged, so long as the
rule and aspect specify different output groups) and
[`InstrumentedFilesInfo`](/rules/lib/providers/InstrumentedFilesInfo)
(which is taken from the aspect). This means that aspect implementations may
never return [`DefaultInfo`](/rules/lib/providers/DefaultInfo).

The parameters and private attributes are passed in the attributes of the
``ctx``. This example references the ``extension`` parameter and determines
what files to count.

For returning providers, the values of attributes along which
the aspect is propagated (from the `attr_aspects` list) are replaced with
the results of an application of the aspect to them. For example, if target
X has Y and Z in its deps, `ctx.rule.attr.deps` for A(X) will be [A(Y), A(Z)].
In this example, ``ctx.rule.attr.deps`` are Target objects that are the
results of applying the aspect to the 'deps' of the original target to which
the aspect has been applied.

In the example, the aspect accesses the ``FileCountInfo`` provider from the
target's dependencies to accumulate the total transitive number of files.

### Invoking the aspect from a rule

```python
def _file_count_rule_impl(ctx):
    for dep in ctx.attr.deps:
        print(dep[FileCountInfo].count)

file_count_rule = rule(
    implementation = _file_count_rule_impl,
    attrs = {
        'deps' : attr.label_list(aspects = [file_count_aspect]),
        'extension' : attr.string(default = '*'),
    },
)
```

The rule implementation demonstrates how to access the ``FileCountInfo``
via the ``ctx.attr.deps``.

The rule definition demonstrates how to define a parameter (``extension``)
and give it a default value (``*``). Note that having a default value that
was not one of '``cc``', '``h``', or '``*``' would be an error due to the
restrictions placed on the parameter in the aspect definition.

### Invoking an aspect through a target rule

```python
load('//:file_count.bzl', 'file_count_rule')

cc_binary(
    name = 'app',
...
)

file_count_rule(
    name = 'file_count',
    deps = ['app'],
    extension = 'h',
)
```

This demonstrates how to pass the ``extension`` parameter into the aspect
via the rule. Since the ``extension`` parameter has a default value in the
rule implementation, ``extension`` would be considered an optional parameter.

When the ``file_count`` target is built, our aspect will be evaluated for
itself, and all of the targets accessible recursively via ``deps``.

## References

* [`aspect` API reference](/rules/lib/globals/bzl#aspect)


Project: /_project.yaml
Book: /_book.yaml

# Configurations

<devsite-mathjax config="TeX-AMS-MML_SVG"></devsite-mathjax>

{% include "_buttons.html" %}

This page covers the benefits and basic usage of Starlark configurations,
Bazel's API for customizing how your project builds. It includes how to define
build settings and provides examples.

This makes it possible to:

*   define custom flags for your project, obsoleting the need for
     [`--define`](/docs/configurable-attributes#custom-keys)
*   write
    [transitions](/rules/lib/builtins/transition#transition) to configure deps in
    different configurations than their parents
    (such as `--compilation_mode=opt` or `--cpu=arm`)
*   bake better defaults into rules (such as automatically build `//my:android_app`
    with a specified SDK)

and more, all completely from .bzl files (no Bazel release required). See the
`bazelbuild/examples` repo for
[examples](https://github.com/bazelbuild/examples/tree/HEAD/configurations){: .external}.

## User-defined build settings {:#user-defined-build-settings}

A build setting is a single piece of
[configuration](/extending/rules#configurations)
information. Think of a configuration as a key/value map. Setting `--cpu=ppc`
and `--copt="-DFoo"` produces a configuration that looks like
`{cpu: ppc, copt: "-DFoo"}`. Each entry is a build setting.

Traditional flags like `cpu` and `copt` are native settings —
their keys are defined and their values are set inside native bazel java code.
Bazel users can only read and write them via the command line
and other APIs maintained natively. Changing native flags, and the APIs
that expose them, requires a bazel release. User-defined build
settings are defined in `.bzl` files (and thus, don't need a bazel release to
register changes). They also can be set via the command line
(if they're designated as `flags`, see more below), but can also be
set via [user-defined transitions](#user-defined-transitions).

### Defining build settings {:#defining-build-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/basic_build_setting){: .external}

#### The `build_setting` `rule()` parameter {:#rule-parameter}

Build settings are rules like any other rule and are differentiated using the
Starlark `rule()` function's `build_setting`
[attribute](/rules/lib/globals/bzl#rule.build_setting).

```python
# example/buildsettings/build_settings.bzl
string_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

The `build_setting` attribute takes a function that designates the type of the
build setting. The type is limited to a set of basic Starlark types like
`bool` and `string`. See the `config` module
[documentation](/rules/lib/toplevel/config)  for details. More complicated typing can be
done in the rule's implementation function. More on this below.

The `config` module's functions takes an optional boolean parameter, `flag`,
which is set to false by default. if `flag` is set to true, the build setting
can be set on the command line by users as well as internally by rule writers
via default values and [transitions](/rules/lib/builtins/transition#transition).
Not all settings should be settable by users. For example, if you as a rule
writer have some debug mode that you'd like to turn on inside test rules,
you don't want to give users the ability to indiscriminately turn on that
feature inside other non-test rules.

#### Using ctx.build_setting_value {:#ctx-build-setting-value}

Like all rules, build setting rules have [implementation functions](/extending/rules#implementation-function).
The basic Starlark-type value of the build settings can be accessed via the
`ctx.build_setting_value` method. This method is only available to
[`ctx`](/rules/lib/builtins/ctx) objects of build setting rules. These implementation
methods can directly forward the build settings value or do additional work on
it, like type checking or more complex struct creation. Here's how you would
implement an `enum`-typed build setting:

```python
# example/buildsettings/build_settings.bzl
TemperatureProvider = provider(fields = ['type'])

temperatures = ["HOT", "LUKEWARM", "ICED"]

def _impl(ctx):
    raw_temperature = ctx.build_setting_value
    if raw_temperature not in temperatures:
        fail(str(ctx.label) + " build setting allowed to take values {"
             + ", ".join(temperatures) + "} but was set to unallowed value "
             + raw_temperature)
    return TemperatureProvider(type = raw_temperature)

temperature = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

Note: if a rule depends on a build setting, it will receive whatever providers
the build setting implementation function returns, like any other dependency.
But all other references to the value of the build setting (such as in transitions)
will see its basic Starlark-typed value, not this post implementation function
value.

#### Defining multi-set string flags {:#multi-set-string-flags}

String settings have an additional `allow_multiple` parameter which allows the
flag to be set multiple times on the command line or in bazelrcs. Their default
value is still set with a string-typed attribute:

```python
# example/buildsettings/build_settings.bzl
allow_multiple_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True, allow_multiple = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "allow_multiple_flag")
allow_multiple_flag(
    name = "roasts",
    build_setting_default = "medium"
)
```

Each setting of the flag is treated as a single value:

```shell
$ bazel build //my/target --//example:roasts=blonde \
    --//example:roasts=medium,dark
```

The above is parsed to `{"//example:roasts": ["blonde", "medium,dark"]}` and
`ctx.build_setting_value` returns the list `["blonde", "medium,dark"]`.

#### Instantiating build settings {:#instantiating-build-settings}

Rules defined with the `build_setting` parameter have an implicit mandatory
`build_setting_default` attribute. This attribute takes on the same type as
declared by the `build_setting` param.

```python
# example/buildsettings/build_settings.bzl
FlavorProvider = provider(fields = ['type'])

def _impl(ctx):
    return FlavorProvider(type = ctx.build_setting_value)

flavor = rule(
    implementation = _impl,
    build_setting = config.string(flag = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "flavor")
flavor(
    name = "favorite_flavor",
    build_setting_default = "APPLE"
)
```

### Predefined settings {:#predefined-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/use_skylib_build_setting){: .external}

The
[Skylib](https://github.com/bazelbuild/bazel-skylib){: .external}
library includes a set of predefined settings you can instantiate without having
to write custom Starlark.

For example, to define a setting that accepts a limited set of string values:

```python
# example/BUILD
load("@bazel_skylib//rules:common_settings.bzl", "string_flag")
string_flag(
    name = "myflag",
    values = ["a", "b", "c"],
    build_setting_default = "a",
)
```

For a complete list, see
[Common build setting rules](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/common_settings.bzl){: .external}.

### Using build settings {:#using-build-settings}

#### Depending on build settings {:#depending-on-build-settings}

If a target would like to read a piece of configuration information, it can
directly depend on the build setting via a regular attribute dependency.

```python
# example/rules.bzl
load("//example/buildsettings:build_settings.bzl", "FlavorProvider")
def _rule_impl(ctx):
    if ctx.attr.flavor[FlavorProvider].type == "ORANGE":
        ...

drink_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "flavor": attr.label()
    }
)
```

```python
# example/BUILD
load("//example:rules.bzl", "drink_rule")
load("//example/buildsettings:build_settings.bzl", "flavor")
flavor(
    name = "favorite_flavor",
    build_setting_default = "APPLE"
)
drink_rule(
    name = "my_drink",
    flavor = ":favorite_flavor",
)
```

Languages may wish to create a canonical set of build settings which all rules
for that language depend on. Though the native concept of `fragments` no longer
exists as a hardcoded object in Starlark configuration world, one way to
translate this concept would be to use sets of common implicit attributes. For
example:

```python
# kotlin/rules.bzl
_KOTLIN_CONFIG = {
    "_compiler": attr.label(default = "//kotlin/config:compiler-flag"),
    "_mode": attr.label(default = "//kotlin/config:mode-flag"),
    ...
}

...

kotlin_library = rule(
    implementation = _rule_impl,
    attrs = dicts.add({
        "library-attr": attr.string()
    }, _KOTLIN_CONFIG)
)

kotlin_binary = rule(
    implementation = _binary_impl,
    attrs = dicts.add({
        "binary-attr": attr.label()
    }, _KOTLIN_CONFIG)

```

#### Using build settings on the command line {:#build-settings-command-line}

Similar to most native flags, you can use the command line to set build settings
[that are marked as flags](#rule-parameter). The build
setting's name is its full target path using `name=value` syntax:

```shell
$ bazel build //my/target --//example:string_flag=some-value # allowed
$ bazel build //my/target --//example:string_flag some-value # not allowed
```

Special boolean syntax is supported:

```shell
$ bazel build //my/target --//example:boolean_flag
$ bazel build //my/target --no//example:boolean_flag
```

#### Using build setting aliases {:#using-build-setting-aliases}

You can set an alias for your build setting target path to make it easier to read
on the command line. Aliases function similarly to native flags and also make use
of the double-dash option syntax.

Set an alias by adding `--flag_alias=ALIAS_NAME=TARGET_PATH`
to your `.bazelrc` . For example, to set an alias to `coffee`:

```shell
# .bazelrc
build --flag_alias=coffee=//experimental/user/starlark_configurations/basic_build_setting:coffee-temp
```

Best Practice: Setting an alias multiple times results in the most recent
one taking precedence. Use unique alias names to avoid unintended parsing results.

To make use of the alias, type it in place of the build setting target path.
With the above example of `coffee` set in the user's `.bazelrc`:

```shell
$ bazel build //my/target --coffee=ICED
```

instead of

```shell
$ bazel build //my/target --//experimental/user/starlark_configurations/basic_build_setting:coffee-temp=ICED
```
Best Practice: While it possible to set aliases on the command line, leaving them
in a `.bazelrc` reduces command line clutter.

### Label-typed build settings {:#label-typed-build-settings}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/label_typed_build_setting){: .external}

Unlike other build settings, label-typed settings cannot be defined using the
`build_setting` rule parameter. Instead, bazel has two built-in rules:
`label_flag` and `label_setting`. These rules forward the providers of the
actual target to which the build setting is set. `label_flag` and
`label_setting` can be read/written by transitions and `label_flag` can be set
by the user like other `build_setting` rules can. Their only difference is they
can't customely defined.

Label-typed settings will eventually replace the functionality of late-bound
defaults. Late-bound default attributes are Label-typed attributes whose
final values can be affected by configuration. In Starlark, this will replace
the [`configuration_field`](/rules/lib/globals/bzl#configuration_field)
 API.

```python
# example/rules.bzl
MyProvider = provider(fields = ["my_field"])

def _dep_impl(ctx):
    return MyProvider(my_field = "yeehaw")

dep_rule = rule(
    implementation = _dep_impl
)

def _parent_impl(ctx):
    if ctx.attr.my_field_provider[MyProvider].my_field == "cowabunga":
        ...

parent_rule = rule(
    implementation = _parent_impl,
    attrs = { "my_field_provider": attr.label() }
)

```

```python
# example/BUILD
load("//example:rules.bzl", "dep_rule", "parent_rule")

dep_rule(name = "dep")

parent_rule(name = "parent", my_field_provider = ":my_field_provider")

label_flag(
    name = "my_field_provider",
    build_setting_default = ":dep"
)
```

### Build settings and select() {:#build-settings-and-select}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/select_on_build_setting){: .external}

Users can configure attributes on build settings by using
 [`select()`](/reference/be/functions#select). Build setting targets can be passed to the `flag_values` attribute of
`config_setting`. The value to match to the configuration is passed as a
`String` then parsed to the type of the build setting for matching.

```python
config_setting(
    name = "my_config",
    flag_values = {
        "//example:favorite_flavor": "MANGO"
    }
)
```

## User-defined transitions {:#user-defined-transitions}

A configuration
[transition](/rules/lib/builtins/transition#transition)
maps the transformation from one configured target to another within the
build graph.

Important: Transitions have [memory and performance impact](#memory-performance-considerations).

### Defining {:#defining}

Transitions define configuration changes between rules. For example, a request
like "compile my dependency for a different CPU than its parent" is handled by a
transition.

Formally, a transition is a function from an input configuration to one or more
output configurations. Most transitions are 1:1 such as "override the input
configuration with `--cpu=ppc`". 1:2+ transitions can also exist but come
with special restrictions.

In Starlark, transitions are defined much like rules, with a defining
`transition()`
[function](/rules/lib/builtins/transition#transition)
and an implementation function.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {"//example:favorite_flavor" : "MINT"}

hot_chocolate_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)
```
The `transition()` function takes in an implementation function, a set of
build settings to read(`inputs`), and a set of build settings to write
(`outputs`). The implementation function has two parameters, `settings` and
`attr`. `settings` is a dictionary {`String`:`Object`} of all settings declared
in the `inputs` parameter to `transition()`.

`attr` is a dictionary of attributes and values of the rule to which the
transition is attached. When attached as an
[outgoing edge transition](#outgoing-edge-transitions), the values of these
attributes are all configured post-select() resolution. When attached as
an [incoming edge transition](#incoming-edge-transitions), `attr` does not
include any attributes that use a selector to resolve their value. If an
incoming edge transition on `--foo` reads attribute `bar` and then also
selects on `--foo` to set attribute `bar`, then there's a chance for the
incoming edge transition to read the wrong value of `bar` in the transition.

Note: Since transitions are attached to rule definitions and `select()`s are
attached to rule instantiations (such as targets), errors related to `select()`s on
read attributes will pop up when users create targets rather than when rules are
written. It may be worth taking extra care to communicate to rule users which
attributes they should be wary of selecting on or taking other precautions.

The implementation function must return a dictionary (or list of
dictionaries, in the case of
transitions with multiple output configurations)
of new build settings values to apply. The returned dictionary keyset(s) must
contain exactly the set of build settings passed to the `outputs`
parameter of the transition function. This is true even if a build setting is
not actually changed over the course of the transition - its original value must
be explicitly passed through in the returned dictionary.

### Defining 1:2+ transitions {:#defining-1-2-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/multi_arch_binary){: .external}

[Outgoing edge transition](#outgoing-edge-transitions) can map a single input
configuration to two or more output configurations. This is useful for defining
rules that bundle multi-architecture code.

1:2+ transitions are defined by returning a list of dictionaries in the
transition implementation function.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return [
        {"//example:favorite_flavor" : "LATTE"},
        {"//example:favorite_flavor" : "MOCHA"},
    ]

coffee_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)
```
They can also set custom keys that the rule implementation function can use to
read individual dependencies:

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {
        "Apple deps": {"//command_line_option:cpu": "ppc"},
        "Linux deps": {"//command_line_option:cpu": "x86"},
    }

multi_arch_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
)
```

### Attaching transitions {:#attaching-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/attaching_transitions_to_rules){: .external}

Transitions can be attached in two places: incoming edges and outgoing edges.
Effectively this means rules can transition their own configuration (incoming
edge transition) and transition their dependencies' configurations (outgoing
edge transition).

NOTE: There is currently no way to attach Starlark transitions to native rules.
If you need to do this, contact
bazel-discuss@googlegroups.com
for help with figuring out workarounds.

### Incoming edge transitions {:#incoming-edge-transitions}

Incoming edge transitions are activated by attaching a `transition` object
(created by `transition()`) to `rule()`'s `cfg` parameter:

```python
# example/rules.bzl
load("example/transitions:transitions.bzl", "hot_chocolate_transition")
drink_rule = rule(
    implementation = _impl,
    cfg = hot_chocolate_transition,
    ...
```

Incoming edge transitions must be 1:1 transitions.

### Outgoing edge transitions {:#outgoing-edge-transitions}

Outgoing edge transitions are activated by attaching a `transition` object
(created by `transition()`) to an attribute's `cfg` parameter:

```python
# example/rules.bzl
load("example/transitions:transitions.bzl", "coffee_transition")
drink_rule = rule(
    implementation = _impl,
    attrs = { "dep": attr.label(cfg = coffee_transition)}
    ...
```
Outgoing edge transitions can be 1:1 or 1:2+.

See [Accessing attributes with transitions](#accessing-attributes-with-transitions)
for how to read these keys.

### Transitions on native options {:#transitions-native-options}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/transition_on_native_flag){: .external}

Starlark transitions can also declare reads and writes on native build
configuration options via a special prefix to the option name.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {"//command_line_option:cpu": "k8"}

cpu_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
```

#### Unsupported native options {:#unsupported-native-options}

Bazel doesn't support transitioning on `--define` with
`"//command_line_option:define"`. Instead, use a custom
[build setting](#user-defined-build-settings). In general, new usages of
`--define` are discouraged in favor of build settings.

Bazel doesn't support transitioning on `--config`. This is because `--config` is
an "expansion" flag that expands to other flags.

Crucially, `--config` may include flags that don't affect build configuration,
such as
[`--spawn_strategy`](/docs/user-manual#spawn-strategy)
. Bazel, by design, can't bind such flags to individual targets. This means
there's no coherent way to apply them in transitions.

As a workaround, you can explicitly itemize the flags that *are* part of
the configuration in your transition. This requires maintaining the `--config`'s
expansion in two places, which is a known UI blemish.

### Transitions on allow multiple build settings {:#transitions-multiple-build-settings}

When setting build settings that
[allow multiple values](#defining-multi-set-string-flags), the value of the
setting must be set with a list.

```python
# example/buildsettings/build_settings.bzl
string_flag = rule(
    implementation = _impl,
    build_setting = config.string(flag = True, allow_multiple = True)
)
```

```python
# example/BUILD
load("//example/buildsettings:build_settings.bzl", "string_flag")
string_flag(name = "roasts", build_setting_default = "medium")
```

```python
# example/transitions/rules.bzl
def _transition_impl(settings, attr):
    # Using a value of just "dark" here will throw an error
    return {"//example:roasts" : ["dark"]},

coffee_transition = transition(
    implementation = _transition_impl,
    inputs = [],
    outputs = ["//example:roasts"]
)
```

### No-op transitions {:#no-op-transitions}

If a transition returns `{}`, `[]`, or `None`, this is shorthand for keeping all
settings at their original values. This can be more convenient than explicitly
setting each output to itself.

```python
# example/transitions/transitions.bzl
def _impl(settings, attr):
    _ignore = (attr)
    if settings["//example:already_chosen"] is True:
      return {}
    return {
      "//example:favorite_flavor": "dark chocolate",
      "//example:include_marshmallows": "yes",
      "//example:desired_temperature": "38C",
    }

hot_chocolate_transition = transition(
    implementation = _impl,
    inputs = ["//example:already_chosen"],
    outputs = [
        "//example:favorite_flavor",
        "//example:include_marshmallows",
        "//example:desired_temperature",
    ]
)
```

### Accessing attributes with transitions {:#accessing-attributes-with-transitions}

[End to end example](https://github.com/bazelbuild/examples/tree/HEAD/configurations/read_attr_in_transition){: .external}

When [attaching a transition to an outgoing edge](#outgoing-edge-transitions)
(regardless of whether the transition is a 1:1 or 1:2+ transition), `ctx.attr` is forced to be a list
if it isn't already. The order of elements in this list is unspecified.


```python
# example/transitions/rules.bzl
def _transition_impl(settings, attr):
    return {"//example:favorite_flavor" : "LATTE"},

coffee_transition = transition(
    implementation = _transition_impl,
    inputs = [],
    outputs = ["//example:favorite_flavor"]
)

def _rule_impl(ctx):
    # Note: List access even though "dep" is not declared as list
    transitioned_dep = ctx.attr.dep[0]

    # Note: Access doesn't change, other_deps was already a list
    for other_dep in ctx.attr.other_deps:
      # ...


coffee_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "dep": attr.label(cfg = coffee_transition)
        "other_deps": attr.label_list(cfg = coffee_transition)
    })
```

If the transition is `1:2+` and sets custom keys, `ctx.split_attr` can be used
to read individual deps for each key:

```python
# example/transitions/rules.bzl
def _impl(settings, attr):
    _ignore = (settings, attr)
    return {
        "Apple deps": {"//command_line_option:cpu": "ppc"},
        "Linux deps": {"//command_line_option:cpu": "x86"},
    }

multi_arch_transition = transition(
    implementation = _impl,
    inputs = [],
    outputs = ["//command_line_option:cpu"]
)

def _rule_impl(ctx):
    apple_dep = ctx.split_attr.dep["Apple deps"]
    linux_dep = ctx.split_attr.dep["Linux deps"]
    # ctx.attr has a list of all deps for all keys. Order is not guaranteed.
    all_deps = ctx.attr.dep

multi_arch_rule = rule(
    implementation = _rule_impl,
    attrs = {
        "dep": attr.label(cfg = multi_arch_transition)
    })
```

See [complete example](https://github.com/bazelbuild/examples/tree/main/configurations/multi_arch_binary)
here.

## Integration with platforms and toolchains {:#integration-platforms-toolchains}

Many native flags today, like `--cpu` and `--crosstool_top` are related to
toolchain resolution. In the future, explicit transitions on these types of
flags will likely be replaced by transitioning on the
[target platform](/extending/platforms).

## Memory and performance considerations {:#memory-performance-considerations}

Adding transitions, and therefore new configurations, to your build comes at a
cost: larger build graphs, less comprehensible build graphs, and slower
builds. It's worth considering these costs when considering
using transitions in your build rules. Below is an example of how a transition
might create exponential growth of your build graph.

### Badly behaved builds: a case study {:#badly-behaved-builds}

![Scalability graph](/rules/scalability-graph.png "Scalability graph")

**Figure 1.** Scalability graph showing a top level target and its dependencies.

This graph shows a top level target, `//pkg:app`, which depends on two targets, a
`//pkg:1_0` and `//pkg:1_1`. Both these targets depend on two targets, `//pkg:2_0` and
`//pkg:2_1`. Both these targets depend on two targets, `//pkg:3_0` and `//pkg:3_1`.
This continues on until `//pkg:n_0` and `//pkg:n_1`, which both depend on a single
target, `//pkg:dep`.

Building `//pkg:app` requires \\(2n+2\\) targets:

* `//pkg:app`
* `//pkg:dep`
* `//pkg:i_0` and `//pkg:i_1` for \\(i\\) in \\([1..n]\\)

Imagine you [implement](#user-defined-build-settings) a flag
`--//foo:owner=<STRING>` and `//pkg:i_b` applies

    depConfig = myConfig + depConfig.owner="$(myConfig.owner)$(b)"

In other words, `//pkg:i_b` appends `b` to the old value of `--owner` for all
its deps.

This produces the following [configured targets](/reference/glossary#configured-target):

```
//pkg:app                              //foo:owner=""
//pkg:1_0                              //foo:owner=""
//pkg:1_1                              //foo:owner=""
//pkg:2_0 (via //pkg:1_0)              //foo:owner="0"
//pkg:2_0 (via //pkg:1_1)              //foo:owner="1"
//pkg:2_1 (via //pkg:1_0)              //foo:owner="0"
//pkg:2_1 (via //pkg:1_1)              //foo:owner="1"
//pkg:3_0 (via //pkg:1_0 → //pkg:2_0)  //foo:owner="00"
//pkg:3_0 (via //pkg:1_0 → //pkg:2_1)  //foo:owner="01"
//pkg:3_0 (via //pkg:1_1 → //pkg:2_0)  //foo:owner="10"
//pkg:3_0 (via //pkg:1_1 → //pkg:2_1)  //foo:owner="11"
...
```

`//pkg:dep` produces \\(2^n\\) configured targets: `config.owner=`
"\\(b_0b_1...b_n\\)" for all \\(b_i\\) in \\(\{0,1\}\\).

This makes the build graph exponentially larger than the target graph, with
corresponding memory and performance consequences.

TODO: Add strategies for measurement and mitigation of these issues.

## Further reading {:#further-reading}

For more details on modifying build configurations, see:

 * [Starlark Build Configuration](https://docs.google.com/document/d/1vc8v-kXjvgZOdQdnxPTaV0rrLxtP2XwnD2tAZlYJOqw/edit?usp=sharing){: .external}
 * [Bazel Configurability Roadmap](https://bazel.build/community/roadmaps-configurability){: .external}
 * Full [set](https://github.com/bazelbuild/examples/tree/HEAD/configurations){: .external} of end to end examples


Project: /_project.yaml
Book: /_book.yaml

# Platforms

{% include "_buttons.html" %}

Bazel can build and test code on a variety of hardware, operating systems, and
system configurations, using many different versions of build tools such as
linkers and compilers. To help manage this complexity, Bazel has a concept of
*constraints* and *platforms*. A constraint is a dimension in which build or
production environments may differ, such as CPU architecture, the presence or
absence of a GPU, or the version of a system-installed compiler. A platform is a
named collection of choices for these constraints, representing the particular
resources that are available in some environment.

Modeling the environment as a platform helps Bazel to automatically select the
appropriate
[toolchains](/extending/toolchains)
for build actions. Platforms can also be used in combination with the
[config_setting](/reference/be/general#config_setting)
rule to write [configurable attributes](/docs/configurable-attributes).

Bazel recognizes three roles that a platform may serve:

*  **Host** - the platform on which Bazel itself runs.
*  **Execution** - a platform on which build tools execute build actions to
   produce intermediate and final outputs.
*  **Target** - a platform on which a final output resides and executes.

Bazel supports the following build scenarios regarding platforms:

*  **Single-platform builds** (default) - host, execution, and target platforms
   are the same. For example, building a Linux executable on Ubuntu running on
   an Intel x64 CPU.

*  **Cross-compilation builds** - host and execution platforms are the same, but
   the target platform is different. For example, building an iOS app on macOS
   running on a MacBook Pro.

*  **Multi-platform builds** - host, execution, and target platforms are all
   different.

Tip: for detailed instructions on migrating your project to platforms, see
[Migrating to Platforms](/concepts/platforms).

## Defining constraints and platforms {:#constraints-platforms}

The space of possible choices for platforms is defined by using the
[`constraint_setting`][constraint_setting] and
[`constraint_value`][constraint_value] rules within `BUILD` files.
`constraint_setting` creates a new dimension, while
`constraint_value` creates a new value for a given dimension; together they
effectively define an enum and its possible values. For example, the following
snippet of a `BUILD` file introduces a constraint for the system's glibc version
with two possible values.

[constraint_setting]: /reference/be/platforms-and-toolchains#constraint_setting
[constraint_value]: /reference/be/platforms-and-toolchains#constraint_value

```python
constraint_setting(name = "glibc_version")

constraint_value(
    name = "glibc_2_25",
    constraint_setting = ":glibc_version",
)

constraint_value(
    name = "glibc_2_26",
    constraint_setting = ":glibc_version",
)
```

Constraints and their values may be defined across different packages in the
workspace. They are referenced by label and subject to the usual visibility
controls. If visibility allows, you can extend an existing constraint setting by
defining your own value for it.

The [`platform`](/reference/be/platforms-and-toolchains#platform) rule introduces a new platform with
certain choices of constraint values. The
following creates a platform named `linux_x86`, and says that it describes any
environment that runs a Linux operating system on an x86_64 architecture with a
glibc version of 2.25. (See below for more on Bazel's built-in constraints.)

```python
platform(
    name = "linux_x86",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
        ":glibc_2_25",
    ],
)
```

Note: It is an error for a platform to specify more than one value of the
same constraint setting, such as `@platforms//cpu:x86_64` and
`@platforms//cpu:arm` for `@platforms//cpu:cpu`.

## Generally useful constraints and platforms {:#useful-constraints-platforms}

To keep the ecosystem consistent, Bazel team maintains a repository with
constraint definitions for the most popular CPU architectures and operating
systems. These are all located in
[https://github.com/bazelbuild/platforms](https://github.com/bazelbuild/platforms){: .external}.

Bazel ships with the following special platform definition:
`@platforms//host` (aliased as `@bazel_tools//tools:host_platform`). This is the
autodetected host platform value -
represents autodetected platform for the system Bazel is running on.

## Specifying a platform for a build {:#specifying-build-platform}

You can specify the host and target platforms for a build using the following
command-line flags:

*  `--host_platform` - defaults to `@bazel_tools//tools:host_platform`
   *  This target is aliased to `@platforms//host`, which is backed by a repo
      rule that detects the host OS and CPU and writes the platform target.
   *  There's also `@platforms//host:constraints.bzl`, which exposes
      an array called `HOST_CONSTRAINTS`, which can be used in other BUILD and
      Starlark files.
*  `--platforms` - defaults to the host platform
   *  This means that when no other flags are set,
      `@platforms//host` is the target platform.
   *  If `--host_platform` is set and not `--platforms`, the value of
      `--host_platform` is both the host and target platform.

## Skipping incompatible targets {:#skipping-incompatible-targets}

When building for a specific target platform it is often desirable to skip
targets that will never work on that platform. For example, your Windows device
driver is likely going to generate lots of compiler errors when building on a
Linux machine with `//...`. Use the
[`target_compatible_with`](/reference/be/common-definitions#common.target_compatible_with)
attribute to tell Bazel what target platform constraints your code has.

The simplest use of this attribute restricts a target to a single platform.
The target will not be built for any platform that doesn't satisfy all of the
constraints. The following example restricts `win_driver_lib.cc` to 64-bit
Windows.

```python
cc_library(
    name = "win_driver_lib",
    srcs = ["win_driver_lib.cc"],
    target_compatible_with = [
        "@platforms//cpu:x86_64",
        "@platforms//os:windows",
    ],
)
```

`:win_driver_lib` is *only* compatible for building with 64-bit Windows and
incompatible with all else. Incompatibility is transitive. Any targets
that transitively depend on an incompatible target are themselves considered
incompatible.

### When are targets skipped? {:#when-targets-skipped}

Targets are skipped when they are considered incompatible and included in the
build as part of a target pattern expansion. For example, the following two
invocations skip any incompatible targets found in a target pattern expansion.

```console
$ bazel build --platforms=//:myplatform //...
```

```console
$ bazel build --platforms=//:myplatform //:all
```

Incompatible tests in a [`test_suite`](/reference/be/general#test_suite) are
similarly skipped if the `test_suite` is specified on the command line with
[`--expand_test_suites`](/reference/command-line-reference#flag--expand_test_suites).
In other words, `test_suite` targets on the command line behave like `:all` and
`...`. Using `--noexpand_test_suites` prevents expansion and causes
`test_suite` targets with incompatible tests to also be incompatible.

Explicitly specifying an incompatible target on the command line results in an
error message and a failed build.

```console
$ bazel build --platforms=//:myplatform //:target_incompatible_with_myplatform
...
ERROR: Target //:target_incompatible_with_myplatform is incompatible and cannot be built, but was explicitly requested.
...
FAILED: Build did NOT complete successfully
```

Incompatible explicit targets are silently skipped if
`--skip_incompatible_explicit_targets` is enabled.

### More expressive constraints {:#expressive-constraints}

For more flexibility in expressing constraints, use the
`@platforms//:incompatible`
[`constraint_value`](/reference/be/platforms-and-toolchains#constraint_value)
that no platform satisfies.

Use [`select()`](/reference/be/functions#select) in combination with
`@platforms//:incompatible` to express more complicated restrictions. For
example, use it to implement basic OR logic. The following marks a library
compatible with macOS and Linux, but no other platforms.

Note: An empty constraints list is equivalent to "compatible with everything".

```python
cc_library(
    name = "unixish_lib",
    srcs = ["unixish_lib.cc"],
    target_compatible_with = select({
        "@platforms//os:osx": [],
        "@platforms//os:linux": [],
        "//conditions:default": ["@platforms//:incompatible"],
    }),
)
```

The above can be interpreted as follows:

1. When targeting macOS, the target has no constraints.
2. When targeting Linux, the target has no constraints.
3. Otherwise, the target has the `@platforms//:incompatible` constraint. Because
   `@platforms//:incompatible` is not part of any platform, the target is
   deemed incompatible.

To make your constraints more readable, use
[skylib](https://github.com/bazelbuild/bazel-skylib){: .external}'s
[`selects.with_or()`](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/selects_doc.md#selectswith_or){: .external}.

You can express inverse compatibility in a similar way. The following example
describes a library that is compatible with everything _except_ for ARM.

```python
cc_library(
    name = "non_arm_lib",
    srcs = ["non_arm_lib.cc"],
    target_compatible_with = select({
        "@platforms//cpu:arm": ["@platforms//:incompatible"],
        "//conditions:default": [],
    }),
)
```

### Detecting incompatible targets using `bazel cquery` {:#cquery-incompatible-target-detection}

You can use the
[`IncompatiblePlatformProvider`](/rules/lib/providers/IncompatiblePlatformProvider)
in `bazel cquery`'s [Starlark output
format](/query/cquery#output-format-definition) to distinguish
incompatible targets from compatible ones.

This can be used to filter out incompatible targets. The example below will
only print the labels for targets that are compatible. Incompatible targets are
not printed.

```console
$ cat example.cquery

def format(target):
  if "IncompatiblePlatformProvider" not in providers(target):
    return target.label
  return ""


$ bazel cquery //... --output=starlark --starlark:file=example.cquery
```

### Known Issues

Incompatible targets [ignore visibility
restrictions](https://github.com/bazelbuild/bazel/issues/16044).


Project: /_project.yaml
Book: /_book.yaml

# Execution Groups

{% include "_buttons.html" %}

Execution groups allow for multiple execution platforms within a single target.
Each execution group has its own [toolchain](/extending/toolchains) dependencies and
performs its own [toolchain resolution](/extending/toolchains#toolchain-resolution).

## Current status {:#current-status}

Execution groups for certain natively declared actions, like `CppLink`, can be
used inside `exec_properties` to set per-action, per-target execution
requirements. For more details, see the
[Default execution groups](#exec-groups-for-native-rules) section.

## Background {:#background}

Execution groups allow the rule author to define sets of actions, each with a
potentially different execution platform. Multiple execution platforms can allow
actions to execution differently, for example compiling an iOS app on a remote
(linux) worker and then linking/code signing on a local mac worker.

Being able to define groups of actions also helps alleviate the usage of action
mnemonics as a proxy for specifying actions. Mnemonics are not guaranteed to be
unique and can only reference a single action. This is especially helpful in
allocating extra resources to specific memory and processing intensive actions
like linking in C++ builds without over-allocating to less demanding tasks.

## Defining execution groups {:#defining-exec-groups}

During rule definition, rule authors can
[declare](/rules/lib/globals/bzl#exec_group)
a set of execution groups. On each execution group, the rule author can specify
everything needed to select an execution platform for that execution group,
namely any constraints via `exec_compatible_with` and toolchain types via
`toolchain`.

```python
# foo.bzl
my_rule = rule(
    _impl,
    exec_groups = {
        "link": exec_group(
            exec_compatible_with = ["@platforms//os:linux"],
            toolchains = ["//foo:toolchain_type"],
        ),
        "test": exec_group(
            toolchains = ["//foo_tools:toolchain_type"],
        ),
    },
    attrs = {
        "_compiler": attr.label(cfg = config.exec("link"))
    },
)
```

In the code snippet above, you can see that tool dependencies can also specify
transition for an exec group using the
[`cfg`](/rules/lib/toplevel/attr#label)
attribute param and the
[`config`](/rules/lib/toplevel/config)
module. The module exposes an `exec` function which takes a single string
parameter which is the name of the exec group for which the dependency should be
built.

As on native rules, the `test` execution group is present by default on Starlark
test rules.

## Accessing execution groups {:#accessing-exec-groups}

In the rule implementation, you can declare that actions should be run on the
execution platform of an execution group. You can do this by using the `exec_group`
param of action generating methods, specifically [`ctx.actions.run`]
(/rules/lib/builtins/actions#run) and
[`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell).

```python
# foo.bzl
def _impl(ctx):
  ctx.actions.run(
     inputs = [ctx.attr._some_tool, ctx.srcs[0]]
     exec_group = "compile",
     # ...
  )
```

Rule authors will also be able to access the [resolved toolchains](/extending/toolchains#toolchain-resolution)
of execution groups, similarly to how you
can access the resolved toolchain of a target:

```python
# foo.bzl
def _impl(ctx):
  foo_info = ctx.exec_groups["link"].toolchains["//foo:toolchain_type"].fooinfo
  ctx.actions.run(
     inputs = [foo_info, ctx.srcs[0]]
     exec_group = "link",
     # ...
  )
```

Note: If an action uses a toolchain from an execution group, but doesn't specify
that execution group in the action declaration, that may potentially cause
issues. A mismatch like this may not immediately cause failures, but is a latent
problem.

### Default execution groups {:#exec-groups-for-native-rules}

The following execution groups are predefined:

* `test`: Test runner actions (for more details, see
  the [execution platform section of the Test Encylopedia](/reference/test-encyclopedia#execution-platform)).
* `cpp_link`: C++ linking actions.

## Using execution groups to set execution properties {:#using-exec-groups-for-exec-properties}

Execution groups are integrated with the
[`exec_properties`](/reference/be/common-definitions#common-attributes)
attribute that exists on every rule and allows the target writer to specify a
string dict of properties that is then passed to the execution machinery. For
example, if you wanted to set some property, say memory, for the target and give
certain actions a higher memory allocation, you would write an `exec_properties`
entry with an execution-group-augmented key, such as:

```python
# BUILD
my_rule(
    name = 'my_target',
    exec_properties = {
        'mem': '12g',
        'link.mem': '16g'
    }
    …
)
```

All actions with `exec_group = "link"` would see the exec properties
dictionary as `{"mem": "16g"}`. As you see here, execution-group-level
settings override target-level settings.

## Using execution groups to set platform constraints {:#using-exec-groups-for-platform-constraints}

Execution groups are also integrated with the
[`exec_compatible_with`](/reference/be/common-definitions#common-attributes) and
[`exec_group_compatible_with`](/reference/be/common-definitions#common-attributes)
attributes that exist on every rule and allow the target writer to specify
additional constraints that must be satisfied by the execution platforms
selected for the target's actions.

For example, if the rule `my_test` defines the `link` execution group in
addition to the default and the `test` execution group, then the following
usage of these attributes would run actions in the default execution group on
a platform with a high number of CPUs, the test action on Linux, and the link
action on the default execution platform:

```python
# BUILD
constraint_setting(name = "cpu")
constraint_value(name = "high_cpu", constraint_setting = ":cpu")

platform(
  name = "high_cpu_platform",
  constraint_values = [":high_cpu"],
  exec_properties = {
    "cpu": "256",
  },
)

my_test(
  name = "my_test",
  exec_compatible_with = ["//constraints:high_cpu"],
  exec_group_compatible_with = {
    "test": ["@platforms//os:linux"],
  },
  ...
)
```

### Execution groups for native rules {:#execution-groups-for-native-rules}

The following execution groups are available for actions defined by native
rules:

* `test`: Test runner actions.
* `cpp_link`: C++ linking actions.

### Execution groups and platform execution properties {:#platform-execution-properties}

It is possible to define `exec_properties` for arbitrary execution groups on
platform targets (unlike `exec_properties` set directly on a target, where
properties for unknown execution groups are rejected). Targets then inherit the
execution platform's `exec_properties` that affect the default execution group
and any other relevant execution groups.

For example, suppose running tests on the exec platform requires some resource
to be available, but it isn't required for compiling and linking; this can be
modelled as follows:

```python
constraint_setting(name = "resource")
constraint_value(name = "has_resource", constraint_setting = ":resource")

platform(
    name = "platform_with_resource",
    constraint_values = [":has_resource"],
    exec_properties = {
        "test.resource": "...",
    },
)

cc_test(
    name = "my_test",
    srcs = ["my_test.cc"],
    exec_compatible_with = [":has_resource"],
)
```

`exec_properties` defined directly on targets take precedence over those that
are inherited from the execution platform.


Project: /_project.yaml
Book: /_book.yaml

# Rules

{% include "_buttons.html" %}

A **rule** defines a series of [**actions**](#actions) that Bazel performs on
inputs to produce a set of outputs, which are referenced in
[**providers**](#providers) returned by the rule's
[**implementation function**](#implementation_function). For example, a C++
binary rule might:

1.  Take a set of `.cpp` source files (inputs).
2.  Run `g++` on the source files (action).
3.  Return the `DefaultInfo` provider with the executable output and other files
    to make available at runtime.
4.  Return the `CcInfo` provider with C++-specific information gathered from the
    target and its dependencies.

From Bazel's perspective, `g++` and the standard C++ libraries are also inputs
to this rule. As a rule writer, you must consider not only the user-provided
inputs to a rule, but also all of the tools and libraries required to execute
the actions.

Before creating or modifying any rule, ensure you are familiar with Bazel's
[build phases](/extending/concepts). It is important to understand the three
phases of a build (loading, analysis, and execution). It is also useful to
learn about [macros](/extending/macros) to understand the difference between rules and
macros. To get started, first review the [Rules Tutorial](/rules/rules-tutorial).
Then, use this page as a reference.

A few rules are built into Bazel itself. These *native rules*, such as
`genrule` and `filegroup`, provide some core support.
By defining your own rules, you can add support for languages and tools
that Bazel doesn't support natively.

Bazel provides an extensibility model for writing rules using the
[Starlark](/rules/language) language. These rules are written in `.bzl` files, which
can be loaded directly from `BUILD` files.

When defining your own rule, you get to decide what attributes it supports and
how it generates its outputs.

The rule's `implementation` function defines its exact behavior during the
[analysis phase](/extending/concepts#evaluation-model). This function doesn't run any
external commands. Rather, it registers [actions](#actions) that will be used
later during the execution phase to build the rule's outputs, if they are
needed.

## Rule creation

In a `.bzl` file, use the [rule](/rules/lib/globals/bzl#rule) function to define a new
rule, and store the result in a global variable. The call to `rule` specifies
[attributes](#attributes) and an
[implementation function](#implementation_function):

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        "deps": attr.label_list(),
        ...
    },
)
```

This defines a [rule kind](/query/language#kind) named `example_library`.

The call to `rule` also must specify if the rule creates an
[executable](#executable-rules) output (with `executable = True`), or specifically
a test executable (with `test = True`). If the latter, the rule is a *test rule*,
and the name of the rule must end in `_test`.

## Target instantiation

Rules can be [loaded](/concepts/build-files#load) and called in `BUILD` files:

```python
load('//some/pkg:rules.bzl', 'example_library')

example_library(
    name = "example_target",
    deps = [":another_target"],
    ...
)
```

Each call to a build rule returns no value, but has the side effect of defining
a target. This is called *instantiating* the rule. This specifies a name for the
new target and values for the target's [attributes](#attributes).

Rules can also be called from Starlark functions and loaded in `.bzl` files.
Starlark functions that call rules are called [Starlark macros](/extending/macros).
Starlark macros must ultimately be called from `BUILD` files, and can only be
called during the [loading phase](/extending/concepts#evaluation-model), when `BUILD`
files are evaluated to instantiate targets.

## Attributes

An *attribute* is a rule argument. Attributes can provide specific values to a
target's [implementation](#implementation_function), or they can refer to other
targets, creating a graph of dependencies.

Rule-specific attributes, such as `srcs` or `deps`, are defined by passing a map
from attribute names to schemas (created using the [`attr`](/rules/lib/toplevel/attr)
module) to the `attrs` parameter of `rule`.
[Common attributes](/reference/be/common-definitions#common-attributes), such as
`name` and `visibility`, are implicitly added to all rules. Additional
attributes are implicitly added to
[executable and test rules](#executable-rules) specifically. Attributes which
are implicitly added to a rule can't be included in the dictionary passed to
`attrs`.

### Dependency attributes

Rules that process source code usually define the following attributes to handle
various [types of dependencies](/concepts/dependencies#types_of_dependencies):

*   `srcs` specifies source files processed by a target's actions. Often, the
    attribute schema specifies which file extensions are expected for the sort
    of source file the rule processes. Rules for languages with header files
    generally specify a separate `hdrs` attribute for headers processed by a
    target and its consumers.
*   `deps` specifies code dependencies for a target. The attribute schema should
    specify which [providers](#providers) those dependencies must provide. (For
    example, `cc_library` provides `CcInfo`.)
*   `data` specifies files to be made available at runtime to any executable
    which depends on a target. That should allow arbitrary files to be
    specified.

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = [".example"]),
        "hdrs": attr.label_list(allow_files = [".header"]),
        "deps": attr.label_list(providers = [ExampleInfo]),
        "data": attr.label_list(allow_files = True),
        ...
    },
)
```

These are examples of *dependency attributes*. Any attribute that specifies
an input label (those defined with
[`attr.label_list`](/rules/lib/toplevel/attr#label_list),
[`attr.label`](/rules/lib/toplevel/attr#label), or
[`attr.label_keyed_string_dict`](/rules/lib/toplevel/attr#label_keyed_string_dict))
specifies dependencies of a certain type
between a target and the targets whose labels (or the corresponding
[`Label`](/rules/lib/builtins/Label) objects) are listed in that attribute when the target
is defined. The repository, and possibly the path, for these labels is resolved
relative to the defined target.

```python
example_library(
    name = "my_target",
    deps = [":other_target"],
)

example_library(
    name = "other_target",
    ...
)
```

In this example, `other_target` is a dependency of `my_target`, and therefore
`other_target` is analyzed first. It is an error if there is a cycle in the
dependency graph of targets.

<a name="private-attributes"></a>

### Private attributes and implicit dependencies {:#private_attributes_and_implicit_dependencies}

A dependency attribute with a default value creates an *implicit dependency*. It
is implicit because it's a part of the target graph that the user doesn't
specify it in a `BUILD` file. Implicit dependencies are useful for hard-coding a
relationship between a rule and a *tool* (a build-time dependency, such as a
compiler), since most of the time a user is not interested in specifying what
tool the rule uses. Inside the rule's implementation function, this is treated
the same as other dependencies.

If you want to provide an implicit dependency without allowing the user to
override that value, you can make the attribute *private* by giving it a name
that begins with an underscore (`_`). Private attributes must have default
values. It generally only makes sense to use private attributes for implicit
dependencies.

```python
example_library = rule(
    implementation = _example_library_impl,
    attrs = {
        ...
        "_compiler": attr.label(
            default = Label("//tools:example_compiler"),
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
    },
)
```

In this example, every target of type `example_library` has an implicit
dependency on the compiler `//tools:example_compiler`. This allows
`example_library`'s implementation function to generate actions that invoke the
compiler, even though the user did not pass its label as an input. Since
`_compiler` is a private attribute, it follows that `ctx.attr._compiler`
will always point to `//tools:example_compiler` in all targets of this rule
type. Alternatively, you can name the attribute `compiler` without the
underscore and keep the default value. This allows users to substitute a
different compiler if necessary, but it requires no awareness of the compiler's
label.

Implicit dependencies are generally used for tools that reside in the same
repository as the rule implementation. If the tool comes from the
[execution platform](/extending/platforms) or a different repository instead, the
rule should obtain that tool from a [toolchain](/extending/toolchains).

### Output attributes

*Output attributes*, such as [`attr.output`](/rules/lib/toplevel/attr#output) and
[`attr.output_list`](/rules/lib/toplevel/attr#output_list), declare an output file that the
target generates. These differ from dependency attributes in two ways:

*   They define output file targets instead of referring to targets defined
    elsewhere.
*   The output file targets depend on the instantiated rule target, instead of
    the other way around.

Typically, output attributes are only used when a rule needs to create outputs
with user-defined names which can't be based on the target name. If a rule has
one output attribute, it is typically named `out` or `outs`.

Output attributes are the preferred way of creating *predeclared outputs*, which
can be specifically depended upon or
[requested at the command line](#requesting_output_files).

## Implementation function

Every rule requires an `implementation` function. These functions are executed
strictly in the [analysis phase](/extending/concepts#evaluation-model) and transform the
graph of targets generated in the loading phase into a graph of
[actions](#actions) to be performed during the execution phase. As such,
implementation functions can't actually read or write files.

Rule implementation functions are usually private (named with a leading
underscore). Conventionally, they are named the same as their rule, but suffixed
with `_impl`.

Implementation functions take exactly one parameter: a
[rule context](/rules/lib/builtins/ctx), conventionally named `ctx`. They return a list of
[providers](#providers).

### Targets

Dependencies are represented at analysis time as [`Target`](/rules/lib/builtins/Target)
objects. These objects contain the [providers](#providers) generated when the
target's implementation function was executed.

[`ctx.attr`](/rules/lib/builtins/ctx#attr) has fields corresponding to the names of each
dependency attribute, containing `Target` objects representing each direct
dependency using that attribute. For `label_list` attributes, this is a list of
`Targets`. For `label` attributes, this is a single `Target` or `None`.

A list of provider objects are returned by a target's implementation function:

```python
return [ExampleInfo(headers = depset(...))]
```

Those can be accessed using index notation (`[]`), with the type of provider as
a key. These can be [custom providers](#custom_providers) defined in Starlark or
[providers for native rules](/rules/lib/providers) available as Starlark
global variables.

For example, if a rule takes header files using a `hdrs` attribute and provides
them to the compilation actions of the target and its consumers, it could
collect them like so:

```python
def _example_library_impl(ctx):
    ...
    transitive_headers = [hdr[ExampleInfo].headers for hdr in ctx.attr.hdrs]
```

There's a legacy struct style, which is strongly discouraged and rules should be
[migrated away from it](#migrating_from_legacy_providers).

### Files

Files are represented by [`File`](/rules/lib/builtins/File) objects. Since Bazel doesn't
perform file I/O during the analysis phase, these objects can't be used to
directly read or write file content. Rather, they are passed to action-emitting
functions (see [`ctx.actions`](/rules/lib/builtins/actions)) to construct pieces of the
action graph.

A `File` can either be a source file or a generated file. Each generated file
must be an output of exactly one action. Source files can't be the output of
any action.

For each dependency attribute, the corresponding field of
[`ctx.files`](/rules/lib/builtins/ctx#files) contains a list of the default outputs of all
dependencies using that attribute:

```python
def _example_library_impl(ctx):
    ...
    headers = depset(ctx.files.hdrs, transitive = transitive_headers)
    srcs = ctx.files.srcs
    ...
```

[`ctx.file`](/rules/lib/builtins/ctx#file) contains a single `File` or `None` for
dependency attributes whose specs set `allow_single_file = True`.
[`ctx.executable`](/rules/lib/builtins/ctx#executable) behaves the same as `ctx.file`, but only
contains fields for dependency attributes whose specs set `executable = True`.

### Declaring outputs

During the analysis phase, a rule's implementation function can create outputs.
Since all labels have to be known during the loading phase, these additional
outputs have no labels. `File` objects for outputs can be created using
[`ctx.actions.declare_file`](/rules/lib/builtins/actions#declare_file) and
[`ctx.actions.declare_directory`](/rules/lib/builtins/actions#declare_directory).
Often, the names of outputs are based on the target's name,
[`ctx.label.name`](/rules/lib/builtins/ctx#label):

```python
def _example_library_impl(ctx):
  ...
  output_file = ctx.actions.declare_file(ctx.label.name + ".output")
  ...
```

For *predeclared outputs*, like those created for
[output attributes](#output_attributes), `File` objects instead can be retrieved
from the corresponding fields of [`ctx.outputs`](/rules/lib/builtins/ctx#outputs).

### Actions

An action describes how to generate a set of outputs from a set of inputs, for
example "run gcc on hello.c and get hello.o". When an action is created, Bazel
doesn't run the command immediately. It registers it in a graph of dependencies,
because an action can depend on the output of another action. For example, in C,
the linker must be called after the compiler.

General-purpose functions that create actions are defined in
[`ctx.actions`](/rules/lib/builtins/actions):

*   [`ctx.actions.run`](/rules/lib/builtins/actions#run), to run an executable.
*   [`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell), to run a shell
    command.
*   [`ctx.actions.write`](/rules/lib/builtins/actions#write), to write a string to a file.
*   [`ctx.actions.expand_template`](/rules/lib/builtins/actions#expand_template), to
    generate a file from a template.

[`ctx.actions.args`](/rules/lib/builtins/actions#args) can be used to efficiently
accumulate the arguments for actions. It avoids flattening depsets until
execution time:

```python
def _example_library_impl(ctx):
    ...

    transitive_headers = [dep[ExampleInfo].headers for dep in ctx.attr.deps]
    headers = depset(ctx.files.hdrs, transitive = transitive_headers)
    srcs = ctx.files.srcs
    inputs = depset(srcs, transitive = [headers])
    output_file = ctx.actions.declare_file(ctx.label.name + ".output")

    args = ctx.actions.args()
    args.add_joined("-h", headers, join_with = ",")
    args.add_joined("-s", srcs, join_with = ",")
    args.add("-o", output_file)

    ctx.actions.run(
        mnemonic = "ExampleCompile",
        executable = ctx.executable._compiler,
        arguments = [args],
        inputs = inputs,
        outputs = [output_file],
    )
    ...
```

Actions take a list or depset of input files and generate a (non-empty) list of
output files. The set of input and output files must be known during the
[analysis phase](/extending/concepts#evaluation-model). It might depend on the value of
attributes, including providers from dependencies, but it can't depend on the
result of the execution. For example, if your action runs the unzip command, you
must specify which files you expect to be inflated (before running unzip).
Actions which create a variable number of files internally can wrap those in a
single file (such as a zip, tar, or other archive format).

Actions must list all of their inputs. Listing inputs that are not used is
permitted, but inefficient.

Actions must create all of their outputs. They may write other files, but
anything not in outputs won't be available to consumers. All declared outputs
must be written by some action.

Actions are comparable to pure functions: They should depend only on the
provided inputs, and avoid accessing computer information, username, clock,
network, or I/O devices (except for reading inputs and writing outputs). This is
important because the output will be cached and reused.

Dependencies are resolved by Bazel, which decides which actions to
execute. It is an error if there is a cycle in the dependency graph. Creating
an action doesn't guarantee that it will be executed, that depends on whether
its outputs are needed for the build.

### Providers

Providers are pieces of information that a rule exposes to other rules that
depend on it. This data can include output files, libraries, parameters to pass
on a tool's command line, or anything else a target's consumers should know
about.

Since a rule's implementation function can only read providers from the
instantiated target's immediate dependencies, rules need to forward any
information from a target's dependencies that needs to be known by a target's
consumers, generally by accumulating that into a [`depset`](/rules/lib/builtins/depset).

A target's providers are specified by a list of provider objects returned by
the implementation function.

Old implementation functions can also be written in a legacy style where the
implementation function returns a [`struct`](/rules/lib/builtins/struct) instead of list of
provider objects. This style is strongly discouraged and rules should be
[migrated away from it](#migrating_from_legacy_providers).

#### Default outputs

A target's *default outputs* are the outputs that are requested by default when
the target is requested for build at the command line. For example, a
`java_library` target `//pkg:foo` has `foo.jar` as a default output, so that
will be built by the command `bazel build //pkg:foo`.

Default outputs are specified by the `files` parameter of
[`DefaultInfo`](/rules/lib/providers/DefaultInfo):

```python
def _example_library_impl(ctx):
    ...
    return [
        DefaultInfo(files = depset([output_file]), ...),
        ...
    ]
```

If `DefaultInfo` is not returned by a rule implementation or the `files`
parameter is not specified, `DefaultInfo.files` defaults to all
*predeclared outputs* (generally, those created by [output
attributes](#output_attributes)).

Rules that perform actions should provide default outputs, even if those outputs
are not expected to be directly used. Actions that are not in the graph of the
requested outputs are pruned. If an output is only used by a target's consumers,
those actions won't be performed when the target is built in isolation. This
makes debugging more difficult because rebuilding just the failing target won't
reproduce the failure.

#### Runfiles

Runfiles are a set of files used by a target at runtime (as opposed to build
time). During the [execution phase](/extending/concepts#evaluation-model), Bazel creates
a directory tree containing symlinks pointing to the runfiles. This stages the
environment for the binary so it can access the runfiles during runtime.

Runfiles can be added manually during rule creation.
[`runfiles`](/rules/lib/builtins/runfiles) objects can be created by the `runfiles` method
on the rule context, [`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles) and passed to the
`runfiles` parameter on `DefaultInfo`. The executable output of
[executable rules](#executable-rules) is implicitly added to the runfiles.

Some rules specify attributes, generally named
[`data`](/reference/be/common-definitions#common.data), whose outputs are added to
a targets' runfiles. Runfiles should also be merged in from `data`, as well as
from any attributes which might provide code for eventual execution, generally
`srcs` (which might contain `filegroup` targets with associated `data`) and
`deps`.

```python
def _example_library_impl(ctx):
    ...
    runfiles = ctx.runfiles(files = ctx.files.data)
    transitive_runfiles = []
    for runfiles_attr in (
        ctx.attr.srcs,
        ctx.attr.hdrs,
        ctx.attr.deps,
        ctx.attr.data,
    ):
        for target in runfiles_attr:
            transitive_runfiles.append(target[DefaultInfo].default_runfiles)
    runfiles = runfiles.merge_all(transitive_runfiles)
    return [
        DefaultInfo(..., runfiles = runfiles),
        ...
    ]
```

#### Custom providers

Providers can be defined using the [`provider`](/rules/lib/globals/bzl#provider)
function to convey rule-specific information:

```python
ExampleInfo = provider(
    "Info needed to compile/link Example code.",
    fields = {
        "headers": "depset of header Files from transitive dependencies.",
        "files_to_link": "depset of Files from compilation.",
    },
)
```

Rule implementation functions can then construct and return provider instances:

```python
def _example_library_impl(ctx):
  ...
  return [
      ...
      ExampleInfo(
          headers = headers,
          files_to_link = depset(
              [output_file],
              transitive = [
                  dep[ExampleInfo].files_to_link for dep in ctx.attr.deps
              ],
          ),
      )
  ]
```

##### Custom initialization of providers

It's possible to guard the instantiation of a provider with custom
preprocessing and validation logic. This can be used to ensure that all
provider instances satisfy certain invariants, or to give users a cleaner API for
obtaining an instance.

This is done by passing an `init` callback to the
[`provider`](/rules/lib/globals/bzl.html#provider) function. If this callback is given, the
return type of `provider()` changes to be a tuple of two values: the provider
symbol that is the ordinary return value when `init` is not used, and a "raw
constructor".

In this case, when the provider symbol is called, instead of directly returning
a new instance, it will forward the arguments along to the `init` callback. The
callback's return value must be a dict mapping field names (strings) to values;
this is used to initialize the fields of the new instance. Note that the
callback may have any signature, and if the arguments don't match the signature
an error is reported as if the callback were invoked directly.

The raw constructor, by contrast, will bypass the `init` callback.

The following example uses `init` to preprocess and validate its arguments:

```python
# //pkg:exampleinfo.bzl

_core_headers = [...]  # private constant representing standard library files

# Keyword-only arguments are preferred.
def _exampleinfo_init(*, files_to_link, headers = None, allow_empty_files_to_link = False):
    if not files_to_link and not allow_empty_files_to_link:
        fail("files_to_link may not be empty")
    all_headers = depset(_core_headers, transitive = headers)
    return {"files_to_link": files_to_link, "headers": all_headers}

ExampleInfo, _new_exampleinfo = provider(
    fields = ["files_to_link", "headers"],
    init = _exampleinfo_init,
)
```

A rule implementation may then instantiate the provider as follows:

```python
ExampleInfo(
    files_to_link = my_files_to_link,  # may not be empty
    headers = my_headers,  # will automatically include the core headers
)
```

The raw constructor can be used to define alternative public factory functions
that don't go through the `init` logic. For example, exampleinfo.bzl
could define:

```python
def make_barebones_exampleinfo(headers):
    """Returns an ExampleInfo with no files_to_link and only the specified headers."""
    return _new_exampleinfo(files_to_link = depset(), headers = all_headers)
```

Typically, the raw constructor is bound to a variable whose name begins with an
underscore (`_new_exampleinfo` above), so that user code can't load it and
generate arbitrary provider instances.

Another use for `init` is to prevent the user from calling the provider
symbol altogether, and force them to use a factory function instead:

```python
def _exampleinfo_init_banned(*args, **kwargs):
    fail("Do not call ExampleInfo(). Use make_exampleinfo() instead.")

ExampleInfo, _new_exampleinfo = provider(
    ...
    init = _exampleinfo_init_banned)

def make_exampleinfo(...):
    ...
    return _new_exampleinfo(...)
```

<a name="executable-rules"></a>

## Executable rules and test rules

Executable rules define targets that can be invoked by a `bazel run` command.
Test rules are a special kind of executable rule whose targets can also be
invoked by a `bazel test` command. Executable and test rules are created by
setting the respective [`executable`](/rules/lib/globals/bzl#rule.executable) or
[`test`](/rules/lib/globals/bzl#rule.test) argument to `True` in the call to `rule`:

```python
example_binary = rule(
   implementation = _example_binary_impl,
   executable = True,
   ...
)

example_test = rule(
   implementation = _example_binary_impl,
   test = True,
   ...
)
```

Test rules must have names that end in `_test`. (Test *target* names also often
end in `_test` by convention, but this is not required.) Non-test rules must not
have this suffix.

Both kinds of rules must produce an executable output file (which may or may not
be predeclared) that will be invoked by the `run` or `test` commands. To tell
Bazel which of a rule's outputs to use as this executable, pass it as the
`executable` argument of a returned [`DefaultInfo`](/rules/lib/providers/DefaultInfo)
provider. That `executable` is added to the default outputs of the rule (so you
don't need to pass that to both `executable` and `files`). It's also implicitly
added to the [runfiles](#runfiles):

```python
def _example_binary_impl(ctx):
    executable = ctx.actions.declare_file(ctx.label.name)
    ...
    return [
        DefaultInfo(executable = executable, ...),
        ...
    ]
```

The action that generates this file must set the executable bit on the file. For
a [`ctx.actions.run`](/rules/lib/builtins/actions#run) or
[`ctx.actions.run_shell`](/rules/lib/builtins/actions#run_shell) action this should be done
by the underlying tool that is invoked by the action. For a
[`ctx.actions.write`](/rules/lib/builtins/actions#write) action, pass `is_executable = True`.

As [legacy behavior](#deprecated_predeclared_outputs), executable rules have a
special `ctx.outputs.executable` predeclared output. This file serves as the
default executable if you don't specify one using `DefaultInfo`; it must not be
used otherwise. This output mechanism is deprecated because it doesn't support
customizing the executable file's name at analysis time.

See examples of an
[executable rule](https://github.com/bazelbuild/examples/blob/main/rules/executable/fortune.bzl){: .external}
and a
[test rule](https://github.com/bazelbuild/examples/blob/main/rules/test_rule/line_length.bzl){: .external}.

[Executable rules](/reference/be/common-definitions#common-attributes-binaries) and
[test rules](/reference/be/common-definitions#common-attributes-tests) have additional
attributes implicitly defined, in addition to those added for
[all rules](/reference/be/common-definitions#common-attributes). The defaults of
implicitly-added attributes can't be changed, though this can be worked around
by wrapping a private rule in a [Starlark macro](/extending/macros) which alters the
default:

```python
def example_test(size = "small", **kwargs):
  _example_test(size = size, **kwargs)

_example_test = rule(
 ...
)
```

### Runfiles location

When an executable target is run with `bazel run` (or `test`), the root of the
runfiles directory is adjacent to the executable. The paths relate as follows:

```python
# Given launcher_path and runfile_file:
runfiles_root = launcher_path.path + ".runfiles"
workspace_name = ctx.workspace_name
runfile_path = runfile_file.short_path
execution_root_relative_path = "%s/%s/%s" % (
    runfiles_root, workspace_name, runfile_path)
```

The path to a `File` under the runfiles directory corresponds to
[`File.short_path`](/rules/lib/builtins/File#short_path).

The binary executed directly by `bazel` is adjacent to the root of the
`runfiles` directory. However, binaries called *from* the runfiles can't make
the same assumption. To mitigate this, each binary should provide a way to
accept its runfiles root as a parameter using an environment, or command line
argument or flag. This allows binaries to pass the correct canonical runfiles root
to the binaries it calls. If that's not set, a binary can guess that it was the
first binary called and look for an adjacent runfiles directory.

## Advanced topics

### Requesting output files

A single target can have several output files. When a `bazel build` command is
run, some of the outputs of the targets given to the command are considered to
be *requested*. Bazel only builds these requested files and the files that they
directly or indirectly depend on. (In terms of the action graph, Bazel only
executes the actions that are reachable as transitive dependencies of the
requested files.)

In addition to [default outputs](#default_outputs), any *predeclared output* can
be explicitly requested on the command line. Rules can specify predeclared
outputs using [output attributes](#output_attributes). In that case, the user
explicitly chooses labels for outputs when they instantiate the rule. To obtain
[`File`](/rules/lib/builtins/File) objects for output attributes, use the corresponding
attribute of [`ctx.outputs`](/rules/lib/builtins/ctx#outputs). Rules can
[implicitly define predeclared outputs](#deprecated_predeclared_outputs) based
on the target name as well, but this feature is deprecated.

In addition to default outputs, there are *output groups*, which are collections
of output files that may be requested together. These can be requested with
[`--output_groups`](/reference/command-line-reference#flag--output_groups). For
example, if a target `//pkg:mytarget` is of a rule type that has a `debug_files`
output group, these files can be built by running `bazel build //pkg:mytarget
--output_groups=debug_files`. Since non-predeclared outputs don't have labels,
they can only be requested by appearing in the default outputs or an output
group.

Output groups can be specified with the
[`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo) provider. Note that unlike many
built-in providers, `OutputGroupInfo` can take parameters with arbitrary names
to define output groups with that name:

```python
def _example_library_impl(ctx):
    ...
    debug_file = ctx.actions.declare_file(name + ".pdb")
    ...
    return [
        DefaultInfo(files = depset([output_file]), ...),
        OutputGroupInfo(
            debug_files = depset([debug_file]),
            all_files = depset([output_file, debug_file]),
        ),
        ...
    ]
```

Also unlike most providers, `OutputGroupInfo` can be returned by both an
[aspect](/extending/aspects) and the rule target to which that aspect is applied, as
long as they don't define the same output groups. In that case, the resulting
providers are merged.

Note that `OutputGroupInfo` generally shouldn't be used to convey specific sorts
of files from a target to the actions of its consumers. Define
[rule-specific providers](#custom_providers) for that instead.

### Configurations

Imagine that you want to build a C++ binary for a different architecture. The
build can be complex and involve multiple steps. Some of the intermediate
binaries, like compilers and code generators, have to run on
[the execution platform](/extending/platforms#overview) (which could be your host,
or a remote executor). Some binaries like the final output must be built for the
target architecture.

For this reason, Bazel has a concept of "configurations" and transitions. The
topmost targets (the ones requested on the command line) are built-in the
"target" configuration, while tools that should run on the execution platform
are built-in an "exec" configuration. Rules may generate different actions based
on the configuration, for instance to change the cpu architecture that is passed
to the compiler. In some cases, the same library may be needed for different
configurations. If this happens, it will be analyzed and potentially built
multiple times.

By default, Bazel builds a target's dependencies in the same configuration as
the target itself, in other words without transitions. When a dependency is a
tool that's needed to help build the target, the corresponding attribute should
specify a transition to an exec configuration. This causes the tool and all its
dependencies to build for the execution platform.

For each dependency attribute, you can use `cfg` to decide if dependencies
should build in the same configuration or transition to an exec configuration.
If a dependency attribute has the flag `executable = True`, `cfg` must be set
explicitly. This is to guard against accidentally building a tool for the wrong
configuration.
[See example](https://github.com/bazelbuild/examples/blob/main/rules/actions_run/execute.bzl){: .external}

In general, sources, dependent libraries, and executables that will be needed at
runtime can use the same configuration.

Tools that are executed as part of the build (such as compilers or code generators)
should be built for an exec configuration. In this case, specify `cfg = "exec"` in
the attribute.

Otherwise, executables that are used at runtime (such as as part of a test) should
be built for the target configuration. In this case, specify `cfg = "target"` in
the attribute.

`cfg = "target"` doesn't actually do anything: it's purely a convenience value to
help rule designers be explicit about their intentions. When `executable = False`,
which means `cfg` is optional, only set this when it truly helps readability.

You can also use `cfg = my_transition` to use
[user-defined transitions](/extending/config#user-defined-transitions), which allow
rule authors a great deal of flexibility in changing configurations, with the
drawback of
[making the build graph larger and less comprehensible](/extending/config#memory-and-performance-considerations).

**Note**: Historically, Bazel didn't have the concept of execution platforms,
and instead all build actions were considered to run on the host machine. Bazel
versions before 6.0 created a distinct "host" configuration to represent this.
If you see references to "host" in code or old documentation, that's what this
refers to. We recommend using Bazel 6.0 or newer to avoid this extra conceptual
overhead.

<a name="fragments"></a>

### Configuration fragments

Rules may access
[configuration fragments](/rules/lib/fragments) such as
`cpp` and `java`. However, all required fragments must be declared in
order to avoid access errors:

```python
def _impl(ctx):
    # Using ctx.fragments.cpp leads to an error since it was not declared.
    x = ctx.fragments.java
    ...

my_rule = rule(
    implementation = _impl,
    fragments = ["java"],      # Required fragments of the target configuration
    ...
)
```

### Runfiles symlinks

Normally, the relative path of a file in the runfiles tree is the same as the
relative path of that file in the source tree or generated output tree. If these
need to be different for some reason, you can specify the `root_symlinks` or
`symlinks` arguments. The `root_symlinks` is a dictionary mapping paths to
files, where the paths are relative to the root of the runfiles directory. The
`symlinks` dictionary is the same, but paths are implicitly prefixed with the
name of the main workspace (*not* the name of the repository containing the
current target).

```python
    ...
    runfiles = ctx.runfiles(
        root_symlinks = {"some/path/here.foo": ctx.file.some_data_file2}
        symlinks = {"some/path/here.bar": ctx.file.some_data_file3}
    )
    # Creates something like:
    # sometarget.runfiles/
    #     some/
    #         path/
    #             here.foo -> some_data_file2
    #     <workspace_name>/
    #         some/
    #             path/
    #                 here.bar -> some_data_file3
```

If `symlinks` or `root_symlinks` is used, be careful not to map two different
files to the same path in the runfiles tree. This will cause the build to fail
with an error describing the conflict. To fix, you will need to modify your
`ctx.runfiles` arguments to remove the collision. This checking will be done for
any targets using your rule, as well as targets of any kind that depend on those
targets. This is especially risky if your tool is likely to be used transitively
by another tool; symlink names must be unique across the runfiles of a tool and
all of its dependencies.

### Code coverage

When the [`coverage`](/reference/command-line-reference#coverage) command is run,
the build may need to add coverage instrumentation for certain targets. The
build also gathers the list of source files that are instrumented. The subset of
targets that are considered is controlled by the flag
[`--instrumentation_filter`](/reference/command-line-reference#flag--instrumentation_filter).
Test targets are excluded, unless
[`--instrument_test_targets`](/reference/command-line-reference#flag--instrument_test_targets)
is specified.

If a rule implementation adds coverage instrumentation at build time, it needs
to account for that in its implementation function.
[ctx.coverage_instrumented](/rules/lib/builtins/ctx#coverage_instrumented) returns
`True` in coverage mode if a target's sources should be instrumented:

```python
# Are this rule's sources instrumented?
if ctx.coverage_instrumented():
  # Do something to turn on coverage for this compile action
```

Logic that always needs to be on in coverage mode (whether a target's sources
specifically are instrumented or not) can be conditioned on
[ctx.configuration.coverage_enabled](/rules/lib/builtins/configuration#coverage_enabled).

If the rule directly includes sources from its dependencies before compilation
(such as header files), it may also need to turn on compile-time instrumentation if
the dependencies' sources should be instrumented:

```python
# Are this rule's sources or any of the sources for its direct dependencies
# in deps instrumented?
if (ctx.configuration.coverage_enabled and
    (ctx.coverage_instrumented() or
     any([ctx.coverage_instrumented(dep) for dep in ctx.attr.deps]))):
    # Do something to turn on coverage for this compile action
```

Rules also should provide information about which attributes are relevant for
coverage with the `InstrumentedFilesInfo` provider, constructed using
[`coverage_common.instrumented_files_info`](/rules/lib/toplevel/coverage_common#instrumented_files_info).
The `dependency_attributes` parameter of `instrumented_files_info` should list
all runtime dependency attributes, including code dependencies like `deps` and
data dependencies like `data`. The `source_attributes` parameter should list the
rule's source files attributes if coverage instrumentation might be added:

```python
def _example_library_impl(ctx):
    ...
    return [
        ...
        coverage_common.instrumented_files_info(
            ctx,
            dependency_attributes = ["deps", "data"],
            # Omitted if coverage is not supported for this rule:
            source_attributes = ["srcs", "hdrs"],
        )
        ...
    ]
```

If `InstrumentedFilesInfo` is not returned, a default one is created with each
non-tool [dependency attribute](#dependency_attributes) that doesn't set
[`cfg`](#configuration) to `"exec"` in the attribute schema. in
`dependency_attributes`. (This isn't ideal behavior, since it puts attributes
like `srcs` in `dependency_attributes` instead of `source_attributes`, but it
avoids the need for explicit coverage configuration for all rules in the
dependency chain.)

### Validation Actions

Sometimes you need to validate something about the build, and the
information required to do that validation is available only in artifacts
(source files or generated files). Because this information is in artifacts,
rules can't do this validation at analysis time because rules can't read
files. Instead, actions must do this validation at execution time. When
validation fails, the action will fail, and hence so will the build.

Examples of validations that might be run are static analysis, linting,
dependency and consistency checks, and style checks.

Validation actions can also help to improve build performance by moving parts
of actions that are not required for building artifacts into separate actions.
For example, if a single action that does compilation and linting can be
separated into a compilation action and a linting action, then the linting
action can be run as a validation action and run in parallel with other actions.

These "validation actions" often don't produce anything that is used elsewhere
in the build, since they only need to assert things about their inputs. This
presents a problem though: If a validation action doesn't produce anything that
is used elsewhere in the build, how does a rule get the action to run?
Historically, the approach was to have the validation action output an empty
file, and artificially add that output to the inputs of some other important
action in the build:

<img src="/rules/validation_action_historical.svg" width="35%" />

This works, because Bazel will always run the validation action when the compile
action is run, but this has significant drawbacks:

1. The validation action is in the critical path of the build. Because Bazel
thinks the empty output is required to run the compile action, it will run the
validation action first, even though the compile action will ignore the input.
This reduces parallelism and slows down builds.

2. If other actions in the build might run instead of the
compile action, then the empty outputs of validation actions need to be added to
those actions as well (`java_library`'s source jar output, for example). This is
also a problem if new actions that might run instead of the compile action are
added later, and the empty validation output is accidentally left off.

The solution to these problems is to use the Validations Output Group.

#### Validations Output Group

The Validations Output Group is an output group designed to hold the otherwise
unused outputs of validation actions, so that they don't need to be artificially
added to the inputs of other actions.

This group is special in that its outputs are always requested, regardless of
the value of the `--output_groups` flag, and regardless of how the target is
depended upon (for example, on the command line, as a dependency, or through
implicit outputs of the target). Note that normal caching and incrementality
still apply: if the inputs to the validation action have not changed and the
validation action previously succeeded, then the validation action won't be
run.

<img src="/rules/validation_action.svg" width="35%" />

Using this output group still requires that validation actions output some file,
even an empty one. This might require wrapping some tools that normally don't
create outputs so that a file is created.

A target's validation actions are not run in three cases:

*    When the target is depended upon as a tool
*    When the target is depended upon as an implicit dependency (for example, an
     attribute that starts with "_")
*    When the target is built in the exec configuration.

It is assumed that these targets have their own
separate builds and tests that would uncover any validation failures.

#### Using the Validations Output Group

The Validations Output Group is named `_validation` and is used like any other
output group:

```python
def _rule_with_validation_impl(ctx):

  ctx.actions.write(ctx.outputs.main, "main output\n")
  ctx.actions.write(ctx.outputs.implicit, "implicit output\n")

  validation_output = ctx.actions.declare_file(ctx.attr.name + ".validation")
  ctx.actions.run(
    outputs = [validation_output],
    executable = ctx.executable._validation_tool,
    arguments = [validation_output.path],
  )

  return [
    DefaultInfo(files = depset([ctx.outputs.main])),
    OutputGroupInfo(_validation = depset([validation_output])),
  ]


rule_with_validation = rule(
  implementation = _rule_with_validation_impl,
  outputs = {
    "main": "%{name}.main",
    "implicit": "%{name}.implicit",
  },
  attrs = {
    "_validation_tool": attr.label(
        default = Label("//validation_actions:validation_tool"),
        executable = True,
        cfg = "exec"
    ),
  }
)
```

Notice that the validation output file is not added to the `DefaultInfo` or the
inputs to any other action. The validation action for a target of this rule kind
will still run if the target is depended upon by label, or any of the target's
implicit outputs are directly or indirectly depended upon.

It is usually important that the outputs of validation actions only go into the
validation output group, and are not added to the inputs of other actions, as
this could defeat parallelism gains. Note however that Bazel doesn't
have any special checking to enforce this. Therefore, you should test
that validation action outputs are not added to the inputs of any actions in the
tests for Starlark rules. For example:

```python
load("@bazel_skylib//lib:unittest.bzl", "analysistest")

def _validation_outputs_test_impl(ctx):
  env = analysistest.begin(ctx)

  actions = analysistest.target_actions(env)
  target = analysistest.target_under_test(env)
  validation_outputs = target.output_groups._validation.to_list()
  for action in actions:
    for validation_output in validation_outputs:
      if validation_output in action.inputs.to_list():
        analysistest.fail(env,
            "%s is a validation action output, but is an input to action %s" % (
                validation_output, action))

  return analysistest.end(env)

validation_outputs_test = analysistest.make(_validation_outputs_test_impl)
```

#### Validation Actions Flag

Running validation actions is controlled by the `--run_validations` command line
flag, which defaults to true.

## Deprecated features

### Deprecated predeclared outputs

There are two **deprecated** ways of using predeclared outputs:

*   The [`outputs`](/rules/lib/globals/bzl#rule.outputs) parameter of `rule` specifies
    a mapping between output attribute names and string templates for generating
    predeclared output labels. Prefer using non-predeclared outputs and
    explicitly adding outputs to `DefaultInfo.files`. Use the rule target's
    label as input for rules which consume the output instead of a predeclared
    output's label.

*   For [executable rules](#executable-rules), `ctx.outputs.executable` refers
    to a predeclared executable output with the same name as the rule target.
    Prefer declaring the output explicitly, for example with
    `ctx.actions.declare_file(ctx.label.name)`, and ensure that the command that
    generates the executable sets its permissions to allow execution. Explicitly
    pass the executable output to the `executable` parameter of `DefaultInfo`.

### Runfiles features to avoid

[`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles) and the [`runfiles`](/rules/lib/builtins/runfiles)
type have a complex set of features, many of which are kept for legacy reasons.
The following recommendations help reduce complexity:

*   **Avoid** use of the `collect_data` and `collect_default` modes of
    [`ctx.runfiles`](/rules/lib/builtins/ctx#runfiles). These modes implicitly collect
    runfiles across certain hardcoded dependency edges in confusing ways.
    Instead, add files using the `files` or `transitive_files` parameters of
    `ctx.runfiles`, or by merging in runfiles from dependencies with
    `runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)`.

*   **Avoid** use of the `data_runfiles` and `default_runfiles` of the
    `DefaultInfo` constructor. Specify `DefaultInfo(runfiles = ...)` instead.
    The distinction between "default" and "data" runfiles is maintained for
    legacy reasons. For example, some rules put their default outputs in
    `data_runfiles`, but not `default_runfiles`. Instead of using
    `data_runfiles`, rules should *both* include default outputs and merge in
    `default_runfiles` from attributes which provide runfiles (often
    [`data`](/reference/be/common-definitions#common-attributes.data)).

*   When retrieving `runfiles` from `DefaultInfo` (generally only for merging
    runfiles between the current rule and its dependencies), use
    `DefaultInfo.default_runfiles`, **not** `DefaultInfo.data_runfiles`.

### Migrating from legacy providers

Historically, Bazel providers were simple fields on the `Target` object. They
were accessed using the dot operator, and they were created by putting the field
in a [`struct`](/rules/lib/builtins/struct) returned by the rule's
implementation function instead of a list of provider objects:

```python
return struct(example_info = struct(headers = depset(...)))
```

Such providers can be retrieved from the corresponding field of the `Target` object:

```python
transitive_headers = [hdr.example_info.headers for hdr in ctx.attr.hdrs]
```

*This style is deprecated and should not be used in new code;* see following for
information that may help you migrate. The new provider mechanism avoids name
clashes. It also supports data hiding, by requiring any code accessing a
provider instance to retrieve it using the provider symbol.

For the moment, legacy providers are still supported. A rule can return both
legacy and modern providers as follows:

```python
def _old_rule_impl(ctx):
  ...
  legacy_data = struct(x = "foo", ...)
  modern_data = MyInfo(y = "bar", ...)
  # When any legacy providers are returned, the top-level returned value is a
  # struct.
  return struct(
      # One key = value entry for each legacy provider.
      legacy_info = legacy_data,
      ...
      # Additional modern providers:
      providers = [modern_data, ...])
```

If `dep` is the resulting `Target` object for an instance of this rule, the
providers and their contents can be retrieved as `dep.legacy_info.x` and
`dep[MyInfo].y`.

In addition to `providers`, the returned struct can also take several other
fields that have special meaning (and thus don't create a corresponding legacy
provider):

*   The fields `files`, `runfiles`, `data_runfiles`, `default_runfiles`, and
    `executable` correspond to the same-named fields of
    [`DefaultInfo`](/rules/lib/providers/DefaultInfo). It is not allowed to specify any of
    these fields while also returning a `DefaultInfo` provider.

*   The field `output_groups` takes a struct value and corresponds to an
    [`OutputGroupInfo`](/rules/lib/providers/OutputGroupInfo).

In [`provides`](/rules/lib/globals/bzl#rule.provides) declarations of rules, and in
[`providers`](/rules/lib/toplevel/attr#label_list.providers) declarations of dependency
attributes, legacy providers are passed in as strings and modern providers are
passed in by their `Info` symbol. Be sure to change from strings to symbols
when migrating. For complex or large rule sets where it is difficult to update
all rules atomically, you may have an easier time if you follow this sequence of
steps:

1.  Modify the rules that produce the legacy provider to produce both the legacy
    and modern providers, using the preceding syntax. For rules that declare they
    return the legacy provider, update that declaration to include both the
    legacy and modern providers.

2.  Modify the rules that consume the legacy provider to instead consume the
    modern provider. If any attribute declarations require the legacy provider,
    also update them to instead require the modern provider. Optionally, you can
    interleave this work with step 1 by having consumers accept or require either
    provider: Test for the presence of the legacy provider using
    `hasattr(target, 'foo')`, or the new provider using `FooInfo in target`.

3.  Fully remove the legacy provider from all rules.


Project: /_project.yaml
Book: /_book.yaml

# Toolchains

{% include "_buttons.html" %}

This page describes the toolchain framework, which is a way for rule authors to
decouple their rule logic from platform-based selection of tools. It is
recommended to read the [rules](/extending/rules) and [platforms](/extending/platforms)
pages before continuing. This page covers why toolchains are needed, how to
define and use them, and how Bazel selects an appropriate toolchain based on
platform constraints.

## Motivation {:#motivation}

Let's first look at the problem toolchains are designed to solve. Suppose you
are writing rules to support the "bar" programming language. Your `bar_binary`
rule would compile `*.bar` files using the `barc` compiler, a tool that itself
is built as another target in your workspace. Since users who write `bar_binary`
targets shouldn't have to specify a dependency on the compiler, you make it an
implicit dependency by adding it to the rule definition as a private attribute.

```python
bar_binary = rule(
    implementation = _bar_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        ...
        "_compiler": attr.label(
            default = "//bar_tools:barc_linux",  # the compiler running on linux
            providers = [BarcInfo],
        ),
    },
)
```

`//bar_tools:barc_linux` is now a dependency of every `bar_binary` target, so
it'll be built before any `bar_binary` target. It can be accessed by the rule's
implementation function just like any other attribute:

```python
BarcInfo = provider(
    doc = "Information about how to invoke the barc compiler.",
    # In the real world, compiler_path and system_lib might hold File objects,
    # but for simplicity they are strings for this example. arch_flags is a list
    # of strings.
    fields = ["compiler_path", "system_lib", "arch_flags"],
)

def _bar_binary_impl(ctx):
    ...
    info = ctx.attr._compiler[BarcInfo]
    command = "%s -l %s %s" % (
        info.compiler_path,
        info.system_lib,
        " ".join(info.arch_flags),
    )
    ...
```

The issue here is that the compiler's label is hardcoded into `bar_binary`, yet
different targets may need different compilers depending on what platform they
are being built for and what platform they are being built on -- called the
*target platform* and *execution platform*, respectively. Furthermore, the rule
author does not necessarily even know all the available tools and platforms, so
it is not feasible to hardcode them in the rule's definition.

A less-than-ideal solution would be to shift the burden onto users, by making
the `_compiler` attribute non-private. Then individual targets could be
hardcoded to build for one platform or another.

```python
bar_binary(
    name = "myprog_on_linux",
    srcs = ["mysrc.bar"],
    compiler = "//bar_tools:barc_linux",
)

bar_binary(
    name = "myprog_on_windows",
    srcs = ["mysrc.bar"],
    compiler = "//bar_tools:barc_windows",
)
```

You can improve on this solution by using `select` to choose the `compiler`
[based on the platform](/docs/configurable-attributes):

```python
config_setting(
    name = "on_linux",
    constraint_values = [
        "@platforms//os:linux",
    ],
)

config_setting(
    name = "on_windows",
    constraint_values = [
        "@platforms//os:windows",
    ],
)

bar_binary(
    name = "myprog",
    srcs = ["mysrc.bar"],
    compiler = select({
        ":on_linux": "//bar_tools:barc_linux",
        ":on_windows": "//bar_tools:barc_windows",
    }),
)
```

But this is tedious and a bit much to ask of every single `bar_binary` user.
If this style is not used consistently throughout the workspace, it leads to
builds that work fine on a single platform but fail when extended to
multi-platform scenarios. It also does not address the problem of adding support
for new platforms and compilers without modifying existing rules or targets.

The toolchain framework solves this problem by adding an extra level of
indirection. Essentially, you declare that your rule has an abstract dependency
on *some* member of a family of targets (a toolchain type), and Bazel
automatically resolves this to a particular target (a toolchain) based on the
applicable platform constraints. Neither the rule author nor the target author
need know the complete set of available platforms and toolchains.

## Writing rules that use toolchains {:#writing-rules-toolchains}

Under the toolchain framework, instead of having rules depend directly on tools,
they instead depend on *toolchain types*. A toolchain type is a simple target
that represents a class of tools that serve the same role for different
platforms. For instance, you can declare a type that represents the bar
compiler:

```python
# By convention, toolchain_type targets are named "toolchain_type" and
# distinguished by their package path. So the full path for this would be
# //bar_tools:toolchain_type.
toolchain_type(name = "toolchain_type")
```

The rule definition in the previous section is modified so that instead of
taking in the compiler as an attribute, it declares that it consumes a
`//bar_tools:toolchain_type` toolchain.

```python
bar_binary = rule(
    implementation = _bar_binary_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        ...
        # No `_compiler` attribute anymore.
    },
    toolchains = ["//bar_tools:toolchain_type"],
)
```

The implementation function now accesses this dependency under `ctx.toolchains`
instead of `ctx.attr`, using the toolchain type as the key.

```python
def _bar_binary_impl(ctx):
    ...
    info = ctx.toolchains["//bar_tools:toolchain_type"].barcinfo
    # The rest is unchanged.
    command = "%s -l %s %s" % (
        info.compiler_path,
        info.system_lib,
        " ".join(info.arch_flags),
    )
    ...
```

`ctx.toolchains["//bar_tools:toolchain_type"]` returns the
[`ToolchainInfo` provider](/rules/lib/toplevel/platform_common#ToolchainInfo)
of whatever target Bazel resolved the toolchain dependency to. The fields of the
`ToolchainInfo` object are set by the underlying tool's rule; in the next
section, this rule is defined such that there is a `barcinfo` field that wraps
a `BarcInfo` object.

Bazel's procedure for resolving toolchains to targets is described
[below](#toolchain-resolution). Only the resolved toolchain target is actually
made a dependency of the `bar_binary` target, not the whole space of candidate
toolchains.

### Mandatory and Optional Toolchains {:#optional-toolchains}

By default, when a rule expresses a toolchain type dependency using a bare label
(as shown above), the toolchain type is considered to be **mandatory**. If Bazel
is unable to find a matching toolchain (see
[Toolchain resolution](#toolchain-resolution) below) for a mandatory toolchain
type, this is an error and analysis halts.

It is possible instead to declare an **optional** toolchain type dependency, as
follows:

```python
bar_binary = rule(
    ...
    toolchains = [
        config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False),
    ],
)
```

When an optional toolchain type cannot be resolved, analysis continues, and the
result of `ctx.toolchains["//bar_tools:toolchain_type"]` is `None`.

The [`config_common.toolchain_type`](/rules/lib/toplevel/config_common#toolchain_type)
function defaults to mandatory.

The following forms can be used:

-  Mandatory toolchain types:
   -  `toolchains = ["//bar_tools:toolchain_type"]`
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type")]`
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = True)]`
- Optional toolchain types:
   -  `toolchains = [config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False)]`

```python
bar_binary = rule(
    ...
    toolchains = [
        "//foo_tools:toolchain_type",
        config_common.toolchain_type("//bar_tools:toolchain_type", mandatory = False),
    ],
)
```

You can mix and match forms in the same rule, also. However, if the same
toolchain type is listed multiple times, it will take the most strict version,
where mandatory is more strict than optional.

### Writing aspects that use toolchains {:#writing-aspects-toolchains}

Aspects have access to the same toolchain API as rules: you can define required
toolchain types, access toolchains via the context, and use them to generate new
actions using the toolchain.

```py
bar_aspect = aspect(
    implementation = _bar_aspect_impl,
    attrs = {},
    toolchains = ['//bar_tools:toolchain_type'],
)

def _bar_aspect_impl(target, ctx):
  toolchain = ctx.toolchains['//bar_tools:toolchain_type']
  # Use the toolchain provider like in a rule.
  return []
```

## Defining toolchains {:#toolchain-definitions}

To define some toolchains for a given toolchain type, you need three things:

1. A language-specific rule representing the kind of tool or tool suite. By
   convention this rule's name is suffixed with "\_toolchain".

    1.  **Note:** The `\_toolchain` rule cannot create any build actions.
        Rather, it collects artifacts from other rules and forwards them to the
        rule that uses the toolchain. That rule is responsible for creating all
        build actions.

2. Several targets of this rule type, representing versions of the tool or tool
   suite for different platforms.

3. For each such target, an associated target of the generic
  [`toolchain`](/reference/be/platforms-and-toolchains#toolchain)
   rule, to provide metadata used by the toolchain framework. This `toolchain`
   target also refers to the `toolchain_type` associated with this toolchain.
   This means that a given `_toolchain` rule could be associated with any
   `toolchain_type`, and that only in a `toolchain` instance that uses
   this `_toolchain` rule that the rule is associated with a `toolchain_type`.

For our running example, here's a definition for a `bar_toolchain` rule. Our
example has only a compiler, but other tools such as a linker could also be
grouped underneath it.

```python
def _bar_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        barcinfo = BarcInfo(
            compiler_path = ctx.attr.compiler_path,
            system_lib = ctx.attr.system_lib,
            arch_flags = ctx.attr.arch_flags,
        ),
    )
    return [toolchain_info]

bar_toolchain = rule(
    implementation = _bar_toolchain_impl,
    attrs = {
        "compiler_path": attr.string(),
        "system_lib": attr.string(),
        "arch_flags": attr.string_list(),
    },
)
```

The rule must return a `ToolchainInfo` provider, which becomes the object that
the consuming rule retrieves using `ctx.toolchains` and the label of the
toolchain type. `ToolchainInfo`, like `struct`, can hold arbitrary field-value
pairs. The specification of exactly what fields are added to the `ToolchainInfo`
should be clearly documented at the toolchain type. In this example, the values
return wrapped in a `BarcInfo` object to reuse the schema defined above; this
style may be useful for validation and code reuse.

Now you can define targets for specific `barc` compilers.

```python
bar_toolchain(
    name = "barc_linux",
    arch_flags = [
        "--arch=Linux",
        "--debug_everything",
    ],
    compiler_path = "/path/to/barc/on/linux",
    system_lib = "/usr/lib/libbarc.so",
)

bar_toolchain(
    name = "barc_windows",
    arch_flags = [
        "--arch=Windows",
        # Different flags, no debug support on windows.
    ],
    compiler_path = "C:\\path\\on\\windows\\barc.exe",
    system_lib = "C:\\path\\on\\windows\\barclib.dll",
)
```

Finally, you create `toolchain` definitions for the two `bar_toolchain` targets.
These definitions link the language-specific targets to the toolchain type and
provide the constraint information that tells Bazel when the toolchain is
appropriate for a given platform.

```python
toolchain(
    name = "barc_linux_toolchain",
    exec_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":barc_linux",
    toolchain_type = ":toolchain_type",
)

toolchain(
    name = "barc_windows_toolchain",
    exec_compatible_with = [
        "@platforms//os:windows",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:windows",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":barc_windows",
    toolchain_type = ":toolchain_type",
)
```

The use of relative path syntax above suggests these definitions are all in the
same package, but there's no reason the toolchain type, language-specific
toolchain targets, and `toolchain` definition targets can't all be in separate
packages.

See the [`go_toolchain`](https://github.com/bazelbuild/rules_go/blob/master/go/private/go_toolchain.bzl){: .external}
for a real-world example.

### Toolchains and configurations

An important question for rule authors is, when a `bar_toolchain` target is
analyzed, what [configuration](/reference/glossary#configuration) does it see, and what transitions
should be used for dependencies? The example above uses string attributes, but
what would happen for a more complicated toolchain that depends on other targets
in the Bazel repository?

Let's see a more complex version of `bar_toolchain`:

```python
def _bar_toolchain_impl(ctx):
    # The implementation is mostly the same as above, so skipping.
    pass

bar_toolchain = rule(
    implementation = _bar_toolchain_impl,
    attrs = {
        "compiler": attr.label(
            executable = True,
            mandatory = True,
            cfg = "exec",
        ),
        "system_lib": attr.label(
            mandatory = True,
            cfg = "target",
        ),
        "arch_flags": attr.string_list(),
    },
)
```

The use of [`attr.label`](/rules/lib/toplevel/attr#label) is the same as for a standard rule,
but the meaning of the `cfg` parameter is slightly different.

The dependency from a target (called the "parent") to a toolchain via toolchain
resolution uses a special configuration transition called the "toolchain
transition". The toolchain transition keeps the configuration the same, except
that it forces the execution platform to be the same for the toolchain as for
the parent (otherwise, toolchain resolution for the toolchain could pick any
execution platform, and wouldn't necessarily be the same as for parent). This
allows any `exec` dependencies of the toolchain to also be executable for the
parent's build actions. Any of the toolchain's dependencies which use `cfg =
"target"` (or which don't specify `cfg`, since "target" is the default) are
built for the same target platform as the parent. This allows toolchain rules to
contribute both libraries (the `system_lib` attribute above) and tools (the
`compiler` attribute) to the build rules which need them. The system libraries
are linked into the final artifact, and so need to be built for the same
platform, whereas the compiler is a tool invoked during the build, and needs to
be able to run on the execution platform.

## Registering and building with toolchains {:#registering-building-toolchains}

At this point all the building blocks are assembled, and you just need to make
the toolchains available to Bazel's resolution procedure. This is done by
registering the toolchain, either in a `MODULE.bazel` file using
`register_toolchains()`, or by passing the toolchains' labels on the command
line using the `--extra_toolchains` flag.

```python
register_toolchains(
    "//bar_tools:barc_linux_toolchain",
    "//bar_tools:barc_windows_toolchain",
    # Target patterns are also permitted, so you could have also written:
    # "//bar_tools:all",
    # or even
    # "//bar_tools/...",
)
```

When using target patterns to register toolchains, the order in which the
individual toolchains are registered is determined by the following rules:

* The toolchains defined in a subpackage of a package are registered before the
  toolchains defined in the package itself.
* Within a package, toolchains are registered in the lexicographical order of
  their names.

Now when you build a target that depends on a toolchain type, an appropriate
toolchain will be selected based on the target and execution platforms.

```python
# my_pkg/BUILD

platform(
    name = "my_target_platform",
    constraint_values = [
        "@platforms//os:linux",
    ],
)

bar_binary(
    name = "my_bar_binary",
    ...
)
```

```sh
bazel build //my_pkg:my_bar_binary --platforms=//my_pkg:my_target_platform
```

Bazel will see that `//my_pkg:my_bar_binary` is being built with a platform that
has `@platforms//os:linux` and therefore resolve the
`//bar_tools:toolchain_type` reference to `//bar_tools:barc_linux_toolchain`.
This will end up building `//bar_tools:barc_linux` but not
`//bar_tools:barc_windows`.

## Toolchain resolution {:#toolchain-resolution}

Note: [Some Bazel rules](/concepts/platforms#status) do not yet support
toolchain resolution.

For each target that uses toolchains, Bazel's toolchain resolution procedure
determines the target's concrete toolchain dependencies. The procedure takes as
input a set of required toolchain types, the target platform, the list of
available execution platforms, and the list of available toolchains. Its outputs
are a selected toolchain for each toolchain type as well as a selected execution
platform for the current target.

The available execution platforms and toolchains are gathered from the
external dependency graph via
[`register_execution_platforms`](/rules/lib/globals/module#register_execution_platforms)
and
[`register_toolchains`](/rules/lib/globals/module#register_toolchains) calls in
`MODULE.bazel` files.
Additional execution platforms and toolchains may also be specified on the
command line via
[`--extra_execution_platforms`](/reference/command-line-reference#flag--extra_execution_platforms)
and
[`--extra_toolchains`](/reference/command-line-reference#flag--extra_toolchains).
The host platform is automatically included as an available execution platform.
Available platforms and toolchains are tracked as ordered lists for determinism,
with preference given to earlier items in the list.

The set of available toolchains, in priority order, is created from
`--extra_toolchains` and `register_toolchains`:

1. Toolchains registered using `--extra_toolchains` are added first. (Within
   these, the **last** toolchain has highest priority.)
2. Toolchains registered using `register_toolchains` in the transitive external
   dependency graph, in the following order: (Within these, the **first**
   mentioned toolchain has highest priority.)
  1. Toolchains registered by the root module (as in, the `MODULE.bazel` at the
     workspace root);
  2. Toolchains registered in the user's `WORKSPACE` file, including in any
     macros invoked from there;
  3. Toolchains registered by non-root modules (as in, dependencies specified by
     the root module, and their dependencies, and so forth);
  4. Toolchains registered in the "WORKSPACE suffix"; this is only used by
     certain native rules bundled with the Bazel installation.

**NOTE:** [Pseudo-targets like `:all`, `:*`, and
`/...`](/run/build#specifying-build-targets) are ordered by Bazel's package
loading mechanism, which uses a lexicographic ordering.

The resolution steps are as follows.

1. A `target_compatible_with` or `exec_compatible_with` clause *matches* a
   platform if, for each `constraint_value` in its list, the platform also has
   that `constraint_value` (either explicitly or as a default).

   If the platform has `constraint_value`s from `constraint_setting`s not
   referenced by the clause, these do not affect matching.

1. If the target being built specifies the
   [`exec_compatible_with` attribute](/reference/be/common-definitions#common.exec_compatible_with)
   (or its rule definition specifies the
   [`exec_compatible_with` argument](/rules/lib/globals/bzl#rule.exec_compatible_with)),
   the list of available execution platforms is filtered to remove
   any that do not match the execution constraints.

1. The list of available toolchains is filtered to remove any toolchains
   specifying `target_settings` that don't match the current configuration.

1. For each available execution platform, you associate each toolchain type with
   the first available toolchain, if any, that is compatible with this execution
   platform and the target platform.

1. Any execution platform that failed to find a compatible mandatory toolchain
   for one of its toolchain types is ruled out. Of the remaining platforms, the
   first one becomes the current target's execution platform, and its associated
   toolchains (if any) become dependencies of the target.

The chosen execution platform is used to run all actions that the target
generates.

In cases where the same target can be built in multiple configurations (such as
for different CPUs) within the same build, the resolution procedure is applied
independently to each version of the target.

If the rule uses [execution groups](/extending/exec-groups), each execution
group performs toolchain resolution separately, and each has its own execution
platform and toolchains.

## Debugging toolchains {:#debugging-toolchains}

If you are adding toolchain support to an existing rule, use the
`--toolchain_resolution_debug=regex` flag. During toolchain resolution, the flag
provides verbose output for toolchain types or target names that match the regex variable. You
can use `.*` to output all information. Bazel will output names of toolchains it
checks and skips during the resolution process.

If you'd like to see which [`cquery`](/query/cquery) dependencies are from toolchain
resolution, use `cquery`'s [`--transitions`](/query/cquery#transitions) flag:

```
# Find all direct dependencies of //cc:my_cc_lib. This includes explicitly
# declared dependencies, implicit dependencies, and toolchain dependencies.
$ bazel cquery 'deps(//cc:my_cc_lib, 1)'
//cc:my_cc_lib (96d6638)
@bazel_tools//tools/cpp:toolchain (96d6638)
@bazel_tools//tools/def_parser:def_parser (HOST)
//cc:my_cc_dep (96d6638)
@local_config_platform//:host (96d6638)
@bazel_tools//tools/cpp:toolchain_type (96d6638)
//:default_host_platform (96d6638)
@local_config_cc//:cc-compiler-k8 (HOST)
//cc:my_cc_lib.cc (null)
@bazel_tools//tools/cpp:grep-includes (HOST)

# Which of these are from toolchain resolution?
$ bazel cquery 'deps(//cc:my_cc_lib, 1)' --transitions=lite | grep "toolchain dependency"
  [toolchain dependency]#@local_config_cc//:cc-compiler-k8#HostTransition -> b6df211
```


Project: /_project.yaml
Book: /_book.yaml
{# disableFinding("native") #}
{# disableFinding("Native") #}
{# disableFinding(LINE_OVER_80_LINK) #}

# Legacy Macros

{% include "_buttons.html" %}

Legacy macros are unstructured functions called from `BUILD` files that can
create targets. By the end of the
[loading phase](/extending/concepts#evaluation-model), legacy macros don't exist
anymore, and Bazel sees only the concrete set of instantiated rules.

## Why you shouldn't use legacy macros (and should use Symbolic macros instead) {:#no-legacy-macros}

Where possible you should use [symbolic macros](macros.md#macros).

Symbolic macros

*   Prevent action at a distance
*   Make it possible to hide implementation details through granular visibility
*   Take typed attributes, which in turn means automatic label and select
    conversion.
*   Are more readable
*   Will soon have [lazy evaluation](macros.md/laziness)

## Usage {:#usage}

The typical use case for a macro is when you want to reuse a rule.

For example, genrule in a `BUILD` file generates a file using `//:generator`
with a `some_arg` argument hardcoded in the command:

```python
genrule(
    name = "file",
    outs = ["file.txt"],
    cmd = "$(location //:generator) some_arg > $@",
    tools = ["//:generator"],
)
```

Note: `$@` is a
[Make variable](/reference/be/make-variables#predefined_genrule_variables) that
refers to the execution-time locations of the files in the `outs` attribute
list. It is equivalent to `$(locations :file.txt)`.

If you want to generate more files with different arguments, you may want to
extract this code to a macro function. To create a macro called
`file_generator`, which has `name` and `arg` parameters, we can replace the
genrule with the following:

```python
load("//path:generator.bzl", "file_generator")

file_generator(
    name = "file",
    arg = "some_arg",
)

file_generator(
    name = "file-two",
    arg = "some_arg_two",
)

file_generator(
    name = "file-three",
    arg = "some_arg_three",
)
```

Here, you load the `file_generator` symbol from a `.bzl` file located in the
`//path` package. By putting macro function definitions in a separate `.bzl`
file, you keep your `BUILD` files clean and declarative, The `.bzl` file can be
loaded from any package in the workspace.

Finally, in `path/generator.bzl`, write the definition of the macro to
encapsulate and parameterize the original genrule definition:

```python
def file_generator(name, arg, visibility=None):
  native.genrule(
    name = name,
    outs = [name + ".txt"],
    cmd = "$(location //:generator) %s > $@" % arg,
    tools = ["//:generator"],
    visibility = visibility,
  )
```

You can also use macros to chain rules together. This example shows chained
genrules, where a genrule uses the outputs of a previous genrule as inputs:

```python
def chained_genrules(name, visibility=None):
  native.genrule(
    name = name + "-one",
    outs = [name + ".one"],
    cmd = "$(location :tool-one) $@",
    tools = [":tool-one"],
    visibility = ["//visibility:private"],
  )

  native.genrule(
    name = name + "-two",
    srcs = [name + ".one"],
    outs = [name + ".two"],
    cmd = "$(location :tool-two) $< $@",
    tools = [":tool-two"],
    visibility = visibility,
  )
```

The example only assigns a visibility value to the second genrule. This allows
macro authors to hide the outputs of intermediate rules from being depended upon
by other targets in the workspace.

Note: Similar to `$@` for outputs, `$<` expands to the locations of files in the
`srcs` attribute list.

## Expanding macros {:#expanding-macros}

When you want to investigate what a macro does, use the `query` command with
`--output=build` to see the expanded form:

```none
$ bazel query --output=build :file
# /absolute/path/test/ext.bzl:42:3
genrule(
  name = "file",
  tools = ["//:generator"],
  outs = ["//test:file.txt"],
  cmd = "$(location //:generator) some_arg > $@",
)
```

## Instantiating native rules {:#instantiating-native-rules}

Native rules (rules that don't need a `load()` statement) can be instantiated
from the [native](/rules/lib/toplevel/native) module:

```python
def my_macro(name, visibility=None):
  native.cc_library(
    name = name,
    srcs = ["main.cc"],
    visibility = visibility,
  )
```

If you need to know the package name (for example, which `BUILD` file is calling
the macro), use the function
[native.package_name()](/rules/lib/toplevel/native#package_name). Note that
`native` can only be used in `.bzl` files, and not in `BUILD` files.

## Label resolution in macros {:#label-resolution}

Since legacy macros are evaluated in the
[loading phase](concepts.md#evaluation-model), label strings such as
`"//foo:bar"` that occur in a legacy macro are interpreted relative to the
`BUILD` file in which the macro is used rather than relative to the `.bzl` file
in which it is defined. This behavior is generally undesirable for macros that
are meant to be used in other repositories, such as because they are part of a
published Starlark ruleset.

To get the same behavior as for Starlark rules, wrap the label strings with the
[`Label`](/rules/lib/builtins/Label#Label) constructor:

```python
# @my_ruleset//rules:defs.bzl
def my_cc_wrapper(name, deps = [], **kwargs):
  native.cc_library(
    name = name,
    deps = deps + select({
      # Due to the use of Label, this label is resolved within @my_ruleset,
      # regardless of its site of use.
      Label("//config:needs_foo"): [
        # Due to the use of Label, this label will resolve to the correct target
        # even if the canonical name of @dep_of_my_ruleset should be different
        # in the main repo, such as due to repo mappings.
        Label("@dep_of_my_ruleset//tools:foo"),
      ],
      "//conditions:default": [],
    }),
    **kwargs,
  )
```

## Debugging {:#debugging}

*   `bazel query --output=build //my/path:all` will show you how the `BUILD`
    file looks after evaluation. All legacy macros, globs, loops are expanded.
    Known limitation: `select` expressions are not shown in the output.

*   You may filter the output based on `generator_function` (which function
    generated the rules) or `generator_name` (the name attribute of the macro):
    `bash $ bazel query --output=build 'attr(generator_function, my_macro,
    //my/path:all)'`

*   To find out where exactly the rule `foo` is generated in a `BUILD` file, you
    can try the following trick. Insert this line near the top of the `BUILD`
    file: `cc_library(name = "foo")`. Run Bazel. You will get an exception when
    the rule `foo` is created (due to a name conflict), which will show you the
    full stack trace.

*   You can also use [print](/rules/lib/globals/all#print) for debugging. It
    displays the message as a `DEBUG` log line during the loading phase. Except
    in rare cases, either remove `print` calls, or make them conditional under a
    `debugging` parameter that defaults to `False` before submitting the code to
    the depot.

## Errors {:#errors}

If you want to throw an error, use the [fail](/rules/lib/globals/all#fail)
function. Explain clearly to the user what went wrong and how to fix their
`BUILD` file. It is not possible to catch an error.

```python
def my_macro(name, deps, visibility=None):
  if len(deps) < 2:
    fail("Expected at least two values in deps")
  # ...
```

## Conventions {:#conventions}

*   All public functions (functions that don't start with underscore) that
    instantiate rules must have a `name` argument. This argument should not be
    optional (don't give a default value).

*   Public functions should use a docstring following
    [Python conventions](https://www.python.org/dev/peps/pep-0257/#one-line-docstrings).

*   In `BUILD` files, the `name` argument of the macros must be a keyword
    argument (not a positional argument).

*   The `name` attribute of rules generated by a macro should include the name
    argument as a prefix. For example, `macro(name = "foo")` can generate a
    `cc_library` `foo` and a genrule `foo_gen`.

*   In most cases, optional parameters should have a default value of `None`.
    `None` can be passed directly to native rules, which treat it the same as if
    you had not passed in any argument. Thus, there is no need to replace it
    with `0`, `False`, or `[]` for this purpose. Instead, the macro should defer
    to the rules it creates, as their defaults may be complex or may change over
    time. Additionally, a parameter that is explicitly set to its default value
    looks different than one that is never set (or set to `None`) when accessed
    through the query language or build-system internals.

*   Macros should have an optional `visibility` argument.
