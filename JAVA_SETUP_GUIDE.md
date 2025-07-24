# 🚨 Guia de Instalação do Java 8/11 para Android

## Problema Identificado
Você está usando **Java 21** que é incompatível com Gradle 7.x. O Android Studio precisa de Java 8 ou 11.

## ✅ Solução Recomendada: Instalar Java 8

### 📥 Download do Java 8
1. **Acesse:** https://adoptium.net/temurin/releases/?version=8
2. **Selecione:**
   - Version: 8
   - Operating System: Windows
   - Architecture: x64
   - Package Type: JDK
3. **Baixe:** OpenJDK 8 (.msi)

### 🔧 Instalação
1. Execute o arquivo `.msi` baixado
2. Siga o assistente de instalação
3. Instale em: `C:\Program Files\Eclipse Adoptium\jdk-8.0.XXX-hotspot\`

### 🌍 Configurar Variáveis de Ambiente

#### Método 1: Via Interface Gráfica
1. **Abra:** Painel de Controle → Sistema → Configurações Avançadas
2. **Clique:** "Variáveis de Ambiente"
3. **Adicione nova variável do sistema:**
   - Nome: `JAVA_HOME`
   - Valor: `C:\Program Files\Eclipse Adoptium\jdk-8.0.XXX-hotspot`
4. **Edite a variável PATH:**
   - Adicione: `%JAVA_HOME%\bin`

#### Método 2: Via PowerShell (Administrador)
```powershell
# Definir JAVA_HOME
[Environment]::SetEnvironmentVariable("JAVA_HOME", "C:\Program Files\Eclipse Adoptium\jdk-8.0.XXX-hotspot", "Machine")

# Adicionar ao PATH
$path = [Environment]::GetEnvironmentVariable("PATH", "Machine")
$newPath = "$path;%JAVA_HOME%\bin"
[Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
```

### ✅ Verificar Instalação
```powershell
# Reinicie o PowerShell e execute:
java -version
javac -version
echo $env:JAVA_HOME
```

**Resultado esperado:**
```
openjdk version "1.8.0_XXX"
OpenJDK Runtime Environment (Temurin)(build 1.8.0_XXX)
OpenJDK 64-Bit Server VM (Temurin)(build 25.XXX, mixed mode)
```

## 🔄 Alternativa: Usar Java 11
Se preferir Java 11:
1. **Download:** https://adoptium.net/temurin/releases/?version=11
2. **Siga os mesmos passos** de instalação e configuração

## 🎯 Configurar Android Studio

### 1. Definir JDK no Android Studio
1. **Abra:** Android Studio
2. **Vá para:** File → Settings → Build, Execution, Deployment → Build Tools → Gradle
3. **Gradle JVM:** Selecione o Java 8 instalado
4. **Clique:** Apply → OK

### 2. Configurar Projeto
1. **Abra:** File → Project Structure
2. **SDK Location:** Verifique se JDK Location aponta para Java 8
3. **Clique:** Apply → OK

## 🚀 Testar o Projeto

### 1. Limpar Cache
```powershell
cd "C:\App Painel Auvo"
.\fix_java_compatibility.ps1
```

### 2. Abrir no Android Studio
1. **File → Open**
2. **Selecione:** `C:\App Painel Auvo\app_android`
3. **Aguarde:** Sincronização do Gradle

### 3. Se ainda houver erro
1. **File → Invalidate Caches and Restart**
2. **Build → Clean Project**
3. **Build → Rebuild Project**

## 📋 Versões Configuradas no Projeto

- **Gradle:** 7.3.3
- **Android Gradle Plugin:** 7.2.2
- **Kotlin:** 1.6.21
- **Compile SDK:** 33
- **Target SDK:** 33
- **Min SDK:** 24

## 🆘 Solução de Problemas

### Erro: "JAVA_HOME não definido"
```powershell
# Verificar se JAVA_HOME está definido
echo $env:JAVA_HOME

# Se vazio, definir manualmente
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-8.0.XXX-hotspot"
```

### Erro: "Java não encontrado"
```powershell
# Verificar PATH
echo $env:PATH | Select-String "java"

# Adicionar ao PATH da sessão atual
$env:PATH = "$env:PATH;$env:JAVA_HOME\bin"
```

### Múltiplas versões de Java
1. **Desinstale** versões antigas do Java
2. **Mantenha apenas** Java 8 ou 11
3. **Reinicie** o computador

## ✅ Checklist Final

- [ ] Java 8 ou 11 instalado
- [ ] JAVA_HOME configurado
- [ ] PATH atualizado
- [ ] Android Studio configurado
- [ ] Cache do Gradle limpo
- [ ] Projeto sincronizado

---

**Após seguir este guia, o projeto Android deve abrir sem erros no Android Studio.**
