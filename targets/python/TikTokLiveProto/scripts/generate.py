from __future__ import annotations

import re
import shutil
import subprocess
import sysconfig
import textwrap
from pathlib import Path
from shutil import which
from site import getuserbase

PKG_ROOT = Path(__file__).resolve().parent.parent
PROTO_ROOT = PKG_ROOT.parent.parent.parent / "src"
TMP_DIR = PKG_ROOT / "tmp"
SRC_PKG = PKG_ROOT / "src" / "TikTokLiveProto"
GEN_DIR = SRC_PKG / "generated"

# betterproto generates a flatter, TikTokLive-style module layout when the
# synthetic merged schema omits the package declaration during codegen.
HEADER = 'syntax = "proto3";\n\n'
VERSION_DIR_RE = re.compile(r"^v\d+$")
HEADER_LINE_RE = re.compile(r"^\s*(syntax|import|package)\b")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
MODULE_NAME = "tiktok_proto.py"


def list_protos(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*.proto") if path.is_file())


def strip_header_lines(content: str) -> str:
    content = BLOCK_COMMENT_RE.sub("", content)
    out_lines: list[str] = []
    for line in content.splitlines():
        stripped = line.lstrip()
        if HEADER_LINE_RE.match(line) or stripped.startswith("//"):
            continue
        out_lines.append(line.split("//", 1)[0].rstrip())
    return "\n".join(out_lines).strip()


def resolve_plugin() -> Path:
    env_path = which("protoc-gen-python_betterproto")
    if env_path:
        return Path(env_path)

    candidates = [
        Path(sysconfig.get_path("scripts") or "") / "protoc-gen-python_betterproto",
        Path(getuserbase()) / "bin" / "protoc-gen-python_betterproto",
        PKG_ROOT / ".venv" / "bin" / "protoc-gen-python_betterproto",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "protoc-gen-python_betterproto not found. "
        "Install it with `pip install \"betterproto[compiler]==2.0.0b7\"`."
    )


def merge_version(version: str) -> tuple[Path, Path]:
    src_dir = PROTO_ROOT / version
    if not src_dir.exists():
        raise FileNotFoundError(f"Missing proto source dir: {src_dir}")

    protos = list_protos(src_dir)
    if not protos:
        raise FileNotFoundError(f"No .proto files under {src_dir}")

    merged = HEADER + "\n\n".join(
        strip_header_lines(path.read_text(encoding="utf8")) for path in protos
    ) + "\n"

    out_dir = TMP_DIR / "proto" / version
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"tiktok-schema-{version}.proto"
    out_file.write_text(merged, encoding="utf8")
    return out_dir, out_file


def extract_generated_module(tmp_out: Path, out_gen: Path) -> None:
    generated_file = tmp_out / "__init__.py"
    if not generated_file.exists():
        raise RuntimeError(f"Expected betterproto to emit {generated_file}")

    shutil.rmtree(out_gen, ignore_errors=True)
    out_gen.mkdir(parents=True, exist_ok=True)
    shutil.move(str(generated_file), out_gen / MODULE_NAME)


def run_betterproto(
    version: str,
    proto_dir: Path,
    proto_file: Path,
    plugin_path: Path,
) -> None:
    tmp_out = TMP_DIR / "compiled" / version
    out_gen = GEN_DIR / version
    shutil.rmtree(tmp_out, ignore_errors=True)
    tmp_out.mkdir(parents=True, exist_ok=True)
    out_gen.mkdir(parents=True, exist_ok=True)

    cmd = [
        "protoc",
        f"--plugin=protoc-gen-python_betterproto={plugin_path}",
        f"-I={proto_dir}",
        f"--python_betterproto_out={tmp_out}",
        str(proto_file),
    ]

    print(f"[{version}] protoc + betterproto ...")
    subprocess.run(cmd, check=True)
    extract_generated_module(tmp_out, out_gen)


def write_package_files(versions: list[str]) -> None:
    SRC_PKG.mkdir(parents=True, exist_ok=True)
    import_block = "\n".join(
        f'{version} = _import_module(".generated.{version}", __name__)\n'
        f'_sys.modules[__name__ + ".{version}"] = {version}'
        for version in versions
    )
    (SRC_PKG / "__init__.py").write_text(
        textwrap.dedent(
            '''\
            """Python betterproto bindings for the TikTok Webcast protobuf schema."""

            import sys as _sys
            from importlib import import_module as _import_module

            '''
        )
        + import_block
        + "\n\n__all__ = [\n"
        + "".join(f'    "{version}",\n' for version in versions)
        + "]\n",
        encoding="utf8",
    )
    (SRC_PKG / "py.typed").touch()

    GEN_DIR.mkdir(parents=True, exist_ok=True)

    for version in versions:
        generated_version_dir = GEN_DIR / version
        generated_version_dir.mkdir(parents=True, exist_ok=True)
        (generated_version_dir / "__init__.py").write_text(
            f"from .tiktok_proto import *  # noqa: F401,F403\n",
            encoding="utf8",
        )


def clean_previous_outputs() -> None:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    shutil.rmtree(GEN_DIR, ignore_errors=True)
    shutil.rmtree(PKG_ROOT / "src" / "tiktok_live_proto", ignore_errors=True)

    if not SRC_PKG.exists():
        return

    for child in SRC_PKG.iterdir():
        if child.is_dir() and VERSION_DIR_RE.match(child.name):
            shutil.rmtree(child, ignore_errors=True)


def main() -> None:
    clean_previous_outputs()
    plugin_path = resolve_plugin()

    versions = sorted(
        entry.name
        for entry in PROTO_ROOT.iterdir()
        if entry.is_dir() and VERSION_DIR_RE.match(entry.name)
    )
    if not versions:
        raise FileNotFoundError(f"No version directories found under {PROTO_ROOT}")

    for version in versions:
        proto_dir, proto_file = merge_version(version)
        run_betterproto(version, proto_dir, proto_file, plugin_path)

    write_package_files(versions)
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    print("Done.")


if __name__ == "__main__":
    main()
