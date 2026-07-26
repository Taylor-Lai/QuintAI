package com.quaintai.huiwenrongtong.ui.screens

import android.net.Uri
import android.provider.OpenableColumns
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.AttachFile
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
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
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quaintai.huiwenrongtong.data.remote.FeatureKind
import com.quaintai.huiwenrongtong.data.SimpleXlsxWriter
import com.quaintai.huiwenrongtong.data.local.TemplateStore
import com.quaintai.huiwenrongtong.ui.components.BrandPill
import com.quaintai.huiwenrongtong.ui.theme.BrandBackground
import com.quaintai.huiwenrongtong.ui.theme.BrandBorder
import com.quaintai.huiwenrongtong.ui.theme.BrandCard
import com.quaintai.huiwenrongtong.ui.theme.BrandGoldDark
import com.quaintai.huiwenrongtong.ui.theme.BrandMuted

@Composable
fun UploadScreen(
    kind: FeatureKind,
    loading: Boolean,
    onBack: () -> Unit,
    onSubmit: (Uri, List<Uri>, String) -> Unit,
) {
    var primary by remember { mutableStateOf<Uri?>(null) }
    var sources by remember { mutableStateOf<List<Uri>>(emptyList()) }
    var instruction by remember { mutableStateOf("") }
    var validationMessage by remember { mutableStateOf("") }
    val context = LocalContext.current
    val templateStore = remember { TemplateStore(context) }
    var activeTemplate by remember(kind) { mutableStateOf(if (kind == FeatureKind.TABLE) templateStore.active() else null) }
    val primaryPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null && context.fileSize(uri) > MAX_FILE_BYTES) {
            validationMessage = "单个文件不能超过 25 MB"
        } else {
            primary = uri
            validationMessage = ""
        }
    }
    val sourcesPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
        when {
            uris.size > MAX_SOURCE_FILES -> validationMessage = "单次最多选择 10 个来源文件"
            uris.any { context.fileSize(it) > MAX_FILE_BYTES } -> validationMessage = "单个来源文件不能超过 25 MB"
            else -> { sources = uris; validationMessage = "" }
        }
    }
    val hasPrimary = primary != null || (kind == FeatureKind.TABLE && activeTemplate?.fields?.isNotEmpty() == true)
    val valid = hasPrimary && (kind == FeatureKind.TABLE || instruction.isNotBlank()) && (kind != FeatureKind.TABLE || sources.isNotEmpty())
    val selectedLibraryTemplate = activeTemplate

    Scaffold(containerColor = BrandBackground) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().padding(padding).verticalScroll(rememberScrollState()),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth().statusBarsPadding().padding(horizontal = 8.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "返回") }
                Text("返回首页", color = BrandGoldDark, fontWeight = FontWeight.SemiBold)
            }
            Column(
                modifier = Modifier.padding(horizontal = 20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                BrandPill(kind.badge())
                Text(kind.title, style = MaterialTheme.typography.headlineLarge)
                Text(kind.longDescription(), color = BrandMuted, lineHeight = 23.sp)

                StepLabel("01", if (kind == FeatureKind.TABLE) "上传目标模板" else "上传待处理文档")
                if (kind == FeatureKind.TABLE && selectedLibraryTemplate != null) {
                    Card(colors = CardDefaults.cardColors(containerColor = BrandCard), modifier = Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(16.dp)) {
                            Text("已从模板库选择：${selectedLibraryTemplate.name}", fontWeight = FontWeight.SemiBold)
                            Text("${selectedLibraryTemplate.category} · ${selectedLibraryTemplate.scene} · ${selectedLibraryTemplate.fields.size} 个字段", color = BrandMuted, fontSize = 12.sp)
                            Text(selectedLibraryTemplate.fields.joinToString(" · "), color = BrandMuted, fontSize = 12.sp, maxLines = 3)
                            TextButton(onClick = { templateStore.clearActive(); activeTemplate = null }) { Text("不使用此模板") }
                        }
                    }
                }
                FileSelector(
                    title = if (kind == FeatureKind.TABLE) "选择目标模板" else "选择文档",
                    selected = primary?.let { context.displayName(it) },
                    onClick = { primaryPicker.launch(primaryMimeTypes(kind)) },
                )
                if (kind == FeatureKind.TABLE) {
                    StepLabel("02", "上传来源文件")
                    FileSelector(
                        title = "选择来源文档（可多选）",
                        selected = sources.takeIf { it.isNotEmpty() }?.let { "已选择 ${it.size} 个文件" },
                        onClick = { sourcesPicker.launch(SOURCE_MIME_TYPES) },
                    )
                }
                StepLabel(if (kind == FeatureKind.TABLE) "03" else "02", kind.inputLabel())
                OutlinedTextField(
                    value = instruction,
                    onValueChange = { instruction = it },
                    label = { Text(kind.inputLabel()) },
                    placeholder = { Text(kind.placeholder()) },
                    minLines = 4,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                )
                if (validationMessage.isNotBlank()) Text(validationMessage, color = MaterialTheme.colorScheme.error, fontSize = 12.sp)
                Button(
                    onClick = {
                        val target = primary ?: activeTemplate?.let { template ->
                            val safeName = template.name.replace(Regex("[\\\\/:*?\"<>|]"), "_")
                            val file = java.io.File(context.cacheDir, "$safeName.xlsx")
                            SimpleXlsxWriter.write(file, template.fields)
                            Uri.fromFile(file)
                        }
                        if (target != null) onSubmit(target, sources, instruction.trim())
                    },
                    enabled = valid && !loading,
                    modifier = Modifier.fillMaxWidth().height(54.dp),
                    shape = RoundedCornerShape(12.dp),
                ) {
                    if (loading) CircularProgressIndicator(Modifier.size(22.dp), strokeWidth = 2.dp)
                    else Text("开始智能处理")
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Outlined.CheckCircle, null, tint = BrandGoldDark, modifier = Modifier.size(17.dp))
                    Text(" 提交后可以离开，进度和结果会保存在任务中心。", color = BrandMuted, fontSize = 12.sp)
                }
                Spacer(Modifier.height(28.dp))
            }
        }
    }
}

