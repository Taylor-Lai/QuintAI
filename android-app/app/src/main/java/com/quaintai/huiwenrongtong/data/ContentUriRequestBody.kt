package com.quaintai.huiwenrongtong.data

import android.content.ContentResolver
import android.net.Uri
import okhttp3.MediaType
import okhttp3.RequestBody
import okio.BufferedSink
import okio.source

class ContentUriRequestBody(
    private val resolver: ContentResolver,
    private val uri: Uri,
    private val mediaType: MediaType?,
) : RequestBody() {
    override fun contentType(): MediaType? = mediaType

    override fun contentLength(): Long =
        resolver.openAssetFileDescriptor(uri, "r")?.use { it.length } ?: -1L

    override fun writeTo(sink: BufferedSink) {
        val input = resolver.openInputStream(uri)
            ?: error("无法读取所选文件")
        input.source().use { sink.writeAll(it) }
    }
}
