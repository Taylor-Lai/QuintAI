# Retrofit service interfaces and Gson DTOs are retained by their runtime annotations.
-keepattributes Signature, InnerClasses, EnclosingMethod, RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations
-keep interface com.zhihuiwenshu.app.data.remote.DocNexusApi { *; }
-keep class com.zhihuiwenshu.app.data.remote.** { *; }
