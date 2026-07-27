/**
 * Monster AI 公測 — app 模組
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 *
 * applicationId：com.monster_ai_hk.monsterai
 * productFlavors：publicBeta（公測訪客）/ full（預留正式）
 */
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

val keystorePropsFile = rootProject.file("keystore.properties")
val keystoreProps = Properties()
if (keystorePropsFile.exists()) {
    keystorePropsFile.inputStream().use { keystoreProps.load(it) }
}

android {
    namespace = "com.monster_ai_hk.monsterai"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.monster_ai_hk.monsterai"
        minSdk = 26
        targetSdk = 34
        versionCode = 10001
        versionName = "1.0.0-public-beta"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        buildConfigField("String", "DEVELOPER", "\"suckbob\"")
        buildConfigField("String", "PUBLISHER", "\"Monster_Ai_hk\"")
        buildConfigField("boolean", "PUBLIC_BETA", "true")
        buildConfigField("int", "DAILY_RP_LIMIT", "50")
        buildConfigField("int", "DAILY_IMAGE_LIMIT", "10")

        // Capacitor web 資產由 cap sync 複製到 assets/public
        // manifestPlaceholders 可擴充
    }

    signingConfigs {
        create("release") {
            if (keystorePropsFile.exists()) {
                storeFile = rootProject.file(
                    keystoreProps.getProperty("storeFile", "keystore/monster-ai-public-beta.jks"),
                )
                storePassword = keystoreProps.getProperty("storePassword", "")
                keyAlias = keystoreProps.getProperty("keyAlias", "monster_ai_beta")
                keyPassword = keystoreProps.getProperty("keyPassword", "")
            }
        }
    }

    flavorDimensions += "channel"
    productFlavors {
        create("publicBeta") {
            dimension = "channel"
            applicationIdSuffix = ""
            versionNameSuffix = "-public-beta"
            resValue("string", "app_name", "Monster AI 公測")
            buildConfigField("boolean", "PUBLIC_BETA", "true")
            buildConfigField("boolean", "FORCE_GUEST", "true")
            buildConfigField("String", "BETA_BADGE", "\"公測版 · 訪客免費\"")
        }
        create("full") {
            dimension = "channel"
            // 正式版預留（不同 applicationId 避免與公測衝突，可按需改）
            applicationIdSuffix = ".full"
            versionNameSuffix = "-full"
            resValue("string", "app_name", "Monster AI")
            buildConfigField("boolean", "PUBLIC_BETA", "false")
            buildConfigField("boolean", "FORCE_GUEST", "false")
            buildConfigField("String", "BETA_BADGE", "\"\"")
        }
    }

    buildTypes {
        getByName("debug") {
            isMinifyEnabled = false
            applicationIdSuffix = ".debug"
            isDebuggable = true
        }
        getByName("release") {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            if (keystorePropsFile.exists()) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        buildConfig = true
        // Compose 可選擴展（原生橋接 UI）
        // compose = true
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.coordinatorlayout:coordinatorlayout:1.2.0")
    implementation("androidx.core:core-splashscreen:1.0.1")
    implementation("com.google.android.material:material:1.11.0")

    // Capacitor：cap sync 後取消註解 / 由 capacitor.build.gradle 注入
    // implementation(project(":capacitor-android"))
    // implementation(project(":capacitor-cordova-android-plugins"))

    // 原生擴展預留（Kotlin）
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")

    testImplementation("junit:junit:4.13.2")
}

// 若存在 Capacitor 生成的腳本則套用
val capacitorBuild = file("capacitor.build.gradle")
if (capacitorBuild.exists()) {
    apply(from = "capacitor.build.gradle")
}
