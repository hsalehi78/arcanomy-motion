"""Remotion CLI wrapper for video rendering."""

import json
import subprocess
import shutil
import os
from pathlib import Path
from typing import Optional

# #region agent log
_DEBUG_LOG_PATH = r"c:\Dev\arcanomy-motion\.cursor\debug.log"
def _dbg(loc, msg, data, hyp):
    import time; open(_DEBUG_LOG_PATH, "a").write(json.dumps({"location": loc, "message": msg, "data": data, "timestamp": int(time.time()*1000), "sessionId": "debug-session", "hypothesisId": hyp}) + "\n")
# #endregion


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

        # Build render command (Remotion 4.x requires: render <entry-file> <composition-id> <output>)
        entry_file = "src/index.ts"
        cmd = [
            "pnpm",
            "exec",
            "remotion",
            "render",
            entry_file,
            composition_id,
            str(output_path),
            "--props",
            str(props_file),
        ]

        # #region agent log
        _dbg("remotion_cli.py:render", "pnpm_which", {"pnpm_path": shutil.which("pnpm"), "pnpm_cmd_path": shutil.which("pnpm.cmd")}, "A")
        _dbg("remotion_cli.py:render", "path_env", {"PATH": os.environ.get("PATH", "")[:500]}, "B")
        _dbg("remotion_cli.py:render", "remotion_dir_check", {"remotion_dir": str(self.remotion_dir), "exists": self.remotion_dir.exists()}, "C")
        _dbg("remotion_cli.py:render", "cmd_info", {"cmd": cmd, "os_name": os.name}, "D")
        # #endregion

        # Run Remotion render
        # #region agent log
        use_shell = os.name == "nt"  # Windows needs shell=True for .cmd executables
        _dbg("remotion_cli.py:render", "using_shell", {"use_shell": use_shell, "os_name": os.name}, "A")
        try:
            result = subprocess.run(
                cmd,
                cwd=self.remotion_dir,
                capture_output=True,
                text=True,
                shell=use_shell,
            )
            _dbg("remotion_cli.py:render", "subprocess_success", {"returncode": result.returncode, "stderr": result.stderr[:500] if result.stderr else ""}, "D")
        except FileNotFoundError as e:
            _dbg("remotion_cli.py:render", "subprocess_filenotfound", {"error": str(e), "cmd0": cmd[0]}, "A")
            raise
        except Exception as e:
            _dbg("remotion_cli.py:render", "subprocess_error", {"error": str(e), "error_type": type(e).__name__}, "E")
            raise
        # #endregion

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

