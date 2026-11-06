"""
Generate C# bindings from the TikTok Webcast Protobuf schema.

Prerequisites:
  - protoc in PATH  OR  auto-downloaded via Grpc.Tools NuGet
  - Python 3.10+

Usage:
  python scripts/generate.py
"""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent.parent
PROTO_ROOT = PKG_ROOT.parent.parent.parent / "src" / "slim"
GEN_DIR = PKG_ROOT / "src" / "generated"
TMP_DIR = PKG_ROOT / "tmp"

GRPC_TOOLS_VERSION = "2.70.0"
VERSION_DIR_RE = re.compile(r"^v\d+$")


def list_protos(directory: Path) -> list[Path]:
    return sorted(p for p in directory.rglob("*.proto") if p.is_file())


def resolve_protoc() -> Path:
    """Return path to protoc, using PATH if available, otherwise downloading via Grpc.Tools NuGet."""
    in_path = shutil.which("protoc")
    if in_path:
        return Path(in_path)
    return _download_protoc()


def _download_protoc() -> Path:
    """Extract protoc from the Grpc.Tools NuGet package."""
    nupkg_url = f"https://www.nuget.org/api/v2/package/Grpc.Tools/{GRPC_TOOLS_VERSION}"
    nupkg_path = TMP_DIR / "grpc.tools.nupkg"
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading Grpc.Tools {GRPC_TOOLS_VERSION}...")
    urllib.request.urlretrieve(nupkg_url, nupkg_path)

    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows":
        rid = "windows_x86_64" if "64" in machine else "windows_x86"
        exe = "protoc.exe"
    elif system == "darwin":
        rid = "macosx_x86_64" if "x86" in machine else "macosx_arm64"
        exe = "protoc"
    else:
        rid = "linux_x86_64" if "64" in machine else "linux_x86"
        exe = "protoc"

    extract_dir = TMP_DIR / "grpc.tools"
    with zipfile.ZipFile(nupkg_path) as zf:
        zf.extractall(extract_dir)

    protoc_path = extract_dir / "tools" / rid / exe
    if not protoc_path.exists():
        found = list(extract_dir.rglob(exe))
        if not found:
            raise FileNotFoundError(f"protoc not found in Grpc.Tools nupkg (rid={rid})")
        protoc_path = found[0]

    if sys.platform != "win32":
        protoc_path.chmod(0o755)

    print(f"Using protoc: {protoc_path}")
    return protoc_path


def inject_csharp_namespace(src_dir: Path, dst_dir: Path, version_prefix: str) -> None:
    """Copy .proto files to dst_dir, injecting/overriding csharp_namespace.

    Namespace is derived from the file's directory path (not its package
    declaration) to guarantee uniqueness even when multiple protos share
    the same package but live in different subdirectories.

    Examples (version_prefix="V3"):
      webcast/im/messages.proto        → V3.Webcast.Im
      webcast/model/gift/model.proto   → V3.Webcast.Model.Gift
    """
    ns_re  = re.compile(r'^\s*option\s+csharp_namespace\s*=\s*"[^"]*"\s*;', re.MULTILINE)
    syn_re = re.compile(r'(^\s*syntax\s*=\s*"[^"]*"\s*;)', re.MULTILINE)

    for proto in src_dir.rglob("*.proto"):
        rel  = proto.relative_to(src_dir)
        dest = dst_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = proto.read_text(encoding="utf-8")

        # Build namespace from the directory path parts.
        # Subdirectory components that share a name with a message type in the
        # parent namespace would create a C# namespace/type conflict (CS0101).
        # Known conflicts in v3: webcast/model/gift/ conflicts with message Gift
        # in webcast/model/ → merge gift/ into its parent namespace.
        MERGE_INTO_PARENT = {
            ("webcast", "model", "gift"),
        }
        dir_parts = rel.parent.parts  # e.g. ('webcast', 'model', 'gift')
        effective_parts = dir_parts
        for prefix in MERGE_INTO_PARENT:
            if dir_parts[:len(prefix)] == prefix:
                effective_parts = dir_parts[:len(prefix) - 1]
                break
        if effective_parts:
            dir_ns = ".".join(part.replace("_", " ").title().replace(" ", "") for part in effective_parts)
            new_ns = f"{version_prefix}.{dir_ns}"
        else:
            new_ns = version_prefix

        ns_line = f'option csharp_namespace = "{new_ns}";'

        if ns_re.search(text):
            text = ns_re.sub(ns_line, text)
        else:
            text = syn_re.sub(r'\1\n' + ns_line, text, count=1)

        dest.write_text(text, encoding="utf-8")


def generate_version(protoc: Path, version: str) -> None:
    version_dir = PROTO_ROOT / version
    protos = list_protos(version_dir)
    if not protos:
        print(f"  No .proto files found under {version_dir}, skipping.")
        return

    stage_dir = TMP_DIR / "stage" / version
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    inject_csharp_namespace(version_dir, stage_dir, f"TikTokLiveProto.{version.upper()}")

    out_dir = GEN_DIR / version
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    errors: list[str] = []
    for proto in list_protos(stage_dir):
        rel = proto.relative_to(stage_dir)
        file_out_dir = out_dir / rel.parent
        file_out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(protoc),
            f"--csharp_out={file_out_dir}",
            "--proto_path=.",
            "--csharp_opt=file_extension=.g.cs",
            str(rel),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(stage_dir))
        if result.returncode != 0:
            errors.append(f"  {rel}: {result.stderr.strip()}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise RuntimeError(f"protoc failed for {len(errors)} file(s) in version {version}")

    generated = list(out_dir.rglob("*.cs"))
    print(f"  [{version}] Generated {len(generated)} .cs files → {out_dir}")


def main() -> None:
    protoc = resolve_protoc()

    versions = sorted(
        d.name for d in PROTO_ROOT.iterdir()
        if d.is_dir() and VERSION_DIR_RE.match(d.name)
    )

    if not versions:
        raise RuntimeError(f"No version directories found under {PROTO_ROOT}")

    GEN_DIR.mkdir(parents=True, exist_ok=True)

    for version in versions:
        generate_version(protoc, version)

    # cleanup
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)

    print("Done.")


if __name__ == "__main__":
    main()
