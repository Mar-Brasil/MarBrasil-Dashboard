package com.auvo.painel.ui.settings

import android.content.Intent
import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.auvo.painel.BuildConfig
import com.auvo.painel.R
import com.auvo.painel.databinding.ActivitySettingsBinding
import com.auvo.painel.ui.login.LoginActivity
import com.auvo.painel.utils.NotificationFrequency
import com.auvo.painel.utils.PreferencesManager

class SettingsActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivitySettingsBinding
    private lateinit var preferencesManager: PreferencesManager
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        preferencesManager = PreferencesManager(this)
        
        setupUI()
        loadUserInfo()
        loadSettings()
    }
    
    private fun setupUI() {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        
        binding.toolbar.setNavigationOnClickListener {
            finish()
        }
        
        // Setup frequency spinner
        val frequencies = listOf("15 minutos", "30 minutos", "1 hora", "6 horas")
        val adapter = ArrayAdapter(this, android.R.layout.simple_dropdown_item_1line, frequencies)
        binding.spinnerFrequency.setAdapter(adapter)
        
        // Setup click listeners
        binding.btnSaveSettings.setOnClickListener {
            saveSettings()
        }
        
        binding.btnLogout.setOnClickListener {
            showLogoutDialog()
        }
    }
    
    private fun loadUserInfo() {
        val user = preferencesManager.getUser()
        if (user != null) {
            binding.tvUserName.text = user.nome_completo
            binding.tvUserUsername.text = "@${user.username}"
            binding.tvUserContracts.text = "${user.contratos.size} contratos"
        }
        
        // Set app version
        binding.tvAppVersion.text = BuildConfig.VERSION_NAME
    }
    
    private fun loadSettings() {
        // Load notification settings
        binding.switchNotifications.isChecked = preferencesManager.areNotificationsEnabled()
        
        // Load frequency
        val frequency = preferencesManager.getNotificationFrequency()
        val frequencyText = when (frequency) {
            NotificationFrequency.FIFTEEN_MINUTES -> "15 minutos"
            NotificationFrequency.THIRTY_MINUTES -> "30 minutos"
            NotificationFrequency.HOURLY -> "1 hora"
            NotificationFrequency.SIX_HOURS -> "6 horas"
        }
        binding.spinnerFrequency.setText(frequencyText, false)
        
        // Load due days
        binding.etDueDays.setText(preferencesManager.getDueDaysAhead().toString())
    }
    
    private fun saveSettings() {
        try {
            // Save notification enabled
            preferencesManager.setNotificationsEnabled(binding.switchNotifications.isChecked)
            
            // Save frequency
            val frequencyText = binding.spinnerFrequency.text.toString()
            val frequency = when (frequencyText) {
                "15 minutos" -> NotificationFrequency.FIFTEEN_MINUTES
                "30 minutos" -> NotificationFrequency.THIRTY_MINUTES
                "1 hora" -> NotificationFrequency.HOURLY
                "6 horas" -> NotificationFrequency.SIX_HOURS
                else -> NotificationFrequency.HOURLY
            }
            preferencesManager.setNotificationFrequency(frequency)
            
            // Save due days
            val dueDaysText = binding.etDueDays.text.toString()
            val dueDays = if (dueDaysText.isNotEmpty()) {
                dueDaysText.toIntOrNull() ?: 7
            } else {
                7
            }
            preferencesManager.setDueDaysAhead(dueDays)
            
            Toast.makeText(this, "Configurações salvas com sucesso!", Toast.LENGTH_SHORT).show()
            
            // TODO: Reschedule notifications with new settings
            // NotificationScheduler.scheduleNotifications(this)
            
        } catch (e: Exception) {
            Toast.makeText(this, "Erro ao salvar configurações: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }
    
    private fun showLogoutDialog() {
        AlertDialog.Builder(this)
            .setTitle("Sair")
            .setMessage("Tem certeza que deseja sair do aplicativo?")
            .setPositiveButton("Sim") { _, _ ->
                logout()
            }
            .setNegativeButton("Cancelar", null)
            .show()
    }
    
    private fun logout() {
        // Clear user data
        preferencesManager.clearUser()
        
        // Navigate to login
        val intent = Intent(this, LoginActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        startActivity(intent)
        finish()
    }
}
