package com.zhihuiwenshu.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.zhihuiwenshu.app.ui.AppViewModel
import com.zhihuiwenshu.app.ui.ZhihuiWenshuApp
import com.zhihuiwenshu.app.ui.theme.ZhihuiWenshuTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val container = (application as ZhihuiWenshuApplication).container

        setContent {
            val appViewModel: AppViewModel = viewModel(factory = AppViewModel.Factory(container.repository))
            val uiState by appViewModel.uiState.collectAsStateWithLifecycle()

            ZhihuiWenshuTheme {
                ZhihuiWenshuApp(
                    state = uiState,
                    onLogin = appViewModel::login,
                    onRegister = appViewModel::register,
                    onLogout = appViewModel::logout,
                    onRefreshTasks = appViewModel::refreshTasks,
                    onOpenTask = appViewModel::loadTask,
                    onLoadModule = appViewModel::loadModule,
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
                    onCreateBackup = appViewModel::createBackup,
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
                    onDownloadTask = appViewModel::downloadTask,
                    onDismissMessage = appViewModel::dismissMessage,
                )
            }
        }
    }
}
