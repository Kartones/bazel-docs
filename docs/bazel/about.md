

Project: /_project.yaml
Book: /_book.yaml

# Intro to Bazel

{% include "_buttons.html" %}

Bazel is an open-source build and test tool similar to Make, Maven, and Gradle.
It uses a human-readable, high-level build language. Bazel supports projects in
multiple languages and builds outputs for multiple platforms. Bazel supports
large codebases across multiple repositories, and large numbers of users.

## Benefits {:#benefits}

Bazel offers the following advantages:

*   **High-level build language.** Bazel uses an abstract, human-readable
    language to describe the build properties of your project at a high
    semantical level. Unlike other tools, Bazel operates on the *concepts*
    of libraries, binaries, scripts, and data sets, shielding you from the
    complexity of writing individual calls to tools such as compilers and
    linkers.

*   **Bazel is fast and reliable.** Bazel caches all previously done work and
    tracks changes to both file content and build commands. This way, Bazel
    knows when something needs to be rebuilt, and rebuilds only that. To further
    speed up your builds, you can set up your project to build in a  highly
    parallel and incremental fashion.

*   **Bazel is multi-platform.** Bazel runs on Linux, macOS, and Windows. Bazel
    can build binaries and deployable packages for multiple platforms, including
    desktop, server, and mobile, from the same project.

*   **Bazel scales.** Bazel maintains agility while handling builds with 100k+
    source files. It works with multiple repositories and user bases in the tens
    of thousands.

*   **Bazel is extensible.** Many [languages](/rules) are
    supported, and you can extend Bazel to support any other language or
    framework.

## Using Bazel {:#using-bazel}

To build or test a project with Bazel, you typically do the following:

1.  **Set up Bazel.** Download and [install Bazel](/install).

