# Scanforge

A progressive Python project that starts as a simple CLI barcode generator and evolves through ten stages into a full-stack, database-backed, deployment-ready application. Each stage introduces new Python concepts and libraries while building on the previous one.

## Project overview

| Detail | Value |
|---|---|
| Name | Scanforge |
| Language | Python 3.10+ |
| Package manager | uv |
| Licence | MIT |
| Author | Drogo |
| Repository type | Learning project (progressive build) |

The project is structured so that each stage is a self-contained milestone. You can stop at any stage and have a working tool, or continue to the next to layer on new functionality.

## System requirements

| Requirement | Minimum |
|---|---|
| Python | 3.10 or later (managed by uv) |
| uv | Latest stable (handles Python installs, virtual environments, and dependencies) |
| OS | Windows 10/11, macOS 12+, or Ubuntu 22.04+ |
| RAM | 512 MB (stages 1 to 8), 2 GB recommended for stage 9 (OpenCV) |
| Disk | 500 MB for all dependencies across all stages |
| Webcam | Required only for stage 9 (live barcode scanning) |
| Docker | Required only for stage 10 |

## Dependencies by stage

Dependencies are cumulative. Each stage inherits everything from the stages before it.

| Stage | New dependencies | Install |
|---|---|---|
| 1 | `python-barcode`, `Pillow` | `uv add python-barcode Pillow` |
| 2 | `qrcode` | `uv add "qrcode[pil]"` |
| 3 | `openpyxl` | `uv add openpyxl` |
| 4 | `reportlab` | `uv add reportlab` |
| 5 | `customtkinter` | `uv add customtkinter` |
| 6 | `flask` | `uv add flask` |
| 7 | `fastapi`, `uvicorn` | `uv add fastapi uvicorn` |
| 8 | `sqlalchemy` | `uv add sqlalchemy` |
| 9 | `pyzbar`, `opencv-python` | `uv add pyzbar opencv-python` |
| 10 | `pytest`, `gunicorn`, `ruff` | System-level Docker install; `uv add --group dev pytest ruff` and `uv add gunicorn` |

> **Note on pyzbar (stage 9):** On Linux, you also need the system library `libzbar0` (`sudo apt install libzbar0`). On macOS, install via Homebrew (`brew install zbar`). Windows wheels bundle the library automatically.

## Project structure

The recommended layout once all stages are complete:

```
scanforge/
├── README.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── Dockerfile
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   ├── __init__.py
│   ├── cli.py                  # Stage 1-2: CLI entry point
│   ├── generator.py            # Core generation logic
│   ├── formats.py              # Barcode format registry and validation
│   ├── batch.py                # Stage 3: CSV/Excel batch processing
│   ├── customise.py            # Stage 4: Colour, sizing, PDF output
│   ├── gui.py                  # Stage 5: Desktop GUI
│   ├── web/
│   │   ├── __init__.py
│   │   ├── flask_app.py        # Stage 6: Flask web app
│   │   ├── api.py              # Stage 7: FastAPI REST API
│   │   ├── templates/
│   │   │   └── index.html
│   │   └── static/
│   │       └── style.css
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py           # Stage 8: SQLAlchemy models
│   │   ├── crud.py             # Stage 8: Database operations
│   │   └── connection.py       # Stage 8: DB session management
│   └── scanner.py              # Stage 9: Barcode reader/decoder
├── tests/
│   ├── test_generator.py
│   ├── test_batch.py
│   ├── test_api.py
│   └── test_scanner.py
├── input/                      # Sample CSV/Excel files for batch mode
│   └── sample_products.csv
└── output/                     # Generated barcode images (gitignored)
    └── .gitkeep
```

Build the structure gradually. At stage 1 you only need `src/cli.py` and `src/generator.py`. Add files as each stage requires them.

---

## Stage 1: CLI generator

### Objective

Generate a single Code128 barcode image from a command-line argument and save it to disk.

### What you will learn

- Initialising a Python project with `uv init` and managing dependencies with `uv add`
- Parsing command-line arguments with `argparse`
- Using third-party libraries (`python-barcode`, `Pillow`)
- File I/O and path handling with `pathlib`
- Writing your first `if __name__ == "__main__"` entry point

### Technical specification

| Item | Detail |
|---|---|
| Input | A string value passed as a CLI argument |
| Output | A PNG image of a Code128 barcode saved to `./output/` |
| Default filename | `<value>_code128.png` |
| CLI flags | `--value` (required), `--output-dir` (optional, defaults to `./output/`) |

