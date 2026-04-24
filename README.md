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

> [!NOTE]
> This is a **clean-room rewrite** of the Webcast wire format, ~~~~reconstructed from observed client traffic for the purposes of **interoperability and proof-of-concept reverse engineering**. It is **non-commercial** and is not affiliated with, endorsed by, or sourced from TikTok or ByteDance. Fields are added, removed, and renamed by TikTok without notice, so the schemas should be treated as a best-effort snapshot — not a stable contract.


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

Only `src/**/*.proto` is hand-edited. Everything under `targets/**/src/generated/` is rewritten by CI whenever a `.proto` file changes.

## Language Targets

| Target     | Package                                                    | Status    |
|------------|------------------------------------------------------------|-----------|
| TypeScript | [`tiktok-live-proto`](https://www.npmjs.com/package/tiktok-live-proto) on npm | ✅ Shipping |
| Python     | —                                                          | Planned   |
| Go         | —                                                          | Planned   |
| Rust       | —                                                          | Planned   |

## Contributing a New Target

Each target lives under `targets/<language>/<package-name>/` with:

1. A build script that reads the canonical `src/v{1,2}/*.proto` files and emits bindings into `src/generated/` (committed).
2. A native package manifest (e.g. `package.json`, `pyproject.toml`, `Cargo.toml`).
3. Two GitHub workflows:
   - `generate-<language>.yml` — regenerates and commits bindings on `.proto` change.
   - `release-<language>.yml` — workflow-dispatched publish with version bump.

The TypeScript target is the reference implementation — mirror its layout and CI conventions when adding a new language.

## License

This project is licensed under the MIT License and is intended for **non-commercial use only** (research, interoperability, and reverse-engineering). See the `LICENSE` file at the repo root for details.

## Contributors

* **Isaac Kogan** — *Creator, Primary Maintainer, and Reverse-Engineering* — [isaackogan](https://github.com/isaackogan)
~~~~
See also the full list of [contributors](https://github.com/isaackogan/TikTok-Webcast-Protobuf/contributors) who have participated in this project.
