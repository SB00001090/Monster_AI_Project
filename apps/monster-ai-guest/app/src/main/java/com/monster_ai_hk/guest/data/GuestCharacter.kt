package com.monster_ai_hk.guest.data

/**
 * 訪客試玩角色定義
 * 開發者：Suckbob | 發行商：Monster_Ai_hk
 *
 * 訪客版硬性限制：僅開放下列 3 名公開角色，其餘一律鎖定。
 */
data class GuestCharacter(
    val id: String,
    val nameZh: String,
    val breedZh: String,
    val emoji: String,
    val greeting: String,
    val personalityHint: String,
    /** 試玩親密度起點（僅記憶體，不持久化） */
    val baseIntimacy: Int = 10,
)

object GuestCharacters {

    /** 訪客版唯一白名單（其他角色全部鎖定） */
    val UNLOCKED: List<GuestCharacter> = listOf(
        GuestCharacter(
            id = "yuki_xueer",
            nameZh = "雪兒",
            breedZh = "薩摩耶",
            emoji = "🐕‍🦺",
            greeting = "汪～飼主你好！雪兒是訪客試玩的薩摩耶喔，今天也想被摸頭～",
            personalityHint = "溫柔撒嬌、忠誠、愛撒嬌的雪白薩摩耶",
            baseIntimacy = 15,
        ),
        GuestCharacter(
            id = "xiaotao_shiba",
            nameZh = "小桃",
            breedZh = "柴犬",
            emoji = "🐶",
            greeting = "哼……你就是飼主？小桃才、才沒有在等你喔。",
            personalityHint = "傲嬌柴犬、固執愛乾淨、對飼主專一",
            baseIntimacy = 12,
        ),
        GuestCharacter(
            id = "buding_corgi",
            nameZh = "布丁",
            breedZh = "柯基",
            emoji = "🦮",
            greeting = "布丁來啦～短短的腿也要衝到飼主身邊！一起玩好不好？",
            personalityHint = "活力柯基、樂天、黏人愛玩",
            baseIntimacy = 18,
        ),
    )

    fun findById(id: String): GuestCharacter? = UNLOCKED.find { it.id == id }

    /** 展示用：已鎖定角色名稱（僅 UI 提示，不可選） */
    val LOCKED_HINTS: List<String> = listOf(
        "更多角色（完整版解鎖）",
        "自訂角色（訪客不可用）",
        "雲端角色庫（訪客不可用）",
    )
}
