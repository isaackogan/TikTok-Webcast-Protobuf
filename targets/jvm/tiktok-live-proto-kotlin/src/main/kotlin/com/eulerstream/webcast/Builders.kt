@file:JvmName("WebcastBuilders")

package com.eulerstream.webcast

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
 * Layers a minimal building DSL on top of the Wire-generated Kotlin message
 * classes shipped by this module.
 */
inline fun <M : Message<M, B>, B : Message.Builder<M, B>> build(
    builder: B,
    block: B.() -> Unit,
): M = builder.apply(block).build()
