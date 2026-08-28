# flint2-ssh-api

REST API built with **FastAPI** for querying device connectivity status
on **GL.iNet FLINT2 (GL-MT6000)** routers via SSH.

## Features

- [TODO] Check if a device is online (connected to Wi-Fi) by IP address and by name
- Persistent SSH connection pool — no reconnect overhead per request
- [TODO] TTL-based response cache — reduces router load
- [TODO] Input validation, structured error responses
- [TODO] Docker-ready

## Requirements

- Python 3.13+
- GL.iNet FLINT2 router with SSH enabled

## Starting server

Install dependencies
```shell
pip install uv
uv sync --extra dev
```

Copy env file and complete them with your data 
```shell
cp .env.example .env
```

Start server
```shell
uvicorn app.main:app --reload --reload-dir ./app
```

## UnitTests

Run unit tests with pytest
```shell
pytest tests/ -v
```

## Code Quality

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting, and [Mypy](https://mypy-lang.org/) for type checking.

### Available scripts

| Script                | Description                                                  |
|-----------------------|--------------------------------------------------------------|
| `scripts\cleanup.bat` | Auto-fixes linting issues and formats code                   |
| `scripts\lint.bat`    | Checks linting, formatting and types (read-only, no changes) |

### Usage

**Fix issues before committing:**
```shell
uv run ruff check . --fix --unsafe-fixes
uv run ruff format .
```
or with bat file:
```shell
.\scripts\cleanup.bat
```

**Check code quality before creating pull request:**
```shell
uv run ruff check .
uv run ruff format --check .
uv run mypy app/
```
or with bat file:
```shell
.\scripts\lint.bat
```
