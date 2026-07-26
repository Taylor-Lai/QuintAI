package com.quaintai.huiwenrongtong.data

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.google.gson.JsonParser
import com.google.gson.JsonObject
import com.quaintai.huiwenrongtong.data.local.TokenStore
import com.quaintai.huiwenrongtong.data.remote.HuiwenRongtongApi
import com.quaintai.huiwenrongtong.data.remote.FeatureKind
import com.quaintai.huiwenrongtong.data.remote.LoginRequest
import com.quaintai.huiwenrongtong.data.remote.PlatformModule
import com.quaintai.huiwenrongtong.data.remote.RegisterRequest
import com.quaintai.huiwenrongtong.data.remote.TaskDto
import com.quaintai.huiwenrongtong.data.remote.UserInfo
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.HttpException
import java.io.IOException
import java.net.SocketTimeoutException

class ApiException(val statusCode: Int, override val message: String) : IOException(message)

class HuiwenRongtongRepository(
    private val context: Context,
    private val api: HuiwenRongtongApi,
    private val tokenStore: TokenStore,
) {
    val isAuthenticated: Boolean get() = tokenStore.readToken() != null
    val cachedUser: UserInfo
        get() = UserInfo(username = tokenStore.username(), email = tokenStore.email(), role = tokenStore.role())

    suspend fun login(email: String, password: String): UserInfo = apiCall {
        val response = api.login(LoginRequest(email.trim(), password))
        tokenStore.saveSession(
            response.accessToken,
            response.userInfo.username,
            response.userInfo.email,
            response.userInfo.role,
        )
        response.userInfo
    }

    suspend fun profile(): JsonObject = apiCall { api.profile() }

    suspend fun updateProfile(nickname: String, email: String, gender: String, phone: String): JsonObject = apiCall {
        api.updateProfile(JsonObject().apply {
            addProperty("nickname", nickname)
            addProperty("email", email)
            addProperty("gender", gender)
            addProperty("phone", phone)
        })
    }

    suspend fun register(username: String, email: String, password: String): String = apiCall {
        api.register(RegisterRequest(username.trim(), email.trim(), password)).message
    }

    suspend fun logout() {
        runCatching { api.logout() }
        tokenStore.clear()
    }

    suspend fun heartbeat() = apiCall { api.heartbeat() }
    fun clearLocalSession() = tokenStore.clear()

    suspend fun tasks(): List<TaskDto> = apiCall { api.tasks().items }
    suspend fun task(id: String): TaskDto = apiCall { api.task(id) }
    suspend fun cancelTask(id: String): TaskDto = apiCall { api.cancelTask(id) }
    suspend fun retryTask(id: String): TaskDto = apiCall { api.retryTask(id) }

    suspend fun loadModule(module: PlatformModule): JsonObject = apiCall {
        when (module) {
            PlatformModule.OVERVIEW -> api.workspaceOverview()
            PlatformModule.DOCUMENTS -> api.workspaceDocuments()
            PlatformModule.REVIEWS -> api.workspaceReviews()
            PlatformModule.WORKFLOWS -> api.workspaceWorkflows()
            PlatformModule.EXECUTIONS -> JsonObject().apply {
                add("items", JsonParser.parseString(com.google.gson.Gson().toJson(api.tasks().items)))
            }
            PlatformModule.KNOWLEDGE -> api.knowledgeCollections()
            PlatformModule.ENTERPRISE -> JsonObject().apply {
                add("dashboard", api.enterpriseDashboard())
                runCatching { api.organization() }.getOrNull()?.let { add("organization", it) }
                runCatching { api.organizations() }.getOrNull()?.let { add("organizations", it) }
                runCatching { api.auditLogs() }.getOrNull()?.let { add("audit_logs", it) }
                runCatching { api.apiKeys() }.getOrNull()?.let { add("api_keys", it) }
                runCatching { api.webhooks() }.getOrNull()?.let { add("webhooks", it) }
                runCatching { api.webhookDeliveries() }.getOrNull()?.let { add("webhook_deliveries", it) }
                runCatching { api.schedules() }.getOrNull()?.let { add("schedules", it) }
                runCatching { api.operations() }.getOrNull()?.let { add("operations", it) }
                runCatching { api.backups() }.getOrNull()?.let { add("backups", it) }
            }
            PlatformModule.ADMIN -> JsonObject().apply {
                add("statistics", api.adminStatistics())
                add("users", api.adminUsers())
            }
            PlatformModule.TEMPLATES, PlatformModule.EDITOR, PlatformModule.GUIDE -> JsonObject()
        }
    }

    suspend fun createDemoRun(): String = apiCall {
        api.createDemoRun().get("task_id")?.asString ?: error("演示任务创建失败")
    }

    suspend fun uploadWorkspaceDocuments(uris: List<Uri>, category: String, tags: String) = apiCall {
        api.uploadWorkspaceDocuments(
            files = uris.map { part("files", it) },
            category = category.toTextBody(),
            tags = tags.toTextBody(),
        )
    }

    suspend fun deleteWorkspaceDocument(id: String) = apiCall { api.deleteWorkspaceDocument(id) }

    suspend fun archiveWorkspaceDocument(id: String, archived: Boolean) = apiCall {
        api.updateWorkspaceDocument(id, JsonObject().apply {
            addProperty("status", if (archived) "archived" else "ready")
        })
    }

    suspend fun downloadWorkspaceDocument(id: String, destination: Uri) = apiCall {
        val body = api.downloadWorkspaceDocument(id)
        context.contentResolver.openOutputStream(destination, "w")?.use { output ->
            body.byteStream().use { input -> input.copyTo(output) }
        } ?: error("无法写入目标文件")
    }

    suspend fun reviewDetail(id: String) = apiCall { api.review(id) }

    suspend fun updateReview(id: String, fields: com.google.gson.JsonArray, note: String, action: String) = apiCall {
        api.updateReview(id, JsonObject().apply {
            add("fields", fields)
            addProperty("note", note)
            addProperty("action", action)
        })
    }

    suspend fun autoFixReview(id: String) = apiCall { api.autoFixReview(id) }

    suspend fun saveWorkflow(
        id: String?, name: String, description: String, nodeTypes: List<String>,
        fields: List<String>, rules: com.google.gson.JsonArray,
    ) = apiCall {
        val labels = mapOf(
            "intake" to "材料接收", "extract" to "信息提取", "validate" to "字段校验",
            "review" to "人工复核", "export" to "结果导出", "notify" to "消息通知",
        )
        val nodeFields = com.google.gson.JsonArray().apply { fields.forEach(::add) }
        val nodes = com.google.gson.JsonArray().apply {
            nodeTypes.forEachIndexed { index, type ->
                add(JsonObject().apply {
                    addProperty("id", "node-${index + 1}")
                    addProperty("type", type)
                    addProperty("label", labels[type] ?: type)
                    addProperty("order", index + 1)
                    if (type == "extract") add("fields", nodeFields)
                })
            }
        }
        val payload = JsonObject().apply {
            addProperty("name", name)
            addProperty("description", description)
            add("nodes", nodes)
            add("rules", rules)
        }
        if (id == null) api.createWorkflow(payload) else api.updateWorkflow(id, payload)
    }

    suspend fun setWorkflowStatus(id: String, status: String) = apiCall {
        api.updateWorkflow(id, JsonObject().apply { addProperty("status", status) })
    }

    suspend fun deleteWorkflow(id: String) = apiCall { api.deleteWorkflow(id) }

    suspend fun runWorkflow(id: String, documentId: String) = apiCall {
        api.runWorkflow(id, JsonObject().apply { addProperty("document_id", documentId) })
    }

    suspend fun createKnowledge(name: String, description: String, retrievalMode: String) = apiCall {
        api.createKnowledge(JsonObject().apply {
            addProperty("name", name)
            addProperty("description", description)
            addProperty("retrieval_mode", retrievalMode)
        })
    }

    suspend fun searchKnowledge(id: String, query: String) = apiCall { api.searchKnowledge(id, query) }
    suspend fun knowledgeDetail(id: String): JsonObject = apiCall {
        JsonObject().apply {
            add("documents", api.knowledgeDocuments(id))
            add("graph", api.knowledgeGraph(id))
        }
    }

    suspend fun addKnowledgeDocument(id: String, documentId: String) = apiCall {
        api.addKnowledgeDocument(id, JsonObject().apply { addProperty("document_id", documentId) })
    }

    suspend fun comments(resourceType: String, resourceId: String) = apiCall { api.comments(resourceType, resourceId) }

    suspend fun createComment(resourceType: String, resourceId: String, content: String) = apiCall {
        api.createComment(JsonObject().apply {
            addProperty("resource_type", resourceType)
            addProperty("resource_id", resourceId)
            addProperty("content", content)
            add("mentions", com.google.gson.JsonArray())
        })
    }

    suspend fun resolveComment(id: String) = apiCall { api.resolveComment(id) }
    suspend fun documentVersions(id: String) = apiCall { api.documentVersions(id) }
    suspend fun createDocumentVersion(id: String, note: String) = apiCall { api.createDocumentVersion(id, note) }
    suspend fun adminUser(id: String) = apiCall { api.adminUser(id) }

    suspend fun enterpriseAction(action: String, payload: JsonObject): JsonObject? = apiCall {
        when (action) {
            "organization.rename" -> api.updateOrganization(payload)
            "organization.activate" -> api.activateOrganization(payload.get("id").asString)
            "member.add" -> api.addMember(payload)
            "member.role" -> api.updateMember(payload.get("id").asString, JsonObject().apply { addProperty("role", payload.get("role").asString) })
            "member.remove" -> { api.removeMember(payload.get("id").asString); null }
            "api_key.create" -> api.createApiKey(payload)
            "api_key.revoke" -> { api.revokeApiKey(payload.get("id").asString); null }
            "webhook.create" -> api.createWebhook(payload)
            "webhook.test" -> api.testWebhook(payload.get("id").asString)
            "webhook.delete" -> { api.deleteWebhook(payload.get("id").asString); null }
            "schedule.create" -> api.createSchedule(payload)
            "schedule.delete" -> { api.deleteSchedule(payload.get("id").asString); null }
            "subscription.change" -> api.changePlan(payload)
            "comment.create" -> api.createComment(payload)
            "comment.resolve" -> api.resolveComment(payload.get("id").asString)
            "document.version" -> api.createDocumentVersion(payload.get("id").asString, payload.get("note")?.asString.orEmpty())
            else -> error("不支持的企业操作：$action")
        }
    }

    suspend fun createBackup() = apiCall { api.createBackup() }
    suspend fun updateUserStatus(id: String, status: String) = apiCall { api.updateUserStatus(id, status) }
    suspend fun updateUserRole(id: String, isAdmin: Boolean) = apiCall { api.updateUserRole(id, isAdmin) }
    suspend fun deleteAdminUser(id: String) = apiCall { api.deleteAdminUser(id) }

    suspend fun submit(
        kind: FeatureKind,
        primary: Uri,
        sources: List<Uri>,
        instruction: String,
    ): TaskDto = apiCall {
        when (kind) {
            FeatureKind.EDIT -> api.editDocument(
                document = part("document", primary),
                command = instruction.toTextBody(),
            )
            FeatureKind.EXTRACT -> api.extractDocument(
                file = part("file", primary),
                fields = instruction.toTextBody(),
            )
            FeatureKind.TABLE -> api.fillTable(
                template = part("template", primary),
                documents = sources.map { part("documents", it) },
                userRequest = instruction.toTextBody(),
            )
        }
    }

    suspend fun downloadTask(id: String, destination: Uri) = apiCall {
        val body = api.downloadTask(id)
        context.contentResolver.openOutputStream(destination, "w")?.use { output ->
            body.byteStream().use { input -> input.copyTo(output) }
        } ?: error("无法写入目标文件")
    }

    fun displayName(uri: Uri): String {
        context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)
            ?.use { cursor ->
                if (cursor.moveToFirst()) {
                    return cursor.getString(0)
                }
            }
        return uri.lastPathSegment ?: "未命名文件"
    }

    private fun part(field: String, uri: Uri): MultipartBody.Part {
        val resolver = context.contentResolver
        val mime = resolver.getType(uri)?.toMediaTypeOrNull()
        return MultipartBody.Part.createFormData(
            field,
            displayName(uri),
            ContentUriRequestBody(resolver, uri, mime),
        )
    }

    private fun String.toTextBody() = toRequestBody("text/plain; charset=utf-8".toMediaTypeOrNull())

    private suspend fun <T> apiCall(block: suspend () -> T): T = try {
        block()
    } catch (error: HttpException) {
        val detail = runCatching {
            JsonParser.parseString(error.response()?.errorBody()?.string()).asJsonObject
                .get("detail")?.asString
        }.getOrNull()
        throw ApiException(error.code(), detail ?: "请求失败（${error.code()}）")
    } catch (_: SocketTimeoutException) {
        throw IOException("请求超时，请检查网络后重试")
    } catch (error: IOException) {
        throw IOException("网络连接失败，请检查网络和服务器状态", error)
    }
}
