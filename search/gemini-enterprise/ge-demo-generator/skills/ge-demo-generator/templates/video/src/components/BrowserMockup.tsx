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
import { THEME } from "../styles/theme";

interface BrowserMockupProps {
  url?: string;
  children: React.ReactNode;
}

export const BrowserMockup: React.FC<BrowserMockupProps> = ({
  url = "https://vertexaisearch.cloud.google.com/home/cid/default/r/agent/demo",
  children,
}) => {
  return (
    <div
      style={{
        width: "90%",
        height: "82%",
        borderRadius: 16,
        background: "#0F172A",
        border: `1px solid ${THEME.colors.borderSubtle}`,
        boxShadow: THEME.shadows.browserWindow,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        position: "relative",
      }}
    >
      {/* Chrome Window Header */}
      <div
        style={{
          height: 48,
          background: "rgba(30, 41, 59, 0.8)",
          backdropFilter: "blur(12px)",
          display: "flex",
          alignItems: "center",
          padding: "0 18px",
          borderBottom: `1px solid ${THEME.colors.borderSubtle}`,
          gap: 16,
          zIndex: 10,
        }}
      >
        {/* macOS Traffic Lights */}
        <div style={{ display: "flex", gap: 8 }}>
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: THEME.colors.chromeTrafficRed }} />
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: THEME.colors.chromeTrafficYellow }} />
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: THEME.colors.chromeTrafficGreen }} />
        </div>

        {/* Address Bar */}
        <div
          style={{
            flex: 1,
            maxWidth: 680,
            margin: "0 auto",
            height: 30,
            borderRadius: 8,
            background: "rgba(15, 23, 42, 0.6)",
            border: `1px solid rgba(255, 255, 255, 0.08)`,
            display: "flex",
            alignItems: "center",
            padding: "0 12px",
            fontSize: 13,
            color: THEME.colors.textSecondary,
            fontFamily: THEME.fonts.mono,
            gap: 8,
          }}
        >
          <span style={{ color: "#10B981" }}>🔒</span>
          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {url}
          </span>
        </div>

        {/* Brand Chip */}
        <div style={{ fontSize: 13, fontWeight: 600, color: THEME.colors.textSecondary }}>
          Gemini Enterprise
        </div>
      </div>

      {/* Main Viewport Container */}
      <div
        style={{
          flex: 1,
          position: "relative",
          overflow: "hidden",
          background: "#000000",
        }}
      >
        {children}
      </div>
    </div>
  );
};
