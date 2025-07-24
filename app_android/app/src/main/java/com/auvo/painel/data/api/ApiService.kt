package com.auvo.painel.data.api

import com.auvo.painel.data.models.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    
    @POST("login")
    suspend fun login(@Body loginRequest: LoginRequest): Response<User>
    
    @POST("api/dashboard/batch")
    suspend fun getDashboardBatch(@Body request: DashboardBatchRequest): Response<List<DashboardData>>
    
    @GET("api/contracts")
    suspend fun getContracts(): Response<List<Contract>>
    
    @GET("api/dashboard/{contractId}")
    suspend fun getDashboardByContract(@Path("contractId") contractId: Int): Response<DashboardData>
    
    @GET("api/tasks/user/{userId}")
    suspend fun getUserTasks(@Path("userId") userId: Int): Response<List<Task>>
    
    @GET("api/tasks/contract/{contractId}")
    suspend fun getContractTasks(@Path("contractId") contractId: Int): Response<List<Task>>
    
    @GET("api/tasks/pending")
    suspend fun getPendingTasks(@Query("contract_ids") contractIds: String): Response<List<Task>>
    
    @GET("api/tasks/due")
    suspend fun getDueTasks(
        @Query("contract_ids") contractIds: String,
        @Query("days_ahead") daysAhead: Int = 7
    ): Response<List<Task>>
}
