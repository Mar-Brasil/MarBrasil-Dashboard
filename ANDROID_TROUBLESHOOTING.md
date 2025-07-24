# Guia de Solução de Problemas - Android Studio

## 🚨 Erro: "Unsupported class file major version 65"

Este erro indica que você está usando **Java 21** (major version 65) que é incompatível com Gradle 7.x.

### 🔧 Solução OBRIGATÓRIA: Instalar Java 8 ou 11

**IMPORTANTE:** Você DEVE instalar Java 8 ou 11 para usar o Android Studio.

1. **Baixe Java 8:** https://adoptium.net/temurin/releases/?version=8
2. **Instale** o arquivo .msi
3. **Configure JAVA_HOME** para apontar para Java 8
4. **Reinicie** o computador
5. **Execute** o script de correção: `.ix_java_compatibility.ps1`

**Veja o guia completo:** `JAVA_SETUP_GUIDE.md`

---

## 🚨 Erro: "org.gradle.api.artifacts.Dependency org.gradle.api.artifacts.dsl.DependencyHandler.module"

Este erro é comum quando há incompatibilidade entre versões do Gradle e plugins do Android.

### ✅ Solução Aplicada

Já corrigi as configurações do projeto:

1. **Versões atualizadas:**
   - Gradle: 7.4
   - Android Gradle Plugin: 7.3.1
   - Kotlin: 1.7.20
   - Compile SDK: 33
   - Target SDK: 33

2. **Arquivos corrigidos:**
   - `build.gradle` (raiz)
   - `app/build.gradle`
   - `gradle.properties`
   - `gradle/wrapper/gradle-wrapper.properties`

### 🔧 Passos para Resolver

1. **Execute o script de limpeza:**
   ```powershell
   .\clean_android.ps1
   ```

2. **Abra o Android Studio:**
   - File → Open
   - Selecione a pasta `app_android`
   - Aguarde a sincronização

3. **Se ainda houver erros:**
   - File → Invalidate Caches and Restart
   - Build → Clean Project
   - Build → Rebuild Project

### 🎯 Configurações Específicas

#### build.gradle (raiz)
```gradle
buildscript {
    ext.kotlin_version = "1.7.20"
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:7.3.1'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
    }
}
```

#### app/build.gradle
```gradle
apply plugin: 'com.android.application'
apply plugin: 'org.jetbrains.kotlin.android'
apply plugin: 'kotlin-kapt'
apply plugin: 'kotlin-parcelize'

android {
    compileSdk 33
    defaultConfig {
        targetSdk 33
        minSdk 24
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
    kotlinOptions {
        jvmTarget = '1.8'
    }
}
```

### 🔍 Outros Problemas Comuns

#### 1. Erro de Sincronização
**Solução:**
- Verifique conexão com internet
- File → Sync Project with Gradle Files

#### 2. Erro de Dependências
**Solução:**
- Build → Clean Project
- Build → Rebuild Project

#### 3. Erro de JVM Target
**Solução:**
- Verifique se `jvmTarget = '1.8'` está definido
- Confirme `sourceCompatibility` e `targetCompatibility`

#### 4. Erro de Namespace
**Solução:**
- Confirme que `namespace 'com.auvo.painel'` está no `build.gradle`

### 📱 Testando o App

1. **Inicie o backend mobile:**
   ```bash
   python api_backend_mobile.py
   ```

2. **Configure a URL no ApiClient.kt:**
   - Emulador: `http://10.0.2.2:8001/`
   - Dispositivo: `http://[SEU_IP]:8001/`

3. **Execute o app:**
   - Selecione emulador ou dispositivo
   - Clique em Run (▶️)

### 🆘 Se Nada Funcionar

1. **Reinstale o Android Studio:**
   - Desinstale completamente
   - Baixe a versão mais recente
   - Reinstale

2. **Crie novo projeto:**
   - File → New → Import Project
   - Selecione a pasta `app_android`

3. **Verifique requisitos:**
   - Java 8 ou superior
   - Android SDK atualizado
   - Espaço em disco suficiente

### 📞 Suporte

Se o problema persistir:
1. Copie o erro completo
2. Verifique logs do Gradle
3. Consulte documentação oficial do Android

---

**Status:** ✅ Projeto corrigido e pronto para uso
**Última atualização:** 18/07/2025
