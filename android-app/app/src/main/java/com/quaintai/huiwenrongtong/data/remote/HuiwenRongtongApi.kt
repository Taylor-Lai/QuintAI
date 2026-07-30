package com.quaintai.huiwenrongtong.data.remote

import com.google.gson.JsonObject
import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.PUT
import retrofit2.http.Query

interface HuiwenRongtongApi {
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @POST("auth/register")
    suspend fun register(@Body request: RegisterRequest): RegisterResponse

    @POST("auth/logout")
    suspend fun logout()

    @POST("auth/heartbeat")
    suspend fun heartbeat(): JsonObject

    @GET("user/profile")
    suspend fun profile(): JsonObject

    @PUT("user/profile")
    suspend fun updateProfile(@Body payload: JsonObject): JsonObject

    @GET("tasks")
    suspend fun tasks(): TaskListResponse

    @GET("tasks/{id}")
    suspend fun task(@Path("id") id: String): TaskDto

    @POST("tasks/{id}/cancel")
    suspend fun cancelTask(@Path("id") id: String): TaskDto

    @POST("tasks/{id}/retry")
    suspend fun retryTask(@Path("id") id: String): TaskDto

    @DELETE("tasks/{id}")
    suspend fun deleteTask(@Path("id") id: String)

    @GET("tasks/{id}/download")
    suspend fun downloadTask(@Path("id") id: String): ResponseBody

    @GET("tasks/{id}/report")
    suspend fun taskReport(@Path("id") id: String): JsonObject

    @GET("workspace/overview")
    suspend fun workspaceOverview(): JsonObject

    @GET("workspace/documents")
    suspend fun workspaceDocuments(): JsonObject

    @GET("workspace/reviews")
    suspend fun workspaceReviews(): JsonObject

    @GET("workspace/workflows")
    suspend fun workspaceWorkflows(): JsonObject

    @GET("workspace/workflow-runs")
    suspend fun workflowRuns(): JsonObject

    @GET("enterprise/knowledge")
    suspend fun knowledgeCollections(): JsonObject

    @GET("enterprise/dashboard")
    suspend fun enterpriseDashboard(): JsonObject

    @GET("enterprise/organization")
    suspend fun organization(): JsonObject

    @GET("enterprise/organizations")
    suspend fun organizations(): JsonObject

    @POST("enterprise/organizations/{id}/activate")
    suspend fun activateOrganization(@Path("id") id: String): JsonObject

    @PUT("enterprise/organization")
    suspend fun updateOrganization(@Body payload: JsonObject): JsonObject

    @POST("enterprise/members")
    suspend fun addMember(@Body payload: JsonObject): JsonObject

    @PUT("enterprise/members/{id}")
    suspend fun updateMember(@Path("id") id: String, @Body payload: JsonObject): JsonObject

    @DELETE("enterprise/members/{id}")
    suspend fun removeMember(@Path("id") id: String)

    @GET("enterprise/audit-logs")
    suspend fun auditLogs(): JsonObject

    @GET("enterprise/api-keys")
    suspend fun apiKeys(): JsonObject

    @GET("enterprise/webhooks")
    suspend fun webhooks(): JsonObject

    @GET("enterprise/webhook-deliveries")
    suspend fun webhookDeliveries(): JsonObject

    @GET("enterprise/templates")
    suspend fun templates(): JsonObject

    @GET("enterprise/schedules")
    suspend fun schedules(): JsonObject

    @GET("enterprise/operations")
    suspend fun operations(): JsonObject

    @GET("enterprise/backups")
    suspend fun backups(): JsonObject

    @GET("enterprise/comments")
    suspend fun comments(@Query("resource_type") resourceType: String, @Query("resource_id") resourceId: String): JsonObject

    @GET("admin/statistics")
    suspend fun adminStatistics(): JsonObject

    @GET("admin/users")
    suspend fun adminUsers(): JsonObject

    @GET("admin/users/{id}")
    suspend fun adminUser(@Path("id") id: String): JsonObject

    @POST("workspace/demo")
    suspend fun createDemoRun(): JsonObject

    @Multipart
    @POST("workspace/documents")
    suspend fun uploadWorkspaceDocuments(
        @Part files: List<MultipartBody.Part>,
        @Part("category") category: RequestBody,
        @Part("tags") tags: RequestBody,
    ): JsonObject

    @DELETE("workspace/documents/{id}")
    suspend fun deleteWorkspaceDocument(@Path("id") id: String)

    @PATCH("workspace/documents/{id}")
    suspend fun updateWorkspaceDocument(@Path("id") id: String, @Body payload: JsonObject): JsonObject

    @GET("workspace/documents/{id}/download")
    suspend fun downloadWorkspaceDocument(@Path("id") id: String): ResponseBody

    @GET("workspace/reviews/{id}")
    suspend fun review(@Path("id") id: String): JsonObject

    @PUT("workspace/reviews/{id}")
    suspend fun updateReview(@Path("id") id: String, @Body payload: JsonObject): JsonObject

