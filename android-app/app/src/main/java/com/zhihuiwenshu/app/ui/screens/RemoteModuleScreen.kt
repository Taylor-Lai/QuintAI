package com.zhihuiwenshu.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.gson.JsonElement
import com.google.gson.JsonObject
import com.zhihuiwenshu.app.data.remote.PlatformModule
import com.zhihuiwenshu.app.ui.components.BrandPill
import com.zhihuiwenshu.app.ui.theme.BrandCard
import com.zhihuiwenshu.app.ui.theme.BrandGoldDark
import com.zhihuiwenshu.app.ui.theme.BrandMuted

@Composable
fun RemoteModuleScreen(
    module: PlatformModule,
    data: JsonObject?,
    loading: Boolean,
    onBack: () -> Unit,
    onRefresh: () -> Unit,
) {
    val metrics = data?.metricEntries().orEmpty()
    val records = data?.recordEntries().orEmpty()
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(bottom = 30.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(
                Modifier.fillMaxWidth().statusBarsPadding().padding(horizontal = 8.dp, vertical = 6.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "返回") }
                Text(module.title, style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
                IconButton(onClick = onRefresh, enabled = !loading) {
                    if (loading) CircularProgressIndicator(Modifier.size(21.dp), strokeWidth = 2.dp)
                    else Icon(Icons.Outlined.Refresh, "刷新")
                }
            }
        }
        item {
            Column(Modifier.padding(horizontal = 20.dp)) {
                BrandPill("QUINTAI WORKSPACE")
                Text(module.title, style = MaterialTheme.typography.headlineLarge, modifier = Modifier.padding(top = 12.dp))
                Text(module.description, color = BrandMuted, modifier = Modifier.padding(top = 4.dp))
            }
        }
        if (loading && data == null) {
            item {
                Column(Modifier.fillMaxWidth().padding(50.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator()
                    Text("正在加载…", color = BrandMuted, modifier = Modifier.padding(top = 12.dp))
                }
            }
        } else if (data == null) {
            item { EmptyModuleCard("暂时无法读取数据，请点击右上角刷新") }
        } else {
            if (metrics.isNotEmpty()) {
                item { Text("数据概览", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(horizontal = 20.dp, vertical = 6.dp)) }
                items(metrics) { (label, value) -> MetricRow(label, value) }
            }
            if (records.isNotEmpty()) {
                item { Text("内容列表", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(horizontal = 20.dp, vertical = 6.dp)) }
                items(records.take(100)) { record -> RecordCard(record) }
            } else if (metrics.isEmpty()) {
                item { EmptyModuleCard("当前模块暂无数据") }
            }
        }
    }
}

@Composable
private fun MetricRow(label: String, value: String) {
    Card(
        Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = BrandCard),
        shape = RoundedCornerShape(14.dp),
    ) {
        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(label.displayLabel(), color = BrandMuted, modifier = Modifier.weight(1f))
            Text(value, color = BrandGoldDark, fontWeight = FontWeight.Bold, fontSize = 18.sp)
        }
    }
}

@Composable
private fun RecordCard(record: JsonObject) {
    val title = record.stringValue("filename", "name", "username", "title", "kind", "id")
    val subtitle = record.stringValue("description", "category", "email", "stage", "status", "role")
    Card(
        Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = BrandCard),
        shape = RoundedCornerShape(14.dp),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(title.ifBlank { "记录" }, style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
            if (subtitle.isNotBlank()) Text(subtitle, color = BrandMuted, fontSize = 13.sp, modifier = Modifier.padding(top = 5.dp))
            val detail = record.entrySet().asSequence()
                .filterNot { it.key in setOf("id", "filename", "name", "username", "title", "description") }
                .filter { it.value.isJsonPrimitive }
                .take(4)
                .joinToString(" · ") { "${it.key.displayLabel()}: ${it.value.asString}" }
            if (detail.isNotBlank()) Text(detail, color = BrandMuted, fontSize = 11.sp, modifier = Modifier.padding(top = 8.dp), maxLines = 3)
        }
    }
}

@Composable
private fun EmptyModuleCard(text: String) {
    Card(
        Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = BrandCard),
    ) { Text(text, color = BrandMuted, modifier = Modifier.padding(28.dp)) }
}

private fun JsonObject.metricEntries(): List<Pair<String, String>> = entrySet().asSequence()
    .filter { it.value.isJsonPrimitive }
    .map { it.key to it.value.asString }
    .toList()

private fun JsonObject.recordEntries(): List<JsonObject> {
    val arrays = entrySet().mapNotNull { (_, value) -> value.takeIf { it.isJsonArray }?.asJsonArray }
    return arrays.flatMap { array -> array.mapNotNull { it.takeIf(JsonElement::isJsonObject)?.asJsonObject } }
}

private fun JsonObject.stringValue(vararg keys: String): String = keys.firstNotNullOfOrNull { key ->
    get(key)?.takeIf { it.isJsonPrimitive }?.asString?.takeIf(String::isNotBlank)
}.orEmpty()

private fun String.displayLabel(): String = when (this) {
    "documents_total", "total" -> "文档总量"
    "pending_reviews" -> "待复核"
    "active_tasks" -> "运行中任务"
    "active_workflows" -> "启用工作流"
    "status" -> "状态"
    "role" -> "角色"
    "created_at" -> "创建时间"
    "category" -> "分类"
    "progress" -> "进度"
    else -> replace("_", " ")
}
