package com.monster_ai_hk.guest.ui

/**
 * 對話訊息（僅記憶體，訪客禁止持久化）
 * 開發者：Suckbob | 發行商：Monster_Ai_hk
 */
data class ChatMessage(
    val id: Long,
    val fromUser: Boolean,
    val text: String,
    val timestampMs: Long = System.currentTimeMillis(),
)
