package io.slllyio.astro

import android.annotation.SuppressLint
import android.app.AlertDialog
import android.content.Context
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.EditText
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity

/**
 * Thin WebView wrapper around the hosted Jyotish reading engine.
 *
 * The whole reading UI (the FastAPI + Jinja pages) is served by the backend at
 * [BuildConfig.BACKEND_URL]; this app simply opens `<backend>/reading/v15/`.
 * The backend URL is baked in at build time, or entered once on first launch
 * and remembered — so the same .apk works against any deployment.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this)
        setContentView(webView)

        with(webView.settings) {
            javaScriptEnabled = true          // the reading UI uses JS (dark mode, explorer)
            domStorageEnabled = true          // localStorage for the theme toggle
            cacheMode = WebSettings.LOAD_DEFAULT
            loadWithOverviewMode = true
            useWideViewPort = true
            builtInZoomControls = true
            displayZoomControls = false
        }
        // Keep navigation inside the app; open the reading pages in-place.
        webView.webViewClient = WebViewClient()

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })

        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState)
        } else {
            openReading()
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        webView.saveState(outState)
    }

    private fun prefs() = getSharedPreferences("cfg", Context.MODE_PRIVATE)

    private fun backendUrl(): String {
        val saved = prefs().getString("backend_url", null)
        return (saved ?: BuildConfig.BACKEND_URL).trim().trimEnd('/')
    }

    private fun openReading() {
        val base = backendUrl()
        if (base.isBlank() || base.contains("REPLACE_ME")) {
            promptForUrl()
        } else {
            webView.loadUrl("$base/reading/v15/")
        }
    }

    private fun promptForUrl() {
        val input = EditText(this).apply {
            hint = "https://your-server.example.com"
            setText(prefs().getString("backend_url", "") ?: "")
        }
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.server_title))
            .setMessage(getString(R.string.server_message))
            .setView(input)
            .setCancelable(false)
            .setPositiveButton(android.R.string.ok) { _, _ ->
                prefs().edit().putString("backend_url", input.text.toString().trim()).apply()
                openReading()
            }
            .show()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menu.add(0, MENU_SERVER, 0, getString(R.string.server_title))
        menu.add(0, MENU_HOME, 1, getString(R.string.new_reading))
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean = when (item.itemId) {
        MENU_SERVER -> { promptForUrl(); true }
        MENU_HOME -> { openReading(); true }
        else -> super.onOptionsItemSelected(item)
    }

    private companion object {
        const val MENU_SERVER = 1
        const val MENU_HOME = 2
    }
}
