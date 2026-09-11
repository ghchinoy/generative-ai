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

export interface CameraTarget {
  x: number;
  y: number;
  scale: number;
}

export interface SubtitleItem {
  startFrame: number;
  endFrame: number;
  text: string;
  position?: "top" | "bottom";
}

export interface AudioClip {
  id: string;
  file: string;
  startFrame: number;
  durationFrames: number;
}

export interface SceneConfig {
  id: string;
  type: "intro_card" | "agenda_card" | "browser_screen" | "outro_card";
  title: string;
  subtitle?: string;
  startFrame: number;
  durationFrames: number;
  rawVideoTime?: {
    startSec: number;
    typingEndSec: number;
    thinkingEndSec: number;
    completeSec: number;
  };
  fastForward?: {
    startFrame: number;
    durationFrames: number;
    factor: number;
  };
  camera?: {
    typing?: CameraTarget;
    response?: CameraTarget;
    button?: CameraTarget;
    overview?: CameraTarget;
  };
  actionClick?: {
    t_click: number;
    x: number;
    y: number;
    button_label: string;
  };
}

export interface AgendaItem {
  number: number;
  title: string;
  subtitle: string;
  icon: string;
}

export interface VideoManifestProps extends Record<string, unknown> {
  company: string;
  role: string;
  fps: number;
  width: number;
  height: number;
  totalFrames: number;
  totalDurationSec: number;
  rawVideoFile: string;
  scenes: SceneConfig[];
  audioClips: AudioClip[];
  subtitles: SubtitleItem[];
  agendaItems?: AgendaItem[];
  enableNarration?: boolean;
  enableSubtitles?: boolean;
  enableBgm?: boolean;
  bgmFile?: string;
  bgmDurationFrames?: number;
}
