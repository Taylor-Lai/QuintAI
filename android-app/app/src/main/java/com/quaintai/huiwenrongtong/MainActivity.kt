package com.quaintai.huiwenrongtong

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.quaintai.huiwenrongtong.ui.AppViewModel
import com.quaintai.huiwenrongtong.ui.HuiwenRongtongApp
import com.quaintai.huiwenrongtong.ui.theme.HuiwenRongtongTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val container = (application as HuiwenRongtongApplication).container

        setContent {
            val appViewModel: AppViewModel = viewModel(factory = AppViewModel.Factory(container.repository))
            val uiState by appViewModel.uiState.collectAsStateWithLifecycle()

            HuiwenRongtongTheme {
                HuiwenRongtongApp(
                    state = uiState,
                    onLogin = appViewModel::login,
                    onRegister = appViewModel::register,
                    onLogout = appViewModel::logout,
                    onRefreshTasks = appViewModel::refreshTasks,
                    onOpenTask = appViewModel::loadTask,
                    onLoadModule = appViewModel::loadModule,
                    onCreateDemoRun = appViewModel::createDemoRun,
                    onUploadWorkspaceDocuments = appViewModel::uploadWorkspaceDocuments,
                    onDeleteWorkspaceDocument = appViewModel::deleteWorkspaceDocument,
                    onArchiveWorkspaceDocument = appViewModel::archiveWorkspaceDocument,
                    onLoadDocumentVersions = appViewModel::loadDocumentVersions,
                    onCreateDocumentVersion = appViewModel::createDocumentVersion,
                    onDownloadWorkspaceDocument = appViewModel::downloadWorkspaceDocument,
                    onLoadReviewDetail = appViewModel::loadReviewDetail,
                    onReviewAction = appViewModel::reviewAction,
                    onAutoFixReview = appViewModel::autoFixReview,
                    onSaveWorkflow = appViewModel::saveWorkflow,
                    onSetWorkflowStatus = appViewModel::setWorkflowStatus,
                    onDeleteWorkflow = appViewModel::deleteWorkflow,
                    onRunWorkflow = appViewModel::runWorkflow,
                    onCreateKnowledge = appViewModel::createKnowledge,
                    onSearchKnowledge = appViewModel::searchKnowledge,
                    onLoadKnowledgeDetail = appViewModel::loadKnowledgeDetail,
                    onAddKnowledgeDocument = appViewModel::addKnowledgeDocument,
                    onRebuildKnowledgeGraph = appViewModel::rebuildKnowledgeGraph,
                    onReviewKnowledgeEntity = appViewModel::reviewKnowledgeEntity,
                    onCreateBackup = appViewModel::createBackup,
                    onDownloadBackup = appViewModel::downloadBackup,
                    onEnterpriseAction = appViewModel::enterpriseAction,
                    onCreateComment = appViewModel::createComment,
                    onResolveComment = appViewModel::resolveComment,
                    onUpdateUserStatus = appViewModel::updateUserStatus,
                    onUpdateUserRole = appViewModel::updateUserRole,
                    onDeleteAdminUser = appViewModel::deleteAdminUser,
                    onLoadAdminUser = appViewModel::loadAdminUser,
                    onRefreshProfile = appViewModel::refreshProfile,
                    onUpdateProfile = appViewModel::updateProfile,
                    onSubmit = appViewModel::submit,
                    onCancelTask = appViewModel::cancelTask,
                    onRetryTask = appViewModel::retryTask,
                    onDeleteTask = appViewModel::deleteTask,
                    onDownloadTask = appViewModel::downloadTask,
                    onDismissMessage = appViewModel::dismissMessage,
                )
            }
        }
    }
}
