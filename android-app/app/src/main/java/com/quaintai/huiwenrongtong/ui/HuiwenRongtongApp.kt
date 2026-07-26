package com.quaintai.huiwenrongtong.ui

import android.net.Uri
import com.google.gson.JsonObject
import com.google.gson.JsonArray
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.quaintai.huiwenrongtong.data.remote.FeatureKind
import com.quaintai.huiwenrongtong.data.remote.PlatformModule
import com.quaintai.huiwenrongtong.ui.screens.AuthScreen
import com.quaintai.huiwenrongtong.ui.screens.MainShell
import com.quaintai.huiwenrongtong.ui.screens.RemoteModuleScreen
import com.quaintai.huiwenrongtong.ui.screens.TemplateLibraryScreen
import com.quaintai.huiwenrongtong.ui.screens.TemplateEditorScreen
import com.quaintai.huiwenrongtong.ui.screens.GuideScreen
import com.quaintai.huiwenrongtong.ui.screens.DocumentLibraryScreen
import com.quaintai.huiwenrongtong.ui.screens.ReviewCenterScreen
import com.quaintai.huiwenrongtong.ui.screens.WorkflowCenterScreen
import com.quaintai.huiwenrongtong.ui.screens.KnowledgeCenterScreen
import com.quaintai.huiwenrongtong.ui.screens.EnterpriseCenterScreen
import com.quaintai.huiwenrongtong.ui.screens.AdminCenterScreen
import com.quaintai.huiwenrongtong.ui.screens.TaskDetailScreen
import com.quaintai.huiwenrongtong.ui.screens.UploadScreen

