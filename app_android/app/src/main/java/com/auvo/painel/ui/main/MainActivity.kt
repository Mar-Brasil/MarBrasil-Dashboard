package com.auvo.painel.ui.main

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.GridLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.auvo.painel.R
import com.auvo.painel.data.models.*
import com.auvo.painel.data.repository.DashboardRepository
import com.auvo.painel.databinding.ActivityMainBinding
import com.auvo.painel.ui.adapters.TasksAdapter
import com.auvo.painel.ui.login.LoginActivity
import com.auvo.painel.ui.settings.SettingsActivity
import com.auvo.painel.utils.PreferencesManager
import com.google.android.material.card.MaterialCardView
import com.google.android.material.chip.Chip
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    private lateinit var repository: DashboardRepository
    private lateinit var preferencesManager: PreferencesManager
    private lateinit var tasksAdapter: TasksAdapter
    
    private var currentUser: User? = null
    private var dashboardData: List<DashboardData> = emptyList()
    private var currentFilter: TaskFilter = TaskFilter.ALL
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        repository = DashboardRepository()
        preferencesManager = PreferencesManager(this)
        
        setupUI()
        getUserFromIntent()
        loadDashboardData()
    }
    
    private fun setupUI() {
        setSupportActionBar(binding.toolbar)
        
        // Setup RecyclerView
        tasksAdapter = TasksAdapter { task ->
            // Handle task click
            // TODO: Navigate to task details
        }
        binding.recyclerTasks.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = tasksAdapter
        }
        
        // Setup click listeners
        binding.btnRefresh.setOnClickListener {
            loadDashboardData()
        }
        
        binding.btnRetry.setOnClickListener {
            loadDashboardData()
        }
        
        binding.fabSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
        
        // Setup bottom navigation
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_dashboard -> {
                    currentFilter = TaskFilter.ALL
                    filterTasks()
                    true
                }
                R.id.nav_prev_mensal -> {
                    currentFilter = TaskFilter.MENSAL
                    filterTasks()
                    true
                }
                R.id.nav_prev_semestral -> {
                    currentFilter = TaskFilter.SEMESTRAL
                    filterTasks()
                    true
                }
                R.id.nav_corretiva -> {
                    currentFilter = TaskFilter.CORRETIVA
                    filterTasks()
                    true
                }
                R.id.nav_pmoc -> {
                    currentFilter = TaskFilter.PMOC
                    filterTasks()
                    true
                }
                else -> false
            }
        }
    }
    
    private fun getUserFromIntent() {
        currentUser = intent.getParcelableExtra("user")
        if (currentUser == null) {
            // Try to get from preferences
            currentUser = preferencesManager.getUser()
        }
        
        if (currentUser == null) {
            // Redirect to login
            startActivity(Intent(this, LoginActivity::class.java))
            finish()
            return
        }
        
        // Update welcome message
        binding.tvWelcome.text = getString(R.string.welcome_user, currentUser!!.nome_completo)
    }
    
    private fun loadDashboardData() {
        val user = currentUser ?: return
        
        showLoading(true)
        hideError()
        
        lifecycleScope.launch {
            try {
                val result = repository.getDashboardData(user.contratos)
                
                result.onSuccess { data ->
                    dashboardData = data
                    updateUI(data)
                    updateLastUpdateTime()
                    
                }.onFailure { exception ->
                    showError("Erro ao carregar dados: ${exception.message}")
                }
                
            } catch (e: Exception) {
                showError("Erro de conexão. Verifique sua internet.")
            } finally {
                showLoading(false)
            }
        }
    }
    
    private fun updateUI(data: List<DashboardData>) {
        if (data.isEmpty()) {
            showError("Nenhum dado encontrado para seus contratos")
            return
        }
        
        // Aggregate data from all contracts
        val aggregatedKpis = aggregateKpis(data)
        val allTasks = data.flatMap { it.tasks }
        
        // Update KPIs
        updateKpiCards(aggregatedKpis)
        
        // Update progress
        updateProgressSection(aggregatedKpis)
        
        // Update tasks
        updateTasksList(allTasks)
        
        showContent(true)
    }
    
    private fun aggregateKpis(data: List<DashboardData>): KpiData {
        return KpiData(
            total_schools = data.sumOf { it.kpis.total_schools },
            total_collaborators = data.sumOf { it.kpis.total_collaborators },
            total_equipments = data.sumOf { it.kpis.total_equipments },
            tasks_completed = data.sumOf { it.kpis.tasks_completed },
            tasks_pending = data.sumOf { it.kpis.tasks_pending },
            tasks_in_progress = data.sumOf { it.kpis.tasks_in_progress },
            overall_progress = data.map { it.kpis.overall_progress }.average(),
            mensal_progress = data.map { it.kpis.mensal_progress }.average(),
            semestral_progress = data.map { it.kpis.semestral_progress }.average(),
            corretiva_count = data.sumOf { it.kpis.corretiva_count },
            pmoc_progress = data.map { it.kpis.pmoc_progress }.average()
        )
    }
    
    private fun updateKpiCards(kpis: KpiData) {
        binding.gridKpis.removeAllViews()
        
        val kpiItems = listOf(
            KpiItem("Escolas", kpis.total_schools.toString(), R.drawable.ic_school),
            KpiItem("Colaboradores", kpis.total_collaborators.toString(), R.drawable.ic_people),
            KpiItem("Equipamentos", kpis.total_equipments.toString(), R.drawable.ic_build),
            KpiItem("Concluídas", kpis.tasks_completed.toString(), R.drawable.ic_check),
            KpiItem("Pendentes", kpis.tasks_pending.toString(), R.drawable.ic_pending),
            KpiItem("Progresso", "${kpis.overall_progress.toInt()}%", R.drawable.ic_progress)
        )
        
        kpiItems.forEach { kpiItem ->
            val kpiView = layoutInflater.inflate(R.layout.item_kpi, binding.gridKpis, false)
            
            kpiView.findViewById<TextView>(R.id.tvKpiTitle).text = kpiItem.title
            kpiView.findViewById<TextView>(R.id.tvKpiValue).text = kpiItem.value
            kpiView.findViewById<ImageView>(R.id.ivKpiIcon).setImageResource(kpiItem.iconRes)
            
            val layoutParams = GridLayout.LayoutParams().apply {
                width = 0
                height = GridLayout.LayoutParams.WRAP_CONTENT
                columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f)
                setMargins(8, 8, 8, 8)
            }
            kpiView.layoutParams = layoutParams
            
            binding.gridKpis.addView(kpiView)
        }
    }
    
    private fun updateProgressSection(kpis: KpiData) {
        binding.layoutProgress.removeAllViews()
        
        val progressItems = listOf(
            ProgressItem("Prev. Mensal", kpis.mensal_progress, R.drawable.ic_mensal, R.color.task_mensal),
            ProgressItem("Prev. Semestral", kpis.semestral_progress, R.drawable.ic_semestral, R.color.task_semestral),
            ProgressItem("Corretiva", (kpis.corretiva_count / 10.0) * 100, R.drawable.ic_corretiva, R.color.task_corretiva),
            ProgressItem("PMOC", kpis.pmoc_progress, R.drawable.ic_pmoc, R.color.task_pmoc)
        )
        
        progressItems.forEach { progressItem ->
            val progressView = layoutInflater.inflate(R.layout.item_progress, binding.layoutProgress, false)
            
            progressView.findViewById<TextView>(R.id.tvProgressTitle).text = progressItem.title
            progressView.findViewById<TextView>(R.id.tvProgressPercentage).text = "${progressItem.percentage.toInt()}%"
            progressView.findViewById<ImageView>(R.id.ivProgressIcon).setImageResource(progressItem.iconRes)
            
            val progressBar = progressView.findViewById<android.widget.ProgressBar>(R.id.progressBar)
            progressBar.progress = progressItem.percentage.toInt()
            progressBar.progressTintList = getColorStateList(progressItem.colorRes)
            
            binding.layoutProgress.addView(progressView)
        }
    }
    
    private fun updateTasksList(tasks: List<Task>) {
        val recentTasks = tasks.sortedByDescending { it.lastUpdate ?: it.checkInDate }.take(10)
        tasksAdapter.submitList(recentTasks)
    }
    
    private fun filterTasks() {
        val allTasks = dashboardData.flatMap { it.tasks }
        val filteredTasks = when (currentFilter) {
            TaskFilter.ALL -> allTasks
            TaskFilter.MENSAL -> allTasks.filter { isTaskType(it, "mensal") }
            TaskFilter.SEMESTRAL -> allTasks.filter { isTaskType(it, "semestral") }
            TaskFilter.CORRETIVA -> allTasks.filter { isTaskType(it, "corretiva") }
            TaskFilter.PMOC -> allTasks.filter { isTaskType(it, "pmoc") }
        }
        
        tasksAdapter.submitList(filteredTasks.take(20))
    }
    
    private fun isTaskType(task: Task, type: String): Boolean {
        val orientation = task.orientation.lowercase()
        val taskTypeName = task.taskTypeName?.lowercase() ?: ""
        
        return when (type) {
            "mensal" -> orientation.contains("mensal") || taskTypeName.contains("mensal")
            "semestral" -> orientation.contains("semestral") || taskTypeName.contains("semestral")
            "corretiva" -> orientation.contains("corretiva") || taskTypeName.contains("corretiva")
            "pmoc" -> orientation.contains("pmoc") || taskTypeName.contains("pmoc")
            else -> true
        }
    }
    
    private fun updateLastUpdateTime() {
        val currentTime = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault()).format(Date())
        binding.tvLastUpdate.text = "Última atualização: $currentTime"
        preferencesManager.setLastSyncTime(System.currentTimeMillis())
    }
    
    private fun showLoading(show: Boolean) {
        binding.layoutLoading.visibility = if (show) View.VISIBLE else View.GONE
        binding.btnRefresh.isEnabled = !show
    }
    
    private fun showError(message: String) {
        binding.layoutError.visibility = View.VISIBLE
        binding.tvError.text = message
        showContent(false)
    }
    
    private fun hideError() {
        binding.layoutError.visibility = View.GONE
    }
    
    private fun showContent(show: Boolean) {
        val visibility = if (show) View.VISIBLE else View.GONE
        binding.gridKpis.visibility = visibility
        binding.layoutProgress.visibility = visibility
        binding.recyclerTasks.visibility = visibility
    }
}

data class KpiItem(
    val title: String,
    val value: String,
    val iconRes: Int
)

data class ProgressItem(
    val title: String,
    val percentage: Double,
    val iconRes: Int,
    val colorRes: Int
)

enum class TaskFilter {
    ALL, MENSAL, SEMESTRAL, CORRETIVA, PMOC
}