2.  **Set up a project [workspace](/concepts/build-ref#workspaces)**, which is a
    directory where Bazel looks for build inputs and `BUILD` files, and where it
    stores build outputs.

3.  **Write a `BUILD` file**, which tells Bazel what to build and how to
    build it.

    You write your `BUILD` file by declaring build targets using
    [Starlark](/rules/language), a domain-specific language. (See example
    [here](https://github.com/bazelbuild/bazel/blob/master/examples/cpp/BUILD){: .external}.)

    A build target specifies a set of input artifacts that Bazel will build plus
    their dependencies, the build rule Bazel will use to build it, and options
    that configure the build rule.

    A build rule specifies the build tools Bazel will use, such as compilers and
    linkers, and their configurations. Bazel ships with a number of build rules
    covering the most common artifact types in the supported languages on
    supported platforms.

4. **Run Bazel** from the [command line](/reference/command-line-reference). Bazel
   places your outputs within the workspace.

In addition to building, you can also use Bazel to run
[tests](/reference/test-encyclopedia) and [query](/query/guide) the build
to trace dependencies in your code.

## Bazel build process {:#bazel-build-process}

When running a build or a test, Bazel does the following:

1.  **Loads** the `BUILD` files relevant to the target.

2.  **Analyzes** the inputs and their
    [dependencies](/concepts/dependencies), applies the specified build
    rules, and produces an [action](/extending/concepts#evaluation-model)
    graph.

3.  **Executes** the build actions on the inputs until the final build outputs
    are produced.

Since all previous build work is cached, Bazel can identify and reuse cached
artifacts and only rebuild or retest what's changed. To further enforce
correctness, you can set up Bazel to run builds and tests
[hermetically](/basics/hermeticity) through sandboxing, minimizing skew
and maximizing [reproducibility](/run/build#correct-incremental-rebuilds).

### Action graph {:#action-graph}

The action graph represents the build artifacts, the relationships between them,
and the build actions that Bazel will perform. Thanks to this graph, Bazel can
[track](/run/build#build-consistency) changes to
file content as well as changes to actions, such as build or test commands, and
know what build work has previously been done. The graph also enables you to
easily [trace dependencies](/query/guide) in your code.

## Getting started tutorials {:#getting-started-tutorials}

To get started with Bazel, see [Getting Started](/start/) or jump
directly to the Bazel tutorials:

*   [Tutorial: Build a C++ Project](/start/cpp)
*   [Tutorial: Build a Java Project](/start/java)
*   [Tutorial: Build an Android Application](/start/android-app)
*   [Tutorial: Build an iOS Application](/start/ios-app)


Project: /_project.yaml
Book: /_book.yaml

# FAQ

{% include "_buttons.html" %}

If you have questions or need support, see [Getting Help](/help).

## What is Bazel?

Bazel is a tool that automates software builds and tests. Supported build tasks include running compilers and linkers to produce executable programs and libraries, and assembling deployable packages for Android, iOS and other target environments. Bazel is similar to other tools like Make, Ant, Gradle, Buck, Pants and Maven.

## What is special about Bazel?

Bazel was designed to fit the way software is developed at Google. It has the following features:

*   Multi-language support: Bazel supports [many languages](/reference/be/overview), and can be extended to support arbitrary programming languages.
*   High-level build language: Projects are described in the `BUILD` language, a concise text format that describes a project as sets of small interconnected libraries, binaries and tests. In contrast, with tools like Make, you have to describe individual files and compiler invocations.
*   Multi-platform support: The same tool and the same `BUILD` files can be used to build software for different architectures, and even different platforms. At Google, we use Bazel to build everything from server applications running on systems in our data centers to client apps running on mobile phones.
*   Reproducibility: In `BUILD` files, each library, test and binary must specify its direct dependencies completely. Bazel uses this dependency information to know what must be rebuilt when you make changes to a source file, and which tasks can run in parallel. This means that all builds are incremental and will always produce the same result.
*   Scalable: Bazel can handle large builds; at Google, it is common for a server binary to have 100k source files, and builds where no files were changed take about ~200ms.

## Why doesn’t Google use...?

*   Make, Ninja: These tools give very exact control over what commands get invoked to build files, but it’s up to the user to write rules that are correct.
    * Users interact with Bazel on a higher level. For example, Bazel has built-in rules for “Java test”, “C++ binary”, and notions such as “target platform” and “host platform”. These rules have been battle tested to be foolproof.
*   Ant and Maven: Ant and Maven are primarily geared toward Java, while Bazel handles multiple languages. Bazel encourages subdividing codebases in smaller reusable units, and can rebuild only ones that need rebuilding. This speeds up development when working with larger codebases.
*   Gradle: Bazel configuration files are much more structured than Gradle’s, letting Bazel understand exactly what each action does. This allows for more parallelism and better reproducibility.
*   Pants, Buck: Both tools were created and developed by ex-Googlers at Twitter and Foursquare, and Facebook respectively. They have been modeled after Bazel, but their feature sets are different, so they aren’t viable alternatives for us.

## Where did Bazel come from?

Bazel is a flavor of the tool that Google uses to build its server software internally. It has expanded to build other software as well, like mobile apps (iOS, Android) that connect to our servers.

## Did you rewrite your internal tool as open-source? Is it a fork?

Bazel shares most of its code with the internal tool and its rules are used for millions of builds every day.

## Why did Google build Bazel?

A long time ago, Google built its software using large, generated Makefiles. These led to slow and unreliable builds, which began to interfere with our developers’ productivity and the company’s agility. Bazel was a way to solve these problems.

## Does Bazel require a build cluster?

Bazel runs build operations locally by default. However, Bazel can also connect to a build cluster for even faster builds and tests. See our documentation on [remote execution and caching](/remote/rbe) and [remote caching](/remote/caching) for further details.

## How does the Google development process work?

For our server code base, we use the following development workflow:

*   All our server code is in a single, gigantic version control system.
*   Everybody builds their software with Bazel.
*   Different teams own different parts of the source tree, and make their components available as `BUILD` targets.
*   Branching is primarily used for managing releases, so everybody develops their software at the head revision.

Bazel is a cornerstone of this philosophy: since Bazel requires all dependencies to be fully specified, we can predict which programs and tests are affected by a change, and vet them before submission.

More background on the development process at Google can be found on the [eng tools blog](http://google-engtools.blogspot.com/){: .external}.

## Why did you open up Bazel?

Building software should be fun and easy. Slow and unpredictable builds take the fun out of programming.

## Why would I want to use Bazel?

*   Bazel may give you faster build times because it can recompile only the files that need to be recompiled. Similarly, it can skip re-running tests that it knows haven’t changed.
*   Bazel produces deterministic results. This eliminates skew between incremental and clean builds, laptop and CI system, etc.
*   Bazel can build different client and server apps with the same tool from the same workspace. For example, you can change a client/server protocol in a single commit, and test that the updated mobile app works with the updated server, building both with the same tool, reaping all the aforementioned benefits of Bazel.

## Can I see examples?

Yes; see a [simple example](https://github.com/bazelbuild/bazel/blob/master/examples/cpp/BUILD){: .external}
or read the [Bazel source code](https://github.com/bazelbuild/bazel/blob/master/src/BUILD){: .external} for a more complex example.


## What is Bazel best at?

Bazel shines at building and testing projects with the following properties:

*   Projects with a large codebase
*   Projects written in (multiple) compiled languages
*   Projects that deploy on multiple platforms
*   Projects that have extensive tests

## Where can I run Bazel?

Bazel runs on Linux, macOS (OS X), and Windows.

Porting to other UNIX platforms should be relatively easy, as long as a JDK is available for the platform.

## What should I not use Bazel for?

*   Bazel tries to be smart about caching. This means that it is not good for running build operations whose outputs should not be cached. For example, the following steps should not be run from Bazel:
    *   A compilation step that fetches data from the internet.
    *   A test step that connects to the QA instance of your site.
    *   A deployment step that changes your site’s cloud configuration.
*   If your build consists of a few long, sequential steps, Bazel may not be able to help much. You’ll get more speed by breaking long steps into smaller, discrete targets that Bazel can run in parallel.

## How stable is Bazel’s feature set?

The core features (C++, Java, and shell rules) have extensive use inside Google, so they are thoroughly tested and have very little churn. Similarly, we test new versions of Bazel across hundreds of thousands of targets every day to find regressions, and we release new versions multiple times every month.

In short, except for features marked as experimental, Bazel should Just Work. Changes to non-experimental rules will be backward compatible. A more detailed list of feature support statuses can be found in our [support document](/contribute/support).

## How stable is Bazel as a binary?

Inside Google, we make sure that Bazel crashes are very rare. This should also hold for our open source codebase.

## How can I start using Bazel?

See [Getting Started](/start/).

## Doesn’t Docker solve the reproducibility problems?

With Docker you can easily create sandboxes with fixed OS releases, for example, Ubuntu 12.04, Fedora 21. This solves the problem of reproducibility for the system environment – that is, “which version of /usr/bin/c++ do I need?”

Docker does not address reproducibility with regard to changes in the source code. Running Make with an imperfectly written Makefile inside a Docker container can still yield unpredictable results.

Inside Google, we check tools into source control for reproducibility. In this way, we can vet changes to tools (“upgrade GCC to 4.6.1”) with the same mechanism as changes to base libraries (“fix bounds check in OpenSSL”).

## Can I build binaries for deployment on Docker?

With Bazel, you can build standalone, statically linked binaries in C/C++, and self-contained jar files for Java. These run with few dependencies on normal UNIX systems, and as such should be simple to install inside a Docker container.

Bazel has conventions for structuring more complex programs, for example, a Java program that consumes a set of data files, or runs another program as subprocess. It is possible to package up such environments as standalone archives, so they can be deployed on different systems, including Docker images.

## Can I build Docker images with Bazel?

Yes, you can use our [Docker rules](https://github.com/bazelbuild/rules_docker){: .external} to build reproducible Docker images.

## Will Bazel make my builds reproducible automatically?

For Java and C++ binaries, yes, assuming you do not change the toolchain. If you have build steps that involve custom recipes (for example, executing binaries through a shell script inside a rule), you will need to take some extra care:

*   Do not use dependencies that were not declared. Sandboxed execution (–spawn\_strategy=sandboxed, only on Linux) can help find undeclared dependencies.
*   Avoid storing timestamps and user-IDs in generated files. ZIP files and other archives are especially prone to this.
*   Avoid connecting to the network. Sandboxed execution can help here too.
*   Avoid processes that use random numbers, in particular, dictionary traversal is randomized in many programming languages.

## Do you have binary releases?

Yes, you can find the latest [release binaries](https://github.com/bazelbuild/bazel/releases/latest){: .external} and review our [release policy](/release/)

## I use Eclipse/IntelliJ/XCode. How does Bazel interoperate with IDEs?

For IntelliJ, check out the [IntelliJ with Bazel plugin](https://ij.bazel.build/).

For XCode, check out [Tulsi](http://tulsi.bazel.build/).

For Eclipse, check out [E4B plugin](https://github.com/bazelbuild/e4b){: .external}.

For other IDEs, check out the [blog post](https://blog.bazel.build/2016/06/10/ide-support.html) on how these plugins work.

## I use Jenkins/CircleCI/TravisCI. How does Bazel interoperate with CI systems?

Bazel returns a non-zero exit code if the build or test invocation fails, and this should be enough for basic CI integration. Since Bazel does not need clean builds for correctness, the CI system should not be configured to clean before starting a build/test run.

Further details on exit codes are in the [User Manual](/docs/user-manual).

## What future features can we expect in Bazel?

See our [Roadmaps](/about/roadmap).

## Can I use Bazel for my INSERT LANGUAGE HERE project?

Bazel is extensible. Anyone can add support for new languages. Many languages are supported: see the [build encyclopedia](/reference/be/overview) for a list of recommendations and [awesomebazel.com](https://awesomebazel.com/){: .external} for a more comprehensive list.

If you would like to develop extensions or learn how they work, see the documentation for [extending Bazel](/extending/concepts).

## Can I contribute to the Bazel code base?

See our [contribution guidelines](/contribute/).

## Why isn’t all development done in the open?

We still have to refactor the interfaces between the public code in Bazel and our internal extensions frequently. This makes it hard to do much development in the open.

## Are you done open sourcing Bazel?

Open sourcing Bazel is a work-in-progress. In particular, we’re still working on open sourcing:

*   Many of our unit and integration tests (which should make contributing patches easier).
*   Full IDE integration.

Beyond code, we’d like to eventually have all code reviews, bug tracking, and design decisions happen publicly, with the Bazel community involved. We are not there yet, so some changes will simply appear in the Bazel repository without clear explanation. Despite this lack of transparency, we want to support external developers and collaborate. Thus, we are opening up the code, even though some of the development is still happening internal to Google. Please let us know if anything seems unclear or unjustified as we transition to an open model.

## Are there parts of Bazel that will never be open sourced?

Yes, some of the code base either integrates with Google-specific technology or we have been looking for an excuse to get rid of (or is some combination of the two). These parts of the code base are not available on GitHub and probably never will be.

## How do I contact the team?

We are reachable at bazel-discuss@googlegroups.com.

## Where do I report bugs?

Open an issue [on GitHub](https://github.com/bazelbuild/bazel/issues){: .external}.

## What’s up with the word “Blaze” in the codebase?

This is an internal name for the tool. Please refer to Blaze as Bazel.

## Why do other Google projects (Android, Chrome) use other build tools?

Until the first (Alpha) release, Bazel was not available externally, so open source projects such as Chromium and Android could not use it. In addition, the original lack of Windows support was a problem for building Windows applications, such as Chrome. Since the project has matured and become more stable, the [Android Open Source Project](https://source.android.com/) is in the process of migrating to Bazel.

## How do you pronounce “Bazel”?

The same way as “basil” (the herb) in US English: “BAY-zel”. It rhymes with “hazel”. IPA: /ˈbeɪzˌəl/


Project: /_project.yaml
Book: /_book.yaml

# Bazel Vision

{% include "_buttons.html" %}

Any software developer can efficiently build, test, and package
any project, of any size or complexity, with tooling that's easy to adopt and
extend.

*   **Engineers can take build fundamentals for granted.** Software developers
    focus on the creative process of authoring code because the mechanical
    process of build and test is solved. When customizing the build system to
    support new languages or unique organizational needs, users focus on the
    aspects of extensibility that are unique to their use case, without having
    to reinvent the basic plumbing.

*   **Engineers can easily contribute to any project.** A developer who wants to
    start working on a new project can simply clone the project and run the
    build. There's no need for local configuration - it just works. With
    cross-platform remote execution, they can work on any machine anywhere and
    fully test their changes against all platforms the project targets.
    Engineers can quickly configure the build for a new project or incrementally
    migrate an existing build.

*   **Projects can scale to any size codebase, any size team.** Fast,
    incremental testing allows teams to fully validate every change before it is
    committed. This remains true even as repos grow, projects span multiple
    repos, and multiple languages are introduced. Infrastructure does not force
    developers to trade test coverage for build speed.

**We believe Bazel has the potential to fulfill this vision.**

Bazel was built from the ground up to enable builds that are reproducible (a
given set of inputs will always produce the same outputs) and portable (a build
can be run on any machine without affecting the output).

These characteristics support safe incrementality (rebuilding only changed
inputs doesn't introduce the risk of corruption) and distributability (build
actions are isolated and can be offloaded). By minimizing the work needed to do
a correct build and parallelizing that work across multiple cores and remote
systems, Bazel can make any build fast.

Bazel's abstraction layer — instructions specific to languages, platforms, and
toolchains implemented in a simple extensibility language — allows it to be
easily applied to any context.

## Bazel core competencies {:#bazel-core-competencies}

1.  Bazel supports **multi-language, multi-platform** builds and tests. You can
    run a single command to build and test your entire source tree, no matter
    which combination of languages and platforms you target.
1.  Bazel builds are **fast and correct**. Every build and test run is
    incremental, on your developers' machines and on CI.
1.  Bazel provides a **uniform, extensible language** to define builds for any
    language or platform.
1.  Bazel allows your builds **to scale** by connecting to remote execution and
    caching services.
1.  Bazel works across **all major development platforms** (Linux, MacOS, and
    Windows).
1.  We accept that adopting Bazel requires effort, but **gradual adoption** is
    possible. Bazel interfaces with de-facto standard tools for a given
    language/platform.

## Serving language communities {:#language-communities}

Software engineering evolves in the context of language communities — typically,
self-organizing groups of people who use common tools and practices.

To be of use to members of a language community, high-quality Bazel rules must be
available that integrate with the workflows and conventions of that community.

Bazel is committed to be extensible and open, and to support good rulesets for
any language.

###  Requirements of a good ruleset {:#ruleset-requirements}

1.  The rules need to support efficient **building and testing** for the
    language, including code coverage.
1.  The rules need to **interface with a widely-used "package manager"** for the
    language (such as Maven for Java), and support incremental migration paths
    from other widely-used build systems.
1.  The rules need to be **extensible and interoperable**, following
    ["Bazel sandwich"](https://github.com/bazelbuild/bazel-website/blob/master/designs/_posts/2016-08-04-extensibility-for-native-rules.md)
    principles.
1.  The rules need to be **remote-execution ready**. In practice, this means
    **configurable using the [toolchains](/extending/toolchains) mechanism**.
1.  The rules (and Bazel) need to interface with a **widely-used IDE** for the
    language, if there is one.
1.  The rules need to have **thorough, usable documentation,** with introductory
    material for new users, comprehensive docs for expert users.

Each of these items is essential and only together do they deliver on Bazel's
competencies for their particular ecosystem.

They are also, by and large, sufficient - once all are fulfilled, Bazel fully
delivers its value to members of that language community.


Project: /_project.yaml
Book: /_book.yaml
# Bazel roadmap

{% include "_buttons.html" %}

As Bazel continues to evolve in response to your needs, we want to share our
2025 roadmap update.

We plan to bring Bazel 9.0
[long term support (LTS)](https://bazel.build/release/versioning) to you in late
2025.

## Full transition to Bzlmod

[Bzlmod](https://bazel.build/docs/bzlmod) has been the standard external
dependency system in Bazel since Bazel 7, replacing the legacy WORKSPACE system.
As of March 2025, the [Bazel Central Registry](https://registry.bazel.build/)
hosts more than 650 modules.

With Bazel 9, we will completely remove WORKSPACE functionality, and Bzlmod will
be the only way to introduce external dependencies in Bazel. To minimize the
migration cost for the community, we'll focus on further improving our migration
[guide](https://bazel.build/external/migration) and
[tool](https://github.com/bazelbuild/bazel-central-registry/tree/main/tools#migrate_to_bzlmodpy).

Additionally, we aim to implement an improved shared repository cache (see
[#12227](https://github.com/bazelbuild/bazel/issues/12227))
with garbage collection, and may backport it to Bazel 8. The Bazel Central
Registry will also support verifying SLSA attestations.

## Migration of Android, C++, Java, Python, and Proto rules

With Bazel 8, we have migrated support for Android, Java, Python, and Proto
rules out of the Bazel codebase into Starlark rules in their corresponding
repositories. To ease the migration, we implemented the autoload features in
Bazel, which can be controlled with
[--incompatible_autoload_externally](https://github.com/bazelbuild/bazel/issues/23043)
and [--incompatible_disable_autoloads_in_main_repo](https://github.com/bazelbuild/bazel/issues/25755)
flags.

With Bazel 9, we aim to disable autoloads by default and require every project
to explicitly load required rules in BUILD files.

We will rewrite most of C++ language support to Starlark, detach it from Bazel
binary and move it into the [/rules_cc](https://github.com/bazelbuild/rules_cc)
repository. This is the last remaining major language support that is still part
of Bazel.

We're also porting unit tests for C++, Java, and Proto rules to Starlark, moving
them to repositories next to the implementation to increase velocity of rule
authors.

## Starlark improvements

Bazel will have the ability to evaluate symbolic macros lazily. This means that
a symbolic macro won't run if the targets it declares are not requested,
improving performance for very large packages.

Starlark will have an experimental type system, similar to Python's type
annotations. We expect the type system to stabilize _after_ Bazel 9 is launched.

## Configurability

Our main focus is reducing the cost and confusion of build flags.

We're [experimenting](https://github.com/bazelbuild/bazel/issues/24839) with a
new project configuration model that doesn't make users have to know which build
and test flags to set where. So `$ bazel test //foo` automatically sets the
right flags based on `foo`'s project's policy. This will likely remain
experimental in 9.0 but guiding feedback is welcome.

[Flag scoping](https://github.com/bazelbuild/bazel/issues/24042) lets you strip
out Starlark flags when they leave project boundaries, so they don't break
caching on transitive dependencies that don't need them. This makes builds that
use [transitions](https://bazel.build/extending/config#user-defined-transitions)
cheaper and faster.
[Here's](https://github.com/gregestren/snippets/tree/master/project_scoped_flags)
an example. We're extending the idea to control which flags propagate to
[exec configurations](https://bazel.build/extending/rules#configurations) and
are considering even more flexible support like custom Starlark to determine
which dependency edges should propagate flags.

We're up-prioritizing effort to move built-in language flags out of Bazel and
into Starlark, where they can live with related rule definitions.

## Remote execution improvements

We plan to add support for asynchronous execution, speeding up remote execution
by increasing parallelism.

---

To follow updates to the roadmap and discuss planned features, join the
community Slack server at [slack.bazel.build](https://slack.bazel.build/).

*This roadmap is intended to help inform the community about the team's
intentions for Bazel 9.0. Priorities are subject to change in response to
developer and customer feedback, or to new market opportunities.*


Project: /_project.yaml
Book: /_book.yaml

# Why Bazel?

{% include "_buttons.html" %}

Bazel is a [fast](#fast), [correct](#correct), and [extensible](#extensible)
build tool with [integrated testing](#integrated-testing) that supports multiple
[languages](#multi-language), [repositories](#multi-repository), and
[platforms](#multi-platform) in an industry-leading [ecosystem](#ecosystem).

## Bazel is fast {:#fast}

Bazel knows exactly what input files each build command needs, avoiding
unnecessary work by re-running only when the set of input files have
changed between each build.
It runs build commands with as much parallelism as possible, either within the
same computer or on [remote build nodes](/remote/rbe). If the structure of build
allows for it, it can run thousands of build or test commands at the same time.

This is supported by multiple caching layers, in memory, on disk and on the
remote build farm, if available. At Google, we routinely achieve cache hit rates
north of 99%.

## Bazel is correct {:#correct}

Bazel ensures that your binaries are built *only* from your own
source code. Bazel actions run in individual sandboxes and Bazel tracks
every input file of the build, only and always re-running build
commands when it needs to. This keeps your binaries up-to-date so that the
[same source code always results in the same binary](/basics/hermeticity), bit
by bit.

Say goodbyte to endless `make clean` invocations and to chasing phantom bugs
that were in fact resolved in source code that never got built.

## Bazel is extensible {:#extensible}

Harness the full power of Bazel by writing your own rules and macros to
customize Bazel for your specific needs across a wide range of projects.

Bazel rules are written in [Starlark](/rules/language), our
in-house programming language that's a subset of Python. Starlark makes
rule-writing accessible to most developers, while also creating rules that can
be used across the ecosystem.

## Integrated testing {:#integrated-testing}

Bazel's [integrated test runner](/docs/user-manual#running-tests)
knows and runs only those tests needing to be re-run, using remote execution
(if available) to run them in parallel. Detect flakes early by using remote
execution to quickly run a test thousands of times.

Bazel [provides facilities](/remote/bep) to upload test results to a central
location, thereby facilitating efficient communication of test outcomes, be it
on CI or by individual developers.

## Multi-language support {:#multi-language}

Bazel supports many common programming languages including C++, Java,
Kotlin, Python, Go, and Rust. You can build multiple binaries (for example,
backend, web UI and mobile app) in the same Bazel invocation without being
constrained to one language's idiomatic build tool.

## Multi-repository support {:#multi-repository}

Bazel can [gather source code from multiple locations](/external/overview): you
don't need to vendor your dependencies (but you can!), you can instead point
Bazel to the location of your source code or prebuilt artifacts (e.g. a git
repository or Maven Central), and it takes care of the rest.

## Multi-platform support {:#multi-platform}

Bazel can simultaneously build projects for multiple platforms including Linux,
macOS, Windows, and Android. It also provides powerful
[cross-compilation capabilities](/extending/platforms) to build code for one
platform while running the build on another.

## Wide ecosystem {:#ecosystem}

[Industry leaders](/community/users) love Bazel, building a large
community of developers who use and contribute to Bazel. Find a tools, services
and documentation, including [consulting and SaaS offerings](/community/experts)
Bazel can use. Explore extensions like support for programming languages in
our [open source software repositories](/rules).

Project: /_project.yaml
Book: /_book.yaml

# Intro to Bazel

{% include "_buttons.html" %}

Bazel is an open-source build and test tool similar to Make, Maven, and Gradle.
It uses a human-readable, high-level build language. Bazel supports projects in
multiple languages and builds outputs for multiple platforms. Bazel supports
large codebases across multiple repositories, and large numbers of users.

## Benefits {:#benefits}

Bazel offers the following advantages:

*   **High-level build language.** Bazel uses an abstract, human-readable
    language to describe the build properties of your project at a high
    semantical level. Unlike other tools, Bazel operates on the *concepts*
    of libraries, binaries, scripts, and data sets, shielding you from the
    complexity of writing individual calls to tools such as compilers and
    linkers.

*   **Bazel is fast and reliable.** Bazel caches all previously done work and
    tracks changes to both file content and build commands. This way, Bazel
    knows when something needs to be rebuilt, and rebuilds only that. To further
    speed up your builds, you can set up your project to build in a  highly
    parallel and incremental fashion.

*   **Bazel is multi-platform.** Bazel runs on Linux, macOS, and Windows. Bazel
    can build binaries and deployable packages for multiple platforms, including
    desktop, server, and mobile, from the same project.

*   **Bazel scales.** Bazel maintains agility while handling builds with 100k+
    source files. It works with multiple repositories and user bases in the tens
    of thousands.

*   **Bazel is extensible.** Many [languages](/rules) are
    supported, and you can extend Bazel to support any other language or
    framework.

## Using Bazel {:#using-bazel}

To build or test a project with Bazel, you typically do the following:

1.  **Set up Bazel.** Download and [install Bazel](/install).

2.  **Set up a project [workspace](/concepts/build-ref#workspaces)**, which is a
    directory where Bazel looks for build inputs and `BUILD` files, and where it
    stores build outputs.

3.  **Write a `BUILD` file**, which tells Bazel what to build and how to
    build it.

    You write your `BUILD` file by declaring build targets using
    [Starlark](/rules/language), a domain-specific language. (See example
    [here](https://github.com/bazelbuild/bazel/blob/master/examples/cpp/BUILD){: .external}.)

    A build target specifies a set of input artifacts that Bazel will build plus
    their dependencies, the build rule Bazel will use to build it, and options
    that configure the build rule.

    A build rule specifies the build tools Bazel will use, such as compilers and
    linkers, and their configurations. Bazel ships with a number of build rules
    covering the most common artifact types in the supported languages on
    supported platforms.

4. **Run Bazel** from the [command line](/reference/command-line-reference). Bazel
   places your outputs within the workspace.

In addition to building, you can also use Bazel to run
[tests](/reference/test-encyclopedia) and [query](/query/guide) the build
to trace dependencies in your code.

## Bazel build process {:#bazel-build-process}

When running a build or a test, Bazel does the following:

1.  **Loads** the `BUILD` files relevant to the target.

2.  **Analyzes** the inputs and their
    [dependencies](/concepts/dependencies), applies the specified build
    rules, and produces an [action](/extending/concepts#evaluation-model)
    graph.

3.  **Executes** the build actions on the inputs until the final build outputs
    are produced.

Since all previous build work is cached, Bazel can identify and reuse cached
artifacts and only rebuild or retest what's changed. To further enforce
correctness, you can set up Bazel to run builds and tests
[hermetically](/basics/hermeticity) through sandboxing, minimizing skew
and maximizing [reproducibility](/run/build#correct-incremental-rebuilds).

### Action graph {:#action-graph}

The action graph represents the build artifacts, the relationships between them,
and the build actions that Bazel will perform. Thanks to this graph, Bazel can
[track](/run/build#build-consistency) changes to
file content as well as changes to actions, such as build or test commands, and
know what build work has previously been done. The graph also enables you to
easily [trace dependencies](/query/guide) in your code.

## Getting started tutorials {:#getting-started-tutorials}

To get started with Bazel, see [Getting Started](/start/) or jump
directly to the Bazel tutorials:

*   [Tutorial: Build a C++ Project](/start/cpp)
*   [Tutorial: Build a Java Project](/start/java)
*   [Tutorial: Build an Android Application](/start/android-app)
*   [Tutorial: Build an iOS Application](/start/ios-app)


Project: /_project.yaml
Book: /_book.yaml

# FAQ

{% include "_buttons.html" %}

If you have questions or need support, see [Getting Help](/help).

## What is Bazel?

Bazel is a tool that automates software builds and tests. Supported build tasks include running compilers and linkers to produce executable programs and libraries, and assembling deployable packages for Android, iOS and other target environments. Bazel is similar to other tools like Make, Ant, Gradle, Buck, Pants and Maven.

## What is special about Bazel?

Bazel was designed to fit the way software is developed at Google. It has the following features:

*   Multi-language support: Bazel supports [many languages](/reference/be/overview), and can be extended to support arbitrary programming languages.
*   High-level build language: Projects are described in the `BUILD` language, a concise text format that describes a project as sets of small interconnected libraries, binaries and tests. In contrast, with tools like Make, you have to describe individual files and compiler invocations.
*   Multi-platform support: The same tool and the same `BUILD` files can be used to build software for different architectures, and even different platforms. At Google, we use Bazel to build everything from server applications running on systems in our data centers to client apps running on mobile phones.
*   Reproducibility: In `BUILD` files, each library, test and binary must specify its direct dependencies completely. Bazel uses this dependency information to know what must be rebuilt when you make changes to a source file, and which tasks can run in parallel. This means that all builds are incremental and will always produce the same result.
*   Scalable: Bazel can handle large builds; at Google, it is common for a server binary to have 100k source files, and builds where no files were changed take about ~200ms.

## Why doesn’t Google use...?

*   Make, Ninja: These tools give very exact control over what commands get invoked to build files, but it’s up to the user to write rules that are correct.
    * Users interact with Bazel on a higher level. For example, Bazel has built-in rules for “Java test”, “C++ binary”, and notions such as “target platform” and “host platform”. These rules have been battle tested to be foolproof.
*   Ant and Maven: Ant and Maven are primarily geared toward Java, while Bazel handles multiple languages. Bazel encourages subdividing codebases in smaller reusable units, and can rebuild only ones that need rebuilding. This speeds up development when working with larger codebases.
*   Gradle: Bazel configuration files are much more structured than Gradle’s, letting Bazel understand exactly what each action does. This allows for more parallelism and better reproducibility.
*   Pants, Buck: Both tools were created and developed by ex-Googlers at Twitter and Foursquare, and Facebook respectively. They have been modeled after Bazel, but their feature sets are different, so they aren’t viable alternatives for us.

## Where did Bazel come from?

Bazel is a flavor of the tool that Google uses to build its server software internally. It has expanded to build other software as well, like mobile apps (iOS, Android) that connect to our servers.

## Did you rewrite your internal tool as open-source? Is it a fork?

Bazel shares most of its code with the internal tool and its rules are used for millions of builds every day.

## Why did Google build Bazel?

A long time ago, Google built its software using large, generated Makefiles. These led to slow and unreliable builds, which began to interfere with our developers’ productivity and the company’s agility. Bazel was a way to solve these problems.

## Does Bazel require a build cluster?

Bazel runs build operations locally by default. However, Bazel can also connect to a build cluster for even faster builds and tests. See our documentation on [remote execution and caching](/remote/rbe) and [remote caching](/remote/caching) for further details.

## How does the Google development process work?

For our server code base, we use the following development workflow:

*   All our server code is in a single, gigantic version control system.
*   Everybody builds their software with Bazel.
*   Different teams own different parts of the source tree, and make their components available as `BUILD` targets.
*   Branching is primarily used for managing releases, so everybody develops their software at the head revision.

Bazel is a cornerstone of this philosophy: since Bazel requires all dependencies to be fully specified, we can predict which programs and tests are affected by a change, and vet them before submission.

More background on the development process at Google can be found on the [eng tools blog](http://google-engtools.blogspot.com/){: .external}.

## Why did you open up Bazel?

Building software should be fun and easy. Slow and unpredictable builds take the fun out of programming.

## Why would I want to use Bazel?

*   Bazel may give you faster build times because it can recompile only the files that need to be recompiled. Similarly, it can skip re-running tests that it knows haven’t changed.
*   Bazel produces deterministic results. This eliminates skew between incremental and clean builds, laptop and CI system, etc.
*   Bazel can build different client and server apps with the same tool from the same workspace. For example, you can change a client/server protocol in a single commit, and test that the updated mobile app works with the updated server, building both with the same tool, reaping all the aforementioned benefits of Bazel.

## Can I see examples?

Yes; see a [simple example](https://github.com/bazelbuild/bazel/blob/master/examples/cpp/BUILD){: .external}
or read the [Bazel source code](https://github.com/bazelbuild/bazel/blob/master/src/BUILD){: .external} for a more complex example.


## What is Bazel best at?

Bazel shines at building and testing projects with the following properties:

*   Projects with a large codebase
*   Projects written in (multiple) compiled languages
*   Projects that deploy on multiple platforms
*   Projects that have extensive tests

## Where can I run Bazel?

Bazel runs on Linux, macOS (OS X), and Windows.

Porting to other UNIX platforms should be relatively easy, as long as a JDK is available for the platform.

## What should I not use Bazel for?

*   Bazel tries to be smart about caching. This means that it is not good for running build operations whose outputs should not be cached. For example, the following steps should not be run from Bazel:
    *   A compilation step that fetches data from the internet.
    *   A test step that connects to the QA instance of your site.
    *   A deployment step that changes your site’s cloud configuration.
*   If your build consists of a few long, sequential steps, Bazel may not be able to help much. You’ll get more speed by breaking long steps into smaller, discrete targets that Bazel can run in parallel.

## How stable is Bazel’s feature set?

The core features (C++, Java, and shell rules) have extensive use inside Google, so they are thoroughly tested and have very little churn. Similarly, we test new versions of Bazel across hundreds of thousands of targets every day to find regressions, and we release new versions multiple times every month.

In short, except for features marked as experimental, Bazel should Just Work. Changes to non-experimental rules will be backward compatible. A more detailed list of feature support statuses can be found in our [support document](/contribute/support).

## How stable is Bazel as a binary?

Inside Google, we make sure that Bazel crashes are very rare. This should also hold for our open source codebase.

## How can I start using Bazel?

See [Getting Started](/start/).

## Doesn’t Docker solve the reproducibility problems?

With Docker you can easily create sandboxes with fixed OS releases, for example, Ubuntu 12.04, Fedora 21. This solves the problem of reproducibility for the system environment – that is, “which version of /usr/bin/c++ do I need?”

Docker does not address reproducibility with regard to changes in the source code. Running Make with an imperfectly written Makefile inside a Docker container can still yield unpredictable results.

Inside Google, we check tools into source control for reproducibility. In this way, we can vet changes to tools (“upgrade GCC to 4.6.1”) with the same mechanism as changes to base libraries (“fix bounds check in OpenSSL”).

## Can I build binaries for deployment on Docker?

With Bazel, you can build standalone, statically linked binaries in C/C++, and self-contained jar files for Java. These run with few dependencies on normal UNIX systems, and as such should be simple to install inside a Docker container.

Bazel has conventions for structuring more complex programs, for example, a Java program that consumes a set of data files, or runs another program as subprocess. It is possible to package up such environments as standalone archives, so they can be deployed on different systems, including Docker images.

## Can I build Docker images with Bazel?

Yes, you can use our [Docker rules](https://github.com/bazelbuild/rules_docker){: .external} to build reproducible Docker images.

## Will Bazel make my builds reproducible automatically?

For Java and C++ binaries, yes, assuming you do not change the toolchain. If you have build steps that involve custom recipes (for example, executing binaries through a shell script inside a rule), you will need to take some extra care:

*   Do not use dependencies that were not declared. Sandboxed execution (–spawn\_strategy=sandboxed, only on Linux) can help find undeclared dependencies.
*   Avoid storing timestamps and user-IDs in generated files. ZIP files and other archives are especially prone to this.
*   Avoid connecting to the network. Sandboxed execution can help here too.
*   Avoid processes that use random numbers, in particular, dictionary traversal is randomized in many programming languages.

## Do you have binary releases?

Yes, you can find the latest [release binaries](https://github.com/bazelbuild/bazel/releases/latest){: .external} and review our [release policy](/release/)

## I use Eclipse/IntelliJ/XCode. How does Bazel interoperate with IDEs?

For IntelliJ, check out the [IntelliJ with Bazel plugin](https://ij.bazel.build/).

For XCode, check out [Tulsi](http://tulsi.bazel.build/).

For Eclipse, check out [E4B plugin](https://github.com/bazelbuild/e4b){: .external}.

For other IDEs, check out the [blog post](https://blog.bazel.build/2016/06/10/ide-support.html) on how these plugins work.

## I use Jenkins/CircleCI/TravisCI. How does Bazel interoperate with CI systems?

Bazel returns a non-zero exit code if the build or test invocation fails, and this should be enough for basic CI integration. Since Bazel does not need clean builds for correctness, the CI system should not be configured to clean before starting a build/test run.

Further details on exit codes are in the [User Manual](/docs/user-manual).

## What future features can we expect in Bazel?

See our [Roadmaps](/about/roadmap).

## Can I use Bazel for my INSERT LANGUAGE HERE project?

Bazel is extensible. Anyone can add support for new languages. Many languages are supported: see the [build encyclopedia](/reference/be/overview) for a list of recommendations and [awesomebazel.com](https://awesomebazel.com/){: .external} for a more comprehensive list.

If you would like to develop extensions or learn how they work, see the documentation for [extending Bazel](/extending/concepts).

## Can I contribute to the Bazel code base?

See our [contribution guidelines](/contribute/).

## Why isn’t all development done in the open?

We still have to refactor the interfaces between the public code in Bazel and our internal extensions frequently. This makes it hard to do much development in the open.

## Are you done open sourcing Bazel?

Open sourcing Bazel is a work-in-progress. In particular, we’re still working on open sourcing:

*   Many of our unit and integration tests (which should make contributing patches easier).
*   Full IDE integration.

Beyond code, we’d like to eventually have all code reviews, bug tracking, and design decisions happen publicly, with the Bazel community involved. We are not there yet, so some changes will simply appear in the Bazel repository without clear explanation. Despite this lack of transparency, we want to support external developers and collaborate. Thus, we are opening up the code, even though some of the development is still happening internal to Google. Please let us know if anything seems unclear or unjustified as we transition to an open model.

## Are there parts of Bazel that will never be open sourced?

Yes, some of the code base either integrates with Google-specific technology or we have been looking for an excuse to get rid of (or is some combination of the two). These parts of the code base are not available on GitHub and probably never will be.

## How do I contact the team?

We are reachable at bazel-discuss@googlegroups.com.

## Where do I report bugs?

Open an issue [on GitHub](https://github.com/bazelbuild/bazel/issues){: .external}.

## What’s up with the word “Blaze” in the codebase?

This is an internal name for the tool. Please refer to Blaze as Bazel.

## Why do other Google projects (Android, Chrome) use other build tools?

Until the first (Alpha) release, Bazel was not available externally, so open source projects such as Chromium and Android could not use it. In addition, the original lack of Windows support was a problem for building Windows applications, such as Chrome. Since the project has matured and become more stable, the [Android Open Source Project](https://source.android.com/) is in the process of migrating to Bazel.

## How do you pronounce “Bazel”?

The same way as “basil” (the herb) in US English: “BAY-zel”. It rhymes with “hazel”. IPA: /ˈbeɪzˌəl/


Project: /_project.yaml
Book: /_book.yaml

# Bazel Vision

{% include "_buttons.html" %}

Any software developer can efficiently build, test, and package
any project, of any size or complexity, with tooling that's easy to adopt and
extend.

*   **Engineers can take build fundamentals for granted.** Software developers
    focus on the creative process of authoring code because the mechanical
    process of build and test is solved. When customizing the build system to
    support new languages or unique organizational needs, users focus on the
    aspects of extensibility that are unique to their use case, without having
    to reinvent the basic plumbing.

*   **Engineers can easily contribute to any project.** A developer who wants to
    start working on a new project can simply clone the project and run the
    build. There's no need for local configuration - it just works. With
    cross-platform remote execution, they can work on any machine anywhere and
    fully test their changes against all platforms the project targets.
    Engineers can quickly configure the build for a new project or incrementally
    migrate an existing build.

*   **Projects can scale to any size codebase, any size team.** Fast,
    incremental testing allows teams to fully validate every change before it is
    committed. This remains true even as repos grow, projects span multiple
    repos, and multiple languages are introduced. Infrastructure does not force
    developers to trade test coverage for build speed.

**We believe Bazel has the potential to fulfill this vision.**

Bazel was built from the ground up to enable builds that are reproducible (a
given set of inputs will always produce the same outputs) and portable (a build
can be run on any machine without affecting the output).

These characteristics support safe incrementality (rebuilding only changed
inputs doesn't introduce the risk of corruption) and distributability (build
actions are isolated and can be offloaded). By minimizing the work needed to do
a correct build and parallelizing that work across multiple cores and remote
systems, Bazel can make any build fast.

Bazel's abstraction layer — instructions specific to languages, platforms, and
toolchains implemented in a simple extensibility language — allows it to be
easily applied to any context.

## Bazel core competencies {:#bazel-core-competencies}

1.  Bazel supports **multi-language, multi-platform** builds and tests. You can
    run a single command to build and test your entire source tree, no matter
    which combination of languages and platforms you target.
1.  Bazel builds are **fast and correct**. Every build and test run is
    incremental, on your developers' machines and on CI.
1.  Bazel provides a **uniform, extensible language** to define builds for any
    language or platform.
1.  Bazel allows your builds **to scale** by connecting to remote execution and
    caching services.
1.  Bazel works across **all major development platforms** (Linux, MacOS, and
    Windows).
1.  We accept that adopting Bazel requires effort, but **gradual adoption** is
    possible. Bazel interfaces with de-facto standard tools for a given
    language/platform.

## Serving language communities {:#language-communities}

Software engineering evolves in the context of language communities — typically,
self-organizing groups of people who use common tools and practices.

To be of use to members of a language community, high-quality Bazel rules must be
available that integrate with the workflows and conventions of that community.

Bazel is committed to be extensible and open, and to support good rulesets for
any language.

###  Requirements of a good ruleset {:#ruleset-requirements}

1.  The rules need to support efficient **building and testing** for the
    language, including code coverage.
1.  The rules need to **interface with a widely-used "package manager"** for the
    language (such as Maven for Java), and support incremental migration paths
    from other widely-used build systems.
1.  The rules need to be **extensible and interoperable**, following
    ["Bazel sandwich"](https://github.com/bazelbuild/bazel-website/blob/master/designs/_posts/2016-08-04-extensibility-for-native-rules.md)
    principles.
1.  The rules need to be **remote-execution ready**. In practice, this means
    **configurable using the [toolchains](/extending/toolchains) mechanism**.
1.  The rules (and Bazel) need to interface with a **widely-used IDE** for the
    language, if there is one.
1.  The rules need to have **thorough, usable documentation,** with introductory
    material for new users, comprehensive docs for expert users.

Each of these items is essential and only together do they deliver on Bazel's
competencies for their particular ecosystem.

They are also, by and large, sufficient - once all are fulfilled, Bazel fully
delivers its value to members of that language community.


Project: /_project.yaml
Book: /_book.yaml
# Bazel roadmap

{% include "_buttons.html" %}

As Bazel continues to evolve in response to your needs, we want to share our
2025 roadmap update.

We plan to bring Bazel 9.0
[long term support (LTS)](https://bazel.build/release/versioning) to you in late
2025.

## Full transition to Bzlmod

[Bzlmod](https://bazel.build/docs/bzlmod) has been the standard external
dependency system in Bazel since Bazel 7, replacing the legacy WORKSPACE system.
As of March 2025, the [Bazel Central Registry](https://registry.bazel.build/)
hosts more than 650 modules.

With Bazel 9, we will completely remove WORKSPACE functionality, and Bzlmod will
be the only way to introduce external dependencies in Bazel. To minimize the
migration cost for the community, we'll focus on further improving our migration
[guide](https://bazel.build/external/migration) and
[tool](https://github.com/bazelbuild/bazel-central-registry/tree/main/tools#migrate_to_bzlmodpy).

Additionally, we aim to implement an improved shared repository cache (see
[#12227](https://github.com/bazelbuild/bazel/issues/12227))
with garbage collection, and may backport it to Bazel 8. The Bazel Central
Registry will also support verifying SLSA attestations.

## Migration of Android, C++, Java, Python, and Proto rules

With Bazel 8, we have migrated support for Android, Java, Python, and Proto
rules out of the Bazel codebase into Starlark rules in their corresponding
repositories. To ease the migration, we implemented the autoload features in
Bazel, which can be controlled with
[--incompatible_autoload_externally](https://github.com/bazelbuild/bazel/issues/23043)
and [--incompatible_disable_autoloads_in_main_repo](https://github.com/bazelbuild/bazel/issues/25755)
flags.

With Bazel 9, we aim to disable autoloads by default and require every project
to explicitly load required rules in BUILD files.

We will rewrite most of C++ language support to Starlark, detach it from Bazel
binary and move it into the [/rules_cc](https://github.com/bazelbuild/rules_cc)
repository. This is the last remaining major language support that is still part
of Bazel.

We're also porting unit tests for C++, Java, and Proto rules to Starlark, moving
them to repositories next to the implementation to increase velocity of rule
authors.

## Starlark improvements

Bazel will have the ability to evaluate symbolic macros lazily. This means that
a symbolic macro won't run if the targets it declares are not requested,
improving performance for very large packages.

Starlark will have an experimental type system, similar to Python's type
annotations. We expect the type system to stabilize _after_ Bazel 9 is launched.

## Configurability

Our main focus is reducing the cost and confusion of build flags.

We're [experimenting](https://github.com/bazelbuild/bazel/issues/24839) with a
new project configuration model that doesn't make users have to know which build
and test flags to set where. So `$ bazel test //foo` automatically sets the
right flags based on `foo`'s project's policy. This will likely remain
experimental in 9.0 but guiding feedback is welcome.

[Flag scoping](https://github.com/bazelbuild/bazel/issues/24042) lets you strip
out Starlark flags when they leave project boundaries, so they don't break
caching on transitive dependencies that don't need them. This makes builds that
use [transitions](https://bazel.build/extending/config#user-defined-transitions)
cheaper and faster.
[Here's](https://github.com/gregestren/snippets/tree/master/project_scoped_flags)
an example. We're extending the idea to control which flags propagate to
[exec configurations](https://bazel.build/extending/rules#configurations) and
are considering even more flexible support like custom Starlark to determine
which dependency edges should propagate flags.

We're up-prioritizing effort to move built-in language flags out of Bazel and
into Starlark, where they can live with related rule definitions.

## Remote execution improvements

We plan to add support for asynchronous execution, speeding up remote execution
by increasing parallelism.

---

To follow updates to the roadmap and discuss planned features, join the
community Slack server at [slack.bazel.build](https://slack.bazel.build/).

*This roadmap is intended to help inform the community about the team's
intentions for Bazel 9.0. Priorities are subject to change in response to
developer and customer feedback, or to new market opportunities.*


Project: /_project.yaml
Book: /_book.yaml

# Why Bazel?

{% include "_buttons.html" %}

Bazel is a [fast](#fast), [correct](#correct), and [extensible](#extensible)
build tool with [integrated testing](#integrated-testing) that supports multiple
[languages](#multi-language), [repositories](#multi-repository), and
[platforms](#multi-platform) in an industry-leading [ecosystem](#ecosystem).

## Bazel is fast {:#fast}

Bazel knows exactly what input files each build command needs, avoiding
unnecessary work by re-running only when the set of input files have
changed between each build.
It runs build commands with as much parallelism as possible, either within the
same computer or on [remote build nodes](/remote/rbe). If the structure of build
allows for it, it can run thousands of build or test commands at the same time.

This is supported by multiple caching layers, in memory, on disk and on the
remote build farm, if available. At Google, we routinely achieve cache hit rates
north of 99%.

## Bazel is correct {:#correct}

Bazel ensures that your binaries are built *only* from your own
source code. Bazel actions run in individual sandboxes and Bazel tracks
every input file of the build, only and always re-running build
commands when it needs to. This keeps your binaries up-to-date so that the
[same source code always results in the same binary](/basics/hermeticity), bit
by bit.

Say goodbyte to endless `make clean` invocations and to chasing phantom bugs
that were in fact resolved in source code that never got built.

## Bazel is extensible {:#extensible}

Harness the full power of Bazel by writing your own rules and macros to
customize Bazel for your specific needs across a wide range of projects.

Bazel rules are written in [Starlark](/rules/language), our
in-house programming language that's a subset of Python. Starlark makes
rule-writing accessible to most developers, while also creating rules that can
be used across the ecosystem.

## Integrated testing {:#integrated-testing}

Bazel's [integrated test runner](/docs/user-manual#running-tests)
knows and runs only those tests needing to be re-run, using remote execution
(if available) to run them in parallel. Detect flakes early by using remote
execution to quickly run a test thousands of times.

Bazel [provides facilities](/remote/bep) to upload test results to a central
location, thereby facilitating efficient communication of test outcomes, be it
on CI or by individual developers.

## Multi-language support {:#multi-language}

Bazel supports many common programming languages including C++, Java,
Kotlin, Python, Go, and Rust. You can build multiple binaries (for example,
backend, web UI and mobile app) in the same Bazel invocation without being
constrained to one language's idiomatic build tool.

## Multi-repository support {:#multi-repository}

Bazel can [gather source code from multiple locations](/external/overview): you
don't need to vendor your dependencies (but you can!), you can instead point
Bazel to the location of your source code or prebuilt artifacts (e.g. a git
repository or Maven Central), and it takes care of the rest.

## Multi-platform support {:#multi-platform}

Bazel can simultaneously build projects for multiple platforms including Linux,
macOS, Windows, and Android. It also provides powerful
[cross-compilation capabilities](/extending/platforms) to build code for one
platform while running the build on another.

## Wide ecosystem {:#ecosystem}

[Industry leaders](/community/users) love Bazel, building a large
community of developers who use and contribute to Bazel. Find a tools, services
and documentation, including [consulting and SaaS offerings](/community/experts)
Bazel can use. Explore extensions like support for programming languages in
our [open source software repositories](/rules).