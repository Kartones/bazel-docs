# host_repo.md


Public API

<a id="host_repo"></a>

## host_repo

<pre>
load("@aspect_bazel_lib//lib:host_repo.bzl", "host_repo")

host_repo(<a href="#host_repo-name">name</a>, <a href="#host_repo-repo_mapping">repo_mapping</a>)
</pre>

Exposes information about the host platform

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="host_repo-name"></a>name |  A unique name for this repository.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="host_repo-repo_mapping"></a>repo_mapping |  In `WORKSPACE` context only: a dictionary from local repository name to global repository name. This allows controls over workspace dependency resolution for dependencies of this repository.<br><br>For example, an entry `"@foo": "@bar"` declares that, for any time this repository depends on `@foo` (such as a dependency on `@foo//some:target`, it should actually resolve that dependency within globally-declared `@bar` (`@bar//some:target`).<br><br>This attribute is _not_ supported in `MODULE.bazel` context (when invoking a repository rule inside a module extension's implementation function).   | <a href="https://bazel.build/rules/lib/dict">Dictionary: String -> String</a> | optional |  |


# yq.md


Wrapper rule around the `yq` tool

From the documentation at https://mikefarah.gitbook.io/yq:

> yq is a a lightweight and portable command-line YAML processor.
> yq uses jq like syntax but works with yaml files as well as json.

## Usage examples

```starlark
load("@aspect_bazel_lib//lib:yq.bzl", "yq")
```

```starlark
# Remove fields
yq(
    name = "safe-config",
    srcs = ["config.yaml"],
    expression = "del(.credentials)",
)
```

```starlark
# Merge two yaml documents
yq(
    name = "ab",
    srcs = [
        "a.yaml",
        "b.yaml",
    ],
    expression = ". as $item ireduce ({}; . * $item )",
)
```

```starlark
# Split a yaml file into several files
yq(
    name = "split",
    srcs = ["multidoc.yaml"],
    outs = [
        "first.yml",
        "second.yml",
    ],
    args = [
        "-s '.a'",  # Split expression
        "--no-doc", # Exclude document separator --
    ],
)
```

```starlark
# Convert a yaml file to json
yq(
    name = "convert-to-json",
    srcs = ["foo.yaml"],
    args = ["-o=json"],
    outs = ["foo.json"],
)
```

```starlark
# Convert a json file to yaml
yq(
    name = "convert-to-yaml",
    srcs = ["bar.json"],
    args = ["-P"],
    outs = ["bar.yaml"],
)
```

```starlark
# Call yq in a genrule
genrule(
    name = "generate",
    srcs = ["farm.yaml"],
    outs = ["genrule_output.yaml"],
    cmd = "$(YQ_BIN) '.moo = "cow"' $(location farm.yaml) > $@",
    toolchains = ["@yq_toolchains//:resolved_toolchain"],
)
```

```starlark
# With --stamp, causes properties to be replaced by version control info.
yq(
    name = "stamped",
    srcs = ["package.yaml"],
    expression = "|".join([
        "load(strenv(STAMP)) as $stamp",
        # Provide a default using the "alternative operator" in case $stamp is empty dict.
        ".version = ($stamp.BUILD_EMBED_LABEL // "<unstamped>")",
    ]),
)
```

<a id="yq"></a>

## yq

<pre>
load("@aspect_bazel_lib//lib:yq.bzl", "yq")

yq(<a href="#yq-name">name</a>, <a href="#yq-srcs">srcs</a>, <a href="#yq-expression">expression</a>, <a href="#yq-args">args</a>, <a href="#yq-outs">outs</a>, <a href="#yq-kwargs">**kwargs</a>)
</pre>

Invoke yq with an expression on a set of input files.

yq is capable of parsing and outputting to other formats. See their [docs](https://mikefarah.gitbook.io/yq) for more examples.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="yq-name"></a>name |  Name of the rule   |  none |
| <a id="yq-srcs"></a>srcs |  List of input file labels   |  none |
| <a id="yq-expression"></a>expression |  yq expression (https://mikefarah.gitbook.io/yq/commands/evaluate).<br><br>Defaults to the identity expression ".". Subject to stamp variable replacements, see [Stamping](./stamping.md). When stamping is enabled, an environment variable named "STAMP" will be available in the expression.<br><br>Be careful to write the filter so that it handles unstamped builds, as in the example above.   |  `"."` |
| <a id="yq-args"></a>args |  Additional args to pass to yq.<br><br>Note that you do not need to pass _eval_ or _eval-all_ as this is handled automatically based on the number `srcs`. Passing the output format or the parse format is optional as these can be guessed based on the file extensions in `srcs` and `outs`.   |  `[]` |
| <a id="yq-outs"></a>outs |  Name of the output files.<br><br>Defaults to a single output with the name plus a ".yaml" extension, or the extension corresponding to a passed output argument (e.g., "-o=json"). For split operations you must declare all outputs as the name of the output files depends on the expression.   |  `None` |
| <a id="yq-kwargs"></a>kwargs |  Other common named parameters such as `tags` or `visibility`   |  none |


# repositories.md


Macros for loading dependencies and registering toolchains

<a id="aspect_bazel_lib_dependencies"></a>

## aspect_bazel_lib_dependencies

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "aspect_bazel_lib_dependencies")

aspect_bazel_lib_dependencies()
</pre>

Load dependencies required by aspect rules

<a id="aspect_bazel_lib_register_toolchains"></a>

## aspect_bazel_lib_register_toolchains

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "aspect_bazel_lib_register_toolchains")

aspect_bazel_lib_register_toolchains()
</pre>

Register all bazel-lib toolchains at their default versions.

To be more selective about which toolchains and versions to register,
call the individual toolchain registration macros.

<a id="register_bats_toolchains"></a>

## register_bats_toolchains

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "register_bats_toolchains")

register_bats_toolchains(<a href="#register_bats_toolchains-name">name</a>, <a href="#register_bats_toolchains-core_version">core_version</a>, <a href="#register_bats_toolchains-support_version">support_version</a>, <a href="#register_bats_toolchains-assert_version">assert_version</a>, <a href="#register_bats_toolchains-file_version">file_version</a>,
                         <a href="#register_bats_toolchains-libraries">libraries</a>, <a href="#register_bats_toolchains-register">register</a>)
</pre>

Registers bats toolchain and repositories

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="register_bats_toolchains-name"></a>name |  override the prefix for the generated toolchain repositories   |  `"bats"` |
| <a id="register_bats_toolchains-core_version"></a>core_version |  bats-core version to use   |  `"v1.10.0"` |
| <a id="register_bats_toolchains-support_version"></a>support_version |  bats-support version to use   |  `"v0.3.0"` |
| <a id="register_bats_toolchains-assert_version"></a>assert_version |  bats-assert version to use   |  `"v2.1.0"` |
| <a id="register_bats_toolchains-file_version"></a>file_version |  bats-file version to use   |  `"v0.4.0"` |
| <a id="register_bats_toolchains-libraries"></a>libraries |  additional labels for libraries   |  `[]` |
| <a id="register_bats_toolchains-register"></a>register |  whether to call through to native.register_toolchains. Should be True for WORKSPACE users, but false when used under bzlmod extension   |  `True` |

<a id="register_copy_directory_toolchains"></a>

## register_copy_directory_toolchains

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "register_copy_directory_toolchains")

register_copy_directory_toolchains(<a href="#register_copy_directory_toolchains-name">name</a>, <a href="#register_copy_directory_toolchains-register">register</a>)
</pre>

Registers copy_directory toolchain and repositories

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="register_copy_directory_toolchains-name"></a>name |  override the prefix for the generated toolchain repositories   |  `"copy_directory"` |
| <a id="register_copy_directory_toolchains-register"></a>register |  whether to call through to native.register_toolchains. Should be True for WORKSPACE users, but false when used under bzlmod extension   |  `True` |

<a id="register_copy_to_directory_toolchains"></a>

## register_copy_to_directory_toolchains

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "register_copy_to_directory_toolchains")

register_copy_to_directory_toolchains(<a href="#register_copy_to_directory_toolchains-name">name</a>, <a href="#register_copy_to_directory_toolchains-register">register</a>)
</pre>

Registers copy_to_directory toolchain and repositories

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="register_copy_to_directory_toolchains-name"></a>name |  override the prefix for the generated toolchain repositories   |  `"copy_to_directory"` |
| <a id="register_copy_to_directory_toolchains-register"></a>register |  whether to call through to native.register_toolchains. Should be True for WORKSPACE users, but false when used under bzlmod extension   |  `True` |

<a id="register_coreutils_toolchains"></a>

## register_coreutils_toolchains

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "register_coreutils_toolchains")

register_coreutils_toolchains(<a href="#register_coreutils_toolchains-name">name</a>, <a href="#register_coreutils_toolchains-version">version</a>, <a href="#register_coreutils_toolchains-register">register</a>)
</pre>

Registers coreutils toolchain and repositories

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="register_coreutils_toolchains-name"></a>name |  override the prefix for the generated toolchain repositories   |  `"coreutils"` |
| <a id="register_coreutils_toolchains-version"></a>version |  the version of coreutils to execute (see https://github.com/uutils/coreutils/releases)   |  `"0.0.27"` |
| <a id="register_coreutils_toolchains-register"></a>register |  whether to call through to native.register_toolchains. Should be True for WORKSPACE users, but false when used under bzlmod extension   |  `True` |

<a id="register_expand_template_toolchains"></a>

## register_expand_template_toolchains

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "register_expand_template_toolchains")

register_expand_template_toolchains(<a href="#register_expand_template_toolchains-name">name</a>, <a href="#register_expand_template_toolchains-register">register</a>)
</pre>

Registers expand_template toolchain and repositories

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="register_expand_template_toolchains-name"></a>name |  override the prefix for the generated toolchain repositories   |  `"expand_template"` |
| <a id="register_expand_template_toolchains-register"></a>register |  whether to call through to native.register_toolchains. Should be True for WORKSPACE users, but false when used under bzlmod extension   |  `True` |

<a id="register_jq_toolchains"></a>

## register_jq_toolchains

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "register_jq_toolchains")

register_jq_toolchains(<a href="#register_jq_toolchains-name">name</a>, <a href="#register_jq_toolchains-version">version</a>, <a href="#register_jq_toolchains-register">register</a>)
</pre>

Registers jq toolchain and repositories

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="register_jq_toolchains-name"></a>name |  override the prefix for the generated toolchain repositories   |  `"jq"` |
| <a id="register_jq_toolchains-version"></a>version |  the version of jq to execute (see https://github.com/stedolan/jq/releases)   |  `"1.7"` |
| <a id="register_jq_toolchains-register"></a>register |  whether to call through to native.register_toolchains. Should be True for WORKSPACE users, but false when used under bzlmod extension   |  `True` |

<a id="register_tar_toolchains"></a>

## register_tar_toolchains

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "register_tar_toolchains")

register_tar_toolchains(<a href="#register_tar_toolchains-name">name</a>, <a href="#register_tar_toolchains-register">register</a>)
</pre>

Registers bsdtar toolchain and repositories

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="register_tar_toolchains-name"></a>name |  override the prefix for the generated toolchain repositories   |  `"bsd_tar"` |
| <a id="register_tar_toolchains-register"></a>register |  whether to call through to native.register_toolchains. Should be True for WORKSPACE users, but false when used under bzlmod extension   |  `True` |

<a id="register_yq_toolchains"></a>

## register_yq_toolchains

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "register_yq_toolchains")

register_yq_toolchains(<a href="#register_yq_toolchains-name">name</a>, <a href="#register_yq_toolchains-version">version</a>, <a href="#register_yq_toolchains-register">register</a>)
</pre>

