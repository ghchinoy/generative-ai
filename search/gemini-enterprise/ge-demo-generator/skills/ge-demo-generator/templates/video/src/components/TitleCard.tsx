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

interface TitleBannerProps {
  title: string;
  subtitle: string;
}

export const TitleBanner: React.FC<TitleBannerProps> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();

  // Fades in over 10 frames, stays for 25 frames, fades out over 10 frames (total ~45 frames = 1.5s)
  const opacity = interpolate(frame, [0, 10, 35, 45], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  if (frame > 45) {
    return null;
  }

  return (
    <div
      style={{
        position: "absolute",
        top: 32,
        left: "50%",
        transform: "translateX(-50%)",
        display: "flex",
        alignItems: "center",
        gap: 14,
        padding: "10px 24px",
        borderRadius: 999,
        background: "rgba(32, 33, 36, 0.90)",
        backdropFilter: "blur(16px)",
        border: "1px solid rgba(255, 255, 255, 0.14)",
        boxShadow: "0 8px 28px rgba(0, 0, 0, 0.4)",
        opacity,
        zIndex: 50,
      }}
    >
      <div
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: "#4285F4",
          boxShadow: "0 0 10px #4285F4",
        }}
      />
      <span
        style={{
          color: "#FFFFFF",
          fontSize: 17,
          fontWeight: 700,
          fontFamily: "'Google Sans', 'Inter', sans-serif",
          letterSpacing: "0.02em",
        }}
      >
        {title}
      </span>
      <span style={{ color: "rgba(255, 255, 255, 0.3)" }}>|</span>
      <span
        style={{
          color: "#BDC1C6",
          fontSize: 15,
          fontWeight: 500,
          fontFamily: "'Google Sans', 'Roboto', sans-serif",
        }}
      >
        {subtitle}
      </span>
    </div>
  );
};

export const IntroCard: React.FC<{ company: string; role: string }> = ({ company, role }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(frame, [0, 20], [0.96, 1.0], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#FFFFFF",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Google Sans', 'Inter', sans-serif",
        opacity,
        transform: `scale(${scale})`,
        position: "relative",
      }}
    >
      {/* Google Cloud 4-Color Accent Strip */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 6,
          background: "linear-gradient(90deg, #4285F4 0%, #4285F4 25%, #EA4335 25%, #EA4335 50%, #FBBC04 50%, #FBBC04 75%, #34A853 75%, #34A853 100%)",
        }}
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "8px 22px",
          borderRadius: 999,
          background: "#F1F3F4",
          border: "1px solid #DADCE0",
          marginBottom: 24,
        }}
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z" fill="url(#introSparkle)"/>
          <defs>
            <linearGradient id="introSparkle" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#4285F4"/>
              <stop offset="50%" stopColor="#9B72CB"/>
              <stop offset="100%" stopColor="#D96570"/>
            </linearGradient>
          </defs>
        </svg>
        <span style={{ fontSize: 15, fontWeight: 600, color: "#202124", letterSpacing: "0.02em" }}>
          Gemini Enterprise | Google Cloud
        </span>
      </div>

      <h1
        style={{
          fontSize: 54,
          fontWeight: 800,
          color: "#202124",
          margin: "0 0 14px 0",
          letterSpacing: "-0.02em",
          textAlign: "center",
        }}
      >
        {company}
      </h1>

      <h2
        style={{
          fontSize: 26,
          fontWeight: 500,
          color: "#1A73E8",
          margin: "0 0 28px 0",
          textAlign: "center",
        }}
      >
        {role}
      </h2>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "6px 18px",
          borderRadius: 999,
          background: "#E8F0FE",
          border: "1px solid #D2E3FC",
          color: "#1967D2",
          fontSize: 14,
          fontWeight: 600,
          marginBottom: 32,
        }}
      >
        <span>Autonomous Multi-Agent Systems & Live Web UI Walkthrough</span>
      </div>

      {/* Google Cloud Presentation Footer */}
      <div
        style={{
          position: "absolute",
          bottom: 36,
          display: "flex",
          alignItems: "center",
          gap: 10,
          fontSize: 14,
          color: "#80868B",
          fontWeight: 500,
        }}
      >
        <span>Google Cloud</span>
        <span style={{ opacity: 0.5 }}>•</span>
        <span>Vertex AI Agent Platform</span>
      </div>
    </div>
  );
};

