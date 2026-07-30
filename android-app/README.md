# 慧文融通 Android 原生端

Android 客户端基于 Kotlin 与 Jetpack Compose 构建，最低支持 Android 8.0（API 26），目标 SDK 为 36。客户端与 Web 端共用慧文融通服务端接口，并采用 ViewModel 与 Repository 分层管理界面状态和远程数据访问。

## 名称与包标识

- 安装名称：慧文融通；
- 正式应用 ID：`com.quaintai.huiwenrongtong`；
- 调试应用 ID：`com.quaintai.huiwenrongtong.debug`；
- `quaintai`：QuaintAI 团队使用的组织命名空间。

应用 ID 在应用商店首次发布后应保持稳定；变更应用 ID 将被平台识别为新的应用。确需调整时，应预先完成域名、签名、商店迁移与深链兼容方案评估。

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
http://10.0.2.2:8000/api/
```

可在构建阶段通过参数覆盖默认地址：

```powershell
./gradlew.bat :app:assembleDebug -PdebugApiBaseUrl=http://127.0.0.1:8000/api/
```

URL 必须包含结尾的 `/`。正式构建使用 `apiBaseUrl`，并要求 HTTPS。

## 模拟器联调

1. 在电脑启动完整的 Docker Compose 服务并确认 `/api/health/ready`；
2. 在 Android Studio 的 Device Manager 创建或启动模拟器；
3. 运行 `app`；
4. 使用测试账号登录并执行一条完整任务。

模拟器内的 `127.0.0.1` 指向模拟器自身，访问电脑应使用 `10.0.2.2`。

## 真机联调

连接 USB 或 Android 无线调试后：

```powershell
adb devices -l
adb reverse tcp:8000 tcp:8000
./gradlew.bat :app:assembleDebug -PdebugApiBaseUrl=http://127.0.0.1:8000/api/
adb install -r -t ./app/build/outputs/apk/debug/app-debug.apk
```

部分厂商系统要求在设备端确认风险提示与安装授权。该安全确认无法由自动化脚本替代。无线调试断开、设备重启或重新配对后，应重新执行 `adb reverse --list` 验证端口映射。

ADB 反向端口仅适用于本地调试。独立于开发主机的持续测试环境应部署设备可访问的 HTTPS 服务端，并基于该地址重新构建调试包或正式包。

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

自动化检查通过仅表示既定技术用例满足预期，不能替代完整业务验收。发布前仍须人工验证登录、工作台、三类文档任务、任务详情、结果下载、异常提示及会话恢复。

Android 与 Web 共用服务端任务历史和团队模板。终态任务可在详情页删除，企业管理员可将组织文档归档下载为 ZIP；两项操作均直接调用服务端接口，不使用移动端本地副本替代。

“知识与证据中心”支持知识库创建、文档挂载、证据检索、图谱实体与来源查看、实体人工确认，以及依据最新抽取结果重新构建图谱。移动端显示的关系路径和图谱实体均来自服务端持久化数据，原文证据仍是事实核验依据。

## 正式签名

1. 将 `keystore.properties.example` 复制为 `keystore.properties`；
2. 创建发布密钥，将路径、别名和密码写入本地配置；
3. 使用正式 HTTPS API 构建：

```powershell
./gradlew.bat :app:bundleRelease -PapiBaseUrl=https://docs.example.com/api/
```

`keystore.properties` 和密钥文件已被 Git 忽略。发布密钥丢失可能导致无法升级既有安装包，应使用受控备份并限制访问。

未提供 `keystore.properties` 时，Gradle 仍可生成用于验证 R8、资源压缩和 AAB 打包链路的未签名产物，但该产物不能安装为正式版或提交应用商店。发布前必须使用组织持有的稳定密钥重新构建，并使用 `apksigner` 或商店上传检查验证签名。

## 常见问题

- **Gradle 同步失败**：确认 Android Studio 使用 JDK 17，并验证 SDK 36 已正确安装；
- **中文路径错误**：将仓库映射或复制到纯 ASCII 路径后再运行 JVM 测试；
- **真机无法访问后端**：检查后端健康状态、设备连接和 `adb reverse --list`；
- **安装流程持续等待**：在设备端完成厂商系统要求的风险提示与安装授权确认；
- **正式包无法联网**：确认构建时传入的是受信任 HTTPS 地址且以 `/` 结尾。

返回[项目总览](../README.md)或查看[系统架构](../docs/architecture/overview.md)。
