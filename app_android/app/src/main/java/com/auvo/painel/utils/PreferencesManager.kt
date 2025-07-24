package com.auvo.painel.utils

import android.content.Context
import android.content.SharedPreferences
import com.auvo.painel.data.models.User
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

class PreferencesManager(context: Context) {
    
    private val sharedPreferences: SharedPreferences = 
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val gson = Gson()
    
    companion object {
        private const val PREFS_NAME = "auvo_painel_prefs"
        private const val KEY_USER = "user"
        private const val KEY_NOTIFICATIONS_ENABLED = "notifications_enabled"
        private const val KEY_NOTIFICATION_FREQUENCY = "notification_frequency"
        private const val KEY_NOTIFICATION_TYPES = "notification_types"
        private const val KEY_DUE_DAYS_AHEAD = "due_days_ahead"
        private const val KEY_LAST_SYNC = "last_sync"
        private const val KEY_AUTO_LOGIN = "auto_login"
    }
    
    // User Management
    fun saveUser(user: User) {
        val userJson = gson.toJson(user)
        sharedPreferences.edit()
            .putString(KEY_USER, userJson)
            .apply()
    }
    
    fun getUser(): User? {
        val userJson = sharedPreferences.getString(KEY_USER, null)
        return if (userJson != null) {
            try {
                gson.fromJson(userJson, User::class.java)
            } catch (e: Exception) {
                null
            }
        } else {
            null
        }
    }
    
    fun clearUser() {
        sharedPreferences.edit()
            .remove(KEY_USER)
            .apply()
    }
    
    // Auto Login
    fun setAutoLogin(enabled: Boolean) {
        sharedPreferences.edit()
            .putBoolean(KEY_AUTO_LOGIN, enabled)
            .apply()
    }
    
    fun isAutoLoginEnabled(): Boolean {
        return sharedPreferences.getBoolean(KEY_AUTO_LOGIN, true)
    }
    
    // Notifications Settings
    fun setNotificationsEnabled(enabled: Boolean) {
        sharedPreferences.edit()
            .putBoolean(KEY_NOTIFICATIONS_ENABLED, enabled)
            .apply()
    }
    
    fun areNotificationsEnabled(): Boolean {
        return sharedPreferences.getBoolean(KEY_NOTIFICATIONS_ENABLED, true)
    }
    
    fun setNotificationFrequency(frequency: NotificationFrequency) {
        sharedPreferences.edit()
            .putString(KEY_NOTIFICATION_FREQUENCY, frequency.name)
            .apply()
    }
    
    fun getNotificationFrequency(): NotificationFrequency {
        val frequencyName = sharedPreferences.getString(KEY_NOTIFICATION_FREQUENCY, NotificationFrequency.HOURLY.name)
        return try {
            NotificationFrequency.valueOf(frequencyName!!)
        } catch (e: Exception) {
            NotificationFrequency.HOURLY
        }
    }
    
    fun setNotificationTypes(types: Set<NotificationType>) {
        val typesJson = gson.toJson(types.map { it.name })
        sharedPreferences.edit()
            .putString(KEY_NOTIFICATION_TYPES, typesJson)
            .apply()
    }
    
    fun getNotificationTypes(): Set<NotificationType> {
        val typesJson = sharedPreferences.getString(KEY_NOTIFICATION_TYPES, null)
        return if (typesJson != null) {
            try {
                val typeNames: List<String> = gson.fromJson(typesJson, object : TypeToken<List<String>>() {}.type)
                typeNames.mapNotNull { 
                    try { 
                        NotificationType.valueOf(it) 
                    } catch (e: Exception) { 
                        null 
                    } 
                }.toSet()
            } catch (e: Exception) {
                setOf(NotificationType.PENDING_TASKS, NotificationType.DUE_TASKS)
            }
        } else {
            setOf(NotificationType.PENDING_TASKS, NotificationType.DUE_TASKS)
        }
    }
    
    fun setDueDaysAhead(days: Int) {
        sharedPreferences.edit()
            .putInt(KEY_DUE_DAYS_AHEAD, days)
            .apply()
    }
    
    fun getDueDaysAhead(): Int {
        return sharedPreferences.getInt(KEY_DUE_DAYS_AHEAD, 7)
    }
    
    // Sync Management
    fun setLastSyncTime(timestamp: Long) {
        sharedPreferences.edit()
            .putLong(KEY_LAST_SYNC, timestamp)
            .apply()
    }
    
    fun getLastSyncTime(): Long {
        return sharedPreferences.getLong(KEY_LAST_SYNC, 0)
    }
    
    // Clear all preferences
    fun clearAll() {
        sharedPreferences.edit().clear().apply()
    }
}

enum class NotificationFrequency(val minutes: Long) {
    FIFTEEN_MINUTES(15),
    THIRTY_MINUTES(30),
    HOURLY(60),
    SIX_HOURS(360)
}

enum class NotificationType {
    PENDING_TASKS,
    DUE_TASKS
}
