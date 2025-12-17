# 04 — Pipeline Stages (Detailed)

## Philosophy: Granular Audit Trail

We strictly follow the **"Smart Agent + Dumb Scripts"** model. The pipeline is broken down into granular steps. Each step has a clear **Input** (Prompt) and **Output** (Result).

The state of a reel is defined entirely by the files in its folder. To "resume" a reel, the orchestrator simply checks which files already exist.

---

## The Pipeline

### Stage 0: Initialization
**Manual Input by User.**
- `00_seed.md`: The creative spark, concept, or raw notes.
- `00_reel.yaml`: Configuration (Duration, Voice ID, Music Vibe).
- `00_data/`: Optional CSV files for data-driven reels.

---

### Stage 1: Research
**Goal:** Ground the seed concept in facts and identify the "angle".
- **Agent Action:** Reads seed + data. Browses web (if enabled). Generates a research summary.
- **Files:**
  - `01_research.input.md` (The prompt sent to the LLM)
  - `01_research.output.md` (The research notes and key takeaways)

---

### Stage 2: Story & Segmentation
**Goal:** Write the script and divide it into 10s blocks.
- **Agent Action:** writes a voiceover script and splits it into strict time blocks.
- **Files:**
  - `02_story_generator.input.md`
  - `02_story_generator.output.md` (Human-readable script)
  - `02_story_generator.output.json` **(CRITICAL)**: Structured list of segments.
    ```json
    [
      { "id": 1, "duration": 10, "text": "...", "visual_intent": "..." },
      { "id": 2, "duration": 10, "text": "...", "visual_intent": "..." }
    ]
    ```

---

### Stage 3: Visual & Character Planning
**Goal:** Define the visual language before generating pixels.
- **Agent Action:** Describes the characters, setting, and style.
- **Files:**
  - `03_character_generation.input.md`
  - `03_character_generation.output.md` (Character/Style bios)

---

### Stage 3.5: Asset Prompt Generation (Images)
**Goal:** Create the exact prompts for image generation (Nano Banana pro, IMAG 2.5 from ChptGPT).
- **Agent Action:** Converts "visual intent" from Stage 2 + style from Stage 3 into engineering prompts.
- **Files:**
  - `03.5_generate_assets_agent.input.md`
  - `03.5_generate_assets_agent.output.json`: List of prompts per segment.
    ```json
    [
      { "segment_id": 1, "prompt": "Cinematic shot of...", "type": "image" }
    ]
    ```

---

### Stage 4: Video Prompt Engineering
**Goal:** Create the motion prompts for video models (Kling/Runway/Veo 3.1 etc).
- **Agent Action:** Defines *how* the static images should move.
- **Files:**
  - `04_video_prompt_engineering.input.md`
  - `04_video_prompt_engineering.output.md`

---

### Stage 4.5: Video Generation (The "Dumb Script")
**Goal:** Execute the generation.
- **Script Action:** Reads `03.5...json` and `04...md`. Calls Video APIs. Downloads results.
- **Files:**
  - `04.5_generate_videos_agent.input.md` (Logs of the execution plan)
  - `04.5_generate_videos_agent.output.json`: Map of segment IDs to file paths.
  - **Artifacts:** `renders/bg_01.mp4`, `renders/bg_02.mp4`...

---

### Stage 5: Voice Prompting
**Goal:** Define *how* the lines should be read (prosody, emotion).
- **Agent Action:** Annotates the script with direction tags.
- **Files:**
  - `05_voice_prompt_engineer.input.md`
  - `05_voice_prompt_engineer.output.md`

---

### Stage 5.5: Audio Generation (The "Dumb Script")
**Goal:** Generate speech.
- **Script Action:** Calls ElevenLabs API.
- **Files:**
  - `05.5_generate_audio_agent.input.md`
  - `05.5_generate_audio_agent.output.json`
  - **Artifacts:** `renders/voice_full.mp3` or `renders/voice_01.mp3`...

---

### Stage 6: Music & SFX
**Goal:** Select background track and sound effects.
- **Files:**
  - `06_music.input.md`
  - `06_music.output.json` (Selected track path / SFX list)

---

### Stage 7: Assembly & Rendering
**Goal:** Put it all together.
- **Action:** Orchestrator creates a "Manifest" for Remotion.
- **Files:**
  - `07_assemble_final_agent.input.md`
  - `07_assemble_final_agent.output.json` (The Timeline sent to Remotion)
- **Final Output:**
  - `final/final.mp4`
  - `final/final.srt`
  - `final/metadata.json`

---

## Resuming & Debugging

- **To Debug:** Open any `.input.md` file to see exactly what the agent was asked. Open `.output.md` to see what it said.
- **To Resume:** The system looks for the last existing `.output.json`. If `03.5...json` exists but `04...output.md` does not, it starts at Stage 4.
- **To Retry:** Delete the `.output.*` files of the stage you want to re-run.
