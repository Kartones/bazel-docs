
# Bazel JavaScript toolchain

The `@rules_nodejs` Bazel module contains a toolchain that fetches a hermetic node and npm (independent of what's on the developer's machine).
It is currently useful for Bazel Rules developers who want to make their own JavaScript support, and
is maintained by community volunteers from [Aspect](https://aspect.dev).
    - [Install and setup](install.md)
    - [Rules API](Core.md)
    - [Toolchains](Toolchains.md)

## Deprecated modules

> 🚨 `@build_bazel_rules_nodejs` and `@bazel/*` packages are now mostly unmaintained! 🚨
>
> See the Maintenance Update in the [root README](https://github.com/bazel-contrib/rules_nodejs#maintenance-update)

Previously this repository also contained the `@build_bazel_rules_nodejs` module and additional npm packages under the `@bazel` scope on [npm](http://npmjs.com/~bazel).

**There are currently no maintainers of those npm modules.**

If you would like to write a rule outside the scope of the projects we recommend hosting them in your GitHub account or the one of your organization.

## Design

Our goal is to make Bazel be a minimal layering on top of existing npm tooling, and to have maximal compatibility with those tools.

This means you won't find a "Webpack vs. Rollup" debate here. You can run whatever tools you like under Bazel. In fact, we recommend running the same tools you're currently using, so that your Bazel migration only changes one thing at a time.

In many cases, there are trade-offs. We try not to make these decisions for you, so instead of paving one "best" way to do things like many JS tooling options, we provide multiple ways. This increases complexity in understanding and using these rules, but also avoids choosing a wrong "winner". For example, you could install the dependencies yourself, or have Bazel manage its own copy of the dependencies, or have Bazel symlink to the ones in the project.

The JS ecosystem is also full of false equivalence arguments. The first question we often get is "What's better, Webpack or Bazel?".
This is understandable, since most JS tooling is forced to provide a single turn-key experience with an isolated ecosystem of plugins, and humans love a head-to-head competition.
Instead Bazel just orchestrates calling these tools.


# Generated Repositories

rules_nodejs produces several repositories for you to reference.
Bazel represents your workspace as one repository, and code fetched or installed from outside your workspace lives in other repositories.
These are referenced with the `@repo//` syntax in your BUILD files.

## @nodejs

This repository is created by calling the `nodejs_repositories` function in your `WORKSPACE` file.
It contains the node, npm, and npx programs.

As always, `bazel query` is useful for learning about what targets are available.

```sh
$ bazel query @nodejs//...
@nodejs//:node
...
```

You don't typically need to reference the `@nodejs` repository from your BUILD files because it's used behind the scenes to run node and fetch dependencies.

Some ways you can use this:

- Run the Bazel-managed version of node: `bazel run @nodejs//:node path/to/program.js`
- Run the Bazel-managed version of npm: `bazel run @nodejs//:npm`

(Note: for backward-compatibility, the `@nodejs` repository can also be referenced as `@nodejs_host`).
# Stamping

Bazel is generally only a build tool, and is unaware of your version control system.
However, when publishing releases, you may want to embed version information in the resulting distribution.
Bazel supports this with the concept of a "Workspace status" which is evaluated before each build.
See [the Bazel workspace status docs](https://docs.bazel.build/versions/master/user-manual.html#workspace_status)

To stamp a build, you must pass the `--stamp` argument to Bazel.

Stamping is typically performed on a later action in the graph, like on a packaging rule (`pkg_*`). This means that
a changed status variable only causes re-packaging, not re-compilation and thus does not cause cascading re-builds.

Bazel provides a couple of statuses by default, such as `BUILD_EMBED_LABEL` which is the value of the `--embed_label`
argument, as well as `BUILD_HOST` and `BUILD_USER`. You can supply more with the workspace status script, see below.

Some rules accept an attribute that uses the status variables.

## Stamping with a Workspace status script

To define additional statuses, pass the `--workspace_status_command` argument to `bazel`.
The value of this flag is a path to a script that prints space-separated key/value pairs, one per line, such as

```bash
#!/usr/bin/env bash
echo STABLE_GIT_COMMIT $(git rev-parse HEAD)
```

Make sure you set the executable bit, eg. `chmod 755 tools/bazel_stamp_vars.sh`.

> **NOTE** keys that start with `STABLE_` will cause a re-build when they change.
> Other keys will NOT cause a re-build, so stale values can appear in your app.
> Non-stable (volatile) keys should typically be things like timestamps that always vary between builds.

You might like to encode your setup using an entry in `.bazelrc` such as:

```sh
# This tells Bazel how to interact with the version control system
# Enable this with --config=release
build:release --stamp --workspace_status_command=./tools/bazel_stamp_vars.sh
```

## Release script

If you publish more than one package from your workspace, you might want a release script around Bazel.
A nice pattern is to do a `bazel query` to find publishable targets, build them in parallel, then publish in a loop.
Here is a template to get you started:

```sh
#!/usr/bin/env bash

set -u -e -o pipefail

# Call the script with argument "pack" or "publish"
readonly PKG_COMMAND=${1:-publish}
# Don't rely on $PATH to have the right version
readonly BAZEL=./node_modules/.bin/bazel
# Find all the npm packages in the repo
readonly PKG_LABELS=`$BAZEL query --output=label 'kind("pkg_tar", //...)'`
# Build them in one command to maximize parallelism
$BAZEL build --config=release $PKG_LABELS
# publish one package at a time to make it easier to spot any errors or warnings
for pkg in $PKG_LABELS ; do
  $BAZEL run --config=release -- ${pkg}.${PKG_COMMAND} --access public --tag latest
done
```

See https://www.kchodorow.com/blog/2017/03/27/stamping-your-builds/ for more background.
Make sure you use a "STABLE_" status key, or else Bazel may use a cached npm artifact rather than
building a new one with your current version info.

# Patching changes

One advantage of open-source software is that you can make your own changes that suit your needs.

The `@rules_nodejs` module can simply be fetched from sources in place of the published distribution.
For example, in place of

```starlark
http_archive(
    name = "rules_nodejs",
    sha256 = "...",
    urls = ["https://github.com/bazel-contrib/rules_nodejs/releases/download/6.0.0/rules_nodejs-6.0.0.tar.gz"],
)
```

you can just use a commit from your fork:

```starlark
http_archive(
    name = "rules_nodejs",
    sha256 = "...",
    strip_prefix = "rules_nodejs-abcd123",
    url = "https://github.com/my-org/rules_nodejs/archive/abcd123.tar.gz",
)
```

## Patching the rules_nodejs release

Bazel has a handy patching mechanism that lets you easily apply a local patch to the release artifact for built-in rules: [the `patches` attribute to `http_archive`](https://docs.bazel.build/versions/master/repo/http.html#attributes).

First, make your changes in a clone of the rules_nodejs repo. Export a patch file simply using `git diff`:

```sh
git diff > my.patch
```

Then copy the patch file somewhere in your repo and point to it from your `WORKSPACE` file:

```python
http_archive(
    name = "rules_nodejs",
    patch_args = ["-p1"],
    patches = ["//path/to/my.patch"],
    sha256 = "...",
    urls = ["https://github.com/bazel-contrib/rules_nodejs/releases/download/6.0.0/rules_nodejs-6.0.0.tar.gz"],
)
```


# Installation

## Installation with a specific version of Node.js

You can choose a specific version of Node.js. We mirror all published versions, which you can see in this repo at `/nodejs/private/node_versions.bzl`.

> Now that Node 12 is LTS (Long-term support) we encourage you to upgrade, and don't intend to fix bugs which are only observed in Node 10 or lower.
> Some of our packages have started to use features from Node 12, so you may see warnings if you use an older version.

Add to `WORKSPACE`:

```python
nodejs_repositories(
    node_version = "8.11.1",
)
```

## Installation with a manually specified version of Node.js

If you'd like to use a version of Node.js that is not currently supported here,
for example one that you host within your org, you can manually specify those in your `WORKSPACE`:

```python
load("@rules_nodejs//nodejs:repositories.bzl", "node_repositories")

nodejs_repositories(
  node_version = "8.10.0",
  node_repositories = {
    "8.10.0-darwin_amd64": ("node-v8.10.0-darwin-x64.tar.gz", "node-v8.10.0-darwin-x64", "7d77bd35bc781f02ba7383779da30bd529f21849b86f14d87e097497671b0271"),
    "8.10.0-linux_amd64": ("node-v8.10.0-linux-x64.tar.xz", "node-v8.10.0-linux-x64", "92220638d661a43bd0fee2bf478cb283ead6524f231aabccf14c549ebc2bc338"),
    "8.10.0-windows_amd64": ("node-v8.10.0-win-x64.zip", "node-v8.10.0-win-x64", "936ada36cb6f09a5565571e15eb8006e45c5a513529c19e21d070acf0e50321b"),
  },
  node_urls = ["https://nodejs.org/dist/v{version}/{filename}"],
```

Specifying `node_urls` is optional. If omitted, the default values will be used.

## Installation with local vendored versions of Node.js

You can use your own Node.js binary rather than fetching from the internet.
You could check in a binary file, or build Node.js from sources.
To use See [`nodejs_toolchain`](./Core.md#nodejs_toolchain) for docs.

<!-- *********************
  DO NOT EDIT THIS FILE
  It is a generated build output from Stardoc.
  Instead you must edit the .bzl file where the rules are declared,
  or possibly a markdown file next to the .bzl file
 ********************* -->
# rules_nodejs Bazel module

Features:
- A [Toolchain](https://docs.bazel.build/versions/main/toolchains.html)
  that fetches a hermetic copy of node and npm - independent of what's on the developer's machine.
- Core [Providers](https://docs.bazel.build/versions/main/skylark/rules.html#providers) to allow interop between JS rules.

## UserBuildSettingInfo

**USAGE**

<pre>
UserBuildSettingInfo(<a href="#UserBuildSettingInfo-value">value</a>)
</pre>

**FIELDS**

<h4 id="UserBuildSettingInfo-value">value</h4>

 - 

## nodejs_repositories

**USAGE**

<pre>
nodejs_repositories(<a href="#nodejs_repositories-name">name</a>, <a href="#nodejs_repositories-node_download_auth">node_download_auth</a>, <a href="#nodejs_repositories-node_repositories">node_repositories</a>, <a href="#nodejs_repositories-node_urls">node_urls</a>, <a href="#nodejs_repositories-node_version">node_version</a>,
                    <a href="#nodejs_repositories-node_version_from_nvmrc">node_version_from_nvmrc</a>, <a href="#nodejs_repositories-include_headers">include_headers</a>, <a href="#nodejs_repositories-kwargs">kwargs</a>)
</pre>

To be run in user's WORKSPACE to install rules_nodejs dependencies.

This rule sets up node, npm, and npx. The versions of these tools can be specified in one of three ways

### Simplest Usage

Specify no explicit versions. This will download and use the latest Node.js that was available when the
version of rules_nodejs you're using was released.

### Forced version(s)

You can select the version of Node.js to download & use by specifying it when you call node_repositories,
using a value that matches a known version (see the default values)

### Using a custom version

You can pass in a custom list of Node.js repositories and URLs for node_repositories to use.

#### Custom Node.js versions

To specify custom Node.js versions, use the `node_repositories` attribute

```python
nodejs_repositories(
    node_repositories = {
        "10.10.0-darwin_amd64": ("node-v10.10.0-darwin-x64.tar.gz", "node-v10.10.0-darwin-x64", "00b7a8426e076e9bf9d12ba2d571312e833fe962c70afafd10ad3682fdeeaa5e"),
        "10.10.0-linux_amd64": ("node-v10.10.0-linux-x64.tar.xz", "node-v10.10.0-linux-x64", "686d2c7b7698097e67bcd68edc3d6b5d28d81f62436c7cf9e7779d134ec262a9"),
        "10.10.0-windows_amd64": ("node-v10.10.0-win-x64.zip", "node-v10.10.0-win-x64", "70c46e6451798be9d052b700ce5dadccb75cf917f6bf0d6ed54344c856830cfb"),
    },
)
```

These can be mapped to a custom download URL, using `node_urls`

```python
nodejs_repositories(
    node_version = "10.10.0",
    node_repositories = {"10.10.0-darwin_amd64": ("node-v10.10.0-darwin-x64.tar.gz", "node-v10.10.0-darwin-x64", "00b7a8426e076e9bf9d12ba2d571312e833fe962c70afafd10ad3682fdeeaa5e")},
    node_urls = ["https://mycorpproxy/mirror/node/v{version}/{filename}"],
)
```

A Mac client will try to download node from `https://mycorpproxy/mirror/node/v10.10.0/node-v10.10.0-darwin-x64.tar.gz`
and expect that file to have sha256sum `00b7a8426e076e9bf9d12ba2d571312e833fe962c70afafd10ad3682fdeeaa5e`

See the [the repositories documentation](repositories.html) for how to use the resulting repositories.

### Using a custom node.js.

To avoid downloads, you can check in a vendored node.js binary or can build one from source.
See [toolchains](./toolchains.md).

**PARAMETERS**

<h4 id="nodejs_repositories-name">name</h4>

Unique name for the repository rule

<h4 id="nodejs_repositories-node_download_auth">node_download_auth</h4>

Auth to use for all url requests.

Example: { "type": "basic", "login": "&lt;UserName&gt;", "password": "&lt;Password&gt;" }

Defaults to `{}`

<h4 id="nodejs_repositories-node_repositories">node_repositories</h4>

Custom list of node repositories to use

A dictionary mapping Node.js versions to sets of hosts and their corresponding (filename, strip_prefix, sha256) tuples.
You should list a node binary for every platform users have, likely Mac, Windows, and Linux.

By default, if this attribute has no items, we'll use a list of all public Node.js releases.

Defaults to `{}`

<h4 id="nodejs_repositories-node_urls">node_urls</h4>

List of URLs to use to download Node.js.

Each entry is a template for downloading a node distribution.

The `{version}` parameter is substituted with the `node_version` attribute,
and `{filename}` with the matching entry from the `node_repositories` attribute.

Defaults to `["https://nodejs.org/dist/v{version}/{filename}"]`

<h4 id="nodejs_repositories-node_version">node_version</h4>

The specific version of Node.js to install

Defaults to `"18.20.8"`

<h4 id="nodejs_repositories-node_version_from_nvmrc">node_version_from_nvmrc</h4>

The .nvmrc file containing the version of Node.js to use.

If set then the version found in the .nvmrc file is used instead of the one specified by node_version.

Defaults to `None`

<h4 id="nodejs_repositories-include_headers">include_headers</h4>

Set headers field in NodeInfo provided by this toolchain.

This setting creates a dependency on a c++ toolchain.

Defaults to `False`

<h4 id="nodejs_repositories-kwargs">kwargs</h4>

Additional parameters

## nodejs_toolchain

**USAGE**

<pre>
nodejs_toolchain(<a href="#nodejs_toolchain-name">name</a>, <a href="#nodejs_toolchain-node">node</a>, <a href="#nodejs_toolchain-node_path">node_path</a>, <a href="#nodejs_toolchain-npm">npm</a>, <a href="#nodejs_toolchain-npm_path">npm_path</a>, <a href="#nodejs_toolchain-npm_srcs">npm_srcs</a>, <a href="#nodejs_toolchain-headers">headers</a>, <a href="#nodejs_toolchain-kwargs">kwargs</a>)
</pre>

Defines a node toolchain for a platform.

You can use this to refer to a vendored nodejs binary in your repository,
or even to compile nodejs from sources using rules_foreign_cc or other rules.

First, in a BUILD.bazel file, create a nodejs_toolchain definition:

```starlark
load("@rules_nodejs//nodejs:toolchain.bzl", "nodejs_toolchain")

nodejs_toolchain(
    name = "toolchain",
    node = "//some/path/bin/node",
)
```

Next, declare which execution platforms or target platforms the toolchain should be selected for
based on constraints.

```starlark
toolchain(
    name = "my_nodejs",
    exec_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":toolchain",
    toolchain_type = "@rules_nodejs//nodejs:toolchain_type",
)
```

See https://bazel.build/extending/toolchains#toolchain-resolution for more information on toolchain
resolution.

Finally in your `WORKSPACE`, register it with `register_toolchains("//:my_nodejs")`

For usage see https://docs.bazel.build/versions/main/toolchains.html#defining-toolchains.
You can use the `--toolchain_resolution_debug` flag to `bazel` to help diagnose which toolchain is selected.

**PARAMETERS**

<h4 id="nodejs_toolchain-name">name</h4>

Unique name for this target

<h4 id="nodejs_toolchain-node">node</h4>

Node.js executable

Defaults to `None`

<h4 id="nodejs_toolchain-node_path">node_path</h4>

Path to Node.js executable file

This is typically an absolute path to a non-hermetic Node.js executable.

Only one of `node` and `node_path` may be set.

Defaults to `""`

<h4 id="nodejs_toolchain-npm">npm</h4>

Npm JavaScript entry point

Defaults to `None`

<h4 id="nodejs_toolchain-npm_path">npm_path</h4>

Path to npm JavaScript entry point.

This is typically an absolute path to a non-hermetic npm installation.

Only one of `npm` and `npm_path` may be set.

Defaults to `""`

<h4 id="nodejs_toolchain-npm_srcs">npm_srcs</h4>

Additional source files required to run npm.

Not necessary if specifying `npm_path` to a non-hermetic npm installation.

Defaults to `[]`

<h4 id="nodejs_toolchain-headers">headers</h4>

cc_library that contains the Node/v8 header files

Defaults to `None`

<h4 id="nodejs_toolchain-kwargs">kwargs</h4>

Additional parameters


# Toolchains

API docs for [Toolchain](https://docs.bazel.build/versions/main/toolchains.html) support.

When you call `nodejs_register_toolchains()` in your `WORKSPACE` file it will setup a node toolchain for executing tools on all currently supported platforms.

If you have an advanced use-case and want to use a version of node not supported by this repository, you can also register your own toolchains.

## Registering a custom toolchain

To run a custom toolchain (i.e., to run a node binary not supported by the built-in toolchains), you'll need four things:

1) A rule which can build or load a node binary from your repository
   (a checked-in binary or a build using a relevant [`rules_foreign_cc` build rule](https://bazelbuild.github.io/rules_foreign_cc/) will do nicely).
2) A [`nodejs_toolchain` rule](Core.html#nodejs_toolchain) which depends on your binary defined in step 1 as its `node`.
3) A [`toolchain` rule](https://bazel.build/reference/be/platform#toolchain) that depends on your `nodejs_toolchain` rule defined in step 2 as its `toolchain`
   and on `@rules_nodejs//nodejs:toolchain_type` as its `toolchain_type`. Make sure to define appropriate platform restrictions as described in the
   documentation for the `toolchain` rule.
4) A call to [the `register_toolchains` function](https://bazel.build/rules/lib/globals#register_toolchains) in your `WORKSPACE`
   that refers to the `toolchain` rule defined in step 3.

Examples of steps 2-4 can be found in the [documentation for `nodejs_toolchain`](Core.html#nodejs_toolchain).

If necessary, you can substitute building the node binary as part of the build with using a locally installed version by skipping step 1 and replacing step 2 with:

2) A `nodejs_toolchain` rule which has the path of the system binary as its `node_path`