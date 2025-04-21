

Project: /_project.yaml
Book: /_book.yaml

# The Bazel Query Reference

{% include "_buttons.html" %}

This page is the reference manual for the _Bazel Query Language_ used
when you use `bazel query` to analyze build dependencies. It also
describes the output formats `bazel query` supports.

For practical use cases, see the [Bazel Query How-To](/query/guide).

## Additional query reference

In addition to `query`, which runs on the post-loading phase target graph,
Bazel includes *action graph query* and *configurable query*.

### Action graph query {:#aquery}

The action graph query (`aquery`) operates on the post-analysis Configured
Target Graph and exposes information about **Actions**, **Artifacts**, and
their relationships. `aquery` is useful when you are interested in the
properties of the Actions/Artifacts generated from the Configured Target Graph.
For example, the actual commands run and their inputs, outputs, and mnemonics.

For more details, see the [aquery reference](/query/aquery).

### Configurable query {:#cquery}

Traditional Bazel query runs on the post-loading phase target graph and
therefore has no concept of configurations and their related concepts. Notably,
it doesn't correctly resolve [select statements](/reference/be/functions#select)
and instead returns all possible resolutions of selects. However, the
configurable query environment, `cquery`, properly handles configurations but
doesn't provide all of the functionality of this original query.

For more details, see the [cquery reference](/query/cquery).


## Examples {:#examples}

How do people use `bazel query`?  Here are typical examples:

Why does the `//foo` tree depend on `//bar/baz`?
Show a path:

```
somepath(foo/..., //bar/baz:all)
```

What C++ libraries do all the `foo` tests depend on that
the `foo_bin` target does not?

```
kind("cc_library", deps(kind(".*test rule", foo/...)) except deps(//foo:foo_bin))
```

## Tokens: The lexical syntax {:#tokens}

Expressions in the query language are composed of the following
tokens:

* **Keywords**, such as `let`. Keywords are the reserved words of the
  language, and each of them is described below. The complete set
  of keywords is:

   * [`except`](#set-operations)

   * [`in`](#variables)

   * [`intersect`](#set-operations)

   * [`let`](#variables)

   * [`set`](#set)

   * [`union`](#set-operations)

* **Words**, such as "`foo/...`" or "`.*test rule`" or "`//bar/baz:all`". If a
  character sequence is "quoted" (begins and ends with a single-quote ' or
  begins and ends with a double-quote "), it is a word. If a character sequence
  is not quoted, it may still be parsed as a word. Unquoted words are sequences
  of characters drawn from the alphabet characters A-Za-z, the numerals 0-9,
  and the special characters `*/@.-_:$~[]` (asterisk, forward slash, at, period,
  hyphen, underscore, colon, dollar sign, tilde, left square brace, right square
  brace). However, unquoted words may not start with a hyphen `-` or asterisk `*`
  even though relative [target names](/concepts/labels#target-names) may start
  with those characters. As a special rule meant to simplify the handling of
  labels referring to external repositories, unquoted words that start with
  `@@` may contain `+` characters.

  Unquoted words also may not include the characters plus sign `+` or equals
  sign `=`, even though those characters are permitted in target names. When
  writing code that generates query expressions, target names should be quoted.

  Quoting _is_ necessary when writing scripts that construct Bazel query
  expressions from user-supplied values.

  ```
   //foo:bar+wiz    # WRONG: scanned as //foo:bar + wiz.
   //foo:bar=wiz    # WRONG: scanned as //foo:bar = wiz.
   "//foo:bar+wiz"  # OK.
   "//foo:bar=wiz"  # OK.
  ```

  Note that this quoting is in addition to any quoting that may be required by
  your shell, such as:

  ```posix-terminal
  bazel query ' "//foo:bar=wiz" '   # single-quotes for shell, double-quotes for Bazel.
  ```

  Keywords and operators, when quoted, are treated as ordinary words. For example, `some` is a
  keyword but "some" is a word. Both `foo` and "foo" are words.

  However, be careful when using single or double quotes in target names. When
  quoting one or more target names, use only one type of quotes (either all
  single or all double quotes).

  The following are examples of what the Java query string will be:


  ```
    'a"'a'         # WRONG: Error message: unclosed quotation.
    "a'"a"         # WRONG: Error message: unclosed quotation.
    '"a" + 'a''    # WRONG: Error message: unexpected token 'a' after query expression '"a" + '
    "'a' + "a""    # WRONG: Error message: unexpected token 'a' after query expression ''a' + '
    "a'a"          # OK.
    'a"a'          # OK.
    '"a" + "a"'    # OK
    "'a' + 'a'"    # OK
  ```

  We chose this syntax so that quote marks aren't needed in most cases. The
  (unusual) `".*test rule"` example needs quotes: it starts with a period and
  contains a space. Quoting `"cc_library"` is unnecessary but harmless.

* **Punctuation**, such as parens `()`, period `.` and comma `,`. Words
  containing punctuation (other than the exceptions listed above) must be quoted.

Whitespace characters outside of a quoted word are ignored.

## Bazel query language concepts {:#language-concepts}

The Bazel query language is a language of expressions. Every
expression evaluates to a **partially-ordered set** of targets,
or equivalently, a **graph** (DAG) of targets. This is the only
datatype.

Set and graph refer to the same datatype, but emphasize different
aspects of it, for example:

*   **Set:** The partial order of the targets is not interesting.
*   **Graph:** The partial order of targets is significant.

### Cycles in the dependency graph {:#dependency-graph-cycles}

Build dependency graphs should be acyclic.

The algorithms used by the query language are intended for use in
acyclic graphs, but are robust against cycles. The details of how
cycles are treated are not specified and should not be relied upon.

### Implicit dependencies {:#implicit-dependencies}

In addition to build dependencies that are defined explicitly in `BUILD` files,
Bazel adds additional _implicit_ dependencies to rules. Implicit dependencies
may be defined by:

- [Private attributes](/extending/rules#private_attributes_and_implicit_dependencies)
- [Toolchain requirements](/extending/toolchains#writing-rules-toolchains)

By default, `bazel query` takes implicit dependencies into account
when computing the query result. This behavior can be changed with
the `--[no]implicit_deps` option.

Note that, as query does not consider configurations, potential toolchain
**implementations** are not considered dependencies, only the
required toolchain types. See
[toolchain documentation](/extending/toolchains#writing-rules-toolchains).

### Soundness {:#soundness}

Bazel query language expressions operate over the build
dependency graph, which is the graph implicitly defined by all
rule declarations in all `BUILD` files. It is important to understand
that this graph is somewhat abstract, and does not constitute a
complete description of how to perform all the steps of a build. In
order to perform a build, a _configuration_ is required too;
see the [configurations](/docs/user-manual#configurations)
section of the User's Guide for more detail.

The result of evaluating an expression in the Bazel query language
is true _for all configurations_, which means that it may be
a conservative over-approximation, and not exactly precise. If you
use the query tool to compute the set of all source files needed
during a build, it may report more than are actually necessary
because, for example, the query tool will include all the files
needed to support message translation, even though you don't intend
to use that feature in your build.

### On the preservation of graph order {:#graph-order}

Operations preserve any ordering
constraints inherited from their subexpressions. You can think of
this as "the law of conservation of partial order". Consider an
example: if you issue a query to determine the transitive closure of
dependencies of a particular target, the resulting set is ordered
according to the dependency graph. If you filter that set to
include only the targets of `file` kind, the same
_transitive_ partial ordering relation holds between every
pair of targets in the resulting subset - even though none of
these pairs is actually directly connected in the original graph.
(There are no file-file edges in the build dependency graph).

However, while all operators _preserve_ order, some
operations, such as the [set operations](#set-operations)
don't _introduce_ any ordering constraints of their own.
Consider this expression:

```
deps(x) union y
```

The order of the final result set is guaranteed to preserve all the
ordering constraints of its subexpressions, namely, that all the
transitive dependencies of `x` are correctly ordered with
respect to each other. However, the query guarantees nothing about
the ordering of the targets in `y`, nor about the
ordering of the targets in `deps(x)` relative to those in
`y` (except for those targets in
`y` that also happen to be in `deps(x)`).

Operators that introduce ordering constraints include:
`allpaths`, `deps`, `rdeps`, `somepath`, and the target pattern wildcards
`package:*`, `dir/...`, etc.

### Sky query {:#sky-query}

_Sky Query_ is a mode of query that operates over a specified _universe scope_.

#### Special functions available only in SkyQuery

Sky Query mode has the additional query functions `allrdeps` and
`rbuildfiles`. These functions operate over the entire
universe scope (which is why they don't make sense for normal Query).

#### Specifying a universe scope

Sky Query mode is activated by passing the following two flags:
(`--universe_scope` or `--infer_universe_scope`) and
`--order_output=no`.
`--universe_scope=<target_pattern1>,...,<target_patternN>` tells query to
preload the transitive closure of the target pattern specified by the target patterns, which can
be both additive and subtractive. All queries are then evaluated in this "scope". In particular,
the [`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles) operators only return results from this scope.
`--infer_universe_scope` tells Bazel to infer a value for `--universe_scope`
from the query expression. This inferred value is the list of unique target patterns in the
query expression, but this might not be what you want. For example:

```posix-terminal
bazel query --infer_universe_scope --order_output=no "allrdeps(//my:target)"
```

The list of unique target patterns in this query expression is `["//my:target"]`, so
Bazel treats this the same as the invocation:

```posix-terminal
bazel query --universe_scope=//my:target --order_output=no "allrdeps(//my:target)"
```

But the result of that query with `--universe_scope` is only `//my:target`;
none of the reverse dependencies of `//my:target` are in the universe, by
construction! On the other hand, consider:

```posix-terminal
bazel query --infer_universe_scope --order_output=no "tests(//a/... + b/...) intersect allrdeps(siblings(rbuildfiles(my/starlark/file.bzl)))"
```

This is a meaningful query invocation that is trying to compute the test targets in the
[`tests`](#tests) expansion of the targets under some directories that
transitively depend on targets whose definition uses a certain `.bzl` file. Here,
`--infer_universe_scope` is a convenience, especially in the case where the choice of
`--universe_scope` would otherwise require you to parse the query expression yourself.

So, for query expressions that use universe-scoped operators like
[`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles) be sure to use
`--infer_universe_scope` only if its behavior is what you want.

Sky Query has some advantages and disadvantages compared to the default query. The main
disadvantage is that it cannot order its output according to graph order, and thus certain
[output formats](#output-formats) are forbidden. Its advantages are that it provides
two operators ([`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles)) that are not available in the default query.
As well, Sky Query does its work by introspecting the
[Skyframe](/reference/skyframe) graph, rather than creating a new
graph, which is what the default implementation does. Thus, there are some circumstances in which
it is faster and uses less memory.

## Expressions: Syntax and semantics of the grammar {:#expressions}

This is the grammar of the Bazel query language, expressed in EBNF notation:

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}word{{ '</var>' }}
       | let {{ '<var>' }}name{{ '</var>' }} = {{ '<var>' }}expr{{ '</var>' }} in {{ '<var>' }}expr{{ '</var>' }}
       | ({{ '<var>' }}expr{{ '</var>' }})
       | {{ '<var>' }}expr{{ '</var>' }} intersect {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} ^ {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} union {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} + {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} except {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} - {{ '<var>' }}expr{{ '</var>' }}
       | set({{ '<var>' }}word{{ '</var>' }} *)
       | {{ '<var>' }}word{{ '</var>' }} '(' {{ '<var>' }}int{{ '</var>' }} | {{ '<var>' }}word{{ '</var>' }} | {{ '<var>' }}expr{{ '</var>' }} ... ')'
```

The following sections describe each of the productions of this grammar in order.

### Target patterns {:#target-patterns}

```
expr ::= {{ '<var>' }}word{{ '</var>' }}
```

Syntactically, a _target pattern_ is just a word. It's interpreted as an
(unordered) set of targets. The simplest target pattern is a label, which
identifies a single target (file or rule). For example, the target pattern
`//foo:bar` evaluates to a set containing one element, the target, the `bar`
rule.

Target patterns generalize labels to include wildcards over packages and
targets. For example, `foo/...:all` (or just `foo/...`) is a target pattern
that evaluates to a set containing all _rules_ in every package recursively
beneath the `foo` directory; `bar/baz:all` is a target pattern that evaluates
to a set containing all the rules in the `bar/baz` package, but not its
subpackages.

Similarly, `foo/...:*` is a target pattern that evaluates to a set containing
all _targets_ (rules _and_ files) in every package recursively beneath the
`foo` directory; `bar/baz:*` evaluates to a set containing all the targets in
the `bar/baz` package, but not its subpackages.

Because the `:*` wildcard matches files as well as rules, it's often more
useful than `:all` for queries. Conversely, the `:all` wildcard (implicit in
target patterns like `foo/...`) is typically more useful for builds.

`bazel query` target patterns work the same as `bazel build` build targets do.
For more details, see [Target Patterns](/docs/user-manual#target-patterns), or
type `bazel help target-syntax`.

Target patterns may evaluate to a singleton set (in the case of a label), to a
set containing many elements (as in the case of `foo/...`, which has thousands
of elements) or to the empty set, if the target pattern matches no targets.

All nodes in the result of a target pattern expression are correctly ordered
relative to each other according to the dependency relation. So, the result of
`foo:*` is not just the set of targets in package `foo`, it is also the
_graph_ over those targets. (No guarantees are made about the relative ordering
of the result nodes against other nodes.) For more details, see the
[graph order](#graph-order) section.

### Variables {:#variables}

```none {:.devsite-disable-click-to-copy}
expr ::= let {{ '<var>' }}name{{ '</var>' }} = {{ '<var>' }}expr{{ '</var>' }}{{ '<sub>' }}1{{ '</sub>' }} in {{ '<var>' }}expr{{ '</var>' }}{{ '<sub>' }}2{{ '</sub>' }}
       | {{ '<var>' }}$name{{ '</var>' }}
```

The Bazel query language allows definitions of and references to
variables. The result of evaluation of a `let` expression is the same as
that of {{ '<var>' }}expr{{ '</var>' }}<sub>2</sub>, with all free occurrences
of variable {{ '<var>' }}name{{ '</var>' }} replaced by the value of
{{ '<var>' }}expr{{ '</var>' }}<sub>1</sub>.

For example, `let v = foo/... in allpaths($v, //common) intersect $v` is
equivalent to the `allpaths(foo/...,//common) intersect foo/...`.

An occurrence of a variable reference `name` other than in
an enclosing `let {{ '<var>' }}name{{ '</var>' }} = ...` expression is an
error. In other words, top-level query expressions cannot have free
variables.

In the above grammar productions, `name` is like _word_, but with the
additional constraint that it be a legal identifier in the C programming
language. References to the variable must be prepended with the "$" character.

Each `let` expression defines only a single variable, but you can nest them.

Both [target patterns](#target-patterns) and variable references consist of
just a single token, a word, creating a syntactic ambiguity. However, there is
no semantic ambiguity, because the subset of words that are legal variable
names is disjoint from the subset of words that are legal target patterns.

Technically speaking, `let` expressions do not increase
the expressiveness of the query language: any query expressible in
the language can also be expressed without them. However, they
improve the conciseness of many queries, and may also lead to more
efficient query evaluation.

### Parenthesized expressions {:#parenthesized-expressions}

```none {:.devsite-disable-click-to-copy}
expr ::= ({{ '<var>' }}expr{{ '</var>' }})
```

Parentheses associate subexpressions to force an order of evaluation.
A parenthesized expression evaluates to the value of its argument.

### Algebraic set operations: intersection, union, set difference {:#algebraic-set-operations}

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}expr{{ '</var>' }} intersect {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} ^ {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} union {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} + {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} except {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} - {{ '<var>' }}expr{{ '</var>' }}
```

These three operators compute the usual set operations over their arguments.
Each operator has two forms, a nominal form, such as `intersect`, and a
symbolic form, such as `^`. Both forms are equivalent; the symbolic forms are
quicker to type. (For clarity, the rest of this page uses the nominal forms.)

For example,

```
foo/... except foo/bar/...
```

evaluates to the set of targets that match `foo/...` but not `foo/bar/...`.

You can write the same query as:

```
foo/... - foo/bar/...
```

The `intersect` (`^`) and `union` (`+`) operations are commutative (symmetric);
`except` (`-`) is asymmetric. The parser treats all three operators as
left-associative and of equal precedence, so you might want parentheses. For
example, the first two of these expressions are equivalent, but the third is not:

```
x intersect y union z
(x intersect y) union z
x intersect (y union z)
```

Important: Use parentheses where there is any danger of ambiguity in reading a
query expression.

### Read targets from an external source: set {:#set}

```none {:.devsite-disable-click-to-copy}
expr ::= set({{ '<var>' }}word{{ '</var>' }} *)
```

The `set({{ '<var>' }}a{{ '</var>' }} {{ '<var>' }}b{{ '</var>' }} {{ '<var>' }}c{{ '</var>' }} ...)`
operator computes the union of a set of zero or more
[target patterns](#target-patterns), separated by whitespace (no commas).

In conjunction with the Bourne shell's `$(...)` feature, `set()` provides a
means of saving the results of one query in a regular text file, manipulating
that text file using other programs (such as standard UNIX shell tools), and then
introducing the result back into the query tool as a value for further
processing. For example:

```posix-terminal
bazel query deps(//my:target) --output=label | grep ... | sed ... | awk ... > foo

bazel query "kind(cc_binary, set($(<foo)))"
```

In the next example,`kind(cc_library, deps(//some_dir/foo:main, 5))` is
computed by filtering on the `maxrank` values using an `awk` program.

```posix-terminal
bazel query 'deps(//some_dir/foo:main)' --output maxrank | awk '($1 < 5) { print $2;} ' > foo

bazel query "kind(cc_library, set($(<foo)))"
```

In these examples, `$(<foo)` is a shorthand for `$(cat foo)`, but shell
commands other than `cat` may be used too—such as the previous `awk` command.

Note: `set()` introduces no graph ordering constraints, so path information may
be lost when saving and reloading sets of nodes using it. For more details,
see the [graph order](#graph-order) section below.

## Functions {:#functions}

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}word{{ '</var>' }} '(' {{ '<var>' }}int{{ '</var>' }} | {{ '<var>' }}word{{ '</var>' }} | {{ '<var>' }}expr{{ '</var>' }} ... ')'
```

The query language defines several functions. The name of the function
determines the number and type of arguments it requires. The following
functions are available:

* [`allpaths`](#somepath-allpaths)
* [`attr`](#attr)
* [`buildfiles`](#buildfiles)
* [`rbuildfiles`](#rbuildfiles)
* [`deps`](#deps)
* [`filter`](#filter)
* [`kind`](#kind)
* [`labels`](#labels)
* [`loadfiles`](#loadfiles)
* [`rdeps`](#rdeps)
* [`allrdeps`](#allrdeps)
* [`same_pkg_direct_rdeps`](#same_pkg_direct_rdeps)
* [`siblings`](#siblings)
* [`some`](#some)
* [`somepath`](#somepath-allpaths)
* [`tests`](#tests)
* [`visible`](#visible)



### Transitive closure of dependencies: deps {:#deps}

```none {:.devsite-disable-click-to-copy}
expr ::= deps({{ '<var>' }}expr{{ '</var>' }})
       | deps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

The `deps({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the graph formed
by the transitive closure of dependencies of its argument set
{{ '<var>' }}x{{ '</var>' }}. For example, the value of `deps(//foo)` is the
dependency graph rooted at the single node `foo`, including all its
dependencies. The value of `deps(foo/...)` is the dependency graphs whose roots
are all rules in every package beneath the `foo` directory. In this context,
'dependencies' means only rule and file targets, therefore the `BUILD` and
Starlark files needed to create these targets are not included here. For that
you should use the [`buildfiles`](#buildfiles) operator.

The resulting graph is ordered according to the dependency relation. For more
details, see the section on [graph order](#graph-order).

The `deps` operator accepts an optional second argument, which is an integer
literal specifying an upper bound on the depth of the search. So
`deps(foo:*, 0)` returns all targets in the `foo` package, while
`deps(foo:*, 1)` further includes the direct prerequisites of any target in the
`foo` package, and `deps(foo:*, 2)` further includes the nodes directly
reachable from the nodes in `deps(foo:*, 1)`, and so on. (These numbers
correspond to the ranks shown in the [`minrank`](#output-ranked) output format.)
If the {{ '<var>' }}depth{{ '</var>' }} parameter is omitted, the search is
unbounded: it computes the reflexive transitive closure of prerequisites.

### Transitive closure of reverse dependencies: rdeps {:#rdeps}

```none {:.devsite-disable-click-to-copy}
expr ::= rdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
       | rdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

The `rdeps({{ '<var>' }}u{{ '</var>' }}, {{ '<var>' }}x{{ '</var>' }})`
operator evaluates to the reverse dependencies of the argument set
{{ '<var>' }}x{{ '</var>' }} within the transitive closure of the universe set
{{ '<var>' }}u{{ '</var>' }}.

The resulting graph is ordered according to the dependency relation. See the
section on [graph order](#graph-order) for more details.

The `rdeps` operator accepts an optional third argument, which is an integer
literal specifying an upper bound on the depth of the search. The resulting
graph only includes nodes within a distance of the specified depth from any
node in the argument set. So `rdeps(//foo, //common, 1)` evaluates to all nodes
in the transitive closure of `//foo` that directly depend on `//common`. (These
numbers correspond to the ranks shown in the [`minrank`](#output-ranked) output
format.) If the {{ '<var>' }}depth{{ '</var>' }} parameter is omitted, the
search is unbounded.

### Transitive closure of all reverse dependencies: allrdeps {:#allrdeps}

```
expr ::= allrdeps({{ '<var>' }}expr{{ '</var>' }})
       | allrdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

Note: Only available with [Sky Query](#sky-query)

The `allrdeps` operator behaves just like the [`rdeps`](#rdeps)
operator, except that the "universe set" is whatever the `--universe_scope` flag
evaluated to, instead of being separately specified. Thus, if
`--universe_scope=//foo/...` was passed, then `allrdeps(//bar)` is
equivalent to `rdeps(//foo/..., //bar)`.

### Direct reverse dependencies in the same package: same_pkg_direct_rdeps {:#same_pkg_direct_rdeps}

```
expr ::= same_pkg_direct_rdeps({{ '<var>' }}expr{{ '</var>' }})
```

The `same_pkg_direct_rdeps({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the full set of targets
that are in the same package as a target in the argument set, and which directly depend on it.

### Dealing with a target's package: siblings {:#siblings}

```
expr ::= siblings({{ '<var>' }}expr{{ '</var>' }})
```

The `siblings({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the full set of targets that are in
the same package as a target in the argument set.

### Arbitrary choice: some {:#some}

```
expr ::= some({{ '<var>' }}expr{{ '</var>' }})
       | some({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}count{{ '</var> '}})
```

The `some({{ '<var>' }}x{{ '</var>' }}, {{ '<var>' }}k{{ '</var>' }})` operator
selects at most {{ '<var>' }}k{{ '</var>' }} targets arbitrarily from its
argument set {{ '<var>' }}x{{ '</var>' }}, and evaluates to a set containing
only those targets. Parameter {{ '<var>' }}k{{ '</var>' }} is optional; if
missing, the result will be a singleton set containing only one target
arbitrarily selected. If the size of argument set {{ '<var>' }}x{{ '</var>' }} is
smaller than {{ '<var>' }}k{{ '</var>' }}, the whole argument set
{{ '<var>' }}x{{ '</var>' }} will be returned.

For example, the expression `some(//foo:main union //bar:baz)` evaluates to a
singleton set containing either `//foo:main` or `//bar:baz`—though which
one is not defined. The expression `some(//foo:main union //bar:baz, 2)` or
`some(//foo:main union //bar:baz, 3)` returns both `//foo:main` and
`//bar:baz`.

If the argument is a singleton, then `some`
computes the identity function: `some(//foo:main)` is
equivalent to `//foo:main`.

It is an error if the specified argument set is empty, as in the
expression `some(//foo:main intersect //bar:baz)`.

### Path operators: somepath, allpaths {:#somepath-allpaths}

```
expr ::= somepath({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
       | allpaths({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `somepath({{ '<var>' }}S{{ '</var>' }}, {{ '<var>' }}E{{ '</var>' }})` and
`allpaths({{ '<var>' }}S{{ '</var>' }}, {{ '<var>' }}E{{ '</var>' }})` operators compute
paths between two sets of targets. Both queries accept two
arguments, a set {{ '<var>' }}S{{ '</var>' }} of starting points and a set
{{ '<var>' }}E{{ '</var>' }} of ending points. `somepath` returns the
graph of nodes on _some_ arbitrary path from a target in
{{ '<var>' }}S{{ '</var>' }} to a target in {{ '<var>' }}E{{ '</var>' }}; `allpaths`
returns the graph of nodes on _all_ paths from any target in
{{ '<var>' }}S{{ '</var>' }} to any target in {{ '<var>' }}E{{ '</var>' }}.

The resulting graphs are ordered according to the dependency relation.
See the section on [graph order](#graph-order) for more details.

<table>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/somepath1.svg" alt="Somepath">
        <figcaption><code>somepath(S1 + S2, E)</code>, one possible result.</figcaption>
      </figure>
<!-- digraph somepath1 {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1;
  n2 [fillcolor="pink",style=filled];
  n3 [fillcolor="pink",style=filled];
  n4 [fillcolor="pink",style=filled,label="E"];
  n5; n6;
  n7 [fillcolor="pink",style=filled,label="S1"];
  n8 [label="S2"];
  n9;
  n10 [fillcolor="pink",style=filled];
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
    <td>
      <figure>
        <img src="/docs/images/somepath2.svg" alt="Somepath">
        <figcaption><code>somepath(S1 + S2, E)</code>, another possible result.</figcaption>
      </figure>
<!-- digraph somepath2 {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1; n2; n3;
  n4 [fillcolor="pink",style=filled,label="E"];
  n5;
  n6 [fillcolor="pink",style=filled];
  n7 [label="S1"];
  n8 [fillcolor="pink",style=filled,label="S2"];
  n9; n10;
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
    <td>
      <figure>
        <img src="/docs/images/allpaths.svg" alt="Allpaths">
        <figcaption><code>allpaths(S1 + S2, E)</code></figcaption>
      </figure>
<!-- digraph allpaths {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1;
  n2 [fillcolor="pink",style=filled];
  n3 [fillcolor="pink",style=filled];
  n4 [fillcolor="pink",style=filled,label="E"];
  n5 [fillcolor="pink",style=filled];
  n6 [fillcolor="pink",style=filled];
  n7 [fillcolor="pink",style=filled, label="S1"];
  n8 [fillcolor="pink",style=filled, label="S2"];
  n9;
  n10 [fillcolor="pink",style=filled];
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
  </tr>
</table>

### Target kind filtering: kind {:#kind}

```
expr ::= kind({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `kind({{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards those targets
that are not of the expected kind. The {{ '<var>' }}pattern{{ '</var>' }}
parameter specifies what kind of target to match.

For example, the kinds for the four targets defined by the `BUILD` file
(for package `p`) shown below are illustrated in the table:

<table>
  <tr>
    <th>Code</th>
    <th>Target</th>
    <th>Kind</th>
  </tr>
  <tr>
    <td rowspan="4">
      <pre>
        genrule(
            name = "a",
            srcs = ["a.in"],
            outs = ["a.out"],
            cmd = "...",
        )
      </pre>
    </td>
    <td><code>//p:a</code></td>
    <td>genrule rule</td>
  </tr>
  <tr>
    <td><code>//p:a.in</code></td>
    <td>source file</td>
  </tr>
  <tr>
    <td><code>//p:a.out</code></td>
    <td>generated file</td>
  </tr>
  <tr>
    <td><code>//p:BUILD</code></td>
    <td>source file</td>
  </tr>
</table>

Thus, `kind("cc_.* rule", foo/...)` evaluates to the set
of all `cc_library`, `cc_binary`, etc,
rule targets beneath `foo`, and `kind("source file", deps(//foo))`
evaluates to the set of all source files in the transitive closure
of dependencies of the `//foo` target.

Quotation of the {{ '<var>' }}pattern{{ '</var>' }} argument is often required
because without it, many [regular expressions](#regex), such as `source
file` and `.*_test`, are not considered words by the parser.

When matching for `package group`, targets ending in
`:all` may not yield any results. Use `:all-targets` instead.

### Target name filtering: filter {:#filter}

```
expr ::= filter({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `filter({{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards targets whose
labels (in absolute form) do not match the pattern; it
evaluates to a subset of its input.

The first argument, {{ '<var>' }}pattern{{ '</var>' }} is a word containing a
[regular expression](#regex) over target names. A `filter` expression
evaluates to the set containing all targets {{ '<var>' }}x{{ '</var>' }} such that
{{ '<var>' }}x{{ '</var>' }} is a member of the set {{ '<var>' }}input{{ '</var>' }} and the
label (in absolute form, such as `//foo:bar`)
of {{ '<var>' }}x{{ '</var>' }} contains an (unanchored) match
for the regular expression {{ '<var>' }}pattern{{ '</var>' }}. Since all
target names start with `//`, it may be used as an alternative
to the `^` regular expression anchor.

This operator often provides a much faster and more robust alternative to the
`intersect` operator. For example, in order to see all
`bar` dependencies of the `//foo:foo` target, one could
evaluate

```
deps(//foo) intersect //bar/...
```

This statement, however, will require parsing of all `BUILD` files in the
`bar` tree, which will be slow and prone to errors in
irrelevant `BUILD` files. An alternative would be:

```
filter(//bar, deps(//foo))
```

which would first calculate the set of `//foo` dependencies and
then would filter only targets matching the provided pattern—in other
words, targets with names containing `//bar` as a substring.

Another common use of the `filter({{ '<var>' }}pattern{{ '</var>' }},
{{ '<var>' }}expr{{ '</var>' }})` operator is to filter specific files by their
name or extension. For example,

```
filter("\.cc$", deps(//foo))
```

will provide a list of all `.cc` files used to build `//foo`.

### Rule attribute filtering: attr {:#attr}

```
expr ::= attr({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The
`attr({{ '<var>' }}name{{ '</var>' }}, {{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards targets that aren't
rules, rule targets that do not have attribute {{ '<var>' }}name{{ '</var>' }}
defined or rule targets where the attribute value does not match the provided
[regular expression](#regex) {{ '<var>' }}pattern{{ '</var>' }}; it evaluates
to a subset of its input.

The first argument, {{ '<var>' }}name{{ '</var>' }} is the name of the rule
attribute that should be matched against the provided
[regular expression](#regex) pattern. The second argument,
{{ '<var>' }}pattern{{ '</var>' }} is a regular expression over the attribute
values. An `attr` expression evaluates to the set containing all targets
{{ '<var>' }}x{{ '</var>' }} such that  {{ '<var>' }}x{{ '</var>' }} is a
member of the set {{ '<var>' }}input{{ '</var>' }}, is a rule with the defined
attribute {{ '<var>' }}name{{ '</var>' }} and the attribute value contains an
(unanchored) match for the regular expression
{{ '<var>' }}pattern{{ '</var>' }}. If {{ '<var>' }}name{{ '</var>' }} is an
optional attribute and rule does not specify it explicitly then default
attribute value will be used for comparison. For example,

```
attr(linkshared, 0, deps(//foo))
```

will select all `//foo` dependencies that are allowed to have a
linkshared attribute (such as, `cc_binary` rule) and have it either
explicitly set to 0 or do not set it at all but default value is 0 (such as for
`cc_binary` rules).

List-type attributes (such as `srcs`, `data`, etc) are
converted to strings of the form `[value<sub>1</sub>, ..., value<sub>n</sub>]`,
starting with a `[` bracket, ending with a `]` bracket
and using "`, `" (comma, space) to delimit multiple values.
Labels are converted to strings by using the absolute form of the
label. For example, an attribute `deps=[":foo",
"//otherpkg:bar", "wiz"]` would be converted to the
string `[//thispkg:foo, //otherpkg:bar, //thispkg:wiz]`.
Brackets are always present, so the empty list would use string value `[]`
for matching purposes. For example,

```
attr("srcs", "\[\]", deps(//foo))
```

will select all rules among `//foo` dependencies that have an
empty `srcs` attribute, while

```
attr("data", ".{3,}", deps(//foo))
```

will select all rules among `//foo` dependencies that specify at
least one value in the `data` attribute (every label is at least
3 characters long due to the `//` and `:`).

To select all rules among `//foo` dependencies with a particular `value` in a
list-type attribute, use

```
attr("tags", "[\[ ]value[,\]]", deps(//foo))
```

This works because the character before `value` will be `[` or a space and the
character after `value` will be a comma or `]`.

To select all rules among `//foo` dependencies with a particular `key` and
`value` in a dict-type attribute, use

```
attr("some_dict_attribute", "[\{ ]key=value[,\}]", deps(//foo))
```

This would select `//foo` if `//foo` is defined as

```
some_rule(
  name = "foo",
  some_dict_attribute = {
    "key": "value",
  },
)
```

This works because the character before `key=value` will be `{` or a space and
the character after `key=value` will be a comma or `}`.

### Rule visibility filtering: visible {:#visible}

```
expr ::= visible({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `visible({{ '<var>' }}predicate{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})` operator
applies a filter to a set of targets, and discards targets without the
required visibility.

The first argument, {{ '<var>' }}predicate{{ '</var>' }}, is a set of targets that all targets
in the output must be visible to. A {{ '<var>' }}visible{{ '</var>' }} expression
evaluates to the set containing all targets {{ '<var>' }}x{{ '</var>' }} such that {{ '<var>' }}x{{ '</var>' }}
is a member of the set {{ '<var>' }}input{{ '</var>' }}, and for all targets {{ '<var>' }}y{{ '</var>' }} in
{{ '<var>' }}predicate{{ '</var>' }} {{ '<var>' }}x{{ '</var>' }} is visible to {{ '<var>' }}y{{ '</var>' }}. For example:

```
visible(//foo, //bar:*)
```

will select all targets in the package `//bar` that `//foo`
can depend on without violating visibility restrictions.

### Evaluation of rule attributes of type label: labels {:#labels}

```
expr ::= labels({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `labels({{ '<var>' }}attr_name{{ '</var>' }}, {{ '<var>' }}inputs{{ '</var>' }})`
operator returns the set of targets specified in the
attribute {{ '<var>' }}attr_name{{ '</var>' }} of type "label" or "list of label" in
some rule in set {{ '<var>' }}inputs{{ '</var>' }}.

For example, `labels(srcs, //foo)` returns the set of
targets appearing in the `srcs` attribute of
the `//foo` rule. If there are multiple rules
with `srcs` attributes in the {{ '<var>' }}inputs{{ '</var>' }} set, the
union of their `srcs` is returned.

### Expand and filter test_suites: tests {:#tests}

```
expr ::= tests({{ '<var>' }}expr{{ '</var>' }})
```

The `tests({{ '<var>' }}x{{ '</var>' }})` operator returns the set of all test
rules in set {{ '<var>' }}x{{ '</var>' }}, expanding any `test_suite` rules into
the set of individual tests that they refer to, and applying filtering by
`tag` and `size`.

By default, query evaluation
ignores any non-test targets in all `test_suite` rules. This can be
changed to errors with the `--strict_test_suite` option.

For example, the query `kind(test, foo:*)` lists all
the `*_test` and `test_suite` rules
in the `foo` package. All the results are (by
definition) members of the `foo` package. In contrast,
the query `tests(foo:*)` will return all of the
individual tests that would be executed by `bazel test
foo:*`: this may include tests belonging to other packages,
that are referenced directly or indirectly
via `test_suite` rules.

### Package definition files: buildfiles {:#buildfiles}

```
expr ::= buildfiles({{ '<var>' }}expr{{ '</var>' }})
```

The `buildfiles({{ '<var>' }}x{{ '</var>' }})` operator returns the set
of files that define the packages of each target in
set {{ '<var>' }}x{{ '</var>' }}; in other words, for each package, its `BUILD` file,
plus any .bzl files it references via `load`. Note that this
also returns the `BUILD` files of the packages containing these
`load`ed files.

This operator is typically used when determining what files or
packages are required to build a specified target, often in conjunction with
the [`--output package`](#output-package) option, below). For example,

```posix-terminal
bazel query 'buildfiles(deps(//foo))' --output package
```

returns the set of all packages on which `//foo` transitively depends.

Note: A naive attempt at the above query would omit
the `buildfiles` operator and use only `deps`,
but this yields an incorrect result: while the result contains the
majority of needed packages, those packages that contain only files
that are `load()`'ed will be missing.

Warning: Bazel pretends each `.bzl` file produced by
`buildfiles` has a corresponding target (for example, file `a/b.bzl` =>
target `//a:b.bzl`), but this isn't necessarily the case. Therefore,
`buildfiles` doesn't compose well with other query operators and its results can be
misleading when formatted in a structured way, such as
[`--output=xml`](#xml).

### Package definition files: rbuildfiles {:#rbuildfiles}

```
expr ::= rbuildfiles({{ '<var>' }}word{{ '</var>' }}, ...)
```

Note: Only available with [Sky Query](#sky-query).

The `rbuildfiles` operator takes a comma-separated list of path fragments and returns
the set of `BUILD` files that transitively depend on these path fragments. For instance, if
`//foo` is a package, then `rbuildfiles(foo/BUILD)` will return the
`//foo:BUILD` target. If the `foo/BUILD` file has
`load('//bar:file.bzl'...` in it, then `rbuildfiles(bar/file.bzl)` will
return the `//foo:BUILD` target, as well as the targets for any other `BUILD` files that
load `//bar:file.bzl`

The scope of the <scope>rbuildfiles</scope> operator is the universe specified by the
`--universe_scope` flag. Files that do not correspond directly to `BUILD` files and `.bzl`
files do not affect the results. For instance, source files (like `foo.cc`) are ignored,
even if they are explicitly mentioned in the `BUILD` file. Symlinks, however, are respected, so that
if `foo/BUILD` is a symlink to `bar/BUILD`, then
`rbuildfiles(bar/BUILD)` will include `//foo:BUILD` in its results.

The `rbuildfiles` operator is almost morally the inverse of the
[`buildfiles`](#buildfiles) operator. However, this moral inversion
holds more strongly in one direction: the outputs of `rbuildfiles` are just like the
inputs of `buildfiles`; the former will only contain `BUILD` file targets in packages,
and the latter may contain such targets. In the other direction, the correspondence is weaker. The
outputs of the `buildfiles` operator are targets corresponding to all packages and .`bzl`
files needed by a given input. However, the inputs of the `rbuildfiles` operator are
not those targets, but rather the path fragments that correspond to those targets.

### Package definition files: loadfiles {:#loadfiles}

```
expr ::= loadfiles({{ '<var>' }}expr{{ '</var>' }})
```

The `loadfiles({{ '<var>' }}x{{ '</var>' }})` operator returns the set of
Starlark files that are needed to load the packages of each target in
set {{ '<var>' }}x{{ '</var>' }}. In other words, for each package, it returns the
.bzl files that are referenced from its `BUILD` files.

Warning: Bazel pretends each of these .bzl files has a corresponding target
(for example, file `a/b.bzl` => target `//a:b.bzl`), but this isn't
necessarily the case. Therefore, `loadfiles` doesn't compose well with other query
operators and its results can be misleading when formatted in a structured way, such as
[`--output=xml`](#xml).

## Output formats {:#output-formats}

`bazel query` generates a graph.
You specify the content, format, and ordering by which
`bazel query` presents this graph
by means of the `--output` command-line option.

When running with [Sky Query](#sky-query), only output formats that are compatible with
unordered output are allowed. Specifically, `graph`, `minrank`, and
`maxrank` output formats are forbidden.

Some of the output formats accept additional options. The name of
each output option is prefixed with the output format to which it
applies, so `--graph:factored` applies only
when `--output=graph` is being used; it has no effect if
an output format other than `graph` is used. Similarly,
`--xml:line_numbers` applies only when `--output=xml`
is being used.

### On the ordering of results {:#results-ordering}

Although query expressions always follow the "[law of
conservation of graph order](#graph-order)", _presenting_ the results may be done
in either a dependency-ordered or unordered manner. This does **not**
influence the targets in the result set or how the query is computed. It only
affects how the results are printed to stdout. Moreover, nodes that are
equivalent in the dependency order may or may not be ordered alphabetically.
The `--order_output` flag can be used to control this behavior.
(The `--[no]order_results` flag has a subset of the functionality
of the `--order_output` flag and is deprecated.)

The default value of this flag is `auto`, which prints results in **lexicographical
order**. However, when `somepath(a,b)` is used, the results will be printed in
`deps` order instead.

When this flag is `no` and `--output` is one of
`build`, `label`, `label_kind`, `location`, `package`, `proto`, or
`xml`, the outputs will be printed in arbitrary order. **This is
generally the fastest option**. It is not supported though when
`--output` is one of `graph`, `minrank` or
`maxrank`: with these formats, Bazel always prints results
ordered by the dependency order or rank.

When this flag is `deps`, Bazel prints results in some topological order—that is,
dependents first and dependencies after. However, nodes that are unordered by the
dependency order (because there is no path from either one to the other) may be
printed in any order.

When this flag is `full`, Bazel prints nodes in a fully deterministic (total) order.
First, all nodes are sorted alphabetically. Then, each node in the list is used as the start of a
post-order depth-first search in which outgoing edges to unvisited nodes are traversed in
alphabetical order of the successor nodes. Finally, nodes are printed in the reverse of the order
in which they were visited.

Printing nodes in this order may be slower, so it should be used only when determinism is
important.

### Print the source form of targets as they would appear in BUILD {:#target-source-form}

```
--output build
```

With this option, the representation of each target is as if it were
hand-written in the BUILD language. All variables and function calls
(such as glob, macros) are expanded, which is useful for seeing the effect
of Starlark macros. Additionally, each effective rule reports a
`generator_name` and/or `generator_function`) value,
giving the name of the macro that was evaluated to produce the effective rule.

Although the output uses the same syntax as `BUILD` files, it is not
guaranteed to produce a valid `BUILD` file.

### Print the label of each target {:#print-label-target}

```
--output label
```

With this option, the set of names (or _labels_) of each target
in the resulting graph is printed, one label per line, in
topological order (unless `--noorder_results` is specified, see
[notes on the ordering of results](#result-order)).
(A topological ordering is one in which a graph
node appears earlier than all of its successors.)  Of course there
are many possible topological orderings of a graph (_reverse
postorder_ is just one); which one is chosen is not specified.

When printing the output of a `somepath` query, the order
in which the nodes are printed is the order of the path.

Caveat: in some corner cases, there may be two distinct targets with
the same label; for example, a `sh_binary` rule and its
sole (implicit) `srcs` file may both be called
`foo.sh`. If the result of a query contains both of
these targets, the output (in `label` format) will appear
to contain a duplicate. When using the `label_kind` (see
below) format, the distinction becomes clear: the two targets have
the same name, but one has kind `sh_binary rule` and the
other kind `source file`.

### Print the label and kind of each target {:#print-target-label}

```
--output label_kind
```

Like `label`, this output format prints the labels of
each target in the resulting graph, in topological order, but it
additionally precedes the label by the [_kind_](#kind) of the target.

### Print targets in protocol buffer format {:#print-target-proto}

```
--output proto
```

Prints the query output as a
[`QueryResult`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffer.

### Print targets in length-delimited protocol buffer format {:#print-target-length-delimited-proto}

```
--output streamed_proto
```

Prints a
[length-delimited](https://protobuf.dev/programming-guides/encoding/#size-limit)
stream of
[`Target`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffers. This is useful to _(i)_ get around
[size limitations](https://protobuf.dev/programming-guides/encoding/#size-limit)
of protocol buffers when there are too many targets to fit in a single
`QueryResult` or _(ii)_ to start processing while Bazel is still outputting.

### Print targets in text proto format {:#print-target-textproto}

```
--output textproto
```

Similar to `--output proto`, prints the
[`QueryResult`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffer but in
[text format](https://protobuf.dev/reference/protobuf/textformat-spec/).

### Print targets in ndjson format {:#print-target-streamed-jsonproto}

```
--output streamed_jsonproto
```

Similar to `--output streamed_proto`, prints a stream of
[`Target`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffers but in [ndjson](https://github.com/ndjson/ndjson-spec) format.

### Print the label of each target, in rank order {:#print-target-label-rank-order}

```
--output minrank --output maxrank
```

Like `label`, the `minrank`
and `maxrank` output formats print the labels of each
target in the resulting graph, but instead of appearing in
topological order, they appear in rank order, preceded by their
rank number. These are unaffected by the result ordering
`--[no]order_results` flag (see [notes on
the ordering of results](#result-order)).

There are two variants of this format: `minrank` ranks
each node by the length of the shortest path from a root node to it.
"Root" nodes (those which have no incoming edges) are of rank 0,
their successors are of rank 1, etc. (As always, edges point from a
target to its prerequisites: the targets it depends upon.)

`maxrank` ranks each node by the length of the longest
path from a root node to it. Again, "roots" have rank 0, all other
nodes have a rank which is one greater than the maximum rank of all
their predecessors.

All nodes in a cycle are considered of equal rank. (Most graphs are
acyclic, but cycles do occur
simply because `BUILD` files contain erroneous cycles.)

These output formats are useful for discovering how deep a graph is.
If used for the result of a `deps(x)`, `rdeps(x)`,
or `allpaths` query, then the rank number is equal to the
length of the shortest (with `minrank`) or longest
(with `maxrank`) path from `x` to a node in
that rank. `maxrank` can be used to determine the
longest sequence of build steps required to build a target.

Note: The ranked output of a `somepath` query is
basically meaningless because `somepath` doesn't
guarantee to return either a shortest or a longest path, and it may
include "transitive" edges from one path node to another that are
not direct edges in original graph.

For example, the graph on the left yields the outputs on the right
when `--output minrank` and `--output maxrank`
are specified, respectively.

<table>
  <tr>
    <td><img src="/docs/images/out-ranked.svg" alt="Out ranked">
    </td>
    <td>
      <pre>
      minrank

      0 //c:c
      1 //b:b
      1 //a:a
      2 //b:b.cc
      2 //a:a.cc
      </pre>
    </td>
    <td>
      <pre>
      maxrank

      0 //c:c
      1 //b:b
      2 //a:a
      2 //b:b.cc
      3 //a:a.cc
      </pre>
    </td>
  </tr>
</table>

### Print the location of each target {:#print-target-location}

```
--output location
```

Like `label_kind`, this option prints out, for each
target in the result, the target's kind and label, but it is
prefixed by a string describing the location of that target, as a
filename and line number. The format resembles the output of
`grep`. Thus, tools that can parse the latter (such as Emacs
or vi) can also use the query output to step through a series of
matches, allowing the Bazel query tool to be used as a
dependency-graph-aware "grep for BUILD files".

The location information varies by target kind (see the [kind](#kind) operator). For rules, the
location of the rule's declaration within the `BUILD` file is printed.
For source files, the location of line 1 of the actual file is
printed. For a generated file, the location of the rule that
generates it is printed. (The query tool does not have sufficient
information to find the actual location of the generated file, and
in any case, it might not exist if a build has not yet been performed.)

### Print the set of packages {:#print-package-set}

```--output package```

This option prints the name of all packages to which
some target in the result set belongs. The names are printed in
lexicographical order; duplicates are excluded. Formally, this
is a _projection_ from the set of labels (package, target) onto
packages.

Packages in external repositories are formatted as
`@repo//foo/bar` while packages in the main repository are
formatted as `foo/bar`.

In conjunction with the `deps(...)` query, this output
option can be used to find the set of packages that must be checked
out in order to build a given set of targets.

### Display a graph of the result {:#display-result-graph}

```--output graph```

This option causes the query result to be printed as a directed
graph in the popular AT&amp;T GraphViz format. Typically the
result is saved to a file, such as `.png` or `.svg`.
(If the `dot` program is not installed on your workstation, you
can install it using the command `sudo apt-get install graphviz`.)
See the example section below for a sample invocation.

This output format is particularly useful for `allpaths`,
`deps`, or `rdeps` queries, where the result
includes a _set of paths_ that cannot be easily visualized when
rendered in a linear form, such as with `--output label`.

By default, the graph is rendered in a _factored_ form. That is,
topologically-equivalent nodes are merged together into a single
node with multiple labels. This makes the graph more compact
and readable, because typical result graphs contain highly
repetitive patterns. For example, a `java_library` rule
may depend on hundreds of Java source files all generated by the
same `genrule`; in the factored graph, all these files
are represented by a single node. This behavior may be disabled
with the `--nograph:factored` option.

#### `--graph:node_limit {{ '<var>' }}n{{ '</var>' }}` {:#graph-nodelimit}

The option specifies the maximum length of the label string for a
graph node in the output. Longer labels will be truncated; -1
disables truncation. Due to the factored form in which graphs are
usually printed, the node labels may be very long. GraphViz cannot
handle labels exceeding 1024 characters, which is the default value
of this option. This option has no effect unless
`--output=graph` is being used.

#### `--[no]graph:factored` {:#graph-factored}

By default, graphs are displayed in factored form, as explained
[above](#output-graph).
When `--nograph:factored` is specified, graphs are
printed without factoring. This makes visualization using GraphViz
impractical, but the simpler format may ease processing by other
tools (such as grep). This option has no effect
unless `--output=graph` is being used.

### XML {:#xml}

```--output xml```

This option causes the resulting targets to be printed in an XML
form. The output starts with an XML header such as this

```
  <?xml version="1.0" encoding="UTF-8"?>
  <query version="2">
```

<!-- The docs should continue to document version 2 into perpetuity,
     even if we add new formats, to handle clients synced to old CLs. -->

and then continues with an XML element for each target
in the result graph, in topological order (unless
[unordered results](#result-order) are requested),
and then finishes with a terminating

```
</query>
```

Simple entries are emitted for targets of `file` kind:

```
  <source-file name='//foo:foo_main.cc' .../>
  <generated-file name='//foo:libfoo.so' .../>
```

But for rules, the XML is structured and contains definitions of all
the attributes of the rule, including those whose value was not
explicitly specified in the rule's `BUILD` file.

Additionally, the result includes `rule-input` and
`rule-output` elements so that the topology of the
dependency graph can be reconstructed without having to know that,
for example, the elements of the `srcs` attribute are
forward dependencies (prerequisites) and the contents of the
`outs` attribute are backward dependencies (consumers).

`rule-input` elements for [implicit dependencies](#implicit_deps) are suppressed if
`--noimplicit_deps` is specified.

```
  <rule class='cc_binary rule' name='//foo:foo' ...>
    <list name='srcs'>
      <label value='//foo:foo_main.cc'/>
      <label value='//foo:bar.cc'/>
      ...
    </list>
    <list name='deps'>
      <label value='//common:common'/>
      <label value='//collections:collections'/>
      ...
    </list>
    <list name='data'>
      ...
    </list>
    <int name='linkstatic' value='0'/>
    <int name='linkshared' value='0'/>
    <list name='licenses'/>
    <list name='distribs'>
      <distribution value="INTERNAL" />
    </list>
    <rule-input name="//common:common" />
    <rule-input name="//collections:collections" />
    <rule-input name="//foo:foo_main.cc" />
    <rule-input name="//foo:bar.cc" />
    ...
  </rule>
```

Every XML element for a target contains a `name`
attribute, whose value is the target's label, and
a `location` attribute, whose value is the target's
location as printed by the [`--output location`](#print-target-location).

#### `--[no]xml:line_numbers` {:#xml-linenumbers}

By default, the locations displayed in the XML output contain line numbers.
When `--noxml:line_numbers` is specified, line numbers are not printed.

#### `--[no]xml:default_values` {:#xml-defaultvalues}

By default, XML output does not include rule attribute whose value
is the default value for that kind of attribute (for example, if it
were not specified in the `BUILD` file, or the default value was
provided explicitly). This option causes such attribute values to
be included in the XML output.

### Regular expressions {:#regular-expressions}

Regular expressions in the query language use the Java regex library, so you can use the
full syntax for
[`java.util.regex.Pattern`](https://docs.oracle.com/javase/8/docs/api/java/util/regex/Pattern.html){: .external}.

### Querying with external repositories {:#querying-external-repositories}

If the build depends on rules from [external repositories](/external/overview)
then query results will include these dependencies. For
example, if `//foo:bar` depends on `@other-repo//baz:lib`, then
`bazel query 'deps(//foo:bar)'` will list `@other-repo//baz:lib` as a
dependency.


Project: /_project.yaml
Book: /_book.yaml

#  Configurable Query (cquery)

{% include "_buttons.html" %}

`cquery` is a variant of [`query`](/query/language) that correctly handles
[`select()`](/docs/configurable-attributes) and build options' effects on the build
graph.

It achieves this by running over the results of Bazel's [analysis
phase](/extending/concepts#evaluation-model),
which integrates these effects. `query`, by contrast, runs over the results of
Bazel's loading phase, before options are evaluated.

For example:

<pre>
$ cat > tree/BUILD &lt;&lt;EOF
sh_library(
    name = "ash",
    deps = select({
        ":excelsior": [":manna-ash"],
        ":americana": [":white-ash"],
        "//conditions:default": [":common-ash"],
    }),
)
sh_library(name = "manna-ash")
sh_library(name = "white-ash")
sh_library(name = "common-ash")
config_setting(
    name = "excelsior",
    values = {"define": "species=excelsior"},
)
config_setting(
    name = "americana",
    values = {"define": "species=americana"},
)
EOF
</pre>

<pre>
# Traditional query: query doesn't know which select() branch you will choose,
# so it conservatively lists all of possible choices, including all used config_settings.
$ bazel query "deps(//tree:ash)" --noimplicit_deps
//tree:americana
//tree:ash
//tree:common-ash
//tree:excelsior
//tree:manna-ash
//tree:white-ash

# cquery: cquery lets you set build options at the command line and chooses
# the exact dependencies that implies (and also the config_setting targets).
$ bazel cquery "deps(//tree:ash)" --define species=excelsior --noimplicit_deps
//tree:ash (9f87702)
//tree:manna-ash (9f87702)
//tree:americana (9f87702)
//tree:excelsior (9f87702)
</pre>

Each result includes a [unique identifier](#configurations) `(9f87702)` of
the [configuration](/reference/glossary#configuration) the
target is built with.

Since `cquery` runs over the configured target graph. it doesn't have insight
into artifacts like build actions nor access to [`test_suite`](/reference/be/general#test_suite)
rules as they are not configured targets. For the former, see [`aquery`](/query/aquery).

## Basic syntax {:#basic-syntax}

A simple `cquery` call looks like:

`bazel cquery "function(//target)"`

The query expression `"function(//target)"` consists of the following:

*   **`function(...)`** is the function to run on the target. `cquery`
    supports most
    of `query`'s [functions](/query/language#functions), plus a
    few new ones.
*   **`//target`** is the expression fed to the function. In this example, the
    expression is a simple target. But the query language also allows nesting of functions.
    See the [Query guide](/query/guide) for examples.


`cquery` requires a target to run through the [loading and analysis](/extending/concepts#evaluation-model)
phases. Unless otherwise specified, `cquery` parses the target(s) listed in the
query expression. See [`--universe_scope`](#universe-scope)
for querying dependencies of top-level build targets.

## Configurations {:#configurations}

The line:

<pre>
//tree:ash (9f87702)
</pre>

means `//tree:ash` was built in a configuration with ID `9f87702`. For most
targets, this is an opaque hash of the build option values defining the
configuration.

To see the configuration's complete contents, run:

<pre>
$ bazel config 9f87702
</pre>

`9f87702` is a prefix of the complete ID. This is because complete IDs are
SHA-256 hashes, which are long and hard to follow. `cquery` understands any valid
prefix of a complete ID, similar to
[Git short hashes](https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection#_revision_selection){: .external}.
 To see complete IDs, run `$ bazel config`.

## Target pattern evaluation {:#target-pattern-evaluation}

`//foo` has a different meaning for `cquery` than for `query`. This is because
`cquery` evaluates _configured_ targets and the build graph may have multiple
configured versions of `//foo`.

For `cquery`, a target pattern in the query expression evaluates
to every configured target with a label that matches that pattern. Output is
deterministic, but `cquery` makes no ordering guarantee beyond the
[core query ordering contract](/query/language#graph-order).

This produces subtler results for query expressions than with `query`.
For example, the following can produce multiple results:

<pre>
# Analyzes //foo in the target configuration, but also analyzes
# //genrule_with_foo_as_tool which depends on an exec-configured
# //foo. So there are two configured target instances of //foo in
# the build graph.
$ bazel cquery //foo --universe_scope=//foo,//genrule_with_foo_as_tool
//foo (9f87702)
//foo (exec)
</pre>

If you want to precisely declare which instance to query over, use
the [`config`](#config) function.

See `query`'s [target pattern
documentation](/query/language#target-patterns) for more information on target patterns.

## Functions {:#functions}

Of the [set of functions](/query/language#functions "list of query functions")
supported by `query`, `cquery` supports all but
[`allrdeps`](/query/language#allrdeps),
[`buildfiles`](/query/language#buildfiles),
[`rbuildfiles`](/query/language#rbuildfiles),
[`siblings`](/query/language#siblings), [`tests`](/query/language#tests), and
[`visible`](/query/language#visible).

`cquery` also introduces the following new functions:

### config {:#config}

`expr ::= config(expr, word)`

The `config` operator attempts to find the configured target for
the label denoted by the first argument and configuration specified by the
second argument.

Valid values for the second argument are `null` or a
[custom configuration hash](#configurations). Hashes can be retrieved from `$
bazel config` or a previous `cquery`'s output.

Examples:

<pre>
$ bazel cquery "config(//bar, 3732cc8)" --universe_scope=//foo
</pre>

<pre>
$ bazel cquery "deps(//foo)"
//bar (exec)
//baz (exec)

$ bazel cquery "config(//baz, 3732cc8)"
</pre>

If not all results of the first argument can be found in the specified
configuration, only those that can be found are returned. If no results
can be found in the specified configuration, the query fails.

## Options {:#options}

### Build options {:#build-options}

`cquery` runs over a regular Bazel build and thus inherits the set of
[options](/reference/command-line-reference#build-options) available during a build.

###  Using cquery options {:#using-cquery-options}

#### `--universe_scope` (comma-separated list) {:#universe-scope}

Often, the dependencies of configured targets go through
[transitions](/extending/rules#configurations),
which causes their configuration to differ from their dependent. This flag
allows you to query a target as if it were built as a dependency or a transitive
dependency of another target. For example:

<pre>
# x/BUILD
genrule(
     name = "my_gen",
     srcs = ["x.in"],
     outs = ["x.cc"],
     cmd = "$(locations :tool) $&lt; >$@",
     tools = [":tool"],
)
cc_binary(
    name = "tool",
    srcs = ["tool.cpp"],
)
</pre>

Genrules configure their tools in the
[exec configuration](/extending/rules#configurations)
so the following queries would produce the following outputs:

<table class="table table-condensed table-bordered table-params">
  <thead>
    <tr>
      <th>Query</th>
      <th>Target Built</th>
      <th>Output</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>bazel cquery "//x:tool"</td>
      <td>//x:tool</td>
      <td>//x:tool(targetconfig)</td>
    </tr>
    <tr>
      <td>bazel cquery "//x:tool" --universe_scope="//x:my_gen"</td>
      <td>//x:my_gen</td>
      <td>//x:tool(execconfig)</td>
    </tr>
  </tbody>
</table>

If this flag is set, its contents are built. _If it's not set, all targets
mentioned in the query expression are built_ instead. The transitive closure of the
built targets are used as the universe of the query. Either way, the targets to
be built must be buildable at the top level (that is, compatible with top-level
options). `cquery` returns results in the transitive closure of these
top-level targets.

Even if it's possible to build all targets in a query expression at the top
level, it may be beneficial to not do so. For example, explicitly setting
`--universe_scope` could prevent building targets multiple times in
configurations you don't care about. It could also help specify which configuration version of a
target you're looking for (since it's not currently possible
to fully specify this any other way). You should set this flag
if your query expression is more complex than `deps(//foo)`.

#### `--implicit_deps` (boolean, default=True) {:#implicit-deps}

Setting this flag to false filters out all results that aren't explicitly set in
the BUILD file and instead set elsewhere by Bazel. This includes filtering resolved
toolchains.

#### `--tool_deps` (boolean, default=True) {:#tool-deps}

Setting this flag to false filters out all configured targets for which the
path from the queried target to them crosses a transition between the target
configuration and the
[non-target configurations](/extending/rules#configurations).
If the queried target is in the target configuration, setting `--notool_deps` will
only return targets that also are in the target configuration. If the queried
target is in a non-target configuration, setting `--notool_deps` will only return
targets also in non-target configurations. This setting generally does not affect filtering
of resolved toolchains.

#### `--include_aspects` (boolean, default=True) {:#include-aspects}

Include dependencies added by [aspects](/extending/aspects).

If this flag is disabled, `cquery somepath(X, Y)` and
`cquery deps(X) | grep 'Y'` omit Y if X only depends on it through an aspect.

## Output formats {:#output-formats}

By default, cquery outputs results in a dependency-ordered list of label and configuration pairs.
There are other options for exposing the results as well.

### Transitions {:#transitions}

<pre>
--transitions=lite
--transitions=full
</pre>

Configuration [transitions](/extending/rules#configurations)
are used to build targets underneath the top level targets in different
configurations than the top level targets.

For example, a target might impose a transition to the exec configuration on all
dependencies in its `tools` attribute. These are known as attribute
transitions. Rules can also impose transitions on their own configurations,
known as rule class transitions. This output format outputs information about
these transitions such as what type they are and the effect they have on build
options.

This output format is triggered by the `--transitions` flag which by default is
set to `NONE`. It can be set to `FULL` or `LITE` mode. `FULL` mode outputs
information about rule class transitions and attribute transitions including a
detailed diff of the options before and after the transition. `LITE` mode
outputs the same information without the options diff.

### Protocol message output {:#protocol-message-output}

<pre>
--output=proto
</pre>

This option causes the resulting targets to be printed in a binary protocol
buffer form. The definition of the protocol buffer can be found at
[src/main/protobuf/analysis_v2.proto](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/analysis_v2.proto){: .external}.

`CqueryResult` is the top level message containing the results of the cquery. It
has a list of `ConfiguredTarget` messages and a list of `Configuration`
messages. Each `ConfiguredTarget` has a `configuration_id` whose value is equal
to that of the `id` field from the corresponding `Configuration` message.

#### --[no]proto:include_configurations {:#proto-include-configurations}

By default, cquery results return configuration information as part of each
configured target. If you'd like to omit this information and get proto output
that is formatted exactly like query's proto output, set this flag to false.

See [query's proto output documentation](/query/language#output-formats)
for more proto output-related options.

Note: While selects are resolved both at the top level of returned
targets and within attributes, all possible inputs for selects are still
included as `rule_input` fields.

### Graph output {:#graph-output}

<pre>
--output=graph
</pre>

This option generates output as a Graphviz-compatible .dot file. See `query`'s
[graph output documentation](/query/language#display-result-graph) for details. `cquery`
also supports [`--graph:node_limit`](/query/language#graph-nodelimit) and
[`--graph:factored`](/query/language#graph-factored).

### Files output {:#files-output}

<pre>
--output=files
</pre>

This option prints a list of the output files produced by each target matched
by the query similar to the list printed at the end of a `bazel build`
invocation. The output contains only the files advertised in the requested
output groups as determined by the
[`--output_groups`](/reference/command-line-reference#flag--output_groups) flag.
It does include source files.

All paths emitted by this output format are relative to the
[execroot](https://bazel.build/remote/output-directories), which can be obtained
via `bazel info execution_root`. If the `bazel-out` convenience symlink exists,
paths to files in the main repository also resolve relative to the workspace
directory.

Note: The output of `bazel cquery --output=files //pkg:foo` contains the output
files of `//pkg:foo` in *all* configurations that occur in the build (also see
the [section on target pattern evaluation](#target-pattern-evaluation)). If that
is not desired, wrap you query in [`config(..., target)`](#config).

### Defining the output format using Starlark {:#output-format-definition}

<pre>
--output=starlark
</pre>

This output format calls a [Starlark](/rules/language)
function for each configured target in the query result, and prints the value
returned by the call. The `--starlark:file` flag specifies the location of a
Starlark file that defines a function named `format` with a single parameter,
`target`. This function is called for each [Target](/rules/lib/builtins/Target)
in the query result. Alternatively, for convenience, you may specify just the
body of a function declared as `def format(target): return expr` by using the
`--starlark:expr` flag.

#### 'cquery' Starlark dialect {:#cquery-starlark}

The cquery Starlark environment differs from a BUILD or .bzl file. It includes
all core Starlark
[built-in constants and functions](https://github.com/bazelbuild/starlark/blob/master/spec.md#built-in-constants-and-functions){: .external},
plus a few cquery-specific ones described below, but not (for example) `glob`,
`native`, or `rule`, and it does not support load statements.

##### build_options(target) {:#build-options}

`build_options(target)` returns a map whose keys are build option identifiers (see
[Configurations](/extending/config))
and whose values are their Starlark values. Build options whose values are not legal Starlark
values are omitted from this map.

If the target is an input file, `build_options(target)` returns None, as input file
targets have a null configuration.

##### providers(target) {:#providers}

`providers(target)` returns a map whose keys are names of
[providers](/extending/rules#providers)
(for example, `"DefaultInfo"`) and whose values are their Starlark values. Providers
whose values are not legal Starlark values are omitted from this map.

#### Examples {:#output-format-definition-examples}

Print a space-separated list of the base names of all files produced by `//foo`:

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="' '.join([f.basename for f in target.files.to_list()])"
</pre>

Print a space-separated list of the paths of all files produced by **rule** targets in
`//bar` and its subpackages:

<pre>
  bazel cquery 'kind(rule, //bar/...)' --output=starlark \
    --starlark:expr="' '.join([f.path for f in target.files.to_list()])"
</pre>

Print a list of the mnemonics of all actions registered by `//foo`.

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="[a.mnemonic for a in target.actions]"
</pre>

Print a list of compilation outputs registered by a `cc_library` `//baz`.

<pre>
  bazel cquery //baz --output=starlark \
    --starlark:expr="[f.path for f in target.output_groups.compilation_outputs.to_list()]"
</pre>

Print the value of the command line option `--javacopt` when building `//foo`.

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="build_options(target)['//command_line_option:javacopt']"
</pre>

Print the label of each target with exactly one output. This example uses
Starlark functions defined in a file.

<pre>
  $ cat example.cquery

  def has_one_output(target):
    return len(target.files.to_list()) == 1

  def format(target):
    if has_one_output(target):
      return target.label
    else:
      return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

Print the label of each target which is strictly Python 3. This example uses
Starlark functions defined in a file.

<pre>
  $ cat example.cquery

  def format(target):
    p = providers(target)
    py_info = p.get("PyInfo")
    if py_info and py_info.has_py3_only_sources:
      return target.label
    else:
      return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

Extract a value from a user defined Provider.

<pre>
  $ cat some_package/my_rule.bzl

  MyRuleInfo = provider(fields={"color": "the name of a color"})

  def _my_rule_impl(ctx):
      ...
      return [MyRuleInfo(color="red")]

  my_rule = rule(
      implementation = _my_rule_impl,
      attrs = {...},
  )

  $ cat example.cquery

  def format(target):
    p = providers(target)
    my_rule_info = p.get("//some_package:my_rule.bzl%MyRuleInfo'")
    if my_rule_info:
      return my_rule_info.color
    return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

## cquery vs. query {:#cquery-vs-query}

`cquery` and `query` complement each other and excel in
different niches. Consider the following to decide which is right for you:

*  `cquery` follows specific `select()` branches to
    model the exact graph you build. `query` doesn't know which
    branch the build chooses, so overapproximates by including all branches.
*   `cquery`'s precision requires building more of the graph than
    `query` does. Specifically, `cquery`
    evaluates _configured targets_ while `query` only
    evaluates _targets_. This takes more time and uses more memory.
*   `cquery`'s interpretation of
    the [query language](/query/language) introduces ambiguity
    that `query` avoids. For example,
    if `"//foo"` exists in two configurations, which one
    should `cquery "deps(//foo)"` use?
    The [`config`](#config) function can help with this.
*   As a newer tool, `cquery` lacks support for certain use
    cases. See [Known issues](#known-issues) for details.

## Known issues {:#known-issues}

**All targets that `cquery` "builds" must have the same configuration.**

Before evaluating queries, `cquery` triggers a build up to just
before the point where build actions would execute. The targets it
"builds" are by default selected from all labels that appear in the query
expression (this can be overridden
with [`--universe_scope`](#universe-scope)). These
must have the same configuration.

While these generally share the top-level "target" configuration,
rules can change their own configuration with
[incoming edge transitions](/extending/config#incoming-edge-transitions).
This is where `cquery` falls short.

Workaround: If possible, set `--universe_scope` to a stricter
scope. For example:

<pre>
# This command attempts to build the transitive closures of both //foo and
# //bar. //bar uses an incoming edge transition to change its --cpu flag.
$ bazel cquery 'somepath(//foo, //bar)'
ERROR: Error doing post analysis query: Top-level targets //foo and //bar
have different configurations (top-level targets with different
configurations is not supported)

# This command only builds the transitive closure of //foo, under which
# //bar should exist in the correct configuration.
$ bazel cquery 'somepath(//foo, //bar)' --universe_scope=//foo
</pre>

**No support for [`--output=xml`](/query/language#xml).**

**Non-deterministic output.**

`cquery` does not automatically wipe the build graph from
previous commands and is therefore prone to picking up results from past
queries. For example, `genrule` exerts an exec transition on
its `tools` attribute - that is, it configures its tools in the
[exec configuration](/extending/rules#configurations).

You can see the lingering effects of that transition below.

<pre>
$ cat > foo/BUILD &lt;&lt;&lt;EOF
genrule(
    name = "my_gen",
    srcs = ["x.in"],
    outs = ["x.cc"],
    cmd = "$(locations :tool) $&lt; >$@",
    tools = [":tool"],
)
cc_library(
    name = "tool",
)
EOF

    $ bazel cquery "//foo:tool"
tool(target_config)

    $ bazel cquery "deps(//foo:my_gen)"
my_gen (target_config)
tool (exec_config)
...

    $ bazel cquery "//foo:tool"
tool(exec_config)
</pre>

Workaround: change any startup option to force re-analysis of configured targets.
For example, add `--test_arg=<whatever>` to your build command.

## Troubleshooting {:#troubleshooting}

### Recursive target patterns (`/...`) {:#recursive-target-patterns}

If you encounter:

<pre>
$ bazel cquery --universe_scope=//foo:app "somepath(//foo:app, //foo/...)"
ERROR: Error doing post analysis query: Evaluation failed: Unable to load package '[foo]'
because package is not in scope. Check that all target patterns in query expression are within the
--universe_scope of this query.
</pre>

this incorrectly suggests package `//foo` isn't in scope even though
`--universe_scope=//foo:app` includes it. This is due to design limitations in
`cquery`. As a workaround, explicitly include `//foo/...` in the universe
scope:

<pre>
$ bazel cquery --universe_scope=//foo:app,//foo/... "somepath(//foo:app, //foo/...)"
</pre>

If that doesn't work (for example, because some target in `//foo/...` can't
build with the chosen build flags), manually unwrap the pattern into its
constituent packages with a pre-processing query:

<pre>
# Replace "//foo/..." with a subshell query call (not cquery!) outputting each package, piped into
# a sed call converting "&lt;pkg&gt;" to "//&lt;pkg&gt;:*", piped into a "+"-delimited line merge.
# Output looks like "//foo:*+//foo/bar:*+//foo/baz".
#
$  bazel cquery --universe_scope=//foo:app "somepath(//foo:app, $(bazel query //foo/...
--output=package | sed -e 's/^/\/\//' -e 's/$/:*/' | paste -sd "+" -))"
</pre>


Project: /_project.yaml
Book: /_book.yaml

# Query quickstart

{% include "_buttons.html" %}

This tutorial covers how to work with Bazel to trace dependencies in your code using a premade Bazel project.

For language and `--output` flag details, see the [Bazel query reference](/query/language) and [Bazel cquery reference](/query/cquery) manuals. Get help in your IDE by typing `bazel help query` or `bazel help cquery` on the command line.

## Objective

This guide runs you through a set of basic queries you can use to learn more about your project's file dependencies. It is intended for new Bazel developers with a basic knowledge of how Bazel and `BUILD` files work.


## Prerequisites

Start by installing [Bazel](https://bazel.build/install), if you haven’t already. This tutorial uses Git for source control, so for best results, install [Git](https://github.com/git-guides/install-git) as well.

To visualize dependency graphs, the tool called Graphviz is used, which you can [download](https://graphviz.org/download/) in order to follow along.

### Get the sample project

Next, retrieve the sample app from [Bazel's Examples repository](https://github.com/bazelbuild/examples) by running the following in your command-line tool of choice:

```posix-terminal
git clone https://github.com/bazelbuild/examples.git
```

The sample project for this tutorial is in the `examples/query-quickstart` directory.

## Getting started

### What are Bazel queries?

Queries help you to learn about a Bazel codebase by analyzing the relationships between `BUILD` files and examining the resulting output for useful information. This guide previews some basic query functions, but for more options see the [query guide](https://bazel.build/query/guide). Queries help you learn about dependencies in large scale projects without manually navigating through `BUILD` files.

To run a query, open your command line terminal and enter:

```posix-terminal
bazel query 'query_function'
```

### Scenario

Imagine a scenario that delves into the relationship between Cafe Bazel and its respective chef. This Cafe exclusively sells pizza and mac & cheese. Take a look below at how the project is structured:

```
bazelqueryguide
├── BUILD
├── src
│   └── main
│       └── java
│           └── com
│               └── example
│                   ├── customers
│                   │   ├── Jenny.java
│                   │   ├── Amir.java
│                   │   └── BUILD
│                   ├── dishes
│                   │   ├── Pizza.java
│                   │   ├── MacAndCheese.java
│                   │   └── BUILD
│                   ├── ingredients
│                   │   ├── Cheese.java
│                   │   ├── Tomatoes.java
│                   │   ├── Dough.java
│                   │   ├── Macaroni.java
│                   │   └── BUILD
│                   ├── restaurant
│                   │   ├── Cafe.java
│                   │   ├── Chef.java
│                   │   └── BUILD
│                   ├── reviews
│                   │   ├── Review.java
│                   │   └── BUILD
│                   └── Runner.java
└── MODULE.bazel
```

Throughout this tutorial, unless directed otherwise, try not to look in the `BUILD` files to find the information you need and instead solely use the query function.

A project consists of different packages that make up a Cafe. They are separated into: `restaurant`, `ingredients`, `dishes`, `customers`, and `reviews`. Rules within these packages define different components of the Cafe with various tags and dependencies.

### Running a build

This project contains a main method inside of `Runner.java` that you can execute
to print out a menu of the Cafe. Build the project using Bazel with the command
`bazel build` and use `:` to signal that the target is named `runner`. See
[target names](https://bazel.build/concepts/labels#target-names) to learn how to
reference targets.

To build this project, paste this command into a terminal:

```posix-terminal
bazel build :runner
```

Your output should look something like this if the build is successful.

```bash
INFO: Analyzed target //:runner (49 packages loaded, 784 targets configured).
INFO: Found 1 target...
Target //:runner up-to-date:
  bazel-bin/runner.jar
  bazel-bin/runner
INFO: Elapsed time: 16.593s, Critical Path: 4.32s
INFO: 23 processes: 4 internal, 10 darwin-sandbox, 9 worker.
INFO: Build completed successfully, 23 total actions
```

After it has built successfully, run the application by pasting this command:

```posix-terminal
bazel-bin/runner
```

```bash
--------------------- MENU -------------------------

Pizza - Cheesy Delicious Goodness
Macaroni & Cheese - Kid-approved Dinner

----------------------------------------------------
```
This leaves you with a list of the menu items given along with a short description.

## Exploring targets

The project lists ingredients and dishes in their own packages. To use a query to view the rules of a package, run the command <code>bazel query <em>package</em>/…</code>

In this case, you can use this to look through the ingredients and dishes that this Cafe has by running:

```posix-terminal
bazel query //src/main/java/com/example/dishes/...
```

```posix-terminal
bazel query //src/main/java/com/example/ingredients/...
```

If you query for the targets of the ingredients package, the output should look like:

```bash
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/ingredients:dough
//src/main/java/com/example/ingredients:macaroni
//src/main/java/com/example/ingredients:tomato
```

## Finding dependencies

What targets does your runner rely on to run?

Say you want to dive deeper into the structure of your project without prodding into the filesystem (which may be untenable for large projects). What rules does Cafe Bazel use?

If, like in this example, the target for your runner is `runner`, discover the underlying dependencies of the target by running the command:

```posix-terminal
bazel query --noimplicit_deps "deps(target)"
```

```posix-terminal
bazel query --noimplicit_deps "deps(:runner)"
```

```bash
//:runner
//:src/main/java/com/example/Runner.java
//src/main/java/com/example/dishes:MacAndCheese.java
//src/main/java/com/example/dishes:Pizza.java
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:Cheese.java
//src/main/java/com/example/ingredients:Dough.java
//src/main/java/com/example/ingredients:Macaroni.java
//src/main/java/com/example/ingredients:Tomato.java
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/ingredients:dough
//src/main/java/com/example/ingredients:macaroni
//src/main/java/com/example/ingredients:tomato
//src/main/java/com/example/restaurant:Cafe.java
//src/main/java/com/example/restaurant:Chef.java
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```
Note: Adding the flag `--noimplicit_deps` removes configurations and potential toolchains to simplify the list. When you omit this flag, Bazel returns implicit dependencies not specified in the `BUILD` file and clutters the output.

In most cases, use the query function `deps()` to see individual output dependencies of a specific target.

## Visualizing the dependency graph (optional)

Note: This section uses Graphviz, so make sure to [download Graphviz](https://graphviz.org/download/) to follow along.

The section describes how you can visualize the dependency paths for a specific query. [Graphviz](https://graphviz.org/) helps to see the path as a directed acyclic graph image as opposed to a flattened list. You can alter the display of the Bazel query graph by using various `--output` command line options. See [Output Formats](https://bazel.build/query/language#output-formats) for options.

Start by running your desired query and add the flag `--noimplicit_deps` to remove excessive tool dependencies. Then, follow the query with the output flag and store the graph into a file called `graph.in` to create a text representation of the graph.

To search for all dependencies of the target `:runner` and format the output as a graph:

```posix-terminal
bazel query --noimplicit_deps 'deps(:runner)' --output graph > graph.in
```
This creates a file called `graph.in`, which is a text representation of the build graph. Graphviz uses <code>[dot](https://graphviz.org/docs/layouts/dot/) </code>– a tool that processes text into a visualization —  to create a png:

```posix-terminal
dot -Tpng < graph.in > graph.png
```
If you open up `graph.png`, you should see something like this. The graph below has been simplified to make the essential path details clearer in this guide.

![Diagram showing a relationship from cafe to chef to the dishes: pizza and mac and cheese which diverges into the separate ingredients: cheese, tomatoes, dough, and macaroni.](images/query_graph1.png "Dependency graph")

This helps when you want to see the outputs of the different query functions throughout this guide.

## Finding reverse dependencies

If instead you have a target you’d like to analyze what other targets use it, you can use a query to examine what targets depend on a certain rule. This is called a “reverse dependency”. Using `rdeps()` can be useful when editing a file in a codebase that you’re unfamiliar with, and can save you from unknowingly breaking other files which depended on it.

For instance, you want to make some edits to the ingredient `cheese`. To avoid causing an issue for Cafe Bazel, you need to check what dishes rely on `cheese`.

Caution: Since `ingredients` is its own package, you must use a different naming convention for the target `cheese` in the form of `//package:target`. Read more about referencing targets, or [Labels](https://bazel.build/concepts/labels).

To see what targets depend on a particular target/package, you can use `rdeps(universe_scope, target)`. The `rdeps()` query function takes in at least two arguments: a `universe_scope` — the relevant directory — and a `target`. Bazel searches for the target’s reverse dependencies within the `universe_scope` provided. The `rdeps()` operator accepts an optional third argument: an integer literal specifying the upper bound on the depth of the search.

Tip: To search within the whole scope of the project, set the `universe_scope` to `//...`

To look for reverse dependencies of the target `cheese` within the scope of the entire project ‘//…’ run the command:

```posix-terminal
bazel query "rdeps(universe_scope, target)"
```
```
ex) bazel query "rdeps(//... , //src/main/java/com/example/ingredients:cheese)"
```
```bash
//:runner
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```
The query return shows that cheese is relied on by both pizza and macAndCheese. What a surprise!

## Finding targets based on tags

Two customers walk into Bazel Cafe: Amir and Jenny. There is nothing known about them except for their names. Luckily, they have their orders tagged in the 'customers' `BUILD` file. How can you access this tag?

Developers can tag Bazel targets with different identifiers, often for testing purposes. For instance, tags on tests can annotate a test's role in your debug and release process, especially for C++ and Python tests, which lack any runtime annotation ability. Using tags and size elements gives flexibility in assembling suites of tests based around a codebase’s check-in policy.

In this example, the tags are either one of `pizza` or `macAndCheese` to represent the menu items. This command queries for targets that have tags matching your identifier within a certain package.

```
bazel query 'attr(tags, "pizza", //src/main/java/com/example/customers/...)'
```
This query returns all of the targets in the 'customers' package that have a tag of "pizza".

### Test yourself

Use this query to learn what Jenny wants to order.

<div>
  <devsite-expandable>
  <h4 class="showalways">Answer</h4>
  <p>Mac and Cheese</p>
  </devsite-expandable>
</div>


## Adding a new dependency

Cafe Bazel has expanded its menu — customers can now order a Smoothie! This specific smoothie consists of the ingredients `Strawberry` and `Banana`.

First, add the ingredients that the smoothie depends on: `Strawberry.java` and `Banana.java`. Add the empty Java classes.

**`src/main/java/com/example/ingredients/Strawberry.java`**

```java
package com.example.ingredients;

public class Strawberry {

}
```

**`src/main/java/com/example/ingredients/Banana.java`**

```java
package com.example.ingredients;

public class Banana {

}
```

Next, add `Smoothie.java` to the appropriate directory: `dishes`.

**`src/main/java/com/example/dishes/Smoothie.java`**

```java
package com.example.dishes;

public class Smoothie {
    public static final String DISH_NAME = "Smoothie";
    public static final String DESCRIPTION = "Yummy and Refreshing";
}
```


Lastly, add these files as rules in the appropriate `BUILD` files. Create a new java library for each new ingredient, including its name, public visibility, and its newly created 'src' file. You should wind up with this updated `BUILD` file:

**`src/main/java/com/example/ingredients/BUILD`**

```
java_library(
    name = "cheese",
    visibility = ["//visibility:public"],
    srcs = ["Cheese.java"],
)

java_library(
    name = "dough",
    visibility = ["//visibility:public"],
    srcs = ["Dough.java"],
)

java_library(
    name = "macaroni",
    visibility = ["//visibility:public"],
    srcs = ["Macaroni.java"],
)

java_library(
    name = "tomato",
    visibility = ["//visibility:public"],
    srcs = ["Tomato.java"],
)

java_library(
    name = "strawberry",
    visibility = ["//visibility:public"],
    srcs = ["Strawberry.java"],
)

java_library(
    name = "banana",
    visibility = ["//visibility:public"],
    srcs = ["Banana.java"],
)
```

In the `BUILD` file for dishes, you want to add a new rule for `Smoothie`. Doing so includes the Java file created for `Smoothie` as a 'src' file, and the new rules you made for each ingredient of the smoothie.

**`src/main/java/com/example/dishes/BUILD`**

```
java_library(
    name = "macAndCheese",
    visibility = ["//visibility:public"],
    srcs = ["MacAndCheese.java"],
    deps = [
        "//src/main/java/com/example/ingredients:cheese",
        "//src/main/java/com/example/ingredients:macaroni",
    ],
)

java_library(
    name = "pizza",
    visibility = ["//visibility:public"],
    srcs = ["Pizza.java"],
    deps = [
        "//src/main/java/com/example/ingredients:cheese",
        "//src/main/java/com/example/ingredients:dough",
        "//src/main/java/com/example/ingredients:tomato",
    ],
)

java_library(
    name = "smoothie",
    visibility = ["//visibility:public"],
    srcs = ["Smoothie.java"],
    deps = [
        "//src/main/java/com/example/ingredients:strawberry",
        "//src/main/java/com/example/ingredients:banana",
    ],
)
```

Lastly, you want to include the smoothie as a dependency in the Chef’s `BUILD` file.

**`src/main/java/com/example/restaurant/BUILD`**

```
java\_library(
    name = "chef",
    visibility = ["//visibility:public"],
    srcs = [
        "Chef.java",
    ],

    deps = [
        "//src/main/java/com/example/dishes:macAndCheese",
        "//src/main/java/com/example/dishes:pizza",
        "//src/main/java/com/example/dishes:smoothie",
    ],
)

java\_library(
    name = "cafe",
    visibility = ["//visibility:public"],
    srcs = [
        "Cafe.java",
    ],
    deps = [
        ":chef",
    ],
)
```

Build `cafe` again to confirm that there are no errors. If it builds successfully, congratulations! You’ve added a new dependency for the 'Cafe'. If not, look out for spelling mistakes and package naming. For more information about writing `BUILD` files see [BUILD Style Guide](https://bazel.build/build/style-guide).

Now, visualize the new dependency graph with the addition of the `Smoothie` to compare with the previous one. For clarity, name the graph input as `graph2.in` and `graph2.png`.


```posix-terminal
bazel query --noimplicit_deps 'deps(:runner)' --output graph > graph2.in
```

```posix-terminal
dot -Tpng < graph2.in > graph2.png
```

[![The same graph as the first one except now there is a spoke stemming from the chef target with smoothie which leads to banana and strawberry](images/query_graph2.png "Updated dependency graph")](images/query_graph2.png)

Looking at `graph2.png`, you can see that `Smoothie` has no shared dependencies with other dishes but is just another target that the `Chef` relies on.

## somepath() and allpaths()

What if you want to query why one package depends on another package? Displaying a dependency path between the two provides the answer.

Two functions can help you find dependency paths: `somepath()` and `allpaths()`. Given a starting target S and an end point E, find a path between S and E by using `somepath(S,E)`.

Explore the differences between these two functions by looking at the relationships between the 'Chef' and 'Cheese' targets. There are different possible paths to get from one target to the other:

*   Chef → MacAndCheese → Cheese
*   Chef → Pizza → Cheese

`somepath()` gives you a single path out of the two options, whereas 'allpaths()' outputs every possible path.

Using Cafe Bazel as an example, run the following:

```posix-terminal
bazel query "somepath(//src/main/java/com/example/restaurant/..., //src/main/java/com/example/ingredients:cheese)"
```

```bash
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/ingredients:cheese
```

The output follows the first path of Cafe → Chef → MacAndCheese → Cheese. If instead you use `allpaths()`, you get:

```posix-terminal
bazel query "allpaths(//src/main/java/com/example/restaurant/..., //src/main/java/com/example/ingredients:cheese)"
```

```bash
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```

![Output path of cafe to chef to pizza,mac and cheese to cheese](images/query_graph3.png "Output path for dependency")

The output of `allpaths()` is a little harder to read as it is a flattened list of the dependencies. Visualizing this graph using Graphviz makes the relationship clearer to understand.

## Test yourself

One of Cafe Bazel’s customers gave the restaurant's first review! Unfortunately, the review is missing some details such as the identity of the reviewer and what dish it’s referencing. Luckily, you can access this information with Bazel. The `reviews` package contains a program that prints a review from a mystery customer. Build and run it with:

```posix-terminal
bazel build //src/main/java/com/example/reviews:review
```

```posix-terminal
bazel-bin/src/main/java/com/example/reviews/review
```

Going off Bazel queries only, try to find out who wrote the review, and what dish they were describing.

<div>
  <devsite-expandable>
  <h4 class="showalways">Hint</h4>
  <p>Check the tags and dependencies for useful information.</p>
  </devsite-expandable>
</div>

<div>
  <devsite-expandable>
  <h4 class="showalways">Answer</h4>
  <p>This review was describing the Pizza and Amir was the reviewer. If you look at what dependencies that this rule had using
  <code>bazel query --noimplicit\_deps 'deps(//src/main/java/com/example/reviews:review)'</code>
  The result of this command reveals that Amir is the reviewer!
  Next, since you know the reviewer is Amir, you can use the query function to seek which tag Amir has in the `BUILD` file to see what dish is there.
  The command <code>bazel query 'attr(tags, "pizza", //src/main/java/com/example/customers/...)'</code> output that Amir is the only customer that ordered a pizza and is the reviewer which gives us the answer.
  </p>
  </devsite-expandable>
</div>

## Wrapping up

Congratulations! You have now run several basic queries, which you can try out on own projects. To learn more about the query language syntax, refer to the [Query reference page](https://bazel.build/query/language). Want more advanced queries? The [Query guide](https://bazel.build/query/guide) showcases an in-depth list of more use cases than are covered in this guide.


Project: /_project.yaml
Book: /_book.yaml

# Action Graph Query (aquery)

{% include "_buttons.html" %}

The `aquery` command allows you to query for actions in your build graph.
It operates on the post-analysis Configured Target Graph and exposes
information about **Actions, Artifacts and their relationships.**

`aquery` is useful when you are interested in the properties of the Actions/Artifacts
generated from the Configured Target Graph. For example, the actual commands run
and their inputs/outputs/mnemonics.

The tool accepts several command-line [options](#command-options).
Notably, the aquery command runs on top of a regular Bazel build and inherits
the set of options available during a build.

It supports the same set of functions that is also available to traditional
`query` but `siblings`, `buildfiles` and
`tests`.

An example `aquery` output (without specific details):

<pre>
$ bazel aquery 'deps(//some:label)'
action 'Writing file some_file_name'
  Mnemonic: ...
  Target: ...
  Configuration: ...
  ActionKey: ...
  Inputs: [...]
  Outputs: [...]
</pre>

## Basic syntax {:#basic-syntax}

A simple example of the syntax for `aquery` is as follows:

`bazel aquery "aquery_function(function(//target))"`

The query expression (in quotes) consists of the following:

*   `aquery_function(...)`: functions specific to `aquery`.
    More details [below](#using-aquery-functions).
*   `function(...)`: the standard [functions](/query/language#functions)
    as traditional `query`.
*   `//target` is the label to the interested target.

<pre>
# aquery examples:
# Get the action graph generated while building //src/target_a
$ bazel aquery '//src/target_a'

# Get the action graph generated while building all dependencies of //src/target_a
$ bazel aquery 'deps(//src/target_a)'

# Get the action graph generated while building all dependencies of //src/target_a
# whose inputs filenames match the regex ".*cpp".
$ bazel aquery 'inputs(".*cpp", deps(//src/target_a))'
</pre>

## Using aquery functions {:#using-aquery-functions}

There are three `aquery` functions:

*   `inputs`: filter actions by inputs.
*   `outputs`: filter actions by outputs
*   `mnemonic`: filter actions by mnemonic

`expr ::= inputs(word, expr)`

  The `inputs` operator returns the actions generated from building `expr`,
  whose input filenames match the regex provided by `word`.

`$ bazel aquery 'inputs(".*cpp", deps(//src/target_a))'`

`outputs` and `mnemonic` functions share a similar syntax.

You can also combine functions to achieve the AND operation. For example:

<pre>
  $ bazel aquery 'mnemonic("Cpp.*", (inputs(".*cpp", inputs("foo.*", //src/target_a))))'
</pre>

  The above command would find all actions involved in building `//src/target_a`,
  whose mnemonics match `"Cpp.*"` and inputs match the patterns
  `".*cpp"` and `"foo.*"`.

Important: aquery functions can't be nested inside non-aquery functions.
Conceptually, this makes sense since the output of aquery functions is Actions,
not Configured Targets.

An example of the syntax error produced:

<pre>
        $ bazel aquery 'deps(inputs(".*cpp", //src/target_a))'
        ERROR: aquery filter functions (inputs, outputs, mnemonic) produce actions,
        and therefore can't be the input of other function types: deps
        deps(inputs(".*cpp", //src/target_a))
</pre>

## Options {:#options}

### Build options {:#build-options}

`aquery` runs on top of a regular Bazel build and thus inherits the set of
[options](/reference/command-line-reference#build-options)
available during a build.

### Aquery options {:#aquery-options}

#### `--output=(text|summary|commands|proto|jsonproto|textproto), default=text` {:#output}

The default output format (`text`) is human-readable,
use `proto`, `textproto`, or `jsonproto` for machine-readable format.
The proto message is `analysis.ActionGraphContainer`.

The `commands` output format prints a list of build commands with
one command per line.

In general, do not depend on the order of output. For more information,
see the [core query ordering contract](/query/language#graph-order).

#### `--include_commandline, default=true` {:#include-commandline}

Includes the content of the action command lines in the output (potentially large).

#### `--include_artifacts, default=true` {:#include-artifacts}

Includes names of the action inputs and outputs in the output (potentially large).

#### `--include_aspects, default=true` {:#include-aspects}

Whether to include Aspect-generated actions in the output.

#### `--include_param_files, default=false` {:#include-param-files}

Include the content of the param files used in the command (potentially large).

Warning: Enabling this flag will automatically enable the `--include_commandline` flag.

#### `--include_file_write_contents, default=false` {:#include-file-write-contents}

Include file contents for the `actions.write()` action and the contents of the
manifest file for the `SourceSymlinkManifest` action The file contents is
returned in the `file_contents` field with `--output=`xxx`proto`.
With `--output=text`, the output has
```
FileWriteContents: [<base64-encoded file contents>]
```
line

#### `--skyframe_state, default=false` {:#skyframe-state}

Without performing extra analysis, dump the Action Graph from Skyframe.

Note: Specifying a target with `--skyframe_state` is currently not supported.
This flag is only available with `--output=proto` or `--output=textproto`.

## Other tools and features {:#other-tools-features}

### Querying against the state of Skyframe {:#querying-against-skyframe}

[Skyframe](/reference/skyframe) is the evaluation and
incrementality model of Bazel. On each instance of Bazel server, Skyframe stores the dependency graph
constructed from the previous runs of the [Analysis phase](/run/build#analysis).

In some cases, it is useful to query the Action Graph on Skyframe.
An example use case would be:

1.  Run `bazel build //target_a`
2.  Run `bazel build //target_b`
3.  File `foo.out` was generated.

_As a Bazel user, I want to determine if `foo.out` was generated from building
`//target_a` or `//target_b`_.

One could run `bazel aquery 'outputs("foo.out", //target_a)'` and
`bazel aquery 'outputs("foo.out", //target_b)'` to figure out the action responsible
for creating `foo.out`, and in turn the target. However, the number of different
targets previously built can be larger than 2, which makes running multiple `aquery`
commands a hassle.

As an alternative, the `--skyframe_state` flag can be used:

<pre>
  # List all actions on Skyframe's action graph
  $ bazel aquery --output=proto --skyframe_state

  # or

  # List all actions on Skyframe's action graph, whose output matches "foo.out"
  $ bazel aquery --output=proto --skyframe_state 'outputs("foo.out")'
</pre>

With `--skyframe_state` mode, `aquery` takes the content of the Action Graph
that Skyframe keeps on the instance of Bazel, (optionally) performs filtering on it and
outputs the content, without re-running the analysis phase.

#### Special considerations {:#special-considerations}

##### Output format {:#output-format}

`--skyframe_state` is currently only available for `--output=proto`
and `--output=textproto`

##### Non-inclusion of target labels in the query expression {:#target-labels-non-inclusion}

Currently, `--skyframe_state` queries the whole action graph that exists on Skyframe,
regardless of the targets. Having the target label specified in the query together with
`--skyframe_state` is considered a syntax error:

<pre>
  # WRONG: Target Included
  $ bazel aquery --output=proto --skyframe_state **//target_a**
  ERROR: Error while parsing '//target_a)': Specifying build target(s) [//target_a] with --skyframe_state is currently not supported.

  # WRONG: Target Included
  $ bazel aquery --output=proto --skyframe_state 'inputs(".*.java", **//target_a**)'
  ERROR: Error while parsing '//target_a)': Specifying build target(s) [//target_a] with --skyframe_state is currently not supported.

  # CORRECT: Without Target
  $ bazel aquery --output=proto --skyframe_state
  $ bazel aquery --output=proto --skyframe_state 'inputs(".*.java")'
</pre>

### Comparing aquery outputs {:#comparing-aquery-outputs}

You can compare the outputs of two different aquery invocations using the `aquery_differ` tool.
For instance: when you make some changes to your rule definition and want to verify that the
command lines being run did not change. `aquery_differ` is the tool for that.

The tool is available in the [bazelbuild/bazel](https://github.com/bazelbuild/bazel/tree/master/tools/aquery_differ){: .external} repository.
To use it, clone the repository to your local machine. An example usage:

<pre>
  $ bazel run //tools/aquery_differ -- \
  --before=/path/to/before.proto \
  --after=/path/to/after.proto \
  --input_type=proto \
  --attrs=cmdline \
  --attrs=inputs
</pre>

The above command returns the difference between the `before` and `after` aquery outputs:
which actions were present in one but not the other, which actions have different
command line/inputs in each aquery output, ...). The result of running the above command would be:

<pre>
  Aquery output 'after' change contains an action that generates the following outputs that aquery output 'before' change doesn't:
  ...
  /list of output files/
  ...

  [cmdline]
  Difference in the action that generates the following output(s):
    /path/to/abc.out
  --- /path/to/before.proto
  +++ /path/to/after.proto
  @@ -1,3 +1,3 @@
    ...
    /cmdline diff, in unified diff format/
    ...
</pre>

#### Command options {:#command-options}

`--before, --after`: The aquery output files to be compared

`--input_type=(proto|text_proto), default=proto`: the format of the input
files. Support is provided for `proto` and `textproto` aquery output.

`--attrs=(cmdline|inputs), default=cmdline`: the attributes of actions
to be compared.

### Aspect-on-aspect {:#aspect-on-aspect}

It is possible for [Aspects](/extending/aspects)
to be applied on top of each other. The aquery output of the action generated by
these Aspects would then include the _Aspect path_, which is the sequence of
Aspects applied to the target which generated the action.

An example of Aspect-on-Aspect:

<pre>
  t0
  ^
  | <- a1
  t1
  ^
  | <- a2
  t2
</pre>

Let t<sub>i</sub> be a target of rule r<sub>i</sub>, which applies an Aspect a<sub>i</sub>
to its dependencies.

Assume that a2 generates an action X when applied to target t0. The text output of
`bazel aquery --include_aspects 'deps(//t2)'` for action X would be:

<pre>
  action ...
  Mnemonic: ...
  Target: //my_pkg:t0
  Configuration: ...
  AspectDescriptors: [//my_pkg:rule.bzl%**a2**(foo=...)
    -> //my_pkg:rule.bzl%**a1**(bar=...)]
  ...
</pre>

This means that action `X` was generated by Aspect `a2` applied onto
`a1(t0)`, where `a1(t0)` is the result of Aspect `a1` applied
onto target `t0`.

Each `AspectDescriptor` has the following format:

<pre>
  AspectClass([param=value,...])
</pre>

`AspectClass` could be the name of the Aspect class (for native Aspects) or
`bzl_file%aspect_name` (for Starlark Aspects). `AspectDescriptor` are
sorted in topological order of the
[dependency graph](/extending/aspects#aspect_basics).

### Linking with the JSON profile {:#linking-with-json-profile}

While aquery provides information about the actions being run in a build (why they're being run,
their inputs/outputs), the [JSON profile](/rules/performance#performance-profiling)
tells us the timing and duration of their execution.
It is possible to combine these 2 sets of information via a common denominator: an action's primary output.

To include actions' outputs in the JSON profile, generate the profile with
`--experimental_include_primary_output --noslim_profile`.
Slim profiles are incompatible with the inclusion of primary outputs. An action's primary output
is included by default by aquery.

We don't currently provide a canonical tool to combine these 2 data sources, but you should be
able to build your own script with the above information.

## Known issues {:#known-issues}

### Handling shared actions {:#handling-shared-actions}

Sometimes actions are
[shared](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/Actions.java;l=59;drc=146d51aa1ec9dcb721a7483479ef0b1ac21d39f1){: .external}
between configured targets.

In the execution phase, those shared actions are
[simply considered as one](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/Actions.java;l=241;drc=003b8734036a07b496012730964ac220f486b61f){: .external} and only executed once.
However, aquery operates on the pre-execution, post-analysis action graph, and hence treats these
like separate actions whose output Artifacts have the exact same `execPath`. As a result,
equivalent Artifacts appear duplicated.

The list of aquery issues/planned features can be found on
[GitHub](https://github.com/bazelbuild/bazel/labels/team-Performance){: .external}.

## FAQs {:#faqs}

### The ActionKey remains the same even though the content of an input file changed. {:#actionkey-same}

In the context of aquery, the `ActionKey` refers to the `String` gotten from
[ActionAnalysisMetadata#getKey](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/ActionAnalysisMetadata.java;l=89;drc=8b856f5484f0117b2aebc302f849c2a15f273310){: .external}:

<pre>
  Returns a string encoding all of the significant behaviour of this Action that might affect the
  output. The general contract of `getKey` is this: if the work to be performed by the
  execution of this action changes, the key must change.

  ...

  Examples of changes that should affect the key are:

  - Changes to the BUILD file that materially affect the rule which gave rise to this Action.
  - Changes to the command-line options, environment, or other global configuration resources
      which affect the behaviour of this kind of Action (other than changes to the names of the
      input/output files, which are handled externally).
  - An upgrade to the build tools which changes the program logic of this kind of Action
      (typically this is achieved by incorporating a UUID into the key, which is changed each
      time the program logic of this action changes).
  Note the following exception: for actions that discover inputs, the key must change if any
  input names change or else action validation may falsely validate.
</pre>

This excludes the changes to the content of the input files, and is not to be confused with
[RemoteCacheClient#ActionKey](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/remote/common/RemoteCacheClient.java;l=38;drc=21577f202eb90ce94a337ebd2ede824d609537b6){: .external}.

## Updates {:#updates}

For any issues/feature requests, please file an issue [here](https://github.com/bazelbuild/bazel/issues/new).


Project: /_project.yaml
Book: /_book.yaml

# Query guide

{% include "_buttons.html" %}

This page covers how to get started using Bazel's query language to trace
dependencies in your code.

For a language details and `--output` flag details, please see the
reference manuals, [Bazel query reference](/query/language)
and [Bazel cquery reference](/query/cquery). You can get help by
typing `bazel help query` or `bazel help cquery` on the
command line.

To execute a query while ignoring errors such as missing targets, use the
`--keep_going` flag.

## Finding the dependencies of a rule {:#finding-rule-dependencies}

To see the dependencies of `//foo`, use the
`deps` function in bazel query:

<pre>
$ bazel query "deps(//foo)"
//foo:foo
//foo:foo-dep
...
</pre>

This is the set of all targets required to build `//foo`.

## Tracing the dependency chain between two packages {:#tracing-dependency-chain}

The library `//third_party/zlib:zlibonly` isn't in the BUILD file for
`//foo`, but it is an indirect dependency. How can
we trace this dependency path?  There are two useful functions here:
`allpaths` and `somepath`. You may also want to exclude
tooling dependencies with `--notool_deps` if you care only about
what is included in the artifact you built, and not every possible job.

To visualize the graph of all dependencies, pipe the bazel query output through
  the `dot` command-line tool:

<pre>
$ bazel query "allpaths(//foo, third_party/...)" --notool_deps --output graph | dot -Tsvg > /tmp/deps.svg
</pre>

Note: `dot` supports other image formats, just replace `svg` with the
format identifier, for example, `png`.

When a dependency graph is big and complicated, it can be helpful start with a single path:

<pre>
$ bazel query "somepath(//foo:foo, third_party/zlib:zlibonly)"
//foo:foo
//translations/tools:translator
//translations/base:base
//third_party/py/MySQL:MySQL
//third_party/py/MySQL:_MySQL.so
//third_party/mysql:mysql
//third_party/zlib:zlibonly
</pre>

If you do not specify `--output graph` with `allpaths`,
you will get a flattened list of the dependency graph.

<pre>
$ bazel query "allpaths(//foo, third_party/...)"
  ...many errors detected in BUILD files...
//foo:foo
//translations/tools:translator
//translations/tools:aggregator
//translations/base:base
//tools/pkg:pex
//tools/pkg:pex_phase_one
//tools/pkg:pex_lib
//third_party/python:python_lib
//translations/tools:messages
//third_party/py/xml:xml
//third_party/py/xml:utils/boolean.so
//third_party/py/xml:parsers/sgmlop.so
//third_party/py/xml:parsers/pyexpat.so
//third_party/py/MySQL:MySQL
//third_party/py/MySQL:_MySQL.so
//third_party/mysql:mysql
//third_party/openssl:openssl
//third_party/zlib:zlibonly
//third_party/zlib:zlibonly_v1_2_3
//third_party/python:headers
//third_party/openssl:crypto
</pre>

### Aside: implicit dependencies {:#implicit-dependencies}

The BUILD file for `//foo` never references
`//translations/tools:aggregator`. So, where's the direct dependency?

Certain rules include implicit dependencies on additional libraries or tools.
For example, to build a `genproto` rule, you need first to build the Protocol
Compiler, so every `genproto` rule carries an implicit dependency on the
protocol compiler. These dependencies are not mentioned in the build file,
but added in by the build tool. The full set of implicit dependencies is
  currently undocumented. Using `--noimplicit_deps` allows you to filter out
  these deps from your query results. For cquery, this will include resolved toolchains.

## Reverse dependencies {:#reverse-dependencies}

You might want to know the set of targets that depends on some target. For instance,
if you're going to change some code, you might want to know what other code
you're about to break. You can use `rdeps(u, x)` to find the reverse
dependencies of the targets in `x` within the transitive closure of `u`.

Bazel's [Sky Query](/query/language#sky-query)
supports the `allrdeps` function which allows you to query reverse dependencies
in a universe you specify.

## Miscellaneous uses {:#miscellaneous-uses}

You can use `bazel query` to analyze many dependency relationships.

### What exists ... {:#what-exists}

#### What packages exist beneath `foo`? {:#what-exists-beneath-foo}

<pre>bazel query 'foo/...' --output package</pre>

#### What rules are defined in the `foo` package? {:#rules-defined-in-foo}

<pre>bazel query 'kind(rule, foo:*)' --output label_kind</pre>

#### What files are generated by rules in the `foo` package? {:#files-generated-by-rules}

<pre>bazel query 'kind("generated file", //foo:*)'</pre>

#### What targets are generated by starlark macro `foo`? {:#targets-generated-by-foo}

<pre>bazel query 'attr(generator_function, foo, //path/to/search/...)'</pre>

#### What's the set of BUILD files needed to build `//foo`? {:#build-files-required}

<pre>bazel query 'buildfiles(deps(//foo))' | cut -f1 -d:</pre>

#### What are the individual tests that a `test_suite` expands to? {:#individual-tests-in-testsuite}

<pre>bazel query 'tests(//foo:smoke_tests)'</pre>

#### Which of those are C++ tests? {:#cxx-tests}

<pre>bazel query 'kind(cc_.*, tests(//foo:smoke_tests))'</pre>

#### Which of those are small?  Medium?  Large? {:#size-of-tests}

<pre>
bazel query 'attr(size, small, tests(//foo:smoke_tests))'

bazel query 'attr(size, medium, tests(//foo:smoke_tests))'

bazel query 'attr(size, large, tests(//foo:smoke_tests))'
</pre>

#### What are the tests beneath `foo` that match a pattern? {:#tests-beneath-foo}

<pre>bazel query 'filter("pa?t", kind(".*_test rule", //foo/...))'</pre>

The pattern is a regex and is applied to the full name of the rule. It's similar to doing

<pre>bazel query 'kind(".*_test rule", //foo/...)' | grep -E 'pa?t'</pre>

#### What package contains file `path/to/file/bar.java`? {:#barjava-package}

<pre> bazel query path/to/file/bar.java --output=package</pre>

#### What is the build label for `path/to/file/bar.java?` {:#barjava-build-label}

<pre>bazel query path/to/file/bar.java</pre>

#### What rule target(s) contain file `path/to/file/bar.java` as a source? {:#barjava-rule-targets}

<pre>
fullname=$(bazel query path/to/file/bar.java)
bazel query "attr('srcs', $fullname, ${fullname//:*/}:*)"
</pre>

### What package dependencies exist ... {:#package-dependencies}

#### What packages does `foo` depend on? (What do I need to check out to build `foo`) {:#packages-foo-depends-on}

<pre>bazel query 'buildfiles(deps(//foo:foo))' --output package</pre>

Note: `buildfiles` is required in order to correctly obtain all files
referenced by `subinclude`; see the reference manual for details.

#### What packages does the `foo` tree depend on, excluding `foo/contrib`? {:#packages-foo-tree-depends-on}

<pre>bazel query 'deps(foo/... except foo/contrib/...)' --output package</pre>

### What rule dependencies exist ... {:#rule-dependencies}

#### What genproto rules does bar depend upon? {:#genproto-rules}

<pre>bazel query 'kind(genproto, deps(bar/...))'</pre>

#### Find the definition of some JNI (C++) library that is transitively depended upon by a Java binary rule in the servlet tree. {:#jni-library}

<pre>bazel query 'some(kind(cc_.*library, deps(kind(java_binary, //java/com/example/frontend/...))))' --output location</pre>

##### ...Now find the definitions of all the Java binaries that depend on them {:#java-binaries}

<pre>bazel query 'let jbs = kind(java_binary, //java/com/example/frontend/...) in
  let cls = kind(cc_.*library, deps($jbs)) in
    $jbs intersect allpaths($jbs, $cls)'
</pre>

### What file dependencies exist ... {:#file-dependencies}

#### What's the complete set of Java source files required to build foo? {:#java-source-files}

Source files:

<pre>bazel query 'kind("source file", deps(//path/to/target/foo/...))' | grep java$</pre>

Generated files:

<pre>bazel query 'kind("generated file", deps(//path/to/target/foo/...))' | grep java$</pre>

#### What is the complete set of Java source files required to build QUX's tests? {:qux-tests}

Source files:

<pre>bazel query 'kind("source file", deps(kind(".*_test rule", javatests/com/example/qux/...)))' | grep java$</pre>

Generated files:

<pre>bazel query 'kind("generated file", deps(kind(".*_test rule", javatests/com/example/qux/...)))' | grep java$</pre>

### What differences in dependencies between X and Y exist ... {:#differences-in-dependencies}

#### What targets does `//foo` depend on that `//foo:foolib` does not? {:#foo-targets}

<pre>bazel query 'deps(//foo) except deps(//foo:foolib)'</pre>

#### What C++ libraries do the `foo` tests depend on that the `//foo` production binary does _not_ depend on? {:#foo-cxx-libraries}

<pre>bazel query 'kind("cc_library", deps(kind(".*test rule", foo/...)) except deps(//foo))'</pre>

### Why does this dependency exist ... {:#why-dependencies}

#### Why does `bar` depend on `groups2`? {:#dependency-bar-groups2}

<pre>bazel query 'somepath(bar/...,groups2/...:*)'</pre>

Once you have the results of this query, you will often find that a single
target stands out as being an unexpected or egregious and undesirable
dependency of `bar`. The query can then be further refined to:

#### Show me a path from `docker/updater:updater_systest` (a `py_test`) to some `cc_library` that it depends upon: {:#path-docker-cclibrary}

<pre>bazel query 'let cc = kind(cc_library, deps(docker/updater:updater_systest)) in
  somepath(docker/updater:updater_systest, $cc)'</pre>

#### Why does library `//photos/frontend:lib` depend on two variants of the same library `//third_party/jpeglib` and `//third_party/jpeg`? {:#library-two-variants}

This query boils down to: "show me the subgraph of `//photos/frontend:lib` that
depends on both libraries". When shown in topological order, the last element
of the result is the most likely culprit.

<pre>bazel query 'allpaths(//photos/frontend:lib, //third_party/jpeglib)
                intersect
               allpaths(//photos/frontend:lib, //third_party/jpeg)'
//photos/frontend:lib
//photos/frontend:lib_impl
//photos/frontend:lib_dispatcher
//photos/frontend:icons
//photos/frontend/modules/gadgets:gadget_icon
//photos/thumbnailer:thumbnail_lib
//third_party/jpeg/img:renderer
</pre>

### What depends on  ... {:#depends-on}

#### What rules under bar depend on Y? {:#rules-bar-y}

<pre>bazel query 'bar/... intersect allpaths(bar/..., Y)'</pre>

Note: `X intersect allpaths(X, Y)` is the general idiom for the query "which X
depend on Y?" If expression X is non-trivial, it may be convenient to bind a
name to it using `let` to avoid duplication.

#### What targets directly depend on T, in T's package? {:#targets-t}

<pre>bazel query 'same_pkg_direct_rdeps(T)'</pre>

### How do I break a dependency ... {:#break-dependency}

<!-- TODO find a convincing value of X to plug in here -->

#### What dependency paths do I have to break to make `bar` no longer depend on X? {:#break-dependency-bar-x}

To output the graph to a `svg` file:

<pre>bazel query 'allpaths(bar/...,X)' --output graph | dot -Tsvg &gt; /tmp/dep.svg</pre>

### Misc {:#misc}

#### How many sequential steps are there in the `//foo-tests` build? {:#steps-footests}

Unfortunately, the query language can't currently give you the longest path
from x to y, but it can find the (or rather _a_) most distant node from the
starting point, or show you the _lengths_ of the longest path from x to every
y that it depends on. Use `maxrank`:

<pre>bazel query 'deps(//foo-tests)' --output maxrank | tail -1
85 //third_party/zlib:zutil.c</pre>

The result indicates that there exist paths of length 85 that must occur in
order in this build.


Project: /_project.yaml
Book: /_book.yaml

# The Bazel Query Reference

{% include "_buttons.html" %}

This page is the reference manual for the _Bazel Query Language_ used
when you use `bazel query` to analyze build dependencies. It also
describes the output formats `bazel query` supports.

For practical use cases, see the [Bazel Query How-To](/query/guide).

## Additional query reference

In addition to `query`, which runs on the post-loading phase target graph,
Bazel includes *action graph query* and *configurable query*.

### Action graph query {:#aquery}

The action graph query (`aquery`) operates on the post-analysis Configured
Target Graph and exposes information about **Actions**, **Artifacts**, and
their relationships. `aquery` is useful when you are interested in the
properties of the Actions/Artifacts generated from the Configured Target Graph.
For example, the actual commands run and their inputs, outputs, and mnemonics.

For more details, see the [aquery reference](/query/aquery).

### Configurable query {:#cquery}

Traditional Bazel query runs on the post-loading phase target graph and
therefore has no concept of configurations and their related concepts. Notably,
it doesn't correctly resolve [select statements](/reference/be/functions#select)
and instead returns all possible resolutions of selects. However, the
configurable query environment, `cquery`, properly handles configurations but
doesn't provide all of the functionality of this original query.

For more details, see the [cquery reference](/query/cquery).


## Examples {:#examples}

How do people use `bazel query`?  Here are typical examples:

Why does the `//foo` tree depend on `//bar/baz`?
Show a path:

```
somepath(foo/..., //bar/baz:all)
```

What C++ libraries do all the `foo` tests depend on that
the `foo_bin` target does not?

```
kind("cc_library", deps(kind(".*test rule", foo/...)) except deps(//foo:foo_bin))
```

## Tokens: The lexical syntax {:#tokens}

Expressions in the query language are composed of the following
tokens:

* **Keywords**, such as `let`. Keywords are the reserved words of the
  language, and each of them is described below. The complete set
  of keywords is:

   * [`except`](#set-operations)

   * [`in`](#variables)

   * [`intersect`](#set-operations)

   * [`let`](#variables)

   * [`set`](#set)

   * [`union`](#set-operations)

* **Words**, such as "`foo/...`" or "`.*test rule`" or "`//bar/baz:all`". If a
  character sequence is "quoted" (begins and ends with a single-quote ' or
  begins and ends with a double-quote "), it is a word. If a character sequence
  is not quoted, it may still be parsed as a word. Unquoted words are sequences
  of characters drawn from the alphabet characters A-Za-z, the numerals 0-9,
  and the special characters `*/@.-_:$~[]` (asterisk, forward slash, at, period,
  hyphen, underscore, colon, dollar sign, tilde, left square brace, right square
  brace). However, unquoted words may not start with a hyphen `-` or asterisk `*`
  even though relative [target names](/concepts/labels#target-names) may start
  with those characters. As a special rule meant to simplify the handling of
  labels referring to external repositories, unquoted words that start with
  `@@` may contain `+` characters.

  Unquoted words also may not include the characters plus sign `+` or equals
  sign `=`, even though those characters are permitted in target names. When
  writing code that generates query expressions, target names should be quoted.

  Quoting _is_ necessary when writing scripts that construct Bazel query
  expressions from user-supplied values.

  ```
   //foo:bar+wiz    # WRONG: scanned as //foo:bar + wiz.
   //foo:bar=wiz    # WRONG: scanned as //foo:bar = wiz.
   "//foo:bar+wiz"  # OK.
   "//foo:bar=wiz"  # OK.
  ```

  Note that this quoting is in addition to any quoting that may be required by
  your shell, such as:

  ```posix-terminal
  bazel query ' "//foo:bar=wiz" '   # single-quotes for shell, double-quotes for Bazel.
  ```

  Keywords and operators, when quoted, are treated as ordinary words. For example, `some` is a
  keyword but "some" is a word. Both `foo` and "foo" are words.

  However, be careful when using single or double quotes in target names. When
  quoting one or more target names, use only one type of quotes (either all
  single or all double quotes).

  The following are examples of what the Java query string will be:


  ```
    'a"'a'         # WRONG: Error message: unclosed quotation.
    "a'"a"         # WRONG: Error message: unclosed quotation.
    '"a" + 'a''    # WRONG: Error message: unexpected token 'a' after query expression '"a" + '
    "'a' + "a""    # WRONG: Error message: unexpected token 'a' after query expression ''a' + '
    "a'a"          # OK.
    'a"a'          # OK.
    '"a" + "a"'    # OK
    "'a' + 'a'"    # OK
  ```

  We chose this syntax so that quote marks aren't needed in most cases. The
  (unusual) `".*test rule"` example needs quotes: it starts with a period and
  contains a space. Quoting `"cc_library"` is unnecessary but harmless.

* **Punctuation**, such as parens `()`, period `.` and comma `,`. Words
  containing punctuation (other than the exceptions listed above) must be quoted.

Whitespace characters outside of a quoted word are ignored.

## Bazel query language concepts {:#language-concepts}

The Bazel query language is a language of expressions. Every
expression evaluates to a **partially-ordered set** of targets,
or equivalently, a **graph** (DAG) of targets. This is the only
datatype.

Set and graph refer to the same datatype, but emphasize different
aspects of it, for example:

*   **Set:** The partial order of the targets is not interesting.
*   **Graph:** The partial order of targets is significant.

### Cycles in the dependency graph {:#dependency-graph-cycles}

Build dependency graphs should be acyclic.

The algorithms used by the query language are intended for use in
acyclic graphs, but are robust against cycles. The details of how
cycles are treated are not specified and should not be relied upon.

### Implicit dependencies {:#implicit-dependencies}

In addition to build dependencies that are defined explicitly in `BUILD` files,
Bazel adds additional _implicit_ dependencies to rules. Implicit dependencies
may be defined by:

- [Private attributes](/extending/rules#private_attributes_and_implicit_dependencies)
- [Toolchain requirements](/extending/toolchains#writing-rules-toolchains)

By default, `bazel query` takes implicit dependencies into account
when computing the query result. This behavior can be changed with
the `--[no]implicit_deps` option.

Note that, as query does not consider configurations, potential toolchain
**implementations** are not considered dependencies, only the
required toolchain types. See
[toolchain documentation](/extending/toolchains#writing-rules-toolchains).

### Soundness {:#soundness}

Bazel query language expressions operate over the build
dependency graph, which is the graph implicitly defined by all
rule declarations in all `BUILD` files. It is important to understand
that this graph is somewhat abstract, and does not constitute a
complete description of how to perform all the steps of a build. In
order to perform a build, a _configuration_ is required too;
see the [configurations](/docs/user-manual#configurations)
section of the User's Guide for more detail.

The result of evaluating an expression in the Bazel query language
is true _for all configurations_, which means that it may be
a conservative over-approximation, and not exactly precise. If you
use the query tool to compute the set of all source files needed
during a build, it may report more than are actually necessary
because, for example, the query tool will include all the files
needed to support message translation, even though you don't intend
to use that feature in your build.

### On the preservation of graph order {:#graph-order}

Operations preserve any ordering
constraints inherited from their subexpressions. You can think of
this as "the law of conservation of partial order". Consider an
example: if you issue a query to determine the transitive closure of
dependencies of a particular target, the resulting set is ordered
according to the dependency graph. If you filter that set to
include only the targets of `file` kind, the same
_transitive_ partial ordering relation holds between every
pair of targets in the resulting subset - even though none of
these pairs is actually directly connected in the original graph.
(There are no file-file edges in the build dependency graph).

However, while all operators _preserve_ order, some
operations, such as the [set operations](#set-operations)
don't _introduce_ any ordering constraints of their own.
Consider this expression:

```
deps(x) union y
```

The order of the final result set is guaranteed to preserve all the
ordering constraints of its subexpressions, namely, that all the
transitive dependencies of `x` are correctly ordered with
respect to each other. However, the query guarantees nothing about
the ordering of the targets in `y`, nor about the
ordering of the targets in `deps(x)` relative to those in
`y` (except for those targets in
`y` that also happen to be in `deps(x)`).

Operators that introduce ordering constraints include:
`allpaths`, `deps`, `rdeps`, `somepath`, and the target pattern wildcards
`package:*`, `dir/...`, etc.

### Sky query {:#sky-query}

_Sky Query_ is a mode of query that operates over a specified _universe scope_.

#### Special functions available only in SkyQuery

Sky Query mode has the additional query functions `allrdeps` and
`rbuildfiles`. These functions operate over the entire
universe scope (which is why they don't make sense for normal Query).

#### Specifying a universe scope

Sky Query mode is activated by passing the following two flags:
(`--universe_scope` or `--infer_universe_scope`) and
`--order_output=no`.
`--universe_scope=<target_pattern1>,...,<target_patternN>` tells query to
preload the transitive closure of the target pattern specified by the target patterns, which can
be both additive and subtractive. All queries are then evaluated in this "scope". In particular,
the [`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles) operators only return results from this scope.
`--infer_universe_scope` tells Bazel to infer a value for `--universe_scope`
from the query expression. This inferred value is the list of unique target patterns in the
query expression, but this might not be what you want. For example:

```posix-terminal
bazel query --infer_universe_scope --order_output=no "allrdeps(//my:target)"
```

The list of unique target patterns in this query expression is `["//my:target"]`, so
Bazel treats this the same as the invocation:

```posix-terminal
bazel query --universe_scope=//my:target --order_output=no "allrdeps(//my:target)"
```

But the result of that query with `--universe_scope` is only `//my:target`;
none of the reverse dependencies of `//my:target` are in the universe, by
construction! On the other hand, consider:

```posix-terminal
bazel query --infer_universe_scope --order_output=no "tests(//a/... + b/...) intersect allrdeps(siblings(rbuildfiles(my/starlark/file.bzl)))"
```

This is a meaningful query invocation that is trying to compute the test targets in the
[`tests`](#tests) expansion of the targets under some directories that
transitively depend on targets whose definition uses a certain `.bzl` file. Here,
`--infer_universe_scope` is a convenience, especially in the case where the choice of
`--universe_scope` would otherwise require you to parse the query expression yourself.

So, for query expressions that use universe-scoped operators like
[`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles) be sure to use
`--infer_universe_scope` only if its behavior is what you want.

Sky Query has some advantages and disadvantages compared to the default query. The main
disadvantage is that it cannot order its output according to graph order, and thus certain
[output formats](#output-formats) are forbidden. Its advantages are that it provides
two operators ([`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles)) that are not available in the default query.
As well, Sky Query does its work by introspecting the
[Skyframe](/reference/skyframe) graph, rather than creating a new
graph, which is what the default implementation does. Thus, there are some circumstances in which
it is faster and uses less memory.

## Expressions: Syntax and semantics of the grammar {:#expressions}

This is the grammar of the Bazel query language, expressed in EBNF notation:

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}word{{ '</var>' }}
       | let {{ '<var>' }}name{{ '</var>' }} = {{ '<var>' }}expr{{ '</var>' }} in {{ '<var>' }}expr{{ '</var>' }}
       | ({{ '<var>' }}expr{{ '</var>' }})
       | {{ '<var>' }}expr{{ '</var>' }} intersect {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} ^ {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} union {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} + {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} except {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} - {{ '<var>' }}expr{{ '</var>' }}
       | set({{ '<var>' }}word{{ '</var>' }} *)
       | {{ '<var>' }}word{{ '</var>' }} '(' {{ '<var>' }}int{{ '</var>' }} | {{ '<var>' }}word{{ '</var>' }} | {{ '<var>' }}expr{{ '</var>' }} ... ')'
```

The following sections describe each of the productions of this grammar in order.

### Target patterns {:#target-patterns}

```
expr ::= {{ '<var>' }}word{{ '</var>' }}
```

Syntactically, a _target pattern_ is just a word. It's interpreted as an
(unordered) set of targets. The simplest target pattern is a label, which
identifies a single target (file or rule). For example, the target pattern
`//foo:bar` evaluates to a set containing one element, the target, the `bar`
rule.

Target patterns generalize labels to include wildcards over packages and
targets. For example, `foo/...:all` (or just `foo/...`) is a target pattern
that evaluates to a set containing all _rules_ in every package recursively
beneath the `foo` directory; `bar/baz:all` is a target pattern that evaluates
to a set containing all the rules in the `bar/baz` package, but not its
subpackages.

Similarly, `foo/...:*` is a target pattern that evaluates to a set containing
all _targets_ (rules _and_ files) in every package recursively beneath the
`foo` directory; `bar/baz:*` evaluates to a set containing all the targets in
the `bar/baz` package, but not its subpackages.

Because the `:*` wildcard matches files as well as rules, it's often more
useful than `:all` for queries. Conversely, the `:all` wildcard (implicit in
target patterns like `foo/...`) is typically more useful for builds.

`bazel query` target patterns work the same as `bazel build` build targets do.
For more details, see [Target Patterns](/docs/user-manual#target-patterns), or
type `bazel help target-syntax`.

Target patterns may evaluate to a singleton set (in the case of a label), to a
set containing many elements (as in the case of `foo/...`, which has thousands
of elements) or to the empty set, if the target pattern matches no targets.

All nodes in the result of a target pattern expression are correctly ordered
relative to each other according to the dependency relation. So, the result of
`foo:*` is not just the set of targets in package `foo`, it is also the
_graph_ over those targets. (No guarantees are made about the relative ordering
of the result nodes against other nodes.) For more details, see the
[graph order](#graph-order) section.

### Variables {:#variables}

```none {:.devsite-disable-click-to-copy}
expr ::= let {{ '<var>' }}name{{ '</var>' }} = {{ '<var>' }}expr{{ '</var>' }}{{ '<sub>' }}1{{ '</sub>' }} in {{ '<var>' }}expr{{ '</var>' }}{{ '<sub>' }}2{{ '</sub>' }}
       | {{ '<var>' }}$name{{ '</var>' }}
```

The Bazel query language allows definitions of and references to
variables. The result of evaluation of a `let` expression is the same as
that of {{ '<var>' }}expr{{ '</var>' }}<sub>2</sub>, with all free occurrences
of variable {{ '<var>' }}name{{ '</var>' }} replaced by the value of
{{ '<var>' }}expr{{ '</var>' }}<sub>1</sub>.

For example, `let v = foo/... in allpaths($v, //common) intersect $v` is
equivalent to the `allpaths(foo/...,//common) intersect foo/...`.

An occurrence of a variable reference `name` other than in
an enclosing `let {{ '<var>' }}name{{ '</var>' }} = ...` expression is an
error. In other words, top-level query expressions cannot have free
variables.

In the above grammar productions, `name` is like _word_, but with the
additional constraint that it be a legal identifier in the C programming
language. References to the variable must be prepended with the "$" character.

Each `let` expression defines only a single variable, but you can nest them.

Both [target patterns](#target-patterns) and variable references consist of
just a single token, a word, creating a syntactic ambiguity. However, there is
no semantic ambiguity, because the subset of words that are legal variable
names is disjoint from the subset of words that are legal target patterns.

Technically speaking, `let` expressions do not increase
the expressiveness of the query language: any query expressible in
the language can also be expressed without them. However, they
improve the conciseness of many queries, and may also lead to more
efficient query evaluation.

### Parenthesized expressions {:#parenthesized-expressions}

```none {:.devsite-disable-click-to-copy}
expr ::= ({{ '<var>' }}expr{{ '</var>' }})
```

Parentheses associate subexpressions to force an order of evaluation.
A parenthesized expression evaluates to the value of its argument.

### Algebraic set operations: intersection, union, set difference {:#algebraic-set-operations}

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}expr{{ '</var>' }} intersect {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} ^ {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} union {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} + {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} except {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} - {{ '<var>' }}expr{{ '</var>' }}
```

These three operators compute the usual set operations over their arguments.
Each operator has two forms, a nominal form, such as `intersect`, and a
symbolic form, such as `^`. Both forms are equivalent; the symbolic forms are
quicker to type. (For clarity, the rest of this page uses the nominal forms.)

For example,

```
foo/... except foo/bar/...
```

evaluates to the set of targets that match `foo/...` but not `foo/bar/...`.

You can write the same query as:

```
foo/... - foo/bar/...
```

The `intersect` (`^`) and `union` (`+`) operations are commutative (symmetric);
`except` (`-`) is asymmetric. The parser treats all three operators as
left-associative and of equal precedence, so you might want parentheses. For
example, the first two of these expressions are equivalent, but the third is not:

```
x intersect y union z
(x intersect y) union z
x intersect (y union z)
```

Important: Use parentheses where there is any danger of ambiguity in reading a
query expression.

### Read targets from an external source: set {:#set}

```none {:.devsite-disable-click-to-copy}
expr ::= set({{ '<var>' }}word{{ '</var>' }} *)
```

The `set({{ '<var>' }}a{{ '</var>' }} {{ '<var>' }}b{{ '</var>' }} {{ '<var>' }}c{{ '</var>' }} ...)`
operator computes the union of a set of zero or more
[target patterns](#target-patterns), separated by whitespace (no commas).

In conjunction with the Bourne shell's `$(...)` feature, `set()` provides a
means of saving the results of one query in a regular text file, manipulating
that text file using other programs (such as standard UNIX shell tools), and then
introducing the result back into the query tool as a value for further
processing. For example:

```posix-terminal
bazel query deps(//my:target) --output=label | grep ... | sed ... | awk ... > foo

bazel query "kind(cc_binary, set($(<foo)))"
```

In the next example,`kind(cc_library, deps(//some_dir/foo:main, 5))` is
computed by filtering on the `maxrank` values using an `awk` program.

```posix-terminal
bazel query 'deps(//some_dir/foo:main)' --output maxrank | awk '($1 < 5) { print $2;} ' > foo

bazel query "kind(cc_library, set($(<foo)))"
```

In these examples, `$(<foo)` is a shorthand for `$(cat foo)`, but shell
commands other than `cat` may be used too—such as the previous `awk` command.

Note: `set()` introduces no graph ordering constraints, so path information may
be lost when saving and reloading sets of nodes using it. For more details,
see the [graph order](#graph-order) section below.

## Functions {:#functions}

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}word{{ '</var>' }} '(' {{ '<var>' }}int{{ '</var>' }} | {{ '<var>' }}word{{ '</var>' }} | {{ '<var>' }}expr{{ '</var>' }} ... ')'
```

The query language defines several functions. The name of the function
determines the number and type of arguments it requires. The following
functions are available:

* [`allpaths`](#somepath-allpaths)
* [`attr`](#attr)
* [`buildfiles`](#buildfiles)
* [`rbuildfiles`](#rbuildfiles)
* [`deps`](#deps)
* [`filter`](#filter)
* [`kind`](#kind)
* [`labels`](#labels)
* [`loadfiles`](#loadfiles)
* [`rdeps`](#rdeps)
* [`allrdeps`](#allrdeps)
* [`same_pkg_direct_rdeps`](#same_pkg_direct_rdeps)
* [`siblings`](#siblings)
* [`some`](#some)
* [`somepath`](#somepath-allpaths)
* [`tests`](#tests)
* [`visible`](#visible)



### Transitive closure of dependencies: deps {:#deps}

```none {:.devsite-disable-click-to-copy}
expr ::= deps({{ '<var>' }}expr{{ '</var>' }})
       | deps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

The `deps({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the graph formed
by the transitive closure of dependencies of its argument set
{{ '<var>' }}x{{ '</var>' }}. For example, the value of `deps(//foo)` is the
dependency graph rooted at the single node `foo`, including all its
dependencies. The value of `deps(foo/...)` is the dependency graphs whose roots
are all rules in every package beneath the `foo` directory. In this context,
'dependencies' means only rule and file targets, therefore the `BUILD` and
Starlark files needed to create these targets are not included here. For that
you should use the [`buildfiles`](#buildfiles) operator.

The resulting graph is ordered according to the dependency relation. For more
details, see the section on [graph order](#graph-order).

The `deps` operator accepts an optional second argument, which is an integer
literal specifying an upper bound on the depth of the search. So
`deps(foo:*, 0)` returns all targets in the `foo` package, while
`deps(foo:*, 1)` further includes the direct prerequisites of any target in the
`foo` package, and `deps(foo:*, 2)` further includes the nodes directly
reachable from the nodes in `deps(foo:*, 1)`, and so on. (These numbers
correspond to the ranks shown in the [`minrank`](#output-ranked) output format.)
If the {{ '<var>' }}depth{{ '</var>' }} parameter is omitted, the search is
unbounded: it computes the reflexive transitive closure of prerequisites.

### Transitive closure of reverse dependencies: rdeps {:#rdeps}

```none {:.devsite-disable-click-to-copy}
expr ::= rdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
       | rdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

The `rdeps({{ '<var>' }}u{{ '</var>' }}, {{ '<var>' }}x{{ '</var>' }})`
operator evaluates to the reverse dependencies of the argument set
{{ '<var>' }}x{{ '</var>' }} within the transitive closure of the universe set
{{ '<var>' }}u{{ '</var>' }}.

The resulting graph is ordered according to the dependency relation. See the
section on [graph order](#graph-order) for more details.

The `rdeps` operator accepts an optional third argument, which is an integer
literal specifying an upper bound on the depth of the search. The resulting
graph only includes nodes within a distance of the specified depth from any
node in the argument set. So `rdeps(//foo, //common, 1)` evaluates to all nodes
in the transitive closure of `//foo` that directly depend on `//common`. (These
numbers correspond to the ranks shown in the [`minrank`](#output-ranked) output
format.) If the {{ '<var>' }}depth{{ '</var>' }} parameter is omitted, the
search is unbounded.

### Transitive closure of all reverse dependencies: allrdeps {:#allrdeps}

```
expr ::= allrdeps({{ '<var>' }}expr{{ '</var>' }})
       | allrdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

Note: Only available with [Sky Query](#sky-query)

The `allrdeps` operator behaves just like the [`rdeps`](#rdeps)
operator, except that the "universe set" is whatever the `--universe_scope` flag
evaluated to, instead of being separately specified. Thus, if
`--universe_scope=//foo/...` was passed, then `allrdeps(//bar)` is
equivalent to `rdeps(//foo/..., //bar)`.

### Direct reverse dependencies in the same package: same_pkg_direct_rdeps {:#same_pkg_direct_rdeps}

```
expr ::= same_pkg_direct_rdeps({{ '<var>' }}expr{{ '</var>' }})
```

The `same_pkg_direct_rdeps({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the full set of targets
that are in the same package as a target in the argument set, and which directly depend on it.

### Dealing with a target's package: siblings {:#siblings}

```
expr ::= siblings({{ '<var>' }}expr{{ '</var>' }})
```

The `siblings({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the full set of targets that are in
the same package as a target in the argument set.

### Arbitrary choice: some {:#some}

```
expr ::= some({{ '<var>' }}expr{{ '</var>' }})
       | some({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}count{{ '</var> '}})
```

The `some({{ '<var>' }}x{{ '</var>' }}, {{ '<var>' }}k{{ '</var>' }})` operator
selects at most {{ '<var>' }}k{{ '</var>' }} targets arbitrarily from its
argument set {{ '<var>' }}x{{ '</var>' }}, and evaluates to a set containing
only those targets. Parameter {{ '<var>' }}k{{ '</var>' }} is optional; if
missing, the result will be a singleton set containing only one target
arbitrarily selected. If the size of argument set {{ '<var>' }}x{{ '</var>' }} is
smaller than {{ '<var>' }}k{{ '</var>' }}, the whole argument set
{{ '<var>' }}x{{ '</var>' }} will be returned.

For example, the expression `some(//foo:main union //bar:baz)` evaluates to a
singleton set containing either `//foo:main` or `//bar:baz`—though which
one is not defined. The expression `some(//foo:main union //bar:baz, 2)` or
`some(//foo:main union //bar:baz, 3)` returns both `//foo:main` and
`//bar:baz`.

If the argument is a singleton, then `some`
computes the identity function: `some(//foo:main)` is
equivalent to `//foo:main`.

It is an error if the specified argument set is empty, as in the
expression `some(//foo:main intersect //bar:baz)`.

### Path operators: somepath, allpaths {:#somepath-allpaths}

```
expr ::= somepath({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
       | allpaths({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `somepath({{ '<var>' }}S{{ '</var>' }}, {{ '<var>' }}E{{ '</var>' }})` and
`allpaths({{ '<var>' }}S{{ '</var>' }}, {{ '<var>' }}E{{ '</var>' }})` operators compute
paths between two sets of targets. Both queries accept two
arguments, a set {{ '<var>' }}S{{ '</var>' }} of starting points and a set
{{ '<var>' }}E{{ '</var>' }} of ending points. `somepath` returns the
graph of nodes on _some_ arbitrary path from a target in
{{ '<var>' }}S{{ '</var>' }} to a target in {{ '<var>' }}E{{ '</var>' }}; `allpaths`
returns the graph of nodes on _all_ paths from any target in
{{ '<var>' }}S{{ '</var>' }} to any target in {{ '<var>' }}E{{ '</var>' }}.

The resulting graphs are ordered according to the dependency relation.
See the section on [graph order](#graph-order) for more details.

<table>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/somepath1.svg" alt="Somepath">
        <figcaption><code>somepath(S1 + S2, E)</code>, one possible result.</figcaption>
      </figure>
<!-- digraph somepath1 {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1;
  n2 [fillcolor="pink",style=filled];
  n3 [fillcolor="pink",style=filled];
  n4 [fillcolor="pink",style=filled,label="E"];
  n5; n6;
  n7 [fillcolor="pink",style=filled,label="S1"];
  n8 [label="S2"];
  n9;
  n10 [fillcolor="pink",style=filled];
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
    <td>
      <figure>
        <img src="/docs/images/somepath2.svg" alt="Somepath">
        <figcaption><code>somepath(S1 + S2, E)</code>, another possible result.</figcaption>
      </figure>
<!-- digraph somepath2 {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1; n2; n3;
  n4 [fillcolor="pink",style=filled,label="E"];
  n5;
  n6 [fillcolor="pink",style=filled];
  n7 [label="S1"];
  n8 [fillcolor="pink",style=filled,label="S2"];
  n9; n10;
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
    <td>
      <figure>
        <img src="/docs/images/allpaths.svg" alt="Allpaths">
        <figcaption><code>allpaths(S1 + S2, E)</code></figcaption>
      </figure>
<!-- digraph allpaths {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1;
  n2 [fillcolor="pink",style=filled];
  n3 [fillcolor="pink",style=filled];
  n4 [fillcolor="pink",style=filled,label="E"];
  n5 [fillcolor="pink",style=filled];
  n6 [fillcolor="pink",style=filled];
  n7 [fillcolor="pink",style=filled, label="S1"];
  n8 [fillcolor="pink",style=filled, label="S2"];
  n9;
  n10 [fillcolor="pink",style=filled];
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
  </tr>
</table>

### Target kind filtering: kind {:#kind}

```
expr ::= kind({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `kind({{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards those targets
that are not of the expected kind. The {{ '<var>' }}pattern{{ '</var>' }}
parameter specifies what kind of target to match.

For example, the kinds for the four targets defined by the `BUILD` file
(for package `p`) shown below are illustrated in the table:

<table>
  <tr>
    <th>Code</th>
    <th>Target</th>
    <th>Kind</th>
  </tr>
  <tr>
    <td rowspan="4">
      <pre>
        genrule(
            name = "a",
            srcs = ["a.in"],
            outs = ["a.out"],
            cmd = "...",
        )
      </pre>
    </td>
    <td><code>//p:a</code></td>
    <td>genrule rule</td>
  </tr>
  <tr>
    <td><code>//p:a.in</code></td>
    <td>source file</td>
  </tr>
  <tr>
    <td><code>//p:a.out</code></td>
    <td>generated file</td>
  </tr>
  <tr>
    <td><code>//p:BUILD</code></td>
    <td>source file</td>
  </tr>
</table>

Thus, `kind("cc_.* rule", foo/...)` evaluates to the set
of all `cc_library`, `cc_binary`, etc,
rule targets beneath `foo`, and `kind("source file", deps(//foo))`
evaluates to the set of all source files in the transitive closure
of dependencies of the `//foo` target.

Quotation of the {{ '<var>' }}pattern{{ '</var>' }} argument is often required
because without it, many [regular expressions](#regex), such as `source
file` and `.*_test`, are not considered words by the parser.

When matching for `package group`, targets ending in
`:all` may not yield any results. Use `:all-targets` instead.

### Target name filtering: filter {:#filter}

```
expr ::= filter({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `filter({{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards targets whose
labels (in absolute form) do not match the pattern; it
evaluates to a subset of its input.

The first argument, {{ '<var>' }}pattern{{ '</var>' }} is a word containing a
[regular expression](#regex) over target names. A `filter` expression
evaluates to the set containing all targets {{ '<var>' }}x{{ '</var>' }} such that
{{ '<var>' }}x{{ '</var>' }} is a member of the set {{ '<var>' }}input{{ '</var>' }} and the
label (in absolute form, such as `//foo:bar`)
of {{ '<var>' }}x{{ '</var>' }} contains an (unanchored) match
for the regular expression {{ '<var>' }}pattern{{ '</var>' }}. Since all
target names start with `//`, it may be used as an alternative
to the `^` regular expression anchor.

This operator often provides a much faster and more robust alternative to the
`intersect` operator. For example, in order to see all
`bar` dependencies of the `//foo:foo` target, one could
evaluate

```
deps(//foo) intersect //bar/...
```

This statement, however, will require parsing of all `BUILD` files in the
`bar` tree, which will be slow and prone to errors in
irrelevant `BUILD` files. An alternative would be:

```
filter(//bar, deps(//foo))
```

which would first calculate the set of `//foo` dependencies and
then would filter only targets matching the provided pattern—in other
words, targets with names containing `//bar` as a substring.

Another common use of the `filter({{ '<var>' }}pattern{{ '</var>' }},
{{ '<var>' }}expr{{ '</var>' }})` operator is to filter specific files by their
name or extension. For example,

```
filter("\.cc$", deps(//foo))
```

will provide a list of all `.cc` files used to build `//foo`.

### Rule attribute filtering: attr {:#attr}

```
expr ::= attr({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The
`attr({{ '<var>' }}name{{ '</var>' }}, {{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards targets that aren't
rules, rule targets that do not have attribute {{ '<var>' }}name{{ '</var>' }}
defined or rule targets where the attribute value does not match the provided
[regular expression](#regex) {{ '<var>' }}pattern{{ '</var>' }}; it evaluates
to a subset of its input.

The first argument, {{ '<var>' }}name{{ '</var>' }} is the name of the rule
attribute that should be matched against the provided
[regular expression](#regex) pattern. The second argument,
{{ '<var>' }}pattern{{ '</var>' }} is a regular expression over the attribute
values. An `attr` expression evaluates to the set containing all targets
{{ '<var>' }}x{{ '</var>' }} such that  {{ '<var>' }}x{{ '</var>' }} is a
member of the set {{ '<var>' }}input{{ '</var>' }}, is a rule with the defined
attribute {{ '<var>' }}name{{ '</var>' }} and the attribute value contains an
(unanchored) match for the regular expression
{{ '<var>' }}pattern{{ '</var>' }}. If {{ '<var>' }}name{{ '</var>' }} is an
optional attribute and rule does not specify it explicitly then default
attribute value will be used for comparison. For example,

```
attr(linkshared, 0, deps(//foo))
```

will select all `//foo` dependencies that are allowed to have a
linkshared attribute (such as, `cc_binary` rule) and have it either
explicitly set to 0 or do not set it at all but default value is 0 (such as for
`cc_binary` rules).

List-type attributes (such as `srcs`, `data`, etc) are
converted to strings of the form `[value<sub>1</sub>, ..., value<sub>n</sub>]`,
starting with a `[` bracket, ending with a `]` bracket
and using "`, `" (comma, space) to delimit multiple values.
Labels are converted to strings by using the absolute form of the
label. For example, an attribute `deps=[":foo",
"//otherpkg:bar", "wiz"]` would be converted to the
string `[//thispkg:foo, //otherpkg:bar, //thispkg:wiz]`.
Brackets are always present, so the empty list would use string value `[]`
for matching purposes. For example,

```
attr("srcs", "\[\]", deps(//foo))
```

will select all rules among `//foo` dependencies that have an
empty `srcs` attribute, while

```
attr("data", ".{3,}", deps(//foo))
```

will select all rules among `//foo` dependencies that specify at
least one value in the `data` attribute (every label is at least
3 characters long due to the `//` and `:`).

To select all rules among `//foo` dependencies with a particular `value` in a
list-type attribute, use

```
attr("tags", "[\[ ]value[,\]]", deps(//foo))
```

This works because the character before `value` will be `[` or a space and the
character after `value` will be a comma or `]`.

To select all rules among `//foo` dependencies with a particular `key` and
`value` in a dict-type attribute, use

```
attr("some_dict_attribute", "[\{ ]key=value[,\}]", deps(//foo))
```

This would select `//foo` if `//foo` is defined as

```
some_rule(
  name = "foo",
  some_dict_attribute = {
    "key": "value",
  },
)
```

This works because the character before `key=value` will be `{` or a space and
the character after `key=value` will be a comma or `}`.

### Rule visibility filtering: visible {:#visible}

```
expr ::= visible({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `visible({{ '<var>' }}predicate{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})` operator
applies a filter to a set of targets, and discards targets without the
required visibility.

The first argument, {{ '<var>' }}predicate{{ '</var>' }}, is a set of targets that all targets
in the output must be visible to. A {{ '<var>' }}visible{{ '</var>' }} expression
evaluates to the set containing all targets {{ '<var>' }}x{{ '</var>' }} such that {{ '<var>' }}x{{ '</var>' }}
is a member of the set {{ '<var>' }}input{{ '</var>' }}, and for all targets {{ '<var>' }}y{{ '</var>' }} in
{{ '<var>' }}predicate{{ '</var>' }} {{ '<var>' }}x{{ '</var>' }} is visible to {{ '<var>' }}y{{ '</var>' }}. For example:

```
visible(//foo, //bar:*)
```

will select all targets in the package `//bar` that `//foo`
can depend on without violating visibility restrictions.

### Evaluation of rule attributes of type label: labels {:#labels}

```
expr ::= labels({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `labels({{ '<var>' }}attr_name{{ '</var>' }}, {{ '<var>' }}inputs{{ '</var>' }})`
operator returns the set of targets specified in the
attribute {{ '<var>' }}attr_name{{ '</var>' }} of type "label" or "list of label" in
some rule in set {{ '<var>' }}inputs{{ '</var>' }}.

For example, `labels(srcs, //foo)` returns the set of
targets appearing in the `srcs` attribute of
the `//foo` rule. If there are multiple rules
with `srcs` attributes in the {{ '<var>' }}inputs{{ '</var>' }} set, the
union of their `srcs` is returned.

### Expand and filter test_suites: tests {:#tests}

```
expr ::= tests({{ '<var>' }}expr{{ '</var>' }})
```

The `tests({{ '<var>' }}x{{ '</var>' }})` operator returns the set of all test
rules in set {{ '<var>' }}x{{ '</var>' }}, expanding any `test_suite` rules into
the set of individual tests that they refer to, and applying filtering by
`tag` and `size`.

By default, query evaluation
ignores any non-test targets in all `test_suite` rules. This can be
changed to errors with the `--strict_test_suite` option.

For example, the query `kind(test, foo:*)` lists all
the `*_test` and `test_suite` rules
in the `foo` package. All the results are (by
definition) members of the `foo` package. In contrast,
the query `tests(foo:*)` will return all of the
individual tests that would be executed by `bazel test
foo:*`: this may include tests belonging to other packages,
that are referenced directly or indirectly
via `test_suite` rules.

### Package definition files: buildfiles {:#buildfiles}

```
expr ::= buildfiles({{ '<var>' }}expr{{ '</var>' }})
```

The `buildfiles({{ '<var>' }}x{{ '</var>' }})` operator returns the set
of files that define the packages of each target in
set {{ '<var>' }}x{{ '</var>' }}; in other words, for each package, its `BUILD` file,
plus any .bzl files it references via `load`. Note that this
also returns the `BUILD` files of the packages containing these
`load`ed files.

This operator is typically used when determining what files or
packages are required to build a specified target, often in conjunction with
the [`--output package`](#output-package) option, below). For example,

```posix-terminal
bazel query 'buildfiles(deps(//foo))' --output package
```

returns the set of all packages on which `//foo` transitively depends.

Note: A naive attempt at the above query would omit
the `buildfiles` operator and use only `deps`,
but this yields an incorrect result: while the result contains the
majority of needed packages, those packages that contain only files
that are `load()`'ed will be missing.

Warning: Bazel pretends each `.bzl` file produced by
`buildfiles` has a corresponding target (for example, file `a/b.bzl` =>
target `//a:b.bzl`), but this isn't necessarily the case. Therefore,
`buildfiles` doesn't compose well with other query operators and its results can be
misleading when formatted in a structured way, such as
[`--output=xml`](#xml).

### Package definition files: rbuildfiles {:#rbuildfiles}

```
expr ::= rbuildfiles({{ '<var>' }}word{{ '</var>' }}, ...)
```

Note: Only available with [Sky Query](#sky-query).

The `rbuildfiles` operator takes a comma-separated list of path fragments and returns
the set of `BUILD` files that transitively depend on these path fragments. For instance, if
`//foo` is a package, then `rbuildfiles(foo/BUILD)` will return the
`//foo:BUILD` target. If the `foo/BUILD` file has
`load('//bar:file.bzl'...` in it, then `rbuildfiles(bar/file.bzl)` will
return the `//foo:BUILD` target, as well as the targets for any other `BUILD` files that
load `//bar:file.bzl`

The scope of the <scope>rbuildfiles</scope> operator is the universe specified by the
`--universe_scope` flag. Files that do not correspond directly to `BUILD` files and `.bzl`
files do not affect the results. For instance, source files (like `foo.cc`) are ignored,
even if they are explicitly mentioned in the `BUILD` file. Symlinks, however, are respected, so that
if `foo/BUILD` is a symlink to `bar/BUILD`, then
`rbuildfiles(bar/BUILD)` will include `//foo:BUILD` in its results.

The `rbuildfiles` operator is almost morally the inverse of the
[`buildfiles`](#buildfiles) operator. However, this moral inversion
holds more strongly in one direction: the outputs of `rbuildfiles` are just like the
inputs of `buildfiles`; the former will only contain `BUILD` file targets in packages,
and the latter may contain such targets. In the other direction, the correspondence is weaker. The
outputs of the `buildfiles` operator are targets corresponding to all packages and .`bzl`
files needed by a given input. However, the inputs of the `rbuildfiles` operator are
not those targets, but rather the path fragments that correspond to those targets.

### Package definition files: loadfiles {:#loadfiles}

```
expr ::= loadfiles({{ '<var>' }}expr{{ '</var>' }})
```

The `loadfiles({{ '<var>' }}x{{ '</var>' }})` operator returns the set of
Starlark files that are needed to load the packages of each target in
set {{ '<var>' }}x{{ '</var>' }}. In other words, for each package, it returns the
.bzl files that are referenced from its `BUILD` files.

Warning: Bazel pretends each of these .bzl files has a corresponding target
(for example, file `a/b.bzl` => target `//a:b.bzl`), but this isn't
necessarily the case. Therefore, `loadfiles` doesn't compose well with other query
operators and its results can be misleading when formatted in a structured way, such as
[`--output=xml`](#xml).

## Output formats {:#output-formats}

`bazel query` generates a graph.
You specify the content, format, and ordering by which
`bazel query` presents this graph
by means of the `--output` command-line option.

When running with [Sky Query](#sky-query), only output formats that are compatible with
unordered output are allowed. Specifically, `graph`, `minrank`, and
`maxrank` output formats are forbidden.

Some of the output formats accept additional options. The name of
each output option is prefixed with the output format to which it
applies, so `--graph:factored` applies only
when `--output=graph` is being used; it has no effect if
an output format other than `graph` is used. Similarly,
`--xml:line_numbers` applies only when `--output=xml`
is being used.

### On the ordering of results {:#results-ordering}

Although query expressions always follow the "[law of
conservation of graph order](#graph-order)", _presenting_ the results may be done
in either a dependency-ordered or unordered manner. This does **not**
influence the targets in the result set or how the query is computed. It only
affects how the results are printed to stdout. Moreover, nodes that are
equivalent in the dependency order may or may not be ordered alphabetically.
The `--order_output` flag can be used to control this behavior.
(The `--[no]order_results` flag has a subset of the functionality
of the `--order_output` flag and is deprecated.)

The default value of this flag is `auto`, which prints results in **lexicographical
order**. However, when `somepath(a,b)` is used, the results will be printed in
`deps` order instead.

When this flag is `no` and `--output` is one of
`build`, `label`, `label_kind`, `location`, `package`, `proto`, or
`xml`, the outputs will be printed in arbitrary order. **This is
generally the fastest option**. It is not supported though when
`--output` is one of `graph`, `minrank` or
`maxrank`: with these formats, Bazel always prints results
ordered by the dependency order or rank.

When this flag is `deps`, Bazel prints results in some topological order—that is,
dependents first and dependencies after. However, nodes that are unordered by the
dependency order (because there is no path from either one to the other) may be
printed in any order.

When this flag is `full`, Bazel prints nodes in a fully deterministic (total) order.
First, all nodes are sorted alphabetically. Then, each node in the list is used as the start of a
post-order depth-first search in which outgoing edges to unvisited nodes are traversed in
alphabetical order of the successor nodes. Finally, nodes are printed in the reverse of the order
in which they were visited.

Printing nodes in this order may be slower, so it should be used only when determinism is
important.

### Print the source form of targets as they would appear in BUILD {:#target-source-form}

```
--output build
```

With this option, the representation of each target is as if it were
hand-written in the BUILD language. All variables and function calls
(such as glob, macros) are expanded, which is useful for seeing the effect
of Starlark macros. Additionally, each effective rule reports a
`generator_name` and/or `generator_function`) value,
giving the name of the macro that was evaluated to produce the effective rule.

Although the output uses the same syntax as `BUILD` files, it is not
guaranteed to produce a valid `BUILD` file.

### Print the label of each target {:#print-label-target}

```
--output label
```

With this option, the set of names (or _labels_) of each target
in the resulting graph is printed, one label per line, in
topological order (unless `--noorder_results` is specified, see
[notes on the ordering of results](#result-order)).
(A topological ordering is one in which a graph
node appears earlier than all of its successors.)  Of course there
are many possible topological orderings of a graph (_reverse
postorder_ is just one); which one is chosen is not specified.

When printing the output of a `somepath` query, the order
in which the nodes are printed is the order of the path.

Caveat: in some corner cases, there may be two distinct targets with
the same label; for example, a `sh_binary` rule and its
sole (implicit) `srcs` file may both be called
`foo.sh`. If the result of a query contains both of
these targets, the output (in `label` format) will appear
to contain a duplicate. When using the `label_kind` (see
below) format, the distinction becomes clear: the two targets have
the same name, but one has kind `sh_binary rule` and the
other kind `source file`.

### Print the label and kind of each target {:#print-target-label}

```
--output label_kind
```

Like `label`, this output format prints the labels of
each target in the resulting graph, in topological order, but it
additionally precedes the label by the [_kind_](#kind) of the target.

### Print targets in protocol buffer format {:#print-target-proto}

```
--output proto
```

Prints the query output as a
[`QueryResult`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffer.

### Print targets in length-delimited protocol buffer format {:#print-target-length-delimited-proto}

```
--output streamed_proto
```

Prints a
[length-delimited](https://protobuf.dev/programming-guides/encoding/#size-limit)
stream of
[`Target`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffers. This is useful to _(i)_ get around
[size limitations](https://protobuf.dev/programming-guides/encoding/#size-limit)
of protocol buffers when there are too many targets to fit in a single
`QueryResult` or _(ii)_ to start processing while Bazel is still outputting.

### Print targets in text proto format {:#print-target-textproto}

```
--output textproto
```

Similar to `--output proto`, prints the
[`QueryResult`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffer but in
[text format](https://protobuf.dev/reference/protobuf/textformat-spec/).

### Print targets in ndjson format {:#print-target-streamed-jsonproto}

```
--output streamed_jsonproto
```

Similar to `--output streamed_proto`, prints a stream of
[`Target`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffers but in [ndjson](https://github.com/ndjson/ndjson-spec) format.

### Print the label of each target, in rank order {:#print-target-label-rank-order}

```
--output minrank --output maxrank
```

Like `label`, the `minrank`
and `maxrank` output formats print the labels of each
target in the resulting graph, but instead of appearing in
topological order, they appear in rank order, preceded by their
rank number. These are unaffected by the result ordering
`--[no]order_results` flag (see [notes on
the ordering of results](#result-order)).

There are two variants of this format: `minrank` ranks
each node by the length of the shortest path from a root node to it.
"Root" nodes (those which have no incoming edges) are of rank 0,
their successors are of rank 1, etc. (As always, edges point from a
target to its prerequisites: the targets it depends upon.)

`maxrank` ranks each node by the length of the longest
path from a root node to it. Again, "roots" have rank 0, all other
nodes have a rank which is one greater than the maximum rank of all
their predecessors.

All nodes in a cycle are considered of equal rank. (Most graphs are
acyclic, but cycles do occur
simply because `BUILD` files contain erroneous cycles.)

These output formats are useful for discovering how deep a graph is.
If used for the result of a `deps(x)`, `rdeps(x)`,
or `allpaths` query, then the rank number is equal to the
length of the shortest (with `minrank`) or longest
(with `maxrank`) path from `x` to a node in
that rank. `maxrank` can be used to determine the
longest sequence of build steps required to build a target.

Note: The ranked output of a `somepath` query is
basically meaningless because `somepath` doesn't
guarantee to return either a shortest or a longest path, and it may
include "transitive" edges from one path node to another that are
not direct edges in original graph.

For example, the graph on the left yields the outputs on the right
when `--output minrank` and `--output maxrank`
are specified, respectively.

<table>
  <tr>
    <td><img src="/docs/images/out-ranked.svg" alt="Out ranked">
    </td>
    <td>
      <pre>
      minrank

      0 //c:c
      1 //b:b
      1 //a:a
      2 //b:b.cc
      2 //a:a.cc
      </pre>
    </td>
    <td>
      <pre>
      maxrank

      0 //c:c
      1 //b:b
      2 //a:a
      2 //b:b.cc
      3 //a:a.cc
      </pre>
    </td>
  </tr>
</table>

### Print the location of each target {:#print-target-location}

```
--output location
```

Like `label_kind`, this option prints out, for each
target in the result, the target's kind and label, but it is
prefixed by a string describing the location of that target, as a
filename and line number. The format resembles the output of
`grep`. Thus, tools that can parse the latter (such as Emacs
or vi) can also use the query output to step through a series of
matches, allowing the Bazel query tool to be used as a
dependency-graph-aware "grep for BUILD files".

The location information varies by target kind (see the [kind](#kind) operator). For rules, the
location of the rule's declaration within the `BUILD` file is printed.
For source files, the location of line 1 of the actual file is
printed. For a generated file, the location of the rule that
generates it is printed. (The query tool does not have sufficient
information to find the actual location of the generated file, and
in any case, it might not exist if a build has not yet been performed.)

### Print the set of packages {:#print-package-set}

```--output package```

This option prints the name of all packages to which
some target in the result set belongs. The names are printed in
lexicographical order; duplicates are excluded. Formally, this
is a _projection_ from the set of labels (package, target) onto
packages.

Packages in external repositories are formatted as
`@repo//foo/bar` while packages in the main repository are
formatted as `foo/bar`.

In conjunction with the `deps(...)` query, this output
option can be used to find the set of packages that must be checked
out in order to build a given set of targets.

### Display a graph of the result {:#display-result-graph}

```--output graph```

This option causes the query result to be printed as a directed
graph in the popular AT&amp;T GraphViz format. Typically the
result is saved to a file, such as `.png` or `.svg`.
(If the `dot` program is not installed on your workstation, you
can install it using the command `sudo apt-get install graphviz`.)
See the example section below for a sample invocation.

This output format is particularly useful for `allpaths`,
`deps`, or `rdeps` queries, where the result
includes a _set of paths_ that cannot be easily visualized when
rendered in a linear form, such as with `--output label`.

By default, the graph is rendered in a _factored_ form. That is,
topologically-equivalent nodes are merged together into a single
node with multiple labels. This makes the graph more compact
and readable, because typical result graphs contain highly
repetitive patterns. For example, a `java_library` rule
may depend on hundreds of Java source files all generated by the
same `genrule`; in the factored graph, all these files
are represented by a single node. This behavior may be disabled
with the `--nograph:factored` option.

#### `--graph:node_limit {{ '<var>' }}n{{ '</var>' }}` {:#graph-nodelimit}

The option specifies the maximum length of the label string for a
graph node in the output. Longer labels will be truncated; -1
disables truncation. Due to the factored form in which graphs are
usually printed, the node labels may be very long. GraphViz cannot
handle labels exceeding 1024 characters, which is the default value
of this option. This option has no effect unless
`--output=graph` is being used.

#### `--[no]graph:factored` {:#graph-factored}

By default, graphs are displayed in factored form, as explained
[above](#output-graph).
When `--nograph:factored` is specified, graphs are
printed without factoring. This makes visualization using GraphViz
impractical, but the simpler format may ease processing by other
tools (such as grep). This option has no effect
unless `--output=graph` is being used.

### XML {:#xml}

```--output xml```

This option causes the resulting targets to be printed in an XML
form. The output starts with an XML header such as this

```
  <?xml version="1.0" encoding="UTF-8"?>
  <query version="2">
```

<!-- The docs should continue to document version 2 into perpetuity,
     even if we add new formats, to handle clients synced to old CLs. -->

and then continues with an XML element for each target
in the result graph, in topological order (unless
[unordered results](#result-order) are requested),
and then finishes with a terminating

```
</query>
```

Simple entries are emitted for targets of `file` kind:

```
  <source-file name='//foo:foo_main.cc' .../>
  <generated-file name='//foo:libfoo.so' .../>
```

But for rules, the XML is structured and contains definitions of all
the attributes of the rule, including those whose value was not
explicitly specified in the rule's `BUILD` file.

Additionally, the result includes `rule-input` and
`rule-output` elements so that the topology of the
dependency graph can be reconstructed without having to know that,
for example, the elements of the `srcs` attribute are
forward dependencies (prerequisites) and the contents of the
`outs` attribute are backward dependencies (consumers).

`rule-input` elements for [implicit dependencies](#implicit_deps) are suppressed if
`--noimplicit_deps` is specified.

```
  <rule class='cc_binary rule' name='//foo:foo' ...>
    <list name='srcs'>
      <label value='//foo:foo_main.cc'/>
      <label value='//foo:bar.cc'/>
      ...
    </list>
    <list name='deps'>
      <label value='//common:common'/>
      <label value='//collections:collections'/>
      ...
    </list>
    <list name='data'>
      ...
    </list>
    <int name='linkstatic' value='0'/>
    <int name='linkshared' value='0'/>
    <list name='licenses'/>
    <list name='distribs'>
      <distribution value="INTERNAL" />
    </list>
    <rule-input name="//common:common" />
    <rule-input name="//collections:collections" />
    <rule-input name="//foo:foo_main.cc" />
    <rule-input name="//foo:bar.cc" />
    ...
  </rule>
```

Every XML element for a target contains a `name`
attribute, whose value is the target's label, and
a `location` attribute, whose value is the target's
location as printed by the [`--output location`](#print-target-location).

#### `--[no]xml:line_numbers` {:#xml-linenumbers}

By default, the locations displayed in the XML output contain line numbers.
When `--noxml:line_numbers` is specified, line numbers are not printed.

#### `--[no]xml:default_values` {:#xml-defaultvalues}

By default, XML output does not include rule attribute whose value
is the default value for that kind of attribute (for example, if it
were not specified in the `BUILD` file, or the default value was
provided explicitly). This option causes such attribute values to
be included in the XML output.

### Regular expressions {:#regular-expressions}

Regular expressions in the query language use the Java regex library, so you can use the
full syntax for
[`java.util.regex.Pattern`](https://docs.oracle.com/javase/8/docs/api/java/util/regex/Pattern.html){: .external}.

### Querying with external repositories {:#querying-external-repositories}

If the build depends on rules from [external repositories](/external/overview)
then query results will include these dependencies. For
example, if `//foo:bar` depends on `@other-repo//baz:lib`, then
`bazel query 'deps(//foo:bar)'` will list `@other-repo//baz:lib` as a
dependency.


Project: /_project.yaml
Book: /_book.yaml

#  Configurable Query (cquery)

{% include "_buttons.html" %}

`cquery` is a variant of [`query`](/query/language) that correctly handles
[`select()`](/docs/configurable-attributes) and build options' effects on the build
graph.

It achieves this by running over the results of Bazel's [analysis
phase](/extending/concepts#evaluation-model),
which integrates these effects. `query`, by contrast, runs over the results of
Bazel's loading phase, before options are evaluated.

For example:

<pre>
$ cat > tree/BUILD &lt;&lt;EOF
sh_library(
    name = "ash",
    deps = select({
        ":excelsior": [":manna-ash"],
        ":americana": [":white-ash"],
        "//conditions:default": [":common-ash"],
    }),
)
sh_library(name = "manna-ash")
sh_library(name = "white-ash")
sh_library(name = "common-ash")
config_setting(
    name = "excelsior",
    values = {"define": "species=excelsior"},
)
config_setting(
    name = "americana",
    values = {"define": "species=americana"},
)
EOF
</pre>

<pre>
# Traditional query: query doesn't know which select() branch you will choose,
# so it conservatively lists all of possible choices, including all used config_settings.
$ bazel query "deps(//tree:ash)" --noimplicit_deps
//tree:americana
//tree:ash
//tree:common-ash
//tree:excelsior
//tree:manna-ash
//tree:white-ash

# cquery: cquery lets you set build options at the command line and chooses
# the exact dependencies that implies (and also the config_setting targets).
$ bazel cquery "deps(//tree:ash)" --define species=excelsior --noimplicit_deps
//tree:ash (9f87702)
//tree:manna-ash (9f87702)
//tree:americana (9f87702)
//tree:excelsior (9f87702)
</pre>

Each result includes a [unique identifier](#configurations) `(9f87702)` of
the [configuration](/reference/glossary#configuration) the
target is built with.

Since `cquery` runs over the configured target graph. it doesn't have insight
into artifacts like build actions nor access to [`test_suite`](/reference/be/general#test_suite)
rules as they are not configured targets. For the former, see [`aquery`](/query/aquery).

## Basic syntax {:#basic-syntax}

A simple `cquery` call looks like:

`bazel cquery "function(//target)"`

The query expression `"function(//target)"` consists of the following:

*   **`function(...)`** is the function to run on the target. `cquery`
    supports most
    of `query`'s [functions](/query/language#functions), plus a
    few new ones.
*   **`//target`** is the expression fed to the function. In this example, the
    expression is a simple target. But the query language also allows nesting of functions.
    See the [Query guide](/query/guide) for examples.


`cquery` requires a target to run through the [loading and analysis](/extending/concepts#evaluation-model)
phases. Unless otherwise specified, `cquery` parses the target(s) listed in the
query expression. See [`--universe_scope`](#universe-scope)
for querying dependencies of top-level build targets.

## Configurations {:#configurations}

The line:

<pre>
//tree:ash (9f87702)
</pre>

means `//tree:ash` was built in a configuration with ID `9f87702`. For most
targets, this is an opaque hash of the build option values defining the
configuration.

To see the configuration's complete contents, run:

<pre>
$ bazel config 9f87702
</pre>

`9f87702` is a prefix of the complete ID. This is because complete IDs are
SHA-256 hashes, which are long and hard to follow. `cquery` understands any valid
prefix of a complete ID, similar to
[Git short hashes](https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection#_revision_selection){: .external}.
 To see complete IDs, run `$ bazel config`.

## Target pattern evaluation {:#target-pattern-evaluation}

`//foo` has a different meaning for `cquery` than for `query`. This is because
`cquery` evaluates _configured_ targets and the build graph may have multiple
configured versions of `//foo`.

For `cquery`, a target pattern in the query expression evaluates
to every configured target with a label that matches that pattern. Output is
deterministic, but `cquery` makes no ordering guarantee beyond the
[core query ordering contract](/query/language#graph-order).

This produces subtler results for query expressions than with `query`.
For example, the following can produce multiple results:

<pre>
# Analyzes //foo in the target configuration, but also analyzes
# //genrule_with_foo_as_tool which depends on an exec-configured
# //foo. So there are two configured target instances of //foo in
# the build graph.
$ bazel cquery //foo --universe_scope=//foo,//genrule_with_foo_as_tool
//foo (9f87702)
//foo (exec)
</pre>

If you want to precisely declare which instance to query over, use
the [`config`](#config) function.

See `query`'s [target pattern
documentation](/query/language#target-patterns) for more information on target patterns.

## Functions {:#functions}

Of the [set of functions](/query/language#functions "list of query functions")
supported by `query`, `cquery` supports all but
[`allrdeps`](/query/language#allrdeps),
[`buildfiles`](/query/language#buildfiles),
[`rbuildfiles`](/query/language#rbuildfiles),
[`siblings`](/query/language#siblings), [`tests`](/query/language#tests), and
[`visible`](/query/language#visible).

`cquery` also introduces the following new functions:

### config {:#config}

`expr ::= config(expr, word)`

The `config` operator attempts to find the configured target for
the label denoted by the first argument and configuration specified by the
second argument.

Valid values for the second argument are `null` or a
[custom configuration hash](#configurations). Hashes can be retrieved from `$
bazel config` or a previous `cquery`'s output.

Examples:

<pre>
$ bazel cquery "config(//bar, 3732cc8)" --universe_scope=//foo
</pre>

<pre>
$ bazel cquery "deps(//foo)"
//bar (exec)
//baz (exec)

$ bazel cquery "config(//baz, 3732cc8)"
</pre>

If not all results of the first argument can be found in the specified
configuration, only those that can be found are returned. If no results
can be found in the specified configuration, the query fails.

## Options {:#options}

### Build options {:#build-options}

`cquery` runs over a regular Bazel build and thus inherits the set of
[options](/reference/command-line-reference#build-options) available during a build.

###  Using cquery options {:#using-cquery-options}

#### `--universe_scope` (comma-separated list) {:#universe-scope}

Often, the dependencies of configured targets go through
[transitions](/extending/rules#configurations),
which causes their configuration to differ from their dependent. This flag
allows you to query a target as if it were built as a dependency or a transitive
dependency of another target. For example:

<pre>
# x/BUILD
genrule(
     name = "my_gen",
     srcs = ["x.in"],
     outs = ["x.cc"],
     cmd = "$(locations :tool) $&lt; >$@",
     tools = [":tool"],
)
cc_binary(
    name = "tool",
    srcs = ["tool.cpp"],
)
</pre>

Genrules configure their tools in the
[exec configuration](/extending/rules#configurations)
so the following queries would produce the following outputs:

<table class="table table-condensed table-bordered table-params">
  <thead>
    <tr>
      <th>Query</th>
      <th>Target Built</th>
      <th>Output</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>bazel cquery "//x:tool"</td>
      <td>//x:tool</td>
      <td>//x:tool(targetconfig)</td>
    </tr>
    <tr>
      <td>bazel cquery "//x:tool" --universe_scope="//x:my_gen"</td>
      <td>//x:my_gen</td>
      <td>//x:tool(execconfig)</td>
    </tr>
  </tbody>
</table>

If this flag is set, its contents are built. _If it's not set, all targets
mentioned in the query expression are built_ instead. The transitive closure of the
built targets are used as the universe of the query. Either way, the targets to
be built must be buildable at the top level (that is, compatible with top-level
options). `cquery` returns results in the transitive closure of these
top-level targets.

Even if it's possible to build all targets in a query expression at the top
level, it may be beneficial to not do so. For example, explicitly setting
`--universe_scope` could prevent building targets multiple times in
configurations you don't care about. It could also help specify which configuration version of a
target you're looking for (since it's not currently possible
to fully specify this any other way). You should set this flag
if your query expression is more complex than `deps(//foo)`.

#### `--implicit_deps` (boolean, default=True) {:#implicit-deps}

Setting this flag to false filters out all results that aren't explicitly set in
the BUILD file and instead set elsewhere by Bazel. This includes filtering resolved
toolchains.

#### `--tool_deps` (boolean, default=True) {:#tool-deps}

Setting this flag to false filters out all configured targets for which the
path from the queried target to them crosses a transition between the target
configuration and the
[non-target configurations](/extending/rules#configurations).
If the queried target is in the target configuration, setting `--notool_deps` will
only return targets that also are in the target configuration. If the queried
target is in a non-target configuration, setting `--notool_deps` will only return
targets also in non-target configurations. This setting generally does not affect filtering
of resolved toolchains.

#### `--include_aspects` (boolean, default=True) {:#include-aspects}

Include dependencies added by [aspects](/extending/aspects).

If this flag is disabled, `cquery somepath(X, Y)` and
`cquery deps(X) | grep 'Y'` omit Y if X only depends on it through an aspect.

## Output formats {:#output-formats}

By default, cquery outputs results in a dependency-ordered list of label and configuration pairs.
There are other options for exposing the results as well.

### Transitions {:#transitions}

<pre>
--transitions=lite
--transitions=full
</pre>

Configuration [transitions](/extending/rules#configurations)
are used to build targets underneath the top level targets in different
configurations than the top level targets.

For example, a target might impose a transition to the exec configuration on all
dependencies in its `tools` attribute. These are known as attribute
transitions. Rules can also impose transitions on their own configurations,
known as rule class transitions. This output format outputs information about
these transitions such as what type they are and the effect they have on build
options.

This output format is triggered by the `--transitions` flag which by default is
set to `NONE`. It can be set to `FULL` or `LITE` mode. `FULL` mode outputs
information about rule class transitions and attribute transitions including a
detailed diff of the options before and after the transition. `LITE` mode
outputs the same information without the options diff.

### Protocol message output {:#protocol-message-output}

<pre>
--output=proto
</pre>

This option causes the resulting targets to be printed in a binary protocol
buffer form. The definition of the protocol buffer can be found at
[src/main/protobuf/analysis_v2.proto](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/analysis_v2.proto){: .external}.

`CqueryResult` is the top level message containing the results of the cquery. It
has a list of `ConfiguredTarget` messages and a list of `Configuration`
messages. Each `ConfiguredTarget` has a `configuration_id` whose value is equal
to that of the `id` field from the corresponding `Configuration` message.

#### --[no]proto:include_configurations {:#proto-include-configurations}

By default, cquery results return configuration information as part of each
configured target. If you'd like to omit this information and get proto output
that is formatted exactly like query's proto output, set this flag to false.

See [query's proto output documentation](/query/language#output-formats)
for more proto output-related options.

Note: While selects are resolved both at the top level of returned
targets and within attributes, all possible inputs for selects are still
included as `rule_input` fields.

### Graph output {:#graph-output}

<pre>
--output=graph
</pre>

This option generates output as a Graphviz-compatible .dot file. See `query`'s
[graph output documentation](/query/language#display-result-graph) for details. `cquery`
also supports [`--graph:node_limit`](/query/language#graph-nodelimit) and
[`--graph:factored`](/query/language#graph-factored).

### Files output {:#files-output}

<pre>
--output=files
</pre>

This option prints a list of the output files produced by each target matched
by the query similar to the list printed at the end of a `bazel build`
invocation. The output contains only the files advertised in the requested
output groups as determined by the
[`--output_groups`](/reference/command-line-reference#flag--output_groups) flag.
It does include source files.

All paths emitted by this output format are relative to the
[execroot](https://bazel.build/remote/output-directories), which can be obtained
via `bazel info execution_root`. If the `bazel-out` convenience symlink exists,
paths to files in the main repository also resolve relative to the workspace
directory.

Note: The output of `bazel cquery --output=files //pkg:foo` contains the output
files of `//pkg:foo` in *all* configurations that occur in the build (also see
the [section on target pattern evaluation](#target-pattern-evaluation)). If that
is not desired, wrap you query in [`config(..., target)`](#config).

### Defining the output format using Starlark {:#output-format-definition}

<pre>
--output=starlark
</pre>

This output format calls a [Starlark](/rules/language)
function for each configured target in the query result, and prints the value
returned by the call. The `--starlark:file` flag specifies the location of a
Starlark file that defines a function named `format` with a single parameter,
`target`. This function is called for each [Target](/rules/lib/builtins/Target)
in the query result. Alternatively, for convenience, you may specify just the
body of a function declared as `def format(target): return expr` by using the
`--starlark:expr` flag.

#### 'cquery' Starlark dialect {:#cquery-starlark}

The cquery Starlark environment differs from a BUILD or .bzl file. It includes
all core Starlark
[built-in constants and functions](https://github.com/bazelbuild/starlark/blob/master/spec.md#built-in-constants-and-functions){: .external},
plus a few cquery-specific ones described below, but not (for example) `glob`,
`native`, or `rule`, and it does not support load statements.

##### build_options(target) {:#build-options}

`build_options(target)` returns a map whose keys are build option identifiers (see
[Configurations](/extending/config))
and whose values are their Starlark values. Build options whose values are not legal Starlark
values are omitted from this map.

If the target is an input file, `build_options(target)` returns None, as input file
targets have a null configuration.

##### providers(target) {:#providers}

`providers(target)` returns a map whose keys are names of
[providers](/extending/rules#providers)
(for example, `"DefaultInfo"`) and whose values are their Starlark values. Providers
whose values are not legal Starlark values are omitted from this map.

#### Examples {:#output-format-definition-examples}

Print a space-separated list of the base names of all files produced by `//foo`:

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="' '.join([f.basename for f in target.files.to_list()])"
</pre>

Print a space-separated list of the paths of all files produced by **rule** targets in
`//bar` and its subpackages:

<pre>
  bazel cquery 'kind(rule, //bar/...)' --output=starlark \
    --starlark:expr="' '.join([f.path for f in target.files.to_list()])"
</pre>

Print a list of the mnemonics of all actions registered by `//foo`.

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="[a.mnemonic for a in target.actions]"
</pre>

Print a list of compilation outputs registered by a `cc_library` `//baz`.

<pre>
  bazel cquery //baz --output=starlark \
    --starlark:expr="[f.path for f in target.output_groups.compilation_outputs.to_list()]"
</pre>

Print the value of the command line option `--javacopt` when building `//foo`.

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="build_options(target)['//command_line_option:javacopt']"
</pre>

Print the label of each target with exactly one output. This example uses
Starlark functions defined in a file.

<pre>
  $ cat example.cquery

  def has_one_output(target):
    return len(target.files.to_list()) == 1

  def format(target):
    if has_one_output(target):
      return target.label
    else:
      return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

Print the label of each target which is strictly Python 3. This example uses
Starlark functions defined in a file.

<pre>
  $ cat example.cquery

  def format(target):
    p = providers(target)
    py_info = p.get("PyInfo")
    if py_info and py_info.has_py3_only_sources:
      return target.label
    else:
      return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

Extract a value from a user defined Provider.

<pre>
  $ cat some_package/my_rule.bzl

  MyRuleInfo = provider(fields={"color": "the name of a color"})

  def _my_rule_impl(ctx):
      ...
      return [MyRuleInfo(color="red")]

  my_rule = rule(
      implementation = _my_rule_impl,
      attrs = {...},
  )

  $ cat example.cquery

  def format(target):
    p = providers(target)
    my_rule_info = p.get("//some_package:my_rule.bzl%MyRuleInfo'")
    if my_rule_info:
      return my_rule_info.color
    return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

## cquery vs. query {:#cquery-vs-query}

`cquery` and `query` complement each other and excel in
different niches. Consider the following to decide which is right for you:

*  `cquery` follows specific `select()` branches to
    model the exact graph you build. `query` doesn't know which
    branch the build chooses, so overapproximates by including all branches.
*   `cquery`'s precision requires building more of the graph than
    `query` does. Specifically, `cquery`
    evaluates _configured targets_ while `query` only
    evaluates _targets_. This takes more time and uses more memory.
*   `cquery`'s interpretation of
    the [query language](/query/language) introduces ambiguity
    that `query` avoids. For example,
    if `"//foo"` exists in two configurations, which one
    should `cquery "deps(//foo)"` use?
    The [`config`](#config) function can help with this.
*   As a newer tool, `cquery` lacks support for certain use
    cases. See [Known issues](#known-issues) for details.

## Known issues {:#known-issues}

**All targets that `cquery` "builds" must have the same configuration.**

Before evaluating queries, `cquery` triggers a build up to just
before the point where build actions would execute. The targets it
"builds" are by default selected from all labels that appear in the query
expression (this can be overridden
with [`--universe_scope`](#universe-scope)). These
must have the same configuration.

While these generally share the top-level "target" configuration,
rules can change their own configuration with
[incoming edge transitions](/extending/config#incoming-edge-transitions).
This is where `cquery` falls short.

Workaround: If possible, set `--universe_scope` to a stricter
scope. For example:

<pre>
# This command attempts to build the transitive closures of both //foo and
# //bar. //bar uses an incoming edge transition to change its --cpu flag.
$ bazel cquery 'somepath(//foo, //bar)'
ERROR: Error doing post analysis query: Top-level targets //foo and //bar
have different configurations (top-level targets with different
configurations is not supported)

# This command only builds the transitive closure of //foo, under which
# //bar should exist in the correct configuration.
$ bazel cquery 'somepath(//foo, //bar)' --universe_scope=//foo
</pre>

**No support for [`--output=xml`](/query/language#xml).**

**Non-deterministic output.**

`cquery` does not automatically wipe the build graph from
previous commands and is therefore prone to picking up results from past
queries. For example, `genrule` exerts an exec transition on
its `tools` attribute - that is, it configures its tools in the
[exec configuration](/extending/rules#configurations).

You can see the lingering effects of that transition below.

<pre>
$ cat > foo/BUILD &lt;&lt;&lt;EOF
genrule(
    name = "my_gen",
    srcs = ["x.in"],
    outs = ["x.cc"],
    cmd = "$(locations :tool) $&lt; >$@",
    tools = [":tool"],
)
cc_library(
    name = "tool",
)
EOF

    $ bazel cquery "//foo:tool"
tool(target_config)

    $ bazel cquery "deps(//foo:my_gen)"
my_gen (target_config)
tool (exec_config)
...

    $ bazel cquery "//foo:tool"
tool(exec_config)
</pre>

Workaround: change any startup option to force re-analysis of configured targets.
For example, add `--test_arg=<whatever>` to your build command.

## Troubleshooting {:#troubleshooting}

### Recursive target patterns (`/...`) {:#recursive-target-patterns}

If you encounter:

<pre>
$ bazel cquery --universe_scope=//foo:app "somepath(//foo:app, //foo/...)"
ERROR: Error doing post analysis query: Evaluation failed: Unable to load package '[foo]'
because package is not in scope. Check that all target patterns in query expression are within the
--universe_scope of this query.
</pre>

this incorrectly suggests package `//foo` isn't in scope even though
`--universe_scope=//foo:app` includes it. This is due to design limitations in
`cquery`. As a workaround, explicitly include `//foo/...` in the universe
scope:

<pre>
$ bazel cquery --universe_scope=//foo:app,//foo/... "somepath(//foo:app, //foo/...)"
</pre>

If that doesn't work (for example, because some target in `//foo/...` can't
build with the chosen build flags), manually unwrap the pattern into its
constituent packages with a pre-processing query:

<pre>
# Replace "//foo/..." with a subshell query call (not cquery!) outputting each package, piped into
# a sed call converting "&lt;pkg&gt;" to "//&lt;pkg&gt;:*", piped into a "+"-delimited line merge.
# Output looks like "//foo:*+//foo/bar:*+//foo/baz".
#
$  bazel cquery --universe_scope=//foo:app "somepath(//foo:app, $(bazel query //foo/...
--output=package | sed -e 's/^/\/\//' -e 's/$/:*/' | paste -sd "+" -))"
</pre>


Project: /_project.yaml
Book: /_book.yaml

# Query quickstart

{% include "_buttons.html" %}

This tutorial covers how to work with Bazel to trace dependencies in your code using a premade Bazel project.

For language and `--output` flag details, see the [Bazel query reference](/query/language) and [Bazel cquery reference](/query/cquery) manuals. Get help in your IDE by typing `bazel help query` or `bazel help cquery` on the command line.

## Objective

This guide runs you through a set of basic queries you can use to learn more about your project's file dependencies. It is intended for new Bazel developers with a basic knowledge of how Bazel and `BUILD` files work.


## Prerequisites

Start by installing [Bazel](https://bazel.build/install), if you haven’t already. This tutorial uses Git for source control, so for best results, install [Git](https://github.com/git-guides/install-git) as well.

To visualize dependency graphs, the tool called Graphviz is used, which you can [download](https://graphviz.org/download/) in order to follow along.

### Get the sample project

Next, retrieve the sample app from [Bazel's Examples repository](https://github.com/bazelbuild/examples) by running the following in your command-line tool of choice:

```posix-terminal
git clone https://github.com/bazelbuild/examples.git
```

The sample project for this tutorial is in the `examples/query-quickstart` directory.

## Getting started

### What are Bazel queries?

Queries help you to learn about a Bazel codebase by analyzing the relationships between `BUILD` files and examining the resulting output for useful information. This guide previews some basic query functions, but for more options see the [query guide](https://bazel.build/query/guide). Queries help you learn about dependencies in large scale projects without manually navigating through `BUILD` files.

To run a query, open your command line terminal and enter:

```posix-terminal
bazel query 'query_function'
```

### Scenario

Imagine a scenario that delves into the relationship between Cafe Bazel and its respective chef. This Cafe exclusively sells pizza and mac & cheese. Take a look below at how the project is structured:

```
bazelqueryguide
├── BUILD
├── src
│   └── main
│       └── java
│           └── com
│               └── example
│                   ├── customers
│                   │   ├── Jenny.java
│                   │   ├── Amir.java
│                   │   └── BUILD
│                   ├── dishes
│                   │   ├── Pizza.java
│                   │   ├── MacAndCheese.java
│                   │   └── BUILD
│                   ├── ingredients
│                   │   ├── Cheese.java
│                   │   ├── Tomatoes.java
│                   │   ├── Dough.java
│                   │   ├── Macaroni.java
│                   │   └── BUILD
│                   ├── restaurant
│                   │   ├── Cafe.java
│                   │   ├── Chef.java
│                   │   └── BUILD
│                   ├── reviews
│                   │   ├── Review.java
│                   │   └── BUILD
│                   └── Runner.java
└── MODULE.bazel
```

Throughout this tutorial, unless directed otherwise, try not to look in the `BUILD` files to find the information you need and instead solely use the query function.

A project consists of different packages that make up a Cafe. They are separated into: `restaurant`, `ingredients`, `dishes`, `customers`, and `reviews`. Rules within these packages define different components of the Cafe with various tags and dependencies.

### Running a build

This project contains a main method inside of `Runner.java` that you can execute
to print out a menu of the Cafe. Build the project using Bazel with the command
`bazel build` and use `:` to signal that the target is named `runner`. See
[target names](https://bazel.build/concepts/labels#target-names) to learn how to
reference targets.

To build this project, paste this command into a terminal:

```posix-terminal
bazel build :runner
```

Your output should look something like this if the build is successful.

```bash
INFO: Analyzed target //:runner (49 packages loaded, 784 targets configured).
INFO: Found 1 target...
Target //:runner up-to-date:
  bazel-bin/runner.jar
  bazel-bin/runner
INFO: Elapsed time: 16.593s, Critical Path: 4.32s
INFO: 23 processes: 4 internal, 10 darwin-sandbox, 9 worker.
INFO: Build completed successfully, 23 total actions
```

After it has built successfully, run the application by pasting this command:

```posix-terminal
bazel-bin/runner
```

```bash
--------------------- MENU -------------------------

Pizza - Cheesy Delicious Goodness
Macaroni & Cheese - Kid-approved Dinner

----------------------------------------------------
```
This leaves you with a list of the menu items given along with a short description.

## Exploring targets

The project lists ingredients and dishes in their own packages. To use a query to view the rules of a package, run the command <code>bazel query <em>package</em>/…</code>

In this case, you can use this to look through the ingredients and dishes that this Cafe has by running:

```posix-terminal
bazel query //src/main/java/com/example/dishes/...
```

```posix-terminal
bazel query //src/main/java/com/example/ingredients/...
```

If you query for the targets of the ingredients package, the output should look like:

```bash
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/ingredients:dough
//src/main/java/com/example/ingredients:macaroni
//src/main/java/com/example/ingredients:tomato
```

## Finding dependencies

What targets does your runner rely on to run?

Say you want to dive deeper into the structure of your project without prodding into the filesystem (which may be untenable for large projects). What rules does Cafe Bazel use?

If, like in this example, the target for your runner is `runner`, discover the underlying dependencies of the target by running the command:

```posix-terminal
bazel query --noimplicit_deps "deps(target)"
```

```posix-terminal
bazel query --noimplicit_deps "deps(:runner)"
```

```bash
//:runner
//:src/main/java/com/example/Runner.java
//src/main/java/com/example/dishes:MacAndCheese.java
//src/main/java/com/example/dishes:Pizza.java
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:Cheese.java
//src/main/java/com/example/ingredients:Dough.java
//src/main/java/com/example/ingredients:Macaroni.java
//src/main/java/com/example/ingredients:Tomato.java
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/ingredients:dough
//src/main/java/com/example/ingredients:macaroni
//src/main/java/com/example/ingredients:tomato
//src/main/java/com/example/restaurant:Cafe.java
//src/main/java/com/example/restaurant:Chef.java
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```
Note: Adding the flag `--noimplicit_deps` removes configurations and potential toolchains to simplify the list. When you omit this flag, Bazel returns implicit dependencies not specified in the `BUILD` file and clutters the output.

In most cases, use the query function `deps()` to see individual output dependencies of a specific target.

## Visualizing the dependency graph (optional)

Note: This section uses Graphviz, so make sure to [download Graphviz](https://graphviz.org/download/) to follow along.

The section describes how you can visualize the dependency paths for a specific query. [Graphviz](https://graphviz.org/) helps to see the path as a directed acyclic graph image as opposed to a flattened list. You can alter the display of the Bazel query graph by using various `--output` command line options. See [Output Formats](https://bazel.build/query/language#output-formats) for options.

Start by running your desired query and add the flag `--noimplicit_deps` to remove excessive tool dependencies. Then, follow the query with the output flag and store the graph into a file called `graph.in` to create a text representation of the graph.

To search for all dependencies of the target `:runner` and format the output as a graph:

```posix-terminal
bazel query --noimplicit_deps 'deps(:runner)' --output graph > graph.in
```
This creates a file called `graph.in`, which is a text representation of the build graph. Graphviz uses <code>[dot](https://graphviz.org/docs/layouts/dot/) </code>– a tool that processes text into a visualization —  to create a png:

```posix-terminal
dot -Tpng < graph.in > graph.png
```
If you open up `graph.png`, you should see something like this. The graph below has been simplified to make the essential path details clearer in this guide.

![Diagram showing a relationship from cafe to chef to the dishes: pizza and mac and cheese which diverges into the separate ingredients: cheese, tomatoes, dough, and macaroni.](images/query_graph1.png "Dependency graph")

This helps when you want to see the outputs of the different query functions throughout this guide.

## Finding reverse dependencies

If instead you have a target you’d like to analyze what other targets use it, you can use a query to examine what targets depend on a certain rule. This is called a “reverse dependency”. Using `rdeps()` can be useful when editing a file in a codebase that you’re unfamiliar with, and can save you from unknowingly breaking other files which depended on it.

For instance, you want to make some edits to the ingredient `cheese`. To avoid causing an issue for Cafe Bazel, you need to check what dishes rely on `cheese`.

Caution: Since `ingredients` is its own package, you must use a different naming convention for the target `cheese` in the form of `//package:target`. Read more about referencing targets, or [Labels](https://bazel.build/concepts/labels).

To see what targets depend on a particular target/package, you can use `rdeps(universe_scope, target)`. The `rdeps()` query function takes in at least two arguments: a `universe_scope` — the relevant directory — and a `target`. Bazel searches for the target’s reverse dependencies within the `universe_scope` provided. The `rdeps()` operator accepts an optional third argument: an integer literal specifying the upper bound on the depth of the search.

Tip: To search within the whole scope of the project, set the `universe_scope` to `//...`

To look for reverse dependencies of the target `cheese` within the scope of the entire project ‘//…’ run the command:

```posix-terminal
bazel query "rdeps(universe_scope, target)"
```
```
ex) bazel query "rdeps(//... , //src/main/java/com/example/ingredients:cheese)"
```
```bash
//:runner
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```
The query return shows that cheese is relied on by both pizza and macAndCheese. What a surprise!

## Finding targets based on tags

Two customers walk into Bazel Cafe: Amir and Jenny. There is nothing known about them except for their names. Luckily, they have their orders tagged in the 'customers' `BUILD` file. How can you access this tag?

Developers can tag Bazel targets with different identifiers, often for testing purposes. For instance, tags on tests can annotate a test's role in your debug and release process, especially for C++ and Python tests, which lack any runtime annotation ability. Using tags and size elements gives flexibility in assembling suites of tests based around a codebase’s check-in policy.

In this example, the tags are either one of `pizza` or `macAndCheese` to represent the menu items. This command queries for targets that have tags matching your identifier within a certain package.

```
bazel query 'attr(tags, "pizza", //src/main/java/com/example/customers/...)'
```
This query returns all of the targets in the 'customers' package that have a tag of "pizza".

### Test yourself

Use this query to learn what Jenny wants to order.

<div>
  <devsite-expandable>
  <h4 class="showalways">Answer</h4>
  <p>Mac and Cheese</p>
  </devsite-expandable>
</div>


## Adding a new dependency

Cafe Bazel has expanded its menu — customers can now order a Smoothie! This specific smoothie consists of the ingredients `Strawberry` and `Banana`.

First, add the ingredients that the smoothie depends on: `Strawberry.java` and `Banana.java`. Add the empty Java classes.

**`src/main/java/com/example/ingredients/Strawberry.java`**

```java
package com.example.ingredients;

public class Strawberry {

}
```

**`src/main/java/com/example/ingredients/Banana.java`**

```java
package com.example.ingredients;

public class Banana {

}
```

Next, add `Smoothie.java` to the appropriate directory: `dishes`.

**`src/main/java/com/example/dishes/Smoothie.java`**

```java
package com.example.dishes;

public class Smoothie {
    public static final String DISH_NAME = "Smoothie";
    public static final String DESCRIPTION = "Yummy and Refreshing";
}
```


Lastly, add these files as rules in the appropriate `BUILD` files. Create a new java library for each new ingredient, including its name, public visibility, and its newly created 'src' file. You should wind up with this updated `BUILD` file:

**`src/main/java/com/example/ingredients/BUILD`**

```
java_library(
    name = "cheese",
    visibility = ["//visibility:public"],
    srcs = ["Cheese.java"],
)

java_library(
    name = "dough",
    visibility = ["//visibility:public"],
    srcs = ["Dough.java"],
)

java_library(
    name = "macaroni",
    visibility = ["//visibility:public"],
    srcs = ["Macaroni.java"],
)

java_library(
    name = "tomato",
    visibility = ["//visibility:public"],
    srcs = ["Tomato.java"],
)

java_library(
    name = "strawberry",
    visibility = ["//visibility:public"],
    srcs = ["Strawberry.java"],
)

java_library(
    name = "banana",
    visibility = ["//visibility:public"],
    srcs = ["Banana.java"],
)
```

In the `BUILD` file for dishes, you want to add a new rule for `Smoothie`. Doing so includes the Java file created for `Smoothie` as a 'src' file, and the new rules you made for each ingredient of the smoothie.

**`src/main/java/com/example/dishes/BUILD`**

```
java_library(
    name = "macAndCheese",
    visibility = ["//visibility:public"],
    srcs = ["MacAndCheese.java"],
    deps = [
        "//src/main/java/com/example/ingredients:cheese",
        "//src/main/java/com/example/ingredients:macaroni",
    ],
)

java_library(
    name = "pizza",
    visibility = ["//visibility:public"],
    srcs = ["Pizza.java"],
    deps = [
        "//src/main/java/com/example/ingredients:cheese",
        "//src/main/java/com/example/ingredients:dough",
        "//src/main/java/com/example/ingredients:tomato",
    ],
)

java_library(
    name = "smoothie",
    visibility = ["//visibility:public"],
    srcs = ["Smoothie.java"],
    deps = [
        "//src/main/java/com/example/ingredients:strawberry",
        "//src/main/java/com/example/ingredients:banana",
    ],
)
```

Lastly, you want to include the smoothie as a dependency in the Chef’s `BUILD` file.

**`src/main/java/com/example/restaurant/BUILD`**

```
java\_library(
    name = "chef",
    visibility = ["//visibility:public"],
    srcs = [
        "Chef.java",
    ],

    deps = [
        "//src/main/java/com/example/dishes:macAndCheese",
        "//src/main/java/com/example/dishes:pizza",
        "//src/main/java/com/example/dishes:smoothie",
    ],
)

java\_library(
    name = "cafe",
    visibility = ["//visibility:public"],
    srcs = [
        "Cafe.java",
    ],
    deps = [
        ":chef",
    ],
)
```

Build `cafe` again to confirm that there are no errors. If it builds successfully, congratulations! You’ve added a new dependency for the 'Cafe'. If not, look out for spelling mistakes and package naming. For more information about writing `BUILD` files see [BUILD Style Guide](https://bazel.build/build/style-guide).

Now, visualize the new dependency graph with the addition of the `Smoothie` to compare with the previous one. For clarity, name the graph input as `graph2.in` and `graph2.png`.


```posix-terminal
bazel query --noimplicit_deps 'deps(:runner)' --output graph > graph2.in
```

```posix-terminal
dot -Tpng < graph2.in > graph2.png
```

[![The same graph as the first one except now there is a spoke stemming from the chef target with smoothie which leads to banana and strawberry](images/query_graph2.png "Updated dependency graph")](images/query_graph2.png)

Looking at `graph2.png`, you can see that `Smoothie` has no shared dependencies with other dishes but is just another target that the `Chef` relies on.

## somepath() and allpaths()

What if you want to query why one package depends on another package? Displaying a dependency path between the two provides the answer.

Two functions can help you find dependency paths: `somepath()` and `allpaths()`. Given a starting target S and an end point E, find a path between S and E by using `somepath(S,E)`.

Explore the differences between these two functions by looking at the relationships between the 'Chef' and 'Cheese' targets. There are different possible paths to get from one target to the other:

*   Chef → MacAndCheese → Cheese
*   Chef → Pizza → Cheese

`somepath()` gives you a single path out of the two options, whereas 'allpaths()' outputs every possible path.

Using Cafe Bazel as an example, run the following:

```posix-terminal
bazel query "somepath(//src/main/java/com/example/restaurant/..., //src/main/java/com/example/ingredients:cheese)"
```

```bash
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/ingredients:cheese
```

The output follows the first path of Cafe → Chef → MacAndCheese → Cheese. If instead you use `allpaths()`, you get:

```posix-terminal
bazel query "allpaths(//src/main/java/com/example/restaurant/..., //src/main/java/com/example/ingredients:cheese)"
```

```bash
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```

![Output path of cafe to chef to pizza,mac and cheese to cheese](images/query_graph3.png "Output path for dependency")

The output of `allpaths()` is a little harder to read as it is a flattened list of the dependencies. Visualizing this graph using Graphviz makes the relationship clearer to understand.

## Test yourself

One of Cafe Bazel’s customers gave the restaurant's first review! Unfortunately, the review is missing some details such as the identity of the reviewer and what dish it’s referencing. Luckily, you can access this information with Bazel. The `reviews` package contains a program that prints a review from a mystery customer. Build and run it with:

```posix-terminal
bazel build //src/main/java/com/example/reviews:review
```

```posix-terminal
bazel-bin/src/main/java/com/example/reviews/review
```

Going off Bazel queries only, try to find out who wrote the review, and what dish they were describing.

<div>
  <devsite-expandable>
  <h4 class="showalways">Hint</h4>
  <p>Check the tags and dependencies for useful information.</p>
  </devsite-expandable>
</div>

<div>
  <devsite-expandable>
  <h4 class="showalways">Answer</h4>
  <p>This review was describing the Pizza and Amir was the reviewer. If you look at what dependencies that this rule had using
  <code>bazel query --noimplicit\_deps 'deps(//src/main/java/com/example/reviews:review)'</code>
  The result of this command reveals that Amir is the reviewer!
  Next, since you know the reviewer is Amir, you can use the query function to seek which tag Amir has in the `BUILD` file to see what dish is there.
  The command <code>bazel query 'attr(tags, "pizza", //src/main/java/com/example/customers/...)'</code> output that Amir is the only customer that ordered a pizza and is the reviewer which gives us the answer.
  </p>
  </devsite-expandable>
</div>

## Wrapping up

Congratulations! You have now run several basic queries, which you can try out on own projects. To learn more about the query language syntax, refer to the [Query reference page](https://bazel.build/query/language). Want more advanced queries? The [Query guide](https://bazel.build/query/guide) showcases an in-depth list of more use cases than are covered in this guide.


Project: /_project.yaml
Book: /_book.yaml

# Action Graph Query (aquery)

{% include "_buttons.html" %}

The `aquery` command allows you to query for actions in your build graph.
It operates on the post-analysis Configured Target Graph and exposes
information about **Actions, Artifacts and their relationships.**

`aquery` is useful when you are interested in the properties of the Actions/Artifacts
generated from the Configured Target Graph. For example, the actual commands run
and their inputs/outputs/mnemonics.

The tool accepts several command-line [options](#command-options).
Notably, the aquery command runs on top of a regular Bazel build and inherits
the set of options available during a build.

It supports the same set of functions that is also available to traditional
`query` but `siblings`, `buildfiles` and
`tests`.

An example `aquery` output (without specific details):

<pre>
$ bazel aquery 'deps(//some:label)'
action 'Writing file some_file_name'
  Mnemonic: ...
  Target: ...
  Configuration: ...
  ActionKey: ...
  Inputs: [...]
  Outputs: [...]
</pre>

## Basic syntax {:#basic-syntax}

A simple example of the syntax for `aquery` is as follows:

`bazel aquery "aquery_function(function(//target))"`

The query expression (in quotes) consists of the following:

*   `aquery_function(...)`: functions specific to `aquery`.
    More details [below](#using-aquery-functions).
*   `function(...)`: the standard [functions](/query/language#functions)
    as traditional `query`.
*   `//target` is the label to the interested target.

<pre>
# aquery examples:
# Get the action graph generated while building //src/target_a
$ bazel aquery '//src/target_a'

# Get the action graph generated while building all dependencies of //src/target_a
$ bazel aquery 'deps(//src/target_a)'

# Get the action graph generated while building all dependencies of //src/target_a
# whose inputs filenames match the regex ".*cpp".
$ bazel aquery 'inputs(".*cpp", deps(//src/target_a))'
</pre>

## Using aquery functions {:#using-aquery-functions}

There are three `aquery` functions:

*   `inputs`: filter actions by inputs.
*   `outputs`: filter actions by outputs
*   `mnemonic`: filter actions by mnemonic

`expr ::= inputs(word, expr)`

  The `inputs` operator returns the actions generated from building `expr`,
  whose input filenames match the regex provided by `word`.

`$ bazel aquery 'inputs(".*cpp", deps(//src/target_a))'`

`outputs` and `mnemonic` functions share a similar syntax.

You can also combine functions to achieve the AND operation. For example:

<pre>
  $ bazel aquery 'mnemonic("Cpp.*", (inputs(".*cpp", inputs("foo.*", //src/target_a))))'
</pre>

  The above command would find all actions involved in building `//src/target_a`,
  whose mnemonics match `"Cpp.*"` and inputs match the patterns
  `".*cpp"` and `"foo.*"`.

Important: aquery functions can't be nested inside non-aquery functions.
Conceptually, this makes sense since the output of aquery functions is Actions,
not Configured Targets.

An example of the syntax error produced:

<pre>
        $ bazel aquery 'deps(inputs(".*cpp", //src/target_a))'
        ERROR: aquery filter functions (inputs, outputs, mnemonic) produce actions,
        and therefore can't be the input of other function types: deps
        deps(inputs(".*cpp", //src/target_a))
</pre>

## Options {:#options}

### Build options {:#build-options}

`aquery` runs on top of a regular Bazel build and thus inherits the set of
[options](/reference/command-line-reference#build-options)
available during a build.

### Aquery options {:#aquery-options}

#### `--output=(text|summary|commands|proto|jsonproto|textproto), default=text` {:#output}

The default output format (`text`) is human-readable,
use `proto`, `textproto`, or `jsonproto` for machine-readable format.
The proto message is `analysis.ActionGraphContainer`.

The `commands` output format prints a list of build commands with
one command per line.

In general, do not depend on the order of output. For more information,
see the [core query ordering contract](/query/language#graph-order).

#### `--include_commandline, default=true` {:#include-commandline}

Includes the content of the action command lines in the output (potentially large).

#### `--include_artifacts, default=true` {:#include-artifacts}

Includes names of the action inputs and outputs in the output (potentially large).

#### `--include_aspects, default=true` {:#include-aspects}

Whether to include Aspect-generated actions in the output.

#### `--include_param_files, default=false` {:#include-param-files}

Include the content of the param files used in the command (potentially large).

Warning: Enabling this flag will automatically enable the `--include_commandline` flag.

#### `--include_file_write_contents, default=false` {:#include-file-write-contents}

Include file contents for the `actions.write()` action and the contents of the
manifest file for the `SourceSymlinkManifest` action The file contents is
returned in the `file_contents` field with `--output=`xxx`proto`.
With `--output=text`, the output has
```
FileWriteContents: [<base64-encoded file contents>]
```
line

#### `--skyframe_state, default=false` {:#skyframe-state}

Without performing extra analysis, dump the Action Graph from Skyframe.

Note: Specifying a target with `--skyframe_state` is currently not supported.
This flag is only available with `--output=proto` or `--output=textproto`.

## Other tools and features {:#other-tools-features}

### Querying against the state of Skyframe {:#querying-against-skyframe}

[Skyframe](/reference/skyframe) is the evaluation and
incrementality model of Bazel. On each instance of Bazel server, Skyframe stores the dependency graph
constructed from the previous runs of the [Analysis phase](/run/build#analysis).

In some cases, it is useful to query the Action Graph on Skyframe.
An example use case would be:

1.  Run `bazel build //target_a`
2.  Run `bazel build //target_b`
3.  File `foo.out` was generated.

_As a Bazel user, I want to determine if `foo.out` was generated from building
`//target_a` or `//target_b`_.

One could run `bazel aquery 'outputs("foo.out", //target_a)'` and
`bazel aquery 'outputs("foo.out", //target_b)'` to figure out the action responsible
for creating `foo.out`, and in turn the target. However, the number of different
targets previously built can be larger than 2, which makes running multiple `aquery`
commands a hassle.

As an alternative, the `--skyframe_state` flag can be used:

<pre>
  # List all actions on Skyframe's action graph
  $ bazel aquery --output=proto --skyframe_state

  # or

  # List all actions on Skyframe's action graph, whose output matches "foo.out"
  $ bazel aquery --output=proto --skyframe_state 'outputs("foo.out")'
</pre>

With `--skyframe_state` mode, `aquery` takes the content of the Action Graph
that Skyframe keeps on the instance of Bazel, (optionally) performs filtering on it and
outputs the content, without re-running the analysis phase.

#### Special considerations {:#special-considerations}

##### Output format {:#output-format}

`--skyframe_state` is currently only available for `--output=proto`
and `--output=textproto`

##### Non-inclusion of target labels in the query expression {:#target-labels-non-inclusion}

Currently, `--skyframe_state` queries the whole action graph that exists on Skyframe,
regardless of the targets. Having the target label specified in the query together with
`--skyframe_state` is considered a syntax error:

<pre>
  # WRONG: Target Included
  $ bazel aquery --output=proto --skyframe_state **//target_a**
  ERROR: Error while parsing '//target_a)': Specifying build target(s) [//target_a] with --skyframe_state is currently not supported.

  # WRONG: Target Included
  $ bazel aquery --output=proto --skyframe_state 'inputs(".*.java", **//target_a**)'
  ERROR: Error while parsing '//target_a)': Specifying build target(s) [//target_a] with --skyframe_state is currently not supported.

  # CORRECT: Without Target
  $ bazel aquery --output=proto --skyframe_state
  $ bazel aquery --output=proto --skyframe_state 'inputs(".*.java")'
</pre>

### Comparing aquery outputs {:#comparing-aquery-outputs}

You can compare the outputs of two different aquery invocations using the `aquery_differ` tool.
For instance: when you make some changes to your rule definition and want to verify that the
command lines being run did not change. `aquery_differ` is the tool for that.

The tool is available in the [bazelbuild/bazel](https://github.com/bazelbuild/bazel/tree/master/tools/aquery_differ){: .external} repository.
To use it, clone the repository to your local machine. An example usage:

<pre>
  $ bazel run //tools/aquery_differ -- \
  --before=/path/to/before.proto \
  --after=/path/to/after.proto \
  --input_type=proto \
  --attrs=cmdline \
  --attrs=inputs
</pre>

The above command returns the difference between the `before` and `after` aquery outputs:
which actions were present in one but not the other, which actions have different
command line/inputs in each aquery output, ...). The result of running the above command would be:

<pre>
  Aquery output 'after' change contains an action that generates the following outputs that aquery output 'before' change doesn't:
  ...
  /list of output files/
  ...

  [cmdline]
  Difference in the action that generates the following output(s):
    /path/to/abc.out
  --- /path/to/before.proto
  +++ /path/to/after.proto
  @@ -1,3 +1,3 @@
    ...
    /cmdline diff, in unified diff format/
    ...
</pre>

#### Command options {:#command-options}

`--before, --after`: The aquery output files to be compared

`--input_type=(proto|text_proto), default=proto`: the format of the input
files. Support is provided for `proto` and `textproto` aquery output.

`--attrs=(cmdline|inputs), default=cmdline`: the attributes of actions
to be compared.

### Aspect-on-aspect {:#aspect-on-aspect}

It is possible for [Aspects](/extending/aspects)
to be applied on top of each other. The aquery output of the action generated by
these Aspects would then include the _Aspect path_, which is the sequence of
Aspects applied to the target which generated the action.

An example of Aspect-on-Aspect:

<pre>
  t0
  ^
  | <- a1
  t1
  ^
  | <- a2
  t2
</pre>

Let t<sub>i</sub> be a target of rule r<sub>i</sub>, which applies an Aspect a<sub>i</sub>
to its dependencies.

Assume that a2 generates an action X when applied to target t0. The text output of
`bazel aquery --include_aspects 'deps(//t2)'` for action X would be:

<pre>
  action ...
  Mnemonic: ...
  Target: //my_pkg:t0
  Configuration: ...
  AspectDescriptors: [//my_pkg:rule.bzl%**a2**(foo=...)
    -> //my_pkg:rule.bzl%**a1**(bar=...)]
  ...
</pre>

This means that action `X` was generated by Aspect `a2` applied onto
`a1(t0)`, where `a1(t0)` is the result of Aspect `a1` applied
onto target `t0`.

Each `AspectDescriptor` has the following format:

<pre>
  AspectClass([param=value,...])
</pre>

`AspectClass` could be the name of the Aspect class (for native Aspects) or
`bzl_file%aspect_name` (for Starlark Aspects). `AspectDescriptor` are
sorted in topological order of the
[dependency graph](/extending/aspects#aspect_basics).

### Linking with the JSON profile {:#linking-with-json-profile}

While aquery provides information about the actions being run in a build (why they're being run,
their inputs/outputs), the [JSON profile](/rules/performance#performance-profiling)
tells us the timing and duration of their execution.
It is possible to combine these 2 sets of information via a common denominator: an action's primary output.

To include actions' outputs in the JSON profile, generate the profile with
`--experimental_include_primary_output --noslim_profile`.
Slim profiles are incompatible with the inclusion of primary outputs. An action's primary output
is included by default by aquery.

We don't currently provide a canonical tool to combine these 2 data sources, but you should be
able to build your own script with the above information.

## Known issues {:#known-issues}

### Handling shared actions {:#handling-shared-actions}

Sometimes actions are
[shared](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/Actions.java;l=59;drc=146d51aa1ec9dcb721a7483479ef0b1ac21d39f1){: .external}
between configured targets.

In the execution phase, those shared actions are
[simply considered as one](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/Actions.java;l=241;drc=003b8734036a07b496012730964ac220f486b61f){: .external} and only executed once.
However, aquery operates on the pre-execution, post-analysis action graph, and hence treats these
like separate actions whose output Artifacts have the exact same `execPath`. As a result,
equivalent Artifacts appear duplicated.

The list of aquery issues/planned features can be found on
[GitHub](https://github.com/bazelbuild/bazel/labels/team-Performance){: .external}.

## FAQs {:#faqs}

### The ActionKey remains the same even though the content of an input file changed. {:#actionkey-same}

In the context of aquery, the `ActionKey` refers to the `String` gotten from
[ActionAnalysisMetadata#getKey](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/ActionAnalysisMetadata.java;l=89;drc=8b856f5484f0117b2aebc302f849c2a15f273310){: .external}:

<pre>
  Returns a string encoding all of the significant behaviour of this Action that might affect the
  output. The general contract of `getKey` is this: if the work to be performed by the
  execution of this action changes, the key must change.

  ...

  Examples of changes that should affect the key are:

  - Changes to the BUILD file that materially affect the rule which gave rise to this Action.
  - Changes to the command-line options, environment, or other global configuration resources
      which affect the behaviour of this kind of Action (other than changes to the names of the
      input/output files, which are handled externally).
  - An upgrade to the build tools which changes the program logic of this kind of Action
      (typically this is achieved by incorporating a UUID into the key, which is changed each
      time the program logic of this action changes).
  Note the following exception: for actions that discover inputs, the key must change if any
  input names change or else action validation may falsely validate.
</pre>

This excludes the changes to the content of the input files, and is not to be confused with
[RemoteCacheClient#ActionKey](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/remote/common/RemoteCacheClient.java;l=38;drc=21577f202eb90ce94a337ebd2ede824d609537b6){: .external}.

## Updates {:#updates}

For any issues/feature requests, please file an issue [here](https://github.com/bazelbuild/bazel/issues/new).


Project: /_project.yaml
Book: /_book.yaml

# Query guide

{% include "_buttons.html" %}

This page covers how to get started using Bazel's query language to trace
dependencies in your code.

For a language details and `--output` flag details, please see the
reference manuals, [Bazel query reference](/query/language)
and [Bazel cquery reference](/query/cquery). You can get help by
typing `bazel help query` or `bazel help cquery` on the
command line.

To execute a query while ignoring errors such as missing targets, use the
`--keep_going` flag.

## Finding the dependencies of a rule {:#finding-rule-dependencies}

To see the dependencies of `//foo`, use the
`deps` function in bazel query:

<pre>
$ bazel query "deps(//foo)"
//foo:foo
//foo:foo-dep
...
</pre>

This is the set of all targets required to build `//foo`.

## Tracing the dependency chain between two packages {:#tracing-dependency-chain}

The library `//third_party/zlib:zlibonly` isn't in the BUILD file for
`//foo`, but it is an indirect dependency. How can
we trace this dependency path?  There are two useful functions here:
`allpaths` and `somepath`. You may also want to exclude
tooling dependencies with `--notool_deps` if you care only about
what is included in the artifact you built, and not every possible job.

To visualize the graph of all dependencies, pipe the bazel query output through
  the `dot` command-line tool:

<pre>
$ bazel query "allpaths(//foo, third_party/...)" --notool_deps --output graph | dot -Tsvg > /tmp/deps.svg
</pre>

Note: `dot` supports other image formats, just replace `svg` with the
format identifier, for example, `png`.

When a dependency graph is big and complicated, it can be helpful start with a single path:

<pre>
$ bazel query "somepath(//foo:foo, third_party/zlib:zlibonly)"
//foo:foo
//translations/tools:translator
//translations/base:base
//third_party/py/MySQL:MySQL
//third_party/py/MySQL:_MySQL.so
//third_party/mysql:mysql
//third_party/zlib:zlibonly
</pre>

If you do not specify `--output graph` with `allpaths`,
you will get a flattened list of the dependency graph.

<pre>
$ bazel query "allpaths(//foo, third_party/...)"
  ...many errors detected in BUILD files...
//foo:foo
//translations/tools:translator
//translations/tools:aggregator
//translations/base:base
//tools/pkg:pex
//tools/pkg:pex_phase_one
//tools/pkg:pex_lib
//third_party/python:python_lib
//translations/tools:messages
//third_party/py/xml:xml
//third_party/py/xml:utils/boolean.so
//third_party/py/xml:parsers/sgmlop.so
//third_party/py/xml:parsers/pyexpat.so
//third_party/py/MySQL:MySQL
//third_party/py/MySQL:_MySQL.so
//third_party/mysql:mysql
//third_party/openssl:openssl
//third_party/zlib:zlibonly
//third_party/zlib:zlibonly_v1_2_3
//third_party/python:headers
//third_party/openssl:crypto
</pre>

### Aside: implicit dependencies {:#implicit-dependencies}

The BUILD file for `//foo` never references
`//translations/tools:aggregator`. So, where's the direct dependency?

Certain rules include implicit dependencies on additional libraries or tools.
For example, to build a `genproto` rule, you need first to build the Protocol
Compiler, so every `genproto` rule carries an implicit dependency on the
protocol compiler. These dependencies are not mentioned in the build file,
but added in by the build tool. The full set of implicit dependencies is
  currently undocumented. Using `--noimplicit_deps` allows you to filter out
  these deps from your query results. For cquery, this will include resolved toolchains.

## Reverse dependencies {:#reverse-dependencies}

You might want to know the set of targets that depends on some target. For instance,
if you're going to change some code, you might want to know what other code
you're about to break. You can use `rdeps(u, x)` to find the reverse
dependencies of the targets in `x` within the transitive closure of `u`.

Bazel's [Sky Query](/query/language#sky-query)
supports the `allrdeps` function which allows you to query reverse dependencies
in a universe you specify.

## Miscellaneous uses {:#miscellaneous-uses}

You can use `bazel query` to analyze many dependency relationships.

### What exists ... {:#what-exists}

#### What packages exist beneath `foo`? {:#what-exists-beneath-foo}

<pre>bazel query 'foo/...' --output package</pre>

#### What rules are defined in the `foo` package? {:#rules-defined-in-foo}

<pre>bazel query 'kind(rule, foo:*)' --output label_kind</pre>

#### What files are generated by rules in the `foo` package? {:#files-generated-by-rules}

<pre>bazel query 'kind("generated file", //foo:*)'</pre>

#### What targets are generated by starlark macro `foo`? {:#targets-generated-by-foo}

<pre>bazel query 'attr(generator_function, foo, //path/to/search/...)'</pre>

#### What's the set of BUILD files needed to build `//foo`? {:#build-files-required}

<pre>bazel query 'buildfiles(deps(//foo))' | cut -f1 -d:</pre>

#### What are the individual tests that a `test_suite` expands to? {:#individual-tests-in-testsuite}

<pre>bazel query 'tests(//foo:smoke_tests)'</pre>

#### Which of those are C++ tests? {:#cxx-tests}

<pre>bazel query 'kind(cc_.*, tests(//foo:smoke_tests))'</pre>

#### Which of those are small?  Medium?  Large? {:#size-of-tests}

<pre>
bazel query 'attr(size, small, tests(//foo:smoke_tests))'

bazel query 'attr(size, medium, tests(//foo:smoke_tests))'

bazel query 'attr(size, large, tests(//foo:smoke_tests))'
</pre>

#### What are the tests beneath `foo` that match a pattern? {:#tests-beneath-foo}

<pre>bazel query 'filter("pa?t", kind(".*_test rule", //foo/...))'</pre>

The pattern is a regex and is applied to the full name of the rule. It's similar to doing

<pre>bazel query 'kind(".*_test rule", //foo/...)' | grep -E 'pa?t'</pre>

#### What package contains file `path/to/file/bar.java`? {:#barjava-package}

<pre> bazel query path/to/file/bar.java --output=package</pre>

#### What is the build label for `path/to/file/bar.java?` {:#barjava-build-label}

<pre>bazel query path/to/file/bar.java</pre>

#### What rule target(s) contain file `path/to/file/bar.java` as a source? {:#barjava-rule-targets}

<pre>
fullname=$(bazel query path/to/file/bar.java)
bazel query "attr('srcs', $fullname, ${fullname//:*/}:*)"
</pre>

### What package dependencies exist ... {:#package-dependencies}

#### What packages does `foo` depend on? (What do I need to check out to build `foo`) {:#packages-foo-depends-on}

<pre>bazel query 'buildfiles(deps(//foo:foo))' --output package</pre>

Note: `buildfiles` is required in order to correctly obtain all files
referenced by `subinclude`; see the reference manual for details.

#### What packages does the `foo` tree depend on, excluding `foo/contrib`? {:#packages-foo-tree-depends-on}

<pre>bazel query 'deps(foo/... except foo/contrib/...)' --output package</pre>

### What rule dependencies exist ... {:#rule-dependencies}

#### What genproto rules does bar depend upon? {:#genproto-rules}

<pre>bazel query 'kind(genproto, deps(bar/...))'</pre>

#### Find the definition of some JNI (C++) library that is transitively depended upon by a Java binary rule in the servlet tree. {:#jni-library}

<pre>bazel query 'some(kind(cc_.*library, deps(kind(java_binary, //java/com/example/frontend/...))))' --output location</pre>

##### ...Now find the definitions of all the Java binaries that depend on them {:#java-binaries}

<pre>bazel query 'let jbs = kind(java_binary, //java/com/example/frontend/...) in
  let cls = kind(cc_.*library, deps($jbs)) in
    $jbs intersect allpaths($jbs, $cls)'
</pre>

### What file dependencies exist ... {:#file-dependencies}

#### What's the complete set of Java source files required to build foo? {:#java-source-files}

Source files:

<pre>bazel query 'kind("source file", deps(//path/to/target/foo/...))' | grep java$</pre>

Generated files:

<pre>bazel query 'kind("generated file", deps(//path/to/target/foo/...))' | grep java$</pre>

#### What is the complete set of Java source files required to build QUX's tests? {:qux-tests}

Source files:

<pre>bazel query 'kind("source file", deps(kind(".*_test rule", javatests/com/example/qux/...)))' | grep java$</pre>

Generated files:

<pre>bazel query 'kind("generated file", deps(kind(".*_test rule", javatests/com/example/qux/...)))' | grep java$</pre>

### What differences in dependencies between X and Y exist ... {:#differences-in-dependencies}

#### What targets does `//foo` depend on that `//foo:foolib` does not? {:#foo-targets}

<pre>bazel query 'deps(//foo) except deps(//foo:foolib)'</pre>

#### What C++ libraries do the `foo` tests depend on that the `//foo` production binary does _not_ depend on? {:#foo-cxx-libraries}

<pre>bazel query 'kind("cc_library", deps(kind(".*test rule", foo/...)) except deps(//foo))'</pre>

### Why does this dependency exist ... {:#why-dependencies}

#### Why does `bar` depend on `groups2`? {:#dependency-bar-groups2}

<pre>bazel query 'somepath(bar/...,groups2/...:*)'</pre>

Once you have the results of this query, you will often find that a single
target stands out as being an unexpected or egregious and undesirable
dependency of `bar`. The query can then be further refined to:

#### Show me a path from `docker/updater:updater_systest` (a `py_test`) to some `cc_library` that it depends upon: {:#path-docker-cclibrary}

<pre>bazel query 'let cc = kind(cc_library, deps(docker/updater:updater_systest)) in
  somepath(docker/updater:updater_systest, $cc)'</pre>

#### Why does library `//photos/frontend:lib` depend on two variants of the same library `//third_party/jpeglib` and `//third_party/jpeg`? {:#library-two-variants}

This query boils down to: "show me the subgraph of `//photos/frontend:lib` that
depends on both libraries". When shown in topological order, the last element
of the result is the most likely culprit.

<pre>bazel query 'allpaths(//photos/frontend:lib, //third_party/jpeglib)
                intersect
               allpaths(//photos/frontend:lib, //third_party/jpeg)'
//photos/frontend:lib
//photos/frontend:lib_impl
//photos/frontend:lib_dispatcher
//photos/frontend:icons
//photos/frontend/modules/gadgets:gadget_icon
//photos/thumbnailer:thumbnail_lib
//third_party/jpeg/img:renderer
</pre>

### What depends on  ... {:#depends-on}

#### What rules under bar depend on Y? {:#rules-bar-y}

<pre>bazel query 'bar/... intersect allpaths(bar/..., Y)'</pre>

Note: `X intersect allpaths(X, Y)` is the general idiom for the query "which X
depend on Y?" If expression X is non-trivial, it may be convenient to bind a
name to it using `let` to avoid duplication.

#### What targets directly depend on T, in T's package? {:#targets-t}

<pre>bazel query 'same_pkg_direct_rdeps(T)'</pre>

### How do I break a dependency ... {:#break-dependency}

<!-- TODO find a convincing value of X to plug in here -->

#### What dependency paths do I have to break to make `bar` no longer depend on X? {:#break-dependency-bar-x}

To output the graph to a `svg` file:

<pre>bazel query 'allpaths(bar/...,X)' --output graph | dot -Tsvg &gt; /tmp/dep.svg</pre>

### Misc {:#misc}

#### How many sequential steps are there in the `//foo-tests` build? {:#steps-footests}

Unfortunately, the query language can't currently give you the longest path
from x to y, but it can find the (or rather _a_) most distant node from the
starting point, or show you the _lengths_ of the longest path from x to every
y that it depends on. Use `maxrank`:

<pre>bazel query 'deps(//foo-tests)' --output maxrank | tail -1
85 //third_party/zlib:zutil.c</pre>

The result indicates that there exist paths of length 85 that must occur in
order in this build.


Project: /_project.yaml
Book: /_book.yaml

# The Bazel Query Reference

{% include "_buttons.html" %}

This page is the reference manual for the _Bazel Query Language_ used
when you use `bazel query` to analyze build dependencies. It also
describes the output formats `bazel query` supports.

For practical use cases, see the [Bazel Query How-To](/query/guide).

## Additional query reference

In addition to `query`, which runs on the post-loading phase target graph,
Bazel includes *action graph query* and *configurable query*.

### Action graph query {:#aquery}

The action graph query (`aquery`) operates on the post-analysis Configured
Target Graph and exposes information about **Actions**, **Artifacts**, and
their relationships. `aquery` is useful when you are interested in the
properties of the Actions/Artifacts generated from the Configured Target Graph.
For example, the actual commands run and their inputs, outputs, and mnemonics.

For more details, see the [aquery reference](/query/aquery).

### Configurable query {:#cquery}

Traditional Bazel query runs on the post-loading phase target graph and
therefore has no concept of configurations and their related concepts. Notably,
it doesn't correctly resolve [select statements](/reference/be/functions#select)
and instead returns all possible resolutions of selects. However, the
configurable query environment, `cquery`, properly handles configurations but
doesn't provide all of the functionality of this original query.

For more details, see the [cquery reference](/query/cquery).


## Examples {:#examples}

How do people use `bazel query`?  Here are typical examples:

Why does the `//foo` tree depend on `//bar/baz`?
Show a path:

```
somepath(foo/..., //bar/baz:all)
```

What C++ libraries do all the `foo` tests depend on that
the `foo_bin` target does not?

```
kind("cc_library", deps(kind(".*test rule", foo/...)) except deps(//foo:foo_bin))
```

## Tokens: The lexical syntax {:#tokens}

Expressions in the query language are composed of the following
tokens:

* **Keywords**, such as `let`. Keywords are the reserved words of the
  language, and each of them is described below. The complete set
  of keywords is:

   * [`except`](#set-operations)

   * [`in`](#variables)

   * [`intersect`](#set-operations)

   * [`let`](#variables)

   * [`set`](#set)

   * [`union`](#set-operations)

* **Words**, such as "`foo/...`" or "`.*test rule`" or "`//bar/baz:all`". If a
  character sequence is "quoted" (begins and ends with a single-quote ' or
  begins and ends with a double-quote "), it is a word. If a character sequence
  is not quoted, it may still be parsed as a word. Unquoted words are sequences
  of characters drawn from the alphabet characters A-Za-z, the numerals 0-9,
  and the special characters `*/@.-_:$~[]` (asterisk, forward slash, at, period,
  hyphen, underscore, colon, dollar sign, tilde, left square brace, right square
  brace). However, unquoted words may not start with a hyphen `-` or asterisk `*`
  even though relative [target names](/concepts/labels#target-names) may start
  with those characters. As a special rule meant to simplify the handling of
  labels referring to external repositories, unquoted words that start with
  `@@` may contain `+` characters.

  Unquoted words also may not include the characters plus sign `+` or equals
  sign `=`, even though those characters are permitted in target names. When
  writing code that generates query expressions, target names should be quoted.

  Quoting _is_ necessary when writing scripts that construct Bazel query
  expressions from user-supplied values.

  ```
   //foo:bar+wiz    # WRONG: scanned as //foo:bar + wiz.
   //foo:bar=wiz    # WRONG: scanned as //foo:bar = wiz.
   "//foo:bar+wiz"  # OK.
   "//foo:bar=wiz"  # OK.
  ```

  Note that this quoting is in addition to any quoting that may be required by
  your shell, such as:

  ```posix-terminal
  bazel query ' "//foo:bar=wiz" '   # single-quotes for shell, double-quotes for Bazel.
  ```

  Keywords and operators, when quoted, are treated as ordinary words. For example, `some` is a
  keyword but "some" is a word. Both `foo` and "foo" are words.

  However, be careful when using single or double quotes in target names. When
  quoting one or more target names, use only one type of quotes (either all
  single or all double quotes).

  The following are examples of what the Java query string will be:


  ```
    'a"'a'         # WRONG: Error message: unclosed quotation.
    "a'"a"         # WRONG: Error message: unclosed quotation.
    '"a" + 'a''    # WRONG: Error message: unexpected token 'a' after query expression '"a" + '
    "'a' + "a""    # WRONG: Error message: unexpected token 'a' after query expression ''a' + '
    "a'a"          # OK.
    'a"a'          # OK.
    '"a" + "a"'    # OK
    "'a' + 'a'"    # OK
  ```

  We chose this syntax so that quote marks aren't needed in most cases. The
  (unusual) `".*test rule"` example needs quotes: it starts with a period and
  contains a space. Quoting `"cc_library"` is unnecessary but harmless.

* **Punctuation**, such as parens `()`, period `.` and comma `,`. Words
  containing punctuation (other than the exceptions listed above) must be quoted.

Whitespace characters outside of a quoted word are ignored.

## Bazel query language concepts {:#language-concepts}

The Bazel query language is a language of expressions. Every
expression evaluates to a **partially-ordered set** of targets,
or equivalently, a **graph** (DAG) of targets. This is the only
datatype.

Set and graph refer to the same datatype, but emphasize different
aspects of it, for example:

*   **Set:** The partial order of the targets is not interesting.
*   **Graph:** The partial order of targets is significant.

### Cycles in the dependency graph {:#dependency-graph-cycles}

Build dependency graphs should be acyclic.

The algorithms used by the query language are intended for use in
acyclic graphs, but are robust against cycles. The details of how
cycles are treated are not specified and should not be relied upon.

### Implicit dependencies {:#implicit-dependencies}

In addition to build dependencies that are defined explicitly in `BUILD` files,
Bazel adds additional _implicit_ dependencies to rules. Implicit dependencies
may be defined by:

- [Private attributes](/extending/rules#private_attributes_and_implicit_dependencies)
- [Toolchain requirements](/extending/toolchains#writing-rules-toolchains)

By default, `bazel query` takes implicit dependencies into account
when computing the query result. This behavior can be changed with
the `--[no]implicit_deps` option.

Note that, as query does not consider configurations, potential toolchain
**implementations** are not considered dependencies, only the
required toolchain types. See
[toolchain documentation](/extending/toolchains#writing-rules-toolchains).

### Soundness {:#soundness}

Bazel query language expressions operate over the build
dependency graph, which is the graph implicitly defined by all
rule declarations in all `BUILD` files. It is important to understand
that this graph is somewhat abstract, and does not constitute a
complete description of how to perform all the steps of a build. In
order to perform a build, a _configuration_ is required too;
see the [configurations](/docs/user-manual#configurations)
section of the User's Guide for more detail.

The result of evaluating an expression in the Bazel query language
is true _for all configurations_, which means that it may be
a conservative over-approximation, and not exactly precise. If you
use the query tool to compute the set of all source files needed
during a build, it may report more than are actually necessary
because, for example, the query tool will include all the files
needed to support message translation, even though you don't intend
to use that feature in your build.

### On the preservation of graph order {:#graph-order}

Operations preserve any ordering
constraints inherited from their subexpressions. You can think of
this as "the law of conservation of partial order". Consider an
example: if you issue a query to determine the transitive closure of
dependencies of a particular target, the resulting set is ordered
according to the dependency graph. If you filter that set to
include only the targets of `file` kind, the same
_transitive_ partial ordering relation holds between every
pair of targets in the resulting subset - even though none of
these pairs is actually directly connected in the original graph.
(There are no file-file edges in the build dependency graph).

However, while all operators _preserve_ order, some
operations, such as the [set operations](#set-operations)
don't _introduce_ any ordering constraints of their own.
Consider this expression:

```
deps(x) union y
```

The order of the final result set is guaranteed to preserve all the
ordering constraints of its subexpressions, namely, that all the
transitive dependencies of `x` are correctly ordered with
respect to each other. However, the query guarantees nothing about
the ordering of the targets in `y`, nor about the
ordering of the targets in `deps(x)` relative to those in
`y` (except for those targets in
`y` that also happen to be in `deps(x)`).

Operators that introduce ordering constraints include:
`allpaths`, `deps`, `rdeps`, `somepath`, and the target pattern wildcards
`package:*`, `dir/...`, etc.

### Sky query {:#sky-query}

_Sky Query_ is a mode of query that operates over a specified _universe scope_.

#### Special functions available only in SkyQuery

Sky Query mode has the additional query functions `allrdeps` and
`rbuildfiles`. These functions operate over the entire
universe scope (which is why they don't make sense for normal Query).

#### Specifying a universe scope

Sky Query mode is activated by passing the following two flags:
(`--universe_scope` or `--infer_universe_scope`) and
`--order_output=no`.
`--universe_scope=<target_pattern1>,...,<target_patternN>` tells query to
preload the transitive closure of the target pattern specified by the target patterns, which can
be both additive and subtractive. All queries are then evaluated in this "scope". In particular,
the [`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles) operators only return results from this scope.
`--infer_universe_scope` tells Bazel to infer a value for `--universe_scope`
from the query expression. This inferred value is the list of unique target patterns in the
query expression, but this might not be what you want. For example:

```posix-terminal
bazel query --infer_universe_scope --order_output=no "allrdeps(//my:target)"
```

The list of unique target patterns in this query expression is `["//my:target"]`, so
Bazel treats this the same as the invocation:

```posix-terminal
bazel query --universe_scope=//my:target --order_output=no "allrdeps(//my:target)"
```

But the result of that query with `--universe_scope` is only `//my:target`;
none of the reverse dependencies of `//my:target` are in the universe, by
construction! On the other hand, consider:

```posix-terminal
bazel query --infer_universe_scope --order_output=no "tests(//a/... + b/...) intersect allrdeps(siblings(rbuildfiles(my/starlark/file.bzl)))"
```

This is a meaningful query invocation that is trying to compute the test targets in the
[`tests`](#tests) expansion of the targets under some directories that
transitively depend on targets whose definition uses a certain `.bzl` file. Here,
`--infer_universe_scope` is a convenience, especially in the case where the choice of
`--universe_scope` would otherwise require you to parse the query expression yourself.

So, for query expressions that use universe-scoped operators like
[`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles) be sure to use
`--infer_universe_scope` only if its behavior is what you want.

Sky Query has some advantages and disadvantages compared to the default query. The main
disadvantage is that it cannot order its output according to graph order, and thus certain
[output formats](#output-formats) are forbidden. Its advantages are that it provides
two operators ([`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles)) that are not available in the default query.
As well, Sky Query does its work by introspecting the
[Skyframe](/reference/skyframe) graph, rather than creating a new
graph, which is what the default implementation does. Thus, there are some circumstances in which
it is faster and uses less memory.

## Expressions: Syntax and semantics of the grammar {:#expressions}

This is the grammar of the Bazel query language, expressed in EBNF notation:

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}word{{ '</var>' }}
       | let {{ '<var>' }}name{{ '</var>' }} = {{ '<var>' }}expr{{ '</var>' }} in {{ '<var>' }}expr{{ '</var>' }}
       | ({{ '<var>' }}expr{{ '</var>' }})
       | {{ '<var>' }}expr{{ '</var>' }} intersect {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} ^ {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} union {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} + {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} except {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} - {{ '<var>' }}expr{{ '</var>' }}
       | set({{ '<var>' }}word{{ '</var>' }} *)
       | {{ '<var>' }}word{{ '</var>' }} '(' {{ '<var>' }}int{{ '</var>' }} | {{ '<var>' }}word{{ '</var>' }} | {{ '<var>' }}expr{{ '</var>' }} ... ')'
```

The following sections describe each of the productions of this grammar in order.

### Target patterns {:#target-patterns}

```
expr ::= {{ '<var>' }}word{{ '</var>' }}
```

Syntactically, a _target pattern_ is just a word. It's interpreted as an
(unordered) set of targets. The simplest target pattern is a label, which
identifies a single target (file or rule). For example, the target pattern
`//foo:bar` evaluates to a set containing one element, the target, the `bar`
rule.

Target patterns generalize labels to include wildcards over packages and
targets. For example, `foo/...:all` (or just `foo/...`) is a target pattern
that evaluates to a set containing all _rules_ in every package recursively
beneath the `foo` directory; `bar/baz:all` is a target pattern that evaluates
to a set containing all the rules in the `bar/baz` package, but not its
subpackages.

Similarly, `foo/...:*` is a target pattern that evaluates to a set containing
all _targets_ (rules _and_ files) in every package recursively beneath the
`foo` directory; `bar/baz:*` evaluates to a set containing all the targets in
the `bar/baz` package, but not its subpackages.

Because the `:*` wildcard matches files as well as rules, it's often more
useful than `:all` for queries. Conversely, the `:all` wildcard (implicit in
target patterns like `foo/...`) is typically more useful for builds.

`bazel query` target patterns work the same as `bazel build` build targets do.
For more details, see [Target Patterns](/docs/user-manual#target-patterns), or
type `bazel help target-syntax`.

Target patterns may evaluate to a singleton set (in the case of a label), to a
set containing many elements (as in the case of `foo/...`, which has thousands
of elements) or to the empty set, if the target pattern matches no targets.

All nodes in the result of a target pattern expression are correctly ordered
relative to each other according to the dependency relation. So, the result of
`foo:*` is not just the set of targets in package `foo`, it is also the
_graph_ over those targets. (No guarantees are made about the relative ordering
of the result nodes against other nodes.) For more details, see the
[graph order](#graph-order) section.

### Variables {:#variables}

```none {:.devsite-disable-click-to-copy}
expr ::= let {{ '<var>' }}name{{ '</var>' }} = {{ '<var>' }}expr{{ '</var>' }}{{ '<sub>' }}1{{ '</sub>' }} in {{ '<var>' }}expr{{ '</var>' }}{{ '<sub>' }}2{{ '</sub>' }}
       | {{ '<var>' }}$name{{ '</var>' }}
```

The Bazel query language allows definitions of and references to
variables. The result of evaluation of a `let` expression is the same as
that of {{ '<var>' }}expr{{ '</var>' }}<sub>2</sub>, with all free occurrences
of variable {{ '<var>' }}name{{ '</var>' }} replaced by the value of
{{ '<var>' }}expr{{ '</var>' }}<sub>1</sub>.

For example, `let v = foo/... in allpaths($v, //common) intersect $v` is
equivalent to the `allpaths(foo/...,//common) intersect foo/...`.

An occurrence of a variable reference `name` other than in
an enclosing `let {{ '<var>' }}name{{ '</var>' }} = ...` expression is an
error. In other words, top-level query expressions cannot have free
variables.

In the above grammar productions, `name` is like _word_, but with the
additional constraint that it be a legal identifier in the C programming
language. References to the variable must be prepended with the "$" character.

Each `let` expression defines only a single variable, but you can nest them.

Both [target patterns](#target-patterns) and variable references consist of
just a single token, a word, creating a syntactic ambiguity. However, there is
no semantic ambiguity, because the subset of words that are legal variable
names is disjoint from the subset of words that are legal target patterns.

Technically speaking, `let` expressions do not increase
the expressiveness of the query language: any query expressible in
the language can also be expressed without them. However, they
improve the conciseness of many queries, and may also lead to more
efficient query evaluation.

### Parenthesized expressions {:#parenthesized-expressions}

```none {:.devsite-disable-click-to-copy}
expr ::= ({{ '<var>' }}expr{{ '</var>' }})
```

Parentheses associate subexpressions to force an order of evaluation.
A parenthesized expression evaluates to the value of its argument.

### Algebraic set operations: intersection, union, set difference {:#algebraic-set-operations}

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}expr{{ '</var>' }} intersect {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} ^ {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} union {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} + {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} except {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} - {{ '<var>' }}expr{{ '</var>' }}
```

These three operators compute the usual set operations over their arguments.
Each operator has two forms, a nominal form, such as `intersect`, and a
symbolic form, such as `^`. Both forms are equivalent; the symbolic forms are
quicker to type. (For clarity, the rest of this page uses the nominal forms.)

For example,

```
foo/... except foo/bar/...
```

evaluates to the set of targets that match `foo/...` but not `foo/bar/...`.

You can write the same query as:

```
foo/... - foo/bar/...
```

The `intersect` (`^`) and `union` (`+`) operations are commutative (symmetric);
`except` (`-`) is asymmetric. The parser treats all three operators as
left-associative and of equal precedence, so you might want parentheses. For
example, the first two of these expressions are equivalent, but the third is not:

```
x intersect y union z
(x intersect y) union z
x intersect (y union z)
```

Important: Use parentheses where there is any danger of ambiguity in reading a
query expression.

### Read targets from an external source: set {:#set}

```none {:.devsite-disable-click-to-copy}
expr ::= set({{ '<var>' }}word{{ '</var>' }} *)
```

The `set({{ '<var>' }}a{{ '</var>' }} {{ '<var>' }}b{{ '</var>' }} {{ '<var>' }}c{{ '</var>' }} ...)`
operator computes the union of a set of zero or more
[target patterns](#target-patterns), separated by whitespace (no commas).

In conjunction with the Bourne shell's `$(...)` feature, `set()` provides a
means of saving the results of one query in a regular text file, manipulating
that text file using other programs (such as standard UNIX shell tools), and then
introducing the result back into the query tool as a value for further
processing. For example:

```posix-terminal
bazel query deps(//my:target) --output=label | grep ... | sed ... | awk ... > foo

bazel query "kind(cc_binary, set($(<foo)))"
```

In the next example,`kind(cc_library, deps(//some_dir/foo:main, 5))` is
computed by filtering on the `maxrank` values using an `awk` program.

```posix-terminal
bazel query 'deps(//some_dir/foo:main)' --output maxrank | awk '($1 < 5) { print $2;} ' > foo

bazel query "kind(cc_library, set($(<foo)))"
```

In these examples, `$(<foo)` is a shorthand for `$(cat foo)`, but shell
commands other than `cat` may be used too—such as the previous `awk` command.

Note: `set()` introduces no graph ordering constraints, so path information may
be lost when saving and reloading sets of nodes using it. For more details,
see the [graph order](#graph-order) section below.

## Functions {:#functions}

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}word{{ '</var>' }} '(' {{ '<var>' }}int{{ '</var>' }} | {{ '<var>' }}word{{ '</var>' }} | {{ '<var>' }}expr{{ '</var>' }} ... ')'
```

The query language defines several functions. The name of the function
determines the number and type of arguments it requires. The following
functions are available:

* [`allpaths`](#somepath-allpaths)
* [`attr`](#attr)
* [`buildfiles`](#buildfiles)
* [`rbuildfiles`](#rbuildfiles)
* [`deps`](#deps)
* [`filter`](#filter)
* [`kind`](#kind)
* [`labels`](#labels)
* [`loadfiles`](#loadfiles)
* [`rdeps`](#rdeps)
* [`allrdeps`](#allrdeps)
* [`same_pkg_direct_rdeps`](#same_pkg_direct_rdeps)
* [`siblings`](#siblings)
* [`some`](#some)
* [`somepath`](#somepath-allpaths)
* [`tests`](#tests)
* [`visible`](#visible)



### Transitive closure of dependencies: deps {:#deps}

```none {:.devsite-disable-click-to-copy}
expr ::= deps({{ '<var>' }}expr{{ '</var>' }})
       | deps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

The `deps({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the graph formed
by the transitive closure of dependencies of its argument set
{{ '<var>' }}x{{ '</var>' }}. For example, the value of `deps(//foo)` is the
dependency graph rooted at the single node `foo`, including all its
dependencies. The value of `deps(foo/...)` is the dependency graphs whose roots
are all rules in every package beneath the `foo` directory. In this context,
'dependencies' means only rule and file targets, therefore the `BUILD` and
Starlark files needed to create these targets are not included here. For that
you should use the [`buildfiles`](#buildfiles) operator.

The resulting graph is ordered according to the dependency relation. For more
details, see the section on [graph order](#graph-order).

The `deps` operator accepts an optional second argument, which is an integer
literal specifying an upper bound on the depth of the search. So
`deps(foo:*, 0)` returns all targets in the `foo` package, while
`deps(foo:*, 1)` further includes the direct prerequisites of any target in the
`foo` package, and `deps(foo:*, 2)` further includes the nodes directly
reachable from the nodes in `deps(foo:*, 1)`, and so on. (These numbers
correspond to the ranks shown in the [`minrank`](#output-ranked) output format.)
If the {{ '<var>' }}depth{{ '</var>' }} parameter is omitted, the search is
unbounded: it computes the reflexive transitive closure of prerequisites.

### Transitive closure of reverse dependencies: rdeps {:#rdeps}

```none {:.devsite-disable-click-to-copy}
expr ::= rdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
       | rdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

The `rdeps({{ '<var>' }}u{{ '</var>' }}, {{ '<var>' }}x{{ '</var>' }})`
operator evaluates to the reverse dependencies of the argument set
{{ '<var>' }}x{{ '</var>' }} within the transitive closure of the universe set
{{ '<var>' }}u{{ '</var>' }}.

The resulting graph is ordered according to the dependency relation. See the
section on [graph order](#graph-order) for more details.

The `rdeps` operator accepts an optional third argument, which is an integer
literal specifying an upper bound on the depth of the search. The resulting
graph only includes nodes within a distance of the specified depth from any
node in the argument set. So `rdeps(//foo, //common, 1)` evaluates to all nodes
in the transitive closure of `//foo` that directly depend on `//common`. (These
numbers correspond to the ranks shown in the [`minrank`](#output-ranked) output
format.) If the {{ '<var>' }}depth{{ '</var>' }} parameter is omitted, the
search is unbounded.

### Transitive closure of all reverse dependencies: allrdeps {:#allrdeps}

```
expr ::= allrdeps({{ '<var>' }}expr{{ '</var>' }})
       | allrdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

Note: Only available with [Sky Query](#sky-query)

The `allrdeps` operator behaves just like the [`rdeps`](#rdeps)
operator, except that the "universe set" is whatever the `--universe_scope` flag
evaluated to, instead of being separately specified. Thus, if
`--universe_scope=//foo/...` was passed, then `allrdeps(//bar)` is
equivalent to `rdeps(//foo/..., //bar)`.

### Direct reverse dependencies in the same package: same_pkg_direct_rdeps {:#same_pkg_direct_rdeps}

```
expr ::= same_pkg_direct_rdeps({{ '<var>' }}expr{{ '</var>' }})
```

The `same_pkg_direct_rdeps({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the full set of targets
that are in the same package as a target in the argument set, and which directly depend on it.

### Dealing with a target's package: siblings {:#siblings}

```
expr ::= siblings({{ '<var>' }}expr{{ '</var>' }})
```

The `siblings({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the full set of targets that are in
the same package as a target in the argument set.

### Arbitrary choice: some {:#some}

```
expr ::= some({{ '<var>' }}expr{{ '</var>' }})
       | some({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}count{{ '</var> '}})
```

The `some({{ '<var>' }}x{{ '</var>' }}, {{ '<var>' }}k{{ '</var>' }})` operator
selects at most {{ '<var>' }}k{{ '</var>' }} targets arbitrarily from its
argument set {{ '<var>' }}x{{ '</var>' }}, and evaluates to a set containing
only those targets. Parameter {{ '<var>' }}k{{ '</var>' }} is optional; if
missing, the result will be a singleton set containing only one target
arbitrarily selected. If the size of argument set {{ '<var>' }}x{{ '</var>' }} is
smaller than {{ '<var>' }}k{{ '</var>' }}, the whole argument set
{{ '<var>' }}x{{ '</var>' }} will be returned.

For example, the expression `some(//foo:main union //bar:baz)` evaluates to a
singleton set containing either `//foo:main` or `//bar:baz`—though which
one is not defined. The expression `some(//foo:main union //bar:baz, 2)` or
`some(//foo:main union //bar:baz, 3)` returns both `//foo:main` and
`//bar:baz`.

If the argument is a singleton, then `some`
computes the identity function: `some(//foo:main)` is
equivalent to `//foo:main`.

It is an error if the specified argument set is empty, as in the
expression `some(//foo:main intersect //bar:baz)`.

### Path operators: somepath, allpaths {:#somepath-allpaths}

```
expr ::= somepath({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
       | allpaths({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `somepath({{ '<var>' }}S{{ '</var>' }}, {{ '<var>' }}E{{ '</var>' }})` and
`allpaths({{ '<var>' }}S{{ '</var>' }}, {{ '<var>' }}E{{ '</var>' }})` operators compute
paths between two sets of targets. Both queries accept two
arguments, a set {{ '<var>' }}S{{ '</var>' }} of starting points and a set
{{ '<var>' }}E{{ '</var>' }} of ending points. `somepath` returns the
graph of nodes on _some_ arbitrary path from a target in
{{ '<var>' }}S{{ '</var>' }} to a target in {{ '<var>' }}E{{ '</var>' }}; `allpaths`
returns the graph of nodes on _all_ paths from any target in
{{ '<var>' }}S{{ '</var>' }} to any target in {{ '<var>' }}E{{ '</var>' }}.

The resulting graphs are ordered according to the dependency relation.
See the section on [graph order](#graph-order) for more details.

<table>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/somepath1.svg" alt="Somepath">
        <figcaption><code>somepath(S1 + S2, E)</code>, one possible result.</figcaption>
      </figure>
<!-- digraph somepath1 {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1;
  n2 [fillcolor="pink",style=filled];
  n3 [fillcolor="pink",style=filled];
  n4 [fillcolor="pink",style=filled,label="E"];
  n5; n6;
  n7 [fillcolor="pink",style=filled,label="S1"];
  n8 [label="S2"];
  n9;
  n10 [fillcolor="pink",style=filled];
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
    <td>
      <figure>
        <img src="/docs/images/somepath2.svg" alt="Somepath">
        <figcaption><code>somepath(S1 + S2, E)</code>, another possible result.</figcaption>
      </figure>
<!-- digraph somepath2 {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1; n2; n3;
  n4 [fillcolor="pink",style=filled,label="E"];
  n5;
  n6 [fillcolor="pink",style=filled];
  n7 [label="S1"];
  n8 [fillcolor="pink",style=filled,label="S2"];
  n9; n10;
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
    <td>
      <figure>
        <img src="/docs/images/allpaths.svg" alt="Allpaths">
        <figcaption><code>allpaths(S1 + S2, E)</code></figcaption>
      </figure>
<!-- digraph allpaths {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1;
  n2 [fillcolor="pink",style=filled];
  n3 [fillcolor="pink",style=filled];
  n4 [fillcolor="pink",style=filled,label="E"];
  n5 [fillcolor="pink",style=filled];
  n6 [fillcolor="pink",style=filled];
  n7 [fillcolor="pink",style=filled, label="S1"];
  n8 [fillcolor="pink",style=filled, label="S2"];
  n9;
  n10 [fillcolor="pink",style=filled];
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
  </tr>
</table>

### Target kind filtering: kind {:#kind}

```
expr ::= kind({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `kind({{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards those targets
that are not of the expected kind. The {{ '<var>' }}pattern{{ '</var>' }}
parameter specifies what kind of target to match.

For example, the kinds for the four targets defined by the `BUILD` file
(for package `p`) shown below are illustrated in the table:

<table>
  <tr>
    <th>Code</th>
    <th>Target</th>
    <th>Kind</th>
  </tr>
  <tr>
    <td rowspan="4">
      <pre>
        genrule(
            name = "a",
            srcs = ["a.in"],
            outs = ["a.out"],
            cmd = "...",
        )
      </pre>
    </td>
    <td><code>//p:a</code></td>
    <td>genrule rule</td>
  </tr>
  <tr>
    <td><code>//p:a.in</code></td>
    <td>source file</td>
  </tr>
  <tr>
    <td><code>//p:a.out</code></td>
    <td>generated file</td>
  </tr>
  <tr>
    <td><code>//p:BUILD</code></td>
    <td>source file</td>
  </tr>
</table>

Thus, `kind("cc_.* rule", foo/...)` evaluates to the set
of all `cc_library`, `cc_binary`, etc,
rule targets beneath `foo`, and `kind("source file", deps(//foo))`
evaluates to the set of all source files in the transitive closure
of dependencies of the `//foo` target.

Quotation of the {{ '<var>' }}pattern{{ '</var>' }} argument is often required
because without it, many [regular expressions](#regex), such as `source
file` and `.*_test`, are not considered words by the parser.

When matching for `package group`, targets ending in
`:all` may not yield any results. Use `:all-targets` instead.

### Target name filtering: filter {:#filter}

```
expr ::= filter({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `filter({{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards targets whose
labels (in absolute form) do not match the pattern; it
evaluates to a subset of its input.

The first argument, {{ '<var>' }}pattern{{ '</var>' }} is a word containing a
[regular expression](#regex) over target names. A `filter` expression
evaluates to the set containing all targets {{ '<var>' }}x{{ '</var>' }} such that
{{ '<var>' }}x{{ '</var>' }} is a member of the set {{ '<var>' }}input{{ '</var>' }} and the
label (in absolute form, such as `//foo:bar`)
of {{ '<var>' }}x{{ '</var>' }} contains an (unanchored) match
for the regular expression {{ '<var>' }}pattern{{ '</var>' }}. Since all
target names start with `//`, it may be used as an alternative
to the `^` regular expression anchor.

This operator often provides a much faster and more robust alternative to the
`intersect` operator. For example, in order to see all
`bar` dependencies of the `//foo:foo` target, one could
evaluate

```
deps(//foo) intersect //bar/...
```

This statement, however, will require parsing of all `BUILD` files in the
`bar` tree, which will be slow and prone to errors in
irrelevant `BUILD` files. An alternative would be:

```
filter(//bar, deps(//foo))
```

which would first calculate the set of `//foo` dependencies and
then would filter only targets matching the provided pattern—in other
words, targets with names containing `//bar` as a substring.

Another common use of the `filter({{ '<var>' }}pattern{{ '</var>' }},
{{ '<var>' }}expr{{ '</var>' }})` operator is to filter specific files by their
name or extension. For example,

```
filter("\.cc$", deps(//foo))
```

will provide a list of all `.cc` files used to build `//foo`.

### Rule attribute filtering: attr {:#attr}

```
expr ::= attr({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The
`attr({{ '<var>' }}name{{ '</var>' }}, {{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards targets that aren't
rules, rule targets that do not have attribute {{ '<var>' }}name{{ '</var>' }}
defined or rule targets where the attribute value does not match the provided
[regular expression](#regex) {{ '<var>' }}pattern{{ '</var>' }}; it evaluates
to a subset of its input.

The first argument, {{ '<var>' }}name{{ '</var>' }} is the name of the rule
attribute that should be matched against the provided
[regular expression](#regex) pattern. The second argument,
{{ '<var>' }}pattern{{ '</var>' }} is a regular expression over the attribute
values. An `attr` expression evaluates to the set containing all targets
{{ '<var>' }}x{{ '</var>' }} such that  {{ '<var>' }}x{{ '</var>' }} is a
member of the set {{ '<var>' }}input{{ '</var>' }}, is a rule with the defined
attribute {{ '<var>' }}name{{ '</var>' }} and the attribute value contains an
(unanchored) match for the regular expression
{{ '<var>' }}pattern{{ '</var>' }}. If {{ '<var>' }}name{{ '</var>' }} is an
optional attribute and rule does not specify it explicitly then default
attribute value will be used for comparison. For example,

```
attr(linkshared, 0, deps(//foo))
```

will select all `//foo` dependencies that are allowed to have a
linkshared attribute (such as, `cc_binary` rule) and have it either
explicitly set to 0 or do not set it at all but default value is 0 (such as for
`cc_binary` rules).

List-type attributes (such as `srcs`, `data`, etc) are
converted to strings of the form `[value<sub>1</sub>, ..., value<sub>n</sub>]`,
starting with a `[` bracket, ending with a `]` bracket
and using "`, `" (comma, space) to delimit multiple values.
Labels are converted to strings by using the absolute form of the
label. For example, an attribute `deps=[":foo",
"//otherpkg:bar", "wiz"]` would be converted to the
string `[//thispkg:foo, //otherpkg:bar, //thispkg:wiz]`.
Brackets are always present, so the empty list would use string value `[]`
for matching purposes. For example,

```
attr("srcs", "\[\]", deps(//foo))
```

will select all rules among `//foo` dependencies that have an
empty `srcs` attribute, while

```
attr("data", ".{3,}", deps(//foo))
```

will select all rules among `//foo` dependencies that specify at
least one value in the `data` attribute (every label is at least
3 characters long due to the `//` and `:`).

To select all rules among `//foo` dependencies with a particular `value` in a
list-type attribute, use

```
attr("tags", "[\[ ]value[,\]]", deps(//foo))
```

This works because the character before `value` will be `[` or a space and the
character after `value` will be a comma or `]`.

To select all rules among `//foo` dependencies with a particular `key` and
`value` in a dict-type attribute, use

```
attr("some_dict_attribute", "[\{ ]key=value[,\}]", deps(//foo))
```

This would select `//foo` if `//foo` is defined as

```
some_rule(
  name = "foo",
  some_dict_attribute = {
    "key": "value",
  },
)
```

This works because the character before `key=value` will be `{` or a space and
the character after `key=value` will be a comma or `}`.

### Rule visibility filtering: visible {:#visible}

```
expr ::= visible({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `visible({{ '<var>' }}predicate{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})` operator
applies a filter to a set of targets, and discards targets without the
required visibility.

The first argument, {{ '<var>' }}predicate{{ '</var>' }}, is a set of targets that all targets
in the output must be visible to. A {{ '<var>' }}visible{{ '</var>' }} expression
evaluates to the set containing all targets {{ '<var>' }}x{{ '</var>' }} such that {{ '<var>' }}x{{ '</var>' }}
is a member of the set {{ '<var>' }}input{{ '</var>' }}, and for all targets {{ '<var>' }}y{{ '</var>' }} in
{{ '<var>' }}predicate{{ '</var>' }} {{ '<var>' }}x{{ '</var>' }} is visible to {{ '<var>' }}y{{ '</var>' }}. For example:

```
visible(//foo, //bar:*)
```

will select all targets in the package `//bar` that `//foo`
can depend on without violating visibility restrictions.

### Evaluation of rule attributes of type label: labels {:#labels}

```
expr ::= labels({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `labels({{ '<var>' }}attr_name{{ '</var>' }}, {{ '<var>' }}inputs{{ '</var>' }})`
operator returns the set of targets specified in the
attribute {{ '<var>' }}attr_name{{ '</var>' }} of type "label" or "list of label" in
some rule in set {{ '<var>' }}inputs{{ '</var>' }}.

For example, `labels(srcs, //foo)` returns the set of
targets appearing in the `srcs` attribute of
the `//foo` rule. If there are multiple rules
with `srcs` attributes in the {{ '<var>' }}inputs{{ '</var>' }} set, the
union of their `srcs` is returned.

### Expand and filter test_suites: tests {:#tests}

```
expr ::= tests({{ '<var>' }}expr{{ '</var>' }})
```

The `tests({{ '<var>' }}x{{ '</var>' }})` operator returns the set of all test
rules in set {{ '<var>' }}x{{ '</var>' }}, expanding any `test_suite` rules into
the set of individual tests that they refer to, and applying filtering by
`tag` and `size`.

By default, query evaluation
ignores any non-test targets in all `test_suite` rules. This can be
changed to errors with the `--strict_test_suite` option.

For example, the query `kind(test, foo:*)` lists all
the `*_test` and `test_suite` rules
in the `foo` package. All the results are (by
definition) members of the `foo` package. In contrast,
the query `tests(foo:*)` will return all of the
individual tests that would be executed by `bazel test
foo:*`: this may include tests belonging to other packages,
that are referenced directly or indirectly
via `test_suite` rules.

### Package definition files: buildfiles {:#buildfiles}

```
expr ::= buildfiles({{ '<var>' }}expr{{ '</var>' }})
```

The `buildfiles({{ '<var>' }}x{{ '</var>' }})` operator returns the set
of files that define the packages of each target in
set {{ '<var>' }}x{{ '</var>' }}; in other words, for each package, its `BUILD` file,
plus any .bzl files it references via `load`. Note that this
also returns the `BUILD` files of the packages containing these
`load`ed files.

This operator is typically used when determining what files or
packages are required to build a specified target, often in conjunction with
the [`--output package`](#output-package) option, below). For example,

```posix-terminal
bazel query 'buildfiles(deps(//foo))' --output package
```

returns the set of all packages on which `//foo` transitively depends.

Note: A naive attempt at the above query would omit
the `buildfiles` operator and use only `deps`,
but this yields an incorrect result: while the result contains the
majority of needed packages, those packages that contain only files
that are `load()`'ed will be missing.

Warning: Bazel pretends each `.bzl` file produced by
`buildfiles` has a corresponding target (for example, file `a/b.bzl` =>
target `//a:b.bzl`), but this isn't necessarily the case. Therefore,
`buildfiles` doesn't compose well with other query operators and its results can be
misleading when formatted in a structured way, such as
[`--output=xml`](#xml).

### Package definition files: rbuildfiles {:#rbuildfiles}

```
expr ::= rbuildfiles({{ '<var>' }}word{{ '</var>' }}, ...)
```

Note: Only available with [Sky Query](#sky-query).

The `rbuildfiles` operator takes a comma-separated list of path fragments and returns
the set of `BUILD` files that transitively depend on these path fragments. For instance, if
`//foo` is a package, then `rbuildfiles(foo/BUILD)` will return the
`//foo:BUILD` target. If the `foo/BUILD` file has
`load('//bar:file.bzl'...` in it, then `rbuildfiles(bar/file.bzl)` will
return the `//foo:BUILD` target, as well as the targets for any other `BUILD` files that
load `//bar:file.bzl`

The scope of the <scope>rbuildfiles</scope> operator is the universe specified by the
`--universe_scope` flag. Files that do not correspond directly to `BUILD` files and `.bzl`
files do not affect the results. For instance, source files (like `foo.cc`) are ignored,
even if they are explicitly mentioned in the `BUILD` file. Symlinks, however, are respected, so that
if `foo/BUILD` is a symlink to `bar/BUILD`, then
`rbuildfiles(bar/BUILD)` will include `//foo:BUILD` in its results.

The `rbuildfiles` operator is almost morally the inverse of the
[`buildfiles`](#buildfiles) operator. However, this moral inversion
holds more strongly in one direction: the outputs of `rbuildfiles` are just like the
inputs of `buildfiles`; the former will only contain `BUILD` file targets in packages,
and the latter may contain such targets. In the other direction, the correspondence is weaker. The
outputs of the `buildfiles` operator are targets corresponding to all packages and .`bzl`
files needed by a given input. However, the inputs of the `rbuildfiles` operator are
not those targets, but rather the path fragments that correspond to those targets.

### Package definition files: loadfiles {:#loadfiles}

```
expr ::= loadfiles({{ '<var>' }}expr{{ '</var>' }})
```

The `loadfiles({{ '<var>' }}x{{ '</var>' }})` operator returns the set of
Starlark files that are needed to load the packages of each target in
set {{ '<var>' }}x{{ '</var>' }}. In other words, for each package, it returns the
.bzl files that are referenced from its `BUILD` files.

Warning: Bazel pretends each of these .bzl files has a corresponding target
(for example, file `a/b.bzl` => target `//a:b.bzl`), but this isn't
necessarily the case. Therefore, `loadfiles` doesn't compose well with other query
operators and its results can be misleading when formatted in a structured way, such as
[`--output=xml`](#xml).

## Output formats {:#output-formats}

`bazel query` generates a graph.
You specify the content, format, and ordering by which
`bazel query` presents this graph
by means of the `--output` command-line option.

When running with [Sky Query](#sky-query), only output formats that are compatible with
unordered output are allowed. Specifically, `graph`, `minrank`, and
`maxrank` output formats are forbidden.

Some of the output formats accept additional options. The name of
each output option is prefixed with the output format to which it
applies, so `--graph:factored` applies only
when `--output=graph` is being used; it has no effect if
an output format other than `graph` is used. Similarly,
`--xml:line_numbers` applies only when `--output=xml`
is being used.

### On the ordering of results {:#results-ordering}

Although query expressions always follow the "[law of
conservation of graph order](#graph-order)", _presenting_ the results may be done
in either a dependency-ordered or unordered manner. This does **not**
influence the targets in the result set or how the query is computed. It only
affects how the results are printed to stdout. Moreover, nodes that are
equivalent in the dependency order may or may not be ordered alphabetically.
The `--order_output` flag can be used to control this behavior.
(The `--[no]order_results` flag has a subset of the functionality
of the `--order_output` flag and is deprecated.)

The default value of this flag is `auto`, which prints results in **lexicographical
order**. However, when `somepath(a,b)` is used, the results will be printed in
`deps` order instead.

When this flag is `no` and `--output` is one of
`build`, `label`, `label_kind`, `location`, `package`, `proto`, or
`xml`, the outputs will be printed in arbitrary order. **This is
generally the fastest option**. It is not supported though when
`--output` is one of `graph`, `minrank` or
`maxrank`: with these formats, Bazel always prints results
ordered by the dependency order or rank.

When this flag is `deps`, Bazel prints results in some topological order—that is,
dependents first and dependencies after. However, nodes that are unordered by the
dependency order (because there is no path from either one to the other) may be
printed in any order.

When this flag is `full`, Bazel prints nodes in a fully deterministic (total) order.
First, all nodes are sorted alphabetically. Then, each node in the list is used as the start of a
post-order depth-first search in which outgoing edges to unvisited nodes are traversed in
alphabetical order of the successor nodes. Finally, nodes are printed in the reverse of the order
in which they were visited.

Printing nodes in this order may be slower, so it should be used only when determinism is
important.

### Print the source form of targets as they would appear in BUILD {:#target-source-form}

```
--output build
```

With this option, the representation of each target is as if it were
hand-written in the BUILD language. All variables and function calls
(such as glob, macros) are expanded, which is useful for seeing the effect
of Starlark macros. Additionally, each effective rule reports a
`generator_name` and/or `generator_function`) value,
giving the name of the macro that was evaluated to produce the effective rule.

Although the output uses the same syntax as `BUILD` files, it is not
guaranteed to produce a valid `BUILD` file.

### Print the label of each target {:#print-label-target}

```
--output label
```

With this option, the set of names (or _labels_) of each target
in the resulting graph is printed, one label per line, in
topological order (unless `--noorder_results` is specified, see
[notes on the ordering of results](#result-order)).
(A topological ordering is one in which a graph
node appears earlier than all of its successors.)  Of course there
are many possible topological orderings of a graph (_reverse
postorder_ is just one); which one is chosen is not specified.

When printing the output of a `somepath` query, the order
in which the nodes are printed is the order of the path.

Caveat: in some corner cases, there may be two distinct targets with
the same label; for example, a `sh_binary` rule and its
sole (implicit) `srcs` file may both be called
`foo.sh`. If the result of a query contains both of
these targets, the output (in `label` format) will appear
to contain a duplicate. When using the `label_kind` (see
below) format, the distinction becomes clear: the two targets have
the same name, but one has kind `sh_binary rule` and the
other kind `source file`.

### Print the label and kind of each target {:#print-target-label}

```
--output label_kind
```

Like `label`, this output format prints the labels of
each target in the resulting graph, in topological order, but it
additionally precedes the label by the [_kind_](#kind) of the target.

### Print targets in protocol buffer format {:#print-target-proto}

```
--output proto
```

Prints the query output as a
[`QueryResult`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffer.

### Print targets in length-delimited protocol buffer format {:#print-target-length-delimited-proto}

```
--output streamed_proto
```

Prints a
[length-delimited](https://protobuf.dev/programming-guides/encoding/#size-limit)
stream of
[`Target`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffers. This is useful to _(i)_ get around
[size limitations](https://protobuf.dev/programming-guides/encoding/#size-limit)
of protocol buffers when there are too many targets to fit in a single
`QueryResult` or _(ii)_ to start processing while Bazel is still outputting.

### Print targets in text proto format {:#print-target-textproto}

```
--output textproto
```

Similar to `--output proto`, prints the
[`QueryResult`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffer but in
[text format](https://protobuf.dev/reference/protobuf/textformat-spec/).

### Print targets in ndjson format {:#print-target-streamed-jsonproto}

```
--output streamed_jsonproto
```

Similar to `--output streamed_proto`, prints a stream of
[`Target`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffers but in [ndjson](https://github.com/ndjson/ndjson-spec) format.

### Print the label of each target, in rank order {:#print-target-label-rank-order}

```
--output minrank --output maxrank
```

Like `label`, the `minrank`
and `maxrank` output formats print the labels of each
target in the resulting graph, but instead of appearing in
topological order, they appear in rank order, preceded by their
rank number. These are unaffected by the result ordering
`--[no]order_results` flag (see [notes on
the ordering of results](#result-order)).

There are two variants of this format: `minrank` ranks
each node by the length of the shortest path from a root node to it.
"Root" nodes (those which have no incoming edges) are of rank 0,
their successors are of rank 1, etc. (As always, edges point from a
target to its prerequisites: the targets it depends upon.)

`maxrank` ranks each node by the length of the longest
path from a root node to it. Again, "roots" have rank 0, all other
nodes have a rank which is one greater than the maximum rank of all
their predecessors.

All nodes in a cycle are considered of equal rank. (Most graphs are
acyclic, but cycles do occur
simply because `BUILD` files contain erroneous cycles.)

These output formats are useful for discovering how deep a graph is.
If used for the result of a `deps(x)`, `rdeps(x)`,
or `allpaths` query, then the rank number is equal to the
length of the shortest (with `minrank`) or longest
(with `maxrank`) path from `x` to a node in
that rank. `maxrank` can be used to determine the
longest sequence of build steps required to build a target.

Note: The ranked output of a `somepath` query is
basically meaningless because `somepath` doesn't
guarantee to return either a shortest or a longest path, and it may
include "transitive" edges from one path node to another that are
not direct edges in original graph.

For example, the graph on the left yields the outputs on the right
when `--output minrank` and `--output maxrank`
are specified, respectively.

<table>
  <tr>
    <td><img src="/docs/images/out-ranked.svg" alt="Out ranked">
    </td>
    <td>
      <pre>
      minrank

      0 //c:c
      1 //b:b
      1 //a:a
      2 //b:b.cc
      2 //a:a.cc
      </pre>
    </td>
    <td>
      <pre>
      maxrank

      0 //c:c
      1 //b:b
      2 //a:a
      2 //b:b.cc
      3 //a:a.cc
      </pre>
    </td>
  </tr>
</table>

### Print the location of each target {:#print-target-location}

```
--output location
```

Like `label_kind`, this option prints out, for each
target in the result, the target's kind and label, but it is
prefixed by a string describing the location of that target, as a
filename and line number. The format resembles the output of
`grep`. Thus, tools that can parse the latter (such as Emacs
or vi) can also use the query output to step through a series of
matches, allowing the Bazel query tool to be used as a
dependency-graph-aware "grep for BUILD files".

The location information varies by target kind (see the [kind](#kind) operator). For rules, the
location of the rule's declaration within the `BUILD` file is printed.
For source files, the location of line 1 of the actual file is
printed. For a generated file, the location of the rule that
generates it is printed. (The query tool does not have sufficient
information to find the actual location of the generated file, and
in any case, it might not exist if a build has not yet been performed.)

### Print the set of packages {:#print-package-set}

```--output package```

This option prints the name of all packages to which
some target in the result set belongs. The names are printed in
lexicographical order; duplicates are excluded. Formally, this
is a _projection_ from the set of labels (package, target) onto
packages.

Packages in external repositories are formatted as
`@repo//foo/bar` while packages in the main repository are
formatted as `foo/bar`.

In conjunction with the `deps(...)` query, this output
option can be used to find the set of packages that must be checked
out in order to build a given set of targets.

### Display a graph of the result {:#display-result-graph}

```--output graph```

This option causes the query result to be printed as a directed
graph in the popular AT&amp;T GraphViz format. Typically the
result is saved to a file, such as `.png` or `.svg`.
(If the `dot` program is not installed on your workstation, you
can install it using the command `sudo apt-get install graphviz`.)
See the example section below for a sample invocation.

This output format is particularly useful for `allpaths`,
`deps`, or `rdeps` queries, where the result
includes a _set of paths_ that cannot be easily visualized when
rendered in a linear form, such as with `--output label`.

By default, the graph is rendered in a _factored_ form. That is,
topologically-equivalent nodes are merged together into a single
node with multiple labels. This makes the graph more compact
and readable, because typical result graphs contain highly
repetitive patterns. For example, a `java_library` rule
may depend on hundreds of Java source files all generated by the
same `genrule`; in the factored graph, all these files
are represented by a single node. This behavior may be disabled
with the `--nograph:factored` option.

#### `--graph:node_limit {{ '<var>' }}n{{ '</var>' }}` {:#graph-nodelimit}

The option specifies the maximum length of the label string for a
graph node in the output. Longer labels will be truncated; -1
disables truncation. Due to the factored form in which graphs are
usually printed, the node labels may be very long. GraphViz cannot
handle labels exceeding 1024 characters, which is the default value
of this option. This option has no effect unless
`--output=graph` is being used.

#### `--[no]graph:factored` {:#graph-factored}

By default, graphs are displayed in factored form, as explained
[above](#output-graph).
When `--nograph:factored` is specified, graphs are
printed without factoring. This makes visualization using GraphViz
impractical, but the simpler format may ease processing by other
tools (such as grep). This option has no effect
unless `--output=graph` is being used.

### XML {:#xml}

```--output xml```

This option causes the resulting targets to be printed in an XML
form. The output starts with an XML header such as this

```
  <?xml version="1.0" encoding="UTF-8"?>
  <query version="2">
```

<!-- The docs should continue to document version 2 into perpetuity,
     even if we add new formats, to handle clients synced to old CLs. -->

and then continues with an XML element for each target
in the result graph, in topological order (unless
[unordered results](#result-order) are requested),
and then finishes with a terminating

```
</query>
```

Simple entries are emitted for targets of `file` kind:

```
  <source-file name='//foo:foo_main.cc' .../>
  <generated-file name='//foo:libfoo.so' .../>
```

But for rules, the XML is structured and contains definitions of all
the attributes of the rule, including those whose value was not
explicitly specified in the rule's `BUILD` file.

Additionally, the result includes `rule-input` and
`rule-output` elements so that the topology of the
dependency graph can be reconstructed without having to know that,
for example, the elements of the `srcs` attribute are
forward dependencies (prerequisites) and the contents of the
`outs` attribute are backward dependencies (consumers).

`rule-input` elements for [implicit dependencies](#implicit_deps) are suppressed if
`--noimplicit_deps` is specified.

```
  <rule class='cc_binary rule' name='//foo:foo' ...>
    <list name='srcs'>
      <label value='//foo:foo_main.cc'/>
      <label value='//foo:bar.cc'/>
      ...
    </list>
    <list name='deps'>
      <label value='//common:common'/>
      <label value='//collections:collections'/>
      ...
    </list>
    <list name='data'>
      ...
    </list>
    <int name='linkstatic' value='0'/>
    <int name='linkshared' value='0'/>
    <list name='licenses'/>
    <list name='distribs'>
      <distribution value="INTERNAL" />
    </list>
    <rule-input name="//common:common" />
    <rule-input name="//collections:collections" />
    <rule-input name="//foo:foo_main.cc" />
    <rule-input name="//foo:bar.cc" />
    ...
  </rule>
```

Every XML element for a target contains a `name`
attribute, whose value is the target's label, and
a `location` attribute, whose value is the target's
location as printed by the [`--output location`](#print-target-location).

#### `--[no]xml:line_numbers` {:#xml-linenumbers}

By default, the locations displayed in the XML output contain line numbers.
When `--noxml:line_numbers` is specified, line numbers are not printed.

#### `--[no]xml:default_values` {:#xml-defaultvalues}

By default, XML output does not include rule attribute whose value
is the default value for that kind of attribute (for example, if it
were not specified in the `BUILD` file, or the default value was
provided explicitly). This option causes such attribute values to
be included in the XML output.

### Regular expressions {:#regular-expressions}

Regular expressions in the query language use the Java regex library, so you can use the
full syntax for
[`java.util.regex.Pattern`](https://docs.oracle.com/javase/8/docs/api/java/util/regex/Pattern.html){: .external}.

### Querying with external repositories {:#querying-external-repositories}

If the build depends on rules from [external repositories](/external/overview)
then query results will include these dependencies. For
example, if `//foo:bar` depends on `@other-repo//baz:lib`, then
`bazel query 'deps(//foo:bar)'` will list `@other-repo//baz:lib` as a
dependency.


Project: /_project.yaml
Book: /_book.yaml

#  Configurable Query (cquery)

{% include "_buttons.html" %}

`cquery` is a variant of [`query`](/query/language) that correctly handles
[`select()`](/docs/configurable-attributes) and build options' effects on the build
graph.

It achieves this by running over the results of Bazel's [analysis
phase](/extending/concepts#evaluation-model),
which integrates these effects. `query`, by contrast, runs over the results of
Bazel's loading phase, before options are evaluated.

For example:

<pre>
$ cat > tree/BUILD &lt;&lt;EOF
sh_library(
    name = "ash",
    deps = select({
        ":excelsior": [":manna-ash"],
        ":americana": [":white-ash"],
        "//conditions:default": [":common-ash"],
    }),
)
sh_library(name = "manna-ash")
sh_library(name = "white-ash")
sh_library(name = "common-ash")
config_setting(
    name = "excelsior",
    values = {"define": "species=excelsior"},
)
config_setting(
    name = "americana",
    values = {"define": "species=americana"},
)
EOF
</pre>

<pre>
# Traditional query: query doesn't know which select() branch you will choose,
# so it conservatively lists all of possible choices, including all used config_settings.
$ bazel query "deps(//tree:ash)" --noimplicit_deps
//tree:americana
//tree:ash
//tree:common-ash
//tree:excelsior
//tree:manna-ash
//tree:white-ash

# cquery: cquery lets you set build options at the command line and chooses
# the exact dependencies that implies (and also the config_setting targets).
$ bazel cquery "deps(//tree:ash)" --define species=excelsior --noimplicit_deps
//tree:ash (9f87702)
//tree:manna-ash (9f87702)
//tree:americana (9f87702)
//tree:excelsior (9f87702)
</pre>

Each result includes a [unique identifier](#configurations) `(9f87702)` of
the [configuration](/reference/glossary#configuration) the
target is built with.

Since `cquery` runs over the configured target graph. it doesn't have insight
into artifacts like build actions nor access to [`test_suite`](/reference/be/general#test_suite)
rules as they are not configured targets. For the former, see [`aquery`](/query/aquery).

## Basic syntax {:#basic-syntax}

A simple `cquery` call looks like:

`bazel cquery "function(//target)"`

The query expression `"function(//target)"` consists of the following:

*   **`function(...)`** is the function to run on the target. `cquery`
    supports most
    of `query`'s [functions](/query/language#functions), plus a
    few new ones.
*   **`//target`** is the expression fed to the function. In this example, the
    expression is a simple target. But the query language also allows nesting of functions.
    See the [Query guide](/query/guide) for examples.


`cquery` requires a target to run through the [loading and analysis](/extending/concepts#evaluation-model)
phases. Unless otherwise specified, `cquery` parses the target(s) listed in the
query expression. See [`--universe_scope`](#universe-scope)
for querying dependencies of top-level build targets.

## Configurations {:#configurations}

The line:

<pre>
//tree:ash (9f87702)
</pre>

means `//tree:ash` was built in a configuration with ID `9f87702`. For most
targets, this is an opaque hash of the build option values defining the
configuration.

To see the configuration's complete contents, run:

<pre>
$ bazel config 9f87702
</pre>

`9f87702` is a prefix of the complete ID. This is because complete IDs are
SHA-256 hashes, which are long and hard to follow. `cquery` understands any valid
prefix of a complete ID, similar to
[Git short hashes](https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection#_revision_selection){: .external}.
 To see complete IDs, run `$ bazel config`.

## Target pattern evaluation {:#target-pattern-evaluation}

`//foo` has a different meaning for `cquery` than for `query`. This is because
`cquery` evaluates _configured_ targets and the build graph may have multiple
configured versions of `//foo`.

For `cquery`, a target pattern in the query expression evaluates
to every configured target with a label that matches that pattern. Output is
deterministic, but `cquery` makes no ordering guarantee beyond the
[core query ordering contract](/query/language#graph-order).

This produces subtler results for query expressions than with `query`.
For example, the following can produce multiple results:

<pre>
# Analyzes //foo in the target configuration, but also analyzes
# //genrule_with_foo_as_tool which depends on an exec-configured
# //foo. So there are two configured target instances of //foo in
# the build graph.
$ bazel cquery //foo --universe_scope=//foo,//genrule_with_foo_as_tool
//foo (9f87702)
//foo (exec)
</pre>

If you want to precisely declare which instance to query over, use
the [`config`](#config) function.

See `query`'s [target pattern
documentation](/query/language#target-patterns) for more information on target patterns.

## Functions {:#functions}

Of the [set of functions](/query/language#functions "list of query functions")
supported by `query`, `cquery` supports all but
[`allrdeps`](/query/language#allrdeps),
[`buildfiles`](/query/language#buildfiles),
[`rbuildfiles`](/query/language#rbuildfiles),
[`siblings`](/query/language#siblings), [`tests`](/query/language#tests), and
[`visible`](/query/language#visible).

`cquery` also introduces the following new functions:

### config {:#config}

`expr ::= config(expr, word)`

The `config` operator attempts to find the configured target for
the label denoted by the first argument and configuration specified by the
second argument.

Valid values for the second argument are `null` or a
[custom configuration hash](#configurations). Hashes can be retrieved from `$
bazel config` or a previous `cquery`'s output.

Examples:

<pre>
$ bazel cquery "config(//bar, 3732cc8)" --universe_scope=//foo
</pre>

<pre>
$ bazel cquery "deps(//foo)"
//bar (exec)
//baz (exec)

$ bazel cquery "config(//baz, 3732cc8)"
</pre>

If not all results of the first argument can be found in the specified
configuration, only those that can be found are returned. If no results
can be found in the specified configuration, the query fails.

## Options {:#options}

### Build options {:#build-options}

`cquery` runs over a regular Bazel build and thus inherits the set of
[options](/reference/command-line-reference#build-options) available during a build.

###  Using cquery options {:#using-cquery-options}

#### `--universe_scope` (comma-separated list) {:#universe-scope}

Often, the dependencies of configured targets go through
[transitions](/extending/rules#configurations),
which causes their configuration to differ from their dependent. This flag
allows you to query a target as if it were built as a dependency or a transitive
dependency of another target. For example:

<pre>
# x/BUILD
genrule(
     name = "my_gen",
     srcs = ["x.in"],
     outs = ["x.cc"],
     cmd = "$(locations :tool) $&lt; >$@",
     tools = [":tool"],
)
cc_binary(
    name = "tool",
    srcs = ["tool.cpp"],
)
</pre>

Genrules configure their tools in the
[exec configuration](/extending/rules#configurations)
so the following queries would produce the following outputs:

<table class="table table-condensed table-bordered table-params">
  <thead>
    <tr>
      <th>Query</th>
      <th>Target Built</th>
      <th>Output</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>bazel cquery "//x:tool"</td>
      <td>//x:tool</td>
      <td>//x:tool(targetconfig)</td>
    </tr>
    <tr>
      <td>bazel cquery "//x:tool" --universe_scope="//x:my_gen"</td>
      <td>//x:my_gen</td>
      <td>//x:tool(execconfig)</td>
    </tr>
  </tbody>
</table>

If this flag is set, its contents are built. _If it's not set, all targets
mentioned in the query expression are built_ instead. The transitive closure of the
built targets are used as the universe of the query. Either way, the targets to
be built must be buildable at the top level (that is, compatible with top-level
options). `cquery` returns results in the transitive closure of these
top-level targets.

Even if it's possible to build all targets in a query expression at the top
level, it may be beneficial to not do so. For example, explicitly setting
`--universe_scope` could prevent building targets multiple times in
configurations you don't care about. It could also help specify which configuration version of a
target you're looking for (since it's not currently possible
to fully specify this any other way). You should set this flag
if your query expression is more complex than `deps(//foo)`.

#### `--implicit_deps` (boolean, default=True) {:#implicit-deps}

Setting this flag to false filters out all results that aren't explicitly set in
the BUILD file and instead set elsewhere by Bazel. This includes filtering resolved
toolchains.

#### `--tool_deps` (boolean, default=True) {:#tool-deps}

Setting this flag to false filters out all configured targets for which the
path from the queried target to them crosses a transition between the target
configuration and the
[non-target configurations](/extending/rules#configurations).
If the queried target is in the target configuration, setting `--notool_deps` will
only return targets that also are in the target configuration. If the queried
target is in a non-target configuration, setting `--notool_deps` will only return
targets also in non-target configurations. This setting generally does not affect filtering
of resolved toolchains.

#### `--include_aspects` (boolean, default=True) {:#include-aspects}

Include dependencies added by [aspects](/extending/aspects).

If this flag is disabled, `cquery somepath(X, Y)` and
`cquery deps(X) | grep 'Y'` omit Y if X only depends on it through an aspect.

## Output formats {:#output-formats}

By default, cquery outputs results in a dependency-ordered list of label and configuration pairs.
There are other options for exposing the results as well.

### Transitions {:#transitions}

<pre>
--transitions=lite
--transitions=full
</pre>

Configuration [transitions](/extending/rules#configurations)
are used to build targets underneath the top level targets in different
configurations than the top level targets.

For example, a target might impose a transition to the exec configuration on all
dependencies in its `tools` attribute. These are known as attribute
transitions. Rules can also impose transitions on their own configurations,
known as rule class transitions. This output format outputs information about
these transitions such as what type they are and the effect they have on build
options.

This output format is triggered by the `--transitions` flag which by default is
set to `NONE`. It can be set to `FULL` or `LITE` mode. `FULL` mode outputs
information about rule class transitions and attribute transitions including a
detailed diff of the options before and after the transition. `LITE` mode
outputs the same information without the options diff.

### Protocol message output {:#protocol-message-output}

<pre>
--output=proto
</pre>

This option causes the resulting targets to be printed in a binary protocol
buffer form. The definition of the protocol buffer can be found at
[src/main/protobuf/analysis_v2.proto](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/analysis_v2.proto){: .external}.

`CqueryResult` is the top level message containing the results of the cquery. It
has a list of `ConfiguredTarget` messages and a list of `Configuration`
messages. Each `ConfiguredTarget` has a `configuration_id` whose value is equal
to that of the `id` field from the corresponding `Configuration` message.

#### --[no]proto:include_configurations {:#proto-include-configurations}

By default, cquery results return configuration information as part of each
configured target. If you'd like to omit this information and get proto output
that is formatted exactly like query's proto output, set this flag to false.

See [query's proto output documentation](/query/language#output-formats)
for more proto output-related options.

Note: While selects are resolved both at the top level of returned
targets and within attributes, all possible inputs for selects are still
included as `rule_input` fields.

### Graph output {:#graph-output}

<pre>
--output=graph
</pre>

This option generates output as a Graphviz-compatible .dot file. See `query`'s
[graph output documentation](/query/language#display-result-graph) for details. `cquery`
also supports [`--graph:node_limit`](/query/language#graph-nodelimit) and
[`--graph:factored`](/query/language#graph-factored).

### Files output {:#files-output}

<pre>
--output=files
</pre>

This option prints a list of the output files produced by each target matched
by the query similar to the list printed at the end of a `bazel build`
invocation. The output contains only the files advertised in the requested
output groups as determined by the
[`--output_groups`](/reference/command-line-reference#flag--output_groups) flag.
It does include source files.

All paths emitted by this output format are relative to the
[execroot](https://bazel.build/remote/output-directories), which can be obtained
via `bazel info execution_root`. If the `bazel-out` convenience symlink exists,
paths to files in the main repository also resolve relative to the workspace
directory.

Note: The output of `bazel cquery --output=files //pkg:foo` contains the output
files of `//pkg:foo` in *all* configurations that occur in the build (also see
the [section on target pattern evaluation](#target-pattern-evaluation)). If that
is not desired, wrap you query in [`config(..., target)`](#config).

### Defining the output format using Starlark {:#output-format-definition}

<pre>
--output=starlark
</pre>

This output format calls a [Starlark](/rules/language)
function for each configured target in the query result, and prints the value
returned by the call. The `--starlark:file` flag specifies the location of a
Starlark file that defines a function named `format` with a single parameter,
`target`. This function is called for each [Target](/rules/lib/builtins/Target)
in the query result. Alternatively, for convenience, you may specify just the
body of a function declared as `def format(target): return expr` by using the
`--starlark:expr` flag.

#### 'cquery' Starlark dialect {:#cquery-starlark}

The cquery Starlark environment differs from a BUILD or .bzl file. It includes
all core Starlark
[built-in constants and functions](https://github.com/bazelbuild/starlark/blob/master/spec.md#built-in-constants-and-functions){: .external},
plus a few cquery-specific ones described below, but not (for example) `glob`,
`native`, or `rule`, and it does not support load statements.

##### build_options(target) {:#build-options}

`build_options(target)` returns a map whose keys are build option identifiers (see
[Configurations](/extending/config))
and whose values are their Starlark values. Build options whose values are not legal Starlark
values are omitted from this map.

If the target is an input file, `build_options(target)` returns None, as input file
targets have a null configuration.

##### providers(target) {:#providers}

`providers(target)` returns a map whose keys are names of
[providers](/extending/rules#providers)
(for example, `"DefaultInfo"`) and whose values are their Starlark values. Providers
whose values are not legal Starlark values are omitted from this map.

#### Examples {:#output-format-definition-examples}

Print a space-separated list of the base names of all files produced by `//foo`:

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="' '.join([f.basename for f in target.files.to_list()])"
</pre>

Print a space-separated list of the paths of all files produced by **rule** targets in
`//bar` and its subpackages:

<pre>
  bazel cquery 'kind(rule, //bar/...)' --output=starlark \
    --starlark:expr="' '.join([f.path for f in target.files.to_list()])"
</pre>

Print a list of the mnemonics of all actions registered by `//foo`.

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="[a.mnemonic for a in target.actions]"
</pre>

Print a list of compilation outputs registered by a `cc_library` `//baz`.

<pre>
  bazel cquery //baz --output=starlark \
    --starlark:expr="[f.path for f in target.output_groups.compilation_outputs.to_list()]"
</pre>

Print the value of the command line option `--javacopt` when building `//foo`.

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="build_options(target)['//command_line_option:javacopt']"
</pre>

Print the label of each target with exactly one output. This example uses
Starlark functions defined in a file.

<pre>
  $ cat example.cquery

  def has_one_output(target):
    return len(target.files.to_list()) == 1

  def format(target):
    if has_one_output(target):
      return target.label
    else:
      return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

Print the label of each target which is strictly Python 3. This example uses
Starlark functions defined in a file.

<pre>
  $ cat example.cquery

  def format(target):
    p = providers(target)
    py_info = p.get("PyInfo")
    if py_info and py_info.has_py3_only_sources:
      return target.label
    else:
      return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

Extract a value from a user defined Provider.

<pre>
  $ cat some_package/my_rule.bzl

  MyRuleInfo = provider(fields={"color": "the name of a color"})

  def _my_rule_impl(ctx):
      ...
      return [MyRuleInfo(color="red")]

  my_rule = rule(
      implementation = _my_rule_impl,
      attrs = {...},
  )

  $ cat example.cquery

  def format(target):
    p = providers(target)
    my_rule_info = p.get("//some_package:my_rule.bzl%MyRuleInfo'")
    if my_rule_info:
      return my_rule_info.color
    return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

## cquery vs. query {:#cquery-vs-query}

`cquery` and `query` complement each other and excel in
different niches. Consider the following to decide which is right for you:

*  `cquery` follows specific `select()` branches to
    model the exact graph you build. `query` doesn't know which
    branch the build chooses, so overapproximates by including all branches.
*   `cquery`'s precision requires building more of the graph than
    `query` does. Specifically, `cquery`
    evaluates _configured targets_ while `query` only
    evaluates _targets_. This takes more time and uses more memory.
*   `cquery`'s interpretation of
    the [query language](/query/language) introduces ambiguity
    that `query` avoids. For example,
    if `"//foo"` exists in two configurations, which one
    should `cquery "deps(//foo)"` use?
    The [`config`](#config) function can help with this.
*   As a newer tool, `cquery` lacks support for certain use
    cases. See [Known issues](#known-issues) for details.

## Known issues {:#known-issues}

**All targets that `cquery` "builds" must have the same configuration.**

Before evaluating queries, `cquery` triggers a build up to just
before the point where build actions would execute. The targets it
"builds" are by default selected from all labels that appear in the query
expression (this can be overridden
with [`--universe_scope`](#universe-scope)). These
must have the same configuration.

While these generally share the top-level "target" configuration,
rules can change their own configuration with
[incoming edge transitions](/extending/config#incoming-edge-transitions).
This is where `cquery` falls short.

Workaround: If possible, set `--universe_scope` to a stricter
scope. For example:

<pre>
# This command attempts to build the transitive closures of both //foo and
# //bar. //bar uses an incoming edge transition to change its --cpu flag.
$ bazel cquery 'somepath(//foo, //bar)'
ERROR: Error doing post analysis query: Top-level targets //foo and //bar
have different configurations (top-level targets with different
configurations is not supported)

# This command only builds the transitive closure of //foo, under which
# //bar should exist in the correct configuration.
$ bazel cquery 'somepath(//foo, //bar)' --universe_scope=//foo
</pre>

**No support for [`--output=xml`](/query/language#xml).**

**Non-deterministic output.**

`cquery` does not automatically wipe the build graph from
previous commands and is therefore prone to picking up results from past
queries. For example, `genrule` exerts an exec transition on
its `tools` attribute - that is, it configures its tools in the
[exec configuration](/extending/rules#configurations).

You can see the lingering effects of that transition below.

<pre>
$ cat > foo/BUILD &lt;&lt;&lt;EOF
genrule(
    name = "my_gen",
    srcs = ["x.in"],
    outs = ["x.cc"],
    cmd = "$(locations :tool) $&lt; >$@",
    tools = [":tool"],
)
cc_library(
    name = "tool",
)
EOF

    $ bazel cquery "//foo:tool"
tool(target_config)

    $ bazel cquery "deps(//foo:my_gen)"
my_gen (target_config)
tool (exec_config)
...

    $ bazel cquery "//foo:tool"
tool(exec_config)
</pre>

Workaround: change any startup option to force re-analysis of configured targets.
For example, add `--test_arg=<whatever>` to your build command.

## Troubleshooting {:#troubleshooting}

### Recursive target patterns (`/...`) {:#recursive-target-patterns}

If you encounter:

<pre>
$ bazel cquery --universe_scope=//foo:app "somepath(//foo:app, //foo/...)"
ERROR: Error doing post analysis query: Evaluation failed: Unable to load package '[foo]'
because package is not in scope. Check that all target patterns in query expression are within the
--universe_scope of this query.
</pre>

this incorrectly suggests package `//foo` isn't in scope even though
`--universe_scope=//foo:app` includes it. This is due to design limitations in
`cquery`. As a workaround, explicitly include `//foo/...` in the universe
scope:

<pre>
$ bazel cquery --universe_scope=//foo:app,//foo/... "somepath(//foo:app, //foo/...)"
</pre>

If that doesn't work (for example, because some target in `//foo/...` can't
build with the chosen build flags), manually unwrap the pattern into its
constituent packages with a pre-processing query:

<pre>
# Replace "//foo/..." with a subshell query call (not cquery!) outputting each package, piped into
# a sed call converting "&lt;pkg&gt;" to "//&lt;pkg&gt;:*", piped into a "+"-delimited line merge.
# Output looks like "//foo:*+//foo/bar:*+//foo/baz".
#
$  bazel cquery --universe_scope=//foo:app "somepath(//foo:app, $(bazel query //foo/...
--output=package | sed -e 's/^/\/\//' -e 's/$/:*/' | paste -sd "+" -))"
</pre>


Project: /_project.yaml
Book: /_book.yaml

# Query quickstart

{% include "_buttons.html" %}

This tutorial covers how to work with Bazel to trace dependencies in your code using a premade Bazel project.

For language and `--output` flag details, see the [Bazel query reference](/query/language) and [Bazel cquery reference](/query/cquery) manuals. Get help in your IDE by typing `bazel help query` or `bazel help cquery` on the command line.

## Objective

This guide runs you through a set of basic queries you can use to learn more about your project's file dependencies. It is intended for new Bazel developers with a basic knowledge of how Bazel and `BUILD` files work.


## Prerequisites

Start by installing [Bazel](https://bazel.build/install), if you haven’t already. This tutorial uses Git for source control, so for best results, install [Git](https://github.com/git-guides/install-git) as well.

To visualize dependency graphs, the tool called Graphviz is used, which you can [download](https://graphviz.org/download/) in order to follow along.

### Get the sample project

Next, retrieve the sample app from [Bazel's Examples repository](https://github.com/bazelbuild/examples) by running the following in your command-line tool of choice:

```posix-terminal
git clone https://github.com/bazelbuild/examples.git
```

The sample project for this tutorial is in the `examples/query-quickstart` directory.

## Getting started

### What are Bazel queries?

Queries help you to learn about a Bazel codebase by analyzing the relationships between `BUILD` files and examining the resulting output for useful information. This guide previews some basic query functions, but for more options see the [query guide](https://bazel.build/query/guide). Queries help you learn about dependencies in large scale projects without manually navigating through `BUILD` files.

To run a query, open your command line terminal and enter:

```posix-terminal
bazel query 'query_function'
```

### Scenario

Imagine a scenario that delves into the relationship between Cafe Bazel and its respective chef. This Cafe exclusively sells pizza and mac & cheese. Take a look below at how the project is structured:

```
bazelqueryguide
├── BUILD
├── src
│   └── main
│       └── java
│           └── com
│               └── example
│                   ├── customers
│                   │   ├── Jenny.java
│                   │   ├── Amir.java
│                   │   └── BUILD
│                   ├── dishes
│                   │   ├── Pizza.java
│                   │   ├── MacAndCheese.java
│                   │   └── BUILD
│                   ├── ingredients
│                   │   ├── Cheese.java
│                   │   ├── Tomatoes.java
│                   │   ├── Dough.java
│                   │   ├── Macaroni.java
│                   │   └── BUILD
│                   ├── restaurant
│                   │   ├── Cafe.java
│                   │   ├── Chef.java
│                   │   └── BUILD
│                   ├── reviews
│                   │   ├── Review.java
│                   │   └── BUILD
│                   └── Runner.java
└── MODULE.bazel
```

Throughout this tutorial, unless directed otherwise, try not to look in the `BUILD` files to find the information you need and instead solely use the query function.

A project consists of different packages that make up a Cafe. They are separated into: `restaurant`, `ingredients`, `dishes`, `customers`, and `reviews`. Rules within these packages define different components of the Cafe with various tags and dependencies.

### Running a build

This project contains a main method inside of `Runner.java` that you can execute
to print out a menu of the Cafe. Build the project using Bazel with the command
`bazel build` and use `:` to signal that the target is named `runner`. See
[target names](https://bazel.build/concepts/labels#target-names) to learn how to
reference targets.

To build this project, paste this command into a terminal:

```posix-terminal
bazel build :runner
```

Your output should look something like this if the build is successful.

```bash
INFO: Analyzed target //:runner (49 packages loaded, 784 targets configured).
INFO: Found 1 target...
Target //:runner up-to-date:
  bazel-bin/runner.jar
  bazel-bin/runner
INFO: Elapsed time: 16.593s, Critical Path: 4.32s
INFO: 23 processes: 4 internal, 10 darwin-sandbox, 9 worker.
INFO: Build completed successfully, 23 total actions
```

After it has built successfully, run the application by pasting this command:

```posix-terminal
bazel-bin/runner
```

```bash
--------------------- MENU -------------------------

Pizza - Cheesy Delicious Goodness
Macaroni & Cheese - Kid-approved Dinner

----------------------------------------------------
```
This leaves you with a list of the menu items given along with a short description.

## Exploring targets

The project lists ingredients and dishes in their own packages. To use a query to view the rules of a package, run the command <code>bazel query <em>package</em>/…</code>

In this case, you can use this to look through the ingredients and dishes that this Cafe has by running:

```posix-terminal
bazel query //src/main/java/com/example/dishes/...
```

```posix-terminal
bazel query //src/main/java/com/example/ingredients/...
```

If you query for the targets of the ingredients package, the output should look like:

```bash
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/ingredients:dough
//src/main/java/com/example/ingredients:macaroni
//src/main/java/com/example/ingredients:tomato
```

## Finding dependencies

What targets does your runner rely on to run?

Say you want to dive deeper into the structure of your project without prodding into the filesystem (which may be untenable for large projects). What rules does Cafe Bazel use?

If, like in this example, the target for your runner is `runner`, discover the underlying dependencies of the target by running the command:

```posix-terminal
bazel query --noimplicit_deps "deps(target)"
```

```posix-terminal
bazel query --noimplicit_deps "deps(:runner)"
```

```bash
//:runner
//:src/main/java/com/example/Runner.java
//src/main/java/com/example/dishes:MacAndCheese.java
//src/main/java/com/example/dishes:Pizza.java
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:Cheese.java
//src/main/java/com/example/ingredients:Dough.java
//src/main/java/com/example/ingredients:Macaroni.java
//src/main/java/com/example/ingredients:Tomato.java
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/ingredients:dough
//src/main/java/com/example/ingredients:macaroni
//src/main/java/com/example/ingredients:tomato
//src/main/java/com/example/restaurant:Cafe.java
//src/main/java/com/example/restaurant:Chef.java
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```
Note: Adding the flag `--noimplicit_deps` removes configurations and potential toolchains to simplify the list. When you omit this flag, Bazel returns implicit dependencies not specified in the `BUILD` file and clutters the output.

In most cases, use the query function `deps()` to see individual output dependencies of a specific target.

## Visualizing the dependency graph (optional)

Note: This section uses Graphviz, so make sure to [download Graphviz](https://graphviz.org/download/) to follow along.

The section describes how you can visualize the dependency paths for a specific query. [Graphviz](https://graphviz.org/) helps to see the path as a directed acyclic graph image as opposed to a flattened list. You can alter the display of the Bazel query graph by using various `--output` command line options. See [Output Formats](https://bazel.build/query/language#output-formats) for options.

Start by running your desired query and add the flag `--noimplicit_deps` to remove excessive tool dependencies. Then, follow the query with the output flag and store the graph into a file called `graph.in` to create a text representation of the graph.

To search for all dependencies of the target `:runner` and format the output as a graph:

```posix-terminal
bazel query --noimplicit_deps 'deps(:runner)' --output graph > graph.in
```
This creates a file called `graph.in`, which is a text representation of the build graph. Graphviz uses <code>[dot](https://graphviz.org/docs/layouts/dot/) </code>– a tool that processes text into a visualization —  to create a png:

```posix-terminal
dot -Tpng < graph.in > graph.png
```
If you open up `graph.png`, you should see something like this. The graph below has been simplified to make the essential path details clearer in this guide.

![Diagram showing a relationship from cafe to chef to the dishes: pizza and mac and cheese which diverges into the separate ingredients: cheese, tomatoes, dough, and macaroni.](images/query_graph1.png "Dependency graph")

This helps when you want to see the outputs of the different query functions throughout this guide.

## Finding reverse dependencies

If instead you have a target you’d like to analyze what other targets use it, you can use a query to examine what targets depend on a certain rule. This is called a “reverse dependency”. Using `rdeps()` can be useful when editing a file in a codebase that you’re unfamiliar with, and can save you from unknowingly breaking other files which depended on it.

For instance, you want to make some edits to the ingredient `cheese`. To avoid causing an issue for Cafe Bazel, you need to check what dishes rely on `cheese`.

Caution: Since `ingredients` is its own package, you must use a different naming convention for the target `cheese` in the form of `//package:target`. Read more about referencing targets, or [Labels](https://bazel.build/concepts/labels).

To see what targets depend on a particular target/package, you can use `rdeps(universe_scope, target)`. The `rdeps()` query function takes in at least two arguments: a `universe_scope` — the relevant directory — and a `target`. Bazel searches for the target’s reverse dependencies within the `universe_scope` provided. The `rdeps()` operator accepts an optional third argument: an integer literal specifying the upper bound on the depth of the search.

Tip: To search within the whole scope of the project, set the `universe_scope` to `//...`

To look for reverse dependencies of the target `cheese` within the scope of the entire project ‘//…’ run the command:

```posix-terminal
bazel query "rdeps(universe_scope, target)"
```
```
ex) bazel query "rdeps(//... , //src/main/java/com/example/ingredients:cheese)"
```
```bash
//:runner
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```
The query return shows that cheese is relied on by both pizza and macAndCheese. What a surprise!

## Finding targets based on tags

Two customers walk into Bazel Cafe: Amir and Jenny. There is nothing known about them except for their names. Luckily, they have their orders tagged in the 'customers' `BUILD` file. How can you access this tag?

Developers can tag Bazel targets with different identifiers, often for testing purposes. For instance, tags on tests can annotate a test's role in your debug and release process, especially for C++ and Python tests, which lack any runtime annotation ability. Using tags and size elements gives flexibility in assembling suites of tests based around a codebase’s check-in policy.

In this example, the tags are either one of `pizza` or `macAndCheese` to represent the menu items. This command queries for targets that have tags matching your identifier within a certain package.

```
bazel query 'attr(tags, "pizza", //src/main/java/com/example/customers/...)'
```
This query returns all of the targets in the 'customers' package that have a tag of "pizza".

### Test yourself

Use this query to learn what Jenny wants to order.

<div>
  <devsite-expandable>
  <h4 class="showalways">Answer</h4>
  <p>Mac and Cheese</p>
  </devsite-expandable>
</div>


## Adding a new dependency

Cafe Bazel has expanded its menu — customers can now order a Smoothie! This specific smoothie consists of the ingredients `Strawberry` and `Banana`.

First, add the ingredients that the smoothie depends on: `Strawberry.java` and `Banana.java`. Add the empty Java classes.

**`src/main/java/com/example/ingredients/Strawberry.java`**

```java
package com.example.ingredients;

public class Strawberry {

}
```

**`src/main/java/com/example/ingredients/Banana.java`**

```java
package com.example.ingredients;

public class Banana {

}
```

Next, add `Smoothie.java` to the appropriate directory: `dishes`.

**`src/main/java/com/example/dishes/Smoothie.java`**

```java
package com.example.dishes;

public class Smoothie {
    public static final String DISH_NAME = "Smoothie";
    public static final String DESCRIPTION = "Yummy and Refreshing";
}
```


Lastly, add these files as rules in the appropriate `BUILD` files. Create a new java library for each new ingredient, including its name, public visibility, and its newly created 'src' file. You should wind up with this updated `BUILD` file:

**`src/main/java/com/example/ingredients/BUILD`**

```
java_library(
    name = "cheese",
    visibility = ["//visibility:public"],
    srcs = ["Cheese.java"],
)

java_library(
    name = "dough",
    visibility = ["//visibility:public"],
    srcs = ["Dough.java"],
)

java_library(
    name = "macaroni",
    visibility = ["//visibility:public"],
    srcs = ["Macaroni.java"],
)

java_library(
    name = "tomato",
    visibility = ["//visibility:public"],
    srcs = ["Tomato.java"],
)

java_library(
    name = "strawberry",
    visibility = ["//visibility:public"],
    srcs = ["Strawberry.java"],
)

java_library(
    name = "banana",
    visibility = ["//visibility:public"],
    srcs = ["Banana.java"],
)
```

In the `BUILD` file for dishes, you want to add a new rule for `Smoothie`. Doing so includes the Java file created for `Smoothie` as a 'src' file, and the new rules you made for each ingredient of the smoothie.

**`src/main/java/com/example/dishes/BUILD`**

```
java_library(
    name = "macAndCheese",
    visibility = ["//visibility:public"],
    srcs = ["MacAndCheese.java"],
    deps = [
        "//src/main/java/com/example/ingredients:cheese",
        "//src/main/java/com/example/ingredients:macaroni",
    ],
)

java_library(
    name = "pizza",
    visibility = ["//visibility:public"],
    srcs = ["Pizza.java"],
    deps = [
        "//src/main/java/com/example/ingredients:cheese",
        "//src/main/java/com/example/ingredients:dough",
        "//src/main/java/com/example/ingredients:tomato",
    ],
)

java_library(
    name = "smoothie",
    visibility = ["//visibility:public"],
    srcs = ["Smoothie.java"],
    deps = [
        "//src/main/java/com/example/ingredients:strawberry",
        "//src/main/java/com/example/ingredients:banana",
    ],
)
```

Lastly, you want to include the smoothie as a dependency in the Chef’s `BUILD` file.

**`src/main/java/com/example/restaurant/BUILD`**

```
java\_library(
    name = "chef",
    visibility = ["//visibility:public"],
    srcs = [
        "Chef.java",
    ],

    deps = [
        "//src/main/java/com/example/dishes:macAndCheese",
        "//src/main/java/com/example/dishes:pizza",
        "//src/main/java/com/example/dishes:smoothie",
    ],
)

java\_library(
    name = "cafe",
    visibility = ["//visibility:public"],
    srcs = [
        "Cafe.java",
    ],
    deps = [
        ":chef",
    ],
)
```

Build `cafe` again to confirm that there are no errors. If it builds successfully, congratulations! You’ve added a new dependency for the 'Cafe'. If not, look out for spelling mistakes and package naming. For more information about writing `BUILD` files see [BUILD Style Guide](https://bazel.build/build/style-guide).

Now, visualize the new dependency graph with the addition of the `Smoothie` to compare with the previous one. For clarity, name the graph input as `graph2.in` and `graph2.png`.


```posix-terminal
bazel query --noimplicit_deps 'deps(:runner)' --output graph > graph2.in
```

```posix-terminal
dot -Tpng < graph2.in > graph2.png
```

[![The same graph as the first one except now there is a spoke stemming from the chef target with smoothie which leads to banana and strawberry](images/query_graph2.png "Updated dependency graph")](images/query_graph2.png)

Looking at `graph2.png`, you can see that `Smoothie` has no shared dependencies with other dishes but is just another target that the `Chef` relies on.

## somepath() and allpaths()

What if you want to query why one package depends on another package? Displaying a dependency path between the two provides the answer.

Two functions can help you find dependency paths: `somepath()` and `allpaths()`. Given a starting target S and an end point E, find a path between S and E by using `somepath(S,E)`.

Explore the differences between these two functions by looking at the relationships between the 'Chef' and 'Cheese' targets. There are different possible paths to get from one target to the other:

*   Chef → MacAndCheese → Cheese
*   Chef → Pizza → Cheese

`somepath()` gives you a single path out of the two options, whereas 'allpaths()' outputs every possible path.

Using Cafe Bazel as an example, run the following:

```posix-terminal
bazel query "somepath(//src/main/java/com/example/restaurant/..., //src/main/java/com/example/ingredients:cheese)"
```

```bash
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/ingredients:cheese
```

The output follows the first path of Cafe → Chef → MacAndCheese → Cheese. If instead you use `allpaths()`, you get:

```posix-terminal
bazel query "allpaths(//src/main/java/com/example/restaurant/..., //src/main/java/com/example/ingredients:cheese)"
```

```bash
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```

![Output path of cafe to chef to pizza,mac and cheese to cheese](images/query_graph3.png "Output path for dependency")

The output of `allpaths()` is a little harder to read as it is a flattened list of the dependencies. Visualizing this graph using Graphviz makes the relationship clearer to understand.

## Test yourself

One of Cafe Bazel’s customers gave the restaurant's first review! Unfortunately, the review is missing some details such as the identity of the reviewer and what dish it’s referencing. Luckily, you can access this information with Bazel. The `reviews` package contains a program that prints a review from a mystery customer. Build and run it with:

```posix-terminal
bazel build //src/main/java/com/example/reviews:review
```

```posix-terminal
bazel-bin/src/main/java/com/example/reviews/review
```

Going off Bazel queries only, try to find out who wrote the review, and what dish they were describing.

<div>
  <devsite-expandable>
  <h4 class="showalways">Hint</h4>
  <p>Check the tags and dependencies for useful information.</p>
  </devsite-expandable>
</div>

<div>
  <devsite-expandable>
  <h4 class="showalways">Answer</h4>
  <p>This review was describing the Pizza and Amir was the reviewer. If you look at what dependencies that this rule had using
  <code>bazel query --noimplicit\_deps 'deps(//src/main/java/com/example/reviews:review)'</code>
  The result of this command reveals that Amir is the reviewer!
  Next, since you know the reviewer is Amir, you can use the query function to seek which tag Amir has in the `BUILD` file to see what dish is there.
  The command <code>bazel query 'attr(tags, "pizza", //src/main/java/com/example/customers/...)'</code> output that Amir is the only customer that ordered a pizza and is the reviewer which gives us the answer.
  </p>
  </devsite-expandable>
</div>

## Wrapping up

Congratulations! You have now run several basic queries, which you can try out on own projects. To learn more about the query language syntax, refer to the [Query reference page](https://bazel.build/query/language). Want more advanced queries? The [Query guide](https://bazel.build/query/guide) showcases an in-depth list of more use cases than are covered in this guide.


Project: /_project.yaml
Book: /_book.yaml

# Action Graph Query (aquery)

{% include "_buttons.html" %}

The `aquery` command allows you to query for actions in your build graph.
It operates on the post-analysis Configured Target Graph and exposes
information about **Actions, Artifacts and their relationships.**

`aquery` is useful when you are interested in the properties of the Actions/Artifacts
generated from the Configured Target Graph. For example, the actual commands run
and their inputs/outputs/mnemonics.

The tool accepts several command-line [options](#command-options).
Notably, the aquery command runs on top of a regular Bazel build and inherits
the set of options available during a build.

It supports the same set of functions that is also available to traditional
`query` but `siblings`, `buildfiles` and
`tests`.

An example `aquery` output (without specific details):

<pre>
$ bazel aquery 'deps(//some:label)'
action 'Writing file some_file_name'
  Mnemonic: ...
  Target: ...
  Configuration: ...
  ActionKey: ...
  Inputs: [...]
  Outputs: [...]
</pre>

## Basic syntax {:#basic-syntax}

A simple example of the syntax for `aquery` is as follows:

`bazel aquery "aquery_function(function(//target))"`

The query expression (in quotes) consists of the following:

*   `aquery_function(...)`: functions specific to `aquery`.
    More details [below](#using-aquery-functions).
*   `function(...)`: the standard [functions](/query/language#functions)
    as traditional `query`.
*   `//target` is the label to the interested target.

<pre>
# aquery examples:
# Get the action graph generated while building //src/target_a
$ bazel aquery '//src/target_a'

# Get the action graph generated while building all dependencies of //src/target_a
$ bazel aquery 'deps(//src/target_a)'

# Get the action graph generated while building all dependencies of //src/target_a
# whose inputs filenames match the regex ".*cpp".
$ bazel aquery 'inputs(".*cpp", deps(//src/target_a))'
</pre>

## Using aquery functions {:#using-aquery-functions}

There are three `aquery` functions:

*   `inputs`: filter actions by inputs.
*   `outputs`: filter actions by outputs
*   `mnemonic`: filter actions by mnemonic

`expr ::= inputs(word, expr)`

  The `inputs` operator returns the actions generated from building `expr`,
  whose input filenames match the regex provided by `word`.

`$ bazel aquery 'inputs(".*cpp", deps(//src/target_a))'`

`outputs` and `mnemonic` functions share a similar syntax.

You can also combine functions to achieve the AND operation. For example:

<pre>
  $ bazel aquery 'mnemonic("Cpp.*", (inputs(".*cpp", inputs("foo.*", //src/target_a))))'
</pre>

  The above command would find all actions involved in building `//src/target_a`,
  whose mnemonics match `"Cpp.*"` and inputs match the patterns
  `".*cpp"` and `"foo.*"`.

Important: aquery functions can't be nested inside non-aquery functions.
Conceptually, this makes sense since the output of aquery functions is Actions,
not Configured Targets.

An example of the syntax error produced:

<pre>
        $ bazel aquery 'deps(inputs(".*cpp", //src/target_a))'
        ERROR: aquery filter functions (inputs, outputs, mnemonic) produce actions,
        and therefore can't be the input of other function types: deps
        deps(inputs(".*cpp", //src/target_a))
</pre>

## Options {:#options}

### Build options {:#build-options}

`aquery` runs on top of a regular Bazel build and thus inherits the set of
[options](/reference/command-line-reference#build-options)
available during a build.

### Aquery options {:#aquery-options}

#### `--output=(text|summary|commands|proto|jsonproto|textproto), default=text` {:#output}

The default output format (`text`) is human-readable,
use `proto`, `textproto`, or `jsonproto` for machine-readable format.
The proto message is `analysis.ActionGraphContainer`.

The `commands` output format prints a list of build commands with
one command per line.

In general, do not depend on the order of output. For more information,
see the [core query ordering contract](/query/language#graph-order).

#### `--include_commandline, default=true` {:#include-commandline}

Includes the content of the action command lines in the output (potentially large).

#### `--include_artifacts, default=true` {:#include-artifacts}

Includes names of the action inputs and outputs in the output (potentially large).

#### `--include_aspects, default=true` {:#include-aspects}

Whether to include Aspect-generated actions in the output.

#### `--include_param_files, default=false` {:#include-param-files}

Include the content of the param files used in the command (potentially large).

Warning: Enabling this flag will automatically enable the `--include_commandline` flag.

#### `--include_file_write_contents, default=false` {:#include-file-write-contents}

Include file contents for the `actions.write()` action and the contents of the
manifest file for the `SourceSymlinkManifest` action The file contents is
returned in the `file_contents` field with `--output=`xxx`proto`.
With `--output=text`, the output has
```
FileWriteContents: [<base64-encoded file contents>]
```
line

#### `--skyframe_state, default=false` {:#skyframe-state}

Without performing extra analysis, dump the Action Graph from Skyframe.

Note: Specifying a target with `--skyframe_state` is currently not supported.
This flag is only available with `--output=proto` or `--output=textproto`.

## Other tools and features {:#other-tools-features}

### Querying against the state of Skyframe {:#querying-against-skyframe}

[Skyframe](/reference/skyframe) is the evaluation and
incrementality model of Bazel. On each instance of Bazel server, Skyframe stores the dependency graph
constructed from the previous runs of the [Analysis phase](/run/build#analysis).

In some cases, it is useful to query the Action Graph on Skyframe.
An example use case would be:

1.  Run `bazel build //target_a`
2.  Run `bazel build //target_b`
3.  File `foo.out` was generated.

_As a Bazel user, I want to determine if `foo.out` was generated from building
`//target_a` or `//target_b`_.

One could run `bazel aquery 'outputs("foo.out", //target_a)'` and
`bazel aquery 'outputs("foo.out", //target_b)'` to figure out the action responsible
for creating `foo.out`, and in turn the target. However, the number of different
targets previously built can be larger than 2, which makes running multiple `aquery`
commands a hassle.

As an alternative, the `--skyframe_state` flag can be used:

<pre>
  # List all actions on Skyframe's action graph
  $ bazel aquery --output=proto --skyframe_state

  # or

  # List all actions on Skyframe's action graph, whose output matches "foo.out"
  $ bazel aquery --output=proto --skyframe_state 'outputs("foo.out")'
</pre>

With `--skyframe_state` mode, `aquery` takes the content of the Action Graph
that Skyframe keeps on the instance of Bazel, (optionally) performs filtering on it and
outputs the content, without re-running the analysis phase.

#### Special considerations {:#special-considerations}

##### Output format {:#output-format}

`--skyframe_state` is currently only available for `--output=proto`
and `--output=textproto`

##### Non-inclusion of target labels in the query expression {:#target-labels-non-inclusion}

Currently, `--skyframe_state` queries the whole action graph that exists on Skyframe,
regardless of the targets. Having the target label specified in the query together with
`--skyframe_state` is considered a syntax error:

<pre>
  # WRONG: Target Included
  $ bazel aquery --output=proto --skyframe_state **//target_a**
  ERROR: Error while parsing '//target_a)': Specifying build target(s) [//target_a] with --skyframe_state is currently not supported.

  # WRONG: Target Included
  $ bazel aquery --output=proto --skyframe_state 'inputs(".*.java", **//target_a**)'
  ERROR: Error while parsing '//target_a)': Specifying build target(s) [//target_a] with --skyframe_state is currently not supported.

  # CORRECT: Without Target
  $ bazel aquery --output=proto --skyframe_state
  $ bazel aquery --output=proto --skyframe_state 'inputs(".*.java")'
</pre>

### Comparing aquery outputs {:#comparing-aquery-outputs}

You can compare the outputs of two different aquery invocations using the `aquery_differ` tool.
For instance: when you make some changes to your rule definition and want to verify that the
command lines being run did not change. `aquery_differ` is the tool for that.

The tool is available in the [bazelbuild/bazel](https://github.com/bazelbuild/bazel/tree/master/tools/aquery_differ){: .external} repository.
To use it, clone the repository to your local machine. An example usage:

<pre>
  $ bazel run //tools/aquery_differ -- \
  --before=/path/to/before.proto \
  --after=/path/to/after.proto \
  --input_type=proto \
  --attrs=cmdline \
  --attrs=inputs
</pre>

The above command returns the difference between the `before` and `after` aquery outputs:
which actions were present in one but not the other, which actions have different
command line/inputs in each aquery output, ...). The result of running the above command would be:

<pre>
  Aquery output 'after' change contains an action that generates the following outputs that aquery output 'before' change doesn't:
  ...
  /list of output files/
  ...

  [cmdline]
  Difference in the action that generates the following output(s):
    /path/to/abc.out
  --- /path/to/before.proto
  +++ /path/to/after.proto
  @@ -1,3 +1,3 @@
    ...
    /cmdline diff, in unified diff format/
    ...
</pre>

#### Command options {:#command-options}

`--before, --after`: The aquery output files to be compared

`--input_type=(proto|text_proto), default=proto`: the format of the input
files. Support is provided for `proto` and `textproto` aquery output.

`--attrs=(cmdline|inputs), default=cmdline`: the attributes of actions
to be compared.

### Aspect-on-aspect {:#aspect-on-aspect}

It is possible for [Aspects](/extending/aspects)
to be applied on top of each other. The aquery output of the action generated by
these Aspects would then include the _Aspect path_, which is the sequence of
Aspects applied to the target which generated the action.

An example of Aspect-on-Aspect:

<pre>
  t0
  ^
  | <- a1
  t1
  ^
  | <- a2
  t2
</pre>

Let t<sub>i</sub> be a target of rule r<sub>i</sub>, which applies an Aspect a<sub>i</sub>
to its dependencies.

Assume that a2 generates an action X when applied to target t0. The text output of
`bazel aquery --include_aspects 'deps(//t2)'` for action X would be:

<pre>
  action ...
  Mnemonic: ...
  Target: //my_pkg:t0
  Configuration: ...
  AspectDescriptors: [//my_pkg:rule.bzl%**a2**(foo=...)
    -> //my_pkg:rule.bzl%**a1**(bar=...)]
  ...
</pre>

This means that action `X` was generated by Aspect `a2` applied onto
`a1(t0)`, where `a1(t0)` is the result of Aspect `a1` applied
onto target `t0`.

Each `AspectDescriptor` has the following format:

<pre>
  AspectClass([param=value,...])
</pre>

`AspectClass` could be the name of the Aspect class (for native Aspects) or
`bzl_file%aspect_name` (for Starlark Aspects). `AspectDescriptor` are
sorted in topological order of the
[dependency graph](/extending/aspects#aspect_basics).

### Linking with the JSON profile {:#linking-with-json-profile}

While aquery provides information about the actions being run in a build (why they're being run,
their inputs/outputs), the [JSON profile](/rules/performance#performance-profiling)
tells us the timing and duration of their execution.
It is possible to combine these 2 sets of information via a common denominator: an action's primary output.

To include actions' outputs in the JSON profile, generate the profile with
`--experimental_include_primary_output --noslim_profile`.
Slim profiles are incompatible with the inclusion of primary outputs. An action's primary output
is included by default by aquery.

We don't currently provide a canonical tool to combine these 2 data sources, but you should be
able to build your own script with the above information.

## Known issues {:#known-issues}

### Handling shared actions {:#handling-shared-actions}

Sometimes actions are
[shared](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/Actions.java;l=59;drc=146d51aa1ec9dcb721a7483479ef0b1ac21d39f1){: .external}
between configured targets.

In the execution phase, those shared actions are
[simply considered as one](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/Actions.java;l=241;drc=003b8734036a07b496012730964ac220f486b61f){: .external} and only executed once.
However, aquery operates on the pre-execution, post-analysis action graph, and hence treats these
like separate actions whose output Artifacts have the exact same `execPath`. As a result,
equivalent Artifacts appear duplicated.

The list of aquery issues/planned features can be found on
[GitHub](https://github.com/bazelbuild/bazel/labels/team-Performance){: .external}.

## FAQs {:#faqs}

### The ActionKey remains the same even though the content of an input file changed. {:#actionkey-same}

In the context of aquery, the `ActionKey` refers to the `String` gotten from
[ActionAnalysisMetadata#getKey](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/ActionAnalysisMetadata.java;l=89;drc=8b856f5484f0117b2aebc302f849c2a15f273310){: .external}:

<pre>
  Returns a string encoding all of the significant behaviour of this Action that might affect the
  output. The general contract of `getKey` is this: if the work to be performed by the
  execution of this action changes, the key must change.

  ...

  Examples of changes that should affect the key are:

  - Changes to the BUILD file that materially affect the rule which gave rise to this Action.
  - Changes to the command-line options, environment, or other global configuration resources
      which affect the behaviour of this kind of Action (other than changes to the names of the
      input/output files, which are handled externally).
  - An upgrade to the build tools which changes the program logic of this kind of Action
      (typically this is achieved by incorporating a UUID into the key, which is changed each
      time the program logic of this action changes).
  Note the following exception: for actions that discover inputs, the key must change if any
  input names change or else action validation may falsely validate.
</pre>

This excludes the changes to the content of the input files, and is not to be confused with
[RemoteCacheClient#ActionKey](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/remote/common/RemoteCacheClient.java;l=38;drc=21577f202eb90ce94a337ebd2ede824d609537b6){: .external}.

## Updates {:#updates}

For any issues/feature requests, please file an issue [here](https://github.com/bazelbuild/bazel/issues/new).


Project: /_project.yaml
Book: /_book.yaml

# Query guide

{% include "_buttons.html" %}

This page covers how to get started using Bazel's query language to trace
dependencies in your code.

For a language details and `--output` flag details, please see the
reference manuals, [Bazel query reference](/query/language)
and [Bazel cquery reference](/query/cquery). You can get help by
typing `bazel help query` or `bazel help cquery` on the
command line.

To execute a query while ignoring errors such as missing targets, use the
`--keep_going` flag.

## Finding the dependencies of a rule {:#finding-rule-dependencies}

To see the dependencies of `//foo`, use the
`deps` function in bazel query:

<pre>
$ bazel query "deps(//foo)"
//foo:foo
//foo:foo-dep
...
</pre>

This is the set of all targets required to build `//foo`.

## Tracing the dependency chain between two packages {:#tracing-dependency-chain}

The library `//third_party/zlib:zlibonly` isn't in the BUILD file for
`//foo`, but it is an indirect dependency. How can
we trace this dependency path?  There are two useful functions here:
`allpaths` and `somepath`. You may also want to exclude
tooling dependencies with `--notool_deps` if you care only about
what is included in the artifact you built, and not every possible job.

To visualize the graph of all dependencies, pipe the bazel query output through
  the `dot` command-line tool:

<pre>
$ bazel query "allpaths(//foo, third_party/...)" --notool_deps --output graph | dot -Tsvg > /tmp/deps.svg
</pre>

Note: `dot` supports other image formats, just replace `svg` with the
format identifier, for example, `png`.

When a dependency graph is big and complicated, it can be helpful start with a single path:

<pre>
$ bazel query "somepath(//foo:foo, third_party/zlib:zlibonly)"
//foo:foo
//translations/tools:translator
//translations/base:base
//third_party/py/MySQL:MySQL
//third_party/py/MySQL:_MySQL.so
//third_party/mysql:mysql
//third_party/zlib:zlibonly
</pre>

If you do not specify `--output graph` with `allpaths`,
you will get a flattened list of the dependency graph.

<pre>
$ bazel query "allpaths(//foo, third_party/...)"
  ...many errors detected in BUILD files...
//foo:foo
//translations/tools:translator
//translations/tools:aggregator
//translations/base:base
//tools/pkg:pex
//tools/pkg:pex_phase_one
//tools/pkg:pex_lib
//third_party/python:python_lib
//translations/tools:messages
//third_party/py/xml:xml
//third_party/py/xml:utils/boolean.so
//third_party/py/xml:parsers/sgmlop.so
//third_party/py/xml:parsers/pyexpat.so
//third_party/py/MySQL:MySQL
//third_party/py/MySQL:_MySQL.so
//third_party/mysql:mysql
//third_party/openssl:openssl
//third_party/zlib:zlibonly
//third_party/zlib:zlibonly_v1_2_3
//third_party/python:headers
//third_party/openssl:crypto
</pre>

### Aside: implicit dependencies {:#implicit-dependencies}

The BUILD file for `//foo` never references
`//translations/tools:aggregator`. So, where's the direct dependency?

Certain rules include implicit dependencies on additional libraries or tools.
For example, to build a `genproto` rule, you need first to build the Protocol
Compiler, so every `genproto` rule carries an implicit dependency on the
protocol compiler. These dependencies are not mentioned in the build file,
but added in by the build tool. The full set of implicit dependencies is
  currently undocumented. Using `--noimplicit_deps` allows you to filter out
  these deps from your query results. For cquery, this will include resolved toolchains.

## Reverse dependencies {:#reverse-dependencies}

You might want to know the set of targets that depends on some target. For instance,
if you're going to change some code, you might want to know what other code
you're about to break. You can use `rdeps(u, x)` to find the reverse
dependencies of the targets in `x` within the transitive closure of `u`.

Bazel's [Sky Query](/query/language#sky-query)
supports the `allrdeps` function which allows you to query reverse dependencies
in a universe you specify.

## Miscellaneous uses {:#miscellaneous-uses}

You can use `bazel query` to analyze many dependency relationships.

### What exists ... {:#what-exists}

#### What packages exist beneath `foo`? {:#what-exists-beneath-foo}

<pre>bazel query 'foo/...' --output package</pre>

#### What rules are defined in the `foo` package? {:#rules-defined-in-foo}

<pre>bazel query 'kind(rule, foo:*)' --output label_kind</pre>

#### What files are generated by rules in the `foo` package? {:#files-generated-by-rules}

<pre>bazel query 'kind("generated file", //foo:*)'</pre>

#### What targets are generated by starlark macro `foo`? {:#targets-generated-by-foo}

<pre>bazel query 'attr(generator_function, foo, //path/to/search/...)'</pre>

#### What's the set of BUILD files needed to build `//foo`? {:#build-files-required}

<pre>bazel query 'buildfiles(deps(//foo))' | cut -f1 -d:</pre>

#### What are the individual tests that a `test_suite` expands to? {:#individual-tests-in-testsuite}

<pre>bazel query 'tests(//foo:smoke_tests)'</pre>

#### Which of those are C++ tests? {:#cxx-tests}

<pre>bazel query 'kind(cc_.*, tests(//foo:smoke_tests))'</pre>

#### Which of those are small?  Medium?  Large? {:#size-of-tests}

<pre>
bazel query 'attr(size, small, tests(//foo:smoke_tests))'

bazel query 'attr(size, medium, tests(//foo:smoke_tests))'

bazel query 'attr(size, large, tests(//foo:smoke_tests))'
</pre>

#### What are the tests beneath `foo` that match a pattern? {:#tests-beneath-foo}

<pre>bazel query 'filter("pa?t", kind(".*_test rule", //foo/...))'</pre>

The pattern is a regex and is applied to the full name of the rule. It's similar to doing

<pre>bazel query 'kind(".*_test rule", //foo/...)' | grep -E 'pa?t'</pre>

#### What package contains file `path/to/file/bar.java`? {:#barjava-package}

<pre> bazel query path/to/file/bar.java --output=package</pre>

#### What is the build label for `path/to/file/bar.java?` {:#barjava-build-label}

<pre>bazel query path/to/file/bar.java</pre>

#### What rule target(s) contain file `path/to/file/bar.java` as a source? {:#barjava-rule-targets}

<pre>
fullname=$(bazel query path/to/file/bar.java)
bazel query "attr('srcs', $fullname, ${fullname//:*/}:*)"
</pre>

### What package dependencies exist ... {:#package-dependencies}

#### What packages does `foo` depend on? (What do I need to check out to build `foo`) {:#packages-foo-depends-on}

<pre>bazel query 'buildfiles(deps(//foo:foo))' --output package</pre>

Note: `buildfiles` is required in order to correctly obtain all files
referenced by `subinclude`; see the reference manual for details.

#### What packages does the `foo` tree depend on, excluding `foo/contrib`? {:#packages-foo-tree-depends-on}

<pre>bazel query 'deps(foo/... except foo/contrib/...)' --output package</pre>

### What rule dependencies exist ... {:#rule-dependencies}

#### What genproto rules does bar depend upon? {:#genproto-rules}

<pre>bazel query 'kind(genproto, deps(bar/...))'</pre>

#### Find the definition of some JNI (C++) library that is transitively depended upon by a Java binary rule in the servlet tree. {:#jni-library}

<pre>bazel query 'some(kind(cc_.*library, deps(kind(java_binary, //java/com/example/frontend/...))))' --output location</pre>

##### ...Now find the definitions of all the Java binaries that depend on them {:#java-binaries}

<pre>bazel query 'let jbs = kind(java_binary, //java/com/example/frontend/...) in
  let cls = kind(cc_.*library, deps($jbs)) in
    $jbs intersect allpaths($jbs, $cls)'
</pre>

### What file dependencies exist ... {:#file-dependencies}

#### What's the complete set of Java source files required to build foo? {:#java-source-files}

Source files:

<pre>bazel query 'kind("source file", deps(//path/to/target/foo/...))' | grep java$</pre>

Generated files:

<pre>bazel query 'kind("generated file", deps(//path/to/target/foo/...))' | grep java$</pre>

#### What is the complete set of Java source files required to build QUX's tests? {:qux-tests}

Source files:

<pre>bazel query 'kind("source file", deps(kind(".*_test rule", javatests/com/example/qux/...)))' | grep java$</pre>

Generated files:

<pre>bazel query 'kind("generated file", deps(kind(".*_test rule", javatests/com/example/qux/...)))' | grep java$</pre>

### What differences in dependencies between X and Y exist ... {:#differences-in-dependencies}

#### What targets does `//foo` depend on that `//foo:foolib` does not? {:#foo-targets}

<pre>bazel query 'deps(//foo) except deps(//foo:foolib)'</pre>

#### What C++ libraries do the `foo` tests depend on that the `//foo` production binary does _not_ depend on? {:#foo-cxx-libraries}

<pre>bazel query 'kind("cc_library", deps(kind(".*test rule", foo/...)) except deps(//foo))'</pre>

### Why does this dependency exist ... {:#why-dependencies}

#### Why does `bar` depend on `groups2`? {:#dependency-bar-groups2}

<pre>bazel query 'somepath(bar/...,groups2/...:*)'</pre>

Once you have the results of this query, you will often find that a single
target stands out as being an unexpected or egregious and undesirable
dependency of `bar`. The query can then be further refined to:

#### Show me a path from `docker/updater:updater_systest` (a `py_test`) to some `cc_library` that it depends upon: {:#path-docker-cclibrary}

<pre>bazel query 'let cc = kind(cc_library, deps(docker/updater:updater_systest)) in
  somepath(docker/updater:updater_systest, $cc)'</pre>

#### Why does library `//photos/frontend:lib` depend on two variants of the same library `//third_party/jpeglib` and `//third_party/jpeg`? {:#library-two-variants}

This query boils down to: "show me the subgraph of `//photos/frontend:lib` that
depends on both libraries". When shown in topological order, the last element
of the result is the most likely culprit.

<pre>bazel query 'allpaths(//photos/frontend:lib, //third_party/jpeglib)
                intersect
               allpaths(//photos/frontend:lib, //third_party/jpeg)'
//photos/frontend:lib
//photos/frontend:lib_impl
//photos/frontend:lib_dispatcher
//photos/frontend:icons
//photos/frontend/modules/gadgets:gadget_icon
//photos/thumbnailer:thumbnail_lib
//third_party/jpeg/img:renderer
</pre>

### What depends on  ... {:#depends-on}

#### What rules under bar depend on Y? {:#rules-bar-y}

<pre>bazel query 'bar/... intersect allpaths(bar/..., Y)'</pre>

Note: `X intersect allpaths(X, Y)` is the general idiom for the query "which X
depend on Y?" If expression X is non-trivial, it may be convenient to bind a
name to it using `let` to avoid duplication.

#### What targets directly depend on T, in T's package? {:#targets-t}

<pre>bazel query 'same_pkg_direct_rdeps(T)'</pre>

### How do I break a dependency ... {:#break-dependency}

<!-- TODO find a convincing value of X to plug in here -->

#### What dependency paths do I have to break to make `bar` no longer depend on X? {:#break-dependency-bar-x}

To output the graph to a `svg` file:

<pre>bazel query 'allpaths(bar/...,X)' --output graph | dot -Tsvg &gt; /tmp/dep.svg</pre>

### Misc {:#misc}

#### How many sequential steps are there in the `//foo-tests` build? {:#steps-footests}

Unfortunately, the query language can't currently give you the longest path
from x to y, but it can find the (or rather _a_) most distant node from the
starting point, or show you the _lengths_ of the longest path from x to every
y that it depends on. Use `maxrank`:

<pre>bazel query 'deps(//foo-tests)' --output maxrank | tail -1
85 //third_party/zlib:zutil.c</pre>

The result indicates that there exist paths of length 85 that must occur in
order in this build.


Project: /_project.yaml
Book: /_book.yaml

# The Bazel Query Reference

{% include "_buttons.html" %}

This page is the reference manual for the _Bazel Query Language_ used
when you use `bazel query` to analyze build dependencies. It also
describes the output formats `bazel query` supports.

For practical use cases, see the [Bazel Query How-To](/query/guide).

## Additional query reference

In addition to `query`, which runs on the post-loading phase target graph,
Bazel includes *action graph query* and *configurable query*.

### Action graph query {:#aquery}

The action graph query (`aquery`) operates on the post-analysis Configured
Target Graph and exposes information about **Actions**, **Artifacts**, and
their relationships. `aquery` is useful when you are interested in the
properties of the Actions/Artifacts generated from the Configured Target Graph.
For example, the actual commands run and their inputs, outputs, and mnemonics.

For more details, see the [aquery reference](/query/aquery).

### Configurable query {:#cquery}

Traditional Bazel query runs on the post-loading phase target graph and
therefore has no concept of configurations and their related concepts. Notably,
it doesn't correctly resolve [select statements](/reference/be/functions#select)
and instead returns all possible resolutions of selects. However, the
configurable query environment, `cquery`, properly handles configurations but
doesn't provide all of the functionality of this original query.

For more details, see the [cquery reference](/query/cquery).


## Examples {:#examples}

How do people use `bazel query`?  Here are typical examples:

Why does the `//foo` tree depend on `//bar/baz`?
Show a path:

```
somepath(foo/..., //bar/baz:all)
```

What C++ libraries do all the `foo` tests depend on that
the `foo_bin` target does not?

```
kind("cc_library", deps(kind(".*test rule", foo/...)) except deps(//foo:foo_bin))
```

## Tokens: The lexical syntax {:#tokens}

Expressions in the query language are composed of the following
tokens:

* **Keywords**, such as `let`. Keywords are the reserved words of the
  language, and each of them is described below. The complete set
  of keywords is:

   * [`except`](#set-operations)

   * [`in`](#variables)

   * [`intersect`](#set-operations)

   * [`let`](#variables)

   * [`set`](#set)

   * [`union`](#set-operations)

* **Words**, such as "`foo/...`" or "`.*test rule`" or "`//bar/baz:all`". If a
  character sequence is "quoted" (begins and ends with a single-quote ' or
  begins and ends with a double-quote "), it is a word. If a character sequence
  is not quoted, it may still be parsed as a word. Unquoted words are sequences
  of characters drawn from the alphabet characters A-Za-z, the numerals 0-9,
  and the special characters `*/@.-_:$~[]` (asterisk, forward slash, at, period,
  hyphen, underscore, colon, dollar sign, tilde, left square brace, right square
  brace). However, unquoted words may not start with a hyphen `-` or asterisk `*`
  even though relative [target names](/concepts/labels#target-names) may start
  with those characters. As a special rule meant to simplify the handling of
  labels referring to external repositories, unquoted words that start with
  `@@` may contain `+` characters.

  Unquoted words also may not include the characters plus sign `+` or equals
  sign `=`, even though those characters are permitted in target names. When
  writing code that generates query expressions, target names should be quoted.

  Quoting _is_ necessary when writing scripts that construct Bazel query
  expressions from user-supplied values.

  ```
   //foo:bar+wiz    # WRONG: scanned as //foo:bar + wiz.
   //foo:bar=wiz    # WRONG: scanned as //foo:bar = wiz.
   "//foo:bar+wiz"  # OK.
   "//foo:bar=wiz"  # OK.
  ```

  Note that this quoting is in addition to any quoting that may be required by
  your shell, such as:

  ```posix-terminal
  bazel query ' "//foo:bar=wiz" '   # single-quotes for shell, double-quotes for Bazel.
  ```

  Keywords and operators, when quoted, are treated as ordinary words. For example, `some` is a
  keyword but "some" is a word. Both `foo` and "foo" are words.

  However, be careful when using single or double quotes in target names. When
  quoting one or more target names, use only one type of quotes (either all
  single or all double quotes).

  The following are examples of what the Java query string will be:


  ```
    'a"'a'         # WRONG: Error message: unclosed quotation.
    "a'"a"         # WRONG: Error message: unclosed quotation.
    '"a" + 'a''    # WRONG: Error message: unexpected token 'a' after query expression '"a" + '
    "'a' + "a""    # WRONG: Error message: unexpected token 'a' after query expression ''a' + '
    "a'a"          # OK.
    'a"a'          # OK.
    '"a" + "a"'    # OK
    "'a' + 'a'"    # OK
  ```

  We chose this syntax so that quote marks aren't needed in most cases. The
  (unusual) `".*test rule"` example needs quotes: it starts with a period and
  contains a space. Quoting `"cc_library"` is unnecessary but harmless.

* **Punctuation**, such as parens `()`, period `.` and comma `,`. Words
  containing punctuation (other than the exceptions listed above) must be quoted.

Whitespace characters outside of a quoted word are ignored.

## Bazel query language concepts {:#language-concepts}

The Bazel query language is a language of expressions. Every
expression evaluates to a **partially-ordered set** of targets,
or equivalently, a **graph** (DAG) of targets. This is the only
datatype.

Set and graph refer to the same datatype, but emphasize different
aspects of it, for example:

*   **Set:** The partial order of the targets is not interesting.
*   **Graph:** The partial order of targets is significant.

### Cycles in the dependency graph {:#dependency-graph-cycles}

Build dependency graphs should be acyclic.

The algorithms used by the query language are intended for use in
acyclic graphs, but are robust against cycles. The details of how
cycles are treated are not specified and should not be relied upon.

### Implicit dependencies {:#implicit-dependencies}

In addition to build dependencies that are defined explicitly in `BUILD` files,
Bazel adds additional _implicit_ dependencies to rules. Implicit dependencies
may be defined by:

- [Private attributes](/extending/rules#private_attributes_and_implicit_dependencies)
- [Toolchain requirements](/extending/toolchains#writing-rules-toolchains)

By default, `bazel query` takes implicit dependencies into account
when computing the query result. This behavior can be changed with
the `--[no]implicit_deps` option.

Note that, as query does not consider configurations, potential toolchain
**implementations** are not considered dependencies, only the
required toolchain types. See
[toolchain documentation](/extending/toolchains#writing-rules-toolchains).

### Soundness {:#soundness}

Bazel query language expressions operate over the build
dependency graph, which is the graph implicitly defined by all
rule declarations in all `BUILD` files. It is important to understand
that this graph is somewhat abstract, and does not constitute a
complete description of how to perform all the steps of a build. In
order to perform a build, a _configuration_ is required too;
see the [configurations](/docs/user-manual#configurations)
section of the User's Guide for more detail.

The result of evaluating an expression in the Bazel query language
is true _for all configurations_, which means that it may be
a conservative over-approximation, and not exactly precise. If you
use the query tool to compute the set of all source files needed
during a build, it may report more than are actually necessary
because, for example, the query tool will include all the files
needed to support message translation, even though you don't intend
to use that feature in your build.

### On the preservation of graph order {:#graph-order}

Operations preserve any ordering
constraints inherited from their subexpressions. You can think of
this as "the law of conservation of partial order". Consider an
example: if you issue a query to determine the transitive closure of
dependencies of a particular target, the resulting set is ordered
according to the dependency graph. If you filter that set to
include only the targets of `file` kind, the same
_transitive_ partial ordering relation holds between every
pair of targets in the resulting subset - even though none of
these pairs is actually directly connected in the original graph.
(There are no file-file edges in the build dependency graph).

However, while all operators _preserve_ order, some
operations, such as the [set operations](#set-operations)
don't _introduce_ any ordering constraints of their own.
Consider this expression:

```
deps(x) union y
```

The order of the final result set is guaranteed to preserve all the
ordering constraints of its subexpressions, namely, that all the
transitive dependencies of `x` are correctly ordered with
respect to each other. However, the query guarantees nothing about
the ordering of the targets in `y`, nor about the
ordering of the targets in `deps(x)` relative to those in
`y` (except for those targets in
`y` that also happen to be in `deps(x)`).

Operators that introduce ordering constraints include:
`allpaths`, `deps`, `rdeps`, `somepath`, and the target pattern wildcards
`package:*`, `dir/...`, etc.

### Sky query {:#sky-query}

_Sky Query_ is a mode of query that operates over a specified _universe scope_.

#### Special functions available only in SkyQuery

Sky Query mode has the additional query functions `allrdeps` and
`rbuildfiles`. These functions operate over the entire
universe scope (which is why they don't make sense for normal Query).

#### Specifying a universe scope

Sky Query mode is activated by passing the following two flags:
(`--universe_scope` or `--infer_universe_scope`) and
`--order_output=no`.
`--universe_scope=<target_pattern1>,...,<target_patternN>` tells query to
preload the transitive closure of the target pattern specified by the target patterns, which can
be both additive and subtractive. All queries are then evaluated in this "scope". In particular,
the [`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles) operators only return results from this scope.
`--infer_universe_scope` tells Bazel to infer a value for `--universe_scope`
from the query expression. This inferred value is the list of unique target patterns in the
query expression, but this might not be what you want. For example:

```posix-terminal
bazel query --infer_universe_scope --order_output=no "allrdeps(//my:target)"
```

The list of unique target patterns in this query expression is `["//my:target"]`, so
Bazel treats this the same as the invocation:

```posix-terminal
bazel query --universe_scope=//my:target --order_output=no "allrdeps(//my:target)"
```

But the result of that query with `--universe_scope` is only `//my:target`;
none of the reverse dependencies of `//my:target` are in the universe, by
construction! On the other hand, consider:

```posix-terminal
bazel query --infer_universe_scope --order_output=no "tests(//a/... + b/...) intersect allrdeps(siblings(rbuildfiles(my/starlark/file.bzl)))"
```

This is a meaningful query invocation that is trying to compute the test targets in the
[`tests`](#tests) expansion of the targets under some directories that
transitively depend on targets whose definition uses a certain `.bzl` file. Here,
`--infer_universe_scope` is a convenience, especially in the case where the choice of
`--universe_scope` would otherwise require you to parse the query expression yourself.

So, for query expressions that use universe-scoped operators like
[`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles) be sure to use
`--infer_universe_scope` only if its behavior is what you want.

Sky Query has some advantages and disadvantages compared to the default query. The main
disadvantage is that it cannot order its output according to graph order, and thus certain
[output formats](#output-formats) are forbidden. Its advantages are that it provides
two operators ([`allrdeps`](#allrdeps) and
[`rbuildfiles`](#rbuildfiles)) that are not available in the default query.
As well, Sky Query does its work by introspecting the
[Skyframe](/reference/skyframe) graph, rather than creating a new
graph, which is what the default implementation does. Thus, there are some circumstances in which
it is faster and uses less memory.

## Expressions: Syntax and semantics of the grammar {:#expressions}

This is the grammar of the Bazel query language, expressed in EBNF notation:

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}word{{ '</var>' }}
       | let {{ '<var>' }}name{{ '</var>' }} = {{ '<var>' }}expr{{ '</var>' }} in {{ '<var>' }}expr{{ '</var>' }}
       | ({{ '<var>' }}expr{{ '</var>' }})
       | {{ '<var>' }}expr{{ '</var>' }} intersect {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} ^ {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} union {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} + {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} except {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} - {{ '<var>' }}expr{{ '</var>' }}
       | set({{ '<var>' }}word{{ '</var>' }} *)
       | {{ '<var>' }}word{{ '</var>' }} '(' {{ '<var>' }}int{{ '</var>' }} | {{ '<var>' }}word{{ '</var>' }} | {{ '<var>' }}expr{{ '</var>' }} ... ')'
```

The following sections describe each of the productions of this grammar in order.

### Target patterns {:#target-patterns}

```
expr ::= {{ '<var>' }}word{{ '</var>' }}
```

Syntactically, a _target pattern_ is just a word. It's interpreted as an
(unordered) set of targets. The simplest target pattern is a label, which
identifies a single target (file or rule). For example, the target pattern
`//foo:bar` evaluates to a set containing one element, the target, the `bar`
rule.

Target patterns generalize labels to include wildcards over packages and
targets. For example, `foo/...:all` (or just `foo/...`) is a target pattern
that evaluates to a set containing all _rules_ in every package recursively
beneath the `foo` directory; `bar/baz:all` is a target pattern that evaluates
to a set containing all the rules in the `bar/baz` package, but not its
subpackages.

Similarly, `foo/...:*` is a target pattern that evaluates to a set containing
all _targets_ (rules _and_ files) in every package recursively beneath the
`foo` directory; `bar/baz:*` evaluates to a set containing all the targets in
the `bar/baz` package, but not its subpackages.

Because the `:*` wildcard matches files as well as rules, it's often more
useful than `:all` for queries. Conversely, the `:all` wildcard (implicit in
target patterns like `foo/...`) is typically more useful for builds.

`bazel query` target patterns work the same as `bazel build` build targets do.
For more details, see [Target Patterns](/docs/user-manual#target-patterns), or
type `bazel help target-syntax`.

Target patterns may evaluate to a singleton set (in the case of a label), to a
set containing many elements (as in the case of `foo/...`, which has thousands
of elements) or to the empty set, if the target pattern matches no targets.

All nodes in the result of a target pattern expression are correctly ordered
relative to each other according to the dependency relation. So, the result of
`foo:*` is not just the set of targets in package `foo`, it is also the
_graph_ over those targets. (No guarantees are made about the relative ordering
of the result nodes against other nodes.) For more details, see the
[graph order](#graph-order) section.

### Variables {:#variables}

```none {:.devsite-disable-click-to-copy}
expr ::= let {{ '<var>' }}name{{ '</var>' }} = {{ '<var>' }}expr{{ '</var>' }}{{ '<sub>' }}1{{ '</sub>' }} in {{ '<var>' }}expr{{ '</var>' }}{{ '<sub>' }}2{{ '</sub>' }}
       | {{ '<var>' }}$name{{ '</var>' }}
```

The Bazel query language allows definitions of and references to
variables. The result of evaluation of a `let` expression is the same as
that of {{ '<var>' }}expr{{ '</var>' }}<sub>2</sub>, with all free occurrences
of variable {{ '<var>' }}name{{ '</var>' }} replaced by the value of
{{ '<var>' }}expr{{ '</var>' }}<sub>1</sub>.

For example, `let v = foo/... in allpaths($v, //common) intersect $v` is
equivalent to the `allpaths(foo/...,//common) intersect foo/...`.

An occurrence of a variable reference `name` other than in
an enclosing `let {{ '<var>' }}name{{ '</var>' }} = ...` expression is an
error. In other words, top-level query expressions cannot have free
variables.

In the above grammar productions, `name` is like _word_, but with the
additional constraint that it be a legal identifier in the C programming
language. References to the variable must be prepended with the "$" character.

Each `let` expression defines only a single variable, but you can nest them.

Both [target patterns](#target-patterns) and variable references consist of
just a single token, a word, creating a syntactic ambiguity. However, there is
no semantic ambiguity, because the subset of words that are legal variable
names is disjoint from the subset of words that are legal target patterns.

Technically speaking, `let` expressions do not increase
the expressiveness of the query language: any query expressible in
the language can also be expressed without them. However, they
improve the conciseness of many queries, and may also lead to more
efficient query evaluation.

### Parenthesized expressions {:#parenthesized-expressions}

```none {:.devsite-disable-click-to-copy}
expr ::= ({{ '<var>' }}expr{{ '</var>' }})
```

Parentheses associate subexpressions to force an order of evaluation.
A parenthesized expression evaluates to the value of its argument.

### Algebraic set operations: intersection, union, set difference {:#algebraic-set-operations}

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}expr{{ '</var>' }} intersect {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} ^ {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} union {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} + {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} except {{ '<var>' }}expr{{ '</var>' }}
       | {{ '<var>' }}expr{{ '</var>' }} - {{ '<var>' }}expr{{ '</var>' }}
```

These three operators compute the usual set operations over their arguments.
Each operator has two forms, a nominal form, such as `intersect`, and a
symbolic form, such as `^`. Both forms are equivalent; the symbolic forms are
quicker to type. (For clarity, the rest of this page uses the nominal forms.)

For example,

```
foo/... except foo/bar/...
```

evaluates to the set of targets that match `foo/...` but not `foo/bar/...`.

You can write the same query as:

```
foo/... - foo/bar/...
```

The `intersect` (`^`) and `union` (`+`) operations are commutative (symmetric);
`except` (`-`) is asymmetric. The parser treats all three operators as
left-associative and of equal precedence, so you might want parentheses. For
example, the first two of these expressions are equivalent, but the third is not:

```
x intersect y union z
(x intersect y) union z
x intersect (y union z)
```

Important: Use parentheses where there is any danger of ambiguity in reading a
query expression.

### Read targets from an external source: set {:#set}

```none {:.devsite-disable-click-to-copy}
expr ::= set({{ '<var>' }}word{{ '</var>' }} *)
```

The `set({{ '<var>' }}a{{ '</var>' }} {{ '<var>' }}b{{ '</var>' }} {{ '<var>' }}c{{ '</var>' }} ...)`
operator computes the union of a set of zero or more
[target patterns](#target-patterns), separated by whitespace (no commas).

In conjunction with the Bourne shell's `$(...)` feature, `set()` provides a
means of saving the results of one query in a regular text file, manipulating
that text file using other programs (such as standard UNIX shell tools), and then
introducing the result back into the query tool as a value for further
processing. For example:

```posix-terminal
bazel query deps(//my:target) --output=label | grep ... | sed ... | awk ... > foo

bazel query "kind(cc_binary, set($(<foo)))"
```

In the next example,`kind(cc_library, deps(//some_dir/foo:main, 5))` is
computed by filtering on the `maxrank` values using an `awk` program.

```posix-terminal
bazel query 'deps(//some_dir/foo:main)' --output maxrank | awk '($1 < 5) { print $2;} ' > foo

bazel query "kind(cc_library, set($(<foo)))"
```

In these examples, `$(<foo)` is a shorthand for `$(cat foo)`, but shell
commands other than `cat` may be used too—such as the previous `awk` command.

Note: `set()` introduces no graph ordering constraints, so path information may
be lost when saving and reloading sets of nodes using it. For more details,
see the [graph order](#graph-order) section below.

## Functions {:#functions}

```none {:.devsite-disable-click-to-copy}
expr ::= {{ '<var>' }}word{{ '</var>' }} '(' {{ '<var>' }}int{{ '</var>' }} | {{ '<var>' }}word{{ '</var>' }} | {{ '<var>' }}expr{{ '</var>' }} ... ')'
```

The query language defines several functions. The name of the function
determines the number and type of arguments it requires. The following
functions are available:

* [`allpaths`](#somepath-allpaths)
* [`attr`](#attr)
* [`buildfiles`](#buildfiles)
* [`rbuildfiles`](#rbuildfiles)
* [`deps`](#deps)
* [`filter`](#filter)
* [`kind`](#kind)
* [`labels`](#labels)
* [`loadfiles`](#loadfiles)
* [`rdeps`](#rdeps)
* [`allrdeps`](#allrdeps)
* [`same_pkg_direct_rdeps`](#same_pkg_direct_rdeps)
* [`siblings`](#siblings)
* [`some`](#some)
* [`somepath`](#somepath-allpaths)
* [`tests`](#tests)
* [`visible`](#visible)



### Transitive closure of dependencies: deps {:#deps}

```none {:.devsite-disable-click-to-copy}
expr ::= deps({{ '<var>' }}expr{{ '</var>' }})
       | deps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

The `deps({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the graph formed
by the transitive closure of dependencies of its argument set
{{ '<var>' }}x{{ '</var>' }}. For example, the value of `deps(//foo)` is the
dependency graph rooted at the single node `foo`, including all its
dependencies. The value of `deps(foo/...)` is the dependency graphs whose roots
are all rules in every package beneath the `foo` directory. In this context,
'dependencies' means only rule and file targets, therefore the `BUILD` and
Starlark files needed to create these targets are not included here. For that
you should use the [`buildfiles`](#buildfiles) operator.

The resulting graph is ordered according to the dependency relation. For more
details, see the section on [graph order](#graph-order).

The `deps` operator accepts an optional second argument, which is an integer
literal specifying an upper bound on the depth of the search. So
`deps(foo:*, 0)` returns all targets in the `foo` package, while
`deps(foo:*, 1)` further includes the direct prerequisites of any target in the
`foo` package, and `deps(foo:*, 2)` further includes the nodes directly
reachable from the nodes in `deps(foo:*, 1)`, and so on. (These numbers
correspond to the ranks shown in the [`minrank`](#output-ranked) output format.)
If the {{ '<var>' }}depth{{ '</var>' }} parameter is omitted, the search is
unbounded: it computes the reflexive transitive closure of prerequisites.

### Transitive closure of reverse dependencies: rdeps {:#rdeps}

```none {:.devsite-disable-click-to-copy}
expr ::= rdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
       | rdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

The `rdeps({{ '<var>' }}u{{ '</var>' }}, {{ '<var>' }}x{{ '</var>' }})`
operator evaluates to the reverse dependencies of the argument set
{{ '<var>' }}x{{ '</var>' }} within the transitive closure of the universe set
{{ '<var>' }}u{{ '</var>' }}.

The resulting graph is ordered according to the dependency relation. See the
section on [graph order](#graph-order) for more details.

The `rdeps` operator accepts an optional third argument, which is an integer
literal specifying an upper bound on the depth of the search. The resulting
graph only includes nodes within a distance of the specified depth from any
node in the argument set. So `rdeps(//foo, //common, 1)` evaluates to all nodes
in the transitive closure of `//foo` that directly depend on `//common`. (These
numbers correspond to the ranks shown in the [`minrank`](#output-ranked) output
format.) If the {{ '<var>' }}depth{{ '</var>' }} parameter is omitted, the
search is unbounded.

### Transitive closure of all reverse dependencies: allrdeps {:#allrdeps}

```
expr ::= allrdeps({{ '<var>' }}expr{{ '</var>' }})
       | allrdeps({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}depth{{ '</var>' }})
```

Note: Only available with [Sky Query](#sky-query)

The `allrdeps` operator behaves just like the [`rdeps`](#rdeps)
operator, except that the "universe set" is whatever the `--universe_scope` flag
evaluated to, instead of being separately specified. Thus, if
`--universe_scope=//foo/...` was passed, then `allrdeps(//bar)` is
equivalent to `rdeps(//foo/..., //bar)`.

### Direct reverse dependencies in the same package: same_pkg_direct_rdeps {:#same_pkg_direct_rdeps}

```
expr ::= same_pkg_direct_rdeps({{ '<var>' }}expr{{ '</var>' }})
```

The `same_pkg_direct_rdeps({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the full set of targets
that are in the same package as a target in the argument set, and which directly depend on it.

### Dealing with a target's package: siblings {:#siblings}

```
expr ::= siblings({{ '<var>' }}expr{{ '</var>' }})
```

The `siblings({{ '<var>' }}x{{ '</var>' }})` operator evaluates to the full set of targets that are in
the same package as a target in the argument set.

### Arbitrary choice: some {:#some}

```
expr ::= some({{ '<var>' }}expr{{ '</var>' }})
       | some({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}count{{ '</var> '}})
```

The `some({{ '<var>' }}x{{ '</var>' }}, {{ '<var>' }}k{{ '</var>' }})` operator
selects at most {{ '<var>' }}k{{ '</var>' }} targets arbitrarily from its
argument set {{ '<var>' }}x{{ '</var>' }}, and evaluates to a set containing
only those targets. Parameter {{ '<var>' }}k{{ '</var>' }} is optional; if
missing, the result will be a singleton set containing only one target
arbitrarily selected. If the size of argument set {{ '<var>' }}x{{ '</var>' }} is
smaller than {{ '<var>' }}k{{ '</var>' }}, the whole argument set
{{ '<var>' }}x{{ '</var>' }} will be returned.

For example, the expression `some(//foo:main union //bar:baz)` evaluates to a
singleton set containing either `//foo:main` or `//bar:baz`—though which
one is not defined. The expression `some(//foo:main union //bar:baz, 2)` or
`some(//foo:main union //bar:baz, 3)` returns both `//foo:main` and
`//bar:baz`.

If the argument is a singleton, then `some`
computes the identity function: `some(//foo:main)` is
equivalent to `//foo:main`.

It is an error if the specified argument set is empty, as in the
expression `some(//foo:main intersect //bar:baz)`.

### Path operators: somepath, allpaths {:#somepath-allpaths}

```
expr ::= somepath({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
       | allpaths({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `somepath({{ '<var>' }}S{{ '</var>' }}, {{ '<var>' }}E{{ '</var>' }})` and
`allpaths({{ '<var>' }}S{{ '</var>' }}, {{ '<var>' }}E{{ '</var>' }})` operators compute
paths between two sets of targets. Both queries accept two
arguments, a set {{ '<var>' }}S{{ '</var>' }} of starting points and a set
{{ '<var>' }}E{{ '</var>' }} of ending points. `somepath` returns the
graph of nodes on _some_ arbitrary path from a target in
{{ '<var>' }}S{{ '</var>' }} to a target in {{ '<var>' }}E{{ '</var>' }}; `allpaths`
returns the graph of nodes on _all_ paths from any target in
{{ '<var>' }}S{{ '</var>' }} to any target in {{ '<var>' }}E{{ '</var>' }}.

The resulting graphs are ordered according to the dependency relation.
See the section on [graph order](#graph-order) for more details.

<table>
  <tr>
    <td>
      <figure>
        <img src="/docs/images/somepath1.svg" alt="Somepath">
        <figcaption><code>somepath(S1 + S2, E)</code>, one possible result.</figcaption>
      </figure>
<!-- digraph somepath1 {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1;
  n2 [fillcolor="pink",style=filled];
  n3 [fillcolor="pink",style=filled];
  n4 [fillcolor="pink",style=filled,label="E"];
  n5; n6;
  n7 [fillcolor="pink",style=filled,label="S1"];
  n8 [label="S2"];
  n9;
  n10 [fillcolor="pink",style=filled];
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
    <td>
      <figure>
        <img src="/docs/images/somepath2.svg" alt="Somepath">
        <figcaption><code>somepath(S1 + S2, E)</code>, another possible result.</figcaption>
      </figure>
<!-- digraph somepath2 {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1; n2; n3;
  n4 [fillcolor="pink",style=filled,label="E"];
  n5;
  n6 [fillcolor="pink",style=filled];
  n7 [label="S1"];
  n8 [fillcolor="pink",style=filled,label="S2"];
  n9; n10;
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
    <td>
      <figure>
        <img src="/docs/images/allpaths.svg" alt="Allpaths">
        <figcaption><code>allpaths(S1 + S2, E)</code></figcaption>
      </figure>
<!-- digraph allpaths {
  graph [size="4,4"]
  node [label="",shape=circle];
  n1;
  n2 [fillcolor="pink",style=filled];
  n3 [fillcolor="pink",style=filled];
  n4 [fillcolor="pink",style=filled,label="E"];
  n5 [fillcolor="pink",style=filled];
  n6 [fillcolor="pink",style=filled];
  n7 [fillcolor="pink",style=filled, label="S1"];
  n8 [fillcolor="pink",style=filled, label="S2"];
  n9;
  n10 [fillcolor="pink",style=filled];
  n1 -> n2;
  n2 -> n3;
  n7 -> n5;
  n7 -> n2;
  n5 -> n6;
  n6 -> n4;
  n8 -> n6;
  n6 -> n9;
  n2 -> n10;
  n3 -> n10;
  n10 -> n4;
  n10 -> n11;
} -->
    </td>
  </tr>
</table>

### Target kind filtering: kind {:#kind}

```
expr ::= kind({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `kind({{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards those targets
that are not of the expected kind. The {{ '<var>' }}pattern{{ '</var>' }}
parameter specifies what kind of target to match.

For example, the kinds for the four targets defined by the `BUILD` file
(for package `p`) shown below are illustrated in the table:

<table>
  <tr>
    <th>Code</th>
    <th>Target</th>
    <th>Kind</th>
  </tr>
  <tr>
    <td rowspan="4">
      <pre>
        genrule(
            name = "a",
            srcs = ["a.in"],
            outs = ["a.out"],
            cmd = "...",
        )
      </pre>
    </td>
    <td><code>//p:a</code></td>
    <td>genrule rule</td>
  </tr>
  <tr>
    <td><code>//p:a.in</code></td>
    <td>source file</td>
  </tr>
  <tr>
    <td><code>//p:a.out</code></td>
    <td>generated file</td>
  </tr>
  <tr>
    <td><code>//p:BUILD</code></td>
    <td>source file</td>
  </tr>
</table>

Thus, `kind("cc_.* rule", foo/...)` evaluates to the set
of all `cc_library`, `cc_binary`, etc,
rule targets beneath `foo`, and `kind("source file", deps(//foo))`
evaluates to the set of all source files in the transitive closure
of dependencies of the `//foo` target.

Quotation of the {{ '<var>' }}pattern{{ '</var>' }} argument is often required
because without it, many [regular expressions](#regex), such as `source
file` and `.*_test`, are not considered words by the parser.

When matching for `package group`, targets ending in
`:all` may not yield any results. Use `:all-targets` instead.

### Target name filtering: filter {:#filter}

```
expr ::= filter({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `filter({{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards targets whose
labels (in absolute form) do not match the pattern; it
evaluates to a subset of its input.

The first argument, {{ '<var>' }}pattern{{ '</var>' }} is a word containing a
[regular expression](#regex) over target names. A `filter` expression
evaluates to the set containing all targets {{ '<var>' }}x{{ '</var>' }} such that
{{ '<var>' }}x{{ '</var>' }} is a member of the set {{ '<var>' }}input{{ '</var>' }} and the
label (in absolute form, such as `//foo:bar`)
of {{ '<var>' }}x{{ '</var>' }} contains an (unanchored) match
for the regular expression {{ '<var>' }}pattern{{ '</var>' }}. Since all
target names start with `//`, it may be used as an alternative
to the `^` regular expression anchor.

This operator often provides a much faster and more robust alternative to the
`intersect` operator. For example, in order to see all
`bar` dependencies of the `//foo:foo` target, one could
evaluate

```
deps(//foo) intersect //bar/...
```

This statement, however, will require parsing of all `BUILD` files in the
`bar` tree, which will be slow and prone to errors in
irrelevant `BUILD` files. An alternative would be:

```
filter(//bar, deps(//foo))
```

which would first calculate the set of `//foo` dependencies and
then would filter only targets matching the provided pattern—in other
words, targets with names containing `//bar` as a substring.

Another common use of the `filter({{ '<var>' }}pattern{{ '</var>' }},
{{ '<var>' }}expr{{ '</var>' }})` operator is to filter specific files by their
name or extension. For example,

```
filter("\.cc$", deps(//foo))
```

will provide a list of all `.cc` files used to build `//foo`.

### Rule attribute filtering: attr {:#attr}

```
expr ::= attr({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The
`attr({{ '<var>' }}name{{ '</var>' }}, {{ '<var>' }}pattern{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})`
operator applies a filter to a set of targets, and discards targets that aren't
rules, rule targets that do not have attribute {{ '<var>' }}name{{ '</var>' }}
defined or rule targets where the attribute value does not match the provided
[regular expression](#regex) {{ '<var>' }}pattern{{ '</var>' }}; it evaluates
to a subset of its input.

The first argument, {{ '<var>' }}name{{ '</var>' }} is the name of the rule
attribute that should be matched against the provided
[regular expression](#regex) pattern. The second argument,
{{ '<var>' }}pattern{{ '</var>' }} is a regular expression over the attribute
values. An `attr` expression evaluates to the set containing all targets
{{ '<var>' }}x{{ '</var>' }} such that  {{ '<var>' }}x{{ '</var>' }} is a
member of the set {{ '<var>' }}input{{ '</var>' }}, is a rule with the defined
attribute {{ '<var>' }}name{{ '</var>' }} and the attribute value contains an
(unanchored) match for the regular expression
{{ '<var>' }}pattern{{ '</var>' }}. If {{ '<var>' }}name{{ '</var>' }} is an
optional attribute and rule does not specify it explicitly then default
attribute value will be used for comparison. For example,

```
attr(linkshared, 0, deps(//foo))
```

will select all `//foo` dependencies that are allowed to have a
linkshared attribute (such as, `cc_binary` rule) and have it either
explicitly set to 0 or do not set it at all but default value is 0 (such as for
`cc_binary` rules).

List-type attributes (such as `srcs`, `data`, etc) are
converted to strings of the form `[value<sub>1</sub>, ..., value<sub>n</sub>]`,
starting with a `[` bracket, ending with a `]` bracket
and using "`, `" (comma, space) to delimit multiple values.
Labels are converted to strings by using the absolute form of the
label. For example, an attribute `deps=[":foo",
"//otherpkg:bar", "wiz"]` would be converted to the
string `[//thispkg:foo, //otherpkg:bar, //thispkg:wiz]`.
Brackets are always present, so the empty list would use string value `[]`
for matching purposes. For example,

```
attr("srcs", "\[\]", deps(//foo))
```

will select all rules among `//foo` dependencies that have an
empty `srcs` attribute, while

```
attr("data", ".{3,}", deps(//foo))
```

will select all rules among `//foo` dependencies that specify at
least one value in the `data` attribute (every label is at least
3 characters long due to the `//` and `:`).

To select all rules among `//foo` dependencies with a particular `value` in a
list-type attribute, use

```
attr("tags", "[\[ ]value[,\]]", deps(//foo))
```

This works because the character before `value` will be `[` or a space and the
character after `value` will be a comma or `]`.

To select all rules among `//foo` dependencies with a particular `key` and
`value` in a dict-type attribute, use

```
attr("some_dict_attribute", "[\{ ]key=value[,\}]", deps(//foo))
```

This would select `//foo` if `//foo` is defined as

```
some_rule(
  name = "foo",
  some_dict_attribute = {
    "key": "value",
  },
)
```

This works because the character before `key=value` will be `{` or a space and
the character after `key=value` will be a comma or `}`.

### Rule visibility filtering: visible {:#visible}

```
expr ::= visible({{ '<var>' }}expr{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `visible({{ '<var>' }}predicate{{ '</var>' }}, {{ '<var>' }}input{{ '</var>' }})` operator
applies a filter to a set of targets, and discards targets without the
required visibility.

The first argument, {{ '<var>' }}predicate{{ '</var>' }}, is a set of targets that all targets
in the output must be visible to. A {{ '<var>' }}visible{{ '</var>' }} expression
evaluates to the set containing all targets {{ '<var>' }}x{{ '</var>' }} such that {{ '<var>' }}x{{ '</var>' }}
is a member of the set {{ '<var>' }}input{{ '</var>' }}, and for all targets {{ '<var>' }}y{{ '</var>' }} in
{{ '<var>' }}predicate{{ '</var>' }} {{ '<var>' }}x{{ '</var>' }} is visible to {{ '<var>' }}y{{ '</var>' }}. For example:

```
visible(//foo, //bar:*)
```

will select all targets in the package `//bar` that `//foo`
can depend on without violating visibility restrictions.

### Evaluation of rule attributes of type label: labels {:#labels}

```
expr ::= labels({{ '<var>' }}word{{ '</var>' }}, {{ '<var>' }}expr{{ '</var>' }})
```

The `labels({{ '<var>' }}attr_name{{ '</var>' }}, {{ '<var>' }}inputs{{ '</var>' }})`
operator returns the set of targets specified in the
attribute {{ '<var>' }}attr_name{{ '</var>' }} of type "label" or "list of label" in
some rule in set {{ '<var>' }}inputs{{ '</var>' }}.

For example, `labels(srcs, //foo)` returns the set of
targets appearing in the `srcs` attribute of
the `//foo` rule. If there are multiple rules
with `srcs` attributes in the {{ '<var>' }}inputs{{ '</var>' }} set, the
union of their `srcs` is returned.

### Expand and filter test_suites: tests {:#tests}

```
expr ::= tests({{ '<var>' }}expr{{ '</var>' }})
```

The `tests({{ '<var>' }}x{{ '</var>' }})` operator returns the set of all test
rules in set {{ '<var>' }}x{{ '</var>' }}, expanding any `test_suite` rules into
the set of individual tests that they refer to, and applying filtering by
`tag` and `size`.

By default, query evaluation
ignores any non-test targets in all `test_suite` rules. This can be
changed to errors with the `--strict_test_suite` option.

For example, the query `kind(test, foo:*)` lists all
the `*_test` and `test_suite` rules
in the `foo` package. All the results are (by
definition) members of the `foo` package. In contrast,
the query `tests(foo:*)` will return all of the
individual tests that would be executed by `bazel test
foo:*`: this may include tests belonging to other packages,
that are referenced directly or indirectly
via `test_suite` rules.

### Package definition files: buildfiles {:#buildfiles}

```
expr ::= buildfiles({{ '<var>' }}expr{{ '</var>' }})
```

The `buildfiles({{ '<var>' }}x{{ '</var>' }})` operator returns the set
of files that define the packages of each target in
set {{ '<var>' }}x{{ '</var>' }}; in other words, for each package, its `BUILD` file,
plus any .bzl files it references via `load`. Note that this
also returns the `BUILD` files of the packages containing these
`load`ed files.

This operator is typically used when determining what files or
packages are required to build a specified target, often in conjunction with
the [`--output package`](#output-package) option, below). For example,

```posix-terminal
bazel query 'buildfiles(deps(//foo))' --output package
```

returns the set of all packages on which `//foo` transitively depends.

Note: A naive attempt at the above query would omit
the `buildfiles` operator and use only `deps`,
but this yields an incorrect result: while the result contains the
majority of needed packages, those packages that contain only files
that are `load()`'ed will be missing.

Warning: Bazel pretends each `.bzl` file produced by
`buildfiles` has a corresponding target (for example, file `a/b.bzl` =>
target `//a:b.bzl`), but this isn't necessarily the case. Therefore,
`buildfiles` doesn't compose well with other query operators and its results can be
misleading when formatted in a structured way, such as
[`--output=xml`](#xml).

### Package definition files: rbuildfiles {:#rbuildfiles}

```
expr ::= rbuildfiles({{ '<var>' }}word{{ '</var>' }}, ...)
```

Note: Only available with [Sky Query](#sky-query).

The `rbuildfiles` operator takes a comma-separated list of path fragments and returns
the set of `BUILD` files that transitively depend on these path fragments. For instance, if
`//foo` is a package, then `rbuildfiles(foo/BUILD)` will return the
`//foo:BUILD` target. If the `foo/BUILD` file has
`load('//bar:file.bzl'...` in it, then `rbuildfiles(bar/file.bzl)` will
return the `//foo:BUILD` target, as well as the targets for any other `BUILD` files that
load `//bar:file.bzl`

The scope of the <scope>rbuildfiles</scope> operator is the universe specified by the
`--universe_scope` flag. Files that do not correspond directly to `BUILD` files and `.bzl`
files do not affect the results. For instance, source files (like `foo.cc`) are ignored,
even if they are explicitly mentioned in the `BUILD` file. Symlinks, however, are respected, so that
if `foo/BUILD` is a symlink to `bar/BUILD`, then
`rbuildfiles(bar/BUILD)` will include `//foo:BUILD` in its results.

The `rbuildfiles` operator is almost morally the inverse of the
[`buildfiles`](#buildfiles) operator. However, this moral inversion
holds more strongly in one direction: the outputs of `rbuildfiles` are just like the
inputs of `buildfiles`; the former will only contain `BUILD` file targets in packages,
and the latter may contain such targets. In the other direction, the correspondence is weaker. The
outputs of the `buildfiles` operator are targets corresponding to all packages and .`bzl`
files needed by a given input. However, the inputs of the `rbuildfiles` operator are
not those targets, but rather the path fragments that correspond to those targets.

### Package definition files: loadfiles {:#loadfiles}

```
expr ::= loadfiles({{ '<var>' }}expr{{ '</var>' }})
```

The `loadfiles({{ '<var>' }}x{{ '</var>' }})` operator returns the set of
Starlark files that are needed to load the packages of each target in
set {{ '<var>' }}x{{ '</var>' }}. In other words, for each package, it returns the
.bzl files that are referenced from its `BUILD` files.

Warning: Bazel pretends each of these .bzl files has a corresponding target
(for example, file `a/b.bzl` => target `//a:b.bzl`), but this isn't
necessarily the case. Therefore, `loadfiles` doesn't compose well with other query
operators and its results can be misleading when formatted in a structured way, such as
[`--output=xml`](#xml).

## Output formats {:#output-formats}

`bazel query` generates a graph.
You specify the content, format, and ordering by which
`bazel query` presents this graph
by means of the `--output` command-line option.

When running with [Sky Query](#sky-query), only output formats that are compatible with
unordered output are allowed. Specifically, `graph`, `minrank`, and
`maxrank` output formats are forbidden.

Some of the output formats accept additional options. The name of
each output option is prefixed with the output format to which it
applies, so `--graph:factored` applies only
when `--output=graph` is being used; it has no effect if
an output format other than `graph` is used. Similarly,
`--xml:line_numbers` applies only when `--output=xml`
is being used.

### On the ordering of results {:#results-ordering}

Although query expressions always follow the "[law of
conservation of graph order](#graph-order)", _presenting_ the results may be done
in either a dependency-ordered or unordered manner. This does **not**
influence the targets in the result set or how the query is computed. It only
affects how the results are printed to stdout. Moreover, nodes that are
equivalent in the dependency order may or may not be ordered alphabetically.
The `--order_output` flag can be used to control this behavior.
(The `--[no]order_results` flag has a subset of the functionality
of the `--order_output` flag and is deprecated.)

The default value of this flag is `auto`, which prints results in **lexicographical
order**. However, when `somepath(a,b)` is used, the results will be printed in
`deps` order instead.

When this flag is `no` and `--output` is one of
`build`, `label`, `label_kind`, `location`, `package`, `proto`, or
`xml`, the outputs will be printed in arbitrary order. **This is
generally the fastest option**. It is not supported though when
`--output` is one of `graph`, `minrank` or
`maxrank`: with these formats, Bazel always prints results
ordered by the dependency order or rank.

When this flag is `deps`, Bazel prints results in some topological order—that is,
dependents first and dependencies after. However, nodes that are unordered by the
dependency order (because there is no path from either one to the other) may be
printed in any order.

When this flag is `full`, Bazel prints nodes in a fully deterministic (total) order.
First, all nodes are sorted alphabetically. Then, each node in the list is used as the start of a
post-order depth-first search in which outgoing edges to unvisited nodes are traversed in
alphabetical order of the successor nodes. Finally, nodes are printed in the reverse of the order
in which they were visited.

Printing nodes in this order may be slower, so it should be used only when determinism is
important.

### Print the source form of targets as they would appear in BUILD {:#target-source-form}

```
--output build
```

With this option, the representation of each target is as if it were
hand-written in the BUILD language. All variables and function calls
(such as glob, macros) are expanded, which is useful for seeing the effect
of Starlark macros. Additionally, each effective rule reports a
`generator_name` and/or `generator_function`) value,
giving the name of the macro that was evaluated to produce the effective rule.

Although the output uses the same syntax as `BUILD` files, it is not
guaranteed to produce a valid `BUILD` file.

### Print the label of each target {:#print-label-target}

```
--output label
```

With this option, the set of names (or _labels_) of each target
in the resulting graph is printed, one label per line, in
topological order (unless `--noorder_results` is specified, see
[notes on the ordering of results](#result-order)).
(A topological ordering is one in which a graph
node appears earlier than all of its successors.)  Of course there
are many possible topological orderings of a graph (_reverse
postorder_ is just one); which one is chosen is not specified.

When printing the output of a `somepath` query, the order
in which the nodes are printed is the order of the path.

Caveat: in some corner cases, there may be two distinct targets with
the same label; for example, a `sh_binary` rule and its
sole (implicit) `srcs` file may both be called
`foo.sh`. If the result of a query contains both of
these targets, the output (in `label` format) will appear
to contain a duplicate. When using the `label_kind` (see
below) format, the distinction becomes clear: the two targets have
the same name, but one has kind `sh_binary rule` and the
other kind `source file`.

### Print the label and kind of each target {:#print-target-label}

```
--output label_kind
```

Like `label`, this output format prints the labels of
each target in the resulting graph, in topological order, but it
additionally precedes the label by the [_kind_](#kind) of the target.

### Print targets in protocol buffer format {:#print-target-proto}

```
--output proto
```

Prints the query output as a
[`QueryResult`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffer.

### Print targets in length-delimited protocol buffer format {:#print-target-length-delimited-proto}

```
--output streamed_proto
```

Prints a
[length-delimited](https://protobuf.dev/programming-guides/encoding/#size-limit)
stream of
[`Target`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffers. This is useful to _(i)_ get around
[size limitations](https://protobuf.dev/programming-guides/encoding/#size-limit)
of protocol buffers when there are too many targets to fit in a single
`QueryResult` or _(ii)_ to start processing while Bazel is still outputting.

### Print targets in text proto format {:#print-target-textproto}

```
--output textproto
```

Similar to `--output proto`, prints the
[`QueryResult`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffer but in
[text format](https://protobuf.dev/reference/protobuf/textformat-spec/).

### Print targets in ndjson format {:#print-target-streamed-jsonproto}

```
--output streamed_jsonproto
```

Similar to `--output streamed_proto`, prints a stream of
[`Target`](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/build.proto)
protocol buffers but in [ndjson](https://github.com/ndjson/ndjson-spec) format.

### Print the label of each target, in rank order {:#print-target-label-rank-order}

```
--output minrank --output maxrank
```

Like `label`, the `minrank`
and `maxrank` output formats print the labels of each
target in the resulting graph, but instead of appearing in
topological order, they appear in rank order, preceded by their
rank number. These are unaffected by the result ordering
`--[no]order_results` flag (see [notes on
the ordering of results](#result-order)).

There are two variants of this format: `minrank` ranks
each node by the length of the shortest path from a root node to it.
"Root" nodes (those which have no incoming edges) are of rank 0,
their successors are of rank 1, etc. (As always, edges point from a
target to its prerequisites: the targets it depends upon.)

`maxrank` ranks each node by the length of the longest
path from a root node to it. Again, "roots" have rank 0, all other
nodes have a rank which is one greater than the maximum rank of all
their predecessors.

All nodes in a cycle are considered of equal rank. (Most graphs are
acyclic, but cycles do occur
simply because `BUILD` files contain erroneous cycles.)

These output formats are useful for discovering how deep a graph is.
If used for the result of a `deps(x)`, `rdeps(x)`,
or `allpaths` query, then the rank number is equal to the
length of the shortest (with `minrank`) or longest
(with `maxrank`) path from `x` to a node in
that rank. `maxrank` can be used to determine the
longest sequence of build steps required to build a target.

Note: The ranked output of a `somepath` query is
basically meaningless because `somepath` doesn't
guarantee to return either a shortest or a longest path, and it may
include "transitive" edges from one path node to another that are
not direct edges in original graph.

For example, the graph on the left yields the outputs on the right
when `--output minrank` and `--output maxrank`
are specified, respectively.

<table>
  <tr>
    <td><img src="/docs/images/out-ranked.svg" alt="Out ranked">
    </td>
    <td>
      <pre>
      minrank

      0 //c:c
      1 //b:b
      1 //a:a
      2 //b:b.cc
      2 //a:a.cc
      </pre>
    </td>
    <td>
      <pre>
      maxrank

      0 //c:c
      1 //b:b
      2 //a:a
      2 //b:b.cc
      3 //a:a.cc
      </pre>
    </td>
  </tr>
</table>

### Print the location of each target {:#print-target-location}

```
--output location
```

Like `label_kind`, this option prints out, for each
target in the result, the target's kind and label, but it is
prefixed by a string describing the location of that target, as a
filename and line number. The format resembles the output of
`grep`. Thus, tools that can parse the latter (such as Emacs
or vi) can also use the query output to step through a series of
matches, allowing the Bazel query tool to be used as a
dependency-graph-aware "grep for BUILD files".

The location information varies by target kind (see the [kind](#kind) operator). For rules, the
location of the rule's declaration within the `BUILD` file is printed.
For source files, the location of line 1 of the actual file is
printed. For a generated file, the location of the rule that
generates it is printed. (The query tool does not have sufficient
information to find the actual location of the generated file, and
in any case, it might not exist if a build has not yet been performed.)

### Print the set of packages {:#print-package-set}

```--output package```

This option prints the name of all packages to which
some target in the result set belongs. The names are printed in
lexicographical order; duplicates are excluded. Formally, this
is a _projection_ from the set of labels (package, target) onto
packages.

Packages in external repositories are formatted as
`@repo//foo/bar` while packages in the main repository are
formatted as `foo/bar`.

In conjunction with the `deps(...)` query, this output
option can be used to find the set of packages that must be checked
out in order to build a given set of targets.

### Display a graph of the result {:#display-result-graph}

```--output graph```

This option causes the query result to be printed as a directed
graph in the popular AT&amp;T GraphViz format. Typically the
result is saved to a file, such as `.png` or `.svg`.
(If the `dot` program is not installed on your workstation, you
can install it using the command `sudo apt-get install graphviz`.)
See the example section below for a sample invocation.

This output format is particularly useful for `allpaths`,
`deps`, or `rdeps` queries, where the result
includes a _set of paths_ that cannot be easily visualized when
rendered in a linear form, such as with `--output label`.

By default, the graph is rendered in a _factored_ form. That is,
topologically-equivalent nodes are merged together into a single
node with multiple labels. This makes the graph more compact
and readable, because typical result graphs contain highly
repetitive patterns. For example, a `java_library` rule
may depend on hundreds of Java source files all generated by the
same `genrule`; in the factored graph, all these files
are represented by a single node. This behavior may be disabled
with the `--nograph:factored` option.

#### `--graph:node_limit {{ '<var>' }}n{{ '</var>' }}` {:#graph-nodelimit}

The option specifies the maximum length of the label string for a
graph node in the output. Longer labels will be truncated; -1
disables truncation. Due to the factored form in which graphs are
usually printed, the node labels may be very long. GraphViz cannot
handle labels exceeding 1024 characters, which is the default value
of this option. This option has no effect unless
`--output=graph` is being used.

#### `--[no]graph:factored` {:#graph-factored}

By default, graphs are displayed in factored form, as explained
[above](#output-graph).
When `--nograph:factored` is specified, graphs are
printed without factoring. This makes visualization using GraphViz
impractical, but the simpler format may ease processing by other
tools (such as grep). This option has no effect
unless `--output=graph` is being used.

### XML {:#xml}

```--output xml```

This option causes the resulting targets to be printed in an XML
form. The output starts with an XML header such as this

```
  <?xml version="1.0" encoding="UTF-8"?>
  <query version="2">
```

<!-- The docs should continue to document version 2 into perpetuity,
     even if we add new formats, to handle clients synced to old CLs. -->

and then continues with an XML element for each target
in the result graph, in topological order (unless
[unordered results](#result-order) are requested),
and then finishes with a terminating

```
</query>
```

Simple entries are emitted for targets of `file` kind:

```
  <source-file name='//foo:foo_main.cc' .../>
  <generated-file name='//foo:libfoo.so' .../>
```

But for rules, the XML is structured and contains definitions of all
the attributes of the rule, including those whose value was not
explicitly specified in the rule's `BUILD` file.

Additionally, the result includes `rule-input` and
`rule-output` elements so that the topology of the
dependency graph can be reconstructed without having to know that,
for example, the elements of the `srcs` attribute are
forward dependencies (prerequisites) and the contents of the
`outs` attribute are backward dependencies (consumers).

`rule-input` elements for [implicit dependencies](#implicit_deps) are suppressed if
`--noimplicit_deps` is specified.

```
  <rule class='cc_binary rule' name='//foo:foo' ...>
    <list name='srcs'>
      <label value='//foo:foo_main.cc'/>
      <label value='//foo:bar.cc'/>
      ...
    </list>
    <list name='deps'>
      <label value='//common:common'/>
      <label value='//collections:collections'/>
      ...
    </list>
    <list name='data'>
      ...
    </list>
    <int name='linkstatic' value='0'/>
    <int name='linkshared' value='0'/>
    <list name='licenses'/>
    <list name='distribs'>
      <distribution value="INTERNAL" />
    </list>
    <rule-input name="//common:common" />
    <rule-input name="//collections:collections" />
    <rule-input name="//foo:foo_main.cc" />
    <rule-input name="//foo:bar.cc" />
    ...
  </rule>
```

Every XML element for a target contains a `name`
attribute, whose value is the target's label, and
a `location` attribute, whose value is the target's
location as printed by the [`--output location`](#print-target-location).

#### `--[no]xml:line_numbers` {:#xml-linenumbers}

By default, the locations displayed in the XML output contain line numbers.
When `--noxml:line_numbers` is specified, line numbers are not printed.

#### `--[no]xml:default_values` {:#xml-defaultvalues}

By default, XML output does not include rule attribute whose value
is the default value for that kind of attribute (for example, if it
were not specified in the `BUILD` file, or the default value was
provided explicitly). This option causes such attribute values to
be included in the XML output.

### Regular expressions {:#regular-expressions}

Regular expressions in the query language use the Java regex library, so you can use the
full syntax for
[`java.util.regex.Pattern`](https://docs.oracle.com/javase/8/docs/api/java/util/regex/Pattern.html){: .external}.

### Querying with external repositories {:#querying-external-repositories}

If the build depends on rules from [external repositories](/external/overview)
then query results will include these dependencies. For
example, if `//foo:bar` depends on `@other-repo//baz:lib`, then
`bazel query 'deps(//foo:bar)'` will list `@other-repo//baz:lib` as a
dependency.


Project: /_project.yaml
Book: /_book.yaml

#  Configurable Query (cquery)

{% include "_buttons.html" %}

`cquery` is a variant of [`query`](/query/language) that correctly handles
[`select()`](/docs/configurable-attributes) and build options' effects on the build
graph.

It achieves this by running over the results of Bazel's [analysis
phase](/extending/concepts#evaluation-model),
which integrates these effects. `query`, by contrast, runs over the results of
Bazel's loading phase, before options are evaluated.

For example:

<pre>
$ cat > tree/BUILD &lt;&lt;EOF
sh_library(
    name = "ash",
    deps = select({
        ":excelsior": [":manna-ash"],
        ":americana": [":white-ash"],
        "//conditions:default": [":common-ash"],
    }),
)
sh_library(name = "manna-ash")
sh_library(name = "white-ash")
sh_library(name = "common-ash")
config_setting(
    name = "excelsior",
    values = {"define": "species=excelsior"},
)
config_setting(
    name = "americana",
    values = {"define": "species=americana"},
)
EOF
</pre>

<pre>
# Traditional query: query doesn't know which select() branch you will choose,
# so it conservatively lists all of possible choices, including all used config_settings.
$ bazel query "deps(//tree:ash)" --noimplicit_deps
//tree:americana
//tree:ash
//tree:common-ash
//tree:excelsior
//tree:manna-ash
//tree:white-ash

# cquery: cquery lets you set build options at the command line and chooses
# the exact dependencies that implies (and also the config_setting targets).
$ bazel cquery "deps(//tree:ash)" --define species=excelsior --noimplicit_deps
//tree:ash (9f87702)
//tree:manna-ash (9f87702)
//tree:americana (9f87702)
//tree:excelsior (9f87702)
</pre>

Each result includes a [unique identifier](#configurations) `(9f87702)` of
the [configuration](/reference/glossary#configuration) the
target is built with.

Since `cquery` runs over the configured target graph. it doesn't have insight
into artifacts like build actions nor access to [`test_suite`](/reference/be/general#test_suite)
rules as they are not configured targets. For the former, see [`aquery`](/query/aquery).

## Basic syntax {:#basic-syntax}

A simple `cquery` call looks like:

`bazel cquery "function(//target)"`

The query expression `"function(//target)"` consists of the following:

*   **`function(...)`** is the function to run on the target. `cquery`
    supports most
    of `query`'s [functions](/query/language#functions), plus a
    few new ones.
*   **`//target`** is the expression fed to the function. In this example, the
    expression is a simple target. But the query language also allows nesting of functions.
    See the [Query guide](/query/guide) for examples.


`cquery` requires a target to run through the [loading and analysis](/extending/concepts#evaluation-model)
phases. Unless otherwise specified, `cquery` parses the target(s) listed in the
query expression. See [`--universe_scope`](#universe-scope)
for querying dependencies of top-level build targets.

## Configurations {:#configurations}

The line:

<pre>
//tree:ash (9f87702)
</pre>

means `//tree:ash` was built in a configuration with ID `9f87702`. For most
targets, this is an opaque hash of the build option values defining the
configuration.

To see the configuration's complete contents, run:

<pre>
$ bazel config 9f87702
</pre>

`9f87702` is a prefix of the complete ID. This is because complete IDs are
SHA-256 hashes, which are long and hard to follow. `cquery` understands any valid
prefix of a complete ID, similar to
[Git short hashes](https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection#_revision_selection){: .external}.
 To see complete IDs, run `$ bazel config`.

## Target pattern evaluation {:#target-pattern-evaluation}

`//foo` has a different meaning for `cquery` than for `query`. This is because
`cquery` evaluates _configured_ targets and the build graph may have multiple
configured versions of `//foo`.

For `cquery`, a target pattern in the query expression evaluates
to every configured target with a label that matches that pattern. Output is
deterministic, but `cquery` makes no ordering guarantee beyond the
[core query ordering contract](/query/language#graph-order).

This produces subtler results for query expressions than with `query`.
For example, the following can produce multiple results:

<pre>
# Analyzes //foo in the target configuration, but also analyzes
# //genrule_with_foo_as_tool which depends on an exec-configured
# //foo. So there are two configured target instances of //foo in
# the build graph.
$ bazel cquery //foo --universe_scope=//foo,//genrule_with_foo_as_tool
//foo (9f87702)
//foo (exec)
</pre>

If you want to precisely declare which instance to query over, use
the [`config`](#config) function.

See `query`'s [target pattern
documentation](/query/language#target-patterns) for more information on target patterns.

## Functions {:#functions}

Of the [set of functions](/query/language#functions "list of query functions")
supported by `query`, `cquery` supports all but
[`allrdeps`](/query/language#allrdeps),
[`buildfiles`](/query/language#buildfiles),
[`rbuildfiles`](/query/language#rbuildfiles),
[`siblings`](/query/language#siblings), [`tests`](/query/language#tests), and
[`visible`](/query/language#visible).

`cquery` also introduces the following new functions:

### config {:#config}

`expr ::= config(expr, word)`

The `config` operator attempts to find the configured target for
the label denoted by the first argument and configuration specified by the
second argument.

Valid values for the second argument are `null` or a
[custom configuration hash](#configurations). Hashes can be retrieved from `$
bazel config` or a previous `cquery`'s output.

Examples:

<pre>
$ bazel cquery "config(//bar, 3732cc8)" --universe_scope=//foo
</pre>

<pre>
$ bazel cquery "deps(//foo)"
//bar (exec)
//baz (exec)

$ bazel cquery "config(//baz, 3732cc8)"
</pre>

If not all results of the first argument can be found in the specified
configuration, only those that can be found are returned. If no results
can be found in the specified configuration, the query fails.

## Options {:#options}

### Build options {:#build-options}

`cquery` runs over a regular Bazel build and thus inherits the set of
[options](/reference/command-line-reference#build-options) available during a build.

###  Using cquery options {:#using-cquery-options}

#### `--universe_scope` (comma-separated list) {:#universe-scope}

Often, the dependencies of configured targets go through
[transitions](/extending/rules#configurations),
which causes their configuration to differ from their dependent. This flag
allows you to query a target as if it were built as a dependency or a transitive
dependency of another target. For example:

<pre>
# x/BUILD
genrule(
     name = "my_gen",
     srcs = ["x.in"],
     outs = ["x.cc"],
     cmd = "$(locations :tool) $&lt; >$@",
     tools = [":tool"],
)
cc_binary(
    name = "tool",
    srcs = ["tool.cpp"],
)
</pre>

Genrules configure their tools in the
[exec configuration](/extending/rules#configurations)
so the following queries would produce the following outputs:

<table class="table table-condensed table-bordered table-params">
  <thead>
    <tr>
      <th>Query</th>
      <th>Target Built</th>
      <th>Output</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>bazel cquery "//x:tool"</td>
      <td>//x:tool</td>
      <td>//x:tool(targetconfig)</td>
    </tr>
    <tr>
      <td>bazel cquery "//x:tool" --universe_scope="//x:my_gen"</td>
      <td>//x:my_gen</td>
      <td>//x:tool(execconfig)</td>
    </tr>
  </tbody>
</table>

If this flag is set, its contents are built. _If it's not set, all targets
mentioned in the query expression are built_ instead. The transitive closure of the
built targets are used as the universe of the query. Either way, the targets to
be built must be buildable at the top level (that is, compatible with top-level
options). `cquery` returns results in the transitive closure of these
top-level targets.

Even if it's possible to build all targets in a query expression at the top
level, it may be beneficial to not do so. For example, explicitly setting
`--universe_scope` could prevent building targets multiple times in
configurations you don't care about. It could also help specify which configuration version of a
target you're looking for (since it's not currently possible
to fully specify this any other way). You should set this flag
if your query expression is more complex than `deps(//foo)`.

#### `--implicit_deps` (boolean, default=True) {:#implicit-deps}

Setting this flag to false filters out all results that aren't explicitly set in
the BUILD file and instead set elsewhere by Bazel. This includes filtering resolved
toolchains.

#### `--tool_deps` (boolean, default=True) {:#tool-deps}

Setting this flag to false filters out all configured targets for which the
path from the queried target to them crosses a transition between the target
configuration and the
[non-target configurations](/extending/rules#configurations).
If the queried target is in the target configuration, setting `--notool_deps` will
only return targets that also are in the target configuration. If the queried
target is in a non-target configuration, setting `--notool_deps` will only return
targets also in non-target configurations. This setting generally does not affect filtering
of resolved toolchains.

#### `--include_aspects` (boolean, default=True) {:#include-aspects}

Include dependencies added by [aspects](/extending/aspects).

If this flag is disabled, `cquery somepath(X, Y)` and
`cquery deps(X) | grep 'Y'` omit Y if X only depends on it through an aspect.

## Output formats {:#output-formats}

By default, cquery outputs results in a dependency-ordered list of label and configuration pairs.
There are other options for exposing the results as well.

### Transitions {:#transitions}

<pre>
--transitions=lite
--transitions=full
</pre>

Configuration [transitions](/extending/rules#configurations)
are used to build targets underneath the top level targets in different
configurations than the top level targets.

For example, a target might impose a transition to the exec configuration on all
dependencies in its `tools` attribute. These are known as attribute
transitions. Rules can also impose transitions on their own configurations,
known as rule class transitions. This output format outputs information about
these transitions such as what type they are and the effect they have on build
options.

This output format is triggered by the `--transitions` flag which by default is
set to `NONE`. It can be set to `FULL` or `LITE` mode. `FULL` mode outputs
information about rule class transitions and attribute transitions including a
detailed diff of the options before and after the transition. `LITE` mode
outputs the same information without the options diff.

### Protocol message output {:#protocol-message-output}

<pre>
--output=proto
</pre>

This option causes the resulting targets to be printed in a binary protocol
buffer form. The definition of the protocol buffer can be found at
[src/main/protobuf/analysis_v2.proto](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/analysis_v2.proto){: .external}.

`CqueryResult` is the top level message containing the results of the cquery. It
has a list of `ConfiguredTarget` messages and a list of `Configuration`
messages. Each `ConfiguredTarget` has a `configuration_id` whose value is equal
to that of the `id` field from the corresponding `Configuration` message.

#### --[no]proto:include_configurations {:#proto-include-configurations}

By default, cquery results return configuration information as part of each
configured target. If you'd like to omit this information and get proto output
that is formatted exactly like query's proto output, set this flag to false.

See [query's proto output documentation](/query/language#output-formats)
for more proto output-related options.

Note: While selects are resolved both at the top level of returned
targets and within attributes, all possible inputs for selects are still
included as `rule_input` fields.

### Graph output {:#graph-output}

<pre>
--output=graph
</pre>

This option generates output as a Graphviz-compatible .dot file. See `query`'s
[graph output documentation](/query/language#display-result-graph) for details. `cquery`
also supports [`--graph:node_limit`](/query/language#graph-nodelimit) and
[`--graph:factored`](/query/language#graph-factored).

### Files output {:#files-output}

<pre>
--output=files
</pre>

This option prints a list of the output files produced by each target matched
by the query similar to the list printed at the end of a `bazel build`
invocation. The output contains only the files advertised in the requested
output groups as determined by the
[`--output_groups`](/reference/command-line-reference#flag--output_groups) flag.
It does include source files.

All paths emitted by this output format are relative to the
[execroot](https://bazel.build/remote/output-directories), which can be obtained
via `bazel info execution_root`. If the `bazel-out` convenience symlink exists,
paths to files in the main repository also resolve relative to the workspace
directory.

Note: The output of `bazel cquery --output=files //pkg:foo` contains the output
files of `//pkg:foo` in *all* configurations that occur in the build (also see
the [section on target pattern evaluation](#target-pattern-evaluation)). If that
is not desired, wrap you query in [`config(..., target)`](#config).

### Defining the output format using Starlark {:#output-format-definition}

<pre>
--output=starlark
</pre>

This output format calls a [Starlark](/rules/language)
function for each configured target in the query result, and prints the value
returned by the call. The `--starlark:file` flag specifies the location of a
Starlark file that defines a function named `format` with a single parameter,
`target`. This function is called for each [Target](/rules/lib/builtins/Target)
in the query result. Alternatively, for convenience, you may specify just the
body of a function declared as `def format(target): return expr` by using the
`--starlark:expr` flag.

#### 'cquery' Starlark dialect {:#cquery-starlark}

The cquery Starlark environment differs from a BUILD or .bzl file. It includes
all core Starlark
[built-in constants and functions](https://github.com/bazelbuild/starlark/blob/master/spec.md#built-in-constants-and-functions){: .external},
plus a few cquery-specific ones described below, but not (for example) `glob`,
`native`, or `rule`, and it does not support load statements.

##### build_options(target) {:#build-options}

`build_options(target)` returns a map whose keys are build option identifiers (see
[Configurations](/extending/config))
and whose values are their Starlark values. Build options whose values are not legal Starlark
values are omitted from this map.

If the target is an input file, `build_options(target)` returns None, as input file
targets have a null configuration.

##### providers(target) {:#providers}

`providers(target)` returns a map whose keys are names of
[providers](/extending/rules#providers)
(for example, `"DefaultInfo"`) and whose values are their Starlark values. Providers
whose values are not legal Starlark values are omitted from this map.

#### Examples {:#output-format-definition-examples}

Print a space-separated list of the base names of all files produced by `//foo`:

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="' '.join([f.basename for f in target.files.to_list()])"
</pre>

Print a space-separated list of the paths of all files produced by **rule** targets in
`//bar` and its subpackages:

<pre>
  bazel cquery 'kind(rule, //bar/...)' --output=starlark \
    --starlark:expr="' '.join([f.path for f in target.files.to_list()])"
</pre>

Print a list of the mnemonics of all actions registered by `//foo`.

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="[a.mnemonic for a in target.actions]"
</pre>

Print a list of compilation outputs registered by a `cc_library` `//baz`.

<pre>
  bazel cquery //baz --output=starlark \
    --starlark:expr="[f.path for f in target.output_groups.compilation_outputs.to_list()]"
</pre>

Print the value of the command line option `--javacopt` when building `//foo`.

<pre>
  bazel cquery //foo --output=starlark \
    --starlark:expr="build_options(target)['//command_line_option:javacopt']"
</pre>

Print the label of each target with exactly one output. This example uses
Starlark functions defined in a file.

<pre>
  $ cat example.cquery

  def has_one_output(target):
    return len(target.files.to_list()) == 1

  def format(target):
    if has_one_output(target):
      return target.label
    else:
      return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

Print the label of each target which is strictly Python 3. This example uses
Starlark functions defined in a file.

<pre>
  $ cat example.cquery

  def format(target):
    p = providers(target)
    py_info = p.get("PyInfo")
    if py_info and py_info.has_py3_only_sources:
      return target.label
    else:
      return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

Extract a value from a user defined Provider.

<pre>
  $ cat some_package/my_rule.bzl

  MyRuleInfo = provider(fields={"color": "the name of a color"})

  def _my_rule_impl(ctx):
      ...
      return [MyRuleInfo(color="red")]

  my_rule = rule(
      implementation = _my_rule_impl,
      attrs = {...},
  )

  $ cat example.cquery

  def format(target):
    p = providers(target)
    my_rule_info = p.get("//some_package:my_rule.bzl%MyRuleInfo'")
    if my_rule_info:
      return my_rule_info.color
    return ""

  $ bazel cquery //baz --output=starlark --starlark:file=example.cquery
</pre>

## cquery vs. query {:#cquery-vs-query}

`cquery` and `query` complement each other and excel in
different niches. Consider the following to decide which is right for you:

*  `cquery` follows specific `select()` branches to
    model the exact graph you build. `query` doesn't know which
    branch the build chooses, so overapproximates by including all branches.
*   `cquery`'s precision requires building more of the graph than
    `query` does. Specifically, `cquery`
    evaluates _configured targets_ while `query` only
    evaluates _targets_. This takes more time and uses more memory.
*   `cquery`'s interpretation of
    the [query language](/query/language) introduces ambiguity
    that `query` avoids. For example,
    if `"//foo"` exists in two configurations, which one
    should `cquery "deps(//foo)"` use?
    The [`config`](#config) function can help with this.
*   As a newer tool, `cquery` lacks support for certain use
    cases. See [Known issues](#known-issues) for details.

## Known issues {:#known-issues}

**All targets that `cquery` "builds" must have the same configuration.**

Before evaluating queries, `cquery` triggers a build up to just
before the point where build actions would execute. The targets it
"builds" are by default selected from all labels that appear in the query
expression (this can be overridden
with [`--universe_scope`](#universe-scope)). These
must have the same configuration.

While these generally share the top-level "target" configuration,
rules can change their own configuration with
[incoming edge transitions](/extending/config#incoming-edge-transitions).
This is where `cquery` falls short.

Workaround: If possible, set `--universe_scope` to a stricter
scope. For example:

<pre>
# This command attempts to build the transitive closures of both //foo and
# //bar. //bar uses an incoming edge transition to change its --cpu flag.
$ bazel cquery 'somepath(//foo, //bar)'
ERROR: Error doing post analysis query: Top-level targets //foo and //bar
have different configurations (top-level targets with different
configurations is not supported)

# This command only builds the transitive closure of //foo, under which
# //bar should exist in the correct configuration.
$ bazel cquery 'somepath(//foo, //bar)' --universe_scope=//foo
</pre>

**No support for [`--output=xml`](/query/language#xml).**

**Non-deterministic output.**

`cquery` does not automatically wipe the build graph from
previous commands and is therefore prone to picking up results from past
queries. For example, `genrule` exerts an exec transition on
its `tools` attribute - that is, it configures its tools in the
[exec configuration](/extending/rules#configurations).

You can see the lingering effects of that transition below.

<pre>
$ cat > foo/BUILD &lt;&lt;&lt;EOF
genrule(
    name = "my_gen",
    srcs = ["x.in"],
    outs = ["x.cc"],
    cmd = "$(locations :tool) $&lt; >$@",
    tools = [":tool"],
)
cc_library(
    name = "tool",
)
EOF

    $ bazel cquery "//foo:tool"
tool(target_config)

    $ bazel cquery "deps(//foo:my_gen)"
my_gen (target_config)
tool (exec_config)
...

    $ bazel cquery "//foo:tool"
tool(exec_config)
</pre>

Workaround: change any startup option to force re-analysis of configured targets.
For example, add `--test_arg=<whatever>` to your build command.

## Troubleshooting {:#troubleshooting}

### Recursive target patterns (`/...`) {:#recursive-target-patterns}

If you encounter:

<pre>
$ bazel cquery --universe_scope=//foo:app "somepath(//foo:app, //foo/...)"
ERROR: Error doing post analysis query: Evaluation failed: Unable to load package '[foo]'
because package is not in scope. Check that all target patterns in query expression are within the
--universe_scope of this query.
</pre>

this incorrectly suggests package `//foo` isn't in scope even though
`--universe_scope=//foo:app` includes it. This is due to design limitations in
`cquery`. As a workaround, explicitly include `//foo/...` in the universe
scope:

<pre>
$ bazel cquery --universe_scope=//foo:app,//foo/... "somepath(//foo:app, //foo/...)"
</pre>

If that doesn't work (for example, because some target in `//foo/...` can't
build with the chosen build flags), manually unwrap the pattern into its
constituent packages with a pre-processing query:

<pre>
# Replace "//foo/..." with a subshell query call (not cquery!) outputting each package, piped into
# a sed call converting "&lt;pkg&gt;" to "//&lt;pkg&gt;:*", piped into a "+"-delimited line merge.
# Output looks like "//foo:*+//foo/bar:*+//foo/baz".
#
$  bazel cquery --universe_scope=//foo:app "somepath(//foo:app, $(bazel query //foo/...
--output=package | sed -e 's/^/\/\//' -e 's/$/:*/' | paste -sd "+" -))"
</pre>


Project: /_project.yaml
Book: /_book.yaml

# Query quickstart

{% include "_buttons.html" %}

This tutorial covers how to work with Bazel to trace dependencies in your code using a premade Bazel project.

For language and `--output` flag details, see the [Bazel query reference](/query/language) and [Bazel cquery reference](/query/cquery) manuals. Get help in your IDE by typing `bazel help query` or `bazel help cquery` on the command line.

## Objective

This guide runs you through a set of basic queries you can use to learn more about your project's file dependencies. It is intended for new Bazel developers with a basic knowledge of how Bazel and `BUILD` files work.


## Prerequisites

Start by installing [Bazel](https://bazel.build/install), if you haven’t already. This tutorial uses Git for source control, so for best results, install [Git](https://github.com/git-guides/install-git) as well.

To visualize dependency graphs, the tool called Graphviz is used, which you can [download](https://graphviz.org/download/) in order to follow along.

### Get the sample project

Next, retrieve the sample app from [Bazel's Examples repository](https://github.com/bazelbuild/examples) by running the following in your command-line tool of choice:

```posix-terminal
git clone https://github.com/bazelbuild/examples.git
```

The sample project for this tutorial is in the `examples/query-quickstart` directory.

## Getting started

### What are Bazel queries?

Queries help you to learn about a Bazel codebase by analyzing the relationships between `BUILD` files and examining the resulting output for useful information. This guide previews some basic query functions, but for more options see the [query guide](https://bazel.build/query/guide). Queries help you learn about dependencies in large scale projects without manually navigating through `BUILD` files.

To run a query, open your command line terminal and enter:

```posix-terminal
bazel query 'query_function'
```

### Scenario

Imagine a scenario that delves into the relationship between Cafe Bazel and its respective chef. This Cafe exclusively sells pizza and mac & cheese. Take a look below at how the project is structured:

```
bazelqueryguide
├── BUILD
├── src
│   └── main
│       └── java
│           └── com
│               └── example
│                   ├── customers
│                   │   ├── Jenny.java
│                   │   ├── Amir.java
│                   │   └── BUILD
│                   ├── dishes
│                   │   ├── Pizza.java
│                   │   ├── MacAndCheese.java
│                   │   └── BUILD
│                   ├── ingredients
│                   │   ├── Cheese.java
│                   │   ├── Tomatoes.java
│                   │   ├── Dough.java
│                   │   ├── Macaroni.java
│                   │   └── BUILD
│                   ├── restaurant
│                   │   ├── Cafe.java
│                   │   ├── Chef.java
│                   │   └── BUILD
│                   ├── reviews
│                   │   ├── Review.java
│                   │   └── BUILD
│                   └── Runner.java
└── MODULE.bazel
```

Throughout this tutorial, unless directed otherwise, try not to look in the `BUILD` files to find the information you need and instead solely use the query function.

A project consists of different packages that make up a Cafe. They are separated into: `restaurant`, `ingredients`, `dishes`, `customers`, and `reviews`. Rules within these packages define different components of the Cafe with various tags and dependencies.

### Running a build

This project contains a main method inside of `Runner.java` that you can execute
to print out a menu of the Cafe. Build the project using Bazel with the command
`bazel build` and use `:` to signal that the target is named `runner`. See
[target names](https://bazel.build/concepts/labels#target-names) to learn how to
reference targets.

To build this project, paste this command into a terminal:

```posix-terminal
bazel build :runner
```

Your output should look something like this if the build is successful.

```bash
INFO: Analyzed target //:runner (49 packages loaded, 784 targets configured).
INFO: Found 1 target...
Target //:runner up-to-date:
  bazel-bin/runner.jar
  bazel-bin/runner
INFO: Elapsed time: 16.593s, Critical Path: 4.32s
INFO: 23 processes: 4 internal, 10 darwin-sandbox, 9 worker.
INFO: Build completed successfully, 23 total actions
```

After it has built successfully, run the application by pasting this command:

```posix-terminal
bazel-bin/runner
```

```bash
--------------------- MENU -------------------------

Pizza - Cheesy Delicious Goodness
Macaroni & Cheese - Kid-approved Dinner

----------------------------------------------------
```
This leaves you with a list of the menu items given along with a short description.

## Exploring targets

The project lists ingredients and dishes in their own packages. To use a query to view the rules of a package, run the command <code>bazel query <em>package</em>/…</code>

In this case, you can use this to look through the ingredients and dishes that this Cafe has by running:

```posix-terminal
bazel query //src/main/java/com/example/dishes/...
```

```posix-terminal
bazel query //src/main/java/com/example/ingredients/...
```

If you query for the targets of the ingredients package, the output should look like:

```bash
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/ingredients:dough
//src/main/java/com/example/ingredients:macaroni
//src/main/java/com/example/ingredients:tomato
```

## Finding dependencies

What targets does your runner rely on to run?

Say you want to dive deeper into the structure of your project without prodding into the filesystem (which may be untenable for large projects). What rules does Cafe Bazel use?

If, like in this example, the target for your runner is `runner`, discover the underlying dependencies of the target by running the command:

```posix-terminal
bazel query --noimplicit_deps "deps(target)"
```

```posix-terminal
bazel query --noimplicit_deps "deps(:runner)"
```

```bash
//:runner
//:src/main/java/com/example/Runner.java
//src/main/java/com/example/dishes:MacAndCheese.java
//src/main/java/com/example/dishes:Pizza.java
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:Cheese.java
//src/main/java/com/example/ingredients:Dough.java
//src/main/java/com/example/ingredients:Macaroni.java
//src/main/java/com/example/ingredients:Tomato.java
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/ingredients:dough
//src/main/java/com/example/ingredients:macaroni
//src/main/java/com/example/ingredients:tomato
//src/main/java/com/example/restaurant:Cafe.java
//src/main/java/com/example/restaurant:Chef.java
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```
Note: Adding the flag `--noimplicit_deps` removes configurations and potential toolchains to simplify the list. When you omit this flag, Bazel returns implicit dependencies not specified in the `BUILD` file and clutters the output.

In most cases, use the query function `deps()` to see individual output dependencies of a specific target.

## Visualizing the dependency graph (optional)

Note: This section uses Graphviz, so make sure to [download Graphviz](https://graphviz.org/download/) to follow along.

The section describes how you can visualize the dependency paths for a specific query. [Graphviz](https://graphviz.org/) helps to see the path as a directed acyclic graph image as opposed to a flattened list. You can alter the display of the Bazel query graph by using various `--output` command line options. See [Output Formats](https://bazel.build/query/language#output-formats) for options.

Start by running your desired query and add the flag `--noimplicit_deps` to remove excessive tool dependencies. Then, follow the query with the output flag and store the graph into a file called `graph.in` to create a text representation of the graph.

To search for all dependencies of the target `:runner` and format the output as a graph:

```posix-terminal
bazel query --noimplicit_deps 'deps(:runner)' --output graph > graph.in
```
This creates a file called `graph.in`, which is a text representation of the build graph. Graphviz uses <code>[dot](https://graphviz.org/docs/layouts/dot/) </code>– a tool that processes text into a visualization —  to create a png:

```posix-terminal
dot -Tpng < graph.in > graph.png
```
If you open up `graph.png`, you should see something like this. The graph below has been simplified to make the essential path details clearer in this guide.

![Diagram showing a relationship from cafe to chef to the dishes: pizza and mac and cheese which diverges into the separate ingredients: cheese, tomatoes, dough, and macaroni.](images/query_graph1.png "Dependency graph")

This helps when you want to see the outputs of the different query functions throughout this guide.

## Finding reverse dependencies

If instead you have a target you’d like to analyze what other targets use it, you can use a query to examine what targets depend on a certain rule. This is called a “reverse dependency”. Using `rdeps()` can be useful when editing a file in a codebase that you’re unfamiliar with, and can save you from unknowingly breaking other files which depended on it.

For instance, you want to make some edits to the ingredient `cheese`. To avoid causing an issue for Cafe Bazel, you need to check what dishes rely on `cheese`.

Caution: Since `ingredients` is its own package, you must use a different naming convention for the target `cheese` in the form of `//package:target`. Read more about referencing targets, or [Labels](https://bazel.build/concepts/labels).

To see what targets depend on a particular target/package, you can use `rdeps(universe_scope, target)`. The `rdeps()` query function takes in at least two arguments: a `universe_scope` — the relevant directory — and a `target`. Bazel searches for the target’s reverse dependencies within the `universe_scope` provided. The `rdeps()` operator accepts an optional third argument: an integer literal specifying the upper bound on the depth of the search.

Tip: To search within the whole scope of the project, set the `universe_scope` to `//...`

To look for reverse dependencies of the target `cheese` within the scope of the entire project ‘//…’ run the command:

```posix-terminal
bazel query "rdeps(universe_scope, target)"
```
```
ex) bazel query "rdeps(//... , //src/main/java/com/example/ingredients:cheese)"
```
```bash
//:runner
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```
The query return shows that cheese is relied on by both pizza and macAndCheese. What a surprise!

## Finding targets based on tags

Two customers walk into Bazel Cafe: Amir and Jenny. There is nothing known about them except for their names. Luckily, they have their orders tagged in the 'customers' `BUILD` file. How can you access this tag?

Developers can tag Bazel targets with different identifiers, often for testing purposes. For instance, tags on tests can annotate a test's role in your debug and release process, especially for C++ and Python tests, which lack any runtime annotation ability. Using tags and size elements gives flexibility in assembling suites of tests based around a codebase’s check-in policy.

In this example, the tags are either one of `pizza` or `macAndCheese` to represent the menu items. This command queries for targets that have tags matching your identifier within a certain package.

```
bazel query 'attr(tags, "pizza", //src/main/java/com/example/customers/...)'
```
This query returns all of the targets in the 'customers' package that have a tag of "pizza".

### Test yourself

Use this query to learn what Jenny wants to order.

<div>
  <devsite-expandable>
  <h4 class="showalways">Answer</h4>
  <p>Mac and Cheese</p>
  </devsite-expandable>
</div>


## Adding a new dependency

Cafe Bazel has expanded its menu — customers can now order a Smoothie! This specific smoothie consists of the ingredients `Strawberry` and `Banana`.

First, add the ingredients that the smoothie depends on: `Strawberry.java` and `Banana.java`. Add the empty Java classes.

**`src/main/java/com/example/ingredients/Strawberry.java`**

```java
package com.example.ingredients;

public class Strawberry {

}
```

**`src/main/java/com/example/ingredients/Banana.java`**

```java
package com.example.ingredients;

public class Banana {

}
```

Next, add `Smoothie.java` to the appropriate directory: `dishes`.

**`src/main/java/com/example/dishes/Smoothie.java`**

```java
package com.example.dishes;

public class Smoothie {
    public static final String DISH_NAME = "Smoothie";
    public static final String DESCRIPTION = "Yummy and Refreshing";
}
```


Lastly, add these files as rules in the appropriate `BUILD` files. Create a new java library for each new ingredient, including its name, public visibility, and its newly created 'src' file. You should wind up with this updated `BUILD` file:

**`src/main/java/com/example/ingredients/BUILD`**

```
java_library(
    name = "cheese",
    visibility = ["//visibility:public"],
    srcs = ["Cheese.java"],
)

java_library(
    name = "dough",
    visibility = ["//visibility:public"],
    srcs = ["Dough.java"],
)

java_library(
    name = "macaroni",
    visibility = ["//visibility:public"],
    srcs = ["Macaroni.java"],
)

java_library(
    name = "tomato",
    visibility = ["//visibility:public"],
    srcs = ["Tomato.java"],
)

java_library(
    name = "strawberry",
    visibility = ["//visibility:public"],
    srcs = ["Strawberry.java"],
)

java_library(
    name = "banana",
    visibility = ["//visibility:public"],
    srcs = ["Banana.java"],
)
```

In the `BUILD` file for dishes, you want to add a new rule for `Smoothie`. Doing so includes the Java file created for `Smoothie` as a 'src' file, and the new rules you made for each ingredient of the smoothie.

**`src/main/java/com/example/dishes/BUILD`**

```
java_library(
    name = "macAndCheese",
    visibility = ["//visibility:public"],
    srcs = ["MacAndCheese.java"],
    deps = [
        "//src/main/java/com/example/ingredients:cheese",
        "//src/main/java/com/example/ingredients:macaroni",
    ],
)

java_library(
    name = "pizza",
    visibility = ["//visibility:public"],
    srcs = ["Pizza.java"],
    deps = [
        "//src/main/java/com/example/ingredients:cheese",
        "//src/main/java/com/example/ingredients:dough",
        "//src/main/java/com/example/ingredients:tomato",
    ],
)

java_library(
    name = "smoothie",
    visibility = ["//visibility:public"],
    srcs = ["Smoothie.java"],
    deps = [
        "//src/main/java/com/example/ingredients:strawberry",
        "//src/main/java/com/example/ingredients:banana",
    ],
)
```

Lastly, you want to include the smoothie as a dependency in the Chef’s `BUILD` file.

**`src/main/java/com/example/restaurant/BUILD`**

```
java\_library(
    name = "chef",
    visibility = ["//visibility:public"],
    srcs = [
        "Chef.java",
    ],

    deps = [
        "//src/main/java/com/example/dishes:macAndCheese",
        "//src/main/java/com/example/dishes:pizza",
        "//src/main/java/com/example/dishes:smoothie",
    ],
)

java\_library(
    name = "cafe",
    visibility = ["//visibility:public"],
    srcs = [
        "Cafe.java",
    ],
    deps = [
        ":chef",
    ],
)
```

Build `cafe` again to confirm that there are no errors. If it builds successfully, congratulations! You’ve added a new dependency for the 'Cafe'. If not, look out for spelling mistakes and package naming. For more information about writing `BUILD` files see [BUILD Style Guide](https://bazel.build/build/style-guide).

Now, visualize the new dependency graph with the addition of the `Smoothie` to compare with the previous one. For clarity, name the graph input as `graph2.in` and `graph2.png`.


```posix-terminal
bazel query --noimplicit_deps 'deps(:runner)' --output graph > graph2.in
```

```posix-terminal
dot -Tpng < graph2.in > graph2.png
```

[![The same graph as the first one except now there is a spoke stemming from the chef target with smoothie which leads to banana and strawberry](images/query_graph2.png "Updated dependency graph")](images/query_graph2.png)

Looking at `graph2.png`, you can see that `Smoothie` has no shared dependencies with other dishes but is just another target that the `Chef` relies on.

## somepath() and allpaths()

What if you want to query why one package depends on another package? Displaying a dependency path between the two provides the answer.

Two functions can help you find dependency paths: `somepath()` and `allpaths()`. Given a starting target S and an end point E, find a path between S and E by using `somepath(S,E)`.

Explore the differences between these two functions by looking at the relationships between the 'Chef' and 'Cheese' targets. There are different possible paths to get from one target to the other:

*   Chef → MacAndCheese → Cheese
*   Chef → Pizza → Cheese

`somepath()` gives you a single path out of the two options, whereas 'allpaths()' outputs every possible path.

Using Cafe Bazel as an example, run the following:

```posix-terminal
bazel query "somepath(//src/main/java/com/example/restaurant/..., //src/main/java/com/example/ingredients:cheese)"
```

```bash
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/ingredients:cheese
```

The output follows the first path of Cafe → Chef → MacAndCheese → Cheese. If instead you use `allpaths()`, you get:

```posix-terminal
bazel query "allpaths(//src/main/java/com/example/restaurant/..., //src/main/java/com/example/ingredients:cheese)"
```

```bash
//src/main/java/com/example/dishes:macAndCheese
//src/main/java/com/example/dishes:pizza
//src/main/java/com/example/ingredients:cheese
//src/main/java/com/example/restaurant:cafe
//src/main/java/com/example/restaurant:chef
```

![Output path of cafe to chef to pizza,mac and cheese to cheese](images/query_graph3.png "Output path for dependency")

The output of `allpaths()` is a little harder to read as it is a flattened list of the dependencies. Visualizing this graph using Graphviz makes the relationship clearer to understand.

## Test yourself

One of Cafe Bazel’s customers gave the restaurant's first review! Unfortunately, the review is missing some details such as the identity of the reviewer and what dish it’s referencing. Luckily, you can access this information with Bazel. The `reviews` package contains a program that prints a review from a mystery customer. Build and run it with:

```posix-terminal
bazel build //src/main/java/com/example/reviews:review
```

```posix-terminal
bazel-bin/src/main/java/com/example/reviews/review
```

Going off Bazel queries only, try to find out who wrote the review, and what dish they were describing.

<div>
  <devsite-expandable>
  <h4 class="showalways">Hint</h4>
  <p>Check the tags and dependencies for useful information.</p>
  </devsite-expandable>
</div>

<div>
  <devsite-expandable>
  <h4 class="showalways">Answer</h4>
  <p>This review was describing the Pizza and Amir was the reviewer. If you look at what dependencies that this rule had using
  <code>bazel query --noimplicit\_deps 'deps(//src/main/java/com/example/reviews:review)'</code>
  The result of this command reveals that Amir is the reviewer!
  Next, since you know the reviewer is Amir, you can use the query function to seek which tag Amir has in the `BUILD` file to see what dish is there.
  The command <code>bazel query 'attr(tags, "pizza", //src/main/java/com/example/customers/...)'</code> output that Amir is the only customer that ordered a pizza and is the reviewer which gives us the answer.
  </p>
  </devsite-expandable>
</div>

## Wrapping up

Congratulations! You have now run several basic queries, which you can try out on own projects. To learn more about the query language syntax, refer to the [Query reference page](https://bazel.build/query/language). Want more advanced queries? The [Query guide](https://bazel.build/query/guide) showcases an in-depth list of more use cases than are covered in this guide.


Project: /_project.yaml
Book: /_book.yaml

# Action Graph Query (aquery)

{% include "_buttons.html" %}

The `aquery` command allows you to query for actions in your build graph.
It operates on the post-analysis Configured Target Graph and exposes
information about **Actions, Artifacts and their relationships.**

`aquery` is useful when you are interested in the properties of the Actions/Artifacts
generated from the Configured Target Graph. For example, the actual commands run
and their inputs/outputs/mnemonics.

The tool accepts several command-line [options](#command-options).
Notably, the aquery command runs on top of a regular Bazel build and inherits
the set of options available during a build.

It supports the same set of functions that is also available to traditional
`query` but `siblings`, `buildfiles` and
`tests`.

An example `aquery` output (without specific details):

<pre>
$ bazel aquery 'deps(//some:label)'
action 'Writing file some_file_name'
  Mnemonic: ...
  Target: ...
  Configuration: ...
  ActionKey: ...
  Inputs: [...]
  Outputs: [...]
</pre>

## Basic syntax {:#basic-syntax}

A simple example of the syntax for `aquery` is as follows:

`bazel aquery "aquery_function(function(//target))"`

The query expression (in quotes) consists of the following:

*   `aquery_function(...)`: functions specific to `aquery`.
    More details [below](#using-aquery-functions).
*   `function(...)`: the standard [functions](/query/language#functions)
    as traditional `query`.
*   `//target` is the label to the interested target.

<pre>
# aquery examples:
# Get the action graph generated while building //src/target_a
$ bazel aquery '//src/target_a'

# Get the action graph generated while building all dependencies of //src/target_a
$ bazel aquery 'deps(//src/target_a)'

# Get the action graph generated while building all dependencies of //src/target_a
# whose inputs filenames match the regex ".*cpp".
$ bazel aquery 'inputs(".*cpp", deps(//src/target_a))'
</pre>

## Using aquery functions {:#using-aquery-functions}

There are three `aquery` functions:

*   `inputs`: filter actions by inputs.
*   `outputs`: filter actions by outputs
*   `mnemonic`: filter actions by mnemonic

`expr ::= inputs(word, expr)`

  The `inputs` operator returns the actions generated from building `expr`,
  whose input filenames match the regex provided by `word`.

`$ bazel aquery 'inputs(".*cpp", deps(//src/target_a))'`

`outputs` and `mnemonic` functions share a similar syntax.

You can also combine functions to achieve the AND operation. For example:

<pre>
  $ bazel aquery 'mnemonic("Cpp.*", (inputs(".*cpp", inputs("foo.*", //src/target_a))))'
</pre>

  The above command would find all actions involved in building `//src/target_a`,
  whose mnemonics match `"Cpp.*"` and inputs match the patterns
  `".*cpp"` and `"foo.*"`.

Important: aquery functions can't be nested inside non-aquery functions.
Conceptually, this makes sense since the output of aquery functions is Actions,
not Configured Targets.

An example of the syntax error produced:

<pre>
        $ bazel aquery 'deps(inputs(".*cpp", //src/target_a))'
        ERROR: aquery filter functions (inputs, outputs, mnemonic) produce actions,
        and therefore can't be the input of other function types: deps
        deps(inputs(".*cpp", //src/target_a))
</pre>

## Options {:#options}

### Build options {:#build-options}

`aquery` runs on top of a regular Bazel build and thus inherits the set of
[options](/reference/command-line-reference#build-options)
available during a build.

### Aquery options {:#aquery-options}

#### `--output=(text|summary|commands|proto|jsonproto|textproto), default=text` {:#output}

The default output format (`text`) is human-readable,
use `proto`, `textproto`, or `jsonproto` for machine-readable format.
The proto message is `analysis.ActionGraphContainer`.

The `commands` output format prints a list of build commands with
one command per line.

In general, do not depend on the order of output. For more information,
see the [core query ordering contract](/query/language#graph-order).

#### `--include_commandline, default=true` {:#include-commandline}

Includes the content of the action command lines in the output (potentially large).

#### `--include_artifacts, default=true` {:#include-artifacts}

Includes names of the action inputs and outputs in the output (potentially large).

#### `--include_aspects, default=true` {:#include-aspects}

Whether to include Aspect-generated actions in the output.

#### `--include_param_files, default=false` {:#include-param-files}

Include the content of the param files used in the command (potentially large).

Warning: Enabling this flag will automatically enable the `--include_commandline` flag.

#### `--include_file_write_contents, default=false` {:#include-file-write-contents}

Include file contents for the `actions.write()` action and the contents of the
manifest file for the `SourceSymlinkManifest` action The file contents is
returned in the `file_contents` field with `--output=`xxx`proto`.
With `--output=text`, the output has
```
FileWriteContents: [<base64-encoded file contents>]
```
line

#### `--skyframe_state, default=false` {:#skyframe-state}

Without performing extra analysis, dump the Action Graph from Skyframe.

Note: Specifying a target with `--skyframe_state` is currently not supported.
This flag is only available with `--output=proto` or `--output=textproto`.

## Other tools and features {:#other-tools-features}

### Querying against the state of Skyframe {:#querying-against-skyframe}

[Skyframe](/reference/skyframe) is the evaluation and
incrementality model of Bazel. On each instance of Bazel server, Skyframe stores the dependency graph
constructed from the previous runs of the [Analysis phase](/run/build#analysis).

In some cases, it is useful to query the Action Graph on Skyframe.
An example use case would be:

1.  Run `bazel build //target_a`
2.  Run `bazel build //target_b`
3.  File `foo.out` was generated.

_As a Bazel user, I want to determine if `foo.out` was generated from building
`//target_a` or `//target_b`_.

One could run `bazel aquery 'outputs("foo.out", //target_a)'` and
`bazel aquery 'outputs("foo.out", //target_b)'` to figure out the action responsible
for creating `foo.out`, and in turn the target. However, the number of different
targets previously built can be larger than 2, which makes running multiple `aquery`
commands a hassle.

As an alternative, the `--skyframe_state` flag can be used:

<pre>
  # List all actions on Skyframe's action graph
  $ bazel aquery --output=proto --skyframe_state

  # or

  # List all actions on Skyframe's action graph, whose output matches "foo.out"
  $ bazel aquery --output=proto --skyframe_state 'outputs("foo.out")'
</pre>

With `--skyframe_state` mode, `aquery` takes the content of the Action Graph
that Skyframe keeps on the instance of Bazel, (optionally) performs filtering on it and
outputs the content, without re-running the analysis phase.

#### Special considerations {:#special-considerations}

##### Output format {:#output-format}

`--skyframe_state` is currently only available for `--output=proto`
and `--output=textproto`

##### Non-inclusion of target labels in the query expression {:#target-labels-non-inclusion}

Currently, `--skyframe_state` queries the whole action graph that exists on Skyframe,
regardless of the targets. Having the target label specified in the query together with
`--skyframe_state` is considered a syntax error:

<pre>
  # WRONG: Target Included
  $ bazel aquery --output=proto --skyframe_state **//target_a**
  ERROR: Error while parsing '//target_a)': Specifying build target(s) [//target_a] with --skyframe_state is currently not supported.

  # WRONG: Target Included
  $ bazel aquery --output=proto --skyframe_state 'inputs(".*.java", **//target_a**)'
  ERROR: Error while parsing '//target_a)': Specifying build target(s) [//target_a] with --skyframe_state is currently not supported.

  # CORRECT: Without Target
  $ bazel aquery --output=proto --skyframe_state
  $ bazel aquery --output=proto --skyframe_state 'inputs(".*.java")'
</pre>

### Comparing aquery outputs {:#comparing-aquery-outputs}

You can compare the outputs of two different aquery invocations using the `aquery_differ` tool.
For instance: when you make some changes to your rule definition and want to verify that the
command lines being run did not change. `aquery_differ` is the tool for that.

The tool is available in the [bazelbuild/bazel](https://github.com/bazelbuild/bazel/tree/master/tools/aquery_differ){: .external} repository.
To use it, clone the repository to your local machine. An example usage:

<pre>
  $ bazel run //tools/aquery_differ -- \
  --before=/path/to/before.proto \
  --after=/path/to/after.proto \
  --input_type=proto \
  --attrs=cmdline \
  --attrs=inputs
</pre>

The above command returns the difference between the `before` and `after` aquery outputs:
which actions were present in one but not the other, which actions have different
command line/inputs in each aquery output, ...). The result of running the above command would be:

<pre>
  Aquery output 'after' change contains an action that generates the following outputs that aquery output 'before' change doesn't:
  ...
  /list of output files/
  ...

  [cmdline]
  Difference in the action that generates the following output(s):
    /path/to/abc.out
  --- /path/to/before.proto
  +++ /path/to/after.proto
  @@ -1,3 +1,3 @@
    ...
    /cmdline diff, in unified diff format/
    ...
</pre>

#### Command options {:#command-options}

`--before, --after`: The aquery output files to be compared

`--input_type=(proto|text_proto), default=proto`: the format of the input
files. Support is provided for `proto` and `textproto` aquery output.

`--attrs=(cmdline|inputs), default=cmdline`: the attributes of actions
to be compared.

### Aspect-on-aspect {:#aspect-on-aspect}

It is possible for [Aspects](/extending/aspects)
to be applied on top of each other. The aquery output of the action generated by
these Aspects would then include the _Aspect path_, which is the sequence of
Aspects applied to the target which generated the action.

An example of Aspect-on-Aspect:

<pre>
  t0
  ^
  | <- a1
  t1
  ^
  | <- a2
  t2
</pre>

Let t<sub>i</sub> be a target of rule r<sub>i</sub>, which applies an Aspect a<sub>i</sub>
to its dependencies.

Assume that a2 generates an action X when applied to target t0. The text output of
`bazel aquery --include_aspects 'deps(//t2)'` for action X would be:

<pre>
  action ...
  Mnemonic: ...
  Target: //my_pkg:t0
  Configuration: ...
  AspectDescriptors: [//my_pkg:rule.bzl%**a2**(foo=...)
    -> //my_pkg:rule.bzl%**a1**(bar=...)]
  ...
</pre>

This means that action `X` was generated by Aspect `a2` applied onto
`a1(t0)`, where `a1(t0)` is the result of Aspect `a1` applied
onto target `t0`.

Each `AspectDescriptor` has the following format:

<pre>
  AspectClass([param=value,...])
</pre>

`AspectClass` could be the name of the Aspect class (for native Aspects) or
`bzl_file%aspect_name` (for Starlark Aspects). `AspectDescriptor` are
sorted in topological order of the
[dependency graph](/extending/aspects#aspect_basics).

### Linking with the JSON profile {:#linking-with-json-profile}

While aquery provides information about the actions being run in a build (why they're being run,
their inputs/outputs), the [JSON profile](/rules/performance#performance-profiling)
tells us the timing and duration of their execution.
It is possible to combine these 2 sets of information via a common denominator: an action's primary output.

To include actions' outputs in the JSON profile, generate the profile with
`--experimental_include_primary_output --noslim_profile`.
Slim profiles are incompatible with the inclusion of primary outputs. An action's primary output
is included by default by aquery.

We don't currently provide a canonical tool to combine these 2 data sources, but you should be
able to build your own script with the above information.

## Known issues {:#known-issues}

### Handling shared actions {:#handling-shared-actions}

Sometimes actions are
[shared](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/Actions.java;l=59;drc=146d51aa1ec9dcb721a7483479ef0b1ac21d39f1){: .external}
between configured targets.

In the execution phase, those shared actions are
[simply considered as one](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/Actions.java;l=241;drc=003b8734036a07b496012730964ac220f486b61f){: .external} and only executed once.
However, aquery operates on the pre-execution, post-analysis action graph, and hence treats these
like separate actions whose output Artifacts have the exact same `execPath`. As a result,
equivalent Artifacts appear duplicated.

The list of aquery issues/planned features can be found on
[GitHub](https://github.com/bazelbuild/bazel/labels/team-Performance){: .external}.

## FAQs {:#faqs}

### The ActionKey remains the same even though the content of an input file changed. {:#actionkey-same}

In the context of aquery, the `ActionKey` refers to the `String` gotten from
[ActionAnalysisMetadata#getKey](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/actions/ActionAnalysisMetadata.java;l=89;drc=8b856f5484f0117b2aebc302f849c2a15f273310){: .external}:

<pre>
  Returns a string encoding all of the significant behaviour of this Action that might affect the
  output. The general contract of `getKey` is this: if the work to be performed by the
  execution of this action changes, the key must change.

  ...

  Examples of changes that should affect the key are:

  - Changes to the BUILD file that materially affect the rule which gave rise to this Action.
  - Changes to the command-line options, environment, or other global configuration resources
      which affect the behaviour of this kind of Action (other than changes to the names of the
      input/output files, which are handled externally).
  - An upgrade to the build tools which changes the program logic of this kind of Action
      (typically this is achieved by incorporating a UUID into the key, which is changed each
      time the program logic of this action changes).
  Note the following exception: for actions that discover inputs, the key must change if any
  input names change or else action validation may falsely validate.
</pre>

This excludes the changes to the content of the input files, and is not to be confused with
[RemoteCacheClient#ActionKey](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/remote/common/RemoteCacheClient.java;l=38;drc=21577f202eb90ce94a337ebd2ede824d609537b6){: .external}.

## Updates {:#updates}

For any issues/feature requests, please file an issue [here](https://github.com/bazelbuild/bazel/issues/new).


Project: /_project.yaml
Book: /_book.yaml

# Query guide

{% include "_buttons.html" %}

This page covers how to get started using Bazel's query language to trace
dependencies in your code.

For a language details and `--output` flag details, please see the
reference manuals, [Bazel query reference](/query/language)
and [Bazel cquery reference](/query/cquery). You can get help by
typing `bazel help query` or `bazel help cquery` on the
command line.

To execute a query while ignoring errors such as missing targets, use the
`--keep_going` flag.

## Finding the dependencies of a rule {:#finding-rule-dependencies}

To see the dependencies of `//foo`, use the
`deps` function in bazel query:

<pre>
$ bazel query "deps(//foo)"
//foo:foo
//foo:foo-dep
...
</pre>

This is the set of all targets required to build `//foo`.

## Tracing the dependency chain between two packages {:#tracing-dependency-chain}

The library `//third_party/zlib:zlibonly` isn't in the BUILD file for
`//foo`, but it is an indirect dependency. How can
we trace this dependency path?  There are two useful functions here:
`allpaths` and `somepath`. You may also want to exclude
tooling dependencies with `--notool_deps` if you care only about
what is included in the artifact you built, and not every possible job.

To visualize the graph of all dependencies, pipe the bazel query output through
  the `dot` command-line tool:

<pre>
$ bazel query "allpaths(//foo, third_party/...)" --notool_deps --output graph | dot -Tsvg > /tmp/deps.svg
</pre>

Note: `dot` supports other image formats, just replace `svg` with the
format identifier, for example, `png`.

When a dependency graph is big and complicated, it can be helpful start with a single path:

<pre>
$ bazel query "somepath(//foo:foo, third_party/zlib:zlibonly)"
//foo:foo
//translations/tools:translator
//translations/base:base
//third_party/py/MySQL:MySQL
//third_party/py/MySQL:_MySQL.so
//third_party/mysql:mysql
//third_party/zlib:zlibonly
</pre>

If you do not specify `--output graph` with `allpaths`,
you will get a flattened list of the dependency graph.

<pre>
$ bazel query "allpaths(//foo, third_party/...)"
  ...many errors detected in BUILD files...
//foo:foo
//translations/tools:translator
//translations/tools:aggregator
//translations/base:base
//tools/pkg:pex
//tools/pkg:pex_phase_one
//tools/pkg:pex_lib
//third_party/python:python_lib
//translations/tools:messages
//third_party/py/xml:xml
//third_party/py/xml:utils/boolean.so
//third_party/py/xml:parsers/sgmlop.so
//third_party/py/xml:parsers/pyexpat.so
//third_party/py/MySQL:MySQL
//third_party/py/MySQL:_MySQL.so
//third_party/mysql:mysql
//third_party/openssl:openssl
//third_party/zlib:zlibonly
//third_party/zlib:zlibonly_v1_2_3
//third_party/python:headers
//third_party/openssl:crypto
</pre>

### Aside: implicit dependencies {:#implicit-dependencies}

The BUILD file for `//foo` never references
`//translations/tools:aggregator`. So, where's the direct dependency?

Certain rules include implicit dependencies on additional libraries or tools.
For example, to build a `genproto` rule, you need first to build the Protocol
Compiler, so every `genproto` rule carries an implicit dependency on the
protocol compiler. These dependencies are not mentioned in the build file,
but added in by the build tool. The full set of implicit dependencies is
  currently undocumented. Using `--noimplicit_deps` allows you to filter out
  these deps from your query results. For cquery, this will include resolved toolchains.

## Reverse dependencies {:#reverse-dependencies}

You might want to know the set of targets that depends on some target. For instance,
if you're going to change some code, you might want to know what other code
you're about to break. You can use `rdeps(u, x)` to find the reverse
dependencies of the targets in `x` within the transitive closure of `u`.

Bazel's [Sky Query](/query/language#sky-query)
supports the `allrdeps` function which allows you to query reverse dependencies
in a universe you specify.

## Miscellaneous uses {:#miscellaneous-uses}

You can use `bazel query` to analyze many dependency relationships.

### What exists ... {:#what-exists}

#### What packages exist beneath `foo`? {:#what-exists-beneath-foo}

<pre>bazel query 'foo/...' --output package</pre>

#### What rules are defined in the `foo` package? {:#rules-defined-in-foo}

<pre>bazel query 'kind(rule, foo:*)' --output label_kind</pre>

#### What files are generated by rules in the `foo` package? {:#files-generated-by-rules}

<pre>bazel query 'kind("generated file", //foo:*)'</pre>

#### What targets are generated by starlark macro `foo`? {:#targets-generated-by-foo}

<pre>bazel query 'attr(generator_function, foo, //path/to/search/...)'</pre>

#### What's the set of BUILD files needed to build `//foo`? {:#build-files-required}

<pre>bazel query 'buildfiles(deps(//foo))' | cut -f1 -d:</pre>

#### What are the individual tests that a `test_suite` expands to? {:#individual-tests-in-testsuite}

<pre>bazel query 'tests(//foo:smoke_tests)'</pre>

#### Which of those are C++ tests? {:#cxx-tests}

<pre>bazel query 'kind(cc_.*, tests(//foo:smoke_tests))'</pre>

#### Which of those are small?  Medium?  Large? {:#size-of-tests}

<pre>
bazel query 'attr(size, small, tests(//foo:smoke_tests))'

bazel query 'attr(size, medium, tests(//foo:smoke_tests))'

bazel query 'attr(size, large, tests(//foo:smoke_tests))'
</pre>

#### What are the tests beneath `foo` that match a pattern? {:#tests-beneath-foo}

<pre>bazel query 'filter("pa?t", kind(".*_test rule", //foo/...))'</pre>

The pattern is a regex and is applied to the full name of the rule. It's similar to doing

<pre>bazel query 'kind(".*_test rule", //foo/...)' | grep -E 'pa?t'</pre>

#### What package contains file `path/to/file/bar.java`? {:#barjava-package}

<pre> bazel query path/to/file/bar.java --output=package</pre>

#### What is the build label for `path/to/file/bar.java?` {:#barjava-build-label}

<pre>bazel query path/to/file/bar.java</pre>

#### What rule target(s) contain file `path/to/file/bar.java` as a source? {:#barjava-rule-targets}

<pre>
fullname=$(bazel query path/to/file/bar.java)
bazel query "attr('srcs', $fullname, ${fullname//:*/}:*)"
</pre>

### What package dependencies exist ... {:#package-dependencies}

#### What packages does `foo` depend on? (What do I need to check out to build `foo`) {:#packages-foo-depends-on}

<pre>bazel query 'buildfiles(deps(//foo:foo))' --output package</pre>

Note: `buildfiles` is required in order to correctly obtain all files
referenced by `subinclude`; see the reference manual for details.

#### What packages does the `foo` tree depend on, excluding `foo/contrib`? {:#packages-foo-tree-depends-on}

<pre>bazel query 'deps(foo/... except foo/contrib/...)' --output package</pre>

### What rule dependencies exist ... {:#rule-dependencies}

#### What genproto rules does bar depend upon? {:#genproto-rules}

<pre>bazel query 'kind(genproto, deps(bar/...))'</pre>

#### Find the definition of some JNI (C++) library that is transitively depended upon by a Java binary rule in the servlet tree. {:#jni-library}

<pre>bazel query 'some(kind(cc_.*library, deps(kind(java_binary, //java/com/example/frontend/...))))' --output location</pre>

##### ...Now find the definitions of all the Java binaries that depend on them {:#java-binaries}

<pre>bazel query 'let jbs = kind(java_binary, //java/com/example/frontend/...) in
  let cls = kind(cc_.*library, deps($jbs)) in
    $jbs intersect allpaths($jbs, $cls)'
</pre>

### What file dependencies exist ... {:#file-dependencies}

#### What's the complete set of Java source files required to build foo? {:#java-source-files}

Source files:

<pre>bazel query 'kind("source file", deps(//path/to/target/foo/...))' | grep java$</pre>

Generated files:

<pre>bazel query 'kind("generated file", deps(//path/to/target/foo/...))' | grep java$</pre>

#### What is the complete set of Java source files required to build QUX's tests? {:qux-tests}

Source files:

<pre>bazel query 'kind("source file", deps(kind(".*_test rule", javatests/com/example/qux/...)))' | grep java$</pre>

Generated files:

<pre>bazel query 'kind("generated file", deps(kind(".*_test rule", javatests/com/example/qux/...)))' | grep java$</pre>

### What differences in dependencies between X and Y exist ... {:#differences-in-dependencies}

#### What targets does `//foo` depend on that `//foo:foolib` does not? {:#foo-targets}

<pre>bazel query 'deps(//foo) except deps(//foo:foolib)'</pre>

#### What C++ libraries do the `foo` tests depend on that the `//foo` production binary does _not_ depend on? {:#foo-cxx-libraries}

<pre>bazel query 'kind("cc_library", deps(kind(".*test rule", foo/...)) except deps(//foo))'</pre>

### Why does this dependency exist ... {:#why-dependencies}

#### Why does `bar` depend on `groups2`? {:#dependency-bar-groups2}

<pre>bazel query 'somepath(bar/...,groups2/...:*)'</pre>

Once you have the results of this query, you will often find that a single
target stands out as being an unexpected or egregious and undesirable
dependency of `bar`. The query can then be further refined to:

#### Show me a path from `docker/updater:updater_systest` (a `py_test`) to some `cc_library` that it depends upon: {:#path-docker-cclibrary}

<pre>bazel query 'let cc = kind(cc_library, deps(docker/updater:updater_systest)) in
  somepath(docker/updater:updater_systest, $cc)'</pre>

#### Why does library `//photos/frontend:lib` depend on two variants of the same library `//third_party/jpeglib` and `//third_party/jpeg`? {:#library-two-variants}

This query boils down to: "show me the subgraph of `//photos/frontend:lib` that
depends on both libraries". When shown in topological order, the last element
of the result is the most likely culprit.

<pre>bazel query 'allpaths(//photos/frontend:lib, //third_party/jpeglib)
                intersect
               allpaths(//photos/frontend:lib, //third_party/jpeg)'
//photos/frontend:lib
//photos/frontend:lib_impl
//photos/frontend:lib_dispatcher
//photos/frontend:icons
//photos/frontend/modules/gadgets:gadget_icon
//photos/thumbnailer:thumbnail_lib
//third_party/jpeg/img:renderer
</pre>

### What depends on  ... {:#depends-on}

#### What rules under bar depend on Y? {:#rules-bar-y}

<pre>bazel query 'bar/... intersect allpaths(bar/..., Y)'</pre>

Note: `X intersect allpaths(X, Y)` is the general idiom for the query "which X
depend on Y?" If expression X is non-trivial, it may be convenient to bind a
name to it using `let` to avoid duplication.

#### What targets directly depend on T, in T's package? {:#targets-t}

<pre>bazel query 'same_pkg_direct_rdeps(T)'</pre>

### How do I break a dependency ... {:#break-dependency}

<!-- TODO find a convincing value of X to plug in here -->

#### What dependency paths do I have to break to make `bar` no longer depend on X? {:#break-dependency-bar-x}

To output the graph to a `svg` file:

<pre>bazel query 'allpaths(bar/...,X)' --output graph | dot -Tsvg &gt; /tmp/dep.svg</pre>

### Misc {:#misc}

#### How many sequential steps are there in the `//foo-tests` build? {:#steps-footests}

Unfortunately, the query language can't currently give you the longest path
from x to y, but it can find the (or rather _a_) most distant node from the
starting point, or show you the _lengths_ of the longest path from x to every
y that it depends on. Use `maxrank`:

<pre>bazel query 'deps(//foo-tests)' --output maxrank | tail -1
85 //third_party/zlib:zutil.c</pre>

The result indicates that there exist paths of length 85 that must occur in
order in this build.
