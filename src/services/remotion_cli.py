"""Remotion CLI wrapper for video rendering."""

import json
import subprocess
from pathlib import Path
from typing import Optional


class RemotionCLI:
    """Wrapper for calling Remotion render via CLI."""

    def __init__(self, remotion_dir: Optional[Path] = None):
        self.remotion_dir = remotion_dir or Path(__file__).parent.parent.parent / "remotion"

    def render(
        self,
        composition_id: str,
        output_path: Path,
        props: dict,
        props_file: Optional[Path] = None,
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

        # Build render command
        cmd = [
            "pnpm",
            "exec",
            "remotion",
            "render",
            composition_id,
            str(output_path),
            "--props",
            str(props_file),
        ]

        # Run Remotion render
        result = subprocess.run(
            cmd,
            cwd=self.remotion_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Remotion render failed:\n{result.stderr}")

        return output_path

    def preview(self) -> subprocess.Popen:
        """Start Remotion preview server."""
        cmd = ["pnpm", "exec", "remotion", "studio"]
        return subprocess.Popen(cmd, cwd=self.remotion_dir)

    def get_compositions(self) -> list[str]:
        """List available compositions."""
        cmd = ["pnpm", "exec", "remotion", "compositions"]
        result = subprocess.run(
            cmd,
            cwd=self.remotion_dir,
            capture_output=True,
            text=True,
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

