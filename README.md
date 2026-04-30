TikTok Webcast Protobuf (Unofficial)
==================
Canonical Protobuf schemas for TikTok's Webcast WebSocket protocol, plus auto-generated language bindings published to their native package registries. Originally reverse-engineered for the [TikTokLive](https://github.com/isaackogan/TikTokLive) project; maintained here as a standalone source of truth so multiple client libraries can share one schema.

[![Discord](https://img.shields.io/discord/977648006063091742?logo=discord&label=TikTokLive%20Discord&labelColor=%23171717&color=%231877af)](https://discord.gg/N3KSxzvDX8)
![Connections](https://tiktok.eulerstream.com/analytics/pips)
![npm](https://img.shields.io/npm/v/tiktok-live-proto?label=tiktok-live-proto&color=0274b5)
![npm downloads](https://img.shields.io/npm/dt/tiktok-live-proto?color=0274b5)
![Stars](https://img.shields.io/github/stars/isaackogan/TikTok-Webcast-Protobuf?style=flat&color=0274b5)
![Forks](https://img.shields.io/github/forks/isaackogan/TikTok-Webcast-Protobuf?style=flat&color=0274b5)
![Issues](https://img.shields.io/github/issues/isaackogan/TikTok-Webcast-Protobuf)

## Legal Notice 🏛️

> [!IMPORTANT]
> This repository is an independent, non-commercial interoperability project. Its purpose is to document and provide compatible Protocol Buffer interface definitions for systems that need to communicate with TikTok-related services or data formats.
> 
> The Protocol Buffer definitions in this repository were produced through a clean-room reverse-engineering process. They are intended to describe interface behavior and wire-format compatibility, not to copy TikTok’s implementation code, internal systems, proprietary documentation, branding, or other protected expressive materials.
> 
> This project is based on the good-faith position that independently reimplemented interface definitions used for interoperability is permissible under applicable law, including principles reflected in *Google LLC v. Oracle America, Inc.*, > 593 U.S. 1 (2021), where the U.S. Supreme Court held that limited reuse of software interface material for a transformative interoperability-related purpose constituted fair use.
>
> Nothing in this repository is intended to:
> - misappropriate trade secrets;
> - reproduce TikTok source code or proprietary implementation logic;
> - imply affiliation with, endorsement by, or sponsorship from TikTok or ByteDance;
> - bypass technical protection measures;
> - facilitate unauthorized access to any system; or
> - enable infringement of TikTok’s intellectual property rights.
>
> All trademarks, service marks, and product names are the property of their respective owners and are used only for identification and interoperability purposes.
> 
> If you believe this repository contains material that infringes your rights or otherwise raises a legal concern, please contact `info@isaackogan.com`.

## Table of Contents

- [Repository Layout](#repository-layout)
- [Language Targets](#language-targets)
- [Contributing a New Target](#contributing-a-new-target)
- [Community](#community)
- [Licensing](#license)
- [Contributors](#contributors)

## Community

Join the [TikTokLive discord](https://discord.gg/e2XwPNTBBr) for questions, contributions, and ideas.

## Repository Layout

Only `src/**/*.proto` is hand-edited. Generated bindings live under each target package's `src/` tree and are rewritten by CI whenever a `.proto` file changes.

## Language Targets

| Target     | Package                                                    | Status    |
|------------|------------------------------------------------------------|-----------|
| TypeScript | [`tiktok-live-proto`](https://www.npmjs.com/package/tiktok-live-proto) on npm | ✅ Shipping |
| Python     | [`TikTokLiveProto`](targets/python/TikTokLiveProto) | ✅ Ready |
| Go         | —                                                          | Planned   |
| Rust       | —                                                          | Planned   |

The Python target uses `betterproto2` with Pydantic-backed generated
dataclasses, versioned directly under `v1` and `v2`, and imported as
`TikTokLiveProto.v1` and `TikTokLiveProto.v2`.

## Contributing a New Target

Each target lives under `targets/<language>/<package-name>/` with:

1. A build script that reads the canonical `src/v{1,2}/*.proto` files and emits committed bindings under the package's `src/` tree.
2. A native package manifest (e.g. `package.json`, `pyproject.toml`, `Cargo.toml`).
3. Two GitHub workflows:
   - `generate-<language>.yml` — regenerates and commits bindings on `.proto` change.
   - `release-<language>.yml` — workflow-dispatched publish with version bump.

The TypeScript target is the reference implementation — mirror its layout and CI conventions when adding a new language.

## License

This project is licensed under the MIT License and is intended for **non-commercial use only** (research, interoperability, and reverse-engineering). See the `LICENSE` file at the repo root for details.

## Contributors

* **Isaac Kogan** — *Creator, Primary Maintainer, and Reverse-Engineering* — [isaackogan](https://github.com/isaackogan)

See also the full list of [contributors](https://github.com/isaackogan/TikTok-Webcast-Protobuf/contributors) who have participated in this project.
