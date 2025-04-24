

# Migrating to Bazel

This page links to migration guides for Bazel.

*  [Maven](/migrate/maven)
*  [Xcode](/migrate/xcode)



# Migrating from Maven to Bazel

This page describes how to migrate from Maven to Bazel, including the
prerequisites and installation steps. It describes the differences between Maven
and Bazel, and provides a migration example using the Guava project.

When migrating from any build tool to Bazel, it's best to have both build tools
running in parallel until you have fully migrated your development team, CI
system, and any other relevant systems. You can run Maven and Bazel in the same
repository.

Note: While Bazel supports downloading and publishing Maven artifacts with
[rules_jvm_external](https://github.com/bazelbuild/rules_jvm_external){: .external}
, it does not directly support Maven-based plugins. Maven plugins can't be
directly run by Bazel since there's no Maven compatibility layer.

## Before you begin

*   [Install Bazel](/install) if it's not yet installed.
*   If you're new to Bazel, go through the tutorial [Introduction to Bazel:
    Build Java](/start/java) before you start migrating. The tutorial explains
    Bazel's concepts, structure, and label syntax.

## Differences between Maven and Bazel

*   Maven uses top-level `pom.xml` file(s). Bazel supports multiple build files
    and multiple targets per `BUILD` file, allowing for builds that are more
    incremental than Maven's.
*   Maven takes charge of steps for the deployment process. Bazel does not
    automate deployment.
*   Bazel enables you to express dependencies between languages.
*   As you add new sections to the project, with Bazel you may need to add new
    `BUILD` files. Best practice is to add a `BUILD` file to each new Java
    package.

## Migrate from Maven to Bazel

The steps below describe how to migrate your project to Bazel:

