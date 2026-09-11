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

"""Generates Professional Ambient Background Music (BGM) for Demo Videos.

Dual-Engine Architecture:
1. Primary: Vertex AI Agent Platform Lyria API with dynamic domain/industry prompt engineering.
2. Fallback: Autonomous offline mathematical audio synthesizer (Python + FFmpeg)
   generating a warm corporate ambient chord progression loop with zero external dependencies.
"""

import argparse
import base64
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import urllib.error
import urllib.request
import wave


def get_gcp_project_id(explicit_project: str = "") -> str:
    """Resolves active Google Cloud project ID."""
    if explicit_project:
        return explicit_project
    proj = os.environ.get("PROJECT_ID", "")
    if proj:
        return proj
    try:
        res = subprocess.run(["gcloud", "config", "get-value", "project"], capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return ""


def get_gcp_access_token() -> str:
    """Retrieves access token via gcloud auth."""
    try:
        res = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return ""


def ensure_aiplatform_api(project_id: str) -> bool:
    """Ensures Vertex AI Agent Platform API (aiplatform.googleapis.com) is enabled on the target project."""
    if not project_id:
        return False
    try:
        # Check if already enabled
        check_cmd = [
            "gcloud", "services", "list",
            "--enabled",
            f"--project={project_id}",
            "--filter=name:aiplatform.googleapis.com",
            "--format=value(name)"
        ]
        res = subprocess.run(check_cmd, capture_output=True, text=True, timeout=15)
        if "aiplatform.googleapis.com" in res.stdout:
            return True

        print(f"🔧 [BGM Engine] Enabling Vertex AI Agent Platform API (aiplatform.googleapis.com) on project '{project_id}'...")
        enable_cmd = [
            "gcloud", "services", "enable",
            "aiplatform.googleapis.com",
            f"--project={project_id}"
        ]
        enable_res = subprocess.run(enable_cmd, capture_output=True, text=True, timeout=45)
        if enable_res.returncode == 0:
            print("✅ [BGM Engine] Vertex AI Agent Platform API enabled successfully.")
            return True
        else:
            err_snip = enable_res.stderr.strip()[:150]
            print(f"⚠️ [BGM Engine] Could not enable Vertex AI Agent Platform API ({err_snip}); proceeding with generation attempt.", file=sys.stderr)
            return False
    except Exception as e:
        print(f"⚠️ [BGM Engine] API check/enablement exception: {e}", file=sys.stderr)
        return False


def synthesize_offline_ambient_loop(output_path: str, duration_sec: int = 60) -> bool:
    """Synthesizes an elegant, royalty-free corporate ambient chord progression loop using standard library wave + FFmpeg."""
    print(f"🎹 [BGM Engine] Synthesizing autonomous corporate ambient track ({duration_sec}s loop)...")
    sample_rate = 44100
    num_samples = sample_rate * duration_sec

    # Harmonic Keynote Progression: C Major 7th -> A Minor 7th -> F Major 7th -> G 7th (warm, inspiring, professional)
    chords = [
        [261.63, 329.63, 392.00, 493.88],  # C Major 7th (C4, E4, G4, B4)
        [220.00, 261.63, 329.63, 392.00],  # A Minor 7th (A3, C4, E4, G4)
        [174.61, 220.00, 261.63, 329.63],  # F Major 7th (F3, A3, C4, E4)
        [196.00, 246.94, 293.66, 349.23],  # G 7th       (G3, B3, D4, F4)
    ]

    temp_wav = output_path.replace(".mp3", ".tmp.wav") if output_path.endswith(".mp3") else output_path + ".tmp.wav"
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    try:
        with wave.open(temp_wav, "w") as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            chord_len = duration_sec / len(chords)
            frames = []
            for i in range(num_samples):
                t = i / sample_rate
                chord_idx = min(int(t / chord_len), len(chords) - 1)
                chord = chords[chord_idx]

                # Soft envelope per chord to eliminate click artifacts
                sub_t = (t % chord_len) / chord_len
                env = math.sin(sub_t * math.pi) ** 0.5

                # Overall loop fade-in / fade-out (first 1.5s and last 1.5s)
                fade = 1.0
                if t < 1.5:
                    fade = t / 1.5
                elif t > duration_sec - 1.5:
                    fade = (duration_sec - t) / 1.5

                left = 0.0
                right = 0.0
                for freq in chord:
                    # Fundamental tone with stereo detuning
                    left += math.sin(2.0 * math.pi * freq * t) * 0.12
                    right += math.sin(2.0 * math.pi * (freq * 1.003) * t) * 0.12
                    # Sub-octave warmth
                    left += math.sin(2.0 * math.pi * (freq * 0.5) * t) * 0.07
                    right += math.sin(2.0 * math.pi * (freq * 0.501) * t) * 0.07
                    # Gentle shimmer harmonic
                    left += math.sin(2.0 * math.pi * (freq * 2.0) * t) * 0.02
                    right += math.sin(2.0 * math.pi * (freq * 2.002) * t) * 0.02

                left *= env * fade * 0.45
                right *= env * fade * 0.45

                l_val = max(-32767, min(32767, int(left * 32767)))
                r_val = max(-32767, min(32767, int(right * 32767)))
                frames.append(struct.pack("<hh", l_val, r_val))

            wav_file.writeframes(b"".join(frames))

        # Convert WAV to MP3 via ffmpeg if MP3 requested, else move
        if output_path.endswith(".mp3"):
            conv_cmd = [
                "ffmpeg", "-y",
                "-i", temp_wav,
                "-c:a", "libmp3lame",
                "-q:a", "2",
                output_path
            ]
            subprocess.run(conv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
        else:
            os.replace(temp_wav, output_path)

        print(f"✅ [BGM Engine] Autonomous offline ambient BGM generated: {output_path}")
        return True
    except Exception as e:
        print(f"⚠️ [BGM Engine] Offline audio synthesis exception: {e}", file=sys.stderr)
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
        return False


def create_seamless_loop(input_path: str, output_path: str) -> bool:
    """Creates a seamless audio loop using FFmpeg equal-power crossfading."""
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path],
            capture_output=True, text=True, check=True
        )
        duration = float(probe.stdout.strip())
        if duration < 15.0:
            shutil.copy2(input_path, output_path)
            return True

        crossfade_dur = 4.0 if duration > 60 else 2.5
        trim_point = duration - (crossfade_dur + 1.5)
        if trim_point <= crossfade_dur:
            shutil.copy2(input_path, output_path)
            return True

        filter_complex = (
            f"[0:a]asplit=2[a1][a2]; "
            f"[a1]atrim=0:{trim_point:.2f}[main]; "
            f"[a2]atrim={trim_point:.2f}:{duration:.2f},asetpts=PTS-STARTPTS[tail]; "
            f"[tail][main]acrossfade=d={crossfade_dur}:c1=tri:c2=tri[out]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-" + "filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "libmp3lame",
            "-q:a", "2",
            output_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"🔄 [BGM Engine] Applied equal-power crossfade ({crossfade_dur}s) for seamless looping.")
            return True
        else:
            shutil.copy2(input_path, output_path)
            return True
    except Exception as e:
        print(f"⚠️ [BGM Engine] Loop crossfading skipped ({e}); using raw track.")
        try:
            shutil.copy2(input_path, output_path)
            return True
        except Exception:
            return False


