plugins {
    `java-library`
    id("com.squareup.wire") version "5.5.1"
    `maven-publish`
}

group = "com.isaackogan.webcast"
version = "0.1.0"
description = "Java bindings for the slim TikTok Webcast Protobuf schema (Square Wire)."

repositories {
    mavenCentral()
}

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(17)
    }
}

dependencies {
    api("com.squareup.wire:wire-runtime-jvm:5.5.1")
}

val prepareProtos by tasks.registering(Exec::class) {
    description = "Copy slim/* protos into build/proto-staging with `option java_package` injected per version."
    executable = "python3"
    args(file("scripts/prepare_protos.py").absolutePath)
    inputs.dir(rootDir.resolve("../../../src/slim"))
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

java {
    withSourcesJar()
    withJavadocJar()
}

tasks.named<Javadoc>("javadoc") {
    isFailOnError = false
    (options as StandardJavadocDocletOptions).addStringOption("Xdoclint:none", "-quiet")
}

publishing {
    repositories {
        maven {
            name = "mavenTarget"
            url = uri(System.getenv("MAVEN_REPO_URL")
                ?: "https://maven.cloudsmith.io/eulerstream/maven/")
            credentials {
                username = System.getenv("MAVEN_USERNAME")
                password = System.getenv("MAVEN_PASSWORD")
            }
        }
    }
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
                scm {
                    url.set("https://github.com/isaackogan/TikTok-Webcast-Protobuf")
                    connection.set("scm:git:https://github.com/isaackogan/TikTok-Webcast-Protobuf.git")
                }
            }
        }
    }
}
