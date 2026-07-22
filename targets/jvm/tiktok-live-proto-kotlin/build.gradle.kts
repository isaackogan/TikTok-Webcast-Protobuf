plugins {
    `java-library`
    kotlin("jvm")
    `maven-publish`
}

description = "Kotlin bindings for the slim TikTok Webcast Protobuf schema (Square Wire)."

kotlin {
    jvmToolchain(17)
}

// Wire is applied only when (re)generating sources (-PgenerateProtos). Normal builds and releases
// compile the committed src/generated/kotlin directly — no Wire, protoc, or python needed.
val generateProtos = providers.gradleProperty("generateProtos").isPresent
val generatedKotlinDir = layout.projectDirectory.dir("src/generated/kotlin")

dependencies {
    // Standalone Kotlin binding: ships its own Wire-generated Kotlin messages (no Java module dep).
    api("com.squareup.wire:wire-runtime-jvm:5.5.1")
}

if (generateProtos) {
    apply(plugin = "com.squareup.wire")

    configure<com.squareup.wire.gradle.WireExtension> {
        permitPackageCycles(true)
        sourcePath {
            srcDir(rootProject.layout.buildDirectory.dir("proto-staging/v1").get().asFile.absolutePath)
        }
        sourcePath {
            srcDir(rootProject.layout.buildDirectory.dir("proto-staging/v2").get().asFile.absolutePath)
        }
        sourcePath {
            srcDir(rootProject.layout.buildDirectory.dir("proto-staging/v3").get().asFile.absolutePath)
        }
        kotlin {
            // Emit directly into the git-tracked source dir so regeneration is authoritative.
            out = generatedKotlinDir.asFile.absolutePath
        }
    }

    tasks.withType<com.squareup.wire.gradle.WireTask>().configureEach {
        dependsOn(rootProject.tasks.named("prepareProtos"))
    }
} else {
    // Build/publish mode: compile the committed generated Kotlin sources.
    kotlin {
        sourceSets["main"].kotlin.srcDir(generatedKotlinDir)
    }
}

publishing {
    publications {
        register<MavenPublication>("maven") {
            from(components["java"])
            pom {
                name.set("tiktok-live-proto-kotlin")
                description.set(project.description)
                url.set("https://github.com/isaackogan/TikTok-Webcast-Protobuf")
                licenses {
                    license {
                        name.set("AGPL-3.0-only")
                        url.set("https://github.com/isaackogan/TikTok-Webcast-Protobuf/blob/main/LICENSE")
                    }
                }
                developers {
                    developer {
                        id.set("eulerstream")
                        name.set("EulerStream")
                        url.set("https://www.eulerstream.com")
                    }
                }
                scm {
                    url.set("https://github.com/isaackogan/TikTok-Webcast-Protobuf")
                    connection.set("scm:git:https://github.com/isaackogan/TikTok-Webcast-Protobuf.git")
                }
            }
        }
    }
}
