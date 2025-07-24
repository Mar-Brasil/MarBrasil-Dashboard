// Importações de ícones e utilitários
import BuildIcon from '@mui/icons-material/Build';
import ArticleIcon from '@mui/icons-material/Article';
import EventRepeatIcon from '@mui/icons-material/EventRepeat';
import CalendarViewWeekIcon from '@mui/icons-material/CalendarViewWeek';

// Exemplo de importação de utilitário de data (ajuste conforme sua base)
import { isInPeriod } from './dateUtils';

// ---- Ícones usados para taguear escolas com tarefas especiais ----
export const specialTaskIconsConfig = {
  PMOC: {
    description: 'Preventiva Levantamento de PMOC',
    Icon: ArticleIcon,
    color: 'warning.main',
    tooltip: 'Contém tarefa de PMOC'
  },
  MENSAL: {
    description: 'Preventiva Mensal',
    Icon: EventRepeatIcon,
    color: 'success.main',
    tooltip: 'Contém tarefa Mensal'
  },
  SEMESTRAL: {
    description: 'Preventiva Semestral',
    Icon: CalendarViewWeekIcon,
    color: 'info.main',
    tooltip: 'Contém tarefa Semestral'
  },
  CORRETIVA: {
    description: 'Corretiva',
    Icon: BuildIcon,
    color: 'error.main',
    tooltip: 'Contém tarefa Corretiva'
  }
};

// ---- Funções utilitárias extraídas do Dashboard.js ----

// Formata uma data para dd/mm/yyyy
export function formatDate(dateString) {
  const date = new Date(dateString);
  if (isNaN(date)) return '';
  return date.toLocaleDateString('pt-BR');
}

// Retorna uma cor baseada no percentual
export function getPercentageColor(percentage) {
  if (percentage >= 90) return 'success.main';
  if (percentage >= 70) return 'warning.main';
  return 'error.main';
}

// Verifica se a data pertence ao intervalo informado (inclusive)
export function isInPeriodUtil(dateLike, start, end) {
  return isInPeriod(dateLike, start, end);
}

// Calcula a porcentagem de tarefas válidas concluídas para a escola
export function getSchoolPercentual(school, startDate, endDate) {
  // ... (implemente aqui conforme seu Dashboard.js)
}

// Função para remover IDs numéricos do início dos nomes das escolas
export function cleanSchoolName(name) {
  if (!name) return '';
  return name.replace(/^[0-9]+\s*-\s*/, '').trim();
}

// Função para contar equipamentos em uma tarefa
export function getEquipmentCount(task) {
  if (!task || !task.equipmentsId) return 0;
  if (Array.isArray(task.equipmentsId)) return task.equipmentsId.length;
  return String(task.equipmentsId).split(',').filter(Boolean).length;
}

// Verifica se a tarefa pertence à categoria
export function matchesCategory(task, cat) {
  // ... (implemente aqui conforme seu Dashboard.js)
}

// Retorna array de IDs numéricos a partir de task.equipmentsId
export function parseEquipIds(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw.map(Number).filter(n => !isNaN(n));
  return String(raw)
    .split(',')
    .map(s => parseInt(s, 10))
    .filter(n => !isNaN(n));
}

// Outras funções utilitárias do Dashboard (adicione conforme necessidade)
