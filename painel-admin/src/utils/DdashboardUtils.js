import BuildIcon from '@mui/icons-material/Build';
import ArticleIcon from '@mui/icons-material/Article';
import EventRepeatIcon from '@mui/icons-material/EventRepeat';
import React from 'react';
import Grid from '@mui/material/Grid';
import KpiCard from '../components/dashboard/KpiCard';
import CalendarViewWeekIcon from '@mui/icons-material/CalendarViewWeek';

import { isInPeriod } from './dateUtils';

// ---- Icons used to tag schools with special tasks ----
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

// ---- Simple helpers ----
export const getPercentageColor = (pct) => {
  if (pct === 100) return 'success.main';
  if (pct >= 50) return 'warning.main';
  if (pct >= 20) return 'orange';
  return 'error.main';
};

export function cleanSchoolName(name = '') {
  return name.replace(/^[\[({]?\d+(,\s*\d+)*[\]})]?\s*-\s*/, '');
}

// ---- KPI & task helpers ----
export const TASK_TYPE_IDS = {
  PREVENTIVA_MENSAL: 175648,
  PREVENTIVA_SEMESTRAL: 175652,
  PMOC: 175656,
  CORRETIVA: 175644,
};

export const ALLOWED_PROGRESS_KEYWORDS = [
  'preventiva mensal',
  'mensal',
  'semestral',
  'preventiva semestral',
];

export const KPI_TOTAL_EQUIP = 478;

export const KPI_CATEGORIES = {
  MENSAL: {
    ids: [TASK_TYPE_IDS.PREVENTIVA_MENSAL, TASK_TYPE_IDS.PREVENTIVA_SEMESTRAL],
    keywords: ['preventiva mensal', 'mensal', 'semestral', 'preventiva semestral'],
    denominator: KPI_TOTAL_EQUIP,
  },
  SEMESTRAL: {
    ids: [TASK_TYPE_IDS.PREVENTIVA_SEMESTRAL],
    keywords: ['semestral', 'preventiva semestral'],
    denominator: Math.round(KPI_TOTAL_EQUIP / 6),
  },
  PMOC: {
    ids: [TASK_TYPE_IDS.PMOC],
    keywords: ['pmoc'],
    denominator: KPI_TOTAL_EQUIP,
  },
  CORRETIVA: {
    ids: [TASK_TYPE_IDS.CORRETIVA],
    keywords: ['corretiva'],
  },
};

export function matchesCategory(task, cat) {
  const orientation = (task.orientation || '').toLowerCase();
  const matchId = (cat.ids || []).includes(task.taskType);
  const matchKeyword = (cat.keywords || []).some((k) => orientation.includes(k));
  return matchId || matchKeyword;
}

export function parseEquipIds(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (typeof raw === 'string') {
    const trimmed = raw.trim();
    if (trimmed.startsWith('[')) {
      try {
        const parsed = JSON.parse(trimmed);
        return Array.isArray(parsed) ? parsed : [];
      } catch (_) {
        return trimmed.match(/\d+/g) || [];
      }
    }
    return trimmed.split(',').map((t) => t.trim()).filter(Boolean);
  }
  return [];
}

export function getExcedentEquipments(schools, category, denominator, startDate, endDate) {
  const equipList = [];
  schools.forEach((school) => {
    (school.tasks || []).forEach((task) => {
      const dateRef = task.checkInDate || task.lastUpdate;
      if (!dateRef || !task.taskUrl) return;
      if (!isInPeriod(dateRef, startDate, endDate)) return;
      if (!matchesCategory(task, category)) return;
      const ids = parseEquipIds(task.equipmentsId);
      ids.forEach((id) => {
        equipList.push(`${school.school_info?.description || 'Escola'} - ${id}`);
      });
    });
  });
  if (equipList.length > denominator) {
    return equipList.slice(denominator);
  }
  return [];
}

export function getSchoolPercentual(school, startDate, endDate) {
  if (!school || !school.tasks || school.tasks.length === 0) return 0;

  const relevantTasks = school.tasks.filter(task => {
    const taskDate = task.checkInDate || task.lastUpdate;
    if (!taskDate || !isInPeriod(taskDate, startDate, endDate)) return false;

    // Apenas tarefas de progresso contam para a porcentagem da escola
    return matchesCategory(task, KPI_CATEGORIES.MENSAL) || 
           matchesCategory(task, KPI_CATEGORIES.SEMESTRAL) || 
           matchesCategory(task, KPI_CATEGORIES.PMOC);
  });

  if (relevantTasks.length === 0) return 0;

  const completedTasks = relevantTasks.filter(task => isFinalizada(task.taskStatus));

  return Math.round((completedTasks.length / relevantTasks.length) * 100);
}

