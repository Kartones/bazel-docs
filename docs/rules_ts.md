# repositories.md


Declare runtime dependencies

These are needed for local dev, and users must install them as well.
See https://docs.bazel.build/versions/main/skylark/deploying.html#dependencies

<a id="rules_ts_dependencies"></a>

## rules_ts_dependencies

<pre>
load("@aspect_rules_ts//ts:repositories.bzl", "rules_ts_dependencies")

rules_ts_dependencies(<a href="#rules_ts_dependencies-name">name</a>, <a href="#rules_ts_dependencies-ts_version_from">ts_version_from</a>, <a href="#rules_ts_dependencies-ts_version">ts_version</a>, <a href="#rules_ts_dependencies-ts_integrity">ts_integrity</a>)
</pre>

Dependencies needed by users of rules_ts.

To skip fetching the typescript package, call `rules_ts_bazel_dependencies` instead.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="rules_ts_dependencies-name"></a>name |  name of the resulting external repository containing the TypeScript compiler.   |  `"npm_typescript"` |
| <a id="rules_ts_dependencies-ts_version_from"></a>ts_version_from |  label of a json file which declares a typescript version.<br><br>This may be a `package.json` file, with "typescript" in the dependencies or devDependencies property, and the version exactly specified.<br><br>With rules_js v1.32.0 or greater, it may also be a `resolved.json` file produced by `npm_translate_lock`, such as `@npm//path/to/linked:typescript/resolved.json`<br><br>Exactly one of `ts_version` or `ts_version_from` must be set.   |  `None` |
| <a id="rules_ts_dependencies-ts_version"></a>ts_version |  version of the TypeScript compiler. Exactly one of `ts_version` or `ts_version_from` must be set.   |  `None` |
| <a id="rules_ts_dependencies-ts_integrity"></a>ts_integrity |  integrity hash for the npm package. By default, uses values mirrored into rules_ts. For example, to get the integrity of version 4.6.3 you could run `curl --silent https://registry.npmjs.org/typescript/4.6.3 \| jq -r '.dist.integrity'`   |  `None` |


# transpiler.md
# Transpiling TypeScript to JavaScript

The TypeScript compiler `tsc` can perform type-checking, transpilation to JavaScript, or both.
Type-checking is typically slow, and is really only possible with TypeScript, not with alternative tools.
Transpilation is mostly "erase the type syntax" and can be done well by a variety of tools.

`ts_project` allows us to split the work, with the following design goals:

- The user should only need a single BUILD.bazel declaration: "these are my TypeScript sources and their dependencies".
- Most developers have a working TypeScript Language Service in their editor, so they got type hinting before they ran `bazel`.
- Development activities which rely only on runtime code, like running tests or manually verifying behavior in a devserver, should not need to wait on type-checking.
- Type-checking still needs to be verified before checking in the code, but only needs to be as fast as a typical test.

Read more: https://blog.aspect.build/typescript-speedup

## ts_project#transpiler

The `transpiler` attribute of `ts_project` lets you select which tool produces the JavaScript outputs.
Starting in rules_ts 2.0, we require you to select one of these, as there is no good default for all users.

### [SWC](http://swc.rs) (recommended)

SWC is a fast transpiler, and the authors of rules_ts recommend using it.
This option results in the fastest development round-trip time, however it may have subtle
compatibility issues due to producing different JavaScript output than `tsc`.
See https://github.com/aspect-build/rules_ts/discussions/398 for known issues.

To switch to SWC, follow these steps:

