plugins {
    `java-library`
    kotlin("jvm")
    `maven-publish`
}

description = "Kotlin extensions for tiktok-live-proto (TikTok Webcast Protobuf schema)."

kotlin {
    jvmToolchain(17)
}

dependencies {
    api(project(":tiktok-live-proto"))
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
