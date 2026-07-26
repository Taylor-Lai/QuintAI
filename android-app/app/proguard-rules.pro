# Retrofit service interfaces and Gson DTOs are retained by their runtime annotations.
-keepattributes Signature, InnerClasses, EnclosingMethod, RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations
-keep interface com.quaintai.huiwenrongtong.data.remote.HuiwenRongtongApi { *; }
-keep class com.quaintai.huiwenrongtong.data.remote.** { *; }