1. Install a [recent release of rules_swc](https://github.com/aspect-build/rules_swc/releases)
2. Load `swc`. You can automate this by running:

    ```
    npx @bazel/buildozer 'fix movePackageToTop' //...:__pkg__
    npx @bazel/buildozer 'new_load @aspect_rules_swc//swc:defs.bzl swc' //...:__pkg__
    ```

3. In the simplest case you can skip passing attributes to swc (such as an `.swcrc` file).
   You can update your `ts_project` rules with this command:

    ```
    npx @bazel/buildozer 'set transpiler swc' //...:%ts_project
    ```

4. However, most codebases do rely on configuration options for SWC.
   First, [Synchronize settings with tsconfig.json](https://github.com/aspect-build/rules_swc/blob/main/docs/tsconfig.md) to get an `.swcrc` file,
   then use a pattern like the following to pass this option to `swc`:

        load("@aspect_rules_swc//swc:defs.bzl", "swc")
        load("@bazel_skylib//lib:partial.bzl", "partial")
    
        ts_project(
            ...
            transpiler = partial.make(swc, swcrc = "//:.swcrc"),
        )

6. Cleanup unused load statements:

    ```
    npx @bazel/buildozer 'fix unusedLoads' //...:__pkg__
    ```

### TypeScript [tsc](https://www.typescriptlang.org/docs/handbook/compiler-options.html)

`tsc` can do transpiling along with type-checking.
This is the simplest configuration without additional dependencies. However, it's also the slowest.

> Note that rules_ts used to recommend a "Persistent Worker" mode to keep the `tsc` process running
> as a background daemon, however this introduces correctness issues in the build and is no longer
> recommended. As of rules_ts 2.0, the "Persistent Worker" mode is no longer enabled by default.

To choose this option for a single `ts_project`, set `transpiler = "tsc"`.
You can run `npx @bazel/buildozer 'set transpiler "tsc"' //...:%ts_project` to set the attribute
on all `ts_project` rules.

If you use the default value `transpiler = None`, rules_ts will print an error.
You can simply disable this error for all targets in the build, behaving the same as rules_ts 1.x.
Just add this to `/.bazelrc``:

    # Use "tsc" as the transpiler when ts_project has no `transpiler` set.
    # Bazel 6.4 or greater: 'common' means 'any command that supports this flag'
    common --@aspect_rules_ts//ts:default_to_tsc_transpiler

    # Between Bazel 6.0 and 6.3, you need all of this, to avoid discarding the analysis cache:
    build --@aspect_rules_ts//ts:default_to_tsc_transpiler
    fetch --@aspect_rules_ts//ts:default_to_tsc_transpiler
    query --@aspect_rules_ts//ts:default_to_tsc_transpiler

    # Before Bazel 6.0, only the 'build' and 'fetch' lines work.

### Other Transpilers

The `transpiler` attribute accepts any rule or macro with this signature: `(name, srcs, **kwargs)`
The `**kwargs` attribute propagates the tags, visibility, and testonly attributes from `ts_project`.

See the examples/transpiler directory for a simple example using Babel, or
<https://github.com/aspect-build/bazel-examples/tree/main/ts_project_transpiler>
for a more complete example that also shows usage of SWC.

If you need to pass additional attributes to the transpiler rule such as `out_dir`, you can use a
[partial](https://github.com/bazelbuild/bazel-skylib/blob/main/lib/partial.bzl)
to bind those arguments at the "make site", then pass that partial to this attribute where it will be called with the remaining arguments.

The transpiler rule or macro is responsible for predicting and declaring outputs.
If you want to pre-declare the outputs (so that they can be addressed by a Bazel label, like `//path/to:index.js`)
then you should use a macro which calculates the predicted outputs and supplies them to a `ctx.attr.outputs` attribute
on the rule.

You may want to create a `ts_project` macro within your repository where your choice is setup,
then `load()` from your own macro rather than from `@aspect_rules_ts`.

## Macro expansion

When `no_emit`, `transpiler` or `declaration_transpiler` is set, then the `ts_project` macro expands to these targets:

- `[name]` - the default target which can be included in the `deps` of downstream rules.
    Note that it will successfully build *even if there are typecheck failures* because invoking `tsc` is not needed to produce the default outputs.
    This is considered a feature, as it allows you to have a faster development mode where type-checking is not on the critical path.
- `[name]_types` - provides typings (`.d.ts` files) as the default outputs.
    This target is not created if `no_emit` is set.
- `[name]_typecheck` - provides default outputs asserting type-checking has been run.
    Building this target always causes the typechecker to run.
- `[name]_typecheck_test` - a [`build_test`] target which simply depends on the `[name]_typecheck` target.
    This ensures that typechecking will be run under `bazel test` with [`--build_tests_only`].
-  Any additional target(s) the custom transpiler rule/macro produces.
    (For example, some rules produce one target per TypeScript input file.)

[`build_test`]: https://github.com/bazelbuild/bazel-skylib/blob/main/rules/build_test.bzl
[`--build_tests_only`]: https://docs.bazel.build/versions/main/user-manual.html#flag--build_tests_only

# troubleshooting.md
# Troubleshooting ts_project failures

`ts_project` is a thin wrapper around the [`tsc` compiler from TypeScript](https://www.typescriptlang.org/docs/handbook/compiler-options.html). Any code that works with `tsc` should work with `ts_project` with a few caveats:

- `ts_project` always produces some output files, or else Bazel would never run it.
    Therefore you shouldn't use it with TypeScript's `noEmit` option.
    If you only want to test that the code typechecks, use `tsc` directly.
    See [examples/typecheck_only](https://github.com/aspect-build/rules_ts/blob/main/examples/typecheck_only/BUILD.bazel)
- `ts_project` needs to know which `.ts` sources exist. If you have a tool which produces an "opaque" folder of
    `.ts` files and you cannot predict what they will be, then you can use `tsc` directly.
- Your tsconfig settings for `outDir` and `declarationDir` are ignored.
    Bazel requires that outputs are written beneath `bazel-out/[target architecture]/bin/path/to/package`.
- Bazel expects that each output is produced by a single rule.
    Thus if you have two `ts_project` rules with overlapping sources (the same `.ts` file
    appears in more than one) then you get an error about conflicting `.js` output
    files if you try to build both together.
    Worse, if you build them separately then the output directory will contain whichever
    one you happened to build most recently. This is highly discouraged.

You can often create a minimal repro of your problem outside of Bazel.
This is a good way to bisect whether your issue is purely with TypeScript, or there's something
Bazel-specific going on.

# Getting unstuck

The basic methodology for diagnosing problems is:

1. Gather information from Bazel about how `tsc` is spawned, like with `bazel aquery //path/to:my_ts_project`.
1. Reason about whether Bazel is providing all the inputs to `tsc` that you expect it to need. If not, the problem is with the dependencies.
1. Reason about whether Bazel has predicted the right outputs.
1. Gather information from TypeScript, typically by adding flags to the `args` attribute of the failing `ts_project`, as described below. Be prepared to deal with a large volume of data, like by writing the output to a file and using tools like an editor or unix utilities to analyze it.
1. Reason about whether TypeScript is looking for a file in the wrong place, or writing a file to the wrong place.

## Verbose mode

Running your build with `--@aspect_rules_ts//ts:verbose` causes the `ts_project` rule to enable several
flags for the TypeScript compiler. This produces a ton of output, so you'll probably want to 
redirect the stdout to a file that you can analyze with power tools.

## Problems with Persistent Workers

When Worker Support is enabled, we run `tsc` in a "watch mode" using the [Bazel Persistent Worker](https://bazel.build/remote/persistent) feature.
See the [`supports_workers`](https://docs.aspect.build/rules/aspect_rules_ts/docs/rules#supports_workers-1) attribute for docs on enabling this feature.

### Non-deterministic behavior

Persistent workers risk leaking state from one compilation to another, and you may still encounter such bugs, for example:
- removing a required types package from `deps` but the compilation still succeeds
- outputs created by a previous compilation are still produced even though the source file is deleted

You can confirm that it's a worker bug by running `bazel shutdown` and trying again. If that resolves the issue, it means that some state was leaking.

Please check for issues with persistent workers:
[persistent workers label](https://github.com/aspect-build/rules_ts/issues?q=label%3A%22persistent+workers%22)

### Not reproducible ts_project worker bugs
Not reproducible ts_project, a.k.a. state, bugs has been a challenge for anyone to diagnose and possibly, fix in ts_project. 
Not knowing what state the worker has been at when it falsely failed, or what went wrong along the way is hard to know.
For this, we introduced support  for `--worker_verbose` flag which prints a bunch of helpful logs to worker log file.

If you find yourself getting yelled at by ts_project falsely on occasion, drop `build --worker_verbose` to the `.bazelrc` file.
In addition to `--worker_verbose`, set `extendedDiagnostics` and `traceResolution` to true in the `tsconfig.json` file to log
additional information about how tsc reacts to events fed by worker protocol. 

```
{
    "compilerOptions": {
        "extendedDiagnostics": true,
        "traceResolution": true
    }
}
```

Next time, the ts_project yields false negative diagnostics messages, collect the logs files output_base and file a bug with the log files.

To collect log files run the command below at the workspace directory and attach the logs.tar file to issued file.
```
tar -cf logs.tar $(ls $(bazel info output_base)/bazel-workers/worker-*-TsProject.log)
```

This will help us understand what went wrong in your case, and hopefully implement a permanent fix for it.

## Which files should be emitted

TypeScript emits for each file in the "Program". `--listFiles` is a `tsc` flag to show what is in the program, and `--listEmittedFiles` shows what was written.

Upgrading to TypeScript 4.2 or greater can be helpful, because error messages were improved, and new flags were added.

TS 4.1:
```
error TS6059: File '/private/var/tmp/_bazel_alex.eagle/efa8e81f99c35c1227ef40a83cd29a26/execroot/examples_jest/ts/test/index.test.ts' is not under 'rootDir' '/private/var/tmp/_bazel_alex.eagle/efa8e81f99c35c1227ef40a83cd29a26/execroot/examples_jest/ts/src'. 'rootDir' is expected to contain all source files.
Target //ts/src:src failed to build
```

TS 4.2:
```
error TS6059: File '/private/var/tmp/_bazel_alex.eagle/efa8e81f99c35c1227ef40a83cd29a26/execroot/examples_jest/ts/test/index.test.ts' is not under 'rootDir' '/private/var/tmp/_bazel_alex.eagle/efa8e81f99c35c1227ef40a83cd29a26/execroot/examples_jest/ts/src'. 'rootDir' is expected to contain all source files.
  The file is in the program because:
    Matched by include pattern '**/*' in 'tsconfig.json'
```

The `--explainFiles` flag in TS 4.2 also gives information about why a given file was added to the program.

## Module not resolved

Use the `--traceResolution` flag to `tsc` to understand where TypeScript looked for the file.

Verify that there is actually a `.d.ts` file for TypeScript to resolve. Check that the dependency library has the `declarations = True` flag set, and that the `.d.ts` files appear where you expect them under `bazel-out`.

## Source maps missing

TypeScript source maps can be configured in various ways which may effect compatibility with Bazel or other tools.

First, the tsconfig `compilerOptions.sourceMap` and associated `ts_project(source_map)` must be set to `True` to enable source maps. If these are misaligned the the `ts_project(validate)` will report an error.

Second, if `compilerOptions.inlineSources` is set *not* set to `true` then the .ts source files must be manually included alongside the compiled .js.map files to ensure they are present at runtime.

The recommended approach is using `compilerOptions.inlineSources` set to `true` to place the original TypeScript source code inline within the .js.map files, or `compilerOptions.inlineSourceMap` set to `true` to place the full sourcemap and original TypeScript source code within .js files. This way no extra bazel configuration is required to ensure the TypeScript source code is available when debugging.

## NPM package type-checking failures

Strict dependencies and non-hoisted packages can cause type-checking failures when a package does not correctly declare TypeScript related npm dependencies. If a package exposes a dependency via TypeScript (such as publicly exporting a type from a dependency) then that dependency must be declared in the `package.json` `dependencies` in order for dependents to compile. Outside rules_ts with hoisted packages this *may* not be exposed if the missing dependency is declared in a parent or root package.json, however with strict dependencies in rules_js and bazel this will more likely be an issue.

Common solutions:

1. TypeScript `skipLibCheck` will avoid type-checking within dependencies where this errors may be occurring.
2. PNPM [packageExtensions](https://pnpm.io/package_json#pnpmpackageextensions) can be used to correct the dependencies of packages (normally by adding `@types/*` to the `dependencies` of the package).

Example type-checking errors due to use of `devDependencies`:

A React component from a library which does not declare `@types/react` as a dependency (JSX error):
```console
src/index.tsx(40,10): error TS2786: 'X' cannot be used as a JSX component.
  Its instance type 'X' is not a valid JSX element.
    Type 'X' is missing the following properties from type 'ElementClass': setState, forceUpdate, props, state, refs
```

A React component extending a component from a library which does not declare `@types/react` as a dependency (JSX error):
```console
src/index.tsx(55,12): error TS2786: 'Y' cannot be used as a JSX component.
  Its instance type 'Y' is not a valid JSX element.
    Type 'Y' is missing the following properties from type 'ElementClass': setState, forceUpdate, props, state, refs
```

Use of a library which does not declare `@types/express` as a dependency (type error):
```console
src/index.ts(2,25): error TS7016: Could not find a declaration file for module 'express'. '/bazel-out/.../node_modules/express/index.js' implicitly has an 'any' type.
  If the 'express' package actually exposes this module, consider sending a pull request to amend 'https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/express'
```

- Undeclared type-only dependencies (often `@types/*`).
    Type-checking is done at compile-time so type-only packages are normally npm `devDependencies`. However many packages contain type-definitions which expose those type-only package as part of their TypeScript API, this makes the types required for any downstream TypeScript compilation but the use of `devDependencies` means those packages are not available downstream.

## TS5033: EPERM 

```
error TS5033: Could not write file 'bazel-out/x64_windows-fastbuild/bin/setup_script.js': EPERM: operation not permitted, open 'bazel-out/x64_windows-fastbuild/bin/setup_script.js'.
```
This likely means two different Bazel targets tried to write the same output file. Use `--listFiles` to ask `tsc` to show what files are in the program. Try `--explainFiles` (see above) to see how they got there.

You may find that the program contained a `.ts` file rather than the corresponding `.d.ts` file.

Also see https://github.com/microsoft/TypeScript/issues/22208 - it's possible that TypeScript is resolving a `.ts` input where it should have used a `.d.ts` from another compilation.

## Webpack resolution failures when dropping ts-loader

The `compilerOptions.paths` property in `tsconfig.json` is often used for module names or simplifying import statements. A tool such as [`ts-loader`](https://github.com/TypeStrong/ts-loader) enables Webpack to understand such paths.

When typescript compilation is moved to a separate step under `rules_ts` this understanding within webpack may be lost since it only sees JavaScript inputs.

Possible solutions:
* `tsconfig-paths-webpack-plugin` webpack plugin for tsconfig paths (module names or just simplified import statements)
```
  resolve: {
    plugins: [new TsconfigPathsPlugin({ configFile: 'tsconfig.json' })]
  },
```

* Use pnpm workspaces and `npm_package`/`npm_link_package` in between the `ts_project` rule and the `webpack` rule, so that the loader finds files under the `node_modules` tree like it would with third-party npm packages.

# Troubleshooting performance issues 
Running your build with `--@aspect_rules_ts//ts:generate_tsc_trace` causes the `ts_project` rule to run with the `generate_trace` option enabled. This generates a profile that can be analyzed to understand TypeScript compilation performance. The trace files will be written in `bazel-bin/<package>/<target>_trace/`. To analyze it use ChromeDevTools or [@typescript/analyze-trace](https://www.npmjs.com/package/@typescript/analyze-trace). See the [TypeScript documentation](https://github.com/microsoft/TypeScript-wiki/blob/main/Performance-Tracing.md) for more information.
# proto.md


# Protocol Buffers and gRPC (UNSTABLE)

**UNSTABLE API**: contents of this page are not subject to our usual semver guarantees.
We may make breaking changes in any release.
Please try this API and provide feedback.
We intend to promote it to a stable API in a minor release, possibly as soon as v2.1.0.

`ts_proto_library` uses the Connect library from bufbuild, and supports both Web and Node.js:

- https://connectrpc.com/docs/web/getting-started
- https://connectrpc.com/docs/node/getting-started

This Bazel integration follows the "Local Generation" mechanism described at
https://connectrpc.com/docs/web/generating-code#local-generation,
using packages such as `@bufbuild/protoc-gen-es` and `@connectrpc/protoc-gen-connect-query`
as plugins to protoc.

The [aspect configure](https://docs.aspect.build/cli/commands/aspect_configure) command
auto-generates `ts_proto_library` rules as of the 5.7.2 release.
It's also possible to compile this library into your Gazelle binary.

Note: this API surface is not included in `defs.bzl` to avoid eager loads of rules_proto for all rules_ts users.

Installation
---------
- Allow users to choose other plugins. We intend to wait until http://github.com/bazelbuild/rules_proto supports protoc plugins.
- Allow users to control the output format. Currently it is hard-coded to `js+dts`, and the JS output uses ES Modules.

<a id="ts_proto_library"></a>

## ts_proto_library

<pre>
load("@aspect_rules_ts//ts:proto.bzl", "ts_proto_library")

ts_proto_library(<a href="#ts_proto_library-name">name</a>, <a href="#ts_proto_library-node_modules">node_modules</a>, <a href="#ts_proto_library-proto">proto</a>, <a href="#ts_proto_library-protoc_gen_options">protoc_gen_options</a>, <a href="#ts_proto_library-gen_connect_es">gen_connect_es</a>, <a href="#ts_proto_library-gen_connect_query">gen_connect_query</a>,
                 <a href="#ts_proto_library-gen_connect_query_service_mapping">gen_connect_query_service_mapping</a>, <a href="#ts_proto_library-copy_files">copy_files</a>, <a href="#ts_proto_library-proto_srcs">proto_srcs</a>, <a href="#ts_proto_library-files_to_copy">files_to_copy</a>, <a href="#ts_proto_library-kwargs">kwargs</a>)
</pre>

A macro to generate JavaScript code and TypeScript typings from .proto files.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="ts_proto_library-name"></a>name |  name of resulting ts_proto_library target   |  none |
| <a id="ts_proto_library-node_modules"></a>node_modules |  Label pointing to the linked node_modules target where @bufbuild/protoc-gen-es is linked, e.g. //:node_modules. Since the generated code depends on @bufbuild/protobuf, this package must also be linked. If `gen_connect_es = True` then @bufbuild/proto-gen-connect-es should be linked as well. If `gen_connect_query = True` then @bufbuild/proto-gen-connect-query should be linked as well.   |  none |
| <a id="ts_proto_library-proto"></a>proto |  the `proto_library` target that contains the .proto files to generate code for.   |  none |
| <a id="ts_proto_library-protoc_gen_options"></a>protoc_gen_options |  dict of protoc_gen_es options. See https://github.com/bufbuild/protobuf-es/tree/main/packages/protoc-gen-es#plugin-options   |  `{}` |
| <a id="ts_proto_library-gen_connect_es"></a>gen_connect_es |  [deprecated] whether protoc_gen_connect_es should generate grpc services, and therefore `*_connect.{js,d.ts}` should be written.   |  `False` |
| <a id="ts_proto_library-gen_connect_query"></a>gen_connect_query |  whether protoc_gen_connect_query should generate [TanStack Query](https://tanstack.com/query) clients, and therefore `*_connectquery.{js,d.ts}` should be written.   |  `False` |
| <a id="ts_proto_library-gen_connect_query_service_mapping"></a>gen_connect_query_service_mapping |  mapping from source proto file to the named RPC services that file contains. Needed to predict which files will be generated by gen_connect_query. See https://github.com/connectrpc/connect-query-es/tree/main/examples/react/basic/src/gen<br><br>For example, given `a.proto` which contains a service `Foo` and `b.proto` that contains a service `Bar`, the mapping would be `{"a.proto": ["Foo"], "b.proto": ["Bar"]}`   |  `{}` |
| <a id="ts_proto_library-copy_files"></a>copy_files |  whether to copy the resulting `.d.ts` files back to the source tree, for the editor to locate them.   |  `True` |
| <a id="ts_proto_library-proto_srcs"></a>proto_srcs |  the .proto files that are being generated. Repeats the `srcs` of the `proto_library` target. This is used only to determine a default for `files_to_copy`.   |  `None` |
| <a id="ts_proto_library-files_to_copy"></a>files_to_copy |  which files from the protoc output to copy. By default, performs a replacement on `proto_srcs` with the typical output filenames.   |  `None` |
| <a id="ts_proto_library-kwargs"></a>kwargs |  additional named arguments to the ts_proto_library rule   |  none |


# performance.md
# Performance

The primary method of improving build performance is essentially avoiding `tsc`, the TypeScript compiler, as much as possible.

There are 3 main goals of `ts_project`, where `tsc` is the traditional tool:
* transpile TypeScript to javascript files
* transpile TypeScript to declaration files
* type-check TypeScript

## Transpilers

The easiest and most common performance improvement is to use a transpiler other than `tsc` for the transpiling
of TypeScript to javascript files. See [transpiler.md](transpiler.md) for details.

## Isolated Typecheck

Isolating the type-check action from the transpiling actions can also improve performance.

The tsconfig `compilerOptions.isolatedDeclarations` option ensures TypeScript code can be transpiled
to declaration files without the need for dependencies to be present.

The `ts_project(isolated_typecheck)` option can take advantage of `isolatedDeclarations` by separating the
transpiling vs type-checking into separate bazel actions. The transpiling of TypeScript files with `isolatedDeclarations`
can be done without blocking waiting for dependencies, greatly increasing parallelization of declaration file creation.
Declaration files being created faster then allows the type-checking to start sooner.

### When to use `isolated_typecheck`

It is not always possible or convenient to use the TypeScript `isolatedDeclarations` option, especially when it requires
significant code changes. However it may be worth enabling `isolatedDeclarations` for a subset of projects that are bottlenecks
in the build graph.

Bottlenecks in the build graph are normally targets with a lot of dependencies (including transitive), while also being depended
on by a lot of targets (including transitive).

In this example scenario C is a bottleneck in the build graph:
```
┌─────┐             ┌─────┐        
│  A  ┼────┐    ┌───►  D  │        
└─────┘    │    │   └─────┘        
┌─────┐   ┌▼────┤   ┌─────┐ ┌─────┐
│  B  ┼───►  C  ┼───►  E  ┼─►  F  │
└─────┘   └─────┘   └─────┘ └─────┘
```

Without `isolated_typecheck` transpiling declaration files follows the dependency graph. Project (A) and (B) require declaration
files outputted from (C). Project (C) requires declaration files outputted from (D), (E), and (F) etc.

With `isolated_typecheck` on module C more can be parallelized:
```
┌─────┐          
│  A  ┼────┐     
└─────┘    │     
┌─────┐   ┌▼────┐
│  B  ┼───►  C  │
└─────┘   └─────┘
┌─────┐          
│  D  │          
└─────┘          
┌─────┐   ┌─────┐  
│  E  ┼───►  F  │  
└─────┘   └─────┘  
```

The additional parallelization will also lead to type-checking starting sooner.

# tsconfig.md
# Configuring TypeScript

TypeScript provides "compiler options" which interact with how Bazel builds and type-checks code.

## General guidance

Keep a `tsconfig.json` file at the root of your TypeScript sources tree, as an ancestor of all TypeScript files.
This should have your standard settings that apply to all code in the package or repository.
This ensures that editors agree with rules_ts, and that you have minimal repetition of settings which can get diverged over time.

## Mirroring tsconfig settings

`ts_project` needs to know some of the values from tsconfig.json.
This is so we can mimic the semantics of `tsc` for things like which files are included in the program, and to predict output locations.

These attributes are named as snake-case equivalents of the tsconfig.json settings.
For example, [`outDir`](https://www.typescriptlang.org/tsconfig#outDir) is translated to `out_dir`.

The `ts_project` macro expands to include a validation action, which uses the TypeScript API to load the `tsconfig.json` file (along with any that it `extends`) and compare these values to attributes on the `ts_project` rule.
It produces [buildozer] commands to correct the BUILD.bazel file when they disagree.

[buildozer]: https://github.com/bazelbuild/buildtools/blob/master/buildozer/README.md

## Locations of tsconfig.json files

You can use a single `tsconfig.json` file for a repository.
Since rules_js expects files to appear in the `bazel-out` tree, the common pattern is:

1. In the `BUILD.bazel` file next to `tsconfig.json`, expose it using a `ts_config` rule:

```starlark
load("@aspect_rules_ts//ts:defs.bzl", "ts_config")

ts_config(
    name = "tsconfig",
    src = "tsconfig.json",
    visibility = [":__subpackages__"],
)
```

2. In child packages, set the `tsconfig` attribute of `ts_project` rules in subpackages to point to this rule.

```
load("@aspect_rules_ts//ts:defs.bzl", "ts_config")

ts_project(
    ...
    tsconfig = "//my_root:tsconfig",
)
```

You can also use nested `tsconfig.json` files. Typically you want these to inherit common settings from the parent, so use the [`extends`](https://www.typescriptlang.org/tsconfig#extends) feature in the `tsconfig.json` file. Then you'll need to tell Bazel about this dependency structure, so add a `deps` list to `ts_config` and repeat the files there.

## Inline (generated) tsconfig

The `ts_project#tsconfig` attribute accepts a dictionary.
If supplied, this dictionary is converted into a JSON file.
It should have a top-level `compilerOptions` key, matching the tsconfig file JSON schema.

Since its location differs from `tsconfig.json` in the source tree, and TypeScript
resolves paths in `tsconfig.json` relative to its location, some paths must be
written into the generated file:

- each file in srcs will be converted to a relative path in the `files` section.
- the `extends` attribute will be converted to a relative path

The generated `tsconfig.json` file can be inspected in `bazel-out`.

> Remember that editors need to know some of the tsconfig settings, so if you rely
> exclusively on this approach, you may find that the editor skew affects development.

You can mix-and-match values in the dictionary with attributes.
Values in the dictionary take precedence over those in the attributes,
and conflicts between them are not validated. For example, in

```starlark
ts_project(
    name = "which",
    tsconfig = {
        "compilerOptions": {
            "declaration": True,
            "rootDir": "subdir",
        },
    },
    out_dir = "dist",
    root_dir = "other",
)
```

the value `subdir` will be used by `tsc`, and `other` will be silently ignored.
Both `outDir: dist` and `declaration: true` will be used.

As with any Starlark code, you could define this dictionary in a central location and load it as a symbol into your BUILD.bazel files.
            
# rules.md


# Public API for TypeScript rules

The most commonly used is the [ts_project](#ts_project) macro which accepts TypeScript sources as
inputs and produces JavaScript or declaration (.d.ts) outputs.

<a id="ts_config"></a>

## ts_config

<pre>
load("@aspect_rules_ts//ts:defs.bzl", "ts_config")

ts_config(<a href="#ts_config-name">name</a>, <a href="#ts_config-deps">deps</a>, <a href="#ts_config-src">src</a>)
</pre>

Allows a tsconfig.json file to extend another file.

Normally, you just give a single `tsconfig.json` file as the tsconfig attribute
of a `ts_library` or `ts_project` rule. However, if your `tsconfig.json` uses the `extends`
feature from TypeScript, then the Bazel implementation needs to know about that
extended configuration file as well, to pass them both to the TypeScript compiler.

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="ts_config-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="ts_config-deps"></a>deps |  Additional tsconfig.json files referenced via extends   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="ts_config-src"></a>src |  The tsconfig.json file passed to the TypeScript compiler   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |

<a id="ts_project_rule"></a>

## ts_project_rule

<pre>
load("@aspect_rules_ts//ts:defs.bzl", "ts_project_rule")

ts_project_rule(<a href="#ts_project_rule-name">name</a>, <a href="#ts_project_rule-deps">deps</a>, <a href="#ts_project_rule-srcs">srcs</a>, <a href="#ts_project_rule-data">data</a>, <a href="#ts_project_rule-allow_js">allow_js</a>, <a href="#ts_project_rule-args">args</a>, <a href="#ts_project_rule-assets">assets</a>, <a href="#ts_project_rule-buildinfo_out">buildinfo_out</a>, <a href="#ts_project_rule-composite">composite</a>,
                <a href="#ts_project_rule-declaration">declaration</a>, <a href="#ts_project_rule-declaration_dir">declaration_dir</a>, <a href="#ts_project_rule-declaration_map">declaration_map</a>, <a href="#ts_project_rule-declaration_transpile">declaration_transpile</a>,
                <a href="#ts_project_rule-emit_declaration_only">emit_declaration_only</a>, <a href="#ts_project_rule-extends">extends</a>, <a href="#ts_project_rule-generate_trace">generate_trace</a>, <a href="#ts_project_rule-incremental">incremental</a>,
                <a href="#ts_project_rule-is_typescript_5_or_greater">is_typescript_5_or_greater</a>, <a href="#ts_project_rule-isolated_typecheck">isolated_typecheck</a>, <a href="#ts_project_rule-js_outs">js_outs</a>, <a href="#ts_project_rule-map_outs">map_outs</a>, <a href="#ts_project_rule-no_emit">no_emit</a>, <a href="#ts_project_rule-out_dir">out_dir</a>,
                <a href="#ts_project_rule-preserve_jsx">preserve_jsx</a>, <a href="#ts_project_rule-pretranspiled_dts">pretranspiled_dts</a>, <a href="#ts_project_rule-pretranspiled_js">pretranspiled_js</a>, <a href="#ts_project_rule-resolve_json_module">resolve_json_module</a>, <a href="#ts_project_rule-resource_set">resource_set</a>,
                <a href="#ts_project_rule-root_dir">root_dir</a>, <a href="#ts_project_rule-source_map">source_map</a>, <a href="#ts_project_rule-supports_workers">supports_workers</a>, <a href="#ts_project_rule-transpile">transpile</a>, <a href="#ts_project_rule-ts_build_info_file">ts_build_info_file</a>, <a href="#ts_project_rule-tsc">tsc</a>,
                <a href="#ts_project_rule-tsc_worker">tsc_worker</a>, <a href="#ts_project_rule-tsconfig">tsconfig</a>, <a href="#ts_project_rule-typing_maps_outs">typing_maps_outs</a>, <a href="#ts_project_rule-typings_outs">typings_outs</a>, <a href="#ts_project_rule-validate">validate</a>, <a href="#ts_project_rule-validator">validator</a>)
</pre>

Implementation rule behind the ts_project macro.
Most users should use [ts_project](#ts_project) instead.

This skips conveniences like validation of the tsconfig attributes, default settings
for srcs and tsconfig, and pre-declaring output files.

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="ts_project_rule-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="ts_project_rule-deps"></a>deps |  List of targets that produce TypeScript typings (`.d.ts` files)<br><br>Follows the same runfiles semantics as `js_library` `deps` attribute. See https://docs.aspect.build/rulesets/aspect_rules_js/docs/js_library#deps for more info.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="ts_project_rule-srcs"></a>srcs |  TypeScript source files   | <a href="https://bazel.build/concepts/labels">List of labels</a> | required |  |
| <a id="ts_project_rule-data"></a>data |  Runtime dependencies to include in binaries/tests that depend on this target.<br><br>Follows the same semantics as `js_library` `data` attribute. See https://docs.aspect.build/rulesets/aspect_rules_js/docs/js_library#data for more info.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="ts_project_rule-allow_js"></a>allow_js |  https://www.typescriptlang.org/tsconfig#allowJs   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-args"></a>args |  https://www.typescriptlang.org/docs/handbook/compiler-options.html   | List of strings | optional |  `[]`  |
| <a id="ts_project_rule-assets"></a>assets |  Files which are needed by a downstream build step such as a bundler.<br><br>See more details on the `assets` parameter of the `ts_project` macro.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="ts_project_rule-buildinfo_out"></a>buildinfo_out |  Location in bazel-out where tsc will write a `.tsbuildinfo` file   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="ts_project_rule-composite"></a>composite |  https://www.typescriptlang.org/tsconfig#composite   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-declaration"></a>declaration |  https://www.typescriptlang.org/tsconfig#declaration   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-declaration_dir"></a>declaration_dir |  https://www.typescriptlang.org/tsconfig#declarationDir   | String | optional |  `""`  |
| <a id="ts_project_rule-declaration_map"></a>declaration_map |  https://www.typescriptlang.org/tsconfig#declarationMap   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-declaration_transpile"></a>declaration_transpile |  Whether tsc should be used to produce .d.ts outputs   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-emit_declaration_only"></a>emit_declaration_only |  https://www.typescriptlang.org/tsconfig#emitDeclarationOnly   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-extends"></a>extends |  https://www.typescriptlang.org/tsconfig#extends   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="ts_project_rule-generate_trace"></a>generate_trace |  https://www.typescriptlang.org/tsconfig/#generateTrace   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-incremental"></a>incremental |  https://www.typescriptlang.org/tsconfig#incremental   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-is_typescript_5_or_greater"></a>is_typescript_5_or_greater |  Whether TypeScript version is >= 5.0.0   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-isolated_typecheck"></a>isolated_typecheck |  Whether type-checking should be a separate action.<br><br>This allows the transpilation action to run without waiting for typings from dependencies.<br><br>Requires a minimum version of typescript 5.6 for the [noCheck](https://www.typescriptlang.org/tsconfig#noCheck) flag which is automatically set on the transpilation action when the typecheck action is isolated.<br><br>Requires [isolatedDeclarations](https://www.typescriptlang.org/tsconfig#isolatedDeclarations) to be set so that declarations can be emitted without dependencies. The use of `isolatedDeclarations` may require significant changes to your codebase and should be done as a pre-requisite to enabling `isolated_typecheck`.   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-js_outs"></a>js_outs |  Locations in bazel-out where tsc will write `.js` files   | List of labels | optional |  `[]`  |
| <a id="ts_project_rule-map_outs"></a>map_outs |  Locations in bazel-out where tsc will write `.js.map` files   | List of labels | optional |  `[]`  |
| <a id="ts_project_rule-no_emit"></a>no_emit |  https://www.typescriptlang.org/tsconfig#noEmit   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-out_dir"></a>out_dir |  https://www.typescriptlang.org/tsconfig#outDir   | String | optional |  `""`  |
| <a id="ts_project_rule-preserve_jsx"></a>preserve_jsx |  https://www.typescriptlang.org/tsconfig#jsx   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-pretranspiled_dts"></a>pretranspiled_dts |  Externally transpiled .d.ts to be included in output providers   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="ts_project_rule-pretranspiled_js"></a>pretranspiled_js |  Externally transpiled .js to be included in output providers   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="ts_project_rule-resolve_json_module"></a>resolve_json_module |  https://www.typescriptlang.org/tsconfig#resolveJsonModule   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-resource_set"></a>resource_set |  A predefined function used as the resource_set for actions.<br><br>Used with --experimental_action_resource_set to reserve more RAM/CPU, preventing Bazel overscheduling resource-intensive actions.<br><br>By default, Bazel allocates 1 CPU and 250M of RAM. https://github.com/bazelbuild/bazel/blob/058f943037e21710837eda9ca2f85b5f8538c8c5/src/main/java/com/google/devtools/build/lib/actions/AbstractAction.java#L77   | String | optional |  `"default"`  |
| <a id="ts_project_rule-root_dir"></a>root_dir |  https://www.typescriptlang.org/tsconfig#rootDir   | String | optional |  `""`  |
| <a id="ts_project_rule-source_map"></a>source_map |  https://www.typescriptlang.org/tsconfig#sourceMap   | Boolean | optional |  `False`  |
| <a id="ts_project_rule-supports_workers"></a>supports_workers |  Whether to use a custom `tsc` compiler which understands Bazel's persistent worker protocol.<br><br>See the docs for `supports_workers` on the [`ts_project`](#ts_project-supports_workers) macro.   | Integer | optional |  `0`  |
| <a id="ts_project_rule-transpile"></a>transpile |  Whether tsc should be used to produce .js outputs<br><br>Values are: - -1: Error if --@aspect_rules_ts//ts:default_to_tsc_transpiler not set, otherwise transpile - 0: Do not transpile - 1: Transpile   | Integer | optional |  `-1`  |
| <a id="ts_project_rule-ts_build_info_file"></a>ts_build_info_file |  https://www.typescriptlang.org/tsconfig#tsBuildInfoFile   | String | optional |  `""`  |
| <a id="ts_project_rule-tsc"></a>tsc |  TypeScript compiler binary   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |
| <a id="ts_project_rule-tsc_worker"></a>tsc_worker |  TypeScript compiler worker binary   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |
| <a id="ts_project_rule-tsconfig"></a>tsconfig |  tsconfig.json file, see https://www.typescriptlang.org/tsconfig   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |
| <a id="ts_project_rule-typing_maps_outs"></a>typing_maps_outs |  Locations in bazel-out where tsc will write `.d.ts.map` files   | List of labels | optional |  `[]`  |
| <a id="ts_project_rule-typings_outs"></a>typings_outs |  Locations in bazel-out where tsc will write `.d.ts` files   | List of labels | optional |  `[]`  |
| <a id="ts_project_rule-validate"></a>validate |  whether to add a Validation Action to verify the other attributes match settings in the tsconfig.json file   | Boolean | optional |  `True`  |
| <a id="ts_project_rule-validator"></a>validator |  -   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |

<a id="TsConfigInfo"></a>

## TsConfigInfo

<pre>
load("@aspect_rules_ts//ts:defs.bzl", "TsConfigInfo")

TsConfigInfo(<a href="#TsConfigInfo-deps">deps</a>)
</pre>

Provides TypeScript configuration, in the form of a tsconfig.json file
along with any transitively referenced tsconfig.json files chained by the
"extends" feature

**FIELDS**

| Name  | Description |
| :------------- | :------------- |
| <a id="TsConfigInfo-deps"></a>deps |  all tsconfig.json files needed to configure TypeScript    |

<a id="ts_project"></a>

## ts_project

<pre>
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")

ts_project(<a href="#ts_project-name">name</a>, <a href="#ts_project-tsconfig">tsconfig</a>, <a href="#ts_project-srcs">srcs</a>, <a href="#ts_project-args">args</a>, <a href="#ts_project-data">data</a>, <a href="#ts_project-deps">deps</a>, <a href="#ts_project-assets">assets</a>, <a href="#ts_project-extends">extends</a>, <a href="#ts_project-allow_js">allow_js</a>, <a href="#ts_project-isolated_typecheck">isolated_typecheck</a>,
           <a href="#ts_project-declaration">declaration</a>, <a href="#ts_project-source_map">source_map</a>, <a href="#ts_project-declaration_map">declaration_map</a>, <a href="#ts_project-resolve_json_module">resolve_json_module</a>, <a href="#ts_project-preserve_jsx">preserve_jsx</a>, <a href="#ts_project-composite">composite</a>,
           <a href="#ts_project-incremental">incremental</a>, <a href="#ts_project-no_emit">no_emit</a>, <a href="#ts_project-emit_declaration_only">emit_declaration_only</a>, <a href="#ts_project-transpiler">transpiler</a>, <a href="#ts_project-declaration_transpiler">declaration_transpiler</a>,
           <a href="#ts_project-ts_build_info_file">ts_build_info_file</a>, <a href="#ts_project-generate_trace">generate_trace</a>, <a href="#ts_project-tsc">tsc</a>, <a href="#ts_project-tsc_worker">tsc_worker</a>, <a href="#ts_project-validate">validate</a>, <a href="#ts_project-validator">validator</a>, <a href="#ts_project-declaration_dir">declaration_dir</a>,
           <a href="#ts_project-out_dir">out_dir</a>, <a href="#ts_project-root_dir">root_dir</a>, <a href="#ts_project-supports_workers">supports_workers</a>, <a href="#ts_project-kwargs">kwargs</a>)
</pre>

Compiles one TypeScript project using `tsc --project`.

This is a drop-in replacement for the `tsc` rule automatically generated for the "typescript"
package, typically loaded from `@npm//typescript:package_json.bzl`.
Unlike bare `tsc`, this rule understands the Bazel interop mechanism (Providers)
so that this rule works with others that produce or consume TypeScript typings (`.d.ts` files).

One of the benefits of using ts_project is that it understands the [Bazel Worker Protocol]
which makes the overhead of starting the compiler be a one-time cost.
Worker mode is on by default to speed up build and typechecking process.

Some TypeScript options affect which files are emitted, and Bazel needs to predict these ahead-of-time.
As a result, several options from the tsconfig file must be mirrored as attributes to ts_project.
A validation action is run to help ensure that these are correctly mirrored.
See https://www.typescriptlang.org/tsconfig for a listing of the TypeScript options.

If you have problems getting your `ts_project` to work correctly, read the dedicated
[troubleshooting guide](/docs/troubleshooting.md).

[Bazel Worker Protocol]: https://bazel.build/remote/persistent

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="ts_project-name"></a>name |  a name for this target   |  none |
| <a id="ts_project-tsconfig"></a>tsconfig |  Label of the tsconfig.json file to use for the compilation. To support "chaining" of more than one extended config, this label could be a target that provides `TsConfigInfo` such as `ts_config`.<br><br>By default, if a "tsconfig.json" file is in the same folder with the ts_project rule, it is used.<br><br>Instead of a label, you can pass a dictionary matching the JSON schema.<br><br>See [docs/tsconfig.md](/docs/tsconfig.md) for detailed information.   |  `None` |
| <a id="ts_project-srcs"></a>srcs |  List of labels of TypeScript source files to be provided to the compiler.<br><br>If absent, the default is set as follows:<br><br>- Include all TypeScript files in the package, recursively. - If `allow_js` is set, include all JavaScript files in the package as well. - If `resolve_json_module` is set, include all JSON files in the package,   but exclude `package.json`, `package-lock.json`, and `tsconfig*.json`.   |  `None` |
| <a id="ts_project-args"></a>args |  List of strings of additional command-line arguments to pass to tsc. See https://www.typescriptlang.org/docs/handbook/compiler-options.html#compiler-options Typically useful arguments for debugging are `--listFiles` and `--listEmittedFiles`.   |  `[]` |
| <a id="ts_project-data"></a>data |  Files needed at runtime by binaries or tests that transitively depend on this target. See https://bazel.build/reference/be/common-definitions#typical-attributes   |  `[]` |
| <a id="ts_project-deps"></a>deps |  List of targets that produce TypeScript typings (`.d.ts` files)<br><br>If this list contains linked npm packages, npm package store targets or other targets that provide `JsInfo`, `NpmPackageStoreInfo` providers are gathered from `JsInfo`. This is done directly from the `npm_package_store_deps` field of these. For linked npm package targets, the underlying `npm_package_store` target(s) that back the links is used. Gathered `NpmPackageStoreInfo` providers are propagated to the direct dependencies of downstream linked `npm_package` targets.<br><br>NB: Linked npm package targets that are "dev" dependencies do not forward their underlying `npm_package_store` target(s) through `npm_package_store_deps` and will therefore not be propagated to the direct dependencies of downstream linked `npm_package` targets. npm packages that come in from `npm_translate_lock` are considered "dev" dependencies if they are have `dev: true` set in the pnpm lock file. This should be all packages that are only listed as "devDependencies" in all `package.json` files within the pnpm workspace. This behavior is intentional to mimic how `devDependencies` work in published npm packages.   |  `[]` |
| <a id="ts_project-assets"></a>assets |  Files which are needed by a downstream build step such as a bundler.<br><br>These files are **not** included as inputs to any actions spawned by `ts_project`. They are not transpiled, and are not visible to the type-checker. Instead, these files appear among the *outputs* of this target.<br><br>A typical use is when your TypeScript code has an import that TS itself doesn't understand such as<br><br>`import './my.scss'`<br><br>and the type-checker allows this because you have an "ambient" global type declaration like<br><br>`declare module '*.scss' { ... }`<br><br>A bundler like webpack will expect to be able to resolve the `./my.scss` import to a file and doesn't care about the typing declaration. A bundler runs as a build step, so it does not see files included in the `data` attribute.<br><br>Note that `data` is used for files that are resolved by some binary, including a test target. Behind the scenes, `data` populates Bazel's Runfiles object in `DefaultInfo`, while this attribute populates the `transitive_sources` of the `JsInfo`.   |  `[]` |
| <a id="ts_project-extends"></a>extends |  Label of the tsconfig file referenced in the `extends` section of tsconfig To support "chaining" of more than one extended config, this label could be a target that provdes `TsConfigInfo` such as `ts_config`.   |  `None` |
| <a id="ts_project-allow_js"></a>allow_js |  Whether TypeScript will read .js and .jsx files. When used with `declaration`, TypeScript will generate `.d.ts` files from `.js` files.   |  `False` |
| <a id="ts_project-isolated_typecheck"></a>isolated_typecheck |  Whether to type-check asynchronously as a separate bazel action. Requires https://devblogs.microsoft.com/typescript/announcing-typescript-5-6/#the---nocheck-option6 Requires https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-5.html#isolated-declarations   |  `False` |
| <a id="ts_project-declaration"></a>declaration |  Whether the `declaration` bit is set in the tsconfig. Instructs Bazel to expect a `.d.ts` output for each `.ts` source.   |  `False` |
| <a id="ts_project-source_map"></a>source_map |  Whether the `sourceMap` bit is set in the tsconfig. Instructs Bazel to expect a `.js.map` output for each `.ts` source.   |  `False` |
| <a id="ts_project-declaration_map"></a>declaration_map |  Whether the `declarationMap` bit is set in the tsconfig. Instructs Bazel to expect a `.d.ts.map` output for each `.ts` source.   |  `False` |
| <a id="ts_project-resolve_json_module"></a>resolve_json_module |  Boolean; specifies whether TypeScript will read .json files. If set to True or False and tsconfig is a dict, resolveJsonModule is set in the generated config file. If set to None and tsconfig is a dict, resolveJsonModule is unset in the generated config and typescript default or extended tsconfig value will be load bearing.   |  `None` |
| <a id="ts_project-preserve_jsx"></a>preserve_jsx |  Whether the `jsx` value is set to "preserve" in the tsconfig. Instructs Bazel to expect a `.jsx` or `.jsx.map` output for each `.tsx` source.   |  `False` |
| <a id="ts_project-composite"></a>composite |  Whether the `composite` bit is set in the tsconfig. Instructs Bazel to expect a `.tsbuildinfo` output and a `.d.ts` output for each `.ts` source.   |  `False` |
| <a id="ts_project-incremental"></a>incremental |  Whether the `incremental` bit is set in the tsconfig. Instructs Bazel to expect a `.tsbuildinfo` output.   |  `False` |
| <a id="ts_project-no_emit"></a>no_emit |  Whether the `noEmit` bit is set in the tsconfig. Instructs Bazel *not* to expect any outputs.   |  `False` |
| <a id="ts_project-emit_declaration_only"></a>emit_declaration_only |  Whether the `emitDeclarationOnly` bit is set in the tsconfig. Instructs Bazel *not* to expect `.js` or `.js.map` outputs for `.ts` sources.   |  `False` |
| <a id="ts_project-transpiler"></a>transpiler |  A custom transpiler tool to run that produces the JavaScript outputs instead of `tsc`.<br><br>Under `--@aspect_rules_ts//ts:default_to_tsc_transpiler`, the default is to use `tsc` to produce `.js` outputs in the same action that does the type-checking to produce `.d.ts` outputs. This is the simplest configuration, however `tsc` is slower than alternatives. It also means developers must wait for the type-checking in the developer loop.<br><br>Without `--@aspect_rules_ts//ts:default_to_tsc_transpiler`, an explicit value must be set. This may be the string `"tsc"` to explicitly choose `tsc`, just like the default above.<br><br>It may also be any rule or macro with this signature: `(name, srcs, **kwargs)`<br><br>If JavaScript outputs are configured to not be emitted the custom transpiler will not be used, such as when `no_emit = True` or `emit_declaration_only = True`.<br><br>See [docs/transpiler.md](/docs/transpiler.md) for more details.   |  `None` |
| <a id="ts_project-declaration_transpiler"></a>declaration_transpiler |  A custom transpiler tool to run that produces the TypeScript declaration outputs instead of `tsc`.<br><br>It may be any rule or macro with this signature: `(name, srcs, **kwargs)`<br><br>If TypeScript declaration outputs are configured to not be emitted the custom declaration transpiler will not be used, such as when `no_emit = True` or `declaration = False`.<br><br>See [docs/transpiler.md](/docs/transpiler.md) for more details.   |  `None` |
| <a id="ts_project-ts_build_info_file"></a>ts_build_info_file |  The user-specified value of `tsBuildInfoFile` from the tsconfig. Helps Bazel to predict the path where the .tsbuildinfo output is written.   |  `None` |
| <a id="ts_project-generate_trace"></a>generate_trace |  Whether to generate a trace file for TypeScript compiler performance analysis. When enabled, creates a trace directory containing performance tracing information that can be loaded in chrome://tracing. Use the `--@aspect_rules_ts//ts:generate_tsc_trace` flag to enable this by default.   |  `None` |
| <a id="ts_project-tsc"></a>tsc |  Label of the TypeScript compiler binary to run. This allows you to use a custom API-compatible compiler in place of the regular `tsc` such as a custom `js_binary` or Angular's `ngc`. compatible with it such as Angular's `ngc`.<br><br>See examples of use in [examples/custom_compiler](https://github.com/aspect-build/rules_ts/blob/main/examples/custom_compiler/BUILD.bazel)   |  `"@npm_typescript//:tsc"` |
| <a id="ts_project-tsc_worker"></a>tsc_worker |  Label of a custom TypeScript compiler binary which understands Bazel's persistent worker protocol.   |  `"@npm_typescript//:tsc_worker"` |
| <a id="ts_project-validate"></a>validate |  Whether to check that the dependencies are valid and the tsconfig JSON settings match the attributes on this target. Set this to `False` to skip running our validator, in case you have a legitimate reason for these to differ, e.g. you have a setting enabled just for the editor but you want different behavior when Bazel runs `tsc`.   |  `True` |
| <a id="ts_project-validator"></a>validator |  Label of the tsconfig validator to run when `validate = True`.   |  `"@npm_typescript//:validator"` |
| <a id="ts_project-declaration_dir"></a>declaration_dir |  String specifying a subdirectory under the bazel-out folder where generated declaration outputs are written. Equivalent to the TypeScript --declarationDir option. By default declarations are written to the out_dir.   |  `None` |
| <a id="ts_project-out_dir"></a>out_dir |  String specifying a subdirectory under the bazel-out folder where outputs are written. Equivalent to the TypeScript --outDir option.<br><br>Note that Bazel always requires outputs be written under a subdirectory matching the input package, so if your rule appears in `path/to/my/package/BUILD.bazel` and out_dir = "foo" then the .js files will appear in `bazel-out/[arch]/bin/path/to/my/package/foo/*.js`.<br><br>By default the out_dir is the package's folder under bazel-out.   |  `None` |
| <a id="ts_project-root_dir"></a>root_dir |  String specifying a subdirectory under the input package which should be consider the root directory of all the input files. Equivalent to the TypeScript --rootDir option. By default it is '.', meaning the source directory where the BUILD file lives.   |  `None` |
| <a id="ts_project-supports_workers"></a>supports_workers |  Whether the "Persistent Worker" protocol is enabled. This uses a custom `tsc` compiler to make rebuilds faster. Note that this causes some known correctness bugs, see https://docs.aspect.build/rules/aspect_rules_ts/docs/troubleshooting. We do not intend to fix these bugs.<br><br>Worker mode can be enabled for all `ts_project`s in a build with the global `--@aspect_rules_ts//ts:supports_workers` flag. To enable worker mode for all builds in the workspace, add `build --@aspect_rules_ts//ts:supports_workers` to the .bazelrc.<br><br>This is a "tri-state" attribute, accepting values `[-1, 0, 1]`. The behavior is:<br><br>- `-1`: use the value of the global `--@aspect_rules_ts//ts:supports_workers` flag. - `0`: Override the global flag, disabling workers for this target. - `1`: Override the global flag, enabling workers for this target.   |  `-1` |
| <a id="ts_project-kwargs"></a>kwargs |  passed through to underlying [`ts_project_rule`](#ts_project_rule), eg. `visibility`, `tags`   |  none |

