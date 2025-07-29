# docx2LaTeX

DOCX to LaTeX Converter for Medical and Scientific Publications.

## Description

docx2LaTeX is a PyQt6 application that allows doctors and researchers to easily convert their Word documents into LaTeX articles formatted according to scientific journal templates.

### Main Features

- **Simple Interface**: Drag & drop for files
- **Automatic Conversion**: DOCX → Markdown → LaTeX via Pandoc
- **Reference Management**: Automatic BibTeX citation matching
- **Structured Editor**: Section-by-section editing in simple markdown
- **Multiple Templates**: Support for different journal formats
- **PDF Generation**: Automatic compilation of the final document

### Workflow

1. **Drag & drop** your Word file
2. **Select** the target journal template
3. **Add** your BibTeX reference file
4. **Edit** content by sections in markdown
5. **Generate** the final PDF

## Installation

### Prerequisites

- Python 3.8+
- Pandoc (https://pandoc.org/installing.html)
- LaTeX distribution (TeX Live, MiKTeX)

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Project Structure

```
docx2latex/
├── main.py              # Entry point
├── config.json          # Configuration
├── requirements.txt     # Python dependencies
├── ui/                  # User interface
├── core/                # Conversion logic
├── utils/               # Utilities
└── templates/           # LaTeX templates
```

## Development

Each module contains detailed docstrings. Types are specified for all input parameters.

## Author

harmonips - 2025