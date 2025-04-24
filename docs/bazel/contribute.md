

# Contributing to Bazel

There are many ways to help the Bazel project and ecosystem.

## Provide feedback

As you use Bazel, you may find things that can be improved.
You can help by [reporting issues](http://github.com/bazelbuild/bazel/issues){: .external}
when:

   - Bazel crashes or you encounter a bug that can [only be resolved using `bazel
     clean`](/run/build#correct-incremental-rebuilds).
   - The documentation is incomplete or unclear. You can also report issues
     from the page you are viewing by using the "Create issue"
     link at the top right corner of the page.
   - An error message could be improved.

## Participate in the community

You can engage with the Bazel community by:

   - Answering questions [on Stack Overflow](
     https://stackoverflow.com/questions/tagged/bazel){: .external}.
   - Helping other users [on Slack](https://slack.bazel.build){: .external}.
   - Improving documentation or [contributing examples](
     https://github.com/bazelbuild/examples){: .external}.
   - Sharing your experience or your tips, for example, on a blog or social media.

## Contribute code

Bazel is a large project and making a change to the Bazel source code
can be difficult.

You can contribute to the Bazel ecosystem by:

   - Helping rules maintainers by contributing pull requests.
   - Creating new rules and open-sourcing them.
   - Contributing to Bazel-related tools, for example, migration tools.
   - Improving Bazel integration with other IDEs and tools.

Before making a change, [create a GitHub
issue](http://github.com/bazelbuild/bazel/issues){: .external}
or email [bazel-discuss@](mailto:bazel-discuss@googlegroups.com){: .external}.

The most helpful contributions fix bugs or add features (as opposed
to stylistic, refactoring, or "cleanup" changes). Your change should
include tests and documentation, keeping in mind backward-compatibility,
portability, and the impact on memory usage and performance.

To learn about how to submit a change, see the
[patch acceptance process](/contribute/patch-acceptance).

## Bazel's code description

Bazel has a large codebase with code in multiple locations. See the [codebase guide](/contribute/codebase) for more details.

Bazel is organized as follows:

*  Client code is in `src/main/cpp` and provides the command-line interface.
*  Protocol buffers are in `src/main/protobuf`.
*  Server code is in `src/main/java` and `src/test/java`.
   *  Core code which is mostly composed of [SkyFrame](/reference/skyframe)
      and some utilities.
   *  Built-in rules are in `com.google.devtools.build.lib.rules` and in
     `com.google.devtools.build.lib.bazel.rules`. You might want to read about
     the [Challenges of Writing Rules](/rules/challenges) first.
*  Java native interfaces are in `src/main/native`.
*  Various tooling for language support are described in the list in the
   [compiling Bazel](/install/compile-source) section.

### Searching Bazel's source code

To quickly search through Bazel's source code, use
[Bazel Code Search](https://source.bazel.build/). You can navigate Bazel's
repositories, branches, and files. You can also view history, diffs, and blame
information. To learn more, see the
[Bazel Code Search User Guide](/contribute/search).



# Searching the codebase

## Product overview

Bazel's [code search and source browsing interface](https://source.bazel.build)
is a web-based tool for browsing Bazel source code repositories. You can
use these features to navigate among different repositories, branches, and
files. You can also view history, diffs, and blame information.

## Getting started

Note: For the best experience, use the latest version of Chrome, Safari, or
Firefox.

To access the code search and source browsing interface, open
[https://source.bazel.build](https://source.bazel.build) in your web browser.

The main screen appears. This screen contains the following components:

1. The Breadcrumb toolbar. This toolbar displays your current location in the
repository and allows you to move quickly to another location such as another
repository, or another location within a repository, such as a file, branch, or
commit.

1. A list of repositories that you can browse.

At the top of the screen is a search box. You can use this box to search for
specific files and code.

## Working with repositories

### Opening a repository

To open a repository, click its name from the main screen.

Alternatively, you can use the Breadcrumb toolbar to browse for a
specificrepository. This toolbar displays your current location in the
repository and allows you to move quickly to another location such as another
repository, or another location within a repository, such as a file, branch, or
commit.

### Switch repositories

To switch to a different repository, select the repository from the Breadcrumb toolbar.

### View a repository at a specific commit

To view a repository at a specific commit:

1. From the view of the repository, select the file.
1. From the Breadcrumb toolbar, open the **Branch** menu.
1. In the submenu that appears, click **Commit**.
1. Select the commit you want to view.

The interface now shows the repository as it existed at that commit.

### Open a branch, commit, or tag

By default, the code search and source browsing interface opens a repository to
the default branch.  To open a different branch, from the Breadcrumb toolbar,
click the **Branch/Commit/Tag** menu. A submenu opens, allowing you to select a
branch using a branch name, a tag name, or through a search box.

*  To select a branch using a branch name, select **Branch** and then click the
   name of the branch.
*  To select a branch using a tag name, select **Tag** and
   then click the tag name.
*  To select a branch using a commit id, select **Commit** and then click the
   commit id.
*  To search for a branch, commit, or tag, select the corresponding item and
   type a search term in the search box.

## Working with files

When you select a repository from the main screen, the screen changes to display
a view of that repository. If a README file exists, its contents appear in the
file pane, located on the right side of the screen. Otherwise, a list of
repository's files and folders appear.  On the left side of the screen is a tree
view of the repository's files and folders. You can use this tree to browse and
open specific files.

Notice that, when you are viewing a repository, the Breadcrumb toolbar now has
three components:

*  A **Repository** menu, from which you can select different repositories
*  A **Branch/Commit/Tag** menu, from which you can select specific branches,
   tags, or commits
*  A **File path** box, which displays the name of the current file or folder
   and its corresponding path

### Open a file

You can open a file by browsing to its directory and selecting it. The view of
the repository updates to show the contents of the file in the file pane, and
its location in the repository in the tree pane.

### View file changes

To view file changes:

1. From the view of the repository, select the file.
1. Click **BLAME**, located in the upper-right corner.

The file pane updates to display who made changes to the file and when.

### View change history

To view the change history of a file:

1.  From the view of the repository, select the file.
1.  Click **HISTORY**, located in the upper-right corner.
    The **Change history** pane appears, showing the commits for this file.

### View code reviews

For Gerrit code reviews, you can open the tool directly from the Change History pane.

To view the code review for a file:

1. From the view of the repository, select the file.
1. Click **HISTORY**, located in the upper-right corner. The Change History pane
   appears, showing the commits for this file.
1. Hover over a commit. A **More** button (three vertical dots) appears.
1. Click the **More** button.
1. Select **View code review**.

The Gerrit Code Review tool opens in a new browser window.

### Open a file at a specific commit

To open a file at a specific commit:

1. From the view of the repository, select the file.
1. Click **HISTORY**, located in the upper-right corner. The Change History pane
   appears, showing the commits for this file.
1. Hover over a commit. A **VIEW** button appears.
1. Click the **VIEW** button.

### Compare a file to a different commit

To compare a file at a different commit:

1. From the view of the repository, select the file. To compare from two
   different commits, first open the file at that commit.
1. Hover over a commit. A **DIFF** button appears.
1. Click the **DIFF** button.

The file pane updates to display a side-by-side comparison between the two
files. The oldest of the two commits is always on the left.

In the Change History pane, both commits are highlighted, and a label indicates
if the commit is displayed on the left or the right.

To change either file, hover over the commit in the Change History pane. Then,
click either the **Left** or **Right** button to have the open the commit on the
left or right side of the diff.

### Browsing cross references

Another way to browse source repositories is through the use of cross
references. These references appear automatically as hyperlinks within a given
source file.

To make cross references easier to identify, click **Cross References**,
located in the upper-right corner. This option displays an underline below all
cross references in a file.

**Note:** If **Cross References** is grayed out, it indicates that
cross references are not available for that file.

Click a cross reference to open the Cross Reference pane. This pane contains
two sections:

* A **Definition** section, which lists the file or files that define the
  reference
* A **References** section, which lists the files in which the reference also
  appears

Both sections display the name of the file, as well as the line or lines
that contains the reference. To open a file from the Cross Reference pane,
click the line number entry. The file appears in a new section of the pane,
allowing you to continue to browse the file while keeping the original file
in view.

You can continue to browse cross references using the Cross Reference pane, just
as you can in the File pane. When you do, the pane displays a breadcrumb trail,
which you can use to navigate between different cross references.

## Searching for code

You can search for specific files or code snippets using the search box located
at the top of the screen. Searches are always against the default branch.

All searches use [RE2 regular expressions](https://github.com/google/re2/wiki/Syntax){: .external}
by default. If you do not want to use regular expressions, enclose your search
in double quotes ( " ).

**Note:** To quickly search for a specific file, either add a backslash in front
of the period, or enclose the entire file name in quotes.

```
foo\.java
"foo.java"
```

You can refine your search using the following filters.

<table border="1px">
<thead>
<tr>
<th style="padding:5px"><strong>Filter</strong></th>
<th style="padding:5px"><strong>Other options</strong></th>
<th style="padding:5px"><strong>Description</strong></th>
<th style="padding:5px"><strong>Example</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td style="padding:5px">lang:</td>
<td style="padding:5px">language:</td>
<td style="padding:5px">Perform an exact match by file language.</td>
<td style="padding:5px">lang:java test</td>
</tr>
<tr>
<td style="padding:5px">file:</td>
<td style="padding:5px">filepath:<br>
path:<br>
f:</td>
<td style="padding:5px"></td>
<td style="padding:5px"></td>
</tr>
<tr>
<td style="padding:5px">case:yes</td>
<td style="padding:5px"></td>
<td style="padding:5px">Make the search case sensitive. By default, searches are not case-sensitive.</td>
<td style="padding:5px">case:yes Hello World</td>
</tr>
<tr>
<td style="padding:5px">class:</td>
<td style="padding:5px"></td>
<td style="padding:5px">Search for a class name.</td>
<td style="padding:5px">class:MainClass</td>
</tr>
<tr>
<td style="padding:5px">function:</td>
<td style="padding:5px">func:</td>
<td style="padding:5px">Search for a function name.</td>
<td style="padding:5px">function:print</td>
</tr>
<tr>
<td style="padding:5px">-</td>
<td style="padding:5px"></td>
<td style="padding:5px">Negates the term from the search.</td>
<td style="padding:5px">hello -world</td>
</tr>
<tr>
<td style="padding:5px">\</td>
<td style="padding:5px"></td>
<td style="padding:5px">Escapes special characters, such as ., \, or (.</td>
<td style="padding:5px">run\(\)</td>
</tr>
<tr>
<td style="padding:5px">"[term]"</td>
<td style="padding:5px"></td>
<td style="padding:5px">Perform a literal search.</td>
<td style="padding:5px">"class:main"</td>
</tr>
</tbody>
</table>

## Additional Support

To report an issue, click the **Feedback** button that appears in the top
right-hand corner of the screen and enter your feedback in the provided form.



# Guide for Bazel Maintainers

This is a guide for the maintainers of the Bazel open source project.

If you are looking to contribute to Bazel, please read [Contributing to
Bazel](/contribute) instead.

The objectives of this page are to:

1. Serve as the maintainers' source of truth for the project’s contribution
   process.
1. Set expectations between the community contributors and the project
   maintainers.

Bazel's [core group of contributors](/contribute/policy) has dedicated
subteams to manage aspects of the open source project. These are:

* **Release Process**: Manage Bazel's release process.
* **Green Team**: Grow a healthy ecosystem of rules and tools.
* **Developer Experience Gardeners**: Encourage external contributions, review
  issues and pull requests, and make our development workflow more open.

## Releases

* [Release Playbook](https://github.com/bazelbuild/continuous-integration/blob/master/docs/release-playbook.md){: .external}
* [Testing local changes with downstream projects](https://github.com/bazelbuild/continuous-integration/blob/master/docs/downstream-testing.md){: .external}

## Continuous Integration

Read the Green team's guide to Bazel's CI infrastructure on the
[bazelbuild/continuous-integration](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/README.md){: .external}
repository.

## Lifecycle of an Issue

1. A user creates an issue by choosing one of the
[issue templates](https://github.com/bazelbuild/bazel/issues/new/choose){: .external}
   and it enters the pool of [unreviewed open
   issues](https://github.com/bazelbuild/bazel/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+-label%3Auntriaged+-label%3Ap2+-label%3Ap1+-label%3Ap3+-label%3Ap4+-label%3Ateam-Starlark+-label%3Ateam-Rules-CPP+-label%3Ateam-Rules-Java+-label%3Ateam-XProduct+-label%3Ateam-Android+-label%3Ateam-Apple+-label%3Ateam-Configurability++-label%3Ateam-Performance+-label%3Ateam-Rules-Server+-label%3Ateam-Core+-label%3Ateam-Rules-Python+-label%3Ateam-Remote-Exec+-label%3Ateam-Local-Exec+-label%3Ateam-Bazel){: .external}.
1. A member on the Developer Experience (DevEx) subteam rotation reviews the
   issue.
   1. If the issue is **not a bug** or a **feature request**, the DevEx member
      will usually close the issue and redirect the user to
      [StackOverflow](https://stackoverflow.com/questions/tagged/bazel){: .external} and
      [bazel-discuss](https://groups.google.com/forum/#!forum/bazel-discuss){: .external} for
      higher visibility on the question.
   1. If the issue belongs in one of the rules repositories owned by the
      community, like [rules_apple](https://github.com.bazelbuild/rules_apple){: .external},
      the DevEx member will [transfer this issue](https://docs.github.com/en/free-pro-team@latest/github/managing-your-work-on-github/transferring-an-issue-to-another-repository){: .external}
      to the correct repository.
   1. If the issue is vague or has missing information, the DevEx member will
      assign the issue back to the user to request for more information before
      continuing. This usually occurs when the user does not choose the right
      [issue template](https://github.com/bazelbuild/bazel/issues/new/choose)
      {: .external} or provides incomplete information.
1. After reviewing the issue, the DevEx member decides if the issue requires
   immediate attention. If it does, they will assign the **P0**
   [priority](#priority) label and an owner from the list of team leads.
1. The DevEx member assigns the `untriaged` label and exactly one [team
   label](#team-labels) for routing.
1. The DevEx member also assigns exactly one `type:` label, such as `type: bug`
   or `type: feature request`, according to the type of the issue.
1. For platform-specific issues, the DevEx member assigns one `platform:` label,
   such as `platform:apple` for Mac-specific issues.
1. If the issue is low priority and can be worked on by a new community
   contributor, the DevEx member assigns the `good first issue` label.
At this stage, the issue enters the pool of [untriaged open
issues](https://github.com/bazelbuild/bazel/issues?q=is%3Aissue+is%3Aopen+label%3Auntriaged).

Each Bazel subteam will triage all issues under labels they own, preferably on a
weekly basis. The subteam will review and evaluate the issue and provide a
resolution, if possible. If you are an owner of a team label, see [this section
](#label-own) for more information.

When an issue is resolved, it can be closed.

## Lifecycle of a Pull Request

1. A user creates a pull request.
1. If you a member of a Bazel team and sending a PR against your own area,
   you are responsible for assigning your team label and finding the best
   reviewer.
1. Otherwise, during daily triage, a DevEx member assigns one
   [team label](#team-labels) and the team's technical lead (TL) for routing.
   1. The TL may optionally assign someone else to review the PR.
1. The assigned reviewer reviews the PR and works with the author until it is
   approved or dropped.
1. If approved, the reviewer **imports** the PR's commit(s) into Google's
   internal version control system for further tests. As Bazel is the same build
   system used internally at Google, we need to test all PR commits against the
   internal test suite. This is the reason why we do not merge PRs directly.
1. If the imported commit passes all internal tests, the commit will be squashed
   and exported back out to GitHub.
1. When the commit merges into master, GitHub automatically closes the PR.

## My team owns a label. What should I do?

Subteams need to triage all issues in the [labels they own](#team-labels),
preferably on a weekly basis.

### Issues

1. Filter the list of issues by your team label **and** the `untriaged` label.
1. Review the issue.
1. Identify a [priority level](#priority) and assign the label.
  1. The issue may have already been prioritized by the DevEx subteam if it's a
     P0. Re-prioritize if needed.
  1. Each issue needs to have exactly one [priority label](#priority). If an
     issue is either P0 or P1 we assume that is actively worked on.
1. Remove the `untriaged` label.

Note that you need to be in the [bazelbuild
organization](https://github.com/bazelbuild){: .external} to be able to add or remove labels.

### Pull Requests

1. Filter the list of pull requests by your team label.
1. Review open pull requests.
  1. **Optional**: If you are assigned for the review but is not the right fit
  for it, re-assign the appropriate reviewer to perform a code review.
1. Work with the pull request creator to complete a code review.
1. Approve the PR.
1. Ensure that all tests pass.
1. Import the patch to the internal version control system and run the internal
   presubmits.
1. Submit the internal patch. If the patch submits and exports successfully, the
   PR will be closed automatically by GitHub.

## Priority

The following definitions for priority will be used by the maintainers to triage
issues.

* [**P0**](https://github.com/bazelbuild/bazel/labels/P0){: .external} - Major broken
  functionality that causes a Bazel release (minus release candidates) to be
  unusable, or a downed service that severely impacts development of the Bazel
  project. This includes regressions introduced in a new release that blocks a
  significant number of users, or an incompatible breaking change that was not
  compliant to the [Breaking
  Change](https://docs.google.com/document/d/1q5GGRxKrF_mnwtaPKI487P8OdDRh2nN7jX6U-FXnHL0/edit?pli=1#heading=h.ceof6vpkb3ik){: .external}
  policy. No practical workaround exists.
* [**P1**](https://github.com/bazelbuild/bazel/labels/P1){: .external} - Critical defect or
  feature which should be addressed in the next release, or a serious issue that
  impacts many users (including the development of the Bazel project), but a
  practical workaround exists. Typically does not require immediate action. In
  high demand and planned in the current quarter's roadmap.
* [**P2**](https://github.com/bazelbuild/bazel/labels/P2){: .external} - Defect or feature
  that should be addressed but we don't currently work on. Moderate live issue
  in a released Bazel version that is inconvenient for a user that needs to be
  addressed in an future release and/or an easy workaround exists.
* [**P3**](https://github.com/bazelbuild/bazel/labels/P3){: .external} - Desirable minor bug
  fix or enhancement with small impact. Not prioritized into Bazel roadmaps or
  any imminent release, however community contributions are encouraged.
* [**P4**](https://github.com/bazelbuild/bazel/labels/P4){: .external} - Low priority defect
  or feature request that is unlikely to get closed. Can also be kept open for a
  potential re-prioritization if more users are impacted.
* [**ice-box**](https://github.com/bazelbuild/bazel/issues?q=label%3Aice-box+is%3Aclosed){: .external}
  - Issues that we currently don't have time to deal with nor the
  time to accept contributions. We will close these issues to indicate that
  nobody is working on them, but will continue to monitor their validity over
  time and revive them if enough people are impacted and if we happen to have
  resources to deal with them. As always, feel free to comment or add reactions
  to these issues even when closed.

## Team labels

*   [`team-Android`](https://github.com/bazelbuild/bazel/labels/team-Android){: .external}: Issues for Android team
    *   Contact: [ahumesky](https://github.com/ahumesky){: .external}
*   [`team-Bazel`](https://github.com/bazelbuild/bazel/labels/team-Bazel){: .external}: General Bazel product/strategy issues
    * Contact: [meisterT](https://github.com/meisterT){: .external}
*   [`team-CLI`](https://github.com/bazelbuild/bazel/labels/team-CLI){: .external}: Console UI
    * Contact: [meisterT](https://github.com/meisterT){: .external}
*   [`team-Configurability`](https://github.com/bazelbuild/bazel/labels/team-Configurability){: .external}: Issues for Configurability team. Includes: Core build configuration and transition system. Does *not* include: Changes to new or existing flags
    * Contact: [gregestren](https://github.com/gregestren){: .external}
*   [`team-Core`](https://github.com/bazelbuild/bazel/labels/team-Core){: .external}: Skyframe, bazel query, BEP, options parsing, bazelrc
    * Contact: [haxorz](https://github.com/haxorz){: .external}
*   [`team-Documentation`](https://github.com/bazelbuild/bazel/labels/team-Documentation){: .external}: Issues for Documentation team
*   [`team-ExternalDeps`](https://github.com/bazelbuild/bazel/labels/team-ExternalDeps){: .external}: External dependency handling, Bzlmod, remote repositories, WORKSPACE file
    * Contact: [meteorcloudy](https://github.com/meteorcloudy){: .external}
*   [`team-Loading-API`](https://github.com/bazelbuild/bazel/labels/team-Loading-API){: .external}: BUILD file and macro processing: labels, package(), visibility, glob
    * Contact: [brandjon](https://github.com/brandjon){: .external}
*   [`team-Local-Exec`](https://github.com/bazelbuild/bazel/labels/team-Local-Exec){: .external}: Issues for Execution (Local) team
    * Contact: [meisterT](https://github.com/meisterT){: .external}
*   [`team-OSS`](https://github.com/bazelbuild/bazel/labels/team-OSS){: .external}: Issues for Bazel OSS team: installation, release process, Bazel packaging, website, docs infrastructure
    * Contact: [meteorcloudy](https://github.com/meteorcloudy){: .external}
*   [`team-Performance`](https://github.com/bazelbuild/bazel/labels/team-Performance){: .external}: Issues for Bazel Performance team
    * Contact: [meisterT](https://github.com/meisterT){: .external}
*   [`team-Remote-Exec`](https://github.com/bazelbuild/bazel/labels/team-Remote-Exec){: .external}: Issues for Execution (Remote) team
    * Contact: [coeuvre](https://github.com/coeuvre){: .external}
*   [`team-Rules-API`](https://github.com/bazelbuild/bazel/labels/team-Rules-API){: .external}: API for writing rules/aspects: providers, runfiles, actions, artifacts
    * Contact: [comius](https://github.com/comius){: .external}
*   [`team-Rules-CPP`](https://github.com/bazelbuild/bazel/labels/team-Rules-CPP){: .external} / [`team-Rules-ObjC`](https://github.com/bazelbuild/bazel/labels/team-Rules-ObjC){: .external}: Issues for C++/Objective-C rules, including native Apple rule logic
    * Contact: [pzembrod](https://github.com/pzembrod){: .external}
*   [`team-Rules-Java`](https://github.com/bazelbuild/bazel/labels/team-Rules-Java){: .external}: Issues for Java rules
    * Contact: [hvadehra](https://github.com/hvadehra){: .external}
*   [`team-Rules-Python`](https://github.com/bazelbuild/bazel/labels/team-Rules-Python){: .external}: Issues for the native Python rules
    * Contact: [rickeylev](https://github.com/rickeylev){: .external}
*   [`team-Rules-Server`](https://github.com/bazelbuild/bazel/labels/team-Rules-Server){: .external}: Issues for server-side rules included with Bazel
    * Contact: [comius](https://github.com/comius){: .external}
*   [`team-Starlark-Integration`](https://github.com/bazelbuild/bazel/labels/team-Starlark-Integration){: .external}: Non-API Bazel + Starlark integration. Includes: how Bazel triggers the Starlark interpreter, Stardoc, builtins injection, character encoding.  Does *not* include: BUILD or .bzl language issues.
    * Contact: [brandjon](https://github.com/brandjon){: .external}
*   [`team-Starlark-Interpreter`](https://github.com/bazelbuild/bazel/labels/team-Starlark-Interpreter){: .external}: Issues for the Starlark interpreter (anything in [java.net.starlark](https://github.com/bazelbuild/bazel/tree/master/src/main/java/net/starlark/java)). BUILD and .bzl API issues (which represent Bazel's *integration* with Starlark) go in `team-Build-Language`.
    * Contact: [brandjon](https://github.com/brandjon){: .external}

For new issues, we deprecated the `category: *` labels in favor of the team
labels.

See the full list of labels [here](https://github.com/bazelbuild/bazel/labels){: .external}.



# Bazel docs style guide

Thank you for contributing to Bazel's documentation. This serves as a quick
documentation style guide to get you started. For any style questions not
answered by this guide, follow the
[Google developer documentation style guide](https://developers.google.com/style){: .external}.

## Defining principles

Bazel docs should uphold these principles:

-  **Concise.** Use as few words as possible.
-  **Clear.** Use plain language. Write without jargon for a fifth-grade
   reading level.
-  **Consistent.** Use the same words or phrases for repeated concepts
   throughout the docs.
-  **Correct.** Write in a way where the content stays correct for as long as
   possible by avoiding time-based information and promises for the future.

## Writing

This section contains basic writing tips.

### Headings

-  Page-level headings start at H2. (H1 headings are used as page titles.)
-  Make headers as short as is sensible. This way, they fit in the TOC
   without wrapping.

   -  <span class="compare-better">Yes</span>: Permissions
   -  <span class="compare-worse">No</span>: A brief note on permissions

-  Use sentence case for headings

   -  <span class="compare-better">Yes</span>: Set up your workspace
   -  <span class="compare-worse">No</span>: Set Up Your Workspace

-  Try to make headings task-based or actionable. If headings are conceptual,
   it may be based around understanding, but write to what the user does.

   -  <span class="compare-better">Yes</span>: Preserving graph order
   -  <span class="compare-worse">No</span>: On the preservation of graph order

### Names

-  Capitalize proper nouns, such as Bazel and Starlark.

   -  <span class="compare-better">Yes</span>: At the end of the build, Bazel prints the requested targets.
   -  <span class="compare-worse">No</span>: At the end of the build, bazel prints the requested targets.

-  Keep it consistent. Don't introduce new names for existing concepts. Where
   applicable, use the term defined in the
   [Glossary](/reference/glossary).

   -  For example, if you're writing about issuing commands on a
      terminal, don't use both terminal and command line on the page.

### Page scope

-  Each page should have one purpose and that should be defined at the
   beginning. This helps readers find what they need quicker.

   -  <span class="compare-better">Yes</span>: This page covers how to install Bazel on Windows.
   -  <span class="compare-worse">No</span>: (No introductory sentence.)

-  At the end of the page, tell the reader what to do next. For pages where
   there is no clear action, you can include links to similar concepts,
   examples, or other avenues for exploration.

### Subject

In Bazel documentation, the audience should primarily be users—the people using
Bazel to build their software.

-  Address your reader as "you". (If for some reason you can't use "you",
   use gender-neutral language, such as they.)
   -  <span class="compare-better">Yes</span>: To build Java code using Bazel,
      you must install a JDK.
   -  **MAYBE:** For users to build Java code with Bazel, they must install a JDK.
   -  <span class="compare-worse">No</span>: For a user to build Java code with
      Bazel, he or she must install a JDK.

-  If your audience is NOT general Bazel users, define the audience at the
   beginning of the page or in the section. Other audiences can include
   maintainers, contributors, migrators, or other roles.
-  Avoid "we". In user docs, there is no author; just tell people what's
   possible.
   -  <span class="compare-better">Yes</span>: As Bazel evolves, you should update your code base to maintain
      compatibility.
   -  <span class="compare-worse">No</span>: Bazel is evolving, and we will make changes to Bazel that at
      times will be incompatible and require some changes from Bazel users.

### Temporal

Where possible, avoid terms that orient things in time, such as referencing
specific dates (Q2 2022) or saying "now", "currently", or "soon."  These go
stale quickly and could be incorrect if it's a future projection. Instead,
specify a version level instead, such as "Bazel X.x and higher supports
\<feature\> or a GitHub issue link.

-  <span class="compare-better">Yes</span>: Bazel 0.10.0 or later supports
   remote caching.
-  <span class="compare-worse">No</span>: Bazel will soon support remote
   caching, likely in October 2017.

### Tense

-  Use present tense. Avoid past or future tense unless absolutely necessary
   for clarity.
   -  <span class="compare-better">Yes</span>: Bazel issues an error when it
      finds dependencies that don't conform to this rule.
   -  <span class="compare-worse">No</span>:  If Bazel finds a dependency that
      does not conform to this rule, Bazel will issue an error.

-  Where possible, use active voice (where a subject acts upon an object) not
   passive voice (where an object is acted upon by a subject). Generally,
   active voice makes sentences clearer because it shows who is responsible. If
   using active voice detracts from clarity, use passive voice.
   -  <span class="compare-better">Yes</span>: Bazel initiates X and uses the
      output to build Y.
   -  <span class="compare-worse">No</span>: X is initiated by Bazel and then
      afterward Y will be built with the output.

### Tone

Write with a business friendly tone.

-  Avoid colloquial language. It's harder to translate phrases that are
   specific to English.
   -  <span class="compare-better">Yes</span>: Good rulesets
   -  <span class="compare-worse">No</span>: So what is a good ruleset?

-  Avoid overly formal language. Write as though you're explaining the
   concept to someone who is curious about tech, but doesn't know the details.

## Formatting

### File type

For readability, wrap lines at 80 characters. Long links or code snippets
may be longer, but should start on a new line. For example:

Note: Where possible, use Markdown instead of HTML in your files. Follow the
[GitHub Markdown Syntax Guide](https://guides.github.com/features/mastering-markdown/#syntax){: .external}
for recommended Markdown style.

### Links

-  Use descriptive link text instead of "here" or "below". This practice
   makes it easier to scan a doc and is better for screen readers.
   -  <span class="compare-better">Yes</span>: For more details, see [Installing Bazel].
   -  <span class="compare-worse">No</span>: For more details, see [here].

-  End the sentence with the link, if possible.
   -  <span class="compare-better">Yes</span>: For more details, see [link].
   -  <span class="compare-worse">No</span>: See [link] for more information.

### Lists

-  Use an ordered list to describe how to accomplish a task with steps
-  Use an unordered list to list things that aren't task based. (There should
   still be an order of sorts, such as alphabetical, importance, etc.)
-  Write with parallel structure. For example:
   1. Make all the list items sentences.
   1. Start with verbs that are the same tense.
   1. Use an ordered list if there are steps to follow.

### Placeholders

-  Use angle brackets to denote a variable that users should change.
   In Markdown, escape the angle brackets with a back slash: `\<example\>`.
   -  <span class="compare-better">Yes</span>: `bazel help <command>`: Prints
      help and options for `<command>`
   -  <span class="compare-worse">No</span>: bazel help _command_: Prints help
      and options for "command"

-  Especially for complicated code samples, use placeholders that make sense
   in context.

### Table of contents

Use the auto-generated TOC supported by the site. Don't add a manual TOC.

## Code

Code samples are developers' best friends. You probably know how to write these
already, but here are a few tips.

If you're referencing a small snippet of code, you can embed it in a sentence.
If you want the reader to use the code, such as copying a command, use a code
block.

### Code blocks

-  Keep it short. Eliminate all redundant or unnecessary text from a code
   sample.
-  In Markdown, specify the type of code block by adding the sample's language.

```
```shell
...
```

-  Separate commands and output into different code blocks.

### Inline code formatting

-  Use code style for filenames, directories, paths, and small bits of code.
-  Use inline code styling instead of _italics_, "quotes," or **bolding**.
   -  <span class="compare-better">Yes</span>: `bazel help <command>`: Prints
      help and options for `<command>`
   -  <span class="compare-worse">No</span>: bazel help _command_: Prints help
      and options for "command"



# Writing release notes

This document is targeted at Bazel contributors.

Commit descriptions in Bazel include a `RELNOTES:` tag followed by a release
note. This is used by the Bazel team to track changes in each release and write
the release announcement.

## Overview

* Is your change a bugfix? In that case, you don't need a release note. Please
  include a reference to the GitHub issue.

* If the change adds / removes / changes Bazel in a user-visible way, then it
  may be advantageous to mention it.

If the change is significant, follow the [design document
policy](/contribute/design-documents) first.

## Guidelines

The release notes will be read by our users, so it should be short (ideally one
sentence), avoid jargon (Bazel-internal terminology), should focus on what the
change is about.

* Include a link to the relevant documentation. Almost any release note should
  contain a link. If the description mentions a flag, a feature, a command name,
  users will probably want to know more about it.

* Use backquotes around code, symbols, flags, or any word containing an
  underscore.

* Do not just copy and paste bug descriptions. They are often cryptic and only
  make sense to us and leave the user scratching their head. Release notes are
  meant to explain what has changed and why in user-understandable language.

* Always use present tense and the format "Bazel now supports Y" or "X now does
  Z." We don't want our release notes to sound like bug entries. All release
  note entries should be informative and use a consistent style and language.

* If something has been deprecated or removed, use "X has been deprecated" or "X
  has been removed." Not "is removed" or "was removed."

* If Bazel now does something differently, use "X now $newBehavior instead of
  $oldBehavior" in present tense. This lets the user know in detail what to
  expect when they use the new release.

* If Bazel now supports or no longer supports something, use "Bazel now supports
  / no longer supports X".

* Explain why something has been removed / deprecated / changed. One sentence is
  enough but we want the user to be able to evaluate impact on their builds.

* Do NOT make any promises about future functionality. Avoid "this flag will be
  removed" or "this will be changed." It introduces uncertainty. The first thing
  the user will wonder is "when?" and we don't want them to start worrying about
  their current builds breaking at some unknown time.

## Process

As part of the [release
process](https://github.com/bazelbuild/continuous-integration/blob/master/docs/release-playbook.md){: .external},
we collect the `RELNOTES` tags of every commit. We copy everything in a [Google
Doc](https://docs.google.com/document/d/1wDvulLlj4NAlPZamdlEVFORks3YXJonCjyuQMUQEmB0/edit){: .external}
where we review, edit, and organize the notes.

The release manager sends an email to the
[bazel-dev](https://groups.google.com/forum/#!forum/bazel-dev) mailing-list.
Bazel contributors are invited to contribute to the document and make sure
their changes are correctly reflected in the announcement.

Later, the announcement will be submitted to the [Bazel
blog](https://blog.bazel.build/), using the [bazel-blog
repository](https://github.com/bazelbuild/bazel-blog/tree/master/_posts){: .external}.



# Guide for rolling out breaking changes

It is inevitable that we will make breaking changes to Bazel. We will have to
change our designs and fix the things that do not quite work. However, we need
to make sure that community and Bazel ecosystem can follow along. To that end,
Bazel project has adopted a
[backward compatibility policy](/release/backward-compatibility).
This document describes the process for Bazel contributors to make a breaking
change in Bazel to adhere to this policy.

1. Follow the [design document policy](/contribute/design-documents).

1. [File a GitHub issue.](#github-issue)

1. [Implement the change.](#implementation)

1. [Update labels.](#labels)

1. [Update repositories.](#update-repos)

1. [Flip the incompatible flag.](#flip-flag)

## GitHub issue

[File a GitHub issue](https://github.com/bazelbuild/bazel/issues){: .external}
in the Bazel repository.
[See example.](https://github.com/bazelbuild/bazel/issues/6611){: .external}

We recommend that:

* The title starts with the name of the flag (the flag name will start with
  `incompatible_`).

* You add the label
  [`incompatible-change`](https://github.com/bazelbuild/bazel/labels/incompatible-change){: .external}.

* The description contains a description of the change and a link to relevant
  design documents.

* The description contains a migration recipe, to explain users how they should
  update their code. Ideally, when the change is mechanical, include a link to a
  migration tool.

* The description includes an example of the error message users will get if
  they don't migrate. This will make the GitHub issue more discoverable from
  search engines. Make sure that the error message is helpful and actionable.
  When possible, the error message should include the name of the incompatible
  flag.

For the migration tool, consider contributing to
[Buildifier](https://github.com/bazelbuild/buildtools/blob/master/buildifier/README.md){: .external}.
It is able to apply automated fixes to `BUILD`, `WORKSPACE`, and `.bzl` files.
It may also report warnings.

## Implementation

Create a new flag in Bazel. The default value must be false. The help text
should contain the URL of the GitHub issue. As the flag name starts with
`incompatible_`, it needs metadata tags:

```java
      metadataTags = {
        OptionMetadataTag.INCOMPATIBLE_CHANGE,
      },
```

In the commit description, add a brief summary of the flag.
Also add [`RELNOTES:`](release-notes.md) in the following form:
`RELNOTES: --incompatible_name_of_flag has been added. See #xyz for details`

The commit should also update the relevant documentation, so that there is no
window of commits in which the code is inconsistent with the docs. Since our
documentation is versioned, changes to the docs will not be inadvertently
released prematurely.

## Labels

Once the commit is merged and the incompatible change is ready to be adopted, add the label
[`migration-ready`](https://github.com/bazelbuild/bazel/labels/migration-ready){: .external}
to the GitHub issue.

If a problem is found with the flag and users are not expected to migrate yet:
remove the flags `migration-ready`.

If you plan to flip the flag in the next major release, add label `breaking-change-X.0" to the issue.

## Updating repositories

Bazel CI tests a list of important projects at
[Bazel@HEAD + Downstream](https://buildkite.com/bazel/bazel-at-head-plus-downstream){: .external}. Most of them are often
dependencies of other Bazel projects, therefore it's important to migrate them to unblock the migration for the broader community. To monitor the migration status of those projects, you can use the [`bazelisk-plus-incompatible-flags` pipeline](https://buildkite.com/bazel/bazelisk-plus-incompatible-flags){: .external}.
Check how this pipeline works [here](https://github.com/bazelbuild/continuous-integration/tree/master/buildkite#checking-incompatible-changes-status-for-downstream-projects){: .external}.

Our dev support team monitors the [`migration-ready`](https://github.com/bazelbuild/bazel/labels/migration-ready){: .external} label. Once you add this label to the GitHub issue, they will handle the following:

1. Create a comment in the GitHub issue to track the list of failures and downstream projects that need to be migrated ([see example](https://github.com/bazelbuild/bazel/issues/17032#issuecomment-1353077469){: .external})

1. File Github issues to notify the owners of every downstream project broken by your incompatible change ([see example](https://github.com/bazelbuild/intellij/issues/4208){: .external})

1. Follow up to make sure all issues are addressed before the target release date

Migrating projects in the downstream pipeline is NOT entirely the responsibility of the incompatible change author, but you can do the following to accelerate the migration and make life easier for both Bazel users and the Bazel Green Team.

1. Send PRs to fix downstream projects.

1. Reach out to the Bazel community for help on migration (e.g. [Bazel Rules Authors SIG](https://bazel-contrib.github.io/SIG-rules-authors/)).

## Flipping the flag

Before flipping the default value of the flag to true, please make sure that:

* Core repositories in the ecosystem are migrated.

    On the [`bazelisk-plus-incompatible-flags` pipeline](https://buildkite.com/bazel/bazelisk-plus-incompatible-flags){: .external},
    the flag should appear under `The following flags didn't break any passing Bazel team owned/co-owned projects`.

* All issues in the checklist are marked as fixed/closed.

* User concerns and questions have been resolved.

When the flag is ready to flip in Bazel, but blocked on internal migration at Google, please consider setting the flag value to false in the internal `blazerc` file to unblock the flag flip. By doing this, we can ensure Bazel users depend on the new behaviour by default as early as possible.

When changing the flag default to true, please:

* Use `RELNOTES[INC]` in the commit description, with the
    following format:
    `RELNOTES[INC]: --incompatible_name_of_flag is flipped to true. See #xyz for
    details`
    You can include additional information in the rest of the commit description.
* Use `Fixes #xyz` in the description, so that the GitHub issue gets closed
    when the commit is merged.
* Review and update documentation if needed.
* File a new issue `#abc` to track the removal of the flag.

## Removing the flag

After the flag is flipped at HEAD, it should be removed from Bazel eventually.
When you plan to remove the incompatible flag:

* Consider leaving more time for users to migrate if it's a major incompatible change.
  Ideally, the flag  should be available in at least one major release.
* For the commit that removes the flag, use `Fixes #abc` in the description
  so that the GitHub issue gets closed when the commit is merged.



# Patch Acceptance Process

This page outlines how contributors can propose and make changes to the Bazel
code base.

1. Read the [Bazel Contribution policy](/contribute/policy).
1. Create a [GitHub issue](https://github.com/bazelbuild/bazel/){: .external} to
   discuss your plan and design. Pull requests that change or add behavior
   need a corresponding issue for tracking.
1. If you're proposing significant changes, write a
   [design document](/contribute/design-documents).
1. Ensure you've signed a [Contributor License
   Agreement](https://cla.developers.google.com){: .external}.
1. Prepare a git commit that implements the feature. Don't forget to add tests
   and update the documentation. If your change has user-visible effects, please
   [add release notes](/contribute/release-notes). If it is an incompatible change,
   read the [guide for rolling out breaking changes](/contribute/breaking-changes).
1. Create a pull request on
   [GitHub](https://github.com/bazelbuild/bazel/pulls){: .external}. If you're new to GitHub,
   read [about pull
   requests](https://help.github.com/articles/about-pull-requests/){: .external}. Note that
   we restrict permissions to create branches on the main Bazel repository, so
   you will need to push your commit to [your own fork of the
   repository](https://help.github.com/articles/working-with-forks/){: .external}.
1. A Bazel maintainer should assign you a reviewer within two business days
   (excluding holidays in the USA and Germany). If you aren't assigned a
   reviewer in that time, you can request one by emailing
   [bazel-discuss@googlegroups.com]
   (mailto:bazel-discuss@googlegroups.com){: .external}.
1. Work with the reviewer to complete a code review. For each change, create a
   new commit and push it to make changes to your pull request. If the review
   takes too long (for instance, if the reviewer is unresponsive), send an email to
   [bazel-discuss@googlegroups.com]
   (mailto:bazel-discuss@googlegroups.com){: .external}.
1. After your review is complete, a Bazel maintainer applies your patch to
   Google's internal version control system.

   This triggers internal presubmit checks
   that may suggest more changes. If you haven't expressed a preference, the
   maintainer submitting your change  adds "trivial" changes (such as
   [linting](https://en.wikipedia.org/wiki/Lint_(software))) that don't affect
   design. If deeper changes are required or you'd prefer to apply
   changes directly, you and the reviewer should communicate preferences
   clearly in review comments.

   After internal submission, the patch is exported as a Git commit,
   at which point the GitHub pull request is closed. All final changes
   are attributed to you.



# Design Documents

If you're planning to add, change, or remove a user-facing feature, or make a
*significant architectural change* to Bazel, you **must** write a design
document and have it reviewed before you can submit the change.

Here are some examples of significant changes:

*   Addition or deletion of native build rules
*   Breaking-changes to native rules
*   Changes to a native build rule semantics that affect the behavior of more
    than a single rule
*   Changes to Bazel's rule definition API
*   Changes to the APIs that Bazel uses to connect to other systems
*   Changes to the Starlark language, semantics, or APIs
*   Changes that could have a pervasive effect on Bazel performance or memory
    usage (for better or for worse)
*   Changes to widely used internal APIs
*   Changes to flags and command-line interface.

## Reasons for design reviews

When you write a design document, you can coordinate with other Bazel developers
and seek guidance from Bazel's core team. For example, when a proposal adds,
removes, or modifies any function or object available in BUILD, MODULE.bazel, or
bzl files, add the [Starlark team](maintainers-guide.md) as reviewers.
Design documents are reviewed before submission because:

*   Bazel is a very complex system; seemingly innocuous local changes can have
    significant global consequences.
*   The team gets many feature requests from users; such requests need to be
    evaluated not only for technical feasibility but importance with regards to
    other feature requests.
*   Bazel features are frequently implemented by people outside the core team;
    such contributors have widely varying levels of Bazel expertise.
*   The Bazel team itself has varying levels of expertise; no single team member
    has a complete understanding of every corner of Bazel.
*   Changes to Bazel must account for backward compatibility and avoid breaking
    changes.

Bazel's design review policy helps to maximize the likelihood that:

*   all feature requests get a baseline level of scrutiny.
*   the right people will weigh in on designs before we've invested in an
    implementation that may not work.

To help you get started, take a look at the design documents in the
[Bazel Proposals Repository](https://github.com/bazelbuild/proposals){: .external}.
Designs are works in progress, so implementation details can change over time
and with feedback. The published design documents capture the initial design,
and *not* the ongoing changes as designs are implemented. Always go to the
documentation for descriptions of current Bazel functionality.

## Contributor Workflow

As a contributor, you can write a design document, send pull requests and
request reviewers for your proposal.

### Write the design document

All design documents must have a header that includes:

*   author
*   date of last major change
*   list of reviewers, including one (and only one)
    [lead reviewer](#lead-reviewer)
*   current status (_draft_, _in review_, _approved_, _rejected_,
    _being implemented_, _implemented_)
*   link to discussion thread (_to be added after the announcement_)

The document can be written either [as a world-readable Google Doc](#gdocs)
or [using Markdown](#markdown). Read below about for a
[Markdown / Google Docs comparison](#markdown-versus-gdocs).

Proposals that have a user-visible impact must have a section documenting the
impact on backward compatibility (and a rollout plan if needed).

### Create a Pull Request

Share your design doc by creating a pull request (PR) to add the document to
[the design index](https://github.com/bazelbuild/proposals){: .external}. Add
your markdown file or a document link to your PR.

When possible, [choose a lead reviewer](#lead-reviewer).
and cc other reviewers. If you don't choose a lead reviewer, a Bazel
maintainer will assign one to your PR.

After you create your PR, reviewers can make preliminary comments during the
code review. For example, the lead reviewer can suggest extra reviewers, or
point out missing information. The lead reviewer approves the PR when they
believe the review process can start. This doesn't mean the proposal is perfect
or will be approved; it means that the proposal contains enough information to
start the discussion.

### Announce the new proposal

Send an announcement to
[bazel-dev](https://groups.google.com/forum/#!forum/bazel-dev){: .external} when
the PR is submitted.

You may copy other groups (for example,
[bazel-discuss](https://groups.google.com/forum/#!forum/bazel-discuss){: .external},
to get feedback from Bazel end-users).

### Iterate with reviewers

Anyone interested can comment on your proposal. Try to answer questions,
clarify the proposal, and address concerns.

Discussion should happen on the announcement thread. If the proposal is in a
Google Doc, comments may be used instead (Note that anonymous comments are
allowed).

### Update the status

Create a new PR to update the status of the proposal, when iteration is
complete. Send the PR to the same lead reviewer and cc the other reviewers.

To officially accept the proposal, the lead reviewer approves the PR after
ensuring that the other reviewers agree with the decision.

There must be at least 1 week between the first announcement and the approval of
a proposal. This ensures that users had enough time to read the document and
share their concerns.

Implementation can begin before the proposal is accepted, for example as a
proof-of-concept or an experimentation. However, you cannot submit the change
before the review is complete.

### Choosing a lead reviewer

A lead reviewer should be a domain expert who is:

*   Knowledgeable of the relevant subsystems
*   Objective and capable of providing constructive feedback
*   Available for the entire review period to lead the process

Consider checking the contacts for various [team
labels](/contribute/maintainers-guide#team-labels).

## Markdown vs Google Docs

Decide what works best for you, since both are accepted.

Benefits of using Google Docs:

* Effective for brainstorming, since it is easy to get started with.
* Collaborative editing.
* Quick iteration.
* Easy way to suggest edits.

Benefits of using Markdown files:

*   Clean URLs for linking.
*   Explicit record of revisions.
*   No forgetting to set up access rights before publicizing a link.
*   Easily searchable with search engines.
*   Future-proof: Plain text is not at the mercy of any specific tool
    and doesn't require an Internet connection.
*   It is possible to update them even if the author is not around anymore.
*   They can be processed automatically (update/detect dead links, fetch
    list of authors, etc.).

You can choose to first iterate on a Google Doc, and then convert it to
Markdown for posterity.

### Using Google Docs

For consistency, use the [Bazel design doc template](
https://docs.google.com/document/d/1cE5zrjrR40RXNg64XtRFewSv6FrLV6slGkkqxBumS1w/edit){: .external}.
It includes the necessary header and creates visual
consistency with other Bazel related documents. To do that, click on **File** >
**Make a copy** or click this link to [make a copy of the design doc
template](https://docs.google.com/document/d/1cE5zrjrR40RXNg64XtRFewSv6FrLV6slGkkqxBumS1w/copy){: .external}.

To make your document readable to the world, click on
**Share** > **Advanced** > **Change…**, and
choose "On - Anyone with the link".  If you allow comments on the document,
anyone can comment anonymously, even without a Google account.

### Using Markdown

Documents are stored on GitHub and use the
[GitHub flavor of Markdown](https://guides.github.com/features/mastering-markdown/){: .external}
([Specification](https://github.github.com/gfm/){: .external}).

Create a PR to update an existing document. Significant changes should be
reviewed by the document reviewers. Trivial changes (such as typos, formatting)
can be approved by anyone.

## Reviewer workflow

A reviewer comments, reviews and approves design documents.

### General reviewer responsibilities

You're responsible for reviewing design documents, asking for additional
information if needed, and approving a design that passes the review process.

#### When you receive a new proposal

1.  Take a quick look at the document.
1.  Comment if critical information is missing, or if the design doesn't fit
    with the goals of the project.
1.  Suggest additional reviewers.
1.  Approve the PR when it is ready for review.

#### During the review process

1. Engage in a dialogue with the design author about issues that are problematic
   or require clarification.
1. If appropriate, invite comments from non-reviewers who should be aware of
   the design.
1. Decide which comments must be addressed by the author as a prerequisite to
   approval.
1. Write "LGTM" (_Looks Good To Me_) in the discussion thread when you are
   happy with the current state of the proposal.

Follow this process for all design review requests. Do not approve designs
affecting Bazel if they are not in the
[design index](https://github.com/bazelbuild/proposals){: .external}.

### Lead reviewer responsibilities

You're responsible for making the go / no-go decision on implementation
of a pending design. If you're not able to do this, you should identify a
suitable delegate (reassign the PR to the delegate), or reassign the bug to a
Bazel manager for further disposition.

#### During the review process

1.  Ensure that the comment and design iteration process moves forward
    constructively.
1.  Prior to approval, ensure that concerns from other reviewers have been
    resolved.

#### After approval by all reviewers

1.  Make sure there has been at least 1 week since the announcement on the
    mailing list.
1.  Make sure the PR updates the status.
1.  Approve the PR sent by the proposal author.

#### Rejecting designs

1.  Make sure the PR author sends a PR; or send them a PR.
1.  The PR updates the status of the document.
1.  Add a comment to the document explaining why the design can't be approved in
    its current state, and outlining next steps, if any (such as "revisit invalid
    assumptions and resubmit").



# Maintaining Bazel Chocolatey package on Windows

Note: The Chocolatey package is experimental; please provide feedback
(`@petemounce` in issue tracker).

## Prerequisites

You need:

*    [chocolatey package manager](https://chocolatey.org) installed
*    (to publish) a chocolatey API key granting you permission to publish the
     `bazel` package
     * [@petemounce](https://github.com/petemounce){: .external} currently
     maintains this unofficial package.
*    (to publish) to have set up that API key for the chocolatey source locally
     via `choco apikey -k <your key here> -s https://chocolatey.org/`

## Build

Compile bazel with msys2 shell and `compile.sh`.

```powershell
pushd scripts/packages/chocolatey
  ./build.ps1 -version 0.3.2 -mode local
popd
```

Should result in `scripts/packages/chocolatey/bazel.<version>.nupkg` being
created.

The `build.ps1` script supports `mode` values `local`, `rc` and `release`.

## Test

0. Build the package (with `-mode local`)

    * run a webserver (`python -m SimpleHTTPServer` in
      `scripts/packages/chocolatey` is convenient and starts one on
      `http://localhost:8000`)

0. Test the install

    The `test.ps1` should install the package cleanly (and error if it did not
    install cleanly), then tell you what to do next.

0. Test the uninstall

    ```sh
    choco uninstall bazel
    # should remove bazel from the system
    ```

Chocolatey's moderation process automates checks here as well.

## Release

Modify `tools/parameters.json` for the new release's URI and checksum once the
release has been published to github releases.

```powershell
./build.ps1 -version <version> -isRelease
./test.ps1 -version <version>
# if the test.ps1 passes
choco push bazel.x.y.z.nupkg --source https://chocolatey.org/
```

Chocolatey.org will then run automated checks and respond to the push via email
to the maintainers.



# The Bazel codebase

This document is a description of the codebase and how Bazel is structured. It
is intended for people willing to contribute to Bazel, not for end-users.

## Introduction

The codebase of Bazel is large (~350KLOC production code and ~260 KLOC test
code) and no one is familiar with the whole landscape: everyone knows their
particular valley very well, but few know what lies over the hills in every
direction.

In order for people midway upon the journey not to find themselves within a
forest dark with the straightforward pathway being lost, this document tries to
give an overview of the codebase so that it's easier to get started with
working on it.

The public version of the source code of Bazel lives on GitHub at
[github.com/bazelbuild/bazel](http://github.com/bazelbuild/bazel). This is not
the "source of truth"; it's derived from a Google-internal source tree that
contains additional functionality that is not useful outside Google. The
long-term goal is to make GitHub the source of truth.

Contributions are accepted through the regular GitHub pull request mechanism,
and manually imported by a Googler into the internal source tree, then
re-exported back out to GitHub.

## Client/server architecture

The bulk of Bazel resides in a server process that stays in RAM between builds.
This allows Bazel to maintain state between builds.

This is why the Bazel command line has two kinds of options: startup and
command. In a command line like this:

```
    bazel --host_jvm_args=-Xmx8G build -c opt //foo:bar
```

Some options (`--host_jvm_args=`) are before the name of the command to be run
and some are after (`-c opt`); the former kind is called a "startup option" and
affects the server process as a whole, whereas the latter kind, the "command
option", only affects a single command.

Each server instance has a single associated workspace (collection of source
trees known as "repositories") and each workspace usually has a single active
server instance. This can be circumvented by specifying a custom output base
(see the "Directory layout" section for more information).

Bazel is distributed as a single ELF executable that is also a valid .zip file.
When you type `bazel`, the above ELF executable implemented in C++ (the
"client") gets control. It sets up an appropriate server process using the
following steps:

1.  Checks whether it has already extracted itself. If not, it does that. This
    is where the implementation of the server comes from.
2.  Checks whether there is an active server instance that works: it is running,
    it has the right startup options and uses the right workspace directory. It
    finds the running server by looking at the directory `$OUTPUT_BASE/server`
    where there is a lock file with the port the server is listening on.
3.  If needed, kills the old server process
4.  If needed, starts up a new server process

After a suitable server process is ready, the command that needs to be run is
communicated to it over a gRPC interface, then the output of Bazel is piped back
to the terminal. Only one command can be running at the same time. This is
implemented using an elaborate locking mechanism with parts in C++ and parts in
Java. There is some infrastructure for running multiple commands in parallel,
since the inability to run `bazel version` in parallel with another command
is somewhat embarrassing. The main blocker is the life cycle of `BlazeModule`s
and some state in `BlazeRuntime`.

At the end of a command, the Bazel server transmits the exit code the client
should return. An interesting wrinkle is the implementation of `bazel run`: the
job of this command is to run something Bazel just built, but it can't do that
from the server process because it doesn't have a terminal. So instead it tells
the client what binary it should `exec()` and with what arguments.

When one presses Ctrl-C, the client translates it to a Cancel call on the gRPC
connection, which tries to terminate the command as soon as possible. After the
third Ctrl-C, the client sends a SIGKILL to the server instead.

The source code of the client is under `src/main/cpp` and the protocol used to
communicate with the server is in `src/main/protobuf/command_server.proto` .

The main entry point of the server is `BlazeRuntime.main()` and the gRPC calls
from the client are handled by `GrpcServerImpl.run()`.

## Directory layout

Bazel creates a somewhat complicated set of directories during a build. A full
description is available in [Output directory layout](/remote/output-directories).

The "main repo" is the source tree Bazel is run in. It usually corresponds to
something you checked out from source control. The root of this directory is
known as the "workspace root".

Bazel puts all of its data under the "output user root". This is usually
`$HOME/.cache/bazel/_bazel_${USER}`, but can be overridden using the
`--output_user_root` startup option.

The "install base" is where Bazel is extracted to. This is done automatically
and each Bazel version gets a subdirectory based on its checksum under the
install base. It's at `$OUTPUT_USER_ROOT/install` by default and can be changed
using the `--install_base` command line option.

The "output base" is the place where the Bazel instance attached to a specific
workspace writes to. Each output base has at most one Bazel server instance
running at any time. It's usually at `$OUTPUT_USER_ROOT/<checksum of the path
to the workspace>`. It can be changed using the `--output_base` startup option,
which is, among other things, useful for getting around the limitation that only
one Bazel instance can be running in any workspace at any given time.

The output directory contains, among other things:

*   The fetched external repositories at `$OUTPUT_BASE/external`.
*   The exec root, a directory that contains symlinks to all the source
    code for the current build. It's located at `$OUTPUT_BASE/execroot`. During
    the build, the working directory is `$EXECROOT/<name of main
    repository>`. We are planning to change this to `$EXECROOT`, although it's a
    long term plan because it's a very incompatible change.
*   Files built during the build.

## The process of executing a command

Once the Bazel server gets control and is informed about a command it needs to
execute, the following sequence of events happens:

1.  `BlazeCommandDispatcher` is informed about the new request. It decides
    whether the command needs a workspace to run in (almost every command except
    for ones that don't have anything to do with source code, such as version or
    help) and whether another command is running.

2.  The right command is found. Each command must implement the interface
    `BlazeCommand` and must have the `@Command` annotation (this is a bit of an
    antipattern, it would be nice if all the metadata a command needs was
    described by methods on `BlazeCommand`)

3.  The command line options are parsed. Each command has different command line
    options, which are described in the `@Command` annotation.

4.  An event bus is created. The event bus is a stream for events that happen
    during the build. Some of these are exported to outside of Bazel under the
    aegis of the Build Event Protocol in order to tell the world how the build
    goes.

5.  The command gets control. The most interesting commands are those that run a
    build: build, test, run, coverage and so on: this functionality is
    implemented by `BuildTool`.

6.  The set of target patterns on the command line is parsed and wildcards like
    `//pkg:all` and `//pkg/...` are resolved. This is implemented in
    `AnalysisPhaseRunner.evaluateTargetPatterns()` and reified in Skyframe as
    `TargetPatternPhaseValue`.

7.  The loading/analysis phase is run to produce the action graph (a directed
    acyclic graph of commands that need to be executed for the build).

8.  The execution phase is run. This means running every action required to
    build the top-level targets that are requested are run.

## Command line options

The command line options for a Bazel invocation are described in an
`OptionsParsingResult` object, which in turn contains a map from "option
classes" to the values of the options. An "option class" is a subclass of
`OptionsBase` and groups command line options together that are related to each
other. For example:

1.  Options related to a programming language (`CppOptions` or `JavaOptions`).
    These should be a subclass of `FragmentOptions` and are eventually wrapped
    into a `BuildOptions` object.
2.  Options related to the way Bazel executes actions (`ExecutionOptions`)

These options are designed to be consumed in the analysis phase and (either
through `RuleContext.getFragment()` in Java or `ctx.fragments` in Starlark).
Some of them (for example, whether to do C++ include scanning or not) are read
in the execution phase, but that always requires explicit plumbing since
`BuildConfiguration` is not available then. For more information, see the
section "Configurations".

**WARNING:** We like to pretend that `OptionsBase` instances are immutable and
use them that way (such as a part of `SkyKeys`). This is not the case and
modifying them is a really good way to break Bazel in subtle ways that are hard
to debug. Unfortunately, making them actually immutable is a large endeavor.
(Modifying a `FragmentOptions` immediately after construction before anyone else
gets a chance to keep a reference to it and before `equals()` or `hashCode()` is
called on it is okay.)

Bazel learns about option classes in the following ways:

1.  Some are hard-wired into Bazel (`CommonCommandOptions`)
2.  From the `@Command` annotation on each Bazel command
3.  From `ConfiguredRuleClassProvider` (these are command line options related
    to individual programming languages)
4.  Starlark rules can also define their own options (see
    [here](/extending/config))

Each option (excluding Starlark-defined options) is a member variable of a
`FragmentOptions` subclass that has the `@Option` annotation, which specifies
the name and the type of the command line option along with some help text.

The Java type of the value of a command line option is usually something simple
(a string, an integer, a Boolean, a label, etc.). However, we also support
options of more complicated types; in this case, the job of converting from the
command line string to the data type falls to an implementation of
`com.google.devtools.common.options.Converter`.

## The source tree, as seen by Bazel

Bazel is in the business of building software, which happens by reading and
interpreting the source code. The totality of the source code Bazel operates on
is called "the workspace" and it is structured into repositories, packages and
rules.

### Repositories

A "repository" is a source tree on which a developer works; it usually
represents a single project. Bazel's ancestor, Blaze, operated on a monorepo,
that is, a single source tree that contains all source code used to run the build.
Bazel, in contrast, supports projects whose source code spans multiple
repositories. The repository from which Bazel is invoked is called the "main
repository", the others are called "external repositories".

A repository is marked by a repo boundary file (`MODULE.bazel`, `REPO.bazel`, or
in legacy contexts, `WORKSPACE` or `WORKSPACE.bazel`) in its root directory. The
main repo is the source tree where you're invoking Bazel from. External repos
are defined in various ways; see [external dependencies
overview](/external/overview) for more information.

Code of external repositories is symlinked or downloaded under
`$OUTPUT_BASE/external`.

When running the build, the whole source tree needs to be pieced together; this
is done by `SymlinkForest`, which symlinks every package in the main repository
to `$EXECROOT` and every external repository to either `$EXECROOT/external` or
`$EXECROOT/..`.

### Packages

Every repository is composed of packages, a collection of related files and
a specification of the dependencies. These are specified by a file called
`BUILD` or `BUILD.bazel`. If both exist, Bazel prefers `BUILD.bazel`; the reason
why `BUILD` files are still accepted is that Bazel's ancestor, Blaze, used this
file name. However, it turned out to be a commonly used path segment, especially
on Windows, where file names are case-insensitive.

Packages are independent of each other: changes to the `BUILD` file of a package
cannot cause other packages to change. The addition or removal of `BUILD` files
_can _change other packages, since recursive globs stop at package boundaries
and thus the presence of a `BUILD` file stops the recursion.

The evaluation of a `BUILD` file is called "package loading". It's implemented
in the class `PackageFactory`, works by calling the Starlark interpreter and
requires knowledge of the set of available rule classes. The result of package
loading is a `Package` object. It's mostly a map from a string (the name of a
target) to the target itself.

A large chunk of complexity during package loading is globbing: Bazel does not
require every source file to be explicitly listed and instead can run globs
(such as `glob(["**/*.java"])`). Unlike the shell, it supports recursive globs that
descend into subdirectories (but not into subpackages). This requires access to
the file system and since that can be slow, we implement all sorts of tricks to
make it run in parallel and as efficiently as possible.

Globbing is implemented in the following classes:

*   `LegacyGlobber`, a fast and blissfully Skyframe-unaware globber
*   `SkyframeHybridGlobber`, a version that uses Skyframe and reverts back to
    the legacy globber in order to avoid "Skyframe restarts" (described below)

The `Package` class itself contains some members that are exclusively used to
parse the "external" package (related to external dependencies) and which do not
make sense for real packages. This is
a design flaw because objects describing regular packages should not contain
fields that describe something else. These include:

*   The repository mappings
*   The registered toolchains
*   The registered execution platforms

Ideally, there would be more separation between parsing the "external" package
from parsing regular packages so that `Package` does not need to cater for the
needs of both. This is unfortunately difficult to do because the two are
intertwined quite deeply.

### Labels, Targets, and Rules

Packages are composed of targets, which have the following types:

1.  **Files:** things that are either the input or the output of the build. In
    Bazel parlance, we call them _artifacts_ (discussed elsewhere). Not all
    files created during the build are targets; it's common for an output of
    Bazel not to have an associated label.
2.  **Rules:** these describe steps to derive its outputs from its inputs. They
    are generally associated with a programming language (such as `cc_library`,
    `java_library` or `py_library`), but there are some language-agnostic ones
    (such as `genrule` or `filegroup`)
3.  **Package groups:** discussed in the [Visibility](#visibility) section.

The name of a target is called a _Label_. The syntax of labels is
`@repo//pac/kage:name`, where `repo` is the name of the repository the Label is
in, `pac/kage` is the directory its `BUILD` file is in and `name` is the path of
the file (if the label refers to a source file) relative to the directory of the
package. When referring to a target on the command line, some parts of the label
can be omitted:

1.  If the repository is omitted, the label is taken to be in the main
    repository.
2.  If the package part is omitted (such as `name` or `:name`), the label is taken
    to be in the package of the current working directory (relative paths
    containing uplevel references (..) are not allowed)

A kind of a rule (such as "C++ library") is called a "rule class". Rule classes may
be implemented either in Starlark (the `rule()` function) or in Java (so called
"native rules", type `RuleClass`). In the long term, every language-specific
rule will be implemented in Starlark, but some legacy rule families (such as Java
or C++) are still in Java for the time being.

Starlark rule classes need to be imported at the beginning of `BUILD` files
using the `load()` statement, whereas Java rule classes are "innately" known by
Bazel, by virtue of being registered with the `ConfiguredRuleClassProvider`.

Rule classes contain information such as:

1.  Its attributes (such as `srcs`, `deps`): their types, default values,
    constraints, etc.
2.  The configuration transitions and aspects attached to each attribute, if any
3.  The implementation of the rule
4.  The transitive info providers the rule "usually" creates

**Terminology note:** In the codebase, we often use "Rule" to mean the target
created by a rule class. But in Starlark and in user-facing documentation,
"Rule" should be used exclusively to refer to the rule class itself; the target
is just a "target". Also note that despite `RuleClass` having "class" in its
name, there is no Java inheritance relationship between a rule class and targets
of that type.

## Skyframe

The evaluation framework underlying Bazel is called Skyframe. Its model is that
everything that needs to be built during a build is organized into a directed
acyclic graph with edges pointing from any pieces of data to its dependencies,
that is, other pieces of data that need to be known to construct it.

The nodes in the graph are called `SkyValue`s and their names are called
`SkyKey`s. Both are deeply immutable; only immutable objects should be
reachable from them. This invariant almost always holds, and in case it doesn't
(such as for the individual options classes `BuildOptions`, which is a member of
`BuildConfigurationValue` and its `SkyKey`) we try really hard not to change
them or to change them in only ways that are not observable from the outside.
From this it follows that everything that is computed within Skyframe (such as
configured targets) must also be immutable.

The most convenient way to observe the Skyframe graph is to run `bazel dump
--skyframe=deps`, which dumps the graph, one `SkyValue` per line. It's best
to do it for tiny builds, since it can get pretty large.

Skyframe lives in the `com.google.devtools.build.skyframe` package. The
similarly-named package `com.google.devtools.build.lib.skyframe` contains the
implementation of Bazel on top of Skyframe. More information about Skyframe is
available [here](/reference/skyframe).

To evaluate a given `SkyKey` into a `SkyValue`, Skyframe will invoke the
`SkyFunction` corresponding to the type of the key. During the function's
evaluation, it may request other dependencies from Skyframe by calling the
various overloads of `SkyFunction.Environment.getValue()`. This has the
side-effect of registering those dependencies into Skyframe's internal graph, so
that Skyframe will know to re-evaluate the function when any of its dependencies
change. In other words, Skyframe's caching and incremental computation work at
the granularity of `SkyFunction`s and `SkyValue`s.

Whenever a `SkyFunction` requests a dependency that is unavailable, `getValue()`
will return null. The function should then yield control back to Skyframe by
itself returning null. At some later point, Skyframe will evaluate the
unavailable dependency, then restart the function from the beginning — only this
time the `getValue()` call will succeed with a non-null result.

A consequence of this is that any computation performed inside the `SkyFunction`
prior to the restart must be repeated. But this does not include work done to
evaluate dependency `SkyValues`, which are cached. Therefore, we commonly work
around this issue by:

1.  Declaring dependencies in batches (by using `getValuesAndExceptions()`) to
    limit the number of restarts.
2.  Breaking up a `SkyValue` into separate pieces computed by different
    `SkyFunction`s, so that they can be computed and cached independently. This
    should be done strategically, since it has the potential to increases memory
    usage.
3.  Storing state between restarts, either using
    `SkyFunction.Environment.getState()`, or keeping an ad hoc static cache
    "behind the back of Skyframe". With complex SkyFunctions, state management
    between restarts can get tricky, so
    [`StateMachine`s](/contribute/statemachine-guide) were introduced for a
    structured approach to logical concurrency, including hooks to suspend and
    resume hierarchical computations within a `SkyFunction`. Example:
    [`DependencyResolver#computeDependencies`][statemachine_example]
    uses a `StateMachine` with `getState()` to compute the potentially huge set
    of direct dependencies of a configured target, which otherwise can result in
    expensive restarts.

[statemachine_example]: https://developers.google.com/devsite/reference/markdown/links#reference_links

Fundamentally, Bazel need these types of workarounds because hundreds of
thousands of in-flight Skyframe nodes is common, and Java's support of
lightweight threads [does not outperform][virtual_threads] the
`StateMachine` implementation as of 2023.

[virtual_threads]: /contribute/statemachine-guide#epilogue_eventually_removing_callbacks

## Starlark

Starlark is the domain-specific language people use to configure and extend
Bazel. It's conceived as a restricted subset of Python that has far fewer types,
more restrictions on control flow, and most importantly, strong immutability
guarantees to enable concurrent reads. It is not Turing-complete, which
discourages some (but not all) users from trying to accomplish general
programming tasks within the language.

Starlark is implemented in the `net.starlark.java` package.
It also has an independent Go implementation
[here](https://github.com/google/starlark-go){: .external}. The Java
implementation used in Bazel is currently an interpreter.

Starlark is used in several contexts, including:

1.  **`BUILD` files.** This is where new build targets are defined. Starlark
    code running in this context only has access to the contents of the `BUILD`
    file itself and `.bzl` files loaded by it.
2.  **The `MODULE.bazel` file.** This is where external dependencies are
    defined. Starlark code running in this context only has very limited access
    to a few predefined directives.
3.  **`.bzl` files.** This is where new build rules, repo rules, module
    extensions are defined. Starlark code here can define new functions and load
    from other `.bzl` files.

The dialects available for `BUILD` and `.bzl` files are slightly different
because they express different things. A list of differences is available
[here](/rules/language#differences-between-build-and-bzl-files).

More information about Starlark is available [here](/rules/language).

## The loading/analysis phase

The loading/analysis phase is where Bazel determines what actions are needed to
build a particular rule. Its basic unit is a "configured target", which is,
quite sensibly, a (target, configuration) pair.

It's called the "loading/analysis phase" because it can be split into two
distinct parts, which used to be serialized, but they can now overlap in time:

1.  Loading packages, that is, turning `BUILD` files into the `Package` objects
    that represent them
2.  Analyzing configured targets, that is, running the implementation of the
    rules to produce the action graph

Each configured target in the transitive closure of the configured targets
requested on the command line must be analyzed bottom-up; that is, leaf nodes
first, then up to the ones on the command line. The inputs to the analysis of
a single configured target are:

1.  **The configuration.** ("how" to build that rule; for example, the target
    platform but also things like command line options the user wants to be
    passed to the C++ compiler)
2.  **The direct dependencies.** Their transitive info providers are available
    to the rule being analyzed. They are called like that because they provide a
    "roll-up" of the information in the transitive closure of the configured
    target, such as all the .jar files on the classpath or all the .o files that
    need to be linked into a C++ binary)
3.  **The target itself**. This is the result of loading the package the target
    is in. For rules, this includes its attributes, which is usually what
    matters.
4.  **The implementation of the configured target.** For rules, this can either
    be in Starlark or in Java. All non-rule configured targets are implemented
    in Java.

The output of analyzing a configured target is:

1.  The transitive info providers that configured targets that depend on it can
    access
2.  The artifacts it can create and the actions that produce them.

The API offered to Java rules is `RuleContext`, which is the equivalent of the
`ctx` argument of Starlark rules. Its API is more powerful, but at the same
time, it's easier to do Bad Things™, for example to write code whose time or
space complexity is quadratic (or worse), to make the Bazel server crash with a
Java exception or to violate invariants (such as by inadvertently modifying an
`Options` instance or by making a configured target mutable)

The algorithm that determines the direct dependencies of a configured target
lives in `DependencyResolver.dependentNodeMap()`.

### Configurations

Configurations are the "how" of building a target: for what platform, with what
command line options, etc.

The same target can be built for multiple configurations in the same build. This
is useful, for example, when the same code is used for a tool that's run during
the build and for the target code and we are cross-compiling or when we are
building a fat Android app (one that contains native code for multiple CPU
architectures)

Conceptually, the configuration is a `BuildOptions` instance. However, in
practice, `BuildOptions` is wrapped by `BuildConfiguration` that provides
additional sundry pieces of functionality. It propagates from the top of the
dependency graph to the bottom. If it changes, the build needs to be
re-analyzed.

This results in anomalies like having to re-analyze the whole build if, for
example, the number of requested test runs changes, even though that only
affects test targets (we have plans to "trim" configurations so that this is
not the case, but it's not ready yet).

When a rule implementation needs part of the configuration, it needs to declare
it in its definition using `RuleClass.Builder.requiresConfigurationFragments()`
. This is both to avoid mistakes (such as Python rules using the Java fragment) and
to facilitate configuration trimming so that such as if Python options change, C++
targets don't need to be re-analyzed.

The configuration of a rule is not necessarily the same as that of its "parent"
rule. The process of changing the configuration in a dependency edge is called a
"configuration transition". It can happen in two places:

1.  On a dependency edge. These transitions are specified in
    `Attribute.Builder.cfg()` and are functions from a `Rule` (where the
    transition happens) and a `BuildOptions` (the original configuration) to one
    or more `BuildOptions` (the output configuration).
2.  On any incoming edge to a configured target. These are specified in
    `RuleClass.Builder.cfg()`.

The relevant classes are `TransitionFactory` and `ConfigurationTransition`.

Configuration transitions are used, for example:

1.  To declare that a particular dependency is used during the build and it
    should thus be built in the execution architecture
2.  To declare that a particular dependency must be built for multiple
    architectures (such as for native code in fat Android APKs)

If a configuration transition results in multiple configurations, it's called a
_split transition._

Configuration transitions can also be implemented in Starlark (documentation
[here](/extending/config))

### Transitive info providers

Transitive info providers are a way (and the _only _way) for configured targets
to learn things about other configured targets that they depend on, and the only
way to tell things about themselves to other configured targets that depend on
them. The reason why "transitive" is in their name is that this is usually some
sort of roll-up of the transitive closure of a configured target.

There is generally a 1:1 correspondence between Java transitive info providers
and Starlark ones (the exception is `DefaultInfo` which is an amalgamation of
`FileProvider`, `FilesToRunProvider` and `RunfilesProvider` because that API was
deemed to be more Starlark-ish than a direct transliteration of the Java one).
Their key is one of the following things:

1.  A Java Class object. This is only available for providers that are not
    accessible from Starlark. These providers are a subclass of
    `TransitiveInfoProvider`.
2.  A string. This is legacy and heavily discouraged since it's susceptible to
    name clashes. Such transitive info providers are direct subclasses of
    `build.lib.packages.Info` .
3.  A provider symbol. This can be created from Starlark using the `provider()`
    function and is the recommended way to create new providers. The symbol is
    represented by a `Provider.Key` instance in Java.

New providers implemented in Java should be implemented using `BuiltinProvider`.
`NativeProvider` is deprecated (we haven't had time to remove it yet) and
`TransitiveInfoProvider` subclasses cannot be accessed from Starlark.

### Configured targets

Configured targets are implemented as `RuleConfiguredTargetFactory`. There is a
subclass for each rule class implemented in Java. Starlark configured targets
are created through `StarlarkRuleConfiguredTargetUtil.buildRule()` .

Configured target factories should use `RuleConfiguredTargetBuilder` to
construct their return value. It consists of the following things:

1.  Their `filesToBuild`, the hazy concept of "the set of files this rule
    represents." These are the files that get built when the configured target
    is on the command line or in the srcs of a genrule.
2.  Their runfiles, regular and data.
3.  Their output groups. These are various "other sets of files" the rule can
    build. They can be accessed using the output\_group attribute of the
    filegroup rule in BUILD and using the `OutputGroupInfo` provider in Java.

### Runfiles

Some binaries need data files to run. A prominent example is tests that need
input files. This is represented in Bazel by the concept of "runfiles". A
"runfiles tree" is a directory tree of the data files for a particular binary.
It is created in the file system as a symlink tree with individual symlinks
pointing to the files in the source or output trees.

A set of runfiles is represented as a `Runfiles` instance. It is conceptually a
map from the path of a file in the runfiles tree to the `Artifact` instance that
represents it. It's a little more complicated than a single `Map` for two
reasons:

*   Most of the time, the runfiles path of a file is the same as its execpath.
    We use this to save some RAM.
*   There are various legacy kinds of entries in runfiles trees, which also need
    to be represented.

Runfiles are collected using `RunfilesProvider`: an instance of this class
represents the runfiles a configured target (such as a library) and its transitive
closure needs and they are gathered like a nested set (in fact, they are
implemented using nested sets under the cover): each target unions the runfiles
of its dependencies, adds some of its own, then sends the resulting set upwards
in the dependency graph. A `RunfilesProvider` instance contains two `Runfiles`
instances, one for when the rule is depended on through the "data" attribute and
one for every other kind of incoming dependency. This is because a target
sometimes presents different runfiles when depended on through a data attribute
than otherwise. This is undesired legacy behavior that we haven't gotten around
removing yet.

Runfiles of binaries are represented as an instance of `RunfilesSupport`. This
is different from `Runfiles` because `RunfilesSupport` has the capability of
actually being built (unlike `Runfiles`, which is just a mapping). This
necessitates the following additional components:

*   **The input runfiles manifest.** This is a serialized description of the
    runfiles tree. It is used as a proxy for the contents of the runfiles tree
    and Bazel assumes that the runfiles tree changes if and only if the contents
    of the manifest change.
*   **The output runfiles manifest.** This is used by runtime libraries that
    handle runfiles trees, notably on Windows, which sometimes doesn't support
    symbolic links.
*   **The runfiles middleman.** In order for a runfiles tree to exist, one needs
    to build the symlink tree and the artifact the symlinks point to. In order
    to decrease the number of dependency edges, the runfiles middleman can be
    used to represent all these.
*   **Command line arguments** for running the binary whose runfiles the
    `RunfilesSupport` object represents.

### Aspects

Aspects are a way to "propagate computation down the dependency graph". They are
described for users of Bazel
[here](/extending/aspects). A good
motivating example is protocol buffers: a `proto_library` rule should not know
about any particular language, but building the implementation of a protocol
buffer message (the "basic unit" of protocol buffers) in any programming
language should be coupled to the `proto_library` rule so that if two targets in
the same language depend on the same protocol buffer, it gets built only once.

Just like configured targets, they are represented in Skyframe as a `SkyValue`
and the way they are constructed is very similar to how configured targets are
built: they have a factory class called `ConfiguredAspectFactory` that has
access to a `RuleContext`, but unlike configured target factories, it also knows
about the configured target it is attached to and its providers.

The set of aspects propagated down the dependency graph is specified for each
attribute using the `Attribute.Builder.aspects()` function. There are a few
confusingly-named classes that participate in the process:

1.  `AspectClass` is the implementation of the aspect. It can be either in Java
    (in which case it's a subclass) or in Starlark (in which case it's an
    instance of `StarlarkAspectClass`). It's analogous to
    `RuleConfiguredTargetFactory`.
2.  `AspectDefinition` is the definition of the aspect; it includes the
    providers it requires, the providers it provides and contains a reference to
    its implementation, such as the appropriate `AspectClass` instance. It's
    analogous to `RuleClass`.
3.  `AspectParameters` is a way to parametrize an aspect that is propagated down
    the dependency graph. It's currently a string to string map. A good example
    of why it's useful is protocol buffers: if a language has multiple APIs, the
    information as to which API the protocol buffers should be built for should
    be propagated down the dependency graph.
4.  `Aspect` represents all the data that's needed to compute an aspect that
    propagates down the dependency graph. It consists of the aspect class, its
    definition and its parameters.
5.  `RuleAspect` is the function that determines which aspects a particular rule
    should propagate. It's a `Rule` -> `Aspect` function.

A somewhat unexpected complication is that aspects can attach to other aspects;
for example, an aspect collecting the classpath for a Java IDE will probably
want to know about all the .jar files on the classpath, but some of them are
protocol buffers. In that case, the IDE aspect will want to attach to the
(`proto_library` rule + Java proto aspect) pair.

The complexity of aspects on aspects is captured in the class
`AspectCollection`.

### Platforms and toolchains

Bazel supports multi-platform builds, that is, builds where there may be
multiple architectures where build actions run and multiple architectures for
which code is built. These architectures are referred to as _platforms_ in Bazel
parlance (full documentation
[here](/extending/platforms))

A platform is described by a key-value mapping from _constraint settings_ (such as
the concept of "CPU architecture") to _constraint values_ (such as a particular CPU
like x86\_64). We have a "dictionary" of the most commonly used constraint
settings and values in the `@platforms` repository.

The concept of _toolchain_ comes from the fact that depending on what platforms
the build is running on and what platforms are targeted, one may need to use
different compilers; for example, a particular C++ toolchain may run on a
specific OS and be able to target some other OSes. Bazel must determine the C++
compiler that is used based on the set execution and target platform
(documentation for toolchains
[here](/extending/toolchains)).

In order to do this, toolchains are annotated with the set of execution and
target platform constraints they support. In order to do this, the definition of
a toolchain are split into two parts:

1.  A `toolchain()` rule that describes the set of execution and target
    constraints a toolchain supports and tells what kind (such as C++ or Java) of
    toolchain it is (the latter is represented by the `toolchain_type()` rule)
2.  A language-specific rule that describes the actual toolchain (such as
    `cc_toolchain()`)

This is done in this way because we need to know the constraints for every
toolchain in order to do toolchain resolution and language-specific
`*_toolchain()` rules contain much more information than that, so they take more
time to load.

Execution platforms are specified in one of the following ways:

1.  In the MODULE.bazel file using the `register_execution_platforms()` function
2.  On the command line using the --extra\_execution\_platforms command line
    option

The set of available execution platforms is computed in
`RegisteredExecutionPlatformsFunction` .

The target platform for a configured target is determined by
`PlatformOptions.computeTargetPlatform()` . It's a list of platforms because we
eventually want to support multiple target platforms, but it's not implemented
yet.

The set of toolchains to be used for a configured target is determined by
`ToolchainResolutionFunction`. It is a function of:

*   The set of registered toolchains (in the MODULE.bazel file and the
    configuration)
*   The desired execution and target platforms (in the configuration)
*   The set of toolchain types that are required by the configured target (in
    `UnloadedToolchainContextKey)`
*   The set of execution platform constraints of the configured target (the
    `exec_compatible_with` attribute) and the configuration
    (`--experimental_add_exec_constraints_to_targets`), in
    `UnloadedToolchainContextKey`

Its result is an `UnloadedToolchainContext`, which is essentially a map from
toolchain type (represented as a `ToolchainTypeInfo` instance) to the label of
the selected toolchain. It's called "unloaded" because it does not contain the
toolchains themselves, only their labels.

Then the toolchains are actually loaded using `ResolvedToolchainContext.load()`
and used by the implementation of the configured target that requested them.

We also have a legacy system that relies on there being one single "host"
configuration and target configurations being represented by various
configuration flags, such as `--cpu` . We are gradually transitioning to the above
system. In order to handle cases where people rely on the legacy configuration
values, we have implemented
[platform mappings](https://docs.google.com/document/d/1Vg_tPgiZbSrvXcJ403vZVAGlsWhH9BUDrAxMOYnO0Ls){: .external}
to translate between the legacy flags and the new-style platform constraints.
Their code is in `PlatformMappingFunction` and uses a non-Starlark "little
language".

### Constraints

Sometimes one wants to designate a target as being compatible with only a few
platforms. Bazel has (unfortunately) multiple mechanisms to achieve this end:

*   Rule-specific constraints
*   `environment_group()` / `environment()`
*   Platform constraints

Rule-specific constraints are mostly used within Google for Java rules; they are
on their way out and they are not available in Bazel, but the source code may
contain references to it. The attribute that governs this is called
`constraints=` .

#### environment_group() and environment()

These rules are a legacy mechanism and are not widely used.

All build rules can declare which "environments" they can be built for, where an
"environment" is an instance of the `environment()` rule.

There are various ways supported environments can be specified for a rule:

1.  Through the `restricted_to=` attribute. This is the most direct form of
    specification; it declares the exact set of environments the rule supports.
2.  Through the `compatible_with=` attribute. This declares environments a rule
    supports in addition to "standard" environments that are supported by
    default.
3.  Through the package-level attributes `default_restricted_to=` and
    `default_compatible_with=`.
4.  Through default specifications in `environment_group()` rules. Every
    environment belongs to a group of thematically related peers (such as "CPU
    architectures", "JDK versions" or "mobile operating systems"). The
    definition of an environment group includes which of these environments
    should be supported by "default" if not otherwise specified by the
    `restricted_to=` / `environment()` attributes. A rule with no such
    attributes inherits all defaults.
5.  Through a rule class default. This overrides global defaults for all
    instances of the given rule class. This can be used, for example, to make
    all `*_test` rules testable without each instance having to explicitly
    declare this capability.

`environment()` is implemented as a regular rule whereas `environment_group()`
is both a subclass of `Target` but not `Rule` (`EnvironmentGroup`) and a
function that is available by default from Starlark
(`StarlarkLibrary.environmentGroup()`) which eventually creates an eponymous
target. This is to avoid a cyclic dependency that would arise because each
environment needs to declare the environment group it belongs to and each
environment group needs to declare its default environments.

A build can be restricted to a certain environment with the
`--target_environment` command line option.

The implementation of the constraint check is in
`RuleContextConstraintSemantics` and `TopLevelConstraintSemantics`.

#### Platform constraints

The current "official" way to describe what platforms a target is compatible
with is by using the same constraints used to describe toolchains and platforms.
It was implemented in pull request
[#10945](https://github.com/bazelbuild/bazel/pull/10945){: .external}.

### Visibility

If you work on a large codebase with a lot of developers (like at Google), you
want to take care to prevent everyone else from arbitrarily depending on your
code. Otherwise, as per [Hyrum's law](https://www.hyrumslaw.com/){: .external},
people _will_ come to rely on behaviors that you considered to be implementation
details.

Bazel supports this by the mechanism called _visibility_: you can limit which
targets can depend on a particular target using the
[visibility](/reference/be/common-definitions#common-attributes) attribute. This
attribute is a little special because, although it holds a list of labels, these
labels may encode a pattern over package names rather than a pointer to any
particular target. (Yes, this is a design flaw.)

This is implemented in the following places:

*   The `RuleVisibility` interface represents a visibility declaration. It can
    be either a constant (fully public or fully private) or a list of labels.
*   Labels can refer to either package groups (predefined list of packages), to
    packages directly (`//pkg:__pkg__`) or subtrees of packages
    (`//pkg:__subpackages__`). This is different from the command line syntax,
    which uses `//pkg:*` or `//pkg/...`.
*   Package groups are implemented as their own target (`PackageGroup`) and
    configured target (`PackageGroupConfiguredTarget`). We could probably
    replace these with simple rules if we wanted to. Their logic is implemented
    with the help of: `PackageSpecification`, which corresponds to a
    single pattern like `//pkg/...`; `PackageGroupContents`, which corresponds
    to a single `package_group`'s `packages` attribute; and
    `PackageSpecificationProvider`, which aggregates over a `package_group` and
    its transitive `includes`.
*   The conversion from visibility label lists to dependencies is done in
    `DependencyResolver.visitTargetVisibility` and a few other miscellaneous
    places.
*   The actual check is done in
    `CommonPrerequisiteValidator.validateDirectPrerequisiteVisibility()`

### Nested sets

Oftentimes, a configured target aggregates a set of files from its dependencies,
adds its own, and wraps the aggregate set into a transitive info provider so
that configured targets that depend on it can do the same. Examples:

*   The C++ header files used for a build
*   The object files that represent the transitive closure of a `cc_library`
*   The set of .jar files that need to be on the classpath for a Java rule to
    compile or run
*   The set of Python files in the transitive closure of a Python rule

If we did this the naive way by using, for example, `List` or `Set`, we'd end up with
quadratic memory usage: if there is a chain of N rules and each rule adds a
file, we'd have 1+2+...+N collection members.

In order to get around this problem, we came up with the concept of a
`NestedSet`. It's a data structure that is composed of other `NestedSet`
instances and some members of its own, thereby forming a directed acyclic graph
of sets. They are immutable and their members can be iterated over. We define
multiple iteration order (`NestedSet.Order`): preorder, postorder, topological
(a node always comes after its ancestors) and "don't care, but it should be the
same each time".

The same data structure is called `depset` in Starlark.

### Artifacts and Actions

The actual build consists of a set of commands that need to be run to produce
the output the user wants. The commands are represented as instances of the
class `Action` and the files are represented as instances of the class
`Artifact`. They are arranged in a bipartite, directed, acyclic graph called the
"action graph".

Artifacts come in two kinds: source artifacts (ones that are available
before Bazel starts executing) and derived artifacts (ones that need to be
built). Derived artifacts can themselves be multiple kinds:

1.  **Regular artifacts.** These are checked for up-to-dateness by computing
    their checksum, with mtime as a shortcut; we don't checksum the file if its
    ctime hasn't changed.
2.  **Unresolved symlink artifacts.** These are checked for up-to-dateness by
    calling readlink(). Unlike regular artifacts, these can be dangling
    symlinks. Usually used in cases where one then packs up some files into an
    archive of some sort.
3.  **Tree artifacts.** These are not single files, but directory trees. They
    are checked for up-to-dateness by checking the set of files in it and their
    contents. They are represented as a `TreeArtifact`.
4.  **Constant metadata artifacts.** Changes to these artifacts don't trigger a
    rebuild. This is used exclusively for build stamp information: we don't want
    to do a rebuild just because the current time changed.

There is no fundamental reason why source artifacts cannot be tree artifacts or
unresolved symlink artifacts, it's just that we haven't implemented it yet (we
should, though -- referencing a source directory in a `BUILD` file is one of the
few known long-standing incorrectness issues with Bazel; we have an
implementation that kind of works which is enabled by the
`BAZEL_TRACK_SOURCE_DIRECTORIES=1` JVM property)

A notable kind of `Artifact` are middlemen. They are indicated by `Artifact`
instances that are the outputs of `MiddlemanAction`. They are used for one
special case:

*   Runfiles middlemen are used to ensure the presence of a runfiles tree so
    that one does not separately need to depend on the output manifest and every
    single artifact referenced by the runfiles tree.

Actions are best understood as a command that needs to be run, the environment
it needs and the set of outputs it produces. The following things are the main
components of the description of an action:

*   The command line that needs to be run
*   The input artifacts it needs
*   The environment variables that need to be set
*   Annotations that describe the environment (such as platform) it needs to run in
    \

There are also a few other special cases, like writing a file whose content is
known to Bazel. They are a subclass of `AbstractAction`. Most of the actions are
a `SpawnAction` or a `StarlarkAction` (the same, they should arguably not be
separate classes), although Java and C++ have their own action types
(`JavaCompileAction`, `CppCompileAction` and `CppLinkAction`).

We eventually want to move everything to `SpawnAction`; `JavaCompileAction` is
pretty close, but C++ is a bit of a special-case due to .d file parsing and
include scanning.

The action graph is mostly "embedded" into the Skyframe graph: conceptually, the
execution of an action is represented as an invocation of
`ActionExecutionFunction`. The mapping from an action graph dependency edge to a
Skyframe dependency edge is described in
`ActionExecutionFunction.getInputDeps()` and `Artifact.key()` and has a few
optimizations in order to keep the number of Skyframe edges low:

*   Derived artifacts do not have their own `SkyValue`s. Instead,
    `Artifact.getGeneratingActionKey()` is used to find out the key for the
    action that generates it
*   Nested sets have their own Skyframe key.

### Shared actions

Some actions are generated by multiple configured targets; Starlark rules are
more limited since they are only allowed to put their derived actions into a
directory determined by their configuration and their package (but even so,
rules in the same package can conflict), but rules implemented in Java can put
derived artifacts anywhere.

This is considered to be a misfeature, but getting rid of it is really hard
because it produces significant savings in execution time when, for example, a
source file needs to be processed somehow and that file is referenced by
multiple rules (handwave-handwave). This comes at the cost of some RAM: each
instance of a shared action needs to be stored in memory separately.

If two actions generate the same output file, they must be exactly the same:
have the same inputs, the same outputs and run the same command line. This
equivalence relation is implemented in `Actions.canBeShared()` and it is
verified between the analysis and execution phases by looking at every Action.
This is implemented in `SkyframeActionExecutor.findAndStoreArtifactConflicts()`
and is one of the few places in Bazel that requires a "global" view of the
build.

## The execution phase

This is when Bazel actually starts running build actions, such as commands that
produce outputs.

The first thing Bazel does after the analysis phase is to determine what
Artifacts need to be built. The logic for this is encoded in
`TopLevelArtifactHelper`; roughly speaking, it's the `filesToBuild` of the
configured targets on the command line and the contents of a special output
group for the explicit purpose of expressing "if this target is on the command
line, build these artifacts".

The next step is creating the execution root. Since Bazel has the option to read
source packages from different locations in the file system (`--package_path`),
it needs to provide locally executed actions with a full source tree. This is
handled by the class `SymlinkForest` and works by taking note of every target
used in the analysis phase and building up a single directory tree that symlinks
every package with a used target from its actual location. An alternative would
be to pass the correct paths to commands (taking `--package_path` into account).
This is undesirable because:

*   It changes action command lines when a package is moved from a package path
    entry to another (used to be a common occurrence)
*   It results in different command lines if an action is run remotely than if
    it's run locally
*   It requires a command line transformation specific to the tool in use
    (consider the difference between such as Java classpaths and C++ include paths)
*   Changing the command line of an action invalidates its action cache entry
*   `--package_path` is slowly and steadily being deprecated

Then, Bazel starts traversing the action graph (the bipartite, directed graph
composed of actions and their input and output artifacts) and running actions.
The execution of each action is represented by an instance of the `SkyValue`
class `ActionExecutionValue`.

Since running an action is expensive, we have a few layers of caching that can
be hit behind Skyframe:

*   `ActionExecutionFunction.stateMap` contains data to make Skyframe restarts
    of `ActionExecutionFunction` cheap
*   The local action cache contains data about the state of the file system
*   Remote execution systems usually also contain their own cache

### The local action cache

This cache is another layer that sits behind Skyframe; even if an action is
re-executed in Skyframe, it can still be a hit in the local action cache. It
represents the state of the local file system and it's serialized to disk which
means that when one starts up a new Bazel server, one can get local action cache
hits even though the Skyframe graph is empty.

This cache is checked for hits using the method
`ActionCacheChecker.getTokenIfNeedToExecute()` .

Contrary to its name, it's a map from the path of a derived artifact to the
action that emitted it. The action is described as:

1.  The set of its input and output files and their checksum
2.  Its "action key", which is usually the command line that was executed, but
    in general, represents everything that's not captured by the checksum of the
    input files (such as for `FileWriteAction`, it's the checksum of the data
    that's written)

There is also a highly experimental "top-down action cache" that is still under
development, which uses transitive hashes to avoid going to the cache as many
times.

### Input discovery and input pruning

Some actions are more complicated than just having a set of inputs. Changes to
the set of inputs of an action come in two forms:

*   An action may discover new inputs before its execution or decide that some
    of its inputs are not actually necessary. The canonical example is C++,
    where it's better to make an educated guess about what header files a C++
    file uses from its transitive closure so that we don't heed to send every
    file to remote executors; therefore, we have an option not to register every
    header file as an "input", but scan the source file for transitively
    included headers and only mark those header files as inputs that are
    mentioned in `#include` statements (we overestimate so that we don't need to
    implement a full C preprocessor) This option is currently hard-wired to
    "false" in Bazel and is only used at Google.
*   An action may realize that some files were not used during its execution. In
    C++, this is called ".d files": the compiler tells which header files were
    used after the fact, and in order to avoid the embarrassment of having worse
    incrementality than Make, Bazel makes use of this fact. This offers a better
    estimate than the include scanner because it relies on the compiler.

These are implemented using methods on Action:

1.  `Action.discoverInputs()` is called. It should return a nested set of
    Artifacts that are determined to be required. These must be source artifacts
    so that there are no dependency edges in the action graph that don't have an
    equivalent in the configured target graph.
2.  The action is executed by calling `Action.execute()`.
3.  At the end of `Action.execute()`, the action can call
    `Action.updateInputs()` to tell Bazel that not all of its inputs were
    needed. This can result in incorrect incremental builds if a used input is
    reported as unused.

When an action cache returns a hit on a fresh Action instance (such as created
after a server restart), Bazel calls `updateInputs()` itself so that the set of
inputs reflects the result of input discovery and pruning done before.

Starlark actions can make use of the facility to declare some inputs as unused
using the `unused_inputs_list=` argument of
`ctx.actions.run()`.

### Various ways to run actions: Strategies/ActionContexts

Some actions can be run in different ways. For example, a command line can be
executed locally, locally but in various kinds of sandboxes, or remotely. The
concept that embodies this is called an `ActionContext` (or `Strategy`, since we
successfully went only halfway with a rename...)

The life cycle of an action context is as follows:

1.  When the execution phase is started, `BlazeModule` instances are asked what
    action contexts they have. This happens in the constructor of
    `ExecutionTool`. Action context types are identified by a Java `Class`
    instance that refers to a sub-interface of `ActionContext` and which
    interface the action context must implement.
2.  The appropriate action context is selected from the available ones and is
    forwarded to `ActionExecutionContext` and `BlazeExecutor` .
3.  Actions request contexts using `ActionExecutionContext.getContext()` and
    `BlazeExecutor.getStrategy()` (there should really be only one way to do
    it…)

Strategies are free to call other strategies to do their jobs; this is used, for
example, in the dynamic strategy that starts actions both locally and remotely,
then uses whichever finishes first.

One notable strategy is the one that implements persistent worker processes
(`WorkerSpawnStrategy`). The idea is that some tools have a long startup time
and should therefore be reused between actions instead of starting one anew for
every action (This does represent a potential correctness issue, since Bazel
relies on the promise of the worker process that it doesn't carry observable
state between individual requests)

If the tool changes, the worker process needs to be restarted. Whether a worker
can be reused is determined by computing a checksum for the tool used using
`WorkerFilesHash`. It relies on knowing which inputs of the action represent
part of the tool and which represent inputs; this is determined by the creator
of the Action: `Spawn.getToolFiles()` and the runfiles of the `Spawn` are
counted as parts of the tool.

More information about strategies (or action contexts!):

*   Information about various strategies for running actions is available
    [here](https://jmmv.dev/2019/12/bazel-strategies.html).
*   Information about the dynamic strategy, one where we run an action both
    locally and remotely to see whichever finishes first is available
    [here](https://jmmv.dev/series.html#Bazel%20dynamic%20execution).
*   Information about the intricacies of executing actions locally is available
    [here](https://jmmv.dev/2019/11/bazel-process-wrapper.html).

### The local resource manager

Bazel _can_ run many actions in parallel. The number of local actions that
_should_ be run in parallel differs from action to action: the more resources an
action requires, the less instances should be running at the same time to avoid
overloading the local machine.

This is implemented in the class `ResourceManager`: each action has to be
annotated with an estimate of the local resources it requires in the form of a
`ResourceSet` instance (CPU and RAM). Then when action contexts do something
that requires local resources, they call `ResourceManager.acquireResources()`
and are blocked until the required resources are available.

A more detailed description of local resource management is available
[here](https://jmmv.dev/2019/12/bazel-local-resources.html).

### The structure of the output directory

Each action requires a separate place in the output directory where it places
its outputs. The location of derived artifacts is usually as follows:

```
$EXECROOT/bazel-out/<configuration>/bin/<package>/<artifact name>
```

How is the name of the directory that is associated with a particular
configuration determined? There are two conflicting desirable properties:

1.  If two configurations can occur in the same build, they should have
    different directories so that both can have their own version of the same
    action; otherwise, if the two configurations disagree about such as the command
    line of an action producing the same output file, Bazel doesn't know which
    action to choose (an "action conflict")
2.  If two configurations represent "roughly" the same thing, they should have
    the same name so that actions executed in one can be reused for the other if
    the command lines match: for example, changes to the command line options to
    the Java compiler should not result in C++ compile actions being re-run.

So far, we have not come up with a principled way of solving this problem, which
has similarities to the problem of configuration trimming. A longer discussion
of options is available
[here](https://docs.google.com/document/d/1fZI7wHoaS-vJvZy9SBxaHPitIzXE_nL9v4sS4mErrG4/edit){: .external}.
The main problematic areas are Starlark rules (whose authors usually aren't
intimately familiar with Bazel) and aspects, which add another dimension to the
space of things that can produce the "same" output file.

The current approach is that the path segment for the configuration is
`<CPU>-<compilation mode>` with various suffixes added so that configuration
transitions implemented in Java don't result in action conflicts. In addition, a
checksum of the set of Starlark configuration transitions is added so that users
can't cause action conflicts. It is far from perfect. This is implemented in
`OutputDirectories.buildMnemonic()` and relies on each configuration fragment
adding its own part to the name of the output directory.

## Tests

Bazel has rich support for running tests. It supports:

*   Running tests remotely (if a remote execution backend is available)
*   Running tests multiple times in parallel (for deflaking or gathering timing
    data)
*   Sharding tests (splitting test cases in same test over multiple processes
    for speed)
*   Re-running flaky tests
*   Grouping tests into test suites

Tests are regular configured targets that have a TestProvider, which describes
how the test should be run:

*   The artifacts whose building result in the test being run. This is a "cache
    status" file that contains a serialized `TestResultData` message
*   The number of times the test should be run
*   The number of shards the test should be split into
*   Some parameters about how the test should be run (such as the test timeout)

### Determining which tests to run

Determining which tests are run is an elaborate process.

First, during target pattern parsing, test suites are recursively expanded. The
expansion is implemented in `TestsForTargetPatternFunction`. A somewhat
surprising wrinkle is that if a test suite declares no tests, it refers to
_every_ test in its package. This is implemented in `Package.beforeBuild()` by
adding an implicit attribute called `$implicit_tests` to test suite rules.

Then, tests are filtered for size, tags, timeout and language according to the
command line options. This is implemented in `TestFilter` and is called from
`TargetPatternPhaseFunction.determineTests()` during target parsing and the
result is put into `TargetPatternPhaseValue.getTestsToRunLabels()`. The reason
why rule attributes which can be filtered for are not configurable is that this
happens before the analysis phase, therefore, the configuration is not
available.

This is then processed further in `BuildView.createResult()`: targets whose
analysis failed are filtered out and tests are split into exclusive and
non-exclusive tests. It's then put into `AnalysisResult`, which is how
`ExecutionTool` knows which tests to run.

In order to lend some transparency to this elaborate process, the `tests()`
query operator (implemented in `TestsFunction`) is available to tell which tests
are run when a particular target is specified on the command line. It's
unfortunately a reimplementation, so it probably deviates from the above in
multiple subtle ways.

### Running tests

The way the tests are run is by requesting cache status artifacts. This then
results in the execution of a `TestRunnerAction`, which eventually calls the
`TestActionContext` chosen by the `--test_strategy` command line option that
runs the test in the requested way.

Tests are run according to an elaborate protocol that uses environment variables
to tell tests what's expected from them. A detailed description of what Bazel
expects from tests and what tests can expect from Bazel is available
[here](/reference/test-encyclopedia). At the
simplest, an exit code of 0 means success, anything else means failure.

In addition to the cache status file, each test process emits a number of other
files. They are put in the "test log directory" which is the subdirectory called
`testlogs` of the output directory of the target configuration:

*   `test.xml`, a JUnit-style XML file detailing the individual test cases in
    the test shard
*   `test.log`, the console output of the test. stdout and stderr are not
    separated.
*   `test.outputs`, the "undeclared outputs directory"; this is used by tests
    that want to output files in addition to what they print to the terminal.

There are two things that can happen during test execution that cannot during
building regular targets: exclusive test execution and output streaming.

Some tests need to be executed in exclusive mode, for example not in parallel with
other tests. This can be elicited either by adding `tags=["exclusive"]` to the
test rule or running the test with `--test_strategy=exclusive` . Each exclusive
test is run by a separate Skyframe invocation requesting the execution of the
test after the "main" build. This is implemented in
`SkyframeExecutor.runExclusiveTest()`.

Unlike regular actions, whose terminal output is dumped when the action
finishes, the user can request the output of tests to be streamed so that they
get informed about the progress of a long-running test. This is specified by the
`--test_output=streamed` command line option and implies exclusive test
execution so that outputs of different tests are not interspersed.

This is implemented in the aptly-named `StreamedTestOutput` class and works by
polling changes to the `test.log` file of the test in question and dumping new
bytes to the terminal where Bazel rules.

Results of the executed tests are available on the event bus by observing
various events (such as `TestAttempt`, `TestResult` or `TestingCompleteEvent`).
They are dumped to the Build Event Protocol and they are emitted to the console
by `AggregatingTestListener`.

### Coverage collection

Coverage is reported by the tests in LCOV format in the files
`bazel-testlogs/$PACKAGE/$TARGET/coverage.dat` .

To collect coverage, each test execution is wrapped in a script called
`collect_coverage.sh` .

This script sets up the environment of the test to enable coverage collection
and determine where the coverage files are written by the coverage runtime(s).
It then runs the test. A test may itself run multiple subprocesses and consist
of parts written in multiple different programming languages (with separate
coverage collection runtimes). The wrapper script is responsible for converting
the resulting files to LCOV format if necessary, and merges them into a single
file.

The interposition of `collect_coverage.sh` is done by the test strategies and
requires `collect_coverage.sh` to be on the inputs of the test. This is
accomplished by the implicit attribute `:coverage_support` which is resolved to
the value of the configuration flag `--coverage_support` (see
`TestConfiguration.TestOptions.coverageSupport`)

Some languages do offline instrumentation, meaning that the coverage
instrumentation is added at compile time (such as C++) and others do online
instrumentation, meaning that coverage instrumentation is added at execution
time.

Another core concept is _baseline coverage_. This is the coverage of a library,
binary, or test if no code in it was run. The problem it solves is that if you
want to compute the test coverage for a binary, it is not enough to merge the
coverage of all of the tests because there may be code in the binary that is not
linked into any test. Therefore, what we do is to emit a coverage file for every
binary which contains only the files we collect coverage for with no covered
lines. The baseline coverage file for a target is at
`bazel-testlogs/$PACKAGE/$TARGET/baseline_coverage.dat` . It is also generated
for binaries and libraries in addition to tests if you pass the
`--nobuild_tests_only` flag to Bazel.

Baseline coverage is currently broken.

We track two groups of files for coverage collection for each rule: the set of
instrumented files and the set of instrumentation metadata files.

The set of instrumented files is just that, a set of files to instrument. For
online coverage runtimes, this can be used at runtime to decide which files to
instrument. It is also used to implement baseline coverage.

The set of instrumentation metadata files is the set of extra files a test needs
to generate the LCOV files Bazel requires from it. In practice, this consists of
runtime-specific files; for example, gcc emits .gcno files during compilation.
These are added to the set of inputs of test actions if coverage mode is
enabled.

Whether or not coverage is being collected is stored in the
`BuildConfiguration`. This is handy because it is an easy way to change the test
action and the action graph depending on this bit, but it also means that if
this bit is flipped, all targets need to be re-analyzed (some languages, such as
C++ require different compiler options to emit code that can collect coverage,
which mitigates this issue somewhat, since then a re-analysis is needed anyway).

The coverage support files are depended on through labels in an implicit
dependency so that they can be overridden by the invocation policy, which allows
them to differ between the different versions of Bazel. Ideally, these
differences would be removed, and we standardized on one of them.

We also generate a "coverage report" which merges the coverage collected for
every test in a Bazel invocation. This is handled by
`CoverageReportActionFactory` and is called from `BuildView.createResult()` . It
gets access to the tools it needs by looking at the `:coverage_report_generator`
attribute of the first test that is executed.

## The query engine

Bazel has a
[little language](/query/guide)
used to ask it various things about various graphs. The following query kinds
are provided:

*   `bazel query` is used to investigate the target graph
*   `bazel cquery` is used to investigate the configured target graph
*   `bazel aquery` is used to investigate the action graph

Each of these is implemented by subclassing `AbstractBlazeQueryEnvironment`.
Additional additional query functions can be done by subclassing `QueryFunction`
. In order to allow streaming query results, instead of collecting them to some
data structure, a `query2.engine.Callback` is passed to `QueryFunction`, which
calls it for results it wants to return.

The result of a query can be emitted in various ways: labels, labels and rule
classes, XML, protobuf and so on. These are implemented as subclasses of
`OutputFormatter`.

A subtle requirement of some query output formats (proto, definitely) is that
Bazel needs to emit _all _the information that package loading provides so that
one can diff the output and determine whether a particular target has changed.
As a consequence, attribute values need to be serializable, which is why there
are only so few attribute types without any attributes having complex Starlark
values. The usual workaround is to use a label, and attach the complex
information to the rule with that label. It's not a very satisfying workaround
and it would be very nice to lift this requirement.

## The module system

Bazel can be extended by adding modules to it. Each module must subclass
`BlazeModule` (the name is a relic of the history of Bazel when it used to be
called Blaze) and gets information about various events during the execution of
a command.

They are mostly used to implement various pieces of "non-core" functionality
that only some versions of Bazel (such as the one we use at Google) need:

*   Interfaces to remote execution systems
*   New commands

The set of extension points `BlazeModule` offers is somewhat haphazard. Don't
use it as an example of good design principles.

## The event bus

The main way BlazeModules communicate with the rest of Bazel is by an event bus
(`EventBus`): a new instance is created for every build, various parts of Bazel
can post events to it and modules can register listeners for the events they are
interested in. For example, the following things are represented as events:

*   The list of build targets to be built has been determined
    (`TargetParsingCompleteEvent`)
*   The top-level configurations have been determined
    (`BuildConfigurationEvent`)
*   A target was built, successfully or not (`TargetCompleteEvent`)
*   A test was run (`TestAttempt`, `TestSummary`)

Some of these events are represented outside of Bazel in the
[Build Event Protocol](/remote/bep)
(they are `BuildEvent`s). This allows not only `BlazeModule`s, but also things
outside the Bazel process to observe the build. They are accessible either as a
file that contains protocol messages or Bazel can connect to a server (called
the Build Event Service) to stream events.

This is implemented in the `build.lib.buildeventservice` and
`build.lib.buildeventstream` Java packages.

## External repositories

Note: The information in this section is out of date, as code in this area has
undergone extensive change in the past couple of years. Please refer to
[external dependencies overview](/external/overview) for more up-to-date
information.

Whereas Bazel was originally designed to be used in a monorepo (a single source
tree containing everything one needs to build), Bazel lives in a world where
this is not necessarily true. "External repositories" are an abstraction used to
bridge these two worlds: they represent code that is necessary for the build but
is not in the main source tree.

### The WORKSPACE file

The set of external repositories is determined by parsing the WORKSPACE file.
For example, a declaration like this:

```
    local_repository(name="foo", path="/foo/bar")
```

Results in the repository called `@foo` being available. Where this gets
complicated is that one can define new repository rules in Starlark files, which
can then be used to load new Starlark code, which can be used to define new
repository rules and so on…

To handle this case, the parsing of the WORKSPACE file (in
`WorkspaceFileFunction`) is split up into chunks delineated by `load()`
statements. The chunk index is indicated by `WorkspaceFileKey.getIndex()` and
computing `WorkspaceFileFunction` until index X means evaluating it until the
Xth `load()` statement.

### Fetching repositories

Before the code of the repository is available to Bazel, it needs to be
_fetched_. This results in Bazel creating a directory under
`$OUTPUT_BASE/external/<repository name>`.

Fetching the repository happens in the following steps:

1.  `PackageLookupFunction` realizes that it needs a repository and creates a
    `RepositoryName` as a `SkyKey`, which invokes `RepositoryLoaderFunction`
2.  `RepositoryLoaderFunction` forwards the request to
    `RepositoryDelegatorFunction` for unclear reasons (the code says it's to
    avoid re-downloading things in case of Skyframe restarts, but it's not a
    very solid reasoning)
3.  `RepositoryDelegatorFunction` finds out the repository rule it's asked to
    fetch by iterating over the chunks of the WORKSPACE file until the requested
    repository is found
4.  The appropriate `RepositoryFunction` is found that implements the repository
    fetching; it's either the Starlark implementation of the repository or a
    hard-coded map for repositories that are implemented in Java.

There are various layers of caching since fetching a repository can be very
expensive:

1.  There is a cache for downloaded files that is keyed by their checksum
    (`RepositoryCache`). This requires the checksum to be available in the
    WORKSPACE file, but that's good for hermeticity anyway. This is shared by
    every Bazel server instance on the same workstation, regardless of which
    workspace or output base they are running in.
2.  A "marker file" is written for each repository under `$OUTPUT_BASE/external`
    that contains a checksum of the rule that was used to fetch it. If the Bazel
    server restarts but the checksum does not change, it's not re-fetched. This
    is implemented in `RepositoryDelegatorFunction.DigestWriter` .
3.  The `--distdir` command line option designates another cache that is used to
    look up artifacts to be downloaded. This is useful in enterprise settings
    where Bazel should not fetch random things from the Internet. This is
    implemented by `DownloadManager` .

Once a repository is downloaded, the artifacts in it are treated as source
artifacts. This poses a problem because Bazel usually checks for up-to-dateness
of source artifacts by calling stat() on them, and these artifacts are also
invalidated when the definition of the repository they are in changes. Thus,
`FileStateValue`s for an artifact in an external repository need to depend on
their external repository. This is handled by `ExternalFilesHelper`.

### Repository mappings

It can happen that multiple repositories want to depend on the same repository,
but in different versions (this is an instance of the "diamond dependency
problem"). For example, if two binaries in separate repositories in the build
want to depend on Guava, they will presumably both refer to Guava with labels
starting `@guava//` and expect that to mean different versions of it.

Therefore, Bazel allows one to re-map external repository labels so that the
string `@guava//` can refer to one Guava repository (such as `@guava1//`) in the
repository of one binary and another Guava repository (such as `@guava2//`) the
repository of the other.

Alternatively, this can also be used to **join** diamonds. If a repository
depends on `@guava1//`, and another depends on `@guava2//`, repository mapping
allows one to re-map both repositories to use a canonical `@guava//` repository.

The mapping is specified in the WORKSPACE file as the `repo_mapping` attribute
of individual repository definitions. It then appears in Skyframe as a member of
`WorkspaceFileValue`, where it is plumbed to:

*   `Package.Builder.repositoryMapping` which is used to transform label-valued
    attributes of rules in the package by
    `RuleClass.populateRuleAttributeValues()`
*   `Package.repositoryMapping` which is used in the analysis phase (for
    resolving things like `$(location)` which are not parsed in the loading
    phase)
*   `BzlLoadFunction` for resolving labels in load() statements

## JNI bits

The server of Bazel is _mostly_ written in Java. The exception is the parts that
Java cannot do by itself or couldn't do by itself when we implemented it. This
is mostly limited to interaction with the file system, process control and
various other low-level things.

The C++ code lives under src/main/native and the Java classes with native
methods are:

*   `NativePosixFiles` and `NativePosixFileSystem`
*   `ProcessUtils`
*   `WindowsFileOperations` and `WindowsFileProcesses`
*   `com.google.devtools.build.lib.platform`

## Console output

Emitting console output seems like a simple thing, but the confluence of running
multiple processes (sometimes remotely), fine-grained caching, the desire to
have a nice and colorful terminal output and having a long-running server makes
it non-trivial.

Right after the RPC call comes in from the client, two `RpcOutputStream`
instances are created (for stdout and stderr) that forward the data printed into
them to the client. These are then wrapped in an `OutErr` (an (stdout, stderr)
pair). Anything that needs to be printed on the console goes through these
streams. Then these streams are handed over to
`BlazeCommandDispatcher.execExclusively()`.

Output is by default printed with ANSI escape sequences. When these are not
desired (`--color=no`), they are stripped by an `AnsiStrippingOutputStream`. In
addition, `System.out` and `System.err` are redirected to these output streams.
This is so that debugging information can be printed using
`System.err.println()` and still end up in the terminal output of the client
(which is different from that of the server). Care is taken that if a process
produces binary output (such as `bazel query --output=proto`), no munging of stdout
takes place.

Short messages (errors, warnings and the like) are expressed through the
`EventHandler` interface. Notably, these are different from what one posts to
the `EventBus` (this is confusing). Each `Event` has an `EventKind` (error,
warning, info, and a few others) and they may have a `Location` (the place in
the source code that caused the event to happen).

Some `EventHandler` implementations store the events they received. This is used
to replay information to the UI caused by various kinds of cached processing,
for example, the warnings emitted by a cached configured target.

Some `EventHandler`s also allow posting events that eventually find their way to
the event bus (regular `Event`s do _not _appear there). These are
implementations of `ExtendedEventHandler` and their main use is to replay cached
`EventBus` events. These `EventBus` events all implement `Postable`, but not
everything that is posted to `EventBus` necessarily implements this interface;
only those that are cached by an `ExtendedEventHandler` (it would be nice and
most of the things do; it's not enforced, though)

Terminal output is _mostly_ emitted through `UiEventHandler`, which is
responsible for all the fancy output formatting and progress reporting Bazel
does. It has two inputs:

*   The event bus
*   The event stream piped into it through Reporter

The only direct connection the command execution machinery (for example the rest of
Bazel) has to the RPC stream to the client is through `Reporter.getOutErr()`,
which allows direct access to these streams. It's only used when a command needs
to dump large amounts of possible binary data (such as `bazel query`).

## Profiling Bazel

Bazel is fast. Bazel is also slow, because builds tend to grow until just the
edge of what's bearable. For this reason, Bazel includes a profiler which can be
used to profile builds and Bazel itself. It's implemented in a class that's
aptly named `Profiler`. It's turned on by default, although it records only
abridged data so that its overhead is tolerable; The command line
`--record_full_profiler_data` makes it record everything it can.

It emits a profile in the Chrome profiler format; it's best viewed in Chrome.
It's data model is that of task stacks: one can start tasks and end tasks and
they are supposed to be neatly nested within each other. Each Java thread gets
its own task stack. **TODO:** How does this work with actions and
continuation-passing style?

The profiler is started and stopped in `BlazeRuntime.initProfiler()` and
`BlazeRuntime.afterCommand()` respectively and attempts to be live for as long
as possible so that we can profile everything. To add something to the profile,
call `Profiler.instance().profile()`. It returns a `Closeable`, whose closure
represents the end of the task. It's best used with try-with-resources
statements.

We also do rudimentary memory profiling in `MemoryProfiler`. It's also always on
and it mostly records maximum heap sizes and GC behavior.

## Testing Bazel

Bazel has two main kinds of tests: ones that observe Bazel as a "black box" and
ones that only run the analysis phase. We call the former "integration tests"
and the latter "unit tests", although they are more like integration tests that
are, well, less integrated. We also have some actual unit tests, where they are
necessary.

Of integration tests, we have two kinds:

1.  Ones implemented using a very elaborate bash test framework under
    `src/test/shell`
2.  Ones implemented in Java. These are implemented as subclasses of
    `BuildIntegrationTestCase`

`BuildIntegrationTestCase` is the preferred integration testing framework as it
is well-equipped for most testing scenarios. As it is a Java framework, it
provides debuggability and seamless integration with many common development
tools. There are many examples of `BuildIntegrationTestCase` classes in the
Bazel repository.

Analysis tests are implemented as subclasses of `BuildViewTestCase`. There is a
scratch file system you can use to write `BUILD` files, then various helper
methods can request configured targets, change the configuration and assert
various things about the result of the analysis.



# Contribute to Bazel documentation

Thank you for contributing to Bazel's documentation! There are a few ways to
help create better docs for our community.

## Documentation types

This site includes a few types of content.

 - *Narrative documentation*, which is written by technical writers and
   engineers. Most of this site is narrative documentation that covers
   conceptual and task-based guides.
 - *Reference documentation*, which is generated documentation from code comments.
   You can't make changes to the reference doc pages directly, but instead need
   to change their source.

## Documentation infrastructure

Bazel documentation is served from Google and the source files are mirrored in
Bazel's GitHub repository. You can make changes to the source files in GitHub.
If approved, you can merge the changes and a Bazel maintainer will update the
website source to publish your updates.

## Small changes

You can approach small changes, such as fixing errors or typos, in a couple of
ways.

 - **Pull request**. You can create a pull request in GitHub with the
   [web-based editor](https://docs.github.com/repositories/working-with-files/managing-files/editing-files) or on a branch.
 - **Bug**. You can file a bug with details and suggested changes and the Bazel
   documentation owners will make the update.

## Large changes

If you want to make substantial changes to existing documentation or propose
new documentation, you can either create a pull request or start with a Google
doc and contact the Bazel Owners to collaborate.



translation: human
page_type: lcat

# Contribution policy

This page covers Bazel's governance model and contribution policy.

## Governance model

The [Bazel project](https://github.com/bazelbuild){: .external} is led and managed by Google
and has a large community of contributors outside of Google. Some Bazel
components (such as specific rules repositories under the
[bazelbuild](https://github.com/bazelbuild){: .external} organization) are led,
maintained, and managed by members of the community. The Google Bazel team
reviews suggestions to add community-owned repositories (such as rules) to the
[bazelbuild](https://github.com/bazelbuild){: .external} GitHub organization.

### Contributor roles

Here are outlines of the roles in the Bazel project, including their
responsibilities:

*   **Owners**: The Google Bazel team. Owners are responsible for:
    *   Strategy, maintenance, and leadership of the Bazel project.
    *   Building and maintaining Bazel's core functionality.
    *   Appointing Maintainers and approving new repositories.
*   **Maintainers**: The Google Bazel team and designated GitHub users.
    Maintainers are responsible for:
    *   Building and maintaining the primary functionality of their repository.
    *   Reviewing and approving contributions to areas of the Bazel code base.
    *   Supporting users and contributors with timely and transparent issue
        management, PR review, and documentation.
    *   Releasing, testing and collaborating with Bazel Owners.
*   **Contributors**: All users who contribute code or documentation to the
    Bazel project.
    *   Creating well-written PRs to contribute to Bazel's codebase and
        documentation.
    *   Using standard channels, such as GitHub Issues, to propose changes and
        report issues.

### Becoming a Maintainer

Bazel Owners may appoint Maintainers to lead well-defined areas of code, such as
rule sets. Contributors with a record of consistent, responsible past
contributions who are planning major contributions in the future could be
considered to become qualified Maintainers.

## Contribution policy

The Bazel project accepts contributions from external contributors. Here are the
contribution policies for Google-managed and Community-managed areas of code.

*   **Licensing**. All Maintainers and Contributors must sign the
    [Google’s Contributor License Agreement](https://cla.developers.google.com/clas){: .external}.
*   **Contributions**. Owners and Maintainers should make every effort to accept
    worthwhile contributions. All contributions must be:
    *   Well written and well tested
    *   Discussed and approved by the Maintainers of the relevant area of code.
        Discussions and approvals happen on GitHub Issues and in GitHub PRs.
        Larger contributions require a
        [design review](/contribute/design-documents).
    *   Added to Bazel's Continuous Integration system if not already present.
    *   Supportable and aligned with Bazel product direction
*   **Code review**. All changes in all `bazelbuild` repositories require
    review:
    *   All PRs must be approved by an Owner or Maintainer.
    *   Only Owners and Maintainers can merge PRs.
*   **Compatibility**. Owners may need to reject or request modifications to PRs
    in the unlikely event that the change requires substantial modifications to
    internal Google systems.
*   **Documentation**. Where relevant, feature contributions should include
    documentation updates.

For more details on contributing to Bazel, see our
[contribution guidelines](/contribute/).



# Naming a Bazel related project

First, thank you for contributing to the Bazel ecosystem! Please reach out to
the Bazel community on the
[bazel-discuss mailing list](https://groups.google.com/forum/#!forum/bazel-discuss
){: .external} to share your project and its suggested name.

If you are building a Bazel related tool or sharing your Skylark rules,
we recommend following these guidelines for the name of your project:

## Naming Starlark rules

See [Deploying new Starlark rules](/rules/deploying)
in the docs.

## Naming other Bazel related tools

This section applies if you are building a tool to enrich the Bazel ecosystem.
For example, a new IDE plugin or a new build system migrator.

Picking a good name for your tool can be hard. If we’re not careful and use too
many codenames, the Bazel ecosystem could become very difficult to understand
for newcomers.

Follow these guidelines for naming Bazel tools:

1. Prefer **not introducing a new brand name**: "*Bazel*" is already a new brand
for our users, we should avoid confusing them with too many new names.

2. Prefer **using a name that includes "Bazel"**: This helps to express that it
is a Bazel related tool, it also helps people find it with a search engine.

3. Prefer **using names that are descriptive about what the tool is doing**:
Ideally, the name should not need a subtitle for users to have a first good
guess at what the tool does. Using english words separated by spaces is a good
way to achieve this.

4. **It is not a requirement to use a floral or food theme**: Bazel evokes
[basil](https://en.wikipedia.org/wiki/Basil), the plant. You do not need to
look for a name that is a plant, food or that relates to "basil."

5. **If your tool relates to another third party brand, use it only as a
descriptor**: For example, use "Bazel migrator for Cmake" instead of
"Cmake Bazel migrator".

These guidelines also apply to the GitHub repository URL. Reading the repository
URL should help people understand what the tool does. Of course, the repository
name can be shorter and must use dashes instead of spaces and lower case letters.

Examples of good names:

* *Bazel for Eclipse*: Users will understand that if they want to use Bazel
  with Eclipse, this is where they should be looking. It uses a third party brand
  as a descriptor.
* *Bazel buildfarm*: A "buildfarm" is a
  [compile farm](https://en.wikipedia.org/wiki/Compile_farm){: .external}. Users
  will understand that this project relates to building on servers.

Examples of names to avoid:

* *Ocimum*: The [scientific name of basil](https://en.wikipedia.org/wiki/Ocimum){: .external}
  does not relate enough to the Bazel project.
* *Bazelizer*: The tool behind this name could do a lot of things, this name is
   not descriptive enough.

Note that these recommendations are aligned with the
[guidelines](https://opensource.google.com/docs/releasing/preparing/#name){: .external}
Google uses when open sourcing a project.



# Maintaining Bazel Scoop package on Windows

Note: The Scoop package is experimental. To provide feedback, go to
`@excitoon` in issue tracker.

## Prerequisites

You need:

*    [Scoop package manager](https://scoop.sh/) installed
*    GitHub account in order to publish and create pull requests to
     [scoopinstaller/scoop-main](https://github.com/scoopinstaller/scoop-main){: .external}
     * [@excitoon](https://github.com/excitoon){: .external} currently maintains this
       unofficial package. Feel free to ask questions by
       [e-mail](mailto:vladimir.chebotarev@gmail.com) or
       [Telegram](http://telegram.me/excitoon){: .external}.

## Release process

Scoop packages are very easy to maintain. Once you have the URL of released
Bazel, you need to make appropriate changes in
[this file](https://github.com/scoopinstaller/scoop-main/blob/master/bucket/bazel.json){: .external}:

- update version
- update dependencies if needed
- update URL
- update hash (`sha256` by default)

In your filesystem, `bazel.json` is located in the directory
`%UserProfile%/scoop/buckets/main/bucket` by default. This directory belongs to
your clone of a Git repository
[scoopinstaller/scoop-main](https://github.com/scoopinstaller/scoop-main){: .external}.

Test the result:

```
scoop uninstall bazel
scoop install bazel
bazel version
bazel something_else
```

The first time, make a fork of
[scoopinstaller/scoop-main](https://github.com/scoopinstaller/scoop-main){: .external} and
specify it as your own remote for `%UserProfile%/scoop/buckets/main`:

```
git remote add mine FORK_URL
```

Push your changes to your fork and create a pull request.



# A Guide to Skyframe `StateMachine`s

## Overview

A Skyframe `StateMachine` is a *deconstructed* function-object that resides on
the heap. It supports flexible and evaluation without redundancy[^1] when
required values are not immediately available but computed asynchronously. The
`StateMachine` cannot tie up a thread resource while waiting, but instead has to
be suspended and resumed. The deconstruction thus exposes explicit re-entry
points so that prior computations can be skipped.

`StateMachine`s can be used to express sequences, branching, structured logical
concurrency and are tailored specifically for Skyframe interaction.
`StateMachine`s can be composed into larger `StateMachine`s and share
sub-`StateMachine`s. Concurrency is always hierarchical by construction and
purely logical. Every concurrent subtask runs in the single shared parent
SkyFunction thread.

## Introduction

This section briefly motivates and introduces `StateMachine`s, found in the
[`java.com.google.devtools.build.skyframe.state`](https://github.com/bazelbuild/bazel/tree/master/src/main/java/com/google/devtools/build/skyframe/state)
package.

### A brief introduction to Skyframe restarts

Skyframe is a framework that performs parallel evaluation of dependency graphs.
Each node in the graph corresponds with the evaluation of a SkyFunction with a
SkyKey specifying its parameters and SkyValue specifying its result. The
computational model is such that a SkyFunction may lookup SkyValues by SkyKey,
triggering recursive, parallel evaluation of additional SkyFunctions. Instead of
blocking, which would tie up a thread, when a requested SkyValue is not yet
ready because some subgraph of computation is incomplete, the requesting
SkyFunction observes a `null` `getValue` response and should return `null`
instead of a SkyValue, signaling that it is incomplete due to missing inputs.
Skyframe *restarts* the SkyFunctions when all previously requested SkyValues
become available.

Before the introduction of `SkyKeyComputeState`, the traditional way of handling
a restart was to fully rerun the computation. Although this has quadratic
complexity, functions written this way eventually complete because each rerun,
fewer lookups return `null`. With `SkyKeyComputeState` it is possible to
associate hand-specified check-point data with a SkyFunction, saving significant
recomputation.

`StateMachine`s are objects that live inside `SkyKeyComputeState` and eliminate
virtually all recomputation when a SkyFunction restarts (assuming that
`SkyKeyComputeState` does not fall out of cache) by exposing suspend and resume
execution hooks.

### Stateful computations inside `SkyKeyComputeState`

From an object-oriented design standpoint, it makes sense to consider storing
computational objects inside `SkyKeyComputeState` instead of pure data values.
In *Java*, the bare minimum description of a behavior carrying object is a
*functional interface* and it turns out to be sufficient. A `StateMachine` has
the following, curiously recursive, definition[^2].

```
@FunctionalInterface
public interface StateMachine {
  StateMachine step(Tasks tasks) throws InterruptedException;
}
```

The `Tasks` interface is analogous to `SkyFunction.Environment` but it is
designed for asynchrony and adds support for logically concurrent subtasks[^3].

The return value of `step` is another `StateMachine`, allowing the specification
of a sequence of steps, inductively. `step` returns `DONE` when the
`StateMachine` is done. For example:

```
class HelloWorld implements StateMachine {
  @Override
  public StateMachine step(Tasks tasks) {
    System.out.println("hello");
    return this::step2;  // The next step is HelloWorld.step2.
  }

  private StateMachine step2(Tasks tasks) {
     System.out.println("world");
     // DONE is special value defined in the `StateMachine` interface signaling
     // that the computation is done.
     return DONE;
  }
}
```

describes a `StateMachine` with the following output.

```
hello
world
```

Note that the method reference `this::step2` is also a `StateMachine` due to
`step2` satisfying `StateMachine`'s functional interface definition. Method
references are the most common way to specify the next state in a
`StateMachine`.

![Suspending and resuming](/contribute/images/suspend-resume.svg)

Intuitively, breaking a computation down into `StateMachine` steps, instead of a
monolithic function, provides the hooks needed to *suspend* and *resume* a
computation. When `StateMachine.step` returns, there is an explicit *suspension*
point. The continuation specified by the returned `StateMachine` value is an
explicit *resume* point. Recomputation can thus be avoided because the
computation can be picked up exactly where it left off.

### Callbacks, continuations and asynchronous computation

In technical terms, a `StateMachine` serves as a *continuation*, determining the
subsequent computation to be executed. Instead of blocking, a `StateMachine` can
voluntarily *suspend* by returning from the `step` function, which transfers
control back to a [`Driver`](#drivers-and-bridging) instance. The `Driver` can
then switch to a ready `StateMachine` or relinquish control back to Skyframe.

Traditionally, *callbacks* and *continuations* are conflated into one concept.
However, `StateMachine`s maintain a distinction between the two.

*   *Callback* - describes where to store the result of an asynchronous
    computation.
*   *Continuation* - specifies the next execution state.

Callbacks are required when invoking an asynchronous operation, which means that
the actual operation doesn't occur immediately upon calling the method, as in
the case of a SkyValue lookup. Callbacks should be kept as simple as possible.

Caution: A common pitfall of callbacks is that the asynchronous computation must
ensure the callback is called by the end of every reachable path. It's possible
to overlook some branches and the compiler doesn't give warnings about this.

*Continuations* are the `StateMachine` return values of `StateMachine`s and
encapsulate the complex execution that follows once all asynchronous
computations resolve. This structured approach helps to keep the complexity of
callbacks manageable.

## Tasks

The `Tasks` interface provides `StateMachine`s with an API to lookup SkyValues
by SkyKey and to schedule concurrent subtasks.

```
interface Tasks {
  void enqueue(StateMachine subtask);

  void lookUp(SkyKey key, Consumer<SkyValue> sink);

  <E extends Exception>
  void lookUp(SkyKey key, Class<E> exceptionClass, ValueOrExceptionSink<E> sink);

  // lookUp overloads for 2 and 3 exception types exist, but are elided here.
}
```

Tip: When any state uses the `Tasks` interface to perform lookups or create
subtasks, those lookups and subtasks will complete before the next state begins.

Tip: (Corollary) If subtasks are complex `StateMachine`s or recursively create
subtasks, they all *transitively* complete before the next state begins.

### SkyValue lookups

`StateMachine`s use `Tasks.lookUp` overloads to look up SkyValues. They are
analogous to `SkyFunction.Environment.getValue` and
`SkyFunction.Environment.getValueOrThrow` and have similar exception handling
semantics. The implementation does not immediately perform the lookup, but
instead, batches[^4] as many lookups as possible before doing so. The value
might not be immediately available, for example, requiring a Skyframe restart,
so the caller specifies what to do with the resulting value using a callback.

The `StateMachine` processor ([`Driver`s and bridging to
SkyFrame](#drivers-and-bridging)) guarantees that the value is available before
the next state begins. An example follows.

```
class DoesLookup implements StateMachine, Consumer<SkyValue> {
  private Value value;

  @Override
  public StateMachine step(Tasks tasks) {
    tasks.lookUp(new Key(), (Consumer<SkyValue>) this);
    return this::processValue;
  }

  // The `lookUp` call in `step` causes this to be called before `processValue`.
  @Override  // Implementation of Consumer<SkyValue>.
  public void accept(SkyValue value) {
    this.value = (Value)value;
  }

  private StateMachine processValue(Tasks tasks) {
    System.out.println(value);  // Prints the string representation of `value`.
    return DONE;
  }
}
```

In the above example, the first step does a lookup for `new Key()`, passing
`this` as the consumer. That is possible because `DoesLookup` implements
`Consumer<SkyValue>`.

Tip: When passing `this` as a value sink, it's helpful to readers to upcast it
to the receiver type to narrow down the purpose of passing `this`. The example
passes `(Consumer<SkyValue>) this`.

By contract, before the next state `DoesLookup.processValue` begins, all the
lookups of `DoesLookup.step` are complete. Therefore `value` is available when
it is accessed in `processValue`.

### Subtasks

`Tasks.enqueue` requests the execution of logically concurrent subtasks.
Subtasks are also `StateMachine`s and can do anything regular `StateMachine`s
can do, including recursively creating more subtasks or looking up SkyValues.
Much like `lookUp`, the state machine driver ensures that all subtasks are
complete before proceeding to the next step. An example follows.

```
class Subtasks implements StateMachine {
  private int i = 0;

  @Override
  public StateMachine step(Tasks tasks) {
    tasks.enqueue(new Subtask1());
    tasks.enqueue(new Subtask2());
    // The next step is Subtasks.processResults. It won't be called until both
    // Subtask1 and Subtask 2 are complete.
    return this::processResults;
  }

  private StateMachine processResults(Tasks tasks) {
    System.out.println(i);  // Prints "3".
    return DONE;  // Subtasks is done.
  }

  private class Subtask1 implements StateMachine {
    @Override
    public StateMachine step(Tasks tasks) {
      i += 1;
      return DONE;  // Subtask1 is done.
    }
  }

  private class Subtask2 implements StateMachine {
    @Override
    public StateMachine step(Tasks tasks) {
      i += 2;
      return DONE;  // Subtask2 is done.
    }
  }
}
```

Though `Subtask1` and `Subtask2` are logically concurrent, everything runs in a
single thread so the "concurrent" update of `i` does not need any
synchronization.

### Structured concurrency

Since every `lookUp` and `enqueue` must resolve before advancing to the next
state, it means that concurrency is naturally limited to tree-structures. It's
possible to create hierarchical[^5] concurrency as shown in the following
example.

![Structured Concurrency](/contribute/images/structured-concurrency.svg)

It's hard to tell from the *UML* that the concurrency structure forms a tree.
There's an [alternate view](#concurrency-tree-diagram) that better shows the
tree structure.

![Unstructured Concurrency](/contribute/images/unstructured-concurrency.svg)

Structured concurrency is much easier to reason about.

## Composition and control flow patterns

This section presents examples for how multiple `StateMachine`s can be composed
and solutions to certain control flow problems.

### Sequential states

This is the most common and straightforward control flow pattern. An example of
this is shown in [Stateful computations inside
`SkyKeyComputeState`](#stateful-computations).

### Branching

Branching states in `StateMachine`s can be achieved by returning different
values using regular *Java* control flow, as shown in the following example.

```
class Branch implements StateMachine {
  @Override
  public StateMachine step(Tasks tasks) {
    // Returns different state machines, depending on condition.
    if (shouldUseA()) {
      return this::performA;
    }
    return this::performB;
  }
  …
}
```

It’s very common for certain branches to return `DONE`, for early completion.

### Advanced sequential composition

Since the `StateMachine` control structure is memoryless, sharing `StateMachine`
definitions as subtasks can sometimes be awkward. Let *M<sub>1</sub>* and
*M<sub>2</sub>* be `StateMachine` instances that share a `StateMachine`, *S*,
with *M<sub>1</sub>* and *M<sub>2</sub>* being the sequences *&lt;A, S, B>* and
*&lt;X, S, Y>* respectively. The problem is that *S* doesn’t know whether to
continue to *B* or *Y* after it completes and `StateMachine`s don't quite keep a
call stack. This section reviews some techniques for achieving this.

#### `StateMachine` as terminal sequence element

This doesn’t solve the initial problem posed. It only demonstrates sequential
composition when the shared `StateMachine` is terminal in the sequence.

```
// S is the shared state machine.
class S implements StateMachine { … }

class M1 implements StateMachine {
  @Override
  public StateMachine step(Tasks tasks) {
    performA();
    return new S();
  }
}

class M2 implements StateMachine {
  @Override
  public StateMachine step(Tasks tasks) {
    performX();
    return new S();
  }
}
```

This works even if *S* is itself a complex state machine.

#### Subtask for sequential composition

Since enqueued subtasks are guaranteed to complete before the next state, it’s
sometimes possible to slightly abuse[^6] the subtask mechanism.

```
class M1 implements StateMachine {
  @Override
  public StateMachine step(Tasks tasks) {
    performA();
    // S starts after `step` returns and by contract must complete before `doB`
    // begins. It is effectively sequential, inducing the sequence < A, S, B >.
    tasks.enqueue(new S());
    return this::doB;
  }

  private StateMachine doB(Tasks tasks) {
    performB();
    return DONE;
  }
}

class M2 implements StateMachine {
  @Override
  public StateMachine step(Tasks tasks) {
    performX();
    // Similarly, this induces the sequence < X, S, Y>.
    tasks.enqueue(new S());
    return this::doY;
  }

  private StateMachine doY(Tasks tasks) {
    performY();
    return DONE;
  }
}
```

#### `runAfter` injection

Sometimes, abusing `Tasks.enqueue` is impossible because there are other
parallel subtasks or `Tasks.lookUp` calls that must be completed before *S*
executes. In this case, injecting a `runAfter` parameter into *S* can be used to
inform *S* of what to do next.

```
class S implements StateMachine {
  // Specifies what to run after S completes.
  private final StateMachine runAfter;

  @Override
  public StateMachine step(Tasks tasks) {
    … // Performs some computations.
    return this::processResults;
  }

  @Nullable
  private StateMachine processResults(Tasks tasks) {
    … // Does some additional processing.

    // Executes the state machine defined by `runAfter` after S completes.
    return runAfter;
  }
}

class M1 implements StateMachine {
  @Override
  public StateMachine step(Tasks tasks) {
    performA();
    // Passes `this::doB` as the `runAfter` parameter of S, resulting in the
    // sequence < A, S, B >.
    return new S(/* runAfter= */ this::doB);
  }

  private StateMachine doB(Tasks tasks) {
    performB();
    return DONE;
  }
}

class M2 implements StateMachine {
  @Override
  public StateMachine step(Tasks tasks) {
    performX();
    // Passes `this::doY` as the `runAfter` parameter of S, resulting in the
    // sequence < X, S, Y >.
    return new S(/* runAfter= */ this::doY);
  }

  private StateMachine doY(Tasks tasks) {
    performY();
    return DONE;
  }
}
```

This approach is cleaner than abusing subtasks. However, applying this too
liberally, for example, by nesting multiple `StateMachine`s with `runAfter`, is
the road to [Callback Hell](#callback-hell). It’s better to break up sequential
`runAfter`s with ordinary sequential states instead.

```
  return new S(/* runAfter= */ new T(/* runAfter= */ this::nextStep))
```

can be replaced with the following.

```
  private StateMachine step1(Tasks tasks) {
     doStep1();
     return new S(/* runAfter= */ this::intermediateStep);
  }

  private StateMachine intermediateStep(Tasks tasks) {
    return new T(/* runAfter= */ this::nextStep);
  }
```

Note: It's possible to pass `DONE` as the `runAfter` parameter when there's
nothing to run afterwards.

Tip: When using `runAfter`, always annotate the parameter with `/* runAfter= */`
to let the reader know the meaning at the callsite.

#### *Forbidden* alternative: `runAfterUnlessError`

In an earlier draft, we had considered a `runAfterUnlessError` that would abort
early on errors. This was motivated by the fact that errors often end up getting
checked twice, once by the `StateMachine` that has a `runAfter` reference and
once by the `runAfter` machine itself.

After some deliberation, we decided that uniformity of the code is more
important than deduplicating the error checking. It would be confusing if the
`runAfter` mechanism did not work in a consistent manner with the
`tasks.enqueue` mechanism, which always requires error checking.

Warning: When using `runAfter`, the machine that has the injected `runAfter`
should invoke it unconditionally at completion, even on error, for consistency.

### Direct delegation

Each time there is a formal state transition, the main `Driver` loop advances.
As per contract, advancing states means that all previously enqueued SkyValue
lookups and subtasks resolve before the next state executes. Sometimes the logic
of a delegate `StateMachine` makes a phase advance unnecessary or
counterproductive. For example, if the first `step` of the delegate performs
SkyKey lookups that could be parallelized with lookups of the delegating state
then a phase advance would make them sequential. It could make more sense to
perform direct delegation, as shown in the example below.

```
class Parent implements StateMachine {
  @Override
  public StateMachine step(Tasks tasks ) {
    tasks.lookUp(new Key1(), this);
    // Directly delegates to `Delegate`.
    //
    // The (valid) alternative:
    //   return new Delegate(this::afterDelegation);
    // would cause `Delegate.step` to execute after `step` completes which would
    // cause lookups of `Key1` and `Key2` to be sequential instead of parallel.
    return new Delegate(this::afterDelegation).step(tasks);
  }

  private StateMachine afterDelegation(Tasks tasks) {
    …
  }
}

class Delegate implements StateMachine {
  private final StateMachine runAfter;

  Delegate(StateMachine runAfter) {
    this.runAfter = runAfter;
  }

  @Override
  public StateMachine step(Tasks tasks) {
    tasks.lookUp(new Key2(), this);
    return …;
  }

  // Rest of implementation.
  …

  private StateMachine complete(Tasks tasks) {
    …
    return runAfter;
  }
}
```

## Data flow

The focus of the previous discussion has been on managing control flow. This
section describes the propagation of data values.

### Implementing `Tasks.lookUp` callbacks

There’s an example of implementing a `Tasks.lookUp` callback in [SkyValue
lookups](#skyvalue-lookups). This section provides rationale and suggests
approaches for handling multiple SkyValues.

#### `Tasks.lookUp` callbacks

The `Tasks.lookUp` method takes a callback, `sink`, as a parameter.

```
  void lookUp(SkyKey key, Consumer<SkyValue> sink);
```

The idiomatic approach would be to use a *Java* lambda to implement this:

```
  tasks.lookUp(key, value -> myValue = (MyValueClass)value);
```

with `myValue` being a member variable of the `StateMachine` instance doing the
lookup. However, the lambda requires an extra memory allocation compared to
implementing the `Consumer<SkyValue>` interface in the `StateMachine`
implementation. The lambda is still useful when there are multiple lookups that
would be ambiguous.

Note: Bikeshed warning. There is a noticeable difference of approximately 1%
end-to-end CPU usage when implementing callbacks systematically in
`StateMachine` implementations compared to using lambdas, which makes this
recommendation debatable. To avoid unnecessary debates, it is advised to leave
the decision up to the individual implementing the solution.

There are also error handling overloads of `Tasks.lookUp`, that are analogous to
`SkyFunction.Environment.getValueOrThrow`.

```
  <E extends Exception> void lookUp(
      SkyKey key, Class<E> exceptionClass, ValueOrExceptionSink<E> sink);

  interface ValueOrExceptionSink<E extends Exception> {
    void acceptValueOrException(@Nullable SkyValue value, @Nullable E exception);
  }
```

An example implementation is shown below.

```
class PerformLookupWithError extends StateMachine, ValueOrExceptionSink<MyException> {
  private MyValue value;
  private MyException error;

  @Override
  public StateMachine step(Tasks tasks) {
    tasks.lookUp(new MyKey(), MyException.class, ValueOrExceptionSink<MyException>) this);
    return this::processResult;
  }

  @Override
  public acceptValueOrException(@Nullable SkyValue value, @Nullable MyException exception) {
    if (value != null) {
      this.value = (MyValue)value;
      return;
    }
    if (exception != null) {
      this.error = exception;
      return;
    }
    throw new IllegalArgumentException("Both parameters were unexpectedly null.");
  }

  private StateMachine processResult(Tasks tasks) {
    if (exception != null) {
      // Handles the error.
      …
      return DONE;
    }
    // Processes `value`, which is non-null.
    …
  }
}
```

As with lookups without error handling, having the `StateMachine` class directly
implement the callback saves a memory allocation for the lamba.

[Error handling](#error-handling) provides a bit more detail, but essentially,
there's not much difference between the propagation of errors and normal values.

#### Consuming multiple SkyValues

Multiple SkyValue lookups are often required. An approach that works much of the
time is to switch on the type of SkyValue. The following is an example that has
been simplified from prototype production code.

```
  @Nullable
  private StateMachine fetchConfigurationAndPackage(Tasks tasks) {
    var configurationKey = configuredTarget.getConfigurationKey();
    if (configurationKey != null) {
      tasks.lookUp(configurationKey, (Consumer<SkyValue>) this);
    }

    var packageId = configuredTarget.getLabel().getPackageIdentifier();
    tasks.lookUp(PackageValue.key(packageId), (Consumer<SkyValue>) this);

    return this::constructResult;
  }

  @Override  // Implementation of `Consumer<SkyValue>`.
  public void accept(SkyValue value) {
    if (value instanceof BuildConfigurationValue) {
      this.configurationValue = (BuildConfigurationValue) value;
      return;
    }
    if (value instanceof PackageValue) {
      this.pkg = ((PackageValue) value).getPackage();
      return;
    }
    throw new IllegalArgumentException("unexpected value: " + value);
  }
```

The `Consumer<SkyValue>` callback implementation can be shared unambiguously
because the value types are different. When that’s not the case, falling back to
lambda-based implementations or full inner-class instances that implement the
appropriate callbacks is viable.

### Propagating values between `StateMachine`s

So far, this document has only explained how to arrange work in a subtask, but
subtasks also need to report a values back to the caller. Since subtasks are
logically asynchronous, their results are communicated back to the caller using
a *callback*. To make this work, the subtask defines a sink interface that is
injected via its constructor.

```
class BarProducer implements StateMachine {
  // Callers of BarProducer implement the following interface to accept its
  // results. Exactly one of the two methods will be called by the time
  // BarProducer completes.
  interface ResultSink {
    void acceptBarValue(Bar value);
    void acceptBarError(BarException exception);
  }

  private final ResultSink sink;

  BarProducer(ResultSink sink) {
     this.sink = sink;
  }

  … // StateMachine steps that end with this::complete.

  private StateMachine complete(Tasks tasks) {
    if (hasError()) {
      sink.acceptBarError(getError());
      return DONE;
    }
    sink.acceptBarValue(getValue());
    return DONE;
  }
}
```

Tip: It would be tempting to use the more concise signature void `accept(Bar
value)` rather than the stuttery `void acceptBarValue(Bar value)` above.
However, `Consumer<SkyValue>` is a common overload of `void accept(Bar value)`,
so doing this often leads to violations of the [Overloads: never
split](https://google.github.io/styleguide/javaguide.html#s3.4.2-ordering-class-contents)
style-guide rule.

Tip: Using a custom `ResultSink` type instead of a generic one from
`java.util.function` makes it easy to find implementations in the code base,
improving readability.

A caller `StateMachine` would then look like the following.

```
class Caller implements StateMachine, BarProducer.ResultSink {
  interface ResultSink {
    void acceptCallerValue(Bar value);
    void acceptCallerError(BarException error);
  }

  private final ResultSink sink;

  private Bar value;

  Caller(ResultSink sink) {
    this.sink = sink;
  }

  @Override
  @Nullable
  public StateMachine step(Tasks tasks) {
    tasks.enqueue(new BarProducer((BarProducer.ResultSink) this));
    return this::processResult;
  }

  @Override
  public void acceptBarValue(Bar value) {
    this.value = value;
  }

  @Override
  public void acceptBarError(BarException error) {
    sink.acceptCallerError(error);
  }

  private StateMachine processResult(Tasks tasks) {
    // Since all enqueued subtasks resolve before `processResult` starts, one of
    // the `BarResultSink` callbacks must have been called by this point.
    if (value == null) {
      return DONE;  // There was a previously reported error.
    }
    var finalResult = computeResult(value);
    sink.acceptCallerValue(finalResult);
    return DONE;
  }
}
```

The preceding example demonstrates a few things. `Caller` has to propagate its
results back and defines its own `Caller.ResultSink`. `Caller` implements the
`BarProducer.ResultSink` callbacks. Upon resumption, `processResult` checks if
`value` is null to determine if an error occurred. This is a common behavior
pattern after accepting output from either a subtask or SkyValue lookup.

Note that the implementation of `acceptBarError` eagerly forwards the result to
the `Caller.ResultSink`, as required by [Error bubbling](#error-bubbling).

Alternatives for top-level `StateMachine`s are described in [`Driver`s and
bridging to SkyFunctions](#drivers-and-bridging).

### Error handling

There's a couple of examples of error handling already in [`Tasks.lookUp`
callbacks](#tasks-lookup-callbacks) and [Propagating values between
`StateMachines`](#propagating-values). Exceptions, other than
`InterruptedException` are not thrown, but instead passed around through
callbacks as values. Such callbacks often have exclusive-or semantics, with
exactly one of a value or error being passed.

The next section describes a a subtle, but important interaction with Skyframe
error handling.

#### Error bubbling (--nokeep\_going)

Warning: Errors need to be eagerly propagated all the way back to the
SkyFunction for error bubbling to function correctly.

During error bubbling, a SkyFunction may be restarted even if not all requested
SkyValues are available. In such cases, the subsequent state will never be
reached due to the `Tasks` API contract. However, the `StateMachine` should
still propagate the exception.

Since propagation must occur regardless of whether the next state is reached,
the error handling callback must perform this task. For an inner `StateMachine`,
this is achieved by invoking the parent callback.

At the top-level `StateMachine`, which interfaces with the SkyFunction, this can
be done by calling the `setException` method of `ValueOrExceptionProducer`.
`ValueOrExceptionProducer.tryProduceValue` will then throw the exception, even
if there are missing SkyValues.

If a `Driver` is being utilized directly, it is essential to check for
propagated errors from the SkyFunction, even if the machine has not finished
processing.

### Event Handling

For SkyFunctions that need to emit events, a `StoredEventHandler` is injected
into SkyKeyComputeState and further injected into `StateMachine`s that require
them. Historically, the `StoredEventHandler` was needed due to Skyframe dropping
certain events unless they are replayed but this was subsequently fixed.
`StoredEventHandler` injection is preserved because it simplifies the
implementation of events emitted from error handling callbacks.

## `Driver`s and bridging to SkyFunctions

A `Driver` is responsible for managing the execution of `StateMachine`s,
beginning with a specified root `StateMachine`. As `StateMachine`s can
recursively enqueue subtask `StateMachine`s, a single `Driver` can manage
numerous subtasks. These subtasks create a tree structure, a result of
[Structured concurrency](#structured-concurrency). The `Driver` batches SkyValue
lookups across subtasks for improved efficiency.

There are a number of classes built around the `Driver`, with the following API.

```
public final class Driver {
  public Driver(StateMachine root);
  public boolean drive(SkyFunction.Environment env) throws InterruptedException;
}
```

`Driver` takes a single root `StateMachine` as a parameter. Calling
`Driver.drive` executes the `StateMachine` as far as it can go without a
Skyframe restart. It returns true when the `StateMachine` completes and false
otherwise, indicating that not all values were available.

`Driver` maintains the concurrent state of the `StateMachine` and it is well
suited for embedding in `SkyKeyComputeState`.

### Directly instantiating `Driver`

`StateMachine` implementations conventionally communicate their results via
callbacks. It's possible to directly instantiate a `Driver` as shown in the
following example.

The `Driver` is embedded in the `SkyKeyComputeState` implementation along with
an implementation of the corresponding `ResultSink` to be defined a bit further
down. At the top level, the `State` object is an appropriate receiver for the
result of the computation as it is guaranteed to outlive `Driver`.

```
class State implements SkyKeyComputeState, ResultProducer.ResultSink {
  // The `Driver` instance, containing the full tree of all `StateMachine`
  // states. Responsible for calling `StateMachine.step` implementations when
  // asynchronous values are available and performing batched SkyFrame lookups.
  //
  // Non-null while `result` is being computed.
  private Driver resultProducer;

  // Variable for storing the result of the `StateMachine`
  //
  // Will be non-null after the computation completes.
  //
  private ResultType result;

  // Implements `ResultProducer.ResultSink`.
  //
  // `ResultProducer` propagates its final value through a callback that is
  // implemented here.
  @Override
  public void acceptResult(ResultType result) {
    this.result = result;
  }
}
```

The code below sketches the `ResultProducer`.

```
class ResultProducer implements StateMachine {
  interface ResultSink {
    void acceptResult(ResultType value);
  }

  private final Parameters parameters;
  private final ResultSink sink;

  … // Other internal state.

  ResultProducer(Parameters parameters, ResultSink sink) {
    this.parameters = parameters;
    this.sink = sink;
  }

  @Override
  public StateMachine step(Tasks tasks) {
    …  // Implementation.
    return this::complete;
  }

  private StateMachine complete(Tasks tasks) {
    sink.acceptResult(getResult());
    return DONE;
  }
}
```

Then the code for lazily computing the result could look like the following.

```
@Nullable
private Result computeResult(State state, Skyfunction.Environment env)
    throws InterruptedException {
  if (state.result != null) {
    return state.result;
  }
  if (state.resultProducer == null) {
    state.resultProducer = new Driver(new ResultProducer(
      new Parameters(), (ResultProducer.ResultSink)state));
  }
  if (state.resultProducer.drive(env)) {
    // Clears the `Driver` instance as it is no longer needed.
    state.resultProducer = null;
  }
  return state.result;
}
```

### Embedding `Driver`

If the `StateMachine` produces a value and raises no exceptions, embedding
`Driver` is another possible implementation, as shown in the following example.

```
class ResultProducer implements StateMachine {
  private final Parameters parameters;
  private final Driver driver;

  private ResultType result;

  ResultProducer(Parameters parameters) {
    this.parameters = parameters;
    this.driver = new Driver(this);
  }

  @Nullable  // Null when a Skyframe restart is needed.
  public ResultType tryProduceValue( SkyFunction.Environment env)
      throws InterruptedException {
    if (!driver.drive(env)) {
      return null;
    }
    return result;
  }

  @Override
  public StateMachine step(Tasks tasks) {
    …  // Implementation.
}
```

The SkyFunction may have code that looks like the following (where `State` is
the function specific type of `SkyKeyComputeState`).

```
@Nullable  // Null when a Skyframe restart is needed.
Result computeResult(SkyFunction.Environment env, State state)
    throws InterruptedException {
  if (state.result != null) {
    return state.result;
  }
  if (state.resultProducer == null) {
    state.resultProducer = new ResultProducer(new Parameters());
  }
  var result = state.resultProducer.tryProduceValue(env);
  if (result == null) {
    return null;
  }
  state.resultProducer = null;
  return state.result = result;
}
```

Embedding `Driver` in the `StateMachine` implementation is a better fit for
Skyframe's synchronous coding style.

### StateMachines that may produce exceptions

Otherwise, there are `SkyKeyComputeState`-embeddable `ValueOrExceptionProducer`
and `ValueOrException2Producer` classes that have synchronous APIs to match
synchronous SkyFunction code.

The `ValueOrExceptionProducer` abstract class includes the following methods.

```
public abstract class ValueOrExceptionProducer<V, E extends Exception>
    implements StateMachine {
  @Nullable
  public final V tryProduceValue(Environment env)
      throws InterruptedException, E {
    …  // Implementation.
  }

  protected final void setValue(V value)  {  … // Implementation. }
  protected final void setException(E exception) {  … // Implementation. }
}
```

It includes an embedded `Driver` instance and closely resembles the
`ResultProducer` class in [Embedding driver](#embedding-driver) and interfaces
with the SkyFunction in a similar manner. Instead of defining a `ResultSink`,
implementations call `setValue` or `setException` when either of those occur.
When both occur, the exception takes priority. The `tryProduceValue` method
bridges the asynchronous callback code to synchronous code and throws an
exception when one is set.

As previously noted, during error bubbling, it's possible for an error to occur
even if the machine is not yet done because not all inputs are available. To
accommodate this, `tryProduceValue` throws any set exceptions, even before the
machine is done.

## Epilogue: Eventually removing callbacks

`StateMachine`s are a highly efficient, but boilerplate intensive way to perform
asynchronous computation. Continuations (particularly in the form of `Runnable`s
passed to `ListenableFuture`) are widespread in certain parts of *Bazel* code,
but aren't prevalent in analysis SkyFunctions. Analysis is mostly CPU bound and
there are no efficient asynchronous APIs for disk I/O. Eventually, it would be
good to optimize away callbacks as they have a learning curve and impede
readability.

One of the most promising alternatives is *Java* virtual threads. Instead of
having to write callbacks, everything is replaced with synchronous, blocking
calls. This is possible because tying up a virtual thread resource, unlike a
platform thread, is supposed to be cheap. However, even with virtual threads,
replacing simple synchronous operations with thread creation and synchronization
primitives is too expensive. We performed a migration from `StateMachine`s to
*Java* virtual threads and they were orders of magnitude slower, leading to
almost a 3x increase in end-to-end analysis latency. Since virtual threads are
still a preview feature, it's possible that this migration can be performed at a
later date when performance improves.

Another approach to consider is waiting for *Loom* coroutines, if they ever
become available. The advantage here is that it might be possible to reduce
synchronization overhead by using cooperative multitasking.

If all else fails, low-level bytecode rewriting could also be a viable
alternative. With enough optimization, it might be possible to achieve
performance that approaches hand-written callback code.

## Appendix

### Callback Hell

Callback hell is an infamous problem in asynchronous code that uses callbacks.
It stems from the fact that the continuation for a subsequent step is nested
within the previous step. If there are many steps, this nesting can be extremely
deep. If coupled with control flow the code becomes unmanageable.

```
class CallbackHell implements StateMachine {
  @Override
  public StateMachine step(Tasks task) {
    doA();
    return (t, l) -> {
      doB();
      return (t1, l2) -> {
        doC();
        return DONE;
      };
    };
  }
}
```

One of the advantages of nested implementations is that the stack frame of the
outer step can be preserved. In *Java*, captured lambda variables must be
effectively final so using such variables can be cumbersome. Deep nesting is
avoided by returning method references as continuations instead of lambdas as
shown as follows.

```
class CallbackHellAvoided implements StateMachine {
  @Override
  public StateMachine step(Tasks task) {
    doA();
    return this::step2;
  }

  private StateMachine step2(Tasks tasks) {
    doB();
    return this::step3;
  }

  private StateMachine step3(Tasks tasks) {
    doC();
    return DONE;
  }
}
```

Callback hell may also occur if the [`runAfter` injection](#runafter-injection)
pattern is used too densely, but this can be avoided by interspersing injections
with sequential steps.

#### Example: Chained SkyValue lookups

It is often the case that the application logic requires dependent chains of
SkyValue lookups, for example, if a second SkyKey depends on the first SkyValue.
Thinking about this naively, this would result in a complex, deeply nested
callback structure.

```
private ValueType1 value1;
private ValueType2 value2;

private StateMachine step1(...) {
  tasks.lookUp(key1, (Consumer<SkyValue>) this);  // key1 has type KeyType1.
  return this::step2;
}

@Override
public void accept(SkyValue value) {
  this.value1 = (ValueType1) value;
}

private StateMachine step2(...) {
  KeyType2 key2 = computeKey(value1);
  tasks.lookup(key2, this::acceptValueType2);
  return this::step3;
}

private void acceptValueType2(SkyValue value) {
  this.value2 = (ValueType2) value;
}
```

However, since continuations are specified as method references, the code looks
procedural across state transitions: `step2` follows `step1`. Note that here, a
lambda is used to assign `value2`. This makes the ordering of the code match the
ordering of the computation from top-to-bottom.

### Miscellaneous Tips

#### Readability: Execution Ordering

To improve readability, strive to keep the `StateMachine.step` implementations
in execution order and callback implementations immediately following where they
are passed in the code. This isn't always possible where the control flow
branches. Additional comments might be helpful in such cases.

In [Example: Chained SkyValue lookups](#chained-skyvalue-lookups), an
intermediate method reference is created to achieve this. This trades a small
amount of performance for readability, which is likely worthwhile here.

#### Generational Hypothesis

Medium-lived *Java* objects break the generational hypothesis of the *Java*
garbage collector, which is designed to handle objects that live for a very
short time or objects that live forever. By definition, objects in
`SkyKeyComputeState` violate this hypothesis. Such objects, containing the
constructed tree of all still-running `StateMachine`s, rooted at `Driver` have
an intermediate lifespan as they suspend, waiting for asynchronous computations
to complete.

It seems less bad in JDK19, but when using `StateMachine`s, it's sometimes
possible to observe an increase in GC time, even with dramatic decreases in
actual garbage generated. Since `StateMachine`s have an intermediate lifespan
they could be promoted to old gen, causing it to fill up more quickly, thus
necessitating more expensive major or full GCs to clean up.

The initial precaution is to minimize the use of `StateMachine` variables, but
it is not always feasible, for example, if a value is needed across multiple
states. Where it is possible, local stack `step` variables are young generation
variables and efficiently GC'd.

For `StateMachine` variables, breaking things down into subtasks and following
the recommended pattern for [Propagating values between
`StateMachine`s](#propagating-values) is also helpful. Observe that when
following the pattern, only child `StateMachine`s have references to parent
`StateMachine`s and not vice versa. This means that as children complete and
update the parents using result callbacks, the children naturally fall out of
scope and become eligible for GC.

Finally, in some cases, a `StateMachine` variable is needed in earlier states
but not in later states. It can be beneficial to null out references of large
objects once it is known that they are no longer needed.

#### Naming states

When naming a method, it's usually possible to name a method for the behavior
that happens within that method. It's less clear how to do this in
`StateMachine`s because there is no stack. For example, suppose method `foo`
calls a sub-method `bar`. In a `StateMachine`, this could be translated into the
state sequence `foo`, followed by `bar`. `foo` no longer includes the behavior
`bar`. As a result, method names for states tend to be narrower in scope,
potentially reflecting local behavior.

### Concurrency tree diagram

The following is an alternative view of the diagram in [Structured
concurrency](#structured-concurrency) that better depicts the tree structure.
The blocks form a small tree.

![Structured Concurrency 3D](/contribute/images/structured-concurrency-3d.svg)

[^1]: In contrast to Skyframe's convention of restarting from the beginning when
 values are not available.
[^2]: Note that `step` is permitted to throw `InterruptedException`, but the
 examples omit this. There are a few low methods in *Bazel* code that throw
 this exception and it propagates up to the `Driver`, to be described later,
 that runs the `StateMachine`. It's fine to not declare it to be thrown when
 unneeded.
[^3]: Concurrent subtasks were motivated by the `ConfiguredTargetFunction` which
 performs *independent* work for each dependency. Instead of manipulating
 complex data structures that process all the dependencies at once,
 introducing inefficiencies, each dependency has its own independent
 `StateMachine`.
[^4]: Multiple `tasks.lookUp` calls within a single step are batched together.
 Additional batching can be created by lookups occurring within concurrent
 subtasks.
[^5]: This is conceptually similar to Java’s structured concurrency
 [jeps/428](https://openjdk.org/jeps/428).
[^6]: Doing this is similar to spawning a thread and joining it to achieve
 sequential composition.