    @POST("workspace/reviews/{id}/auto-fix")
    suspend fun autoFixReview(@Path("id") id: String): JsonObject

    @POST("workspace/workflows")
    suspend fun createWorkflow(@Body payload: JsonObject): JsonObject

    @PUT("workspace/workflows/{id}")
    suspend fun updateWorkflow(@Path("id") id: String, @Body payload: JsonObject): JsonObject

    @DELETE("workspace/workflows/{id}")
    suspend fun deleteWorkflow(@Path("id") id: String)

    @POST("workspace/workflows/{id}/runs")
    suspend fun runWorkflow(@Path("id") id: String, @Body payload: JsonObject): JsonObject

    @POST("enterprise/knowledge")
    suspend fun createKnowledge(@Body payload: JsonObject): JsonObject

    @GET("enterprise/knowledge/{id}/search")
    suspend fun searchKnowledge(@Path("id") id: String, @Query("query") query: String, @Query("limit") limit: Int = 10): JsonObject

    @POST("enterprise/knowledge/{id}/documents")
    suspend fun addKnowledgeDocument(@Path("id") id: String, @Body payload: JsonObject): JsonObject

    @GET("enterprise/knowledge/{id}/documents")
    suspend fun knowledgeDocuments(@Path("id") id: String): JsonObject

    @GET("enterprise/knowledge/{id}/graph")
    suspend fun knowledgeGraph(@Path("id") id: String): JsonObject

    @POST("enterprise/knowledge/{id}/graph/rebuild")
    suspend fun rebuildKnowledgeGraph(@Path("id") id: String): JsonObject

    @PATCH("enterprise/knowledge/{id}/graph/entities/{entityId}")
    suspend fun reviewKnowledgeEntity(@Path("id") id: String, @Path("entityId") entityId: String, @Body payload: JsonObject): JsonObject

    @POST("enterprise/api-keys")
    suspend fun createApiKey(@Body payload: JsonObject): JsonObject

    @DELETE("enterprise/api-keys/{id}")
    suspend fun revokeApiKey(@Path("id") id: String)

    @POST("enterprise/webhooks")
    suspend fun createWebhook(@Body payload: JsonObject): JsonObject

    @DELETE("enterprise/webhooks/{id}")
    suspend fun deleteWebhook(@Path("id") id: String)

    @POST("enterprise/webhooks/{id}/test")
    suspend fun testWebhook(@Path("id") id: String): JsonObject

    @POST("enterprise/schedules")
    suspend fun createSchedule(@Body payload: JsonObject): JsonObject

    @DELETE("enterprise/schedules/{id}")
    suspend fun deleteSchedule(@Path("id") id: String)

    @PUT("enterprise/subscription")
    suspend fun changePlan(@Body payload: JsonObject): JsonObject

    @POST("enterprise/comments")
    suspend fun createComment(@Body payload: JsonObject): JsonObject

    @PATCH("enterprise/comments/{id}/resolve")
    suspend fun resolveComment(@Path("id") id: String): JsonObject

    @GET("enterprise/documents/{id}/versions")
    suspend fun documentVersions(@Path("id") id: String): JsonObject

    @POST("enterprise/documents/{id}/versions")
    suspend fun createDocumentVersion(@Path("id") id: String, @Query("note") note: String): JsonObject

    @POST("enterprise/backups")
    suspend fun createBackup(): JsonObject

    @GET("enterprise/backups/{id}/download")
    suspend fun downloadBackup(@Path("id") id: String): ResponseBody

    @POST("enterprise/templates")
    suspend fun createTemplate(@Body payload: JsonObject): JsonObject

    @PUT("enterprise/templates/{id}")
    suspend fun updateTemplate(@Path("id") id: String, @Body payload: JsonObject): JsonObject

    @DELETE("enterprise/templates/{id}")
    suspend fun deleteTemplate(@Path("id") id: String)

    @DELETE("admin/users/{id}")
    suspend fun deleteAdminUser(@Path("id") id: String)

    @PUT("admin/users/{id}/status")
    suspend fun updateUserStatus(@Path("id") id: String, @Query("account_status") status: String): JsonObject

    @PUT("admin/users/{id}/role")
    suspend fun updateUserRole(@Path("id") id: String, @Query("is_admin") isAdmin: Boolean): JsonObject

    @Multipart
    @POST("doc-chat/upload")
    suspend fun editDocument(
        @Part document: MultipartBody.Part,
        @Part("command") command: RequestBody,
    ): TaskDto

    @Multipart
    @POST("doc-extract/upload")
    suspend fun extractDocument(
        @Part file: MultipartBody.Part,
        @Part("fields") fields: RequestBody,
    ): TaskDto

    @Multipart
    @POST("table-fill/upload")
    suspend fun fillTable(
        @Part template: MultipartBody.Part,
        @Part documents: List<MultipartBody.Part>,
        @Part("user_request") userRequest: RequestBody,
    ): TaskDto
}
