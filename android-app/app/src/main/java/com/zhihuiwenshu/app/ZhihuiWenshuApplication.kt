package com.zhihuiwenshu.app

import android.app.Application
import com.zhihuiwenshu.app.data.AppContainer

class ZhihuiWenshuApplication : Application() {
    val container: AppContainer by lazy { AppContainer(this) }
}
