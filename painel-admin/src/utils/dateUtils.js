/* Utility date-related helper functions extracted from Dashboard.js */

/**
 * Formats an ISO-like date string to Brazilian locale `dd/mm/yyyy hh:mm` or returns fallback text.
 * @param {string|Date} dateString
 */
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    return 'Data inválida';
  }
  return date.toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
};

/**
 * Checks if `dateLike` is between (inclusive) `start` and `end` (both `yyyy-mm-dd` strings).
 */
export const isInPeriod = (dateLike, start, end) => {
  const d = new Date(dateLike);
  if (isNaN(d)) return false;
  return d >= new Date(start) && d <= new Date(end);
};

/**
 * Returns true when `dateLike` belongs to the current month and year.
 */
export const isCurrentMonth = (dateLike) => {
  const date = new Date(dateLike);
  if (isNaN(date)) return false;
  const now = new Date();
  return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
};
