import org.gradle.plugins.signing.SigningExtension

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
    apply(plugin = "signing")

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

    // Maven Central requires every artifact to be GPG-signed. The key is supplied in CI as an
    // ASCII-armored secret (MAVEN_GPG_PRIVATE_KEY) plus its passphrase; when absent (local dev)
    // signing is skipped so ordinary builds still work. Upload itself is handled by the nmcp
    // aggregation plugin via `./gradlew publishAggregationToCentralPortal`.
    afterEvaluate {
        val publishing = extensions.findByType<PublishingExtension>() ?: return@afterEvaluate
        extensions.configure<SigningExtension> {
            val signingKey = System.getenv("MAVEN_GPG_PRIVATE_KEY")
            val signingPassword = System.getenv("MAVEN_GPG_PASSPHRASE")
            if (!signingKey.isNullOrBlank()) {
                useInMemoryPgpKeys(signingKey, signingPassword)
                sign(publishing.publications)
            }
        }
    }
}
