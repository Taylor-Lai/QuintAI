package com.quaintai.huiwenrongtong.ui.screens

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Download
import androidx.compose.material.icons.outlined.EditNote
import androidx.compose.material3.Button
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quaintai.huiwenrongtong.data.SimpleXlsxWriter
import com.quaintai.huiwenrongtong.data.local.LocalTemplate
import com.quaintai.huiwenrongtong.data.local.TemplateStore
import com.google.gson.JsonObject
import com.quaintai.huiwenrongtong.ui.components.BrandPill
import com.quaintai.huiwenrongtong.ui.theme.BrandCard
import com.quaintai.huiwenrongtong.ui.theme.BrandGoldDark
import com.quaintai.huiwenrongtong.ui.theme.BrandMuted

private data class BusinessTemplate(
    val id: String, val name: String, val category: String, val scene: String,
    val fieldCount: Int, val description: String = "", val fields: List<String> = emptyList(), val editable: Boolean = false,
)

private fun remoteTemplates(data: JsonObject?): List<BusinessTemplate> =
    data?.getAsJsonArray("items")?.mapNotNull { element ->
        runCatching {
            val item = element.asJsonObject
            val fields = item.getAsJsonArray("fields")?.mapIndexed { index, field ->
                if (field.isJsonPrimitive) field.asString
                else field.asJsonObject.get("label")?.asString ?: "字段${index + 1}"
            }.orEmpty()
            BusinessTemplate(
                id = item.get("id").asString,
                name = item.get("name").asString,
                category = item.get("category").asString,
                scene = item.get("scene")?.asString.orEmpty(),
                fieldCount = fields.size,
                description = item.get("description")?.asString.orEmpty(),
                fields = fields,
                editable = item.get("editable")?.asBoolean == true,
            )
        }.getOrNull()
    }.orEmpty()

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun TemplateLibraryScreen(data: JsonObject?, onBack: () -> Unit, onEditor: () -> Unit, onUse: () -> Unit, onDelete: (String) -> Unit) {
    val context = LocalContext.current
    val store = remember { TemplateStore(context) }
    var keyword by remember { mutableStateOf("") }
    var deleteTarget by remember { mutableStateOf<BusinessTemplate?>(null) }
    val templates = remember(data) { remoteTemplates(data) }
    val filteredTemplates = templates.filter {
        keyword.isBlank() || listOf(it.name, it.category, it.scene, it.description).any { value -> value.contains(keyword, ignoreCase = true) }
    }
    var pending by remember { mutableStateOf<BusinessTemplate?>(null) }
    val saveLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    ) { uri ->
        val item = pending
        if (uri != null && item != null) SimpleXlsxWriter.write(context, uri, templateFields(item))
        pending = null
    }
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(bottom = 30.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(Modifier.fillMaxWidth().statusBarsPadding().padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "返回") }
                Text("模板库", style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
                IconButton(onClick = { store.setDraft(null); onEditor() }) { Icon(Icons.Outlined.EditNote, "在线编辑") }
            }
        }
        item {
            Column(Modifier.padding(horizontal = 20.dp)) {
                BrandPill("模板库")
                Text("支持预览与 Excel 下载", style = MaterialTheme.typography.headlineLarge, modifier = Modifier.padding(top = 12.dp))
                Text("覆盖行政、人事、财务、供应链、教育、医疗与项目管理场景。", color = BrandMuted)
                Text("${templates.size} 个模板 · ${templates.map { it.category }.distinct().size} 个分类", color = BrandGoldDark, modifier = Modifier.padding(top = 10.dp))
                OutlinedTextField(keyword, { keyword = it }, label = { Text("搜索名称、分类或场景") }, modifier = Modifier.fillMaxWidth().padding(top = 10.dp))
            }
        }
        items(filteredTemplates, key = { it.id }) { item ->
            Card(
                Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = BrandCard),
                shape = RoundedCornerShape(16.dp),
            ) {
                Column(Modifier.padding(17.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(item.name, style = MaterialTheme.typography.titleMedium)
                            Text("${item.category} · ${item.scene}", color = BrandMuted, fontSize = 12.sp)
                        }
                        BrandPill("${item.fieldCount} 项字段")
                    }
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        OutlinedButton(onClick = {
                            store.setDraft(LocalTemplate(item.id.takeIf { item.editable } ?: "builtin_${System.currentTimeMillis()}", item.name, item.category, item.scene, item.description, templateFields(item)))
                            onEditor()
                        }) { Text("编辑") }
                        OutlinedButton(onClick = {
                            store.setActive(LocalTemplate(item.id, item.name, item.category, item.scene, item.description, templateFields(item)))
                            onUse()
                        }) { Text("使用") }
                        Button(onClick = {
                            pending = item
                            saveLauncher.launch("${item.name}.xlsx")
                        }) {
                            Icon(Icons.Outlined.Download, null)
                            Text(" 下载 Excel")
                        }
                        if (item.editable) OutlinedButton(onClick = { deleteTarget = item }) { Text("删除", color = MaterialTheme.colorScheme.error) }
                    }
                }
            }
        }
    }
    deleteTarget?.let { item ->
        AlertDialog(
            onDismissRequest = { deleteTarget = null },
            title = { Text("删除自定义模板") },
            text = { Text("确定删除“${item.name}”吗？") },
            dismissButton = { TextButton(onClick = { deleteTarget = null }) { Text("取消") } },
            confirmButton = { Button(onClick = { onDelete(item.id); deleteTarget = null }) { Text("删除") } },
        )
    }
}

private fun templateFields(item: BusinessTemplate): List<String> {
    if (item.fields.isNotEmpty()) return item.fields
    val common = when (item.name) {
        "合同信息登记表" -> listOf("合同编号", "合同名称", "甲方", "乙方", "签署日期", "生效日期", "到期日期", "合同金额", "负责人", "状态", "归档编号", "备注")
        "员工入职信息表" -> listOf("姓名", "性别", "手机号", "邮箱", "部门", "岗位", "直属经理", "入职日期", "办公地点", "试用期")
        "费用报销申请表" -> listOf("申请人", "部门", "报销日期", "费用类型", "金额", "事由", "发票号码", "收款账户", "审批人", "备注")
        else -> emptyList()
    }
    return if (common.size >= item.fieldCount) common.take(item.fieldCount)
    else common + (common.size + 1..item.fieldCount).map { "字段$it" }
}