### Acceptance criteria

- Running `uv run src/cli.py --value "ABC123"` produces a valid PNG barcode in the output directory
- The script exits with a clear error message if no value is provided
- The output directory is created automatically if it does not exist

### Example usage

```bash
uv run src/cli.py --value "ABC123"
uv run src/cli.py --value "HELLO-WORLD" --output-dir ./my-barcodes/
```

---

## Stage 2: Multiple barcode formats

### Objective

Extend the CLI to support multiple 1D barcode formats and add QR code generation.

### What you will learn

- Working with multiple libraries for related tasks
- Input validation and user-friendly error messages
- Enums or dictionaries as format registries
- Structuring code across multiple modules

### Technical specification

| Item | Detail |
|---|---|
| Supported 1D formats | Code128, Code39, EAN-13, EAN-8, UPC-A, ISBN-13, ISBN-10, ITF, PZN |
| Supported 2D formats | QR Code |
| New CLI flag | `--format` (optional, defaults to `code128`) |
| Validation | Reject values that are invalid for the chosen format (e.g. EAN-13 must be 12 or 13 digits) |

### Acceptance criteria

- `uv run src/cli.py --value "5901234123457" --format ean13` generates a valid EAN-13 barcode
- `uv run src/cli.py --value "https://example.com" --format qr` generates a QR code
- `uv run src/cli.py --format list` prints all supported formats to stdout
- Invalid format names produce a clear error listing valid options
- Values that do not match the format's requirements produce a specific validation error

---

## Stage 3: Batch generation

### Objective

Read a list of values from a CSV or Excel file and generate barcode images for each row.

### What you will learn

- Reading CSV files with the `csv` standard library module
- Reading Excel files with `openpyxl`
- Iterating over data and handling row-level errors without stopping the batch
- Progress feedback to the terminal (basic print statements or `tqdm`)
- Logging with Python's `logging` module

### Technical specification

| Item | Detail |
|---|---|
| Supported input files | `.csv`, `.xlsx` |
| Expected columns | `value` (required), `format` (optional, defaults to code128), `filename` (optional) |
| Output | One barcode image per row, saved to the output directory |
| Error handling | Log and skip rows that fail validation; do not abort the batch |
| Summary | Print a summary at the end: total rows, successful, failed |

### Acceptance criteria

- A CSV with 50 rows produces 50 barcode images (assuming all rows are valid)
- Rows with invalid data are logged to stderr and skipped without crashing
- The final summary accurately reports success and failure counts
- Both `.csv` and `.xlsx` files are handled correctly

### Sample CSV format

```csv
value,format,filename
ABC123,code128,product_a
5901234123457,ean13,cereal_box
https://example.com,qr,website_link
```

---

## Stage 4: Customisation

### Objective

Add visual customisation options (colours, sizing, text, module dimensions) and support PDF output alongside PNG and SVG.

### What you will learn

- Pillow image manipulation (drawing, fonts, colours)
- `reportlab` for PDF generation
- Passing configuration options through multiple layers of code
- Working with colour formats (hex, RGB tuples)

### Technical specification

| Option | CLI flag | Default |
|---|---|---|
| Foreground colour | `--fg-colour` | `#000000` |
| Background colour | `--bg-colour` | `#FFFFFF` |
| Module width (mm) | `--module-width` | `0.2` |
| Module height (mm) | `--module-height` | `15.0` |
| Show text below barcode | `--text / --no-text` | `--text` |
| Font size | `--font-size` | `10` |
| Output format | `--output-format` | `png` |
| Supported output formats | `png`, `svg`, `pdf` | |

### Acceptance criteria

- A barcode generated with `--fg-colour "#FF0000" --bg-colour "#FFFF00"` has a red barcode on a yellow background
- PDF output produces a valid, openable PDF file with the barcode centred on the page
- All customisation options work in batch mode (applied uniformly to all barcodes in the batch)
- Invalid colour values produce a clear error

---

## Stage 5: Desktop GUI

### Objective

Build a desktop application with a live barcode preview, customisation controls, and save/export functionality.

### What you will learn

- Event-driven programming with callbacks
- GUI layout management (grid, pack, frames)
- Updating a canvas or image widget in response to user input
- Threading (if you want the UI to stay responsive during batch jobs)
- Separation of UI code from business logic

### Technical specification

