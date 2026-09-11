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
import { Composition } from "remotion";
import { DemoHighlightReel } from "./DemoHighlightReel";
import { VideoManifestProps } from "./types";
import activeManifest from "./manifest.json";

const fallbackNeutralProps: VideoManifestProps = {
  company: "Enterprise Demo",
  role: "AI Operations Director",
  fps: 30,
  width: 1920,
  height: 1080,
  totalFrames: 3600,
  totalDurationSec: 120.0,
  rawVideoFile: "raw_recording.mp4",
  scenes: [
    {
      id: "scene_intro",
      type: "intro_card",
      title: "Enterprise Demo",
      subtitle: "AI Operations Director Walkthrough",
      startFrame: 0,
      durationFrames: 90,
    },
    {
      id: "prompt_1",
      type: "browser_screen",
      title: "Scene 1: Welcome & Situational Briefing",
      startFrame: 90,
      durationFrames: 1140,
      camera: {
        response: { x: 960, y: 540, scale: 1.10 },
      },
    },
    {
      id: "prompt_2",
      type: "browser_screen",
      title: "Scene 2: Data Analysis & Anomaly Detection",
      startFrame: 1230,
      durationFrames: 1140,
      camera: {
        response: { x: 960, y: 500, scale: 1.10 },
      },
    },
    {
      id: "prompt_3",
      type: "browser_screen",
      title: "Scene 3: Immediate Workflow Execution",
      startFrame: 2370,
      durationFrames: 1140,
      camera: {
        response: { x: 960, y: 580, scale: 1.10 },
      },
    },
    {
      id: "scene_outro",
      type: "outro_card",
      title: "Gemini Enterprise for Enterprise Demo",
      subtitle: "Autonomous Agent Orchestration — Powered by Google Cloud",
      startFrame: 3510,
      durationFrames: 90,
    },
  ],
  audioClips: [
    {
      id: "audio_intro",
      file: "audio_intro.mp3",
      startFrame: 10,
      durationFrames: 80,
    },
    {
      id: "audio_prompt_1",
      file: "audio_prompt_1.mp3",
      startFrame: 100,
      durationFrames: 300,
    },
    {
      id: "audio_outro",
      file: "audio_outro.mp3",
      startFrame: 3520,
      durationFrames: 80,
    },
  ],
  subtitles: [
    {
      startFrame: 10,
      endFrame: 80,
      text: "Demonstration of Gemini Enterprise autonomous AI agent capabilities",
    },
    {
      startFrame: 100,
      endFrame: 300,
      text: "Reviewing core functions and real-time operational status",
    },
    {
      startFrame: 3520,
      endFrame: 3590,
      text: "Gemini Enterprise transforms enterprise operations and workflow automation",
    },
  ],
  brand: {
    enabled: false,
    primaryColor: "#1A73E8",
    accentColor: "#E8F0FE",
  },
};

const resolvedDefaultProps: VideoManifestProps =
  activeManifest && (activeManifest as any).totalFrames && (activeManifest as any).scenes?.length > 0
    ? (activeManifest as unknown as VideoManifestProps)
    : fallbackNeutralProps;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition<any, VideoManifestProps>
      id="DemoHighlightReel"
      component={DemoHighlightReel}
      durationInFrames={resolvedDefaultProps.totalFrames || 3600}
      fps={resolvedDefaultProps.fps || 30}
      width={resolvedDefaultProps.width || 1920}
      height={resolvedDefaultProps.height || 1080}
      defaultProps={resolvedDefaultProps}
      calculateMetadata={({ props }) => {
        const effective =
          props && props.totalFrames && props.scenes?.length > 0
            ? props
            : resolvedDefaultProps;
        return {
          durationInFrames: effective.totalFrames || 3600,
          fps: effective.fps || 30,
          width: effective.width || 1920,
          height: effective.height || 1080,
          props: effective,
        };
      }}
    />
  );
};
