package com.auvo.painel.ui.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.auvo.painel.R
import com.auvo.painel.data.models.Task
import com.google.android.material.chip.Chip
import java.text.SimpleDateFormat
import java.util.*

class TasksAdapter(
    private val onTaskClick: (Task) -> Unit
) : ListAdapter<Task, TasksAdapter.TaskViewHolder>(TaskDiffCallback()) {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): TaskViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_task, parent, false)
        return TaskViewHolder(view, onTaskClick)
    }
    
    override fun onBindViewHolder(holder: TaskViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
    
    class TaskViewHolder(
        itemView: View,
        private val onTaskClick: (Task) -> Unit
    ) : RecyclerView.ViewHolder(itemView) {
        
        private val ivTaskType: ImageView = itemView.findViewById(R.id.ivTaskType)
        private val tvTaskTitle: TextView = itemView.findViewById(R.id.tvTaskTitle)
        private val chipStatus: Chip = itemView.findViewById(R.id.chipStatus)
        private val tvSchoolName: TextView = itemView.findViewById(R.id.tvSchoolName)
        private val tvTaskDate: TextView = itemView.findViewById(R.id.tvTaskDate)
        private val tvCollaboratorName: TextView = itemView.findViewById(R.id.tvCollaboratorName)
        private val tvEquipmentCount: TextView = itemView.findViewById(R.id.tvEquipmentCount)
        
        fun bind(task: Task) {
            // Set task title
            tvTaskTitle.text = task.orientation
            
            // Set task type icon
            val taskTypeInfo = getTaskTypeInfo(task)
            ivTaskType.setImageResource(taskTypeInfo.iconRes)
            ivTaskType.setColorFilter(ContextCompat.getColor(itemView.context, taskTypeInfo.colorRes))
            
            // Set status chip
            setupStatusChip(task.status)
            
            // Set school name
            tvSchoolName.text = task.customerName ?: "Escola não informada"
            
            // Set task date
            val date = task.checkInDate ?: task.lastUpdate
            tvTaskDate.text = if (date != null) {
                formatDate(date)
            } else {
                "Data não informada"
            }
            
            // Set collaborator name
            tvCollaboratorName.text = task.userName ?: "Colaborador não informado"
            
            // Set equipment count
            val equipmentCount = getEquipmentCount(task)
            if (equipmentCount > 0) {
                tvEquipmentCount.text = "$equipmentCount equip."
                tvEquipmentCount.visibility = View.VISIBLE
            } else {
                tvEquipmentCount.visibility = View.GONE
            }
            
            // Set click listener
            itemView.setOnClickListener {
                onTaskClick(task)
            }
        }
        
        private fun getTaskTypeInfo(task: Task): TaskTypeInfo {
            val orientation = task.orientation.lowercase()
            val taskTypeName = task.taskTypeName?.lowercase() ?: ""
            
            return when {
                orientation.contains("mensal") || taskTypeName.contains("mensal") -> 
                    TaskTypeInfo(R.drawable.ic_mensal, R.color.task_mensal)
                orientation.contains("semestral") || taskTypeName.contains("semestral") -> 
                    TaskTypeInfo(R.drawable.ic_semestral, R.color.task_semestral)
                orientation.contains("corretiva") || taskTypeName.contains("corretiva") -> 
                    TaskTypeInfo(R.drawable.ic_corretiva, R.color.task_corretiva)
                orientation.contains("pmoc") || taskTypeName.contains("pmoc") -> 
                    TaskTypeInfo(R.drawable.ic_pmoc, R.color.task_pmoc)
                else -> 
                    TaskTypeInfo(R.drawable.ic_task_default, R.color.text_secondary)
            }
        }
        
        private fun setupStatusChip(status: String) {
            when (status.lowercase()) {
                "concluída", "concluida", "completed" -> {
                    chipStatus.text = "Concluída"
                    chipStatus.setChipBackgroundColorResource(R.color.status_completed)
                    chipStatus.setTextColor(ContextCompat.getColor(itemView.context, android.R.color.white))
                }
                "pendente", "pending" -> {
                    chipStatus.text = "Pendente"
                    chipStatus.setChipBackgroundColorResource(R.color.status_pending)
                    chipStatus.setTextColor(ContextCompat.getColor(itemView.context, android.R.color.white))
                }
                "em andamento", "in_progress" -> {
                    chipStatus.text = "Em Andamento"
                    chipStatus.setChipBackgroundColorResource(R.color.status_in_progress)
                    chipStatus.setTextColor(ContextCompat.getColor(itemView.context, android.R.color.white))
                }
                else -> {
                    chipStatus.text = status
                    chipStatus.setChipBackgroundColorResource(R.color.background_divider)
                    chipStatus.setTextColor(ContextCompat.getColor(itemView.context, R.color.text_primary))
                }
            }
        }
        
        private fun formatDate(dateString: String): String {
            return try {
                // Try different date formats
                val inputFormats = listOf(
                    SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault()),
                    SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()),
                    SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
                )
                
                val outputFormat = SimpleDateFormat("dd/MM/yyyy", Locale.getDefault())
                
                for (format in inputFormats) {
                    try {
                        val date = format.parse(dateString)
                        return outputFormat.format(date!!)
                    } catch (e: Exception) {
                        continue
                    }
                }
                
                dateString // Return original if no format matches
            } catch (e: Exception) {
                dateString
            }
        }
        
        private fun getEquipmentCount(task: Task): Int {
            return try {
                if (task.equipmentsId.isNullOrEmpty()) {
                    0
                } else {
                    // Count comma-separated equipment IDs
                    task.equipmentsId.split(",").size
                }
            } catch (e: Exception) {
                0
            }
        }
    }
    
    data class TaskTypeInfo(
        val iconRes: Int,
        val colorRes: Int
    )
}

class TaskDiffCallback : DiffUtil.ItemCallback<Task>() {
    override fun areItemsTheSame(oldItem: Task, newItem: Task): Boolean {
        return oldItem.id == newItem.id
    }
    
    override fun areContentsTheSame(oldItem: Task, newItem: Task): Boolean {
        return oldItem == newItem
    }
}
