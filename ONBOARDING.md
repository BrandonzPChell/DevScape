# DevScape Onboarding Guide

Welcome, new Guardian, to the DevScape! This guide will help you set up your local development environment and get started with contributing.

## 1. Local Development Setup

### Prerequisites
*   Python 3.10+
*   `pip` (Python package installer)
*   `git`

### Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-org/devscape.git # Replace with actual repo URL
    cd devscape
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows:
    .venv\Scripts\activate
    # On macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Install dependencies (editable mode for development):**
    ```bash
    pip install -e .
    pip install -r game/requirements.txt
    pip install -r dev-requirements.txt
    ```

### Understanding the `src/devscape` Layout

Our project uses a `src/devscape` layout. This means all production code resides within the `src/devscape` directory. When you install the project in editable mode (`pip install -e .`), the `devscape` package becomes directly importable, allowing you to use `from devscape.module import ...` in your code and tests.

## 2. Running Tests

We use `pytest` for testing. All test files are located in the `tests/` directory.

To run all tests:
```bash
pytest
```

To run tests with coverage:
```bash
pytest --cov=src
```

You can also use the `Makefile` targets:
```bash
make test
make coverage
```

## 3. Running Linters and Formatters

We use `ruff`, `pylint`, `black`, and `isort` to maintain code quality and consistency.

To run linting and formatting checks:
```bash
make lint
make format
```

## 4. How to Open a Pull Request

1.  **Create a new branch:**
    ```bash
    git checkout -b feature/your-feature-name
    ```
2.  **Make your changes.**
3.  **Commit your changes:**
    ```bash
    git add .
    git commit -m "feat: Add your feature"
    ```
4.  **Push your branch:**
    ```bash
    git push origin feature/your-feature-name
    ```
5.  **Open a Pull Request** on GitHub, targeting the `main` branch. Ensure all CI checks pass.

## 5. Where to Find Mentor/Contact

For any questions or assistance, please reach out to [Maintainer Contact/Channel, e.g., Discord, Slack, GitHub Discussions].
