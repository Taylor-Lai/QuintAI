package com.quaintai.huiwenrongtong.data

import android.content.Context
import com.quaintai.huiwenrongtong.BuildConfig
import com.quaintai.huiwenrongtong.data.local.TokenStore
import com.quaintai.huiwenrongtong.data.remote.HuiwenRongtongApi
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

class AppContainer(context: Context) {
    private val appContext = context.applicationContext
    private val tokenStore = TokenStore(appContext)

    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(180, TimeUnit.SECONDS)
        .writeTimeout(180, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            val request = chain.request().newBuilder().apply {
                tokenStore.readToken()?.let { header("Authorization", "Bearer $it") }
            }.build()
            chain.proceed(request)
        }
        .apply {
            if (BuildConfig.DEBUG) {
                addInterceptor(HttpLoggingInterceptor().apply {
                    level = HttpLoggingInterceptor.Level.BASIC
                })
            }
        }
        .build()

    private val api = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(httpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(HuiwenRongtongApi::class.java)

    val repository = HuiwenRongtongRepository(appContext, api, tokenStore)
}
