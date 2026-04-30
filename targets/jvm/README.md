# tiktok-live-proto (JVM)

Multi-module Gradle build that publishes two artifacts to the same Maven repo:

| Module | Artifact | Purpose |
|---|---|---|
| `:tiktok-live-proto` | `com.isaackogan:tiktok-live-proto` | Java emit from the slim protos via Square Wire. Importable from Java *and* Kotlin. |
| `:tiktok-live-proto-kotlin` | `com.isaackogan:tiktok-live-proto-kotlin` | Kotlin extensions that depend on the Java module — DSL builders, coroutine helpers, etc. |

## Layout

```
targets/jvm/
├── settings.gradle.kts          # multi-module declaration
├── build.gradle.kts             # shared config (publishing repo, toolchain)
├── gradle.properties            # group + version (single source of truth)
├── gradlew, gradle/wrapper/...  # Gradle 9.1 wrapper
├── tiktok-live-proto/
│   ├── build.gradle.kts         # Wire java {} emit
│   └── scripts/prepare_protos.py
└── tiktok-live-proto-kotlin/
    ├── build.gradle.kts         # depends on :tiktok-live-proto
    └── src/main/kotlin/...      # extensions
```

## Java packages produced

| Schema | Java package |
|---|---|
| v1 | `com.isaackogan.webcast.v1.*` |
| v2 | `com.isaackogan.webcast.v2.*` |
| v3 (proto pkg `webcast.envelope`) | `com.isaackogan.webcast.v3.webcast.envelope.*` |
| ... | ... |

## Build

```sh
./gradlew build           # both modules
./gradlew publish         # both modules → MAVEN_REPO_URL
```

Requires Python 3.10+ on `PATH` (for the proto staging step). Java toolchain
17 is auto-provisioned by the foojay resolver.

## Publish

`publishing` reads `MAVEN_REPO_URL`, `MAVEN_USERNAME`, `MAVEN_PASSWORD` from
the environment. CI populates these from GitHub secrets.

```sh
MAVEN_REPO_URL=https://maven.cloudsmith.io/eulerstream/maven/ \
MAVEN_USERNAME=... MAVEN_PASSWORD=... \
./gradlew publish
```
