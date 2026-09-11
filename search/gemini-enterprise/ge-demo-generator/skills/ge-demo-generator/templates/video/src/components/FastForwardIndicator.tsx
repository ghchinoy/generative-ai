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

interface FastForwardIndicatorProps {
  factor?: number;
}

export const FastForwardIndicator: React.FC<FastForwardIndicatorProps> = ({ factor = 4 }) => {
  return (
    <div
      style={{
        position: "absolute",
        top: 28,
        right: 32,
        background: "rgba(32, 33, 36, 0.88)",
        backdropFilter: "blur(16px)",
        border: "1px solid rgba(66, 133, 244, 0.4)",
        borderRadius: 9999,
        padding: "6px 16px",
        display: "flex",
        alignItems: "center",
        gap: 8,
        color: "#FFFFFF",
        fontSize: 14,
        fontWeight: 600,
        fontFamily: "'Google Sans', sans-serif",
        letterSpacing: "0.02em",
        zIndex: 40,
        boxShadow: "0 4px 16px rgba(0, 0, 0, 0.3), 0 0 12px rgba(66, 133, 244, 0.2)",
      }}
    >
      <span style={{ color: "#4285F4", fontSize: 13 }}>⏩</span>
      <span>{Number(factor).toFixed(0)}× Fast-Forward</span>
    </div>
  );
};
