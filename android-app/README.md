# 慧文融通 Android 原生端

Android 客户端使用 Kotlin 与 Jetpack Compose 开发，最低支持 Android 8.0（API 26），目标 SDK 为 36。它与 Web 端共用慧文融通后端，采用 ViewModel + Repository 的分层方式管理界面和远程数据。

## 名称与包标识

- 安装名称：慧文融通；
- 正式应用 ID：`com.quaintai.huiwenrongtong`；
- 调试应用 ID：`com.quaintai.huiwenrongtong.debug`；
- `quaintai` 是团队命名空间，不是产品名称。

应用 ID 一旦发布到应用商店不宜再修改，否则会被视为另一个应用。若未来确需更换，应先确定域名、签名、商店迁移和深链方案。

## 开发环境

- Android Studio；
- Android SDK 36；
- JDK 17（推荐使用 Android Studio 自带 JBR）；
- 可用的 Android 8.0+ 模拟器或真机；
- 运行中的慧文融通后端。

使用 Android Studio 的 **Open** 打开本目录，等待 Gradle 同步完成，然后选择 `app` 运行配置。

## API 地址

调试构建默认连接模拟器宿主机：

```text
http://10.0.2.2:8000/
```

也可以在构建时覆盖：

```powershell
./gradlew.bat :app:assembleDebug -PdebugApiBaseUrl=http://127.0.0.1:8000/
```

URL 必须包含结尾的 `/`。正式构建使用 `apiBaseUrl`，并要求 HTTPS。

## 模拟器联调

1. 在电脑启动后端并确认 `/health/ready`；
2. 在 Android Studio 的 Device Manager 创建或启动模拟器；
3. 运行 `app`；
4. 使用测试账号登录并执行一条完整任务。

模拟器内的 `127.0.0.1` 指向模拟器自身，访问电脑应使用 `10.0.2.2`。

## 真机联调

连接 USB 或 Android 无线调试后：

```powershell
adb devices -l
adb reverse tcp:8000 tcp:8000
./gradlew.bat :app:assembleDebug -PdebugApiBaseUrl=http://127.0.0.1:8000/
adb install -r -t ./app/build/outputs/apk/debug/app-debug.apk
```

部分厂商系统会要求在手机上勾选风险提示并手工确认安装，这是系统安全步骤，不能由脚本代替。无线调试断开、手机重启或重新配对后，需要重新检查 `adb reverse --list`。

ADB 反向端口仅适合本地调试。若希望脱离电脑长期测试，应部署一个手机可访问的 HTTPS 后端，并重新构建调试包或正式包。

## 常用构建与检查

```powershell
./gradlew.bat :app:testDebugUnitTest
./gradlew.bat :app:lintDebug
./gradlew.bat :app:assembleDebug
./gradlew.bat :app:assembleRelease
./gradlew.bat :app:bundleRelease
```

连接设备后可运行仪器测试：

```powershell
./gradlew.bat :app:connectedDebugAndroidTest
```

自动化通过不等于完整业务验收。至少还应人工检查登录、工作台、三类文档任务、任务详情、结果下载、失败提示和重新进入后的会话恢复。

## 正式签名

1. 将 `keystore.properties.example` 复制为 `keystore.properties`；
2. 创建发布密钥，将路径、别名和密码写入本地配置；
3. 使用正式 HTTPS API 构建：

```powershell
./gradlew.bat :app:bundleRelease -PapiBaseUrl=https://api.example.com/
```

`keystore.properties` 和密钥文件已被 Git 忽略。发布密钥丢失可能导致无法升级既有安装包，应使用受控备份并限制访问。

## 常见问题

- **Gradle 同步失败**：先确认 Android Studio 使用 JDK 17，并检查 SDK 36 是否安装；
- **中文路径错误**：将仓库映射或复制到纯 ASCII 路径后再运行 JVM 测试；
- **真机无法访问后端**：检查后端健康状态、设备连接和 `adb reverse --list`；
- **安装一直等待**：查看手机屏幕并完成厂商系统要求的人工确认；
- **正式包无法联网**：确认构建时传入的是受信任 HTTPS 地址且以 `/` 结尾。

返回[项目总览](../README.md)或查看[系统架构](../docs/architecture/overview.md)。
