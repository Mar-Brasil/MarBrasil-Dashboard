package com.auvo.painel.notifications

import android.content.Context
import androidx.work.*
import com.auvo.painel.utils.PreferencesManager
import java.util.concurrent.TimeUnit

object NotificationScheduler {
    
    private const val NOTIFICATION_WORK_NAME = "auvo_notification_work"
    
    fun scheduleNotifications(context: Context) {
        val preferencesManager = PreferencesManager(context)
        
        if (!preferencesManager.areNotificationsEnabled()) {
            cancelNotifications(context)
            return
        }
        
        val frequency = preferencesManager.getNotificationFrequency()
        
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .setRequiresBatteryNotLow(false)
            .build()
        
        val notificationWork = PeriodicWorkRequestBuilder<NotificationWorker>(
            frequency.minutes, TimeUnit.MINUTES
        )
            .setConstraints(constraints)
            .setBackoffCriteria(
                BackoffPolicy.LINEAR,
                WorkRequest.MIN_BACKOFF_MILLIS,
                TimeUnit.MILLISECONDS
            )
            .build()
        
        WorkManager.getInstance(context)
            .enqueueUniquePeriodicWork(
                NOTIFICATION_WORK_NAME,
                ExistingPeriodicWorkPolicy.REPLACE,
                notificationWork
            )
    }
    
    fun cancelNotifications(context: Context) {
        WorkManager.getInstance(context)
            .cancelUniqueWork(NOTIFICATION_WORK_NAME)
    }
    
    fun isScheduled(context: Context): Boolean {
        val workInfos = WorkManager.getInstance(context)
            .getWorkInfosForUniqueWork(NOTIFICATION_WORK_NAME)
            .get()
        
        return workInfos.any { workInfo ->
            workInfo.state == WorkInfo.State.ENQUEUED || workInfo.state == WorkInfo.State.RUNNING
        }
    }
}
