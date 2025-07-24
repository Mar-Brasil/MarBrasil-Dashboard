package com.auvo.painel.ui.login

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.auvo.painel.R
import com.auvo.painel.data.repository.DashboardRepository
import com.auvo.painel.databinding.ActivityLoginBinding
import com.auvo.painel.ui.main.MainActivity
import com.auvo.painel.utils.PreferencesManager
import kotlinx.coroutines.launch

class LoginActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityLoginBinding
    private lateinit var repository: DashboardRepository
    private lateinit var preferencesManager: PreferencesManager
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        repository = DashboardRepository()
        preferencesManager = PreferencesManager(this)
        
        setupUI()
        checkAutoLogin()
    }
    
    private fun setupUI() {
        binding.btnLogin.setOnClickListener {
            val username = binding.etUsername.text.toString().trim()
            val password = binding.etPassword.text.toString().trim()
            
            if (validateInput(username, password)) {
                performLogin(username, password)
            }
        }
    }
    
    private fun checkAutoLogin() {
        // Verifica se há credenciais salvas para login automático
        val savedUser = preferencesManager.getUser()
        if (savedUser != null) {
            navigateToMain(savedUser)
        }
    }
    
    private fun validateInput(username: String, password: String): Boolean {
        if (username.isEmpty()) {
            binding.etUsername.error = "Campo obrigatório"
            return false
        }
        
        if (password.isEmpty()) {
            binding.etPassword.error = "Campo obrigatório"
            return false
        }
        
        return true
    }
    
    private fun performLogin(username: String, password: String) {
        showLoading(true)
        hideError()
        
        lifecycleScope.launch {
            try {
                val result = repository.login(username, password)
                
                result.onSuccess { user ->
                    // Salva o usuário nas preferências
                    preferencesManager.saveUser(user)
                    
                    // Navega para a tela principal
                    navigateToMain(user)
                    
                }.onFailure { exception ->
                    showError(getErrorMessage(exception))
                }
                
            } catch (e: Exception) {
                showError("Erro de conexão. Verifique sua internet.")
            } finally {
                showLoading(false)
            }
        }
    }
    
    private fun navigateToMain(user: com.auvo.painel.data.models.User) {
        val intent = Intent(this, MainActivity::class.java).apply {
            putExtra("user", user)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        startActivity(intent)
        finish()
    }
    
    private fun showLoading(show: Boolean) {
        binding.progressBar.visibility = if (show) View.VISIBLE else View.GONE
        binding.btnLogin.isEnabled = !show
        binding.etUsername.isEnabled = !show
        binding.etPassword.isEnabled = !show
    }
    
    private fun showError(message: String) {
        binding.tvError.text = message
        binding.tvError.visibility = View.VISIBLE
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
    }
    
    private fun hideError() {
        binding.tvError.visibility = View.GONE
    }
    
    private fun getErrorMessage(exception: Throwable): String {
        return when {
            exception.message?.contains("401") == true -> "Usuário ou senha inválidos"
            exception.message?.contains("network") == true -> "Erro de conexão"
            exception.message?.contains("timeout") == true -> "Tempo limite excedido"
            else -> "Erro ao fazer login: ${exception.message}"
        }
    }
}
