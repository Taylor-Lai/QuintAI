package com.quaintai.huiwenrongtong.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AdminPanelSettings
import androidx.compose.material.icons.automirrored.outlined.ArrowForward
import androidx.compose.material.icons.outlined.AutoStories
import androidx.compose.material.icons.outlined.Business
import androidx.compose.material.icons.outlined.Dashboard
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.EditNote
import androidx.compose.material.icons.automirrored.outlined.FactCheck
import androidx.compose.material.icons.automirrored.outlined.HelpOutline
import androidx.compose.material.icons.outlined.Hub
import androidx.compose.material.icons.outlined.PlayCircle
import androidx.compose.material.icons.outlined.ViewModule
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quaintai.huiwenrongtong.data.remote.PlatformModule
import com.quaintai.huiwenrongtong.ui.components.BrandHeader
import com.quaintai.huiwenrongtong.ui.components.BrandPill
import com.quaintai.huiwenrongtong.ui.theme.BrandCard
import com.quaintai.huiwenrongtong.ui.theme.BrandGoldDark
import com.quaintai.huiwenrongtong.ui.theme.BrandMuted

private data class ModuleItem(val module: PlatformModule, val icon: ImageVector, val group: String)

private val moduleItems = listOf(
    ModuleItem(PlatformModule.OVERVIEW, Icons.Outlined.Dashboard, "智能工作台"),
    ModuleItem(PlatformModule.DOCUMENTS, Icons.Outlined.Description, "智能工作台"),
    ModuleItem(PlatformModule.REVIEWS, Icons.AutoMirrored.Outlined.FactCheck, "智能工作台"),
    ModuleItem(PlatformModule.WORKFLOWS, Icons.Outlined.Hub, "智能工作台"),
    ModuleItem(PlatformModule.EXECUTIONS, Icons.Outlined.PlayCircle, "智能工作台"),
    ModuleItem(PlatformModule.KNOWLEDGE, Icons.Outlined.AutoStories, "智能工作台"),
    ModuleItem(PlatformModule.ENTERPRISE, Icons.Outlined.Business, "企业能力"),
    ModuleItem(PlatformModule.TEMPLATES, Icons.Outlined.ViewModule, "模板与帮助"),
    ModuleItem(PlatformModule.EDITOR, Icons.Outlined.EditNote, "模板与帮助"),
    ModuleItem(PlatformModule.GUIDE, Icons.AutoMirrored.Outlined.HelpOutline, "模板与帮助"),
    ModuleItem(PlatformModule.ADMIN, Icons.Outlined.AdminPanelSettings, "管理能力"),
)

@Composable
fun WorkbenchScreen(userRole: String, onModuleSelected: (PlatformModule) -> Unit) {
    val visibleModules = moduleItems.filter { it.module != PlatformModule.ADMIN || userRole.contains("管理员") || userRole == "admin" }
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(bottom = 28.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item { BrandHeader { BrandPill("全功能原生版") } }
        item {
            Column(Modifier.padding(horizontal = 20.dp)) {
                Text("智能工作台", style = MaterialTheme.typography.headlineLarge)
                Text("集中管理文档、复核、自动化流程与企业能力", color = BrandMuted, modifier = Modifier.padding(top = 5.dp))
            }
        }
        visibleModules.groupBy { it.group }.forEach { (group, entries) ->
            item {
                Text(
                    group,
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(horizontal = 20.dp, vertical = 8.dp),
                )
            }
            items(entries, key = { it.module.name }) { item -> ModuleCard(item, onModuleSelected) }
        }
    }
}

@Composable
private fun ModuleCard(item: ModuleItem, onClick: (PlatformModule) -> Unit) {
    Card(
        modifier = Modifier.padding(horizontal = 20.dp).fillMaxWidth().clickable { onClick(item.module) },
        colors = CardDefaults.cardColors(containerColor = BrandCard),
        shape = RoundedCornerShape(16.dp),
    ) {
        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(item.icon, null, tint = BrandGoldDark, modifier = Modifier.padding(8.dp))
            Column(Modifier.weight(1f).padding(horizontal = 10.dp)) {
                Text(item.module.title, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
                Text(item.module.description, color = BrandMuted, fontSize = 12.sp)
            }
            Icon(Icons.AutoMirrored.Outlined.ArrowForward, null, tint = BrandGoldDark)
        }
    }
}
