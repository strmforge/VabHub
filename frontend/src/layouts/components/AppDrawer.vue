<template>
  <v-navigation-drawer
    v-model="drawer"
    :permanent="$vuetify.display.mdAndUp"
    :temporary="$vuetify.display.smAndDown"
    color="surface"
    class="app-drawer"
  >
    <!-- Logo区域 -->
    <div class="pa-4 text-center">
      <router-link to="/" class="text-decoration-none">
        <VabHubLogo :size="48" :show-text="true" :glow="true" variant="dark" />
      </router-link>
    </div>
    
    <v-divider />
    
    <!-- 导航菜单 -->
    <v-list nav density="comfortable">
      
      <!-- ========== 影视中心 ========== -->
      <v-list-subheader>
        <v-icon size="small" class="mr-1">mdi-television-play</v-icon>
        影视中心
      </v-list-subheader>
      
      <v-list-item
        prepend-icon="mdi-home"
        title="首页总览"
        value="home-dashboard"
        :to="{ name: 'HomeDashboard' }"
        :active="$route.name === 'HomeDashboard'"
      />
      
      <v-list-item
        prepend-icon="mdi-television-play"
        title="电视墙"
        value="player-wall"
        :to="{ name: 'PlayerWall' }"
        :active="$route.name === 'PlayerWall'"
      />
      
      <v-list-item
        prepend-icon="mdi-filmstrip-box-multiple"
        title="媒体库"
        value="library"
        :to="{ name: 'Library' }"
        :active="$route.name === 'Library'"
      />
      
      <v-list-item
        prepend-icon="mdi-compass"
        title="发现"
        value="discover"
        :to="{ name: 'Discover' }"
        :active="$route.name === 'Discover'"
      />
      
      <v-list-item
        prepend-icon="mdi-calendar"
        title="日历"
        value="calendar"
        :to="{ name: 'Calendar' }"
        :active="$route.name === 'Calendar'"
      />
      
      <v-list-item
        prepend-icon="mdi-drama-masks"
        title="短剧工作台"
        value="short-drama"
        :to="{ name: 'ShortDrama' }"
        :active="$route.name === 'ShortDrama'"
      />
      
      <!-- ========== 下载 & 订阅 ========== -->
      <v-divider class="my-2" />
      <v-list-subheader>
        <v-icon size="small" class="mr-1">mdi-download</v-icon>
        下载 & 订阅
      </v-list-subheader>
      
      <v-list-item
        prepend-icon="mdi-magnify"
        title="搜索"
        value="search"
        :to="{ name: 'Search' }"
        :active="$route.name === 'Search'"
      />
      
      <v-list-item
        prepend-icon="mdi-download"
        title="下载管理"
        value="downloads"
        :to="{ name: 'Downloads' }"
        :active="$route.name === 'Downloads'"
      />
      
      <v-list-group value="subscriptions">
        <template #activator="{ props }">
          <v-list-item
            v-bind="props"
            prepend-icon="mdi-bookmark-multiple"
            title="订阅管理"
          />
        </template>
        <v-list-item
          title="电影订阅"
          prepend-icon="mdi-movie-open"
          :to="{ name: 'MovieSubscriptions' }"
          :active="$route.name === 'MovieSubscriptions'"
        />
        <v-list-item
          title="电视剧订阅"
          prepend-icon="mdi-television-classic"
          :to="{ name: 'TvSubscriptions' }"
          :active="$route.name === 'TvSubscriptions'"
        />
        <v-list-item
          title="音乐订阅"
          prepend-icon="mdi-music"
          :to="{ name: 'MusicSubscriptions' }"
          :active="$route.name === 'MusicSubscriptions'"
        />
        <v-list-item
          title="书籍订阅"
          prepend-icon="mdi-book-open-page-variant"
          :to="{ name: 'BookSubscriptions' }"
          :active="$route.name === 'BookSubscriptions'"
        />
      </v-list-group>
      
      <v-list-item
        prepend-icon="mdi-rss"
        title="RSS订阅"
        value="rss-subscriptions"
        :to="{ name: 'RSSSubscriptions' }"
        :active="$route.name === 'RSSSubscriptions'"
      />
      
      <v-list-item
        prepend-icon="mdi-rss-box"
        title="RSSHub订阅"
        value="rsshub"
        :to="{ name: 'RSSHub' }"
        :active="$route.name === 'RSSHub'"
      />
      
      <v-list-item
        prepend-icon="mdi-workflow"
        title="工作流管理"
        value="workflows"
        :to="{ name: 'Workflows' }"
        :active="$route.name === 'Workflows'"
      />
      
      <!-- ========== 阅读 & 听书 ========== -->
      <v-divider class="my-2" />
      <v-list-subheader>
        <v-icon size="small" class="mr-1">mdi-book-open-variant</v-icon>
        阅读 & 听书
      </v-list-subheader>
      
      <v-list-item
        prepend-icon="mdi-book-open-variant"
        title="阅读中心"
        value="reading-hub"
        :to="{ name: 'ReadingHubPage' }"
        :active="$route.name === 'ReadingHubPage'"
      />
      
      <v-list-item
        prepend-icon="mdi-bookshelf"
        title="我的书架"
        value="my-shelf"
        :to="{ name: 'MyShelf' }"
        :active="$route.name === 'MyShelf'"
      />
      
      <v-list-item
        prepend-icon="mdi-heart"
        title="我的收藏"
        value="reading-favorites"
        :to="{ name: 'ReadingFavoriteShelf' }"
        :active="$route.name === 'ReadingFavoriteShelf'"
      />
      
      <v-list-item
        prepend-icon="mdi-book-open-page-variant"
        title="小说中心"
        value="novel-center"
        :to="{ name: 'NovelCenter' }"
        :active="$route.name === 'NovelCenter'"
      />
      
      <v-list-item
        prepend-icon="mdi-headphones"
        title="有声书中心"
        value="audiobook-center"
        :to="{ name: 'AudiobookCenter' }"
        :active="$route.name === 'AudiobookCenter'"
      />
      
      <v-list-item
        prepend-icon="mdi-text-to-speech"
        title="TTS 有声书"
        value="tts-center"
        :to="{ name: 'TTSCenter' }"
        :active="$route.name === 'TTSCenter'"
      />
      
      <!-- ========== 漫画中心 ========== -->
      <v-divider class="my-2" />
      <v-list-subheader>
        <v-icon size="small" class="mr-1">mdi-book-open-page-variant</v-icon>
        漫画中心
      </v-list-subheader>
      
      <v-list-item
        prepend-icon="mdi-bookshelf"
        title="本地漫画库"
        value="manga-library"
        :to="{ name: 'MangaLibraryPage' }"
        :active="$route.name === 'MangaLibraryPage'"
      />
      
      <v-list-item
        prepend-icon="mdi-bell-ring"
        title="漫画追更中心"
        value="manga-follow-center"
        :to="{ name: 'MangaFollowCenter' }"
        :active="$route.name === 'MangaFollowCenter'"
      />
      
      <v-list-item
        prepend-icon="mdi-cloud-search"
        title="远程漫画"
        value="manga-remote"
        :to="{ name: 'MangaRemoteExplorer' }"
        :active="$route.name === 'MangaRemoteExplorer'"
      />
      
      <v-list-item
        prepend-icon="mdi-web"
        title="第三方漫画源"
        value="manga-source-browser"
        :to="{ name: 'MangaSourceBrowser' }"
        :active="$route.name === 'MangaSourceBrowser'"
      />
      
      <v-list-item
        prepend-icon="mdi-history"
        title="阅读历史"
        value="manga-history"
        :to="{ name: 'MangaHistoryPage' }"
        :active="$route.name === 'MangaHistoryPage'"
      />
      
      <!-- ========== 音乐中心 ========== -->
      <v-divider class="my-2" />
      <v-list-subheader>
        <v-icon size="small" class="mr-1">mdi-music</v-icon>
        音乐中心
      </v-list-subheader>
      
      <v-list-item
        prepend-icon="mdi-music-box-multiple"
        title="音乐库"
        value="music-center"
        :to="{ name: 'MusicCenter' }"
        :active="$route.name === 'MusicCenter'"
      />
      
      <!-- ========== AI 中心 ========== -->
      <v-divider class="my-2" />
      <v-list-subheader>
        <v-icon size="small" class="mr-1">mdi-robot</v-icon>
        <span class="text-primary">AI 中心</span>
      </v-list-subheader>
      
      <v-list-item
        prepend-icon="mdi-flask"
        title="AI 实验室"
        value="ai-lab"
        :to="{ name: 'AiLab' }"
        :active="$route.name === 'AiLab'"
      >
        <template #append>
          <v-chip size="x-small" color="info" variant="flat">Beta</v-chip>
        </template>
      </v-list-item>
      
      <v-list-item
        prepend-icon="mdi-bookmark-plus"
        title="AI 订阅助手"
        value="ai-subs-assistant"
        :to="{ name: 'AiSubsAssistant' }"
        :active="$route.name === 'AiSubsAssistant'"
      >
        <template #append>
          <v-chip size="x-small" color="info" variant="flat">Beta</v-chip>
        </template>
      </v-list-item>
      
      <v-list-item
        prepend-icon="mdi-stethoscope"
        title="AI 故障医生"
        value="ai-log-doctor"
        :to="{ name: 'AiLogDoctor' }"
        :active="$route.name === 'AiLogDoctor'"
      >
        <template #append>
          <v-chip size="x-small" color="info" variant="flat">Beta</v-chip>
        </template>
      </v-list-item>
      
      <v-list-item
        prepend-icon="mdi-broom"
        title="AI 整理顾问"
        value="ai-cleanup-advisor"
        :to="{ name: 'AiCleanupAdvisor' }"
        :active="$route.name === 'AiCleanupAdvisor'"
      >
        <template #append>
          <v-chip size="x-small" color="info" variant="flat">Beta</v-chip>
        </template>
      </v-list-item>
      
      <v-list-item
        prepend-icon="mdi-book-clock"
        title="AI 阅读助手"
        value="ai-reading-assistant"
        :to="{ name: 'AiReadingAssistant' }"
        :active="$route.name === 'AiReadingAssistant'"
      >
        <template #append>
          <v-chip size="x-small" color="info" variant="flat">Beta</v-chip>
        </template>
      </v-list-item>
      
      <v-list-item
        prepend-icon="mdi-lightbulb-on"
        title="AI 推荐"
        value="recommendations"
        :to="{ name: 'Recommendations' }"
        :active="$route.name === 'Recommendations'"
      />
      
      <!-- ========== 站点 & 插件 ========== -->
      <v-divider class="my-2" />
      <v-list-subheader>
        <v-icon size="small" class="mr-1">mdi-server</v-icon>
        站点 & 插件
      </v-list-subheader>
      
      <v-list-item
        prepend-icon="mdi-server"
        title="站点管理"
        value="site-manager"
        :to="{ name: 'SiteManager' }"
        :active="$route.name === 'SiteManager'"
      />
      
      <v-list-item
        prepend-icon="mdi-shield-alert"
        title="HNR 风险检测"
        value="hnr"
        :to="{ name: 'HNRMonitoring' }"
        :active="$route.name === 'HNRMonitoring'"
      >
        <template #append>
          <v-chip size="x-small" color="warning" variant="flat">PRO</v-chip>
        </template>
      </v-list-item>
      
      <v-list-item
        prepend-icon="mdi-puzzle"
        title="插件市场"
        value="plugins"
        :to="{ name: 'Plugins' }"
        :active="$route.name === 'Plugins'"
      />
      
      <template v-if="isDevMode()">
        <v-list-item
          prepend-icon="mdi-brain"
          title="Local Intel"
          value="local-intel"
          :to="{ name: 'LocalIntel' }"
          :active="$route.name === 'LocalIntel'"
        >
          <template #append>
            <v-chip size="x-small" color="warning" variant="flat">PRO</v-chip>
          </template>
        </v-list-item>
        
        <v-list-item
          prepend-icon="mdi-bridge"
          title="外部索引"
          value="external-indexer"
          :to="{ name: 'ExternalIndexer' }"
          :active="$route.name === 'ExternalIndexer'"
        >
          <template #append>
            <v-chip size="x-small" color="purple" variant="flat">实验</v-chip>
          </template>
        </v-list-item>
      </template>
      
      <!-- ========== 系统 & 设置 ========== -->
      <v-divider class="my-2" />
      <v-list-subheader>
        <v-icon size="small" class="mr-1">mdi-cog</v-icon>
        系统 & 设置
      </v-list-subheader>
      
      <v-list-item
        prepend-icon="mdi-cog"
        title="系统设置"
        value="settings"
        :to="{ name: 'Settings' }"
        :active="$route.name === 'Settings'"
      />
      
      <v-list-item
        prepend-icon="mdi-bell"
        title="通知中心"
        value="notifications"
        :to="{ name: 'Notifications' }"
        :active="$route.name === 'Notifications'"
      />
      
      <v-list-item
        prepend-icon="mdi-progress-clock"
        title="任务中心"
        value="task-center"
        :to="{ name: 'TaskCenter' }"
        :active="$route.name === 'TaskCenter'"
      />
      
      <v-list-item
        prepend-icon="mdi-console-line"
        title="实时日志"
        value="log-center"
        :to="{ name: 'LogCenter' }"
        :active="$route.name === 'LogCenter'"
      />
      
      <v-list-item
        prepend-icon="mdi-harddisk"
        title="存储监控"
        value="storage-monitor"
        :to="{ name: 'StorageMonitor' }"
        :active="$route.name === 'StorageMonitor'"
      />
      
      <v-list-item
        prepend-icon="mdi-clock-outline"
        title="调度器监控"
        value="scheduler-monitor"
        :to="{ name: 'SchedulerMonitor' }"
        :active="$route.name === 'SchedulerMonitor'"
      />
      
      <v-list-item
        prepend-icon="mdi-stethoscope"
        title="系统自检"
        value="system-selfcheck"
        :to="{ name: 'SystemSelfCheck' }"
        :active="$route.name === 'SystemSelfCheck'"
      />
      
      <v-list-item
        prepend-icon="mdi-cloud"
        title="云存储管理"
        value="cloud-storage"
        :to="{ name: 'CloudStorage' }"
        :active="$route.name === 'CloudStorage'"
      />
      
      <v-list-item
        prepend-icon="mdi-server"
        title="媒体服务器"
        value="media-servers"
        :to="{ name: 'MediaServers' }"
        :active="$route.name === 'MediaServers'"
      />
      
      <v-list-item
        prepend-icon="mdi-console"
        title="系统控制台"
        value="admin-dashboard"
        :to="{ name: 'AdminDashboard' }"
        :active="$route.name === 'AdminDashboard'"
      />
      
      <!-- ========== 开发工具（仅 Dev 模式） ========== -->
      <template v-if="isDevMode()">
        <v-divider class="my-2" />
        <v-list-subheader>
          <v-icon size="small" class="mr-1">mdi-code-braces</v-icon>
          <span class="text-warning">开发工具</span>
        </v-list-subheader>
        
        <v-list-item
          prepend-icon="mdi-graphql"
          title="GraphQL 实验室"
          value="graphql-explorer"
          :to="{ name: 'GraphQLExplorer' }"
          :active="$route.name === 'GraphQLExplorer'"
        />
        
        <v-list-item
          prepend-icon="mdi-notebook-edit"
          title="小说 Inbox 日志"
          value="novel-inbox-admin"
          :to="{ name: 'NovelInboxAdmin' }"
          :active="$route.name === 'NovelInboxAdmin'"
        />
        
        <v-list-item
          prepend-icon="mdi-book-cog"
          title="漫画源配置"
          value="manga-source-admin"
          :to="{ name: 'MangaSourceAdmin' }"
          :active="$route.name === 'MangaSourceAdmin'"
        />
        
        <v-list-item
          prepend-icon="mdi-folder-cog"
          title="目录配置"
          value="directory-config"
          :to="{ name: 'DirectoryConfig' }"
          :active="$route.name === 'DirectoryConfig'"
        />
        
        <v-list-item
          prepend-icon="mdi-file-movie"
          title="媒体文件管理"
          value="media-renamer"
          :to="{ name: 'MediaRenamer' }"
          :active="$route.name === 'MediaRenamer'"
        />
        
        <v-list-item
          prepend-icon="mdi-folder-move"
          title="媒体整理"
          value="file-browser"
          :to="{ name: 'FileBrowser' }"
          :active="$route.name === 'FileBrowser'"
        />
        
        <v-list-item
          prepend-icon="mdi-history"
          title="转移历史"
          value="transfer-history"
          :to="{ name: 'TransferHistory' }"
          :active="$route.name === 'TransferHistory'"
        />
        
        <v-list-item
          prepend-icon="mdi-subtitles"
          title="字幕管理"
          value="subtitles"
          :to="{ name: 'Subtitles' }"
          :active="$route.name === 'Subtitles'"
        />
      </template>
      
    </v-list>
    
    <!-- 底部：系统状态 -->
    <template v-slot:append>
      <div class="pa-2">
        <v-card variant="flat" color="surface-variant" class="pa-2">
          <div class="d-flex align-center mb-2">
            <v-icon size="small" color="success" class="mr-2">mdi-circle</v-icon>
            <span class="text-caption">系统运行正常</span>
          </div>
          <div class="text-caption text-medium-emphasis">
            v{{ appVersion }}
          </div>
        </v-card>
      </div>
    </template>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import VabHubLogo from '@/components/common/VabHubLogo.vue'
import { isDevMode } from '@/utils/devMode'

const appStore = useAppStore()

const drawer = computed({
  get: () => appStore.drawer,
  set: (value) => appStore.setDrawer(value)
})

const appVersion = '1.0.0'
</script>

<style lang="scss" scoped>
.app-drawer {
  border-right: 1px solid rgba(var(--v-border-color), 0.12);
}

:deep(.v-list-item--active) {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  
  .v-icon {
    color: rgb(var(--v-theme-primary));
  }
}
</style>

