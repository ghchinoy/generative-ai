#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Compiles Browser Recording Telemetry and TTS Audio into Remotion Video Props.

Merges `actions.json` and `narration_manifest.json` into `video_props.json`.
Calculates exact frame timelines (30fps), 4x-5x wait-time acceleration, dynamic camera
coordinates (zoom/pan), synchronized subtitle tracks, and audio ducking schedules.
"""

import argparse
import json
import os
import subprocess
import sys

FPS = 30
INTRO_DURATION_SEC = 3.0
OUTRO_DURATION_SEC = 3.0
FAST_FORWARD_FACTOR = 4.0


def build_manifest(actions_path: str, narration_path: str, output_path: str, enable_narration: bool = True, enable_subtitles: bool = True, enable_bgm: bool = False, bgm_file: str = "bgm.mp3") -> dict:
    """Builds complete Remotion composition props JSON."""
    with open(actions_path, "r", encoding="utf-8") as f:
        actions_data = json.load(f)

    with open(narration_path, "r", encoding="utf-8") as f:
        narration_data = json.load(f)

    company = narration_data.get("company", "Enterprise")
    role = narration_data.get("role", "AI Operations Director")
    lang = narration_data.get("language", "en-US")
    raw_video_path = actions_data.get("raw_video_path", "raw_recording.mp4")

    # Map narration scenes by scene_id
    narration_by_id = {s["scene_id"]: s for s in narration_data.get("scenes", [])}

    current_frame = 0
    timeline_scenes = []
    audio_clips = []
    all_subtitles = []

    # 1. Intro Card
    intro_narration = narration_by_id.get("intro")
    intro_dur_sec = max(INTRO_DURATION_SEC, intro_narration.get("duration_sec", INTRO_DURATION_SEC) + 0.8) if intro_narration else INTRO_DURATION_SEC
    intro_frames = int(intro_dur_sec * FPS)
    if intro_narration and intro_narration.get("audio_file"):
        audio_clips.append({
            "id": "audio_intro",
            "file": intro_narration["audio_file"],
            "startFrame": current_frame + 10,
            "durationFrames": int(intro_narration.get("duration_sec", INTRO_DURATION_SEC) * FPS)
        })
        for sub in intro_narration.get("subtitles", []):
            all_subtitles.append({
                "startFrame": current_frame + 10 + int(sub["start_sec"] * FPS),
                "endFrame": current_frame + 10 + int(sub["end_sec"] * FPS),
                "text": sub["text"]
            })

    timeline_scenes.append({
        "id": "scene_intro",
        "type": "intro_card",
        "title": company,
        "subtitle": f"{role} Demo",
        "startFrame": current_frame,
        "durationFrames": intro_frames,
        "camera": {
            "typing": {"x": 960, "y": 540, "scale": 1.0},
            "response": {"x": 960, "y": 540, "scale": 1.0},
            "overview": {"x": 960, "y": 540, "scale": 1.0}
        }
    })
    current_frame += intro_frames

    # 1.5 Agenda Card (Scenario Overview)
    agenda_narration = narration_by_id.get("agenda")
    if agenda_narration:
        agenda_dur_sec = max(3.5, agenda_narration.get("duration_sec", 3.5) + 0.8)
        agenda_frames = int(agenda_dur_sec * FPS)
        if agenda_narration.get("audio_file"):
            audio_clips.append({
                "id": "audio_agenda",
                "file": agenda_narration["audio_file"],
                "startFrame": current_frame + 10,
                "durationFrames": int(agenda_narration.get("duration_sec", 3.5) * FPS)
            })
        for sub in agenda_narration.get("subtitles", []):
            all_subtitles.append({
                "startFrame": current_frame + 10 + int(sub["start_sec"] * FPS),
                "endFrame": current_frame + 10 + int(sub["end_sec"] * FPS),
                "text": sub["text"]
            })

        timeline_scenes.append({
            "id": "scene_agenda",
            "type": "agenda_card",
            "title": agenda_narration.get("title") or "Walkthrough Agenda",
            "subtitle": f"{company} — {role}",
            "startFrame": current_frame,
            "durationFrames": agenda_frames,
            "camera": {
                "typing": {"x": 960, "y": 540, "scale": 1.0},
                "response": {"x": 960, "y": 540, "scale": 1.0},
                "overview": {"x": 960, "y": 540, "scale": 1.0}
            }
        })
        current_frame += agenda_frames

    # 2. Main Recorded Action Scenes (P1, P3, P4)
    actions = actions_data.get("actions", [])
    for idx, act in enumerate(actions):
        scene_id = act.get("scene_id", f"prompt_{idx + 1}")
        scene_narr = narration_by_id.get(scene_id)
        if not scene_narr:
            content_narration = [s for s in narration_data.get("scenes", []) if s["scene_id"] not in ("intro", "outro", "agenda")]
            if idx < len(content_narration):
                scene_narr = content_narration[idx]

        t_type_start = act.get("t_type_start", 0.0)
        t_type_end = act.get("t_type_end", 3.0)
        t_submit = act.get("t_submit", t_type_end + 0.5)
        t_resp_comp = act.get("t_response_complete", t_submit + 5.0)

        # Raw end of this scene in raw_recording.mp4
        if idx + 1 < len(actions):
            t_scene_raw_end = actions[idx + 1].get("t_type_start", t_resp_comp + 10.0)
        else:
            t_scene_raw_end = actions_data.get("total_duration_sec", t_resp_comp + 15.0)

        # Timeline segments for this scene:
        dur_typing_sec = max(1.5, t_submit - t_type_start)
        t_wait_start = act.get("t_wait_start", t_submit)
        t_wait_end = act.get("t_response_start", t_resp_comp)
        raw_wait_sec = max(0.5, t_wait_end - t_wait_start)
        ff_wait_sec = raw_wait_sec / FAST_FORWARD_FACTOR
        raw_recorded_resp_sec = max(4.0, t_scene_raw_end - t_resp_comp)

        phases = scene_narr.get("phases") if scene_narr else None
        if phases and "response" in phases:
            dur_lead_sec = phases["lead"].get("duration_sec", 4.0)
            dur_think_sec = phases["thinking"].get("duration_sec", 6.0)
            dur_resp_narr_sec = phases["response"].get("duration_sec", 18.0)
            dur_resp_sec = max(dur_resp_narr_sec + 3.0, raw_recorded_resp_sec, 16.0)
        else:
            dur_resp_sec = max(scene_narr.get("duration_sec", 14.0) + 3.0, raw_recorded_resp_sec, 16.0) if scene_narr else raw_recorded_resp_sec

        typing_frames = int(dur_typing_sec * FPS)
        ff_frames = int(ff_wait_sec * FPS)
        resp_frames = int(dur_resp_sec * FPS)

        # Audio scheduling
        if phases and "response" in phases:
            lead_start_frame = current_frame
            lead_dur_frames = int(dur_lead_sec * FPS)

            think_start_frame = max(current_frame + typing_frames, lead_start_frame + lead_dur_frames + 5)
            think_dur_frames = int(dur_think_sec * FPS)

            resp_start_frame = max(current_frame + typing_frames + ff_frames, think_start_frame + think_dur_frames + 5)
            resp_dur_frames = int(dur_resp_narr_sec * FPS)

            needed_resp_frames = (resp_start_frame - (current_frame + typing_frames + ff_frames)) + resp_dur_frames + int(2.5 * FPS)
            if needed_resp_frames > resp_frames:
                resp_frames = needed_resp_frames
                dur_resp_sec = resp_frames / FPS

        scene_frames = typing_frames + ff_frames + resp_frames

        # Camera focus:
        focus_rect = act.get("focus_rect", {"x": 480, "y": 420, "width": 960, "height": 450})
        center_x = focus_rect["x"] + focus_rect["width"] / 2
        center_y = focus_rect["y"] + focus_rect["height"] / 2

        camera_dict = {
            "typing": {"x": 960, "y": 920, "scale": 1.50},
            "response": {"x": center_x, "y": center_y, "scale": 1.10},
            "overview": {"x": 960, "y": 540, "scale": 1.0}
        }
        action_click = act.get("action_click")
        if action_click and "x" in action_click and "y" in action_click:
            camera_dict["button"] = {
                "x": action_click["x"],
                "y": action_click["y"],
                "scale": 1.45
            }

        scene_item = {
            "id": scene_id,
            "type": "browser_screen",
            "title": act.get("title", f"Scene {idx + 1}"),
            "startFrame": current_frame,
            "durationFrames": scene_frames,
            "rawVideoTime": {
                "startSec": t_type_start,
                "typingEndSec": t_submit,
                "thinkingEndSec": t_resp_comp,
                "completeSec": t_scene_raw_end
            },
            "fastForward": {
                "startFrame": current_frame + int(dur_typing_sec * FPS),
                "durationFrames": int(ff_wait_sec * FPS),
                "factor": FAST_FORWARD_FACTOR
            },
            "camera": camera_dict
        }
        if action_click:
            scene_item["actionClick"] = action_click

        timeline_scenes.append(scene_item)

        # Add voice narration clips and subtitles
        if phases and "response" in phases:
            lead_info = phases["lead"]
            think_info = phases["thinking"]
            resp_info = phases["response"]

            if lead_info.get("audio_file"):
                audio_clips.append({
                    "id": f"audio_{scene_id}_lead",
                    "file": lead_info["audio_file"],
                    "startFrame": lead_start_frame,
                    "durationFrames": lead_dur_frames
                })
                for sub in lead_info.get("subtitles", []):
                    all_subtitles.append({
                        "startFrame": lead_start_frame + int(sub["start_sec"] * FPS),
                        "endFrame": lead_start_frame + int(sub["end_sec"] * FPS),
                        "text": sub["text"],
                        "position": "top"
                    })

            if think_info.get("audio_file"):
                audio_clips.append({
                    "id": f"audio_{scene_id}_think",
                    "file": think_info["audio_file"],
                    "startFrame": think_start_frame,
                    "durationFrames": think_dur_frames
                })
                for sub in think_info.get("subtitles", []):
                    all_subtitles.append({
                        "startFrame": think_start_frame + int(sub["start_sec"] * FPS),
                        "endFrame": think_start_frame + int(sub["end_sec"] * FPS),
                        "text": sub["text"],
                        "position": "bottom"
                    })

            if resp_info.get("audio_file"):
                audio_clips.append({
                    "id": f"audio_{scene_id}_resp",
                    "file": resp_info["audio_file"],
                    "startFrame": resp_start_frame,
                    "durationFrames": resp_dur_frames
                })
                for sub in resp_info.get("subtitles", []):
                    all_subtitles.append({
                        "startFrame": resp_start_frame + int(sub["start_sec"] * FPS),
                        "endFrame": resp_start_frame + int(sub["end_sec"] * FPS),
                        "text": sub["text"],
                        "position": "bottom"
                    })
        elif scene_narr and scene_narr.get("audio_file"):
            narr_start_frame = current_frame
            typing_end_frame = current_frame + int(dur_typing_sec * FPS)
            audio_clips.append({
                "id": f"audio_{scene_id}",
                "file": scene_narr["audio_file"],
                "startFrame": narr_start_frame,
                "durationFrames": int(scene_narr.get("duration_sec", 10.0) * FPS)
            })
            for sub in scene_narr.get("subtitles", []):
                sub_start = narr_start_frame + int(sub["start_sec"] * FPS)
                sub_end = narr_start_frame + int(sub["end_sec"] * FPS)
                pos = "top" if sub_start < typing_end_frame else "bottom"
                all_subtitles.append({
                    "startFrame": sub_start,
                    "endFrame": sub_end,
                    "text": sub["text"],
                    "position": pos
                })

        current_frame += scene_frames

    # 3. Outro Card
    outro_narration = narration_by_id.get("outro")
    outro_dur_sec = max(OUTRO_DURATION_SEC, outro_narration.get("duration_sec", OUTRO_DURATION_SEC) + 0.8) if outro_narration else OUTRO_DURATION_SEC
    outro_frames = int(outro_dur_sec * FPS)
    if outro_narration and outro_narration.get("audio_file"):
        audio_clips.append({
            "id": "audio_outro",
            "file": outro_narration["audio_file"],
            "startFrame": current_frame + 10,
            "durationFrames": int(outro_narration.get("duration_sec", OUTRO_DURATION_SEC) * FPS)
        })
        for sub in outro_narration.get("subtitles", []):
            all_subtitles.append({
                "startFrame": current_frame + 10 + int(sub["start_sec"] * FPS),
                "endFrame": current_frame + 10 + int(sub["end_sec"] * FPS),
                "text": sub["text"]
            })

    timeline_scenes.append({
        "id": "scene_outro",
        "type": "outro_card",
        "title": f"Gemini Enterprise for {company}",
        "subtitle": "Next Step: Explore your custom agents today",
        "startFrame": current_frame,
        "durationFrames": outro_frames,
        "camera": {
            "typing": {"x": 960, "y": 540, "scale": 1.0},
            "response": {"x": 960, "y": 540, "scale": 1.0},
            "overview": {"x": 960, "y": 540, "scale": 1.0}
        }
    })
    current_frame += outro_frames

    total_duration_sec = round(current_frame / FPS, 2)

    # Build dynamic agenda items from actions
    agenda_items = []
    icon_map = {
        "welcome": "💬",
        "catalog": "📦",
        "analytics_wow": "📊",
        "workflow_action": "⚡",
        "investigation": "🔍",
        "simulation": "📈",
        "summary": "📝",
    }
    default_icons = ["💬", "📦", "📊", "⚡", "🔍", "📈", "📝"]
    for idx, act in enumerate(actions):
        s_type = act.get("scene_type", "")
        icon = icon_map.get(s_type, default_icons[idx % len(default_icons)])
        title = act.get("title", f"Scene {idx + 1}")
        clean_title = title.split(":", 1)[-1].strip() if ":" in title else title
        prompt_snippet = act.get("prompt_text", "")
        clean_subtitle = prompt_snippet[:60] + ("..." if len(prompt_snippet) > 60 else "")
        agenda_items.append({
            "number": idx + 1,
            "title": clean_title,
            "subtitle": clean_subtitle,
            "icon": icon,
        })

    props = {
        "company": company,
        "role": role,
        "fps": FPS,
        "width": 1920,
        "height": 1080,
        "totalFrames": current_frame,
        "totalDurationSec": total_duration_sec,
        "rawVideoFile": os.path.basename(raw_video_path),
        "scenes": timeline_scenes,
        "audioClips": audio_clips,
        "subtitles": all_subtitles,
        "agendaItems": agenda_items,
        "enableNarration": enable_narration,
        "enableSubtitles": enable_subtitles,
        "enableBgm": enable_bgm,
        "bgmFile": bgm_file,
    }

    if enable_bgm:
        bgm_candidates = [
            os.path.join(os.path.dirname(os.path.abspath(output_path)), "public/audio", bgm_file),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public/audio", bgm_file),
        ]
        for p in bgm_candidates:
            if os.path.exists(p):
                try:
                    probe = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", p],
                        capture_output=True, text=True
                    )
                    dur = float(probe.stdout.strip())
                    if dur > 0:
                        props["bgmDurationFrames"] = int(dur * FPS)
                        break
                except Exception:
                    pass

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(props, f, indent=2, ensure_ascii=False)

    print(f"🎬 Video manifest created: {output_path}")
    print(f"   Total Composition Duration: {total_duration_sec}s ({current_frame} frames @ {FPS}fps)")
    print(f"   Scenes: {len(timeline_scenes)} | Audio Clips: {len(audio_clips)} | Subtitles: {len(all_subtitles)} | BGM: {enable_bgm}")
    return props


def main():
    parser = argparse.ArgumentParser(description="Build Remotion video properties from actions and narration.")
    parser.add_argument("--actions", required=True, help="Path to actions.json")
    parser.add_argument("--narration", required=True, help="Path to narration_manifest.json")
    parser.add_argument("--output", default="./output/video_props.json", help="Path to write video_props.json")
    parser.add_argument("--no-narration", action="store_true", help="Disable voice narration audio tracks")
    parser.add_argument("--no-subtitles", action="store_true", help="Disable subtitle overlays")
    parser.add_argument("--enable-bgm", action="store_true", help="Enable ambient background music track")
    parser.add_argument("--bgm-file", default="bgm.mp3", help="Background music audio filename")
    args = parser.parse_args()

    build_manifest(
        args.actions,
        args.narration,
        args.output,
        enable_narration=not args.no_narration,
        enable_subtitles=not args.no_subtitles,
        enable_bgm=args.enable_bgm,
        bgm_file=args.bgm_file
    )


if __name__ == "__main__":
    main()
