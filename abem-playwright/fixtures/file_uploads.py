"""Test file preparation fixtures for upload tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from utils.file_helpers import (
    create_exe,
    create_jpeg,
    create_large_file,
    create_pdf,
    create_png,
    create_polyglot_jpg_exe,
)


@pytest.fixture(scope="function")
def test_jpeg_file() -> Path:
    """Temporary valid JPEG file (>= 1KB)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield create_jpeg(Path(tmpdir), size_kb=5)


@pytest.fixture(scope="function")
def test_png_file() -> Path:
    """Temporary valid PNG file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield create_png(Path(tmpdir))


@pytest.fixture(scope="function")
def test_pdf_file() -> Path:
    """Temporary valid PDF file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield create_pdf(Path(tmpdir))


@pytest.fixture(scope="function")
def test_exe_file() -> Path:
    """Temporary .exe file with valid PE magic bytes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield create_exe(Path(tmpdir))


@pytest.fixture(scope="function")
def test_large_file() -> Path:
    """Temporary file of exactly 10.1 MB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield create_large_file(Path(tmpdir), size_mb=10.1)


@pytest.fixture(scope="function")
def test_polyglot_file() -> Path:
    """Temporary file with JPEG header but embedded PE content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield create_polyglot_jpg_exe(Path(tmpdir))
