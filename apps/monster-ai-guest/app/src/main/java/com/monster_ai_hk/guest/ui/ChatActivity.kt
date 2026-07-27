package com.monster_ai_hk.guest.ui

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.monster_ai_hk.guest.BuildConfig
import com.monster_ai_hk.guest.MonsterGuestApp
import com.monster_ai_hk.guest.R
import com.monster_ai_hk.guest.data.GuestCharacter
import com.monster_ai_hk.guest.data.GuestCharacters
import com.monster_ai_hk.guest.data.GuestModeManager
import com.monster_ai_hk.guest.data.SimpleReplyEngine

/**
 * 基本對話介面（文字輸入 + 簡易回覆）
 * 開發者：Suckbob | 發行商：Monster_Ai_hk
 *
 * 訪客限制：
 * - 聊天僅存在於 memoryMessages，Activity 銷毀即消失
 * - 禁止儲存 / 匯出
 * - 倒數歸零自動結束並導向正式版引導
 */
class ChatActivity : AppCompatActivity(), GuestModeManager.Listener {

    private lateinit var guest: GuestModeManager
    private lateinit var character: GuestCharacter

    private lateinit var tvTitle: TextView
    private lateinit var tvTimer: TextView
    private lateinit var tvIntimacy: TextView
    private lateinit var tvWatermark: TextView
    private lateinit var etInput: EditText
    private lateinit var btnSend: Button
    private lateinit var btnBack: Button
    private lateinit var recycler: RecyclerView

    private val messages = mutableListOf<ChatMessage>()
    private lateinit var adapter: MessageAdapter

    private val handler = Handler(Looper.getMainLooper())
    private val tickRunnable = object : Runnable {
        override fun run() {
            val remain = guest.tick()
            updateTimer(remain)
            if (remain > 0) {
                handler.postDelayed(this, 1000L)
            }
        }
    }