@Composable
fun HuiwenRongtongApp(
    state: AppUiState,
    onLogin: (String, String) -> Unit,
    onRegister: (String, String, String, () -> Unit) -> Unit,
    onLogout: () -> Unit,
    onRefreshTasks: () -> Unit,
    onOpenTask: (String) -> Unit,
    onLoadModule: (PlatformModule) -> Unit,
    onUploadWorkspaceDocuments: (List<Uri>, String, String) -> Unit,
    onDeleteWorkspaceDocument: (String) -> Unit,
    onArchiveWorkspaceDocument: (String, Boolean) -> Unit,
    onLoadDocumentVersions: (String) -> Unit,
    onCreateDocumentVersion: (String, String) -> Unit,
    onDownloadWorkspaceDocument: (String, Uri) -> Unit,
    onLoadReviewDetail: (String) -> Unit,
    onReviewAction: (String, JsonArray, String, String) -> Unit,
    onAutoFixReview: (String) -> Unit,
    onSaveWorkflow: (String?, String, String, List<String>, List<String>, JsonArray) -> Unit,
    onSetWorkflowStatus: (String, String) -> Unit,
    onDeleteWorkflow: (String) -> Unit,
    onRunWorkflow: (String, String) -> Unit,
    onCreateKnowledge: (String, String, String) -> Unit,
    onSearchKnowledge: (String, String) -> Unit,
    onLoadKnowledgeDetail: (String) -> Unit,
    onAddKnowledgeDocument: (String, String) -> Unit,
    onCreateBackup: () -> Unit,
    onEnterpriseAction: (String, JsonObject) -> Unit,
    onCreateComment: (String, String, String) -> Unit,
    onResolveComment: (String, String, String) -> Unit,
    onUpdateUserStatus: (String, String) -> Unit,
    onUpdateUserRole: (String, Boolean) -> Unit,
    onDeleteAdminUser: (String) -> Unit,
    onLoadAdminUser: (String) -> Unit,
    onRefreshProfile: () -> Unit,
    onUpdateProfile: (String, String, String, String) -> Unit,
    onSubmit: (FeatureKind, Uri, List<Uri>, String, () -> Unit) -> Unit,
    onCancelTask: (String) -> Unit,
    onRetryTask: (String) -> Unit,
    onDownloadTask: (String, Uri) -> Unit,
    onDismissMessage: () -> Unit,
) {
    if (!state.authenticated) {
        AuthScreen(loading = state.loading, onLogin = onLogin, onRegister = onRegister)
    } else {
        val navController = rememberNavController()
        NavHost(navController = navController, startDestination = "main") {
            composable("main") {
                MainShell(
                    state = state,
                    onFeatureSelected = { navController.navigate("upload/${it.name}") },
                    onTaskSelected = { task ->
                        onOpenTask(task.id)
                        navController.navigate("task/${task.id}")
                    },
                    onModuleSelected = { module ->
                        if (module !in setOf(PlatformModule.TEMPLATES, PlatformModule.EDITOR, PlatformModule.GUIDE)) {
                            onLoadModule(module)
                            if (module == PlatformModule.DOCUMENTS) onLoadModule(PlatformModule.WORKFLOWS)
                        }
                        navController.navigate("module/${module.name}")
                    },
                    onRefreshTasks = onRefreshTasks,
                    onRefreshProfile = onRefreshProfile,
                    onUpdateProfile = onUpdateProfile,
                    onLogout = onLogout,
                )
            }
            composable("upload/{kind}") { entry ->
                val kind = runCatching { FeatureKind.valueOf(entry.arguments?.getString("kind").orEmpty()) }
                    .getOrDefault(FeatureKind.EDIT)
                UploadScreen(
                    kind = kind,
                    loading = state.loading,
                    onBack = { navController.popBackStack() },
                    onSubmit = { primary, sources, instruction ->
                        onSubmit(kind, primary, sources, instruction) { navController.popBackStack() }
                    },
                )
            }
            composable("task/{id}") { entry ->
                val id = entry.arguments?.getString("id").orEmpty()
                state.tasks.firstOrNull { it.id == id }?.let { task ->
                    TaskDetailScreen(
                        task = task,
                        onBack = { navController.popBackStack() },
                        onCancel = onCancelTask,
                        onRetry = onRetryTask,
                        onDownload = onDownloadTask,
                    )
                }
            }
            composable("module/{name}") { entry ->
                val module = runCatching { PlatformModule.valueOf(entry.arguments?.getString("name").orEmpty()) }
                    .getOrDefault(PlatformModule.OVERVIEW)
                when (module) {
                    PlatformModule.TEMPLATES -> TemplateLibraryScreen(
                        onBack = { navController.popBackStack() },
                        onEditor = { navController.navigate("module/${PlatformModule.EDITOR.name}") },
                        onUse = { navController.navigate("upload/${FeatureKind.TABLE.name}") },
                    )
                    PlatformModule.EDITOR -> TemplateEditorScreen(onBack = { navController.popBackStack() })
                    PlatformModule.GUIDE -> GuideScreen(onBack = { navController.popBackStack() })
                    PlatformModule.DOCUMENTS -> DocumentLibraryScreen(
                        data = state.moduleData[module], loading = module in state.loadingModules,
                        onBack = { navController.popBackStack() }, onRefresh = { onLoadModule(module) },
                        onUpload = onUploadWorkspaceDocuments, onDelete = onDeleteWorkspaceDocument,
                        onDownload = onDownloadWorkspaceDocument, onArchive = onArchiveWorkspaceDocument,
                        versions = state.documentVersions, onLoadVersions = onLoadDocumentVersions,
                        onCreateVersion = onCreateDocumentVersion,
                        workflowData = state.moduleData[PlatformModule.WORKFLOWS], onRunWorkflow = onRunWorkflow,
                    )
                    PlatformModule.REVIEWS -> ReviewCenterScreen(
                        data = state.moduleData[module], loading = module in state.loadingModules,
                        onBack = { navController.popBackStack() }, onRefresh = { onLoadModule(module) },
                        detail = state.reviewDetail,
                        comments = state.reviewDetail?.strForKey()?.let { state.resourceComments["review:$it"] },
                        onSelect = onLoadReviewDetail, onAction = onReviewAction, onAutoFix = onAutoFixReview,
                        onComment = { id, content -> onCreateComment("review", id, content) },
                        onResolveComment = { id, commentId -> onResolveComment("review", id, commentId) },
                    )
                    PlatformModule.WORKFLOWS -> WorkflowCenterScreen(
                        data = state.moduleData[module], loading = module in state.loadingModules,
                        onBack = { navController.popBackStack() }, onRefresh = { onLoadModule(module) },
                        onSave = onSaveWorkflow, onStatus = onSetWorkflowStatus,
                        onDelete = onDeleteWorkflow, onRun = onRunWorkflow,
                    )
                    PlatformModule.KNOWLEDGE -> KnowledgeCenterScreen(
                        data = state.moduleData[module], searchData = state.knowledgeSearch,
                        loading = module in state.loadingModules, onBack = { navController.popBackStack() },
                        detailData = state.knowledgeDetail,
                        onRefresh = { onLoadModule(module) }, onCreate = onCreateKnowledge, onSearch = onSearchKnowledge,
                        onSelect = onLoadKnowledgeDetail, onAttach = onAddKnowledgeDocument,
                    )
                    PlatformModule.ENTERPRISE -> EnterpriseCenterScreen(
                        data = state.moduleData[module], loading = module in state.loadingModules,
                        onBack = { navController.popBackStack() }, onRefresh = { onLoadModule(module) },
                        onBackup = onCreateBackup, onAction = onEnterpriseAction,
                    )
                    PlatformModule.ADMIN -> AdminCenterScreen(
                        data = state.moduleData[module], loading = module in state.loadingModules,
                        onBack = { navController.popBackStack() }, onRefresh = { onLoadModule(module) },
                        detail = state.adminUserDetail, onDetail = onLoadAdminUser,
                        onStatus = onUpdateUserStatus, onRole = onUpdateUserRole, onDelete = onDeleteAdminUser,
                    )
                    else -> RemoteModuleScreen(
                        module = module,
                        data = state.moduleData[module],
                        loading = module in state.loadingModules,
                        onBack = { navController.popBackStack() },
                        onRefresh = { onLoadModule(module) },
                    )
                }
            }
        }
    }

    state.message?.let { message ->
        AlertDialog(
            onDismissRequest = onDismissMessage,
            confirmButton = { TextButton(onClick = onDismissMessage) { Text("知道了") } },
            text = { Text(message) },
        )
    }
}

private fun JsonObject.strForKey(): String = get("id")?.takeIf { it.isJsonPrimitive }?.asString.orEmpty()