Registers yq toolchain and repositories

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="register_yq_toolchains-name"></a>name |  override the prefix for the generated toolchain repositories   |  `"yq"` |
| <a id="register_yq_toolchains-version"></a>version |  the version of yq to execute (see https://github.com/mikefarah/yq/releases)   |  `"4.25.2"` |
| <a id="register_yq_toolchains-register"></a>register |  whether to call through to native.register_toolchains. Should be True for WORKSPACE users, but false when used under bzlmod extension   |  `True` |

<a id="register_zstd_toolchains"></a>

## register_zstd_toolchains

<pre>
load("@aspect_bazel_lib//lib:repositories.bzl", "register_zstd_toolchains")

register_zstd_toolchains(<a href="#register_zstd_toolchains-name">name</a>, <a href="#register_zstd_toolchains-register">register</a>)
</pre>

Registers zstd toolchain and repositories

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="register_zstd_toolchains-name"></a>name |  override the prefix for the generated toolchain repositories   |  `"zstd"` |
| <a id="register_zstd_toolchains-register"></a>register |  whether to call through to native.register_toolchains. Should be True for WORKSPACE users, but false when used under bzlmod extension   |  `True` |


# copy_directory.md


A rule that copies a directory to another place.

The rule uses a precompiled binary to perform the copy, so no shell is required.

## Preserving modification times

`copy_directory` and `copy_to_directory` have a `preserve_mtime` attribute, however
there are two caveats to consider when using this feature:

1. Remote Execution / Caching: These layers will reset the modify time and are
    incompatible with this feature. To avoid these failures the [no-remote tag](https://bazel.build/reference/be/common-definitions)
    can be added.
2. Caching: Changes to only the modified time will not re-trigger cached actions. This can
    be worked around by using a clean build when these types of changes occur. For tests the
    [external tag](https://bazel.build/reference/be/common-definitions) can be used but this
    will result in tests never being cached.

<a id="copy_directory"></a>

## copy_directory

<pre>
load("@aspect_bazel_lib//lib:copy_directory.bzl", "copy_directory")

copy_directory(<a href="#copy_directory-name">name</a>, <a href="#copy_directory-src">src</a>, <a href="#copy_directory-out">out</a>, <a href="#copy_directory-hardlink">hardlink</a>, <a href="#copy_directory-kwargs">**kwargs</a>)
</pre>

Copies a directory to another location.

This rule uses a precompiled binary to perform the copy, so no shell is required.

If using this rule with source directories, it is recommended that you use the
`--host_jvm_args=-DBAZEL_TRACK_SOURCE_DIRECTORIES=1` startup option so that changes
to files within source directories are detected. See
https://github.com/bazelbuild/bazel/commit/c64421bc35214f0414e4f4226cc953e8c55fa0d2
for more context.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="copy_directory-name"></a>name |  Name of the rule.   |  none |
| <a id="copy_directory-src"></a>src |  The directory to make a copy of. Can be a source directory or TreeArtifact.   |  none |
| <a id="copy_directory-out"></a>out |  Path of the output directory, relative to this package.   |  none |
| <a id="copy_directory-hardlink"></a>hardlink |  Controls when to use hardlinks to files instead of making copies.<br><br>Creating hardlinks is much faster than making copies of files with the caveat that hardlinks share file permissions with their source.<br><br>Since Bazel removes write permissions on files in the output tree after an action completes, hardlinks to source files within source directories is not recommended since write permissions will be inadvertently removed from sources files.<br><br>- "auto": hardlinks are used if src is a tree artifact already in the output tree - "off": files are always copied - "on": hardlinks are always used (not recommended)   |  `"auto"` |
| <a id="copy_directory-kwargs"></a>kwargs |  further keyword arguments, e.g. `visibility`   |  none |

<a id="copy_directory_bin_action"></a>

## copy_directory_bin_action

<pre>
load("@aspect_bazel_lib//lib:copy_directory.bzl", "copy_directory_bin_action")

copy_directory_bin_action(<a href="#copy_directory_bin_action-ctx">ctx</a>, <a href="#copy_directory_bin_action-src">src</a>, <a href="#copy_directory_bin_action-dst">dst</a>, <a href="#copy_directory_bin_action-copy_directory_bin">copy_directory_bin</a>, <a href="#copy_directory_bin_action-copy_directory_toolchain">copy_directory_toolchain</a>, <a href="#copy_directory_bin_action-hardlink">hardlink</a>,
                          <a href="#copy_directory_bin_action-verbose">verbose</a>, <a href="#copy_directory_bin_action-preserve_mtime">preserve_mtime</a>)
</pre>

Factory function that creates an action to copy a directory from src to dst using a tool binary.

The tool binary will typically be the `@aspect_bazel_lib//tools/copy_directory` `go_binary`
either built from source or provided by a toolchain.

This helper is used by the copy_directory rule. It is exposed as a public API so it can be used
within other rule implementations.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="copy_directory_bin_action-ctx"></a>ctx |  The rule context.   |  none |
| <a id="copy_directory_bin_action-src"></a>src |  The source directory to copy.   |  none |
| <a id="copy_directory_bin_action-dst"></a>dst |  The directory to copy to. Must be a TreeArtifact.   |  none |
| <a id="copy_directory_bin_action-copy_directory_bin"></a>copy_directory_bin |  Copy to directory tool binary.   |  none |
| <a id="copy_directory_bin_action-copy_directory_toolchain"></a>copy_directory_toolchain |  The toolchain type for Auto Exec Groups. The default is probably what you want.   |  `"@aspect_bazel_lib//lib:copy_directory_toolchain_type"` |
| <a id="copy_directory_bin_action-hardlink"></a>hardlink |  Controls when to use hardlinks to files instead of making copies.<br><br>See copy_directory rule documentation for more details.   |  `"auto"` |
| <a id="copy_directory_bin_action-verbose"></a>verbose |  print verbose logs to stdout   |  `False` |
| <a id="copy_directory_bin_action-preserve_mtime"></a>preserve_mtime |  preserve the modified time from the source. See the caveats above about interactions with remote execution and caching.   |  `False` |


# jq.md


Wrapper rule around the popular `jq` utility.

For jq documentation, see https://stedolan.github.io/jq/.

## Usage examples

```starlark
load("@aspect_bazel_lib//lib:jq.bzl", "jq")
```

Create a new file `bazel-out/.../no_srcs.json` containing some JSON data:
```starlark
jq(
    name = "no_srcs",
    srcs = [],
    filter = ".name = "Alice"",
)
```

Remove a field from `package.json`:

> The output path `bazel-out/.../package.json` matches the path of the source file,
> which means you must refer to the label `:no_dev_deps` to reference the output,
> since Bazel doesn't provide a label for an output file that collides with an input file.

```starlark
jq(
    name = "no_dev_deps",
    srcs = ["package.json"],
    out = "package.json",
    filter = "del(.devDependencies)",
)
```

Merge data from `bar.json` on top of `foo.json`, producing `foobar.json`:
```starlark
jq(
    name = "merged",
    srcs = ["foo.json", "bar.json"],
    filter = ".[0] * .[1]",
    args = ["--slurp"],
    out = "foobar.json",
)
```

Long filters can be split over several lines with comments:
```starlark
jq(
    name = "complex",
    srcs = ["a.json", "b.json"],
    filter = """
        .[0] as $a
        # Take select fields from b.json
        | (.[1] | {foo, bar, tags}) as $b
        # Merge b onto a
        | ($a * $b)
        # Combine 'tags' array from both
        | .tags = ($a.tags + $b.tags)
        # Add new field
        + {\"aspect_is_cool\": true}
    """,
    args = ["--slurp"],
)
```

Load filter from a file `filter.jq`, making it easier to edit complex filters:
```starlark
jq(
    name = "merged",
    srcs = ["foo.json", "bar.json"],
    filter_file = "filter.jq",
    args = ["--slurp"],
    out = "foobar.json",
)
```

Convert [genquery](https://bazel.build/reference/be/general#genquery) output to JSON.
```starlark
genquery(
    name = "deps",
    expression = "deps(//some:target)",
    scope = ["//some:target"],
)

jq(
    name = "deps_json",
    srcs = [":deps"],
    args = [
        "--raw-input",
        "--slurp",
    ],
    filter = "{ deps: split(\"\\n\") | map(select(. | length > 0)) }",
)
```

When Bazel is run with `--stamp`, replace some properties with version control info:
```starlark
jq(
    name = "stamped",
    srcs = ["package.json"],
    filter = "|".join([
        # Don't directly reference $STAMP as it's only set when stamping
        # This 'as' syntax results in $stamp being null in unstamped builds.
        "$ARGS.named.STAMP as $stamp",
        # Provide a default using the "alternative operator" in case $stamp is null.
        ".version = ($stamp[0].BUILD_EMBED_LABEL // "<unstamped>")",
    ]),
)
```

jq is exposed as a "Make variable", so you could use it directly from a `genrule` by referencing the toolchain.

```starlark
genrule(
    name = "case_genrule",
    srcs = ["a.json"],
    outs = ["genrule_output.json"],
    cmd = "$(JQ_BIN) '.' $(location a.json) > $@",
    toolchains = ["@jq_toolchains//:resolved_toolchain"],
)
```

<a id="jq"></a>

## jq

<pre>
load("@aspect_bazel_lib//lib:jq.bzl", "jq")

jq(<a href="#jq-name">name</a>, <a href="#jq-srcs">srcs</a>, <a href="#jq-filter">filter</a>, <a href="#jq-filter_file">filter_file</a>, <a href="#jq-args">args</a>, <a href="#jq-out">out</a>, <a href="#jq-data">data</a>, <a href="#jq-expand_args">expand_args</a>, <a href="#jq-kwargs">**kwargs</a>)
</pre>

Invoke jq with a filter on a set of json input files.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="jq-name"></a>name |  Name of the rule   |  none |
| <a id="jq-srcs"></a>srcs |  List of input files. May be empty.   |  none |
| <a id="jq-filter"></a>filter |  Filter expression (https://stedolan.github.io/jq/manual/#Basicfilters). Subject to stamp variable replacements, see [Stamping](./stamping.md). When stamping is enabled, a variable named "STAMP" will be available in the filter.<br><br>Be careful to write the filter so that it handles unstamped builds, as in the example above.   |  `None` |
| <a id="jq-filter_file"></a>filter_file |  File containing filter expression (alternative to `filter`)   |  `None` |
| <a id="jq-args"></a>args |  Additional args to pass to jq   |  `[]` |
| <a id="jq-out"></a>out |  Name of the output json file; defaults to the rule name plus ".json"   |  `None` |
| <a id="jq-data"></a>data |  List of additional files. May be empty.   |  `[]` |
| <a id="jq-expand_args"></a>expand_args |  Run bazel's location and make variable expansion on the args.   |  `False` |
| <a id="jq-kwargs"></a>kwargs |  Other common named parameters such as `tags` or `visibility`   |  none |


# bats.md


A test rule that invokes the [Bash Automated Testing System](https://github.com/bats-core/bats-core).

For example, a `bats_test` target containing a single .bat and basic configuration:

```starlark
bats_test(
    name = "my_test",
    size = "small",
    srcs = [
        "my_test.bats",
    ],
    data = [
        "data.bin",
    ],
    env = {
        "DATA_PATH": "$(location :data.bin)",
    },
    args = ["--timing"],
)
```

<a id="bats_test"></a>

## bats_test

<pre>
load("@aspect_bazel_lib//lib:bats.bzl", "bats_test")

bats_test(<a href="#bats_test-name">name</a>, <a href="#bats_test-srcs">srcs</a>, <a href="#bats_test-data">data</a>, <a href="#bats_test-env">env</a>)
</pre>

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="bats_test-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="bats_test-srcs"></a>srcs |  Test files   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="bats_test-data"></a>data |  Runtime dependencies of the test.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="bats_test-env"></a>env |  Environment variables of the action.<br><br>Subject to [$(location)](https://bazel.build/reference/be/make-variables#predefined_label_variables) and ["Make variable"](https://bazel.build/reference/be/make-variables) substitution.   | <a href="https://bazel.build/rules/lib/dict">Dictionary: String -> String</a> | optional |  `{}`  |


# utils.md


General-purpose Starlark utility functions

## Usage example

```starlark
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

out_label = utils.to_label(out_file)
```

<a id="consistent_label_str"></a>

## consistent_label_str

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "consistent_label_str")

consistent_label_str(<a href="#consistent_label_str-ctx">ctx</a>, <a href="#consistent_label_str-label">label</a>)
</pre>

Generate a consistent label string for all Bazel versions.

Starting in Bazel 6, the workspace name is empty for the local workspace and there's no other
way to determine it. This behavior differs from Bazel 5 where the local workspace name was fully
qualified in str(label).

This utility function is meant for use in rules and requires the rule context to determine the
user's workspace name (`ctx.workspace_name`).

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="consistent_label_str-ctx"></a>ctx |  The rule context.   |  none |
| <a id="consistent_label_str-label"></a>label |  A Label.   |  none |

**RETURNS**

String representation of the label including the repository name if the label is from an
  external repository. For labels in the user's repository the label will start with `@//`.

<a id="default_timeout"></a>

## default_timeout

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "default_timeout")

default_timeout(<a href="#default_timeout-size">size</a>, <a href="#default_timeout-timeout">timeout</a>)
</pre>

Provide a sane default for *_test timeout attribute.

The [test-encyclopedia](https://bazel.build/reference/test-encyclopedia) says:

> Tests may return arbitrarily fast regardless of timeout.
> A test is not penalized for an overgenerous timeout, although a warning may be issued:
> you should generally set your timeout as tight as you can without incurring any flakiness.

However Bazel's default for timeout is medium, which is dumb given this guidance.

It also says:

> Tests which do not explicitly specify a timeout have one implied based on the test's size as follows

Therefore if size is specified, we should allow timeout to take its implied default.
If neither is set, then we can fix Bazel's wrong default here to avoid warnings under
`--test_verbose_timeout_warnings`.

This function can be used in a macro which wraps a testing rule.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="default_timeout-size"></a>size |  the size attribute of a test target   |  none |
| <a id="default_timeout-timeout"></a>timeout |  the timeout attribute of a test target   |  none |

**RETURNS**

"short" if neither is set, otherwise timeout

<a id="file_exists"></a>

## file_exists

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "file_exists")

file_exists(<a href="#file_exists-path">path</a>)
</pre>

Check whether a file exists.

Useful in macros to set defaults for a configuration file if it is present.
This can only be called during the loading phase, not from a rule implementation.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="file_exists-path"></a>path |  a label, or a string which is a path relative to this package   |  none |

<a id="glob_directories"></a>

## glob_directories

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "glob_directories")

glob_directories(<a href="#glob_directories-include">include</a>, <a href="#glob_directories-kwargs">**kwargs</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="glob_directories-include"></a>include |  <p align="center"> - </p>   |  none |
| <a id="glob_directories-kwargs"></a>kwargs |  <p align="center"> - </p>   |  none |

<a id="is_bazel_6_or_greater"></a>

## is_bazel_6_or_greater

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "is_bazel_6_or_greater")

is_bazel_6_or_greater()
</pre>

Detects if the Bazel version being used is greater than or equal to 6 (including Bazel 6 pre-releases and RCs).

Detecting Bazel 6 or greater is particularly useful in rules as slightly different code paths may be needed to
support bzlmod which was added in Bazel 6.

Unlike the undocumented `native.bazel_version`, which only works in WORKSPACE and repository rules, this function can
be used in rules and BUILD files.

An alternate approach to make the Bazel version available in BUILD files and rules would be to
use the [host_repo](https://github.com/bazel-contrib/bazel-lib/blob/main/docs/host_repo.md) repository rule
which contains the bazel_version in the exported `host` struct:

WORKSPACE:
```
load("@aspect_bazel_lib//lib:host_repo.bzl", "host_repo")
host_repo(name = "aspect_bazel_lib_host")
```

BUILD.bazel:
```
load("@aspect_bazel_lib_host//:defs.bzl", "host")
print(host.bazel_version)
```

That approach, however, incurs a cost in the user's WORKSPACE.

**RETURNS**

True if the Bazel version being used is greater than or equal to 6 (including pre-releases and RCs)

<a id="is_bazel_7_or_greater"></a>

## is_bazel_7_or_greater

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "is_bazel_7_or_greater")

is_bazel_7_or_greater()
</pre>

Detects if the Bazel version being used is greater than or equal to 7 (including Bazel 7 pre-releases and RCs).

Unlike the undocumented `native.bazel_version`, which only works in WORKSPACE and repository rules, this function can
be used in rules and BUILD files.

An alternate approach to make the Bazel version available in BUILD files and rules would be to
use the [host_repo](https://github.com/bazel-contrib/bazel-lib/blob/main/docs/host_repo.md) repository rule
which contains the bazel_version in the exported `host` struct:

WORKSPACE:
```
load("@aspect_bazel_lib//lib:host_repo.bzl", "host_repo")
host_repo(name = "aspect_bazel_lib_host")
```

BUILD.bazel:
```
load("@aspect_bazel_lib_host//:defs.bzl", "host")
print(host.bazel_version)
```

That approach, however, incurs a cost in the user's WORKSPACE.

**RETURNS**

True if the Bazel version being used is greater than or equal to 7 (including pre-releases and RCs)

<a id="is_bzlmod_enabled"></a>

## is_bzlmod_enabled

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "is_bzlmod_enabled")

is_bzlmod_enabled()
</pre>

Detect the value of the --enable_bzlmod flag

<a id="is_external_label"></a>

## is_external_label

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "is_external_label")

is_external_label(<a href="#is_external_label-param">param</a>)
</pre>

Returns True if the given Label (or stringy version of a label) represents a target outside of the workspace

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="is_external_label-param"></a>param |  a string or label   |  none |

**RETURNS**

a bool

<a id="maybe_http_archive"></a>

## maybe_http_archive

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "maybe_http_archive")

maybe_http_archive(<a href="#maybe_http_archive-kwargs">**kwargs</a>)
</pre>

Adapts a maybe(http_archive, ...) to look like an http_archive.

This makes WORKSPACE dependencies easier to read and update.

Typical usage looks like,

```
load("//lib:utils.bzl", http_archive = "maybe_http_archive")

http_archive(
    name = "aspect_rules_js",
    sha256 = "5bb643d9e119832a383e67f946dc752b6d719d66d1df9b46d840509ceb53e1f1",
    strip_prefix = "rules_js-1.6.2",
    url = "https://github.com/aspect-build/rules_js/archive/refs/tags/v1.6.2.tar.gz",
)
```

instead of the classic maybe pattern of,

```
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:utils.bzl", "maybe")

maybe(
    http_archive,
    name = "aspect_rules_js",
    sha256 = "5bb643d9e119832a383e67f946dc752b6d719d66d1df9b46d840509ceb53e1f1",
    strip_prefix = "rules_js-1.6.2",
    url = "https://github.com/aspect-build/rules_js/archive/refs/tags/v1.6.2.tar.gz",
)
```

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="maybe_http_archive-kwargs"></a>kwargs |  all arguments to pass-forward to http_archive   |  none |

<a id="path_to_workspace_root"></a>

## path_to_workspace_root

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "path_to_workspace_root")

path_to_workspace_root()
</pre>

Returns the path to the workspace root under bazel

**RETURNS**

Path to the workspace root

<a id="propagate_common_binary_rule_attributes"></a>

## propagate_common_binary_rule_attributes

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "propagate_common_binary_rule_attributes")

propagate_common_binary_rule_attributes(<a href="#propagate_common_binary_rule_attributes-attrs">attrs</a>)
</pre>

Returns a dict of rule parameters filtered from the input dict that only contains the ones that are common to all binary rules

These are listed in Bazel's documentation:
https://bazel.build/reference/be/common-definitions#common-attributes
https://bazel.build/reference/be/common-definitions#common-attributes-binary

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="propagate_common_binary_rule_attributes-attrs"></a>attrs |  Dict of parameters to filter   |  none |

**RETURNS**

The dict of parameters, containing only common binary attributes

<a id="propagate_common_rule_attributes"></a>

## propagate_common_rule_attributes

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "propagate_common_rule_attributes")

propagate_common_rule_attributes(<a href="#propagate_common_rule_attributes-attrs">attrs</a>)
</pre>

Returns a dict of rule parameters filtered from the input dict that only contains the ones that are common to all rules

These are listed in Bazel's documentation:
https://bazel.build/reference/be/common-definitions#common-attributes

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="propagate_common_rule_attributes-attrs"></a>attrs |  Dict of parameters to filter   |  none |

**RETURNS**

The dict of parameters, containing only common attributes

<a id="propagate_common_test_rule_attributes"></a>

## propagate_common_test_rule_attributes

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "propagate_common_test_rule_attributes")

propagate_common_test_rule_attributes(<a href="#propagate_common_test_rule_attributes-attrs">attrs</a>)
</pre>

Returns a dict of rule parameters filtered from the input dict that only contains the ones that are common to all test rules

These are listed in Bazel's documentation:
https://bazel.build/reference/be/common-definitions#common-attributes
https://bazel.build/reference/be/common-definitions#common-attributes-tests

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="propagate_common_test_rule_attributes-attrs"></a>attrs |  Dict of parameters to filter   |  none |

**RETURNS**

The dict of parameters, containing only common test attributes

<a id="propagate_well_known_tags"></a>

## propagate_well_known_tags

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "propagate_well_known_tags")

propagate_well_known_tags(<a href="#propagate_well_known_tags-tags">tags</a>)
</pre>

Returns a list of tags filtered from the input set that only contains the ones that are considered "well known"

These are listed in Bazel's documentation:
https://docs.bazel.build/versions/main/test-encyclopedia.html#tag-conventions
https://docs.bazel.build/versions/main/be/common-definitions.html#common-attributes

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="propagate_well_known_tags-tags"></a>tags |  List of tags to filter   |  `[]` |

**RETURNS**

List of tags that only contains the well known set

<a id="to_label"></a>

## to_label

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "to_label")

to_label(<a href="#to_label-param">param</a>)
</pre>

Converts a string to a Label. If Label is supplied, the same label is returned.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="to_label-param"></a>param |  a string representing a label or a Label   |  none |

**RETURNS**

a Label

<a id="utils.consistent_label_str"></a>

## utils.consistent_label_str

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.consistent_label_str(<a href="#utils.consistent_label_str-ctx">ctx</a>, <a href="#utils.consistent_label_str-label">label</a>)
</pre>

Generate a consistent label string for all Bazel versions.

Starting in Bazel 6, the workspace name is empty for the local workspace and there's no other
way to determine it. This behavior differs from Bazel 5 where the local workspace name was fully
qualified in str(label).

This utility function is meant for use in rules and requires the rule context to determine the
user's workspace name (`ctx.workspace_name`).

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.consistent_label_str-ctx"></a>ctx |  The rule context.   |  none |
| <a id="utils.consistent_label_str-label"></a>label |  A Label.   |  none |

**RETURNS**

String representation of the label including the repository name if the label is from an
  external repository. For labels in the user's repository the label will start with `@//`.

<a id="utils.default_timeout"></a>

## utils.default_timeout

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.default_timeout(<a href="#utils.default_timeout-size">size</a>, <a href="#utils.default_timeout-timeout">timeout</a>)
</pre>

Provide a sane default for *_test timeout attribute.

