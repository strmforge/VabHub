import type { ReadingMediaType } from '@/types/readingHub';

export type NotificationType =
  | 'MANGA_NEW_CHAPTER'
  | 'MANGA_UPDATED'
  | 'NOVEL_NEW_CHAPTER'
  | 'AUDIOBOOK_NEW_TRACK'
  | 'SYSTEM_MESSAGE'
  | 'TTS_JOB_COMPLETED'
  | 'TTS_JOB_FAILED'
  | 'AUDIOBOOK_READY'
  | 'DOWNLOAD_SUBSCRIPTION_MATCHED'
  | 'DOWNLOAD_TASK_COMPLETED'
  | 'DOWNLOAD_HR_RISK';

export interface UserNotification {
  id: number;
  type: NotificationType;
  media_type?: ReadingMediaType;
  target_id?: number | null;
  sub_target_id?: number | null;

  title: string;
  message?: string | null;
  payload?: Record<string, any> | null;

  is_read: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserNotificationListResponse {
  items: UserNotification[];
  total: number;
  unread_count: number;
}