import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

export function formatRelativeTime(date: string | undefined) {
  if (!date) return null;
  const timeStr = dayjs(date).fromNow();
  return timeStr
    .replace('a second ago', 'just now')
    .replace('a few seconds ago', 'just now')
    .replace('a minute', '1m')
    .replace(' minutes', 'm')
    .replace(' minute', 'm')
    .replace('an hour', '1h')
    .replace(' hours', 'h')
    .replace(' hour', 'h')
    .replace('a day', '1d')
    .replace(' days', 'd')
    .replace(' day', 'd')
    .replace('a month', '1mo')
    .replace(' months', 'mo')
    .replace(' month', 'mo')
    .replace('a year', '1y')
    .replace(' years', 'y')
    .replace(' year', 'y');
}

export function formatDateTime(date: string | undefined) {
  if (!date) return null;
  return dayjs(date).format('h:mma MMMM D, YYYY');
}
