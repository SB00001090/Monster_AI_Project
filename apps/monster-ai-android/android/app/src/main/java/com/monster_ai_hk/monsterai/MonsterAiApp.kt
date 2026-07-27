package com.monster_ai_hk.monsterai

import android.app.Application

/**
 * Monster AI 公測 Application
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 *
 * 原生擴展入口：可在此初始化本地橋接、通知 channel 等。
 * 公測訪客邏輯主要在 Web（GuestContext）；原生層只做殼與權限。
 */
class MonsterAiApp : Application() {
    override fun onCreate() {
        super.onCreate()
        // 預留：Crash 回報、Notification channel、原生額度橋接
    }
}
