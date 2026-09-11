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

"""Multi-language font verification and automated provisioning utility.

Validates that system fonts required for rendering non-Latin and international
typography (such as Japanese CJK, Chinese, Korean, Arabic, Thai, Devanagari) are
installed on the host environment. If missing, automatically installs them via
system package manager (apt) or downloads Noto font assets directly into the user's
font directory (~/.local/share/fonts/) to eliminate tofu ('□') glyph rendering.
"""

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request

# Mapping from language code prefixes to font requirements
LANGUAGE_FONT_CONFIGS = {
    "ja": {
        "description": "Japanese (Kanji, Hiragana, Katakana)",
        "fc_lang": "ja",
        "apt_packages": ["fonts-noto-cjk", "fonts-noto-core"],
        "fallback_font_urls": [
            "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf",
            "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf",
        ],
        "target_filename": "NotoSansCJKjp-Regular.otf"
    },
    "zh": {
        "description": "Chinese (Simplified and Traditional)",
        "fc_lang": "zh",
        "apt_packages": ["fonts-noto-cjk", "fonts-noto-core"],
        "fallback_font_urls": [
            "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf",
        ],
        "target_filename": "NotoSansCJKsc-Regular.otf"
    },
    "ko": {
        "description": "Korean (Hangul)",
        "fc_lang": "ko",
        "apt_packages": ["fonts-noto-cjk", "fonts-noto-core"],
        "fallback_font_urls": [
            "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf",
        ],
        "target_filename": "NotoSansCJKkr-Regular.otf"
    },
    "ar": {
        "description": "Arabic",
        "fc_lang": "ar",
        "apt_packages": ["fonts-noto-core"],
        "fallback_font_urls": [
            "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf",
        ],
        "target_filename": "NotoSansArabic-Regular.ttf"
    },
    "th": {
        "description": "Thai",
        "fc_lang": "th",
        "apt_packages": ["fonts-noto-core"],
        "fallback_font_urls": [
            "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansThai/NotoSansThai-Regular.ttf",
        ],
        "target_filename": "NotoSansThai-Regular.ttf"
    },
    "hi": {
        "description": "Hindi / Devanagari",
        "fc_lang": "hi",
        "apt_packages": ["fonts-noto-core"],
        "fallback_font_urls": [
            "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf",
        ],
        "target_filename": "NotoSansDevanagari-Regular.ttf"
    }
}


def normalize_lang_code(lang: str) -> str:
    """Extracts base 2-letter language code from locale strings like 'ja-JP' or 'zh_CN'."""
    cleaned = (lang or "en-US").strip().lower().replace("_", "-")
    return cleaned.split("-")[0]


