package com.monster_ai_hk.guest.ui

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.monster_ai_hk.guest.BuildConfig
import com.monster_ai_hk.guest.MonsterGuestApp
import com.monster_ai_hk.guest.R
import com.monster_ai_hk.guest.data.GuestCharacter
import com.monster_ai_hk.guest.data.GuestCharacters
import com.monster_ai_hk.guest.data.GuestModeManager

/**
 * 主畫面：試玩橫幅 + 倒數 + 僅 3 名解鎖角色
 * 開發者：Suckbob | 發行商：Monster_Ai_hk
 */
class MainActivity : AppCompatActivity() {

    private lateinit var guest: GuestModeManager
    private lateinit var tvTimer: TextView
    private lateinit var tvBanner: TextView
    private lateinit var tvWatermark: TextView
    private lateinit var tvMeta: TextView
    private lateinit var btnOfficial: Button
    private lateinit var recycler: RecyclerView

    private val handler = Handler(Looper.getMainLooper())
    private val refreshRunnable = object : Runnable {
        override fun run() {
            refreshTimerUi()
            handler.postDelayed(this, 1000L)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        guest = MonsterGuestApp.get().guestMode

        tvTimer = findViewById(R.id.tvTimer)
        tvBanner = findViewById(R.id.tvBanner)
        tvWatermark = findViewById(R.id.tvWatermark)
        tvMeta = findViewById(R.id.tvMeta)
        btnOfficial = findViewById(R.id.btnOfficial)
        recycler = findViewById(R.id.recyclerCharacters)

        tvBanner.text = getString(R.string.guest_banner)
        tvWatermark.text = BuildConfig.WATERMARK_TEXT
        tvMeta.text = getString(
            R.string.meta_line,
            BuildConfig.DEVELOPER,
            BuildConfig.PUBLISHER,
            BuildConfig.VERSION_NAME,
        )

        recycler.layoutManager = LinearLayoutManager(this)
        recycler.adapter = CharacterAdapter(GuestCharacters.UNLOCKED) { char ->
            openChat(char)
        }

        // 鎖定角色提示（不可點選）
        findViewById<TextView>(R.id.tvLockedHint).text =
            GuestCharacters.LOCKED_HINTS.joinToString(" · ")

        btnOfficial.setOnClickListener {
            openOfficialDownload()
        }

        refreshTimerUi()
        if (guest.isTrialExpired()) {
            goTrialEnded(clearTask = false)
        }
    }

    override fun onResume() {
        super.onResume()
        handler.removeCallbacks(refreshRunnable)
        handler.post(refreshRunnable)
        refreshTimerUi()
    }

    override fun onPause() {
        super.onPause()
        handler.removeCallbacks(refreshRunnable)
    }

    private fun refreshTimerUi() {
        val remain = guest.getRemainingSeconds()
        tvTimer.text = getString(R.string.timer_remaining, guest.formatRemaining())
        if (remain <= 0) {
            tvTimer.setTextColor(getColor(R.color.danger))
        } else if (remain <= 60) {
            tvTimer.setTextColor(getColor(R.color.warning))
        } else {
            tvTimer.setTextColor(getColor(R.color.neon_cyan))
        }
    }

    private fun openChat(character: GuestCharacter) {
        if (guest.isTrialExpired()) {
            Toast.makeText(this, R.string.trial_expired_toast, Toast.LENGTH_SHORT).show()
            goTrialEnded(clearTask = false)
            return
        }
        if (!guest.canChatWith(character.id)) {
            Toast.makeText(this, R.string.character_locked, Toast.LENGTH_SHORT).show()
            return
        }
        // 訪客禁止：自訂角色 / 付費解鎖（此處僅白名單角色可進入）
        startActivity(
            Intent(this, ChatActivity::class.java).putExtra(
                ChatActivity.EXTRA_CHARACTER_ID,
                character.id,
            ),
        )
    }

    private fun openOfficialDownload() {
        try {
            val intent = Intent(Intent.ACTION_VIEW).apply {
                data = android.net.Uri.parse(BuildConfig.OFFICIAL_DOWNLOAD_URL)
            }
            startActivity(intent)
        } catch (_: Exception) {
            Toast.makeText(this, R.string.open_url_failed, Toast.LENGTH_SHORT).show()
        }
    }

    private fun goTrialEnded(clearTask: Boolean) {
        val i = Intent(this, TrialEndedActivity::class.java)
        if (clearTask) {
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        }
        startActivity(i)
        if (clearTask) finish()
    }

    /** 角色列表 Adapter */
    private class CharacterAdapter(
        private val items: List<GuestCharacter>,
        private val onClick: (GuestCharacter) -> Unit,
    ) : RecyclerView.Adapter<CharacterAdapter.VH>() {

        class VH(view: View) : RecyclerView.ViewHolder(view) {
            val emoji: TextView = view.findViewById(R.id.tvEmoji)
            val name: TextView = view.findViewById(R.id.tvName)
            val breed: TextView = view.findViewById(R.id.tvBreed)
            val intimacy: TextView = view.findViewById(R.id.tvIntimacy)
            val btn: Button = view.findViewById(R.id.btnChat)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
            val v = LayoutInflater.from(parent.context)
                .inflate(R.layout.item_character, parent, false)
            return VH(v)
        }

        override fun onBindViewHolder(holder: VH, position: Int) {
            val c = items[position]
            val guest = MonsterGuestApp.get().guestMode
            holder.emoji.text = c.emoji
            holder.name.text = c.nameZh
            holder.breed.text = c.breedZh
            holder.intimacy.text = holder.itemView.context.getString(
                R.string.intimacy_label,
                guest.getIntimacy(c.id),
            )
            holder.btn.setOnClickListener { onClick(c) }
            holder.itemView.setOnClickListener { onClick(c) }
        }

        override fun getItemCount(): Int = items.size
    }
}
