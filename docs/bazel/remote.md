

Project: /_project.yaml
Book: /_book.yaml

# Multiplex Workers (Experimental Feature)

{% include "_buttons.html" %}

This page describes multiplex workers, how to write multiplex-compatible
rules, and workarounds for certain limitations.

Caution: Experimental features are subject to change at any time.

_Multiplex workers_ allow Bazel to handle multiple requests with a single worker
process. For multi-threaded workers, Bazel can use fewer resources to
achieve the same, or better performance. For example, instead of having one
worker process per worker, Bazel can have four multiplexed workers talking to
the same worker process, which can then handle requests in parallel. For
languages like Java and Scala, this saves JVM warm-up time and JIT compilation
time, and in general it allows using one shared cache between all workers of
the same type.

## Overview {:#overview}

There are two layers between the Bazel server and the worker process. For certain
mnemonics that can run processes in parallel, Bazel gets a `WorkerProxy` from
the worker pool. The `WorkerProxy` forwards requests to the worker process
sequentially along with a `request_id`, the worker process processes the request
and sends responses to the `WorkerMultiplexer`. When the `WorkerMultiplexer`
receives a response, it parses the `request_id` and then forwards the responses
back to the correct `WorkerProxy`. Just as with non-multiplexed workers, all
communication is done over standard in/out, but the tool cannot just use
`stderr` for user-visible output ([see below](#output)).

Each worker has a key. Bazel uses the key's hash code (composed of environment
variables, the execution root, and the mnemonic) to determine which
`WorkerMultiplexer` to use. `WorkerProxy`s communicate with the same
`WorkerMultiplexer` if they have the same hash code. Therefore, assuming
environment variables and the execution root are the same in a single Bazel
invocation, each unique mnemonic can only have one `WorkerMultiplexer` and one
worker process. The total number of workers, including regular workers and
`WorkerProxy`s, is still limited by `--worker_max_instances`.

## Writing multiplex-compatible rules {:#multiplex-rules}

The rule's worker process should be multi-threaded to take advantage of
multiplex workers. Protobuf allows a ruleset to parse a single request even
though there might be multiple requests piling up in the stream. Whenever the
worker process parses a request from the stream, it should handle the request in
a new thread. Because different thread could complete and write to the stream at
the same time, the worker process needs to make sure the responses are written
atomically (messages don't overlap). Responses must contain the
`request_id` of the request they're handling.

### Handling multiplex output {:#output}

Multiplex workers need to be more careful about handling their output than
singleplex workers. Anything sent to `stderr` will go into a single log file
shared among all `WorkerProxy`s of the same type,
randomly interleaved between concurrent requests. While redirecting `stdout`
into `stderr` is a good idea, do not collect that output into the `output`
field of `WorkResponse`, as that could show the user mangled pieces of output.
If your tool only sends user-oriented output to `stdout` or `stderr`, you will
need to change that behaviour before you can enable multiplex workers.

## Enabling multiplex workers {:#multiplex-workers}

Multiplex workers are not enabled by default. A ruleset can turn on multiplex
workers by using the `supports-multiplex-workers` tag in the
`execution_requirements` of an action (just like the `supports-workers` tag
enables regular workers). As is the case when using regular workers, a worker
strategy needs to be specified, either at the ruleset level (for example,
`--strategy=[some_mnemonic]=worker`) or generally at the strategy level (for
example, `--dynamic_local_strategy=worker,standalone`.) No additional flags are
necessary, and `supports-multiplex-workers` takes precedence over
`supports-workers`, if both are set. You can turn off multiplex workers
globally by passing `--noworker_multiplex`.

A ruleset is encouraged to use multiplex workers if possible,  to reduce memory
pressure and improve performance. However, multiplex workers are not currently
compatible with [dynamic execution](/remote/dynamic) unless they
implement multiplex sandboxing. Attempting to run non-sandboxed multiplex
workers with dynamic execution will silently use sandboxed
singleplex workers instead.

## Multiplex sandboxing

Multiplex workers can be sandboxed by adding explicit support for it in the
worker implementations. While singleplex worker sandboxing can be done by
running each worker process in its own sandbox, multiplex workers share the
process working directory between multiple parallel requests. To allow
sandboxing of multiplex workers, the worker must support reading from and
writing to a subdirectory specified in each request, instead of directly in
its working directory.

To support multiplex sandboxing, the worker must use the `sandbox_dir` field
from the `WorkRequest` and use that as a prefix for all file reads and writes.
While the `arguments` and `inputs` fields remain unchanged from an unsandboxed
request, the actual inputs are relative to the `sandbox_dir`. The worker must
translate file paths found in `arguments` and `inputs` to read from this
modified path, and must also write all outputs relative to the `sandbox_dir`.
This includes paths such as '.', as well as paths found in files specified
in the arguments (such as ["argfile"](https://docs.oracle.com/javase/7/docs/technotes/tools/windows/javac.html#commandlineargfile) arguments).

Once a worker supports multiplex sandboxing, the ruleset can declare this
support by adding `supports-multiplex-sandboxing` to the
`execution_requirements` of an action. Bazel will then use multiplex sandboxing
if the `--experimental_worker_multiplex_sandboxing` flag is passed, or if
the worker is used with dynamic execution.

The worker files of a sandboxed multiplex worker are still relative to the
working directory of the worker process. Thus, if a file is
used both for running the worker and as an input, it must be specified both as
an input in the flagfile argument as well as in `tools`, `executable`, or
`runfiles`.


Project: /_project.yaml
Book: /_book.yaml

# Build Event Protocol Examples

{% include "_buttons.html" %}

The full specification of the Build Event Protocol can be found in its protocol
buffer definition. However, it might be helpful to build up some intuition
before looking at the specification.

Consider a simple Bazel workspace that consists of two empty shell scripts
`foo.sh` and `foo_test.sh` and the following `BUILD` file:

```bash
sh_library(
    name = "foo_lib",
    srcs = ["foo.sh"],
)

sh_test(
    name = "foo_test",
    srcs = ["foo_test.sh"],
    deps = [":foo_lib"],
)
```

When running `bazel test ...` on this project the build graph of the generated
build events will resemble the graph below. The arrows indicate the
aforementioned parent and child relationship. Note that some build events and
most fields have been omitted for brevity.

![bep-graph](/docs/images/bep-graph.png "BEP graph")

**Figure 1.** BEP graph.

Initially, a `BuildStarted` event is published. The event informs us that the
build was invoked through the `bazel test` command and announces child events:

* `OptionsParsed`
* `WorkspaceStatus`
* `CommandLine`
* `UnstructuredCommandLine`
* `BuildMetadata`
* `BuildFinished`
* `PatternExpanded`
* `Progress`

The first three events provide information about how Bazel was invoked.

The `PatternExpanded` build event provides insight
into which specific targets the `...` pattern expanded to:
`//foo:foo_lib` and `//foo:foo_test`. It does so by declaring two
`TargetConfigured` events as children. Note that the `TargetConfigured` event
declares the `Configuration` event as a child event, even though `Configuration`
has been posted before the `TargetConfigured` event.

Besides the parent and child relationship, events may also refer to each other
using their build event identifiers. For example, in the above graph the
`TargetComplete` event refers to the `NamedSetOfFiles` event in its `fileSets`
field.

Build events that refer to files don’t usually embed the file
names and paths in the event. Instead, they contain the build event identifier
of a `NamedSetOfFiles` event, which will then contain the actual file names and
paths. The `NamedSetOfFiles` event allows a set of files to be reported once and
referred to by many targets. This structure is necessary because otherwise in
some cases the Build Event Protocol output size would grow quadratically with
the number of files. A `NamedSetOfFiles` event may also not have all its files
embedded, but instead refer to other `NamedSetOfFiles` events through their
build event identifiers.

Below is an instance of the `TargetComplete` event for the `//foo:foo_lib`
target from the above graph, printed in protocol buffer’s JSON representation.
The build event identifier contains the target as an opaque string and refers to
the `Configuration` event using its build event identifier. The event does not
announce any child events. The payload contains information about whether the
target was built successfully, the set of output files, and the kind of target
built.

```json
{
  "id": {
    "targetCompleted": {
      "label": "//foo:foo_lib",
      "configuration": {
        "id": "544e39a7f0abdb3efdd29d675a48bc6a"
      }
    }
  },
  "completed": {
    "success": true,
    "outputGroup": [{
      "name": "default",
      "fileSets": [{
        "id": "0"
      }]
    }],
    "targetKind": "sh_library rule"
  }
}
```

## Aspect Results in BEP {:#aspect-results}

Ordinary builds evaluate actions associated with `(target, configuration)`
pairs. When building with [aspects](/extending/aspects) enabled, Bazel
additionally evaluates targets associated with `(target, configuration,
aspect)` triples, for each target affected by a given enabled aspect.

Evaluation results for aspects are available in BEP despite the absence of
aspect-specific event types. For each `(target, configuration)` pair with an
applicable aspect, Bazel publishes an additional `TargetConfigured` and
`TargetComplete` event bearing the result from applying the aspect to the
target. For example, if `//:foo_lib` is built with
`--aspects=aspects/myaspect.bzl%custom_aspect`, this event would also appear in
the BEP:

```json
{
  "id": {
    "targetCompleted": {
      "label": "//foo:foo_lib",
      "configuration": {
        "id": "544e39a7f0abdb3efdd29d675a48bc6a"
      },
      "aspect": "aspects/myaspect.bzl%custom_aspect"
    }
  },
  "completed": {
    "success": true,
    "outputGroup": [{
      "name": "default",
      "fileSets": [{
        "id": "1"
      }]
    }]
  }
}
```

Note: The only difference between the IDs is the presence of the `aspect`
field. A tool that does not check the `aspect` ID field and accumulates output
files by target may conflate target outputs with aspect outputs.

## Consuming `NamedSetOfFiles` {:#consuming-namedsetoffiles}

Determining the artifacts produced by a given target (or aspect) is a common
BEP use-case that can be done efficiently with some preparation. This section
discusses the recursive, shared structure offered by the `NamedSetOfFiles`
event, which matches the structure of a Starlark [Depset](/extending/depsets).

Consumers must take care to avoid quadratic algorithms when processing
`NamedSetOfFiles` events because large builds can contain tens of thousands of
such events, requiring hundreds of millions operations in a traversal with
quadratic complexity.

![namedsetoffiles-bep-graph](/docs/images/namedsetoffiles-bep-graph.png "NamedSetOfFiles BEP graph")

**Figure 2.** `NamedSetOfFiles` BEP graph.

A `NamedSetOfFiles` event always appears in the BEP stream *before* a
`TargetComplete` or `NamedSetOfFiles` event that references it. This is the
inverse of the "parent-child" event relationship, where all but the first event
appears after at least one event announcing it. A `NamedSetOfFiles` event is
announced by a `Progress` event with no semantics.

Given these ordering and sharing constraints, a typical consumer must buffer all
`NamedSetOfFiles` events until the BEP stream is exhausted. The following JSON
event stream and Python code demonstrate how to populate a map from
target/aspect to built artifacts in the "default" output group, and how to
process the outputs for a subset of built targets/aspects:

```python
named_sets = {}  # type: dict[str, NamedSetOfFiles]
outputs = {}     # type: dict[str, dict[str, set[str]]]

for event in stream:
  kind = event.id.WhichOneof("id")
  if kind == "named_set":
    named_sets[event.id.named_set.id] = event.named_set_of_files
  elif kind == "target_completed":
    tc = event.id.target_completed
    target_id = (tc.label, tc.configuration.id, tc.aspect)
    outputs[target_id] = {}
    for group in event.completed.output_group:
      outputs[target_id][group.name] = {fs.id for fs in group.file_sets}

for result_id in relevant_subset(outputs.keys()):
  visit = outputs[result_id].get("default", [])
  seen_sets = set(visit)
  while visit:
    set_name = visit.pop()
    s = named_sets[set_name]
    for f in s.files:
      process_file(result_id, f)
    for fs in s.file_sets:
      if fs.id not in seen_sets:
        visit.add(fs.id)
        seen_sets.add(fs.id)
```


Project: /_project.yaml
Book: /_book.yaml

# Persistent Workers

{% include "_buttons.html" %}

This page covers how to use persistent workers, the benefits, requirements, and
how workers affect sandboxing.

A persistent worker is a long-running process started by the Bazel server, which
functions as a *wrapper* around the actual *tool* (typically a compiler), or is
the *tool* itself. In order to benefit from persistent workers, the tool must
support doing a sequence of compilations, and the wrapper needs to translate
between the tool's API and the request/response format described below. The same
worker might be called with and without the `--persistent_worker` flag in the
same build, and is responsible for appropriately starting and talking to the
tool, as well as shutting down workers on exit. Each worker instance is assigned
(but not chrooted to) a separate working directory under
`<outputBase>/bazel-workers`.

Using persistent workers is an
[execution strategy](/docs/user-manual#execution-strategy) that decreases
start-up overhead, allows more JIT compilation, and enables caching of for
example the abstract syntax trees in the action execution. This strategy
achieves these improvements by sending multiple requests to a long-running
process.

Persistent workers are implemented for multiple languages, including Java,
[Scala](https://github.com/bazelbuild/rules_scala){: .external},
[Kotlin](https://github.com/bazelbuild/rules_kotlin){: .external}, and more.

Programs using a NodeJS runtime can use the
[@bazel/worker](https://www.npmjs.com/package/@bazel/worker) helper library to
implement the worker protocol.

## Using persistent workers {:#usage}

[Bazel 0.27 and higher](https://blog.bazel.build/2019/06/19/list-strategy.html)
uses persistent workers by default when executing builds, though remote
execution takes precedence. For actions that do not support persistent workers,
Bazel falls back to starting a tool instance for each action. You can explicitly
set your build to use persistent workers by setting the `worker`
[strategy](/docs/user-manual#execution-strategy) for the applicable tool
mnemonics. As a best practice, this example includes specifying `local` as a
fallback to the `worker` strategy:

```posix-terminal
bazel build //{{ '<var>' }}my:target{{ '</var>' }} --strategy=Javac=worker,local
```

Using the workers strategy instead of the local strategy can boost compilation
speed significantly, depending on implementation. For Java, builds can be 2–4
times faster, sometimes more for incremental compilation. Compiling Bazel is
about 2.5 times as fast with workers. For more details, see the
"[Choosing number of workers](#number-of-workers)" section.

If you also have a remote build environment that matches your local build
environment, you can use the experimental
[*dynamic* strategy](https://blog.bazel.build/2019/02/01/dynamic-spawn-scheduler.html){: .external},
which races a remote execution and a worker execution. To enable the dynamic
strategy, pass the
[--experimental_spawn_scheduler](/reference/command-line-reference#flag--experimental_spawn_scheduler)
flag. This strategy automatically enables workers, so there is no need to
specify the `worker` strategy, but you can still use `local` or `sandboxed` as
fallbacks.

## Choosing number of workers {:#number-of-workers}

The default number of worker instances per mnemonic is 4, but can be adjusted
with the
[`worker_max_instances`](/reference/command-line-reference#flag--worker_max_instances)
flag. There is a trade-off between making good use of the available CPUs and the
amount of JIT compilation and cache hits you get. With more workers, more
targets will pay start-up costs of running non-JITted code and hitting cold
caches. If you have a small number of targets to build, a single worker may give
the best trade-off between compilation speed and resource usage (for example,
see [issue #8586](https://github.com/bazelbuild/bazel/issues/8586){: .external}.
The `worker_max_instances` flag sets the maximum number of worker instances per
mnemonic and flag set (see below), so in a mixed system you could end up using
quite a lot of memory if you keep the default value. For incremental builds the
benefit of multiple worker instances is even smaller.

This graph shows the from-scratch compilation times for Bazel (target
`//src:bazel`) on a 6-core hyper-threaded Intel Xeon 3.5 GHz Linux workstation
with 64 GB of RAM. For each worker configuration, five clean builds are run and
the average of the last four are taken.

![Graph of performance improvements of clean builds](/docs/images/workers-clean-chart.png "Performance improvements of clean builds")

**Figure 1.** Graph of performance improvements of clean builds.

For this configuration, two workers give the fastest compile, though at only 14%
improvement compared to one worker. One worker is a good option if you want to
use less memory.

Incremental compilation typically benefits even more. Clean builds are
relatively rare, but changing a single file between compiles is common, in
particular in test-driven development. The above example also has some non-Java
packaging actions to it that can overshadow the incremental compile time.

Recompiling the Java sources only
(`//src/main/java/com/google/devtools/build/lib/bazel:BazelServer_deploy.jar`)
after changing an internal string constant in
[AbstractContainerizingSandboxedSpawn.java](https://github.com/bazelbuild/bazel/blob/master/src/main/java/com/google/devtools/build/lib/sandbox/AbstractContainerizingSandboxedSpawn.java){: .external}
gives a 3x speed-up (average of 20 incremental builds with one warmup build
discarded):

![Graph of performance improvements of incremental builds](/docs/images/workers-incremental-chart.png "Performance improvements of incremental builds")

**Figure 2.** Graph of performance improvements of incremental builds.

The speed-up depends on the change being made. A speed-up of a factor 6 is
measured in the above situation when a commonly used constant is changed.

## Modifying persistent workers {:#options}

You can pass the
[`--worker_extra_flag`](/reference/command-line-reference#flag--worker_extra_flag)
flag to specify start-up flags to workers, keyed by mnemonic. For instance,
passing `--worker_extra_flag=javac=--debug` turns on debugging for Javac only.
Only one worker flag can be set per use of this flag, and only for one mnemonic.
Workers are not just created separately for each mnemonic, but also for
variations in their start-up flags. Each combination of mnemonic and start-up
flags is combined into a `WorkerKey`, and for each `WorkerKey` up to
`worker_max_instances` workers may be created. See the next section for how the
action configuration can also specify set-up flags.

Passing the
[`--worker_sandboxing`](/reference/command-line-reference#flag--worker_sandboxing)
flag makes each worker request use a separate sandbox directory for all its
inputs. Setting up the [sandbox](/docs/sandboxing) takes some extra time,
especially on macOS, but gives a better correctness guarantee.

The
[`--worker_quit_after_build`](/reference/command-line-reference#flag--worker_quit_after_build)
flag is mainly useful for debugging and profiling. This flag forces all workers
to quit once a build is done. You can also pass
[`--worker_verbose`](/reference/command-line-reference#flag--worker_verbose) to
get more output about what the workers are doing. This flag is reflected in the
`verbosity` field in `WorkRequest`, allowing worker implementations to also be
more verbose.

Workers store their logs in the `<outputBase>/bazel-workers` directory, for
example
`/tmp/_bazel_larsrc/191013354bebe14fdddae77f2679c3ef/bazel-workers/worker-1-Javac.log`.
The file name includes the worker id and the mnemonic. Since there can be more
than one `WorkerKey` per mnemonic, you may see more than `worker_max_instances`
log files for a given mnemonic.

For Android builds, see details at the
[Android Build Performance page](/docs/android-build-performance).

## Implementing persistent workers {:#implementation}

See the [creating persistent workers](/remote/creating) page for more
information on how to make a worker.

This example shows a Starlark configuration for a worker that uses JSON:

```python
args_file = ctx.actions.declare_file(ctx.label.name + "_args_file")
ctx.actions.write(
    output = args_file,
    content = "\n".join(["-g", "-source", "1.5"] + ctx.files.srcs),
)
ctx.actions.run(
    mnemonic = "SomeCompiler",
    executable = "bin/some_compiler_wrapper",
    inputs = inputs,
    outputs = outputs,
    arguments = [ "-max_mem=4G",  "@%s" % args_file.path],
    execution_requirements = {
        "supports-workers" : "1", "requires-worker-protocol" : "json" }
)
```

With this definition, the first use of this action would start with executing
the command line `/bin/some_compiler -max_mem=4G --persistent_worker`. A request
to compile `Foo.java` would then look like:

NOTE: While the protocol buffer specification uses "snake case" (`request_id`),
the JSON protocol uses "camel case" (`requestId`). In this document, we will use
camel case in the JSON examples, but snake case when talking about the field
regardless of protocol.

```json
{
  "arguments": [ "-g", "-source", "1.5", "Foo.java" ]
  "inputs": [
    { "path": "symlinkfarm/input1", "digest": "d49a..." },
    { "path": "symlinkfarm/input2", "digest": "093d..." },
  ],
}
```

The worker receives this on `stdin` in newline-delimited JSON format (because
`requires-worker-protocol` is set to JSON). The worker then performs the action,
and sends a JSON-formatted `WorkResponse` to Bazel on its stdout. Bazel then
parses this response and manually converts it to a `WorkResponse` proto. To
communicate with the associated worker using binary-encoded protobuf instead of
JSON, `requires-worker-protocol` would be set to `proto`, like this:

```
  execution_requirements = {
    "supports-workers" : "1" ,
    "requires-worker-protocol" : "proto"
  }
```

If you do not include `requires-worker-protocol` in the execution requirements,
Bazel will default the worker communication to use protobuf.

Bazel derives the `WorkerKey` from the mnemonic and the shared flags, so if this
configuration allowed changing the `max_mem` parameter, a separate worker would
be spawned for each value used. This can lead to excessive memory consumption if
too many variations are used.

Each worker can currently only process one request at a time. The experimental
[multiplex workers](/remote/multiplex) feature allows using multiple
threads, if the underlying tool is multithreaded and the wrapper is set up to
understand this.

In
[this GitHub repo](https://github.com/Ubehebe/bazel-worker-examples){: .external},
you can see example worker wrappers written in Java as well as in Python. If you
are working in JavaScript or TypeScript, the
[@bazel/worker package](https://www.npmjs.com/package/@bazel/worker){: .external}
and
[nodejs worker example](https://github.com/bazelbuild/rules_nodejs/tree/stable/examples/worker){: .external}
might be helpful.

## How do workers affect sandboxing? {:#sandboxing}

Using the `worker` strategy by default does not run the action in a
[sandbox](/docs/sandboxing), similar to the `local` strategy. You can set the
`--worker_sandboxing` flag to run all workers inside sandboxes, making sure each
execution of the tool only sees the input files it's supposed to have. The tool
may still leak information between requests internally, for instance through a
cache. Using `dynamic` strategy
[requires workers to be sandboxed](https://github.com/bazelbuild/bazel/blob/master/src/main/java/com/google/devtools/build/lib/exec/SpawnStrategyRegistry.java){: .external}.

To allow correct use of compiler caches with workers, a digest is passed along
with each input file. Thus the compiler or the wrapper can check if the input is
still valid without having to read the file.

Even when using the input digests to guard against unwanted caching, sandboxed
workers offer less strict sandboxing than a pure sandbox, because the tool may
keep other internal state that has been affected by previous requests.

Multiplex workers can only be sandboxed if the worker implementation support it,
and this sandboxing must be separately enabled with the
`--experimental_worker_multiplex_sandboxing` flag. See more details in
[the design doc](https://docs.google.com/document/d/1ncLW0hz6uDhNvci1dpzfEoifwTiNTqiBEm1vi-bIIRM/edit)).

## Further reading {:#further-reading}

For more information on persistent workers, see:

*   [Original persistent workers blog post](https://blog.bazel.build/2015/12/10/java-workers.html)
*   [Haskell implementation description](https://www.tweag.io/blog/2019-09-25-bazel-ghc-persistent-worker-internship/){: .external}
*   [Blog post by Mike Morearty](https://medium.com/@mmorearty/how-to-create-a-persistent-worker-for-bazel-7738bba2cabb){: .external}
*   [Front End Development with Bazel: Angular/TypeScript and Persistent Workers
    w/ Asana](https://www.youtube.com/watch?v=0pgERydGyqo){: .external}
*   [Bazel strategies explained](https://jmmv.dev/2019/12/bazel-strategies.html){: .external}
*   [Informative worker strategy discussion on the bazel-discuss mailing list](https://groups.google.com/forum/#!msg/bazel-discuss/oAEnuhYOPm8/ol7hf4KWJgAJ){: .external}


Project: /_project.yaml
Book: /_book.yaml

# Dynamic Execution

{% include "_buttons.html" %}

__Dynamic execution__ is a feature in Bazel where local and remote execution of
the same action are started in parallel, using the output from the first branch
that finishes, cancelling the other branch. It combines the execution power
and/or large shared cache of a remote build system with the low latency of local
execution, providing the best of both worlds for clean and incremental builds
alike.

This page describes how to enable, tune, and debug dynamic execution. If you
have both local and remote execution set up and are trying to adjust Bazel
settings for better performance, this page is for you. If you don't already have
remote execution set up, go to the Bazel [Remote Execution
Overview](/remote/rbe) first.

## Enabling dynamic execution? {:#enabling-dynamic-execution}

The dynamic execution module is part of Bazel, but to make use of dynamic
execution, you must already be able to compile both locally and remotely from
the same Bazel setup.

To enable the dynamic execution module, pass the `--internal_spawn_scheduler`
flag to Bazel. This adds a new execution strategy called `dynamic`. You can now
use this as your strategy for the mnemonics you want to run dynamically, such as
`--strategy=Javac=dynamic`. See the next section for how to pick which mnemonics
to enable dynamic execution for.

For any mnemonic using the dynamic strategy, the remote execution strategies are
taken from the `--dynamic_remote_strategy` flag, and local strategies from the
`--dynamic_local_strategy` flag. Passing
`--dynamic_local_strategy=worker,sandboxed` sets the default for the local
branch of dynamic execution to try with workers or sandboxed execution in that
order. Passing `--dynamic_local_strategy=Javac=worker` overrides the default for
the Javac mnemonic only. The remote version works the same way. Both flags can
be specified multiple times. If an action cannot be executed locally, it is
executed remotely as normal, and vice-versa.

If your remote system has a cache, the `--dynamic_local_execution_delay` flag
adds a delay in milliseconds to the local execution after the remote system has
indicated a cache hit. This avoids running local execution when more cache hits
are likely. The default value is 1000ms, but should be tuned to being just a bit
longer than cache hits usually take. The actual time depends both on the remote
system and on how long a round-trip takes. Usually, the value will be the same
for all users of a given remote system, unless some of them are far enough away
to add roundtrip latency. You can use the [Bazel profiling
features](/rules/performance#performance-profiling) to look at how long typical
cache hits take.

Dynamic execution can be used with local sandboxed strategy as well as with
[persistent workers](/remote/persistent). Persistent workers will automatically
run with sandboxing when used with dynamic execution, and cannot use [multiplex
workers](/remote/multiplex). On Darwin and Windows systems, the sandboxed
strategy can be slow; you can pass `--reuse_sandbox_directories` to reduce
overhead of creating sandboxes on these systems.

Dynamic execution can also run with the `standalone` strategy, though since the
`standalone` strategy must take the output lock when it starts executing, it
effectively blocks the remote strategy from finishing first. The
`--experimental_local_lockfree_output` flag enables a way around this problem by
allowing the local execution to write directly to the output, but be aborted by
the remote execution, should that finish first.

If one of the branches of dynamic execution finishes first but is a failure, the
entire action fails. This is an intentional choice to prevent differences
between local and remote execution from going unnoticed.

For more background on how dynamic execution and its locking works, see Julio
Merino's excellent [blog
posts](https://jmmv.dev/series/bazel-dynamic-execution/){: .external}

## When should I use dynamic execution? {:#when-to-use}

Dynamic execution requires some form of [remote execution system](/remote/rbe).
It is not currently possible to use a cache-only remote system, as a cache miss
would be considered a failed action.

Not all types of actions are well suited for remote execution. The best
candidates are those that are inherently faster locally, for instance through
the use of [persistent workers](/remote/persistent), or those that run fast
enough that the overhead of remote execution dominates execution time. Since
each locally executed action locks some amount of CPU and memory resources,
running actions that don't fall into those categories merely delays execution
for those that do.

As of release
[5.0.0-pre.20210708.4](https://github.com/bazelbuild/bazel/releases/tag/5.0.0-pre.20210708.4){: .external},
[performance profiling](/rules/performance#performance-profiling) contains data
about worker execution, including time spent finishing a work request after
losing a dynamic execution race. If you see dynamic execution worker threads
spending significant time acquiring resources, or a lot of time in the
`async-worker-finish`, you may have some slow local actions delaying the worker
threads.

<p align="center">
<img width="596px" alt="Profiling data with poor dynamic execution performance"
 src="/docs/images/dyn-trace-alldynamic.png">
</p>

In the profile above, which uses 8 Javac workers, we see many Javac workers
having lost the races and finishing their work on the `async-worker-finish`
threads. This was caused by a non-worker mnemonic taking enough resources to
delay the workers.

<p align="center">
<img width="596px" alt="Profiling data with better dynamic execution performance"
 src="/docs/images/dyn-trace-javaconly.png">
</p>

When only Javac is run with dynamic execution, only about half of the started
workers end up losing the race after starting their work.

The previously recommended `--experimental_spawn_scheduler` flag is deprecated.
It turns on dynamic execution and sets `dynamic` as the default strategy for all
mnemonics, which would often lead to these kinds of problems.

## Performance {:#performance}

The dynamic execution approach assumes there are enough resources available
locally and remotely that it's worth spending some extra resources to improve
overall performance. But excessive resource usage may slow down Bazel itself or
the machine it runs on, or put unexpected pressure on a remote system. There are
several options for changing the behaviour of dynamic execution:

`--dynamic_local_execution_delay` delays the start of a local branch by a number
of milliseconds after the remote branch has started, but only if there has been
a remote cache hit during the current build. This makes builds that benefit
from remote caching not waste local resources when it is likely that most
outputs can be found in the cache. Depending on the quality of the cache,
reducing this might improve build speeds, at the cost of using more local
resources.

`--experimental_dynamic_local_load_factor` is an experimental advanced resource
management option. It takes a value from 0 to 1, 0 turning off this feature.
When set to a value above 0, Bazel adjusts the number of
locally scheduled actions when many actions waiting to
be scheduled. Setting it to 1 allows as many actions to be scheduled as there
are CPUs available (as per `--local_cpu_resources`). Lower values set the number
of actions scheduled to correspondingly fewer as higher numbers of actions are
available to run. This may sound counter-intuitive, but with a good remote
system, local execution does not help much when many actions are being run, and
the local CPU is better spent managing remote actions.

`--experimental_dynamic_slow_remote_time` prioritizes starting local branches
when the remote branch has been running for at least this long. Normally the
most recently scheduled action gets priority, as it has the greatest chance of
winning the race, but if the remote system sometimes hangs or takes extra long,
this can get a build to move along. This is not enabled by default, because it
could hide issues with the remote system that should rather be fixed. Make sure
to monitor your remote system performance if you enable this option.

`--experimental_dynamic_ignore_local_signals` can be used to let the remote
branch take over when a local spawn exits due to a given signal. This is
is mainly useful together with worker resource limits (see
[`--experimental_worker_memory_limit_mb`](https://bazel.build/reference/command-line-reference#flag--experimental_worker_memory_limit_mb),
[`--experimental_worker_sandbox_hardening`](https://bazel.build/reference/command-line-reference#flag--experimental_worker_sandbox_hardening),
and
[`--experimental_sandbox_memory_limit_mb`)](https://bazel.build/reference/command-line-reference#flag--experimental_sandbox_memory_limit_mb)),
where worker processes may be killed when they use too many resources.

The [JSON trace profile](/advanced/performance/json-trace-profile) contains a
number of performance-related graphs that can help identify ways to improve the
trade-off of performance and resource usage.

## Troubleshooting {:#troubleshooting}

Problems with dynamic execution can be subtle and hard to debug, as they can
manifest only under some specific combinations of local and remote execution.
The `--debug_spawn_scheduler` adds extra output from the dynamic execution
system that can help debug these problems. You can also adjust the
`--dynamic_local_execution_delay` flag and number of remote vs. local jobs to
make it easier to reproduce the problems.

If you are experiencing problems with dynamic execution using the `standalone`
strategy, try running without `--experimental_local_lockfree_output`, or run
your local actions sandboxed. This may slow down your build a bit (see above if
you're on Mac or Windows), but removes some possible causes for failures.

Project: /_project.yaml
Book: /_book.yaml

# Troubleshooting Bazel Remote Execution with Docker Sandbox

{% include "_buttons.html" %}

Bazel builds that succeed locally may fail when executed remotely due to
restrictions and requirements that do not affect local builds. The most common
causes of such failures are described in [Adapting Bazel Rules for Remote Execution](/remote/rules).

This page describes how to identify and resolve the most common issues that
arise with remote execution using the Docker sandbox feature, which imposes
restrictions upon the build equal to those of remote execution. This allows you
to troubleshoot your build without the need for a remote execution service.

The Docker sandbox feature mimics the restrictions of remote execution as
follows:

*   **Build actions execute in toolchain containers.** You can use the same
    toolchain containers to run your build locally and remotely via a service
    supporting containerized remote execution.

*   **No extraneous data crosses the container boundary.** Only explicitly
    declared inputs and outputs enter and leave the container, and only after
    the associated build action successfully completes.

*   **Each action executes in a fresh container.** A new, unique container is
    created for each spawned build action.

Note: Builds take noticeably more time to complete when the Docker sandbox
feature is enabled. This is normal.

You can troubleshoot these issues using one of the following methods:

*   **[Troubleshooting natively.](#troubleshooting-natively)** With this method,
    Bazel and its build actions run natively on your local machine. The Docker
    sandbox feature imposes restrictions upon the build equal to those of remote
    execution. However, this method will not detect local tools, states, and
    data leaking into your build, which will cause problems with remote execution.

*   **[Troubleshooting in a Docker container.](#troubleshooting-docker-container)**
    With this method, Bazel and its build actions run inside a Docker container,
    which allows you to detect tools, states, and data leaking from the local
    machine into the build in addition to imposing restrictions
    equal to those of remote execution. This method provides insight into your
    build even if portions of the build are failing. This method is experimental
    and not officially supported.

## Prerequisites {:#prerequisites}

Before you begin troubleshooting, do the following if you have not already done so:

*   Install Docker and configure the permissions required to run it.
*   Install Bazel 0.14.1 or later. Earlier versions do not support the Docker
    sandbox feature.
*   Add the [bazel-toolchains](https://releases.bazel.build/bazel-toolchains.html)
    repo, pinned to the latest release version, to your build's `WORKSPACE` file
    as described [here](https://releases.bazel.build/bazel-toolchains.html).
*   Add flags to your `.bazelrc` file to enable the feature. Create the file in
    the root directory of your Bazel project if it does not exist. Flags below
    are a reference sample. Please see the latest
    [`.bazelrc`](https://github.com/bazelbuild/bazel-toolchains/tree/master/bazelrc){: .external}
    file in the bazel-toolchains repo and copy the values of the flags defined
    there for config `docker-sandbox`.

```
# Docker Sandbox Mode
build:docker-sandbox --host_javabase=<...>
build:docker-sandbox --javabase=<...>
build:docker-sandbox --crosstool_top=<...>
build:docker-sandbox --experimental_docker_image=<...>
build:docker-sandbox --spawn_strategy=docker --strategy=Javac=docker --genrule_strategy=docker
build:docker-sandbox --define=EXECUTOR=remote
build:docker-sandbox --experimental_docker_verbose
build:docker-sandbox --experimental_enable_docker_sandbox
```

Note: The flags referenced in the `.bazelrc` file shown above are configured
to run within the [`rbe-ubuntu16-04`](https://console.cloud.google.com/launcher/details/google/rbe-ubuntu16-04){: .external}
container.

If your rules require additional tools, do the following:

1.  Create a custom Docker container by installing tools using a [Dockerfile](https://docs.docker.com/engine/reference/builder/){: .external}
    and [building](https://docs.docker.com/engine/reference/commandline/build/){: .external}
    the image locally.

2.  Replace the value of the `--experimental_docker_image` flag above with the
    name of your custom container image.


## Troubleshooting natively {:#troubleshooting-natively}

This method executes Bazel and all of its build actions directly on the local
machine and is a reliable way to confirm whether your build will succeed when
executed remotely.

However, with this method, locally installed tools, binaries, and data may leak
into into your build, especially if it uses [configure-style WORKSPACE rules](/remote/rules#manage-workspace-rules).
Such leaks will cause problems with remote execution; to detect them, [troubleshoot in a Docker container](#troubleshooting-docker-container)
in addition to troubleshooting natively.

### Step 1: Run the build {:#run-build}

1.  Add the `--config=docker-sandbox` flag to the Bazel command that executes
    your build. For example:

    ```posix-terminal
    bazel --bazelrc=.bazelrc build --config=docker-sandbox {{ '<var>' }}target{{ '</var>' }}
    ```

2.  Run the build and wait for it to complete. The build will run up to four
    times slower than normal due to the Docker sandbox feature.

You may encounter the following error:

```none {:.devsite-disable-click-to-copy}
ERROR: 'docker' is an invalid value for docker spawn strategy.
```

If you do, run the build again with the `--experimental_docker_verbose`  flag.
This flag enables verbose error messages. This error is typically caused by a
faulty Docker installation or lack of permissions to execute it under the
current user account. See the [Docker documentation](https://docs.docker.com/install/linux/linux-postinstall/){: .external}
for more information. If problems persist, skip ahead to [Troubleshooting in a Docker container](#troubleshooting-docker-container).

### Step 2: Resolve detected issues {:#resolve-common-issues}

The following are the most commonly encountered issues and their workarounds.

*  **A file, tool, binary, or resource referenced by the Bazel runfiles tree is
   missing.**. Confirm that all dependencies of the affected targets have been
   [explicitly declared](/concepts/dependencies). See
   [Managing implicit dependencies](/remote/rules#manage-dependencies)
   for more information.

*  **A file, tool, binary, or resource referenced by an absolute path or the `PATH`
   variable is missing.** Confirm that all required tools are installed within
   the toolchain container and use [toolchain rules](/extending/toolchains) to properly
   declare dependencies pointing to the missing resource. See
   [Invoking build tools through toolchain rules](/remote/rules#invoking-build-tools-through-toolchain-rules)
   for more information.

*  **A binary execution fails.** One of the build rules is referencing a binary
   incompatible with the execution environment (the Docker container). See
   [Managing platform-dependent binaries](/remote/rules#manage-binaries)
   for more information. If you cannot resolve the issue, contact [bazel-discuss@google.com](mailto:bazel-discuss@google.com)
   for help.

*  **A file from `@local-jdk` is missing or causing errors.** The Java binaries
   on your local machine are leaking into the build while being incompatible with
   it. Use [`java_toolchain`](/reference/be/java#java_toolchain)
   in your rules and targets instead of `@local_jdk`. Contact [bazel-discuss@google.com](mailto:bazel-discuss@google.com) if you need further help.

*  **Other errors.** Contact [bazel-discuss@google.com](mailto:bazel-discuss@google.com) for help.

## Troubleshooting in a Docker container {:#troubleshooting-docker-container}

With this method, Bazel runs inside a host Docker container, and Bazel's build
actions execute inside individual toolchain containers spawned by the Docker
sandbox feature. The sandbox spawns a brand new toolchain container for each
build action and only one action executes in each toolchain container.

This method provides more granular control of tools installed in the host
environment. By separating the execution of the build from the execution of its
build actions and keeping the installed tooling to a minimum, you can verify
whether your build has any dependencies on the local execution environment.

### Step 1: Build the container {:#build-container}

Note: The commands below are tailored specifically for a  `debian:stretch` base.
For other bases, modify them as necessary.

1.  Create a `Dockerfile` that creates the Docker container and installs Bazel
    with a minimal set of build tools:

    ```
    FROM debian:stretch

    RUN apt-get update && apt-get install -y apt-transport-https curl software-properties-common git gcc gnupg2 g++ openjdk-8-jdk-headless python-dev zip wget vim

    RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -

    RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"

    RUN apt-get update && apt-get install -y docker-ce

    RUN wget https://releases.bazel.build/<latest Bazel version>/release/bazel-<latest Bazel version>-installer-linux-x86_64.sh -O ./bazel-installer.sh && chmod 755 ./bazel-installer.sh

    RUN ./bazel-installer.sh
    ```

2.  Build the container as `bazel_container`:

    ```posix-terminal
    docker build -t bazel_container - < Dockerfile
    ```

### Step 2: Start the container {:#start-container}

Start the Docker container using the command shown below. In the command,
substitute the path to the source code on your host that you want to build.

```posix-terminal
docker run -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /tmp:/tmp \
  -v {{ '<var>' }}your source code directory{{ '</var>' }}:/src \
  -w /src \
  bazel_container \
  /bin/bash
```

This command runs the container as root, mapping the docker socket, and mounting
the `/tmp` directory. This allows Bazel to spawn other Docker containers and to
use directories under `/tmp` to share files with those containers. Your source
code is available at `/src` inside the container.

The command intentionally starts from a `debian:stretch` base container that
includes binaries incompatible with the `rbe-ubuntu16-04` container used as a
toolchain container. If binaries from the local environment are leaking into the
toolchain container, they will cause build errors.

### Step 3: Test the container {:#test-container}

Run the following commands from inside the Docker container to test it:

```posix-terminal
docker ps

bazel version
```

### Step 4: Run the build {:#run-build-step}

Run the build as shown below. The output user is root so that it corresponds to
a directory that is accessible with the same absolute path from inside the host
container in which Bazel runs, from the toolchain containers spawned by the Docker
sandbox feature in which Bazel's build actions are running, and from the local
machine on which the host and action containers run.

```posix-terminal
bazel --output_user_root=/tmp/bazel_docker_root --bazelrc=.bazelrc \ build --config=docker-sandbox {{ '<var>' }}target{{ '</var>' }}
```

### Step 5: Resolve detected issues {:#resolve-build-failures}

You can resolve build failures as follows:

*   If the build fails with an "out of disk space" error, you  can increase this
    limit by starting the host container with the flag `--memory=XX` where `XX`
    is the allocated disk space in gigabytes. This is experimental and may
    result in unpredictable behavior.

*   If the build fails during the analysis or loading phases, one or more of
    your build rules declared in the WORKSPACE file are not compatible with
    remote execution. See [Adapting Bazel Rules for Remote Execution](/remote/rules)
    for possible causes and workarounds.

*   If the build fails for any other reason, see the troubleshooting steps in [Step 2: Resolve detected issues](#start-container).


Project: /_project.yaml
Book: /_book.yaml

# Creating Persistent Workers

{% include "_buttons.html" %}

[Persistent workers](/remote/persistent) can make your build faster. If
you have repeated actions in your build that have a high startup cost or would
benefit from cross-action caching, you may want to implement your own persistent
worker to perform these actions.

The Bazel server communicates with the worker using `stdin`/`stdout`. It
supports the use of protocol buffers or JSON strings.

The worker implementation has two parts:

*   The [worker](#making-worker).
*   The [rule that uses the worker](#rule-uses-worker).

## Making the worker {:#making-worker}

A persistent worker upholds a few requirements:

*   It reads
    [WorkRequests](https://github.com/bazelbuild/bazel/blob/54a547f30fd582933889b961df1d6e37a3e33d85/src/main/protobuf/worker_protocol.proto#L36){: .external}
    from its `stdin`.
*   It writes
    [WorkResponses](https://github.com/bazelbuild/bazel/blob/54a547f30fd582933889b961df1d6e37a3e33d85/src/main/protobuf/worker_protocol.proto#L77){: .external}
    (and only `WorkResponse`s) to its `stdout`.
*   It accepts the `--persistent_worker` flag. The wrapper must recognize the
    `--persistent_worker` command-line flag and only make itself persistent if
    that flag is passed, otherwise it must do a one-shot compilation and exit.

If your program upholds these requirements, it can be used as a persistent
worker!

### Work requests {:#work-requests}

A `WorkRequest` contains a list of arguments to the worker, a list of
path-digest pairs representing the inputs the worker can access (this isn’t
enforced, but you can use this info for caching), and a request id, which is 0
for singleplex workers.

NOTE: While the protocol buffer specification uses "snake case" (`request_id`),
the JSON protocol uses "camel case" (`requestId`). This document uses camel case
in the JSON examples, but snake case when talking about the field regardless of
protocol.

```json
{
  "arguments" : ["--some_argument"],
  "inputs" : [
    { "path": "/path/to/my/file/1", "digest": "fdk3e2ml23d"},
    { "path": "/path/to/my/file/2", "digest": "1fwqd4qdd" }
 ],
  "requestId" : 12
}
```

The optional `verbosity` field can be used to request extra debugging output
from the worker. It is entirely up to the worker what and how to output. Higher
values indicate more verbose output. Passing the `--worker_verbose` flag to
Bazel sets the `verbosity` field to 10, but smaller or larger values can be used
manually for different amounts of output.

The optional `sandbox_dir` field is used only by workers that support
[multiplex sandboxing](/remote/multiplex).

### Work responses {:#work-responses}

A `WorkResponse` contains a request id, a zero or nonzero exit code, and an
output message describing any errors encountered in processing or executing
the request. A worker should capture the `stdout` and `stderr` of any tool it
calls and report them through the `WorkResponse`. Writing it to the `stdout` of
the worker process is unsafe, as it will interfere with the worker protocol.
Writing it to the `stderr` of the worker process is safe, but the result is
collected in a per-worker log file instead of ascribed to individual actions.

```json
{
  "exitCode" : 1,
  "output" : "Action failed with the following message:\nCould not find input
    file \"/path/to/my/file/1\"",
  "requestId" : 12
}
```

As per the norm for protobufs, all fields are optional. However, Bazel requires
the `WorkRequest` and the corresponding `WorkResponse`, to have the same request
id, so the request id must be specified if it is nonzero. This is a valid
`WorkResponse`.

```json
{
  "requestId" : 12,
}
```

A `request_id` of 0 indicates a "singleplex" request, used when this request
cannot be processed in parallel with other requests. The server guarantees that
a given worker receives requests with either only `request_id` 0 or only
`request_id` greater than zero. Singleplex requests are sent in serial, for
example if the server doesn't send another request until it has received a
response (except for cancel requests, see below).

**Notes**

*   Each protocol buffer is preceded by its length in `varint` format (see
    [`MessageLite.writeDelimitedTo()`](https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/MessageLite.html#writeDelimitedTo-java.io.OutputStream-){: .external}.
*   JSON requests and responses are not preceded by a size indicator.
*   JSON requests uphold the same structure as the protobuf, but use standard
    JSON and use camel case for all field names.
*   In order to maintain the same backward and forward compatibility properties
    as protobuf, JSON workers must tolerate unknown fields in these messages,
    and use the protobuf defaults for missing values.
*   Bazel stores requests as protobufs and converts them to JSON using
    [protobuf's JSON format](https://cs.opensource.google/protobuf/protobuf/+/master:java/util/src/main/java/com/google/protobuf/util/JsonFormat.java)

### Cancellation {:#cancellation}

Workers can optionally allow work requests to be cancelled before they finish.
This is particularly useful in connection with dynamic execution, where local
execution can regularly be interrupted by a faster remote execution. To allow
cancellation, add `supports-worker-cancellation: 1` to the
`execution-requirements` field (see below) and set the
`--experimental_worker_cancellation` flag.

A **cancel request** is a `WorkRequest` with the `cancel` field set (and
similarly a **cancel response** is a `WorkResponse` with the `was_cancelled`
field set). The only other field that must be in a cancel request or cancel
response is `request_id`, indicating which request to cancel. The `request_id`
field will be 0 for singleplex workers or the non-0 `request_id` of a previously
sent `WorkRequest` for multiplex workers. The server may send cancel requests
for requests that the worker has already responded to, in which case the cancel
request must be ignored.

Each non-cancel `WorkRequest` message must be answered exactly once, whether or
not it was cancelled. Once the server has sent a cancel request, the worker may
respond with a `WorkResponse` with the `request_id` set and the `was_cancelled`
field set to true. Sending a regular `WorkResponse` is also accepted, but the
`output` and `exit_code` fields will be ignored.

Once a response has been sent for a `WorkRequest`, the worker must not touch the
files in its working directory. The server is free to clean up the files,
including temporary files.

## Making the rule that uses the worker {:#rule-uses-worker}

You'll also need to create a rule that generates actions to be performed by the
worker. Making a Starlark rule that uses a worker is just like
[creating any other rule](https://github.com/bazelbuild/examples/tree/master/rules){: .external}.

In addition, the rule needs to contain a reference to the worker itself, and
there are some requirements for the actions it produces.

### Referring to the worker

The rule that uses the worker needs to contain a field that refers to the worker
itself, so you'll need to create an instance of a `\*\_binary` rule to define
your worker. If your worker is called `MyWorker.Java`, this might be the
associated rule:

```python
java_binary(
    name = "worker",
    srcs = ["MyWorker.Java"],
)
```

This creates the "worker" label, which refers to the worker binary. You'll then
define a rule that *uses* the worker. This rule should define an attribute that
refers to the worker binary.

If the worker binary you built is in a package named "work", which is at the top
level of the build, this might be the attribute definition:

```python
"worker": attr.label(
    default = Label("//work:worker"),
    executable = True,
    cfg = "exec",
)
```

`cfg = "exec"` indicates that the worker should be built to run on your
execution platform rather than on the target platform (i.e., the worker is used
as tool during the build).

### Work action requirements {:#work-action-requirements}

The rule that uses the worker creates actions for the worker to perform. These
actions have a couple of requirements.

*   The *"arguments"* field. This takes a list of strings, all but the last of
    which are arguments passed to the worker upon startup. The last element in
    the "arguments" list is a `flag-file` (@-preceded) argument. Workers read
    the arguments from the specified flagfile on a per-WorkRequest basis. Your
    rule can write non-startup arguments for the worker to this flagfile.

*   The *"execution-requirements"* field, which takes a dictionary containing
    `"supports-workers" : "1"`, `"supports-multiplex-workers" : "1"`, or both.

    The "arguments" and "execution-requirements" fields are required for all
    actions sent to workers. Additionally, actions that should be executed by
    JSON workers need to include `"requires-worker-protocol" : "json"` in the
    execution requirements field. `"requires-worker-protocol" : "proto"` is also
    a valid execution requirement, though it’s not required for proto workers,
    since they are the default.

    You can also set a `worker-key-mnemonic` in the execution requirements. This
    may be useful if you're reusing the executable for multiple action types and
    want to distinguish actions by this worker.

*   Temporary files generated in the course of the action should be saved to the
    worker's directory. This enables sandboxing.

Note: To pass an argument starting with a literal `@`, start the argument with
`@@` instead. If an argument is also an external repository label, it will not
be considered a flagfile argument.

Assuming a rule definition with "worker" attribute described above, in addition
to a "srcs" attribute representing the inputs, an "output" attribute
representing the outputs, and an "args" attribute representing the worker
startup args, the call to `ctx.actions.run` might be:

```python
ctx.actions.run(
  inputs=ctx.files.srcs,
  outputs=[ctx.outputs.output],
  executable=ctx.executable.worker,
  mnemonic="someMnemonic",
  execution_requirements={
    "supports-workers" : "1",
    "requires-worker-protocol" : "json"},
  arguments=ctx.attr.args + ["@flagfile"]
 )
```

For another example, see
[Implementing persistent workers](/remote/persistent#implementation).

## Examples {:#examples}

The Bazel code base uses
[Java compiler workers](https://github.com/bazelbuild/bazel/blob/a4251eab6988d6cf4f5e35681fbe2c1b0abe48ef/src/java_tools/buildjar/java/com/google/devtools/build/buildjar/BazelJavaBuilder.java){: .external},
in addition to an
[example JSON worker](https://github.com/bazelbuild/bazel/blob/c65f768fec9889bbf1ee934c61d0dc061ea54ca2/src/test/java/com/google/devtools/build/lib/worker/ExampleWorker.java){: .external}
that is used in our integration tests.

You can use their
[scaffolding](https://github.com/bazelbuild/bazel/blob/a4251eab6988d6cf4f5e35681fbe2c1b0abe48ef/src/main/java/com/google/devtools/build/lib/worker/WorkRequestHandler.java){: .external}
to make any Java-based tool into a worker by passing in the correct callback.

For an example of a rule that uses a worker, take a look at Bazel's
[worker integration test](https://github.com/bazelbuild/bazel/blob/22b4dbcaf05756d506de346728db3846da56b775/src/test/shell/integration/bazel_worker_test.sh#L106){: .external}.

External contributors have implemented workers in a variety of languages; take a
look at
[Polyglot implementations of Bazel persistent workers](https://github.com/Ubehebe/bazel-worker-examples){: .external}.
You can
[find many more examples on GitHub](https://github.com/search?q=bazel+workrequest&type=Code){: .external}!


Project: /_project.yaml
Book: /_book.yaml

# Remote Caching

{% include "_buttons.html" %}

This page covers remote caching, setting up a server to host the cache, and
running builds using the remote cache.

A remote cache is used by a team of developers and/or a continuous integration
(CI) system to share build outputs. If your build is reproducible, the
outputs from one machine can be safely reused on another machine, which can
make builds significantly faster.

## Overview {:#overview}

Bazel breaks a build into discrete steps, which are called actions. Each action
has inputs, output names, a command line, and environment variables. Required
inputs and expected outputs are declared explicitly for each action.

You can set up a server to be a remote cache for build outputs, which are these
action outputs. These outputs consist of a list of output file names and the
hashes of their contents. With a remote cache, you can reuse build outputs
from another user's build rather than building each new output locally.

To use remote caching:

* Set up a server as the cache's backend
* Configure the Bazel build to use the remote cache
* Use Bazel version 0.10.0 or later

The remote cache stores two types of data:

* The action cache, which is a map of action hashes to action result metadata.
* A content-addressable store (CAS) of output files.

Note that the remote cache additionally stores the stdout and stderr for every
action. Inspecting the stdout/stderr of Bazel thus is not a good signal for
[estimating cache hits](/remote/cache-local).

### How a build uses remote caching {:#remote-caching}

Once a server is set up as the remote cache, you use the cache in multiple
ways:

* Read and write to the remote cache
* Read and/or write to the remote cache except for specific targets
* Only read from the remote cache
* Not use the remote cache at all

When you run a Bazel build that can read and write to the remote cache,
the build follows these steps:

1. Bazel creates the graph of targets that need to be built, and then creates
a list of required actions. Each of these actions has declared inputs
and output filenames.
2. Bazel checks your local machine for existing build outputs and reuses any
that it finds.
3. Bazel checks the cache for existing build outputs. If the output is found,
Bazel retrieves the output. This is a cache hit.
4. For required actions where the outputs were not found, Bazel executes the
actions locally and creates the required build outputs.
5. New build outputs are uploaded to the remote cache.

## Setting up a server as the cache's backend {:#cache-backend}

You need to set up a server to act as the cache's backend. A HTTP/1.1
server can treat Bazel's data as opaque bytes and so many existing servers
can be used as a remote caching backend. Bazel's
[HTTP Caching Protocol](#http-caching) is what supports remote
caching.

You are responsible for choosing, setting up, and maintaining the backend
server that will store the cached outputs. When choosing a server, consider:

* Networking speed. For example, if your team is in the same office, you may
want to run your own local server.
* Security. The remote cache will have your binaries and so needs to be secure.
* Ease of management. For example, Google Cloud Storage is a fully managed service.

There are many backends that can be used for a remote cache. Some options
include:

* [nginx](#nginx)
* [bazel-remote](#bazel-remote)
* [Google Cloud Storage](#cloud-storage)

### nginx {:#nginx}

nginx is an open source web server. With its [WebDAV module], it can be
used as a remote cache for Bazel. On Debian and Ubuntu you can install the
`nginx-extras` package. On macOS nginx is available via Homebrew:

```posix-terminal
brew tap denji/nginx

brew install nginx-full --with-webdav
```

Below is an example configuration for nginx. Note that you will need to
change `/path/to/cache/dir` to a valid directory where nginx has permission
to write and read. You may need to change `client_max_body_size` option to a
larger value if you have larger output files. The server will require other
configuration such as authentication.


Example configuration for `server` section in `nginx.conf`:

```nginx
location /cache/ {
  # The path to the directory where nginx should store the cache contents.
  root /path/to/cache/dir;
  # Allow PUT
  dav_methods PUT;
  # Allow nginx to create the /ac and /cas subdirectories.
  create_full_put_path on;
  # The maximum size of a single file.
  client_max_body_size 1G;
  allow all;
}
```

### bazel-remote {:#bazel-remote}

bazel-remote is an open source remote build cache that you can use on
your infrastructure. It has been successfully used in production at
several companies since early 2018. Note that the Bazel project does
not provide technical support for bazel-remote.

This cache stores contents on disk and also provides garbage collection
to enforce an upper storage limit and clean unused artifacts. The cache is
available as a [docker image] and its code is available on
[GitHub](https://github.com/buchgr/bazel-remote/){: .external}.
Both the REST and gRPC remote cache APIs are supported.

Refer to the [GitHub](https://github.com/buchgr/bazel-remote/){: .external}
page for instructions on how to use it.

### Google Cloud Storage {:#cloud-storage}

[Google Cloud Storage] is a fully managed object store which provides an
HTTP API that is compatible with Bazel's remote caching protocol. It requires
that you have a Google Cloud account with billing enabled.

To use Cloud Storage as the cache:

1. [Create a storage bucket](https://cloud.google.com/storage/docs/creating-buckets){: .external}.
Ensure that you select a bucket location that's closest to you, as network bandwidth
is important for the remote cache.

2. Create a service account for Bazel to authenticate to Cloud Storage. See
[Creating a service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating_a_service_account){: .external}.

3. Generate a secret JSON key and then pass it to Bazel for authentication. Store
the key securely, as anyone with the key can read and write arbitrary data
to/from your GCS bucket.

4. Connect to Cloud Storage by adding the following flags to your Bazel command:
   * Pass the following URL to Bazel by using the flag:
       `--remote_cache=https://storage.googleapis.com{{ '<var>' }}/bucket-name{{ '</var>' }}` where `bucket-name` is the name of your storage bucket.
   * Pass the authentication key using the flag: `--google_credentials={{ '<var>' }}/path/to/your/secret-key{{ '</var>'}}.json`, or
     `--google_default_credentials` to use [Application Authentication](https://cloud.google.com/docs/authentication/production){: .external}.

5. You can configure Cloud Storage to automatically delete old files. To do so, see
[Managing Object Lifecycles](https://cloud.google.com/storage/docs/managing-lifecycles){: .external}.

### Other servers {:#other-servers}

You can set up any HTTP/1.1 server that supports PUT and GET as the cache's
backend. Users have reported success with caching backends such as [Hazelcast](https://hazelcast.com){: .external},
[Apache httpd](http://httpd.apache.org){: .external}, and [AWS S3](https://aws.amazon.com/s3){: .external}.

## Authentication {:#authentication}

As of version 0.11.0 support for HTTP Basic Authentication was added to Bazel.
You can pass a username and password to Bazel via the remote cache URL. The
syntax is `https://username:password@hostname.com:port/path`. Note that
HTTP Basic Authentication transmits username and password in plaintext over the
network and it's thus critical to always use it with HTTPS.

## HTTP caching protocol {:#http-caching}

Bazel supports remote caching via HTTP/1.1. The protocol is conceptually simple:
Binary data (BLOB) is uploaded via PUT requests and downloaded via GET requests.
Action result metadata is stored under the path `/ac/` and output files are stored
under the path `/cas/`.

For example, consider a remote cache running under `http://localhost:8080/cache`.
A Bazel request to download action result metadata for an action with the SHA256
hash `01ba4719...` will look as follows:

```http
GET /cache/ac/01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b HTTP/1.1
Host: localhost:8080
Accept: */*
Connection: Keep-Alive
```

A Bazel request to upload an output file with the SHA256 hash `15e2b0d3...` to
the CAS will look as follows:

```http
PUT /cache/cas/15e2b0d3c33891ebb0f1ef609ec419420c20e320ce94c65fbc8c3312448eb225 HTTP/1.1
Host: localhost:8080
Accept: */*
Content-Length: 9
Connection: Keep-Alive

0x310x320x330x340x350x360x370x380x39
```

## Run Bazel using the remote cache {:#run-remote-cache}

Once a server is set up as the remote cache, to use the remote cache you
need to add flags to your Bazel command. See list of configurations and
their flags below.

You may also need configure authentication, which is specific to your
chosen server.

You may want to add these flags in a `.bazelrc` file so that you don't
need to specify them every time you run Bazel. Depending on your project and
team dynamics, you can add flags to a `.bazelrc` file that is:

* On your local machine
* In your project's workspace, shared with the team
* On the CI system

### Read from and write to the remote cache {:#read-write-remote-cache}

Take care in who has the ability to write to the remote cache. You may want
only your CI system to be able to write to the remote cache.

Use the following flag to read from and write to the remote cache:

```posix-terminal
build --remote_cache=http://{{ '<var>' }}your.host:port{{ '</var>' }}
```

Besides `HTTP`, the following protocols are also supported: `HTTPS`, `grpc`, `grpcs`.

Use the following flag in addition to the one above to only read from the
remote cache:

```posix-terminal
build --remote_upload_local_results=false
```

### Exclude specific targets from using the remote cache {:#targets-remote-cache}

To exclude specific targets from using the remote cache, tag the target with
`no-remote-cache`. For example:

```starlark
java_library(
    name = "target",
    tags = ["no-remote-cache"],
)
```

### Delete content from the remote cache {:#delete-remote-cache}

Deleting content from the remote cache is part of managing your server.
How you delete content from the remote cache depends on the server you have
set up as the cache. When deleting outputs, either delete the entire cache,
or delete old outputs.

The cached outputs are stored as a set of names and hashes. When deleting
content, there's no way to distinguish which output belongs to a specific
build.

You may want to delete content from the cache to:

* Create a clean cache after a cache was poisoned
* Reduce the amount of storage used by deleting old outputs

### Unix sockets {:#unix-sockets}

The remote HTTP cache supports connecting over unix domain sockets. The behavior
is similar to curl's `--unix-socket` flag. Use the following to configure unix
domain socket:

```posix-terminal
   build --remote_cache=http://{{ '<var>' }}your.host:port{{ '</var>' }}
   build --remote_proxy=unix:/{{ '<var>' }}path/to/socket{{ '</var>' }}
```

This feature is unsupported on Windows.

## Disk cache {:#disk-cache}

Bazel can use a directory on the file system as a remote cache. This is
useful for sharing build artifacts when switching branches and/or working
on multiple workspaces of the same project, such as multiple checkouts.
Enable the disk cache as follows:

```posix-terminal
build --disk_cache={{ '<var>' }}path/to/build/cache{{ '</var>' }}
```

You can pass a user-specific path to the `--disk_cache` flag using the `~` alias
(Bazel will substitute the current user's home directory). This comes in handy
when enabling the disk cache for all developers of a project via the project's
checked in `.bazelrc` file.

### Garbage collection {:#disk-cache-gc}

Starting with Bazel 7.4, you can use `--experimental_disk_cache_gc_max_size` and
`--experimental_disk_cache_gc_max_age` to set a maximum size for the disk cache
or for the age of individual cache entries. Bazel will automatically garbage
collect the disk cache while idling between builds; the idle timer can be set
with `--experimental_disk_cache_gc_idle_delay` (defaulting to 5 minutes).

As an alternative to automatic garbage collection, we also provide a [tool](
https://github.com/bazelbuild/bazel/tree/master/src/tools/diskcache) to run a
garbage collection on demand.

## Known issues {:#known-issues}

**Input file modification during a build**

When an input file is modified during a build, Bazel might upload invalid
results to the remote cache. You can enable a change detection with
the `--experimental_guard_against_concurrent_changes` flag. There
are no known issues and it will be enabled by default in a future release.
See [issue #3360] for updates. Generally, avoid modifying source files during a
build.

**Environment variables leaking into an action**

An action definition contains environment variables. This can be a problem for
sharing remote cache hits across machines. For example, environments with
different `$PATH` variables won't share cache hits. Only environment variables
explicitly whitelisted via `--action_env` are included in an action
definition. Bazel's Debian/Ubuntu package used to install `/etc/bazel.bazelrc`
with a whitelist of environment variables including `$PATH`. If you are getting
fewer cache hits than expected, check that your environment doesn't have an old
`/etc/bazel.bazelrc` file.

**Bazel does not track tools outside a workspace**

Bazel currently does not track tools outside a workspace. This can be a
problem if, for example, an action uses a compiler from `/usr/bin/`. Then,
two users with different compilers installed will wrongly share cache hits
because the outputs are different but they have the same action hash. See
[issue #4558](https://github.com/bazelbuild/bazel/issues/4558){: .external} for updates.

**Incremental in-memory state is lost when running builds inside docker containers**
Bazel uses server/client architecture even when running in single docker container.
On the server side, Bazel maintains an in-memory state which speeds up builds.
When running builds inside docker containers such as in CI, the in-memory state is lost
and Bazel must rebuild it before using the remote cache.

## External links {:#external-links}

* **Your Build in a Datacenter:** The Bazel team gave a [talk](https://fosdem.org/2018/schedule/event/datacenter_build/){: .external} about remote caching and execution at FOSDEM 2018.

* **Faster Bazel builds with remote caching: a benchmark:** Nicolò Valigi wrote a [blog post](https://nicolovaligi.com/faster-bazel-remote-caching-benchmark.html){: .external}
in which he benchmarks remote caching in Bazel.

* [Adapting Rules for Remote Execution](/remote/rules)
* [Troubleshooting Remote Execution](/remote/sandbox)
* [WebDAV module](https://nginx.org/en/docs/http/ngx_http_dav_module.html){: .external}
* [Docker image](https://hub.docker.com/r/buchgr/bazel-remote-cache/){: .external}
* [bazel-remote](https://github.com/buchgr/bazel-remote/){: .external}
* [Google Cloud Storage](https://cloud.google.com/storage){: .external}
* [Google Cloud Console](https://cloud.google.com/console){: .external}
* [Bucket locations](https://cloud.google.com/storage/docs/bucket-locations){: .external}
* [Hazelcast](https://hazelcast.com){: .external}
* [Apache httpd](http://httpd.apache.org){: .external}
* [AWS S3](https://aws.amazon.com/s3){: .external}
* [issue #3360](https://github.com/bazelbuild/bazel/issues/3360){: .external}
* [gRPC](https://grpc.io/){: .external}
* [gRPC protocol](https://github.com/bazelbuild/remote-apis/blob/main/build/bazel/remote/execution/v2/remote_execution.proto){: .external}
* [Buildbarn](https://github.com/buildbarn){: .external}
* [Buildfarm](https://github.com/bazelbuild/bazel-buildfarm){: .external}
* [BuildGrid](https://gitlab.com/BuildGrid/buildgrid){: .external}
* [issue #4558](https://github.com/bazelbuild/bazel/issues/4558){: .external}
* [Application Authentication](https://cloud.google.com/docs/authentication/production){: .external}
* [NativeLink](https://github.com/TraceMachina/nativelink){: .external}


Project: /_project.yaml
Book: /_book.yaml

# Debugging Remote Cache Hits for Remote Execution

{% include "_buttons.html" %}

This page describes how to check your cache hit rate and how to investigate
cache misses in the context of remote execution.

This page assumes that you have a build and/or test that successfully
utilizes remote execution, and you want to ensure that you are effectively
utilizing remote cache.

## Checking your cache hit rate {:#check-cache-hits}

In the standard output of your Bazel run, look at the `INFO` line that lists
processes, which roughly correspond to Bazel actions. That line details
where the action was run. Look for the `remote` label, which indicates an action
executed remotely, `linux-sandbox` for actions executed in a local sandbox,
and other values for other execution strategies. An action whose result came
from a remote cache is displayed as `remote cache hit`.

For example:

```none {:.devsite-disable-click-to-copy}
INFO: 11 processes: 6 remote cache hit, 3 internal, 2 remote.
```

In this example there were 6 remote cache hits, and 2 actions did not have
cache hits and were executed remotely. The 3 internal part can be ignored.
It is typically tiny internal actions, such as creating symbolic links. Local
cache hits are not included in this summary. If you are getting 0 processes
(or a number lower than expected), run `bazel clean` followed by your build/test
command.

## Troubleshooting cache hits {:#troubleshooting-cache-hits}

If you are not getting the cache hit rate you are expecting, do the following:

### Ensure re-running the same build/test command produces cache hits {:#rerun-cache-hits}

1. Run the build(s) and/or test(s) that you expect to populate the cache. The
   first time a new build is run on a particular stack, you can expect no remote
   cache hits. As part of remote execution, action results are stored in the
   cache and a subsequent run should pick them up.

2. Run `bazel clean`. This command cleans your local cache, which allows
   you to investigate remote cache hits without the results being masked by
   local cache hits.

3. Run the build(s) and test(s) that you are investigating again (on the same
   machine).

4. Check the `INFO` line for cache hit rate. If you see no processes except
   `remote cache hit` and `internal`, then your cache is being correctly populated and
   accessed. In that case, skip to the next section.

5. A likely source of discrepancy is something non-hermetic in the build causing
   the actions to receive different action keys across the two runs. To find
   those actions, do the following:

   a. Re-run the build(s) or test(s) in question to obtain execution logs:

      ```posix-terminal
      bazel clean

      bazel {{ '<var>' }}--optional-flags{{ '</var>' }} build //{{ '<var>' }}your:target{{ '</var>' }} --execution_log_compact_file=/tmp/exec1.log
      ```

   b. [Compare the execution logs](#compare-logs) between the
      two runs. Ensure that the actions are identical across the two log files.
      Discrepancies provide a clue about the changes that occurred between the
      runs. Update your build to eliminate those discrepancies.

   If you are able to resolve the caching problems and now the repeated run
   produces all cache hits, skip to the next section.

   If your action IDs are identical but there are no cache hits, then something
   in your configuration is preventing caching. Continue with this section to
   check for common problems.

5. Check that all actions in the execution log have `cacheable` set to true. If
   `cacheable` does not appear in the execution log for a give action, that
   means that the corresponding rule may have a `no-cache` tag in its
   definition in the `BUILD` file. Look at the `mnemonic` and `target_label`
   fields in the execution log to help determine where the action is coming
   from.

6. If the actions are identical and `cacheable` but there are no cache hits, it
   is possible that your command line includes `--noremote_accept_cached` which
   would disable cache lookups for a build.

   If figuring out the actual command line is difficult, use the canonical
   command line from the
   [Build Event Protocol](/remote/bep)
   as follows:

   a. Add `--build_event_text_file=/tmp/bep.txt` to your Bazel command to get
    the text version of the log.

   b. Open the text version of the log and search for the
    `structured_command_line` message with `command_line_label: "canonical"`.
    It will list all the options after expansion.

   c. Search for `remote_accept_cached` and check whether it's set to `false`.

   d. If `remote_accept_cached` is `false`, determine where it is being
      set to `false`: either at the command line or in a
      [bazelrc](/run/bazelrc#bazelrc-file-locations) file.

### Ensure caching across machines {:#caching-across-machines}

After cache hits are happening as expected on the same machine, run the
same build(s)/test(s) on a different machine. If you suspect that caching is
not happening across machines, do the following:

1. Make a small modification to your build to avoid hitting existing caches.

2. Run the build on the first machine:

   ```posix-terminal
    bazel clean

    bazel ... build ... --execution_log_compact_file=/tmp/exec1.log
   ```

3. Run the build on the second machine, ensuring the modification from step 1
   is included:

   ```posix-terminal
    bazel clean

    bazel ... build ... --execution_log_compact_file=/tmp/exec2.log
   ```

4. [Compare the execution logs](#compare-logs-the-execution-logs) for the two
    runs. If the logs are not identical, investigate your build configurations
    for discrepancies as well as properties from the host environment leaking
    into either of the builds.

## Comparing the execution logs {:#compare-logs}

The execution log contains records of actions executed during the build.
Each record describes both the inputs (not only files, but also command line
arguments, environment variables, etc) and the outputs of the action. Thus,
examination of the log can reveal why an action was reexecuted.

The execution log can be produced in one of three formats:
compact (`--execution_log_compact_file`),
binary (`--execution_log_binary_file`) or JSON (`--execution_log_json_file`).
The compact format is recommended, as it produces much smaller files with very
little runtime overhead. The following instructions work for any format. You
can also convert between them using the `//src/tools/execlog:converter` tool.

To compare logs for two builds that are not sharing cache hits as expected,
do the following:

1. Get the execution logs from each build and store them as `/tmp/exec1.log` and
   `/tmp/exec2.log`.

2. Download the Bazel source code and build the `//src/tools/execlog:parser`
   tool:

       git clone https://github.com/bazelbuild/bazel.git
       cd bazel
       bazel build //src/tools/execlog:parser

3. Use the `//src/tools/execlog:parser` tool to convert the logs into a
   human-readable text format. In this format, the actions in the second log are
   sorted to match the order in the first log, making a comparison easier.

        bazel-bin/src/tools/execlog/parser \
          --log_path=/tmp/exec1.log \
          --log_path=/tmp/exec2.log \
          --output_path=/tmp/exec1.log.txt \
          --output_path=/tmp/exec2.log.txt

4. Use your favourite text differ to diff `/tmp/exec1.log.txt` and
   `/tmp/exec2.log.txt`.


Project: /_project.yaml
Book: /_book.yaml

# Build Event Protocol Glossary

{% include "_buttons.html" %}

Each BEP event type has its own semantics, minimally documented in
[build\_event\_stream.proto](https://github.com/bazelbuild/bazel/blob/master/src/main/java/com/google/devtools/build/lib/buildeventstream/proto/build_event_stream.proto){: .external}.
The following glossary describes each event type.

## Aborted {:#aborted}

Unlike other events, `Aborted` does not have a corresponding ID type, because
the `Aborted` event *replaces* events of other types. This event indicates that
the build terminated early and the event ID it appears under was not produced
normally. `Aborted` contains an enum and human-friendly description to explain
why the build did not complete.

For example, if a build is evaluating a target when the user interrupts Bazel,
BEP contains an event like the following:

```json
{
  "id": {
    "targetCompleted": {
      "label": "//:foo",
      "configuration": {
        "id": "544e39a7f0abdb3efdd29d675a48bc6a"
      }
    }
  },
  "aborted": {
    "reason": "USER_INTERRUPTED"
  }
}
```

## ActionExecuted {:#actionexecuted}

Provides details about the execution of a specific
[Action](/rules/lib/actions) in a build. By default, this event is
included in the BEP only for failed actions, to support identifying the root cause
of build failures. Users may set the `--build_event_publish_all_actions` flag
to include all `ActionExecuted` events.

## BuildFinished {:#buildfinished}

A single `BuildFinished` event is sent after the command is complete and
includes the exit code for the command. This event provides authoritative
success/failure information.

## BuildMetadata {:#buildmetadata}

Contains the parsed contents of the `--build_metadata` flag. This event exists
to support Bazel integration with other tooling by plumbing external data (such as
identifiers).

## BuildMetrics {:#buildmetrics}

A single `BuildMetrics` event is sent at the end of every command and includes
counters/gauges useful for quantifying the build tool's behavior during the
command. These metrics indicate work actually done and does not count cached
work that is reused.

Note that `memory_metrics` may not be populated if there was no Java garbage
collection during the command's execution. Users may set the
`--memory_profile=/dev/null` option which forces the garbage
collector to run at the end of the command to populate `memory_metrics`.

```json
{
  "id": {
    "buildMetrics": {}
  },
  "buildMetrics": {
    "actionSummary": {
      "actionsExecuted": "1"
    },
    "memoryMetrics": {},
    "targetMetrics": {
      "targetsLoaded": "9",
      "targetsConfigured": "19"
    },
    "packageMetrics": {
      "packagesLoaded": "5"
    },
    "timingMetrics": {
      "cpuTimeInMs": "1590",
      "wallTimeInMs": "359"
    }
  }
}
```

## BuildStarted {:#buildstarted}

The first event in a BEP stream, `BuildStarted` includes metadata describing the
command before any meaningful work begins.

## BuildToolLogs {:#buildtoollogs}

A single `BuildToolLogs` event is sent at the end of a command, including URIs
of files generated by the build tool that may aid in understanding or debugging
build tool behavior. Some information may be included inline.

```json
{
  "id": {
    "buildToolLogs": {}
  },
  "lastMessage": true,
  "buildToolLogs": {
    "log": [
      {
        "name": "elapsed time",
        "contents": "MC4xMjEwMDA="
      },
      {
        "name": "process stats",
        "contents": "MSBwcm9jZXNzOiAxIGludGVybmFsLg=="
      },
      {
        "name": "command.profile.gz",
        "uri": "file:///tmp/.cache/bazel/_bazel_foo/cde87985ad0bfef34eacae575224b8d1/command.profile.gz"
      }
    ]
  }
}
```

## CommandLine {:#commandline}

The BEP contains multiple `CommandLine` events containing representations of all
command-line arguments (including options and uninterpreted arguments).
Each `CommandLine` event has a label in its `StructuredCommandLineId` that
indicates which representation it conveys; three such events appear in the BEP:

* `"original"`: Reconstructed commandline as Bazel received it from the Bazel
  client, without startup options sourced from .rc files.
* `"canonical"`: The effective commandline with .rc files expanded and
  invocation policy applied.
* `"tool"`: Populated from the `--experimental_tool_command_line` option. This
  is useful to convey the command-line of a tool wrapping Bazel through the BEP.
  This could be a base64-encoded `CommandLine` binary protocol buffer message
  which is used directly, or a string which is parsed but not interpreted (as
  the tool's options may differ from Bazel's).

## Configuration {:#configuration}

A `Configuration` event is sent for every [`configuration`](/extending/config)
used in the top-level targets in a build. At least one configuration event is
always be present. The `id` is reused by the `TargetConfigured` and
`TargetComplete` event IDs and is necessary to disambiguate those events in
multi-configuration builds.

```json
{
  "id": {
    "configuration": {
      "id": "a5d130b0966b4a9ca2d32725aa5baf40e215bcfc4d5cdcdc60f5cc5b4918903b"
    }
  },
  "configuration": {
    "mnemonic": "k8-fastbuild",
    "platformName": "k8",
    "cpu": "k8",
    "makeVariable": {
      "COMPILATION_MODE": "fastbuild",
      "TARGET_CPU": "k8",
      "GENDIR": "bazel-out/k8-fastbuild/bin",
      "BINDIR": "bazel-out/k8-fastbuild/bin"
    }
  }
}
```

## ConvenienceSymlinksIdentified {:#conveniencesymlinksidentified}

**Experimental.** If the `--experimental_convenience_symlinks_bep_event`
option is set, a single `ConvenienceSymlinksIdentified` event is produced by
`build` commands to indicate how symlinks in the workspace should be managed.
This enables building tools that invoke Bazel remotely then arrange the local
workspace as if Bazel had been run locally.

```json
{
  "id": {
    "convenienceSymlinksIdentified":{}
  },
  "convenienceSymlinksIdentified": {
    "convenienceSymlinks": [
      {
        "path": "bazel-bin",
        "action": "CREATE",
        "target": "execroot/google3/bazel-out/k8-fastbuild/bin"
      },
      {
        "path": "bazel-genfiles",
        "action": "CREATE",
        "target": "execroot/google3/bazel-out/k8-fastbuild/genfiles"
      },
      {
        "path": "bazel-out",
        "action": "CREATE",
        "target": "execroot/google3/bazel-out"
      }
    ]
  }
}
```

## Fetch {:#fetch}

Indicates that a Fetch operation occurred as a part of the command execution.
Unlike other events, if a cached fetch result is re-used, this event does not
appear in the BEP stream.

## NamedSetOfFiles {:#namedsetoffiles}

`NamedSetOfFiles` events report a structure matching a
[`depset`](/extending/depsets) of files produced during command evaluation.
Transitively included depsets are identified by `NamedSetOfFilesId`.

For more information on interpreting a stream's `NamedSetOfFiles` events, see the
[BEP examples page](/remote/bep-examples#consuming-namedsetoffiles).

## OptionsParsed {:#optionsparsed}

A single `OptionsParsed` event lists all options applied to the command,
separating startup options from command options. It also includes the
[InvocationPolicy](/reference/command-line-reference#flag--invocation_policy), if any.

```json
{
  "id": {
    "optionsParsed": {}
  },
  "optionsParsed": {
    "startupOptions": [
      "--max_idle_secs=10800",
      "--noshutdown_on_low_sys_mem",
      "--connect_timeout_secs=30",
      "--output_user_root=/tmp/.cache/bazel/_bazel_foo",
      "--output_base=/tmp/.cache/bazel/_bazel_foo/a61fd0fbee3f9d6c1e30d54b68655d35",
      "--deep_execroot",
      "--idle_server_tasks",
      "--write_command_log",
      "--nowatchfs",
      "--nofatal_event_bus_exceptions",
      "--nowindows_enable_symlinks",
      "--noclient_debug",
    ],
    "cmdLine": [
      "--enable_platform_specific_config",
      "--build_event_json_file=/tmp/bep.json"
    ],
    "explicitCmdLine": [
      "--build_event_json_file=/tmp/bep.json"
    ],
    "invocationPolicy": {}
  }
}
```

## PatternExpanded {:#patternexpanded}

`PatternExpanded` events indicate the set of all targets that match the patterns
supplied on the commandline. For successful commands, a single event is present
with all patterns in the `PatternExpandedId` and all targets in the
`PatternExpanded` event's *children*. If the pattern expands to any
`test_suite`s the set of test targets included by the `test_suite`. For each
pattern that fails to resolve, BEP contains an additional [`Aborted`](#aborted)
event with a `PatternExpandedId` identifying the pattern.

```json
{
  "id": {
    "pattern": {
      "pattern":["//base:all"]
    }
  },
  "children": [
    {"targetConfigured":{"label":"//base:foo"}},
    {"targetConfigured":{"label":"//base:foobar"}}
  ],
  "expanded": {
    "testSuiteExpansions": {
      "suiteLabel": "//base:suite",
      "testLabels": "//base:foo_test"
    }
  }
}
```

## Progress {:#progress}

Progress events contain the standard output and standard error produced by Bazel
during command execution. These events are also auto-generated as needed to
announce events that have not been announced by a logical "parent" event (in
particular, [NamedSetOfFiles](#namedsetoffiles).)

## TargetComplete {:#targetcomplete}

For each `(target, configuration, aspect)` combination that completes the
execution phase, a `TargetComplete` event is included in BEP. The event contains
the target's success/failure and the target's requested output groups.

```json
{
  "id": {
    "targetCompleted": {
      "label": "//examples/py:bep",
      "configuration": {
        "id": "a5d130b0966b4a9ca2d32725aa5baf40e215bcfc4d5cdcdc60f5cc5b4918903b"
      }
    }
  },
  "completed": {
    "success": true,
    "outputGroup": [
      {
        "name": "default",
        "fileSets": [
          {
            "id": "0"
          }
        ]
      }
    ]
  }
}
```

## TargetConfigured {:#targetconfigured}

For each Target that completes the analysis phase, a `TargetConfigured` event is
included in BEP. This is the authoritative source for a target's "rule kind"
attribute. The configuration(s) applied to the target appear in the announced
*children* of the event.

For example, building with the `--experimental_multi_cpu` options may produce
the following `TargetConfigured` event for a single target with two
configurations:

```json
{
  "id": {
    "targetConfigured": {
      "label": "//starlark_configurations/multi_arch_binary:foo"
    }
  },
  "children": [
    {
      "targetCompleted": {
        "label": "//starlark_configurations/multi_arch_binary:foo",
        "configuration": {
          "id": "c62b30c8ab7b9fc51a05848af9276529842a11a7655c71327ade26d7c894c818"
        }
      }
    },
    {
      "targetCompleted": {
        "label": "//starlark_configurations/multi_arch_binary:foo",
        "configuration": {
          "id": "eae0379b65abce68d54e0924c0ebcbf3d3df26c6e84ef7b2be51e8dc5b513c99"
        }
      }
    }
  ],
  "configured": {
    "targetKind": "foo_binary rule"
  }
}
```

## TargetSummary {:#targetsummary}

For each `(target, configuration)` pair that is executed, a `TargetSummary`
event is included with an aggregate success result encompassing the configured
target's execution and all aspects applied to that configured target.

## TestResult {:#testresult}

If testing is requested, a `TestResult` event is sent for each test attempt,
shard, and run per test. This allows BEP consumers to identify precisely which
test actions failed their tests and identify the test outputs (such as logs,
test.xml files) for each test action.

## TestSummary {:#testsummary}

If testing is requested, a `TestSummary` event is sent for each test `(target,
configuration)`, containing information necessary to interpret the test's
results. The number of attempts, shards and runs per test are included to enable
BEP consumers to differentiate artifacts across these dimensions.  The attempts
and runs per test are considered while producing the aggregate `TestStatus` to
differentiate `FLAKY` tests from `FAILED` tests.

## UnstructuredCommandLine {:#unstructuredcommandline}

Unlike [CommandLine](#commandline), this event carries the unparsed commandline
flags in string form as encountered by the build tool after expanding all
[`.bazelrc`](/run/bazelrc) files and
considering the `--config` flag.

The `UnstructuredCommandLine` event may be relied upon to precisely reproduce a
given command execution.

## WorkspaceConfig {:#workspaceconfig}

A single `WorkspaceConfig` event contains configuration information regarding the
workspace, such as the execution root.

## WorkspaceStatus {:#workspacestatus}

A single `WorkspaceStatus` event contains the result of the [workspace status
command](/docs/user-manual#workspace-status).


Project: /_project.yaml
Book: /_book.yaml

# Finding Non-Hermetic Behavior in WORKSPACE Rules

{% include "_buttons.html" %}

In the following, a host machine is the machine where Bazel runs.

When using remote execution, the actual build and/or test steps are not
happening on the host machine, but are instead sent off to the remote execution
system. However, the steps involved in resolving workspace rules are happening
on the host machine. If your workspace rules access information about the
host machine for use during execution, your build is likely to break due to
incompatibilities between the environments.

As part of [adapting Bazel rules for remote
execution](/remote/rules), you need to find such workspace rules
and fix them. This page describes how to find potentially problematic workspace
rules using the workspace log.


## Finding non-hermetic rules {:#nonhermetic-rules}

[Workspace rules](/reference/be/workspace) allow the developer to add dependencies to
external workspaces, but they are rich enough to allow arbitrary processing to
happen in the process. All related commands are happening locally and can be a
potential source of non-hermeticity. Usually non-hermetic behavior is
introduced through
[`repository_ctx`](/rules/lib/builtins/repository_ctx) which allows interacting
with the host machine.

Starting with Bazel 0.18, you can get a log of some potentially non-hermetic
actions by adding the flag `--experimental_workspace_rules_log_file=[PATH]` to
your Bazel command. Here `[PATH]` is a filename under which the log will be
created.

Things to note:

* the log captures the events as they are executed. If some steps are
  cached, they will not show up in the log, so to get a full result, don't
  forget to run `bazel clean --expunge` beforehand.

* Sometimes functions might be re-executed, in which case the related
  events will show up in the log multiple times.

* Workspace rules  currently only log Starlark events.

  Note: These particular rules do not cause hermiticity concerns as long
  as a hash is specified.

To find what was executed during workspace initialization:

1.  Run `bazel clean --expunge`. This command will clean your local cache and
    any cached repositories, ensuring that all initialization will be re-run.

2.  Add `--experimental_workspace_rules_log_file=/tmp/workspacelog` to your
    Bazel command and run the build.

    This produces a binary proto file listing messages of type
    [WorkspaceEvent](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/bazel/debug/workspace_log.proto?q=WorkspaceEvent)

3.  Download the Bazel source code and navigate to the Bazel folder by using
    the command below. You need the source code to be able to parse the
    workspace log with the
    [workspacelog parser](https://source.bazel.build/bazel/+/master:src/tools/workspacelog/).

    ```posix-terminal
    git clone https://github.com/bazelbuild/bazel.git

    cd bazel
    ```

4.  In the Bazel source code repo, convert the whole workspace log to text.

    ```posix-terminal
    bazel build src/tools/workspacelog:parser

    bazel-bin/src/tools/workspacelog/parser --log_path=/tmp/workspacelog > /tmp/workspacelog.txt
    ```

5.  The output may be quite verbose and include output from built in Bazel
    rules.

    To exclude specific rules from the output, use `--exclude_rule` option.
    For example:

    ```posix-terminal
    bazel build src/tools/workspacelog:parser

    bazel-bin/src/tools/workspacelog/parser --log_path=/tmp/workspacelog \
        --exclude_rule "//external:local_config_cc" \
        --exclude_rule "//external:dep" > /tmp/workspacelog.txt
    ```

5.  Open `/tmp/workspacelog.txt` and check for unsafe operations.

The log consists of
[WorkspaceEvent](https://source.bazel.build/bazel/+/master:src/main/java/com/google/devtools/build/lib/bazel/debug/workspace_log.proto?q=WorkspaceEvent)
messages outlining certain potentially non-hermetic actions performed on a
[`repository_ctx`](/rules/lib/builtins/repository_ctx).

The actions that have been highlighted as potentially non-hermetic are as follows:

* `execute`: executes an arbitrary command on the host environment. Check if
  these may introduce any dependencies on the host environment.

* `download`, `download_and_extract`: to ensure hermetic builds, make sure
  that sha256 is specified

* `file`, `template`: this is not non-hermetic in itself, but may be a mechanism
  for introducing dependencies on the host environment into the repository.
  Ensure that you understand where the input comes from, and that it does not
  depend on the host environment.

* `os`: this is not non-hermetic in itself, but an easy way to get dependencies
  on the host environment. A hermetic build would generally not call this.
  In evaluating whether your usage is hermetic, keep in mind that this is
  running on the host and not on the workers. Getting environment specifics
  from the host is generally not a good idea for remote builds.

* `symlink`: this is normally safe, but look for red flags. Any symlinks to
  outside the repository or to an absolute path would cause problems on the
  remote worker. If the symlink is created based on host machine properties
  it would probably be problematic as well.

* `which`: checking for programs installed on the host is usually problematic
  since the workers may have different configurations.


Project: /_project.yaml
Book: /_book.yaml

# Debugging Remote Cache Hits for Local Execution

{% include "_buttons.html" %}

This page describes how to investigate cache misses in the context of local
execution.

This page assumes that you have a build and/or test that successfully builds
locally and is set up to utilize remote caching, and that you want to ensure
that the remote cache is being effectively utilized.

For tips on how to check your cache hit rate and how to compare the execution
logs between two Bazel invocations, see
[Debugging Remote Cache Hits for Remote Execution](/remote/cache-remote).
Everything presented in that guide also applies to remote caching with local
execution. However, local execution presents some additional challenges.

## Checking your cache hit rate {:#cache-hits}

Successful remote cache hits will show up in the status line, similar to
[Cache Hits rate with Remote
Execution](/remote/cache-remote#check-cache-hits).

In the standard output of your Bazel run, you will see something like the
following:

```none {:.devsite-disable-click-to-copy}
   INFO: 7 processes: 3 remote cache hit, 4 linux-sandbox.
```

This means that out of 7 attempted actions, 3 got a remote cache hit and 4
actions did not have cache hits and were executed locally using `linux-sandbox`
strategy. Local cache hits are not included in this summary. If you are getting
0 processes (or a number lower than expected), run `bazel clean` followed by
your build/test command.

## Troubleshooting cache hits {:#troubleshooting-cache-hits}

If you are not getting the cache hit rate you are expecting, do the following:

### Ensure successful communication with the remote endpoint {:#remote-endpoint-success}

To ensure your build is successfully communicating with the remote cache, follow
the steps in this section.

1. Check your output for warnings

   With remote execution, a failure to talk to the remote endpoint would fail
   your build. On the other hand, a cacheable local build would not fail if it
   cannot cache. Check the output of your Bazel invocation for warnings, such
   as:

   ```none {:.devsite-disable-click-to-copy}
      WARNING: Error reading from the remote cache:
   ```


   or

   ```none {:.devsite-disable-click-to-copy}
      WARNING: Error writing to the remote cache:
   ```


   Such warnings will be followed by the error message detailing the connection
   problem that should help you debug: for example, mistyped endpoint name or
   incorrectly set credentials. Find and address any such errors. If the error
   message you see does not give you enough information, try adding
   `--verbose_failures`.

2. Follow the steps from [Troubleshooting cache hits for remote
   execution](/remote/cache-remote#troubleshooting_cache_hits) to
   ensure that your cache-writing Bazel invocations are able to get cache hits
   on the same machine and across machines.

3. Ensure your cache-reading Bazel invocations can get cache hits.

   a. Since cache-reading Bazel invocations will have a different command-line set
      up, take additional care to ensure that they are properly set up to
      communicate with the remote cache. Ensure the `--remote_cache` flag is set
      and there are no warnings in the output.

   b. Ensure your cache-reading Bazel invocations build the same targets as the
      cache-writing Bazel invocations.

   c. Follow the same steps as to [ensure caching across
      machines](/remote/cache-remote#caching-across-machines),
      to ensure caching from your cache-writing Bazel invocation to your
      cache-reading Bazel invocation.


Project: /_project.yaml
Book: /_book.yaml

# Adapting Bazel Rules for Remote Execution

{% include "_buttons.html" %}

This page is intended for Bazel users writing custom build and test rules
who want to understand the requirements for Bazel rules in the context of
remote execution.

Remote execution allows Bazel to execute actions on a separate platform, such as
a datacenter. Bazel uses a
[gRPC protocol](https://github.com/bazelbuild/remote-apis/blob/main/build/bazel/remote/execution/v2/remote_execution.proto){: .external}
for its remote execution. You can try remote execution with
[bazel-buildfarm](https://github.com/bazelbuild/bazel-buildfarm){: .external},
an open-source project that aims to provide a distributed remote execution
platform.

This page uses the following terminology when referring to different
environment types or *platforms*:

*   **Host platform** - where Bazel runs.
*   **Execution platform** - where Bazel actions run.
*   **Target platform** - where the build outputs (and some actions) run.

## Overview {:#overview}

When configuring a Bazel build for remote execution, you must follow the
guidelines described in this page to ensure the build executes remotely
error-free. This is due to the nature of remote execution, namely:

*   **Isolated build actions.** Build tools do not retain state and dependencies
    cannot leak between them.

*   **Diverse execution environments.** Local build configuration is not always
    suitable for remote execution environments.

This page describes the issues that can arise when implementing custom Bazel
build and test rules for remote execution and how to avoid them. It covers the
following topics:

*  [Invoking build tools through toolchain rules](#toolchain-rules)
*  [Managing implicit dependencies](#manage-dependencies)
*  [Managing platform-dependent binaries](#manage-binaries)
*  [Managing configure-style WORKSPACE rules](#manage-workspace-rules)

## Invoking build tools through toolchain rules {:#toolchain-rules}

A Bazel toolchain rule is a configuration provider that tells a build rule what
build tools, such as compilers and linkers, to use and how to configure them
using parameters defined by the rule's creator. A toolchain rule allows build
and test rules to invoke build tools in a predictable, preconfigured manner
that's compatible with remote execution. For example, use a toolchain rule
instead of invoking build tools via the `PATH`, `JAVA_HOME`, or other local
variables that may not be set to equivalent values (or at all) in the remote
execution environment.

Toolchain rules currently exist for Bazel build and test rules for
[Scala](https://github.com/bazelbuild/rules_scala/blob/master/scala/scala_toolch
ain.bzl){: .external},
[Rust](https://github.com/bazelbuild/rules_rust/blob/main/rust/toolchain.bzl){: .external},
and [Go](https://github.com/bazelbuild/rules_go/blob/master/go/toolchains.rst){: .external},
and new toolchain rules are under way for other languages and tools such as
[bash](https://docs.google.com/document/d/e/2PACX-1vRCSB_n3vctL6bKiPkIa_RN_ybzoAccSe0ic8mxdFNZGNBJ3QGhcKjsL7YKf-ngVyjRZwCmhi_5KhcX/pub){: .external}.
If a toolchain rule does not exist for the tool your rule uses, consider
[creating a toolchain rule](/extending/toolchains#creating-a-toolchain-rule).

## Managing implicit dependencies {:#manage-dependencies}

If a build tool can access dependencies across build actions, those actions will
fail when remotely executed because each remote build action is executed
separately from others. Some build tools retain state across build actions and
access dependencies that have not been explicitly included in the tool
invocation, which will cause remotely executed build actions to fail.

For example, when Bazel instructs a stateful compiler to locally build _foo_,
the compiler retains references to foo's build outputs. When Bazel then
instructs the compiler to build _bar_, which depends on _foo_, without
explicitly stating that dependency in the BUILD file for inclusion in the
compiler invocation, the action executes successfully as long as the same
compiler instance executes for both actions (as is typical for local execution).
However, since in a remote execution scenario each build action executes a
separate compiler instance, compiler state and _bar_'s implicit dependency on
_foo_ will be lost and the build will fail.

To help detect and eliminate these dependency problems, Bazel 0.14.1 offers the
local Docker sandbox, which has the same restrictions for dependencies as remote
execution. Use the sandbox to prepare your build for remote execution by
identifying and resolving dependency-related build errors. See [Troubleshooting Bazel Remote Execution with Docker Sandbox](/remote/sandbox)
for more information.

## Managing platform-dependent binaries {:#manage-binaries}

Typically, a binary built on the host platform cannot safely execute on an
arbitrary remote execution platform due to potentially mismatched dependencies.
For example, the SingleJar binary supplied with Bazel targets the host platform.
However, for remote execution, SingleJar must be compiled as part of the process
of building your code so that it targets the remote execution platform. (See the
[target selection logic](https://github.com/bazelbuild/bazel/blob/130aeadfd660336572c3da397f1f107f0c89aa8d/tools/jdk/BUILD#L115){: .external}.)

Do not ship binaries of build tools required by your build with your source code
unless you are sure they will safely run in your execution platform. Instead, do
one of the following:

*   Ship or externally reference the source code for the tool so that it can be
    built for the remote execution platform.

*   Pre-install the tool into the remote execution environment (for example, a
    toolchain container) if it's stable enough and use toolchain rules to run it
    in your build.

## Managing configure-style WORKSPACE rules {:#manage-workspace-rules}

Bazel's `WORKSPACE` rules can be used for probing the host platform for tools
and libraries required by the build, which, for local builds, is also Bazel's
execution platform. If the build explicitly depends on local build tools and
artifacts, it will fail during remote execution if the remote execution platform
is not identical to the host platform.

The following actions performed by `WORKSPACE` rules are not compatible with
remote execution:

*   **Building binaries.** Executing compilation actions in `WORKSPACE` rules
    results in binaries that are incompatible with the remote execution platform
    if different from the host platform.

*   **Installing `pip` packages.** `pip` packages  installed via `WORKSPACE`
    rules require that their dependencies be pre-installed on the host platform.
    Such packages, built specifically for the host platform, will be
    incompatible with the remote execution platform if different from the host
    platform.

*   **Symlinking to local tools or artifacts.** Symlinks to tools or libraries
    installed on the host platform created via `WORKSPACE` rules will cause the
    build to fail on the remote execution platform as Bazel will not be able to
    locate them. Instead, create symlinks using standard build actions so that
    the symlinked tools and libraries are accessible from Bazel's `runfiles`
    tree. Do not use [`repository_ctx.symlink`](/rules/lib/builtins/repository_ctx#symlink)
    to symlink target files outside of the external repo directory.

*   **Mutating the host platform.** Avoid creating files outside of the Bazel
    `runfiles` tree, creating environment variables, and similar actions, as
     they may behave unexpectedly on the remote execution platform.

To help find potential non-hermetic behavior you can use [Workspace rules log](/remote/workspace).

If an external dependency executes specific operations dependent on the host
platform, you should split those operations between `WORKSPACE` and build
rules as follows:

*   **Platform inspection and dependency enumeration.** These operations are
    safe to execute locally via `WORKSPACE` rules, which can check which
    libraries are installed, download packages that must be built, and prepare
    required artifacts for compilation. For remote execution, these rules must
    also support using pre-checked artifacts to provide the information that
    would normally be obtained during host platform inspection. Pre-checked
    artifacts allow Bazel to describe dependencies as if they were local. Use
    conditional statements or the `--override_repository` flag for this.

*   **Generating or compiling target-specific artifacts and platform mutation**.
    These operations must be executed via regular build rules. Actions that
    produce target-specific artifacts for external dependencies must execute
    during the build.

To more easily generate pre-checked artifacts for remote execution, you can use
`WORKSPACE` rules to emit generated files. You can run those rules on each new
execution environment, such as inside each toolchain container, and check the
outputs of your remote execution build in to your source repo to reference.

For example, for Tensorflow's rules for [`cuda`](https://github.com/tensorflow/tensorflow/blob/master/third_party/gpus/cuda_configure.bzl){: .external}
and [`python`](https://github.com/tensorflow/tensorflow/blob/master/third_party/py/python_configure.bzl){: .external},
the `WORKSPACE` rules produce the following [`BUILD files`](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/tools/third_party/toolchains/cpus/py){: .external}.
For local execution, files produced by checking the host environment are used.
For remote execution, a [conditional statement](https://github.com/tensorflow/tensorflow/blob/master/third_party/py/python_configure.bzl#L304){: .external}
on an environment variable allows the rule to use files that are checked into
the repo.

The `BUILD` files declare [`genrules`](https://github.com/tensorflow/tensorflow/blob/master/third_party/py/python_configure.bzl#L84){: .external}
that can run both locally and remotely, and perform the necessary processing
that was previously done via `repository_ctx.symlink` as shown [here](https://github.com/tensorflow/tensorflow/blob/d1ba01f81d8fa1d0171ba9ce871599063d5c7eb9/third_party/gpus/cuda_configure.bzl#L730){: .external}.


Project: /_project.yaml
Book: /_book.yaml

# Remote Execution Overview

{% include "_buttons.html" %}

This page covers the benefits, requirements, and options for running Bazel
with remote execution.

By default, Bazel executes builds and tests on your local machine. Remote
execution of a Bazel build allows you to distribute build and test actions
across multiple machines, such as a datacenter.

Remote execution provides the following benefits:

*  Faster build and test execution through scaling of nodes available
   for parallel actions
*  A consistent execution environment for a development team
*  Reuse of build outputs across a development team

Bazel uses an open-source
[gRPC protocol](https://github.com/bazelbuild/remote-apis){: .external}
to allow for remote execution and remote caching.

For a list of commercially supported remote execution services as well as
self-service tools, see
[Remote Execution Services](https://www.bazel.build/remote-execution-services.html){: .external}

## Requirements {:#requirements}

Remote execution of Bazel builds imposes a set of mandatory configuration
constraints on the build. For more information, see
[Adapting Bazel Rules for Remote Execution](/remote/rules).


Project: /_project.yaml
Book: /_book.yaml

# Configuring Bazel CI to Test Rules for Remote Execution

{% include "_buttons.html" %}

This page is for owners and maintainers of Bazel rule repositories. It
describes how to configure the Bazel Continuous Integration (CI) system for
your repository to test your rules for compatibility against a remote execution
scenario. The instructions on this page apply to projects stored in
GitHub repositories.

## Prerequisites {:#prerequisites}

Before completing the steps on this page, ensure the following:

*   Your GitHub repository is part of the
    [Bazel GitHub organization](https://github.com/bazelbuild){: .external}.
*   You have configured Buildkite for your repository as described in
    [Bazel Continuous Integration](https://github.com/bazelbuild/continuous-integration/tree/master/buildkite){: .external}.

## Setting up the Bazel CI for testing {:#bazel-ci-testing}

1.  In your `.bazelci/presubmit.yml` file, do the following:

    a.  Add a config named `rbe_ubuntu1604`.

    b.  In the `rbe_ubuntu1604` config, add the build and test targets you want to test against remote execution.

2.  Add the[`bazel-toolchains`](https://github.com/bazelbuild/bazel-toolchains){: .external}
    GitHub repository to your `WORKSPACE` file, pinned to the
    [latest release](https://releases.bazel.build/bazel-toolchains.html). Also
    add an `rbe_autoconfig` target with name `buildkite_config`. This example
    creates toolchain configuration for remote execution with BuildKite CI
    for `rbe_ubuntu1604`.

```posix-terminal
load("@bazel_toolchains//rules:rbe_repo.bzl", "rbe_autoconfig")

rbe_autoconfig(name = "buildkite_config")
```

3.  Send a pull request with your changes to the `presubmit.yml` file. (See
    [example pull request](https://github.com/bazelbuild/rules_rust/commit/db141526d89d00748404856524cedd7db8939c35){: .external}.)

4.  To view build results, click **Details** for the RBE (Ubuntu
    16.04) pull request check in GitHub, as shown in the figure below. This link
    becomes available after the pull request has been merged and the CI tests
    have run. (See
    [example results](https://source.cloud.google.com/results/invocations/375e325c-0a05-47af-87bd-fed1363e0333){: .external}.)

    ![Example results](/docs/images/rbe-ci-1.png "Example results")

5.  (Optional) Set the **bazel test (RBE (Ubuntu 16.04))** check as a test
    required to pass before merging in your branch protection rule. The setting
    is located in GitHub in **Settings > Branches > Branch protection rules**,
    as shown in the following figure.

    ![Branch protection rules settings](/docs/images/rbe-ci-2.png "Branch protection rules")

## Troubleshooting failed builds and tests {:#troubleshooting-failed-builds}

If your build or tests fail, it's likely due to the following:

*   **Required build or test tools are not installed in the default container.**
    Builds using the `rbe_ubuntu1604` config run by default inside an
    [`rbe-ubuntu16-04`](https://console.cloud.google.com/marketplace/details/google/rbe-ubuntu16-04){: .external}
    container, which includes tools common to many Bazel builds. However, if
    your rules require tools not present in the default container, you must
    create a custom container based on the
    [`rbe-ubuntu16-04`](https://console.cloud.google.com/marketplace/details/google/rbe-ubuntu16-04){: .external}
    container and include those tools as described later.

*   **Build or test targets are using rules that are incompatible with remote
    execution.** See
    [Adapting Bazel Rules for Remote Execution](/remote/rules) for
    details about compatibility with remote execution.

## Using a custom container in the rbe_ubuntu1604 CI config {:#custom-container}

The `rbe-ubuntu16-04` container is publicly available at the following URL:

```
http://gcr.io/cloud-marketplace/google/rbe-ubuntu16-04
```

You can pull it directly from Container Registry or build it from source. The
next sections describe both options.

Before you begin, make sure you have installed `gcloud`, `docker`, and `git`.
If you are building the container from source, you must also install the latest
version of Bazel.

### Pulling the rbe-ubuntu16-04 from Container Registry {:#container-registry}

To pull the `rbe-ubuntu16-04` container from Container Registry, run the
following command:

```posix-terminal
gcloud docker -- pull gcr.io/cloud-marketplace/google/rbe-ubuntu16-04@sha256:{{ '<var>' }}sha256-checksum{{ '</var>' }}
```

Replace {{ '<var>' }}sha256-checksum{{ '</var>' }} with the SHA256 checksum value for
[the latest container](https://console.cloud.google.com/gcr/images/cloud-marketplace/GLOBAL/google/rbe-ubuntu16-04){: .external}.

### Building the rbe-ubuntu16-04 container from source {:#container-source}

To build the `rbe-ubuntu16-04` container from source, do the following:

1.  Clone the `bazel-toolchains` repository:

    ```posix-terminal
    git clone https://github.com/bazelbuild/bazel-toolchains
    ```

2.  Set up toolchain container targets and build the container as explained in
    [Toolchain Containers](https://github.com/bazelbuild/bazel-toolchains/tree/master/container){: .external}.

3.  Pull the freshly built container:

    ```posix-terminal
gcloud docker -- pull gcr.io/{{ '<var>' }}project-id{{ '</var>' }}/{{ '<var>' }}custom-container-name{{ '</var>' }}{{ '<var>' }}sha256-checksum{{ '</var>' }}
    ```

### Running the custom container {:#run-custom-container}

To run the custom container, do one of the following:

*   If you pulled the container from Container Registry, run the following
    command:

    ```posix-terminal
    docker run -it gcr.io/cloud-marketplace/google/rbe-ubuntu16-04@sha256:{{ '<var>' }}sha256-checksum{{ '</var>'}}/bin/bash
    ```

    Replace `sha256-checksum` with the SHA256 checksum value for the
    [latest container](https://console.cloud.google.com/gcr/images/cloud-marketplace/GLOBAL/google/rbe-ubuntu16-04){: .external}.

*   If you built the container from source, run the following command:

    ```posix-terminal
    docker run -it gcr.io/{{ '<var>' }}project-id{{ '</var>' }}/{{ '<var>' }}custom-container-name{{ '</var>' }}@sha256:{{ '<var>' }}sha256sum{{ '</var>' }} /bin/bash
    ```

### Adding resources to the custom container {:#add-resources-container}

Use a [`Dockerfile`](https://docs.docker.com/engine/reference/builder/){: .external} or
[`rules_docker`](https://github.com/bazelbuild/rules_docker){: .external} to add resources or
alternate versions of the original resources to the `rbe-ubuntu16-04` container.
If you are new to Docker, read the following:

*   [Docker for beginners](https://github.com/docker/labs/tree/master/beginner){: .external}
*   [Docker Samples](https://docs.docker.com/samples/){: .external}

For example, the following `Dockerfile` snippet installs `{{ '<var>' }}my_tool_package{{ '</var>' }}`:

```
FROM gcr.io/cloud-marketplace/google/rbe-ubuntu16-04@sha256:{{ '<var>' }}sha256-checksum{{ '</var>' }}
RUN apt-get update && yes | apt-get install -y {{ '<var>' }}my_tool_package{{ '</var>' }}
```

### Pushing the custom container to Container Registry {:#push-container-registry}

Once you have customized the container, build the container image and push it to
Container Registry as follows:

1. Build the container image:

    ```posix-terminal
    docker build -t {{ '<var>' }}custom-container-name{{ '</var>' }}.

    docker tag {{ '<var>' }}custom-container-name{{ '</var>' }} gcr.io/{{ '<var>' }}project-id{{ '</var>' }}/{{ '<var>' }}custom-container-name{{ '</var>' }}
    ```

2.  Push the container image to Container Registry:

    ```posix-terminal
    gcloud docker -- push gcr.io/{{ '<var>' }}project-id{{ '</var>' }}/{{ '<var>' }}custom-container-name{{ '</var>' }}
    ```

3.  Navigate to the following URL to verify the container has been pushed:

    https://console.cloud.google.com/gcr/images/{{ '<var>' }}project-id{{ '</var>' }}/GLOBAL/{{ '<var>' }}custom-container-name{{ '</var>' }}

4.  Take note of the SHA256 checksum of your custom container. You will need to
    provide it in your build platform definition later.

5.  Configure the container for public access as described in  publicly
    accessible as explained in
    [Serving images publicly](https://cloud.google.com/container-registry/docs/access-control#serving_images_publicly){: .external}.

    For more information, see
    [Pushing and Pulling Images](https://cloud.google.com/container-registry/docs/pushing-and-pulling){: .external}.


### Specifying the build platform definition {:#platform-definition}

You must include a [Bazel platform](/extending/platforms) configuration in your
custom toolchain configuration, which allows Bazel to select a toolchain
appropriate to the desired hardware/software platform. To generate
automatically a valid platform, you can add  to your `WORKSPACE` an
`rbe_autoconfig` target with name `buildkite_config` which includes additional
attrs to select your custom container. For details on this setup, read
the up-to-date documentation for [`rbe_autoconfig`](https://github.com/bazelbuild/bazel-toolchains/blob/master/rules/rbe_repo.bzl){: .external}.


Project: /_project.yaml
Book: /_book.yaml

# Output Directory Layout

{% include "_buttons.html" %}

This page covers requirements and layout for output directories.

## Requirements {:#requirements}

Requirements for an output directory layout:

* Doesn't collide if multiple users are building on the same box.
* Supports building in multiple workspaces at the same time.
* Supports building for multiple target configurations in the same workspace.
* Doesn't collide with any other tools.
* Is easy to access.
* Is easy to clean, even selectively.
* Is unambiguous, even if the user relies on symbolic links when changing into
  their client directory.
* All the build state per user should be underneath one directory ("I'd like to
  clean all the .o files from all my clients.")

## Current layout {:#layout}

The solution that's currently implemented:

* Bazel must be invoked from a directory containing a repo boundary file, or a
  subdirectory thereof. In other words, Bazel must be invoked from inside a
  [repository](../external/overview#repository). Otherwise, an error is
  reported.
* The _outputRoot_ directory defaults to `~/.cache/bazel` on Linux,
  `/private/var/tmp` on macOS, and on Windows it defaults to `%HOME%` if
  set, else `%USERPROFILE%` if set, else the result of calling
  `SHGetKnownFolderPath()` with the `FOLDERID_Profile` flag set. If the
  environment variable `$XDG_CACHE_HOME` is set on either Linux or
  macOS, the value `${XDG_CACHE_HOME}/bazel` will override the default.
  If the environment variable `$TEST_TMPDIR` is set, as in a test of Bazel
  itself, then that value overrides any defaults.
* The Bazel user's build state is located beneath `outputRoot/_bazel_$USER`.
  This is called the _outputUserRoot_ directory.
* Beneath the `outputUserRoot` directory there is an `install` directory, and in
  it is an `installBase` directory whose name is the MD5 hash of the Bazel
  installation manifest.
* Beneath the `outputUserRoot` directory, an `outputBase` directory
  is also created whose name is the MD5 hash of the path name of the workspace
  root. So, for example, if Bazel is running in the workspace root
  `/home/user/src/my-project` (or in a directory symlinked to that one), then
  an output base directory is created called:
  `/home/user/.cache/bazel/_bazel_user/7ffd56a6e4cb724ea575aba15733d113`. You
  can also run `echo -n $(pwd) | md5sum` in the workspace root to get the MD5.
* You can use Bazel's `--output_base` startup option to override the default
  output base directory. For example,
  `bazel --output_base=/tmp/bazel/output build x/y:z`.
* You can also use Bazel's `--output_user_root` startup option to override the
  default install base and output base directories. For example:
  `bazel --output_user_root=/tmp/bazel build x/y:z`.

The symlinks for "bazel-&lt;workspace-name&gt;", "bazel-out", "bazel-testlogs",
and "bazel-bin" are put in the workspace directory; these symlinks point to some
directories inside a target-specific directory inside the output directory.
These symlinks are only for the user's convenience, as Bazel itself does not
use them. Also, this is done only if the workspace root is writable.

## Layout diagram {:#layout-diagram}

The directories are laid out as follows:

<pre>
&lt;workspace-name&gt;/                         <== The workspace root
  bazel-my-project => <..._main>          <== Symlink to execRoot
  bazel-out => <...bazel-out>             <== Convenience symlink to outputPath
  bazel-bin => <...bin>                   <== Convenience symlink to most recent written bin dir $(BINDIR)
  bazel-testlogs => <...testlogs>         <== Convenience symlink to the test logs directory

/home/user/.cache/bazel/                  <== Root for all Bazel output on a machine: outputRoot
  _bazel_$USER/                           <== Top level directory for a given user depends on the user name:
                                              outputUserRoot
    install/
      fba9a2c87ee9589d72889caf082f1029/   <== Hash of the Bazel install manifest: installBase
        _embedded_binaries/               <== Contains binaries and scripts unpacked from the data section of
                                              the bazel executable on first run (such as helper scripts and the
                                              main Java file BazelServer_deploy.jar)
    7ffd56a6e4cb724ea575aba15733d113/     <== Hash of the client's workspace root (such as
                                              /home/user/src/my-project): outputBase
      action_cache/                       <== Action cache directory hierarchy
                                              This contains the persistent record of the file
                                              metadata (timestamps, and perhaps eventually also MD5
                                              sums) used by the FilesystemValueChecker.
      command.log                         <== A copy of the stdout/stderr output from the most
                                              recent bazel command.
      external/                           <== The directory that remote repositories are
                                              downloaded/symlinked into.
      server/                             <== The Bazel server puts all server-related files (such
                                              as socket file, logs, etc) here.
        jvm.out                           <== The debugging output for the server.
      execroot/                           <== The working directory for all actions. For special
                                              cases such as sandboxing and remote execution, the
                                              actions run in a directory that mimics execroot.
                                              Implementation details, such as where the directories
                                              are created, are intentionally hidden from the action.
                                              Every action can access its inputs and outputs relative
                                              to the execroot directory.
        _main/                            <== Working tree for the Bazel build & root of symlink forest: execRoot
          _bin/                           <== Helper tools are linked from or copied to here.

          bazel-out/                      <== All actual output of the build is under here: outputPath
            _tmp/actions/                 <== Action output directory. This contains a file with the
                                              stdout/stderr for every action from the most recent
                                              bazel run that produced output.
            local_linux-fastbuild/        <== one subdirectory per unique target BuildConfiguration instance;
                                              this is currently encoded
              bin/                        <== Bazel outputs binaries for target configuration here: $(BINDIR)
                foo/bar/_objs/baz/        <== Object files for a cc_* rule named //foo/bar:baz
                  foo/bar/baz1.o          <== Object files from source //foo/bar:baz1.cc
                  other_package/other.o   <== Object files from source //other_package:other.cc
                foo/bar/baz               <== foo/bar/baz might be the artifact generated by a cc_binary named
                                              //foo/bar:baz
                foo/bar/baz.runfiles/     <== The runfiles symlink farm for the //foo/bar:baz executable.
                  MANIFEST
                  _main/
                    ...
              genfiles/                   <== Bazel puts generated source for the target configuration here:
                                              $(GENDIR)
                foo/bar.h                     such as foo/bar.h might be a headerfile generated by //foo:bargen
              testlogs/                   <== Bazel internal test runner puts test log files here
                foo/bartest.log               such as foo/bar.log might be an output of the //foo:bartest test with
                foo/bartest.status            foo/bartest.status containing exit status of the test (such as
                                              PASSED or FAILED (Exit 1), etc)
            host/                         <== BuildConfiguration for build host (user's workstation), for
                                              building prerequisite tools, that will be used in later stages
                                              of the build (ex: Protocol Compiler)
        &lt;packages&gt;/                       <== Packages referenced in the build appear as if under a regular workspace
</pre>

The layout of the \*.runfiles directories is documented in more detail in the places pointed to by RunfilesSupport.

## `bazel clean`

`bazel clean` does an `rm -rf` on the `outputPath` and the `action_cache`
directory. It also removes the workspace symlinks. The `--expunge` option
will clean the entire outputBase.


Project: /_project.yaml
Book: /_book.yaml

# Build Event Protocol

{% include "_buttons.html" %}

The [Build Event
Protocol](https://github.com/bazelbuild/bazel/blob/master/src/main/java/com/google/devtools/build/lib/buildeventstream/proto/build_event_stream.proto){: .external}
(BEP) allows third-party programs to gain insight into a Bazel invocation. For
example, you could use the BEP to gather information for an IDE
plugin or a dashboard that displays build results.

The protocol is a set of [protocol
buffer](https://developers.google.com/protocol-buffers/){: .external} messages with some
semantics defined on top of it. It includes information about build and test
results, build progress, the build configuration and much more. The BEP is
intended to be consumed programmatically and makes parsing Bazel’s
command line output a thing of the past.

The Build Event Protocol represents information about a build as events. A
build event is a protocol buffer message consisting of a build event identifier,
a set of child event identifiers, and a payload.

*  __Build Event Identifier:__ Depending on the kind of build event, it might be
an [opaque
string](https://github.com/bazelbuild/bazel/blob/7.1.0/src/main/java/com/google/devtools/build/lib/buildeventstream/proto/build_event_stream.proto#L131-L140){: .external}
or [structured
information](https://github.com/bazelbuild/bazel/blob/7.1.0/src/main/java/com/google/devtools/build/lib/buildeventstream/proto/build_event_stream.proto#L194-L205){: .external}
revealing more about the build event. A build event identifier is unique within
a build.

*  __Children:__ A build event may announce other build events, by including
their build event identifiers in its [children
field](https://github.com/bazelbuild/bazel/blob/7.1.0/src/main/java/com/google/devtools/build/lib/buildeventstream/proto/build_event_stream.proto#L1276){: .external}.
For example, the `PatternExpanded` build event announces the targets it expands
to as children. The protocol guarantees that all events, except for the first
event, are announced by a previous event.

* __Payload:__ The payload contains structured information about a build event,
encoded as a protocol buffer message specific to that event. Note that the
payload might not be the expected type, but could be an `Aborted` message
if the build aborted prematurely.

### Build event graph {:#build-event-graph}

All build events form a directed acyclic graph through their parent and child
relationship. Every build event except for the initial build event has one or
more parent events. Please note that not all parent events of a child event must
necessarily be posted before it. When a build is complete (succeeded or failed)
all announced events will have been posted. In case of a Bazel crash or a failed
network transport, some announced build events may never be posted.

The event graph's structure reflects the lifecycle of a command. Every BEP
graph has the following characteristic shape:

1. The root event is always a [`BuildStarted`](/remote/bep-glossary#buildstarted)
   event. All other events are its descendants.
1. Immediate children of the BuildStarted event contain metadata about the
   command.
1. Events containing data produced by the command, such as files built and test
   results, appear before the [`BuildFinished`](/remote/bep-glossary#buildfinished)
   event.
1. The [`BuildFinished`](/remote/bep-glossary#buildfinished) event *may* be followed
   by events containing summary information about the build (for example, metric
   or profiling data).

## Consuming Build Event Protocol {:#consuming-bep}

### Consume in binary format {:#consuming-bep-binary}

To consume the BEP in a binary format:

1. Have Bazel serialize the protocol buffer messages to a file by specifying the
   option `--build_event_binary_file=/path/to/file`. The file will contain
   serialized protocol buffer messages with each message being length delimited.
   Each message is prefixed with its length encoded as a variable length integer.
   This format can be read using the protocol buffer library’s
   [`parseDelimitedFrom(InputStream)`](https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/AbstractParser#parseDelimitedFrom-java.io.InputStream-){: .external}
   method.

2. Then, write a program that extracts the relevant information from the
   serialized protocol buffer message.

### Consume in text or JSON formats {:#consuming-bep-text-json}

The following Bazel command line flags will output the BEP in
human-readable formats, such as text and JSON:

```
--build_event_text_file
--build_event_json_file
```

## Build Event Service {:#build-event-service}

The [Build Event
Service](https://github.com/googleapis/googleapis/blob/master/google/devtools/build/v1/publish_build_event.proto){: .external}
Protocol is a generic [gRPC](https://www.grpc.io){: .external} service for publishing build events. The Build Event
Service protocol is independent of the BEP and treats BEP events as opaque bytes.
Bazel ships with a gRPC client implementation of the Build Event Service protocol that
publishes Build Event Protocol events. One can specify the endpoint to send the
events to using the `--bes_backend=HOST:PORT` flag. If your backend uses gRPC,
you must prefix the address with the appropriate scheme: `grpc://` for plaintext
gRPC and `grpcs://` for gRPC with TLS enabled.

### Build Event Service flags {:#bes-flags}

Bazel has several flags related to the Build Event Service protocol, including:

*  `--bes_backend`
*  `--[no]bes_lifecycle_events`
*  `--bes_results_url`
*  `--bes_timeout`
*  `--bes_instance_name`

For a description of each of these flags, see the
[Command-Line Reference](/reference/command-line-reference).

### Authentication and security {:#authentication-security}

Bazel’s Build Event Service implementation also supports authentication and TLS.
These settings can be controlled using the below flags. Please note that these
flags are also used for Bazel’s Remote Execution. This implies that the Build
Event Service and Remote Execution Endpoints need to share the same
authentication and TLS infrastructure.

*  `--[no]google_default_credentials`
*  `--google_credentials`
*  `--google_auth_scopes`
*  `--tls_certificate`
*  `--[no]tls_enabled`

For a description of each of these flags, see the
[Command-Line Reference](/reference/command-line-reference).

### Build Event Service and remote caching {:#bes-remote-caching}

The BEP typically contains many references to log files (test.log, test.xml,
etc. ) stored on the machine where Bazel is running. A remote BES server
typically can't access these files as they are on different machines. A way to
work around this issue is to use Bazel with [remote
caching](/remote/caching).
Bazel will upload all output files to the remote cache (including files
referenced in the BEP) and the BES server can then fetch the referenced files
from the cache.

See [GitHub issue 3689](https://github.com/bazelbuild/bazel/issues/3689){: .external} for
more details.
