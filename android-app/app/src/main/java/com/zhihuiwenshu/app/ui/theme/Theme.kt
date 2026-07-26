package com.zhihuiwenshu.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

val BrandGold = Color(0xFFD5B076)
val BrandGoldDark = Color(0xFFB48742)
val BrandBackground = Color(0xFFECECEC)
val BrandSurface = Color(0xFFF8F8F8)
val BrandCard = Color(0xFFFFFFFF)
val BrandInk = Color(0xFF2D2D2D)
val BrandMuted = Color(0xFF6D6A66)
val BrandSand = Color(0xFFFAF6EF)
val BrandBorder = Color(0xFFE5DED3)

private val LightColors = lightColorScheme(
    primary = BrandGoldDark,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFF3E5CD),
    onPrimaryContainer = BrandInk,
    background = BrandBackground,
    onBackground = BrandInk,
    surface = BrandSurface,
    onSurface = BrandInk,
    surfaceVariant = BrandSand,
    onSurfaceVariant = BrandMuted,
    outline = BrandBorder,
    error = Color(0xFFB85C5C),
)

private val BrandTypography = androidx.compose.material3.Typography(
    displaySmall = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Bold, fontSize = 32.sp),
    headlineLarge = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Bold, fontSize = 28.sp),
    headlineMedium = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Bold, fontSize = 24.sp),
    titleLarge = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Bold, fontSize = 21.sp),
    titleMedium = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.SemiBold, fontSize = 17.sp),
    bodyLarge = TextStyle(fontFamily = FontFamily.Serif, fontSize = 16.sp),
    bodyMedium = TextStyle(fontFamily = FontFamily.Serif, fontSize = 14.sp),
    labelLarge = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.SemiBold, fontSize = 14.sp),
)

@Composable
fun ZhihuiWenshuTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightColors,
        typography = BrandTypography,
        content = content,
    )
}
