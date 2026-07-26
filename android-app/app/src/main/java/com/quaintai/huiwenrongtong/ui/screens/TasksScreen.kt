package com.quaintai.huiwenrongtong.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quaintai.huiwenrongtong.data.remote.TaskDto
import com.quaintai.huiwenrongtong.ui.components.BrandHeader
import com.quaintai.huiwenrongtong.ui.components.BrandPill
import com.quaintai.huiwenrongtong.ui.theme.BrandCard
import com.quaintai.huiwenrongtong.ui.theme.BrandGoldDark
import com.quaintai.huiwenrongtong.ui.theme.BrandMuted

@Composable
fun TasksScreen(
    tasks: List<TaskDto>,
    loading: Boolean,
    onRefresh: () -> Unit,
    onTaskSelected: (TaskDto) -> Unit,
) {
    Column(Modifier.fillMaxSize()) {
        BrandHeader {
            IconButton(onClick = onRefresh, enabled = !loading) {
                if (loading) CircularProgressIndicator(Modifier.size(22.dp), strokeWidth = 2.dp)
                else Icon(Icons.Outlined.Refresh, "刷新")
            }
        }
        Column(Modifier.padding(horizontal = 20.dp)) {
            Text("任务中心", style = MaterialTheme.typography.headlineLarge)
            Text("每一次处理都有进度、有结果、可追溯", color = BrandMuted, modifier = Modifier.padding(top = 4.dp))
            Row(
                modifier = Modifier.fillMaxWidth().padding(vertical = 18.dp),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                StatCard("全部", tasks.size, Modifier.weight(1f))
                StatCard("处理中", tasks.count { it.status in setOf("queued", "running") }, Modifier.weight(1f))
                StatCard("已完成", tasks.count { it.status == "succeeded" }, Modifier.weight(1f))
            }
        }

        if (tasks.isEmpty()) {
            Column(
                modifier = Modifier.fillMaxSize(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Icon(Icons.Outlined.Description, null, tint = BrandGoldDark, modifier = Modifier.size(44.dp))
                Text("还没有任务", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 12.dp))
                Text("从首页选择一项能力开始", color = BrandMuted)
            }
        } else {
            LazyColumn(
                contentPadding = PaddingValues(horizontal = 20.dp, vertical = 2.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                items(tasks, key = { it.id }) { task -> TaskCard(task) { onTaskSelected(task) } }
            }
        }
    }
}

@Composable
private fun StatCard(label: String, value: Int, modifier: Modifier) {
    Card(modifier, shape = RoundedCornerShape(14.dp), colors = CardDefaults.cardColors(containerColor = BrandCard)) {
        Column(Modifier.padding(13.dp)) {
            Text(value.toString(), style = MaterialTheme.typography.titleLarge, color = BrandGoldDark)
            Text(label, color = BrandMuted, fontSize = 12.sp)
        }
    }
}

@Composable
private fun TaskCard(task: TaskDto, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = BrandCard),
    ) {
        Column(Modifier.padding(17.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(task.kind.displayKind(), style = MaterialTheme.typography.titleMedium)
                    Text(
                        task.filename ?: task.createdAt.replace("T", " ").take(16),
                        color = BrandMuted,
                        fontSize = 12.sp,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                BrandPill(task.status.displayStatus())
                Icon(Icons.Outlined.ChevronRight, null, tint = BrandMuted)
            }
            if (task.status in setOf("queued", "running")) {
                LinearProgressIndicator(
                    progress = { task.progress.coerceIn(0, 100) / 100f },
                    modifier = Modifier.fillMaxWidth(),
                )
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(task.stage.ifBlank { "等待服务端处理" }, color = BrandMuted, fontSize = 12.sp)
                    Text("${task.progress}%", color = BrandGoldDark, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                }
            } else {
                Text(
                    if (task.status == "succeeded") "点击查看处理结果与质量信息" else task.error?.message ?: task.stage,
                    color = BrandMuted,
                    fontSize = 12.sp,
                    maxLines = 2,
                )
            }
        }
    }
}
