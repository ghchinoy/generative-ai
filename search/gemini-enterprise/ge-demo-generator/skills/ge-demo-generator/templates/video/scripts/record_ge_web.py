#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Playwright CDP Browser Screen Recording Engine for Gemini Enterprise Demos.

Connects to a running Google Chrome session over Chromium DevTools Protocol (CDP,
port 9222) to reuse the authenticated Google Account session without credential
exposure. Executes scripted demo prompts with natural human typing cadence, smooth
Bézier cursor motion, interaction feedback, wait-time telemetry, and live screencast capture.

Incorporates design rules from `browser-video-recording`:
- 1920x1080 locked viewport.
- Natural word-burst typing intervals (25-40ms) with cognitive hesitation.
- Smooth cubic ease-in-out Bézier curve cursor movement with distance-adaptive steps.
- In-DOM virtual SVG cursor overlay and radial click ripple animations.
- Live CDP screencast frame streaming (`Page.startScreencast`) to FFmpeg.
- Stylized dark-mode Gemini Enterprise mock video generation fallback.
- Action and wait-time telemetry output (actions.json) for Remotion.
"""

import argparse
import asyncio
import base64
import html
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse

DEFAULT_CDP_URL = "http://localhost:9222"
DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}

DEFAULT_DEMO_SCENES_EN = [
    {
        "scene_id": "prompt_1",
        "scene_type": "welcome",
        "title": "Scene 1: Welcome & Overview",
        "prompt": "Hello, please provide an operational overview and your core capabilities."
    },
    {
        "scene_id": "prompt_2",
        "scene_type": "catalog",
        "title": "Scene 2: Metadata & Catalog Discovery",
        "prompt": "Please explain the structure of our tea products catalog and boutique store network."
    },
    {
        "scene_id": "prompt_3",
        "scene_type": "analytics_wow",
        "title": "Scene 3: Cross-Source Anomaly Detection",
        "prompt": "Cross-reference recent supplier ledger shipments against internal order records to identify anomalies."
    },
    {
        "scene_id": "prompt_4",
        "scene_type": "workflow_action",
        "title": "Scene 4: Immediate Workflow Execution",
        "prompt": "Trigger immediate inventory reallocation and request supervisor sign-off."
    },
    {
        "scene_id": "prompt_5",
        "scene_type": "investigation",
        "title": "Scene 5: Root Cause Analysis & Quality Inspection",
        "prompt": "Analyze component telemetry and supplier batch records to identify the root cause of recent quality discrepancies."
    },
    {
        "scene_id": "prompt_6",
        "scene_type": "simulation",
        "title": "Scene 6: Predictive Planning & Line Simulation",
        "prompt": "Simulate tomorrow's assembly line capacity under current supply constraints and rebalance production schedules."
    },
    {
        "scene_id": "prompt_7",
        "scene_type": "summary",
        "title": "Scene 7: Operational Summary & Recommendations",
        "prompt": "Please summarize today's operational actions and provide procurement recommendations for tomorrow."
    }
]

DEFAULT_DEMO_SCENES_JA = [
    {
        "scene_id": "prompt_1",
        "scene_type": "welcome",
        "title": "Scene 1: 初期対話と状況把握",
        "prompt": "こんにちは。あなたのコア機能と本日の全店舗オペレーション状況を教えてください。"
    },
    {
        "scene_id": "prompt_2",
        "scene_type": "catalog",
        "title": "Scene 2: メタデータと製品カタログ探索",
        "prompt": "登録されているティー製品カタログ（tea_products）と店舗一覧（boutique_stores）の構成を教えてください。"
    },
    {
        "scene_id": "prompt_3",
        "scene_type": "analytics_wow",
        "title": "Scene 3: 複合データ分析と不整合検知",
        "prompt": "サプライヤー台帳の配送実績とBigQueryの注文履歴を突合し、データの不整合や配送遅延の異常値を抽出してください。"
    },
    {
        "scene_id": "prompt_4",
        "scene_type": "workflow_action",
        "title": "Scene 4: 即時アクションとワークフロー承認",
        "prompt": "検出された不整合に対して緊急の在庫再配分アクションを起票し、承認リクエストを提示してください。"
    },
    {
        "scene_id": "prompt_5",
        "scene_type": "investigation",
        "title": "Scene 5: 根本原因分析と品質検査",
        "prompt": "センサーテレメトリとロット別不良率を分析し、品質不整合の根本原因を特定してください。"
    },
    {
        "scene_id": "prompt_6",
        "scene_type": "simulation",
        "title": "Scene 6: 生産計画シミュレーションと予測的配分",
        "prompt": "現在の供給制約下における翌日の製造ライン処理能力をシミュレーションし、最適なスケジュールを再配分してください。"
    },
    {
        "scene_id": "prompt_7",
        "scene_type": "summary",
        "title": "Scene 7: 業務サマリーと推奨事項",
        "prompt": "本日の対応完了サマリーと、明日に向けた発注推奨事項をまとめてください。"
    }
]

DEFAULT_DEMO_PROMPTS = [sc["prompt"] for sc in DEFAULT_DEMO_SCENES_EN]

# Track cursor coordinates across the active browser session
_CURSOR_STATE = {"x": 960.0, "y": 540.0}


def ease_in_out_cubic(t: float) -> float:
    """Calculates cubic ease-in-out velocity easing for human-like motion."""
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - math.pow(-2.0 * t + 2.0, 3.0) / 2.0


async def inject_virtual_cursor(page) -> None:
    """Injects a realistic SVG cursor and interaction ripple container into the DOM.
    
    Ensures pointer motions and click actions are cleanly visible on CDP video frames.
    """
    cursor_script = """
    (() => {
      if (document.getElementById('__ge_virtual_cursor_root__')) return;

      const style = document.createElement('style');
      style.id = '__ge_virtual_cursor_style__';
      style.textContent = `
        #__ge_virtual_cursor_root__ {
          position: fixed;
          top: 0;
          left: 0;
          width: 0;
          height: 0;
          pointer-events: none;
          z-index: 2147483647;
        }
        #__ge_virtual_cursor__ {
          position: fixed;
          top: 0;
          left: 0;
          width: 24px;
          height: 24px;
          pointer-events: none;
          z-index: 2147483647;
          transform: translate3d(var(--cur-x, 960px), var(--cur-y, 540px), 0) scale(var(--cur-scale, 1));
          transform-origin: top left;
          transition: transform 0.04s cubic-bezier(0, 0, 0.2, 1);
          filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.45));
        }
        .ge-click-ripple {
          position: fixed;
          pointer-events: none;
          z-index: 2147483646;
          border-radius: 50%;
          border: 2px solid rgba(66, 133, 244, 0.85);
          background: radial-gradient(circle, rgba(66, 133, 244, 0.35) 0%, rgba(66, 133, 244, 0) 70%);
          transform: translate(-50%, -50%) scale(0.2);
          animation: geRippleAnim 0.42s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
        }
        @keyframes geRippleAnim {
          0% {
            width: 10px;
            height: 10px;
            opacity: 0.95;
            transform: translate(-50%, -50%) scale(0.25);
          }
          100% {
            width: 68px;
            height: 68px;
            opacity: 0;
            transform: translate(-50%, -50%) scale(1.6);
          }
        }
      `;
      (document.head || document.documentElement).appendChild(style);

      const root = document.createElement('div');
      root.id = '__ge_virtual_cursor_root__';
      root.innerHTML = `
        <div id="__ge_virtual_cursor__">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5.5 3.5L18.5 13.5L12.5 14.5L16 20.5L13.5 22L10 16L5.5 19.5V3.5Z" fill="#1A1A1A" stroke="#FFFFFF" stroke-width="1.5" stroke-linejoin="round"/>
          </svg>
        </div>
      `;
      (document.body || document.documentElement).appendChild(root);

      window.__updateGeCursor = (x, y, isDepressed) => {
        const cursor = document.getElementById('__ge_virtual_cursor__');
        if (!cursor) return;
        cursor.style.setProperty('--cur-x', `${x}px`);
        cursor.style.setProperty('--cur-y', `${y}px`);
        cursor.style.setProperty('--cur-scale', isDepressed ? '0.85' : '1.0');
      };

      window.__triggerGeRipple = (x, y) => {
        const ripple = document.createElement('div');
        ripple.className = 'ge-click-ripple';
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        (document.body || document.documentElement).appendChild(ripple);
        setTimeout(() => { ripple.remove(); }, 450);
      };

      window.addEventListener('mousemove', (e) => {
        window.__updateGeCursor(e.clientX, e.clientY, false);
      }, { passive: true });

      window.addEventListener('mousedown', (e) => {
        window.__updateGeCursor(e.clientX, e.clientY, true);
        window.__triggerGeRipple(e.clientX, e.clientY);
      }, { passive: true });

      window.addEventListener('mouseup', (e) => {
        window.__updateGeCursor(e.clientX, e.clientY, false);
      }, { passive: true });
    })();
    """
    try:
        await page.add_init_script(cursor_script)
        await page.evaluate(cursor_script)
    except Exception:
        pass


async def bezier_move(page, end_x: float, end_y: float, steps: int = 0) -> None:
    """Simulates a natural curved human mouse movement with cubic ease-in-out velocity."""
    start_x = _CURSOR_STATE["x"]
    start_y = _CURSOR_STATE["y"]
    dist = math.hypot(end_x - start_x, end_y - start_y)

    if dist < 2.0:
        _CURSOR_STATE["x"] = end_x
        _CURSOR_STATE["y"] = end_y
        await page.mouse.move(end_x, end_y)
        try:
            await page.evaluate("([x, y]) => window.__updateGeCursor && window.__updateGeCursor(x, y, false)", [end_x, end_y])
        except Exception:
            pass
        return

    if steps <= 0:
        steps = max(18, min(65, int(dist / 14.0)))

    # Perpendicular control point offset for natural curvature arc
    dx = end_x - start_x
    dy = end_y - start_y
    nx = -dy / dist
    ny = dx / dist
    curve_amp = min(90.0, dist * 0.22) * random.choice([-1.0, 1.0]) * random.uniform(0.6, 1.0)
    ctrl_x = (start_x + end_x) / 2.0 + nx * curve_amp
    ctrl_y = (start_y + end_y) / 2.0 + ny * curve_amp

    for i in range(1, steps + 1):
        raw_t = i / float(steps)
        t = ease_in_out_cubic(raw_t)
        curr_x = (1.0 - t) ** 2 * start_x + 2.0 * (1.0 - t) * t * ctrl_x + t ** 2 * end_x
        curr_y = (1.0 - t) ** 2 * start_y + 2.0 * (1.0 - t) * t * ctrl_y + t ** 2 * end_y

        await page.mouse.move(curr_x, curr_y)
        try:
            await page.evaluate("([x, y]) => window.__updateGeCursor && window.__updateGeCursor(x, y, false)", [curr_x, curr_y])
        except Exception:
            pass

        _CURSOR_STATE["x"] = curr_x
        _CURSOR_STATE["y"] = curr_y
        await asyncio.sleep(random.uniform(0.008, 0.016))

    # Ensure precise final coordinate
    await page.mouse.move(end_x, end_y)
    try:
        await page.evaluate("([x, y]) => window.__updateGeCursor && window.__updateGeCursor(x, y, false)", [end_x, end_y])
    except Exception:
        pass
    _CURSOR_STATE["x"] = end_x
    _CURSOR_STATE["y"] = end_y


async def click_target(page, x: float, y: float, press_scale: float = 0.85) -> None:
    """Moves to coordinate, animates cursor press and radial click ripple, and releases."""
    await bezier_move(page, x, y)
    await asyncio.sleep(random.uniform(0.10, 0.18))

    try:
        await page.evaluate(
            "([x, y, s]) => { if (window.__updateGeCursor) window.__updateGeCursor(x, y, true); if (window.__triggerGeRipple) window.__triggerGeRipple(x, y); }",
            [x, y, press_scale]
        )
    except Exception:
        pass

    await page.mouse.down()
    await asyncio.sleep(random.uniform(0.08, 0.14))
    await page.mouse.up()

    try:
        await page.evaluate(
            "([x, y]) => { if (window.__updateGeCursor) window.__updateGeCursor(x, y, false); }",
            [x, y]
        )
    except Exception:
        pass

    await asyncio.sleep(random.uniform(0.15, 0.25))


async def ensure_light_theme(page) -> None:
    """Ensures Gemini Enterprise Web UI is configured in Light Mode."""
    try:
        # Check computed background color of body
        bg = await page.evaluate("() => window.getComputedStyle(document.body).backgroundColor")
        if bg in ("rgb(255, 255, 255)", "rgba(255, 255, 255, 1)", "rgb(250, 250, 250)"):
            print("  ℹ️ Gemini Enterprise is already in Light Mode.")
            return

        print("  ⚙️ Switching Gemini Enterprise UI to Light Mode...")
        settings_btn = await page.query_selector("button[aria-label*='設定とヘルプ'], button[aria-label*='Settings and help']")
        if settings_btn and await settings_btn.is_visible():
            box = await settings_btn.bounding_box()
            if box:
                await click_target(page, box["x"] + box["width"] / 2.0, box["y"] + box["height"] / 2.0)
            else:
                await settings_btn.click()
            await asyncio.sleep(0.6)

            design_item = await page.query_selector("md-menu-item:has-text('デザイン'), md-menu-item:has-text('Theme')")
            if design_item and await design_item.is_visible():
                await design_item.click()
                await asyncio.sleep(0.6)

                light_opt = await page.query_selector("div.label:has-text('ライト'), div.label:has-text('Light')")
                if light_opt and await light_opt.is_visible():
                    await light_opt.click()
                    await asyncio.sleep(0.4)

            await page.keyboard.press("Escape")
            await asyncio.sleep(0.6)
            print("  ✅ Switched Gemini Enterprise to Light Mode.")
    except Exception as e:
        print(f"  ⚠️ Could not set light mode: {e}")


async def ensure_sidebar_collapsed(page) -> None:
    """Ensures the left navigation drawer is closed/collapsed before recording starts."""
    try:
        collapse_btn = await page.query_selector("button[aria-label*='サイドバーを閉じる'], button[aria-label*='Close sidebar']")
        if collapse_btn and await collapse_btn.is_visible():
            print("  🚪 Collapsing left navigation sidebar...")
            box = await collapse_btn.bounding_box()
            if box:
                await click_target(page, box["x"] + box["width"] / 2.0, box["y"] + box["height"] / 2.0)
            else:
                await collapse_btn.click()
            await asyncio.sleep(0.6)
            print("  ✅ Collapsed left navigation sidebar.")
    except Exception as e:
        print(f"  ⚠️ Could not collapse sidebar: {e}")


async def smooth_scroll_response_if_needed(page, dwell_sec: float) -> None:
    """If the agent response is tall and overflows the viewport, smoothly scrolls down so the full response is visible in the video."""
    try:
        scroll_info = await page.evaluate("""
        () => {
            function findDeepElement(selector, root) {
                root = root || document.body;
                if (!root) return null;
                if (root.matches && root.matches(selector)) return root;
                if (root.shadowRoot) {
                    const found = findDeepElement(selector, root.shadowRoot);
                    if (found) return found;
                }
                for (const c of root.children || []) {
                    const found = findDeepElement(selector, c);
                    if (found) return found;
                }
                return null;
            }

            function findDeepAll(matcher, root) {
                root = root || document.body;
                let results = [];
                if (!root) return results;
                if (matcher(root)) results.push(root);
                if (root.shadowRoot) {
                    for (const c of root.shadowRoot.children || []) {
                        results = results.concat(findDeepAll(matcher, c));
                    }
                }
                for (const c of root.children || []) {
                    results = results.concat(findDeepAll(matcher, c));
                }
                return results;
            }

            const scroller = findDeepElement(".chat-mode-scroller") ||
                             findDeepElement('[class*="scroll"]') ||
                             document.querySelector("main") ||
                             document.documentElement;

            const allTurns = findDeepAll(el => el.tagName === "UCS-SUMMARY" || (el.className && typeof el.className === "string" && el.className.includes("message-item")));
            const lastTurn = allTurns.length > 0 ? allTurns[allTurns.length - 1] : null;

            if (!scroller || !lastTurn) {
                const maxScroll = Math.max(0, (scroller ? scroller.scrollHeight - scroller.clientHeight : 0));
                return { needsScroll: maxScroll > 80, isFallback: true };
            }

            const scrollerRect = scroller.getBoundingClientRect();
            const turnRect = lastTurn.getBoundingClientRect();

            const topScroll = Math.max(0, scroller.scrollTop + (turnRect.top - scrollerRect.top) - 30);
            const targetBottomScroll = Math.max(topScroll, scroller.scrollTop + (turnRect.bottom - scrollerRect.bottom) - 30);
            const bottomScroll = Math.min(scroller.scrollHeight - scroller.clientHeight, targetBottomScroll);

            const isTall = turnRect.height > (scroller.clientHeight * 0.75) || (bottomScroll - topScroll) > 80;
            return {
                needsScroll: isTall,
                topScroll: topScroll,
                bottomScroll: bottomScroll,
                turnHeight: turnRect.height,
                scrollerHeight: scroller.clientHeight,
                currentScroll: scroller.scrollTop
            };
        }
        """)

        if scroll_info.get("needsScroll"):
            top_scroll = scroll_info.get("topScroll", 0)
            bottom_scroll = scroll_info.get("bottomScroll", 0)
            print(f"  📜 Tall response detected (turnHeight={scroll_info.get('turnHeight')}px, top={top_scroll}px -> bottom={bottom_scroll}px). Smooth scrolling full response...")

            # 1. Smoothly scroll up to the top of this response turn and dwell so viewer sees the initial header
            await page.evaluate("""
            (top) => {
                function findDeepElement(selector, root) {
                    root = root || document.body;
                    if (!root) return null;
                    if (root.matches && root.matches(selector)) return root;
                    if (root.shadowRoot) {
                        const found = findDeepElement(selector, root.shadowRoot);
                        if (found) return found;
                    }
                    for (const c of root.children || []) {
                        const found = findDeepElement(selector, c);
                        if (found) return found;
                    }
                    return null;
                }
                const scroller = findDeepElement(".chat-mode-scroller") ||
                                 findDeepElement('[class*="scroll"]') ||
                                 document.querySelector("main") ||
                                 window;
                if (scroller && scroller.scrollTo) {
                    scroller.scrollTo({top: top, behavior: 'smooth'});
                }
            }
            """, top_scroll)
            await asyncio.sleep(2.5)

            # 2. Smoothly scroll down across the response narration duration
            scroll_duration = max(4.0, dwell_sec - 5.5)
            steps = int(scroll_duration * 25)
            for i in range(1, steps + 1):
                raw_t = i / float(steps)
                ease = 4 * raw_t * raw_t * raw_t if raw_t < 0.5 else 1 - math.pow(-2 * raw_t + 2, 3) / 2.0
                curr_y = top_scroll + ease * (bottom_scroll - top_scroll)
                await page.evaluate("""
                (y) => {
                    function findDeepElement(selector, root) {
                        root = root || document.body;
                        if (!root) return null;
                        if (root.matches && root.matches(selector)) return root;
                        if (root.shadowRoot) {
                            const found = findDeepElement(selector, root.shadowRoot);
                            if (found) return found;
                        }
                        for (const c of root.children || []) {
                            const found = findDeepElement(selector, c);
                            if (found) return found;
                        }
                        return null;
                    }
                    const scroller = findDeepElement(".chat-mode-scroller") ||
                                     findDeepElement('[class*="scroll"]') ||
                                     document.querySelector("main") ||
                                     window;
                    if (scroller) {
                        scroller.scrollTop = y;
                    }
                }
                """, curr_y)
                await asyncio.sleep(scroll_duration / float(steps))

            await asyncio.sleep(2.5)
            # Dwell remaining time so raw recording completes full dwell duration
            elapsed_scroll = 2.5 + scroll_duration + 2.5
            remaining = max(0.0, dwell_sec - elapsed_scroll)
            if remaining > 0:
                await asyncio.sleep(remaining)
        else:
            await asyncio.sleep(dwell_sec)
    except Exception as e:
        print(f"  Note on response scrolling: {e}")
        await asyncio.sleep(dwell_sec)


async def natural_type(page, selector: str, text: str, min_delay_ms: int = 25, max_delay_ms: int = 40) -> None:
    """Focuses input element, clears existing text, and types with word bursts and cognitive pauses."""
    element = await page.query_selector(selector)
    if not element:
        raise RuntimeError(f"Input element not found: {selector}")

    box = await element.bounding_box()
    if box:
        center_x = box["x"] + box["width"] / 2.0
        center_y = box["y"] + box["height"] / 2.0
        await click_target(page, center_x, center_y)
    else:
        await element.click()

    # Pre-typing input clearing (Ctrl+A / Meta+A then Backspace)
    await page.keyboard.press("Control+A")
    await page.keyboard.press("Backspace")

    # Ensure rich-text and contenteditable inputs are completely cleared
    try:
        await page.evaluate("""el => {
            if (el.isContentEditable) {
                el.innerText = '';
                el.textContent = '';
                el.focus();
            } else if ('value' in el) {
                el.value = '';
            }
        }""", element)
    except Exception:
        pass

    # Cognitive hesitation before typing starts (300-450ms)
    await asyncio.sleep(random.uniform(0.30, 0.45))

    for char in text:
        if char == " ":
            await page.keyboard.type(" ")
            # Inter-word burst pause (90-160ms)
            await asyncio.sleep(random.uniform(0.090, 0.160))
        elif char in (",", ".", "!", "?", "、", "。", ";", ":"):
            await page.keyboard.type(char)
            # Thinking pause at sentence clauses and punctuation (300-450ms)
            await asyncio.sleep(random.uniform(0.300, 0.450))
        else:
            await page.keyboard.type(char)
            # Rapid intra-word typing interval (25-40ms)
            await asyncio.sleep(random.uniform(min_delay_ms / 1000.0, max_delay_ms / 1000.0))
            # Rare human cognitive hesitation
            if random.random() < 0.03:
                await asyncio.sleep(random.uniform(0.180, 0.320))

    # Post-typing cognitive pause
    await asyncio.sleep(random.uniform(0.35, 0.50))


def _build_mock_scene_svg(title: str, scene_type: str, prompt_text: str, state: str, button_label: str = "Execute Reallocation Now") -> str:
    """Generates a styled 1920x1080 light-mode Gemini Enterprise SVG frame."""
    prompt_esc = html.escape(prompt_text)
    title_esc = html.escape(title)
    btn_esc = html.escape(button_label)

    svg = f"""<svg width="1920" height="1080" viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="geminiSparkle" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4285F4"/>
      <stop offset="50%" stop-color="#9B72CB"/>
      <stop offset="100%" stop-color="#D96570"/>
    </linearGradient>
  </defs>

  <!-- Background (Light Mode) -->
  <rect width="100%" height="100%" fill="#FFFFFF"/>

  <!-- Left Sidebar (Light Mode) -->
  <rect x="0" y="0" width="280" height="1080" fill="#F8F9FA"/>
  <line x1="280" y1="0" x2="280" y2="1080" stroke="#E0E2E6" stroke-width="1"/>

  <!-- Gemini Enterprise Header -->
  <path d="M32 36 L36 24 L40 36 L52 40 L40 44 L36 56 L32 44 L20 40 Z" fill="url(#geminiSparkle)"/>
  <text x="62" y="46" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="bold">Gemini Enterprise</text>

  <!-- New Chat Pill -->
  <rect x="24" y="80" width="232" height="44" rx="22" fill="#EDF2FA" stroke="#D3E3FD" stroke-width="1"/>
  <text x="54" y="108" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="500">+ New conversation</text>

  <!-- Recent Chats List -->
  <text x="24" y="160" fill="#5F6368" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="bold" letter-spacing="1">RECENT SESSIONS</text>
  <text x="24" y="196" fill="#3C4043" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">• Operational Briefing</text>
  <text x="24" y="232" fill="#3C4043" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">• Cross-Source Ledger Audit</text>
  <text x="24" y="268" fill="#3C4043" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">• Inventory Reallocation</text>

  <!-- Top Navigation Header -->
  <rect x="280" y="0" width="1640" height="64" fill="#FFFFFF"/>
  <line x1="280" y1="64" x2="1920" y2="64" stroke="#E0E2E6" stroke-width="1"/>
  <rect x="310" y="16" width="230" height="32" rx="16" fill="#F1F3F4" stroke="#DADCE0" stroke-width="1"/>
  <text x="328" y="37" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13">✨ Gemini 2.5 Pro Enterprise</text>

  <!-- User Avatar Pill -->
  <circle cx="1860" cy="32" r="18" fill="#1A73E8"/>
  <text x="1860" y="38" fill="white" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="bold" text-anchor="middle">E</text>
