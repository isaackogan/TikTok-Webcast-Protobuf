plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "0.8.0"
    // Applies com.gradleup.nmcp to every project and com.gradleup.nmcp.aggregation to the root,
    // wiring up `publishAggregationToCentralPortal` to upload all modules to Maven Central.
    id("com.gradleup.nmcp.settings") version "1.4.4"
}

rootProject.name = "tiktok-live-proto-jvm"

nmcpSettings {
    centralPortal {
        username = System.getenv("MAVEN_CENTRAL_USERNAME")
        password = System.getenv("MAVEN_CENTRAL_PASSWORD")
        // AUTOMATIC publishes as soon as Central's validation passes.
        // Switch to "USER_MANAGED" to require a manual "Publish" click in the Central Portal UI.
        publishingType = "AUTOMATIC"
    }
}

include(":tiktok-live-proto")
include(":tiktok-live-proto-kotlin")