| Component | Detail |
|---|---|
| Framework | CustomTkinter (modern themed tkinter wrapper) |
| Window size | 900 x 600, resizable |
| Panels | Left panel for input and options, right panel for live preview |
| Controls | Text input for value, dropdown for format, colour pickers, sliders for dimensions, toggle for text display |
| Actions | Generate, save as PNG/SVG/PDF, copy to clipboard, batch import |
| Preview | Updates in real time as the user types or changes settings |

### Acceptance criteria

- Typing a value in the input field updates the barcode preview within 200ms
- Changing any customisation option immediately reflects in the preview
- The save button opens a native file dialog and saves in the selected format
- Batch import opens a file dialog, processes the file, and shows a progress bar
- The application does not freeze during batch generation

---

## Stage 6: Web application

### Objective

Create a browser-based barcode generator using Flask, with a form for input and instant download of the generated barcode.

### What you will learn

- Flask application structure (routes, templates, static files)
- HTML forms and POST request handling
- Jinja2 templating
- Serving files for download (BytesIO, send_file)
- Basic CSS for a usable interface

### Technical specification

| Item | Detail |
|---|---|
| Framework | Flask |
| Routes | `GET /` (form page), `POST /generate` (generates and returns barcode) |
| Form fields | Value, format (dropdown), output format (PNG/SVG/PDF), customisation options |
| Response | Browser downloads the generated barcode file directly |
| Error display | Validation errors shown on the form page without losing user input |

### Acceptance criteria

- Visiting `http://localhost:5000` shows a clean, functional form
- Submitting the form downloads a barcode file in the chosen format
- Validation errors appear inline on the form without clearing the user's input
- The application handles concurrent requests without errors

---

## Stage 7: REST API

### Objective

Build a RESTful API that accepts JSON requests and returns barcode images, with proper HTTP semantics, content negotiation, and auto-generated documentation.

### What you will learn

- FastAPI framework and Pydantic models for request validation
- HTTP methods, status codes, and content types
- Streaming binary responses (images)
- Auto-generated interactive API docs (Swagger UI)
- Query parameters vs. request body design

### Technical specification

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/barcode` | POST | Generate a single barcode |
| `/api/v1/barcode/formats` | GET | List supported formats |
| `/api/v1/health` | GET | Health check |

### Request body (`POST /api/v1/barcode`)

```json
{
  "value": "ABC123",
  "format": "code128",
  "output_format": "png",
  "options": {
    "fg_colour": "#000000",
    "bg_colour": "#FFFFFF",
    "module_width": 0.2,
    "module_height": 15.0,
    "show_text": true,
    "font_size": 10
  }
}
```

### Response

- `200 OK` with `Content-Type: image/png` (or `image/svg+xml`, `application/pdf`)
- `422 Unprocessable Entity` for validation errors, with a JSON error body
- `400 Bad Request` for unsupported formats

### Acceptance criteria

- `POST /api/v1/barcode` with valid JSON returns a barcode image with the correct content type
- Swagger docs are accessible at `/docs` and allow testing from the browser
- All Pydantic validation errors return structured JSON error responses
- The API runs concurrently under `uvicorn` without blocking

---

## Stage 8: Database-backed inventory

### Objective

Store every generated barcode's metadata in a database, enabling search, retrieval, and history.

### What you will learn

- SQLAlchemy ORM (models, sessions, queries)
- Database schema design and relationships
- CRUD operations through an API
- Alembic migrations (optional extension)
- Pagination and filtering

### Technical specification

| Item | Detail |
|---|---|
| Database | SQLite for development, PostgreSQL for production |
| ORM | SQLAlchemy 2.0+ |
| Table: `barcodes` | `id`, `value`, `format`, `output_format`, `options_json`, `file_path`, `created_at` |

### New API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/barcodes` | GET | List all generated barcodes (paginated) |
| `/api/v1/barcodes/{id}` | GET | Retrieve a specific barcode's metadata and image |
| `/api/v1/barcodes/{id}` | DELETE | Delete a barcode record and its file |
| `/api/v1/barcodes/search` | GET | Search by value or format |

### Acceptance criteria

- Every barcode generated through the API is recorded in the database
- `GET /api/v1/barcodes?page=1&per_page=20` returns paginated results with total count
- Deleting a barcode removes both the database record and the file on disk
- The search endpoint supports partial value matching

---

## Stage 9: Barcode scanner and reader

### Objective

