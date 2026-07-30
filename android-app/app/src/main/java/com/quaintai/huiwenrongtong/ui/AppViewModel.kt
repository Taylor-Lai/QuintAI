package com.quaintai.huiwenrongtong.ui

import android.net.Uri
import com.google.gson.JsonObject
import com.google.gson.JsonArray
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.quaintai.huiwenrongtong.data.HuiwenRongtongRepository
import com.quaintai.huiwenrongtong.data.ApiException
import com.quaintai.huiwenrongtong.data.remote.FeatureKind
import com.quaintai.huiwenrongtong.data.remote.PlatformModule
import com.quaintai.huiwenrongtong.data.remote.TaskDto
import com.quaintai.huiwenrongtong.data.remote.UserInfo
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

data class AppUiState(
    val authenticated: Boolean = false,
    val loading: Boolean = false,
    val user: UserInfo = UserInfo(),
    val tasks: List<TaskDto> = emptyList(),
    val moduleData: Map<PlatformModule, JsonObject> = emptyMap(),
    val loadingModules: Set<PlatformModule> = emptySet(),
    val knowledgeSearch: JsonObject? = null,
    val knowledgeDetail: JsonObject? = null,
    val reviewDetail: JsonObject? = null,
    val documentVersions: Map<String, JsonObject> = emptyMap(),
    val resourceComments: Map<String, JsonObject> = emptyMap(),
    val adminUserDetail: JsonObject? = null,
    val profile: JsonObject? = null,
    val message: String? = null,
)