"""

    if state == "typing":
        svg += f"""
  <!-- Active Prompt Input Bar -->
  <rect x="440" y="920" width="1040" height="80" rx="24" fill="#FFFFFF" stroke="#1A73E8" stroke-width="2"/>
  <text x="480" y="968" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="18">{prompt_esc}<tspan fill="#1A73E8">|</tspan></text>
  <circle cx="1430" cy="960" r="20" fill="#1A73E8"/>
  <path d="M1422 960 L1436 960 M1430 954 L1436 960 L1430 966" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>

  <!-- In-DOM Virtual Cursor on Send Button -->
  <g transform="translate(1430, 960)">
    <path d="M0 0 L13 13 L8 14 L12 21 L9 22 L5 15 L0 19 Z" fill="#1F1F1F" stroke="white" stroke-width="1.5"/>
  </g>
"""
    elif state == "thinking":
        svg += f"""
  <!-- User Prompt Bubble -->
  <rect x="720" y="110" width="760" height="64" rx="18" fill="#E8F0FE"/>
  <text x="750" y="148" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="17">{prompt_esc}</text>

  <!-- Agent Thinking Indicator -->
  <g transform="translate(360, 240)">
    <path d="M16 20 L20 8 L24 20 L36 24 L24 28 L20 40 L16 28 L4 24 Z" fill="url(#geminiSparkle)"/>
    <rect x="54" y="10" width="300" height="36" rx="18" fill="#F8F9FA" stroke="#DADCE0"/>
    <text x="74" y="33" fill="#1A73E8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">Thinking • Querying Enterprise Data...</text>
  </g>
