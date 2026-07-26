package com.quaintai.huiwenrongtong.ui.screens

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
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
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.gson.JsonArray
import com.google.gson.JsonElement
import com.google.gson.JsonObject
import com.quaintai.huiwenrongtong.data.remote.PlatformModule
import com.quaintai.huiwenrongtong.ui.components.BrandPill
import com.quaintai.huiwenrongtong.ui.theme.BrandCard
import com.quaintai.huiwenrongtong.ui.theme.BrandGoldDark
import com.quaintai.huiwenrongtong.ui.theme.BrandMuted

@Composable
private fun ModuleTopBar(title: String, loading: Boolean, onBack: () -> Unit, onRefresh: () -> Unit) {
    Row(Modifier.fillMaxWidth().statusBarsPadding().padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
        IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "返回") }
        Text(title, style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
        IconButton(onClick = onRefresh, enabled = !loading) {
            if (loading) CircularProgressIndicator(Modifier.padding(10.dp), strokeWidth = 2.dp)
            else Icon(Icons.Outlined.Refresh, "刷新")
        }
    }
}

@Composable
fun DocumentLibraryScreen(
    data: JsonObject?, loading: Boolean, onBack: () -> Unit, onRefresh: () -> Unit,
    onUpload: (List<Uri>, String, String) -> Unit, onDelete: (String) -> Unit,
    onDownload: (String, Uri) -> Unit,
    onArchive: (String, Boolean) -> Unit,
    versions: Map<String, JsonObject>, onLoadVersions: (String) -> Unit,
    onCreateVersion: (String, String) -> Unit,
    workflowData: JsonObject?, onRunWorkflow: (String, String) -> Unit,
) {
    var category by remember { mutableStateOf("未分类") }
    var tags by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf<List<Uri>>(emptyList()) }
    var downloadTarget by remember { mutableStateOf<Pair<String, String>?>(null) }
    var versionDocumentId by remember { mutableStateOf("") }
    var versionNote by remember { mutableStateOf("人工保存版本") }
    var confirmation by remember { mutableStateOf<PendingConfirmation?>(null) }
    var runDocumentId by remember { mutableStateOf("") }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { selected = it }
    val saver = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/octet-stream")) { uri ->
        val target = downloadTarget
        if (uri != null && target != null) onDownload(target.first, uri)
        downloadTarget = null
    }
    val records = data.items()
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 30.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { ModuleTopBar("文档库", loading, onBack, onRefresh) }
        item {
            Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                BrandPill("DOCUMENT LIBRARY")
                Text("统一管理业务材料", style = MaterialTheme.typography.headlineLarge)
                Text("支持批量导入、分类、下载和归档。", color = BrandMuted)
                OutlinedTextField(category, { category = it }, label = { Text("分类") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(tags, { tags = it }, label = { Text("标签（逗号分隔）") }, modifier = Modifier.fillMaxWidth())
                OutlinedButton(onClick = { picker.launch(arrayOf("*/*")) }, modifier = Modifier.fillMaxWidth()) {
                    Text(if (selected.isEmpty()) "选择文件" else "已选择 ${selected.size} 个文件")
                }
                Button(
                    onClick = { onUpload(selected, category, tags); selected = emptyList() },
                    enabled = selected.isNotEmpty() && !loading,
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("导入文档") }
            }
        }
        item { Text("全部文档（${records.size}）", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(horizontal = 20.dp, vertical = 8.dp)) }
        items(records, key = { it.str("id") }) { item ->
            PlatformRecordCard(
                title = item.str("filename"),
                subtitle = "${item.str("category")} · ${item.str("file_type").uppercase()} · ${item.str("status")}",
            ) {
                OutlinedButton(onClick = { downloadTarget = item.str("id") to item.str("filename"); saver.launch(item.str("filename")) }) {
                    Icon(Icons.Outlined.Download, null); Text(" 下载")
                }
                OutlinedButton(onClick = { onArchive(item.str("id"), item.str("status") != "archived") }) {
                    Text(if (item.str("status") == "archived") "恢复" else "归档")
                }
                OutlinedButton(onClick = { versionDocumentId = item.str("id"); onLoadVersions(item.str("id")) }) { Text("版本") }
                if (item.str("status") != "archived") OutlinedButton(onClick = { runDocumentId = item.str("id") }) { Text("运行流程") }
                OutlinedButton(onClick = {
                    confirmation = PendingConfirmation("删除文档", "确定删除“${item.str("filename")}”吗？删除后无法恢复。") { onDelete(item.str("id")) }
                }) { Text("删除", color = MaterialTheme.colorScheme.error) }
            }
            if (runDocumentId == item.str("id")) {
                val activeWorkflows = workflowData.items().filter { it.str("status") == "active" }
                Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("选择要运行的工作流", style = MaterialTheme.typography.titleMedium)
                    if (activeWorkflows.isEmpty()) Text("暂无已启用工作流，请先到工作流中心启用。", color = BrandMuted)
                    activeWorkflows.forEach { workflow ->
                        Button(onClick = { onRunWorkflow(workflow.str("id"), item.str("id")); runDocumentId = "" }, modifier = Modifier.fillMaxWidth()) { Text(workflow.str("name")) }
                    }
                }
            }
            if (versionDocumentId == item.str("id")) {
                val history = versions[item.str("id")].items()
                Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(versionNote, { versionNote = it }, label = { Text("版本说明") }, modifier = Modifier.fillMaxWidth())
                    Button(onClick = { onCreateVersion(item.str("id"), versionNote) }, enabled = !loading, modifier = Modifier.fillMaxWidth()) { Text("保存当前版本") }
                    history.forEach { version -> Text("v${version.str("version")} · ${version.str("note")} · ${version.str("created_at")}", color = BrandMuted, fontSize = 12.sp) }
                }
            }
        }
    }
    ConfirmationDialog(confirmation) { confirmation = null }
}

