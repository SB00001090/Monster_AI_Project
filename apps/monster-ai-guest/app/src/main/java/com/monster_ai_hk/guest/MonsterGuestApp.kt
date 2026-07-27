package com.monster_ai_hk.guest

import android.app.Application
import com.monster_ai_hk.guest.data.GuestModeManager

/**
 * Monster AI 訪客試玩版 Application
 * 開發者：Suckbob | 發行商：Monster_Ai_hk
 *
 * 訪客版原則：
 * - 不初始化付費、帳號、雲端同步
 * - 僅載入 GuestModeManager（本地試玩計時與角色鎖定）
 */
class MonsterGuestApp : Application() {

    lateinit var guestMode: GuestModeManager
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this
        guestMode = GuestModeManager(this)
        // 明確不註冊 Billing / OAuth / 雲端 Worker
    }

    companion object {
        @Volatile
        private var instance: MonsterGuestApp? = null

        fun get(): MonsterGuestApp =
            instance ?: error("MonsterGuestApp 尚未初始化")
    }
}
