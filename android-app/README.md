# 慧文融通 Android

原生 Kotlin + Jetpack Compose 客户端，最低支持 Android 8.0（API 26）。

## 开发构建

调试版默认连接 Android 模拟器宿主机的 `http://10.0.2.2:8000/`：

```powershell
./gradlew.bat :app:assembleDebug
```

## 正式构建

1. 将 `keystore.properties.example` 复制为 `keystore.properties`。
2. 创建并妥善保管发布密钥，将真实路径和密码填写到该文件。
3. 传入使用 HTTPS 的正式后端地址：

```powershell
./gradlew.bat :app:bundleRelease -PapiBaseUrl=https://api.example.com/
```

`keystore.properties` 和密钥文件已被 Git 忽略。发布密钥丢失后无法对既有应用执行升级签名，请单独备份。

## 验证

```powershell
./gradlew.bat :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

若项目位于包含中文字符的 Windows 路径，Gradle 的 JVM 测试运行器可能无法加载测试类。可临时将项目映射到纯 ASCII 盘符后执行测试；APK 构建本身不受影响。
