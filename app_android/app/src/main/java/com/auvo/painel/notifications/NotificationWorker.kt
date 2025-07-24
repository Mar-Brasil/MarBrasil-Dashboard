package com.auvo.painel.notifications

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.auvo.painel.R
import com.auvo.painel.data.repository.DashboardRepository
import com.auvo.painel.ui.main.MainActivity
import com.auvo.painel.utils.NotificationType
import com.auvo.painel.utils.PreferencesManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class NotificationWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {
    
    private val preferencesManager = PreferencesManager(context)
    private val repository = DashboardRepository()
    
    companion object {
        const val CHANNEL_ID = "auvo_tasks_channel"
        const val PENDING_TASKS_NOTIFICATION_ID = 1001
        const val DUE_TASKS_NOTIFICATION_ID = 1002
    }
    
    override suspend fun doWork(): Result {
        return withContext(Dispatchers.IO) {
            try {
                // Verifica se as notificações estão habilitadas
                if (!preferencesManager.areNotificationsEnabled()) {
                    return@withContext Result.success()
                }
                
                val user = preferencesManager.getUser()
                if (user == null || user.contratos.isEmpty()) {
                    return@withContext Result.success()
                }
                
                createNotificationChannel()
                
                val notificationTypes = preferencesManager.getNotificationTypes()
                
                // Verifica tarefas pendentes
                if (notificationTypes.contains(NotificationType.PENDING_TASKS)) {
                    checkPendingTasks(user.contratos)
                }
                
                // Verifica tarefas próximas do prazo
                if (notificationTypes.contains(NotificationType.DUE_TASKS)) {
                    checkDueTasks(user.contratos)
                }
                
                Result.success()
                
            } catch (e: Exception) {
                android.util.Log.e("NotificationWorker", "Erro ao verificar notificações", e)
                Result.retry()
            }
        }
    }
    
    private suspend fun checkPendingTasks(contractIds: List<Int>) {
        try {
            val result = repository.getPendingTasks(contractIds)
            
            result.onSuccess { tasks ->
                if (tasks.isNotEmpty()) {
                    val title = "Tarefas Pendentes"
                    val content = when {
                        tasks.size == 1 -> "Você tem 1 tarefa pendente"
                        else -> "Você tem ${tasks.size} tarefas pendentes"
                    }
                    
                    showNotification(
                        id = PENDING_TASKS_NOTIFICATION_ID,
                        title = title,
                        content = content,
                        tasks = tasks.take(5) // Mostra até 5 tarefas
                    )
                }
            }
            
        } catch (e: Exception) {
            android.util.Log.e("NotificationWorker", "Erro ao verificar tarefas pendentes", e)
        }
    }
    
    private suspend fun checkDueTasks(contractIds: List<Int>) {
        try {
            val daysAhead = preferencesManager.getDueDaysAhead()
            val result = repository.getDueTasks(contractIds, daysAhead)
            
            result.onSuccess { tasks ->
                if (tasks.isNotEmpty()) {
                    val title = "Tarefas Próximas do Prazo"
                    val content = when {
                        tasks.size == 1 -> "1 tarefa está próxima do prazo"
                        else -> "${tasks.size} tarefas estão próximas do prazo"
                    }
                    
                    showNotification(
                        id = DUE_TASKS_NOTIFICATION_ID,
                        title = title,
                        content = content,
                        tasks = tasks.take(5) // Mostra até 5 tarefas
                    )
                }
            }
            
        } catch (e: Exception) {
            android.util.Log.e("NotificationWorker", "Erro ao verificar tarefas próximas do prazo", e)
        }
    }
    
    private fun showNotification(
        id: Int,
        title: String,
        content: String,
        tasks: List<com.auvo.painel.data.models.Task>
    ) {
        val notificationManager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        
        // Intent para abrir o app
        val intent = Intent(applicationContext, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        
        val pendingIntent = PendingIntent.getActivity(
            applicationContext,
            id,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        val notificationBuilder = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle(title)
            .setContentText(content)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
        
        // Adiciona estilo expandido se houver múltiplas tarefas
        if (tasks.size > 1) {
            val inboxStyle = NotificationCompat.InboxStyle()
                .setBigContentTitle(title)
                .setSummaryText("${tasks.size} tarefas")
            
            tasks.forEach { task ->
                val taskLine = "${task.customerName}: ${task.orientation}"
                inboxStyle.addLine(taskLine)
            }
            
            notificationBuilder.setStyle(inboxStyle)
        }
        
        notificationManager.notify(id, notificationBuilder.build())
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                applicationContext.getString(R.string.notification_channel_name),
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = applicationContext.getString(R.string.notification_channel_description)
            }
            
            val notificationManager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }
}