export interface AgendaItem {
  number: number;
  title: string;
  subtitle: string;
  icon: string;
}

export const DEFAULT_AGENDA_ITEMS_EN: AgendaItem[] = [
  { number: 1, title: "Welcome & Overview", subtitle: "Operational briefing and priority status alerts", icon: "💬" },
  { number: 2, title: "Metadata & Catalog Discovery", subtitle: "Structured catalog and plant equipment schema", icon: "📦" },
  { number: 3, title: "Cross-Source Anomaly Detection", subtitle: "Reconcile BigQuery shipment logs with IoT sensors", icon: "📊" },
  { number: 4, title: "Immediate Workflow Execution", subtitle: "Automated reallocation requisition & one-click sign-off", icon: "⚡" },
  { number: 5, title: "Root Cause Quality Inspection", subtitle: "Analyze telemetry discrepancies and supplier batches", icon: "🔍" },
  { number: 6, title: "Predictive Line Simulation", subtitle: "Simulate capacity constraints and balance schedules", icon: "📈" },
  { number: 7, title: "Operational Summary & Handover", subtitle: "Consolidated actions summary & procurement report", icon: "📝" },
];

export const DEFAULT_AGENDA_ITEMS = DEFAULT_AGENDA_ITEMS_EN;

export const AgendaCard: React.FC<{ company: string; role: string; items?: AgendaItem[]; brand?: BrandConfig }> = ({
  company,
  role,
  items = DEFAULT_AGENDA_ITEMS_EN,
  brand,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(frame, [0, 20], [0.97, 1.0], { extrapolateRight: "clamp" });
  const isCompact = items.length > 5;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#FFFFFF",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        fontFamily: "'Google Sans', 'Inter', -apple-system, sans-serif",
        opacity,
        transform: `scale(${scale})`,
        padding: isCompact ? "28px 60px 140px 60px" : "36px 60px 140px 60px",
        boxSizing: "border-box",
        position: "relative",
      }}
    >
      {/* Google Cloud 4-Color Accent Strip */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 6,
          background: "linear-gradient(90deg, #4285F4 0%, #4285F4 25%, #EA4335 25%, #EA4335 50%, #FBBC04 50%, #FBBC04 75%, #34A853 75%, #34A853 100%)",
        }}
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: isCompact ? "5px 16px" : "6px 18px",
          borderRadius: 999,
          background: "#F1F3F4",
          border: "1px solid #DADCE0",
          marginBottom: isCompact ? 8 : 12,
        }}
      >
        <span style={{ fontSize: isCompact ? 13 : 14, fontWeight: 600, color: "#1F1F1F", letterSpacing: "0.02em" }}>
          ✨ Gemini Enterprise | Demo Walkthrough Agenda
        </span>
      </div>

      <h1
        style={{
          fontSize: isCompact ? 34 : 38,
          fontWeight: 800,
          color: "#1F1F1F",
          margin: "0 0 4px 0",
          letterSpacing: "-0.01em",
          textAlign: "center",
        }}
      >
        Demo Scenarios Agenda
      </h1>

      <p
        style={{
          fontSize: isCompact ? 17 : 19,
          color: "#1A73E8",
          fontWeight: 600,
          margin: isCompact ? "0 0 16px 0" : "0 0 22px 0",
          textAlign: "center",
        }}
      >
        {company} — {role}
      </p>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: isCompact ? 10 : 12,
          width: "100%",
          maxWidth: 1140,
        }}
      >
        {items.map((item, idx) => {
          const itemDelay = 8 + idx * (isCompact ? 4 : 6);
          const itemOpacity = interpolate(frame, [itemDelay, itemDelay + 8], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const itemTranslateY = interpolate(frame, [itemDelay, itemDelay + 8], [8, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          return (
            <div
              key={item.number}
              style={{
                display: "flex",
                alignItems: "center",
                gap: isCompact ? 16 : 20,
                padding: isCompact ? "12px 26px" : "14px 28px",
                borderRadius: 14,
                background: "#F8F9FA",
                border: "1px solid #E0E2E6",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
                opacity: itemOpacity,
                transform: `translateY(${itemTranslateY}px)`,
              }}
            >
              <div
                style={{
                  width: isCompact ? 36 : 40,
                  height: isCompact ? 36 : 40,
                  borderRadius: 10,
                  background: "#1A73E8",
                  color: "#FFFFFF",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: isCompact ? 18 : 20,
                  fontWeight: 700,
                  flexShrink: 0,
                }}
              >
                {item.number}
              </div>
              <div style={{ fontSize: isCompact ? 26 : 30, flexShrink: 0 }}>{item.icon}</div>
              <div style={{ display: "flex", flexDirection: "column", flexGrow: 1, overflow: "hidden" }}>
                <span style={{ fontSize: isCompact ? 21 : 23, fontWeight: 700, color: "#1F1F1F", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", letterSpacing: "-0.01em" }}>
                  {item.title}
                </span>
                <span style={{ fontSize: isCompact ? 15 : 16, color: "#444746", marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {item.subtitle}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const OutroCard: React.FC<{ company: string; role?: string }> = ({ company }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#FFFFFF",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Google Sans', 'Inter', sans-serif",
        opacity,
        position: "relative",
      }}
    >
      {/* Google Cloud 4-Color Accent Strip */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 6,
          background: "linear-gradient(90deg, #4285F4 0%, #4285F4 25%, #EA4335 25%, #EA4335 50%, #FBBC04 50%, #FBBC04 75%, #34A853 75%, #34A853 100%)",
        }}
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "8px 22px",
          borderRadius: 999,
          background: "#E8F0FE",
          border: "1px solid #D2E3FC",
          marginBottom: 24,
        }}
      >
        <span style={{ fontSize: 15, fontWeight: 600, color: "#1967D2" }}>
          ✨ Ready for Autonomous Operations
        </span>
      </div>

      <h1
        style={{
          fontSize: 50,
          fontWeight: 800,
          color: "#202124",
          margin: "0 0 16px 0",
          letterSpacing: "-0.02em",
          textAlign: "center",
        }}
      >
        Gemini Enterprise for {company}
      </h1>

      <p
        style={{
          fontSize: 20,
          color: "#5F6368",
          margin: "0 0 36px 0",
          textAlign: "center",
          maxWidth: 820,
          lineHeight: 1.5,
        }}
      >
        Accelerating enterprise operations with grounded, autonomous AI agents
      </p>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "10px 28px",
          borderRadius: 999,
          background: "#1A73E8",
          color: "#FFFFFF",
          fontSize: 15,
          fontWeight: 600,
          boxShadow: "0 4px 14px rgba(26, 115, 232, 0.35)",
        }}
      >
        <span>Transform your enterprise workflows today</span>
      </div>

      {/* Google Cloud Presentation Footer */}
      <div
        style={{
          position: "absolute",
          bottom: 36,
          display: "flex",
          alignItems: "center",
          gap: 10,
          fontSize: 14,
          color: "#80868B",
          fontWeight: 500,
        }}
      >
        <span>Google Cloud</span>
        <span style={{ opacity: 0.5 }}>•</span>
        <span>Vertex AI Agent Platform</span>
      </div>
    </div>
  );
};