@Composable
private fun StepLabel(number: String, title: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(number, color = BrandGoldDark, fontWeight = FontWeight.Bold, fontSize = 12.sp)
        Text("  $title", style = MaterialTheme.typography.titleMedium)
    }
}

@Composable
private fun FileSelector(title: String, selected: String?, onClick: () -> Unit) {
    Card(
        shape = RoundedCornerShape(16.dp),
        modifier = Modifier.fillMaxWidth().border(1.dp, BrandBorder, RoundedCornerShape(16.dp)),
        colors = CardDefaults.cardColors(containerColor = BrandCard),
    ) {
        Row(Modifier.fillMaxWidth().padding(17.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Outlined.AttachFile, null, tint = BrandGoldDark, modifier = Modifier.size(28.dp))
            Column(Modifier.weight(1f).padding(horizontal = 12.dp)) {
                Text(title, fontWeight = FontWeight.SemiBold)
                Text(
                    selected ?: "支持 DOCX、XLSX、TXT、MD",
                    color = BrandMuted,
                    fontSize = 12.sp,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            OutlinedButton(onClick = onClick) { Text(if (selected == null) "选择" else "更换") }
        }
    }
}

private fun FeatureKind.badge() = when (this) {
    FeatureKind.EDIT -> "智能文档交互"
    FeatureKind.EXTRACT -> "信息提取引擎"
    FeatureKind.TABLE -> "表格智能处理"
}

private fun FeatureKind.longDescription() = when (this) {
    FeatureKind.EDIT -> "上传 Word 文件，用自然语言描述目标格式与修改要求，系统将生成可下载的新文档。"
    FeatureKind.EXTRACT -> "针对合同、报告、说明书等非结构化文件，提取关键字段并完成结构化输出。"
    FeatureKind.TABLE -> "上传空白模板和多个来源文件，按你的业务规则自动融合、校验并填写数据。"
}

private fun FeatureKind.inputLabel() = when (this) {
    FeatureKind.EDIT -> "编辑要求"
    FeatureKind.EXTRACT -> "需要提取的字段"
    FeatureKind.TABLE -> "填写要求"
}

private fun FeatureKind.placeholder() = when (this) {
    FeatureKind.EDIT -> "例如：统一标题格式，并修正文中的错别字"
    FeatureKind.EXTRACT -> "例如：合同编号、甲方、金额、签署日期"
    FeatureKind.TABLE -> "例如：按客户名称合并数据，缺失项保持空白"
}

private fun android.content.Context.displayName(uri: Uri): String {
    contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
        if (cursor.moveToFirst()) return cursor.getString(0)
    }
    return uri.lastPathSegment ?: "未命名文件"
}

private fun android.content.Context.fileSize(uri: Uri): Long {
    contentResolver.query(uri, arrayOf(OpenableColumns.SIZE), null, null, null)?.use { cursor ->
        if (cursor.moveToFirst() && !cursor.isNull(0)) return cursor.getLong(0)
    }
    return 0L
}

private fun primaryMimeTypes(kind: FeatureKind): Array<String> = when (kind) {
    FeatureKind.EDIT -> arrayOf(DOCX_MIME)
    FeatureKind.EXTRACT -> SOURCE_MIME_TYPES
    FeatureKind.TABLE -> arrayOf(DOCX_MIME, XLSX_MIME)
}

private const val DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
private const val XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
private val SOURCE_MIME_TYPES = arrayOf(DOCX_MIME, XLSX_MIME, "text/plain", "text/markdown")
private const val MAX_FILE_BYTES = 25L * 1024L * 1024L
private const val MAX_SOURCE_FILES = 10
