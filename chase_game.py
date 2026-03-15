import os
import sys
import json
import random
import math
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

import pygame

# --- Paths & storage helpers ---
def _is_frozen():
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _resource_path(relative_path):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative_path


def _data_dir():
    if _is_frozen():
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if base:
            root = Path(base)
        else:
            root = Path.home() / "AppData" / "Local"
        data_path = root / "KittyChase"
    else:
        data_path = Path(__file__).resolve().parent
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


# --- Account save/load helpers ---
ACCOUNTS_FILE = _data_dir() / "accounts.json"
UNLOCKED_LEVELS_FILE = _data_dir() / "unlocked_levels.json"


def load_accounts():
    try:
        with open(ACCOUNTS_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Ensure Don is always available
            if "don" not in data:
                data["don"] = {"level": 1, "password": None}
                save_accounts(data)
            # Upgrade old format if needed
            for name, value in list(data.items()):
                if isinstance(value, int):
                    data[name] = {"level": value, "password": None}
                    save_accounts(data)
            return data
    except Exception:
        pass
    # Default
    return {"don": {"level": 1, "password": None}}


def save_accounts(accounts):
    try:
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(accounts, f)
    except Exception:
        pass


# Game settings
APP_NAME = "Kitty Chase"
APP_VERSION = "1.0.3"
GITHUB_OWNER = "david-m15"
GITHUB_REPO = "kitty-chase"
WINDOWS_INSTALLER_ASSET_NAME = "KittyChase-Setup.exe"
MAC_INSTALLER_ASSET_NAME = "KittyChase-macOS.dmg"


def _installer_asset_name():
    if sys.platform == "darwin":
        return MAC_INSTALLER_ASSET_NAME
    if sys.platform.startswith("win"):
        return WINDOWS_INSTALLER_ASSET_NAME
    return ""

WIDTH, HEIGHT = 800, 600
PLAYER_RADIUS = 20
RED_RADIUS = 20
BLUE_RADIUS = 10
SPEED = 5
RED_SPEED = 2
BG_COLOR = (255, 140, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def _lerp(a, b, t):
    return int(a + (b - a) * t)

def _vertical_gradient(surface, top_color, bottom_color):
    """Fill a surface with a simple vertical gradient."""
    height = surface.get_height()
    width = surface.get_width()
    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            _lerp(top_color[0], bottom_color[0], t),
            _lerp(top_color[1], bottom_color[1], t),
            _lerp(top_color[2], bottom_color[2], t),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))

def build_liquid_glass_background():
    """Pre-render a soft 'liquid glass' background in the Apple-style glassmorphism vibe."""
    bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    _vertical_gradient(bg, (246, 250, 255), (205, 220, 235))

    # Large soft specular highlight
    shine = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(
        shine,
        (255, 255, 255, 82),
        pygame.Rect(-WIDTH * 0.15, -HEIGHT * 0.55, WIDTH * 1.3, HEIGHT * 1.1),
    )
    bg.blit(shine, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # Subtle frosted overlay
    frost = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    frost.fill((255, 255, 255, 18))
    bg.blit(frost, (0, 0))

    return bg.convert_alpha()

def draw_glassy_button(screen, rect, base_color, border_radius=15):
    # Soft shadow for lift
    shadow_rect = rect.move(4, 6)
    shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 55), shadow.get_rect(), border_radius=border_radius)
    screen.blit(shadow, shadow_rect.topleft)

    # Solid button body (no white highlight)
    btn = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(btn, base_color, btn.get_rect(), border_radius=border_radius)

    # Subtle darker border for definition without whitening
    border_color = (max(0, base_color[0] - 40), max(0, base_color[1] - 40), max(0, base_color[2] - 40))
    pygame.draw.rect(btn, border_color, btn.get_rect(), width=2, border_radius=border_radius)

    screen.blit(btn, rect.topleft)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
LIQUID_BG = build_liquid_glass_background()

def fill_background():
    # Use the pre-rendered glass background everywhere instead of a flat fill
    screen.blit(LIQUID_BG, (0, 0))
# Load tiger image (place 'tiger.png' and 'tiger.ico' in the same folder as this script)
try:
    tiger_img = pygame.image.load(_resource_path("tiger.png"))
    tiger_img = pygame.transform.smoothscale(tiger_img, (160, 120))
except Exception:
    tiger_img = None  # If image not found, skip drawing

# Set window icon to tiger
try:
    icon_img = pygame.image.load(_resource_path("tiger.png"))
    pygame.display.set_icon(icon_img)
except Exception:
    pass

pygame.display.set_caption(APP_NAME)
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 32)
clock = pygame.time.Clock()


def draw_text(text, font, color, surface, x, y):
    # Soft shadow to keep text legible on bright glass backgrounds
    shadow = font.render(text, True, (0, 0, 0))
    shadow.set_alpha(80)
    shadow_rect = shadow.get_rect(center=(x + 2, y + 2))
    surface.blit(shadow, shadow_rect)

    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)


def _version_tuple(value):
    if not value:
        return tuple()
    text = value.strip()
    if text.startswith(("v", "V")):
        text = text[1:]
    parts = re.split(r"[.\-+]", text)
    out = []
    for part in parts:
        if part.isdigit():
            out.append(int(part))
            continue
        num = ""
        for ch in part:
            if ch.isdigit():
                num += ch
            else:
                break
        if num:
            out.append(int(num))
    return tuple(out)


def _is_update_configured():
    return (
        GITHUB_OWNER not in {"REPLACE_ME", "", None}
        and GITHUB_REPO not in {"REPLACE_ME", "", None}
    )


def _fetch_latest_release():
    if not _is_update_configured():
        return None, None
    asset_name = _installer_asset_name()
    if not asset_name:
        return None, None
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME} updater"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    tag = data.get("tag_name") or ""
    asset_url = None
    for asset in data.get("assets", []):
        if asset.get("name") == asset_name:
            asset_url = asset.get("browser_download_url")
            break
    return tag, asset_url


def _show_update_prompt(latest_version):
    yes_button = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 40, 120, 55)
    no_button = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 40, 120, 55)
    while True:
        fill_background()
        draw_text("Update Available", font, BLACK, screen, WIDTH // 2, HEIGHT // 2 - 60)
        draw_text(
            f"Version {latest_version}",
            small_font,
            BLACK,
            screen,
            WIDTH // 2,
            HEIGHT // 2 - 20,
        )
        draw_glassy_button(screen, yes_button, BLUE, 18)
        draw_text("Update", small_font, WHITE, screen, yes_button.centerx, yes_button.centery)
        draw_glassy_button(screen, no_button, (120, 120, 120), 18)
        draw_text("Later", small_font, WHITE, screen, no_button.centerx, no_button.centery)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if yes_button.collidepoint(event.pos):
                    return True
                if no_button.collidepoint(event.pos):
                    return False
        pygame.display.flip()
        clock.tick(30)


def _show_update_status(message):
    fill_background()
    draw_text(message, font, BLACK, screen, WIDTH // 2, HEIGHT // 2)
    pygame.display.flip()


def _launch_installer(installer_path):
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(installer_path)])
        return
    subprocess.Popen([str(installer_path)])


def check_for_updates():
    if not _is_frozen():
        return
    try:
        installer_name = _installer_asset_name()
        if not installer_name:
            return
        latest_tag, asset_url = _fetch_latest_release()
        if not latest_tag or not asset_url:
            return
        if _version_tuple(latest_tag) <= _version_tuple(APP_VERSION):
            return
        if not _show_update_prompt(latest_tag):
            return
        _show_update_status("Downloading update...")
        installer_path = Path(tempfile.gettempdir()) / installer_name
        req = urllib.request.Request(asset_url, headers={"User-Agent": f"{APP_NAME} updater"})
        with urllib.request.urlopen(req, timeout=30) as resp, open(installer_path, "wb") as f:
            shutil.copyfileobj(resp, f)
        _show_update_status("Launching installer...")
        pygame.quit()
        _launch_installer(installer_path)
        sys.exit()
    except Exception:
        return


