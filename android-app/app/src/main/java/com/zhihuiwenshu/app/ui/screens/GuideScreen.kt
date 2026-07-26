package com.zhihuiwenshu.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.zhihuiwenshu.app.ui.components.BrandPill
import com.zhihuiwenshu.app.ui.theme.BrandCard
import com.zhihuiwenshu.app.ui.theme.BrandGoldDark
import com.zhihuiwenshu.app.ui.theme.BrandMuted

@Composable
fun GuideScreen(onBack: () -> Unit) {
    val steps = listOf(
        "01" to ("选择能力" to "按目标选择文档编辑、信息提取或表格填写。"),
        "02" to ("上传材料" to "从手机文件中选择待处理文档或业务模板。"),
        "03" to ("描述要求" to "用自然语言填写字段、编辑要求或表格规则。"),
        "04" to ("跟踪执行" to "在任务中心查看实时进度和完整处理轨迹。"),
        "05" to ("复核交付" to "核对结构化结果，必要时人工复核并保存文件。"),
    )
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Row(Modifier.fillMaxWidth().statusBarsPadding().padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "返回") }
            Text("上手指南", style = MaterialTheme.typography.titleLarge)
        }
        Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            BrandPill("GETTING STARTED")
            Text("五步完成文档处理", style = MaterialTheme.typography.headlineLarge)
            Text("从材料进入到业务交付，每一步都有状态、结果和记录。", color = BrandMuted)
            steps.forEach { (number, content) ->
                Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = BrandCard), shape = RoundedCornerShape(16.dp)) {
                    Row(Modifier.padding(18.dp), verticalAlignment = Alignment.Top) {
                        Text(number, color = BrandGoldDark, style = MaterialTheme.typography.titleLarge)
                        Column(Modifier.padding(start = 16.dp)) {
                            Text(content.first, style = MaterialTheme.typography.titleMedium)
                            Text(content.second, color = BrandMuted, modifier = Modifier.padding(top = 5.dp))
                        }
                    }
                }
            }
        }
    }
}
