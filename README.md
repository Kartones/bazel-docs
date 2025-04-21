# Bazel Documentation Processor

A tool to download and process Bazel and rules_nodejs documentation into a more readable format.

## Features

- Downloads Bazel documentation using git sparse checkout
- Downloads rules_nodejs documentation using git sparse checkout
- Processes documentation into organized markdown files
- Handles both Bazel and rules_nodejs documentation in a single command

## Installation

```bash
git clone https://github.com/yourusername/bazel-docs.git
cd bazel-docs
pip install -r requirements.txt
```

## Usage

The tool provides two main commands:

### Download Documentation

Downloads both Bazel and rules_nodejs documentation:

```bash
python3 -m main download
```

Optional arguments:
- `--bazel-output-dir`: Output directory for Bazel documentation (default: `input/bazel-site`)
- `--rules-nodejs-output-dir`: Output directory for rules_nodejs documentation (default: `input/rules-nodejs`)

### Process Documentation

Processes the downloaded documentation into markdown files:

```bash
python3 -m main process
```

Optional arguments:
- `--bazel-input-dir`: Input directory containing Bazel documentation (default: `input/bazel-site/site/en`)
- `--bazel-output-dir`: Output directory for processed Bazel documentation (default: `docs/bazel`)
- `--rules-nodejs-input-dir`: Input directory containing rules_nodejs documentation (default: `input/rules-nodejs`)
- `--rules-nodejs-output-file`: Output file for processed rules_nodejs documentation (default: `docs/rules_nodejs.md`)

## Examples

Download documentation to custom directories:
```bash
python3 -m main download --bazel-output-dir custom/bazel --rules-nodejs-output-dir custom/rules-nodejs
```

Process documentation from custom directories:
```bash
python3 -m main process --bazel-input-dir custom/bazel/site/en --rules-nodejs-input-dir custom/rules-nodejs
```

## Output Structure

- Bazel documentation is processed into multiple markdown files in the `docs/bazel` directory
- rules_nodejs documentation is processed into a single markdown file at `docs/rules_nodejs.md`

## License

MIT
