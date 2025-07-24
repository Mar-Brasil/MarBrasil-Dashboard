package com.auvo.painel.data.repository

import com.auvo.painel.data.api.ApiClient
import com.auvo.painel.data.api.ApiService
import com.auvo.painel.data.models.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class DashboardRepository(
    private val apiService: ApiService = ApiClient.apiService
) {
    
    suspend fun login(username: String, password: String): Result<User> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.login(LoginRequest(username, password))
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Login failed: ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun getDashboardData(contractIds: List<Int>): Result<List<DashboardData>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getDashboardBatch(DashboardBatchRequest(contractIds))
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Failed to load dashboard data: ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun getContracts(): Result<List<Contract>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getContracts()
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Failed to load contracts: ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun getDashboardByContract(contractId: Int): Result<DashboardData> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getDashboardByContract(contractId)
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Failed to load contract dashboard: ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun getUserTasks(userId: Int): Result<List<Task>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getUserTasks(userId)
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Failed to load user tasks: ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun getPendingTasks(contractIds: List<Int>): Result<List<Task>> {
        return withContext(Dispatchers.IO) {
            try {
                val contractIdsString = contractIds.joinToString(",")
                val response = apiService.getPendingTasks(contractIdsString)
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Failed to load pending tasks: ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun getDueTasks(contractIds: List<Int>, daysAhead: Int = 7): Result<List<Task>> {
        return withContext(Dispatchers.IO) {
            try {
                val contractIdsString = contractIds.joinToString(",")
                val response = apiService.getDueTasks(contractIdsString, daysAhead)
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Failed to load due tasks: ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
}
