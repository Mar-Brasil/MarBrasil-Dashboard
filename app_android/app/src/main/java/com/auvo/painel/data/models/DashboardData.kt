package com.auvo.painel.data.models

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

@Parcelize
data class DashboardBatchRequest(
    val contract_ids: List<Int>
) : Parcelable

@Parcelize
data class DashboardData(
    val contract_id: Int,
    val contract_name: String,
    val schools: List<School>,
    val collaborators: List<Collaborator>,
    val kpis: KpiData,
    val tasks: List<Task>
) : Parcelable

@Parcelize
data class School(
    val id: Int,
    val name: String,
    val description: String,
    val equipments: List<Equipment>,
    val tasks: List<Task>,
    val progress_percentage: Double
) : Parcelable

@Parcelize
data class Equipment(
    val id: Int,
    val name: String,
    val description: String?,
    val tipo: String?,
    val active: Boolean
) : Parcelable

@Parcelize
data class Collaborator(
    val id: Int,
    val name: String,
    val email: String?,
    val tasks_completed: Int,
    val tasks_pending: Int,
    val total_tasks: Int
) : Parcelable

@Parcelize
data class Task(
    val id: Int,
    val orientation: String,
    val status: String,
    val taskType: Int,
    val taskTypeName: String?,
    val customerId: Int,
    val customerName: String?,
    val idUserTo: Int,
    val userName: String?,
    val checkInDate: String?,
    val lastUpdate: String?,
    val equipmentsId: String?,
    val equipmentNames: List<String>?
) : Parcelable

@Parcelize
data class KpiData(
    val total_schools: Int,
    val total_collaborators: Int,
    val total_equipments: Int,
    val tasks_completed: Int,
    val tasks_pending: Int,
    val tasks_in_progress: Int,
    val overall_progress: Double,
    val mensal_progress: Double,
    val semestral_progress: Double,
    val corretiva_count: Int,
    val pmoc_progress: Double
) : Parcelable