def generate_lyria_music(project_id: str, prompt: str, output_path: str) -> bool:
    """Attempts to generate high-quality ambient music using Vertex AI Agent Platform Lyria 3 Pro (with Lyria 3 Clip fallback)."""
    token = get_gcp_access_token()
    if not token or not project_id:
        print("ℹ️ [BGM Engine] Google Cloud credentials or Project ID missing for Vertex AI Agent Platform Lyria; delegating to offline synthesizer.")
        return False

    ensure_aiplatform_api(project_id)

    # Models to try: primary Lyria 3 Pro (up to 3 min), secondary Lyria 3 Clip (up to 30s)
    models = ["lyria-3-pro-preview", "lyria-3-clip-preview"]
    raw_temp_mp3 = output_path + ".raw.mp3"
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    for model_id in models:
        url = f"https://aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/global/interactions"
        payload = {
            "model": model_id,
            "input": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Goog-User-Project": project_id,
            },
            method="POST"
        )

        try:
            print(f"🎵 [BGM Engine] Requesting music from Vertex AI Agent Platform Lyria API ({model_id})...")
            # Pro model takes ~34s to generate ~174s audio; clip takes ~13s
            timeout = 90 if "pro" in model_id else 45
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            outputs = data.get("outputs", [])
            audio_b64 = ""
            for out in outputs:
                if out.get("type") == "audio" and out.get("data"):
                    audio_b64 = out["data"]
                    break

            if not audio_b64:
                print(f"⚠️ [BGM Engine] Lyria ({model_id}) response contained no audio data.")
                continue

            audio_bytes = base64.b64decode(audio_b64)
            with open(raw_temp_mp3, "wb") as f:
                f.write(audio_bytes)

            # Apply seamless looping crossfade
            create_seamless_loop(raw_temp_mp3, output_path)
            if os.path.exists(raw_temp_mp3):
                try:
                    os.remove(raw_temp_mp3)
                except Exception:
                    pass

            print(f"🎉 [BGM Engine] Successfully generated Lyria music track ({model_id}): {output_path}")
            return True
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")[:250]
            print(f"ℹ️ [BGM Engine] Lyria ({model_id}) returned HTTP {e.code}: {err_msg}")
        except Exception as e:
            print(f"ℹ️ [BGM Engine] Lyria ({model_id}) request failed: {e}")

    return False