1.  [Create the MODULE.bazel file](#1-build)
2.  [Create one BUILD file](#2-build)
3.  [Create more BUILD files](#3-build)
4.  [Build using Bazel](#4-build)

Examples below come from a migration of the [Guava
project](https://github.com/google/guava){: .external} from Maven to Bazel. The
Guava project used is release `v31.1`. The examples using Guava do not walk
through each step in the migration, but they do show the files and contents that
are generated or added manually for the migration.

```
$ git clone https://github.com/google/guava.git && cd guava
$ git checkout v31.1
```

### 1. Create the MODULE.bazel file

Create a file named `MODULE.bazel` at the root of your project. If your project
has no external dependencies, this file can be empty.

If your project depends on files or packages that are not in one of the
project's directories, specify these external dependencies in the MODULE.bazel
file. You can use `rules_jvm_external` to manage dependencies from Maven. For
instructions about using this ruleset, see [the
README](https://github.com/bazelbuild/rules_jvm_external/#rules_jvm_external){: .external}
.

#### Guava project example: external dependencies

You can list the external dependencies of the [Guava
project](https://github.com/google/guava){: .external} with the
[`rules_jvm_external`](https://github.com/bazelbuild/rules_jvm_external){: .external}
ruleset.

Add the following snippet to the `MODULE.bazel` file:

```python
bazel_dep(name = "rules_jvm_external", version = "6.2")
maven = use_extension("@rules_jvm_external//:extensions.bzl", "maven")
maven.install(
    artifacts = [
        "com.google.code.findbugs:jsr305:3.0.2",
        "com.google.errorprone:error_prone_annotations:2.11.0",
        "com.google.j2objc:j2objc-annotations:1.3",
        "org.codehaus.mojo:animal-sniffer-annotations:1.20",
        "org.checkerframework:checker-qual:3.12.0",
    ],
    repositories = [
        "https://repo1.maven.org/maven2",
    ],
)
use_repo(maven, "maven")
```

### 2. Create one BUILD file

Now that you have your workspace defined and external dependencies (if
applicable) listed, you need to create `BUILD` files to describe how your
project should be built. Unlike Maven with its one `pom.xml` file, Bazel can use
many `BUILD` files to build a project. These files specify multiple build
targets, which allow Bazel to produce incremental builds.

Add `BUILD` files in stages. Start with adding one `BUILD` file at the root of
your project and using it to do an initial build using Bazel. Then, you refine
your build by adding more `BUILD` files with more granular targets.

1.  In the same directory as your `MODULE.bazel` file, create a text file and
    name it `BUILD`.

2.  In this `BUILD` file, use the appropriate rule to create one target to build
    your project. Here are some tips:

    *   Use the appropriate rule:
        *   To build projects with a single Maven module, use the
            `java_library` rule as follows:

            ```python
            java_library(
               name = "everything",
               srcs = glob(["src/main/java/**/*.java"]),
               resources = glob(["src/main/resources/**"]),
               deps = ["//:all-external-targets"],
            )
            ```

        *   To build projects with multiple Maven modules, use the
            `java_library` rule as follows:

            ```python
            java_library(
               name = "everything",
               srcs = glob([
                     "Module1/src/main/java/**/*.java",
                     "Module2/src/main/java/**/*.java",
                     ...
               ]),
               resources = glob([
                     "Module1/src/main/resources/**",
                     "Module2/src/main/resources/**",
                     ...
               ]),
               deps = ["//:all-external-targets"],
            )
            ```

        *   To build binaries, use the `java_binary` rule:

            ```python
            java_binary(
               name = "everything",
               srcs = glob(["src/main/java/**/*.java"]),
               resources = glob(["src/main/resources/**"]),
               deps = ["//:all-external-targets"],
               main_class = "com.example.Main"
            )
            ```

        *   Specify the attributes:
            *   `name`: Give the target a meaningful name. In the examples
                above, the target is called "everything."
            *   `srcs`: Use globbing to list all .java files in your project.
            *   `resources`: Use globbing to list all resources in your project.
            *   `deps`: You need to determine which external dependencies your
                project needs.
        *   Take a look at the [example below of this top-level BUILD
            file](#guava-2) from the migration of the Guava project.

3.  Now that you have a `BUILD` file at the root of your project, build your
    project to ensure that it works. On the command line, from your workspace
    directory, use `bazel build //:everything` to build your project with Bazel.

    The project has now been successfully built with Bazel. You will need to add
    more `BUILD` files to allow incremental builds of the project.

#### Guava project example: start with one BUILD file

When migrating the Guava project to Bazel, initially one `BUILD` file is used to
build the entire project. Here are the contents of this initial `BUILD` file in
the workspace directory:

```python
java_library(
    name = "everything",
    srcs = glob([
        "guava/src/**/*.java",
        "futures/failureaccess/src/**/*.java",
    ]),
    javacopts = ["-XepDisableAllChecks"],
    deps = [
        "@maven//:com_google_code_findbugs_jsr305",
        "@maven//:com_google_errorprone_error_prone_annotations",
        "@maven//:com_google_j2objc_j2objc_annotations",
        "@maven//:org_checkerframework_checker_qual",
        "@maven//:org_codehaus_mojo_animal_sniffer_annotations",
    ],
)
```

### 3. Create more BUILD files (optional)

Bazel does work with just one `BUILD file`, as you saw after completing your
first build. You should still consider breaking the build into smaller chunks by
adding more `BUILD` files with granular targets.

Multiple `BUILD` files with multiple targets will give the build increased
granularity, allowing:

*   increased incremental builds of the project,
*   increased parallel execution of the build,
*   better maintainability of the build for future users, and
*   control over visibility of targets between packages, which can prevent
    issues such as libraries containing implementation details leaking into
    public APIs.

Tips for adding more `BUILD` files:

*   You can start by adding a `BUILD` file to each Java package. Start with Java
    packages that have the fewest dependencies and work you way up to packages
    with the most dependencies.
*   As you add `BUILD` files and specify targets, add these new targets to the
    `deps` sections of targets that depend on them. Note that the `glob()`
    function does not cross package boundaries, so as the number of packages
    grows the files matched by `glob()` will shrink.
*   Any time you add a `BUILD` file to a `main` directory, ensure that you add a
    `BUILD` file to the corresponding `test` directory.
*   Take care to limit visibility properly between packages.
*   To simplify troubleshooting errors in your setup of `BUILD` files, ensure
    that the project continues to build with Bazel as you add each build file.
    Run `bazel build //...` to ensure all of your targets still build.

### 4. Build using Bazel

You've been building using Bazel as you add `BUILD` files to validate the setup
of the build.

When you have `BUILD` files at the desired granularity, you can use Bazel to
produce all of your builds.


# Migrating from Xcode to Bazel

This page describes how to build or test an Xcode project with Bazel. It
describes the differences between Xcode and Bazel, and provides the steps for
converting an Xcode project to a Bazel project. It also provides troubleshooting
solutions to address common errors.

## Differences between Xcode and Bazel

*   Bazel requires you to explicitly specify every build target and its
    dependencies, plus the corresponding build settings via build rules.

*   Bazel requires all files on which the project depends to be present within
    the workspace directory or specified as dependencies in the `MODULE.bazel`
    file.

*   When building Xcode projects with Bazel, the `BUILD` file(s) become the
    source of truth. If you work on the project in Xcode, you must generate a
    new version of the Xcode project that matches the `BUILD` files using
    [rules_xcodeproj](https://github.com/buildbuddy-io/rules_xcodeproj/){: .external}
    whenever you update the `BUILD` files. Certain changes to the `BUILD` files
    such as adding dependencies to a target don't require regenerating the
    project which can speed up development. If you're not using Xcode, the
    `bazel build` and `bazel test` commands provide build and test capabilities
    with certain limitations described later in this guide.

## Before you begin

Before you begin, do the following:

1.  [Install Bazel](/install) if you have not already done so.

2.  If you're not familiar with Bazel and its concepts, complete the [iOS app
    tutorial](/start/ios-app)). You should understand the Bazel workspace,
    including the `MODULE.bazel` and `BUILD` files, as well as the concepts of
    targets, build rules, and Bazel packages.

3.  Analyze and understand the project's dependencies.

### Analyze project dependencies

Unlike Xcode, Bazel requires you to explicitly declare all dependencies for
every target in the `BUILD` file.

For more information on external dependencies, see [Working with external
dependencies](/docs/external).

## Build or test an Xcode project with Bazel

To build or test an Xcode project with Bazel, do the following:

1.  [Create the `MODULE.bazel` file](#create-workspace)

2.  [(Experimental) Integrate SwiftPM dependencies](#integrate-swiftpm)

3.  [Create a `BUILD` file:](#create-build-file)

    a.  [Add the application target](#add-app-target)

    b.  [(Optional) Add the test target(s)](#add-test-target)

    c.  [Add the library target(s)](#add-library-target)

4.  [(Optional) Granularize the build](#granularize-build)

5.  [Run the build](#run-build)

6.  [Generate the Xcode project with rules_xcodeproj](#generate-the-xcode-project-with-rules_xcodeproj)

### Step 1: Create the `MODULE.bazel` file

Create a `MODULE.bazel` file in a new directory. This directory becomes the
Bazel workspace root. If the project uses no external dependencies, this file
can be empty. If the project depends on files or packages that are not in one of
the project's directories, specify these external dependencies in the
`MODULE.bazel` file.

Note: Place the project source code within the directory tree containing the
`MODULE.bazel` file.

### Step 2: (Experimental) Integrate SwiftPM dependencies

To integrate SwiftPM dependencies into the Bazel workspace with
[swift_bazel](https://github.com/cgrindel/swift_bazel){: .external}, you must
convert them into Bazel packages as described in the [following
tutorial](https://chuckgrindel.com/swift-packages-in-bazel-using-swift_bazel/){: .external}
.

Note: SwiftPM support is a manual process with many variables. SwiftPM
integration with Bazel has not been fully verified and is not officially
supported.

### Step 3: Create a `BUILD` file

Once you have defined the workspace and external dependencies, you need to
create a `BUILD` file that tells Bazel how the project is structured. Create the
`BUILD` file at the root of the Bazel workspace and configure it to do an
initial build of the project as follows:

*   [Step 3a: Add the application target](#step-3a-add-the-application-target)
*   [Step 3b: (Optional) Add the test target(s)](#step-3b-optional-add-the-test-target-s)
*   [Step 3c: Add the library target(s)](#step-3c-add-the-library-target-s)

**Tip:** To learn more about packages and other Bazel concepts, see [Workspaces,
packages, and targets](/concepts/build-ref).

#### Step 3a: Add the application target

Add a
[`macos_application`](https://github.com/bazelbuild/rules_apple/blob/master/doc/rules-macos.md#macos_application){: .external}
or an
[`ios_application`](https://github.com/bazelbuild/rules_apple/blob/master/doc/rules-ios.md#ios_application){: .external}
rule target. This target builds a macOS or iOS application bundle, respectively.
In the target, specify the following at the minimum:

*   `bundle_id` - the bundle ID (reverse-DNS path followed by app name) of the
    binary.

*   `provisioning_profile` - provisioning profile from your Apple Developer
    account (if building for an iOS device device).

*   `families` (iOS only) - whether to build the application for iPhone, iPad,
    or both.

*   `infoplists` - list of .plist files to merge into the final Info.plist file.

*   `minimum_os_version` - the minimum version of macOS or iOS that the
    application supports. This ensures Bazel builds the application with the
    correct API levels.

#### Step 3b: (Optional) Add the test target(s)

Bazel's [Apple build
rules](https://github.com/bazelbuild/rules_apple){: .external} support running
unit and UI tests on all Apple platforms. Add test targets as follows:

*   [`macos_unit_test`](https://github.com/bazelbuild/rules_apple/blob/master/doc/rules-macos.md#macos_unit_test){: .external}
    to run library-based and application-based unit tests on a macOS.

*   [`ios_unit_test`](https://github.com/bazelbuild/rules_apple/blob/master/doc/rules-ios.md#ios_unit_test){: .external}
    to build and run library-based unit tests on iOS.

*   [`ios_ui_test`](https://github.com/bazelbuild/rules_apple/blob/master/doc/rules-ios.md#ios_ui_test){: .external}
    to build and run user interface tests in the iOS simulator.

*   Similar test rules exist for
    [tvOS](https://github.com/bazelbuild/rules_apple/blob/master/doc/rules-tvos.md){: .external},
    [watchOS](https://github.com/bazelbuild/rules_apple/blob/master/doc/rules-watchos.md){: .external}
    and
    [visionOS](https://github.com/bazelbuild/rules_apple/blob/master/doc/rules-visionos.md){: .external}.

At the minimum, specify a value for the `minimum_os_version` attribute. While
other packaging attributes, such as `bundle_identifier` and `infoplists`,
default to most commonly used values, ensure that those defaults are compatible
with the project and adjust them as necessary. For tests that require the iOS
simulator, also specify the `ios_application` target name as the value of the
`test_host` attribute.

#### Step 3c: Add the library target(s)

Add an [`objc_library`](/reference/be/objective-c#objc_library) target for each
Objective-C library and a
[`swift_library`](https://github.com/bazelbuild/rules_swift/blob/master/doc/rules.md#swift_library){: .external}
target for each Swift library on which the application and/or tests depend.

Add the library targets as follows:

*   Add the application library targets as dependencies to the application
    targets.

*   Add the test library targets as dependencies to the test targets.

*   List the implementation sources in the `srcs` attribute.

*   List the headers in the `hdrs` attribute.

Note: You can use the [`glob`](/reference/be/functions#glob) function to include
all sources and/or headers of a certain type. Use it carefully as it might
include files you do not want Bazel to build.

You can browse existing examples for various types of applications directly in
the [rules_apple examples
directory](https://github.com/bazelbuild/rules_apple/tree/master/examples/). For
example:

*   [macOS application targets](https://github.com/bazelbuild/rules_apple/tree/master/examples/macos){: .external}

*   [iOS applications targets](https://github.com/bazelbuild/rules_apple/tree/master/examples/ios){: .external}

*   [Multi platform applications (macOS, iOS, watchOS, tvOS)](https://github.com/bazelbuild/rules_apple/tree/master/examples/multi_platform){: .external}

For more information on build rules, see [Apple Rules for
Bazel](https://github.com/bazelbuild/rules_apple){: .external}.

At this point, it is a good idea to test the build:

`bazel build //:<application_target>`

### Step 4: (Optional) Granularize the build

If the project is large, or as it grows, consider chunking it into multiple
Bazel packages. This increased granularity provides:

*   Increased incrementality of builds,

*   Increased parallelization of build tasks,

*   Better maintainability for future users,

*   Better control over source code visibility across targets and packages. This
    prevents issues such as libraries containing implementation details leaking
    into public APIs.

Tips for granularizing the project:

*   Put each library in its own Bazel package. Start with those requiring the
    fewest dependencies and work your way up the dependency tree.

*   As you add `BUILD` files and specify targets, add these new targets to the
    `deps` attributes of targets that depend on them.

*   The `glob()` function does not cross package boundaries, so as the number of
    packages grows the files matched by `glob()` will shrink.

*   When adding a `BUILD` file to a `main` directory, also add a `BUILD` file to
    the corresponding `test` directory.

*   Enforce healthy visibility limits across packages.

*   Build the project after each major change to the `BUILD` files and fix build
    errors as you encounter them.

### Step 5: Run the build

Run the fully migrated build to ensure it completes with no errors or warnings.
Run every application and test target individually to more easily find sources
of any errors that occur.

For example:

```posix-terminal
bazel build //:my-target
```

### Step 6: Generate the Xcode project with rules_xcodeproj

When building with Bazel, the `MODULE.bazel` and `BUILD` files become the source
of truth about the build. To make Xcode aware of this, you must generate a
Bazel-compatible Xcode project using
[rules_xcodeproj](https://github.com/buildbuddy-io/rules_xcodeproj#features){: .external}
.

### Troubleshooting

Bazel errors can arise when it gets out of sync with the selected Xcode version,
like when you apply an update. Here are some things to try if you're
experiencing errors with Xcode, for example "Xcode version must be specified to
use an Apple CROSSTOOL".

*   Manually run Xcode and accept any terms and conditions.

*   Use Xcode select to indicate the correct version, accept the license, and
    clear Bazel's state.

```posix-terminal
  sudo xcode-select -s /Applications/Xcode.app/Contents/Developer

  sudo xcodebuild -license

  bazel sync --configure
```

*   If this does not work, you may also try running `bazel clean --expunge`.

Note: If you've saved your Xcode to a different path, you can use `xcode-select
-s` to point to that path.