# New: Title screen before name entry
def show_title_screen():
    play_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 60)
    while True:
        fill_background()
        draw_text(APP_NAME, font, BLACK, screen, WIDTH // 2, HEIGHT // 2 - 60)
        # Draw tiger image below the title if available
        if tiger_img:
            tiger_rect = tiger_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
            screen.blit(tiger_img, tiger_rect)
        draw_glassy_button(screen, play_button, BLUE, 20)
        draw_text("PLAY", font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 70)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    return
        pygame.display.flip()
        clock.tick(30)


def get_player_name():
    # Account selection screen
    player_name = None
    accounts = load_accounts()
    account_buttons = []
    for idx, acc_name in enumerate(accounts.keys()):
        rect = pygame.Rect(WIDTH // 2 - 330 + idx * 120, HEIGHT // 2 - 30, 110, 50)
        account_buttons.append((rect, acc_name))
    david_button = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 + 60, 100, 50)
    other_button = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 + 130, 100, 50)
    guest_confirm = False
    david_password_prompt = False
    david_password = ""
    david_error = ""
    david_input_focused = False
    easy_hard_mode = None  # None, 'easy', or 'hard'
    selected_account = None
    mode_selection = False
    custom_password_prompt = False
    custom_password = ""
    custom_error = ""
    custom_input_focused = False
    selected_custom = None
    while True:
        # Easy/Hard selection for non-David/Kate users
        if easy_hard_mode is not None:
            return player_name, easy_hard_mode
        if custom_password_prompt:
            # Password entry screen for custom account
            input_box = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 60)
            fill_background()
            draw_text(
                f"Enter password for {selected_custom.title()}:",
                font,
                BLACK,
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 60,
            )
            # Highlight input box if focused
            if custom_input_focused:
                pygame.draw.rect(screen, (0, 200, 255), input_box, 4)
            else:
                pygame.draw.rect(screen, WHITE, input_box, 2)
            draw_text(custom_password, font, BLACK, screen, WIDTH // 2, HEIGHT // 2 + 70)
            if custom_error:
                draw_text(
                    custom_error, small_font, RED, screen, WIDTH // 2, HEIGHT // 2 + 120
                )
            cancel_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 40)
            pygame.draw.rect(screen, (120, 120, 120), cancel_button, border_radius=15)
            draw_text(
                "Cancel",
                small_font,
                WHITE,
                screen,
                cancel_button.centerx,
                cancel_button.centery,
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if cancel_button.collidepoint(event.pos):
                        custom_password_prompt = False
                        custom_password = ""
                        custom_error = ""
                        custom_input_focused = False
                        selected_custom = None
                        break
                    elif input_box.collidepoint(event.pos):
                        custom_input_focused = True
                    else:
                        # Click outside input box or cancel closes dialog
                        custom_password_prompt = False
                        custom_input_focused = False
                        break
                if custom_input_focused and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if custom_password == accounts[selected_custom].get("password"):
                            return selected_custom, None
                        else:
                            custom_error = "Incorrect password!"
                            custom_password = ""
                    elif event.key == pygame.K_BACKSPACE:
                        custom_password = custom_password[:-1]
                    else:
                        if len(custom_password) < 16 and event.unicode.isprintable():
                            custom_password += event.unicode
            pygame.display.flip()
            clock.tick(30)
            continue
        if mode_selection:
            # Mode selection screen
            fill_background()
            draw_text(
                "Select Mode",
                font,
                BLACK,
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 60,
            )
            easy_button = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 + 20, 120, 50)
            hard_button = pygame.Rect(WIDTH // 2 + 40, HEIGHT // 2 + 20, 120, 50)
            back_button = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 + 100, 100, 50)
            draw_glassy_button(screen, easy_button, (0, 200, 0), 15)
            draw_glassy_button(screen, hard_button, (200, 0, 0), 15)
            draw_glassy_button(screen, back_button, (120, 120, 120), 15)
            draw_text(
                "Easy",
                small_font,
                WHITE,
                screen,
                easy_button.centerx,
                easy_button.centery,
            )
            draw_text(
                "Hard",
                small_font,
                WHITE,
                screen,
                hard_button.centerx,
                hard_button.centery,
            )
            draw_text(
                "Back",
                small_font,
                WHITE,
                screen,
                back_button.centerx,
                back_button.centery,
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if easy_button.collidepoint(event.pos):
                        return selected_account, "easy"
                    elif hard_button.collidepoint(event.pos):
                        return selected_account, "hard"
                    elif back_button.collidepoint(event.pos):
                        mode_selection = False
                        selected_account = None
                        break
            pygame.display.flip()
            clock.tick(30)
            continue
        if david_password_prompt:
            # Password entry screen for David
            input_box = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 60)
            fill_background()
            draw_text(
                "Enter password for David:",
                font,
                BLACK,
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 60,
            )
            # Highlight input box if focused
            if david_input_focused:
                pygame.draw.rect(screen, (0, 200, 255), input_box, 4)
            else:
                pygame.draw.rect(screen, WHITE, input_box, 2)
            draw_text(david_password, font, BLACK, screen, WIDTH // 2, HEIGHT // 2 + 70)
            if david_error:
                draw_text(
                    david_error, small_font, RED, screen, WIDTH // 2, HEIGHT // 2 + 120
                )
            cancel_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 40)
            pygame.draw.rect(screen, (120, 120, 120), cancel_button, border_radius=15)
            draw_text(
                "Cancel",
                small_font,
                WHITE,
                screen,
                cancel_button.centerx,
                cancel_button.centery,
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if cancel_button.collidepoint(event.pos):
                        david_password_prompt = False
                        david_password = ""
                        david_error = ""
                        david_input_focused = False
                        break
                    elif input_box.collidepoint(event.pos):
                        david_input_focused = True
                    else:
                        # Click outside input box or cancel closes dialog
                        david_password_prompt = False
                        david_input_focused = False
                        break
                if david_input_focused and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if david_password == "1538354159":
                            return "david"
                        else:
                            david_error = "Incorrect password!"
                            david_password = ""
                    elif event.key == pygame.K_BACKSPACE:
                        david_password = david_password[:-1]
                    else:
                        if len(david_password) < 16 and event.unicode.isprintable():
                            david_password += event.unicode
            pygame.display.flip()
            clock.tick(30)
            continue
        if not guest_confirm:
            fill_background()
            draw_text(
                "Choose your account:",
                font,
                BLACK,
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 100,
            )
            # Draw account buttons
            for rect, acc_name in account_buttons:
                draw_glassy_button(screen, rect, (100, 100, 255), 15)
                # display names with capitalization for readability
                draw_text(
                    acc_name.title(), small_font, WHITE, screen, rect.centerx, rect.centery
                )
            # Draw David button
            draw_glassy_button(screen, david_button, RED, 15)
            draw_text(
                "David",
                small_font,
                WHITE,
                screen,
                david_button.centerx,
                david_button.centery,
            )
            # Draw Other button
            draw_glassy_button(screen, other_button, BLACK, 15)
            draw_text(
                "Other",
                small_font,
                WHITE,
                screen,
                other_button.centerx,
                other_button.centery,
            )
            draw_text(
                "Or select Other to play as guest",
                small_font,
                BLACK,
                screen,
                WIDTH // 2,
                HEIGHT // 2 + 200,
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Account button click
                    for rect, acc_name in account_buttons:
                        if rect.collidepoint(event.pos):
                            if accounts[acc_name].get("password"):
                                selected_custom = acc_name
                                custom_password_prompt = True
                                custom_password = ""
                                custom_error = ""
                                custom_input_focused = False
                                break
                            else:
                                player_name = acc_name
                                # If not David/guest, go to mode selection
                                if player_name not in ["david", "guest"]:
                                    selected_account = acc_name
                                    mode_selection = True
                                    break
                                return player_name, None
                    if david_button.collidepoint(event.pos):
                        david_password_prompt = True
                        david_password = ""
                        david_error = ""
                        david_input_focused = False
                        break
                    elif other_button.collidepoint(event.pos):
                        guest_confirm = True
                        break
            pygame.display.flip()
            clock.tick(30)
        else:
            # Guest confirmation screen with back button
            guest_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 60)
            back_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50)
            fill_background()
            draw_text(
                "Play as Guest?", font, BLACK, screen, WIDTH // 2, HEIGHT // 2 - 60
            )
            draw_text(
                "Progress will only be saved if you save your progress.",
                small_font,
                RED,
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 10,
            )
            draw_glassy_button(screen, guest_button, BLUE, 20)
            draw_text(
                "Continue as Guest",
                small_font,
                WHITE,
                screen,
                guest_button.centerx,
                guest_button.centery,
            )
            draw_glassy_button(screen, back_button, (120, 120, 120), 15)
            draw_text(
                "Back",
                small_font,
                WHITE,
                screen,
                back_button.centerx,
                back_button.centery,
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if guest_button.collidepoint(event.pos):
                        return "guest"
                    if back_button.collidepoint(event.pos):
                        guest_confirm = False
                        break
            pygame.display.flip()
            clock.tick(30)


# Level select screen (must be defined before wait_for_start_and_choose_level)
def choose_level_screen(unlocked_levels, versus_mode=False, page=0, player_name=None):
    levels_per_page = 10
    while True:
        start_level = page * levels_per_page + 1
        end_level = start_level + levels_per_page - 1
        fill_background()
        if versus_mode:
            draw_text(
                "Versus Mode: Select Level",
                font,
                (255, 100, 0),
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 200,
            )
        else:
            draw_text(
                "Select Level", font, BLACK, screen, WIDTH // 2, HEIGHT // 2 - 150
            )
        level_buttons = []
        for i in range(levels_per_page):
            level_num = start_level + i
            row = i // 5
            col = i % 5
            rect = pygame.Rect(
                WIDTH // 2 - 275 + col * 110, HEIGHT // 2 - 60 + row * 100, 100, 80
            )
            unlocked = level_num <= unlocked_levels
            color = (0, 200, 0) if unlocked else (120, 120, 120)
            if versus_mode:
                draw_glassy_button(
                    screen, rect, (255, 180, 80) if unlocked else (120, 120, 120), 15
                )
            else:
                draw_glassy_button(screen, rect, color, 15)
            draw_text(
                f"{level_num}",
                font,
                WHITE if unlocked else (200, 200, 200),
                screen,
                rect.centerx,
                rect.centery,
            )
            if not unlocked:
                draw_text(
                    "Locked",
                    small_font,
                    (200, 0, 0),
                    screen,
                    rect.centerx,
                    rect.centery + 30,
                )
            level_buttons.append((rect, level_num, unlocked))
        # Prev/Next buttons
        prev_rect = pygame.Rect(WIDTH // 2 - 275, HEIGHT // 2 + 150, 100, 50)
        next_rect = pygame.Rect(WIDTH // 2 + 175, HEIGHT // 2 + 150, 100, 50)
        pygame.draw.rect(screen, BLUE, prev_rect, border_radius=15)
        pygame.draw.rect(screen, BLUE, next_rect, border_radius=15)
        draw_text(
            "Prev", small_font, WHITE, screen, prev_rect.centerx, prev_rect.centery
        )
        draw_text(
            "Next", small_font, WHITE, screen, next_rect.centerx, next_rect.centery
        )
        # Go to Farthest button
        goto_rect = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 + 210, 100, 40)
        pygame.draw.rect(screen, (0, 150, 255), goto_rect, border_radius=15)
        draw_text(
            "Go to Farthest",
            small_font,
            WHITE,
            screen,
            goto_rect.centerx,
            goto_rect.centery,
        )
        # Change Sign Out button to Close
        close_rect = pygame.Rect(WIDTH - 160, 30, 130, 40)
        pygame.draw.rect(screen, (120, 120, 120), close_rect, border_radius=15)
        draw_text(
            "Close", small_font, WHITE, screen, close_rect.centerx, close_rect.centery
        )
        # Settings button
        settings_button = pygame.Rect(10, 10, 100, 40)
        pygame.draw.rect(screen, (100, 100, 100), settings_button, border_radius=15)
        draw_text("Settings", small_font, WHITE, screen, settings_button.centerx, settings_button.centery)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Close button
                if close_rect.collidepoint(event.pos):
                    return None, None, "signout"
                for rect, level_num, unlocked in level_buttons:
                    if rect.collidepoint(event.pos) and unlocked:
                        return level_num, False, None
                if prev_rect.collidepoint(event.pos) and page > 0:
                    return choose_level_screen(unlocked_levels, False, page - 1, player_name)
                if next_rect.collidepoint(event.pos):
                    return choose_level_screen(unlocked_levels, False, page + 1, player_name)
                if goto_rect.collidepoint(event.pos):
                    farthest = unlocked_levels
                    new_page = (farthest - 1) // levels_per_page
                    return choose_level_screen(unlocked_levels, False, new_page, player_name)
                if settings_button.collidepoint(event.pos):
                    result = show_settings_screen(player_name)
                    if result == "delete":
                        return None, None, "delete_account"
        pygame.display.flip()
        clock.tick(30)


def show_settings_screen(player_name):
    set_password_prompt = False
    set_password = ""
    set_error = ""
    set_input_focused = False
    confirm_remove_password = False
    accounts_list = False
    confirm_delete_account = None
    confirm_remove_password_account = None
    selected_account = None
    set_level_prompt = False
    set_level_value = ""
    set_level_error = ""
    set_level_focused = False
    set_level_target = None

    def parse_level_input(value):
        if not value:
            return None, "Level cannot be empty!"
        if not value.isdigit():
            return None, "Enter a whole number!"
        level_int = int(value)
        if level_int < 1:
            return None, "Level must be 1 or higher!"
        return level_int, ""
    while True:
        fill_background()
        if set_password_prompt:
            # Set password input screen
            input_box = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 60)
            draw_text(
                f"Set password for {player_name.title()}:",
                font,
                BLACK,
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 60,
            )
            # Highlight input box if focused
            if set_input_focused:
                pygame.draw.rect(screen, (0, 200, 255), input_box, 4)
            else:
                pygame.draw.rect(screen, WHITE, input_box, 2)
            draw_text(set_password, font, BLACK, screen, WIDTH // 2, HEIGHT // 2 + 70)
            if set_error:
                draw_text(
                    set_error, small_font, RED, screen, WIDTH // 2, HEIGHT // 2 + 120
                )
            set_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 40)
            pygame.draw.rect(screen, BLUE, set_button, border_radius=15)
            draw_text(
                "Set Password",
                small_font,
                WHITE,
                screen,
                set_button.centerx,
                set_button.centery,
            )
            cancel_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 160, 200, 40)
            pygame.draw.rect(screen, (120, 120, 120), cancel_button, border_radius=15)
            draw_text(
                "Cancel",
                small_font,
                WHITE,
                screen,
                cancel_button.centerx,
                cancel_button.centery,
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if set_button.collidepoint(event.pos):
                        if set_password:
                            accounts = load_accounts()
                            accounts[player_name]["password"] = set_password
                            save_accounts(accounts)
                            return None  # Back to settings
                        else:
                            set_error = "Password cannot be empty!"
                    elif cancel_button.collidepoint(event.pos):
                        set_password_prompt = False
                        set_password = ""
                        set_error = ""
                        set_input_focused = False
                        break
                    elif input_box.collidepoint(event.pos):
                        set_input_focused = True
                    else:
                        set_input_focused = False
                if set_input_focused and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if set_password:
                            accounts = load_accounts()
                            accounts[player_name]["password"] = set_password
                            save_accounts(accounts)
                            return None
                        else:
                            set_error = "Password cannot be empty!"
                    elif event.key == pygame.K_BACKSPACE:
                        set_password = set_password[:-1]
                    else:
                        if len(set_password) < 16 and event.unicode.isprintable():
                            set_password += event.unicode
            pygame.display.flip()
            clock.tick(30)
            continue
        if set_level_prompt:
            input_box = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 60)
            draw_text(
                f"Set level for {set_level_target.title() if set_level_target else 'user'}:",
                font,
                BLACK,
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 60,
            )
            if set_level_focused:
                pygame.draw.rect(screen, (0, 200, 255), input_box, 4)
            else:
                pygame.draw.rect(screen, WHITE, input_box, 2)
            draw_text(
                set_level_value, font, BLACK, screen, WIDTH // 2, HEIGHT // 2 + 70
            )
            if set_level_error:
                draw_text(
                    set_level_error,
                    small_font,
                    RED,
                    screen,
                    WIDTH // 2,
                    HEIGHT // 2 + 120,
                )
            set_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 40)
            pygame.draw.rect(screen, BLUE, set_button, border_radius=15)
            draw_text(
                "Set Level",
                small_font,
                WHITE,
                screen,
                set_button.centerx,
                set_button.centery,
            )
            cancel_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 160, 200, 40)
            pygame.draw.rect(screen, (120, 120, 120), cancel_button, border_radius=15)
            draw_text(
                "Cancel",
                small_font,
                WHITE,
                screen,
                cancel_button.centerx,
                cancel_button.centery,
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if set_button.collidepoint(event.pos):
                        level_int, error = parse_level_input(set_level_value)
                        if error:
                            set_level_error = error
                        else:
                            accounts = load_accounts()
                            if set_level_target in accounts:
                                entry = accounts[set_level_target]
                                if isinstance(entry, dict):
                                    entry["level"] = level_int
                                else:
                                    entry = {"level": level_int, "password": None}
                                accounts[set_level_target] = entry
                                save_accounts(accounts)
                            set_level_prompt = False
                            set_level_target = None
                            set_level_value = ""
                            set_level_error = ""
                            set_level_focused = False
                            fill_background()
                            draw_text(
                                "Level updated!",
                                small_font,
                                (0, 150, 0),
                                screen,
                                WIDTH // 2,
                                HEIGHT // 2 + 120,
                            )
                            pygame.display.flip()
                            pygame.time.wait(600)
                    elif cancel_button.collidepoint(event.pos):
                        set_level_prompt = False
                        set_level_target = None
                        set_level_value = ""
                        set_level_error = ""
                        set_level_focused = False
                        break
                    elif input_box.collidepoint(event.pos):
                        set_level_focused = True
                    else:
                        set_level_focused = False
                if set_level_focused and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        level_int, error = parse_level_input(set_level_value)
                        if error:
                            set_level_error = error
                        else:
                            accounts = load_accounts()
                            if set_level_target in accounts:
                                entry = accounts[set_level_target]
                                if isinstance(entry, dict):
                                    entry["level"] = level_int
                                else:
                                    entry = {"level": level_int, "password": None}
                                accounts[set_level_target] = entry
                                save_accounts(accounts)
                            set_level_prompt = False
                            set_level_target = None
                            set_level_value = ""
                            set_level_error = ""
                            set_level_focused = False
                            fill_background()
                            draw_text(
                                "Level updated!",
                                small_font,
                                (0, 150, 0),
                                screen,
                                WIDTH // 2,
                                HEIGHT // 2 + 120,
                            )
                            pygame.display.flip()
                            pygame.time.wait(600)
                    elif event.key == pygame.K_BACKSPACE:
                        set_level_value = set_level_value[:-1]
                    else:
                        if (
                            len(set_level_value) < 6
                            and event.unicode.isdigit()
                        ):
                            set_level_value += event.unicode
            pygame.display.flip()
            clock.tick(30)
            continue
        if confirm_remove_password:
            # Confirmation screen for removing password
            draw_text(
                "Are you sure you want to remove the password?",
                font,
                BLACK,
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 40,
            )
            remove_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 50)
            cancel_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50)
            pygame.draw.rect(screen, RED, remove_button, border_radius=15)
            draw_text("Remove Password", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 65)
            pygame.draw.rect(screen, (120, 120, 120), cancel_button, border_radius=15)
            draw_text("Cancel", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 145)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if remove_button.collidepoint(event.pos):
                        # Remove password
                        accounts = load_accounts()
                        accounts[player_name]["password"] = None
                        save_accounts(accounts)
                        confirm_remove_password = False
                    elif cancel_button.collidepoint(event.pos):
                        confirm_remove_password = False
            pygame.display.flip()
            clock.tick(30)
            continue
        if accounts_list:
            # Accounts list screen for David
            accounts = load_accounts()
            accounts_to_show = list(accounts.keys())
            if selected_account:
                # Show options for selected account
                draw_text(f"Options for {selected_account.title()}", font, BLACK, screen, WIDTH // 2, HEIGHT // 2 - 100)
                entry = accounts.get(selected_account, {})
                if isinstance(entry, dict):
                    has_password = entry.get("password") is not None
                    current_level = entry.get("level", 1)
                else:
                    has_password = False
                    current_level = entry if isinstance(entry, int) else 1
                draw_text(
                    f"Current level: {current_level}",
                    small_font,
                    BLACK,
                    screen,
                    WIDTH // 2,
                    HEIGHT // 2 - 60,
                )
                option_y = HEIGHT // 2 - 20
                remove_button = None
                if has_password:
                    remove_button = pygame.Rect(WIDTH // 2 - 100, option_y, 200, 50)
                    draw_glassy_button(screen, remove_button, (255, 165, 0), 15)
                    draw_text("Remove Password", small_font, WHITE, screen, WIDTH // 2, option_y + 25)
                    option_y += 60
                set_level_button = pygame.Rect(WIDTH // 2 - 100, option_y, 200, 50)
                draw_glassy_button(screen, set_level_button, (0, 120, 200), 15)
                draw_text("Set Level", small_font, WHITE, screen, WIDTH // 2, option_y + 25)
                option_y += 60
                delete_button = pygame.Rect(WIDTH // 2 - 100, option_y, 200, 50)
                draw_glassy_button(screen, delete_button, RED, 15)
                draw_text("Delete Account", small_font, WHITE, screen, WIDTH // 2, option_y + 25)
                option_y += 60
                back_button = pygame.Rect(WIDTH // 2 - 100, option_y, 200, 50)
                draw_glassy_button(screen, back_button, (120, 120, 120), 15)
                draw_text("Back", small_font, WHITE, screen, WIDTH // 2, option_y + 25)
                if player_name == "david" and has_password:
                    draw_text(
                        f"Password: {accounts[selected_account]['password']}",
                        small_font,
                        BLACK,
                        screen,
                        WIDTH // 2,
                        option_y + 55,
                    )
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if has_password and remove_button.collidepoint(event.pos):
                            confirm_remove_password_account = selected_account
                        elif set_level_button.collidepoint(event.pos):
                            set_level_prompt = True
                            set_level_target = selected_account
                            set_level_value = ""
                            set_level_error = ""
                            set_level_focused = False
                        elif delete_button.collidepoint(event.pos):
                            confirm_delete_account = selected_account
                        elif back_button.collidepoint(event.pos):
                            selected_account = None
            else:
                # Show list of accounts
                draw_text("Accounts", font, BLACK, screen, WIDTH // 2, HEIGHT // 2 - 150)
                account_buttons = []
                y_pos = HEIGHT // 2 - 100
                for acc_name in accounts_to_show:
                    if acc_name != "david":  # Don't show David's own account
                        rect = pygame.Rect(WIDTH // 2 - 100, y_pos, 200, 40)
                        account_buttons.append((rect, acc_name))
                        draw_glassy_button(screen, rect, BLUE, 15)
                        draw_text(acc_name.title(), small_font, WHITE, screen, rect.centerx, rect.centery)
                        y_pos += 50
                back_button = pygame.Rect(WIDTH // 2 - 100, y_pos + 20, 200, 50)
                draw_glassy_button(screen, back_button, (120, 120, 120), 15)
                draw_text("Back", small_font, WHITE, screen, WIDTH // 2, back_button.centery)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for rect, acc_name in account_buttons:
                            if rect.collidepoint(event.pos):
                                selected_account = acc_name
                                break
                        if back_button.collidepoint(event.pos):
                            accounts_list = False
            pygame.display.flip()
            clock.tick(30)
            continue
        if confirm_delete_account:
            # Confirmation for deleting account
            draw_text(
                f"Are you sure you want to delete {confirm_delete_account.title()}?",
                font,
                BLACK,
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 40,
            )
            delete_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 50)
            cancel_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50)
            pygame.draw.rect(screen, RED, delete_button, border_radius=15)
            draw_text("Delete Account", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 65)
            pygame.draw.rect(screen, (120, 120, 120), cancel_button, border_radius=15)
            draw_text("Cancel", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 145)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if delete_button.collidepoint(event.pos):
                        # Delete account
                        accounts = load_accounts()
                        if confirm_delete_account in accounts:
                            del accounts[confirm_delete_account]
                            save_accounts(accounts)
                        elif confirm_delete_account == "kate":
                            # Remove Kate's progress
                            try:
                                data = {}
                                if UNLOCKED_LEVELS_FILE.exists():
                                    with open(UNLOCKED_LEVELS_FILE, "r") as f:
                                        data = json.load(f)
                                if "kate" in data:
                                    del data["kate"]
                                    with open(UNLOCKED_LEVELS_FILE, "w") as f:
                                        json.dump(data, f)
                            except Exception:
                                pass
                        confirm_delete_account = None
                    elif cancel_button.collidepoint(event.pos):
                        confirm_delete_account = None
            pygame.display.flip()
            clock.tick(30)
            continue
        if confirm_remove_password_account:
            # Confirmation for removing password
            draw_text(
                f"Are you sure you want to remove password for {confirm_remove_password_account.title()}?",
                font,
                BLACK,
                screen,
                WIDTH // 2,
                HEIGHT // 2 - 40,
            )
            remove_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 50)
            cancel_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50)
            pygame.draw.rect(screen, BLUE, remove_button, border_radius=15)
            draw_text("Remove Password", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 65)
            pygame.draw.rect(screen, (120, 120, 120), cancel_button, border_radius=15)
            draw_text("Cancel", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 145)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if remove_button.collidepoint(event.pos):
                        # Remove password
                        accounts = load_accounts()
                        if confirm_remove_password_account in accounts:
                            accounts[confirm_remove_password_account]["password"] = None
                            save_accounts(accounts)
                        confirm_remove_password_account = None
                    elif cancel_button.collidepoint(event.pos):
                        confirm_remove_password_account = None
            pygame.display.flip()
            clock.tick(30)
            continue
        # Main settings screen
        draw_text("Settings", font, BLACK, screen, WIDTH // 2, HEIGHT // 2 - 100)
        delete_button = None
        accounts_button = None
        password_y = HEIGHT // 2 + 50
        if player_name == "david":
            accounts_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 20, 200, 50)
            pygame.draw.rect(screen, (0, 150, 0), accounts_button, border_radius=15)
            draw_text("Accounts", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 5)
            password_y = HEIGHT // 2 + 80
        elif player_name not in ["david", "kate", "guest"]:
            delete_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 20, 200, 50)
            pygame.draw.rect(screen, RED, delete_button, border_radius=15)
            draw_text("Delete Account", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 5)
        accounts = load_accounts()
        has_password = accounts.get(player_name, {}).get("password") is not None
        password_button_text = "Remove Password" if has_password else "Set Password"
        set_password_button = pygame.Rect(WIDTH // 2 - 100, password_y, 200, 50)
        pygame.draw.rect(screen, BLUE, set_password_button, border_radius=15)
        draw_text(password_button_text, small_font, WHITE, screen, WIDTH // 2, password_y + 25)
        back_y = password_y + 70
        back_button = pygame.Rect(WIDTH // 2 - 100, back_y, 200, 50)
        pygame.draw.rect(screen, (120, 120, 120), back_button, border_radius=15)
        draw_text("Back", small_font, WHITE, screen, WIDTH // 2, back_y + 25)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if delete_button and delete_button.collidepoint(event.pos):
                    return "delete"
                if accounts_button and accounts_button.collidepoint(event.pos):
                    accounts_list = True
                if set_password_button.collidepoint(event.pos):
                    if has_password:
                        # Confirm remove password
                        confirm_remove_password = True
                    else:
                        # Set password
                        set_password_prompt = True
                        set_password = ""
                        set_error = ""
                        set_input_focused = False
                    break
                if back_button.collidepoint(event.pos):
                    return None
        pygame.display.flip()
        clock.tick(30)


# Level selection after start
def wait_for_start_and_choose_level(unlocked_levels, player_name):
    button_rect = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 + 40, 150, 50)
    back_button = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 + 180, 150, 50)
    confirm_delete = False
    while True:
        fill_background()
        if confirm_delete:
            # Confirmation screen
            draw_text(
                "Are you sure?", font, BLACK, screen, WIDTH // 2, HEIGHT // 2 - 40
            )
            confirm_delete_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 50)
            cancel_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50)
            pygame.draw.rect(screen, RED, confirm_delete_button, border_radius=15)
            draw_text("DELETE ACCOUNT", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 65)
            pygame.draw.rect(screen, (120, 120, 120), cancel_button, border_radius=15)
            draw_text("Cancel", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 145)
        else:
            # Normal screen
            draw_text(
                "Press Start to play!", font, BLACK, screen, WIDTH // 2, HEIGHT // 2 - 40
            )
            pygame.draw.rect(screen, BLUE, button_rect, border_radius=15)
            draw_text("START", font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 65)
            pygame.draw.rect(screen, (120, 120, 120), back_button, border_radius=15)
            draw_text("BACK", small_font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 205)
            settings_button = pygame.Rect(10, 10, 100, 40)
            pygame.draw.rect(screen, (100, 100, 100), settings_button, border_radius=15)
            draw_text("Settings", small_font, WHITE, screen, settings_button.centerx, settings_button.centery)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if confirm_delete:
                    # Handle confirmation screen
                    confirm_delete_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 50)
                    cancel_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50)
                    if confirm_delete_button.collidepoint(event.pos):
                        # Delete account
                        accounts = load_accounts()
                        if player_name in accounts:
                            del accounts[player_name]
                            save_accounts(accounts)
                        return None, None, "delete_account"
                    elif cancel_button.collidepoint(event.pos):
                        confirm_delete = False
                else:
                    # Handle normal screen
                    if button_rect.collidepoint(event.pos):
                        # Go to level select
                        level, _, action = choose_level_screen(unlocked_levels, player_name=player_name)
                        if action == "delete_account":
                            return None, None, "delete_account"
                        return level, False, None
                    if back_button.collidepoint(event.pos):
                        return None, None, "back"
                    if settings_button.collidepoint(event.pos):
                        result = show_settings_screen(player_name)
                        if result == "delete":
                            confirm_delete = True
        pygame.display.flip()
        clock.tick(30)


# Infinite level unlock: store highest unlocked level (int)


# --- Per-account level progress for David and Kate ---
def load_highest_unlocked_level(player_name=None):
    try:
        with open(UNLOCKED_LEVELS_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if player_name in ["david", "kate"]:
                return data.get(player_name, 1)
        elif isinstance(data, int):
            # Legacy support: if file is just an int, treat as David's progress
            if player_name == "david":
                return data
    except Exception:
        pass
    return 1


def save_highest_unlocked_level(level, player_name=None):
    try:
        # Load existing data
        data = {}
        if UNLOCKED_LEVELS_FILE.exists():
            with open(UNLOCKED_LEVELS_FILE, "r") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}
        if not isinstance(data, dict):
            data = {}
        if player_name in ["david", "kate"]:
            data[player_name] = level
            with open(UNLOCKED_LEVELS_FILE, "w") as f:
                json.dump(data, f)
    except Exception:
        pass


def game_loop():
    authenticated_user = None  # Remember who is logged in for this session
    user_mode = None
    while True:
        check_for_updates()
        show_title_screen()
        # Only ask for account if not already authenticated
        if authenticated_user is None:
            result = get_player_name()
            if isinstance(result, tuple):
                player_name, user_mode = result
            else:
                player_name = result
                user_mode = None
            # If David or Kate, set authenticated_user so we don't ask again
            if player_name in ["david", "kate"]:
                authenticated_user = player_name
        else:
            player_name = authenticated_user
            # For David/Kate, user_mode is always None
            user_mode = None

        accounts = load_accounts()
        if player_name not in ["david", "kate", "guest"]:
            highest_unlocked = accounts.get(player_name, {}).get("level", 1)
        elif player_name == "guest":
            highest_unlocked = 1
        else:
            highest_unlocked = load_highest_unlocked_level(player_name)

        # --- Always go to level select after each round ---
        while True:
            level_result = wait_for_start_and_choose_level(highest_unlocked, player_name)
            if level_result[2] == "signout":
                authenticated_user = None  # Reset authentication
                break  # Break to outer loop to show account selection again
            if level_result[2] == "delete_account":
                authenticated_user = None  # Reset authentication
                break  # Break to outer loop to show account selection again
            if level_result[2] == "back":
                authenticated_user = None  # Reset authentication
                break  # Break to outer loop to show account selection again
            level, _, _ = level_result
            # Skip if no level selected
            if level is None:
                continue
            # Initialize round state variables
            win = False
            lose = False
            collected = 0
            if player_name == "david":
                num_red = 2
                base_blue = 10
                red_speed = 4
            elif player_name == "kate":
                num_red = 1
                base_blue = 5
                red_speed = 1
            else:
                # Easy/Hard mode for non-David/Kate
                if user_mode == "easy":
                    num_red = 1
                    base_blue = 5
                    red_speed = 1
                elif user_mode == "hard":
                    num_red = 2
                    base_blue = 10
                    red_speed = 4
                else:
                    num_red = 1
                    base_blue = 5
                    red_speed = 2
            num_blue = base_blue + (level - 1)
            player_pos = [WIDTH // 2, HEIGHT // 2]
            # --- Gameplay setup ---
            red_balls = []
            if num_red == 1:
                edge = random.choice(["top", "bottom", "left", "right"])
                if edge == "top":
                    x = random.randint(RED_RADIUS, WIDTH - RED_RADIUS)
                    y = RED_RADIUS
                elif edge == "bottom":
                    x = random.randint(RED_RADIUS, WIDTH - RED_RADIUS)
                    y = HEIGHT - RED_RADIUS
                elif edge == "left":
                    x = RED_RADIUS
                    y = random.randint(RED_RADIUS, HEIGHT - RED_RADIUS)
                else:  # right
                    x = WIDTH - RED_RADIUS
                    y = random.randint(RED_RADIUS, HEIGHT - RED_RADIUS)
                red_balls.append([x, y])
            else:
                edge = random.choice(["top", "bottom", "left", "right"])
                spacing = 2 * RED_RADIUS + 5
                if edge in ["top", "bottom"]:
                    start_x = random.randint(
                        RED_RADIUS, WIDTH - RED_RADIUS - (num_red - 1) * spacing
                    )
                    y = RED_RADIUS if edge == "top" else HEIGHT - RED_RADIUS
                    for i in range(num_red):
                        x = start_x + i * spacing
                        red_balls.append([x, y])
                else:
                    start_y = random.randint(
                        RED_RADIUS, HEIGHT - RED_RADIUS - (num_red - 1) * spacing
                    )
                    x = RED_RADIUS if edge == "left" else WIDTH - RED_RADIUS
                    for i in range(num_red):
                        y = start_y + i * spacing
                        red_balls.append([x, y])
            blue_balls = []
            for _ in range(num_blue):
                while True:
                    pos = [
                        random.randint(BLUE_RADIUS, WIDTH - BLUE_RADIUS),
                        random.randint(BLUE_RADIUS, HEIGHT - BLUE_RADIUS),
                    ]
                    if (
                        abs(pos[0] - player_pos[0]) > 100
                        or abs(pos[1] - player_pos[1]) > 100
                    ):
                        blue_balls.append(pos)
                        break
            freeze_idx = random.randint(0, num_blue - 1)
            freeze_pos = None
            speedup_pos = None
            slowdown_pos = None
            if num_blue > 2:
                candidates = [i for i in range(num_blue) if i != freeze_idx]
                speedup_idx = random.choice(candidates)
                candidates2 = [i for i in candidates if i != speedup_idx]
                slowdown_idx = random.choice(candidates2)
                freeze_pos = blue_balls[freeze_idx]
                speedup_pos = blue_balls[speedup_idx]
                slowdown_pos = blue_balls[slowdown_idx]
            elif num_blue > 1:
                candidates = [i for i in range(num_blue) if i != freeze_idx]
                speedup_idx = random.choice(candidates)
                freeze_pos = blue_balls[freeze_idx]
                speedup_pos = blue_balls[speedup_idx]
                slowdown_pos = None
            else:
                freeze_pos = blue_balls[0]
                speedup_pos = None
                slowdown_pos = None
            speedup_active = False
            speedup_timer = 0
            speedup_seconds_left = 0
            slowdown_active = False
            slowdown_timer = 0
            slowdown_seconds_left = 0
            freeze_active = False
            freeze_timer = 0
            freeze_seconds_left = 0
            player_speed = SPEED
            current_red_speed = red_speed
            # --- Main gameplay loop ---
            running = True
            while running:
                fill_background()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                keys = pygame.key.get_pressed()
                player_moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]
                if keys[pygame.K_LEFT]:
                    player_pos[0] -= player_speed
                if keys[pygame.K_RIGHT]:
                    player_pos[0] += player_speed
                if keys[pygame.K_UP]:
                    player_pos[1] -= player_speed
                if keys[pygame.K_DOWN]:
                    player_pos[1] += player_speed
                player_pos[0] = max(
                    PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, player_pos[0])
                )
                player_pos[1] = max(
                    PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS, player_pos[1])
                )
                # Freeze timer logic
                if freeze_active:
                    freeze_timer -= clock.get_time()
                    if freeze_timer <= 0:
                        freeze_active = False
                    freeze_seconds_left = max(0, int((freeze_timer + 999) // 1000))
                else:
                    freeze_seconds_left = 0
                # Speed up timer logic
                if speedup_active:
                    speedup_timer -= clock.get_time()
                    if speedup_timer <= 0:
                        speedup_active = False
                        player_speed = SPEED
                    speedup_seconds_left = max(0, int((speedup_timer + 999) // 1000))
                else:
                    speedup_seconds_left = 0
                # Slow down timer logic
                if slowdown_active:
                    slowdown_timer -= clock.get_time()
                    if slowdown_timer <= 0:
                        slowdown_active = False
                        current_red_speed = red_speed
                    slowdown_seconds_left = max(0, int((slowdown_timer + 999) // 1000))
                else:
                    slowdown_seconds_left = 0
                # Move red balls toward player (unless freeze is active)
                if not freeze_active:
                    for i, red_pos in enumerate(red_balls):
                        dx = player_pos[0] - red_pos[0]
                        dy = player_pos[1] - red_pos[1]
                        dist = max(1, (dx**2 + dy**2) ** 0.5)
                        move_x = round(current_red_speed * dx / dist)
                        move_y = round(current_red_speed * dy / dist)
                        if move_x == 0 and dx != 0:
                            move_x = 1 if dx > 0 else -1
                        if move_y == 0 and dy != 0:
                            move_y = 1 if dy > 0 else -1
                        red_pos[0] += move_x
                        red_pos[1] += move_y
                # Separate red balls if they touch each other (only when player is moving)
                if player_moving:
                    for i in range(len(red_balls)):
                        for j in range(i + 1, len(red_balls)):
                            r1 = red_balls[i]
                            r2 = red_balls[j]
                            dx = r2[0] - r1[0]
                            dy = r2[1] - r1[1]
                            dist = (dx**2 + dy**2) ** 0.5
                            min_dist = 2 * RED_RADIUS
                            if dist < min_dist and dist > 0:
                                # Find the opposite side of the yellow ball (player)
                                def opposite_edge(player_pos):
                                    px, py = player_pos
                                    # Find which edge is farthest from player
                                    dists = [
                                        (px, "left"),
                                        (WIDTH - px, "right"),
                                        (py, "top"),
                                        (HEIGHT - py, "bottom"),
                                    ]
                                    farthest = max(dists, key=lambda x: x[0])[1]
                                    if farthest == "left":
                                        x = RED_RADIUS
                                        y = random.randint(RED_RADIUS, HEIGHT - RED_RADIUS)
                                    elif farthest == "right":
                                        x = WIDTH - RED_RADIUS
                                        y = random.randint(RED_RADIUS, HEIGHT - RED_RADIUS)
                                    elif farthest == "top":
                                        x = random.randint(RED_RADIUS, WIDTH - RED_RADIUS)
                                        y = RED_RADIUS
                                    else:  # bottom
                                        x = random.randint(RED_RADIUS, WIDTH - RED_RADIUS)
                                        y = HEIGHT - RED_RADIUS
                                    return [x, y]

                                # Respawn both red balls on the opposite side of the player
                                red_balls[i] = opposite_edge(player_pos)
                                red_balls[j] = opposite_edge(player_pos)
                for blue in blue_balls:
                    if freeze_pos is not None and blue == freeze_pos:
                        pygame.draw.circle(screen, (180, 240, 255), blue, BLUE_RADIUS)
                        pygame.draw.circle(screen, WHITE, blue, BLUE_RADIUS, 2)
                        for angle in range(0, 360, 60):
                            rad = angle * math.pi / 180
                            x1 = blue[0] + int(BLUE_RADIUS * 0.7 * math.cos(rad))
                            y1 = blue[1] + int(BLUE_RADIUS * 0.7 * math.sin(rad))
                            x2 = blue[0] - int(BLUE_RADIUS * 0.7 * math.cos(rad))
                            y2 = blue[1] - int(BLUE_RADIUS * 0.7 * math.sin(rad))
                            pygame.draw.line(
                                screen, (0, 180, 255), (x1, y1), (x2, y2), 2
                            )
                    elif speedup_pos is not None and blue == speedup_pos:
                        pygame.draw.circle(screen, (0, 200, 0), blue, BLUE_RADIUS)
                        pygame.draw.circle(screen, WHITE, blue, BLUE_RADIUS, 3)
                        bolt = [
                            (blue[0] - 2, blue[1] - 5),
                            (blue[0] + 2, blue[1] - 1),
                            (blue[0], blue[1] - 1),
                            (blue[0] + 3, blue[1] + 5),
                            (blue[0] - 1, blue[1] + 1),
                            (blue[0] + 1, blue[1] + 1),
                        ]
                        pygame.draw.polygon(screen, YELLOW, bolt)
                        pygame.draw.polygon(screen, BLACK, bolt, 1)
                    elif slowdown_pos is not None and blue == slowdown_pos:
                        pygame.draw.circle(screen, (255, 140, 0), blue, BLUE_RADIUS)
                        pygame.draw.circle(screen, WHITE, blue, BLUE_RADIUS, 3)
                        pygame.draw.arc(
                            screen, BLACK, (blue[0] - 5, blue[1] - 2, 10, 8), 3.14, 0, 2
                        )
                        pygame.draw.line(
                            screen,
                            BLACK,
                            (blue[0] - 5, blue[1] + 2),
                            (blue[0] + 5, blue[1] + 2),
                            2,
                        )
                    else:
                        pygame.draw.circle(screen, BLUE, blue, BLUE_RADIUS)
                for red in red_balls:
                    pygame.draw.circle(screen, RED, red, RED_RADIUS)
                pygame.draw.circle(screen, YELLOW, player_pos, PLAYER_RADIUS)
                for blue in blue_balls[:]:
                    if (player_pos[0] - blue[0]) ** 2 + (
                        player_pos[1] - blue[1]
                    ) ** 2 < (PLAYER_RADIUS + BLUE_RADIUS) ** 2:
                        is_freeze = freeze_pos is not None and blue == freeze_pos
                        is_speedup = speedup_pos is not None and blue == speedup_pos
                        is_slowdown = slowdown_pos is not None and blue == slowdown_pos
                        if is_freeze:
                            freeze_active = True
                            freeze_timer = 5000
                            freeze_seconds_left = max(
                                0, int((freeze_timer + 999) // 1000)
                            )
                        if is_speedup:
                            speedup_active = True
                            speedup_timer = 5000
                            player_speed = SPEED * 2
                            speedup_seconds_left = max(
                                0, int((speedup_timer + 999) // 1000)
                            )
                        if is_slowdown:
                            slowdown_active = True
                            slowdown_timer = 5000
                            current_red_speed = max(1, red_speed // 2)
                            slowdown_seconds_left = max(
                                0, int((slowdown_timer + 999) // 1000)
                            )
                        blue_balls.remove(blue)
                        collected += 1
                        if is_freeze:
                            freeze_pos = None
                        if is_speedup:
                            speedup_pos = None
                        if is_slowdown:
                            slowdown_pos = None
                if not freeze_active:
                    for red in red_balls:
                        if (player_pos[0] - red[0]) ** 2 + (
                            player_pos[1] - red[1]
                        ) ** 2 < (PLAYER_RADIUS + RED_RADIUS) ** 2:
                            lose = True
                            running = False
                if collected == num_blue:
                    win = True
                    running = False
                draw_text(
                    f"Collected: {collected}/{num_blue}",
                    small_font,
                    BLACK,
                    screen,
                    100,
                    30,
                )
                if freeze_active:
                    draw_text(
                        f"Freeze: {freeze_seconds_left}",
                        small_font,
                        (0, 180, 255),
                        screen,
                        WIDTH - 120,
                        30,
                    )
                if speedup_active:
                    draw_text(
                        f"Speed Up: {speedup_seconds_left}",
                        small_font,
                        (0, 200, 0),
                        screen,
                        WIDTH - 120,
                        60,
                    )
                if slowdown_active:
                    draw_text(
                        f"Slow Down: {slowdown_seconds_left}",
                        small_font,
                        YELLOW,
                        screen,
                        WIDTH - 120,
                        90,
                    )
                pygame.display.flip()
                clock.tick(60)
            restart_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 60)
            save_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50)
            show_save = (
                player_name not in ["david", "kate"] and player_name not in accounts
            )
            temp_other = player_name == "guest"
            save_prompt = False
            save_name = ""
            save_box = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 190, 200, 50)
            save_message = ""
            while True:
                # If save_prompt is active, handle save dialog in a dedicated loop
                if save_prompt:
                    input_active = True
                    input_focused = False
                    while input_active:
                        fill_background()
                        if win:
                            draw_text(
                                "You Win!",
                                font,
                                (0, 200, 0),
                                screen,
                                WIDTH // 2,
                                HEIGHT // 2 - 30,
                            )
                        elif lose:
                            draw_text(
                                "You Lose!",
                                font,
                                RED,
                                screen,
                                WIDTH // 2,
                                HEIGHT // 2 - 30,
                            )
                        draw_text(
                            f"Collected: {collected}/{num_blue}",
                            small_font,
                            YELLOW,
                            screen,
                            WIDTH // 2,
                            HEIGHT // 2 + 20,
                        )
                        pygame.draw.rect(screen, BLUE, restart_button, border_radius=20)
                        draw_text(
                            "START OVER",
                            font,
                            WHITE,
                            screen,
                            WIDTH // 2,
                            HEIGHT // 2 + 100,
                        )
                        # Save dialog UI
                        # Highlight input box if focused
                        if input_focused:
                            pygame.draw.rect(screen, (0, 200, 255), save_box, 4)
                        else:
                            pygame.draw.rect(screen, WHITE, save_box, 2)
                        draw_text(
                            "Enter name:",
                            small_font,
                            BLACK,
                            screen,
                            WIDTH // 2,
                            HEIGHT // 2 + 170,
                        )
                        draw_text(
                            save_name,
                            font,
                            BLACK,
                            screen,
                            WIDTH // 2,
                            HEIGHT // 2 + 215,
                        )
                        cancel_button = pygame.Rect(
                            WIDTH // 2 - 100, HEIGHT // 2 + 250, 200, 40
                        )
                        draw_glassy_button(screen, cancel_button, (120, 120, 120), 15)
                        draw_text(
                            "Cancel",
                            small_font,
                            WHITE,
                            screen,
                            cancel_button.centerx,
                            cancel_button.centery,
                        )
                        if save_message:
                            draw_text(
                                save_message,
                                small_font,
                                RED,
                                screen,
                                WIDTH // 2,
                                HEIGHT // 2 + 295,
                            )
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                if cancel_button.collidepoint(event.pos):
                                    save_prompt = False
                                    save_name = ""
                                    save_message = ""
                                    input_active = False
                                elif save_box.collidepoint(event.pos):
                                    input_focused = True
                                else:
                                    # Click outside input box or cancel closes dialog
                                    save_prompt = False
                                    input_active = False
                            if input_focused and event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_RETURN:
                                    if save_name:
                                        accounts = load_accounts()
                                        if (
                                            save_name in ["david", "kate"]
                                            or save_name in accounts
                                        ):
                                            save_message = "Name taken!"
                                        else:
                                            accounts[save_name] = {"level": max(level if level is not None else 1, 1), "password": None}
                                            save_accounts(accounts)
                                            save_message = "Saved!"
                                            pygame.display.flip()
                                            pygame.time.wait(700)
                                            save_prompt = False
                                            input_active = False
                                            # Update player_name and accounts for new user
                                            player_name = save_name
                                            accounts = load_accounts()
                                            show_save = False
                                elif event.key == pygame.K_BACKSPACE:
                                    save_name = save_name[:-1]
                                else:
                                    if (
                                        len(save_name) < 12
                                        and event.unicode.isprintable()
                                    ):
                                        save_name += event.unicode
                        pygame.display.flip()
                        clock.tick(30)
                    continue  # After save dialog, redraw main win/lose screen
                # Main win/lose screen
                fill_background()
                if win:
                    draw_text(
                        "You Win!",
                        font,
                        (0, 200, 0),
                        screen,
                        WIDTH // 2,
                        HEIGHT // 2 - 30,
                    )
                elif lose:
                    draw_text(
                        "You Lose!", font, RED, screen, WIDTH // 2, HEIGHT // 2 - 30
                    )
                draw_text(
                    f"Collected: {collected}/{num_blue}",
                    small_font,
                    YELLOW,
                    screen,
                    WIDTH // 2,
                    HEIGHT // 2 + 20,
                )
                pygame.draw.rect(screen, BLUE, restart_button, border_radius=20)
                draw_text(
                    "START OVER", font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 100
                )
                if show_save and not save_prompt:
                    pygame.draw.rect(screen, (0, 150, 255), save_button, border_radius=15)
                    draw_text(
                        "Save My Progress",
                        small_font,
                        WHITE,
                        screen,
                        save_button.centerx,
                        save_button.centery,
                    )
                settings_button = pygame.Rect(10, 10, 100, 40)
                pygame.draw.rect(screen, (100, 100, 100), settings_button, border_radius=10)
                draw_text("Settings", small_font, WHITE, screen, settings_button.centerx, settings_button.centery)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if restart_button.collidepoint(event.pos):
                            break
                        if (
                            show_save
                            and not save_prompt
                            and save_button.collidepoint(event.pos)
                        ):
                            save_prompt = True
                            save_name = ""
                            save_message = ""
                        if settings_button.collidepoint(event.pos):
                            result = show_settings_screen(player_name)
                            if result == "delete":
                                authenticated_user = None
                                break
                else:
                    pygame.display.flip()
                    clock.tick(30)
                    continue
                break
            # Unlock next level if win and not already unlocked
            if win:
                if player_name in ["david", "kate"]:
                    if level is not None and level >= highest_unlocked:
                        highest_unlocked = level + 1
                        save_highest_unlocked_level(highest_unlocked, player_name)
                elif player_name != "guest":
                    accounts = load_accounts()
                    # Always unlock next level for this user
                    if level is not None:
                        current_level = accounts.get(player_name, {}).get("level", 1)
                        accounts[player_name]["level"] = max(level + 1, current_level)
                        save_accounts(accounts)
                        highest_unlocked = accounts[player_name]["level"]
            # else: playing as 'guest', do NOT save progress
            # After win/lose we already handled any unlocking above.
            # Continuing the loop will take us back to the level selection screen
            # without going all the way back to the title/account screens.
            continue


if __name__ == "__main__":
    game_loop()