Decode barcodes from static images and live webcam feeds, closing the loop between generation and reading.

### What you will learn

- Image processing with OpenCV (loading, colour conversion, thresholding)
- Barcode decoding with `pyzbar`
- Webcam capture and real-time frame processing
- Drawing overlays on video frames (bounding boxes, decoded text)
- Handling multiple barcodes in a single image

### Technical specification

| Mode | Input | Output |
|---|---|---|
| Image scan | Path to an image file | List of decoded barcode values and their formats |
| Webcam scan | Live webcam feed | Real-time overlay showing decoded values; optional log to file or database |
| API endpoint | Image upload via `POST /api/v1/scan` | JSON array of decoded barcodes |

### Acceptance criteria

- Scanning a barcode image generated by this project correctly decodes the original value
- The webcam scanner detects and decodes barcodes in real time with visible bounding boxes
- Multiple barcodes in a single image are all detected and reported
- The API scan endpoint accepts image uploads and returns decoded values as JSON
- Decoding failures (blurry images, unsupported formats) return clear feedback, not crashes

---

## Stage 10: Deployment

### Objective

Containerise the application, add CI/CD, write tests, and deploy to a cloud environment.

### What you will learn

- Writing a `Dockerfile` and `docker-compose.yml` using uv for dependency installation
- Multi-stage Docker builds for smaller images
- Writing unit and integration tests with `pytest` (run via `uv run pytest`)
- GitHub Actions for CI/CD using `astral-sh/setup-uv` (lint, test, build, deploy)
- Environment variable management and secrets handling
- Running a production Python application with `gunicorn` behind a reverse proxy

### Technical specification

| Item | Detail |
|---|---|
| Package manager | uv |
| Container runtime | Docker with docker-compose |
| Base image | `python:3.12-slim` with uv installed via `astral-sh/uv` installer |
| WSGI server | Gunicorn with Uvicorn workers |
| CI/CD | GitHub Actions with `astral-sh/setup-uv` action |
| Test framework | pytest |
| Linting | Ruff (via `uv run ruff check`) |
| Type checking | mypy (optional) |

### Dockerfile pattern

```dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies from lockfile
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/

EXPOSE 8000
CMD ["uv", "run", "gunicorn", "src.web.api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### Docker Compose setup

```yaml
# docker-compose.yml structure
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/barcodes
    depends_on:
      - db
  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
```

### CI/CD pipeline stages

1. **Setup** uv with `astral-sh/setup-uv` action
2. **Lint** with `uv run ruff check`
3. **Type check** with `uv run mypy` (optional)
4. **Test** with `uv run pytest` (unit and integration)
5. **Build** Docker image
6. **Push** to container registry
7. **Deploy** to cloud service (Railway, Fly.io, or AWS ECS)

### Acceptance criteria

- `docker compose up` starts the full stack (API + database) with no manual setup
- All tests pass in the GitHub Actions pipeline before merge is allowed
- The deployed application is accessible via a public URL with HTTPS
- Environment variables control all configuration (no hardcoded secrets)

---

## Getting started

### Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Initialise the project

```bash
# Create the project (flat layout, no build system, git repo initialised automatically)
uv init --no-package scanforge
cd scanforge

# Pin Python version (uv will install it automatically if missing)
uv python pin 3.14

# Add stage 1 dependencies
uv add python-barcode Pillow

# Run the generator (uv creates and manages the virtual environment automatically)
uv run src/cli.py --value "HELLO-WORLD"
```

`--no-package` keeps the flat layout this README assumes, rather than the packaged `src/` layout with a build backend that current uv versions generate by default. That packaged layout is meant for things published to PyPI, which this project isn't.

`uv add` writes each dependency to `pyproject.toml` and updates `uv.lock`. Both files should be committed to version control. The `.venv/` directory should be gitignored (uv recreates it from the lockfile on any machine).

## Progress tracker

| Stage | Description | Status |
|---|---|---|
| 1 | CLI generator | ⬜ Not started |
| 2 | Multiple formats | ⬜ Not started |
| 3 | Batch generation | ⬜ Not started |
| 4 | Customisation | ⬜ Not started |
| 5 | Desktop GUI | ⬜ Not started |
| 6 | Web application | ⬜ Not started |
| 7 | REST API | ⬜ Not started |
| 8 | Database inventory | ⬜ Not started |
| 9 | Barcode scanner | ⬜ Not started |
| 10 | Deployment | ⬜ Not started |

## Licence

MIT