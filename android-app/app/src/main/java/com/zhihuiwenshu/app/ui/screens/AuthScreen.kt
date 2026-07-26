package com.zhihuiwenshu.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.zhihuiwenshu.app.ui.theme.BrandBackground
import com.zhihuiwenshu.app.ui.theme.BrandCard
import com.zhihuiwenshu.app.ui.theme.BrandGoldDark
import com.zhihuiwenshu.app.ui.theme.BrandMuted

@Composable
fun AuthScreen(
    loading: Boolean,
    onLogin: (String, String) -> Unit,
    onRegister: (String, String, String, () -> Unit) -> Unit,
) {
    var registering by remember { mutableStateOf(false) }
    var username by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }

    Box(Modifier.fillMaxSize().background(BrandBackground), contentAlignment = Alignment.Center) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 24.dp).verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Box(
                Modifier.padding(bottom = 14.dp).clip(CircleShape)
                    .background(Brush.linearGradient(listOf(Color(0xFFE2C08C), Color(0xFFCFA15C))))
                    .padding(horizontal = 18.dp, vertical = 12.dp),
            ) { Text("◔", color = Color.White, fontSize = 30.sp, fontWeight = FontWeight.Bold) }
            Text("智汇文枢", style = MaterialTheme.typography.headlineLarge)
            Text(
                "让复杂文档处理变得简单高效",
                color = BrandMuted,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(top = 6.dp, bottom = 24.dp),
            )
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(22.dp),
                colors = CardDefaults.cardColors(containerColor = BrandCard),
            ) {
                Column(Modifier.padding(22.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
                    Text(if (registering) "创建账户" else "欢迎回来", style = MaterialTheme.typography.titleLarge)
                    Text(if (registering) "注册后即可同步处理记录" else "登录后继续你的文档任务", color = BrandMuted)
                    if (registering) {
                        OutlinedTextField(
                            value = username,
                            onValueChange = { username = it },
                            label = { Text("用户名") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp),
                        )
                    }
                    OutlinedTextField(
                        value = email,
                        onValueChange = { email = it },
                        label = { Text("邮箱") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp),
                    )
                    OutlinedTextField(
                        value = password,
                        onValueChange = { password = it },
                        label = { Text("密码") },
                        visualTransformation = PasswordVisualTransformation(),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp),
                    )
                    Spacer(Modifier.height(2.dp))
                    Button(
                        onClick = {
                            if (registering) onRegister(username, email, password) { registering = false }
                            else onLogin(email, password)
                        },
                        enabled = !loading && email.isNotBlank() && password.isNotBlank() && (!registering || username.length >= 2),
                        modifier = Modifier.fillMaxWidth().height(52.dp),
                        shape = RoundedCornerShape(12.dp),
                    ) {
                        if (loading) CircularProgressIndicator(Modifier.height(22.dp), strokeWidth = 2.dp, color = Color.White)
                        else Text(if (registering) "创建账户" else "登录")
                    }
                    TextButton(onClick = { registering = !registering }, enabled = !loading, modifier = Modifier.align(Alignment.CenterHorizontally)) {
                        Text(if (registering) "已有账户？返回登录" else "没有账户？立即注册", color = BrandGoldDark)
                    }
                }
            }
        }
    }
}
