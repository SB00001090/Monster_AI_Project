package com.monster_ai_hk.guest.data

/**
 * 簡易本地回覆引擎（訪客版離線可用）
 * 開發者：Suckbob | 發行商：Monster_Ai_hk
 *
 * 不連雲端、不呼叫付費 API。僅做關鍵字規則 + 輪替範本。
 * 正式版請改接 Monster AI / LLM 管線。
 */
object SimpleReplyEngine {

    private val counters = mutableMapOf<String, Int>()

    fun reply(character: GuestCharacter, userText: String): String {
        val text = userText.trim()
        if (text.isEmpty()) {
            return fallback(character, "……？")
        }

        // 簡單安全：明顯未成年關鍵字拒絕（訪客守護）
        if (containsBlocked(text)) {
            return "（訪客守護）這個話題不適合喔。我們聊點溫暖日常好不好？"
        }

        val lower = text.lowercase()
        val keyed = when {
            containsAny(lower, listOf("你好", "嗨", "哈囉", "hello", "hi")) ->
                greet(character)
            containsAny(lower, listOf("摸頭", "抱抱", "親親", "撒嬌")) ->
                affection(character)
            containsAny(lower, listOf("喜歡", "愛", "在嗎")) ->
                bond(character)
            containsAny(lower, listOf("正式版", "完整版", "付費", "解鎖")) ->
                "訪客試玩只能陪你一下下～完整角色與存檔請下載正式版（Monster_Ai_hk）喔！"
            containsAny(lower, listOf("時間", "倒數", "試玩")) ->
                "訪客每天有 30 分鐘試玩時間，用完就會結束對話。珍惜每一句話吧～"
            else -> generic(character, text)
        }
        return keyed
    }

    private fun greet(c: GuestCharacter): String = when (c.id) {
        "yuki_xueer" -> "雪兒搖著螺旋尾：「飼主好～今天也要對雪兒溫柔一點喔。」"
        "xiaotao_shiba" -> "小桃別過頭：「……嗯。知道了。不要一直盯著本小姐看。」"
        "buding_corgi" -> "布丁小短腿踏踏踏：「飼主！布丁在這裡！一起玩嘛～」"
        else -> c.greeting
    }

    private fun affection(c: GuestCharacter): String = when (c.id) {
        "yuki_xueer" -> "雪兒把頭頂輕輕頂到你掌心，耳朵舒服地抖了抖。「再摸一下……就好。」"
        "xiaotao_shiba" -> "小桃耳朵微微後折：「才、才不是想被摸……哼。隨便你。」尾巴卻偷偷轉圈。"
        "buding_corgi" -> "布丁整個人撲過來轉圈：「抱抱！再抱抱！布丁電量滿滿！」"
        else -> "（親暱地靠近你）"
    }

    private fun bond(c: GuestCharacter): String = when (c.id) {
        "yuki_xueer" -> "雪兒蜜琥珀色眼睛彎起來：「雪兒最喜歡飼主了。一直都在。」"
        "xiaotao_shiba" -> "小桃小聲說：「……喜歡之類的，才不會說出口。但是……你在就好。」"
        "buding_corgi" -> "布丁開心晃尾：「布丁超愛飼主！永遠永遠在一起玩！」"
        else -> "我也喜歡和你聊天。"
    }

    private fun generic(c: GuestCharacter, userText: String): String {
        val i = nextIndex(c.id)
        val snippets = when (c.id) {
            "yuki_xueer" -> listOf(
                "雪兒側耳聽完，溫柔點頭：「飼主說的「${clip(userText)}」，雪兒記住了。」",
                "雪白尾巴輕輕掃過地板：「嗯嗯，繼續說給雪兒聽好不好？」",
                "雪兒靠過來一點：「訪客時間有限，但雪兒會好好陪你。」",
            )
            "xiaotao_shiba" -> listOf(
                "小桃哼了一聲：「「${clip(userText)}」啊……本小姐知道了。」",
                "柴柴耳尖動了動：「廢話少說。你還有什麼想講的？」",
                "小桃抱著靠枕：「訪客版而已……不要以為可以一直纏著本小姐。」",
            )
            "buding_corgi" -> listOf(
                "布丁眼睛發亮：「喔喔！「${clip(userText)}」！好好玩的樣子！」",
                "短腿原地踏步：「再說一次嘛～布丁想聽！」",
                "布丁笑嘻嘻：「訪客也能開心聊天！正式版還有更多朋友喔！」",
            )
            else -> listOf("我聽到了：「${clip(userText)}」。")
        }
        return snippets[i % snippets.size]
    }

    private fun fallback(c: GuestCharacter, hint: String): String =
        "${c.nameZh}$hint"

    private fun nextIndex(id: String): Int {
        val n = (counters[id] ?: 0) + 1
        counters[id] = n
        return n
    }

    private fun clip(s: String, max: Int = 24): String {
        val t = s.replace("\n", " ").trim()
        return if (t.length <= max) t else t.take(max) + "…"
    }

    private fun containsAny(hay: String, needles: List<String>): Boolean =
        needles.any { hay.contains(it) }

    private fun containsBlocked(text: String): Boolean {
        val blocked = listOf("未成年", "兒童", "小孩", "幼女", "正太", "蘿莉", "loli", "shota")
        val lower = text.lowercase()
        return blocked.any { lower.contains(it) }
    }
}
