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
import { CameraTarget } from "../types";

export interface CameraKeyframe {
  frame: number;
  x: number;
  y: number;
  scale: number;
}

export interface DynamicCameraProps {
  target?: CameraTarget;
  initialScale?: number;
  zoomStartFrame?: number;
  zoomDurationFrames?: number;
  keyframes?: CameraKeyframe[];
  children: React.ReactNode;
}

export const DynamicCamera: React.FC<DynamicCameraProps> = ({
  target,
  initialScale = 1.0,
  zoomStartFrame = 0,
  zoomDurationFrames = 15,
  keyframes,
  children,
}) => {
  const frame = useCurrentFrame();

  if (keyframes && keyframes.length >= 2) {
    const frames = keyframes.map((k) => k.frame);
    const scales = keyframes.map((k) => k.scale);
    const xs = keyframes.map((k) => k.x);
    const ys = keyframes.map((k) => k.y);

    const scale = interpolate(frame, frames, scales, {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const x = interpolate(frame, frames, xs, {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const y = interpolate(frame, frames, ys, {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });

    const originX = `${(x / 1920) * 100}%`;
    const originY = `${(y / 1080) * 100}%`;

    return (
      <div
        style={{
          width: "100%",
          height: "100%",
          transformOrigin: `${originX} ${originY}`,
          transform: `scale(${scale})`,
        }}
      >
        {children}
      </div>
    );
  }

  const targetScale = target?.scale ?? 1.0;
  const targetX = target?.x ?? 960;
  const targetY = target?.y ?? 540;

  let scale = targetScale;
  if (zoomDurationFrames > 0 && initialScale !== targetScale) {
    scale = interpolate(
      frame,
      [zoomStartFrame, zoomStartFrame + zoomDurationFrames],
      [initialScale, targetScale],
      {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }
    );
  }

  const originX = `${(targetX / 1920) * 100}%`;
  const originY = `${(targetY / 1080) * 100}%`;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        transformOrigin: `${originX} ${originY}`,
        transform: `scale(${scale})`,
      }}
    >
      {children}
    </div>
  );
};