export function computeCustomKpis(schools, startDate, endDate) {
  let totalTasks = { MENSAL: 0, SEMESTRAL: 0, PMOC: 0 };
  let completedTasks = { MENSAL: 0, SEMESTRAL: 0, PMOC: 0 };
  let corretivaCount = 0;

  schools.forEach((school) => {
    (school.tasks || []).forEach((task) => {
      const dateRef = task.checkInDate || task.lastUpdate;
      if (!dateRef || !isInPeriod(dateRef, startDate, endDate)) return;

      if (matchesCategory(task, KPI_CATEGORIES.CORRETIVA)) {
        corretivaCount++;
      }

      Object.keys(totalTasks).forEach(key => {
        if(matchesCategory(task, KPI_CATEGORIES[key])) {
          totalTasks[key]++;
          if (isFinalizada(task.taskStatus)) {
            completedTasks[key]++;
          }
        }
      });
    });
  });

  const mensalPct = totalTasks.MENSAL > 0 ? Math.round((completedTasks.MENSAL / totalTasks.MENSAL) * 100) : 0;
  const semestralPct = totalTasks.SEMESTRAL > 0 ? Math.round((completedTasks.SEMESTRAL / totalTasks.SEMESTRAL) * 100) : 0;
  const pmocPct = totalTasks.PMOC > 0 ? Math.round((completedTasks.PMOC / totalTasks.PMOC) * 100) : 0;

  return {
    mensalPct, mensalDone: completedTasks.MENSAL, mensalTotal: totalTasks.MENSAL,
    semestralPct, semestralDone: completedTasks.SEMESTRAL, semestralTotal: totalTasks.SEMESTRAL,
    pmocPct, pmocDone: completedTasks.PMOC, pmocTotal: totalTasks.PMOC,
    corretivaCount
  };
}

export function getSchoolIcons(school, startDate, endDate) {
  const icons = {};
  if (!school || !school.tasks) return icons;

  const tasksInRange = school.tasks.filter(task => {
    const taskDate = task.checkInDate || task.lastUpdate;
    return taskDate && isInPeriod(taskDate, startDate, endDate);
  });

  if (tasksInRange.length === 0) return {};

  Object.keys(specialTaskIconsConfig).forEach(key => {
    const categoryInfo = KPI_CATEGORIES[key];
    if (categoryInfo) {
      const categoryTasks = tasksInRange.filter(task => matchesCategory(task, categoryInfo));
      if (categoryTasks.length > 0) {
        const allCompleted = categoryTasks.every(task => isFinalizada(task.taskStatus));
        icons[key] = allCompleted ? 'completed' : 'present';
      }
    }
  });

  return icons;
}

export function getEquipmentCount(task) {
  if (!task || !task.equipmentsId) return 0;
  return parseEquipIds(task.equipmentsId).length;
}

export function isFinalizada(status) {
  const completedStatus = [5, 6, '5', '6', 'Finalizada', 'Concluído', 'Concluido'];
  return completedStatus.includes(status);
}

export function isValidKpiTask(task) {
  const desc = (task.orientation || '').toLowerCase();
  const validTypes = ['preventiva mensal', 'preventiva semestral'];
  return validTypes.some(type => desc.includes(type));
}

export function getBestTask(tasks) {
  if (!tasks || tasks.length === 0) return null;
  if (tasks.length === 1) return tasks[0];

  const validLinkTasks = tasks.filter(t => t.is_link_valid === 1);
  
  const candidates = validLinkTasks.length > 0 ? validLinkTasks : tasks;

  return candidates.reduce((best, current) => 
    getEquipmentCount(current) > getEquipmentCount(best) ? current : best
  );
}

// Esta função retorna JSX, o que não é ideal em um arquivo de utilitários,
// mas mantém a estrutura que estava sendo refatorada.
// O ideal seria que este fosse um componente React separado.
export const renderCustomKpiCards = (kpiData, openExDialog, mensalItems, semestralItems, pmocItems) => {
  if (!kpiData) return null;

  const { 
    mensalPct, 
    mensalTotal, 
    semestralPct, 
    semestralTotal, 
    pmocPct, 
    pmocTotal, 
    corretivaCount 
  } = kpiData;

  const mensalDone = Math.max(0, mensalTotal - mensalItems.length);
  const semestralDone = Math.max(0, semestralTotal - semestralItems.length);
  const pmocDone = Math.max(0, pmocTotal - pmocItems.length);

  return (
    <Grid container spacing={2} sx={{ mb: 2 }}>
      <Grid item xs={12} sm={6} md={3}>
        <KpiCard 
          title="Preventiva Mensal"
          value={`${mensalPct}%`}
          icon={<EventRepeatIcon />}
          color={getPercentageColor(mensalPct)}
          extra={`${mensalDone}/${mensalTotal} equip.`}
          onClick={() => openExDialog('Equipamentos Excedentes - Mensal', mensalItems)}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <KpiCard 
          title="Preventiva Semestral"
          value={`${semestralPct}%`}
          icon={<CalendarViewWeekIcon />}
          color={getPercentageColor(semestralPct)}
          extra={`${semestralDone}/${semestralTotal} equip.`}
          onClick={() => openExDialog('Equipamentos Excedentes - Semestral', semestralItems)}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <KpiCard 
          title="Levantamento PMOC"
          value={`${pmocPct}%`}
          icon={<ArticleIcon />}
          color={getPercentageColor(pmocPct)}
          extra={`${pmocDone}/${pmocTotal} equip.`}
          onClick={() => openExDialog('Equipamentos Excedentes - PMOC', pmocItems)}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <KpiCard 
          title="Corretivas Abertas"
          value={corretivaCount}
          icon={<BuildIcon />}
          color="error.main"
          extra="Ordens de Serviço"
        />
      </Grid>
    </Grid>
  );
};
