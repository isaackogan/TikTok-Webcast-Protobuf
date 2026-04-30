@file:JvmName("WebcastBuilders")

package com.isaackogan.webcast

import com.squareup.wire.Message

/**
 * Kotlin DSL helper for building any Wire-generated [Message] via its `Builder`.
 *
 * Usage:
 * ```
 * val response = build(WebcastResponse.Builder()) {
 *     cursor("abc")
 *     fetchInterval(1000)
 * }
 * ```
 *
 * Companion artifacts can layer richer per-type DSL on top; this helper is the
 * minimal hook that proves Kotlin extensions can target the generated Java
 * classes from [tiktok-live-proto](:tiktok-live-proto).
 */
inline fun <M : Message<M, B>, B : Message.Builder<M, B>> build(
    builder: B,
    block: B.() -> Unit,
): M = builder.apply(block).build()
