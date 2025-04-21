## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Download Bazel Documentation

Download the documentation to the default location (`input/bazel-site`):
```bash
python main.py download
```

Download to a custom location:
```bash
python main.py download --output-dir custom/path
```

### Process Documentation

Process the downloaded documentation to generate a consolidated version:
```bash
python main.py process
```

Process with custom input and output directories:
```bash
python main.py process --input-dir custom/input --output-dir custom/output
```

The script will:
- Create the output directory if it doesn't exist
- Use git sparse checkout to only download the `/site/en` directory
- Skip git history for faster downloads
- Support updates for existing repositories