def build_dynamic_bgm_prompt(company: str, role: str, domain: str, custom_prompt: str = "") -> str:
    """Builds a refined prompt tailored to the enterprise domain."""
    if custom_prompt:
        return custom_prompt

    # Domain mood and industry tailoring (acoustic-first, brand-free to avoid trademark policy filters)
    industry = "modern operations and technology"
    mood = "modern, elegant corporate tech"
    if any(k in domain.lower() for k in ["mfg", "factory", "line", "plant", "supply", "logistics"]):
        industry = "manufacturing and supply chain"
        mood = "clean, modern rhythmic pulse and technology soundscape"
    elif any(k in domain.lower() for k in ["retail", "tea", "luxury", "hospitality", "store"]):
        industry = "retail and commerce"
        mood = "calm, sophisticated acoustic-ambient and warm synthesizer"
    elif any(k in domain.lower() for k in ["finance", "bank", "audit", "security", "tax"]):
        industry = "finance and enterprise systems"
        mood = "sleek, precise high-tech corporate ambient"

    return (
        f"Corporate keynote ambient background music for enterprise software demo in {industry}. "
        f"{mood}, warm synthesizer pads, subtle acoustic piano, gentle inspiring tempo (110 bpm), "
        "calm and professional soundscape, strictly instrumental, no vocals, high-fidelity stereo."
    )


def generate_bgm(output_path: str, company: str = "Enterprise", role: str = "Operations Director", domain: str = "", prompt: str = "", project_id: str = "") -> bool:
    """Coordinates Lyria music generation with autonomous offline fallback."""
    project_id = get_gcp_project_id(project_id)
    full_prompt = build_dynamic_bgm_prompt(company, role, domain, prompt)

    print("\n" + "-" * 70)
    print("🎼 [BGM Engine] Starting Background Music Synthesis")
    print(f"   Company : {company}")
    print(f"   Role    : {role}")
    print(f"   Output  : {output_path}")
    print("-" * 70)

    # 1. Primary Engine: Vertex AI Agent Platform Lyria API
    success = False
    if project_id:
        success = generate_lyria_music(project_id, full_prompt, output_path)

    # 2. Fallback Engine: Autonomous Offline Synthesis
    if not success:
        print("ℹ️ [BGM Engine] Activating autonomous offline ambient audio synthesizer fallback...")
        success = synthesize_offline_ambient_loop(output_path, duration_sec=60)

    return success


def main():
    parser = argparse.ArgumentParser(description="Generate Background Music for Demo Videos.")
    parser.add_argument("--output", default="public/audio/bgm.mp3", help="Output MP3 path")
    parser.add_argument("--company", default="Enterprise", help="Company name")
    parser.add_argument("--role", default="Operations Director", help="Agent role")
    parser.add_argument("--domain", default="", help="Domain slug or industry keywords")
    parser.add_argument("--prompt", default="", help="Custom soundscape prompt override")
    parser.add_argument("--project", default="", help="Google Cloud project ID override")
    args = parser.parse_args()

    ok = generate_bgm(
        output_path=args.output,
        company=args.company,
        role=args.role,
        domain=args.domain,
        prompt=args.prompt,
        project_id=args.project
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