@Composable
fun ReviewCenterScreen(
    data: JsonObject?, detail: JsonObject?, comments: JsonObject?, loading: Boolean, onBack: () -> Unit, onRefresh: () -> Unit,
    onSelect: (String) -> Unit, onAction: (String, JsonArray, String, String) -> Unit, onAutoFix: (String) -> Unit,
    onComment: (String, String) -> Unit, onResolveComment: (String, String) -> Unit,
) {
    val reviews = data.items()
    var selectedId by remember { mutableStateOf("") }
    var editableFields by remember { mutableStateOf(JsonArray()) }
    var note by remember { mutableStateOf("") }
    var commentText by remember { mutableStateOf("") }
    LaunchedEffect(detail?.toString()) {
        if (detail != null) {
            selectedId = detail.str("id")
            editableFields = detail.array("fields").deepCopy()
            note = detail.str("note")
        }
    }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 30.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { ModuleTopBar("人工复核", loading, onBack, onRefresh) }
        item {
            Column(Modifier.padding(horizontal = 20.dp)) {
                BrandPill("HUMAN REVIEW")
                Text("核验字段、质量与证据", style = MaterialTheme.typography.headlineLarge, modifier = Modifier.padding(top = 10.dp))
                Text("对机器提取结果进行确认、修复、通过或驳回。", color = BrandMuted)
            }
        }
        if (reviews.isEmpty()) item { EmptyWorkspaceCard("当前没有待复核任务") }
        items(reviews, key = { it.str("id") }) { review ->
            PlatformRecordCard(review.str("title"), "${review.str("status")} · 优先级 ${review.str("priority")} · ${review.array("fields").size()} 个字段") {
                Button(onClick = { selectedId = review.str("id"); onSelect(selectedId) }) { Text(if (selectedId == review.str("id")) "正在复核" else "打开复核") }
            }
        }
        if (detail != null && detail.str("id") == selectedId) {
            item {
                Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(detail.str("title"), style = MaterialTheme.typography.titleLarge)
                    Text("校验问题 ${detail.array("validation_results").size()} 项", color = BrandMuted)
                    editableFields.forEachIndexed { index, element ->
                        if (element.isJsonObject) {
                            val field = element.asJsonObject
                            OutlinedTextField(
                                value = field.str("value"),
                                onValueChange = { value ->
                                    editableFields = editableFields.deepCopy().apply { get(index).asJsonObject.addProperty("value", value) }
                                },
                                label = { Text(field.str("name").ifBlank { "字段 ${index + 1}" }) },
                                supportingText = { Text("置信度 ${field.str("confidence")} · ${field.str("evidence")}", maxLines = 2) },
                                modifier = Modifier.fillMaxWidth(),
                            )
                        }
                    }
                    OutlinedTextField(note, { note = it }, label = { Text("复核备注") }, modifier = Modifier.fillMaxWidth())
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(onClick = { onAutoFix(selectedId); onSelect(selectedId) }) { Text("自动修复") }
                        OutlinedButton(onClick = { onAction(selectedId, editableFields, note, "reject") }) { Text("驳回") }
                        OutlinedButton(onClick = { onAction(selectedId, editableFields, note, "save") }) { Text("保存进度") }
                        Button(onClick = { onAction(selectedId, editableFields, note, "approve") }) { Text("通过复核") }
                    }
                    Text("协作讨论", style = MaterialTheme.typography.titleMedium)
                    comments.items().forEach { comment ->
                        PlatformRecordCard(comment.str("content"), comment.str("created_at")) {
                            if (comment.str("resolved") != "true") OutlinedButton(onClick = { onResolveComment(selectedId, comment.str("id")) }) { Text("标记解决") }
                        }
                    }
                    OutlinedTextField(commentText, { commentText = it }, label = { Text("输入协作评论") }, modifier = Modifier.fillMaxWidth())
                    Button(onClick = { onComment(selectedId, commentText); commentText = "" }, enabled = commentText.isNotBlank()) { Text("发送评论") }
                }
            }
        }
    }
}

