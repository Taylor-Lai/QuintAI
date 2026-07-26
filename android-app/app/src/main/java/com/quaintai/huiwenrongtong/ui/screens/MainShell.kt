package com.quaintai.huiwenrongtong.ui.screens

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AccountCircle
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.DashboardCustomize
import androidx.compose.material.icons.outlined.TaskAlt
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.quaintai.huiwenrongtong.data.remote.FeatureKind
import com.quaintai.huiwenrongtong.data.remote.TaskDto
import com.quaintai.huiwenrongtong.data.remote.PlatformModule
import com.quaintai.huiwenrongtong.ui.AppUiState
import com.quaintai.huiwenrongtong.ui.theme.BrandBackground
import com.quaintai.huiwenrongtong.ui.theme.BrandGoldDark

private enum class MainTab(val title: String) { HOME("首页"), WORKBENCH("工作台"), TASKS("任务"), PROFILE("我的") }

@Composable
fun MainShell(
    state: AppUiState,
    onFeatureSelected: (FeatureKind) -> Unit,
    onTaskSelected: (TaskDto) -> Unit,
    onModuleSelected: (PlatformModule) -> Unit,
    onRefreshTasks: () -> Unit,
    onRefreshProfile: () -> Unit,
    onUpdateProfile: (String, String, String, String) -> Unit,
    onLogout: () -> Unit,
) {
    var tab by rememberSaveable { mutableStateOf(MainTab.HOME) }
    Scaffold(
        containerColor = BrandBackground,
        bottomBar = {
            NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                MainTab.entries.forEach { item ->
                    NavigationBarItem(
                        selected = tab == item,
                        onClick = {
                            tab = item
                            if (item == MainTab.TASKS) onRefreshTasks()
                        },
                        icon = {
                            Icon(
                                when (item) {
                                    MainTab.HOME -> Icons.Outlined.Home
                                    MainTab.WORKBENCH -> Icons.Outlined.DashboardCustomize
                                    MainTab.TASKS -> Icons.Outlined.TaskAlt
                                    MainTab.PROFILE -> Icons.Outlined.AccountCircle
                                },
                                item.title,
                            )
                        },
                        label = { Text(item.title) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = BrandGoldDark,
                            selectedTextColor = BrandGoldDark,
                            indicatorColor = MaterialTheme.colorScheme.primaryContainer,
                        ),
                    )
                }
            }
        },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when (tab) {
                MainTab.HOME -> HomeScreen(state.user.username, state.tasks, onFeatureSelected, onTaskSelected)
                MainTab.WORKBENCH -> WorkbenchScreen(state.profile?.get("role")?.asString ?: state.user.role, onModuleSelected)
                MainTab.TASKS -> TasksScreen(state.tasks, state.loading, onRefreshTasks, onTaskSelected)
                MainTab.PROFILE -> ProfileScreen(
                    state.user.username, state.user.email, state.tasks, state.profile,
                    onRefreshProfile, onUpdateProfile, onLogout,
                )
            }
        }
    }
}