"""
    else:  # response state
        svg += f"""
  <!-- User Prompt Bubble -->
  <rect x="720" y="85" width="760" height="54" rx="18" fill="#E8F0FE"/>
  <text x="750" y="119" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16">{prompt_esc}</text>

  <!-- Main Agent Response Card -->
  <g transform="translate(360, 160)">
    <rect width="1120" height="730" rx="16" fill="#FFFFFF" stroke="#DADCE0" stroke-width="1"/>
    
    <!-- Sparkle & Title -->
    <path d="M28 32 L32 20 L36 32 L48 36 L36 40 L32 52 L28 40 L16 36 Z" fill="url(#geminiSparkle)"/>
    <text x="64" y="42" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="bold">{title_esc}</text>
    <rect x="910" y="24" width="170" height="28" rx="14" fill="#E6F4EA" stroke="#34A853"/>
    <text x="995" y="43" fill="#137333" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="bold" text-anchor="middle">LIVE SYNCHRONIZED</text>

    <!-- KPI Metrics -->
    <g transform="translate(40, 75)">
      <rect x="0" y="0" width="320" height="80" rx="12" fill="#F8F9FA" stroke="#E0E2E6"/>
      <text x="20" y="32" fill="#5F6368" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13">TOTAL TRANSACTIONS</text>
      <text x="20" y="64" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="24" font-weight="bold">14,820 Units</text>

      <rect x="350" y="0" width="320" height="80" rx="12" fill="#FCE8E6" stroke="#F28B82"/>
      <text x="370" y="32" fill="#C5221F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13">ANOMALY COUNT</text>
      <text x="370" y="64" fill="#C5221F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="24" font-weight="bold">128 Shipments</text>

      <rect x="700" y="0" width="320" height="80" rx="12" fill="#E8F0FE" stroke="#8AB4F8"/>
      <text x="720" y="32" fill="#1A73E8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13">FINANCIAL IMPACT</text>
      <text x="720" y="64" fill="#1A73E8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="24" font-weight="bold">$342,500.00</text>
    </g>

    <!-- Structured Data Table -->
    <g transform="translate(40, 185)">
      <rect width="1040" height="370" rx="10" fill="#FFFFFF" stroke="#DADCE0"/>
      
      <!-- Table Header -->
      <rect width="1040" height="44" rx="10" fill="#F1F3F4"/>
      <text x="24" y="28" fill="#5F6368" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="bold">SHIPMENT ID</text>
      <text x="220" y="28" fill="#5F6368" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="bold">SUPPLIER / CARRIER</text>
      <text x="480" y="28" fill="#5F6368" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="bold">EXPECTED</text>
      <text x="640" y="28" fill="#5F6368" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="bold">ACTUAL</text>
      <text x="780" y="28" fill="#5F6368" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="bold">VARIANCE</text>
      <text x="920" y="28" fill="#5F6368" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="bold">STATUS</text>

      <!-- Row 1 -->
      <line x1="0" y1="94" x2="1040" y2="94" stroke="#E0E2E6"/>
      <text x="24" y="76" fill="#1A73E8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">SHP-2026-8821</text>
      <text x="220" y="76" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">Apex Global Logistics</text>
      <text x="480" y="76" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">1,200</text>
      <text x="640" y="76" fill="#D93025" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">850</text>
      <text x="780" y="76" fill="#D93025" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="bold">-350 Units</text>
      <rect x="910" y="58" width="100" height="26" rx="13" fill="#FCE8E6"/>
      <text x="960" y="75" fill="#C5221F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="bold" text-anchor="middle">CRITICAL</text>

      <!-- Row 2 -->
      <line x1="0" y1="144" x2="1040" y2="144" stroke="#E0E2E6"/>
      <text x="24" y="126" fill="#1A73E8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">SHP-2026-8845</text>
      <text x="220" y="126" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">Pacific Freightways</text>
      <text x="480" y="126" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">2,400</text>
      <text x="640" y="126" fill="#E37400" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">2,180</text>
      <text x="780" y="126" fill="#E37400" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="bold">-220 Units</text>
      <rect x="910" y="108" width="100" height="26" rx="13" fill="#FEF7E0"/>
      <text x="960" y="125" fill="#B06000" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="bold" text-anchor="middle">WARNING</text>

      <!-- Row 3 -->
      <line x1="0" y1="194" x2="1040" y2="194" stroke="#E0E2E6"/>
      <text x="24" y="176" fill="#1A73E8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">SHP-2026-8890</text>
      <text x="220" y="176" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">Continental Air Cargo</text>
      <text x="480" y="176" fill="#1F1F1F" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">5,000</text>
      <text x="640" y="176" fill="#137333" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14">5,000</text>
      <text x="780" y="176" fill="#137333" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="bold">0 (Match)</text>
      <rect x="910" y="158" width="100" height="26" rx="13" fill="#E6F4EA"/>
      <text x="960" y="175" fill="#137333" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="bold" text-anchor="middle">VERIFIED</text>
    </g>

    <!-- Interactive Workflow Button -->
    <g transform="translate(40, 585)">
      <rect x="0" y="0" width="340" height="52" rx="26" fill="#1A73E8"/>
      <text x="170" y="32" fill="#FFFFFF" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="bold" text-anchor="middle">{btn_esc}</text>
      
      <!-- Radial Click Ripple Animation Feedback -->
      <circle cx="170" cy="26" r="30" fill="rgba(66, 133, 244, 0.25)" stroke="#4285F4" stroke-width="2"/>
      
      <!-- In-DOM Virtual Cursor Depressed (scale 0.85) -->
      <g transform="translate(170, 26) scale(0.85)">
        <path d="M0 0 L13 13 L8 14 L12 21 L9 22 L5 15 L0 19 Z" fill="#1F1F1F" stroke="white" stroke-width="1.5"/>
      </g>
    </g>
  </g>
