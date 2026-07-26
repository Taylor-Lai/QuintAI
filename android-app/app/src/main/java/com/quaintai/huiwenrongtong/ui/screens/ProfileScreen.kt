package com.quaintai.huiwenrongtong.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.gson.JsonObject
import com.quaintai.huiwenrongtong.data.remote.TaskDto
import com.quaintai.huiwenrongtong.ui.components.BrandHeader
import com.quaintai.huiwenrongtong.ui.theme.BrandCard
import com.quaintai.huiwenrongtong.ui.theme.BrandGoldDark
import com.quaintai.huiwenrongtong.ui.theme.BrandMuted

@Composable
fun ProfileScreen(
    username: String, email: String, tasks: List<TaskDto>, profile: JsonObject?,
    onRefresh: () -> Unit, onUpdate: (String, String, String, String) -> Unit, onLogout: () -> Unit,
) {
    var editing by remember { mutableStateOf(false) }
    var nickname by remember(profile) { mutableStateOf(profile.value("nickname").ifBlank { username }) }
    var formEmail by remember(profile) { mutableStateOf(profile.value("email").ifBlank { email }) }
    var gender by remember(profile) { mutableStateOf(profile.value("gender").ifBlank { "未设置" }) }
    var phone by remember(profile) { mutableStateOf(profile.value("phone")) }
    var confirmLogout by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        BrandHeader()
        Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text("个人中心", style = MaterialTheme.typography.headlineLarge)
            Text("管理你的账户、资料与处理记录", color = BrandMuted)
            Card(Modifier.fillMaxWidth(), shape = RoundedCornerShape(20.dp), colors = CardDefaults.cardColors(containerColor = BrandCard)) {
                Row(Modifier.padding(20.dp), verticalAlignment = Alignment.CenterVertically) {
                    Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
                        Text(username.take(1).uppercase().ifBlank { "U" }, color = BrandGoldDark, fontWeight = FontWeight.Bold, fontSize = 28.sp, modifier = Modifier.padding(horizontal = 21.dp, vertical = 15.dp))
                    }
                    Column(Modifier.weight(1f).padding(start = 16.dp)) {
                        Text(nickname.ifBlank { username }, style = MaterialTheme.typography.titleLarge)
                        Text(formEmail, color = BrandMuted)
                        Text(profile.value("role").ifBlank { "普通用户" }, color = BrandGoldDark, fontSize = 12.sp)
                    }
                    OutlinedButton(onClick = { editing = !editing; if (!editing) onRefresh() }) { Text(if (editing) "取消" else "编辑") }
                }
            }
            if (editing) {
                Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = BrandCard)) {
                    Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        OutlinedTextField(nickname, { nickname = it }, label = { Text("昵称") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(formEmail, { formEmail = it }, label = { Text("邮箱") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(gender, { gender = it }, label = { Text("性别") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(phone, { phone = it }, label = { Text("手机号") }, modifier = Modifier.fillMaxWidth())
                        Button(onClick = { onUpdate(nickname, formEmail, gender, phone); editing = false }, modifier = Modifier.fillMaxWidth()) { Text("保存修改") }
                    }
                }
            }
            Text("使用概览", style = MaterialTheme.typography.titleLarge)
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                OverviewCard("处理任务", tasks.size, Modifier.weight(1f))
                OverviewCard("成功完成", tasks.count { it.status == "succeeded" }, Modifier.weight(1f))
            }
            Card(Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = BrandCard)) {
                Column(Modifier.padding(18.dp)) {
                    Text("数据与安全", style = MaterialTheme.typography.titleMedium)
                    Text("登录凭证使用 Android 系统安全存储保护，业务数据按账户与组织隔离。", color = BrandMuted, modifier = Modifier.padding(top = 7.dp))
                }
            }
            OutlinedButton(onClick = { confirmLogout = true }, modifier = Modifier.fillMaxWidth()) { Text("退出登录") }
        }
    }
    if (confirmLogout) {
        AlertDialog(
            onDismissRequest = { confirmLogout = false },
            title = { Text("退出登录") },
            text = { Text("确定退出当前账户吗？未完成的后台任务不会被取消。") },
            dismissButton = { TextButton(onClick = { confirmLogout = false }) { Text("取消") } },
            confirmButton = { Button(onClick = { confirmLogout = false; onLogout() }) { Text("退出") } },
        )
    }
}

@Composable
private fun OverviewCard(label: String, count: Int, modifier: Modifier) {
    Card(modifier, colors = CardDefaults.cardColors(containerColor = BrandCard), shape = RoundedCornerShape(16.dp)) {
        Column(Modifier.padding(18.dp)) {
            Text(count.toString(), style = MaterialTheme.typography.headlineMedium, color = BrandGoldDark)
            Text(label, color = BrandMuted, fontSize = 12.sp)
        }
    }
}

private fun JsonObject?.value(key: String): String = this?.get(key)?.takeIf { it.isJsonPrimitive && !it.isJsonNull }?.asString.orEmpty()
