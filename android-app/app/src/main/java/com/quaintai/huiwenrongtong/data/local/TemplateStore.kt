package com.quaintai.huiwenrongtong.data.local

import android.content.Context
import androidx.core.content.edit
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

data class LocalTemplate(
    val id: String = "local_${System.currentTimeMillis()}",
    val name: String = "未命名模板",
    val category: String = "自定义分类",
    val scene: String = "在线编辑",
    val description: String = "",
    val fields: List<String> = emptyList(),
)

class TemplateStore(context: Context) {
    private val preferences = context.getSharedPreferences("template_library", Context.MODE_PRIVATE)
    private val gson = Gson()

    fun templates(): List<LocalTemplate> = runCatching {
        gson.fromJson<List<LocalTemplate>>(
            preferences.getString(KEY_TEMPLATES, "[]"),
            object : TypeToken<List<LocalTemplate>>() {}.type,
        )
    }.getOrDefault(emptyList())

    fun save(template: LocalTemplate) {
        val updated = listOf(template) + templates().filterNot { it.id == template.id }
        preferences.edit { putString(KEY_TEMPLATES, gson.toJson(updated)) }
    }

    fun delete(id: String) {
        preferences.edit { putString(KEY_TEMPLATES, gson.toJson(templates().filterNot { it.id == id })) }
    }

    fun setDraft(template: LocalTemplate?) = preferences.edit {
        if (template == null) remove(KEY_DRAFT) else putString(KEY_DRAFT, gson.toJson(template))
    }

    fun draft(): LocalTemplate? = runCatching {
        preferences.getString(KEY_DRAFT, null)?.let { gson.fromJson(it, LocalTemplate::class.java) }
    }.getOrNull()

    fun setActive(template: LocalTemplate) = preferences.edit { putString(KEY_ACTIVE, gson.toJson(template)) }
    fun clearActive() = preferences.edit { remove(KEY_ACTIVE) }
    fun active(): LocalTemplate? = runCatching {
        preferences.getString(KEY_ACTIVE, null)?.let { gson.fromJson(it, LocalTemplate::class.java) }
    }.getOrNull()

    private companion object {
        const val KEY_TEMPLATES = "templates"
        const val KEY_DRAFT = "draft"
        const val KEY_ACTIVE = "active"
    }
}
