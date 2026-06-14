plugins {
    `java-library`
    id("com.squareup.wire")
    `maven-publish`
}

description = "Java bindings for the slim TikTok Webcast Protobuf schema (Square Wire)."

dependencies {
    api("com.squareup.wire:wire-runtime-jvm:5.5.1")
}

val prepareProtos by tasks.registering(Exec::class) {
    description = "Copy slim/* protos into build/proto-staging with `option java_package` injected per version."
    executable = "python3"
    args(file("scripts/prepare_protos.py").absolutePath)
    inputs.dir(rootDir.resolve("../../src/slim"))
    inputs.file("scripts/prepare_protos.py")
    outputs.dir(layout.buildDirectory.dir("proto-staging"))
}

wire {
    permitPackageCycles(true)
    sourcePath {
        srcDir(layout.buildDirectory.dir("proto-staging/v1").get().asFile.absolutePath)
    }
    sourcePath {
        srcDir(layout.buildDirectory.dir("proto-staging/v2").get().asFile.absolutePath)
    }
    sourcePath {
        srcDir(layout.buildDirectory.dir("proto-staging/v3").get().asFile.absolutePath)
    }
    java {}
}

tasks.withType<com.squareup.wire.gradle.WireTask>().configureEach {
    dependsOn(prepareProtos)
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
                        name.set("MIT")
                        url.set("https://opensource.org/licenses/MIT")
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
