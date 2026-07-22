plugins {
    `java-library`
    `maven-publish`
}

description = "Java bindings for the slim TikTok Webcast Protobuf schema (Square Wire)."

// Wire is applied only when (re)generating sources (-PgenerateProtos). Normal builds and releases
// compile the committed src/generated/java directly — no Wire, protoc, or python needed.
val generateProtos = providers.gradleProperty("generateProtos").isPresent
val generatedJavaDir = layout.projectDirectory.dir("src/generated/java")

dependencies {
    // Generated code extends com.squareup.wire.Message etc.; needed at compile + runtime.
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
        java {
            // Emit directly into the git-tracked source dir so regeneration is authoritative.
            out = generatedJavaDir.asFile.absolutePath
        }
    }

    tasks.withType<com.squareup.wire.gradle.WireTask>().configureEach {
        dependsOn(rootProject.tasks.named("prepareProtos"))
    }
} else {
    // Build/publish mode: compile the committed generated sources as plain Java.
    sourceSets.named("main") {
        java.srcDir(generatedJavaDir)
    }
}

publishing {
    publications {
        register<MavenPublication>("maven") {
            from(components["java"])
            pom {
                name.set("tiktok-live-proto")
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
