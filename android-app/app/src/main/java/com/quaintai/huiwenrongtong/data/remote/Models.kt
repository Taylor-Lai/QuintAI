package com.quaintai.huiwenrongtong.data.remote

import com.google.gson.JsonElement
import com.google.gson.annotations.SerializedName

data class LoginRequest(val email: String, val password: String)

data class RegisterRequest(
    val username: String,
    val email: String,
    val password: String,
)

data class LoginResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    @SerializedName("user_info") val userInfo: UserInfo,
)

data class UserInfo(
    val id: String = "",
    val username: String = "",
    val email: String = "",
    val role: String = "",
)

data class RegisterResponse(
    val message: String = "注册成功",
    @SerializedName("user_id") val userId: String = "",
    val username: String = "",
)

data class TaskListResponse(val items: List<TaskDto> = emptyList())

data class TaskDto(
    val id: String,
    val kind: String,
    val status: String,
    val progress: Int = 0,
    val stage: String = "",
    @SerializedName("has_file") val hasFile: Boolean = false,
    val filename: String? = null,
    val result: JsonElement? = null,
    val error: TaskError? = null,
    val attempts: Int = 0,
    @SerializedName("created_at") val createdAt: String = "",
    @SerializedName("completed_at") val completedAt: String? = null,
    @SerializedName("quality_report") val qualityReport: JsonElement? = null,
    @SerializedName("evidence_summary") val evidenceSummary: JsonElement? = null,
    val events: List<TaskEvent>? = emptyList(),
)

data class TaskEvent(
    val stage: String = "",
    val message: String = "",
    val status: String = "",
    val progress: Int = 0,
    @SerializedName("created_at") val createdAt: String = "",
)

data class TaskError(
    val code: String? = null,
    val message: String? = null,
)

enum class FeatureKind(val apiKind: String, val title: String, val description: String) {
    EDIT("document_edit", "文档智能操作交互", "根据自然语言要求调整 Word 文档"),
    EXTRACT("document_extract", "非结构化文档信息提取", "从文档中提取指定字段与证据"),
    TABLE("table_fill", "表格自定义数据填写", "融合多个来源并填写目标表格"),
}

enum class PlatformModule(val title: String, val description: String) {
    OVERVIEW("工作台概览", "文档、复核、任务与工作流总览"),
    DOCUMENTS("文档库", "集中管理、归档和下载业务材料"),
    REVIEWS("人工复核", "核验提取字段、质量问题与证据"),
    WORKFLOWS("工作流", "配置并运行自动化文档处理链路"),
    EXECUTIONS("AI 执行驾驶舱", "查看任务进度、结果与运行轨迹"),
    KNOWLEDGE("知识与证据中心", "构建知识集合并进行检索"),
    ENTERPRISE("企业控制台", "组织、成员、集成、安全与运维"),
    TEMPLATES("模板库", "浏览常用业务模板与字段"),
    EDITOR("在线模板编辑", "自定义模板及字段结构"),
    GUIDE("上手指南", "了解从上传到交付的完整流程"),
    ADMIN("后台管理", "用户、权限和系统统计"),
}
