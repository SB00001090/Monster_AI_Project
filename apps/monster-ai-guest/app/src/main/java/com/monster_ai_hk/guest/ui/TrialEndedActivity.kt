package com.monster_ai_hk.guest.ui

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.monster_ai_hk.guest.BuildConfig
import com.monster_ai_hk.guest.MonsterGuestApp
import com.monster_ai_hk.guest.R

/**
 * 試玩結束畫面 — 引導下載正式版
 * 開發者：Suckbob | 發行商：Monster_Ai_hk
 *
 * 不提供付費內購、不提供帳號登入延長試玩。
 */
class TrialEndedActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_trial_ended)

        // 停止任何殘留計時
        MonsterGuestApp.get().guestMode.stopTicking()

        val tvTitle = findViewById<TextView>(R.id.tvEndedTitle)
        val tvBody = findViewById<TextView>(R.id.tvEndedBody)
        val tvWatermark = findViewById<TextView>(R.id.tvWatermark)
        val btnDownload = findViewById<Button>(R.id.btnDownloadOfficial)
        val btnBackHome = findViewById<Button>(R.id.btnBackHome)

        tvTitle.text = getString(R.string.trial_ended_title)
        tvBody.text = getString(
            R.string.trial_ended_body,
            BuildConfig.PUBLISHER,
            BuildConfig.DEVELOPER,
        )
        tvWatermark.text = BuildConfig.WATERMARK_TEXT

        btnDownload.setOnClickListener {
            try {
                startActivity(
                    Intent(Intent.ACTION_VIEW, Uri.parse(BuildConfig.OFFICIAL_DOWNLOAD_URL)),
                )
            } catch (_: Exception) {
                Toast.makeText(this, R.string.open_url_failed, Toast.LENGTH_SHORT).show()
            }
        }

        btnBackHome.setOnClickListener {
            val i = Intent(this, MainActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            }
            startActivity(i)
            finish()
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        // 回到主畫面而非再次進入對話
        val i = Intent(this, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
        }
        startActivity(i)
        finish()
    }
}