def check_font_installed(fc_lang: str) -> bool:
    """Queries fontconfig via fc-list to verify if fonts for the language exist."""
    fc_list_bin = shutil.which("fc-list")
    if not fc_list_bin:
        return False

    try:
        res = subprocess.run(
            [fc_list_bin, f":lang={fc_lang}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode == 0 and res.stdout.strip():
            font_lines = [line for line in res.stdout.strip().splitlines() if line.strip()]
            return len(font_lines) > 0
    except Exception as e:
        print(f"⚠️ [Font Check] fc-list check failed: {e}", file=sys.stderr)

    return False


def install_fonts_via_apt(packages: list[str]) -> bool:
    """Attempts to install missing font packages using apt-get if permissions allow."""
    apt_bin = shutil.which("apt-get")
    if not apt_bin:
        return False

    is_root = (os.geteuid() == 0)
    can_sudo = False

    if not is_root and shutil.which("sudo"):
        try:
            res = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=5)
            can_sudo = (res.returncode == 0)
        except Exception:
            can_sudo = False

    if not is_root and not can_sudo:
        return False

    prefix = [] if is_root else ["sudo", "-n"]
    print(f"📦 [Font Provisioning] Attempting system installation of {packages} via apt-get...")
    try:
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        subprocess.run(
            prefix + ["apt-get", "update", "-qq"],
            env=env,
            capture_output=True,
            timeout=60
        )
        install_cmd = prefix + ["apt-get", "install", "-y", "-qq", "--no-install-recommends"] + packages
        res = subprocess.run(install_cmd, env=env, capture_output=True, text=True, timeout=180)
        if res.returncode == 0:
            print("✅ [Font Provisioning] Successfully installed font packages via apt-get.")
            return True
        else:
            print(f"⚠️ [Font Provisioning] apt-get install exited with code {res.returncode}: {res.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ [Font Provisioning] apt-get execution failed: {e}", file=sys.stderr)

    return False


def install_fonts_user_space(font_urls: list[str]) -> bool:
    """Downloads font files directly into user's ~/.local/share/fonts/ and updates font cache."""
    user_font_dir = os.path.expanduser("~/.local/share/fonts")
    os.makedirs(user_font_dir, exist_ok=True)

    downloaded_any = False
    for url in font_urls:
        fname = url.split("/")[-1]
        dest_path = os.path.join(user_font_dir, fname)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
            downloaded_any = True
            continue

        print(f"⬇️ [Font Provisioning] Downloading font asset {fname} to {user_font_dir}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (FontProvisioner)"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as out_f:
                shutil.copyfileobj(resp, out_f)
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
                print(f"  ✅ Downloaded {fname} ({os.path.getsize(dest_path)} bytes)")
                downloaded_any = True
        except Exception as e:
            print(f"⚠️ [Font Provisioning] Failed to download {url}: {e}", file=sys.stderr)

    if downloaded_any:
        fc_cache_bin = shutil.which("fc-cache")
        if fc_cache_bin:
            try:
                print(f"🔄 [Font Provisioning] Refreshing font cache via fc-cache in {user_font_dir}...")
                subprocess.run([fc_cache_bin, "-fv", user_font_dir], capture_output=True, timeout=30)
            except Exception as e:
                print(f"⚠️ [Font Provisioning] fc-cache invocation failed: {e}", file=sys.stderr)
        return True

    return False


def ensure_fonts_for_language(lang: str) -> bool:
    """Ensures that required typography fonts for the specified language are available."""
    lang_prefix = normalize_lang_code(lang)
    config = LANGUAGE_FONT_CONFIGS.get(lang_prefix)

    # Standard Latin languages (en, de, fr, es, it, pt, etc.) have broad base font coverage
    if not config:
        print(f"ℹ️ [Font Check] Locale '{lang}' uses standard Latin/base typography. Verifying base font availability...")
        if check_font_installed("en"):
            print("✅ [Font Check] Base system typography verified.")
            return True
        # If even base Latin is missing, install noto-core
        packages = ["fonts-noto-core"]
        return install_fonts_via_apt(packages) or True

    print(f"🔍 [Font Check] Verifying typography for {config['description']} (locale: '{lang}')...")
    fc_lang = config["fc_lang"]

    if check_font_installed(fc_lang):
        print(f"✅ [Font Check] Fonts for {config['description']} are already installed and verified.")
        return True

    print(f"⚠️ [Font Check] Required fonts for {config['description']} not found. Initiating automated provisioning...")

    # Attempt 1: System-wide install via apt-get
    if install_fonts_via_apt(config["apt_packages"]):
        if check_font_installed(fc_lang):
            print(f"✅ [Font Check] Typography for {config['description']} successfully verified after apt install.")
            return True

    # Attempt 2: User-space direct font asset download
    fallback_urls = config.get("fallback_font_urls", [])
    if fallback_urls and install_fonts_user_space(fallback_urls):
        if check_font_installed(fc_lang):
            print(f"✅ [Font Check] Typography for {config['description']} successfully verified after user-space install.")
            return True

    print(f"⚠️ [Font Check] Automated font installation could not be fully verified for '{lang}'.", file=sys.stderr)
    print("   Subtitles and Remotion composition will use Google Web Fonts fallback.", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser(description="Ensure typography fonts for target locale.")
    parser.add_argument("--lang", default="en-US", help="Language code (e.g. ja-JP, en-US, zh-CN, ko-KR, ar, th)")
    args = parser.parse_args()

    success = ensure_fonts_for_language(args.lang)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