The [test-encyclopedia](https://bazel.build/reference/test-encyclopedia) says:

> Tests may return arbitrarily fast regardless of timeout.
> A test is not penalized for an overgenerous timeout, although a warning may be issued:
> you should generally set your timeout as tight as you can without incurring any flakiness.

However Bazel's default for timeout is medium, which is dumb given this guidance.

It also says:

> Tests which do not explicitly specify a timeout have one implied based on the test's size as follows

Therefore if size is specified, we should allow timeout to take its implied default.
If neither is set, then we can fix Bazel's wrong default here to avoid warnings under
`--test_verbose_timeout_warnings`.

This function can be used in a macro which wraps a testing rule.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.default_timeout-size"></a>size |  the size attribute of a test target   |  none |
| <a id="utils.default_timeout-timeout"></a>timeout |  the timeout attribute of a test target   |  none |

**RETURNS**

"short" if neither is set, otherwise timeout

<a id="utils.file_exists"></a>

## utils.file_exists

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.file_exists(<a href="#utils.file_exists-path">path</a>)
</pre>

Check whether a file exists.

Useful in macros to set defaults for a configuration file if it is present.
This can only be called during the loading phase, not from a rule implementation.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.file_exists-path"></a>path |  a label, or a string which is a path relative to this package   |  none |

<a id="utils.glob_directories"></a>

## utils.glob_directories

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.glob_directories(<a href="#utils.glob_directories-include">include</a>, <a href="#utils.glob_directories-kwargs">**kwargs</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.glob_directories-include"></a>include |  <p align="center"> - </p>   |  none |
| <a id="utils.glob_directories-kwargs"></a>kwargs |  <p align="center"> - </p>   |  none |

<a id="utils.is_bazel_6_or_greater"></a>

## utils.is_bazel_6_or_greater

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.is_bazel_6_or_greater()
</pre>

Detects if the Bazel version being used is greater than or equal to 6 (including Bazel 6 pre-releases and RCs).

Detecting Bazel 6 or greater is particularly useful in rules as slightly different code paths may be needed to
support bzlmod which was added in Bazel 6.

Unlike the undocumented `native.bazel_version`, which only works in WORKSPACE and repository rules, this function can
be used in rules and BUILD files.

An alternate approach to make the Bazel version available in BUILD files and rules would be to
use the [host_repo](https://github.com/bazel-contrib/bazel-lib/blob/main/docs/host_repo.md) repository rule
which contains the bazel_version in the exported `host` struct:

WORKSPACE:
```
load("@aspect_bazel_lib//lib:host_repo.bzl", "host_repo")
host_repo(name = "aspect_bazel_lib_host")
```

BUILD.bazel:
```
load("@aspect_bazel_lib_host//:defs.bzl", "host")
print(host.bazel_version)
```

That approach, however, incurs a cost in the user's WORKSPACE.

**RETURNS**

True if the Bazel version being used is greater than or equal to 6 (including pre-releases and RCs)

<a id="utils.is_bazel_7_or_greater"></a>

## utils.is_bazel_7_or_greater

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.is_bazel_7_or_greater()
</pre>

Detects if the Bazel version being used is greater than or equal to 7 (including Bazel 7 pre-releases and RCs).

Unlike the undocumented `native.bazel_version`, which only works in WORKSPACE and repository rules, this function can
be used in rules and BUILD files.

An alternate approach to make the Bazel version available in BUILD files and rules would be to
use the [host_repo](https://github.com/bazel-contrib/bazel-lib/blob/main/docs/host_repo.md) repository rule
which contains the bazel_version in the exported `host` struct:

WORKSPACE:
```
load("@aspect_bazel_lib//lib:host_repo.bzl", "host_repo")
host_repo(name = "aspect_bazel_lib_host")
```

BUILD.bazel:
```
load("@aspect_bazel_lib_host//:defs.bzl", "host")
print(host.bazel_version)
```

That approach, however, incurs a cost in the user's WORKSPACE.

**RETURNS**

True if the Bazel version being used is greater than or equal to 7 (including pre-releases and RCs)

<a id="utils.is_bzlmod_enabled"></a>

## utils.is_bzlmod_enabled

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.is_bzlmod_enabled()
</pre>

Detect the value of the --enable_bzlmod flag

<a id="utils.is_external_label"></a>

## utils.is_external_label

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.is_external_label(<a href="#utils.is_external_label-param">param</a>)
</pre>

Returns True if the given Label (or stringy version of a label) represents a target outside of the workspace

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.is_external_label-param"></a>param |  a string or label   |  none |

**RETURNS**

a bool

<a id="utils.maybe_http_archive"></a>

## utils.maybe_http_archive

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.maybe_http_archive(<a href="#utils.maybe_http_archive-kwargs">**kwargs</a>)
</pre>

Adapts a maybe(http_archive, ...) to look like an http_archive.

This makes WORKSPACE dependencies easier to read and update.

Typical usage looks like,

```
load("//lib:utils.bzl", http_archive = "maybe_http_archive")

http_archive(
    name = "aspect_rules_js",
    sha256 = "5bb643d9e119832a383e67f946dc752b6d719d66d1df9b46d840509ceb53e1f1",
    strip_prefix = "rules_js-1.6.2",
    url = "https://github.com/aspect-build/rules_js/archive/refs/tags/v1.6.2.tar.gz",
)
```

instead of the classic maybe pattern of,

```
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:utils.bzl", "maybe")

maybe(
    http_archive,
    name = "aspect_rules_js",
    sha256 = "5bb643d9e119832a383e67f946dc752b6d719d66d1df9b46d840509ceb53e1f1",
    strip_prefix = "rules_js-1.6.2",
    url = "https://github.com/aspect-build/rules_js/archive/refs/tags/v1.6.2.tar.gz",
)
```

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.maybe_http_archive-kwargs"></a>kwargs |  all arguments to pass-forward to http_archive   |  none |

<a id="utils.path_to_workspace_root"></a>

## utils.path_to_workspace_root

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.path_to_workspace_root()
</pre>

Returns the path to the workspace root under bazel

**RETURNS**

Path to the workspace root

<a id="utils.propagate_common_binary_rule_attributes"></a>

## utils.propagate_common_binary_rule_attributes

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.propagate_common_binary_rule_attributes(<a href="#utils.propagate_common_binary_rule_attributes-attrs">attrs</a>)
</pre>

Returns a dict of rule parameters filtered from the input dict that only contains the ones that are common to all binary rules

These are listed in Bazel's documentation:
https://bazel.build/reference/be/common-definitions#common-attributes
https://bazel.build/reference/be/common-definitions#common-attributes-binary

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.propagate_common_binary_rule_attributes-attrs"></a>attrs |  Dict of parameters to filter   |  none |

**RETURNS**

The dict of parameters, containing only common binary attributes

<a id="utils.propagate_common_rule_attributes"></a>

## utils.propagate_common_rule_attributes

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.propagate_common_rule_attributes(<a href="#utils.propagate_common_rule_attributes-attrs">attrs</a>)
</pre>

Returns a dict of rule parameters filtered from the input dict that only contains the ones that are common to all rules

These are listed in Bazel's documentation:
https://bazel.build/reference/be/common-definitions#common-attributes

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.propagate_common_rule_attributes-attrs"></a>attrs |  Dict of parameters to filter   |  none |

**RETURNS**

The dict of parameters, containing only common attributes

<a id="utils.propagate_common_test_rule_attributes"></a>

## utils.propagate_common_test_rule_attributes

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.propagate_common_test_rule_attributes(<a href="#utils.propagate_common_test_rule_attributes-attrs">attrs</a>)
</pre>

Returns a dict of rule parameters filtered from the input dict that only contains the ones that are common to all test rules

These are listed in Bazel's documentation:
https://bazel.build/reference/be/common-definitions#common-attributes
https://bazel.build/reference/be/common-definitions#common-attributes-tests

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.propagate_common_test_rule_attributes-attrs"></a>attrs |  Dict of parameters to filter   |  none |

**RETURNS**

The dict of parameters, containing only common test attributes

<a id="utils.propagate_well_known_tags"></a>

## utils.propagate_well_known_tags

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.propagate_well_known_tags(<a href="#utils.propagate_well_known_tags-tags">tags</a>)
</pre>

Returns a list of tags filtered from the input set that only contains the ones that are considered "well known"

These are listed in Bazel's documentation:
https://docs.bazel.build/versions/main/test-encyclopedia.html#tag-conventions
https://docs.bazel.build/versions/main/be/common-definitions.html#common-attributes

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.propagate_well_known_tags-tags"></a>tags |  List of tags to filter   |  `[]` |

**RETURNS**

List of tags that only contains the well known set

<a id="utils.to_label"></a>

## utils.to_label

<pre>
load("@aspect_bazel_lib//lib:utils.bzl", "utils")

utils.to_label(<a href="#utils.to_label-param">param</a>)
</pre>

Converts a string to a Label. If Label is supplied, the same label is returned.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="utils.to_label-param"></a>param |  a string representing a label or a Label   |  none |

**RETURNS**

a Label


# transitions.md


Rules for working with transitions.

<a id="platform_transition_binary"></a>

## platform_transition_binary

<pre>
load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_binary")

platform_transition_binary(<a href="#platform_transition_binary-name">name</a>, <a href="#platform_transition_binary-basename">basename</a>, <a href="#platform_transition_binary-binary">binary</a>, <a href="#platform_transition_binary-target_platform">target_platform</a>)
</pre>

Transitions the binary to use the provided platform. Will forward RunEnvironmentInfo

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="platform_transition_binary-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="platform_transition_binary-basename"></a>basename |  -   | String | optional |  `""`  |
| <a id="platform_transition_binary-binary"></a>binary |  -   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="platform_transition_binary-target_platform"></a>target_platform |  The target platform to transition the binary.   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |

<a id="platform_transition_filegroup"></a>

## platform_transition_filegroup

<pre>
load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_filegroup")

platform_transition_filegroup(<a href="#platform_transition_filegroup-name">name</a>, <a href="#platform_transition_filegroup-srcs">srcs</a>, <a href="#platform_transition_filegroup-target_platform">target_platform</a>)
</pre>

Transitions the srcs to use the provided platform. The filegroup will contain artifacts for the target platform.

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="platform_transition_filegroup-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="platform_transition_filegroup-srcs"></a>srcs |  The input to be transitioned to the target platform.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="platform_transition_filegroup-target_platform"></a>target_platform |  The target platform to transition the srcs.   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |

<a id="platform_transition_test"></a>

## platform_transition_test

<pre>
load("@aspect_bazel_lib//lib:transitions.bzl", "platform_transition_test")

platform_transition_test(<a href="#platform_transition_test-name">name</a>, <a href="#platform_transition_test-basename">basename</a>, <a href="#platform_transition_test-binary">binary</a>, <a href="#platform_transition_test-target_platform">target_platform</a>)
</pre>

Transitions the test to use the provided platform. Will forward RunEnvironmentInfo

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="platform_transition_test-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="platform_transition_test-basename"></a>basename |  -   | String | optional |  `""`  |
| <a id="platform_transition_test-binary"></a>binary |  -   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="platform_transition_test-target_platform"></a>target_platform |  The target platform to transition the binary.   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |


# platform_utils.md


Public API

<a id="platform_utils.host_platform_is_darwin"></a>

## platform_utils.host_platform_is_darwin

<pre>
load("@aspect_bazel_lib//lib:platform_utils.bzl", "platform_utils")

platform_utils.host_platform_is_darwin()
</pre>

<a id="platform_utils.host_platform_is_linux"></a>

## platform_utils.host_platform_is_linux

<pre>
load("@aspect_bazel_lib//lib:platform_utils.bzl", "platform_utils")

platform_utils.host_platform_is_linux()
</pre>

<a id="platform_utils.host_platform_is_windows"></a>

## platform_utils.host_platform_is_windows

<pre>
load("@aspect_bazel_lib//lib:platform_utils.bzl", "platform_utils")

platform_utils.host_platform_is_windows()
</pre>


# strings.md


Utilities for strings

<a id="chr"></a>

## chr

<pre>
load("@aspect_bazel_lib//lib:strings.bzl", "chr")

chr(<a href="#chr-i">i</a>)
</pre>

returns a string encoding a codepoint

chr returns a string that encodes the single Unicode code
point whose value is specified by the integer `i`

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="chr-i"></a>i |  position of the character   |  none |

**RETURNS**

unicode string of the position

<a id="hex"></a>

## hex

<pre>
load("@aspect_bazel_lib//lib:strings.bzl", "hex")

hex(<a href="#hex-number">number</a>)
</pre>

Format integer to hexadecimal representation

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="hex-number"></a>number |  number to format   |  none |

**RETURNS**

hexadecimal representation of the number argument

<a id="ord"></a>

## ord

<pre>
load("@aspect_bazel_lib//lib:strings.bzl", "ord")

ord(<a href="#ord-c">c</a>)
</pre>

returns the codepoint of a character

ord(c) returns the integer value of the sole Unicode code point
encoded by the string `c`.

If `c` does not encode exactly one Unicode code point, `ord` fails.
Each invalid code within the string is treated as if it encodes the
Unicode replacement character, U+FFFD.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="ord-c"></a>c |  character whose codepoint to be returned.   |  none |

**RETURNS**

codepoint of `c` argument.

<a id="split_args"></a>

## split_args

<pre>
load("@aspect_bazel_lib//lib:strings.bzl", "split_args")

split_args(<a href="#split_args-s">s</a>)
</pre>

Split a string into a list space separated arguments

Unlike the naive `.split(" ")`, this function takes quoted strings
and escapes into account.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="split_args-s"></a>s |  input string   |  none |

**RETURNS**

list of strings with each an argument found in the input string


# run_binary.md


Runs a binary as a build action. This rule does not require Bash (unlike native.genrule()).

This fork of bazel-skylib's run_binary adds directory output support and better makevar expansions.

<a id="run_binary"></a>

## run_binary

<pre>
load("@aspect_bazel_lib//lib:run_binary.bzl", "run_binary")

run_binary(<a href="#run_binary-name">name</a>, <a href="#run_binary-tool">tool</a>, <a href="#run_binary-srcs">srcs</a>, <a href="#run_binary-args">args</a>, <a href="#run_binary-env">env</a>, <a href="#run_binary-outs">outs</a>, <a href="#run_binary-out_dirs">out_dirs</a>, <a href="#run_binary-mnemonic">mnemonic</a>, <a href="#run_binary-progress_message">progress_message</a>,
           <a href="#run_binary-execution_requirements">execution_requirements</a>, <a href="#run_binary-use_default_shell_env">use_default_shell_env</a>, <a href="#run_binary-stamp">stamp</a>, <a href="#run_binary-kwargs">**kwargs</a>)
</pre>

Runs a binary as a build action.

This rule does not require Bash (unlike `native.genrule`).

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="run_binary-name"></a>name |  The target name   |  none |
| <a id="run_binary-tool"></a>tool |  The tool to run in the action.<br><br>Must be the label of a *_binary rule of a rule that generates an executable file, or of a file that can be executed as a subprocess (e.g. an .exe or .bat file on Windows or a binary with executable permission on Linux). This label is available for `$(location)` expansion in `args` and `env`.   |  none |
| <a id="run_binary-srcs"></a>srcs |  Additional inputs of the action.<br><br>These labels are available for `$(location)` expansion in `args` and `env`.   |  `[]` |
| <a id="run_binary-args"></a>args |  Command line arguments of the binary.<br><br>Subject to `$(location)` and make variable expansions via [expand_location](./expand_make_vars#expand_locations) and [expand_make_vars](./expand_make_vars).   |  `[]` |
| <a id="run_binary-env"></a>env |  Environment variables of the action.<br><br>Subject to `$(location)` and make variable expansions via [expand_location](./expand_make_vars#expand_locations) and [expand_make_vars](./expand_make_vars).   |  `{}` |
| <a id="run_binary-outs"></a>outs |  Output files generated by the action.<br><br>These labels are available for `$(location)` expansion in `args` and `env`.<br><br>Output files cannot be nested within output directories in out_dirs.   |  `[]` |
| <a id="run_binary-out_dirs"></a>out_dirs |  Output directories generated by the action.<br><br>These labels are _not_ available for `$(location)` expansion in `args` and `env` since they are not pre-declared labels created via `attr.output_list()`. Output directories are declared instead by `ctx.actions.declare_directory`.<br><br>Output directories cannot be nested within other output directories in out_dirs.   |  `[]` |
| <a id="run_binary-mnemonic"></a>mnemonic |  A one-word description of the action, for example, CppCompile or GoLink.   |  `"RunBinary"` |
| <a id="run_binary-progress_message"></a>progress_message |  Progress message to show to the user during the build, for example, "Compiling foo.cc to create foo.o". The message may contain %{label}, %{input}, or %{output} patterns, which are substituted with label string, first input, or output's path, respectively. Prefer to use patterns instead of static strings, because the former are more efficient.   |  `None` |
| <a id="run_binary-execution_requirements"></a>execution_requirements |  Information for scheduling the action.<br><br>For example,<br><br><pre><code>execution_requirements = {&#10;    "no-cache": "1",&#10;},</code></pre><br><br>See https://docs.bazel.build/versions/main/be/common-definitions.html#common.tags for useful keys.   |  `None` |
| <a id="run_binary-use_default_shell_env"></a>use_default_shell_env |  Passed to the underlying ctx.actions.run.<br><br>May introduce non-determinism when True; use with care! See e.g. https://github.com/bazelbuild/bazel/issues/4912<br><br>Refer to https://bazel.build/rules/lib/builtins/actions#run for more details.   |  `False` |
| <a id="run_binary-stamp"></a>stamp |  Whether to include build status files as inputs to the tool. Possible values:<br><br>- `stamp = 0` (default): Never include build status files as inputs to the tool.     This gives good build result caching.     Most tools don't use the status files, so including them in `--stamp` builds makes those     builds have many needless cache misses.     (Note: this default is different from most rules with an integer-typed `stamp` attribute.) - `stamp = 1`: Always include build status files as inputs to the tool, even in     [--nostamp](https://docs.bazel.build/versions/main/user-manual.html#flag--stamp) builds.     This setting should be avoided, since it is non-deterministic.     It potentially causes remote cache misses for the target and     any downstream actions that depend on the result. - `stamp = -1`: Inclusion of build status files as inputs is controlled by the     [--[no]stamp](https://docs.bazel.build/versions/main/user-manual.html#flag--stamp) flag.     Stamped targets are not rebuilt unless their dependencies change.<br><br>When stamping is enabled, an additional two environment variables will be set for the action:     - `BAZEL_STABLE_STATUS_FILE`     - `BAZEL_VOLATILE_STATUS_FILE`<br><br>These files can be read and parsed by the action, for example to pass some values to a linker.   |  `0` |
| <a id="run_binary-kwargs"></a>kwargs |  Additional arguments   |  none |


# stamping.md


# Version Stamping

Bazel is generally only a build tool, and is unaware of your version control system.
However, when publishing releases, you may want to embed version information in the resulting distribution.
Bazel supports this with the concept of a "Workspace status" which is evaluated before each build.
See [the Bazel workspace status docs](https://docs.bazel.build/versions/master/user-manual.html#workspace_status)

To stamp a build, you pass the `--stamp` argument to Bazel.

> Note: https://github.com/bazelbuild/bazel/issues/14341 proposes that Bazel enforce this by
> only giving constant values to rule implementations when stamping isn't enabled.

Stamping is typically performed on a later action in the graph, like on a linking or packaging rule (`pkg_*`).
This means that a changed status variable only causes that action, not re-compilation and thus does not cause cascading re-builds.

Bazel provides a couple of statuses by default, such as `BUILD_EMBED_LABEL` which is the value of the `--embed_label`
argument, as well as `BUILD_HOST`, `BUILD_TIMESTAMP`, and `BUILD_USER`.
You can supply more with the workspace status script, see below.

Some rules accept an attribute that uses the status variables.
They will usually say something like "subject to stamp variable replacements".

## Stamping with a Workspace status script

To define additional statuses, pass the `--workspace_status_command` flag to `bazel`.
This slows down every build, so you should avoid passing this flag unless you need to stamp this build.
The value of this flag is a path to a script that prints space-separated key/value pairs, one per line, such as

```bash
#!/usr/bin/env bash
echo STABLE_GIT_COMMIT $(git rev-parse HEAD)
```
> For a more full-featured script, take a look at this [example in Angular]

Make sure you set the executable bit, eg. `chmod +x tools/bazel_stamp_vars.sh`.

> **NOTE** keys that start with `STABLE_` will cause a re-build when they change.
> Other keys will NOT cause a re-build, so stale values can appear in your app.
> Non-stable (volatile) keys should typically be things like timestamps that always vary between builds.

You might like to encode your setup using an entry in `.bazelrc` such as:

```sh
# This tells Bazel how to interact with the version control system
# Enable this with --config=release
build:release --stamp --workspace_status_command=./tools/bazel_stamp_vars.sh
```

[example in Angular]: https://github.com/angular/angular/blob/df274b478e6597cb1a2f31bb9f599281065aa250/dev-infra/release/env-stamp.ts

## Writing a custom rule which reads stamp variables

First, load the helpers:

```starlark
load("@aspect_bazel_lib//lib:stamping.bzl", "STAMP_ATTRS", "maybe_stamp")
```

In your rule implementation, call the `maybe_stamp` function.
If it returns `None` then this build doesn't have stamping enabled.
Otherwise you can use the returned struct to access two files.

1. The `stable_status` file contains the keys which were prefixed with `STABLE_`, see above.
2. The `volatile_status` file contains the rest of the keys.

```starlark
def _rule_impl(ctx):
    args = ctx.actions.args()
    inputs = []
    stamp = maybe_stamp(ctx)
    if stamp:
        args.add("--volatile_status_file", stamp.volatile_status_file.path)
        args.add("--stable_status_file", stamp.stable_status_file.path)
        inputs.extend([stamp.volatile_status_file, stamp.stable_status_file])

    # ... call actions which parse the stamp files and do something with the values ...
```

Finally, in the declaration of the rule, include the `STAMP_ATTRS` to declare attributes
which are read by that `maybe_stamp` function above.

```starlark
my_stamp_aware_rule = rule(
    attrs = dict({
        # ... my attributes ...
    }, **STAMP_ATTRS),
)
```

<a id="maybe_stamp"></a>

## maybe_stamp

<pre>
load("@aspect_bazel_lib//lib:stamping.bzl", "maybe_stamp")

maybe_stamp(<a href="#maybe_stamp-ctx">ctx</a>)
</pre>

Provide the bazel-out/stable_status.txt and bazel-out/volatile_status.txt files.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="maybe_stamp-ctx"></a>ctx |  The rule context   |  none |

**RETURNS**

If stamping is not enabled for this rule under the current build, returns None.
  Otherwise, returns a struct containing (volatile_status_file, stable_status_file) keys


# copy_to_directory.md


Copy files and directories to an output directory.

<a id="copy_to_directory"></a>

## copy_to_directory

<pre>
load("@aspect_bazel_lib//lib:copy_to_directory.bzl", "copy_to_directory")

copy_to_directory(<a href="#copy_to_directory-name">name</a>, <a href="#copy_to_directory-srcs">srcs</a>, <a href="#copy_to_directory-out">out</a>, <a href="#copy_to_directory-add_directory_to_runfiles">add_directory_to_runfiles</a>, <a href="#copy_to_directory-allow_overwrites">allow_overwrites</a>,
                  <a href="#copy_to_directory-exclude_srcs_packages">exclude_srcs_packages</a>, <a href="#copy_to_directory-exclude_srcs_patterns">exclude_srcs_patterns</a>, <a href="#copy_to_directory-hardlink">hardlink</a>,
                  <a href="#copy_to_directory-include_external_repositories">include_external_repositories</a>, <a href="#copy_to_directory-include_srcs_packages">include_srcs_packages</a>, <a href="#copy_to_directory-include_srcs_patterns">include_srcs_patterns</a>,
                  <a href="#copy_to_directory-preserve_mtime">preserve_mtime</a>, <a href="#copy_to_directory-replace_prefixes">replace_prefixes</a>, <a href="#copy_to_directory-root_paths">root_paths</a>, <a href="#copy_to_directory-verbose">verbose</a>)
</pre>

Copies files and directories to an output directory.

Files and directories can be arranged as needed in the output directory using
the `root_paths`, `include_srcs_patterns`, `exclude_srcs_patterns` and `replace_prefixes` attributes.

Filters and transformations are applied in the following order:

1. `include_external_repositories`

2. `include_srcs_packages`

3. `exclude_srcs_packages`

4. `root_paths`

5. `include_srcs_patterns`

6. `exclude_srcs_patterns`

7. `replace_prefixes`

For more information each filters / transformations applied, see
the documentation for the specific filter / transformation attribute.

Glob patterns are supported. Standard wildcards (globbing patterns) plus the `**` doublestar (aka. super-asterisk)
are supported with the underlying globbing library, https://github.com/bmatcuk/doublestar. This is the same
globbing library used by [gazelle](https://github.com/bazelbuild/bazel-gazelle). See https://github.com/bmatcuk/doublestar#patterns
for more information on supported globbing patterns.

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="copy_to_directory-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="copy_to_directory-srcs"></a>srcs |  Files and/or directories or targets that provide `DirectoryPathInfo` to copy into the output directory.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="copy_to_directory-out"></a>out |  Path of the output directory, relative to this package.<br><br>If not set, the name of the target is used.   | String | optional |  `""`  |
| <a id="copy_to_directory-add_directory_to_runfiles"></a>add_directory_to_runfiles |  Whether to add the outputted directory to the target's runfiles.   | Boolean | optional |  `True`  |
| <a id="copy_to_directory-allow_overwrites"></a>allow_overwrites |  If True, allow files to be overwritten if the same output file is copied to twice.<br><br>The order of srcs matters as the last copy of a particular file will win when overwriting. Performance of copy_to_directory will be slightly degraded when allow_overwrites is True since copies cannot be parallelized out as they are calculated. Instead all copy paths must be calculated before any copies can be started.   | Boolean | optional |  `False`  |
| <a id="copy_to_directory-exclude_srcs_packages"></a>exclude_srcs_packages |  List of Bazel packages (with glob support) to exclude from output directory.<br><br>Files in srcs are not copied to the output directory if the Bazel package of the file matches one of the patterns specified.<br><br>Forward slashes (`/`) should be used as path separators. A first character of `"."` will be replaced by the target's package path.<br><br>Files that have do not have matching Bazel packages are subject to subsequent filters and transformations to determine if they are copied and what their path in the output directory will be.<br><br>Globs are supported (see rule docstring above).   | List of strings | optional |  `[]`  |
| <a id="copy_to_directory-exclude_srcs_patterns"></a>exclude_srcs_patterns |  List of paths (with glob support) to exclude from output directory.<br><br>Files in srcs are not copied to the output directory if their output directory path, after applying `root_paths`, matches one of the patterns specified.<br><br>Forward slashes (`/`) should be used as path separators.<br><br>Files that do not have matching output directory paths are subject to subsequent filters and transformations to determine if they are copied and what their path in the output directory will be.<br><br>Globs are supported (see rule docstring above).   | List of strings | optional |  `[]`  |
| <a id="copy_to_directory-hardlink"></a>hardlink |  Controls when to use hardlinks to files instead of making copies.<br><br>Creating hardlinks is much faster than making copies of files with the caveat that hardlinks share file permissions with their source.<br><br>Since Bazel removes write permissions on files in the output tree after an action completes, hardlinks to source files are not recommended since write permissions will be inadvertently removed from sources files.<br><br>- `auto`: hardlinks are used for generated files already in the output tree - `off`: all files are copied - `on`: hardlinks are used for all files (not recommended)   | String | optional |  `"auto"`  |
| <a id="copy_to_directory-include_external_repositories"></a>include_external_repositories |  List of external repository names (with glob support) to include in the output directory.<br><br>Files from external repositories are only copied into the output directory if the external repository they come from matches one of the external repository patterns specified or if they are in the same external repository as this target.<br><br>When copied from an external repository, the file path in the output directory defaults to the file's path within the external repository. The external repository name is _not_ included in that path.<br><br>For example, the following copies `@external_repo//path/to:file` to `path/to/file` within the output directory.<br><br><pre><code>copy_to_directory(&#10;    name = "dir",&#10;    include_external_repositories = ["external_*"],&#10;    srcs = ["@external_repo//path/to:file"],&#10;)</code></pre><br><br>Files that come from matching external are subject to subsequent filters and transformations to determine if they are copied and what their path in the output directory will be. The external repository name of the file from an external repository is not included in the output directory path and is considered in subsequent filters and transformations.<br><br>Globs are supported (see rule docstring above).   | List of strings | optional |  `[]`  |
| <a id="copy_to_directory-include_srcs_packages"></a>include_srcs_packages |  List of Bazel packages (with glob support) to include in output directory.<br><br>Files in srcs are only copied to the output directory if the Bazel package of the file matches one of the patterns specified.<br><br>Forward slashes (`/`) should be used as path separators. A first character of `"."` will be replaced by the target's package path.<br><br>Defaults to `["**"]` which includes sources from all packages.<br><br>Files that have matching Bazel packages are subject to subsequent filters and transformations to determine if they are copied and what their path in the output directory will be.<br><br>Globs are supported (see rule docstring above).   | List of strings | optional |  `["**"]`  |
| <a id="copy_to_directory-include_srcs_patterns"></a>include_srcs_patterns |  List of paths (with glob support) to include in output directory.<br><br>Files in srcs are only copied to the output directory if their output directory path, after applying `root_paths`, matches one of the patterns specified.<br><br>Forward slashes (`/`) should be used as path separators.<br><br>Defaults to `["**"]` which includes all sources.<br><br>Files that have matching output directory paths are subject to subsequent filters and transformations to determine if they are copied and what their path in the output directory will be.<br><br>Globs are supported (see rule docstring above).   | List of strings | optional |  `["**"]`  |
| <a id="copy_to_directory-preserve_mtime"></a>preserve_mtime |  If True, the last modified time of copied files is preserved. See the [caveats on copy_directory](/docs/copy_directory.md#preserving-modification-times) about interactions with remote execution and caching.   | Boolean | optional |  `False`  |
| <a id="copy_to_directory-replace_prefixes"></a>replace_prefixes |  Map of paths prefixes (with glob support) to replace in the output directory path when copying files.<br><br>If the output directory path for a file starts with or fully matches a a key in the dict then the matching portion of the output directory path is replaced with the dict value for that key. The final path segment matched can be a partial match of that segment and only the matching portion will be replaced. If there are multiple keys that match, the longest match wins.<br><br>Forward slashes (`/`) should be used as path separators.<br><br>Replace prefix transformation are the final step in the list of filters and transformations. The final output path of a file being copied into the output directory is determined at this step.<br><br>Globs are supported (see rule docstring above).   | <a href="https://bazel.build/rules/lib/dict">Dictionary: String -> String</a> | optional |  `{}`  |
| <a id="copy_to_directory-root_paths"></a>root_paths |  List of paths (with glob support) that are roots in the output directory.<br><br>If any parent directory of a file being copied matches one of the root paths patterns specified, the output directory path will be the path relative to the root path instead of the path relative to the file's workspace. If there are multiple root paths that match, the longest match wins.<br><br>Matching is done on the parent directory of the output file path so a trailing '**' glob patterm will match only up to the last path segment of the dirname and will not include the basename. Only complete path segments are matched. Partial matches on the last segment of the root path are ignored.<br><br>Forward slashes (`/`) should be used as path separators.<br><br>A `"."` value expands to the target's package path (`ctx.label.package`).<br><br>Defaults to `["."]` which results in the output directory path of files in the target's package and and sub-packages are relative to the target's package and files outside of that retain their full workspace relative paths.<br><br>Globs are supported (see rule docstring above).   | List of strings | optional |  `["."]`  |
| <a id="copy_to_directory-verbose"></a>verbose |  If true, prints out verbose logs to stdout   | Boolean | optional |  `False`  |

<a id="copy_to_directory_bin_action"></a>

## copy_to_directory_bin_action

<pre>
load("@aspect_bazel_lib//lib:copy_to_directory.bzl", "copy_to_directory_bin_action")

copy_to_directory_bin_action(<a href="#copy_to_directory_bin_action-ctx">ctx</a>, <a href="#copy_to_directory_bin_action-name">name</a>, <a href="#copy_to_directory_bin_action-dst">dst</a>, <a href="#copy_to_directory_bin_action-copy_to_directory_bin">copy_to_directory_bin</a>, <a href="#copy_to_directory_bin_action-copy_to_directory_toolchain">copy_to_directory_toolchain</a>,
                             <a href="#copy_to_directory_bin_action-files">files</a>, <a href="#copy_to_directory_bin_action-targets">targets</a>, <a href="#copy_to_directory_bin_action-root_paths">root_paths</a>, <a href="#copy_to_directory_bin_action-include_external_repositories">include_external_repositories</a>,
                             <a href="#copy_to_directory_bin_action-include_srcs_packages">include_srcs_packages</a>, <a href="#copy_to_directory_bin_action-exclude_srcs_packages">exclude_srcs_packages</a>, <a href="#copy_to_directory_bin_action-include_srcs_patterns">include_srcs_patterns</a>,
                             <a href="#copy_to_directory_bin_action-exclude_srcs_patterns">exclude_srcs_patterns</a>, <a href="#copy_to_directory_bin_action-replace_prefixes">replace_prefixes</a>, <a href="#copy_to_directory_bin_action-allow_overwrites">allow_overwrites</a>, <a href="#copy_to_directory_bin_action-hardlink">hardlink</a>,
                             <a href="#copy_to_directory_bin_action-preserve_mtime">preserve_mtime</a>, <a href="#copy_to_directory_bin_action-verbose">verbose</a>)
</pre>

Factory function to copy files to a directory using a tool binary.

The tool binary will typically be the `@aspect_bazel_lib//tools/copy_to_directory` `go_binary`
either built from source or provided by a toolchain.

This helper is used by copy_to_directory. It is exposed as a public API so it can be used within
other rule implementations where additional_files can also be passed in.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="copy_to_directory_bin_action-ctx"></a>ctx |  The rule context.   |  none |
| <a id="copy_to_directory_bin_action-name"></a>name |  Name of target creating this action used for config file generation.   |  none |
| <a id="copy_to_directory_bin_action-dst"></a>dst |  The directory to copy to. Must be a TreeArtifact.   |  none |
| <a id="copy_to_directory_bin_action-copy_to_directory_bin"></a>copy_to_directory_bin |  Copy to directory tool binary.   |  none |
| <a id="copy_to_directory_bin_action-copy_to_directory_toolchain"></a>copy_to_directory_toolchain |  The toolchain type for Auto Exec Groups. The default is probably what you want.   |  `"@aspect_bazel_lib//lib:copy_to_directory_toolchain_type"` |
| <a id="copy_to_directory_bin_action-files"></a>files |  List of files to copy into the output directory.   |  `[]` |
| <a id="copy_to_directory_bin_action-targets"></a>targets |  List of targets that provide `DirectoryPathInfo` to copy into the output directory.   |  `[]` |
| <a id="copy_to_directory_bin_action-root_paths"></a>root_paths |  List of paths that are roots in the output directory.<br><br>See copy_to_directory rule documentation for more details.   |  `["."]` |
| <a id="copy_to_directory_bin_action-include_external_repositories"></a>include_external_repositories |  List of external repository names to include in the output directory.<br><br>See copy_to_directory rule documentation for more details.   |  `[]` |
| <a id="copy_to_directory_bin_action-include_srcs_packages"></a>include_srcs_packages |  List of Bazel packages to include in output directory.<br><br>See copy_to_directory rule documentation for more details.   |  `["**"]` |
| <a id="copy_to_directory_bin_action-exclude_srcs_packages"></a>exclude_srcs_packages |  List of Bazel packages (with glob support) to exclude from output directory.<br><br>See copy_to_directory rule documentation for more details.   |  `[]` |
| <a id="copy_to_directory_bin_action-include_srcs_patterns"></a>include_srcs_patterns |  List of paths (with glob support) to include in output directory.<br><br>See copy_to_directory rule documentation for more details.   |  `["**"]` |
| <a id="copy_to_directory_bin_action-exclude_srcs_patterns"></a>exclude_srcs_patterns |  List of paths (with glob support) to exclude from output directory.<br><br>See copy_to_directory rule documentation for more details.   |  `[]` |
| <a id="copy_to_directory_bin_action-replace_prefixes"></a>replace_prefixes |  Map of paths prefixes to replace in the output directory path when copying files.<br><br>See copy_to_directory rule documentation for more details.   |  `{}` |
| <a id="copy_to_directory_bin_action-allow_overwrites"></a>allow_overwrites |  If True, allow files to be overwritten if the same output file is copied to twice.<br><br>See copy_to_directory rule documentation for more details.   |  `False` |
| <a id="copy_to_directory_bin_action-hardlink"></a>hardlink |  Controls when to use hardlinks to files instead of making copies.<br><br>See copy_to_directory rule documentation for more details.   |  `"auto"` |
| <a id="copy_to_directory_bin_action-preserve_mtime"></a>preserve_mtime |  If true, preserve the modified time from the source.   |  `False` |
| <a id="copy_to_directory_bin_action-verbose"></a>verbose |  If true, prints out verbose logs to stdout   |  `False` |

<a id="copy_to_directory_lib.impl"></a>

## copy_to_directory_lib.impl

<pre>
load("@aspect_bazel_lib//lib:copy_to_directory.bzl", "copy_to_directory_lib")

copy_to_directory_lib.impl(<a href="#copy_to_directory_lib.impl-ctx">ctx</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="copy_to_directory_lib.impl-ctx"></a>ctx |  <p align="center"> - </p>   |  none |


# expand_make_vars.md


Public API for expanding variables

<a id="expand_locations"></a>

## expand_locations

<pre>
load("@aspect_bazel_lib//lib:expand_make_vars.bzl", "expand_locations")

expand_locations(<a href="#expand_locations-ctx">ctx</a>, <a href="#expand_locations-input">input</a>, <a href="#expand_locations-targets">targets</a>)
</pre>

Expand location templates.

Expands all `$(execpath ...)`, `$(rootpath ...)` and deprecated `$(location ...)` templates in the
given string by replacing with the expanded path. Expansion only works for labels that point to direct dependencies
of this rule or that are explicitly listed in the optional argument targets.

See https://docs.bazel.build/versions/main/be/make-variables.html#predefined_label_variables.

Use `$(rootpath)` and `$(rootpaths)` to expand labels to the runfiles path that a built binary can use
to find its dependencies. This path is of the format:
- `./file`
- `path/to/file`
- `../external_repo/path/to/file`

Use `$(execpath)` and `$(execpaths)` to expand labels to the execroot (where Bazel runs build actions).
This is of the format:
- `./file`
- `path/to/file`
- `external/external_repo/path/to/file`
- `<bin_dir>/path/to/file`
- `<bin_dir>/external/external_repo/path/to/file`

The deprecated `$(location)` and `$(locations)` expansions returns either the execpath or rootpath depending on the context.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="expand_locations-ctx"></a>ctx |  context   |  none |
| <a id="expand_locations-input"></a>input |  String to be expanded   |  none |
| <a id="expand_locations-targets"></a>targets |  List of targets for additional lookup information.   |  `[]` |

**RETURNS**

The expanded path or the original path

**DEPRECATED**

Use vanilla `ctx.expand_location(input, targets = targets)` instead

<a id="expand_variables"></a>

## expand_variables

<pre>
load("@aspect_bazel_lib//lib:expand_make_vars.bzl", "expand_variables")

expand_variables(<a href="#expand_variables-ctx">ctx</a>, <a href="#expand_variables-s">s</a>, <a href="#expand_variables-outs">outs</a>, <a href="#expand_variables-attribute_name">attribute_name</a>)
</pre>

Expand make variables and substitute like genrule does.

Bazel [pre-defined variables](https://bazel.build/reference/be/make-variables#predefined_variables)
are expanded however only `$@`, `$(@D)` and `$(RULEDIR)` of
[pre-defined genrule variables](https://bazel.build/reference/be/make-variables#predefined_genrule_variables)
are supported.

This function is the same as ctx.expand_make_variables with the additional
genrule-like substitutions of:

  - `$@`: The output file if it is a single file. Else triggers a build error.

  - `$(@D)`: The output directory.

    If there is only one file name in outs, this expands to the directory containing that file.

    If there is only one directory in outs, this expands to the single output directory.

    If there are multiple files, this instead expands to the package's root directory in the bin tree,
    even if all generated files belong to the same subdirectory!

  - `$(RULEDIR)`: The output directory of the rule, that is, the directory
    corresponding to the name of the package containing the rule under the bin tree.

  - `$(BUILD_FILE_PATH)`: ctx.build_file_path

  - `$(VERSION_FILE)`: ctx.version_file.path

  - `$(INFO_FILE)`: ctx.info_file.path

  - `$(TARGET)`: ctx.label

  - `$(WORKSPACE)`: ctx.workspace_name

See https://docs.bazel.build/versions/main/be/general.html#genrule.cmd and
https://docs.bazel.build/versions/main/be/make-variables.html#predefined_genrule_variables
for more information of how these special variables are expanded.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="expand_variables-ctx"></a>ctx |  starlark rule context   |  none |
| <a id="expand_variables-s"></a>s |  expression to expand   |  none |
| <a id="expand_variables-outs"></a>outs |  declared outputs of the rule, for expanding references to outputs   |  `[]` |
| <a id="expand_variables-attribute_name"></a>attribute_name |  name of the attribute containing the expression. Used for error reporting.   |  `"args"` |

**RETURNS**

`s` with the variables expanded


# glob_match.md


Public API

<a id="glob_match"></a>

## glob_match

<pre>
load("@aspect_bazel_lib//lib:glob_match.bzl", "glob_match")

glob_match(<a href="#glob_match-expr">expr</a>, <a href="#glob_match-path">path</a>, <a href="#glob_match-match_path_separator">match_path_separator</a>)
</pre>

Test if the passed path matches the glob expression.

`*` A single asterisk stands for zero or more arbitrary characters except for the the path separator `/` if `match_path_separator` is False

`?` The question mark stands for exactly one character except for the the path separator `/` if `match_path_separator` is False

`**` A double asterisk stands for an arbitrary sequence of 0 or more characters. It is only allowed when preceded by either the beginning of the string or a slash. Likewise it must be followed by a slash or the end of the pattern.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="glob_match-expr"></a>expr |  the glob expression   |  none |
| <a id="glob_match-path"></a>path |  the path against which to match the glob expression   |  none |
| <a id="glob_match-match_path_separator"></a>match_path_separator |  whether or not to match the path separator '/' when matching `*` and `?` expressions   |  `False` |

**RETURNS**

True if the path matches the glob expression

<a id="is_glob"></a>

## is_glob

<pre>
load("@aspect_bazel_lib//lib:glob_match.bzl", "is_glob")

is_glob(<a href="#is_glob-expr">expr</a>)
</pre>

Determine if the passed string is a global expression

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="is_glob-expr"></a>expr |  the potential glob expression   |  none |

**RETURNS**

True if the passed string is a global expression


# directory_path.md


Rule and corresponding provider that joins a label pointing to a TreeArtifact
with a path nested within that directory

<a id="directory_path"></a>

## directory_path

<pre>
load("@aspect_bazel_lib//lib:directory_path.bzl", "directory_path")

directory_path(<a href="#directory_path-name">name</a>, <a href="#directory_path-directory">directory</a>, <a href="#directory_path-path">path</a>)
</pre>

Provide DirectoryPathInfo to reference some path within a directory.

Otherwise there is no way to give a Bazel label for it.

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="directory_path-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="directory_path-directory"></a>directory |  a TreeArtifact (ctx.actions.declare_directory)   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |
| <a id="directory_path-path"></a>path |  path relative to the directory   | String | required |  |

<a id="DirectoryPathInfo"></a>

## DirectoryPathInfo

<pre>
load("@aspect_bazel_lib//lib:directory_path.bzl", "DirectoryPathInfo")

DirectoryPathInfo(<a href="#DirectoryPathInfo-directory">directory</a>, <a href="#DirectoryPathInfo-path">path</a>)
</pre>

Joins a label pointing to a TreeArtifact with a path nested within that directory.

**FIELDS**

| Name  | Description |
| :------------- | :------------- |
| <a id="DirectoryPathInfo-directory"></a>directory |  a TreeArtifact (ctx.actions.declare_directory)    |
| <a id="DirectoryPathInfo-path"></a>path |  path relative to the directory    |

<a id="make_directory_path"></a>

## make_directory_path

<pre>
load("@aspect_bazel_lib//lib:directory_path.bzl", "make_directory_path")

make_directory_path(<a href="#make_directory_path-name">name</a>, <a href="#make_directory_path-directory">directory</a>, <a href="#make_directory_path-path">path</a>, <a href="#make_directory_path-kwargs">**kwargs</a>)
</pre>

Helper function to generate a directory_path target and return its label.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="make_directory_path-name"></a>name |  unique name for the generated `directory_path` target   |  none |
| <a id="make_directory_path-directory"></a>directory |  `directory` attribute passed to generated `directory_path` target   |  none |
| <a id="make_directory_path-path"></a>path |  `path` attribute passed to generated `directory_path` target   |  none |
| <a id="make_directory_path-kwargs"></a>kwargs |  parameters to pass to generated `output_files` target   |  none |

**RETURNS**

The label `name`

<a id="make_directory_paths"></a>

## make_directory_paths

<pre>
load("@aspect_bazel_lib//lib:directory_path.bzl", "make_directory_paths")

make_directory_paths(<a href="#make_directory_paths-name">name</a>, <a href="#make_directory_paths-dict">dict</a>, <a href="#make_directory_paths-kwargs">**kwargs</a>)
</pre>

Helper function to convert a dict of directory to path mappings to directory_path targets and labels.

For example,

```
make_directory_paths("my_name", {
    "//directory/artifact:target_1": "file/path",
    "//directory/artifact:target_2": ["file/path1", "file/path2"],
})
```

generates the targets,

```
directory_path(
    name = "my_name_0",
    directory = "//directory/artifact:target_1",
    path = "file/path"
)

directory_path(
    name = "my_name_1",
    directory = "//directory/artifact:target_2",
    path = "file/path1"
)

directory_path(
    name = "my_name_2",
    directory = "//directory/artifact:target_2",
    path = "file/path2"
)
```

and the list of targets is returned,

```
[
    "my_name_0",
    "my_name_1",
    "my_name_2",
]
```

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="make_directory_paths-name"></a>name |  The target name to use for the generated targets & labels.<br><br>The names are generated as zero-indexed `name + "_" + i`   |  none |
| <a id="make_directory_paths-dict"></a>dict |  The dictionary of directory keys to path or path list values.   |  none |
| <a id="make_directory_paths-kwargs"></a>kwargs |  additional parameters to pass to each generated target   |  none |

**RETURNS**

The label of the generated `directory_path` targets named `name + "_" + i`


# output_files.md


A rule that provides file(s) specific via DefaultInfo from a given target's DefaultInfo or OutputGroupInfo.

See also [select_file](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/select_file_doc.md) from bazel-skylib.

<a id="output_files"></a>

## output_files

<pre>
load("@aspect_bazel_lib//lib:output_files.bzl", "output_files")

output_files(<a href="#output_files-name">name</a>, <a href="#output_files-output_group">output_group</a>, <a href="#output_files-paths">paths</a>, <a href="#output_files-target">target</a>)
</pre>

A rule that provides file(s) specific via DefaultInfo from a given target's DefaultInfo or OutputGroupInfo

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="output_files-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="output_files-output_group"></a>output_group |  if set, we look in the specified output group for paths instead of DefaultInfo   | String | optional |  `""`  |
| <a id="output_files-paths"></a>paths |  the paths of the file(s), relative to their roots, to provide via DefaultInfo from the given target's DefaultInfo or OutputGroupInfo   | List of strings | required |  |
| <a id="output_files-target"></a>target |  the target to look in for requested paths in its' DefaultInfo or OutputGroupInfo   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |

<a id="make_output_files"></a>

## make_output_files

<pre>
load("@aspect_bazel_lib//lib:output_files.bzl", "make_output_files")

make_output_files(<a href="#make_output_files-name">name</a>, <a href="#make_output_files-target">target</a>, <a href="#make_output_files-paths">paths</a>, <a href="#make_output_files-kwargs">**kwargs</a>)
</pre>

Helper function to generate a output_files target and return its label.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="make_output_files-name"></a>name |  unique name for the generated `output_files` target   |  none |
| <a id="make_output_files-target"></a>target |  `target` attribute passed to generated `output_files` target   |  none |
| <a id="make_output_files-paths"></a>paths |  `paths` attribute passed to generated `output_files` target   |  none |
| <a id="make_output_files-kwargs"></a>kwargs |  parameters to pass to generated `output_files` target   |  none |

**RETURNS**

The label `name`


# testing.md


Helpers for making test assertions

<a id="assert_archive_contains"></a>

## assert_archive_contains

<pre>
load("@aspect_bazel_lib//lib:testing.bzl", "assert_archive_contains")

assert_archive_contains(<a href="#assert_archive_contains-name">name</a>, <a href="#assert_archive_contains-archive">archive</a>, <a href="#assert_archive_contains-expected">expected</a>, <a href="#assert_archive_contains-type">type</a>, <a href="#assert_archive_contains-kwargs">**kwargs</a>)
</pre>

Assert that an archive file contains at least the given file entries.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="assert_archive_contains-name"></a>name |  name of the resulting sh_test target   |  none |
| <a id="assert_archive_contains-archive"></a>archive |  Label of the the .tar or .zip file   |  none |
| <a id="assert_archive_contains-expected"></a>expected |  a (partial) file listing, either as a Label of a file containing it, or a list of strings   |  none |
| <a id="assert_archive_contains-type"></a>type |  "tar" or "zip". If None, a type will be inferred from the filename.   |  `None` |
| <a id="assert_archive_contains-kwargs"></a>kwargs |  additional named arguments for the resulting sh_test   |  none |

<a id="assert_contains"></a>

## assert_contains

<pre>
load("@aspect_bazel_lib//lib:testing.bzl", "assert_contains")

assert_contains(<a href="#assert_contains-name">name</a>, <a href="#assert_contains-actual">actual</a>, <a href="#assert_contains-expected">expected</a>, <a href="#assert_contains-size">size</a>, <a href="#assert_contains-kwargs">**kwargs</a>)
</pre>

Generates a test target which fails if the file doesn't contain the string.

Depends on bash, as it creates an sh_test target.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="assert_contains-name"></a>name |  target to create   |  none |
| <a id="assert_contains-actual"></a>actual |  Label of a file   |  none |
| <a id="assert_contains-expected"></a>expected |  a string which should appear in the file   |  none |
| <a id="assert_contains-size"></a>size |  standard attribute for tests   |  `"small"` |
| <a id="assert_contains-kwargs"></a>kwargs |  additional named arguments for the resulting sh_test   |  none |

<a id="assert_directory_contains"></a>

## assert_directory_contains

<pre>
load("@aspect_bazel_lib//lib:testing.bzl", "assert_directory_contains")

assert_directory_contains(<a href="#assert_directory_contains-name">name</a>, <a href="#assert_directory_contains-directory">directory</a>, <a href="#assert_directory_contains-expected">expected</a>, <a href="#assert_directory_contains-kwargs">**kwargs</a>)
</pre>

Assert that a directory contains at least the given file entries.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="assert_directory_contains-name"></a>name |  name of the resulting sh_test target   |  none |
| <a id="assert_directory_contains-directory"></a>directory |  Label of the directory artifact   |  none |
| <a id="assert_directory_contains-expected"></a>expected |  a (partial) file listing, either as a Label of a file containing it, or a list of strings   |  none |
| <a id="assert_directory_contains-kwargs"></a>kwargs |  additional named arguments for the resulting sh_test   |  none |

<a id="assert_json_matches"></a>

## assert_json_matches

<pre>
load("@aspect_bazel_lib//lib:testing.bzl", "assert_json_matches")

assert_json_matches(<a href="#assert_json_matches-name">name</a>, <a href="#assert_json_matches-file1">file1</a>, <a href="#assert_json_matches-file2">file2</a>, <a href="#assert_json_matches-filter1">filter1</a>, <a href="#assert_json_matches-filter2">filter2</a>, <a href="#assert_json_matches-kwargs">**kwargs</a>)
</pre>

Assert that the given json files have the same semantic content.

Uses jq to filter each file. The default value of `"."` as the filter
means to compare the whole file.

See the [jq rule](./jq.md#jq) for more about the filter expressions as well as
setup notes for the `jq` toolchain.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="assert_json_matches-name"></a>name |  name of resulting diff_test target   |  none |
| <a id="assert_json_matches-file1"></a>file1 |  a json file   |  none |
| <a id="assert_json_matches-file2"></a>file2 |  another json file   |  none |
| <a id="assert_json_matches-filter1"></a>filter1 |  a jq filter to apply to file1   |  `"."` |
| <a id="assert_json_matches-filter2"></a>filter2 |  a jq filter to apply to file2   |  `"."` |
| <a id="assert_json_matches-kwargs"></a>kwargs |  additional named arguments for the resulting diff_test   |  none |

<a id="assert_outputs"></a>

## assert_outputs

<pre>
load("@aspect_bazel_lib//lib:testing.bzl", "assert_outputs")

assert_outputs(<a href="#assert_outputs-name">name</a>, <a href="#assert_outputs-actual">actual</a>, <a href="#assert_outputs-expected">expected</a>, <a href="#assert_outputs-kwargs">**kwargs</a>)
</pre>

Assert that the default outputs of a target are the expected ones.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="assert_outputs-name"></a>name |  name of the resulting diff_test   |  none |
| <a id="assert_outputs-actual"></a>actual |  string of the label to check the outputs   |  none |
| <a id="assert_outputs-expected"></a>expected |  a list of rootpaths of expected outputs, as they would appear in a runfiles manifest   |  none |
| <a id="assert_outputs-kwargs"></a>kwargs |  additional named arguments for the resulting diff_test   |  none |


# expand_template.md


Public API for expand template

<a id="expand_template_rule"></a>

## expand_template_rule

<pre>
load("@aspect_bazel_lib//lib:expand_template.bzl", "expand_template_rule")

expand_template_rule(<a href="#expand_template_rule-name">name</a>, <a href="#expand_template_rule-data">data</a>, <a href="#expand_template_rule-out">out</a>, <a href="#expand_template_rule-is_executable">is_executable</a>, <a href="#expand_template_rule-stamp">stamp</a>, <a href="#expand_template_rule-stamp_substitutions">stamp_substitutions</a>, <a href="#expand_template_rule-substitutions">substitutions</a>,
                     <a href="#expand_template_rule-template">template</a>)
</pre>

Template expansion

This performs a simple search over the template file for the keys in substitutions,
and replaces them with the corresponding values.

Values may also use location templates as documented in
[expand_locations](https://github.com/bazel-contrib/bazel-lib/blob/main/docs/expand_make_vars.md#expand_locations)
as well as [configuration variables](https://docs.bazel.build/versions/main/skylark/lib/ctx.html#var)
such as `$(BINDIR)`, `$(TARGET_CPU)`, and `$(COMPILATION_MODE)` as documented in
[expand_variables](https://github.com/bazel-contrib/bazel-lib/blob/main/docs/expand_make_vars.md#expand_variables).

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="expand_template_rule-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="expand_template_rule-data"></a>data |  List of targets for additional lookup information.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="expand_template_rule-out"></a>out |  Where to write the expanded file.<br><br>If the `template` is a source file, then `out` defaults to be named the same as the template file and outputted to the same workspace-relative path. In this case there will be no pre-declared label for the output file. It can be referenced by the target label instead. This pattern is similar to `copy_to_bin` but with substitutions on the copy.<br><br>Otherwise, `out` defaults to `[name].txt`.   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="expand_template_rule-is_executable"></a>is_executable |  Whether to mark the output file as executable.   | Boolean | optional |  `False`  |
| <a id="expand_template_rule-stamp"></a>stamp |  Whether to encode build information into the output. Possible values:<br><br>- `stamp = 1`: Always stamp the build information into the output, even in     [--nostamp](https://docs.bazel.build/versions/main/user-manual.html#flag--stamp) builds.     This setting should be avoided, since it is non-deterministic.     It potentially causes remote cache misses for the target and     any downstream actions that depend on the result. - `stamp = 0`: Never stamp, instead replace build information by constant values.     This gives good build result caching. - `stamp = -1`: Embedding of build information is controlled by the     [--[no]stamp](https://docs.bazel.build/versions/main/user-manual.html#flag--stamp) flag.     Stamped targets are not rebuilt unless their dependencies change.   | Integer | optional |  `-1`  |
| <a id="expand_template_rule-stamp_substitutions"></a>stamp_substitutions |  Mapping of strings to substitutions.<br><br>There are overlaid on top of substitutions when stamping is enabled for the target.<br><br>Substitutions can contain $(execpath :target) and $(rootpath :target) expansions, $(MAKEVAR) expansions and {{STAMP_VAR}} expansions when stamping is enabled for the target.   | <a href="https://bazel.build/rules/lib/dict">Dictionary: String -> String</a> | optional |  `{}`  |
| <a id="expand_template_rule-substitutions"></a>substitutions |  Mapping of strings to substitutions.<br><br>Substitutions can contain $(execpath :target) and $(rootpath :target) expansions, $(MAKEVAR) expansions and {{STAMP_VAR}} expansions when stamping is enabled for the target.   | <a href="https://bazel.build/rules/lib/dict">Dictionary: String -> String</a> | optional |  `{}`  |
| <a id="expand_template_rule-template"></a>template |  The template file to expand.   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |

<a id="expand_template"></a>

## expand_template

<pre>
load("@aspect_bazel_lib//lib:expand_template.bzl", "expand_template")

expand_template(<a href="#expand_template-name">name</a>, <a href="#expand_template-template">template</a>, <a href="#expand_template-kwargs">**kwargs</a>)
</pre>

Wrapper macro for `expand_template_rule`.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="expand_template-name"></a>name |  name of resulting rule   |  none |
| <a id="expand_template-template"></a>template |  the label of a template file, or a list of strings which are lines representing the content of the template.   |  none |
| <a id="expand_template-kwargs"></a>kwargs |  other named parameters to `expand_template_rule`.   |  none |


# copy_to_bin.md


A rule that copies source files to the output tree.

This rule uses a Bash command (diff) on Linux/macOS/non-Windows, and a cmd.exe
command (fc.exe) on Windows (no Bash is required).

Originally authored in rules_nodejs
https://github.com/bazel-contrib/rules_nodejs/blob/8b5d27400db51e7027fe95ae413eeabea4856f8e/internal/common/copy_to_bin.bzl

<a id="copy_file_to_bin_action"></a>

## copy_file_to_bin_action

<pre>
load("@aspect_bazel_lib//lib:copy_to_bin.bzl", "copy_file_to_bin_action")

copy_file_to_bin_action(<a href="#copy_file_to_bin_action-ctx">ctx</a>, <a href="#copy_file_to_bin_action-file">file</a>)
</pre>

Factory function that creates an action to copy a file to the output tree.

File are copied to the same workspace-relative path. The resulting files is
returned.

If the file passed in is already in the output tree is then it is returned
without a copy action.

To use `copy_file_to_bin_action` in your own rules, you need to include the toolchains it uses
in your rule definition. For example:

```starlark
load("@aspect_bazel_lib//lib:copy_to_bin.bzl", "COPY_FILE_TO_BIN_TOOLCHAINS")

my_rule = rule(
    ...,
    toolchains = COPY_FILE_TO_BIN_TOOLCHAINS,
)
```

Additionally, you must ensure that the coreutils toolchain is has been registered in your
WORKSPACE if you are not using bzlmod:

```starlark
load("@aspect_bazel_lib//lib:repositories.bzl", "register_coreutils_toolchains")

register_coreutils_toolchains()
```

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="copy_file_to_bin_action-ctx"></a>ctx |  The rule context.   |  none |
| <a id="copy_file_to_bin_action-file"></a>file |  The file to copy.   |  none |

**RETURNS**

A File in the output tree.

<a id="copy_files_to_bin_actions"></a>

## copy_files_to_bin_actions

<pre>
load("@aspect_bazel_lib//lib:copy_to_bin.bzl", "copy_files_to_bin_actions")

copy_files_to_bin_actions(<a href="#copy_files_to_bin_actions-ctx">ctx</a>, <a href="#copy_files_to_bin_actions-files">files</a>)
</pre>

Factory function that creates actions to copy files to the output tree.

Files are copied to the same workspace-relative path. The resulting list of
files is returned.

If a file passed in is already in the output tree is then it is added
directly to the result without a copy action.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="copy_files_to_bin_actions-ctx"></a>ctx |  The rule context.   |  none |
| <a id="copy_files_to_bin_actions-files"></a>files |  List of File objects.   |  none |

**RETURNS**

List of File objects in the output tree.

<a id="copy_to_bin"></a>

## copy_to_bin

<pre>
load("@aspect_bazel_lib//lib:copy_to_bin.bzl", "copy_to_bin")

copy_to_bin(<a href="#copy_to_bin-name">name</a>, <a href="#copy_to_bin-srcs">srcs</a>, <a href="#copy_to_bin-kwargs">**kwargs</a>)
</pre>

Copies a source file to output tree at the same workspace-relative path.

e.g. `<execroot>/path/to/file -> <execroot>/bazel-out/<platform>/bin/path/to/file`

If a file passed in is already in the output tree is then it is added directly to the
DefaultInfo provided by the rule without a copy.

This is useful to populate the output folder with all files needed at runtime, even
those which aren't outputs of a Bazel rule.

This way you can run a binary in the output folder (execroot or runfiles_root)
without that program needing to rely on a runfiles helper library or be aware that
files are divided between the source tree and the output tree.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="copy_to_bin-name"></a>name |  Name of the rule.   |  none |
| <a id="copy_to_bin-srcs"></a>srcs |  A list of labels. File(s) to copy.   |  none |
| <a id="copy_to_bin-kwargs"></a>kwargs |  further keyword arguments, e.g. `visibility`   |  none |


# resource_sets.md


Utilities for rules that expose resource_set on ctx.actions.run[_shell]

Workaround for https://github.com/bazelbuild/bazel/issues/15187

Note, this workaround only provides some fixed values for either CPU or Memory.

Rule authors who are ALSO the BUILD author might know better, and can
write custom resource_set functions for use within their own repository.
This seems to be the use case that Google engineers imagined.

<a id="resource_set"></a>

## resource_set

<pre>
load("@aspect_bazel_lib//lib:resource_sets.bzl", "resource_set")

resource_set(<a href="#resource_set-attr">attr</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="resource_set-attr"></a>attr |  <p align="center"> - </p>   |  none |


# base64.md


Utility functions for encoding and decoding strings with base64.

See https://en.wikipedia.org/wiki/Base64.

<a id="base64.decode"></a>

## base64.decode

<pre>
load("@aspect_bazel_lib//lib:base64.bzl", "base64")

base64.decode(<a href="#base64.decode-data">data</a>)
</pre>

Decode a base64 encoded string.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="base64.decode-data"></a>data |  base64-encoded string   |  none |

**RETURNS**

A string containing the decoded data

<a id="base64.encode"></a>

## base64.encode

<pre>
load("@aspect_bazel_lib//lib:base64.bzl", "base64")

base64.encode(<a href="#base64.encode-data">data</a>)
</pre>

Base64 encode a string.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="base64.encode-data"></a>data |  string to encode   |  none |

**RETURNS**

The base64-encoded string


# lists.md


Functions for lists

<a id="every"></a>

## every

<pre>
load("@aspect_bazel_lib//lib:lists.bzl", "every")

every(<a href="#every-f">f</a>, <a href="#every-arr">arr</a>)
</pre>

Check if every item of `arr` passes function `f`.

Example:
  `every(lambda i: i.endswith(".js"), ["app.js", "lib.js"]) // True`

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="every-f"></a>f |  Function to execute on every item   |  none |
| <a id="every-arr"></a>arr |  List to iterate over   |  none |

**RETURNS**

True or False

<a id="filter"></a>

## filter

<pre>
load("@aspect_bazel_lib//lib:lists.bzl", "filter")

filter(<a href="#filter-f">f</a>, <a href="#filter-arr">arr</a>)
</pre>

Filter a list `arr` by applying a function `f` to each item.

Example:
  `filter(lambda i: i.endswith(".js"), ["app.ts", "app.js", "lib.ts", "lib.js"]) // ["app.js", "lib.js"]`

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="filter-f"></a>f |  Function to execute on every item   |  none |
| <a id="filter-arr"></a>arr |  List to iterate over   |  none |

**RETURNS**

A new list containing items that passed the filter function.

<a id="find"></a>

## find

<pre>
load("@aspect_bazel_lib//lib:lists.bzl", "find")

find(<a href="#find-f">f</a>, <a href="#find-arr">arr</a>)
</pre>

Find a particular item from list `arr` by a given function `f`.

Unlike `pick`, the `find` method returns a tuple of the index and the value of first item passing by `f`.
Furthermore `find` does not fail if no item passes `f`.
In this case `(-1, None)` is returned.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="find-f"></a>f |  Function to execute on every item   |  none |
| <a id="find-arr"></a>arr |  List to iterate over   |  none |

**RETURNS**

Tuple (index, item)

<a id="map"></a>

## map

<pre>
load("@aspect_bazel_lib//lib:lists.bzl", "map")

map(<a href="#map-f">f</a>, <a href="#map-arr">arr</a>)
</pre>

Apply a function `f` with each item of `arr` and return a new list.

Example:
  `map(lambda i: i*2, [1, 2, 3]) // [2, 4, 6]`

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="map-f"></a>f |  Function to execute on every item   |  none |
| <a id="map-arr"></a>arr |  List to iterate over   |  none |

**RETURNS**

A new list with all mapped items.

<a id="once"></a>

## once

<pre>
load("@aspect_bazel_lib//lib:lists.bzl", "once")

once(<a href="#once-f">f</a>, <a href="#once-arr">arr</a>)
</pre>

Check if exactly one item in list `arr` passes the given function `f`.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="once-f"></a>f |  Function to execute on every item   |  none |
| <a id="once-arr"></a>arr |  List to iterate over   |  none |

**RETURNS**

True or False

<a id="pick"></a>

## pick

<pre>
load("@aspect_bazel_lib//lib:lists.bzl", "pick")

pick(<a href="#pick-f">f</a>, <a href="#pick-arr">arr</a>)
</pre>

Pick a particular item in list `arr` by a given function `f`.

Unlike `filter`, the `pick` method returns the first item _found_ by `f`.
If no item has passed `f`, the function will _fail_.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="pick-f"></a>f |  Function to execute on every item   |  none |
| <a id="pick-arr"></a>arr |  List to iterate over   |  none |

**RETURNS**

item

<a id="some"></a>

## some

<pre>
load("@aspect_bazel_lib//lib:lists.bzl", "some")

some(<a href="#some-f">f</a>, <a href="#some-arr">arr</a>)
</pre>

Check if at least one item of `arr` passes function `f`.

Example:
  `some(lambda i: i.endswith(".js"), ["app.js", "lib.ts"]) // True`

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="some-f"></a>f |  Function to execute on every item   |  none |
| <a id="some-arr"></a>arr |  List to iterate over   |  none |

**RETURNS**

True or False

<a id="unique"></a>

## unique

<pre>
load("@aspect_bazel_lib//lib:lists.bzl", "unique")

unique(<a href="#unique-arr">arr</a>)
</pre>

Return a new list with unique items in it.

Example:
  `unique(["foo", "bar", "foo", "baz"]) // ["foo", "bar", "baz"]`

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="unique-arr"></a>arr |  List to iterate over   |  none |

**RETURNS**

A new list with unique items


# copy_file.md


A rule that copies a file to another place.

`native.genrule()` is sometimes used to copy files (often wishing to rename them).
The `copy_file` rule does this with a simpler interface than genrule.

This rule uses a hermetic uutils/coreutils `cp` binary, no shell is required.

This fork of bazel-skylib's copy_file adds `DirectoryPathInfo` support and allows multiple
`copy_file` rules in the same package.

<a id="copy_file"></a>

## copy_file

<pre>
load("@aspect_bazel_lib//lib:copy_file.bzl", "copy_file")

copy_file(<a href="#copy_file-name">name</a>, <a href="#copy_file-src">src</a>, <a href="#copy_file-out">out</a>, <a href="#copy_file-is_executable">is_executable</a>, <a href="#copy_file-allow_symlink">allow_symlink</a>, <a href="#copy_file-kwargs">**kwargs</a>)
</pre>

Copies a file or directory to another location.

`native.genrule()` is sometimes used to copy files (often wishing to rename them). The 'copy_file' rule does this with a simpler interface than genrule.

This rule uses a hermetic uutils/coreutils `cp` binary, no shell is required.

If using this rule with source directories, it is recommended that you use the
`--host_jvm_args=-DBAZEL_TRACK_SOURCE_DIRECTORIES=1` startup option so that changes
to files within source directories are detected. See
https://github.com/bazelbuild/bazel/commit/c64421bc35214f0414e4f4226cc953e8c55fa0d2
for more context.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="copy_file-name"></a>name |  Name of the rule.   |  none |
| <a id="copy_file-src"></a>src |  A Label. The file to make a copy of. (Can also be the label of a rule that generates a file.)   |  none |
| <a id="copy_file-out"></a>out |  Path of the output file, relative to this package.   |  none |
| <a id="copy_file-is_executable"></a>is_executable |  A boolean. Whether to make the output file executable. When True, the rule's output can be executed using `bazel run` and can be in the srcs of binary and test rules that require executable sources. WARNING: If `allow_symlink` is True, `src` must also be executable.   |  `False` |
| <a id="copy_file-allow_symlink"></a>allow_symlink |  A boolean. Whether to allow symlinking instead of copying. When False, the output is always a hard copy. When True, the output *can* be a symlink, but there is no guarantee that a symlink is created (i.e., at the time of writing, we don't create symlinks on Windows). Set this to True if you need fast copying and your tools can handle symlinks (which most UNIX tools can).   |  `False` |
| <a id="copy_file-kwargs"></a>kwargs |  further keyword arguments, e.g. `visibility`   |  none |

<a id="copy_file_action"></a>

## copy_file_action

<pre>
load("@aspect_bazel_lib//lib:copy_file.bzl", "copy_file_action")

copy_file_action(<a href="#copy_file_action-ctx">ctx</a>, <a href="#copy_file_action-src">src</a>, <a href="#copy_file_action-dst">dst</a>, <a href="#copy_file_action-dir_path">dir_path</a>)
</pre>

Factory function that creates an action to copy a file from src to dst.

If src is a TreeArtifact, dir_path must be specified as the path within
the TreeArtifact to the file to copy.

This helper is used by copy_file. It is exposed as a public API so it can be used within
other rule implementations.

To use `copy_file_action` in your own rules, you need to include the toolchains it uses
in your rule definition. For example:

```starlark
load("@aspect_bazel_lib//lib:copy_file.bzl", "COPY_FILE_TOOLCHAINS")

my_rule = rule(
    ...,
    toolchains = COPY_FILE_TOOLCHAINS,
)
```

Additionally, you must ensure that the coreutils toolchain is has been registered in your
WORKSPACE if you are not using bzlmod:

```starlark
load("@aspect_bazel_lib//lib:repositories.bzl", "register_coreutils_toolchains")

register_coreutils_toolchains()
```

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="copy_file_action-ctx"></a>ctx |  The rule context.   |  none |
| <a id="copy_file_action-src"></a>src |  The source file to copy or TreeArtifact to copy a single file out of.   |  none |
| <a id="copy_file_action-dst"></a>dst |  The destination file.   |  none |
| <a id="copy_file_action-dir_path"></a>dir_path |  If src is a TreeArtifact, the path within the TreeArtifact to the file to copy.   |  `None` |


# paths.md


Utilities for working with file paths.

<a id="relative_file"></a>

## relative_file

<pre>
load("@aspect_bazel_lib//lib:paths.bzl", "relative_file")

relative_file(<a href="#relative_file-to_file">to_file</a>, <a href="#relative_file-frm_file">frm_file</a>)
</pre>

Resolves a relative path between two files, "to_file" and "frm_file".

If neither of the paths begin with ../ it is assumed that they share the same root. When finding the relative path,
the incoming files are treated as actual files (not folders) so the resulting relative path may differ when compared
to passing the same arguments to python's "os.path.relpath()" or NodeJs's "path.relative()".

For example, 'relative_file("../foo/foo.txt", "bar/bar.txt")' will return '../../foo/foo.txt'

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="relative_file-to_file"></a>to_file |  the path with file name to resolve to, from frm   |  none |
| <a id="relative_file-frm_file"></a>frm_file |  the path with file name to resolve from   |  none |

**RETURNS**

The relative path from frm_file to to_file, including the file name

<a id="to_output_relative_path"></a>

## to_output_relative_path

<pre>
load("@aspect_bazel_lib//lib:paths.bzl", "to_output_relative_path")

to_output_relative_path(<a href="#to_output_relative_path-file">file</a>)
</pre>

The relative path from bazel-out/[arch]/bin to the given File object

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="to_output_relative_path-file"></a>file |  a `File` object   |  none |

**RETURNS**

The output relative path for the `File`

<a id="to_repository_relative_path"></a>

## to_repository_relative_path

<pre>
load("@aspect_bazel_lib//lib:paths.bzl", "to_repository_relative_path")

to_repository_relative_path(<a href="#to_repository_relative_path-file">file</a>)
</pre>

The repository relative path for a `File`

This is the full runfiles path of a `File` excluding its workspace name.

This differs from  root path (a.k.a. [short_path](https://bazel.build/rules/lib/File#short_path)) and
rlocation path as it does not include the repository name if the `File` is from an external repository.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="to_repository_relative_path-file"></a>file |  a `File` object   |  none |

**RETURNS**

The repository relative path for the `File`

<a id="to_rlocation_path"></a>

## to_rlocation_path

<pre>
load("@aspect_bazel_lib//lib:paths.bzl", "to_rlocation_path")

to_rlocation_path(<a href="#to_rlocation_path-ctx">ctx</a>, <a href="#to_rlocation_path-file">file</a>)
</pre>

The rlocation path for a `File`

This produces the same value as the `rlocationpath` predefined source/output path variable.

From https://bazel.build/reference/be/make-variables#predefined_genrule_variables:

> `rlocationpath`: The path a built binary can pass to the `Rlocation` function of a runfiles
> library to find a dependency at runtime, either in the runfiles directory (if available)
> or using the runfiles manifest.

> This is similar to root path (a.k.a. [short_path](https://bazel.build/rules/lib/File#short_path))
> in that it does not contain configuration prefixes, but differs in that it always starts with the
> name of the repository.

> The rlocation path of a `File` in an external repository repo will start with `repo/`, followed by the
> repository-relative path.

> Passing this path to a binary and resolving it to a file system path using the runfiles libraries
> is the preferred approach to find dependencies at runtime. Compared to root path, it has the
> advantage that it works on all platforms and even if the runfiles directory is not available.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="to_rlocation_path-ctx"></a>ctx |  starlark rule execution context   |  none |
| <a id="to_rlocation_path-file"></a>file |  a `File` object   |  none |

**RETURNS**

The rlocationpath for the `File`


# bazelrc_presets.md


'Presets' for bazelrc

See https://docs.aspect.build/guides/bazelrc

<a id="write_aspect_bazelrc_presets"></a>

## write_aspect_bazelrc_presets

<pre>
load("@aspect_bazel_lib//lib:bazelrc_presets.bzl", "write_aspect_bazelrc_presets")

write_aspect_bazelrc_presets(<a href="#write_aspect_bazelrc_presets-name">name</a>, <a href="#write_aspect_bazelrc_presets-presets">presets</a>, <a href="#write_aspect_bazelrc_presets-kwargs">**kwargs</a>)
</pre>

Keeps your vendored copy of Aspect recommended `.bazelrc` presets up-to-date.

This macro uses a [write_source_files](https://docs.aspect.build/rules/aspect_bazel_lib/docs/write_source_files)
rule under the hood to keep your presets up-to-date.

By default all presets are vendored but this list can be customized using
the `presets` attribute.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="write_aspect_bazelrc_presets-name"></a>name |  a unique name for this target   |  none |
| <a id="write_aspect_bazelrc_presets-presets"></a>presets |  a list of preset names to keep up-to-date   |  `["bazel6", "bazel7", "ci", "convenience", "correctness", "debug", "java", "javascript", "performance"]` |
| <a id="write_aspect_bazelrc_presets-kwargs"></a>kwargs |  Additional arguments to pass to `write_source_files`   |  none |


# docs.md


Public API for docs helpers

<a id="stardoc_with_diff_test"></a>

## stardoc_with_diff_test

<pre>
load("@aspect_bazel_lib//lib:docs.bzl", "stardoc_with_diff_test")

stardoc_with_diff_test(<a href="#stardoc_with_diff_test-name">name</a>, <a href="#stardoc_with_diff_test-bzl_library_target">bzl_library_target</a>, <a href="#stardoc_with_diff_test-kwargs">**kwargs</a>)
</pre>

Creates a stardoc target that can be auto-detected by update_docs to write the generated doc to the source tree and test that it's up to date.

This is helpful for minimizing boilerplate in repos with lots of stardoc targets.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="stardoc_with_diff_test-name"></a>name |  the name of the stardoc file to be written to the current source directory (.md will be appended to the name). Call bazel run on this target to update the file.   |  none |
| <a id="stardoc_with_diff_test-bzl_library_target"></a>bzl_library_target |  the label of the `bzl_library` target to generate documentation for   |  none |
| <a id="stardoc_with_diff_test-kwargs"></a>kwargs |  additional attributes passed to the stardoc() rule, such as for overriding the templates   |  none |

<a id="update_docs"></a>

## update_docs

<pre>
load("@aspect_bazel_lib//lib:docs.bzl", "update_docs")

update_docs(<a href="#update_docs-name">name</a>, <a href="#update_docs-kwargs">**kwargs</a>)
</pre>

Stamps an executable run for writing all stardocs declared with stardoc_with_diff_test to the source tree.

This is to be used in tandem with `stardoc_with_diff_test()` to produce a convenient workflow
for generating, testing, and updating all doc files as follows:

``` bash
# on CI
cd docs; bazel test :all
# if it's out-of-date, then
cd docs; bazel run update
```

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="update_docs-name"></a>name |  the name of executable target   |  `"update"` |
| <a id="update_docs-kwargs"></a>kwargs |  Other common named parameters such as `tags` or `visibility`   |  none |


# params_file.md


params_file public API

<a id="params_file"></a>

## params_file

<pre>
load("@aspect_bazel_lib//lib:params_file.bzl", "params_file")

params_file(<a href="#params_file-name">name</a>, <a href="#params_file-out">out</a>, <a href="#params_file-args">args</a>, <a href="#params_file-data">data</a>, <a href="#params_file-newline">newline</a>, <a href="#params_file-kwargs">**kwargs</a>)
</pre>

Generates a UTF-8 encoded params file from a list of arguments.

Handles variable substitutions for args.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="params_file-name"></a>name |  Name of the rule.   |  none |
| <a id="params_file-out"></a>out |  Path of the output file, relative to this package.   |  none |
| <a id="params_file-args"></a>args |  Arguments to concatenate into a params file.<br><br>- Subject to 'Make variable' substitution. See https://docs.bazel.build/versions/main/be/make-variables.html.<br><br>- Subject to predefined source/output path variables substitutions.<br><br>  The predefined variables `execpath`, `execpaths`, `rootpath`, `rootpaths`, `location`, and `locations` take   label parameters (e.g. `$(execpath //foo:bar)`) and substitute the file paths denoted by that label.<br><br>  See https://docs.bazel.build/versions/main/be/make-variables.html#predefined_label_variables for more info.<br><br>  NB: This $(location) substitution returns the manifest file path which differs from the `*_binary` & `*_test`   args and genrule bazel substitutions. This will be fixed in a future major release.   See docs string of `expand_location_into_runfiles` macro in `internal/common/expand_into_runfiles.bzl`   for more info.<br><br>- Subject to predefined variables & custom variable substitutions.<br><br>  Predefined "Make" variables such as `$(COMPILATION_MODE)` and `$(TARGET_CPU)` are expanded.   See https://docs.bazel.build/versions/main/be/make-variables.html#predefined_variables.<br><br>  Custom variables are also expanded including variables set through the Bazel CLI with `--define=SOME_VAR=SOME_VALUE`.   See https://docs.bazel.build/versions/main/be/make-variables.html#custom_variables.<br><br>  Predefined genrule variables are not supported in this context.   |  `[]` |
| <a id="params_file-data"></a>data |  Data for `$(location)` expansions in args.   |  `[]` |
| <a id="params_file-newline"></a>newline |  Line endings to use. One of [`"auto"`, `"unix"`, `"windows"`].<br><br>- `"auto"` for platform-determined - `"unix"` for LF - `"windows"` for CRLF   |  `"auto"` |
| <a id="params_file-kwargs"></a>kwargs |  undocumented named arguments   |  none |


# repo_utils.md


Public API

<a id="patch"></a>

## patch

<pre>
load("@aspect_bazel_lib//lib:repo_utils.bzl", "patch")

patch(<a href="#patch-ctx">ctx</a>, <a href="#patch-patches">patches</a>, <a href="#patch-patch_cmds">patch_cmds</a>, <a href="#patch-patch_cmds_win">patch_cmds_win</a>, <a href="#patch-patch_tool">patch_tool</a>, <a href="#patch-patch_args">patch_args</a>, <a href="#patch-auth">auth</a>, <a href="#patch-patch_directory">patch_directory</a>)
</pre>

Implementation of patching an already extracted repository.

This rule is intended to be used in the implementation function of
a repository rule. If the parameters `patches`, `patch_tool`,
`patch_args`, `patch_cmds` and `patch_cmds_win` are not specified
then they are taken from `ctx.attr`.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="patch-ctx"></a>ctx |  The repository context of the repository rule calling this utility function.   |  none |
| <a id="patch-patches"></a>patches |  The patch files to apply. List of strings, Labels, or paths.   |  `None` |
| <a id="patch-patch_cmds"></a>patch_cmds |  Bash commands to run for patching, passed one at a time to bash -c. List of strings   |  `None` |
| <a id="patch-patch_cmds_win"></a>patch_cmds_win |  Powershell commands to run for patching, passed one at a time to powershell /c. List of strings. If the boolean value of this parameter is false, patch_cmds will be used and this parameter will be ignored.   |  `None` |
| <a id="patch-patch_tool"></a>patch_tool |  Path of the patch tool to execute for applying patches. String.   |  `None` |
| <a id="patch-patch_args"></a>patch_args |  Arguments to pass to the patch tool. List of strings.   |  `None` |
| <a id="patch-auth"></a>auth |  An optional dict specifying authentication information for some of the URLs.   |  `None` |
| <a id="patch-patch_directory"></a>patch_directory |  Directory to apply the patches in   |  `None` |

<a id="repo_utils.get_env_var"></a>

## repo_utils.get_env_var

<pre>
load("@aspect_bazel_lib//lib:repo_utils.bzl", "repo_utils")

repo_utils.get_env_var(<a href="#repo_utils.get_env_var-rctx">rctx</a>, <a href="#repo_utils.get_env_var-name">name</a>, <a href="#repo_utils.get_env_var-default">default</a>)
</pre>

Find an environment variable in system. Doesn't %-escape the value!

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="repo_utils.get_env_var-rctx"></a>rctx |  rctx   |  none |
| <a id="repo_utils.get_env_var-name"></a>name |  environment variable name   |  none |
| <a id="repo_utils.get_env_var-default"></a>default |  default value to return if env var is not set in system   |  none |

**RETURNS**

The environment variable value or the default if it is not set

<a id="repo_utils.get_home_directory"></a>

## repo_utils.get_home_directory

<pre>
load("@aspect_bazel_lib//lib:repo_utils.bzl", "repo_utils")

repo_utils.get_home_directory(<a href="#repo_utils.get_home_directory-rctx">rctx</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="repo_utils.get_home_directory-rctx"></a>rctx |  <p align="center"> - </p>   |  none |

<a id="repo_utils.is_darwin"></a>

## repo_utils.is_darwin

<pre>
load("@aspect_bazel_lib//lib:repo_utils.bzl", "repo_utils")

repo_utils.is_darwin(<a href="#repo_utils.is_darwin-rctx">rctx</a>)
</pre>

Returns true if the host operating system is Darwin

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="repo_utils.is_darwin-rctx"></a>rctx |  <p align="center"> - </p>   |  none |

<a id="repo_utils.is_linux"></a>

## repo_utils.is_linux

<pre>
load("@aspect_bazel_lib//lib:repo_utils.bzl", "repo_utils")

repo_utils.is_linux(<a href="#repo_utils.is_linux-rctx">rctx</a>)
</pre>

Returns true if the host operating system is Linux

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="repo_utils.is_linux-rctx"></a>rctx |  <p align="center"> - </p>   |  none |

<a id="repo_utils.is_windows"></a>

## repo_utils.is_windows

<pre>
load("@aspect_bazel_lib//lib:repo_utils.bzl", "repo_utils")

repo_utils.is_windows(<a href="#repo_utils.is_windows-rctx">rctx</a>)
</pre>

Returns true if the host operating system is Windows

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="repo_utils.is_windows-rctx"></a>rctx |  <p align="center"> - </p>   |  none |

<a id="repo_utils.os"></a>

## repo_utils.os

<pre>
load("@aspect_bazel_lib//lib:repo_utils.bzl", "repo_utils")

repo_utils.os(<a href="#repo_utils.os-rctx">rctx</a>)
</pre>

Returns the name of the host operating system

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="repo_utils.os-rctx"></a>rctx |  rctx   |  none |

**RETURNS**

The string "windows", "linux", "freebsd" or "darwin" that describes the host os

<a id="repo_utils.platform"></a>

## repo_utils.platform

<pre>
load("@aspect_bazel_lib//lib:repo_utils.bzl", "repo_utils")

repo_utils.platform(<a href="#repo_utils.platform-rctx">rctx</a>)
</pre>

Returns a normalized name of the host os and CPU architecture.

Alias archictures names are normalized:

x86_64 => amd64
aarch64 => arm64

The result can be used to generate repository names for host toolchain
repositories for toolchains that use these normalized names.

Common os & architecture pairs that are returned are,

- darwin_amd64
- darwin_arm64
- linux_amd64
- linux_arm64
- linux_s390x
- linux_ppc64le
- windows_amd64

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="repo_utils.platform-rctx"></a>rctx |  rctx   |  none |

**RETURNS**

The normalized "<os>_<arch>" string of the host os and CPU architecture.


# tar.md


General-purpose rule to create tar archives.

Unlike [pkg_tar from rules_pkg](https://github.com/bazelbuild/rules_pkg/blob/main/docs/latest.md#pkg_tar):

- It does not depend on any Python interpreter setup
- The "manifest" specification is a mature public API and uses a compact tabular format, fixing
  https://github.com/bazelbuild/rules_pkg/pull/238
- It doesn't rely custom program to produce the output, instead
  we rely on the well-known C++ program called "tar".
  Specifically, we use the BSD variant of tar since it provides a means
  of controlling mtimes, uid, symlinks, etc.

We also provide full control for tar'ring binaries including their runfiles.

The `tar` binary is hermetic and fully statically-linked.
It is fetched as a toolchain from https://github.com/aspect-build/bsdtar-prebuilt.

## Examples

See the [`tar` tests](/lib/tests/tar/BUILD.bazel) for examples of usage.

## Mutating the tar contents

The `mtree_spec` rule can be used to create an mtree manifest for the tar file.
Then you can mutate that spec using `mtree_mutate` and feed the result
as the `mtree` attribute of the `tar` rule.

For example, to set the owner uid of files in the tar, you could:

```starlark
_TAR_SRCS = ["//some:files"]

mtree_spec(
    name = "mtree",
    srcs = _TAR_SRCS,
)

mtree_mutate(
    name = "change_owner",
    mtree = ":mtree",
    owner = "1000",
)

tar(
    name = "tar",
    srcs = _TAR_SRCS,
    mtree = "change_owner",
)
```

TODO:
- Provide convenience for rules_pkg users to re-use or replace pkg_files trees

<a id="mtree_spec"></a>

## mtree_spec

<pre>
load("@aspect_bazel_lib//lib:tar.bzl", "mtree_spec")

mtree_spec(<a href="#mtree_spec-name">name</a>, <a href="#mtree_spec-srcs">srcs</a>, <a href="#mtree_spec-out">out</a>, <a href="#mtree_spec-include_runfiles">include_runfiles</a>)
</pre>

Create an mtree specification to map a directory hierarchy. See https://man.freebsd.org/cgi/man.cgi?mtree(8)

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="mtree_spec-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="mtree_spec-srcs"></a>srcs |  Files that are placed into the tar   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="mtree_spec-out"></a>out |  Resulting specification file to write   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="mtree_spec-include_runfiles"></a>include_runfiles |  Include the runfiles tree in the resulting mtree for targets that are executable.<br><br>The runfiles are in the paths that Bazel uses. For example, for the target `//my_prog:foo`, we would see files under paths like `foo.runfiles/<repo name>/my_prog/<file>`   | Boolean | optional |  `True`  |

<a id="tar_rule"></a>

## tar_rule

<pre>
load("@aspect_bazel_lib//lib:tar.bzl", "tar_rule")

tar_rule(<a href="#tar_rule-name">name</a>, <a href="#tar_rule-srcs">srcs</a>, <a href="#tar_rule-out">out</a>, <a href="#tar_rule-args">args</a>, <a href="#tar_rule-compress">compress</a>, <a href="#tar_rule-compute_unused_inputs">compute_unused_inputs</a>, <a href="#tar_rule-mode">mode</a>, <a href="#tar_rule-mtree">mtree</a>)
</pre>

Rule that executes BSD `tar`. Most users should use the [`tar`](#tar) macro, rather than load this directly.

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="tar_rule-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="tar_rule-srcs"></a>srcs |  Files, directories, or other targets whose default outputs are placed into the tar.<br><br>If any of the srcs are binaries with runfiles, those are copied into the resulting tar as well.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="tar_rule-out"></a>out |  Resulting tar file to write. If absent, `[name].tar` is written.   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="tar_rule-args"></a>args |  Additional flags permitted by BSD tar; see the man page.   | List of strings | optional |  `[]`  |
| <a id="tar_rule-compress"></a>compress |  Compress the archive file with a supported algorithm.   | String | optional |  `""`  |
| <a id="tar_rule-compute_unused_inputs"></a>compute_unused_inputs |  Whether to discover and prune input files that will not contribute to the archive.<br><br>Unused inputs are discovered by comparing the set of input files in `srcs` to the set of files referenced by `mtree`. Files not used for content by the mtree specification will not be read by the `tar` tool when creating the archive and can be pruned from the input set using the `unused_inputs_list` [mechanism](https://bazel.build/contribute/codebase#input-discovery).<br><br>Benefits: pruning unused input files can reduce the amount of work the build system must perform. Pruned files are not included in the action cache key; changes to them do not invalidate the cache entry, which can lead to higher cache hit rates. Actions do not need to block on the availability of pruned inputs, which can increase the available parallelism of builds. Pruned files do not need to be transferred to remote-execution workers, which can reduce network costs.<br><br>Risks: pruning an actually-used input file can lead to unexpected, incorrect results. The comparison performed between `srcs` and `mtree` is currently inexact and may fail to handle handwritten or externally-derived mtree specifications. However, it is safe to use this feature when the lines found in `mtree` are derived from one or more `mtree_spec` rules, filtered and/or merged on whole-line basis only.<br><br>Possible values:<br><br>    - `compute_unused_inputs = 1`: Always perform unused input discovery and pruning.     - `compute_unused_inputs = 0`: Never discover or prune unused inputs.     - `compute_unused_inputs = -1`: Discovery and pruning of unused inputs is controlled by the         --[no]@aspect_bazel_lib//lib:tar_compute_unused_inputs flag.   | Integer | optional |  `-1`  |
| <a id="tar_rule-mode"></a>mode |  A mode indicator from the following list, copied from the tar manpage:<br><br>- create: Create a new archive containing the specified items.<br><br>Other modes may be added in the future.   | String | optional |  `"create"`  |
| <a id="tar_rule-mtree"></a>mtree |  An mtree specification file   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |

<a id="mtree_mutate"></a>

## mtree_mutate

<pre>
load("@aspect_bazel_lib//lib:tar.bzl", "mtree_mutate")

mtree_mutate(<a href="#mtree_mutate-name">name</a>, <a href="#mtree_mutate-mtree">mtree</a>, <a href="#mtree_mutate-srcs">srcs</a>, <a href="#mtree_mutate-preserve_symlinks">preserve_symlinks</a>, <a href="#mtree_mutate-strip_prefix">strip_prefix</a>, <a href="#mtree_mutate-package_dir">package_dir</a>, <a href="#mtree_mutate-mtime">mtime</a>, <a href="#mtree_mutate-owner">owner</a>,
             <a href="#mtree_mutate-ownername">ownername</a>, <a href="#mtree_mutate-awk_script">awk_script</a>, <a href="#mtree_mutate-kwargs">**kwargs</a>)
</pre>

Modify metadata in an mtree file.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="mtree_mutate-name"></a>name |  name of the target, output will be `[name].mtree`.   |  none |
| <a id="mtree_mutate-mtree"></a>mtree |  input mtree file, typically created by `mtree_spec`.   |  none |
| <a id="mtree_mutate-srcs"></a>srcs |  list of files to resolve symlinks for.   |  `None` |
| <a id="mtree_mutate-preserve_symlinks"></a>preserve_symlinks |  `EXPERIMENTAL!` We may remove or change it at any point without further notice. Flag to determine whether to preserve symlinks in the tar.   |  `False` |
| <a id="mtree_mutate-strip_prefix"></a>strip_prefix |  prefix to remove from all paths in the tar. Files and directories not under this prefix are dropped.   |  `None` |
| <a id="mtree_mutate-package_dir"></a>package_dir |  directory prefix to add to all paths in the tar.   |  `None` |
| <a id="mtree_mutate-mtime"></a>mtime |  new modification time for all entries.   |  `None` |
| <a id="mtree_mutate-owner"></a>owner |  new uid for all entries.   |  `None` |
| <a id="mtree_mutate-ownername"></a>ownername |  new uname for all entries.   |  `None` |
| <a id="mtree_mutate-awk_script"></a>awk_script |  may be overridden to change the script containing the modification logic.   |  `Label("@aspect_bazel_lib//lib/private:modify_mtree.awk")` |
| <a id="mtree_mutate-kwargs"></a>kwargs |  additional named parameters to genrule   |  none |

<a id="tar"></a>

## tar

<pre>
load("@aspect_bazel_lib//lib:tar.bzl", "tar")

tar(<a href="#tar-name">name</a>, <a href="#tar-mtree">mtree</a>, <a href="#tar-stamp">stamp</a>, <a href="#tar-kwargs">**kwargs</a>)
</pre>

Wrapper macro around [`tar_rule`](#tar_rule).

### Options for mtree

mtree provides the "specification" or manifest of a tar file.
See https://man.freebsd.org/cgi/man.cgi?mtree(8)
Because BSD tar doesn't have a flag to set modification times to a constant,
we must always supply an mtree input to get reproducible builds.
See https://reproducible-builds.org/docs/archives/ for more explanation.

1. By default, mtree is "auto" which causes the macro to create an `mtree_spec` rule.

2. `mtree` may be supplied as an array literal of lines, e.g.

```
mtree =[
    "usr/bin uid=0 gid=0 mode=0755 type=dir",
    "usr/bin/ls uid=0 gid=0 mode=0755 time=0 type=file content={}/a".format(package_name()),
],
```

For the format of a line, see "There are four types of lines in a specification" on the man page for BSD mtree,
https://man.freebsd.org/cgi/man.cgi?mtree(8)

3. `mtree` may be a label of a file containing the specification lines.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="tar-name"></a>name |  name of resulting `tar_rule`   |  none |
| <a id="tar-mtree"></a>mtree |  "auto", or an array of specification lines, or a label of a file that contains the lines. Subject to [$(location)](https://bazel.build/reference/be/make-variables#predefined_label_variables) and ["Make variable"](https://bazel.build/reference/be/make-variables) substitution.   |  `"auto"` |
| <a id="tar-stamp"></a>stamp |  should mtree attribute be stamped   |  `0` |
| <a id="tar-kwargs"></a>kwargs |  additional named parameters to pass to `tar_rule`   |  none |

<a id="tar_lib.common.add_compression_args"></a>

## tar_lib.common.add_compression_args

<pre>
load("@aspect_bazel_lib//lib:tar.bzl", "tar_lib")

tar_lib.common.add_compression_args(<a href="#tar_lib.common.add_compression_args-compress">compress</a>, <a href="#tar_lib.common.add_compression_args-args">args</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="tar_lib.common.add_compression_args-compress"></a>compress |  <p align="center"> - </p>   |  none |
| <a id="tar_lib.common.add_compression_args-args"></a>args |  <p align="center"> - </p>   |  none |

<a id="tar_lib.implementation"></a>

## tar_lib.implementation

<pre>
load("@aspect_bazel_lib//lib:tar.bzl", "tar_lib")

tar_lib.implementation(<a href="#tar_lib.implementation-ctx">ctx</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="tar_lib.implementation-ctx"></a>ctx |  <p align="center"> - </p>   |  none |

<a id="tar_lib.mtree_implementation"></a>

## tar_lib.mtree_implementation

<pre>
load("@aspect_bazel_lib//lib:tar.bzl", "tar_lib")

tar_lib.mtree_implementation(<a href="#tar_lib.mtree_implementation-ctx">ctx</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="tar_lib.mtree_implementation-ctx"></a>ctx |  <p align="center"> - </p>   |  none |


# write_source_files.md


write_source_files provides a workaround for the restriction that `bazel build` cannot write to the source tree.

Read more about the philosophy of writing to the source tree: <https://blog.aspect.build/bazel-can-write-to-the-source-folder>

## Usage

```starlark
load("@aspect_bazel_lib//lib:write_source_files.bzl", "write_source_files")

write_source_files(
    name = "write_foobar",
    files = {
        "foobar.json": "//some/generated:file",
    },
)
```

To update the source file, run:

```bash
bazel run //:write_foobar
```

The generated `diff_test` will fail if the file is out of date and print out instructions on
how to update it.

If the file does not exist, Bazel will fail at analysis time and print out instructions on
how to create it.

You can declare a tree of generated source file targets:

```starlark
load("@aspect_bazel_lib//lib:write_source_files.bzl", "write_source_files")

write_source_files(
    name = "write_all",
    additional_update_targets = [
        # Other write_source_files targets to run when this target is run
        "//a/b/c:write_foo",
        "//a/b:write_bar",
    ]
)
```

And update them with a single run:

```bash
bazel run //:write_all
```

When a file is out of date, you can leave a suggestion to run a target further up in the tree by specifying `suggested_update_target`.
For example,

```starlark
write_source_files(
    name = "write_foo",
    files = {
        "foo.json": ":generated-foo",
    },
    suggested_update_target = "//:write_all"
)
```

A test failure from `foo.json` being out of date will yield the following message:

```
//a/b:c:foo.json is out of date. To update this and other generated files, run:

    bazel run //:write_all

To update *only* this file, run:

    bazel run //a/b/c:write_foo
```

You can also add a more customized error message using the `diff_test_failure_message` argument:

```starlark
write_source_file(
    name = "write_foo",
    out_file = "foo.json",
    in_file = ":generated-foo",
    diff_test_failure_message = "Failed to build Foo; please run {{TARGET}} to update."
)
```

A test failure from `foo.json` being out of date will then yield:

```
Failed to build Foo; please run //a/b/c:write_foo to update.
```

If you have many `write_source_files` targets that you want to update as a group, we recommend wrapping
`write_source_files` in a macro that defaults `suggested_update_target` to the umbrella update target.

NOTE: If you run formatters or linters on your codebase, it is advised that you exclude/ignore the outputs of this
    rule from those formatters/linters so as to avoid causing collisions and failing tests.

<a id="WriteSourceFileInfo"></a>

## WriteSourceFileInfo

<pre>
load("@aspect_bazel_lib//lib:write_source_files.bzl", "WriteSourceFileInfo")

WriteSourceFileInfo(<a href="#WriteSourceFileInfo-executable">executable</a>)
</pre>

Provider for write_source_file targets

**FIELDS**

| Name  | Description |
| :------------- | :------------- |
| <a id="WriteSourceFileInfo-executable"></a>executable |  Executable that updates the source files    |

<a id="write_source_file"></a>

## write_source_file

<pre>
load("@aspect_bazel_lib//lib:write_source_files.bzl", "write_source_file")

write_source_file(<a href="#write_source_file-name">name</a>, <a href="#write_source_file-in_file">in_file</a>, <a href="#write_source_file-out_file">out_file</a>, <a href="#write_source_file-executable">executable</a>, <a href="#write_source_file-additional_update_targets">additional_update_targets</a>,
                  <a href="#write_source_file-suggested_update_target">suggested_update_target</a>, <a href="#write_source_file-diff_test">diff_test</a>, <a href="#write_source_file-diff_test_failure_message">diff_test_failure_message</a>,
                  <a href="#write_source_file-file_missing_failure_message">file_missing_failure_message</a>, <a href="#write_source_file-diff_args">diff_args</a>, <a href="#write_source_file-check_that_out_file_exists">check_that_out_file_exists</a>, <a href="#write_source_file-verbosity">verbosity</a>,
                  <a href="#write_source_file-kwargs">**kwargs</a>)
</pre>

Write a file or directory to the source tree.

By default, a `diff_test` target ("{name}_test") is generated that ensure the source tree file or directory to be written to
is up to date and the rule also checks that the source tree file or directory to be written to exists.
To disable the exists check and up-to-date test set `diff_test` to `False`.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="write_source_file-name"></a>name |  Name of the runnable target that creates or updates the source tree file or directory.   |  none |
| <a id="write_source_file-in_file"></a>in_file |  File or directory to use as the desired content to write to `out_file`.<br><br>This is typically a file or directory output of another target. If `in_file` is a directory then entire directory contents are copied.   |  `None` |
| <a id="write_source_file-out_file"></a>out_file |  The file or directory to write to in the source tree.<br><br>The output file or directory must be within the same containing Bazel package as this target if `check_that_out_file_exists` is `True`. See `check_that_out_file_exists` docstring for more info.   |  `None` |
| <a id="write_source_file-executable"></a>executable |  Whether source tree file or files within the source tree directory written should be made executable.   |  `False` |
| <a id="write_source_file-additional_update_targets"></a>additional_update_targets |  List of other `write_source_files` or `write_source_file` targets to call in the same run.   |  `[]` |
| <a id="write_source_file-suggested_update_target"></a>suggested_update_target |  Label of the `write_source_files` or `write_source_file` target to suggest running when files are out of date.   |  `None` |
| <a id="write_source_file-diff_test"></a>diff_test |  Test that the source tree file or directory exist and is up to date.   |  `True` |
| <a id="write_source_file-diff_test_failure_message"></a>diff_test_failure_message |  Text to print when the diff test fails, with templating options for relevant targets.<br><br>Substitutions are performed on the failure message, with the following substitutions being available:<br><br>`{{DEFAULT_MESSAGE}}`: Prints the default error message, listing the target(s) that   may be run to update the file(s).<br><br>`{{TARGET}}`: The target to update the individual file that does not match in the   diff test.<br><br>`{{SUGGESTED_UPDATE_TARGET}}`: The suggested_update_target if specified.   |  `"{{DEFAULT_MESSAGE}}"` |
| <a id="write_source_file-file_missing_failure_message"></a>file_missing_failure_message |  Text to print when the output file is missing. Subject to the same substitutions as diff_test_failure_message.   |  `"{{DEFAULT_MESSAGE}}"` |
| <a id="write_source_file-diff_args"></a>diff_args |  Arguments to pass to the `diff` command. (Ignored on Windows)   |  `[]` |
| <a id="write_source_file-check_that_out_file_exists"></a>check_that_out_file_exists |  Test that the output file exists and print a helpful error message if it doesn't.<br><br>If `True`, the output file or directory must be in the same containing Bazel package as the target since the underlying mechanism for this check is limited to files in the same Bazel package.   |  `True` |
| <a id="write_source_file-verbosity"></a>verbosity |  Verbosity of message when the copy target is run. One of `full`, `short`, `quiet`.   |  `"full"` |
| <a id="write_source_file-kwargs"></a>kwargs |  Other common named parameters such as `tags` or `visibility`   |  none |

**RETURNS**

Name of the generated test target if requested, otherwise None.

<a id="write_source_files"></a>

## write_source_files

<pre>
load("@aspect_bazel_lib//lib:write_source_files.bzl", "write_source_files")

write_source_files(<a href="#write_source_files-name">name</a>, <a href="#write_source_files-files">files</a>, <a href="#write_source_files-executable">executable</a>, <a href="#write_source_files-additional_update_targets">additional_update_targets</a>, <a href="#write_source_files-suggested_update_target">suggested_update_target</a>,
                   <a href="#write_source_files-diff_test">diff_test</a>, <a href="#write_source_files-diff_test_failure_message">diff_test_failure_message</a>, <a href="#write_source_files-diff_args">diff_args</a>, <a href="#write_source_files-file_missing_failure_message">file_missing_failure_message</a>,
                   <a href="#write_source_files-check_that_out_file_exists">check_that_out_file_exists</a>, <a href="#write_source_files-kwargs">**kwargs</a>)
</pre>

Write one or more files and/or directories to the source tree.

By default, `diff_test` targets are generated that ensure the source tree files and/or directories to be written to
are up to date and the rule also checks that all source tree files and/or directories to be written to exist.
To disable the exists check and up-to-date tests set `diff_test` to `False`.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="write_source_files-name"></a>name |  Name of the runnable target that creates or updates the source tree files and/or directories.   |  none |
| <a id="write_source_files-files"></a>files |  A dict where the keys are files or directories in the source tree to write to and the values are labels pointing to the desired content, typically file or directory outputs of other targets.<br><br>Destination files and directories must be within the same containing Bazel package as this target if `check_that_out_file_exists` is True. See `check_that_out_file_exists` docstring for more info.   |  `{}` |
| <a id="write_source_files-executable"></a>executable |  Whether source tree files written should be made executable.<br><br>This applies to all source tree files written by this target. This attribute is not propagated to `additional_update_targets`.<br><br>To set different executable permissions on different source tree files use multiple `write_source_files` targets.   |  `False` |
| <a id="write_source_files-additional_update_targets"></a>additional_update_targets |  List of other `write_source_files` or `write_source_file` targets to call in the same run.   |  `[]` |
| <a id="write_source_files-suggested_update_target"></a>suggested_update_target |  Label of the `write_source_files` or `write_source_file` target to suggest running when files are out of date.   |  `None` |
| <a id="write_source_files-diff_test"></a>diff_test |  Test that the source tree files and/or directories exist and are up to date.   |  `True` |
| <a id="write_source_files-diff_test_failure_message"></a>diff_test_failure_message |  Text to print when the diff test fails, with templating options for relevant targets.<br><br>Substitutions are performed on the failure message, with the following substitutions being available:<br><br>`{{DEFAULT_MESSAGE}}`: Prints the default error message, listing the target(s) that   may be run to update the file(s).<br><br>`{{TARGET}}`: The target to update the individual file that does not match in the   diff test.<br><br>`{{SUGGESTED_UPDATE_TARGET}}`: The suggested_update_target if specified, or the   target which will update all of the files which do not match.   |  `"{{DEFAULT_MESSAGE}}"` |
| <a id="write_source_files-diff_args"></a>diff_args |  Arguments to pass to the `diff` command. (Ignored on Windows)   |  `[]` |
| <a id="write_source_files-file_missing_failure_message"></a>file_missing_failure_message |  Text to print when the output file is missing. Subject to the same substitutions as diff_test_failure_message.   |  `"{{DEFAULT_MESSAGE}}"` |
| <a id="write_source_files-check_that_out_file_exists"></a>check_that_out_file_exists |  Test that each output file exists and print a helpful error message if it doesn't.<br><br>If `True`, destination files and directories must be in the same containing Bazel package as the target since the underlying mechanism for this check is limited to files in the same Bazel package.   |  `True` |
| <a id="write_source_files-kwargs"></a>kwargs |  Other common named parameters such as `tags` or `visibility`   |  none |


# diff_test.md


A test rule that compares two binary files or two directories.

Similar to `bazel-skylib`'s [`diff_test`](https://github.com/bazelbuild/bazel-skylib/blob/main/rules/diff_test.bzl)
but also supports comparing directories.

The rule uses a Bash command (diff) on Linux/macOS/non-Windows, and a cmd.exe
command (fc.exe) on Windows (no Bash is required).

See also: [rules_diff](https://gitlab.arm.com/bazel/rules_diff)

<a id="diff_test"></a>

## diff_test

<pre>
load("@aspect_bazel_lib//lib:diff_test.bzl", "diff_test")

diff_test(<a href="#diff_test-name">name</a>, <a href="#diff_test-file1">file1</a>, <a href="#diff_test-file2">file2</a>, <a href="#diff_test-diff_args">diff_args</a>, <a href="#diff_test-size">size</a>, <a href="#diff_test-kwargs">**kwargs</a>)
</pre>

A test that compares two files.

The test succeeds if the files' contents match.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="diff_test-name"></a>name |  The name of the test rule.   |  none |
| <a id="diff_test-file1"></a>file1 |  Label of the file to compare to <code>file2</code>.   |  none |
| <a id="diff_test-file2"></a>file2 |  Label of the file to compare to <code>file1</code>.   |  none |
| <a id="diff_test-diff_args"></a>diff_args |  Arguments to pass to the `diff` command. (Ignored on Windows)   |  `[]` |
| <a id="diff_test-size"></a>size |  standard attribute for tests   |  `"small"` |
| <a id="diff_test-kwargs"></a>kwargs |  The <a href="https://docs.bazel.build/versions/main/be/common-definitions.html#common-attributes-tests">common attributes for tests</a>.   |  none |

