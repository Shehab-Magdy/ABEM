"""Test file generation helpers for upload tests.

Creates valid JPEG, PNG, PDF, and deliberately invalid files
in temp directories for use by upload test fixtures.
"""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path

from PIL import Image


def create_jpeg(directory: Path, filename: str = "test_bill.jpg", size_kb: int = 5) -> Path:
    """Create a valid JPEG file of approximate size_kb."""
    filepath = directory / filename
    # Create a small image and save as JPEG
    img = Image.new("RGB", (100, 100), color=(255, 200, 100))
    img.save(str(filepath), "JPEG", quality=95)
    # Pad to minimum size if needed
    current_size = filepath.stat().st_size
    if current_size < size_kb * 1024:
        with open(filepath, "ab") as f:
            f.write(b"\x00" * (size_kb * 1024 - current_size))
    return filepath


def create_png(directory: Path, filename: str = "test_bill.png") -> Path:
    """Create a valid PNG file."""
    filepath = directory / filename
    img = Image.new("RGBA", (100, 100), color=(100, 200, 255, 255))
    img.save(str(filepath), "PNG")
    return filepath


def create_pdf(directory: Path, filename: str = "test_bill.pdf") -> Path:
    """Create a minimal valid PDF file."""
    filepath = directory / filename
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
190
%%EOF"""
    filepath.write_bytes(pdf_content)
    return filepath


def create_exe(directory: Path, filename: str = "malicious.exe") -> Path:
    """Create a file with valid PE (Windows executable) magic bytes."""
    filepath = directory / filename
    # MZ header (PE magic bytes)
    pe_header = b"MZ" + b"\x90" * 58 + struct.pack("<I", 64)
    pe_header += b"PE\x00\x00"  # PE signature
    pe_header += b"\x00" * 200  # padding
    filepath.write_bytes(pe_header)
    return filepath


def create_large_file(
    directory: Path,
    filename: str = "large_file.bin",
    size_mb: float = 10.1,
) -> Path:
    """Create a file of exactly size_mb megabytes."""
    filepath = directory / filename
    size_bytes = int(size_mb * 1024 * 1024)
    with open(filepath, "wb") as f:
        # Write in 1MB chunks
        chunk = b"\x00" * (1024 * 1024)
        written = 0
        while written + len(chunk) <= size_bytes:
            f.write(chunk)
            written += len(chunk)
        if written < size_bytes:
            f.write(b"\x00" * (size_bytes - written))
    return filepath


def create_polyglot_jpg_exe(directory: Path, filename: str = "polyglot.jpg") -> Path:
    """Create a file that has JPEG headers but contains executable content.

    Used to test magic-bytes-based file validation.
    """
    filepath = directory / filename
    # JPEG SOI marker followed by PE content
    content = b"\xff\xd8\xff\xe0"  # JPEG SOI + APP0 marker
    content += b"\x00\x10JFIF\x00"  # JFIF header
    content += b"\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    content += b"MZ" + b"\x90" * 100  # Embedded PE content
    content += b"\xff\xd9"  # JPEG EOI marker
    filepath.write_bytes(content)
    return filepath
