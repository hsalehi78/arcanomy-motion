"""Stage 7: Final Video Assembly - Stitch video, voice, and SFX using FFmpeg.

This is a Dumb Script stage that:
1. Reads all generated video clips, voice audio, and SFX audio
2. Mixes voice + SFX audio for each clip (voice centered, SFX at 25%)
3. Combines mixed audio with video
4. Concatenates all clips into final video
"""

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from src.utils.io import write_file
from src.utils.logger import get_logger
from src.utils.paths import json_path, prompt_path, sfx_dir as reel_sfx_dir, videos_dir as reel_videos_dir, voice_dir as reel_voice_dir

logger = get_logger()

# Default configuration
DEFAULT_SFX_VOLUME = 0.25  # SFX at 25% volume
DEFAULT_VOICE_VOLUME = 1.0  # Voice at 100% volume
DEFAULT_CLIP_DURATION = 10.0  # Each clip is 10 seconds
AUDIO_BITRATE = "192k"


def check_ffmpeg() -> tuple[bool, str]:
    """Check if FFmpeg is installed and available.
    
    Returns:
        Tuple of (is_available, version_string)
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return True, version_line
        return False, "FFmpeg returned non-zero exit code"
    except FileNotFoundError:
        return False, "FFmpeg not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "FFmpeg check timed out"
    except Exception as e:
        return False, str(e)


def get_audio_duration(audio_path: Path) -> float:
    """Get duration of an audio file using ffprobe.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0.0
    except Exception as e:
        logger.warning(f"Could not get duration for {audio_path}: {e}")
        return 0.0


