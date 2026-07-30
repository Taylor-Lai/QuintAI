package com.quaintai.huiwenrongtong.ui.screens

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.google.gson.GsonBuilder
import com.google.gson.JsonArray
import com.google.gson.JsonObject
import com.quaintai.huiwenrongtong.data.SimpleXlsxWriter
import com.quaintai.huiwenrongtong.data.local.LocalTemplate
import com.quaintai.huiwenrongtong.data.local.TemplateStore
import com.quaintai.huiwenrongtong.ui.components.BrandPill
import com.quaintai.huiwenrongtong.ui.theme.BrandCard
import com.quaintai.huiwenrongtong.ui.theme.BrandMuted

@Composable
fun TemplateEditorScreen(onBack: () -> Unit, onSave: (JsonObject) -> Unit) {
    val context = LocalContext.current
    val store = remember { TemplateStore(context) }
    val draft = remember { store.draft() }
    var name by remember { mutableStateOf(draft?.name ?: "未命名模板") }
    var category by remember { mutableStateOf(draft?.category ?: "自定义分类") }
    var scene by remember { mutableStateOf(draft?.scene ?: "在线编辑") }
    var description by remember { mutableStateOf(draft?.description ?: "") }
    var savedMessage by remember { mutableStateOf("") }
    val fields = remember { mutableStateListOf<String>().apply { addAll(draft?.fields?.takeIf { it.isNotEmpty() } ?: listOf("姓名", "日期", "备注")) } }
    val excelLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    ) { uri -> if (uri != null) SimpleXlsxWriter.write(context, uri, fields.filter(String::isNotBlank)) }
    val jsonLauncher = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri ->
        if (uri != null) {
            val payload = mapOf("name" to name, "category" to category, "scene" to scene, "description" to description, "fields" to fields.toList())
            context.contentResolver.openOutputStream(uri, "w")?.use { it.write(GsonBuilder().setPrettyPrinting().create().toJson(payload).toByteArray()) }
        }
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Row(Modifier.fillMaxWidth().statusBarsPadding().padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "返回") }
            Text("在线模板编辑", style = MaterialTheme.typography.titleLarge)
        }
        Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            BrandPill("在线编辑")
            Text("自定义模板并导出", style = MaterialTheme.typography.headlineLarge)
            Text("配置模板名称、业务场景和字段，生成可直接使用的 Excel 或 JSON。", color = BrandMuted)
            Card(colors = CardDefaults.cardColors(containerColor = BrandCard), shape = RoundedCornerShape(18.dp)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("模板基础信息", style = MaterialTheme.typography.titleMedium)
                    OutlinedTextField(name, { name = it }, label = { Text("模板名称") }, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(category, { category = it }, label = { Text("模板分类") }, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(scene, { scene = it }, label = { Text("适用场景") }, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(description, { description = it }, label = { Text("模板描述") }, minLines = 3, modifier = Modifier.fillMaxWidth())
                }
            }
            Card(colors = CardDefaults.cardColors(containerColor = BrandCard), shape = RoundedCornerShape(18.dp)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("字段配置", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                        OutlinedButton(onClick = { fields.add("") }) { Icon(Icons.Outlined.Add, null); Text(" 新增") }
                    }
                    fields.forEachIndexed { index, field ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            OutlinedTextField(
                                field,
                                { fields[index] = it },
                                label = { Text("字段 ${index + 1}") },
                                modifier = Modifier.weight(1f),
                            )
                            IconButton(onClick = { if (fields.size > 1) fields.removeAt(index) }) { Icon(Icons.Outlined.Delete, "删除") }
                        }
                    }
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = { jsonLauncher.launch("$name.json") }, modifier = Modifier.weight(1f)) { Text("下载 JSON") }
                Button(onClick = { excelLauncher.launch("$name.xlsx") }, modifier = Modifier.weight(1f)) { Text("下载 Excel") }
            }
            Button(
                onClick = {
                    val template = LocalTemplate(
                        id = draft?.id ?: "local_${System.currentTimeMillis()}", name = name.trim(), category = category.trim(),
                        scene = scene.trim(), description = description.trim(), fields = fields.map(String::trim).filter(String::isNotBlank),
                    )
                    store.setDraft(template)
                    onSave(JsonObject().apply {
                        addProperty("id", template.id)
                        addProperty("name", template.name)
                        addProperty("category", template.category)
                        addProperty("scene", template.scene)
                        addProperty("description", template.description)
                        addProperty("format", "Excel / 在线表单")
                        add("tags", JsonArray())
                        add("fields", JsonArray().apply { template.fields.forEach { add(it) } })
                    })
                    savedMessage = "模板已提交到团队模板库"
                },
                enabled = name.isNotBlank() && fields.any(String::isNotBlank),
                modifier = Modifier.fillMaxWidth(),
            ) { Text("保存到模板库") }
            if (savedMessage.isNotBlank()) Text(savedMessage, color = MaterialTheme.colorScheme.primary)
            Text("模板预览", style = MaterialTheme.typography.titleLarge)
            Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = BrandCard)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(name, style = MaterialTheme.typography.titleLarge)
                    Text("$category · $scene · ${fields.count(String::isNotBlank)} 个字段", color = BrandMuted)
                    Text(fields.filter(String::isNotBlank).joinToString(" · "), color = BrandMuted)
                }
            }
        }
    }
}
