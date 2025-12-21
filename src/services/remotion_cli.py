"""Remotion CLI wrapper for video rendering."""

import json
import subprocess
import shutil
import os
from pathlib import Path
from typing import Optional
import re


def _msys_to_windows_path(p: str) -> str:
    """Convert MSYS/Git-Bash style paths to Windows paths for CreateProcess.

    Examples:
      /c/Dev/arcanomy-motion -> C:\\Dev\\arcanomy-motion
      /d/Tools/node -> D:\\Tools\\node
    """
    if os.name != "nt":
        return p
    if not p:
        return p
    m = re.match(r"^/([a-zA-Z])/(.*)$", p)
    if not m:
        return p
    drive = m.group(1).upper()
    rest = m.group(2).replace("/", "\\")
    return f"{drive}:\\{rest}"


def _normalize_runner_exe(p: str) -> str:
    """Normalize runner executable path for Windows subprocess.

    On Windows, `shutil.which()` may return POSIX-like paths when running under Git Bash.
    """
    if os.name != "nt":
        return p
    return _msys_to_windows_path(p)


def _to_forward_slash_path(p: Path) -> str:
    """Represent a Windows path in a Git-Bash-friendly way (C:/... with forward slashes)."""
    s = str(Path(p).resolve())
    return s.replace("\\", "/")


def _find_git_bash() -> Optional[str]:
    """Find bash executable for Git Bash on Windows (for reliable PATH resolution)."""
    if os.name != "nt":
        return None
    for candidate in (
        shutil.which("bash.exe"),
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ):
        if candidate and Path(candidate).exists():
            return str(Path(candidate))
    return None


def _get_package_runner() -> list[str]:
    """Detect available package runner (pnpm, npx, or yarn).
    
    Returns the command prefix to use for running remotion commands.
    Tries pnpm first (faster), then npx (comes with Node), then yarn.
    """
    # On Windows, prefer explicit .cmd resolution to avoid shell=True PATH mismatches
    # (e.g., Git Bash can find `npx`, but cmd.exe can't).
    pnpm = shutil.which("pnpm.cmd") or shutil.which("pnpm")
    if pnpm:
        return [_normalize_runner_exe(pnpm), "exec"]

    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if npx:
        return [_normalize_runner_exe(npx)]

    yarn = shutil.which("yarn.cmd") or shutil.which("yarn")
    if yarn:
        return [_normalize_runner_exe(yarn)]

    # Fallback to npx and hope it works
    return ["npx"]


class RemotionCLI:
    """Wrapper for calling Remotion render via CLI."""

    def __init__(self, remotion_dir: Optional[Path] = None):
        self.remotion_dir = remotion_dir or Path(__file__).parent.parent.parent / "remotion"
        self._runner = _get_package_runner()

    def render(
        self,
        composition_id: str,
        output_path: Path,
        props: dict,
        props_file: Optional[Path] = None,
        frames: Optional[str] = None,
    ) -> Path:
        """Render a Remotion composition to video.

        Args:
            composition_id: The composition to render (e.g., "MainReel")
            output_path: Where to save the rendered video
            props: Props to pass to the composition
            props_file: Optional path to save props JSON (auto-generated if not provided)

        Returns:
            Path to the rendered video
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write props to temp file
        if props_file is None:
            props_file = output_path.parent / "remotion_props.json"

        with open(props_file, "w", encoding="utf-8") as f:
            json.dump(props, f, indent=2)

        # Build render command (Remotion 4.x requires: render <entry-file> <composition-id> <output>)
        # Must use absolute paths since subprocess runs from remotion_dir, not user's CWD
        entry_file = "src/index.ts"
        abs_output_path = output_path.resolve()
        abs_props_file = props_file.resolve()
        
        cmd = [
            *self._runner,
            "remotion",
            "render",
            entry_file,
            composition_id,
            str(abs_output_path),
            "--props",
            str(abs_props_file),
        ]
        if frames:
            cmd.extend(["--frames", frames])

        # Run Remotion render
        # IMPORTANT (Windows/Git Bash):
        # `uv run chart ...` is usually executed from Git Bash. The PATH there may contain
        # shims/functions for pnpm/npx that are NOT visible to plain CreateProcess lookups.
        # To match the working "uv run chart" behavior, prefer running Remotion through
        # Git Bash on Windows.
        bash = _find_git_bash()
        if os.name == "nt" and bash:
            remotion_dir = _to_forward_slash_path(self.remotion_dir)
            out_path = _to_forward_slash_path(abs_output_path)
            props_path = _to_forward_slash_path(abs_props_file)

            # Try runners in deterministic order. Avoid mixing slashes.
            candidates = [
                f'pnpm exec remotion render {entry_file} {composition_id} "{out_path}" --props "{props_path}"'
                + (f' --frames "{frames}"' if frames else ""),
                f'npx remotion render {entry_file} {composition_id} "{out_path}" --props "{props_path}"'
                + (f' --frames "{frames}"' if frames else ""),
                f'yarn remotion render {entry_file} {composition_id} "{out_path}" --props "{props_path}"'
                + (f' --frames "{frames}"' if frames else ""),
            ]
            last = None
            for c in candidates:
                bash_cmd = f'cd "{remotion_dir}" && {c}'
                last = subprocess.run(
                    [bash, "-lc", bash_cmd],
                    capture_output=True,
                    text=True,
                )
                if last.returncode == 0:
                    result = last
                    break
            else:
                # all failed
                result = last  # type: ignore[assignment]
        else:
            result = subprocess.run(
                cmd,
                cwd=self.remotion_dir,
                capture_output=True,
                text=True,
                shell=False,
            )

        if result.returncode != 0:
            raise RuntimeError(f"Remotion render failed:\n{result.stderr}")

        return output_path

    def preview(self) -> subprocess.Popen:
        """Start Remotion preview server."""
        cmd = [*self._runner, "remotion", "studio"]
        bash = _find_git_bash()
        if os.name == "nt" and bash:
            remotion_dir = _to_forward_slash_path(self.remotion_dir)
            bash_cmd = f'cd "{remotion_dir}" && pnpm exec remotion studio'
            return subprocess.Popen([bash, "-lc", bash_cmd])
        return subprocess.Popen(cmd, cwd=self.remotion_dir, shell=False)

    def get_compositions(self) -> list[str]:
        """List available compositions."""
        cmd = [*self._runner, "remotion", "compositions"]
        bash = _find_git_bash()
        if os.name == "nt" and bash:
            remotion_dir = _to_forward_slash_path(self.remotion_dir)
            result = subprocess.run(
                [bash, "-lc", f'cd "{remotion_dir}" && pnpm exec remotion compositions'],
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                cmd,
                cwd=self.remotion_dir,
                capture_output=True,
                text=True,
                shell=False,
            )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to list compositions:\n{result.stderr}")

        # Parse composition names from output
        compositions = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line and not line.startswith("-"):
                compositions.append(line)

        return compositions
