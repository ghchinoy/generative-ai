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
import { interpolate, useCurrentFrame } from "remotion";
import { SubtitleItem } from "../types";

interface SubtitlesProps {
  subtitles?: SubtitleItem[];
}

export const Subtitles: React.FC<SubtitlesProps> = ({ subtitles = [] }) => {
  const frame = useCurrentFrame();

  const activeItem = subtitles.find(
    (s) => frame >= s.startFrame && frame <= s.endFrame
  );

  if (!activeItem) {
    return null;
  }

  const relFrame = frame - activeItem.startFrame;
  const durFrames = activeItem.endFrame - activeItem.startFrame;
  const opacity = durFrames > 8
    ? interpolate(
        relFrame,
        [0, 4, durFrames - 4, durFrames],
        [0, 1, 1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      )
    : 1;

  const isTop = activeItem.position === "top";

  return (
    <div
      style={{
        position: "absolute",
        top: isTop ? 48 : undefined,
        bottom: isTop ? undefined : 42,
        left: "50%",
        transform: "translateX(-50%)",
        display: "flex",
        justifyContent: "center",
        zIndex: 50,
        opacity,
        maxWidth: "88%",
      }}
    >
      <div
        style={{
          background: "rgba(32, 33, 36, 0.90)",
          backdropFilter: "blur(20px) saturate(180%)",
          border: "1px solid rgba(255, 255, 255, 0.14)",
          borderRadius: 16,
          padding: "12px 32px",
          color: "#FFFFFF",
          fontSize: 29,
          fontWeight: 500,
          fontFamily: "'Google Sans', 'Noto Sans JP', -apple-system, sans-serif",
          textAlign: "center",
          lineHeight: 1.45,
          letterSpacing: "0.02em",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
          textShadow: "0 2px 4px rgba(0, 0, 0, 0.4)",
        }}
      >
        {activeItem.text}
      </div>
    </div>
  );
};