"""

    svg += "</svg>"
    return svg


def generate_mock_recording(outdir: str, prompts: list[str] = None, lang: str = "ja-JP") -> tuple[str, list[dict], float]:
    """Renders a stylized light-mode Gemini Enterprise UI walkthrough matching demo scenes."""
    os.makedirs(outdir, exist_ok=True)
    video_path = os.path.join(outdir, "raw_recording.mp4")
    scenes_def = DEFAULT_DEMO_SCENES_JA if lang.startswith("ja") else DEFAULT_DEMO_SCENES_EN
    prompts_to_use = prompts or [sc["prompt"] for sc in scenes_def]

    tmpdir = tempfile.mkdtemp(prefix="ge_mock_rec_")
    segment_files = []
    actions = []
    current_time = 0.0

    try:
        for idx, prompt_text in enumerate(prompts_to_use):
            if idx < len(scenes_def):
                scene_id = scenes_def[idx]["scene_id"]
                scene_type = scenes_def[idx]["scene_type"]
                title = scenes_def[idx]["title"]
            else:
                scene_id = f"prompt_{idx + 1}"
                scene_type = "welcome" if idx == 0 else ("catalog" if idx == 1 else ("analytics_wow" if idx == 2 else ("workflow_action" if idx == 3 else "summary")))
                title = f"Scene {idx + 1}"

            # Realistic timeline segments
            dur_typing = round(max(3.0, min(6.0, len(prompt_text) * 0.045)), 1)
            dur_thinking = 2.5
            dur_response = 7.5

            t_type_start = round(current_time + 1.0, 2)
            t_type_end = round(t_type_start + dur_typing, 2)
            t_submit = round(t_type_end + 0.3, 2)
            t_wait_start = t_submit
            t_response_start = round(t_wait_start + dur_thinking, 2)
            t_response_complete = round(t_response_start + dur_response, 2)

            act_entry = {
                "scene_id": scene_id,
                "scene_type": scene_type,
                "title": title,
                "prompt_text": prompt_text,
                "t_type_start": t_type_start,
                "t_type_end": t_type_end,
                "t_submit": t_submit,
                "t_wait_start": t_wait_start,
                "t_response_start": t_response_start,
                "t_response_complete": t_response_complete,
                "focus_rect": {"x": 360, "y": 160, "width": 1120, "height": 730}
            }

            if scene_type == "workflow_action":
                act_entry["action_click"] = {
                    "t_click": round(t_response_start + 3.2, 2),
                    "button_label": "Execute Reallocation Now"
                }

            actions.append(act_entry)

            # Build SVGs for the 3 scene states
            typing_svg = os.path.join(tmpdir, f"s_{idx}_type.svg")
            thinking_svg = os.path.join(tmpdir, f"s_{idx}_think.svg")
            response_svg = os.path.join(tmpdir, f"s_{idx}_resp.svg")

            with open(typing_svg, "w", encoding="utf-8") as f:
                f.write(_build_mock_scene_svg(title, scene_type, prompt_text, "typing"))
            with open(thinking_svg, "w", encoding="utf-8") as f:
                f.write(_build_mock_scene_svg(title, scene_type, prompt_text, "thinking"))
            with open(response_svg, "w", encoding="utf-8") as f:
                f.write(_build_mock_scene_svg(title, scene_type, prompt_text, "response"))

            # Render video segments via FFmpeg
            seg_typing = os.path.join(tmpdir, f"seg_{idx}_type.mp4")
            seg_thinking = os.path.join(tmpdir, f"seg_{idx}_think.mp4")
            seg_response = os.path.join(tmpdir, f"seg_{idx}_resp.mp4")

            typing_total_dur = round(t_submit - current_time, 2)
            thinking_total_dur = round(t_response_start - t_submit, 2)
            response_total_dur = round(t_response_complete - t_response_start, 2)

            for svg_path, dur, mp4_out in [
                (typing_svg, typing_total_dur, seg_typing),
                (thinking_svg, thinking_total_dur, seg_thinking),
                (response_svg, response_total_dur, seg_response)
            ]:
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-t", str(dur),
                    "-r", "30",
                    "-i", svg_path,
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-preset", "veryfast",
                    mp4_out
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                segment_files.append(mp4_out)

            current_time = t_response_complete

        # Concatenate segments into raw_recording.mp4
        concat_manifest = os.path.join(tmpdir, "concat.txt")
        with open(concat_manifest, "w", encoding="utf-8") as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")

        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_manifest,
            "-c", "copy",
            video_path
        ]
        subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"  ✅ Created stylized mock recording video: {video_path} ({current_time:.1f}s)")

    except Exception as e:
        print(f"  ⚠️ FFmpeg mock compilation failed ({e}), creating fallback color test video")
        fallback_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=#131314:s=1920x1080:d={current_time or 30.0}:r=30",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            video_path
        ]
        try:
            subprocess.run(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            with open(video_path, "wb") as f:
                f.write(b"")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return video_path, actions, round(current_time, 2)


def is_cdp_port_open(url: str = DEFAULT_CDP_URL) -> bool:
    """Checks whether the Chrome DevTools Protocol port is open and accepting requests."""
    import urllib.request
    try:
        req = urllib.request.Request(f"{url.rstrip('/')}/json/version", headers={"User-Agent": "ge-demo-recorder"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def auto_launch_chrome(port: int = 9222, headless: bool = True, session_url: str = "") -> subprocess.Popen:
    """Launches Chrome with remote debugging enabled in the background."""
    chrome_bin = (
        shutil.which("google-chrome")
        or shutil.which("chrome")
        or shutil.which("chromium")
        or "/opt/google/chrome/chrome"
    )
    profile_dir = os.path.expanduser("~/.config/ge-demo-video/chrome-profile")
    os.makedirs(profile_dir, exist_ok=True)

    cmd = [
        chrome_bin,
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile_dir}",
        "--window-size=1920,1080",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=Translate,OptimizationHints",
        "--disable-infobars",
    ]
    if headless:
        cmd.append("--headless=new")
    if session_url:
        cmd.append(session_url)

    print(f"🚀 Auto-launching Google Chrome on CDP port {port} (headless={headless})...")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

    for _ in range(20):
        time.sleep(0.5)
        if is_cdp_port_open(f"http://localhost:{port}"):
            print(f"  ✅ Chrome CDP port {port} is ready and listening.")
            return proc

    return proc


async def record_session(args) -> dict:
    """Connects to Chrome via CDP, executes prompts, and records actions and video frames."""
    os.makedirs(args.outdir, exist_ok=True)
    video_path = os.path.join(args.outdir, "raw_recording.mp4")
    actions_manifest_path = os.path.join(args.outdir, "actions.json")

    lang = getattr(args, "lang", "") or ("ja-JP" if os.environ.get("CURRENCY_SYMBOL") in ("¥", "円") else "en-US")
    if args.prompts:
        prompts = args.prompts
    else:
        scenes_default = DEFAULT_DEMO_SCENES_JA if lang.startswith("ja") else DEFAULT_DEMO_SCENES_EN
        prompts = [sc["prompt"] for sc in scenes_default]

    # Headless / offline simulated recording
    if args.mock:
        print("ℹ️ Running in --mock mode. Synthesizing realistic light-mode action telemetry and mock video.")
        mock_video, mock_actions, total_duration = generate_mock_recording(args.outdir, prompts=prompts, lang=lang)
        manifest_data = {
            "session_url": args.session_url or "https://vertexaisearch.cloud.google.com/home/cid/mock/r/agent/mock/session/-",
            "viewport": DEFAULT_VIEWPORT,
            "total_duration_sec": total_duration,
            "raw_video_path": mock_video,
            "actions": mock_actions
        }
        with open(actions_manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        return manifest_data

    # Live CDP Browser Automation
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        if getattr(args, "fallback_mock", False):
            print("⚠️ Playwright not installed. Falling back to synthetic mock recording.", file=sys.stderr)
            mock_video, mock_actions, total_duration = generate_mock_recording(args.outdir, prompts=prompts, lang=lang)
            manifest_data = {
                "session_url": args.session_url or "https://vertexaisearch.cloud.google.com/home/cid/mock/r/agent/mock/session/-",
                "viewport": DEFAULT_VIEWPORT,
                "total_duration_sec": total_duration,
                "raw_video_path": mock_video,
                "actions": mock_actions
            }
            with open(actions_manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
            return manifest_data
        print("⚠️ Playwright not installed. Please install with `uv pip install playwright` or run with `--mock`.", file=sys.stderr)
        sys.exit(1)

    # Check if CDP port is open; auto-launch if requested and not running
    chrome_proc = None
    if getattr(args, "auto_launch", True) and not is_cdp_port_open(args.cdp_url):
        port = 9222
        try:
            port = int(args.cdp_url.split(":")[-1].split("/")[0])
        except Exception:
            pass
        chrome_proc = auto_launch_chrome(port=port, headless=getattr(args, "headless", True), session_url=args.session_url)

    print(f"Connecting to Chrome via CDP at {args.cdp_url}...")
    recorded_actions = []

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(args.cdp_url)
        except Exception as e:
            if getattr(args, "fallback_mock", False):
                print(f"⚠️ Could not connect to Chrome at {args.cdp_url} ({e}). Switching to synthetic demo recording.")
                mock_video, mock_actions, total_duration = generate_mock_recording(args.outdir, prompts=prompts)
                manifest_data = {
                    "session_url": args.session_url or "https://vertexaisearch.cloud.google.com/home/cid/mock/r/agent/mock/session/-",
                    "viewport": DEFAULT_VIEWPORT,
                    "total_duration_sec": total_duration,
                    "raw_video_path": mock_video,
                    "actions": mock_actions
                }
                with open(actions_manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, indent=2, ensure_ascii=False)
                return manifest_data
            print(f"❌ Failed to connect to Chrome at {args.cdp_url}: {e}", file=sys.stderr)
            sys.exit(1)

        # Tab Management: Search open tabs for matching session URL or spawn dedicated tab
        ge_page = None
        for ctx in browser.contexts:
            for p_item in ctx.pages:
                try:
                    u = p_item.url or ""
                    parsed_u = urllib.parse.urlparse(u)
                    u_host = (parsed_u.hostname or "").lower()
                    if args.session_url and (args.session_url == u or args.session_url in u or u in args.session_url):
                        ge_page = p_item
                        break
                    if u_host == "vertexaisearch.cloud.google.com" or u_host.endswith(".vertexaisearch.cloud.google.com") or "gemini" in u_host:
                        ge_page = p_item
                        break
                except Exception:
                    pass
            if ge_page:
                break

        if ge_page:
            page = ge_page
            print(f"Reusing existing browser session tab: {page.url}")
        else:
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await context.new_page()
            print("Opened dedicated tab for session recording.")

        await page.set_viewport_size(DEFAULT_VIEWPORT)
        await inject_virtual_cursor(page)

        # Navigate if needed with domcontentloaded wait
        if args.session_url and page.url != args.session_url:
            print(f"Navigating to session: {args.session_url}")
            await page.goto(args.session_url, wait_until="domcontentloaded", timeout=60000)
            try:
                await page.wait_for_selector("textarea, div[contenteditable='true'], input", timeout=20000)
            except Exception:
                pass
            await asyncio.sleep(2.0)
            await inject_virtual_cursor(page)

        # Check for Google login boundary
        parsed_page_url = urllib.parse.urlparse(page.url)
        page_host = (parsed_page_url.hostname or "").lower()
        if page_host == "accounts.google.com" or page_host.endswith(".accounts.google.com") or "signin" in parsed_page_url.path:
            print(f"ℹ️ Chrome session reached Google Accounts authentication boundary ({page.url}).")
            if getattr(args, "fallback_mock", False):
                print("🎬 Mock fallback enabled: switching to synthetic recording.")
                mock_video, mock_actions, total_duration = generate_mock_recording(args.outdir, prompts=prompts)
                manifest_data = {
                    "session_url": args.session_url or "https://vertexaisearch.cloud.google.com/home/cid/mock/r/agent/mock/session/-",
                    "viewport": DEFAULT_VIEWPORT,
                    "total_duration_sec": total_duration,
                    "raw_video_path": mock_video,
                    "actions": mock_actions
                }
                with open(actions_manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, indent=2, ensure_ascii=False)
                return manifest_data
            else:
                print("❌ Authentication Required: Chrome session is at Google Accounts sign-in screen.", file=sys.stderr)
                print("   Mock fallback is strictly disabled for production runs.", file=sys.stderr)
                print("   Please complete login in the opened Chrome window and retry.", file=sys.stderr)
                sys.exit(2)

        # -----------------------------------------------------------------
        # Ensure Gemini Enterprise UI is in Light Mode & Sidebar is collapsed
        # -----------------------------------------------------------------
        await ensure_light_theme(page)
        await ensure_sidebar_collapsed(page)
        await inject_virtual_cursor(page)
        await asyncio.sleep(1.0)

        # -----------------------------------------------------------------
        # Live CDP Screencast Capture: Stream Page.startScreencast to FFmpeg
        # -----------------------------------------------------------------
        cdp_session = await page.context.new_cdp_session(page)
        latest_frame_bytes = None
        first_frame_event = asyncio.Event()

        async def on_screencast_frame(params):
            nonlocal latest_frame_bytes
            data = params.get("data")
            session_id = params.get("sessionId")
            if data:
                latest_frame_bytes = base64.b64decode(data)
                first_frame_event.set()
            if session_id is not None:
                try:
                    await cdp_session.send("Page.screencastFrameAck", {"sessionId": session_id})
                except Exception:
                    pass

        cdp_session.on("Page.screencastFrame", on_screencast_frame)

        # Spawn FFmpeg encoder accepting MJPEG frames over stdin
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "image2pipe",
            "-vcodec", "mjpeg",
            "-r", "30",
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            "-movflags", "+faststart",
            video_path
        ]
        ffmpeg_proc = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )

        await cdp_session.send("Page.startScreencast", {
            "format": "jpeg",
            "quality": 85,
            "maxWidth": 1920,
            "maxHeight": 1080,
            "everyNthFrame": 1
        })

        # Steady 30fps feeder loop with drift compensation
        stop_screencast = asyncio.Event()

        async def screencast_writer():
            try:
                await asyncio.wait_for(first_frame_event.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                pass

            fps = 30.0
            frame_interval = 1.0 / fps
            start_loop = asyncio.get_event_loop().time()
            frames_sent = 0

            while not stop_screencast.is_set():
                if latest_frame_bytes is not None and ffmpeg_proc.stdin:
                    try:
                        ffmpeg_proc.stdin.write(latest_frame_bytes)
                        await ffmpeg_proc.stdin.drain()
                        frames_sent += 1
                    except (BrokenPipeError, ConnectionResetError):
                        break

                target_time = start_loop + (frames_sent * frame_interval)
                sleep_duration = target_time - asyncio.get_event_loop().time()
                if sleep_duration > 0:
                    await asyncio.sleep(sleep_duration)
                else:
                    await asyncio.sleep(0)

        writer_task = asyncio.create_task(screencast_writer())

        start_time = time.time()

        try:
            # Common input selectors in Gemini Enterprise Web UI
            input_selectors = [
                "div.ProseMirror",
                "div[contenteditable='true']",
                "textarea[placeholder*='Ask']",
                "textarea[aria-label*='prompt']",
                "textarea",
                "input[type='text']"
            ]

            # Build list of scenes to execute
            if args.prompts:
                scenes_to_run = []
                default_scenes = DEFAULT_DEMO_SCENES_JA if lang.startswith("ja") else DEFAULT_DEMO_SCENES_EN
                type_archetypes = ["welcome", "catalog", "analytics_wow", "workflow_action", "investigation", "simulation", "summary"]
                for idx, p in enumerate(args.prompts):
                    s_id = f"prompt_{idx + 1}"
                    s_type = type_archetypes[idx] if idx < len(type_archetypes) else "summary"
                    sc_title = default_scenes[idx]["title"] if idx < len(default_scenes) else f"Scene {idx + 1}"
                    scenes_to_run.append({
                        "scene_id": s_id,
                        "scene_type": s_type,
                        "title": sc_title,
                        "prompt": p
                    })
            else:
                scenes_to_run = DEFAULT_DEMO_SCENES_JA if lang.startswith("ja") else DEFAULT_DEMO_SCENES_EN

            # Read per-scene audio durations from narration manifest if available
            scene_durations = {}
            if getattr(args, "narration", "") and os.path.exists(args.narration):
                try:
                    with open(args.narration, "r", encoding="utf-8") as f:
                        narr_data = json.load(f)
                    for sc in narr_data.get("scenes", []):
                        if "phases" in sc and "response" in sc["phases"]:
                            scene_durations[sc["scene_id"]] = sc["phases"]["response"].get("duration_sec", 18.0)
                        else:
                            scene_durations[sc["scene_id"]] = sc.get("duration_sec", 18.0)
                except Exception:
                    pass

            for idx, sc_item in enumerate(scenes_to_run):
                scene_id = sc_item["scene_id"]
                scene_type = sc_item["scene_type"]
                prompt_text = sc_item["prompt"]
                title = sc_item.get("title", f"Scene {idx + 1}")
                print(f"\n--- Scene {idx + 1}: {scene_id} ({scene_type}) ---")

                t_type_start = time.time() - start_time
                active_input = None
                for sel in input_selectors:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        active_input = sel
                        break

                if active_input:
                    print(f"Typing prompt into {active_input}...")
                    # Count rating and copy buttons before submission to track new response accurately
                    prev_rating_count = await page.locator("button[aria-label*='良い回答'], button[aria-label*='Good response'], button[aria-label*='回答を評価'], button[aria-label*='コピー'], button[aria-label*='Copy']").count()

                    await natural_type(page, active_input, prompt_text)
                    t_type_end = time.time() - start_time

                    # Choreograph submit action via Send button or Enter
                    await asyncio.sleep(0.4)
                    send_btn = await page.query_selector("button[aria-label*='送信'], button[aria-label*='Send'], button[aria-label*='submit'], button[type='submit']")
                    if send_btn and await send_btn.is_visible():
                        btn_box = await send_btn.bounding_box()
                        if btn_box:
                            await click_target(page, btn_box["x"] + btn_box["width"] / 2.0, btn_box["y"] + btn_box["height"] / 2.0)
                        try:
                            await send_btn.click()
                        except Exception:
                            pass
                    else:
                        await page.keyboard.press("Enter")

                    # Verify if text was submitted; if input still contains text, retry submit
                    for _ in range(6):
                        await asyncio.sleep(0.5)
                        curr_in_el = await page.query_selector(active_input)
                        if curr_in_el:
                            curr_val = (await curr_in_el.inner_text()).strip()
                            if not curr_val:
                                break
                        if send_btn and await send_btn.is_visible():
                            try:
                                await send_btn.click()
                            except Exception:
                                pass
                        await page.keyboard.press("Enter")

                    t_submit = time.time() - start_time
                    t_wait_start = t_submit

                    print("Waiting for response stream to begin...")
                    t_response_start = None
                    for _ in range(40):
                        await asyncio.sleep(0.5)
                        stop_btn = await page.query_selector("button[aria-label*='停止'], button[aria-label*='Stop']")
                        if stop_btn and await stop_btn.is_visible():
                            t_response_start = time.time() - start_time
                            break
                        cur_rating_count = await page.locator("button[aria-label*='良い回答'], button[aria-label*='Good response'], button[aria-label*='回答を評価'], button[aria-label*='コピー'], button[aria-label*='Copy']").count()
                        if cur_rating_count > prev_rating_count:
                            t_response_start = time.time() - start_time
                            break

                    if t_response_start is None:
                        t_response_start = time.time() - start_time

                    print("Waiting for response stream to complete...")
                    stable_done_count = 0
                    last_text_len = 0
                    for _ in range(480):
                        await asyncio.sleep(0.5)
                        stop_btn = await page.query_selector("button[aria-label*='停止'], button[aria-label*='Stop']")
                        if stop_btn and await stop_btn.is_visible():
                            stable_done_count = 0
                            continue

                        # Check if agent requires authorization button
                        auth_btn_found = await page.evaluate("""
                        () => {
                            function findDeep(matcher, root) {
                                root = root || document.body;
                                if (!root) return null;
                                if (matcher(root)) return root;
                                if (root.shadowRoot) {
                                    for (const c of root.shadowRoot.children || []) {
                                        const res = findDeep(matcher, c);
                                        if (res) return res;
                                    }
                                }
                                for (const c of root.children || []) {
                                    const res = findDeep(matcher, c);
                                    if (res) return res;
                                }
                                return null;
                            }
                            const btn = findDeep(el => (el.tagName === "MD-FILLED-BUTTON" || el.tagName === "BUTTON") && (el.innerText || "").match(/Authorize|承認/i));
                            if (btn) {
                                btn.click();
                                return true;
                            }
                            return false;
                        }
                        """)
                        if auth_btn_found:
                            print("Authorization button detected and clicked. Handling consent...")
                            await asyncio.sleep(2.0)
                            for p in page.context.pages:
                                p_host = urllib.parse.urlparse(p.url).hostname or ""
                                if p_host == "accounts.google.com" or p_host.endswith(".google.com"):
                                    try:
                                        acc = await p.query_selector('div[role="link"]:has-text("@"), [data-email]')
                                        if acc:
                                            await acc.click()
                                            await asyncio.sleep(2.0)
                                        cont = await p.query_selector('button:has-text("Continue"), button:has-text("次へ")')
                                        if cont:
                                            await cont.click()
                                            await asyncio.sleep(2.0)
                                        allow = await p.query_selector('button:has-text("Allow"), button:has-text("許可")')
                                        if allow:
                                            await allow.click()
                                            await asyncio.sleep(3.0)
                                    except Exception as ex:
                                        print(f"OAuth flow auto-handling: {ex}")

                        cur_rating_count = await page.locator("button[aria-label*='良い回答'], button[aria-label*='Good response'], button[aria-label*='回答を評価'], button[aria-label*='コピー'], button[aria-label*='Copy']").count()

                        # Check text length of the latest response turn
                        curr_text_len = await page.evaluate("""
                        () => {
                            function findDeepAll(matcher, root) {
                                root = root || document.body;
                                let res = [];
                                if (!root) return res;
                                if (matcher(root)) res.push(root);
                                if (root.shadowRoot) {
                                    for (const c of root.shadowRoot.children || []) {
                                        res = res.concat(findDeepAll(matcher, c));
                                    }
                                }
                                for (const c of root.children || []) {
                                    res = res.concat(findDeepAll(matcher, c));
                                }
                                return res;
                            }
                            const turns = findDeepAll(el => el.tagName === "UCS-SUMMARY" || (el.className && typeof el.className === "string" && el.className.includes("message-item")));
                            if (turns.length === 0) return 0;
                            return (turns[turns.length - 1].innerText || "").length;
                        }
                        """)

                        is_ready = False
                        if cur_rating_count > prev_rating_count:
                            is_ready = True
                        elif curr_text_len > 20 and curr_text_len == last_text_len and (time.time() - start_time - t_response_start) > 6.0:
                            is_ready = True

                        last_text_len = curr_text_len

                        if is_ready:
                            stable_done_count += 1
                            if stable_done_count >= 4:  # 2.0s consecutive stable completion
                                break
                        else:
                            stable_done_count = 0

                    t_response_complete = time.time() - start_time
                    print(f"Response completed at t={t_response_complete:.1f}s")

                    action_entry = {
                        "scene_id": scene_id,
                        "scene_type": scene_type,
                        "title": title,
                        "prompt_text": prompt_text,
                        "t_type_start": round(t_type_start, 2),
                        "t_type_end": round(t_type_end, 2),
                        "t_submit": round(t_submit, 2),
                        "t_wait_start": round(t_wait_start, 2),
                        "t_response_start": round(t_response_start, 2),
                        "t_response_complete": round(t_response_complete, 2),
                        "focus_rect": {"x": 360, "y": 160, "width": 1120, "height": 730}
                    }

                    # Check if an analysis proposal card with execution button was rendered
                    # (e.g. "Run this analysis now", "Run this analysis inline", "今すぐこの分析を実行")
                    analysis_btn_data = await page.evaluate("""
                    () => {
                        function findDeep(matcher, root) {
                            root = root || document.body;
                            if (!root) return null;
                            if (matcher(root)) return root;
                            if (root.shadowRoot) {
                                for (const c of root.shadowRoot.children || []) {
                                    const res = findDeep(matcher, c);
                                    if (res) return res;
                                }
                            }
                            for (const c of root.children || []) {
                                const res = findDeep(matcher, c);
                                if (res) return res;
                            }
                            return null;
                        }
                        const btn = findDeep(el => {
                            if (el.tagName !== 'BUTTON' && el.tagName !== 'MD-FILLED-BUTTON' && el.tagName !== 'MD-OUTLINED-BUTTON') return false;
                            const text = (el.innerText || '').trim();
                            return /Run this analysis (now|inline)|Run analysis|今すぐ(この)?分析を実行|この分析を実行/i.test(text);
                        });
                        if (btn) {
                            const rect = btn.getBoundingClientRect();
                            return {
                                text: btn.innerText.trim(),
                                x: rect.x + rect.width / 2,
                                y: rect.y + rect.height / 2
                            };
                        }
                        return null;
                    }
                    """)

                    if analysis_btn_data:
                        print(f"Detected analysis execution button: '{analysis_btn_data['text']}'. Clicking immediately to execute analysis...")
                        btn_x = analysis_btn_data["x"]
                        btn_y = analysis_btn_data["y"]
                        await click_target(page, btn_x, btn_y)
                        t_click = time.time() - start_time
                        action_entry["action_click"] = {
                            "t_click": round(t_click, 2),
                            "button_label": analysis_btn_data["text"],
                            "x": round(btn_x, 1),
                            "y": round(btn_y, 1)
                        }
                        # Click the button element
                        await page.evaluate("""
                        () => {
                            function findDeep(matcher, root) {
                                root = root || document.body;
                                if (!root) return null;
                                if (matcher(root)) return root;
                                if (root.shadowRoot) {
                                    for (const c of root.shadowRoot.children || []) {
                                        const res = findDeep(matcher, c);
                                        if (res) return res;
                                    }
                                }
                                for (const c of root.children || []) {
                                    const res = findDeep(matcher, c);
                                    if (res) return res;
                                }
                                return null;
                            }
                            const btn = findDeep(el => {
                                if (el.tagName !== 'BUTTON' && el.tagName !== 'MD-FILLED-BUTTON' && el.tagName !== 'MD-OUTLINED-BUTTON') return false;
                                const text = (el.innerText || '').trim();
                                return /Run this analysis (now|inline)|Run analysis|今すぐ(この)?分析を実行|この分析を実行/i.test(text);
                            });
                            if (btn) btn.click();
                        }
                        """)

                        # Wait for the actual analysis execution response stream
                        print("Waiting for actual analysis response stream to begin...")
                        await asyncio.sleep(1.0)
                        prev_rating_count = await page.locator("button[aria-label*='良い回答'], button[aria-label*='Good response'], button[aria-label*='回答を評価'], button[aria-label*='コピー'], button[aria-label*='Copy']").count()
                        t_analysis_start = time.time() - start_time
                        stable_done_count = 0
                        last_text_len = 0
                        for _ in range(480):
                            await asyncio.sleep(0.5)
                            stop_btn = await page.query_selector("button[aria-label*='停止'], button[aria-label*='Stop']")
                            if stop_btn and await stop_btn.is_visible():
                                stable_done_count = 0
                                continue

                            cur_rating_count = await page.locator("button[aria-label*='良い回答'], button[aria-label*='Good response'], button[aria-label*='回答を評価'], button[aria-label*='コピー'], button[aria-label*='Copy']").count()

                            curr_text_len = await page.evaluate("""
                            () => {
                                function findDeepAll(matcher, root) {
                                    root = root || document.body;
                                    let res = [];
                                    if (!root) return res;
                                    if (matcher(root)) res.push(root);
                                    if (root.shadowRoot) {
                                        for (const c of root.shadowRoot.children || []) {
                                            res = res.concat(findDeepAll(matcher, c));
                                        }
                                    }
                                    for (const c of root.children || []) {
                                        res = res.concat(findDeepAll(matcher, c));
                                    }
                                    return res;
                                }
                                const turns = findDeepAll(el => el.tagName === "UCS-SUMMARY" || (el.className && typeof el.className === "string" && el.className.includes("message-item")));
                                if (turns.length === 0) return 0;
                                return (turns[turns.length - 1].innerText || "").length;
                            }
                            """)

                            is_ready = False
                            if cur_rating_count > prev_rating_count:
                                is_ready = True
                            elif curr_text_len > 20 and curr_text_len == last_text_len and (time.time() - start_time - t_analysis_start) > 6.0:
                                is_ready = True

                            last_text_len = curr_text_len

                            if is_ready:
                                stable_done_count += 1
                                if stable_done_count >= 4:
                                    break
                            else:
                                stable_done_count = 0

                        t_response_complete = time.time() - start_time
                        action_entry["t_response_complete"] = round(t_response_complete, 2)
                        print(f"Analysis execution response completed at t={t_response_complete:.1f}s")

                    # Dwell on the completed response for the narration duration + natural buffer
                    audio_dur = scene_durations.get(scene_id, 18.0)
                    min_dwell = max(18.0, audio_dur + 3.0)

                    # Smoothly scroll response if tall so full response is visible in video
                    print(f"Dwelling for {min_dwell:.1f}s to record completed response...")
                    await smooth_scroll_response_if_needed(page, min_dwell)

                    # If workflow action, click interactive execution button during dwell (if not already clicked)
                    if scene_type == "workflow_action" and "action_click" not in action_entry:
                        print("Locating visible action execution button...")
                        await asyncio.sleep(1.0)
                        action_btns = page.locator("button:has-text('承認'), button:has-text('実行'), button:has-text('Approve'), button:has-text('Execute'), button:has-text('Run')")
                        btn_count = await action_btns.count()
                        target_btn = None
                        for b_idx in range(btn_count):
                            candidate = action_btns.nth(b_idx)
                            if await candidate.is_visible():
                                box = await candidate.bounding_box()
                                if box and 100 <= box["y"] <= 950 and box["x"] >= 200:
                                    target_btn = candidate
                                    break

                        if target_btn:
                            box = await target_btn.bounding_box()
                            if box:
                                t_click = time.time() - start_time
                                target_x = box["x"] + box["width"] / 2.0
                                target_y = box["y"] + box["height"] / 2.0
                                await click_target(page, target_x, target_y)
                                try:
                                    await target_btn.click()
                                except Exception:
                                    pass
                                action_entry["action_click"] = {
                                    "t_click": round(t_click, 2),
                                    "button_label": (await target_btn.inner_text()).strip(),
                                    "x": round(target_x, 1),
                                    "y": round(target_y, 1),
                                }
                                print(f"Clicked action button at t={t_click:.1f}s, pos=({target_x:.1f}, {target_y:.1f})")
                                await asyncio.sleep(2.0)

                    recorded_actions.append(action_entry)
                    await asyncio.sleep(1.0)

            total_duration = time.time() - start_time

        finally:
            # Stop screencast and flush encoder
            try:
                await cdp_session.send("Page.stopScreencast")
            except Exception:
                pass

            stop_screencast.set()
            if writer_task:
                await writer_task

            if ffmpeg_proc.stdin:
                try:
                    ffmpeg_proc.stdin.close()
                    await ffmpeg_proc.stdin.wait_closed()
                except Exception:
                    pass
            await ffmpeg_proc.wait()

    manifest_data = {
        "session_url": args.session_url or "",
        "viewport": DEFAULT_VIEWPORT,
        "total_duration_sec": round(total_duration, 2),
        "raw_video_path": video_path,
        "actions": recorded_actions
    }

    with open(actions_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Recording completed! Telemetry saved to {actions_manifest_path}")
    print(f"🎬 Raw video recorded: {video_path}")
    return manifest_data


def main():
    parser = argparse.ArgumentParser(description="Record Gemini Enterprise demo session via CDP.")
    parser.add_argument("--cdp-url", default=DEFAULT_CDP_URL, help="Chrome CDP URL (default: http://localhost:9222)")
    parser.add_argument("--session-url", default="", help="Direct Gemini Enterprise chat session URL")
    parser.add_argument("--outdir", default="./output/recording", help="Directory for output files")
    parser.add_argument("--mock", action="store_true", help="Generate simulated actions and mock video (no Chrome required)")
    parser.add_argument("--prompts", nargs="+", help="Custom prompts to execute")
    parser.add_argument("--lang", default="", help="Language code (e.g. ja-JP, en-US)")
    parser.add_argument("--narration", default="", help="Path to narration_manifest.json")
    parser.add_argument("--auto-launch", action="store_true", default=True, help="Automatically launch Chrome if CDP port is not listening (default: True)")
    parser.add_argument("--no-auto-launch", action="store_false", dest="auto_launch", help="Disable automatic Chrome launching")
    parser.add_argument("--headless", action="store_true", default=True, help="Launch Chrome in headless mode (default: True)")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Launch Chrome with graphical UI")
    parser.add_argument("--fallback-mock", action="store_true", default=False, help="Fall back to synthetic mock recording on connection or auth failure (default: False)")
    parser.add_argument("--no-fallback-mock", action="store_false", dest="fallback_mock", help="Disable fallback mock recording")
    args = parser.parse_args()

    asyncio.run(record_session(args))


if __name__ == "__main__":
    main()
