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

export const THEME = {
  colors: {
    // Google Cloud Brand Colors
    googleBlue: "#1A73E8",
    googleBlueLight: "#4285F4",
    googleRed: "#EA4335",
    googleYellow: "#FBBC04",
    googleGreen: "#34A853",

    // Google Cloud Surface & Canvas
    canvasBg: "#FFFFFF",
    surfaceNeutral: "#F8F9FA",
    surfaceSubtle: "#F1F3F4",
    surfaceDark: "rgba(32, 33, 36, 0.88)",
    surfaceDarkElevated: "rgba(32, 33, 36, 0.95)",

    // Google Cloud Typography
    textPrimary: "#202124",
    textSecondary: "#5F6368",
    textTertiary: "#80868B",
    textInverse: "#FFFFFF",
    textInverseSubtle: "#BDC1C6",

    // Borders & Accents
    borderSubtle: "#DADCE0",
    borderLight: "#E8EAED",
    borderDark: "rgba(255, 255, 255, 0.12)",

    // Badges & Highlights
    chipBg: "#E8F0FE",
    chipBorder: "#D2E3FC",
    chipText: "#1A73E8",

    // Fast Forward Badge
    speedBadgeBg: "rgba(26, 115, 232, 0.12)",
    speedBadgeBorder: "rgba(66, 133, 244, 0.35)",
    speedBadgeText: "#1A73E8",

    // Subtitles
    subtitleBg: "rgba(32, 33, 36, 0.88)",
    subtitleBorder: "rgba(255, 255, 255, 0.12)",
    subtitleText: "#FFFFFF",

    // Legacy compat aliases
    primaryAccent: "#1A73E8",
    primaryGlow: "rgba(66, 133, 244, 0.35)",
    cardBg: "rgba(255, 255, 255, 0.95)",

    // macOS Traffic Lights
    chromeTrafficRed: "#FF5F56",
    chromeTrafficYellow: "#FFBD2E",
    chromeTrafficGreen: "#27C93F",
  },
  fonts: {
    heading: "'Google Sans', 'Inter', -apple-system, sans-serif",
    body: "'Roboto', 'Noto Sans JP', -apple-system, sans-serif",
    mono: "'Roboto Mono', 'Fira Code', monospace",
  },
  shadows: {
    browserWindow: "0 20px 50px rgba(60, 64, 67, 0.15), 0 4px 12px rgba(60, 64, 67, 0.08)",
    card: "0 1px 3px rgba(60, 64, 67, 0.12), 0 1px 2px rgba(60, 64, 67, 0.08)",
    floatingPill: "0 4px 16px rgba(0, 0, 0, 0.28)",
    subtitles: "0 8px 32px rgba(0, 0, 0, 0.35)",
  }
};