    private var nextMsgId = 1L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_chat)

        guest = MonsterGuestApp.get().guestMode

        val charId = intent.getStringExtra(EXTRA_CHARACTER_ID)
        val found = charId?.let { GuestCharacters.findById(it) }
        if (found == null) {
            Toast.makeText(this, R.string.character_locked, Toast.LENGTH_SHORT).show()
            finish()
            return
        }
        character = found

        if (guest.isTrialExpired() || !guest.canChatWith(character.id)) {
            goTrialEnded()
            return
        }

        bindViews()
        setupList()
        // 開場問候（僅記憶體）
        appendBot(character.greeting)
        refreshIntimacy()
    }

    private fun bindViews() {
        tvTitle = findViewById(R.id.tvChatTitle)
        tvTimer = findViewById(R.id.tvChatTimer)
        tvIntimacy = findViewById(R.id.tvChatIntimacy)
        tvWatermark = findViewById(R.id.tvWatermark)
        etInput = findViewById(R.id.etInput)
        btnSend = findViewById(R.id.btnSend)
        btnBack = findViewById(R.id.btnBack)
        recycler = findViewById(R.id.recyclerMessages)

        tvTitle.text = getString(R.string.chat_title, character.emoji, character.nameZh)
        tvWatermark.text = BuildConfig.WATERMARK_TEXT

        btnBack.setOnClickListener { finish() }
        btnSend.setOnClickListener { sendMessage() }

        // 明確關閉：儲存 / 匯出按鈕不存在（訪客版，僅記憶體對話）
        // guest.isChatSaveAllowed() == false
        // guest.isExportAllowed() == false
    }

    private fun setupList() {
        adapter = MessageAdapter(messages)
        recycler.layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }
        recycler.adapter = adapter
    }

    override fun onResume() {
        super.onResume()
        guest.addListener(this)
        guest.startTicking()
        handler.removeCallbacks(tickRunnable)
        handler.post(tickRunnable)
        updateTimer(guest.getRemainingSeconds())
    }

    override fun onPause() {
        super.onPause()
        guest.stopTicking()
        guest.removeListener(this)
        handler.removeCallbacks(tickRunnable)
    }

    override fun onDestroy() {
        // 訪客：不寫入任何聊天紀錄
        messages.clear()
        super.onDestroy()
    }

    override fun onTrialExpired() {
        runOnUiThread {
            vibrateShort()
            Toast.makeText(this, R.string.trial_expired_toast, Toast.LENGTH_LONG).show()
            goTrialEnded()
        }
    }

    override fun onRemainingChanged(remainingSeconds: Int) {
        // tickRunnable 已更新 UI
    }

    private fun sendMessage() {
        if (guest.isTrialExpired()) {
            onTrialExpired()
            return
        }
        val text = etInput.text?.toString()?.trim().orEmpty()
        if (text.isEmpty()) return

        // 防連點：暫時禁用
        btnSend.isEnabled = false
        etInput.setText("")

        appendUser(text)
        val intimacy = guest.addIntimacy(character.id, 1)
        refreshIntimacy()

        // 簡易本地回覆（非雲端）
        val reply = SimpleReplyEngine.reply(character, text)
        appendBot(reply)

        btnSend.isEnabled = true
        etInput.requestFocus()

        // 親密度里程碑輕提示
        if (intimacy in listOf(20, 40, 60, 80)) {
            Toast.makeText(
                this,
                getString(R.string.intimacy_up, character.nameZh, intimacy),
                Toast.LENGTH_SHORT,
            ).show()
        }
    }

    private fun appendUser(text: String) {
        messages.add(ChatMessage(nextMsgId++, fromUser = true, text = text))
        adapter.notifyItemInserted(messages.lastIndex)
        recycler.scrollToPosition(messages.lastIndex)
    }

    private fun appendBot(text: String) {
        messages.add(ChatMessage(nextMsgId++, fromUser = false, text = text))
        adapter.notifyItemInserted(messages.lastIndex)
        recycler.scrollToPosition(messages.lastIndex)
    }

    private fun refreshIntimacy() {
        tvIntimacy.text = getString(
            R.string.intimacy_label,
            guest.getIntimacy(character.id),
        )
    }

    private fun updateTimer(remain: Int) {
        tvTimer.text = getString(R.string.timer_remaining, guest.formatRemaining())
        val color = when {
            remain <= 0 -> R.color.danger
            remain <= 60 -> R.color.warning
            else -> R.color.neon_cyan
        }
        tvTimer.setTextColor(getColor(color))
    }

    private fun goTrialEnded() {
        val i = Intent(this, TrialEndedActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        }
        startActivity(i)
        finish()
    }

    private fun vibrateShort() {
        try {
            val vibrator = if (android.os.Build.VERSION.SDK_INT >= 31) {
                val vm = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                vm.defaultVibrator
            } else {
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            }
            if (android.os.Build.VERSION.SDK_INT >= 26) {
                vibrator.vibrate(VibrationEffect.createOneShot(80, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(80)
            }
        } catch (_: Exception) {
            // 忽略振動失敗
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        // 離開前提醒：訪客不存檔
        AlertDialog.Builder(this)
            .setTitle(R.string.leave_chat_title)
            .setMessage(R.string.leave_chat_message)
            .setPositiveButton(R.string.leave) { _, _ -> finish() }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    private class MessageAdapter(
        private val items: List<ChatMessage>,
    ) : RecyclerView.Adapter<MessageAdapter.VH>() {

        class VH(view: View) : RecyclerView.ViewHolder(view) {
            val bubble: TextView = view.findViewById(R.id.tvBubble)
        }

        override fun getItemViewType(position: Int): Int =
            if (items[position].fromUser) 1 else 0

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
            val layout = if (viewType == 1) {
                R.layout.item_message_user
            } else {
                R.layout.item_message_bot
            }
            val v = LayoutInflater.from(parent.context).inflate(layout, parent, false)
            return VH(v)
        }

        override fun onBindViewHolder(holder: VH, position: Int) {
            holder.bubble.text = items[position].text
        }

        override fun getItemCount(): Int = items.size
    }

    companion object {
        const val EXTRA_CHARACTER_ID = "character_id"
    }
}
