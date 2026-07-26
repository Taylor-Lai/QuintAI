package com.quaintai.huiwenrongtong

import android.app.Application
import com.quaintai.huiwenrongtong.data.AppContainer

class HuiwenRongtongApplication : Application() {
    val container: AppContainer by lazy { AppContainer(this) }
}
