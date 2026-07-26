package com.zhihuiwenshu.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ArrowForward
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.DataObject
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.TableChart
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.zhihuiwenshu.app.data.remote.FeatureKind
import com.zhihuiwenshu.app.data.remote.TaskDto
import com.zhihuiwenshu.app.ui.components.BrandHeader
import com.zhihuiwenshu.app.ui.components.BrandHeroBrush
import com.zhihuiwenshu.app.ui.components.BrandPill
import com.zhihuiwenshu.app.ui.components.BrandSectionTitle
import com.zhihuiwenshu.app.ui.theme.BrandCard
import com.zhihuiwenshu.app.ui.theme.BrandGold
import com.zhihuiwenshu.app.ui.theme.BrandGoldDark
import com.zhihuiwenshu.app.ui.theme.BrandInk
import com.zhihuiwenshu.app.ui.theme.BrandMuted

@Composable
fun HomeScreen(
    username: String,
    tasks: List<TaskDto>,
    onFeatureSelected: (FeatureKind) -> Unit,
    onTaskSelected: (TaskDto) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(bottom = 28.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        item {
            BrandHeader {
                Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
                    Text(
                        username.take(1).uppercase().ifBlank { "U" },
                        color = BrandGoldDark,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 13.dp, vertical = 9.dp),
                    )
                }
            }
        }
        item {
            Column(Modifier.padding(horizontal = 20.dp)) {
                Text("让复杂文档处理", style = MaterialTheme.typography.displaySmall)
                Text("变得简单高效", style = MaterialTheme.typography.displaySmall, color = BrandGoldDark)
                Text(
                    "从识别、分析到处理，在手机上完成文档全流程任务。",
                    color = BrandMuted,
                    lineHeight = 23.sp,
                    modifier = Modifier.padding(top = 10.dp),
                )
            }
        }
        item { HeroFeature(onFeatureSelected) }
        item {
            Column(Modifier.padding(horizontal = 20.dp)) {
                BrandSectionTitle("智能处理能力")
                Spacer(Modifier.height(12.dp))
                FeatureCard(FeatureKind.EDIT, Icons.Outlined.AutoAwesome, "智能文档交互", onFeatureSelected)
                Spacer(Modifier.height(12.dp))
                FeatureCard(FeatureKind.EXTRACT, Icons.Outlined.DataObject, "信息提取引擎", onFeatureSelected)
                Spacer(Modifier.height(12.dp))
                FeatureCard(FeatureKind.TABLE, Icons.Outlined.TableChart, "表格智能处理", onFeatureSelected)
            }
        }
        if (tasks.isNotEmpty()) {
            item {
                Column(Modifier.padding(horizontal = 20.dp)) {
                    BrandSectionTitle("最近任务") { BrandPill("共 ${tasks.size} 项") }
                }
            }
            items(tasks.take(3), key = { it.id }) { task ->
                CompactTask(task, onTaskSelected)
            }
        }
        item {
            Text(
                "© 2026 智汇文枢 · 智能文档处理平台",
                color = BrandMuted,
                fontSize = 12.sp,
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center,
            )
        }
    }
}

@Composable
private fun HeroFeature(onFeatureSelected: (FeatureKind) -> Unit) {
    Box(
        modifier = Modifier.padding(horizontal = 20.dp).fillMaxWidth().height(238.dp)
            .clip(RoundedCornerShape(24.dp)).background(BrandHeroBrush)
            .clickable { onFeatureSelected(FeatureKind.EXTRACT) },
    ) {
        Icon(
            Icons.Outlined.Description,
            null,
            tint = Color.White.copy(alpha = .10f),
            modifier = Modifier.size(190.dp).align(Alignment.BottomEnd).padding(12.dp),
        )
        Column(
            modifier = Modifier.fillMaxSize().padding(24.dp),
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            BrandPill("信息提取引擎")
            Column {
                Text("非结构化文档", color = Color.White, style = MaterialTheme.typography.headlineMedium)
                Text("信息提取", color = Color.White, style = MaterialTheme.typography.headlineMedium)
                Text("针对合同、报告、说明书等文件提取关键字段", color = Color.White.copy(alpha = .82f), fontSize = 13.sp)
                Row(
                    modifier = Modifier.padding(top = 14.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text("点击立即体验", color = BrandGold, fontWeight = FontWeight.Bold)
                    Icon(Icons.Outlined.ArrowForward, null, tint = BrandGold, modifier = Modifier.size(18.dp))
                }
            }
        }
    }
}

@Composable
private fun FeatureCard(kind: FeatureKind, icon: ImageVector, badge: String, onClick: (FeatureKind) -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable { onClick(kind) },
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = BrandCard),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Row(Modifier.padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
            Surface(shape = RoundedCornerShape(14.dp), color = MaterialTheme.colorScheme.primaryContainer) {
                Icon(icon, null, Modifier.padding(13.dp), tint = BrandGoldDark)
            }
            Column(Modifier.weight(1f).padding(horizontal = 14.dp)) {
                Text(badge, color = BrandGoldDark, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                Text(kind.title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 3.dp))
                Text(kind.description, color = BrandMuted, fontSize = 12.sp, maxLines = 2)
            }
            Icon(Icons.Outlined.ArrowForward, null, tint = BrandGoldDark)
        }
    }
}

@Composable
private fun CompactTask(task: TaskDto, onClick: (TaskDto) -> Unit) {
    Card(
        modifier = Modifier.padding(horizontal = 20.dp).fillMaxWidth().clickable { onClick(task) },
        colors = CardDefaults.cardColors(containerColor = BrandCard),
        shape = RoundedCornerShape(16.dp),
    ) {
        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier.size(42.dp).clip(RoundedCornerShape(12.dp))
                    .background(MaterialTheme.colorScheme.primaryContainer),
                contentAlignment = Alignment.Center,
            ) { Icon(Icons.Outlined.Description, null, tint = BrandGoldDark) }
            Column(Modifier.weight(1f).padding(horizontal = 12.dp)) {
                Text(task.kind.displayKind(), fontWeight = FontWeight.SemiBold)
                Text(
                    task.filename ?: task.stage,
                    color = BrandMuted,
                    fontSize = 12.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            BrandPill(task.status.displayStatus())
        }
    }
}

internal fun String.displayKind() = when (this) {
    "document_edit" -> "文档智能操作交互"
    "document_extract" -> "非结构化文档信息提取"
    "table_fill" -> "表格自定义数据填写"
    else -> this
}

internal fun String.displayStatus() = when (this) {
    "queued" -> "等待处理"
    "running" -> "处理中"
    "succeeded" -> "已完成"
    "failed" -> "处理失败"
    "cancelled" -> "已取消"
    else -> this
}
