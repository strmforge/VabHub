/**
 * VabHub 路由配置
 * 现代化、美观的WebUI路由
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'HomeDashboard',
      component: () => import('@/pages/HomeDashboard.vue'),
      meta: { requiresAuth: true, title: '首页总览' }
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import(/* webpackChunkName: "login" */ '@/pages/Login.vue'),
      meta: { 
        requiresAuth: false,
        layout: false // 独立页面，不使用布局
      }
    },
    {
      path: '/onboarding',
      name: 'Onboarding',
      component: () => import('@/pages/OnboardingWizard.vue'),
      meta: { 
        requiresAuth: false,
        layout: false // 独立页面，不使用布局
      }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import(/* webpackChunkName: "dashboard" */ '@/pages/Dashboard.vue'),
      meta: { requiresAuth: true, title: '仪表盘' }
    },
    {
      path: '/search',
      name: 'Search',
      component: () => import(/* webpackChunkName: "search" */ '@/pages/Search.vue'),
      meta: { requiresAuth: true, title: '搜索' }
    },
    {
      path: '/subscriptions',
      name: 'Subscriptions',
      redirect: '/subscriptions/movies'
    },
    {
      path: '/subscriptions/movies',
      name: 'MovieSubscriptions',
      component: () => import(/* webpackChunkName: "subscriptions" */ '@/pages/Subscriptions.vue'),
      meta: { requiresAuth: true, title: '电影订阅', mediaType: 'movie' }
    },
    {
      path: '/subscriptions/tv',
      name: 'TvSubscriptions',
      component: () => import(/* webpackChunkName: "subscriptions" */ '@/pages/Subscriptions.vue'),
      meta: { requiresAuth: true, title: '电视剧订阅', mediaType: 'tv' }
    },
    {
      path: '/subscriptions/music',
      name: 'MusicSubscriptions',
      component: () => import(/* webpackChunkName: "subscriptions" */ '@/pages/Subscriptions.vue'),
      meta: { requiresAuth: true, title: '音乐订阅', mediaType: 'music' }
    },
    {
      path: '/subscriptions/books',
      name: 'BookSubscriptions',
      component: () => import(/* webpackChunkName: "subscriptions" */ '@/pages/Subscriptions.vue'),
      meta: { requiresAuth: true, title: '书籍订阅', mediaType: 'book' }
    },
    {
      path: '/rss-subscriptions',
      name: 'RSSSubscriptions',
      component: () => import('@/pages/RSSSubscriptions.vue'),
      meta: { requiresAuth: true, title: 'RSS订阅管理' }
    },
    {
      path: '/rsshub',
      name: 'RSSHub',
      component: () => import('@/pages/RSSHub.vue'),
      meta: { requiresAuth: true, title: 'RSSHub订阅管理' }
    },
    {
      path: '/media-renamer',
      name: 'MediaRenamer',
      component: () => import('@/pages/MediaRenamer.vue'),
      meta: { requiresAuth: true, title: '媒体文件管理' }
    },
    {
      path: '/file-browser',
      name: 'FileBrowser',
      component: () => import('@/pages/FileBrowser.vue'),
      meta: { requiresAuth: true, title: '媒体整理' }
    },
    {
      path: '/transfer-history',
      name: 'TransferHistory',
      component: () => import('@/pages/TransferHistory.vue'),
      meta: { requiresAuth: true, title: '转移历史' }
    },
    {
      path: '/subtitles',
      name: 'Subtitles',
      component: () => import('@/pages/Subtitles.vue'),
      meta: { requiresAuth: true, title: '字幕管理' }
    },
    {
      path: '/downloads',
      name: 'Downloads',
      component: () => import('@/pages/Downloads.vue'),
      meta: { requiresAuth: true, title: '下载管理' }
    },
    {
      path: '/tasks',
      name: 'TaskCenter',
      component: () => import('@/pages/TaskCenterPage.vue'),
      meta: { requiresAuth: true, title: '任务中心' }
    },
    {
      path: '/directory-config',
      name: 'DirectoryConfig',
      component: () => import('@/pages/DirectoryConfig.vue'),
      meta: { requiresAuth: true, title: '目录配置' }
    },
    {
      path: '/category-config',
      name: 'CategoryConfig',
      component: () => import('@/pages/CategoryConfig.vue'),
      meta: { requiresAuth: true, title: '分类配置' }
    },
    {
      path: '/system-update',
      name: 'SystemUpdate',
      component: () => import('@/pages/SystemUpdate.vue'),
      meta: { requiresAuth: true, title: '系统更新' }
    },
    {
      path: '/system-selfcheck',
      name: 'SystemSelfCheck',
      component: () => import('@/pages/SystemSelfCheck.vue'),
      meta: { requiresAuth: true, title: '系统自检' }
    },
    {
      path: '/music',
      name: 'Music',
      component: () => import('@/pages/Music.vue'),
      meta: { requiresAuth: true, title: '音乐管理', badge: 'NEW' }
    },
    {
      path: '/short-drama',
      name: 'ShortDrama',
      component: () => import('@/pages/ShortDrama.vue'),
      meta: { requiresAuth: true, title: '短剧工作台', badge: 'NEW' }
    },
    {
      path: '/graphql-explorer',
      name: 'GraphQLExplorer',
      component: () => import('@/pages/GraphQLExplorer.vue'),
      meta: { requiresAuth: true, title: 'GraphQL 实验室' }
    },
    {
      path: '/recommendations',
      name: 'Recommendations',
      component: () => import('@/pages/Recommendations.vue'),
      meta: { requiresAuth: true, title: 'AI推荐', badge: 'AI' }
    },
    {
      path: '/site-manager',
      name: 'SiteManager',
      component: () => import('@/pages/SiteManager.vue'),
      meta: { requiresAuth: true, title: '站点管理', badge: 'NEW' }
    },
    {
      path: '/media-identification',
      name: 'MediaIdentification',
      component: () => import('@/pages/MediaIdentification.vue'),
      meta: { requiresAuth: true, title: '媒体识别' }
    },
    {
      path: '/hnr',
      name: 'HNRMonitoring',
      component: () => import('@/pages/HNRMonitoring.vue'),
      meta: { requiresAuth: true, title: 'HNR风险检测', badge: 'PRO' }
    },
    {
      path: '/multimodal-monitoring',
      name: 'MultimodalMonitoring',
      component: () => import('@/pages/MultimodalMonitoring.vue'),
      meta: { requiresAuth: true, title: '多模态分析监控', badge: 'AI' }
    },
    {
      path: '/discover',
      name: 'Discover',
      component: () => import('@/pages/Discover.vue'),
      meta: { requiresAuth: true, title: '发现' }
    },
    {
      path: '/calendar',
      name: 'Calendar',
      component: () => import('@/pages/Calendar.vue'),
      meta: { requiresAuth: true, title: '日历' }
    },
    {
      path: '/sites',
      name: 'Sites',
      component: () => import('@/pages/Sites.vue'),
      meta: { requiresAuth: true, title: '站点管理' }
    },
    {
      path: '/workflows',
      name: 'Workflows',
      component: () => import('@/pages/Workflows.vue'),
      meta: { requiresAuth: true, title: '工作流管理' }
    },
    {
      path: '/notifications',
      name: 'Notifications',
      component: () => import('@/pages/Notifications.vue'),
      meta: { requiresAuth: true, title: '通知中心' }
    },
    {
      path: '/log-center',
      name: 'LogCenter',
      component: () => import('@/pages/LogCenter.vue'),
      meta: { requiresAuth: true, title: '实时日志中心' }
    },
    {
      path: '/plugins',
      name: 'Plugins',
      component: () => import('@/pages/Plugins.vue'),
      meta: { requiresAuth: true, title: '插件市场' }
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/pages/Settings.vue'),
      meta: { requiresAuth: true, title: '设置' }
    },
    {
      path: '/settings/global-rules',
      name: 'GlobalRulesSettings',
      component: () => import('@/pages/GlobalRulesSettings.vue'),
      meta: { requiresAuth: true, title: '全局规则设置' }
    },
    {
      path: '/settings/rule-center',
      name: 'RuleCenter',
      component: () => import('@/pages/RuleCenter.vue'),
      meta: { requiresAuth: true, title: '规则中心' }
    },
    {
      path: '/library',
      name: 'Library',
      component: () => import('@/pages/LibraryPreview.vue'),
      meta: { requiresAuth: true, title: '媒体库' }
    },
    {
      path: '/works/:ebookId',
      name: 'WorkDetail',
      component: () => import('@/pages/WorkDetail.vue'),
      meta: { requiresAuth: true, title: '作品详情' }
    },
    {
      path: '/remote/115/play/:workId',
      name: 'Remote115Player',
      component: () => import('@/pages/Remote115Player.vue'),
      meta: { requiresAuth: true, title: '115 在线播放' }
    },
    {
      path: '/player/wall',
      name: 'PlayerWall',
      component: () => import('@/pages/PlayerWall.vue'),
      meta: { requiresAuth: true, title: '电视墙' }
    },
    {
      path: '/dev/manga/sources',
      name: 'MangaSourceAdmin',
      component: () => import('@/pages/dev/MangaSourceAdmin.vue'),
      meta: {
        requiresAuth: true,
        requiresAdmin: true,
        title: '漫画源配置',
        dev: true
      }
    },
    {
      path: '/settings/manga-sources',
      name: 'MangaSourceSettings',
      component: () => import('@/pages/dev/MangaSourceAdmin.vue'),
      meta: {
        requiresAuth: true,
        title: '漫画源配置'
      }
    },
    {
      path: '/manga/remote',
      name: 'MangaRemoteExplorer',
      component: () => import('@/pages/manga/MangaRemoteExplorer.vue'),
      meta: {
        requiresAuth: true,
        title: '远程漫画'
      }
    },
    {
      path: '/manga/source-browser',
      name: 'MangaSourceBrowser',
      component: () => import('@/pages/manga/MangaRemoteExplorer.vue'),
      meta: {
        requiresAuth: true,
        title: '第三方漫画源'
      }
    },
    {
      path: '/manga/library',
      name: 'MangaLibraryPage',
      component: () => import('@/pages/manga/MangaLibraryPage.vue'),
      meta: {
        requiresAuth: true,
        title: '本地漫画库'
      }
    },
    {
      path: '/manga/following',
      name: 'MangaFollowCenter',
      component: () => import('@/pages/manga/MangaFollowCenterPage.vue'),
      meta: {
        requiresAuth: true,
        title: '漫画追更中心'
      }
    },
    {
      path: '/manga/read/:series_id/:chapter_id?',
      name: 'MangaReaderPage',
      component: () => import('@/pages/manga/MangaReaderPage.vue'),
      meta: {
        requiresAuth: true,
        title: '漫画阅读'
      }
    },
    {
      path: '/manga/history',
      name: 'MangaHistoryPage',
      component: () => import('@/pages/manga/MangaHistoryPage.vue'),
      meta: {
        requiresAuth: true,
        title: '漫画阅读历史'
      }
    },
    {
      path: '/reading',
      name: 'ReadingHubPage',
      component: () => import('@/pages/reading/ReadingHubPage.vue'),
      meta: {
        requiresAuth: true,
        title: '阅读中心'
      }
    },
    {
      path: '/reading/favorites',
      name: 'ReadingFavoriteShelf',
      component: () => import('@/pages/reading/ReadingFavoriteShelf.vue'),
      meta: {
        requiresAuth: true,
        title: '我的收藏'
      }
    },
    {
      path: '/novels',
      name: 'NovelCenter',
      component: () => import('@/pages/NovelCenter.vue'),
      meta: { requiresAuth: true, title: '小说中心' }
    },
    {
      path: '/audiobooks',
      name: 'AudiobookCenter',
      component: () => import('@/pages/AudiobookCenter.vue'),
      meta: { requiresAuth: true, title: '有声书中心' }
    },
    {
      path: '/music',
      name: 'MusicCenter',
      component: () => import('@/pages/MusicCenter.vue'),
      meta: { requiresAuth: true, title: '音乐库' }
    },
    {
      path: '/dev/novels/inbox',
      name: 'NovelInboxAdmin',
      component: () => import('@/pages/NovelInboxAdmin.vue'),
      meta: { requiresAuth: true, title: '小说 Inbox 导入日志', dev: true }
    },
    {
      path: '/novels/:ebookId/read',
      name: 'NovelReader',
      component: () => import('@/pages/NovelReader.vue'),
      meta: { requiresAuth: true, title: '小说阅读' }
    },
    {
      path: '/my/shelf',
      name: 'MyShelf',
      component: () => import('@/pages/MyShelf.vue'),
      meta: { requiresAuth: true, title: '我的书架' }
    },
    {
      path: '/dev/novel-import',
      name: 'NovelImportDemo',
      component: () => import('@/pages/NovelImportDemo.vue'),
      meta: { 
        requiresAuth: true, 
        title: '小说 TXT 导入（Dev）',
        dev: true  // 标记为 Dev 功能
      }
    },
    {
      path: '/dev/inbox-preview',
      name: 'InboxPreview',
      component: () => import('@/pages/InboxPreview.vue'),
      meta: { 
        requiresAuth: true, 
        title: '统一收件箱预览（Dev）',
        dev: true  // 标记为 Dev 功能
      }
    },
    {
      path: '/dev/library-settings',
      name: 'DevLibrarySettings',
      component: () => import('@/pages/DevLibrarySettings.vue'),
      meta: { 
        requiresAuth: true, 
        title: '媒体库与 Inbox 设置总览',
        dev: true  // 标记为 Dev 功能
      }
    },
    {
      path: '/dev/tts-settings',
      name: 'DevTTSSettings',
      component: () => import('@/pages/DevTTSSettings.vue'),
      meta: { 
        requiresAuth: true, 
        title: 'TTS 子系统状态',
        dev: true  // 标记为 Dev 功能
      }
    },
    {
      path: '/dev/tts-jobs',
      name: 'DevTTSJobs',
      component: () => import('@/pages/DevTTSJobs.vue'),
      meta: { 
        requiresAuth: true, 
        title: 'TTS 任务管理',
        dev: true  // 标记为 Dev 功能
      }
    },
    {
      path: '/dev/tts-work-batch',
      name: 'DevTTSWorkBatch',
      component: () => import('@/pages/DevTTSWorkBatch.vue'),
      meta: { 
        requiresAuth: true, 
        title: '批量应用 TTS 声线预设',
        dev: true  // 标记为 Dev 功能
      }
    },
    {
      path: '/dev/tts-playground',
      name: 'DevTTSPlayground',
      component: () => import('@/pages/DevTTSPlayground.vue'),
      meta: { 
        requiresAuth: true, 
        title: 'TTS 开发调试操场',
        dev: true  // 标记为 Dev 功能
      }
    },
    {
      path: '/dev/tts-storage',
      name: 'DevTTSStorage',
      component: () => import('@/pages/DevTTSStorage.vue'),
      meta: { 
        requiresAuth: true, 
        title: 'TTS 存储管理 (Dev)',
        dev: true  // 标记为 Dev 功能
      }
    },
    {
      path: '/tts/center',
      name: 'TTSCenter',
      component: () => import('@/pages/TTSCenter.vue'),
      meta: { 
        requiresAuth: true, 
        title: 'TTS 有声书中心'
      }
    },
    {
      path: '/system-settings',
      name: 'SystemSettings',
      component: () => import('@/pages/SystemSettings.vue'),
      meta: { requiresAuth: true, title: '系统设置' }
    },
    {
      path: '/cloud-storage',
      name: 'CloudStorage',
      component: () => import('@/pages/CloudStorage.vue'),
      meta: { requiresAuth: true, title: '云存储管理' }
    },
    {
      path: '/storage-monitor',
      name: 'StorageMonitor',
      component: () => import('@/pages/StorageMonitor.vue'),
      meta: { requiresAuth: true, title: '存储监控' }
    },
    {
      path: '/scheduler-monitor',
      name: 'SchedulerMonitor',
      component: () => import('@/pages/SchedulerMonitor.vue'),
      meta: { requiresAuth: true, title: '调度器状态监控' }
    },
    {
      path: '/local-intel',
      name: 'LocalIntel',
      component: () => import('@/pages/LocalIntel.vue'),
      meta: { requiresAuth: true, title: 'Local Intel 智能监控', badge: 'PRO', devOnly: true }
    },
    {
      path: '/external-indexer',
      name: 'ExternalIndexer',
      component: () => import('@/pages/ExternalIndexer.vue'),
      meta: { requiresAuth: true, title: '外部索引管理', badge: '实验', devOnly: true }
    },
    {
      path: '/media-servers',
      name: 'MediaServers',
      component: () => import('@/pages/MediaServers.vue'),
      meta: { requiresAuth: true, title: '媒体服务器管理' }
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('@/pages/Profile.vue'),
      meta: { requiresAuth: true, title: '个人资料' }
    },
    {
      path: '/user/notifications',
      name: 'UserNotifications',
      component: () => import('@/pages/UserNotifications.vue'),
      meta: { requiresAuth: true, title: '我的通知' }
    },
    {
      path: '/media/:type/:tmdbId',
      name: 'MediaDetail',
      component: () => import(/* webpackChunkName: "media-detail" */ '@/pages/MediaDetail.vue'),
      meta: { requiresAuth: true, title: '媒体详情' }
    },
    {
      path: '/person/:personId',
      name: 'PersonDetail',
      component: () => import(/* webpackChunkName: "person-detail" */ '@/pages/PersonDetail.vue'),
      meta: { requiresAuth: true, title: '人物详情' }
    },
    {
      path: '/admin',
      name: 'AdminDashboard',
      component: () => import('@/pages/admin/AdminDashboard.vue'),
      meta: { requiresAuth: true, title: '系统控制台' }
    },
    {
      path: '/admin/alert-channels',
      name: 'AlertChannelAdmin',
      component: () => import('@/pages/admin/AlertChannelAdmin.vue'),
      meta: { requiresAuth: true, title: '告警渠道管理' }
    },
    {
      path: '/settings/notify-channels',
      name: 'UserNotifyChannels',
      component: () => import('@/pages/settings/UserNotifyChannelsPage.vue'),
      meta: { requiresAuth: true, title: '通知渠道管理' }
    },
    {
      path: '/settings/notify-preferences',
      name: 'UserNotifyPreferences',
      component: () => import('@/pages/settings/UserNotifyPreferencesPage.vue'),
      meta: { requiresAuth: true, title: '通知偏好' }
    },
    {
      path: '/admin/notify-test',
      name: 'NotifyChannelTest',
      component: () => import('@/pages/admin/NotifyChannelTestPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, title: '通知测试' }
    },
    {
      path: '/admin/self-check',
      name: 'SelfCheck',
      component: () => import('@/pages/admin/SelfCheckPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, title: '系统自检' }
    },
    {
      path: '/dev/plugins',
      name: 'PluginDevCenter',
      component: () => import('@/pages/dev/PluginDevCenter.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, title: '插件开发中心' }
    },
    {
      path: '/ai-lab',
      name: 'AiLab',
      component: () => import('@/pages/AiLab.vue'),
      meta: { 
        requiresAuth: true, 
        title: 'AI 实验室',
        badge: 'Beta',
        dev: true  // 标记为实验性功能
      }
    },
    {
      path: '/ai-subs-assistant',
      name: 'AiSubsAssistant',
      component: () => import('@/pages/AiSubsAssistant.vue'),
      meta: { 
        requiresAuth: true, 
        title: 'AI 订阅助手',
        badge: 'Beta',
        dev: true  // 标记为实验性功能
      }
    },
    {
      path: '/ai-log-doctor',
      name: 'AiLogDoctor',
      component: () => import('@/pages/AiLogDoctor.vue'),
      meta: { 
        requiresAuth: true, 
        title: 'AI 故障医生',
        badge: 'Beta',
        dev: true  // 标记为实验性功能
      }
    },
    {
      path: '/ai-cleanup-advisor',
      name: 'AiCleanupAdvisor',
      component: () => import('@/pages/AiCleanupAdvisor.vue'),
      meta: { 
        requiresAuth: true, 
        title: 'AI 整理顾问',
        badge: 'Beta',
        dev: true  // 标记为实验性功能
      }
    },
    {
      path: '/ai-reading-assistant',
      name: 'AiReadingAssistant',
      component: () => import('@/pages/AiReadingAssistant.vue'),
      meta: { 
        requiresAuth: true, 
        title: 'AI 阅读助手',
        badge: 'Beta',
        dev: true  // 标记为实验性功能
      }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/pages/NotFound.vue')
    }
  ]
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router

