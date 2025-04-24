# npm_translate_lock.md


Repository rule to fetch npm packages for a lockfile.

Load this with,

```starlark
load("@aspect_rules_js//npm:repositories.bzl", "npm_translate_lock")
```

These use Bazel's downloader to fetch the packages.
You can use this to redirect all fetches through a store like Artifactory.

See <https://blog.aspect.build/configuring-bazels-downloader> for more info about how it works
and how to configure it.

[`npm_translate_lock`](#npm_translate_lock) is the primary user-facing API.
It uses the lockfile format from [pnpm](https://pnpm.io/motivation) because it gives us reliable
semantics for how to dynamically lay out `node_modules` trees on disk in bazel-out.

To create `pnpm-lock.yaml`, consider using [`pnpm import`](https://pnpm.io/cli/import)
to preserve the versions pinned by your existing `package-lock.json` or `yarn.lock` file.

If you don't have an existing lock file, you can run `npx pnpm install --lockfile-only`.

Advanced users may want to directly fetch a package from npm rather than start from a lockfile,
[`npm_import`](./npm_import) does this.

<a id="list_patches"></a>

## list_patches

<pre>
list_patches(<a href="#list_patches-name">name</a>, <a href="#list_patches-out">out</a>, <a href="#list_patches-include_patterns">include_patterns</a>, <a href="#list_patches-exclude_package_contents">exclude_package_contents</a>)
</pre>

Write a file containing a list of all patches in the current folder to the source tree.

Use this together with the `verify_patches` attribute of `npm_translate_lock` to verify
that all patches in a patch folder are included. This macro stamps a test to ensure the
file stays up to date.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="list_patches-name"></a>name |  Name of the target   |  none |
| <a id="list_patches-out"></a>out |  Name of file to write to the source tree. If unspecified, `name` is used   |  `None` |
| <a id="list_patches-include_patterns"></a>include_patterns |  Patterns to pass to a glob of patch files   |  `["*.diff", "*.patch"]` |
| <a id="list_patches-exclude_package_contents"></a>exclude_package_contents |  Patterns to ignore in a glob of patch files   |  `[]` |

<a id="npm_translate_lock"></a>

## npm_translate_lock

<pre>
npm_translate_lock(<a href="#npm_translate_lock-name">name</a>, <a href="#npm_translate_lock-pnpm_lock">pnpm_lock</a>, <a href="#npm_translate_lock-npm_package_lock">npm_package_lock</a>, <a href="#npm_translate_lock-yarn_lock">yarn_lock</a>, <a href="#npm_translate_lock-update_pnpm_lock">update_pnpm_lock</a>,
                   <a href="#npm_translate_lock-node_toolchain_prefix">node_toolchain_prefix</a>, <a href="#npm_translate_lock-yq_toolchain_prefix">yq_toolchain_prefix</a>, <a href="#npm_translate_lock-preupdate">preupdate</a>, <a href="#npm_translate_lock-npmrc">npmrc</a>, <a href="#npm_translate_lock-use_home_npmrc">use_home_npmrc</a>, <a href="#npm_translate_lock-data">data</a>,
                   <a href="#npm_translate_lock-patches">patches</a>, <a href="#npm_translate_lock-exclude_package_contents">exclude_package_contents</a>, <a href="#npm_translate_lock-patch_tool">patch_tool</a>, <a href="#npm_translate_lock-patch_args">patch_args</a>, <a href="#npm_translate_lock-custom_postinstalls">custom_postinstalls</a>,
                   <a href="#npm_translate_lock-package_visibility">package_visibility</a>, <a href="#npm_translate_lock-prod">prod</a>, <a href="#npm_translate_lock-public_hoist_packages">public_hoist_packages</a>, <a href="#npm_translate_lock-dev">dev</a>, <a href="#npm_translate_lock-no_optional">no_optional</a>,
                   <a href="#npm_translate_lock-run_lifecycle_hooks">run_lifecycle_hooks</a>, <a href="#npm_translate_lock-lifecycle_hooks">lifecycle_hooks</a>, <a href="#npm_translate_lock-lifecycle_hooks_envs">lifecycle_hooks_envs</a>,
                   <a href="#npm_translate_lock-lifecycle_hooks_exclude">lifecycle_hooks_exclude</a>, <a href="#npm_translate_lock-lifecycle_hooks_execution_requirements">lifecycle_hooks_execution_requirements</a>,
                   <a href="#npm_translate_lock-lifecycle_hooks_no_sandbox">lifecycle_hooks_no_sandbox</a>, <a href="#npm_translate_lock-lifecycle_hooks_use_default_shell_env">lifecycle_hooks_use_default_shell_env</a>,
                   <a href="#npm_translate_lock-replace_packages">replace_packages</a>, <a href="#npm_translate_lock-bins">bins</a>, <a href="#npm_translate_lock-verify_node_modules_ignored">verify_node_modules_ignored</a>, <a href="#npm_translate_lock-verify_patches">verify_patches</a>, <a href="#npm_translate_lock-quiet">quiet</a>,
                   <a href="#npm_translate_lock-external_repository_action_cache">external_repository_action_cache</a>, <a href="#npm_translate_lock-link_workspace">link_workspace</a>, <a href="#npm_translate_lock-pnpm_version">pnpm_version</a>, <a href="#npm_translate_lock-use_pnpm">use_pnpm</a>,
                   <a href="#npm_translate_lock-npm_package_target_name">npm_package_target_name</a>, <a href="#npm_translate_lock-kwargs">kwargs</a>)
</pre>

Repository macro to generate starlark code from a lock file.

In most repositories, it would be an impossible maintenance burden to manually declare all
of the [`npm_import`](./npm_import) rules. This helper generates an external repository
containing a helper starlark module `repositories.bzl`, which supplies a loadable macro
`npm_repositories`. That macro creates an `npm_import` for each package.

The generated repository also contains:

- A `defs.bzl` file containing some rules such as `npm_link_all_packages`, which are [documented here](./npm_link_all_packages.md).
- `BUILD` files declaring targets for the packages listed as `dependencies` or `devDependencies` in `package.json`,
  so you can declare dependencies on those packages without having to repeat version information.

This macro creates a `pnpm` external repository, if the user didn't create a repository named
"pnpm" prior to calling `npm_translate_lock`.
`rules_js` currently only uses this repository when `npm_package_lock` or `yarn_lock` are used.
Set `pnpm_version` to `None` to inhibit this repository creation.

For more about how to use npm_translate_lock, read [pnpm and rules_js](/docs/pnpm.md).

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="npm_translate_lock-name"></a>name |  The repository rule name   |  none |
| <a id="npm_translate_lock-pnpm_lock"></a>pnpm_lock |  The `pnpm-lock.yaml` file.   |  `None` |
| <a id="npm_translate_lock-npm_package_lock"></a>npm_package_lock |  The `package-lock.json` file written by `npm install`.<br><br>Only one of `npm_package_lock` or `yarn_lock` may be set.   |  `None` |
| <a id="npm_translate_lock-yarn_lock"></a>yarn_lock |  The `yarn.lock` file written by `yarn install`.<br><br>Only one of `npm_package_lock` or `yarn_lock` may be set.   |  `None` |
| <a id="npm_translate_lock-update_pnpm_lock"></a>update_pnpm_lock |  When True, the pnpm lock file will be updated automatically when any of its inputs have changed since the last update.<br><br>Defaults to True when one of `npm_package_lock` or `yarn_lock` are set. Otherwise it defaults to False.<br><br>Read more: [using update_pnpm_lock](/docs/pnpm.md#update_pnpm_lock)   |  `False` |
| <a id="npm_translate_lock-node_toolchain_prefix"></a>node_toolchain_prefix |  the prefix of the node toolchain to use when generating the pnpm lockfile.   |  `"nodejs"` |
| <a id="npm_translate_lock-yq_toolchain_prefix"></a>yq_toolchain_prefix |  the prefix of the yq toolchain to use for parsing the pnpm lockfile.   |  `"yq"` |
| <a id="npm_translate_lock-preupdate"></a>preupdate |  Node.js scripts to run in this repository rule before auto-updating the pnpm lock file.<br><br>Scripts are run sequentially in the order they are listed. The working directory is set to the root of the external repository. Make sure all files required by preupdate scripts are added to the `data` attribute.<br><br>A preupdate script could, for example, transform `resolutions` in the root `package.json` file from a format that yarn understands such as `@foo/**/bar` to the equivalent `@foo/*>bar` that pnpm understands so that `resolutions` are compatible with pnpm when running `pnpm import` to update the pnpm lock file.<br><br>Only needed when `update_pnpm_lock` is True. Read more: [using update_pnpm_lock](/docs/pnpm.md#update_pnpm_lock)   |  `[]` |
| <a id="npm_translate_lock-npmrc"></a>npmrc |  The `.npmrc` file, if any, to use.<br><br>When set, the `.npmrc` file specified is parsed and npm auth tokens and basic authentication configuration specified in the file are passed to the Bazel downloader for authentication with private npm registries.<br><br>In a future release, pnpm settings such as public-hoist-patterns will be used.   |  `None` |
| <a id="npm_translate_lock-use_home_npmrc"></a>use_home_npmrc |  Use the `$HOME/.npmrc` file (or `$USERPROFILE/.npmrc` when on Windows) if it exists.<br><br>Settings from home `.npmrc` are merged with settings loaded from the `.npmrc` file specified in the `npmrc` attribute, if any. Where there are conflicting settings, the home `.npmrc` values will take precedence.<br><br>WARNING: The repository rule will not be invalidated by changes to the home `.npmrc` file since there is no way to specify this file as an input to the repository rule. If changes are made to the home `.npmrc` you can force the repository rule to re-run and pick up the changes by running: `bazel run @{name}//:sync` where `name` is the name of the `npm_translate_lock` you want to re-run.<br><br>Because of the repository rule invalidation issue, using the home `.npmrc` is not recommended. `.npmrc` settings should generally go in the `npmrc` in your repository so they are shared by all developers. The home `.npmrc` should be reserved for authentication settings for private npm repositories.   |  `None` |
| <a id="npm_translate_lock-data"></a>data |  Data files required by this repository rule when auto-updating the pnpm lock file.<br><br>Only needed when `update_pnpm_lock` is True. Read more: [using update_pnpm_lock](/docs/pnpm.md#update_pnpm_lock)   |  `[]` |
| <a id="npm_translate_lock-patches"></a>patches |  A map of package names or package names with their version (e.g., "my-package" or "my-package@v1.2.3") to a label list of patches to apply to the downloaded npm package. Multiple matches are additive.<br><br>These patches are applied after any patches in [pnpm.patchedDependencies](https://pnpm.io/next/package_json#pnpmpatcheddependencies).<br><br>Read more: [patching](/docs/pnpm.md#patching)   |  `{}` |
| <a id="npm_translate_lock-exclude_package_contents"></a>exclude_package_contents |  A map of package names or package names with their version (e.g., "my-package" or "my-package@v1.2.3") to a list of patterns to exclude from the package's generated node_modules link targets. Multiple matches are additive.<br><br>Versions must match if used.<br><br>For example,<br><br><pre><code>exclude_package_contents = {&#10;    "@foo/bar": ["**/test/**"],&#10;    "@foo/car@2.0.0": ["**/README*"],&#10;},</code></pre>   |  `{}` |
| <a id="npm_translate_lock-patch_tool"></a>patch_tool |  The patch tool to use. If not specified, the `patch` from `PATH` is used.   |  `None` |
| <a id="npm_translate_lock-patch_args"></a>patch_args |  A map of package names or package names with their version (e.g., "my-package" or "my-package@v1.2.3") to a label list arguments to pass to the patch tool. The most specific match wins.<br><br>Read more: [patching](/docs/pnpm.md#patching)   |  `{"*": ["-p0"]}` |
| <a id="npm_translate_lock-custom_postinstalls"></a>custom_postinstalls |  A map of package names or package names with their version (e.g., "my-package" or "my-package@v1.2.3") to a custom postinstall script to apply to the downloaded npm package after its lifecycle scripts runs. If the version is left out of the package name, the script will run on every version of the npm package. If a custom postinstall scripts exists for a package as well as for a specific version, the script for the versioned package will be appended with `&&` to the non-versioned package script.<br><br>For example,<br><br><pre><code>custom_postinstalls = {&#10;    "@foo/bar": "echo something &gt; somewhere.txt",&#10;    "fum@0.0.1": "echo something_else &gt; somewhere_else.txt",&#10;},</code></pre><br><br>Custom postinstalls are additive and joined with ` && ` when there are multiple matches for a package. More specific matches are appended to previous matches.   |  `{}` |
| <a id="npm_translate_lock-package_visibility"></a>package_visibility |  A map of package names or package names with their version (e.g., "my-package" or "my-package@v1.2.3") to a visibility list to use for the package's generated node_modules link targets. Multiple matches are additive. If there are no matches then the package's generated node_modules link targets default to public visibility (`["//visibility:public"]`).   |  `{}` |
| <a id="npm_translate_lock-prod"></a>prod |  If True, only install `dependencies` but not `devDependencies`.   |  `False` |
| <a id="npm_translate_lock-public_hoist_packages"></a>public_hoist_packages |  A map of package names or package names with their version (e.g., "my-package" or "my-package@v1.2.3") to a list of Bazel packages in which to hoist the package to the top-level of the node_modules tree when linking.<br><br>This is similar to setting https://pnpm.io/npmrc#public-hoist-pattern in an .npmrc file outside of Bazel, however, wild-cards are not yet supported and npm_translate_lock will fail if there are multiple versions of a package that are to be hoisted.<br><br><pre><code>public_hoist_packages = {&#10;    "@foo/bar": [""] # link to the root package in the WORKSPACE&#10;    "fum@0.0.1": ["some/sub/package"]&#10;},</code></pre><br><br>List of public hoist packages are additive when there are multiple matches for a package. More specific matches are appended to previous matches.   |  `{}` |
| <a id="npm_translate_lock-dev"></a>dev |  If True, only install `devDependencies`   |  `False` |
| <a id="npm_translate_lock-no_optional"></a>no_optional |  If True, `optionalDependencies` are not installed.<br><br>Currently `npm_translate_lock` behaves differently from pnpm in that is downloads all `optionaDependencies` while pnpm doesn't download `optionalDependencies` that are not needed for the platform pnpm is run on. See https://github.com/pnpm/pnpm/pull/3672 for more context.   |  `False` |
| <a id="npm_translate_lock-run_lifecycle_hooks"></a>run_lifecycle_hooks |  Sets a default value for `lifecycle_hooks` if `*` not already set. Set this to `False` to disable lifecycle hooks.   |  `True` |
| <a id="npm_translate_lock-lifecycle_hooks"></a>lifecycle_hooks |  A dict of package names to list of lifecycle hooks to run for that package.<br><br>By default the `preinstall`, `install` and `postinstall` hooks are run if they exist. This attribute allows the default to be overridden for packages to run `prepare`.<br><br>List of hooks are not additive. The most specific match wins.<br><br>Read more: [lifecycles](/docs/pnpm.md#lifecycles)   |  `{}` |
| <a id="npm_translate_lock-lifecycle_hooks_envs"></a>lifecycle_hooks_envs |  Environment variables set for the lifecycle hooks actions on npm packages. The environment variables can be defined per package by package name or globally using "*". Variables are declared as key/value pairs of the form "key=value". Multiple matches are additive.<br><br>Read more: [lifecycles](/docs/pnpm.md#lifecycles)   |  `{}` |
| <a id="npm_translate_lock-lifecycle_hooks_exclude"></a>lifecycle_hooks_exclude |  A list of package names or package names with their version (e.g., "my-package" or "my-package@v1.2.3") to not run any lifecycle hooks on.<br><br>Equivalent to adding `<value>: []` to `lifecycle_hooks`.<br><br>Read more: [lifecycles](/docs/pnpm.md#lifecycles)   |  `[]` |
| <a id="npm_translate_lock-lifecycle_hooks_execution_requirements"></a>lifecycle_hooks_execution_requirements |  Execution requirements applied to the preinstall, install and postinstall lifecycle hooks on npm packages.<br><br>The execution requirements can be defined per package by package name or globally using "*".<br><br>Execution requirements are not additive. The most specific match wins.<br><br>Read more: [lifecycles](/docs/pnpm.md#lifecycles)   |  `{}` |
| <a id="npm_translate_lock-lifecycle_hooks_no_sandbox"></a>lifecycle_hooks_no_sandbox |  If True, a "no-sandbox" execution requirement is added to all lifecycle hooks unless overridden by `lifecycle_hooks_execution_requirements`.<br><br>Equivalent to adding `"*": ["no-sandbox"]` to `lifecycle_hooks_execution_requirements`.<br><br>This defaults to True to limit the overhead of sandbox creation and copying the output TreeArtifacts out of the sandbox.<br><br>Read more: [lifecycles](/docs/pnpm.md#lifecycles)   |  `True` |
| <a id="npm_translate_lock-lifecycle_hooks_use_default_shell_env"></a>lifecycle_hooks_use_default_shell_env |  The `use_default_shell_env` attribute of the lifecycle hooks actions on npm packages.<br><br>See [use_default_shell_env](https://bazel.build/rules/lib/builtins/actions#run.use_default_shell_env)<br><br>Note: [--incompatible_merge_fixed_and_default_shell_env](https://bazel.build/reference/command-line-reference#flag--incompatible_merge_fixed_and_default_shell_env) is often required and not enabled by default in Bazel < 7.0.0.<br><br>This defaults to False reduce the negative effects of `use_default_shell_env`. Requires bazel-lib >= 2.4.2.<br><br>Read more: [lifecycles](/docs/pnpm.md#lifecycles)   |  `{}` |
| <a id="npm_translate_lock-replace_packages"></a>replace_packages |  A dict of package names to npm_package targets to link instead of the sources specified in the pnpm lock file for the corresponding packages.<br><br>The injected npm_package targets may optionally contribute transitive npm package dependencies on top of the transitive dependencies specified in the pnpm lock file for their respective packages, however, these transitive dependencies must not collide with pnpm lock specified transitive dependencies.<br><br>Any patches specified for the packages will be not applied to the injected npm_package targets. They will be applied, however, to the fetches sources for their respecitve packages so they can still be useful for patching the fetched `package.json` files, which are used to determine the generated bin entries for packages.<br><br>NB: lifecycle hooks and custom_postinstall scripts, if implicitly or explicitly enabled, will be run on the injected npm_package targets. These may be disabled explicitly using the `lifecycle_hooks` attribute.   |  `{}` |
| <a id="npm_translate_lock-bins"></a>bins |  Binary files to create in `node_modules/.bin` for packages in this lock file.<br><br>For a given package, this is typically derived from the "bin" attribute in the package.json file of that package.<br><br>For example:<br><br><pre><code>bins = {&#10;    "@foo/bar": {&#10;        "foo": "./foo.js",&#10;        "bar": "./bar.js"&#10;    },&#10;}</code></pre><br><br>Dicts of bins not additive. The most specific match wins.<br><br>In the future, this field may be automatically populated from information in the pnpm lock file. That feature is currently blocked on https://github.com/pnpm/pnpm/issues/5131.<br><br>Note: Bzlmod users must use an alternative syntax due to module extensions not supporting dict-of-dict attributes:<br><br><pre><code>bins = {&#10;    "@foo/bar": [&#10;        "foo=./foo.js",&#10;        "bar=./bar.js"&#10;    ],&#10;}</code></pre>   |  `{}` |
| <a id="npm_translate_lock-verify_node_modules_ignored"></a>verify_node_modules_ignored |  node_modules folders in the source tree should be ignored by Bazel.<br><br>This points to a `.bazelignore` file to verify that all nested node_modules directories pnpm will create are listed.<br><br>See https://github.com/bazelbuild/bazel/issues/8106   |  `None` |
| <a id="npm_translate_lock-verify_patches"></a>verify_patches |  Label to a patch list file.<br><br>Use this in together with the `list_patches` macro to guarantee that all patches in a patch folder are included in the `patches` attribute.<br><br>For example:<br><br><pre><code>verify_patches = "//patches:patches.list",</code></pre><br><br>In your patches folder add a BUILD.bazel file containing. <pre><code>load("@aspect_rules_js//npm:repositories.bzl", "list_patches")&#10;&#10;list_patches(&#10;    name = "patches",&#10;    out = "patches.list",&#10;)</code></pre><br><br>Once you have created this file, you need to create an empty `patches.list` file before generating the first list. You can do this by running <pre><code>touch patches/patches.list</code></pre><br><br>Finally, write the patches file at least once to make sure all patches are listed. This can be done by running `bazel run //patches:patches_update`.<br><br>See the `list_patches` documentation for further info. NOTE: if you would like to customize the patches directory location, you can set a flag in the `.npmrc`. Here is an example of what this might look like <pre><code># Set the directory for pnpm when patching&#10;# https://github.com/pnpm/pnpm/issues/6508#issuecomment-1537242124&#10;patches-dir=bazel/js/patches</code></pre> If you do this, you will have to update the `verify_patches` path to be this path instead of `//patches` like above.   |  `None` |
| <a id="npm_translate_lock-quiet"></a>quiet |  Set to False to print info logs and output stdout & stderr of pnpm lock update actions to the console.   |  `True` |
| <a id="npm_translate_lock-external_repository_action_cache"></a>external_repository_action_cache |  The location of the external repository action cache to write to when `update_pnpm_lock` = True.   |  `".aspect/rules/external_repository_action_cache"` |
| <a id="npm_translate_lock-link_workspace"></a>link_workspace |  The workspace name where links will be created for the packages in this lock file.<br><br>This is typically set in rule sets and libraries that vendor the starlark generated by npm_translate_lock so the link_workspace passed to npm_import is set correctly so that links are created in the external repository and not the user workspace.<br><br>Can be left unspecified if the link workspace is the user workspace.   |  `None` |
| <a id="npm_translate_lock-pnpm_version"></a>pnpm_version |  pnpm version to use when generating the @pnpm repository. Set to None to not create this repository.<br><br>Can be left unspecified and the rules_js default `DEFAULT_PNPM_VERSION` will be used.   |  `"8.15.9"` |
| <a id="npm_translate_lock-use_pnpm"></a>use_pnpm |  label of the pnpm entry point to use.   |  `None` |
| <a id="npm_translate_lock-npm_package_target_name"></a>npm_package_target_name |  The name of linked `npm_package`, `js_library` or `JsInfo` producing targets.<br><br>When targets are linked as pnpm workspace packages, the name of the target must align with this value.<br><br>The `{dirname}` placeholder is replaced with the directory name of the target.   |  `"pkg"` |
| <a id="npm_translate_lock-kwargs"></a>kwargs |  Internal use only   |  none |


# js_run_devserver.md


Implementation details for js_run_devserver rule

<a id="js_run_devserver"></a>

## js_run_devserver

<pre>
js_run_devserver(<a href="#js_run_devserver-name">name</a>, <a href="#js_run_devserver-tool">tool</a>, <a href="#js_run_devserver-command">command</a>, <a href="#js_run_devserver-grant_sandbox_write_permissions">grant_sandbox_write_permissions</a>, <a href="#js_run_devserver-use_execroot_entry_point">use_execroot_entry_point</a>,
                 <a href="#js_run_devserver-allow_execroot_entry_point_with_no_copy_data_to_bin">allow_execroot_entry_point_with_no_copy_data_to_bin</a>, <a href="#js_run_devserver-kwargs">kwargs</a>)
</pre>

Runs a devserver via binary target or command.

A simple http-server, for example, can be setup as follows,

```
load("@aspect_rules_js//js:defs.bzl", "js_run_devserver")
load("@npm//:http-server/package_json.bzl", http_server_bin = "bin")

http_server_bin.http_server_binary(
    name = "http_server",
)

js_run_devserver(
    name = "serve",
    args = ["."],
    data = ["index.html"],
    tool = ":http_server",
)
```

A Next.js devserver can be setup as follows,

```
js_run_devserver(
    name = "dev",
    args = ["dev"],
    command = "./node_modules/.bin/next",
    data = [
        "next.config.js",
        "package.json",
        ":node_modules/next",
        ":node_modules/react",
        ":node_modules/react-dom",
        ":node_modules/typescript",
        "//pages",
        "//public",
        "//styles",
    ],
)
```

where the `./node_modules/.bin/next` bin entry of Next.js is configured in
`npm_translate_lock` as such,

```
npm_translate_lock(
    name = "npm",
    bins = {
        # derived from "bin" attribute in node_modules/next/package.json
        "next": {
            "next": "./dist/bin/next",
        },
    },
    pnpm_lock = "//:pnpm-lock.yaml",
)
```

and run in watch mode using [ibazel](https://github.com/bazelbuild/bazel-watcher) with
`ibazel run //:dev`.

The devserver specified by either `tool` or `command` is run in a custom sandbox that is more
compatible with devserver watch modes in Node.js tools such as Webpack and Next.js.

The custom sandbox is populated with the default outputs of all targets in `data`
as well as transitive sources & npm links.

As an optimization, package store files are explicitly excluded from the sandbox since the npm
links will point to the package store in the execroot and Node.js will follow those links as it
does within the execroot. As a result, rules_js npm package link targets such as
`//:node_modules/next` are handled efficiently. Since these targets are symlinks in the output
tree, they are recreated as symlinks in the custom sandbox and do not incur a full copy of the
underlying npm packages.

Supports running with [ibazel](https://github.com/bazelbuild/bazel-watcher).
Only `data` files that change on incremental builds are synchronized when running with ibazel.

Note that the use of `alias` targets is not supported by ibazel: https://github.com/bazelbuild/bazel-watcher/issues/100

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="js_run_devserver-name"></a>name |  A unique name for this target.   |  none |
| <a id="js_run_devserver-tool"></a>tool |  The devserver binary target to run.<br><br>Only one of `command` or `tool` may be specified.   |  `None` |
| <a id="js_run_devserver-command"></a>command |  The devserver command to run.<br><br>For example, this could be the bin entry of an npm package that is included in data such as `./node_modules/.bin/next`.<br><br>Using the bin entry of next, for example, resolves issues with Next.js and React being found in multiple node_modules trees when next is run as an encapsulated `js_binary` tool.<br><br>Only one of `command` or `tool` may be specified.   |  `None` |
| <a id="js_run_devserver-grant_sandbox_write_permissions"></a>grant_sandbox_write_permissions |  If set, write permissions is set on all files copied to the custom sandbox.<br><br>This can be useful to support some devservers such as Next.js which may, under some circumstances, try to modify files when running.<br><br>See https://github.com/aspect-build/rules_js/issues/935 for more context.   |  `False` |
| <a id="js_run_devserver-use_execroot_entry_point"></a>use_execroot_entry_point |  Use the `entry_point` script of the `js_binary` `tool` that is in the execroot output tree instead of the copy that is in runfiles.<br><br>Using the entry point script that is in the execroot output tree means that there will be no conflicting runfiles `node_modules` in the node_modules resolution path which can confuse npm packages such as next and react that don't like being resolved in multiple node_modules trees. This more closely emulates the environment that tools such as Next.js see when they are run outside of Bazel.<br><br>When True, the `js_binary` tool must have `copy_data_to_bin` set to True (the default) so that all data files needed by the binary are available in the execroot output tree. This requirement can be turned off with by setting `allow_execroot_entry_point_with_no_copy_data_to_bin` to True.   |  `True` |
| <a id="js_run_devserver-allow_execroot_entry_point_with_no_copy_data_to_bin"></a>allow_execroot_entry_point_with_no_copy_data_to_bin |  Turn off validation that the `js_binary` tool has `copy_data_to_bin` set to True when `use_execroot_entry_point` is set to True.<br><br>See `use_execroot_entry_point` doc for more info.   |  `False` |
| <a id="js_run_devserver-kwargs"></a>kwargs |  All other args from `js_binary` except for `entry_point` which is set implicitly.<br><br>`entry_point` is set implicitly by `js_run_devserver` and cannot be overridden.<br><br>See https://docs.aspect.build/rules/aspect_rules_js/docs/js_binary   |  none |


# troubleshooting.md
# Common troubleshooting tips

## Module not found errors

This is the most common error rules_js users encounter.
These problems generally stem from a runtime `require` call of some library which was not declared as a dependency.

Fortunately, these problems are not unique to Bazel.
As described in [our documentation](./pnpm.md#hoisting),
rules_js should behave the same way `pnpm` does with [`hoist=false`](https://pnpm.io/npmrc#hoist).

These problems are also reproducible under [Yarn PnP](https://yarnpkg.com/features/pnp) because it
also relies on correct dependencies.

The Node.js documentation describes the algorithm used:
https://nodejs.org/api/modules.html#loading-from-node_modules-folders

Since the resolution starts from the callsite, the remedy depends on where the `require` statement appears.

### require appears in your code

This is the case when you write an `import` or `require` statement.

In this case you should add the runtime dependency to your BUILD file alongside your source file:

For example,

```starlark
js_library(
    name = "requires_foo",
    srcs = ["config.js"],          # contains "require('foo')"
    data = [":node_modules/foo"],  # satisfies that require
)
```

and also, the `foo` module should be listed in your `package.json#dependencies` since pnpm is strict
about hoisting transitive dependencies to the root of `node_modules`.

This case also includes when you run some other tool, passing it a `config.js` file.

> This is the "ideal" way for JavaScript tools to be configured, because it allows an easy
> "symmetry" where you `require` a library and declare your dependency on it in the same place.
> When you pass a tool a `config.json` or other non-JavaScript file, and have string-typed references
> to npm packages, you'll fall into the next case: "require appears in third-party code".

### require appears in third-party code

This case itself breaks down into three possible remedies, depending on whether you can move the
require to your own code, the missing dependency can be considered a "bug",
or the third-party package uses the "plugin pattern" to discover its
plugins dynamically at runtime based on finding them based on a string you provided.

#### The `require` can move to first-party

This is the most principled solution. In many cases, a library that accepts the name of a package as
a string will also accept it as an object, so you can refactor `config: ['some-package']` to
`config: [require('some-package')]`. You may need to change from json or yaml config to a JavaScript
config file to allow the `require` syntax.

Once you've done this, it's handled like the "require appears in your code" case above.

For example, the
[documentation for the postcss-loader for Webpack](https://webpack.js.org/loaders/postcss-loader/#sugarss)
suggests that you `npm install --save-dev sugarss`
and then pass the string "sugarss" to the `options.postcssOptions.parser` property of the loader.
However this violates symmetry and would require workarounds listed below.
You can simply pass `require("sugarss")` instead of the bare string, then include the `sugarss`
package in the `data` (runtime dependencies) of your `webpack.config.js`.

#### It's a bug

This is the case when a package has a `require` statement in its runtime code for some package, but
it doesn't list that package in its `package.json`, or lists it only as a `devDependency`.

pnpm and Yarn PnP will hit the same bug. Conveniently, there's already a shared database used by
both projects to list these, along with the missing dependency edge:
https://github.com/yarnpkg/berry/blob/master/packages/yarnpkg-extensions/sources/index.ts

> We should use this database under Bazel as well. Follow
> https://github.com/aspect-build/rules_js/issues/1215.

The recommended fix for both pnpm and rules_js is to use
[pnpm.packageExtensions](https://pnpm.io/package_json#pnpmpackageextensions)
in your `package.json` to add the missing `dependencies` or `peerDependencies`.

Example,

https://github.com/aspect-build/rules_js/blob/a8c192eed0e553acb7000beee00c60d60a32ed82/package.json#L12

> Make sure you pnpm install after changing `package.json`, as rules_js only reads the
> `pnpm-lock.yaml` file to gather dependency information.
> See [Fetch third-party packages](./README.md#fetch-third-party-packages-from-npm)

#### It's a plugin

Sometimes the package intentionally doesn't list dependencies, because it discovers them at runtime.
This is used for tools that locate their "plugins"; `eslint` and `prettier` are common typical examples.

The solution is based on pnpm's [public-hoist-pattern](https://pnpm.io/npmrc#public-hoist-pattern).
Use the [`public_hoist_packages` attribute of `npm_translate_lock`](./npm_translate_lock.md#npm_translate_lock-public_hoist_packages).
The documentation says the value provided to each element in the map is:

> a list of Bazel packages in which to hoist the package to the top-level of the node_modules tree

To make plugins work, you should have the Bazel package containing the pnpm workspace root (the folder containing `pnpm-lock.yaml`) in this list.
This ensures that the tool in the package store (`node_modules/.aspect_rules_js`) will be able to locate the plugins.
If your lockfile is in the root of the Bazel workspace, this value should be an empty string: `""`.
If the lockfile is in `some/subpkg/pnpm-lock.yaml` then `"some/subpkg"` should appear in the list.

For example:

`WORKSPACE`

```starlark
npm_translate_lock(
    ...
    public_hoist_packages = {
        "eslint-config-react-app": [""],
    },
)
```

Note that `public_hoist_packages` affects the layout of the `node_modules` tree, but you still need
to depend on that hoisted package, e.g. with `deps = [":node_modules/hoisted_pkg"]`. Continuing the example:

`BUILD`

```starlark
eslint_bin.eslint_test(
    ...
    data = [
        ...
        "//:node_modules/eslint-config-react-app",
    ],
)
```

> NB: We plan to add support for the `.npmrc` `public-hoist-pattern` setting to `rules_js` in a future release.
> For now, you must emulate public-hoist-pattern in `rules_js` using the `public_hoist_packages` attribute shown above.

## Ugly stack traces

Bazel's sandboxing and runfiles directory layouts can make stack traces and logs hard to read. This issue is common in many
languages when used within bazel, not only JavaScript.

One solution involving `Error.prepareStackTrace` was [suggested on bazelbuild slack](https://bazelbuild.slack.com/archives/CA31HN1T3/p1733518986229749?thread_ts=1733516180.969159&cid=CA31HN1T3) by [John Firebaugh](https://github.com/jfirebaugh). This overrides `Error.prepareStackTrace` to strip the bazel sandbox and runfiles paths from error stack traces. This also uses [`source-map-support`](https://www.npmjs.com/package/source-map-support) to also apply source maps to the stack traces.

See [examples/stack_traces](../examples/stack_traces) for a working example.

## Performance

For general bazel performance tips see the [Aspect bazelrc guide](https://docs.aspect.build/guides/bazelrc/#performance-options).

### Linking first-party packages

When linking first-party packages it is recommended to use `js_library` or another `JsInfo`-providing rule to represent the package instead of the `npm_package` rule (which provides `NpmPackageInfo`).

The use of `NpmPackageInfo` requires building the full package content in order to output a single directory artifact representing the package.

Using `JsInfo` allows rules_js to passthru the provider without collecting the package content until another action requests it. For example `JsInfo.types`, normally outputted by a slow `.d.ts` producing tool such as `tsc`, is most likely unnecessary when only executing or bundling JavaScript files from `JsInfo.sources`. If `JsInfo.types` is produced by different actions then `JsInfo.sources` then those actions may not be required at all.

### Parallelism (build, test)

A lot of tooling in the JS ecosystem uses parallelism to speed up builds. This is great, but as Bazel also parallels builds this can lead to a lot of contention for resources.

Some rulesets configure tools to take this into account such as the [rules_jest](https://github.com/aspect-build/rules_jest) default [run_in_band](https://github.com/aspect-build/rules_jest/blob/main/docs/jest_test.md#jest_test-run_in_band), while other tools (especially those without dedicated rulesets) may need to be configured manually.

For example, the [default WebPack configuration](https://webpack.js.org/configuration/optimization/#optimizationminimizer) uses Terser for optimization. `terser-webpack-plugin` defaults to [parallelizing its work across os.cpus().length - 1](https://www.npmjs.com/package/terser-webpack-plugin#parallel).
This can lead to builds performing slower due to IO throttling, or even failing if running in a virtualized environment where IO throughput is limited.

If you are experiencing slower than expected builds, you can try disabling or reducing parallelism for the tools you are using.

### Unnecessary npm package content

Npm packages sometimes include unnecessary files such as tests, test data etc. Large files or a large number of files
can effect performance and are sometimes worth explicitly excluding content.

In these cases you can add such packages and the respective files/folders you want to exclude to your npm_translate_lock
rule in the `exclude_package_contents` attribute like so:

```starlark
npm.npm_translate_lock(
    ...
    exclude_package_contents = {
        "resolve": ["**/test/*"],
    },
)
```

This example will remove the test folder.

You can use this to remove whatever you find to be not needed for your project.

#### Jest

See [rules_jest](https://github.com/aspect-build/rules_jest) specific [troubleshooting](https://docs.aspect.build/rulesets/aspect_rules_jest/docs/troubleshooting#performance).

# js_run_binary.md


Runs a js_binary as a build action.

This macro wraps Aspect bazel-lib's run_binary (https://github.com/bazel-contrib/bazel-lib/blob/main/lib/run_binary.bzl)
and adds attributes and features specific to rules_js's js_binary.

Load this with,

```starlark
load("@aspect_rules_js//js:defs.bzl", "js_run_binary")
```

<a id="js_run_binary"></a>

## js_run_binary

<pre>
js_run_binary(<a href="#js_run_binary-name">name</a>, <a href="#js_run_binary-tool">tool</a>, <a href="#js_run_binary-env">env</a>, <a href="#js_run_binary-srcs">srcs</a>, <a href="#js_run_binary-outs">outs</a>, <a href="#js_run_binary-out_dirs">out_dirs</a>, <a href="#js_run_binary-args">args</a>, <a href="#js_run_binary-chdir">chdir</a>, <a href="#js_run_binary-stdout">stdout</a>, <a href="#js_run_binary-stderr">stderr</a>, <a href="#js_run_binary-exit_code_out">exit_code_out</a>,
              <a href="#js_run_binary-silent_on_success">silent_on_success</a>, <a href="#js_run_binary-use_execroot_entry_point">use_execroot_entry_point</a>, <a href="#js_run_binary-copy_srcs_to_bin">copy_srcs_to_bin</a>, <a href="#js_run_binary-include_sources">include_sources</a>,
              <a href="#js_run_binary-include_types">include_types</a>, <a href="#js_run_binary-include_transitive_sources">include_transitive_sources</a>, <a href="#js_run_binary-include_transitive_types">include_transitive_types</a>,
              <a href="#js_run_binary-include_npm_sources">include_npm_sources</a>, <a href="#js_run_binary-log_level">log_level</a>, <a href="#js_run_binary-mnemonic">mnemonic</a>, <a href="#js_run_binary-progress_message">progress_message</a>, <a href="#js_run_binary-execution_requirements">execution_requirements</a>,
              <a href="#js_run_binary-stamp">stamp</a>, <a href="#js_run_binary-patch_node_fs">patch_node_fs</a>, <a href="#js_run_binary-allow_execroot_entry_point_with_no_copy_data_to_bin">allow_execroot_entry_point_with_no_copy_data_to_bin</a>,
              <a href="#js_run_binary-use_default_shell_env">use_default_shell_env</a>, <a href="#js_run_binary-kwargs">kwargs</a>)
</pre>

Wrapper around @aspect_bazel_lib `run_binary` that adds convenience attributes for using a `js_binary` tool.

This rule does not require Bash `native.genrule`.

The following environment variables are made available to the Node.js runtime based on available Bazel [Make variables](https://bazel.build/reference/be/make-variables#predefined_variables):

* BAZEL_BINDIR: the WORKSPACE-relative bazel bin directory; equivalent to the `$(BINDIR)` Make variable of the `js_run_binary` target
* BAZEL_COMPILATION_MODE: One of `fastbuild`, `dbg`, or `opt` as set by [`--compilation_mode`](https://bazel.build/docs/user-manual#compilation-mode); equivalent to `$(COMPILATION_MODE)` Make variable of the `js_run_binary` target
* BAZEL_TARGET_CPU: the target cpu architecture; equivalent to `$(TARGET_CPU)` Make variable of the `js_run_binary` target

The following environment variables are made available to the Node.js runtime based on the rule context:

* BAZEL_BUILD_FILE_PATH: the WORKSPACE-relative path to the BUILD file of the bazel target being run; equivalent to `ctx.build_file_path` of the `js_run_binary` target's rule context
* BAZEL_PACKAGE: the package of the bazel target being run; equivalent to `ctx.label.package` of the `js_run_binary` target's rule context
* BAZEL_TARGET_NAME: the full label of the bazel target being run; a stringified version of `ctx.label` of the `js_run_binary` target's rule context
* BAZEL_TARGET: the name of the bazel target being run; equivalent to `ctx.label.name` of the  `js_run_binary` target's rule context
* BAZEL_WORKSPACE: the bazel workspace name; equivalent to `ctx.workspace_name` of the `js_run_binary` target's rule context

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="js_run_binary-name"></a>name |  Target name   |  none |
| <a id="js_run_binary-tool"></a>tool |  The tool to run in the action.<br><br>Should be a `js_binary` rule. Use Aspect bazel-lib's run_binary (https://github.com/bazel-contrib/bazel-lib/blob/main/lib/run_binary.bzl) for other *_binary rule types.   |  none |
| <a id="js_run_binary-env"></a>env |  Environment variables of the action.<br><br>Subject to `$(location)` and make variable expansion.   |  `{}` |
| <a id="js_run_binary-srcs"></a>srcs |  Additional inputs of the action.<br><br>These labels are available for `$(location)` expansion in `args` and `env`.   |  `[]` |
| <a id="js_run_binary-outs"></a>outs |  Output files generated by the action.<br><br>These labels are available for `$(location)` expansion in `args` and `env`.   |  `[]` |
| <a id="js_run_binary-out_dirs"></a>out_dirs |  Output directories generated by the action.<br><br>These labels are _not_ available for `$(location)` expansion in `args` and `env` since they are not pre-declared labels created via attr.output_list(). Output directories are declared instead by `ctx.actions.declare_directory`.   |  `[]` |
| <a id="js_run_binary-args"></a>args |  Command line arguments of the binary.<br><br>Subject to `$(location)` and make variable expansion.   |  `[]` |
| <a id="js_run_binary-chdir"></a>chdir |  Working directory to run the build action in.<br><br>This overrides the chdir value if set on the `js_binary` tool target.<br><br>By default, `js_binary` tools run in the root of the output tree. For more context on why, please read the aspect_rules_js README https://github.com/aspect-build/rules_js/tree/dbb5af0d2a9a2bb50e4cf4a96dbc582b27567155#running-nodejs-programs.<br><br>To run in the directory containing the js_run_binary in the output tree, use `chdir = package_name()` (or if you're in a macro, use `native.package_name()`).<br><br>WARNING: this will affect other paths passed to the program, either as arguments or in configuration files, which are workspace-relative.<br><br>You may need `../../` segments to re-relativize such paths to the new working directory.   |  `None` |
| <a id="js_run_binary-stdout"></a>stdout |  Output file to capture the stdout of the binary.<br><br>This can later be used as an input to another target subject to the same semantics as `outs`.<br><br>If the binary creates outputs and these are declared, they must still be created.   |  `None` |
| <a id="js_run_binary-stderr"></a>stderr |  Output file to capture the stderr of the binary to.<br><br>This can later be used as an input to another target subject to the same semantics as `outs`.<br><br>If the binary creates outputs and these are declared, they must still be created.   |  `None` |
| <a id="js_run_binary-exit_code_out"></a>exit_code_out |  Output file to capture the exit code of the binary to.<br><br>This can later be used as an input to another target subject to the same semantics as `outs`. Note that setting this will force the binary to exit 0.<br><br>If the binary creates outputs and these are declared, they must still be created.   |  `None` |
| <a id="js_run_binary-silent_on_success"></a>silent_on_success |  produce no output on stdout nor stderr when program exits with status code 0.<br><br>This makes node binaries match the expected bazel paradigm.   |  `True` |
| <a id="js_run_binary-use_execroot_entry_point"></a>use_execroot_entry_point |  Use the `entry_point` script of the `js_binary` `tool` that is in the execroot output tree instead of the copy that is in runfiles.<br><br>Runfiles of `tool` are all hoisted to `srcs` of the underlying `run_binary` so they are included as execroot inputs to the action.<br><br>Using the entry point script that is in the execroot output tree means that there will be no conflicting runfiles `node_modules` in the node_modules resolution path which can confuse npm packages such as next and react that don't like being resolved in multiple node_modules trees. This more closely emulates the environment that tools such as Next.js see when they are run outside of Bazel.<br><br>When True, the `js_binary` tool must have `copy_data_to_bin` set to True (the default) so that all data files needed by the binary are available in the execroot output tree. This requirement can be turned off with by setting `allow_execroot_entry_point_with_no_copy_data_to_bin` to True.   |  `True` |
| <a id="js_run_binary-copy_srcs_to_bin"></a>copy_srcs_to_bin |  When True, all srcs files are copied to the output tree that are not already there.   |  `True` |
| <a id="js_run_binary-include_sources"></a>include_sources |  see `js_info_files` documentation   |  `True` |
| <a id="js_run_binary-include_types"></a>include_types |  see `js_info_files` documentation   |  `False` |
| <a id="js_run_binary-include_transitive_sources"></a>include_transitive_sources |  see `js_info_files` documentation   |  `True` |
| <a id="js_run_binary-include_transitive_types"></a>include_transitive_types |  see `js_info_files` documentation   |  `False` |
| <a id="js_run_binary-include_npm_sources"></a>include_npm_sources |  see `js_info_files` documentation   |  `True` |
| <a id="js_run_binary-log_level"></a>log_level |  Set the logging level of the `js_binary` tool.<br><br>This overrides the log level set on the `js_binary` tool target.   |  `None` |
| <a id="js_run_binary-mnemonic"></a>mnemonic |  A one-word description of the action, for example, CppCompile or GoLink.   |  `"JsRunBinary"` |
| <a id="js_run_binary-progress_message"></a>progress_message |  Progress message to show to the user during the build, for example, "Compiling foo.cc to create foo.o". The message may contain %{label}, %{input}, or %{output} patterns, which are substituted with label string, first input, or output's path, respectively. Prefer to use patterns instead of static strings, because the former are more efficient.   |  `None` |
| <a id="js_run_binary-execution_requirements"></a>execution_requirements |  Information for scheduling the action.<br><br>For example,<br><br><pre><code>execution_requirements = {&#10;    "no-cache": "1",&#10;},</code></pre><br><br>See https://docs.bazel.build/versions/main/be/common-definitions.html#common.tags for useful keys.   |  `None` |
| <a id="js_run_binary-stamp"></a>stamp |  Whether to include build status files as inputs to the tool. Possible values:<br><br>- `stamp = 0 (default)`: Never include build status files as inputs to the tool.     This gives good build result caching.     Most tools don't use the status files, so including them in `--stamp` builds makes those     builds have many needless cache misses.     (Note: this default is different from most rules with an integer-typed `stamp` attribute.) - `stamp = 1`: Always include build status files as inputs to the tool, even in     [--nostamp](https://docs.bazel.build/versions/main/user-manual.html#flag--stamp) builds.     This setting should be avoided, since it is non-deterministic.     It potentially causes remote cache misses for the target and     any downstream actions that depend on the result. - `stamp = -1`: Inclusion of build status files as inputs is controlled by the     [--[no]stamp](https://docs.bazel.build/versions/main/user-manual.html#flag--stamp) flag.     Stamped targets are not rebuilt unless their dependencies change.<br><br>Default value is `0` since the majority of js_run_binary targets in a build graph typically do not use build status files and including them for all js_run_binary actions whenever `--stamp` is set would result in invalidating the entire graph and would prevent cache hits. Stamping is typically done in terminal targets when building release artifacts and stamp should typically be set explicitly in these targets to `-1` so it is enabled when the `--stamp` flag is set.<br><br>When stamping is enabled, an additional two environment variables will be set for the action:     - `BAZEL_STABLE_STATUS_FILE`     - `BAZEL_VOLATILE_STATUS_FILE`<br><br>These files can be read and parsed by the action, for example to pass some values to a bundler.   |  `0` |
| <a id="js_run_binary-patch_node_fs"></a>patch_node_fs |  Patch the to Node.js `fs` API (https://nodejs.org/api/fs.html) for this node program to prevent the program from following symlinks out of the execroot, runfiles and the sandbox.<br><br>When enabled, `js_binary` patches the Node.js sync and async `fs` API functions `lstat`, `readlink`, `realpath`, `readdir` and `opendir` so that the node program being run cannot resolve symlinks out of the execroot and the runfiles tree. When in the sandbox, these patches prevent the program being run from resolving symlinks out of the sandbox.<br><br>When disabled, node programs can leave the execroot, runfiles and sandbox by following symlinks which can lead to non-hermetic behavior.   |  `True` |
| <a id="js_run_binary-allow_execroot_entry_point_with_no_copy_data_to_bin"></a>allow_execroot_entry_point_with_no_copy_data_to_bin |  Turn off validation that the `js_binary` tool has `copy_data_to_bin` set to True when `use_execroot_entry_point` is set to True.<br><br>See `use_execroot_entry_point` doc for more info.   |  `False` |
| <a id="js_run_binary-use_default_shell_env"></a>use_default_shell_env |  If set, passed to the underlying run_binary.<br><br>May introduce non-determinism when True; use with care! See e.g. https://github.com/bazelbuild/bazel/issues/4912<br><br>Requires a minimum of aspect_bazel_lib v1.40.3 or v2.4.2.<br><br>Refer to https://bazel.build/rules/lib/builtins/actions#run for more details.   |  `None` |
| <a id="js_run_binary-kwargs"></a>kwargs |  Additional arguments   |  none |


# migrate.md
# Migrating from rules_nodejs

MOVED to <https://docs.aspect.build/guides/rules_js_migration>

# nextjs.md


Utilities for building Next.js applications with Bazel and rules_js.

All invocations of Next.js are done through a `next_js_binary` target passed into the macros.
This is normally generated once alongside the `package.json` containing the `next` dependency:

```
load("@npm//:next/package_json.bzl", next_bin = "bin")

next_bin.next_binary(
    name = "next_js_binary",
    visibility = ["//visibility:public"],
)
```

The next binary is then passed into the macros, for example:

```
nextjs_build(
    name = "next",
    config = "next.config.mjs",
    srcs = glob(["src/**"]),
    next_js_binary = "//:next_js_binary",
)
```

# Macros

There are two sets of macros for building Next.js applications: standard and standalone.

## Standard

- `nextjs()`: wrap the build+dev+start targets
- `nextjs_build()`: the Next.js [build](https://nextjs.org/docs/app/building-your-application/deploying#production-builds) command
- `nextjs_dev()`: the Next.js [dev](https://nextjs.org/docs/app/getting-started/installation#run-the-development-server) command
- `nextjs_start()`: the Next.js [start](https://nextjs.org/docs/app/building-your-application/deploying#nodejs-server) command,
   accepting a Next.js build artifact to start

## Standalone

For [standalone applications](https://nextjs.org/docs/app/api-reference/config/next-config-js/output#automatically-copying-traced-files):
- `nextjs_standalone_build()`: the Next.js [build](https://nextjs.org/docs/app/building-your-application/deploying#production-builds) command,
   configured for a standalone application within bazel
- `nextjs_standalone_server()`: constructs a standalone Next.js server `js_binary` following the
  [standalone directory structure guidelines](https://nextjs.org/docs/app/api-reference/config/next-config-js/output#automatically-copying-traced-files)

<a id="nextjs"></a>

## nextjs

<pre>
nextjs(<a href="#nextjs-name">name</a>, <a href="#nextjs-srcs">srcs</a>, <a href="#nextjs-next_js_binary">next_js_binary</a>, <a href="#nextjs-config">config</a>, <a href="#nextjs-data">data</a>, <a href="#nextjs-serve_data">serve_data</a>, <a href="#nextjs-kwargs">kwargs</a>)
</pre>

Generates Next.js build, dev & start targets.

`{name}`       - a Next.js production bundle
`{name}.dev`   - a Next.js devserver
`{name}.start` - a Next.js prodserver

Use this macro in the BUILD file at the root of a next app where the `next.config.mjs`
file is located.

For example, a target such as `//app:next` in `app/BUILD.bazel`

```
next(
    name = "next",
    config = "next.config.mjs",
    srcs = glob(["src/**"]),
    data = [
        "//:node_modules/next",
        "//:node_modules/react-dom",
        "//:node_modules/react",
        "package.json",
    ],
    next_js_binary = "//:next_js_binary",
)
```

will create the targets:

```
//app:next
//app:next.dev
//app:next.start
```

To build the above next app, equivalent to running `next build` outside Bazel:

```
bazel build //app:next
```

To run the development server in watch mode with
[ibazel](https://github.com/bazelbuild/bazel-watcher), equivalent to running
`next dev` outside Bazel:

```
ibazel run //app:next.dev
```

To run the production server in watch mode with
[ibazel](https://github.com/bazelbuild/bazel-watcher), equivalent to running
`next start` outside Bazel:

```
ibazel run //app:next.start
```

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="nextjs-name"></a>name |  the name of the build target   |  none |
| <a id="nextjs-srcs"></a>srcs |  Source files to include in build & dev targets. Typically these are source files or transpiled source files in Next.js source folders such as `pages`, `public` & `styles`.   |  none |
| <a id="nextjs-next_js_binary"></a>next_js_binary |  The next `js_binary` target to use for running Next.js<br><br>Typically this is a js_binary target created using `bin` loaded from the `package_json.bzl` file of the npm package.<br><br>See main docstring above for example usage.   |  none |
| <a id="nextjs-config"></a>config |  the Next.js config file. Typically `next.config.mjs`.   |  `"next.config.mjs"` |
| <a id="nextjs-data"></a>data |  Data files to include in all targets. These are typically npm packages required for the build & configuration files such as package.json and next.config.js.   |  `[]` |
| <a id="nextjs-serve_data"></a>serve_data |  Data files to include in devserver targets   |  `[]` |
| <a id="nextjs-kwargs"></a>kwargs |  Other attributes passed to all targets such as `tags`.   |  none |

<a id="nextjs_build"></a>

## nextjs_build

<pre>
nextjs_build(<a href="#nextjs_build-name">name</a>, <a href="#nextjs_build-config">config</a>, <a href="#nextjs_build-srcs">srcs</a>, <a href="#nextjs_build-next_js_binary">next_js_binary</a>, <a href="#nextjs_build-data">data</a>, <a href="#nextjs_build-kwargs">kwargs</a>)
</pre>

Build the Next.js production artifact.

See https://nextjs.org/docs/pages/api-reference/cli/next#build

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="nextjs_build-name"></a>name |  the name of the build target   |  none |
| <a id="nextjs_build-config"></a>config |  the Next.js config file   |  none |
| <a id="nextjs_build-srcs"></a>srcs |  the sources to include in the build, including any transitive deps   |  none |
| <a id="nextjs_build-next_js_binary"></a>next_js_binary |  The next `js_binary` target to use for running Next.js<br><br>Typically this is a js_binary target created using `bin` loaded from the `package_json.bzl` file of the npm package.<br><br>See main docstring above for example usage.   |  none |
| <a id="nextjs_build-data"></a>data |  the data files to include in the build   |  `[]` |
| <a id="nextjs_build-kwargs"></a>kwargs |  Other attributes passed to all targets such as `tags`, env   |  none |

<a id="nextjs_dev"></a>

## nextjs_dev

<pre>
nextjs_dev(<a href="#nextjs_dev-name">name</a>, <a href="#nextjs_dev-config">config</a>, <a href="#nextjs_dev-srcs">srcs</a>, <a href="#nextjs_dev-data">data</a>, <a href="#nextjs_dev-next_js_binary">next_js_binary</a>, <a href="#nextjs_dev-kwargs">kwargs</a>)
</pre>

Run the Next.js development server.

See https://nextjs.org/docs/pages/api-reference/cli/next#next-dev-options

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="nextjs_dev-name"></a>name |  the name of the build target   |  none |
| <a id="nextjs_dev-config"></a>config |  the Next.js config file   |  none |
| <a id="nextjs_dev-srcs"></a>srcs |  the sources to include in the build, including any transitive deps   |  none |
| <a id="nextjs_dev-data"></a>data |  additional devserver runtime data   |  none |
| <a id="nextjs_dev-next_js_binary"></a>next_js_binary |  The next `js_binary` target to use for running Next.js<br><br>Typically this is a js_binary target created using `bin` loaded from the `package_json.bzl` file of the npm package.<br><br>See main docstring above for example usage.   |  none |
| <a id="nextjs_dev-kwargs"></a>kwargs |  Other attributes passed to all targets such as `tags`, env   |  none |

<a id="nextjs_standalone_build"></a>

## nextjs_standalone_build

<pre>
nextjs_standalone_build(<a href="#nextjs_standalone_build-name">name</a>, <a href="#nextjs_standalone_build-config">config</a>, <a href="#nextjs_standalone_build-srcs">srcs</a>, <a href="#nextjs_standalone_build-next_js_binary">next_js_binary</a>, <a href="#nextjs_standalone_build-data">data</a>, <a href="#nextjs_standalone_build-kwargs">kwargs</a>)
</pre>

Compile a standalone Next.js application.

See https://nextjs.org/docs/app/api-reference/config/next-config-js/output#automatically-copying-traced-files

NOTE: a `next.config.mjs` is generated, wrapping the passed `config`, to overcome Next.js limitation with bazel,
rules_js and pnpm (with hoist=false, as required by rules_js).

Due to the generated `next.config.mjs` file the `nextjs_standalone_build(config)` must have a unique name
or file path that does not conflict with standard Next.js config files.

Issues worked around by the generated config include:
* https://github.com/vercel/next.js/issues/48017
* https://github.com/aspect-build/rules_js/issues/714

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="nextjs_standalone_build-name"></a>name |  the name of the build target   |  none |
| <a id="nextjs_standalone_build-config"></a>config |  the Next.js config file   |  none |
| <a id="nextjs_standalone_build-srcs"></a>srcs |  the sources to include in the build, including any transitive deps   |  none |
| <a id="nextjs_standalone_build-next_js_binary"></a>next_js_binary |  the Next.js binary to use for building   |  none |
| <a id="nextjs_standalone_build-data"></a>data |  the data files to include in the build   |  `[]` |
| <a id="nextjs_standalone_build-kwargs"></a>kwargs |  Other attributes passed to all targets such as `tags`, env   |  none |

<a id="nextjs_standalone_server"></a>

## nextjs_standalone_server

<pre>
nextjs_standalone_server(<a href="#nextjs_standalone_server-name">name</a>, <a href="#nextjs_standalone_server-app">app</a>, <a href="#nextjs_standalone_server-pkg">pkg</a>, <a href="#nextjs_standalone_server-data">data</a>, <a href="#nextjs_standalone_server-kwargs">kwargs</a>)
</pre>

Configures the output of a standalone Next.js application to be a standalone server binary.

See the Next.js [standalone server documentation](https://nextjs.org/docs/app/api-reference/config/next-config-js/output#automatically-copying-traced-files)
for details on the standalone server directory structure.

This function is normally used in conjunction with `nextjs_standalone_build` to create a standalone
Next.js application. The standalone server is a `js_binary` target that can be run with `bazel run`
or deployed in a container image etc.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="nextjs_standalone_server-name"></a>name |  the name of the binary target   |  none |
| <a id="nextjs_standalone_server-app"></a>app |  the standalone app directory, typically the output of `nextjs_standalone_build`   |  none |
| <a id="nextjs_standalone_server-pkg"></a>pkg |  the directory server.js is in within the standalone/ directory.<br><br>This is normally the application path relative to the pnpm-lock.yaml.<br><br>Default: native.package_name() (for a pnpm-lock.yaml in the root of the workspace)   |  `None` |
| <a id="nextjs_standalone_server-data"></a>data |  runtime data required to run the standalone server.<br><br>Normally requires `[":node_modules/next", ":node_modules/react"]` which are not included in the Next.js standalone output.   |  `[]` |
| <a id="nextjs_standalone_server-kwargs"></a>kwargs |  additional `js_binary` attributes   |  none |

<a id="nextjs_start"></a>

## nextjs_start

<pre>
nextjs_start(<a href="#nextjs_start-name">name</a>, <a href="#nextjs_start-config">config</a>, <a href="#nextjs_start-app">app</a>, <a href="#nextjs_start-next_js_binary">next_js_binary</a>, <a href="#nextjs_start-data">data</a>, <a href="#nextjs_start-kwargs">kwargs</a>)
</pre>

Run the Next.js production server for an app.

See https://nextjs.org/docs/pages/api-reference/cli/next#next-start-options

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="nextjs_start-name"></a>name |  the name of the build target   |  none |
| <a id="nextjs_start-config"></a>config |  the Next.js config file   |  none |
| <a id="nextjs_start-app"></a>app |  the pre-compiled Next.js application, typically the output of `nextjs_build`   |  none |
| <a id="nextjs_start-next_js_binary"></a>next_js_binary |  The next `js_binary` target to use for running Next.js<br><br>Typically this is a js_binary target created using `bin` loaded from the `package_json.bzl` file of the npm package.<br><br>See main docstring above for example usage.   |  none |
| <a id="nextjs_start-data"></a>data |  additional server data   |  `[]` |
| <a id="nextjs_start-kwargs"></a>kwargs |  Other attributes passed to all targets such as `tags`, env   |  none |


# npm_link_package.md


npm_link_package rule

<a id="npm_link_package"></a>

## npm_link_package

<pre>
npm_link_package(<a href="#npm_link_package-name">name</a>, <a href="#npm_link_package-root_package">root_package</a>, <a href="#npm_link_package-link">link</a>, <a href="#npm_link_package-src">src</a>, <a href="#npm_link_package-deps">deps</a>, <a href="#npm_link_package-fail_if_no_link">fail_if_no_link</a>, <a href="#npm_link_package-auto_manual">auto_manual</a>, <a href="#npm_link_package-visibility">visibility</a>,
                 <a href="#npm_link_package-kwargs">kwargs</a>)
</pre>

"Links an npm package to node_modules if link is True.

When called at the root_package, a package store target is generated named `link__{bazelified_name}__store`.

When linking, a `{name}` target is generated which consists of the `node_modules/<package>` symlink and transitively
its package store link and the package store links of the transitive closure of deps.

When linking, `{name}/dir` filegroup is also generated that refers to a directory artifact can be used to access
the package directory for creating entry points or accessing files in the package.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="npm_link_package-name"></a>name |  The name of the link target to create if `link` is True. For first-party deps linked across a workspace, the name must match in all packages being linked as it is used to derive the package store link target name.   |  none |
| <a id="npm_link_package-root_package"></a>root_package |  the root package where the node_modules package store is linked to   |  `""` |
| <a id="npm_link_package-link"></a>link |  whether or not to link in this package If false, only the npm_package_store target will be created _if_ this is called in the `root_package`.   |  `True` |
| <a id="npm_link_package-src"></a>src |  the npm_package target to link; may only to be specified when linking in the root package   |  `None` |
| <a id="npm_link_package-deps"></a>deps |  list of npm_package_store; may only to be specified when linking in the root package   |  `{}` |
| <a id="npm_link_package-fail_if_no_link"></a>fail_if_no_link |  whether or not to fail if this is called in a package that is not the root package and `link` is False   |  `True` |
| <a id="npm_link_package-auto_manual"></a>auto_manual |  whether or not to automatically add a manual tag to the generated targets Links tagged "manual" dy default is desirable so that they are not built by `bazel build ...` if they are unused downstream. For 3rd party deps, this is particularly important so that 3rd party deps are not fetched at all unless they are used.   |  `True` |
| <a id="npm_link_package-visibility"></a>visibility |  the visibility of the link target   |  `["//visibility:public"]` |
| <a id="npm_link_package-kwargs"></a>kwargs |  see attributes of npm_package_store rule   |  none |

**RETURNS**

Label of the npm_link_package_store if created, else None


# faq.md

## Flaky build failure: Exec failed due to IOException

Known issue: we sometimes see

```
(00:55:55) ERROR: /mnt/ephemeral/workdir/BUILD.bazel:46:22: Copying directory aspect_rules_js~1.37.0~npm~npm__picocolors__1.0.0/package failed: Exec failed due to IOException: /mnt/ephemeral/output/__main__/execroot/_main/external/aspect_rules_js~1.37.0~npm~npm__picocolors__1.0.0/package (No such file or directory)
```

This is most likely caused by https://github.com/bazelbuild/bazel/issues/22073. You can either update to Bazel 7.2.0rc1 or later or temporarily add this line to `.bazelrc`:

```
common --noexperimental_merged_skyframe_analysis_execution
```

## Why does my program fail with "Module not found"?

See the [Troubleshooting guide](./troubleshooting.md).

## Making the editor happy

Editors (and the language services they host) expect a couple of things:

-   third-party tooling like the TypeScript SDK under `<project root>/node_modules`
-   types for your first-party imports

Since rules_js puts the outputs under Bazel's `bazel-out` tree, the editor doesn't find them by default.

To get local tooling installed, you can continue to run `pnpm install` (or use whatever package manager your lockfile is for)
to get a `node_modules` tree in your project.
If there are many packages to install, you could reduce this by only installing the tooling
actually needed for non-Bazel workflows, like the `@types/*` packages and `typescript`.

To resolve first-party imports like `import '@myorg/my_lib'` to resolve in TypeScript, use the
`paths` key in the `tsconfig.json` file to list additional search locations.
This is the same thing you'd do outside of Bazel.
See [example](https://github.com/aspect-build/rules_ts/blob/74d54bda208695d7e8992520e560166875cfbce7/examples/simple/tsconfig.json#L4-L10).

## Bazel isn't seeing my changes to package.json

rules_js relies on what's in the `pnpm-lock.yaml` file. Make sure your changes are reflected there.

Set `update_pnpm_lock` to True in your `npm_translate_lock` rule and Bazel will auto-update your
`pnpm-lock.yaml` when any of its inputs change. When you do this, add all files required
for pnpm to generate the `pnpm-lock.yaml` to the `data` attribute of `npm_translate_lock`. This will
include the `pnpm-workspace.yaml` if it exists and all `package.json` files in your pnpm workspace.

To list all local `package.json` files that pnpm needs to read, you can run
`pnpm recursive ls --depth -1 --porcelain`.

## Can a tool run outside of Bazel write to the `node_modules` in `bazel-out`?

Some tools such as the AWS SDK write to `node_modules` when they are run. Ideally this should be avoided or fixed in an upstream package. Bazel write-protects the files in the `bazel-out` output tree so they can be reliably cached and reused.

If necessary the `node_modules` directory permissions can be manually modified, however these changes will be detected and overwritten next time Bazel runs. To maintain these edits across Bazel runs, you can use the `--experimental_check_output_files=false` flag.

## Can I edit files in `node_modules` for debugging?

Try running Bazel with `--experimental_check_output_files=false` so that your edits inside the `bazel-out/node_modules` tree are preserved.

## Can I use bazel-managed pnpm?

Yes, just run `bazel run -- @pnpm//:pnpm --dir $PWD` followed by the usual arguments to pnpm.

If you're bootstrapping a new project, you'll need to add this to your WORKSPACE:

```starlark
load("@aspect_rules_js//npm:repositories.bzl", "pnpm_repository")

pnpm_repository(name = "pnpm")
```

Or, if you're using [bzlmod](https://bazel.build/external/overview#bzlmod), add these lines to your MODULE.bazel:

```starlark
pnpm = use_extension("@aspect_rules_js//npm:extensions.bzl", "pnpm", dev_dependency = True)

use_repo(pnpm, "pnpm")
```

This defines the `@pnpm` repository so that you can create the lockfile with
`bazel run -- @pnpm//:pnpm --dir $PWD install --lockfile-only`, and then once the file exists you'll
be able to add the `pnpm_translate_lock` to the `WORKSPACE` which requires the lockfile.

Consider documenting running pnpm through bazel as a good practice for your team, so that all developers run the exact same pnpm and node versions that Bazel does.

## Why can't Bazel fetch an npm package?

If the error looks like this: `failed to fetch. no such package '@npm__foo__1.2.3//': at offset 773, object has duplicate key`
then you are hitting https://github.com/bazelbuild/bazel/issues/15605

The workaround is to patch the package.json of any offending packages in npm_translate_lock, see https://github.com/aspect-build/rules_js/issues/148#issuecomment-1144378565.
Or, if a newer version of the package has fixed the duplicate keys, you could upgrade.

If the error looks like this: `ERR_PNPM_FETCH_404 GET https://registry.npmjs.org/@my-workspace%2Ffoo: Not Found - 404`, where `foo` is a package living in a workspace in your local
codebase and it's being declared [`pnpm-workspace.yaml`](https://pnpm.io/pnpm-workspace_yaml) and that you are relying on the `yarn_lock` attribute of `npm_translate_lock`, then
you're hitting a caveat of the migration process.

The workaround is to generate the `pnpm-lock.yaml` on your own as mentioned in the migration guide and to use the `pnpm_lock` attribute of `npm_translate_lock` instead.

## In my monorepo, can Bazel output multiple packages under one dist/ folder?

Many projects have a structure like the following:

```
my-workspace/
├─ packages/
│  ├─ lib1/
│  └─ lib2/
└─ dist/
   ├─ lib1/
   └─ lib2/
```

However, Bazel has a constraint that outputs for a given Bazel package (a directory containing a `BUILD` file) must be written under the corresponding output folder. This means that you have two choices:

1. **Keep your output structure the same.** This implies there must be a single `BUILD` file under `my-workspace`, since this is the only Bazel package which can output to paths beneath `my-workspace/dist`. The downside is that this `BUILD` file may get long, accumulate a lot of `load` statements, and the paths inside will be longer.

The result looks like this:

```
my-workspace/
├─ BUILD.bazel
├─ packages/
│  ├─ lib1/
│  └─ lib2/
└─ bazel-bin/packages/
   ├─ lib1/
   └─ lib2/
```

2. **Change your output structure** to distribute `dist` folders beneath `lib1` and `lib2`. Now you can have `BUILD` files underneath each library, which is more Bazel-idiomatic.

The result looks like this:

```
my-workspace/
├─ packages/
│  ├─ lib1/
│  |  └─ BUILD.bazel
│  ├─ lib2/
│  |  └─ BUILD.bazel
└─ bazel-bin/packages/
   ├─ lib1/
   |  └─ dist/
   └─ lib2/
      └─ dist/
```

Note that when following option 2, it might require updating some configuration files which refer to the original output locations. For example, your `tsconfig.json` file might have a `paths` section which points to the `../../dist` folder.

To keep your legacy build system working during the migration, you might want to avoid changing those configuration files in-place. For this purpose, you can use [the `jq` rule](https://github.com/bazel-contrib/bazel-lib/blob/main/docs/jq.md) in place of `copy_to_bin`, using a `filter` expression so the copy of the configuration file in `bazel-bin` that's used by the Bazel build can have a different path than the configuration file in the source tree.

# migrate_2.md
# Migrating from rules_js 1.x to rules_js 2.x

MOVED to <https://docs.aspect.build/guides/rules_js_2_migration>

# js_binary.md


Rules for running JavaScript programs under Bazel, as tools or with `bazel run` or `bazel test`.

For example, this binary references the `acorn` npm package which was already linked
using an API like `npm_link_all_packages`.

```starlark
load("@aspect_rules_js//js:defs.bzl", "js_binary", "js_test")

js_binary(
    name = "bin",
    # Reference the location where the acorn npm module was linked in the root Bazel package
    data = ["//:node_modules/acorn"],
    entry_point = "require_acorn.js",
)
```

<a id="js_binary"></a>

## js_binary

<pre>
js_binary(<a href="#js_binary-name">name</a>, <a href="#js_binary-data">data</a>, <a href="#js_binary-chdir">chdir</a>, <a href="#js_binary-copy_data_to_bin">copy_data_to_bin</a>, <a href="#js_binary-enable_runfiles">enable_runfiles</a>, <a href="#js_binary-entry_point">entry_point</a>, <a href="#js_binary-env">env</a>, <a href="#js_binary-expand_args">expand_args</a>,
          <a href="#js_binary-expand_env">expand_env</a>, <a href="#js_binary-expected_exit_code">expected_exit_code</a>, <a href="#js_binary-fixed_args">fixed_args</a>, <a href="#js_binary-include_npm">include_npm</a>, <a href="#js_binary-include_npm_sources">include_npm_sources</a>,
          <a href="#js_binary-include_sources">include_sources</a>, <a href="#js_binary-include_transitive_sources">include_transitive_sources</a>, <a href="#js_binary-include_transitive_types">include_transitive_types</a>, <a href="#js_binary-include_types">include_types</a>,
          <a href="#js_binary-log_level">log_level</a>, <a href="#js_binary-no_copy_to_bin">no_copy_to_bin</a>, <a href="#js_binary-node_options">node_options</a>, <a href="#js_binary-node_toolchain">node_toolchain</a>, <a href="#js_binary-patch_node_fs">patch_node_fs</a>,
          <a href="#js_binary-preserve_symlinks_main">preserve_symlinks_main</a>)
</pre>

Execute a program in the Node.js runtime.

The version of Node.js is determined by Bazel's toolchain selection. In the WORKSPACE you used
`nodejs_register_toolchains` to provide options to Bazel. Then Bazel selects from these options
based on the requested target platform. Use the
[`--toolchain_resolution_debug`](https://docs.bazel.build/versions/main/command-line-reference.html#flag--toolchain_resolution_debug)
Bazel option to see more detail about the selection.

All [common binary attributes](https://bazel.build/reference/be/common-definitions#common-attributes-binaries) are supported
including `args` as the list of arguments passed Node.js.

Node.js execution is performed by a shell script that sets environment variables and runs the Node.js binary with the `entry_point` script.
The shell script is located relative to the directory containing the `js_binary` at `\{name\}_/\{name\}` similar to other rulesets
such as rules_go. See [PR #1690](https://github.com/aspect-build/rules_js/pull/1690) for more information on this naming scheme.

The following environment variables are made available to the Node.js runtime based on available Bazel [Make variables](https://bazel.build/reference/be/make-variables#predefined_variables):

* JS_BINARY__BINDIR: the WORKSPACE-relative Bazel bin directory; equivalent to the `$(BINDIR)` Make variable of the `js_binary` target
* JS_BINARY__COMPILATION_MODE: One of `fastbuild`, `dbg`, or `opt` as set by [`--compilation_mode`](https://bazel.build/docs/user-manual#compilation-mode); equivalent to `$(COMPILATION_MODE)` Make variable of the `js_binary` target
* JS_BINARY__TARGET_CPU: the target cpu architecture; equivalent to `$(TARGET_CPU)` Make variable of the `js_binary` target

The following environment variables are made available to the Node.js runtime based on the rule context:

* JS_BINARY__BUILD_FILE_PATH: the WORKSPACE-relative path to the BUILD file of the Bazel target being run; equivalent to `ctx.build_file_path` of the `js_binary` target's rule context
* JS_BINARY__PACKAGE: the package of the Bazel target being run; equivalent to `ctx.label.package` of the `js_binary` target's rule context
* JS_BINARY__TARGET: the full label of the Bazel target being run; a stringified version of `ctx.label` of the `js_binary` target's rule context
* JS_BINARY__TARGET_NAME: the name of the Bazel target being run; equivalent to `ctx.label.name` of the `js_binary` target's rule context
* JS_BINARY__WORKSPACE: the Bazel workspace name; equivalent to `ctx.workspace_name` of the `js_binary` target's rule context

The following environment variables are made available to the Node.js runtime based the runtime environment:

* JS_BINARY__NODE_BINARY: the Node.js binary path run by the `js_binary` target
* JS_BINARY__NPM_BINARY: the npm binary path; this is available when [`include_npm`](https://docs.aspect.build/rules/aspect_rules_js/docs/js_binary#include_npm) is `True` on the `js_binary` target
* JS_BINARY__NODE_WRAPPER: the Node.js wrapper script used to run Node.js which is available as `node` on the `PATH` at runtime
* JS_BINARY__RUNFILES: the absolute path to the Bazel runfiles directory
* JS_BINARY__EXECROOT: the absolute path to the root of the execution root for the action; if in the sandbox, this path absolute path to the root of the execution root within the sandbox

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="js_binary-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="js_binary-data"></a>data |  Runtime dependencies of the program.<br><br>The transitive closure of the `data` dependencies will be available in the .runfiles folder for this binary/test.<br><br>NB: `data` files are copied to the Bazel output tree before being passed as inputs to runfiles. See `copy_data_to_bin` docstring for more info.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="js_binary-chdir"></a>chdir |  Working directory to run the binary or test in, relative to the workspace.<br><br>By default, `js_binary` runs in the root of the output tree.<br><br>To run in the directory containing the `js_binary` use<br><br>    chdir = package_name()<br><br>(or if you're in a macro, use `native.package_name()`)<br><br>WARNING: this will affect other paths passed to the program, either as arguments or in configuration files, which are workspace-relative.<br><br>You may need `../../` segments to re-relativize such paths to the new working directory. In a `BUILD` file you could do something like this to point to the output path:<br><br><pre><code class="language-python">js_binary(&#10;    ...&#10;    chdir = package_name(),&#10;    # ../.. segments to re-relative paths from the chdir back to workspace;&#10;    # add an additional 3 segments to account for running js_binary running&#10;    # in the root of the output tree&#10;    args = ["/".join([".."] * len(package_name().split("/"))) + "$(rootpath //path/to/some:file)"],&#10;)</code></pre>   | String | optional |  `""`  |
| <a id="js_binary-copy_data_to_bin"></a>copy_data_to_bin |  When True, `data` files and the `entry_point` file are copied to the Bazel output tree before being passed as inputs to runfiles.<br><br>Defaults to True so that a `js_binary` with the default value is compatible with `js_run_binary` with `use_execroot_entry_point` set to True, the default there.<br><br>Setting this to False is more optimal in terms of inputs, but there is a yet unresolved issue of ESM imports skirting the node fs patches and escaping the sandbox: https://github.com/aspect-build/rules_js/issues/362. This is hit in some popular test runners such as mocha, which use native `import()` statements (https://github.com/aspect-build/rules_js/pull/353). When set to False, a program such as mocha that uses ESM imports may escape the execroot by following symlinks into the source tree. When set to True, such a program would escape the sandbox but will end up in the output tree where `node_modules` and other inputs required will be available.   | Boolean | optional |  `True`  |
| <a id="js_binary-enable_runfiles"></a>enable_runfiles |  Whether runfiles are enabled in the current build configuration.<br><br>Typical usage of this rule is via a macro which automatically sets this attribute based on a `config_setting` rule.   | Boolean | required |  |
| <a id="js_binary-entry_point"></a>entry_point |  The main script which is evaluated by node.js.<br><br>This is the module referenced by the `require.main` property in the runtime.<br><br>This must be a target that provides a single file or a `DirectoryPathInfo` from `@aspect_bazel_lib//lib::directory_path.bzl`.<br><br>See https://github.com/bazel-contrib/bazel-lib/blob/main/docs/directory_path.md for more info on creating a target that provides a `DirectoryPathInfo`.   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |
| <a id="js_binary-env"></a>env |  Environment variables of the action.<br><br>Subject to [$(location)](https://bazel.build/reference/be/make-variables#predefined_label_variables) and ["Make variable"](https://bazel.build/reference/be/make-variables) substitution if `expand_env` is set to True.   | <a href="https://bazel.build/rules/lib/dict">Dictionary: String -> String</a> | optional |  `{}`  |
| <a id="js_binary-expand_args"></a>expand_args |  Enables [$(location)](https://bazel.build/reference/be/make-variables#predefined_label_variables) and ["Make variable"](https://bazel.build/reference/be/make-variables) substitution for `fixed_args`.<br><br>This comes at some analysis-time cost even for a set of args that does not have any expansions.   | Boolean | optional |  `True`  |
| <a id="js_binary-expand_env"></a>expand_env |  Enables [$(location)](https://bazel.build/reference/be/make-variables#predefined_label_variables) and ["Make variable"](https://bazel.build/reference/be/make-variables) substitution for `env`.<br><br>This comes at some analysis-time cost even for a set of envs that does not have any expansions.   | Boolean | optional |  `True`  |
| <a id="js_binary-expected_exit_code"></a>expected_exit_code |  The expected exit code.<br><br>Can be used to write tests that are expected to fail.   | Integer | optional |  `0`  |
| <a id="js_binary-fixed_args"></a>fixed_args |  Fixed command line arguments to pass to the Node.js when this binary target is executed.<br><br>Subject to [$(location)](https://bazel.build/reference/be/make-variables#predefined_label_variables) and ["Make variable"](https://bazel.build/reference/be/make-variables) substitution if `expand_args` is set to True.<br><br>Unlike the built-in `args`, which are only passed to the target when it is executed either by the `bazel run` command or as a test, `fixed_args` are baked into the generated launcher script so are always passed even when the binary target is run outside of Bazel directly from the launcher script.<br><br>`fixed_args` are passed before the ones specified in `args` and before ones that are specified on the `bazel run` or `bazel test` command line.<br><br>See https://bazel.build/reference/be/common-definitions#common-attributes-binaries for more info on the built-in `args` attribute.   | List of strings | optional |  `[]`  |
| <a id="js_binary-include_npm"></a>include_npm |  When True, npm is included in the runfiles of the target.<br><br>An npm binary is also added on the PATH so tools can spawn npm processes. This is a bash script on Linux and MacOS and a batch script on Windows.<br><br>A minimum of rules_nodejs version 5.7.0 is required which contains the Node.js toolchain changes to use npm.   | Boolean | optional |  `False`  |
| <a id="js_binary-include_npm_sources"></a>include_npm_sources |  When True, files in `npm_sources` from `JsInfo` providers in `data` targets are included in the runfiles of the target.<br><br>`transitive_files` from `NpmPackageStoreInfo` providers in `data` targets are also included in the runfiles of the target.   | Boolean | optional |  `True`  |
| <a id="js_binary-include_sources"></a>include_sources |  When True, `sources` from `JsInfo` providers in `data` targets are included in the runfiles of the target.   | Boolean | optional |  `True`  |
| <a id="js_binary-include_transitive_sources"></a>include_transitive_sources |  When True, `transitive_sources` from `JsInfo` providers in `data` targets are included in the runfiles of the target.   | Boolean | optional |  `True`  |
| <a id="js_binary-include_transitive_types"></a>include_transitive_types |  When True, `transitive_types` from `JsInfo` providers in `data` targets are included in the runfiles of the target.<br><br>Defaults to False since types are generally not needed at runtime and introducing them could slow down developer round trip time due to having to generate typings on source file changes.   | Boolean | optional |  `False`  |
| <a id="js_binary-include_types"></a>include_types |  When True, `types` from `JsInfo` providers in `data` targets are included in the runfiles of the target.<br><br>Defaults to False since types are generally not needed at runtime and introducing them could slow down developer round trip time due to having to generate typings on source file changes.<br><br>NB: These are types from direct `data` dependencies only. You may also need to set `include_transitive_types` to True.   | Boolean | optional |  `False`  |
| <a id="js_binary-log_level"></a>log_level |  Set the logging level.<br><br>Log from are written to stderr. They will be supressed on success when running as the tool of a js_run_binary when silent_on_success is True. In that case, they will be shown only on a build failure along with the stdout & stderr of the node tool being run.<br><br>Log levels: fatal, error, warn, info, debug   | String | optional |  `"error"`  |
| <a id="js_binary-no_copy_to_bin"></a>no_copy_to_bin |  List of files to not copy to the Bazel output tree when `copy_data_to_bin` is True.<br><br>This is useful for exceptional cases where a `copy_to_bin` is not possible or not suitable for an input file such as a file in an external repository. In most cases, this option is not needed. See `copy_data_to_bin` docstring for more info.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="js_binary-node_options"></a>node_options |  Options to pass to the node invocation on the command line.<br><br>https://nodejs.org/api/cli.html<br><br>These options are passed directly to the node invocation on the command line. Options passed here will take precendence over options passed via the NODE_OPTIONS environment variable. Options passed here are not added to the NODE_OPTIONS environment variable so will not be automatically picked up by child processes that inherit that enviroment variable.   | List of strings | optional |  `[]`  |
| <a id="js_binary-node_toolchain"></a>node_toolchain |  The Node.js toolchain to use for this target.<br><br>See https://bazel-contrib.github.io/rules_nodejs/Toolchains.html<br><br>Typically this is left unset so that Bazel automatically selects the right Node.js toolchain for the target platform. See https://bazel.build/extending/toolchains#toolchain-resolution for more information.   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="js_binary-patch_node_fs"></a>patch_node_fs |  Patch the to Node.js `fs` API (https://nodejs.org/api/fs.html) for this node program to prevent the program from following symlinks out of the execroot, runfiles and the sandbox.<br><br>When enabled, `js_binary` patches the Node.js sync and async `fs` API functions `lstat`, `readlink`, `realpath`, `readdir` and `opendir` so that the node program being run cannot resolve symlinks out of the execroot and the runfiles tree. When in the sandbox, these patches prevent the program being run from resolving symlinks out of the sandbox.<br><br>When disabled, node programs can leave the execroot, runfiles and sandbox by following symlinks which can lead to non-hermetic behavior.   | Boolean | optional |  `True`  |
| <a id="js_binary-preserve_symlinks_main"></a>preserve_symlinks_main |  When True, the --preserve-symlinks-main flag is passed to node.<br><br>This prevents node from following an ESM entry script out of runfiles and the sandbox. This can happen for `.mjs` ESM entry points where the fs node patches, which guard the runfiles and sandbox, are not applied. See https://github.com/aspect-build/rules_js/issues/362 for more information. Once #362 is resolved, the default for this attribute can be set to False.<br><br>This flag was added in Node.js v10.2.0 (released 2018-05-23). If your node toolchain is configured to use a Node.js version older than this you'll need to set this attribute to False.<br><br>See https://nodejs.org/api/cli.html#--preserve-symlinks-main for more information.   | Boolean | optional |  `True`  |

<a id="js_test"></a>

## js_test

<pre>
js_test(<a href="#js_test-name">name</a>, <a href="#js_test-data">data</a>, <a href="#js_test-chdir">chdir</a>, <a href="#js_test-copy_data_to_bin">copy_data_to_bin</a>, <a href="#js_test-enable_runfiles">enable_runfiles</a>, <a href="#js_test-entry_point">entry_point</a>, <a href="#js_test-env">env</a>, <a href="#js_test-expand_args">expand_args</a>,
        <a href="#js_test-expand_env">expand_env</a>, <a href="#js_test-expected_exit_code">expected_exit_code</a>, <a href="#js_test-fixed_args">fixed_args</a>, <a href="#js_test-include_npm">include_npm</a>, <a href="#js_test-include_npm_sources">include_npm_sources</a>, <a href="#js_test-include_sources">include_sources</a>,
        <a href="#js_test-include_transitive_sources">include_transitive_sources</a>, <a href="#js_test-include_transitive_types">include_transitive_types</a>, <a href="#js_test-include_types">include_types</a>, <a href="#js_test-log_level">log_level</a>,
        <a href="#js_test-no_copy_to_bin">no_copy_to_bin</a>, <a href="#js_test-node_options">node_options</a>, <a href="#js_test-node_toolchain">node_toolchain</a>, <a href="#js_test-patch_node_fs">patch_node_fs</a>, <a href="#js_test-preserve_symlinks_main">preserve_symlinks_main</a>)
</pre>

Identical to js_binary, but usable under `bazel test`.

All [common test attributes](https://bazel.build/reference/be/common-definitions#common-attributes-tests) are
supported including `args` as the list of arguments passed Node.js.

Bazel will set environment variables when a test target is run under `bazel test` and `bazel run`
that a test runner can use.

A runner can write arbitrary outputs files it wants Bazel to pickup and save with the test logs to
`TEST_UNDECLARED_OUTPUTS_DIR`. These get zipped up and saved along with the test logs.

JUnit XML reports can be written to `XML_OUTPUT_FILE` for Bazel to consume.

`TEST_TMPDIR` is an absolute path to a private writeable directory that the test runner can use for
creating temporary files.

LCOV coverage reports can be written to `COVERAGE_OUTPUT_FILE` when running under `bazel coverage`
or if the `--coverage` flag is set.

See the Bazel [Test encyclopedia](https://bazel.build/reference/test-encyclopedia) for details on
the contract between Bazel and a test runner.

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="js_test-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="js_test-data"></a>data |  Runtime dependencies of the program.<br><br>The transitive closure of the `data` dependencies will be available in the .runfiles folder for this binary/test.<br><br>NB: `data` files are copied to the Bazel output tree before being passed as inputs to runfiles. See `copy_data_to_bin` docstring for more info.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="js_test-chdir"></a>chdir |  Working directory to run the binary or test in, relative to the workspace.<br><br>By default, `js_binary` runs in the root of the output tree.<br><br>To run in the directory containing the `js_binary` use<br><br>    chdir = package_name()<br><br>(or if you're in a macro, use `native.package_name()`)<br><br>WARNING: this will affect other paths passed to the program, either as arguments or in configuration files, which are workspace-relative.<br><br>You may need `../../` segments to re-relativize such paths to the new working directory. In a `BUILD` file you could do something like this to point to the output path:<br><br><pre><code class="language-python">js_binary(&#10;    ...&#10;    chdir = package_name(),&#10;    # ../.. segments to re-relative paths from the chdir back to workspace;&#10;    # add an additional 3 segments to account for running js_binary running&#10;    # in the root of the output tree&#10;    args = ["/".join([".."] * len(package_name().split("/"))) + "$(rootpath //path/to/some:file)"],&#10;)</code></pre>   | String | optional |  `""`  |
| <a id="js_test-copy_data_to_bin"></a>copy_data_to_bin |  When True, `data` files and the `entry_point` file are copied to the Bazel output tree before being passed as inputs to runfiles.<br><br>Defaults to True so that a `js_binary` with the default value is compatible with `js_run_binary` with `use_execroot_entry_point` set to True, the default there.<br><br>Setting this to False is more optimal in terms of inputs, but there is a yet unresolved issue of ESM imports skirting the node fs patches and escaping the sandbox: https://github.com/aspect-build/rules_js/issues/362. This is hit in some popular test runners such as mocha, which use native `import()` statements (https://github.com/aspect-build/rules_js/pull/353). When set to False, a program such as mocha that uses ESM imports may escape the execroot by following symlinks into the source tree. When set to True, such a program would escape the sandbox but will end up in the output tree where `node_modules` and other inputs required will be available.   | Boolean | optional |  `True`  |
| <a id="js_test-enable_runfiles"></a>enable_runfiles |  Whether runfiles are enabled in the current build configuration.<br><br>Typical usage of this rule is via a macro which automatically sets this attribute based on a `config_setting` rule.   | Boolean | required |  |
| <a id="js_test-entry_point"></a>entry_point |  The main script which is evaluated by node.js.<br><br>This is the module referenced by the `require.main` property in the runtime.<br><br>This must be a target that provides a single file or a `DirectoryPathInfo` from `@aspect_bazel_lib//lib::directory_path.bzl`.<br><br>See https://github.com/bazel-contrib/bazel-lib/blob/main/docs/directory_path.md for more info on creating a target that provides a `DirectoryPathInfo`.   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |
| <a id="js_test-env"></a>env |  Environment variables of the action.<br><br>Subject to [$(location)](https://bazel.build/reference/be/make-variables#predefined_label_variables) and ["Make variable"](https://bazel.build/reference/be/make-variables) substitution if `expand_env` is set to True.   | <a href="https://bazel.build/rules/lib/dict">Dictionary: String -> String</a> | optional |  `{}`  |
| <a id="js_test-expand_args"></a>expand_args |  Enables [$(location)](https://bazel.build/reference/be/make-variables#predefined_label_variables) and ["Make variable"](https://bazel.build/reference/be/make-variables) substitution for `fixed_args`.<br><br>This comes at some analysis-time cost even for a set of args that does not have any expansions.   | Boolean | optional |  `True`  |
| <a id="js_test-expand_env"></a>expand_env |  Enables [$(location)](https://bazel.build/reference/be/make-variables#predefined_label_variables) and ["Make variable"](https://bazel.build/reference/be/make-variables) substitution for `env`.<br><br>This comes at some analysis-time cost even for a set of envs that does not have any expansions.   | Boolean | optional |  `True`  |
| <a id="js_test-expected_exit_code"></a>expected_exit_code |  The expected exit code.<br><br>Can be used to write tests that are expected to fail.   | Integer | optional |  `0`  |
| <a id="js_test-fixed_args"></a>fixed_args |  Fixed command line arguments to pass to the Node.js when this binary target is executed.<br><br>Subject to [$(location)](https://bazel.build/reference/be/make-variables#predefined_label_variables) and ["Make variable"](https://bazel.build/reference/be/make-variables) substitution if `expand_args` is set to True.<br><br>Unlike the built-in `args`, which are only passed to the target when it is executed either by the `bazel run` command or as a test, `fixed_args` are baked into the generated launcher script so are always passed even when the binary target is run outside of Bazel directly from the launcher script.<br><br>`fixed_args` are passed before the ones specified in `args` and before ones that are specified on the `bazel run` or `bazel test` command line.<br><br>See https://bazel.build/reference/be/common-definitions#common-attributes-binaries for more info on the built-in `args` attribute.   | List of strings | optional |  `[]`  |
| <a id="js_test-include_npm"></a>include_npm |  When True, npm is included in the runfiles of the target.<br><br>An npm binary is also added on the PATH so tools can spawn npm processes. This is a bash script on Linux and MacOS and a batch script on Windows.<br><br>A minimum of rules_nodejs version 5.7.0 is required which contains the Node.js toolchain changes to use npm.   | Boolean | optional |  `False`  |
| <a id="js_test-include_npm_sources"></a>include_npm_sources |  When True, files in `npm_sources` from `JsInfo` providers in `data` targets are included in the runfiles of the target.<br><br>`transitive_files` from `NpmPackageStoreInfo` providers in `data` targets are also included in the runfiles of the target.   | Boolean | optional |  `True`  |
| <a id="js_test-include_sources"></a>include_sources |  When True, `sources` from `JsInfo` providers in `data` targets are included in the runfiles of the target.   | Boolean | optional |  `True`  |
| <a id="js_test-include_transitive_sources"></a>include_transitive_sources |  When True, `transitive_sources` from `JsInfo` providers in `data` targets are included in the runfiles of the target.   | Boolean | optional |  `True`  |
| <a id="js_test-include_transitive_types"></a>include_transitive_types |  When True, `transitive_types` from `JsInfo` providers in `data` targets are included in the runfiles of the target.<br><br>Defaults to False since types are generally not needed at runtime and introducing them could slow down developer round trip time due to having to generate typings on source file changes.   | Boolean | optional |  `False`  |
| <a id="js_test-include_types"></a>include_types |  When True, `types` from `JsInfo` providers in `data` targets are included in the runfiles of the target.<br><br>Defaults to False since types are generally not needed at runtime and introducing them could slow down developer round trip time due to having to generate typings on source file changes.<br><br>NB: These are types from direct `data` dependencies only. You may also need to set `include_transitive_types` to True.   | Boolean | optional |  `False`  |
| <a id="js_test-log_level"></a>log_level |  Set the logging level.<br><br>Log from are written to stderr. They will be supressed on success when running as the tool of a js_run_binary when silent_on_success is True. In that case, they will be shown only on a build failure along with the stdout & stderr of the node tool being run.<br><br>Log levels: fatal, error, warn, info, debug   | String | optional |  `"error"`  |
| <a id="js_test-no_copy_to_bin"></a>no_copy_to_bin |  List of files to not copy to the Bazel output tree when `copy_data_to_bin` is True.<br><br>This is useful for exceptional cases where a `copy_to_bin` is not possible or not suitable for an input file such as a file in an external repository. In most cases, this option is not needed. See `copy_data_to_bin` docstring for more info.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="js_test-node_options"></a>node_options |  Options to pass to the node invocation on the command line.<br><br>https://nodejs.org/api/cli.html<br><br>These options are passed directly to the node invocation on the command line. Options passed here will take precendence over options passed via the NODE_OPTIONS environment variable. Options passed here are not added to the NODE_OPTIONS environment variable so will not be automatically picked up by child processes that inherit that enviroment variable.   | List of strings | optional |  `[]`  |
| <a id="js_test-node_toolchain"></a>node_toolchain |  The Node.js toolchain to use for this target.<br><br>See https://bazel-contrib.github.io/rules_nodejs/Toolchains.html<br><br>Typically this is left unset so that Bazel automatically selects the right Node.js toolchain for the target platform. See https://bazel.build/extending/toolchains#toolchain-resolution for more information.   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="js_test-patch_node_fs"></a>patch_node_fs |  Patch the to Node.js `fs` API (https://nodejs.org/api/fs.html) for this node program to prevent the program from following symlinks out of the execroot, runfiles and the sandbox.<br><br>When enabled, `js_binary` patches the Node.js sync and async `fs` API functions `lstat`, `readlink`, `realpath`, `readdir` and `opendir` so that the node program being run cannot resolve symlinks out of the execroot and the runfiles tree. When in the sandbox, these patches prevent the program being run from resolving symlinks out of the sandbox.<br><br>When disabled, node programs can leave the execroot, runfiles and sandbox by following symlinks which can lead to non-hermetic behavior.   | Boolean | optional |  `True`  |
| <a id="js_test-preserve_symlinks_main"></a>preserve_symlinks_main |  When True, the --preserve-symlinks-main flag is passed to node.<br><br>This prevents node from following an ESM entry script out of runfiles and the sandbox. This can happen for `.mjs` ESM entry points where the fs node patches, which guard the runfiles and sandbox, are not applied. See https://github.com/aspect-build/rules_js/issues/362 for more information. Once #362 is resolved, the default for this attribute can be set to False.<br><br>This flag was added in Node.js v10.2.0 (released 2018-05-23). If your node toolchain is configured to use a Node.js version older than this you'll need to set this attribute to False.<br><br>See https://nodejs.org/api/cli.html#--preserve-symlinks-main for more information.   | Boolean | optional |  `True`  |

<a id="js_binary_lib.create_launcher"></a>

## js_binary_lib.create_launcher

<pre>
js_binary_lib.create_launcher(<a href="#js_binary_lib.create_launcher-ctx">ctx</a>, <a href="#js_binary_lib.create_launcher-log_prefix_rule_set">log_prefix_rule_set</a>, <a href="#js_binary_lib.create_launcher-log_prefix_rule">log_prefix_rule</a>, <a href="#js_binary_lib.create_launcher-fixed_args">fixed_args</a>, <a href="#js_binary_lib.create_launcher-fixed_env">fixed_env</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="js_binary_lib.create_launcher-ctx"></a>ctx |  <p align="center"> - </p>   |  none |
| <a id="js_binary_lib.create_launcher-log_prefix_rule_set"></a>log_prefix_rule_set |  <p align="center"> - </p>   |  none |
| <a id="js_binary_lib.create_launcher-log_prefix_rule"></a>log_prefix_rule |  <p align="center"> - </p>   |  none |
| <a id="js_binary_lib.create_launcher-fixed_args"></a>fixed_args |  <p align="center"> - </p>   |  `[]` |
| <a id="js_binary_lib.create_launcher-fixed_env"></a>fixed_env |  <p align="center"> - </p>   |  `{}` |

<a id="js_binary_lib.implementation"></a>

## js_binary_lib.implementation

<pre>
js_binary_lib.implementation(<a href="#js_binary_lib.implementation-ctx">ctx</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="js_binary_lib.implementation-ctx"></a>ctx |  <p align="center"> - </p>   |  none |


# npm_package.md


Rules for linking npm dependencies and packaging and linking first-party deps.

Load these with,

```starlark
load("@aspect_rules_js//npm:defs.bzl", "npm_package")
```

<a id="npm_package"></a>

## npm_package

<pre>
npm_package(<a href="#npm_package-name">name</a>, <a href="#npm_package-srcs">srcs</a>, <a href="#npm_package-data">data</a>, <a href="#npm_package-args">args</a>, <a href="#npm_package-out">out</a>, <a href="#npm_package-package">package</a>, <a href="#npm_package-version">version</a>, <a href="#npm_package-root_paths">root_paths</a>,
            <a href="#npm_package-include_external_repositories">include_external_repositories</a>, <a href="#npm_package-include_srcs_packages">include_srcs_packages</a>, <a href="#npm_package-exclude_srcs_packages">exclude_srcs_packages</a>,
            <a href="#npm_package-include_srcs_patterns">include_srcs_patterns</a>, <a href="#npm_package-exclude_srcs_patterns">exclude_srcs_patterns</a>, <a href="#npm_package-replace_prefixes">replace_prefixes</a>, <a href="#npm_package-allow_overwrites">allow_overwrites</a>,
            <a href="#npm_package-include_sources">include_sources</a>, <a href="#npm_package-include_types">include_types</a>, <a href="#npm_package-include_transitive_sources">include_transitive_sources</a>, <a href="#npm_package-include_transitive_types">include_transitive_types</a>,
            <a href="#npm_package-include_npm_sources">include_npm_sources</a>, <a href="#npm_package-include_runfiles">include_runfiles</a>, <a href="#npm_package-hardlink">hardlink</a>, <a href="#npm_package-publishable">publishable</a>, <a href="#npm_package-verbose">verbose</a>, <a href="#npm_package-kwargs">kwargs</a>)
</pre>

A macro that packages sources into a directory (a tree artifact) and provides an `NpmPackageInfo`.

This target can be used as the `src` attribute to `npm_link_package`.

With `publishable = True` the macro also produces a target `[name].publish`, that can be run to publish to an npm registry.
Under the hood, this target runs `npm publish`. You can pass arguments to npm by escaping them from Bazel using a double-hyphen,
for example: `bazel run //path/to:my_package.publish -- --tag=next`

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

`npm_package` makes use of `copy_to_directory`
(https://docs.aspect.build/rules/aspect_bazel_lib/docs/copy_to_directory) under the hood,
adopting its API and its copy action using composition. However, unlike `copy_to_directory`,
`npm_package` includes direct and transitive sources and types files from `JsInfo` providers in srcs
by default. The behavior of including sources and types from `JsInfo` can be configured
using the `include_sources`, `include_transitive_sources`, `include_types`, `include_transitive_types`.

The two `include*_types` options may cause type-check actions to run, which slows down your
development round-trip.

As of rules_js 2.0, the recommended solution for avoiding eager type-checking when linking
1p deps is to link `js_library` or any `JsInfo` producing targets directly without the
indirection of going through an `npm_package` target (see https://github.com/aspect-build/rules_js/pull/1646
for more details).

`npm_package` can also include npm packages sources and default runfiles from `srcs` which `copy_to_directory` does not.
These behaviors can be configured with the `include_npm_sourfes` and `include_runfiles` attributes
respectively.

The default `include_srcs_packages`, `[".", "./**"]`, prevents files from outside of the target's
package and subpackages from being included.

The default `exclude_srcs_patterns`, of `["node_modules/**", "**/node_modules/**"]`, prevents
`node_modules` files from being included.

To stamp the current git tag as the "version" in the package.json file, see
[stamped_package_json](#stamped_package_json)

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="npm_package-name"></a>name |  Unique name for this target.   |  none |
| <a id="npm_package-srcs"></a>srcs |  Files and/or directories or targets that provide `DirectoryPathInfo` to copy into the output directory.   |  `[]` |
| <a id="npm_package-data"></a>data |  Runtime / linktime npm dependencies of this npm package.<br><br>`NpmPackageStoreInfo` providers are gathered from `JsInfo` of the targets specified. Targets can be linked npm packages, npm package store targets or other targets that provide `JsInfo`. This is done directly from the `npm_package_store_infos` field of these. For linked npm package targets, the underlying npm_package_store target(s) that back the links is used.<br><br>Gathered `NpmPackageStoreInfo` providers are used downstream as direct dependencies of this npm package when linking with `npm_link_package`.   |  `[]` |
| <a id="npm_package-args"></a>args |  Arguments that are passed down to `<name>.publish` target and `npm publish` command.   |  `[]` |
| <a id="npm_package-out"></a>out |  Path of the output directory, relative to this package.   |  `None` |
| <a id="npm_package-package"></a>package |  The package name. If set, should match the `name` field in the `package.json` file for this package.<br><br>If set, the package name set here will be used for linking if a npm_link_package does not specify a package name. A npm_link_package that specifies a package name will override the value here when linking.<br><br>If unset, a npm_link_package that references this npm_package must define the package name must be for linking.   |  `""` |
| <a id="npm_package-version"></a>version |  The package version. If set, should match the `version` field in the `package.json` file for this package.<br><br>If set, a npm_link_package may omit the package version and the package version set here will be used for linking. A npm_link_package that specifies a package version will override the value here when linking.<br><br>If unset, a npm_link_package that references this npm_package must define the package version must be for linking.   |  `"0.0.0"` |
| <a id="npm_package-root_paths"></a>root_paths |  List of paths (with glob support) that are roots in the output directory.<br><br>If any parent directory of a file being copied matches one of the root paths patterns specified, the output directory path will be the path relative to the root path instead of the path relative to the file's workspace. If there are multiple root paths that match, the longest match wins.<br><br>Matching is done on the parent directory of the output file path so a trailing '**' glob patterm will match only up to the last path segment of the dirname and will not include the basename. Only complete path segments are matched. Partial matches on the last segment of the root path are ignored.<br><br>Forward slashes (`/`) should be used as path separators.<br><br>A `"."` value expands to the target's package path (`ctx.label.package`).<br><br>Defaults to `["."]` which results in the output directory path of files in the target's package and and sub-packages are relative to the target's package and files outside of that retain their full workspace relative paths.<br><br>Globs are supported (see rule docstring above).   |  `["."]` |
| <a id="npm_package-include_external_repositories"></a>include_external_repositories |  List of external repository names (with glob support) to include in the output directory.<br><br>Files from external repositories are only copied into the output directory if the external repository they come from matches one of the external repository patterns specified.<br><br>When copied from an external repository, the file path in the output directory defaults to the file's path within the external repository. The external repository name is _not_ included in that path.<br><br>For example, the following copies `@external_repo//path/to:file` to `path/to/file` within the output directory.<br><br><pre><code>npp_package(&#10;    name = "dir",&#10;    include_external_repositories = ["external_*"],&#10;    srcs = ["@external_repo//path/to:file"],&#10;)</code></pre><br><br>Files that come from matching external are subject to subsequent filters and transformations to determine if they are copied and what their path in the output directory will be. The external repository name of the file from an external repository is not included in the output directory path and is considered in subsequent filters and transformations.<br><br>Globs are supported (see rule docstring above).   |  `[]` |
| <a id="npm_package-include_srcs_packages"></a>include_srcs_packages |  List of Bazel packages (with glob support) to include in output directory.<br><br>Files in srcs are only copied to the output directory if the Bazel package of the file matches one of the patterns specified.<br><br>Forward slashes (`/`) should be used as path separators. A first character of `"."` will be replaced by the target's package path.<br><br>Defaults to ["./**"] which includes sources target's package and subpackages.<br><br>Files that have matching Bazel packages are subject to subsequent filters and transformations to determine if they are copied and what their path in the output directory will be.<br><br>Globs are supported (see rule docstring above).   |  `["./**"]` |
| <a id="npm_package-exclude_srcs_packages"></a>exclude_srcs_packages |  List of Bazel packages (with glob support) to exclude from output directory.<br><br>Files in srcs are not copied to the output directory if the Bazel package of the file matches one of the patterns specified.<br><br>Forward slashes (`/`) should be used as path separators. A first character of `"."` will be replaced by the target's package path.<br><br>Defaults to ["**/node_modules/**"] which excludes all node_modules folders from the output directory.<br><br>Files that have do not have matching Bazel packages are subject to subsequent filters and transformations to determine if they are copied and what their path in the output directory will be.<br><br>Globs are supported (see rule docstring above).   |  `[]` |
| <a id="npm_package-include_srcs_patterns"></a>include_srcs_patterns |  List of paths (with glob support) to include in output directory.<br><br>Files in srcs are only copied to the output directory if their output directory path, after applying `root_paths`, matches one of the patterns specified.<br><br>Forward slashes (`/`) should be used as path separators.<br><br>Defaults to `["**"]` which includes all sources.<br><br>Files that have matching output directory paths are subject to subsequent filters and transformations to determine if they are copied and what their path in the output directory will be.<br><br>Globs are supported (see rule docstring above).   |  `["**"]` |
| <a id="npm_package-exclude_srcs_patterns"></a>exclude_srcs_patterns |  List of paths (with glob support) to exclude from output directory.<br><br>Files in srcs are not copied to the output directory if their output directory path, after applying `root_paths`, matches one of the patterns specified.<br><br>Forward slashes (`/`) should be used as path separators.<br><br>Files that do not have matching output directory paths are subject to subsequent filters and transformations to determine if they are copied and what their path in the output directory will be.<br><br>Globs are supported (see rule docstring above).   |  `["**/node_modules/**"]` |
| <a id="npm_package-replace_prefixes"></a>replace_prefixes |  Map of paths prefixes (with glob support) to replace in the output directory path when copying files.<br><br>If the output directory path for a file starts with or fully matches a a key in the dict then the matching portion of the output directory path is replaced with the dict value for that key. The final path segment matched can be a partial match of that segment and only the matching portion will be replaced. If there are multiple keys that match, the longest match wins.<br><br>Forward slashes (`/`) should be used as path separators.<br><br>Replace prefix transformation are the final step in the list of filters and transformations. The final output path of a file being copied into the output directory is determined at this step.<br><br>Globs are supported (see rule docstring above).   |  `{}` |
| <a id="npm_package-allow_overwrites"></a>allow_overwrites |  If True, allow files to be overwritten if the same output file is copied to twice.<br><br>The order of srcs matters as the last copy of a particular file will win when overwriting. Performance of `npm_package` will be slightly degraded when allow_overwrites is True since copies cannot be parallelized out as they are calculated. Instead all copy paths must be calculated before any copies can be started.   |  `False` |
| <a id="npm_package-include_sources"></a>include_sources |  When True, `sources` from `JsInfo` providers in `srcs` targets are included in the list of available files to copy.   |  `True` |
| <a id="npm_package-include_types"></a>include_types |  When True, `types` from `JsInfo` providers in `srcs` targets are included in the list of available files to copy.   |  `True` |
| <a id="npm_package-include_transitive_sources"></a>include_transitive_sources |  When True, `transitive_sources` from `JsInfo` providers in `srcs` targets are included in the list of available files to copy.   |  `True` |
| <a id="npm_package-include_transitive_types"></a>include_transitive_types |  When True, `transitive_types` from `JsInfo` providers in `srcs` targets are included in the list of available files to copy.   |  `True` |
| <a id="npm_package-include_npm_sources"></a>include_npm_sources |  When True, `npm_sources` from `JsInfo` providers in `srcs` targets are included in the list of available files to copy.   |  `False` |
| <a id="npm_package-include_runfiles"></a>include_runfiles |  When True, default runfiles from `srcs` targets are included in the list of available files to copy.<br><br>This may be needed in a few cases:<br><br>- to work-around issues with rules that don't provide everything needed in sources, transitive_sources, types & transitive_types - to depend on the runfiles targets that don't use JsInfo<br><br>NB: The default value will be flipped to False in the next major release as runfiles are not needed in the general case and adding them to the list of files available to copy can add noticeable overhead to the analysis phase in a large repository with many npm_package targets.   |  `False` |
| <a id="npm_package-hardlink"></a>hardlink |  Controls when to use hardlinks to files instead of making copies.<br><br>Creating hardlinks is much faster than making copies of files with the caveat that hardlinks share file permissions with their source.<br><br>Since Bazel removes write permissions on files in the output tree after an action completes, hardlinks to source files are not recommended since write permissions will be inadvertently removed from sources files.<br><br>- `auto`: hardlinks are used for generated files already in the output tree - `off`: all files are copied - `on`: hardlinks are used for all files (not recommended)   |  `"auto"` |
| <a id="npm_package-publishable"></a>publishable |  When True, enable generation of `{name}.publish` target   |  `False` |
| <a id="npm_package-verbose"></a>verbose |  If true, prints out verbose logs to stdout   |  `False` |
| <a id="npm_package-kwargs"></a>kwargs |  Additional attributes such as `tags` and `visibility`   |  none |

<a id="npm_package_lib.implementation"></a>

## npm_package_lib.implementation

<pre>
npm_package_lib.implementation(<a href="#npm_package_lib.implementation-ctx">ctx</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="npm_package_lib.implementation-ctx"></a>ctx |  <p align="center"> - </p>   |  none |

<a id="stamped_package_json"></a>

## stamped_package_json

<pre>
stamped_package_json(<a href="#stamped_package_json-name">name</a>, <a href="#stamped_package_json-stamp_var">stamp_var</a>, <a href="#stamped_package_json-kwargs">kwargs</a>)
</pre>

Convenience wrapper to set the "version" property in package.json with the git tag.

In unstamped builds (typically those without `--stamp`) the version will be set to `0.0.0`.
This ensures that actions which use the package.json file can get cache hits.

For more information on stamping, read https://docs.aspect.build/rules/aspect_bazel_lib/docs/stamping.

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="stamped_package_json-name"></a>name |  name of the resulting `jq` target, must be "package"   |  none |
| <a id="stamped_package_json-stamp_var"></a>stamp_var |  a key from the bazel-out/stable-status.txt or bazel-out/volatile-status.txt files   |  none |
| <a id="stamped_package_json-kwargs"></a>kwargs |  additional attributes passed to the jq rule, see https://docs.aspect.build/rules/aspect_bazel_lib/docs/jq   |  none |


# pnpm.md
# pnpm and rules_js

rules_js models npm package dependency handling on [pnpm](https://pnpm.io/). Our design goal is to closely mimic pnpm's behavior.

Our story begins when some non-Bazel-specific tool (typically pnpm) performs dependency resolutions
and solves version constraints.
It also determines how the `node_modules` tree will be structured for runtime.
This information is encoded into a lockfile which is checked into the source repository.

The pnpm lockfile format includes all the information needed to define [`npm_import`](/docs/npm_import.md#npm_import) rules for each package,
allowing Bazel's downloader to do the fetches individually. This info includes the integrity hash, as calculated by the package manager,
so that Bazel can guarantee supply-chain security.

Bazel will only fetch the packages which are required for the requested targets to be analyzed.
Thus it is performant to convert a very large `pnpm-lock.yaml` file without concern for
users needing to fetch many unnecessary packages. We have benchmarked this code with
800+ importers and ~15,000 npm packages to run in 3sec, when Bazel determines that an input changed.

While the [`npm_import`](/docs/npm_import.md#npm_import) rule can be used to bring individual packages into Bazel,
most users will want to import their entire lockfile.
The `npm_translate_lock` rule does this, and its operation is described below.
You may wish to read the [generated API documentation](/docs/npm_import.md#npm_translate_lock) as well.

## Rules overview

As a high level overview, the primary rules and targets used by developers to fetch and link npm package dependencies are:

-   [`npm_translate_lock()`](/docs/npm_import.md#npm_translate_lock) - generate targets representing packages from a pnpm lockfile.
-   [`npm_link_all_packages()`](/docs/npm_link_all_packages.md) - defines a `node_modules` tree and the associated `node_modules/{package}` targets. This rule is required in the BUILD file of each package in the pnpm workspace that has npm packages linked into a `node_modules` folder as well the BUILD file of the package that corresponds to the root of the pnpm workspace where the pnpm lock file resides.
-   `:node_modules/{package}` - targets generated by `npm_link_all_packages()` representing each package dependency from a `package.json` within the pnpm workspace.

For example:

```
pnpm-lock.yaml
WORKSPACE.bazel
> npm_translate_lock()
BUILD.bazel
> npm_link_all_packages()
├── A/
    ├── BUILD.bazel
        > npm_link_all_packages()
├── B/
    ├── BUILD.bazel
        > npm_link_all_packages()
```

Where the lockfile was generated from a pnpm workspace with two projects, A and B:

```
package.json
pnpm-lock.yaml
pnpm-workspace.yaml
├── A/
    ├── package.json
├── B/
    ├── package.json
```

Bazel targets such as `js_library()` rules can now depend on npm packages using the `:node_modules/{package}` targets generated from each `npm_link_all_packages()`.
The `:node_modules/{package}` targets accessible to a package align with how Node.js resolves npm dependencies: `node_modules` from the current directory BUILD and above can be depended on for resolution at runtime.

## Using npm_translate_lock

In `WORKSPACE`, call the repository rule pointing to your `pnpm-lock.yaml` file:

```starlark
load("@aspect_rules_js//npm:repositories.bzl", "npm_translate_lock")

# Uses the pnpm-lock.yaml file to automate creation of npm_import rules
npm_translate_lock(
    # Creates a new repository named "@npm" - you could choose any name you like
    name = "npm",
    pnpm_lock = "//:pnpm-lock.yaml",
    # Bazel 7.x and earlier: this attribute checks the .bazelignore file covers all node_modules folders.
    # Bazel 8.0 can use https://bazel.build/rules/lib/globals/repo#ignore_directories:
    #   ignore_directories(["**/node_modules"])
    # in REPO.bazel
    verify_node_modules_ignored = "//:.bazelignore",
)
```

You can immediately load from the generated `repositories.bzl` file in `WORKSPACE`.
This is similar to the
[`pip_parse`](https://github.com/bazelbuild/rules_python/blob/main/docs/pip.md#pip_parse)
rule in rules_python for example.
It has the advantage of also creating aliases for simpler dependencies that don't require
spelling out the version of the packages.

```starlark
# Following our example above, we named this "npm"
load("@npm//:repositories.bzl", "npm_repositories")

npm_repositories()
```

Note that you could call `npm_translate_lock` more than once, if you have more than one pnpm workspace in your Bazel workspace.

If you really don't want to rely on this being generated at runtime, we have experimental support
to check in the result instead. See [checked-in repositories.bzl](#checked-in-repositoriesbzl) below.

## Hoisting

The `node_modules` tree laid out by `rules_js` should be bug-for-bug compatible with the `node_modules` tree that
pnpm lays out, when [hoisting](https://pnpm.io/npmrc#hoist) is disabled.

To make the behavior outside of Bazel match, we recommend adding `hoist=false` to your `.npmrc`:

```shell
echo "hoist=false" >> .npmrc
```

This will prevent pnpm from creating a hidden `node_modules/.pnpm/node_modules` folder with hoisted
dependencies which allows packages to depend on "phantom" undeclared dependencies.
With hoisting disabled, most import/require failures (in type-checking or at runtime)
in 3rd party npm packages when using `rules_js` will be reproducible with pnpm outside of Bazel.

`rules_js` does not and will not support pnpm "phantom" [hoisting](https://pnpm.io/npmrc#hoist) which allows for
packages to depend on undeclared dependencies.
All dependencies between packages must be declared under `rules_js` in order to support lazy fetching and lazy linking of npm dependencies.

See [Troubleshooting](./troubleshooting.md) for suggestions on how to fix problems caused by hoisting.

## Creating and updating the pnpm-lock.yaml file

### Manual (typical)

If your developers are fully converted to using pnpm, then they'll likely perform workflows like
adding new dependencies by running the pnpm tool in the source directory outside of Bazel.
This results in updates to the `pnpm-lock.yaml` file, and then Bazel naturally finds those updates
next time it reads the file.

### update_pnpm_lock

During a migration, you may have a legacy lockfile from another package manager.
You can use the `update_pnpm_lock` attribute of `npm_translate_lock` to have
Bazel manage the `pnpm-lock.yaml` file for you.
You might also choose this mode if you want changes like additions to `package.json` to be automatically
reflected in the lockfile, unlike a typical frontend developer workflow.

Use of `update_pnpm_lock` requires the `data` attribute be used as well.
This should include the `pnpm-workspace.yaml` file as well as all `package.json` files
in the pnpm workspace.
The pnpm lock file update will fail if `data` is missing any files required to run
`pnpm install --lockfile-only` or `pnpm import`.

> To list all local `package.json` files that pnpm needs to read, you can run
> `pnpm recursive ls --depth -1 --porcelain`.

When the `pnpm-lock.yaml` file needs updating, `npm_translate_lock` will automatically:

-   run `pnpm import` if there is a `npm_package_lock` or `yarn_lock` attribute specified.
-   run `pnpm install --lockfile-only` otherwise.

To update the `pnpm-lock.yaml` file manually, either

-   [install pnpm](https://pnpm.io/installation) and run `pnpm install --lockfile-only` or `pnpm import`
-   use the Bazel-managed pnpm by running `bazel run -- @pnpm//:pnpm --dir $PWD install --lockfile-only` or `bazel run -- @pnpm//:pnpm --dir $PWD import`

If the `ASPECT_RULES_JS_FROZEN_PNPM_LOCK` environment variable is set and `update_pnpm_lock` is True,
the build will fail if the pnpm lock file needs updating.

It is recommended to set this environment variable on CI when `update_pnpm_lock` is True.

If the `ASPECT_RULES_JS_DISABLE_UPDATE_PNPM_LOCK` environment variable is set, `update_pnpm_lock` is disabled
even if set to True. This can be useful for some CI uses cases where multiple jobs run Bazel by you
only want one of the jobs checking that the pnpm lock file is up-to-date.

#### `npm_translate_lock_<hash>`

A `.aspect/rules/external_repository_action_cache/npm_translate_lock_<hash>` file will be created and
used to determine when the `pnpm-lock.yaml` file should be updated. This file persists the state of
package and lock files that may effect the `pnpm-lock.yaml` generation and should be checked into the
source control along with the `pnpm-lock.yaml` file.

The `npm_translate_lock_<hash>` file has been a known source of merge conflicts in workspaces with
frequent lockfile or `package.json` changes. As a generated file manual resolution of merge conflicts
is unnecessary as it should only be generated and updated by `npm_translate_lock`.
To reduce the impact on developer workflows `git` can be configured to ignore merge conflicts using
`.gitattributes` and a [custom merge driver](https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver).
See our [blog post](https://blog.aspect.build/easier-merges-on-lockfiles) for a longer explanation.

First, mark the `npm_translate_lock_<hash>` file (with `<hash>` replaced with the hash generated in your workspace)
to use a custom custom merge driver, in this example named `ours`:

```
.aspect/rules/external_repository_action_cache/npm_translate_lock_<hash>= merge=ours
```

Second, developers must define the `ours` custom merge driver in their git configuration to always accept local change:

```
git config --global merge.ours.driver true
```

## Working with packages

### Patching via pnpm.patchedDependencies

Patches included in [pnpm.patchedDependencies](https://pnpm.io/next/package_json#pnpmpatcheddependencies) are automatically applied by rules_js.

These patches must be included in the `data` attribute of `npm_translate_lock`, for example:

```json
{
    ...
    "pnpm": {
        "patchedDependencies": {
            "fum@0.0.1": "patches/fum@0.0.1.patch"
        }
    }
}
```

```starlark
npm_translate_lock(
    ...
    data = [
        "//:patches/fum@0.0.1.patch",
    ],
)
```

Patching applied by rules_js may slightly deviate from standard pnpm patching behavior.
The [bazel-lib patch util](https://github.com/bazel-contrib/bazel-lib/blob/main/docs/repo_utils.md#patch)
is used for patching within rules_js instead of the internal pnpm patching mechanism.
For example a bad patch file may be partially applied when using pnpm outside of bazel but fail
when applied by rules_js, see [rules_js #1915](https://github.com/aspect-build/rules_js/issues/1915).

### Patching via `patches` attribute

We recommend patching via [pnpm.patchedDependencies](#patching-via-pnpmpatcheddependencies) as above, but if you are importing
a yarn or npm lockfile and do not have this field in your package.json, you can apply additional
patches using the `patches` and `patch_args` attributes of `npm_translate_lock`.

These are designed to be similar to the same-named attributes of
[http_archive](https://bazel.build/rules/lib/repo/http#http_archive-patch_args).

Paths in patch files must be relative to the root of the package.
If the version is left out of the package name, the patch will be applied to every version of the npm package.

`patch_args` defaults to `-p0`, but `-p1` will usually be needed for patches generated by git.

In case multiple entries in `patches` match, the list of patches are additive.
(More specific matches are appended to previous matches.)
However if multiple entries in `patch_args` match, then the more specific name matches take precedence.

Patches in `patches` are applied after any patches included in `pnpm.patchedDependencies`.

For example,

```starlark
npm_translate_lock(
    ...
    patches = {
        "@foo/bar": ["//:patches/foo+bar.patch"],
        "fum@0.0.1": ["//:patches/fum@0.0.1.patch"],
    },
    patch_args = {
        "*": ["-p1"],
        "@foo/bar": ["-p0"],
        "fum@0.0.1": ["-p2"],
    },
)
```

### Lifecycles

npm packages have "lifecycle scripts" such as `postinstall` which are documented here:
<https://docs.npmjs.com/cli/v9/using-npm/scripts#life-cycle-scripts>

We refer to these as "lifecycle hooks".

The lifecycle hooks of a package are determined by the `package.json` [`pnpm.onlyBuiltDependencies` attribute](https://pnpm.io/package_json#pnpmonlybuiltdependencies).

If `pnpm.onlyBuiltDependencies` is unspecified `npm_translate_lock` will fallback to the legacy pnpm lockfile `requiresBuild` attribute.
This attribute is only available in pnpm _before_ v9, see [pnpm #7707](https://github.com/pnpm/pnpm/issues/7707) for reasons why this attribute was removed.

When a package has lifecycle hooks the `lifecycle_*` attributes are applied to filter which hooks are run and how they are run.

For example, you can restrict lifecycle hooks across all packages to only run `postinstall`:

> `lifecycle_hooks = { "*": ["postinstall"] }` in `npm_translate_lock`.

Because rules_js models the execution of these hooks as build actions, rather than repository rules,
the result can be stored in the remote cache and shared between developers.
Typically these actions are not run in Bazel's action sandbox because of the overhead of setting up and tearing down the sandboxes.

In addition to sandboxing, Bazel supports other `execution_requirements` for actions,
in the attribute of <https://bazel.build/rules/lib/actions#run>.
You can have control over these using the `lifecycle_hooks_execution_requirements` attribute of `npm_translate_lock`.

Some hooks may fail to run under rules_js, and you don't care to run them.
You can use the `lifecycle_hooks_exclude` attribute of `npm_translate_lock` to turn them off for a package,
which is equivalent to setting the `lifecycle_hooks` to an empty list for that package.

You can set environment variables for hook build actions using the `lifecycle_hooks_envs` attribute of `npm_translate_lock`.

Some hooks may depend on environment variables specified depending on [use_default_shell_env](https://bazel.build/rules/lib/builtins/actions#run.use_default_shell_env) which may be enabled for hook build actions using the `lifecycle_hooks_use_default_shell_env` attribute of `npm_translate_lock`. Requires bazel-lib >= 2.4.2.

In case there are multiple matches, some attributes are additive.
(More specific matches are appended to previous matches.)
Other attributes have specificity: the most specific match wins and the others are ignored.

| attribute                              | behavior    |
| -------------------------------------- | ----------- |
| lifecycle_hooks                        | specificity |
| lifecycle_hooks_envs                   | additive    |
| lifecycle_hooks_execution_requirements | specificity |

Here's a complete example of managing lifecycles:

```starlark
npm_translate_lock(
    ...
    lifecycle_hooks = {
        # These three values are the default if lifecycle_hooks was absent
        # do not sort
        "*": [
            "preinstall",
            "install",
            "postinstall",
        ],
        # This package comes from a git url so prepare has to run to compile some things
        "@kubernetes/client-node": ["prepare"],
        # Disable install and preinstall for this package, maybe they are broken
        "fum@0.0.1": ["postinstall"],
    },
    lifecycle_hooks_envs = {
        # Set some values for all hook actions
        "*": [
            "GLOBAL_KEY1=value1",
            "GLOBAL_KEY2=value2",
        ],
        # ... but override for this package
        "@foo/bar": [
            "GLOBAL_KEY2=",
            "PREBULT_BINARY=http://downloadurl",
        ],
    },
    lifecycle_hooks_execution_requirements = {
        # This is the default if lifecycle_hooks_execution_requirements was absent
        "*":         ["no-sandbox"],
        # Omit no-sandbox for this package, maybe it relies on sandboxing to succeed
        "@foo/bar":  [],
        # This one is broken in remote execution for whatever reason
        "fum@0.0.1": ["no-sandbox", "no-remote-exec"],
    }
)
```

In this example:

-   Only the `prepare` lifecycle hook will be run for the `@kubernetes/client-node` npm package,
    only the `postinstall` will be run for `fum` at version 0.0.1,
    and the default hooks are run for remaining packages.
-   `@foo/bar` lifecycle hooks will run with Bazel's sandbox enabled, with an effective environment:
    -   `GLOBAL_KEY1=value1`
    -   `GLOBAL_KEY2=`
    -   `PREBULT_BINARY=http://downloadurl`
-   `fum` at version 0.0.1 has remote execution disabled. Like other packages aside from `@foo/bar`
    the action sandbox is disabled for performance.

## Checked-in repositories.bzl

This usage is experimental and difficult to get right! Read on with caution.

You can check in the `repositories.bzl` file to version control, and load that instead.

This makes it easier to ship a ruleset that has its own npm dependencies, as users don't
have to install those dependencies. It also avoids eager-evaluation of `npm_translate_lock`
for builds that don't need it.
This is similar to the [`update-repos`](https://github.com/bazelbuild/bazel-gazelle#update-repos)
approach from bazel-gazelle.

The tradeoffs are similar to
[this rules_python thread](https://github.com/bazelbuild/rules_python/issues/608).

In a BUILD file, use a rule like
[write_source_files](https://github.com/bazel-contrib/bazel-lib/blob/main/docs/write_source_files.md)
to copy the generated file to the repo and test that it stays updated:

```starlark
write_source_files(
    name = "update_repos",
    files = {
        "repositories.bzl": "@npm//:repositories.bzl",
    },
)
```

Then in `WORKSPACE`, load from that checked-in copy or instruct your users to do so.

# js_image_layer.md


Rules for creating container image layers from js_binary targets

For example, this js_image_layer target outputs `node_modules.tar` and `app.tar` with `/app` prefix.

```starlark
load("@aspect_rules_js//js:defs.bzl", "js_image_layer")

js_image_layer(
    name = "layers",
    binary = "//label/to:js_binary",
    root = "/app",
)
```

<a id="js_image_layer"></a>

## js_image_layer

<pre>
js_image_layer(<a href="#js_image_layer-name">name</a>, <a href="#js_image_layer-binary">binary</a>, <a href="#js_image_layer-compression">compression</a>, <a href="#js_image_layer-generate_empty_layers">generate_empty_layers</a>, <a href="#js_image_layer-layer_groups">layer_groups</a>, <a href="#js_image_layer-owner">owner</a>, <a href="#js_image_layer-platform">platform</a>,
               <a href="#js_image_layer-preserve_symlinks">preserve_symlinks</a>, <a href="#js_image_layer-root">root</a>)
</pre>

Create container image layers from js_binary targets.

By design, js_image_layer doesn't have any preference over which rule assembles the container image.
This means the downstream rule (`oci_image` from [rules_oci](https://github.com/bazel-contrib/rules_oci)
or `container_image` from [rules_docker](https://github.com/bazelbuild/rules_docker)) must
set a proper `workdir` and `cmd` to for the container work.

A proper `cmd` usually looks like /`[ js_image_layer 'root' ]`/`[ package name of js_image_layer 'binary' target ]/[ name of js_image_layer 'binary' target ]`,
unless you have a custom launcher script that invokes the entry_point of the `js_binary` in a different path.

On the other hand, `workdir` has to be set to the "runfiles tree root" which would be exactly `cmd` **but with `.runfiles/[ name of the workspace ]` suffix**.
If using bzlmod then name of the local workspace is always `_main`. If bzlmod is not enabled then the name of the local workspace, if not otherwise specified
in the `WORKSPACE` file, is `__main__`. If `workdir` is not set correctly, some attributes such as `chdir` might not work properly.

js_image_layer creates up to 5 layers depending on what files are included in the runfiles of the provided
`binary` target.

1. `node` layer contains the Node.js toolchain
2. `package_store_3p` layer contains all 3p npm deps in the `node_modules/.aspect_rules_js` package store
3. `package_store_1p` layer contains all 1p npm deps in the `node_modules/.aspect_rules_js` package store
4. `node_modules` layer contains all `node_modules/*` symlinks which point into the package store
5. `app` layer contains all files that don't fall into any of the above layers

If no files are found in the runfiles of the `binary` target for one of the layers above, that
layer is not generated. All generated layer tarballs are provided as `DefaultInfo` files.

> The rules_js `node_modules/.aspect_rules_js` package store follows the same pattern as the pnpm
> `node_modules/.pnpm` virtual store. For more information see https://pnpm.io/symlinked-node-modules-structure.

js_image_layer also provides an `OutputGroupInfo` with outputs for each of the layers above which
can be used to reference an individual layer with using `filegroup` with `output_group`. For example,

```starlark
js_image_layer(
    name = "layers",
    binary = ":bin",
    root = "/app",
)

filegroup(
    name = "app_tar",
    srcs = [":layers"],
    output_group = "app",
)
```

> WARNING: The structure of the generated layers are not subject to semver guarantees and may change without a notice.
> However, it is guaranteed to work when all generated layers are provided together in the order specified above.

js_image_layer supports transitioning to specific `platform` to allow building multi-platform container images.

**A partial example using rules_oci with transition to linux/amd64 platform.**

```starlark
load("@aspect_rules_js//js:defs.bzl", "js_binary", "js_image_layer")
load("@rules_oci//oci:defs.bzl", "oci_image")

js_binary(
    name = "bin",
    entry_point = "main.js",
)

platform(
    name = "amd64_linux",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
)

js_image_layer(
    name = "layers",
    binary = ":bin",
    platform = ":amd64_linux",
    root = "/app",
)

oci_image(
    name = "image",
    cmd = ["/app/bin"],
    entrypoint = ["bash"],
    tars = [
        ":layers"
    ],
    workdir = select({
        "@aspect_bazel_lib//lib:bzlmod": "/app/bin.runfiles/_main",
        "//conditions:default": "/app/bin.runfiles/__main__",
    }),
)
```

**A partial example using rules_oci to create multi-platform images.**

```starlark
load("@aspect_rules_js//js:defs.bzl", "js_binary", "js_image_layer")
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_image_index")

js_binary(
    name = "bin",
    entry_point = "main.js",
)

[
    platform(
        name = "linux_{}".format(arch),
        constraint_values = [
            "@platforms//os:linux",
            "@platforms//cpu:{}".format(arch if arch != "amd64" else "x86_64"),
        ],
    )

    js_image_layer(
        name = "{}_layers".format(arch),
        binary = ":bin",
        platform = ":linux_{arch}",
        root = "/app",
    )

    oci_image(
        name = "{}_image".format(arch),
        cmd = ["/app/bin"],
        entrypoint = ["bash"],
        tars = [
            ":{}_layers".format(arch)
        ],
        workdir = select({
            "@aspect_bazel_lib//lib:bzlmod": "/app/bin.runfiles/_main",
            "//conditions:default": "/app/bin.runfiles/__main__",
        }),
    )

    for arch in ["amd64", "arm64"]
]

oci_image_index(
    name = "image",
    images = [
        ":arm64_image",
        ":amd64_image"
    ]
)
```

**An example using legacy rules_docker**

See `e2e/js_image_docker` for full example.

```starlark
load("@aspect_rules_js//js:defs.bzl", "js_binary", "js_image_layer")
load("@io_bazel_rules_docker//container:container.bzl", "container_image")

js_binary(
    name = "bin",
    data = [
        "//:node_modules/args-parser",
    ],
    entry_point = "main.js",
)

js_image_layer(
    name = "layers",
    binary = ":bin",
    root = "/app",
    visibility = ["//visibility:__pkg__"],
)

filegroup(
    name = "node_tar",
    srcs = [":layers"],
    output_group = "node",
)

container_layer(
    name = "node_layer",
    tars = [":node_tar"],
)

filegroup(
    name = "package_store_3p_tar",
    srcs = [":layers"],
    output_group = "package_store_3p",
)

container_layer(
    name = "package_store_3p_layer",
    tars = [":package_store_3p_tar"],
)

filegroup(
    name = "package_store_1p_tar",
    srcs = [":layers"],
    output_group = "package_store_1p",
)

container_layer(
    name = "package_store_1p_layer",
    tars = [":package_store_1p_tar"],
)

filegroup(
    name = "node_modules_tar",
    srcs = [":layers"],
    output_group = "node_modules",
)

container_layer(
    name = "node_modules_layer",
    tars = [":node_modules_tar"],
)

filegroup(
    name = "app_tar",
    srcs = [":layers"],
    output_group = "app",
)

container_layer(
    name = "app_layer",
    tars = [":app_tar"],
)

container_image(
    name = "image",
    cmd = ["/app/bin"],
    entrypoint = ["bash"],
    layers = [
        ":node_layer",
        ":package_store_3p_layer",
        ":package_store_1p_layer",
        ":node_modules_layer",
        ":app_layer",
    ],
    workdir = select({
        "@aspect_bazel_lib//lib:bzlmod": "/app/bin.runfiles/_main",
        "//conditions:default": "/app/bin.runfiles/__main__",
    }),
)
```

## Performance

For better performance, it is recommended to split the large parts of a `js_binary` to have a separate layer.

The matching order for layer groups is as follows:

1. `layer_groups` are checked in order first
2. If no match is found for `layer_groups`, the `default layer groups` are checked.
3. Any remaining files are placed into the app layer.

The default layer groups are as follows and always created.

```
{
    "node": "/js/private/node-patches/|/bin/nodejs/",
    "package_store_1p": "\.aspect_rules_js/.*@0\.0\.0/node_modules",
    "package_store_3p": "\.aspect_rules_js/.*/node_modules",
    "node_modules": "/node_modules/",
    "app": "", # empty means just match anything.
}
```

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="js_image_layer-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="js_image_layer-binary"></a>binary |  Label to an js_binary target   | <a href="https://bazel.build/concepts/labels">Label</a> | required |  |
| <a id="js_image_layer-compression"></a>compression |  Compression algorithm. See https://github.com/bazel-contrib/bazel-lib/blob/bdc6ade0ba1ebe88d822bcdf4d4aaa2ce7e2cd37/lib/private/tar.bzl#L29-L39   | String | optional |  `"gzip"`  |
| <a id="js_image_layer-generate_empty_layers"></a>generate_empty_layers |  DEPRECATED. An empty layer is always generated if the layer group have no matching files.   | Boolean | optional |  `False`  |
| <a id="js_image_layer-layer_groups"></a>layer_groups |  Layer groups to create. These are utilized to categorize files into distinct layers, determined by their respective paths. The expected format for each entry is "<key>": "<value>", where <key> MUST be a valid Bazel and JavaScript identifier (alphanumeric characters), and <value> MAY be either an empty string (signifying a universal match) or a valid regular expression.   | <a href="https://bazel.build/rules/lib/dict">Dictionary: String -> String</a> | optional |  `{}`  |
| <a id="js_image_layer-owner"></a>owner |  Owner of the entries, in `GID:UID` format. By default `0:0` (root, root) is used.   | String | optional |  `"0:0"`  |
| <a id="js_image_layer-platform"></a>platform |  Platform to transition.   | <a href="https://bazel.build/concepts/labels">Label</a> | optional |  `None`  |
| <a id="js_image_layer-preserve_symlinks"></a>preserve_symlinks |  Preserve symlinks for entries matching the pattern. By default symlinks within the `node_modules` is preserved.   | String | optional |  `".*/node_modules/.*"`  |
| <a id="js_image_layer-root"></a>root |  Path where the files from js_binary will reside in. eg: /apps/app1 or /app   | String | optional |  `""`  |

<a id="js_image_layer_lib.implementation"></a>

## js_image_layer_lib.implementation

<pre>
js_image_layer_lib.implementation(<a href="#js_image_layer_lib.implementation-ctx">ctx</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="js_image_layer_lib.implementation-ctx"></a>ctx |  <p align="center"> - </p>   |  none |


# npm_link_all_packages.md


Build rules generated by `npm_translate_lock`
=============================================

These are loaded from the external repository created by `npm_translate_lock` based on the name provided.

For example, if you run `npm_translate_lock(name = "npm")` then these rules can be loaded with

```
load("@npm//:defs.bzl", "npm_link_targets", "npm_link_all_packages")
```

<a id="npm_link_all_packages"></a>

## npm_link_all_packages

<pre>
npm_link_all_packages(<a href="#npm_link_all_packages-name">name</a>, <a href="#npm_link_all_packages-imported_links">imported_links</a>)
</pre>

Generated list of npm_link_package() target generators and first-party linked packages corresponding to the packages in {pnpm_lock_label}

If you use manually-written [`npm_import`](/docs/npm_import.md#npm_import) you can link these as well, for example,

    load("@npm//:defs.bzl", "npm_link_all_packages")
    load("@npm_meaning-of-life__links//:defs.bzl", npm_link_meaning_of_life = "npm_link_imported_package")

    npm_link_all_packages(
        name = "node_modules",
        imported_links = [
            npm_link_meaning_of_life,
        ],
    )

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="npm_link_all_packages-name"></a>name |  name of catch all target to generate for all packages linked   |  `"node_modules"` |
| <a id="npm_link_all_packages-imported_links"></a>imported_links |  optional list link functions from manually imported packages that were fetched with npm_import rules.   |  `[]` |

<a id="npm_link_targets"></a>

## npm_link_targets

<pre>
npm_link_targets(<a href="#npm_link_targets-name">name</a>, <a href="#npm_link_targets-package">package</a>)
</pre>

Generated list of target names that are linked by npm_link_all_packages()

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="npm_link_targets-name"></a>name |  name of catch all target to generate for all packages linked   |  `"node_modules"` |
| <a id="npm_link_targets-package"></a>package |  Bazel package to generate targets names for.<br><br>Set to an empty string "" to specify the root package.<br><br>If unspecified, the current package (`native.package_name()`) is used.   |  `None` |

**RETURNS**

A list of target names that are linked by npm_link_all_packages()


# js_info_files.md


Helper rule to gather files from JsInfo providers of targets and provide them as default outputs

<a id="js_info_files"></a>

## js_info_files

<pre>
js_info_files(<a href="#js_info_files-name">name</a>, <a href="#js_info_files-srcs">srcs</a>, <a href="#js_info_files-include_npm_sources">include_npm_sources</a>, <a href="#js_info_files-include_sources">include_sources</a>, <a href="#js_info_files-include_transitive_sources">include_transitive_sources</a>,
              <a href="#js_info_files-include_transitive_types">include_transitive_types</a>, <a href="#js_info_files-include_types">include_types</a>)
</pre>

Gathers files from the JsInfo providers from targets in srcs and provides them as default outputs.

This helper rule is used by the `js_run_binary` macro.

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="js_info_files-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="js_info_files-srcs"></a>srcs |  List of targets to gather files from.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="js_info_files-include_npm_sources"></a>include_npm_sources |  When True, files in `npm_sources` from `JsInfo` providers in `srcs` targets are included in the default outputs of the target.<br><br>`transitive_files` from `NpmPackageStoreInfo` providers in `srcs` targets are also included in the default outputs of the target.   | Boolean | optional |  `True`  |
| <a id="js_info_files-include_sources"></a>include_sources |  When True, `sources` from `JsInfo` providers in `srcs` targets are included in the default outputs of the target.   | Boolean | optional |  `True`  |
| <a id="js_info_files-include_transitive_sources"></a>include_transitive_sources |  When True, `transitive_sources` from `JsInfo` providers in `srcs` targets are included in the default outputs of the target.   | Boolean | optional |  `True`  |
| <a id="js_info_files-include_transitive_types"></a>include_transitive_types |  When True, `transitive_types` from `JsInfo` providers in `srcs` targets are included in the default outputs of the target.<br><br>Defaults to False since types are generally not needed at runtime and introducing them could slow down developer round trip time due to having to generate typings on source file changes.   | Boolean | optional |  `False`  |
| <a id="js_info_files-include_types"></a>include_types |  When True, `types` from `JsInfo` providers in `srcs` targets are included in the default outputs of the target.<br><br>Defaults to False since types are generally not needed at runtime and introducing them could slow down developer round trip time due to having to generate typings on source file changes.<br><br>NB: These are types from direct `srcs` dependencies only. You may also need to set `include_transitive_types` to True.   | Boolean | optional |  `False`  |


# js_library.md


js_library groups together JS sources and arranges them and their transitive and npm dependencies into a provided
`JsInfo`. There are no Bazel actions to run.

For example, this `BUILD` file groups a pair of `.js/.d.ts` files along with the `package.json`.
The latter is needed because it contains a `typings` key that allows downstream
users of this library to resolve the `one.d.ts` file.
The `main` key is another commonly used field in `package.json` which would require including it in the library.

```starlark
load("@aspect_rules_js//js:defs.bzl", "js_library")

js_library(
    name = "one",
    srcs = [
        "one.d.ts",
        "one.js",
        "package.json",
    ],
)
```

| This is similar to [`py_library`](https://docs.bazel.build/versions/main/be/python.html#py_library) which depends on
| Python sources and provides a `PyInfo`.

<a id="js_library"></a>

## js_library

<pre>
js_library(<a href="#js_library-name">name</a>, <a href="#js_library-deps">deps</a>, <a href="#js_library-srcs">srcs</a>, <a href="#js_library-data">data</a>, <a href="#js_library-copy_data_to_bin">copy_data_to_bin</a>, <a href="#js_library-no_copy_to_bin">no_copy_to_bin</a>, <a href="#js_library-types">types</a>)
</pre>

A library of JavaScript sources. Provides JsInfo, the primary provider used in rules_js
and derivative rule sets.

Declaration files are handled separately from sources since they are generally not needed at
runtime and build rules, such as ts_project, are optimal in their build graph if they only depend
on types from `deps` since these they don't need the JavaScript source files from deps to
typecheck.

Linked npm dependences are also handled separately from sources since not all rules require them and it
is optimal for these rules to not depend on them in the build graph.

NB: `js_library` copies all source files to the output tree before providing them in JsInfo. See
https://github.com/aspect-build/rules_js/tree/dbb5af0d2a9a2bb50e4cf4a96dbc582b27567155/docs#javascript
for more context on why we do this.

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="js_library-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="js_library-deps"></a>deps |  Dependencies of this target.<br><br>This may include other js_library targets or other targets that provide JsInfo<br><br>The transitive npm dependencies, transitive sources & runfiles of targets in the `deps` attribute are added to the runfiles of this target. They should appear in the '*.runfiles' area of any executable which is output by or has a runtime dependency on this target.<br><br>If this list contains linked npm packages, npm package store targets or other targets that provide `JsInfo`, `NpmPackageStoreInfo` providers are gathered from `JsInfo`. This is done directly from the `npm_package_store_infos` field of these. For linked npm package targets, the underlying `npm_package_store` target(s) that back the links are used. Gathered `NpmPackageStoreInfo` providers are propagated to the direct dependencies of downstream linked targets.<br><br>NB: Linked npm package targets that are "dev" dependencies do not forward their underlying `npm_package_store` target(s) through `npm_package_store_infos` and will therefore not be propagated to the direct dependencies of downstream linked targets. npm packages that come in from `npm_translate_lock` are considered "dev" dependencies if they are have `dev: true` set in the pnpm lock file. This should be all packages that are only listed as "devDependencies" in all `package.json` files within the pnpm workspace. This behavior is intentional to mimic how `devDependencies` work in published npm packages.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="js_library-srcs"></a>srcs |  Source files that are included in this library.<br><br>This includes all your checked-in code and any generated source files.<br><br>The transitive npm dependencies, transitive sources & runfiles of targets in the `srcs` attribute are added to the runfiles of this target. They should appear in the '*.runfiles' area of any executable which is output by or has a runtime dependency on this target.<br><br>Source files that are JSON files, declaration files or directory artifacts will be automatically provided as "types" available to downstream rules for type checking. To explicitly provide source files as "types" available to downstream rules for type checking that do not match these criteria, move those files to the `types` attribute instead.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="js_library-data"></a>data |  Runtime dependencies to include in binaries/tests that depend on this target.<br><br>The transitive npm dependencies, transitive sources, default outputs and runfiles of targets in the `data` attribute are added to the runfiles of this target. They should appear in the '*.runfiles' area of any executable which has a runtime dependency on this target.<br><br>If this list contains linked npm packages, npm package store targets or other targets that provide `JsInfo`, `NpmPackageStoreInfo` providers are gathered from `JsInfo`. This is done directly from the `npm_package_store_infos` field of these. For linked npm package targets, the underlying `npm_package_store` target(s) that back the links are used. Gathered `NpmPackageStoreInfo` providers are propagated to the direct dependencies of downstream linked targets.<br><br>NB: Linked npm package targets that are "dev" dependencies do not forward their underlying `npm_package_store` target(s) through `npm_package_store_infos` and will therefore not be propagated to the direct dependencies of downstream linked targets. npm packages that come in from `npm_translate_lock` are considered "dev" dependencies if they are have `dev: true` set in the pnpm lock file. This should be all packages that are only listed as "devDependencies" in all `package.json` files within the pnpm workspace. This behavior is intentional to mimic how `devDependencies` work in published npm packages.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="js_library-copy_data_to_bin"></a>copy_data_to_bin |  When True, `data` files are copied to the Bazel output tree before being passed as inputs to runfiles.   | Boolean | optional |  `True`  |
| <a id="js_library-no_copy_to_bin"></a>no_copy_to_bin |  List of files to not copy to the Bazel output tree when `copy_data_to_bin` is True.<br><br>This is useful for exceptional cases where a `copy_to_bin` is not possible or not suitable for an input file such as a file in an external repository. In most cases, this option is not needed. See `copy_data_to_bin` docstring for more info.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="js_library-types"></a>types |  Same as `srcs` except all files are also provided as "types" available to downstream rules for type checking.<br><br>For example, a js_library with only `.js` files that are intended to be imported as `.js` files by downstream type checking rules such as `ts_project` would list those files in `types`:<br><br><pre><code>js_library(&#10;    name = "js_lib",&#10;    types = ["index.js"],&#10;)</code></pre>   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |

<a id="js_library_lib.implementation"></a>

## js_library_lib.implementation

<pre>
js_library_lib.implementation(<a href="#js_library_lib.implementation-ctx">ctx</a>)
</pre>

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="js_library_lib.implementation-ctx"></a>ctx |  <p align="center"> - </p>   |  none |


# npm_import.md


Repository rule to fetch npm packages.

Load this with,

```starlark
load("@aspect_rules_js//npm:repositories.bzl", "npm_import")
```

This uses Bazel's downloader to fetch the packages.
You can use this to redirect all fetches through a store like Artifactory.

See &lt;https://blog.aspect.build/configuring-bazels-downloader&gt; for more info about how it works
and how to configure it.

See [`npm_translate_lock`](#npm_translate_lock) for the primary user-facing API to fetch npm packages
for a given lockfile.

<a id="npm_import"></a>

## npm_import

<pre>
npm_import(<a href="#npm_import-name">name</a>, <a href="#npm_import-package">package</a>, <a href="#npm_import-version">version</a>, <a href="#npm_import-deps">deps</a>, <a href="#npm_import-extra_build_content">extra_build_content</a>, <a href="#npm_import-transitive_closure">transitive_closure</a>, <a href="#npm_import-root_package">root_package</a>,
           <a href="#npm_import-link_workspace">link_workspace</a>, <a href="#npm_import-link_packages">link_packages</a>, <a href="#npm_import-lifecycle_hooks">lifecycle_hooks</a>, <a href="#npm_import-lifecycle_hooks_execution_requirements">lifecycle_hooks_execution_requirements</a>,
           <a href="#npm_import-lifecycle_hooks_env">lifecycle_hooks_env</a>, <a href="#npm_import-lifecycle_hooks_use_default_shell_env">lifecycle_hooks_use_default_shell_env</a>, <a href="#npm_import-integrity">integrity</a>, <a href="#npm_import-url">url</a>, <a href="#npm_import-commit">commit</a>,
           <a href="#npm_import-replace_package">replace_package</a>, <a href="#npm_import-package_visibility">package_visibility</a>, <a href="#npm_import-patch_tool">patch_tool</a>, <a href="#npm_import-patch_args">patch_args</a>, <a href="#npm_import-patches">patches</a>, <a href="#npm_import-custom_postinstall">custom_postinstall</a>,
           <a href="#npm_import-npm_auth">npm_auth</a>, <a href="#npm_import-npm_auth_basic">npm_auth_basic</a>, <a href="#npm_import-npm_auth_username">npm_auth_username</a>, <a href="#npm_import-npm_auth_password">npm_auth_password</a>, <a href="#npm_import-bins">bins</a>, <a href="#npm_import-dev">dev</a>,
           <a href="#npm_import-exclude_package_contents">exclude_package_contents</a>, <a href="#npm_import-kwargs">kwargs</a>)
</pre>

Import a single npm package into Bazel.

Normally you'd want to use `npm_translate_lock` to import all your packages at once.
It generates `npm_import` rules.
You can create these manually if you want to have exact control.

Bazel will only fetch the given package from an external registry if the package is
required for the user-requested targets to be build/tested.

This is a repository rule, which should be called from your `WORKSPACE` file
or some `.bzl` file loaded from it. For example, with this code in `WORKSPACE`:

```starlark
npm_import(
    name = "npm__at_types_node__15.12.2",
    package = "@types/node",
    version = "15.12.2",
    integrity = "sha512-zjQ69G564OCIWIOHSXyQEEDpdpGl+G348RAKY0XXy9Z5kU9Vzv1GMNnkar/ZJ8dzXB3COzD9Mo9NtRZ4xfgUww==",
)
```

In `MODULE.bazel` the same would look like so:

```starlark
npm.npm_import(
    name = "npm__at_types_node__15.12.2",
    package = "@types/node",
    version = "15.12.2",
    integrity = "sha512-zjQ69G564OCIWIOHSXyQEEDpdpGl+G348RAKY0XXy9Z5kU9Vzv1GMNnkar/ZJ8dzXB3COzD9Mo9NtRZ4xfgUww==",v
)
use_repo(npm, "npm__at_types_node__15.12.2")
use_repo(npm, "npm__at_types_node__15.12.2__links")
```

> This is similar to Bazel rules in other ecosystems named "_import" like
> `apple_bundle_import`, `scala_import`, `java_import`, and `py_import`.
> `go_repository` is also a model for this rule.

The name of this repository should contain the version number, so that multiple versions of the same
package don't collide.
(Note that the npm ecosystem always supports multiple versions of a library depending on where
it is required, unlike other languages like Go or Python.)

To consume the downloaded package in rules, it must be "linked" into the link package in the
package's `BUILD.bazel` file:

```
load("@npm__at_types_node__15.12.2__links//:defs.bzl", npm_link_types_node = "npm_link_imported_package")

npm_link_types_node(name = "node_modules")
```

This links `@types/node` into the `node_modules` of this package with the target name `:node_modules/@types/node`.

A `:node_modules/@types/node/dir` filegroup target is also created that provides the the directory artifact of the npm package.
This target can be used to create entry points for binary target or to access files within the npm package.

NB: You can choose any target name for the link target but we recommend using the `node_modules/@scope/name` and
`node_modules/name` convention for readability.

When using `npm_translate_lock`, you can link all the npm dependencies in the lock file for a package:

```
load("@npm//:defs.bzl", "npm_link_all_packages")

npm_link_all_packages(name = "node_modules")
```

This creates `:node_modules/name` and `:node_modules/@scope/name` targets for all direct npm dependencies in the package.
It also creates `:node_modules/name/dir` and `:node_modules/@scope/name/dir` filegroup targets that provide the the directory artifacts of their npm packages.
These target can be used to create entry points for binary target or to access files within the npm package.

If you have a mix of `npm_link_all_packages` and `npm_link_imported_package` functions to call you can pass the
`npm_link_imported_package` link functions to the `imported_links` attribute of `npm_link_all_packages` to link
them all in one call. For example,

```
load("@npm//:defs.bzl", "npm_link_all_packages")
load("@npm__at_types_node__15.12.2__links//:defs.bzl", npm_link_types_node = "npm_link_imported_package")

npm_link_all_packages(
    name = "node_modules",
    imported_links = [
        npm_link_types_node,
    ]
)
```

This has the added benefit of adding the `imported_links` to the convienence `:node_modules` target which
includes all direct dependencies in that package.

NB: You can pass an name to npm_link_all_packages and this will change the targets generated to "{name}/@scope/name" and
"{name}/name". We recommend using "node_modules" as the convention for readability.

To change the proxy URL we use to fetch, configure the Bazel downloader:

1. Make a file containing a rewrite rule like

    `rewrite (registry.npmjs.org)/(.*) artifactory.build.internal.net/artifactory/$1/$2`

1. To understand the rewrites, see [UrlRewriterConfig] in Bazel sources.

1. Point bazel to the config with a line in .bazelrc like
common --experimental_downloader_config=.bazel_downloader_config

Read more about the downloader config: <https://blog.aspect.build/configuring-bazels-downloader>

[UrlRewriterConfig]: https://github.com/bazelbuild/bazel/blob/4.2.1/src/main/java/com/google/devtools/build/lib/bazel/repository/downloader/UrlRewriterConfig.java#L66

**PARAMETERS**

| Name  | Description | Default Value |
| :------------- | :------------- | :------------- |
| <a id="npm_import-name"></a>name |  Name for this repository rule   |  none |
| <a id="npm_import-package"></a>package |  Name of the npm package, such as `acorn` or `@types/node`   |  none |
| <a id="npm_import-version"></a>version |  Version of the npm package, such as `8.4.0`   |  none |
| <a id="npm_import-deps"></a>deps |  A dict other npm packages this one depends on where the key is the package name and value is the version   |  `{}` |
| <a id="npm_import-extra_build_content"></a>extra_build_content |  Additional content to append on the generated BUILD file at the root of the created repository, either as a string or a list of lines similar to <https://github.com/bazelbuild/bazel-skylib/blob/main/docs/write_file_doc.md>.   |  `""` |
| <a id="npm_import-transitive_closure"></a>transitive_closure |  A dict all npm packages this one depends on directly or transitively where the key is the package name and value is a list of version(s) depended on in the closure.   |  `{}` |
| <a id="npm_import-root_package"></a>root_package |  The root package where the node_modules package store is linked to. Typically this is the package that the pnpm-lock.yaml file is located when using `npm_translate_lock`.   |  `""` |
| <a id="npm_import-link_workspace"></a>link_workspace |  The workspace name where links will be created for this package.<br><br>This is typically set in rule sets and libraries that are to be consumed as external repositories so links are created in the external repository and not the user workspace.<br><br>Can be left unspecified if the link workspace is the user workspace.   |  `""` |
| <a id="npm_import-link_packages"></a>link_packages |  Dict of paths where links may be created at for this package to a list of link aliases to link as in each package. If aliases are an empty list this indicates to link as the package name.<br><br>Defaults to {} which indicates that links may be created in any package as specified by the `direct` attribute of the generated npm_link_package.   |  `{}` |
| <a id="npm_import-lifecycle_hooks"></a>lifecycle_hooks |  List of lifecycle hook `package.json` scripts to run for this package if they exist.   |  `[]` |
| <a id="npm_import-lifecycle_hooks_execution_requirements"></a>lifecycle_hooks_execution_requirements |  Execution requirements when running the lifecycle hooks.<br><br>For example:<br><br><pre><code>lifecycle_hooks_execution_requirements: ["no-sandbox', "requires-network"]</code></pre><br><br>This defaults to ["no-sandbox"] to limit the overhead of sandbox creation and copying the output TreeArtifact out of the sandbox.   |  `["no-sandbox"]` |
| <a id="npm_import-lifecycle_hooks_env"></a>lifecycle_hooks_env |  Environment variables set for the lifecycle hooks action for this npm package if there is one.<br><br>Environment variables are defined by providing an array of "key=value" entries.<br><br>For example:<br><br><pre><code>lifecycle_hooks_env: ["PREBULT_BINARY=https://downloadurl"],</code></pre>   |  `[]` |
| <a id="npm_import-lifecycle_hooks_use_default_shell_env"></a>lifecycle_hooks_use_default_shell_env |  If True, the `use_default_shell_env` attribute of lifecycle hook actions is set to True.<br><br>See [use_default_shell_env](https://bazel.build/rules/lib/builtins/actions#run.use_default_shell_env)<br><br>Note: [--incompatible_merge_fixed_and_default_shell_env](https://bazel.build/reference/command-line-reference#flag--incompatible_merge_fixed_and_default_shell_env) is often required and not enabled by default in Bazel < 7.0.0.<br><br>This defaults to False reduce the negative effects of `use_default_shell_env`. Requires bazel-lib >= 2.4.2.   |  `False` |
| <a id="npm_import-integrity"></a>integrity |  Expected checksum of the file downloaded, in Subresource Integrity format. This must match the checksum of the file downloaded.<br><br>This is the same as appears in the pnpm-lock.yaml, yarn.lock or package-lock.json file.<br><br>It is a security risk to omit the checksum as remote files can change.<br><br>At best omitting this field will make your build non-hermetic.<br><br>It is optional to make development easier but should be set before shipping.   |  `""` |
| <a id="npm_import-url"></a>url |  Optional url for this package. If unset, a default npm registry url is generated from the package name and version.<br><br>May start with `git+ssh://` or `git+https://` to indicate a git repository. For example,<br><br><pre><code>git+ssh://git@github.com/org/repo.git</code></pre><br><br>If url is configured as a git repository, the commit attribute must be set to the desired commit.   |  `""` |
| <a id="npm_import-commit"></a>commit |  Specific commit to be checked out if url is a git repository.   |  `""` |
| <a id="npm_import-replace_package"></a>replace_package |  Use the specified npm_package target when linking instead of the fetched sources for this npm package.<br><br>The injected npm_package target may optionally contribute transitive npm package dependencies on top of the transitive dependencies specified in the pnpm lock file for the same package, however, these transitive dependencies must not collide with pnpm lock specified transitive dependencies.<br><br>Any patches specified for this package will be not applied to the injected npm_package target. They will be applied, however, to the fetches sources so they can still be useful for patching the fetched `package.json` file, which is used to determine the generated bin entries for the package.<br><br>NB: lifecycle hooks and custom_postinstall scripts, if implicitly or explicitly enabled, will be run on the injected npm_package. These may be disabled explicitly using the `lifecycle_hooks` attribute.   |  `None` |
| <a id="npm_import-package_visibility"></a>package_visibility |  Visibility of generated node_module link targets.   |  `["//visibility:public"]` |
| <a id="npm_import-patch_tool"></a>patch_tool |  The patch tool to use. If not specified, the `patch` from `PATH` is used.   |  `None` |
| <a id="npm_import-patch_args"></a>patch_args |  Arguments to pass to the patch tool.<br><br>`-p1` will usually be needed for patches generated by git.   |  `["-p0"]` |
| <a id="npm_import-patches"></a>patches |  Patch files to apply onto the downloaded npm package.   |  `[]` |
| <a id="npm_import-custom_postinstall"></a>custom_postinstall |  Custom string postinstall script to run on the installed npm package.<br><br>Runs after any existing lifecycle hooks if any are enabled.   |  `""` |
| <a id="npm_import-npm_auth"></a>npm_auth |  Auth token to authenticate with npm. When using Bearer authentication.   |  `""` |
| <a id="npm_import-npm_auth_basic"></a>npm_auth_basic |  Auth token to authenticate with npm. When using Basic authentication.<br><br>This is typically the base64 encoded string "username:password".   |  `""` |
| <a id="npm_import-npm_auth_username"></a>npm_auth_username |  Auth username to authenticate with npm. When using Basic authentication.   |  `""` |
| <a id="npm_import-npm_auth_password"></a>npm_auth_password |  Auth password to authenticate with npm. When using Basic authentication.   |  `""` |
| <a id="npm_import-bins"></a>bins |  Dictionary of `node_modules/.bin` binary files to create mapped to their node entry points.<br><br>This is typically derived from the "bin" attribute in the package.json file of the npm package being linked.<br><br>For example:<br><br><pre><code>bins = {&#10;    "foo": "./foo.js",&#10;    "bar": "./bar.js",&#10;}</code></pre><br><br>In the future, this field may be automatically populated by npm_translate_lock from information in the pnpm lock file. That feature is currently blocked on https://github.com/pnpm/pnpm/issues/5131.   |  `{}` |
| <a id="npm_import-dev"></a>dev |  Whether this npm package is a dev dependency   |  `False` |
| <a id="npm_import-exclude_package_contents"></a>exclude_package_contents |  List of glob patterns to exclude from the linked package.<br><br>This is useful for excluding files that are not needed in the linked package.<br><br>For example:<br><br><pre><code>exclude_package_contents = ["**/tests/**"]</code></pre>   |  `[]` |
| <a id="npm_import-kwargs"></a>kwargs |  Internal use only   |  none |


# js_filegroup.md


Helper rule to gather files from JsInfo providers of targets and provide them as default outputs

<a id="js_filegroup"></a>

## js_filegroup

<pre>
js_filegroup(<a href="#js_filegroup-name">name</a>, <a href="#js_filegroup-srcs">srcs</a>, <a href="#js_filegroup-include_declarations">include_declarations</a>, <a href="#js_filegroup-include_npm_linked_packages">include_npm_linked_packages</a>, <a href="#js_filegroup-include_sources">include_sources</a>,
             <a href="#js_filegroup-include_transitive_declarations">include_transitive_declarations</a>, <a href="#js_filegroup-include_transitive_sources">include_transitive_sources</a>)
</pre>

Gathers files from the JsInfo providers from targets in srcs and provides them as default outputs.

This helper rule is used by the `js_run_binary` macro.

**ATTRIBUTES**

| Name  | Description | Type | Mandatory | Default |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| <a id="js_filegroup-name"></a>name |  A unique name for this target.   | <a href="https://bazel.build/concepts/labels#target-names">Name</a> | required |  |
| <a id="js_filegroup-srcs"></a>srcs |  List of targets to gather files from.   | <a href="https://bazel.build/concepts/labels">List of labels</a> | optional |  `[]`  |
| <a id="js_filegroup-include_declarations"></a>include_declarations |  When True, `declarations` from `JsInfo` providers in srcs targets are included in the default outputs of the target.<br><br>Defaults to False since declarations are generally not needed at runtime and introducing them could slow down developer round trip time due to having to generate typings on source file changes.   | Boolean | optional |  `False`  |
| <a id="js_filegroup-include_npm_linked_packages"></a>include_npm_linked_packages |  When True, files in `npm_linked_packages` from `JsInfo` providers in srcs targets are included in the default outputs of the target.<br><br>`transitive_files` from `NpmPackageStoreInfo` providers in data targets are also included in the default outputs of the target.   | Boolean | optional |  `True`  |
| <a id="js_filegroup-include_sources"></a>include_sources |  When True, `sources` from `JsInfo` providers in `srcs` targets are included in the default outputs of the target.   | Boolean | optional |  `True`  |
| <a id="js_filegroup-include_transitive_declarations"></a>include_transitive_declarations |  When True, `transitive_declarations` from `JsInfo` providers in srcs targets are included in the default outputs of the target.<br><br>Defaults to False since declarations are generally not needed at runtime and introducing them could slow down developer round trip time due to having to generate typings on source file changes.   | Boolean | optional |  `False`  |
| <a id="js_filegroup-include_transitive_sources"></a>include_transitive_sources |  When True, `transitive_sources` from `JsInfo` providers in `srcs` targets are included in the default outputs of the target.   | Boolean | optional |  `True`  |

