import { format, formatDistanceToNow } from 'date-fns';

export const formatDate = (date: string | Date, formatStr: string = 'PPP') => {
  return format(new Date(date), formatStr);
};

export const formatRelativeTime = (date: string | Date) => {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
};