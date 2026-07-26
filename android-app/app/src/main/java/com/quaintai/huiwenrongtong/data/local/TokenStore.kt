package com.quaintai.huiwenrongtong.data.local

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import androidx.core.content.edit
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class TokenStore(context: Context) {
    private val preferences = context.getSharedPreferences("secure_session", Context.MODE_PRIVATE)
    private val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }

    fun saveSession(token: String, username: String, email: String, role: String = "") {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
        val encrypted = cipher.doFinal(token.toByteArray(Charsets.UTF_8))
        preferences.edit {
            putString(TOKEN, Base64.encodeToString(encrypted, Base64.NO_WRAP))
            putString(IV, Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
            putString(USERNAME, username)
            putString(EMAIL, email)
            putString(ROLE, role)
        }
    }

    fun readToken(): String? = runCatching {
        val encrypted = preferences.getString(TOKEN, null) ?: return null
        val iv = preferences.getString(IV, null) ?: return null
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(
            Cipher.DECRYPT_MODE,
            getOrCreateKey(),
            GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP)),
        )
        String(cipher.doFinal(Base64.decode(encrypted, Base64.NO_WRAP)), Charsets.UTF_8)
    }.getOrElse {
        clear()
        null
    }

    fun username(): String = preferences.getString(USERNAME, "") ?: ""
    fun email(): String = preferences.getString(EMAIL, "") ?: ""
    fun role(): String = preferences.getString(ROLE, "") ?: ""

    fun clear() {
        preferences.edit { clear() }
    }

    private fun getOrCreateKey(): SecretKey {
        (keyStore.getKey(KEY_ALIAS, null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").run {
            init(
                KeyGenParameterSpec.Builder(
                    KEY_ALIAS,
                    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
                )
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .build()
            )
            generateKey()
        }
    }

    private companion object {
        const val KEY_ALIAS = "zhihui_wenshu_session_key"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val TOKEN = "token"
        const val IV = "iv"
        const val USERNAME = "username"
        const val EMAIL = "email"
        const val ROLE = "role"
    }
}
