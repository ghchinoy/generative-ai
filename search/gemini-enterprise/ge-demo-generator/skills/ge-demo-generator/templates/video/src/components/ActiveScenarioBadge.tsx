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

export interface ActiveScenarioBadgeProps {
  scenarioNumber: number;
  totalScenarios: number;
  title: string;
}

export const ActiveScenarioBadge: React.FC<ActiveScenarioBadgeProps> = ({
  scenarioNumber,
  totalScenarios,
  title,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });
  const translateY = interpolate(frame, [0, 8], [-6, 0], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        position: "absolute",
        top: 24,
        left: 24,
        zIndex: 45,
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "8px 18px",
        borderRadius: 999,
        background: "rgba(32, 33, 36, 0.88)",
        backdropFilter: "blur(16px)",
        border: "1px solid rgba(255, 255, 255, 0.15)",
        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.35)",
        fontFamily: "'Google Sans', 'Noto Sans JP', -apple-system, sans-serif",
        opacity,
        transform: `translateY(${translateY}px)`,
        pointerEvents: "none",
      }}
    >
      {/* Google Blue Accent Dot with Glow */}
      <div
        style={{
          width: 9,
          height: 9,
          borderRadius: "50%",
          background: "#4285F4",
          boxShadow: "0 0 8px #4285F4",
          flexShrink: 0,
        }}
      />
      <span
        style={{
          color: "#FFFFFF",
          fontSize: 14,
          fontWeight: 700,
          letterSpacing: "0.02em",
          whiteSpace: "nowrap",
        }}
      >
        Scene {scenarioNumber} / {totalScenarios}:
      </span>
      <span
        style={{
          color: "#E8EAED",
          fontSize: 14,
          fontWeight: 500,
          whiteSpace: "nowrap",
        }}
      >
        {title}
      </span>
    </div>
  );
};