@Composable
fun WorkflowCenterScreen(
    data: JsonObject?, loading: Boolean, onBack: () -> Unit, onRefresh: () -> Unit,
    onSave: (String?, String, String, List<String>, List<String>, JsonArray) -> Unit,
    onStatus: (String, String) -> Unit, onDelete: (String) -> Unit, onRun: (String, String) -> Unit,
) {
    var name by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var fields by remember { mutableStateOf("") }
    var nodeTypes by remember { mutableStateOf("intake,extract,validate,review,export") }
    var rulesText by remember { mutableStateOf("") }
    var editingId by remember { mutableStateOf<String?>(null) }
    var documentId by remember { mutableStateOf("") }
    var confirmation by remember { mutableStateOf<PendingConfirmation?>(null) }
    val workflows = data.items()
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 30.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { ModuleTopBar("工作流", loading, onBack, onRefresh) }
        item {
            Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                BrandPill("WORKFLOW BUILDER")
                Text("配置自动化处理链路", style = MaterialTheme.typography.headlineLarge)
                OutlinedTextField(name, { name = it }, label = { Text("工作流名称") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(description, { description = it }, label = { Text("描述") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(nodeTypes, { nodeTypes = it }, label = { Text("节点顺序（逗号分隔）") }, supportingText = { Text("intake / extract / validate / review / export / notify") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(fields, { fields = it }, label = { Text("提取字段（逗号分隔）") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(rulesText, { rulesText = it }, label = { Text("校验规则") }, supportingText = { Text("每行：字段|类型|required值|失败提示") }, modifier = Modifier.fillMaxWidth(), minLines = 3)
                Button(
                    onClick = {
                        onSave(editingId, name, description, nodeTypes.csv(), fields.csv(), parseRules(rulesText))
                        editingId = null; name = ""; description = ""; fields = ""; rulesText = ""; nodeTypes = "intake,extract,validate,review,export"
                    },
                    enabled = name.length >= 2 && nodeTypes.csv().isNotEmpty() && !loading,
                    modifier = Modifier.fillMaxWidth(),
                ) { Text(if (editingId == null) "创建工作流" else "保存工作流") }
                if (editingId != null) OutlinedButton(onClick = { editingId = null; name = ""; description = ""; fields = ""; rulesText = "" }, modifier = Modifier.fillMaxWidth()) { Text("取消编辑") }
                OutlinedTextField(documentId, { documentId = it }, label = { Text("运行所用文档 ID") }, modifier = Modifier.fillMaxWidth())
            }
        }
        items(workflows, key = { it.str("id") }) { workflow ->
            val active = workflow.str("status") == "active"
            PlatformRecordCard(workflow.str("name"), "${workflow.str("status")} · v${workflow.str("version")} · 已运行 ${workflow.str("runs_count")} 次") {
                OutlinedButton(onClick = {
                    editingId = workflow.str("id"); name = workflow.str("name"); description = workflow.str("description")
                    nodeTypes = workflow.array("nodes").mapNotNull { it.takeIf(JsonElement::isJsonObject)?.asJsonObject?.str("type") }.joinToString(",")
                    fields = workflow.array("nodes").firstOrNull { it.isJsonObject && it.asJsonObject.str("type") == "extract" }?.asJsonObject?.array("fields")?.joinToString(",") { it.asString }.orEmpty()
                    rulesText = rulesToText(workflow.array("rules"))
                }) { Text("编辑") }
                OutlinedButton(onClick = { onStatus(workflow.str("id"), if (active) "paused" else "active") }) { Text(if (active) "暂停" else "启用") }
                OutlinedButton(onClick = { confirmation = PendingConfirmation("删除工作流", "确定删除“${workflow.str("name")}”吗？") { onDelete(workflow.str("id")) } }) { Text("删除") }
                Button(onClick = { onRun(workflow.str("id"), documentId) }, enabled = active && documentId.length == 32) { Text("运行") }
            }
        }
    }
    ConfirmationDialog(confirmation) { confirmation = null }
}

@Composable
fun KnowledgeCenterScreen(
    data: JsonObject?, searchData: JsonObject?, detailData: JsonObject?, loading: Boolean, onBack: () -> Unit, onRefresh: () -> Unit,
    onCreate: (String, String, String) -> Unit, onSearch: (String, String) -> Unit,
    onSelect: (String) -> Unit, onAttach: (String, String) -> Unit,
) {
    var name by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var query by remember { mutableStateOf("") }
    var selectedId by remember { mutableStateOf("") }
    var documentId by remember { mutableStateOf("") }
    var retrievalMode by remember { mutableStateOf("hybrid") }
    val collections = data.items()
    val results = searchData.items()
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 30.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { ModuleTopBar("知识与证据中心", loading, onBack, onRefresh) }
        item {
            Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                BrandPill("KNOWLEDGE & EVIDENCE")
                Text("构建可检索知识集合", style = MaterialTheme.typography.headlineLarge)
                OutlinedTextField(name, { name = it }, label = { Text("集合名称") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(description, { description = it }, label = { Text("描述") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(retrievalMode, { retrievalMode = it }, label = { Text("检索模式 keyword/vector/hybrid") }, modifier = Modifier.fillMaxWidth())
                Button(onClick = { onCreate(name, description, retrievalMode); name = "" }, enabled = name.length >= 2 && retrievalMode in setOf("keyword", "vector", "hybrid"), modifier = Modifier.fillMaxWidth()) { Text("创建知识集合") }
            }
        }
        items(collections, key = { it.str("id") }) { collection ->
            PlatformRecordCard(collection.str("name"), "${collection.str("retrieval_mode")} · ${collection.str("document_count")} 份文档") {
                OutlinedButton(onClick = { selectedId = collection.str("id"); onSelect(selectedId) }) { Text(if (selectedId == collection.str("id")) "已选择" else "选择") }
            }
        }
        if (selectedId.isNotBlank()) {
            item {
                Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("集合内容与图谱", style = MaterialTheme.typography.titleLarge)
                    Text(
                        "已挂载 ${detailData?.getAsJsonObject("documents").items().size} 份文档 · 实体 ${detailData?.getAsJsonObject("graph")?.array("entities")?.size() ?: 0} · 关系 ${detailData?.getAsJsonObject("graph")?.array("relations")?.size() ?: 0}",
                        color = BrandMuted,
                    )
                    OutlinedTextField(documentId, { documentId = it }, label = { Text("要挂载的文档 ID") }, modifier = Modifier.fillMaxWidth())
                    Button(onClick = { onAttach(selectedId, documentId); documentId = "" }, enabled = documentId.length == 32, modifier = Modifier.fillMaxWidth()) { Text("加入知识集合") }
                    detailData?.getAsJsonObject("documents").items().forEach { doc -> Text("• ${doc.str("filename", "document_id")}", color = BrandMuted) }
                    detailData?.getAsJsonObject("graph")?.array("entities")?.take(20)?.forEach { entity ->
                        if (entity.isJsonObject) Text("实体 · ${entity.asJsonObject.str("name", "entity_id")}", color = BrandMuted, fontSize = 12.sp)
                    }
                }
            }
        }
        item {
            Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("知识检索", style = MaterialTheme.typography.titleLarge)
                OutlinedTextField(query, { query = it }, label = { Text("输入检索问题") }, modifier = Modifier.fillMaxWidth())
                Button(onClick = { onSearch(selectedId, query) }, enabled = selectedId.isNotBlank() && query.length >= 2, modifier = Modifier.fillMaxWidth()) { Text("搜索") }
            }
        }
        items(results) { result -> PlatformRecordCard(result.str("filename", "title", "id"), result.str("snippet", "content")) {} }
    }
}

@Composable
fun EnterpriseCenterScreen(
    data: JsonObject?, loading: Boolean, onBack: () -> Unit, onRefresh: () -> Unit, onBackup: () -> Unit,
    onAction: (String, JsonObject) -> Unit,
) {
    var organizationName by remember { mutableStateOf("") }
    var memberEmail by remember { mutableStateOf("") }
    var memberRole by remember { mutableStateOf("member") }
    var apiKeyName by remember { mutableStateOf("") }
    var webhookName by remember { mutableStateOf("") }
    var webhookUrl by remember { mutableStateOf("") }
    var scheduleName by remember { mutableStateOf("") }
    var workflowId by remember { mutableStateOf("") }
    var scheduleDocumentId by remember { mutableStateOf("") }
    var confirmation by remember { mutableStateOf<PendingConfirmation?>(null) }
    val dashboard = data?.getAsJsonObject("dashboard")
    val organization = data?.getAsJsonObject("organization")
    val organizationRole = organization?.str("role").orEmpty()
    val canAdmin = organizationRole in setOf("owner", "admin")
    val canMember = organizationRole in setOf("owner", "admin", "member", "reviewer")
    val isOwner = organizationRole == "owner"
    val subscription = dashboard?.getAsJsonObject("subscription")
    val usage = dashboard?.getAsJsonObject("usage")
    val sections = listOf(
        "audit_logs" to "审计日志",
        "api_keys" to "API 密钥",
        "webhooks" to "Webhook 集成",
        "schedules" to "计划任务",
    )
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 30.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { ModuleTopBar("企业控制台", loading, onBack, onRefresh) }
        item {
            Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                BrandPill("ENTERPRISE CONSOLE")
                Text("组织、安全、集成与运维", style = MaterialTheme.typography.headlineLarge)
                Text("移动端集中查看企业套餐、成员、用量和服务健康状态。", color = BrandMuted)
                if (canAdmin) Button(onClick = onBackup, enabled = !loading, modifier = Modifier.fillMaxWidth()) { Text("创建系统备份") }
            }
        }
        val organizations = data?.getAsJsonObject("organizations").items()
        if (organizations.size > 1) {
            item { Text("组织空间", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(horizontal = 20.dp)) }
            items(organizations, key = { it.str("id") }) { space ->
                PlatformRecordCard(space.str("name"), "${space.str("plan")} · ${space.str("role")}") {
                    if (space.str("active") != "true") Button(onClick = { onAction("organization.activate", JsonObject().apply { addProperty("id", space.str("id")) }) }) { Text("切换到此组织") }
                    else BrandPill("当前空间")
                }
            }
        }
        if (canAdmin) item {
            Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("组织与成员管理", style = MaterialTheme.typography.titleLarge)
                OutlinedTextField(organizationName, { organizationName = it }, label = { Text("新的组织名称") }, modifier = Modifier.fillMaxWidth())
                Button(
                    onClick = { onAction("organization.rename", JsonObject().apply { addProperty("name", organizationName) }) },
                    enabled = organizationName.length >= 2 && !loading, modifier = Modifier.fillMaxWidth(),
                ) { Text("更新组织名称") }
                OutlinedTextField(memberEmail, { memberEmail = it }, label = { Text("成员注册邮箱") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(memberRole, { memberRole = it }, label = { Text("角色 viewer/member/reviewer/admin") }, modifier = Modifier.fillMaxWidth())
                Button(onClick = {
                    onAction("member.add", JsonObject().apply { addProperty("email", memberEmail); addProperty("role", memberRole) }); memberEmail = ""
                }, enabled = memberEmail.contains('@') && !loading, modifier = Modifier.fillMaxWidth()) { Text("添加成员") }
            }
        }
        organization?.array("members")?.forEach { element ->
            val member = element.asJsonObject
            item {
                PlatformRecordCard(member.str("username", "email", "id"), "${member.str("email")} · ${member.str("role")}") {
                    if (canAdmin && member.str("role") != "owner") OutlinedButton(onClick = { onAction("member.role", JsonObject().apply { addProperty("id", member.str("id")); addProperty("role", if (member.str("role") == "admin") "member" else "admin") }) }) { Text("切换角色") }
                    if (canAdmin && member.str("role") != "owner") OutlinedButton(onClick = {
                        confirmation = PendingConfirmation("移除成员", "确定将 ${member.str("username", "email")} 移出当前组织吗？") {
                            onAction("member.remove", JsonObject().apply { addProperty("id", member.str("id")) })
                        }
                    }) { Text("移除") }
                }
            }
        }
        item {
            PlatformRecordCard(
                organization?.str("name").orEmpty().ifBlank { "当前组织" },
                "角色 ${organization?.str("role").orEmpty().ifBlank { "-" }} · 套餐 ${organization?.str("plan").orEmpty().ifBlank { subscription?.str("plan").orEmpty().ifBlank { "-" } }} · ${organization?.array("members")?.size() ?: 0} 位成员",
            ) {}
        }
        if (usage != null) {
            item { Text("资源用量", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(horizontal = 20.dp, vertical = 4.dp)) }
            usage.entrySet().forEach { (key, value) ->
                item { PlatformRecordCard(enterpriseLabel(key), value.readableValue()) {} }
            }
        }
        if (canMember) item {
            Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("集成与自动化", style = MaterialTheme.typography.titleLarge)
                if (canAdmin) {
                    OutlinedTextField(apiKeyName, { apiKeyName = it }, label = { Text("API 密钥名称") }, modifier = Modifier.fillMaxWidth())
                    Button(onClick = {
                        onAction("api_key.create", JsonObject().apply {
                            addProperty("name", apiKeyName); add("scopes", JsonArray().apply { add("workspace:read") }); addProperty("expires_in_days", 90)
                        }); apiKeyName = ""
                    }, enabled = apiKeyName.length >= 2 && !loading, modifier = Modifier.fillMaxWidth()) { Text("创建 API 密钥") }
                    OutlinedTextField(webhookName, { webhookName = it }, label = { Text("Webhook 名称") }, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(webhookUrl, { webhookUrl = it }, label = { Text("Webhook HTTPS 地址") }, modifier = Modifier.fillMaxWidth())
                    Button(onClick = {
                        onAction("webhook.create", JsonObject().apply {
                            addProperty("name", webhookName); addProperty("url", webhookUrl); add("events", JsonArray().apply { add("task.succeeded"); add("task.failed") })
                        }); webhookName = ""; webhookUrl = ""
                    }, enabled = webhookName.length >= 2 && webhookUrl.startsWith("https://") && !loading, modifier = Modifier.fillMaxWidth()) { Text("创建 Webhook") }
                }
                OutlinedTextField(scheduleName, { scheduleName = it }, label = { Text("计划任务名称") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(workflowId, { workflowId = it }, label = { Text("工作流 ID") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(scheduleDocumentId, { scheduleDocumentId = it }, label = { Text("文档 ID") }, modifier = Modifier.fillMaxWidth())
                Button(onClick = {
                    onAction("schedule.create", JsonObject().apply {
                        addProperty("name", scheduleName); addProperty("workflow_id", workflowId); addProperty("document_id", scheduleDocumentId)
                        addProperty("cron_expression", "0 9 * * 1-5"); addProperty("timezone", "Asia/Shanghai"); addProperty("retry_limit", 2)
                    }); scheduleName = ""
                }, enabled = scheduleName.length >= 2 && workflowId.length == 32 && scheduleDocumentId.length == 32 && !loading, modifier = Modifier.fillMaxWidth()) { Text("创建工作日计划") }
                if (isOwner) Text("套餐切换", style = MaterialTheme.typography.titleMedium)
                if (isOwner) Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("starter" to "基础版", "team" to "团队版", "enterprise" to "企业版").forEach { (plan, label) ->
                        OutlinedButton(onClick = {
                            confirmation = PendingConfirmation("切换套餐", "确认切换为${label}吗？此操作会立即更新当前组织额度。") {
                                onAction("subscription.change", JsonObject().apply { addProperty("plan", plan) })
                            }
                        }) { Text(label) }
                    }
                }
            }
        }
        sections.plus(listOf("webhook_deliveries" to "投递记录", "backups" to "备份记录")).forEach { (key, title) ->
            val records = data?.getAsJsonObject(key).items()
            if (records.isNotEmpty()) {
                item { Text(title, style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(horizontal = 20.dp, vertical = 4.dp)) }
                items(records, key = { it.str("id") }) { record ->
                    PlatformRecordCard(
                        record.str("name", "action", "event", "id").ifBlank { title },
                        record.entrySet().filterNot { it.key == "id" || it.key == "name" }
                            .take(4).joinToString(" · ") { "${enterpriseLabel(it.key)} ${it.value.readableValue()}" },
                    ) {
                        when (key) {
                            "api_keys" -> OutlinedButton(onClick = {
                                confirmation = PendingConfirmation("撤销 API 密钥", "撤销后使用该密钥的集成将立即失效。") {
                                    onAction("api_key.revoke", JsonObject().apply { addProperty("id", record.str("id")) })
                                }
                            }) { Text("撤销") }
                            "webhooks" -> {
                                OutlinedButton(onClick = { onAction("webhook.test", JsonObject().apply { addProperty("id", record.str("id")) }) }) { Text("测试") }
                                OutlinedButton(onClick = {
                                    confirmation = PendingConfirmation("删除 Webhook", "确定删除“${record.str("name")}”吗？") {
                                        onAction("webhook.delete", JsonObject().apply { addProperty("id", record.str("id")) })
                                    }
                                }) { Text("删除") }
                            }
                            "schedules" -> OutlinedButton(onClick = {
                                confirmation = PendingConfirmation("删除计划任务", "确定删除“${record.str("name")}”吗？") {
                                    onAction("schedule.delete", JsonObject().apply { addProperty("id", record.str("id")) })
                                }
                            }) { Text("删除") }
                        }
                    }
                }
            }
        }
        val operations = data?.getAsJsonObject("operations")
        if (operations != null) {
            item { Text("服务运维", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(horizontal = 20.dp, vertical = 4.dp)) }
            operations.entrySet().forEach { (key, value) ->
                item { PlatformRecordCard(enterpriseLabel(key), value.readableValue()) {} }
            }
        }
    }
    ConfirmationDialog(confirmation) { confirmation = null }
}

@Composable
fun AdminCenterScreen(
    data: JsonObject?, loading: Boolean, onBack: () -> Unit, onRefresh: () -> Unit,
    detail: JsonObject?, onDetail: (String) -> Unit,
    onStatus: (String, String) -> Unit, onRole: (String, Boolean) -> Unit, onDelete: (String) -> Unit,
) {
    var detailId by remember { mutableStateOf("") }
    var confirmation by remember { mutableStateOf<PendingConfirmation?>(null) }
    val statistics = data?.getAsJsonObject("statistics")
    val users = data?.getAsJsonObject("users")?.items().orEmpty()
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 30.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { ModuleTopBar("后台管理", loading, onBack, onRefresh) }
        item {
            Column(Modifier.padding(horizontal = 20.dp)) {
                BrandPill("ADMINISTRATION")
                Text("用户与权限管理", style = MaterialTheme.typography.headlineLarge, modifier = Modifier.padding(top = 10.dp))
                Text("总用户 ${statistics?.str("total_users") ?: "-"} · 在线 ${statistics?.str("online_users") ?: "-"} · 正常 ${statistics?.str("normal_users") ?: "-"}", color = BrandMuted)
            }
        }
        items(users, key = { it.str("id") }) { user ->
            val isAdmin = user.str("role").contains("管理员")
            val normal = user.str("account_status") == "正常"
            PlatformRecordCard(user.str("username"), "${user.str("email")} · ${user.str("role")} · ${user.str("login_status")}") {
                OutlinedButton(onClick = { detailId = user.str("id"); onDetail(detailId) }) { Text("详情") }
                OutlinedButton(onClick = {
                    confirmation = PendingConfirmation(if (normal) "禁用用户" else "启用用户", "确定${if (normal) "禁用" else "启用"} ${user.str("username")} 吗？") {
                        onStatus(user.str("id"), if (normal) "异常" else "正常")
                    }
                }) { Text(if (normal) "禁用" else "启用") }
                OutlinedButton(onClick = {
                    confirmation = PendingConfirmation("修改管理员权限", "确定${if (isAdmin) "取消" else "授予"} ${user.str("username")} 的管理员权限吗？") { onRole(user.str("id"), !isAdmin) }
                }) { Text(if (isAdmin) "取消管理员" else "设为管理员") }
                OutlinedButton(onClick = {
                    confirmation = PendingConfirmation("删除用户", "确定删除 ${user.str("username")} 吗？此操作不可恢复。") { onDelete(user.str("id")) }
                }) { Text("删除", color = MaterialTheme.colorScheme.error) }
            }
        }
        if (detail != null && detail.str("id") == detailId) {
            item {
                PlatformRecordCard("用户详情 · ${detail.str("username")}", detail.entrySet().take(10).joinToString(" · ") { "${it.key}: ${it.value.readableValue()}" }) {}
            }
        }
    }
    ConfirmationDialog(confirmation) { confirmation = null }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun PlatformRecordCard(title: String, subtitle: String, actions: @Composable () -> Unit) {
    Card(
        Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = BrandCard),
        shape = RoundedCornerShape(16.dp),
    ) {
        Column(Modifier.padding(17.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title.ifBlank { "未命名记录" }, style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
            if (subtitle.isNotBlank()) Text(subtitle, color = BrandMuted, fontSize = 12.sp, maxLines = 4, overflow = TextOverflow.Ellipsis)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) { actions() }
        }
    }
}

@Composable
private fun EmptyWorkspaceCard(text: String) {
    Card(Modifier.padding(horizontal = 20.dp).fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = BrandCard)) {
        Text(text, color = BrandMuted, modifier = Modifier.padding(28.dp))
    }
}

private fun JsonObject?.items(): List<JsonObject> = this?.get("items")?.takeIf(JsonElement::isJsonArray)?.asJsonArray
    ?.mapNotNull { it.takeIf(JsonElement::isJsonObject)?.asJsonObject }.orEmpty()

private fun JsonObject.str(vararg keys: String): String = keys.firstNotNullOfOrNull { key ->
    get(key)?.takeIf { it.isJsonPrimitive && !it.isJsonNull }?.asString
}.orEmpty()

private fun JsonObject.array(key: String): JsonArray = get(key)?.takeIf(JsonElement::isJsonArray)?.asJsonArray ?: JsonArray()

private data class PendingConfirmation(val title: String, val message: String, val action: () -> Unit)

@Composable
private fun ConfirmationDialog(pending: PendingConfirmation?, onDismiss: () -> Unit) {
    if (pending == null) return
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(pending.title) },
        text = { Text(pending.message) },
        dismissButton = { TextButton(onClick = onDismiss) { Text("取消") } },
        confirmButton = {
            Button(onClick = { val action = pending.action; onDismiss(); action() }) { Text("确定") }
        },
    )
}

private fun String.csv(): List<String> = replace('，', ',').split(',').map(String::trim).filter(String::isNotBlank)

private fun parseRules(text: String): JsonArray = JsonArray().apply {
    text.lines().filter(String::isNotBlank).forEach { line ->
        val values = line.split('|').map(String::trim)
        val type = values.getOrNull(1).orEmpty().ifBlank { "required" }
        add(JsonObject().apply {
            addProperty("field", values.getOrNull(0).orEmpty())
            addProperty("type", type)
            if (type != "required") addProperty("value", values.getOrNull(2).orEmpty())
            if (type == "regex") addProperty("pattern", values.getOrNull(2).orEmpty())
            addProperty("message", values.getOrNull(3).orEmpty().ifBlank { "字段校验失败" })
            addProperty("level", "error")
        })
    }
}

private fun rulesToText(rules: JsonArray): String = rules.joinToString("\n") { element ->
    val rule = element.asJsonObject
    listOf(rule.str("field"), rule.str("type"), rule.str("value", "pattern"), rule.str("message")).joinToString("|")
}

private fun enterpriseLabel(key: String): String = mapOf(
    "documents" to "文档", "workflows" to "工作流", "members" to "成员",
    "storage_bytes" to "存储空间", "tasks" to "任务", "services" to "服务状态",
    "recent_errors" to "最近错误", "created_at" to "创建时间", "last_used_at" to "最后使用",
    "cron_expression" to "Cron 表达式", "status" to "状态", "events" to "事件",
)[key] ?: key.replace('_', ' ')

private fun JsonElement.readableValue(): String = when {
    isJsonNull -> "-"
    isJsonPrimitive -> asString
    isJsonArray -> asJsonArray.joinToString(", ") { it.readableValue() }.ifBlank { "暂无" }
    isJsonObject -> asJsonObject.entrySet().take(5).joinToString(" · ") {
        "${enterpriseLabel(it.key)} ${it.value.readableValue()}"
    }.ifBlank { "暂无" }
    else -> toString()
}
