package com.zhihuiwenshu.app.ui.screens

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.CloudDownload
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.gson.JsonElement
import com.zhihuiwenshu.app.data.remote.TaskDto
import com.zhihuiwenshu.app.ui.components.BrandPill
import com.zhihuiwenshu.app.ui.theme.BrandCard
import com.zhihuiwenshu.app.ui.theme.BrandGoldDark
import com.zhihuiwenshu.app.ui.theme.BrandMuted
import com.zhihuiwenshu.app.ui.theme.BrandSand

@Composable
fun TaskDetailScreen(
    task: TaskDto,
    onBack: () -> Unit,
    onCancel: (String) -> Unit,
    onRetry: (String) -> Unit,
    onDownload: (String, Uri) -> Unit,
) {
    var confirmCancel by remember { mutableStateOf(false) }
    val saveLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/octet-stream")
    ) { uri -> if (uri != null) onDownload(task.id, uri) }
    val fields = task.extractedFields()

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(bottom = 30.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Row(
                modifier = Modifier.fillMaxWidth().statusBarsPadding().padding(horizontal = 8.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "返回") }
                Text("任务详情", style = MaterialTheme.typography.titleLarge)
            }
        }
        item {
            Card(
                modifier = Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = BrandCard),
                shape = RoundedCornerShape(20.dp),
            ) {
                Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            Modifier.size(48.dp).background(BrandSand, CircleShape),
                            contentAlignment = Alignment.Center,
                        ) {
                            Icon(Icons.Outlined.CheckCircle, null, tint = BrandGoldDark)
                        }
                        Column(Modifier.weight(1f).padding(horizontal = 13.dp)) {
                            Text(task.kind.displayKind(), style = MaterialTheme.typography.titleLarge)
                            Text(task.filename ?: "文档处理任务", color = BrandMuted, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                        BrandPill(task.status.displayStatus())
                    }
                    if (task.status in setOf("queued", "running")) {
                        LinearProgressIndicator(
                            progress = { task.progress.coerceIn(0, 100) / 100f },
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                    Text(task.stage, color = BrandMuted, fontSize = 13.sp)
                    Text("创建时间  ${task.createdAt.prettyTime()}", color = BrandMuted, fontSize = 12.sp)
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        when (task.status) {
                            "queued", "running" -> OutlinedButton(onClick = { confirmCancel = true }) { Text("取消任务") }
                            "failed", "cancelled" -> Button(onClick = { onRetry(task.id) }) {
                                Icon(Icons.Outlined.Refresh, null, Modifier.size(18.dp))
                                Text(" 重新执行")
                            }
                        }
                        if (task.status == "succeeded" && task.hasFile) {
                            Button(onClick = { saveLauncher.launch(task.filename ?: "智汇文枢处理结果") }) {
                                Icon(Icons.Outlined.CloudDownload, null, Modifier.size(18.dp))
                                Text(" 保存结果")
                            }
                        }
                    }
                }
            }
        }

        if (fields.isNotEmpty()) {
            item { SectionHeading("结构化结果", "已识别 ${fields.size} 个字段") }
            items(fields, key = { it.first }) { (name, value) -> ResultField(name, value) }
        } else if (task.status == "succeeded") {
            item {
                Card(
                    modifier = Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = BrandCard),
                ) {
                    Column(Modifier.padding(18.dp)) {
                        Text("处理已完成", style = MaterialTheme.typography.titleMedium)
                        Text(
                            if (task.hasFile) "结果已经生成，可点击上方“保存结果”下载到手机。" else "本次任务没有可展示的结构化字段。",
                            color = BrandMuted,
                            modifier = Modifier.padding(top = 6.dp),
                        )
                    }
                }
            }
        }

        task.qualityReport?.takeIf { it.entrySet().isNotEmpty() }?.let { quality ->
            item { SectionHeading("质量报告", "自动校验结果") }
            items(quality.entrySet().toList(), key = { it.key }) { entry -> ResultField(entry.key, entry.value.displayValue()) }
        }
        task.evidenceSummary?.takeIf { it.entrySet().isNotEmpty() }?.let { evidence ->
            item { SectionHeading("证据摘要", "来源可追溯") }
            items(evidence.entrySet().toList(), key = { it.key }) { entry -> ResultField(entry.key, entry.value.displayValue()) }
        }

        task.error?.message?.let { error ->
            item {
                Card(
                    modifier = Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFFFEEEE)),
                ) { Text(error, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(18.dp)) }
            }
        }

        if (task.events.orEmpty().isNotEmpty()) {
            item { SectionHeading("处理轨迹", "全过程可追溯") }
            items(task.events.orEmpty()) { event ->
                Row(Modifier.padding(horizontal = 24.dp), verticalAlignment = Alignment.Top) {
                    Box(Modifier.padding(top = 5.dp).size(9.dp).background(BrandGoldDark, CircleShape))
                    Column(Modifier.padding(start = 12.dp)) {
                        Text(event.message.ifBlank { event.stage }, fontWeight = FontWeight.SemiBold)
                        Text(event.createdAt.prettyTime(), color = BrandMuted, fontSize = 12.sp)
                    }
                }
            }
        }
    }
    if (confirmCancel) {
        AlertDialog(
            onDismissRequest = { confirmCancel = false },
            title = { Text("取消任务") },
            text = { Text("确定取消当前任务吗？已完成的处理步骤不会继续执行。") },
            dismissButton = { TextButton(onClick = { confirmCancel = false }) { Text("继续等待") } },
            confirmButton = { Button(onClick = { confirmCancel = false; onCancel(task.id) }) { Text("取消任务") } },
        )
    }
}

@Composable
private fun SectionHeading(title: String, subtitle: String) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 4.dp),
        verticalAlignment = Alignment.Bottom,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(title, style = MaterialTheme.typography.titleLarge)
        Text(subtitle, color = BrandMuted, fontSize = 12.sp)
    }
}

@Composable
private fun ResultField(name: String, value: String) {
    Card(
        modifier = Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = BrandCard),
        shape = RoundedCornerShape(14.dp),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(name.displayFieldName(), color = BrandGoldDark, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(5.dp))
            Text(value, fontSize = 16.sp, lineHeight = 23.sp)
        }
    }
}

private fun TaskDto.extractedFields(): List<Pair<String, String>> {
    val data = result?.getAsJsonObject("extracted_data") ?: return emptyList()
    return data.entrySet().asSequence()
        .filterNot { it.key == "_meta" || it.value.isJsonNull }
        .map { it.key to it.value.displayValue() }
        .toList()
}

private fun JsonElement.displayValue(): String = when {
    isJsonPrimitive -> asJsonPrimitive.let { if (it.isString) it.asString else it.toString() }
    isJsonArray -> asJsonArray.joinToString("、") { it.displayValue() }
    else -> toString()
}

private fun String.prettyTime(): String = replace("T", " ").take(16)

private fun String.displayFieldName(): String = when (lowercase()) {
    "name" -> "姓名"
    "date" -> "日期"
    "department" -> "部门"
    "role", "position" -> "岗位"
    "manager" -> "直属经理"
    "location" -> "办公地点"
    "probation" -> "试用期"
    else -> this
}
