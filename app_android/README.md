# Painel Auvo - Aplicativo Android

Este é o aplicativo Android para o sistema Painel Auvo, desenvolvido em Kotlin com arquitetura moderna e design Material 3.

## 🚀 Funcionalidades

### ✅ Implementadas
- **Login seguro** com autenticação via API
- **Dashboard interativo** com KPIs e métricas
- **Visualização de tarefas** por tipo (Mensal, Semestral, Corretiva, PMOC)
- **Navegação por filtros** na barra inferior
- **Sistema de notificações** para tarefas pendentes e próximas do prazo
- **Configurações personalizáveis** de notificação
- **Interface responsiva** e moderna

### 🔄 Arquitetura
- **MVVM** (Model-View-ViewModel)
- **Repository Pattern** para gerenciamento de dados
- **Retrofit** para comunicação com API
- **Coroutines** para operações assíncronas
- **WorkManager** para notificações em background
- **Material Design 3** para UI/UX

## 🛠️ Configuração

### Pré-requisitos
- Android Studio Arctic Fox ou superior
- SDK Android 24+ (Android 7.0)
- Kotlin 1.8.20+

### Configuração da API
1. **Para Emulador Android:**
   - A URL base está configurada como `http://10.0.2.2:8001/`
   - Inicie o backend mobile: `python api_backend_mobile.py`

2. **Para Dispositivo Físico:**
   - Altere a URL em `ApiClient.kt` para o IP da sua máquina
   - Exemplo: `http://192.168.1.28:8001/`
   - Certifique-se de que o dispositivo está na mesma rede Wi-Fi

### Backend Mobile
O projeto inclui um backend otimizado para mobile (`api_backend_mobile.py`) que:
- Roda na porta 8001 (diferente do backend web)
- Fornece endpoints otimizados para mobile
- Usa o mesmo banco de dados `auvo.db`

## 📱 Como Executar

### Opção 1: Android Studio
1. Abra o projeto no Android Studio
2. Sincronize as dependências Gradle
3. Execute o app no emulador ou dispositivo

### Opção 2: Linha de Comando
```bash
cd app_android
./gradlew assembleDebug
./gradlew installDebug
```

## 🔧 Configuração de Rede

### Firewall Windows
Para permitir conexões do dispositivo físico:
```powershell
New-NetFirewallRule -DisplayName "Auvo Mobile API" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow
```

### Iniciar Backend Mobile
```bash
cd "C:\App Painel Auvo"
python api_backend_mobile.py
```

## 📋 Estrutura do Projeto

```
app_android/
├── app/
│   ├── src/main/
│   │   ├── java/com/auvo/painel/
│   │   │   ├── data/
│   │   │   │   ├── api/          # Retrofit services
│   │   │   │   ├── models/       # Data models
│   │   │   │   └── repository/   # Repository pattern
│   │   │   ├── ui/
│   │   │   │   ├── login/        # Tela de login
│   │   │   │   ├── main/         # Dashboard principal
│   │   │   │   ├── settings/     # Configurações
│   │   │   │   └── adapters/     # RecyclerView adapters
│   │   │   ├── utils/            # Utilities e helpers
│   │   │   └── notifications/    # Sistema de notificações
│   │   └── res/
│   │       ├── layout/           # Layouts XML
│   │       ├── values/           # Strings, colors, themes
│   │       ├── drawable/         # Ícones e drawables
│   │       └── menu/             # Menus de navegação
│   └── build.gradle              # Dependências do módulo
├── build.gradle                  # Configuração raiz
└── settings.gradle               # Configuração do projeto
```

## 🎨 Design System

### Cores Principais
- **Primary:** `#1976D2` (Azul Auvo)
- **Accent:** `#FF5722` (Laranja)
- **Success:** `#4CAF50` (Verde)
- **Warning:** `#FF9800` (Amarelo)
- **Error:** `#F44336` (Vermelho)

### Tipos de Tarefa
- **Mensal:** Verde (`#4CAF50`)
- **Semestral:** Azul (`#2196F3`)
- **Corretiva:** Laranja (`#FF9800`)
- **PMOC:** Roxo (`#9C27B0`)

## 🔔 Sistema de Notificações

### Configurações Disponíveis
- **Frequência:** 15min, 30min, 1h, 6h
- **Tipos:** Tarefas pendentes, próximas do prazo
- **Antecedência:** 1-7 dias para tarefas próximas do prazo

### Funcionamento
- Usa **WorkManager** para execução confiável
- Verifica tarefas em background
- Reagenda automaticamente após reboot
- Respeita configurações de economia de bateria

## 🚀 Próximos Passos

### Funcionalidades Planejadas
- [ ] Detalhes de tarefa individual
- [ ] Filtros avançados
- [ ] Sincronização offline
- [ ] Relatórios em PDF
- [ ] Modo escuro
- [ ] Biometria para login

### Melhorias Técnicas
- [ ] Testes unitários
- [ ] Testes de integração
- [ ] CI/CD pipeline
- [ ] Análise de performance
- [ ] Logs estruturados

## 🐛 Troubleshooting

### Problemas Comuns

**1. Erro de conexão com API**
- Verifique se o backend está rodando
- Confirme a URL no `ApiClient.kt`
- Teste a conectividade de rede

**2. Notificações não funcionam**
- Verifique permissões de notificação
- Confirme configurações de economia de bateria
- Teste em dispositivo físico

**3. Login falha**
- Verifique credenciais no banco
- Confirme hash da senha
- Teste endpoint diretamente

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do Android Studio
2. Teste os endpoints da API diretamente
3. Confirme configurações de rede
4. Verifique permissões do app

## 📄 Licença

Este projeto é propriedade da empresa e destinado ao uso interno do sistema Auvo.
