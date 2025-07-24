package com.auvo.painel.notifications

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.auvo.painel.utils.PreferencesManager

class BootReceiver : BroadcastReceiver() {
    
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED ||
            intent.action == Intent.ACTION_MY_PACKAGE_REPLACED ||
            intent.action == Intent.ACTION_PACKAGE_REPLACED) {
            
            val preferencesManager = PreferencesManager(context)
            
            // Reagenda as notificações se estiverem habilitadas
            if (preferencesManager.areNotificationsEnabled()) {
                NotificationScheduler.scheduleNotifications(context)
            }
        }
    }
}
