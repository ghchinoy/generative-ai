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
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile } from "remotion";
import { AudioMixer } from "./components/AudioMixer";
import { DynamicCamera } from "./components/DynamicCamera";
import { FastForwardIndicator } from "./components/FastForwardIndicator";
import { Subtitles } from "./components/Subtitles";
import { ActiveScenarioBadge } from "./components/ActiveScenarioBadge";
import { IntroCard, AgendaCard, OutroCard, TitleBanner } from "./components/TitleCard";
import { VideoManifestProps } from "./types";

export const DemoHighlightReel: React.FC<VideoManifestProps> = (props) => {
  const fps = props.fps || 30;

  return (
    <AbsoluteFill
      style={{
        background: "#FFFFFF",
        overflow: "hidden",
      }}
    >
      {/* 1. Scene Sequences */}
      {props.scenes.map((sc) => {
        if (sc.type === "intro_card") {
          return (
            <Sequence
              key={sc.id}
              from={sc.startFrame}
              durationInFrames={sc.durationFrames}
            >
              <IntroCard company={props.company} role={props.role} />
            </Sequence>
          );
        }

        if (sc.type === "agenda_card") {
          return (
            <Sequence
              key={sc.id}
              from={sc.startFrame}
              durationInFrames={sc.durationFrames}
            >
              <AgendaCard company={props.company} role={props.role} items={props.agendaItems} />
            </Sequence>
          );
        }

        if (sc.type === "outro_card") {
          return (
            <Sequence
              key={sc.id}
              from={sc.startFrame}
              durationInFrames={sc.durationFrames}
            >
              <OutroCard company={props.company} role={props.role} />
            </Sequence>
          );
        }

        if (sc.type === "browser_screen" && sc.rawVideoTime) {
          const raw = sc.rawVideoTime;
          // Segment A: Typing (1x real speed)
          const typingDurSec = Math.max(0.1, raw.typingEndSec - raw.startSec);
          const typingFrames = Math.round(typingDurSec * fps);

          // Segment B: Thinking / Wait (Fast-forwarded 4x)
          const thinkingDurSec = Math.max(0.1, raw.thinkingEndSec - raw.typingEndSec);
          const ffFactor = sc.fastForward?.factor || 4;
          const ffDurSec = thinkingDurSec / ffFactor;
          const ffFrames = Math.round(ffDurSec * fps);

          // Segment C: Response inspection and narration (1x)
          const respFrames = Math.max(1, sc.durationFrames - (typingFrames + ffFrames));

          const cameraOverview = sc.camera?.overview || { x: 960, y: 540, scale: 1.0 };
          const cameraTyping = sc.camera?.typing || { x: 960, y: 920, scale: 1.50 };
          const cameraResponse = sc.camera?.response || { x: 960, y: 540, scale: 1.10 };
          const cameraButton = sc.camera?.button;
          const actionClick = sc.actionClick;

          // Build dynamic camera keyframes for Segment 3 when an action button is clicked
          let responseKeyframes: Array<{ frame: number; x: number; y: number; scale: number }> | undefined;
          if (cameraButton && actionClick && typeof actionClick.t_click === "number") {
            const clickOffsetSec = actionClick.t_click - raw.thinkingEndSec;
            const clickFrame = Math.round(clickOffsetSec * fps);
            const zoomInStart = Math.max(15, clickFrame - 45);
            const zoomInPeak = zoomInStart + 18;
            const zoomOutStart = Math.min(respFrames - 25, clickFrame + 60);
            const zoomOutEnd = Math.min(respFrames, zoomOutStart + 18);

            if (zoomInPeak < zoomOutStart && zoomOutStart < respFrames) {
              responseKeyframes = [
                { frame: 0, x: 960, y: 540, scale: 1.0 },
                { frame: 18, x: cameraResponse.x, y: cameraResponse.y, scale: cameraResponse.scale },
                { frame: zoomInStart, x: cameraResponse.x, y: cameraResponse.y, scale: cameraResponse.scale },
                { frame: zoomInPeak, x: cameraButton.x, y: cameraButton.y, scale: cameraButton.scale },
                { frame: zoomOutStart, x: cameraButton.x, y: cameraButton.y, scale: cameraButton.scale },
                { frame: zoomOutEnd, x: cameraResponse.x, y: cameraResponse.y, scale: cameraResponse.scale },
                { frame: respFrames, x: cameraResponse.x, y: cameraResponse.y, scale: cameraResponse.scale },
              ];
            }
          }

          return (
            <Sequence
              key={sc.id}
              from={sc.startFrame}
              durationInFrames={sc.durationFrames}
            >
              {/* Segment 1: Typing at 1x real speed with 1.5x prompt input close-up */}
              <Sequence from={0} durationInFrames={typingFrames}>
                <DynamicCamera
                  target={cameraTyping}
                  initialScale={1.0}
                  zoomStartFrame={0}
                  zoomDurationFrames={Math.min(18, Math.round(typingFrames * 0.4))}
                >
                  <OffthreadVideo
                    src={staticFile(`recordings/${props.rawVideoFile}`)}
                    startFrom={Math.round(raw.startSec * fps)}
                    endAt={Math.round(raw.typingEndSec * fps)}
                    playbackRate={1}
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                </DynamicCamera>
              </Sequence>

              {/* Segment 2: Fast-forward thinking wait at 4x */}
              <Sequence from={typingFrames} durationInFrames={ffFrames}>
                <DynamicCamera
                  target={cameraOverview}
                  initialScale={1.50}
                  zoomStartFrame={0}
                  zoomDurationFrames={Math.min(12, Math.round(ffFrames * 0.4))}
                >
                  <OffthreadVideo
                    src={staticFile(`recordings/${props.rawVideoFile}`)}
                    startFrom={Math.round(raw.typingEndSec * fps)}
                    endAt={Math.round(raw.thinkingEndSec * fps)}
                    playbackRate={ffFactor}
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                </DynamicCamera>
                <FastForwardIndicator factor={ffFactor} />
              </Sequence>

              {/* Segment 3: Response inspection and narration at 1x with subtle zoom & button zoom */}
              <Sequence from={typingFrames + ffFrames} durationInFrames={respFrames}>
                <DynamicCamera
                  target={cameraResponse}
                  initialScale={1.0}
                  zoomStartFrame={0}
                  zoomDurationFrames={Math.min(20, Math.round(respFrames * 0.2))}
                  keyframes={responseKeyframes}
                >
                  <OffthreadVideo
                    src={staticFile(`recordings/${props.rawVideoFile}`)}
                    startFrom={Math.round(raw.thinkingEndSec * fps)}
                    endAt={Math.round(Math.max(raw.completeSec, raw.thinkingEndSec + (respFrames / fps) + 2.0) * fps)}
                    playbackRate={1}
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                </DynamicCamera>
              </Sequence>
            </Sequence>
          );
        }

        return null;
      })}

      {/* 2. Global Title Banner (First 1.5s of Scene 1, right after intro) */}
      {props.scenes.filter((s) => s.type === "browser_screen").length > 0 && (
        <Sequence
          from={props.scenes.filter((s) => s.type === "browser_screen")[0].startFrame}
          durationInFrames={45}
        >
          <TitleBanner
            title={props.company}
            subtitle={`${props.role} — AI Agent Walkthrough`}
          />
        </Sequence>
      )}

      {/* 2.5 Active Scenario Pill Badge (Top-Left during browser scenes) */}
      {props.scenes
        .filter((s) => s.type === "browser_screen")
        .map((sc, idx, arr) => (
          <Sequence
            key={`badge_${sc.id}`}
            from={sc.startFrame}
            durationInFrames={sc.durationFrames}
          >
            <ActiveScenarioBadge
              scenarioNumber={idx + 1}
              totalScenarios={arr.length}
              title={sc.title}
            />
          </Sequence>
        ))}

      {/* 3. Clean Lower-Third Subtitles */}
      {props.enableSubtitles !== false && <Subtitles subtitles={props.subtitles} />}

      {/* 4. Professional Narration Audio Tracks & Background Music */}
      {(props.enableNarration !== false || props.enableBgm) && (
        <AudioMixer
          audioClips={props.enableNarration !== false ? props.audioClips : []}
          enableBgm={props.enableBgm}
          bgmFile={props.bgmFile}
          bgmDurationFrames={props.bgmDurationFrames}
        />
      )}
    </AbsoluteFill>
  );
};