def create_centered_voice(
    voice_path: Path,
    output_path: Path,
    clip_duration: float = DEFAULT_CLIP_DURATION,
) -> bool:
    """Create a voice track centered within the clip duration.
    
    Adds silence padding before and after the voice to center it.
    
    Args:
        voice_path: Path to original voice audio
        output_path: Path for output centered audio
        clip_duration: Total duration to center within
        
    Returns:
        True if successful
    """
    voice_duration = get_audio_duration(voice_path)
    if voice_duration <= 0:
        logger.warning(f"Could not get voice duration for {voice_path}")
        voice_duration = 8.0  # Fallback assumption
    
    # Calculate padding needed
    padding = (clip_duration - voice_duration) / 2.0
    if padding < 0:
        padding = 0  # Voice is longer than clip, no padding needed
    
    try:
        # FFmpeg command to add silence padding before and after
        # Uses concat filter with generated silence
        cmd = [
            "ffmpeg", "-y",
            # Generate silence before
            "-f", "lavfi", "-t", str(padding),
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            # Original voice audio
            "-i", str(voice_path),
            # Generate silence after
            "-f", "lavfi", "-t", str(padding),
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            # Concat filter
            "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[centered]",
            "-map", "[centered]",
            "-t", str(clip_duration),
            "-acodec", "libmp3lame", "-b:a", AUDIO_BITRATE,
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error creating centered voice: {e}")
        return False


def mix_audio_tracks(
    voice_path: Path,
    sfx_path: Path,
    output_path: Path,
    voice_volume: float = DEFAULT_VOICE_VOLUME,
    sfx_volume: float = DEFAULT_SFX_VOLUME,
    duration: float = DEFAULT_CLIP_DURATION,
) -> bool:
    """Mix voice and SFX audio tracks together.
    
    Args:
        voice_path: Path to centered voice audio
        sfx_path: Path to SFX audio
        output_path: Path for mixed output
        voice_volume: Volume for voice (0-1)
        sfx_volume: Volume for SFX (0-1)
        duration: Output duration
        
    Returns:
        True if successful
    """
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(voice_path),
            "-i", str(sfx_path),
            "-filter_complex",
            f"[0:a]volume={voice_volume}[voice];[1:a]volume={sfx_volume}[sfx];[voice][sfx]amix=inputs=2:duration=first[mixed]",
            "-map", "[mixed]",
            "-t", str(duration),
            "-acodec", "libmp3lame", "-b:a", AUDIO_BITRATE,
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            logger.error(f"FFmpeg mix error: {result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error mixing audio: {e}")
        return False


def combine_video_audio(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    duration: float = DEFAULT_CLIP_DURATION,
) -> bool:
    """Combine video with audio track.
    
    Args:
        video_path: Path to video file
        audio_path: Path to mixed audio
        output_path: Path for output video
        duration: Output duration
        
    Returns:
        True if successful
    """
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",  # Copy video codec (no re-encode)
            "-c:a", "aac", "-b:a", AUDIO_BITRATE,
            "-map", "0:v:0", "-map", "1:a:0",
            "-t", str(duration),
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.error(f"FFmpeg combine error: {result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error combining video/audio: {e}")
        return False


def concatenate_clips(
    clip_paths: list[Path],
    output_path: Path,
    working_dir: Path,
) -> bool:
    """Concatenate multiple video clips into one.
    
    Args:
        clip_paths: List of video clip paths in order
        output_path: Path for final output video
        working_dir: Working directory for concat list file
        
    Returns:
        True if successful
    """
    # Create concat list file
    concat_list_path = working_dir / "concat_list.txt"
    
    # Use relative paths from working_dir
    concat_content = ""
    for clip_path in clip_paths:
        # Get relative path from working_dir
        try:
            rel_path = clip_path.relative_to(working_dir)
        except ValueError:
            # If not relative, use absolute
            rel_path = clip_path
        concat_content += f"file '{rel_path}'\n"
    
    concat_list_path.write_text(concat_content)
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_path),
            "-c", "copy",
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(working_dir)  # Run from working directory
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg concat error: {result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error concatenating clips: {e}")
        return False


def run_final_assembly(
    reel_path: Path,
    sfx_volume: float = DEFAULT_SFX_VOLUME,
    voice_volume: float = DEFAULT_VOICE_VOLUME,
    dry_run: bool = False,
    cleanup: bool = True,
) -> dict:
    """Assemble final video from clips, voice, and SFX.
    
    Two-stage process:
    1. Mix individual clips (video + voice + SFX)
    2. Concatenate all mixed clips into final video
    
    Args:
        reel_path: Path to the reel folder
        sfx_volume: Volume for sound effects (0-1, default 0.25)
        voice_volume: Volume for voice (0-1, default 1.0)
        dry_run: If True, only validate files without processing
        cleanup: If True, remove intermediate files after completion
        
    Returns:
        Assembly result dictionary
    """
    execution_log = []
    
    # Step 1: Check FFmpeg
    execution_log.append("## Prerequisites Check")
    ffmpeg_ok, ffmpeg_version = check_ffmpeg()
    
    if not ffmpeg_ok:
        execution_log.append(f"❌ FFmpeg not found: {ffmpeg_version}")
        execution_log.append("\nInstallation instructions:")
        execution_log.append("- **Windows:** Download from https://ffmpeg.org/download.html")
        execution_log.append("- **macOS:** `brew install ffmpeg`")
        execution_log.append("- **Ubuntu:** `sudo apt-get install ffmpeg`")
        
        _save_execution_log(reel_path, execution_log, dry_run, {
            "status": "failed",
            "error": "FFmpeg not installed"
        })
        return {"status": "failed", "error": "FFmpeg not installed"}
    
    execution_log.append(f"✅ FFmpeg: {ffmpeg_version}")
    
    # Step 2: Scan for required files
    execution_log.append("\n## File Scan")
    
    videos_dir = reel_videos_dir(reel_path)
    voice_dir = reel_voice_dir(reel_path)
    sfx_dir = reel_sfx_dir(reel_path)
    
    # Find video clips
    video_files = sorted(videos_dir.glob("clip_*.mp4"))
    voice_files = sorted(voice_dir.glob("voice_*.mp3"))
    sfx_files = sorted(sfx_dir.glob("clip_*_sfx.mp3"))
    
    execution_log.append(f"- Video clips found: {len(video_files)}")
    execution_log.append(f"- Voice files found: {len(voice_files)}")
    execution_log.append(f"- SFX files found: {len(sfx_files)}")
    
    # Determine number of clips from available files
    num_clips = min(len(video_files), len(voice_files), len(sfx_files))
    
    if num_clips == 0:
        execution_log.append("\n❌ No complete clip sets found!")
        execution_log.append("Ensure you have video, voice, and SFX for each clip.")
        
        _save_execution_log(reel_path, execution_log, dry_run, {
            "status": "failed",
            "error": "No complete clip sets found"
        })
        return {"status": "failed", "error": "No complete clip sets found"}
    
    # Build matched file sets
    clips = []
    missing = {"video": [], "voice": [], "sfx": []}
    
    for i in range(1, num_clips + 1):
        clip_id = f"{i:02d}"
        video_path = videos_dir / f"clip_{clip_id}.mp4"
        voice_path = voice_dir / f"voice_{clip_id}.mp3"
        sfx_path = sfx_dir / f"clip_{clip_id}_sfx.mp3"
        
        # Check existence
        has_video = video_path.exists()
        has_voice = voice_path.exists()
        has_sfx = sfx_path.exists()
        
        if not has_video:
            missing["video"].append(f"clip_{clip_id}.mp4")
        if not has_voice:
            missing["voice"].append(f"voice_{clip_id}.mp3")
        if not has_sfx:
            missing["sfx"].append(f"clip_{clip_id}_sfx.mp3")
        
        if has_video and has_voice and has_sfx:
            clips.append({
                "id": i,
                "video": video_path,
                "voice": voice_path,
                "sfx": sfx_path,
            })
    
    # Report missing files
    has_missing = any(missing.values())
    if has_missing:
        execution_log.append("\n⚠️ Missing files:")
        for category, files in missing.items():
            if files:
                for f in files:
                    execution_log.append(f"  - {category}: {f}")
    
    execution_log.append(f"\n✅ Complete clip sets: {len(clips)}")
    
    if len(clips) == 0:
        _save_execution_log(reel_path, execution_log, dry_run, {
            "status": "failed", 
            "error": "No complete clip sets available"
        })
        return {"status": "failed", "error": "No complete clip sets available"}
    
    if dry_run:
        execution_log.append("\n## Dry Run Mode")
        execution_log.append("Would process the following clips:")
        for clip in clips:
            execution_log.append(f"  - Clip {clip['id']:02d}")
        
        _save_execution_log(reel_path, execution_log, dry_run, {
            "status": "dry_run",
            "clips": len(clips)
        })
        return {"status": "dry_run", "clips": len(clips)}
    
    # Step 3: Create output directories
    final_dir = reel_path / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 4: Stage 1 - Mix individual clips
    execution_log.append("\n## Stage 1: Mixing Individual Clips")
    
    mixed_clips = []
    results = []
    
    for clip in clips:
        clip_id = clip["id"]
        execution_log.append(f"\n### Clip {clip_id:02d}")
        
        # Paths for intermediate files
        centered_path = final_dir / f"clip_{clip_id:02d}_centered.mp3"
        mixed_audio_path = final_dir / f"clip_{clip_id:02d}_mixed_audio.mp3"
        final_clip_path = final_dir / f"clip_{clip_id:02d}_final.mp4"
        
        clip_result = {
            "clip_id": clip_id,
            "video": str(clip["video"]),
            "voice": str(clip["voice"]),
            "sfx": str(clip["sfx"]),
            "output": str(final_clip_path),
        }
        
        try:
            # Step 4.1: Get voice duration
            voice_duration = get_audio_duration(clip["voice"])
            execution_log.append(f"- Voice duration: {voice_duration:.2f}s")
            
            # Step 4.2: Create centered voice
            if not create_centered_voice(clip["voice"], centered_path):
                raise RuntimeError("Failed to create centered voice")
            execution_log.append("- ✅ Centered voice created")
            
            # Step 4.3: Mix voice + SFX
            if not mix_audio_tracks(
                centered_path, 
                clip["sfx"], 
                mixed_audio_path,
                voice_volume=voice_volume,
                sfx_volume=sfx_volume
            ):
                raise RuntimeError("Failed to mix audio tracks")
            execution_log.append(f"- ✅ Audio mixed (voice={voice_volume*100:.0f}%, sfx={sfx_volume*100:.0f}%)")
            
            # Step 4.4: Combine with video
            if not combine_video_audio(clip["video"], mixed_audio_path, final_clip_path):
                raise RuntimeError("Failed to combine video and audio")
            execution_log.append(f"- ✅ Video combined: {final_clip_path.name}")
            
            # Cleanup intermediate files
            if cleanup:
                centered_path.unlink(missing_ok=True)
                mixed_audio_path.unlink(missing_ok=True)
            
            mixed_clips.append(final_clip_path)
            clip_result["status"] = "success"
            clip_result["voice_duration"] = voice_duration
            
            logger.info(f"[OK] Clip {clip_id:02d}/{len(clips)} mixed successfully ({voice_duration:.1f}s voice centered)")
            
        except Exception as e:
            clip_result["status"] = "failed"
            clip_result["error"] = str(e)
            execution_log.append(f"- ❌ FAILED: {e}")
            logger.error(f"[!!] Clip {clip_id:02d}: Failed - {e}")
        
        results.append(clip_result)
    
    # Step 5: Stage 2 - Concatenate all clips
    execution_log.append("\n## Stage 2: Concatenating Clips")
    
    if len(mixed_clips) == 0:
        execution_log.append("❌ No clips to concatenate")
        _save_execution_log(reel_path, execution_log, dry_run, {
            "status": "failed",
            "error": "No clips were successfully mixed"
        })
        return {"status": "failed", "error": "No clips were successfully mixed"}
    
    # Final output filename is fixed (final/final_raw.mp4). Keep reel_name for logs/UI.
    reel_name = reel_path.name
    
    # This file is the audio-correct base video (voice centered + SFX mixed).
    # A later stage may burn captions into final/final.mp4.
    final_video_path = final_dir / "final_raw.mp4"
    
    if len(mixed_clips) == 1:
        # Single clip - just copy it
        execution_log.append("- Single clip, copying to final_raw.mp4")
        shutil.copy2(mixed_clips[0], final_video_path)
        concat_success = True
    else:
        # Multiple clips - concatenate
        execution_log.append(f"- Concatenating {len(mixed_clips)} clips...")
        concat_success = concatenate_clips(mixed_clips, final_video_path, final_dir)
    
    if not concat_success:
        execution_log.append("❌ Concatenation failed")
        _save_execution_log(reel_path, execution_log, dry_run, {
            "status": "failed",
            "error": "Concatenation failed"
        })
        return {"status": "failed", "error": "Concatenation failed"}
    
    execution_log.append("✅ Final video created")
    
    # Step 6: Verify output
    execution_log.append("\n## Final Output")
    
    final_duration = get_audio_duration(final_video_path)  # Works for video too
    final_size = final_video_path.stat().st_size if final_video_path.exists() else 0
    final_size_mb = final_size / (1024 * 1024)
    
    execution_log.append(f"- 📁 Location: {final_video_path}")
    execution_log.append(f"- ⏱️ Duration: {final_duration:.1f} seconds ({final_duration/60:.1f} minutes)")
    execution_log.append(f"- 💾 File Size: {final_size_mb:.2f} MB")
    
    # Cleanup individual mixed clips if not keeping
    if cleanup:
        execution_log.append("\n## Cleanup")
        concat_list = final_dir / "concat_list.txt"
        concat_list.unlink(missing_ok=True)
        
        for clip_path in mixed_clips:
            clip_path.unlink(missing_ok=True)
            execution_log.append(f"- Removed: {clip_path.name}")
    
    # Build final result
    success_count = sum(1 for r in results if r.get("status") == "success")
    failed_count = sum(1 for r in results if r.get("status") == "failed")
    
    output_result = {
        "status": "success",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "clips_processed": len(clips),
        "clips_successful": success_count,
        "clips_failed": failed_count,
        "audio_settings": {
            "voice_volume": voice_volume,
            "sfx_volume": sfx_volume,
        },
        "final_video": {
            "path": str(final_video_path),
            "duration_seconds": final_duration,
            "size_bytes": final_size,
            "size_mb": round(final_size_mb, 2),
        },
        "clip_results": results,
    }
    
    _save_execution_log(reel_path, execution_log, dry_run, output_result)
    
    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("FINAL ASSEMBLY COMPLETE")
    logger.info("=" * 60)
    logger.info(f"[OK] Clips processed: {success_count}/{len(clips)}")
    logger.info(f"Output: {final_video_path}")
    logger.info(f"Duration: {final_duration:.1f}s")
    logger.info(f"Size: {final_size_mb:.2f} MB")
    logger.info("=" * 60)
    
    return output_result


def _save_execution_log(
    reel_path: Path,
    execution_log: list[str],
    dry_run: bool,
    result: dict,
) -> None:
    """Save execution log and result files."""
    # Save input/execution log
    input_path = prompt_path(reel_path, "07_final.input.md")
    log_content = f"""# Final Assembly Execution Log

Generated: {datetime.now(timezone.utc).isoformat()}
Mode: {"Dry Run" if dry_run else "Live Execution"}

{chr(10).join(execution_log)}
"""
    write_file(input_path, log_content)
    
    # Save output JSON
    output_path = json_path(reel_path, "07_final.output.json")
    write_file(output_path, json.dumps(result, indent=2))

