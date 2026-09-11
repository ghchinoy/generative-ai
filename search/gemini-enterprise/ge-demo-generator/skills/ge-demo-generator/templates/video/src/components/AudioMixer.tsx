// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import React from "react";
import { Audio, Loop, Sequence, staticFile, useCurrentFrame } from "remotion";
import { AudioClip } from "../types";

interface AudioMixerProps {
  audioClips?: AudioClip[];
  enableBgm?: boolean;
  bgmFile?: string;
  bgmDurationFrames?: number;
}

export const AudioMixer: React.FC<AudioMixerProps> = ({
  audioClips = [],
  enableBgm = false,
  bgmFile = "bgm.mp3",
  bgmDurationFrames,
}) => {
  const frame = useCurrentFrame();

  // Dynamic Audio Ducking:
  // Detect if voice narration is playing within current frame (+-10 frames buffer)
  let isSpeaking = false;
  let minDistanceToSpeech = 999999;

  for (const clip of audioClips) {
    const clipStart = clip.startFrame;
    const clipEnd = clip.startFrame + clip.durationFrames;
    if (frame >= clipStart && frame <= clipEnd) {
      isSpeaking = true;
      minDistanceToSpeech = 0;
      break;
    }
    const dist = Math.min(Math.abs(frame - clipStart), Math.abs(frame - clipEnd));
    if (dist < minDistanceToSpeech) {
      minDistanceToSpeech = dist;
    }
  }

  // Smooth volume easing:
  // Default non-speech ambient volume: 0.28 (28%)
  // Ducked speech volume: 0.10 (10%)
  // Transition window: 15 frames (0.5s at 30fps)
  let bgmVolume = 0.28;
  if (isSpeaking) {
    bgmVolume = 0.10;
  } else if (minDistanceToSpeech < 15) {
    const progress = minDistanceToSpeech / 15.0;
    bgmVolume = 0.10 + 0.18 * (0.5 - 0.5 * Math.cos(progress * Math.PI));
  }

  // Intro fade-in (first 30 frames)
  if (frame < 30) {
    bgmVolume *= frame / 30.0;
  }

  return (
    <>
      {/* 1. Voice Narration Clips (Clean Speech Only) */}
      {audioClips.map((clip) => (
        <Sequence
          key={clip.id}
          from={clip.startFrame}
          durationInFrames={clip.durationFrames}
        >
          <Audio src={staticFile(`audio/${clip.file}`)} volume={1.0} />
        </Sequence>
      ))}

      {/* 2. Ambient Background Music (Optional with Dynamic Audio Ducking) */}
      {enableBgm && (
        <Loop durationInFrames={bgmDurationFrames || 1800}>
          <Audio src={staticFile(`audio/${bgmFile}`)} volume={bgmVolume} />
        </Loop>
      )}
    </>
  );
};
