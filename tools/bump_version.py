import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHASER = ROOT / "chase_game.py"
INSTALLER = ROOT / "installer.iss"


def parse_version(value):
    parts = [p for p in value.strip().split(".") if p != ""]
    nums = []
    for part in parts:
        num = ""
        for ch in part:
            if ch.isdigit():
                num += ch
            else:
                break
        if num == "":
            nums.append(0)
        else:
            nums.append(int(num))
    while len(nums) < 3:
        nums.append(0)
    return nums[:3]


def format_version(nums):
    return ".".join(str(n) for n in nums)


def bump_version(nums, part):
    major, minor, patch = nums
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return [major, minor, patch]


def version_key(nums):
    return (nums[0], nums[1], nums[2])


def read_version_from_file(path, pattern):
    text = path.read_text(encoding="utf-8")
    match = re.search(pattern, text)
    if not match:
        raise RuntimeError(f"Version not found in {path}")
    return match.group(1), text


def write_version(path, text, pattern, new_version):
    updated, count = re.subn(
        pattern,
        lambda m: m.group(0).replace(m.group(1), new_version),
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"Failed to update {path}")
    path.write_text(updated, encoding="utf-8")


def main():
    part = "patch"
    if "--part" in sys.argv:
        idx = sys.argv.index("--part")
        if idx + 1 >= len(sys.argv):
            raise RuntimeError("--part requires major|minor|patch")
        part = sys.argv[idx + 1].strip().lower()
    part = os.getenv("BUMP_PART", part).strip().lower()
    if part not in {"major", "minor", "patch"}:
        raise RuntimeError("BUMP_PART must be major, minor, or patch")

    chase_version, chase_text = read_version_from_file(
        CHASER, r'APP_VERSION\s*=\s*"([^"]+)"'
    )
    inst_version, inst_text = read_version_from_file(
        INSTALLER, r'#define\s+AppVersion\s+"([^"]+)"'
    )

    chase_nums = parse_version(chase_version)
    inst_nums = parse_version(inst_version)

    base_nums = chase_nums
    if version_key(inst_nums) > version_key(chase_nums):
        base_nums = inst_nums

    new_nums = bump_version(base_nums, part)
    new_version = format_version(new_nums)

    write_version(CHASER, chase_text, r'APP_VERSION\s*=\s*"([^"]+)"', new_version)
    write_version(INSTALLER, inst_text, r'#define\s+AppVersion\s+"([^"]+)"', new_version)

    print(new_version)


if __name__ == "__main__":
    main()
