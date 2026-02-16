import subprocess
import platform
import re
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from typing import List, Optional, Callable

# Platform detection for compatible symbols
IS_WINDOWS = platform.system().lower() == 'windows'

# Use ASCII-compatible symbols for Windows cmd.exe, Unicode for Linux/Mac
if IS_WINDOWS:
    SYMBOL_SUCCESS = "[OK]"
    SYMBOL_FAILED = "[X]"
    SYMBOL_PROGRESS = "..."
    SPINNER_STYLE = "line"  # ASCII-compatible spinner for Windows
else:
    SYMBOL_SUCCESS = "✅"
    SYMBOL_FAILED = "❌"
    SYMBOL_PROGRESS = "⏳"
    SPINNER_STYLE = "dots"  # Unicode spinner for Linux/Mac

console = Console()


class DockerProgressMonitor:
    """Context manager for Docker operations with progress feedback."""

    def __init__(self, message: str = "Docker operation in progress"):
        """Initialize the progress monitor. """
        self.message = message
        self.spinner = Spinner(SPINNER_STYLE, text=f"│     {message}")
        self.live = None
        self.result = None
        self.success = False

    def __enter__(self):
        """Start the spinner display."""
        self.live = Live(self.spinner, console=console, refresh_per_second=10)
        self.live.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the spinner and show final status."""
        if self.live:
            self.live.stop()

        # Show result with platform-compatible symbols (with vertical line prefix)
        if self.success:
            console.print(f"  │     {SYMBOL_SUCCESS} {self.message} - Complete!", style="bold green")
        elif exc_type is not None:
            console.print(f"  │     {SYMBOL_FAILED} {self.message} - Failed (Exception)", style="bold red")
        elif self.result and self.result.returncode != 0:
            console.print(f"  │     {SYMBOL_FAILED} {self.message} - Failed", style="bold red")

    def update_status(self, new_message: str):
        """Update spinner message dynamically during operation."""
        self.message = new_message
        if self.live:
            self.spinner.text = f"│     {new_message}"
            self.live.update(self.spinner)

    def set_result(self, result):
        """Set subprocess result and determine success status."""
        self.result = result
        self.success = result.returncode == 0


def run_docker_with_progress(
    command: List[str],
    message: str,
    capture_output: bool = True,
    text: bool = True,
    encoding: str = 'utf-8',
    errors: str = 'ignore'
) -> subprocess.CompletedProcess:
    """Run a Docker command with progress spinner. """
    with DockerProgressMonitor(message) as monitor:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=text,
            encoding=encoding,
            errors=errors
        )
        monitor.set_result(result)

    return result


def run_command_with_progress(
    command,
    message: str,
    shell: bool = False,
    capture_output: bool = True,
    text: bool = True,
    encoding: str = 'utf-8',
    errors: str = 'ignore'
) -> subprocess.CompletedProcess:
    """Run any command with progress spinner (not just Docker)."""
    with DockerProgressMonitor(message) as monitor:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=capture_output,
            text=text,
            encoding=encoding,
            errors=errors
        )
        monitor.set_result(result)

    return result


def filter_docker_errors(stderr: str) -> str:
    """Filter Docker stderr to show only real errors, not progress lines."""
    if not stderr:
        return ""

    # Progress indicators to filter out
    progress_keywords = [
        'Pulling', 'Download', 'Extracting', 'Pull complete',
        'Waiting', 'Verifying', 'Already exists', 'Digest:',
        'Status:', 'Image is up to date', 'Downloaded newer image'
    ]

    error_lines = []
    for line in stderr.split('\n'):
        # Skip progress lines
        if any(keyword in line for keyword in progress_keywords):
            continue

        # Keep non-empty lines
        if line.strip():
            error_lines.append(line)

    return '\n'.join(error_lines)


def run_docker_pull_with_progress(image: str, callback: Optional[Callable[[int, str], None]] = None) -> subprocess.CompletedProcess:
    """
    Pull Docker image with real-time progress tracking.

    Args:
        image: Docker image name (e.g. 'nginx:latest')
        callback: Optional callback function(progress: int, status: str) for progress updates

    Returns:
        subprocess.CompletedProcess with pull result
    """
    console.print(f"  │     Pulling image {image}...")

    process = subprocess.Popen(
        ['docker', 'pull', image],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    layers_total = 0
    layers_done = 0
    last_progress = 0

    with Progress(
        TextColumn("  │     [progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Pulling layers...", total=100)

        for line in iter(process.stdout.readline, ''):
            if not line:
                break

            # Count total layers
            if 'Pulling fs layer' in line:
                layers_total += 1
            elif 'Pull complete' in line or 'Already exists' in line:
                layers_done += 1

            # Calculate progress
            if layers_total > 0:
                pct = int((layers_done / layers_total) * 100)
                if pct > last_progress:
                    last_progress = pct
                    progress.update(task, completed=pct)
                    status = f"Pulled {layers_done}/{layers_total} layers"
                    progress.update(task, description=status)

                    # Call callback if provided (for web UI streaming)
                    if callback:
                        callback(pct, status)

    process.wait()

    if process.returncode == 0:
        console.print(f"  │     {SYMBOL_SUCCESS} Image pulled successfully!", style="bold green")
    else:
        console.print(f"  │     {SYMBOL_FAILED} Image pull failed!", style="bold red")

    return subprocess.CompletedProcess(
        args=['docker', 'pull', image],
        returncode=process.returncode,
        stdout='',
        stderr=''
    )