class AppViewModel(private val repository: HuiwenRongtongRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(
        AppUiState(
            authenticated = repository.isAuthenticated,
            user = repository.cachedUser,
        )
    )
    val uiState: StateFlow<AppUiState> = _uiState.asStateFlow()
    private var pollingJob: Job? = null
    private var heartbeatJob: Job? = null

    init {
        if (_uiState.value.authenticated) {
            refreshTasks()
            refreshProfile()
            startHeartbeat()
        }
    }

    fun login(email: String, password: String) = launchAction {
        val user = repository.login(email, password)
        _uiState.update { it.copy(authenticated = true, user = user, message = null) }
        refreshTasks()
        refreshProfile()
        startHeartbeat()
    }

    fun register(username: String, email: String, password: String, onSuccess: () -> Unit) = launchAction {
        val message = repository.register(username, email, password)
        _uiState.update { it.copy(message = message) }
        onSuccess()
    }

    fun logout() {
        viewModelScope.launch {
            pollingJob?.cancel()
            heartbeatJob?.cancel()
            repository.logout()
            _uiState.value = AppUiState()
        }
    }

    fun refreshTasks() {
        if (!_uiState.value.authenticated) return
        viewModelScope.launch {
            runCatching { repository.tasks() }
                .onSuccess { tasks -> _uiState.update { it.copy(tasks = tasks) } }
                .onFailure { showError(it) }
        }
    }

    fun loadTask(id: String) {
        if (!_uiState.value.authenticated) return
        viewModelScope.launch {
            runCatching { repository.task(id) }
                .onSuccess(::replaceTask)
                .onFailure(::showError)
        }
    }

    fun refreshProfile() {
        if (!_uiState.value.authenticated) return
        viewModelScope.launch {
            runCatching { repository.profile() }
                .onSuccess { profile -> _uiState.update { it.copy(profile = profile) } }
                .onFailure(::showError)
        }
    }

    fun updateProfile(nickname: String, email: String, gender: String, phone: String) = launchAction {
        val profile = repository.updateProfile(nickname, email, gender, phone)
        _uiState.update { it.copy(profile = profile, message = "个人资料已更新") }
    }

    fun loadModule(module: PlatformModule) {
        if (!_uiState.value.authenticated || module in _uiState.value.loadingModules) return
        viewModelScope.launch {
            _uiState.update { it.copy(loadingModules = it.loadingModules + module) }
            runCatching { repository.loadModule(module) }
                .onSuccess { data ->
                    _uiState.update { state -> state.copy(moduleData = state.moduleData + (module to data)) }
                }
                .onFailure(::showError)
            _uiState.update { it.copy(loadingModules = it.loadingModules - module) }
        }
    }

    fun createDemoRun(onCreated: (String) -> Unit) = launchAction {
        val taskId = repository.createDemoRun()
        replaceTask(repository.task(taskId))
        onCreated(taskId)
        pollTask(taskId)
    }

    fun uploadWorkspaceDocuments(uris: List<Uri>, category: String, tags: String) = launchAction {
        repository.uploadWorkspaceDocuments(uris, category, tags)
        _uiState.update { it.copy(message = "文档已导入工作台") }
        loadModule(PlatformModule.DOCUMENTS)
        loadModule(PlatformModule.OVERVIEW)
    }

    fun deleteWorkspaceDocument(id: String) = launchAction {
        repository.deleteWorkspaceDocument(id)
        _uiState.update { it.copy(message = "文档已删除") }
        loadModule(PlatformModule.DOCUMENTS)
    }

    fun archiveWorkspaceDocument(id: String, archived: Boolean) = launchAction {
        repository.archiveWorkspaceDocument(id, archived)
        _uiState.update { it.copy(message = if (archived) "文档已归档" else "文档已恢复") }
        loadModule(PlatformModule.DOCUMENTS)
    }

    fun loadDocumentVersions(id: String) = launchAction {
        val versions = repository.documentVersions(id)
        _uiState.update { it.copy(documentVersions = it.documentVersions + (id to versions)) }
    }

    fun createDocumentVersion(id: String, note: String) = launchAction {
        val version = repository.createDocumentVersion(id, note)
        _uiState.update { it.copy(message = "已保存为 v${version.get("version")?.asString ?: "-"}") }
        loadDocumentVersions(id)
    }

    fun downloadWorkspaceDocument(id: String, destination: Uri) = launchAction {
        repository.downloadWorkspaceDocument(id, destination)
        _uiState.update { it.copy(message = "文档已保存") }
    }

    fun loadReviewDetail(id: String) = launchAction {
        val detail = repository.reviewDetail(id)
        _uiState.update { it.copy(reviewDetail = detail) }
        loadComments("review", id)
    }

    fun reviewAction(id: String, fields: JsonArray, note: String, action: String) = launchAction {
        val detail = repository.updateReview(id, fields, note, action)
        _uiState.update { it.copy(reviewDetail = detail) }
        _uiState.update { it.copy(message = if (action == "approve") "复核已通过" else "复核状态已更新") }
        loadModule(PlatformModule.REVIEWS)
    }

    fun autoFixReview(id: String) = launchAction {
        val detail = repository.autoFixReview(id)
        _uiState.update { it.copy(reviewDetail = detail) }
        _uiState.update { it.copy(message = "已完成安全自动修复") }
        loadModule(PlatformModule.REVIEWS)
    }

    fun saveWorkflow(id: String?, name: String, description: String, nodeTypes: List<String>, fields: List<String>, rules: JsonArray) = launchAction {
        repository.saveWorkflow(id, name, description, nodeTypes, fields, rules)
        _uiState.update { it.copy(message = if (id == null) "工作流已创建" else "工作流已更新") }
        loadModule(PlatformModule.WORKFLOWS)
    }

    fun setWorkflowStatus(id: String, status: String) = launchAction {
        repository.setWorkflowStatus(id, status)
        loadModule(PlatformModule.WORKFLOWS)
    }

    fun deleteWorkflow(id: String) = launchAction {
        repository.deleteWorkflow(id)
        _uiState.update { it.copy(message = "工作流已删除") }
        loadModule(PlatformModule.WORKFLOWS)
    }

    fun runWorkflow(id: String, documentId: String) = launchAction {
        repository.runWorkflow(id, documentId)
        _uiState.update { it.copy(message = "工作流已启动") }
        refreshTasks()
    }

    fun createKnowledge(name: String, description: String, retrievalMode: String) = launchAction {
        repository.createKnowledge(name, description, retrievalMode)
        _uiState.update { it.copy(message = "知识集合已创建") }
        loadModule(PlatformModule.KNOWLEDGE)
    }

    fun searchKnowledge(id: String, query: String) = launchAction {
        val result = repository.searchKnowledge(id, query)
        _uiState.update { it.copy(knowledgeSearch = result) }
    }

    fun loadKnowledgeDetail(id: String) = launchAction {
        val result = repository.knowledgeDetail(id)
        _uiState.update { it.copy(knowledgeDetail = result) }
    }

    fun addKnowledgeDocument(id: String, documentId: String) = launchAction {
        repository.addKnowledgeDocument(id, documentId)
        _uiState.update { it.copy(message = "文档已加入知识集合") }
        loadKnowledgeDetail(id)
        loadModule(PlatformModule.KNOWLEDGE)
    }

    fun rebuildKnowledgeGraph(id: String) = launchAction {
        repository.rebuildKnowledgeGraph(id)
        _uiState.update { it.copy(message = "知识图谱已依据最新证据重新构建") }
        loadKnowledgeDetail(id)
    }

    fun reviewKnowledgeEntity(id: String, entityId: String, reviewStatus: String) = launchAction {
        repository.reviewKnowledgeEntity(id, entityId, reviewStatus)
        _uiState.update { it.copy(message = if (reviewStatus == "confirmed") "图谱实体已确认" else "图谱实体已标记存疑") }
        loadKnowledgeDetail(id)
    }

    fun loadComments(resourceType: String, resourceId: String) = launchAction {
        val comments = repository.comments(resourceType, resourceId)
        _uiState.update { it.copy(resourceComments = it.resourceComments + ("$resourceType:$resourceId" to comments)) }
    }

    fun createComment(resourceType: String, resourceId: String, content: String) = launchAction {
        repository.createComment(resourceType, resourceId, content)
        _uiState.update { it.copy(message = "评论已发送") }
        loadComments(resourceType, resourceId)
    }

    fun resolveComment(resourceType: String, resourceId: String, commentId: String) = launchAction {
        repository.resolveComment(commentId)
        loadComments(resourceType, resourceId)
    }

    fun enterpriseAction(action: String, payload: JsonObject) = launchAction {
        val result = repository.enterpriseAction(action, payload)
        val oneTimeSecret = result?.get("key")?.asString ?: result?.get("signing_secret")?.asString
        val message = when {
            oneTimeSecret != null -> "${result?.get("warning")?.asString ?: "密钥仅显示一次"}\n\n$oneTimeSecret"
            result?.get("message") != null -> result.get("message").asString
            else -> "企业配置已更新"
        }
        _uiState.update { it.copy(message = message) }
        loadModule(if (action.startsWith("template.")) PlatformModule.TEMPLATES else PlatformModule.ENTERPRISE)
    }

    fun createBackup() = launchAction {
        repository.createBackup()
        _uiState.update { it.copy(message = "备份已创建") }
        loadModule(PlatformModule.ENTERPRISE)
    }

    fun updateUserStatus(id: String, status: String) = launchAction {
        repository.updateUserStatus(id, status)
        loadModule(PlatformModule.ADMIN)
    }

    fun updateUserRole(id: String, isAdmin: Boolean) = launchAction {
        repository.updateUserRole(id, isAdmin)
        loadModule(PlatformModule.ADMIN)
    }

    fun deleteAdminUser(id: String) = launchAction {
        repository.deleteAdminUser(id)
        _uiState.update { it.copy(message = "用户已删除") }
        loadModule(PlatformModule.ADMIN)
    }

    fun loadAdminUser(id: String) = launchAction {
        val detail = repository.adminUser(id)
        _uiState.update { it.copy(adminUserDetail = detail) }
    }

    fun submit(
        kind: FeatureKind,
        primary: Uri,
        sources: List<Uri>,
        instruction: String,
        onSuccess: () -> Unit,
    ) = launchAction {
        val task = repository.submit(kind, primary, sources, instruction)
        _uiState.update { state -> state.copy(tasks = listOf(task) + state.tasks.filterNot { it.id == task.id }) }
        onSuccess()
        pollTask(task.id)
    }

    fun cancelTask(id: String) = launchAction {
        replaceTask(repository.cancelTask(id))
    }

    fun retryTask(id: String) = launchAction {
        val task = repository.retryTask(id)
        replaceTask(task)
        pollTask(task.id)
    }

    fun deleteTask(id: String) = launchAction {
        repository.deleteTask(id)
        _uiState.update { state -> state.copy(tasks = state.tasks.filterNot { it.id == id }, message = "任务记录已删除") }
    }

    fun downloadTask(id: String, destination: Uri) = launchAction {
        repository.downloadTask(id, destination)
        _uiState.update { it.copy(message = "文件已保存") }
    }

    fun downloadBackup(id: String, destination: Uri) = launchAction {
        repository.downloadBackup(id, destination)
        _uiState.update { it.copy(message = "备份文件已保存") }
    }

    fun dismissMessage() {
        _uiState.update { it.copy(message = null) }
    }

    private fun pollTask(id: String) {
        pollingJob?.cancel()
        pollingJob = viewModelScope.launch {
            while (isActive) {
                val task = runCatching { repository.task(id) }
                    .getOrElse {
                        showError(it)
                        return@launch
                    }
                replaceTask(task)
                if (task.status in TERMINAL_STATUSES) break
                delay(1_500)
            }
        }
    }

    private fun replaceTask(task: TaskDto) {
        _uiState.update { state ->
            state.copy(tasks = listOf(task) + state.tasks.filterNot { it.id == task.id })
        }
    }

    private fun launchAction(block: suspend () -> Unit) {
        viewModelScope.launch {
            _uiState.update { it.copy(loading = true, message = null) }
            runCatching { block() }
                .onFailure(::showError)
            _uiState.update { it.copy(loading = false) }
        }
    }

    private fun showError(error: Throwable) {
        if (error is ApiException && error.statusCode == 401) {
            pollingJob?.cancel()
            heartbeatJob?.cancel()
            repository.clearLocalSession()
            _uiState.value = AppUiState(message = "登录已过期，请重新登录")
            return
        }
        _uiState.update { it.copy(message = error.message ?: "操作失败，请稍后重试") }
    }

    private fun startHeartbeat() {
        heartbeatJob?.cancel()
        heartbeatJob = viewModelScope.launch {
            while (isActive && _uiState.value.authenticated) {
                delay(60_000)
                runCatching { repository.heartbeat() }.onFailure(::showError)
            }
        }
    }

    class Factory(private val repository: HuiwenRongtongRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T =
            AppViewModel(repository) as T
    }

    private companion object {
        val TERMINAL_STATUSES = setOf("succeeded", "failed", "cancelled")
    }
}
