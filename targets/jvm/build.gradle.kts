plugins {
    kotlin("jvm") version "2.2.21" apply false
    id("com.squareup.wire") version "5.5.1" apply false
}

allprojects {
    repositories {
        mavenCentral()
    }
}

subprojects {
    apply(plugin = "maven-publish")

    plugins.withId("java-library") {
        extensions.configure<JavaPluginExtension> {
            toolchain {
                languageVersion.set(JavaLanguageVersion.of(17))
            }
            withSourcesJar()
            withJavadocJar()
        }

        tasks.named<Javadoc>("javadoc") {
            isFailOnError = false
            (options as StandardJavadocDocletOptions).addStringOption("Xdoclint:none", "-quiet")
        }
    }

    afterEvaluate {
        extensions.findByType<PublishingExtension>()?.apply {
            repositories {
                maven {
                    name = "mavenTarget"
                    url = uri(System.getenv("MAVEN_REPO_URL")?.takeIf { it.isNotBlank() }
                        ?: "https://maven.cloudsmith.io/eulerstream/maven/")
                    credentials {
                        username = System.getenv("MAVEN_USERNAME")
                        password = System.getenv("MAVEN_PASSWORD")
                    }
                }
            }
        }
    }
}
