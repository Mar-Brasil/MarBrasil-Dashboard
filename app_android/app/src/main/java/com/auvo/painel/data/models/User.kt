package com.auvo.painel.data.models

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

@Parcelize
data class User(
    val id: Int,
    val nome_completo: String,
    val cpf: String,
    val data_nascimento: String?,
    val foto: String?,
    val username: String,
    val permissoes: List<String>,
    val contratos: List<Int>
) : Parcelable
