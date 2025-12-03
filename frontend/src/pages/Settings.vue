<template>
  <div class="settings-page">
    <PageHeader
      title="设置"
      subtitle="系统配置和偏好设置"
    />

    <v-container fluid class="pa-4">
      <v-row>
        <!-- 设置分类导航 -->
        <v-col cols="12" md="3">
          <v-card variant="outlined">
            <v-list density="compact" nav>
              <v-list-item
                v-for="category in categories"
                :key="category.value"
                :value="category.value"
                :prepend-icon="category.icon"
                :title="category.title"
                :active="activeCategory === category.value"
                @click="handleCategoryClick(category)"
              />
            </v-list>
          </v-card>
        </v-col>

        <!-- 设置内容 -->
        <v-col cols="12" md="9">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center justify-space-between">
              <span>{{ getCategoryTitle(activeCategory) }}</span>
              <v-btn
                color="primary"
                prepend-icon="mdi-content-save"
                @click="saveSettings"
                :loading="saving"
              >
                保存设置
              </v-btn>
            </v-card-title>

            <v-card-text>
              <div v-if="loading" class="text-center py-12">
                <v-progress-circular indeterminate color="primary" size="64" />
                <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
              </div>

              <!-- 基础设置 -->
              <v-form v-else-if="activeCategory === 'basic'" ref="basicFormRef">
                <v-text-field
                  v-model="settings.system_name"
                  label="系统名称"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-rename-box"
                  class="mb-4"
                />
                <v-select
                  v-model="settings.language"
                  :items="languages"
                  label="语言"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-translate"
                  class="mb-4"
                />
              </v-form>

              <!-- P4-1: 安全策略设置 -->
              <v-form v-else-if="activeCategory === 'safety'" ref="safetyFormRef">
                <div class="text-subtitle-1 font-weight-medium mb-4">全局安全策略</div>
                
                <v-select
                  v-model="safetySettings.mode"
                  :items="safetyModes"
                  label="安全模式"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-shield-check"
                  class="mb-4"
                >
                  <template #item="{ props, item }">
                    <v-list-item v-bind="props">
                      <template #append>
                        <v-chip size="x-small" :color="getSafetyModeColor(item.value)">
                          {{ getSafetyModeDescription(item.value) }}
                        </v-chip>
                      </template>
                    </v-list-item>
                  </template>
                </v-select>

                <v-checkbox
                  v-model="safetySettings.hr_protection_enabled"
                  label="启用HR保护"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-shield-account"
                  class="mb-4"
                />

                <v-text-field
                  v-model.number="safetySettings.min_ratio_for_delete"
                  label="删除最低分享率"
                  type="number"
                  step="0.1"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-chart-line"
                  class="mb-4"
                />

                <v-text-field
                  v-model.number="safetySettings.min_keep_hours"
                  label="最少保种时间（小时）"
                  type="number"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-clock-outline"
                  class="mb-4"
                />

                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">HR移动策略</div>
                
                <v-select
                  v-model="safetySettings.hr_move_strategy"
                  :items="hrMoveStrategies"
                  label="HR文件移动策略"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-file-move"
                  class="mb-4"
                />

                <v-text-field
                  v-model.number="safetySettings.auto_approve_hours"
                  label="自动批准时间（小时）"
                  type="number"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-clock-fast"
                  class="mb-4"
                />
              </v-form>

              <!-- 基础设置 -->
              <v-form v-else-if="activeCategory === 'basic'" ref="basicFormRef">
                <v-select
                  v-model="settings.theme"
                  :items="themes"
                  label="主题"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-palette"
                  class="mb-4"
                />
                <v-text-field
                  v-model="settings.timezone"
                  label="时区"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-clock-outline"
                  class="mb-4"
                />
              </v-form>

              <!-- 下载器设置 -->
              <v-form v-else-if="activeCategory === 'downloader'" ref="downloaderFormRef">
                <v-select
                  v-model="settings.default_downloader"
                  :items="downloaders"
                  label="默认下载器"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-download"
                  class="mb-4"
                />
                <v-text-field
                  v-model="settings.default_save_path"
                  label="默认保存路径"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-folder"
                  class="mb-4"
                />

                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">qBittorrent 设置</div>
                <v-text-field
                  v-model="settings.qbittorrent_host"
                  label="主机地址"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model.number="settings.qbittorrent_port"
                  label="端口"
                  type="number"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model="settings.qbittorrent_username"
                  label="用户名"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model="settings.qbittorrent_password"
                  label="密码"
                  type="password"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />

                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">Transmission 设置</div>
                <v-text-field
                  v-model="settings.transmission_host"
                  label="主机地址"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model.number="settings.transmission_port"
                  label="端口"
                  type="number"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model="settings.transmission_username"
                  label="用户名"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model="settings.transmission_password"
                  label="密码"
                  type="password"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
              </v-form>

              <!-- 全局规则设置 -->
              <div v-else-if="activeCategory === 'global-rules'" class="global-rules-section">
                <div class="text-center py-8">
                  <v-icon size="64" color="primary" class="mb-4">mdi-shield-check</v-icon>
                  <div class="text-h5 font-weight-medium mb-2">全局规则设置</div>
                  <div class="text-body-1 text-medium-emphasis mb-6">
                    统一管理HR策略、质量过滤和文件行为
                  </div>
                  <v-btn
                    color="primary"
                    size="large"
                    prepend-icon="mdi-cog"
                    @click="openGlobalRulesSettings"
                  >
                    打开全局规则设置
                  </v-btn>
                </div>
              </div>

              <!-- 通知设置 -->
              <v-form v-else-if="activeCategory === 'notification'" ref="notificationFormRef">
                <v-switch
                  v-model="settings.notification_enabled"
                  label="启用通知"
                  color="primary"
                  hide-details
                  class="mb-4"
                />
                <v-select
                  v-model="settings.notification_channels"
                  :items="notificationChannels"
                  label="通知渠道"
                  multiple
                  chips
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-bell"
                  class="mb-4"
                />

                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">邮件设置</div>
                <v-text-field
                  v-model="settings.email_smtp_host"
                  label="SMTP服务器"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model.number="settings.email_smtp_port"
                  label="SMTP端口"
                  type="number"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model="settings.email_smtp_user"
                  label="用户名"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model="settings.email_smtp_password"
                  label="密码"
                  type="password"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model="settings.email_to"
                  label="收件人邮箱"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />

                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">Telegram 设置</div>
                <v-text-field
                  v-model="settings.telegram_bot_token"
                  label="Bot Token"
                  type="password"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-text-field
                  v-model="settings.telegram_chat_id"
                  label="Chat ID"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />

                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">微信设置</div>
                <v-text-field
                  v-model="settings.wechat_webhook_url"
                  label="Webhook URL"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
              </v-form>

              <!-- TMDB设置 -->
              <v-form v-else-if="activeCategory === 'tmdb'" ref="tmdbFormRef">
                <v-text-field
                  v-model="settings.tmdb_api_key"
                  label="TMDB API Key"
                  type="password"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-key"
                  hint="在 https://www.themoviedb.org/ 申请API Key"
                  persistent-hint
                  class="mb-4"
                />
                <v-select
                  v-model="settings.tmdb_language"
                  :items="tmdbLanguages"
                  label="语言"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-translate"
                  class="mb-4"
                />
              </v-form>

                     <!-- STRM设置 -->
                     <v-form v-else-if="activeCategory === 'strm'" ref="strmFormRef">
                       <v-switch
                         v-model="strmConfig.enabled"
                         label="启用STRM系统"
                         color="primary"
                         hide-details
                         class="mb-4"
                       />
                       
                       <v-divider class="my-4" />
                       <div class="text-subtitle-1 font-weight-medium mb-4">STRM URL模式设置</div>
                       
                       <!-- STRM URL模式选择 -->
                       <v-radio-group
                         v-model="strmConfig.strm_url_mode"
                         inline
                         class="mb-4"
                       >
                         <v-radio
                           label="直接下载地址（推荐，无需服务器）"
                           value="direct"
                           color="primary"
                         >
                           <template #label>
                             <div>
                               <div class="font-weight-medium">直接下载地址</div>
                               <div class="text-caption text-medium-emphasis">
                                 STRM文件直接包含115网盘下载地址，无需额外配置
                               </div>
                             </div>
                           </template>
                         </v-radio>
                         <v-radio
                           label="本地重定向（自动刷新链接）"
                           value="local_redirect"
                           color="primary"
                         >
                           <template #label>
                             <div>
                               <div class="font-weight-medium">本地重定向</div>
                               <div class="text-caption text-medium-emphasis">
                                 自动刷新过期链接，需要VabHub服务运行
                               </div>
                             </div>
                           </template>
                         </v-radio>
                       </v-radio-group>
                       
                       <!-- Local Redirect模式配置（仅当选择local_redirect时显示） -->
                       <v-card
                         v-if="strmConfig.strm_url_mode === 'local_redirect'"
                         variant="tonal"
                         color="primary"
                         class="mb-4"
                       >
                         <v-card-title class="text-subtitle-1">
                           <v-icon start>mdi-information</v-icon>
                           本地重定向配置（自动检测）
                         </v-card-title>
                         <v-card-text>
                           <div class="mb-2">
                             <v-btn
                               color="primary"
                               prepend-icon="mdi-refresh"
                               @click="detectNetworkInfo"
                               :loading="detectingNetwork"
                               size="small"
                             >
                               自动检测网络信息
                             </v-btn>
                           </div>
                           
                           <v-alert
                             v-if="networkInfo"
                             type="success"
                             variant="tonal"
                             class="mb-3"
                           >
                             <div class="text-body-2">
                               <div><strong>检测到内网IP:</strong> {{ networkInfo.primary_ip }}</div>
                               <div><strong>服务端口:</strong> {{ networkInfo.port }}</div>
                               <div v-if="networkInfo.redirect_url_example" class="mt-2">
                                 <strong>重定向URL示例:</strong>
                                 <code class="text-caption">{{ networkInfo.redirect_url_example }}</code>
                               </div>
                             </div>
                           </v-alert>
                           
                           <v-alert
                             v-else-if="networkInfo === null && !detectingNetwork"
                             type="info"
                             variant="tonal"
                             class="mb-3"
                           >
                             点击"自动检测网络信息"按钮，系统将自动检测内网IP和端口
                           </v-alert>
                           
                           <v-btn
                             v-if="networkInfo"
                             color="success"
                             prepend-icon="mdi-check"
                             @click="applyNetworkInfo"
                             size="small"
                             class="mt-2"
                           >
                             应用检测到的网络信息
                           </v-btn>
                           
                           <v-divider class="my-3" />
                           
                           <div class="text-caption text-medium-emphasis">
                             <div class="mb-1"><strong>说明:</strong></div>
                             <ul class="pl-4">
                               <li>系统会自动检测内网IP和端口，无需手动配置</li>
                               <li>媒体服务器（Emby/Jellyfin/Plex）将通过此地址访问STRM文件</li>
                               <li>确保媒体服务器和VabHub在同一局域网内</li>
                               <li>如果自动检测失败，可以手动输入IP和端口</li>
                             </ul>
                           </div>
                           
                           <!-- 手动配置选项（高级） -->
                           <v-expansion-panels variant="accordion" class="mt-3">
                             <v-expansion-panel>
                               <v-expansion-panel-title>
                                 <v-icon start>mdi-cog</v-icon>
                                 高级配置（手动设置）
                               </v-expansion-panel-title>
                               <v-expansion-panel-text>
                                 <v-text-field
                                   v-model="strmConfig.local_redirect_host"
                                   label="重定向服务器主机"
                                   variant="outlined"
                                   density="compact"
                                   prepend-inner-icon="mdi-server-network"
                                   hint="留空则自动检测内网IP"
                                   persistent-hint
                                   class="mb-3"
                                 />
                                 <v-text-field
                                   v-model.number="strmConfig.local_redirect_port"
                                   label="重定向服务器端口"
                                   type="number"
                                   variant="outlined"
                                   density="compact"
                                   prepend-inner-icon="mdi-network-port"
                                   hint="0表示使用系统配置的端口"
                                   persistent-hint
                                 />
                               </v-expansion-panel-text>
                             </v-expansion-panel>
                           </v-expansion-panels>
                         </v-card-text>
                       </v-card>
                       
                       <v-divider class="my-4" />
                       <div class="text-subtitle-1 font-weight-medium mb-4">媒体库路径设置</div>
                
                <!-- 本地STRM文件存放的媒体库地址 -->
                <v-combobox
                  v-model="strmConfig.media_library_path"
                  :items="mediaLibraryPathOptions"
                  label="本地STRM文件存放的媒体库地址 *"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-folder"
                  hint="本地STRM文件存放的媒体库地址，可通过输入或点击选择按钮选择路径"
                  persistent-hint
                  class="mb-4"
                  clearable
                  required
                >
                  <template #append>
                    <v-btn
                      icon="mdi-folder-open"
                      variant="text"
                      size="small"
                      @click="browseMediaLibraryPath"
                      title="浏览文件夹（输入路径）"
                    />
                  </template>
                </v-combobox>
                
                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">分类路径设置（相对于媒体库路径）</div>
                
                <v-text-field
                  v-model="strmConfig.movie_path"
                  label="电影STRM文件存放路径"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-movie"
                  hint="电影STRM文件存放路径（相对于媒体库路径）"
                  persistent-hint
                  class="mb-4"
                />
                
                <v-text-field
                  v-model="strmConfig.tv_path"
                  label="电视剧STRM文件存放路径"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-television"
                  hint="电视剧STRM文件存放路径（相对于媒体库路径）"
                  persistent-hint
                  class="mb-4"
                />
                
                <v-text-field
                  v-model="strmConfig.anime_path"
                  label="动漫STRM文件存放路径"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-animation"
                  hint="动漫STRM文件存放路径（相对于媒体库路径）"
                  persistent-hint
                  class="mb-4"
                />
                
                <v-text-field
                  v-model="strmConfig.other_path"
                  label="其他类型STRM文件存放路径"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-folder-multiple"
                  hint="其他类型STRM文件存放路径（相对于媒体库路径）"
                  persistent-hint
                  class="mb-4"
                />
                
                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">STRM文件生成设置</div>
                
                <v-switch
                  v-model="strmConfig.generate_nfo"
                  label="生成NFO文件"
                  color="primary"
                  hide-details
                  class="mb-4"
                />
                
                <v-switch
                  v-model="strmConfig.generate_subtitle_files"
                  label="生成字幕文件"
                  color="primary"
                  hide-details
                  class="mb-4"
                />
                
                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">外网访问配置（用于外网播放）</div>
                
                <v-alert
                  type="info"
                  variant="tonal"
                  class="mb-4"
                >
                  <div class="text-body-2">
                    <div class="font-weight-medium mb-2">为什么要填写外网域名和端口？</div>
                    <ul class="pl-4 mb-0">
                      <li>填写外网域名和端口后，系统会自动启用"从115网盘检测字幕"功能</li>
                      <li>外网播放时，字幕将从115网盘实时获取，无需访问本地NAS</li>
                      <li>本地播放时，仍然使用本地字幕文件（快速、可靠）</li>
                      <li>如果不填写外网域名和端口，则只使用本地字幕文件</li>
                    </ul>
                  </div>
                </v-alert>
                
                <v-text-field
                  v-model="strmConfig.external_redirect_host"
                  label="外网访问域名（支持带端口号）"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-web"
                  hint="例如：vabhub.example.com:8096 或 frp.example.com:6000。如果使用默认端口映射（内网8096->外网8096），建议配置为 domain.com:8096，这样Emby客户端只需填写域名即可连接"
                  persistent-hint
                  class="mb-4"
                />
                
                <v-text-field
                  v-model.number="strmConfig.external_redirect_port"
                  label="外网访问端口（可选）"
                  type="number"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-network-port"
                  hint="如果域名中已包含端口号，此配置可留空（填0）。否则建议使用媒体库默认端口（Emby/Jellyfin: 8096, Plex: 32400）或自定义端口"
                  persistent-hint
                  min="0"
                  max="65535"
                  class="mb-4"
                />
                
                <v-switch
                  v-model="strmConfig.use_https"
                  label="外网访问使用HTTPS"
                  color="primary"
                  hide-details
                  class="mb-4"
                />
                
                <v-switch
                  v-model="strmConfig.auto_adapt_network"
                  label="自动适配内外网环境"
                  color="primary"
                  hide-details
                  class="mb-4"
                >
                  <template #label>
                    <div>
                      <div class="font-weight-medium">自动适配内外网环境</div>
                      <div class="text-caption text-medium-emphasis">
                        根据请求来源自动选择内网/外网地址（推荐开启）
                      </div>
                    </div>
                  </template>
                </v-switch>
                
                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">刮削设置</div>
                
                <v-switch
                  v-model="strmConfig.scrape_cloud_files"
                  label="对网盘文件进行刮削"
                  color="primary"
                  hide-details
                  class="mb-4"
                />
                
                <v-switch
                  v-model="strmConfig.scrape_local_strm"
                  label="对本地STRM文件进行刮削"
                  color="primary"
                  hide-details
                  class="mb-4"
                />
                
                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">同步设置</div>
                
                <v-switch
                  v-model="strmConfig.periodic_full_sync"
                  label="定期全量同步"
                  color="primary"
                  hide-details
                  class="mb-4"
                >
                  <template #label>
                    <div>
                      <div class="font-weight-medium">定期全量同步</div>
                      <div class="text-caption text-medium-emphasis">
                        定期检查本地STRM文件是否缺失，自动补全（降低风控风险）
                      </div>
                    </div>
                  </template>
                </v-switch>
                
                <v-text-field
                  v-if="strmConfig.periodic_full_sync"
                  v-model.number="strmConfig.periodic_full_sync_interval_days"
                  label="定期全量同步间隔（天）"
                  type="number"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-calendar-clock"
                  hint="建议3-7天，默认7天（1周）"
                  persistent-hint
                  min="1"
                  max="30"
                  class="mb-4"
                />
                
                <v-text-field
                  v-if="strmConfig.periodic_full_sync"
                  v-model="strmConfig.cloud_media_library_path"
                  label="网盘媒体库路径"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-cloud"
                  hint="只扫描此路径下的文件，不进行全盘扫描，降低风控风险（例如：/115/电影）"
                  persistent-hint
                  class="mb-4"
                />
              </v-form>

              <!-- CookieCloud 设置 -->
              <div v-else-if="activeCategory === 'cookiecloud'" class="cookiecloud-section">
                <CookieCloudSettings />
              </div>

              <!-- Local Intel 设置（Phase 8） -->
              <v-form v-else-if="activeCategory === 'local-intel'" ref="localIntelFormRef">
                <v-alert
                  type="info"
                  variant="tonal"
                  class="mb-4"
                >
                  <div class="text-body-2">
                    <div class="font-weight-medium mb-2">Local Intel 智能监控</div>
                    <p>Local Intel 提供 HR 保护、站点风控和智能事件监控功能，帮助您更好地管理 PT 站点下载任务。</p>
                  </div>
                </v-alert>

                <v-switch
                  v-model="intelSettings.intel_enabled"
                  label="启用 Local Intel"
                  color="primary"
                  hide-details
                  class="mb-4"
                >
                  <template #append>
                    <div class="text-caption text-medium-emphasis">
                      启用后，系统将监控 HR 状态、站点健康状态和智能事件
                    </div>
                  </template>
                </v-switch>

                <v-divider class="my-4" />

                <div class="text-subtitle-1 font-weight-medium mb-4">HR 保护模式</div>
                <v-radio-group
                  v-model="intelSettings.intel_hr_mode"
                  inline
                  class="mb-4"
                >
                  <v-radio
                    label="严格模式"
                    value="strict"
                    color="warning"
                  >
                    <template #label>
                      <div>
                        <div class="font-weight-medium">严格模式</div>
                        <div class="text-caption text-medium-emphasis">
                          更谨慎地判断风险，MOVE 操作更容易被转换为 COPY，更好地保护 HR 种子源文件
                        </div>
                      </div>
                    </template>
                  </v-radio>
                  <v-radio
                    label="宽松模式"
                    value="relaxed"
                    color="success"
                  >
                    <template #label>
                      <div>
                        <div class="font-weight-medium">宽松模式</div>
                        <div class="text-caption text-medium-emphasis">
                          只在非常明确的 HR 风险时才阻止 MOVE，减少对正常下载的影响
                        </div>
                      </div>
                    </template>
                  </v-radio>
                </v-radio-group>

                <v-divider class="my-4" />

                <v-switch
                  v-model="intelSettings.intel_move_check_enabled"
                  label="在 MOVE 前强制执行 HR 检查"
                  color="primary"
                  hide-details
                  class="mb-4"
                >
                  <template #append>
                    <div class="text-caption text-medium-emphasis">
                      启用后，在执行 MOVE 操作前会检查 HR 状态，不安全的操作会自动改为 COPY
                    </div>
                  </template>
                </v-switch>

                <v-divider class="my-4" />

                <v-switch
                  v-model="intelSettings.intel_subscription_respect_site_guard"
                  label="订阅任务尊重站点风控状态"
                  color="primary"
                  hide-details
                  class="mb-4"
                >
                  <template #append>
                    <div class="text-caption text-medium-emphasis">
                      启用后，订阅刷新时会自动跳过被限流站点的订阅，并在选择种子下载时检查 HR 风险并记录提醒
                    </div>
                  </template>
                </v-switch>

                <v-alert
                  type="warning"
                  variant="tonal"
                  class="mb-4"
                >
                  <div class="text-body-2">
                    <div class="font-weight-medium mb-1">注意事项</div>
                    <ul class="pl-4 mb-0">
                      <li>HR 保护功能需要站点配置和数据库支持</li>
                      <li>建议在配置好站点 Cookie 后再启用此功能</li>
                      <li>如果遇到问题，可以暂时禁用此功能</li>
                      <li>订阅任务感知功能会在站点被限流时自动跳过相关订阅，避免触发更严重的风控</li>
                    </ul>
                  </div>
                </v-alert>
              </v-form>

              <!-- 系统设置 -->
              <v-form v-else-if="activeCategory === 'system'" ref="systemFormRef">
                <v-alert
                  type="info"
                  variant="tonal"
                  class="mb-4"
                >
                  <div class="text-body-2">
                    <div class="font-weight-medium mb-2">密钥管理说明</div>
                    <ul class="pl-4 mb-0">
                      <li>系统会在首次启动时自动生成随机密钥</li>
                      <li>所有密钥都存储在 <code>./data/.vabhub_secrets.json</code> 文件中</li>
                      <li>密钥文件权限已设置为仅所有者可读写（Unix系统）</li>
                      <li>支持通过环境变量覆盖密钥值</li>
                      <li>每个安装实例的密钥都是唯一的，确保安全性</li>
                    </ul>
                  </div>
                </v-alert>

                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">系统密钥</div>

                <v-text-field
                  :model-value="apiToken || '未生成'"
                  label="API Token"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-key"
                  readonly
                  hint="用于STRM重定向等功能的API令牌，首次启动时自动生成"
                  persistent-hint
                  class="mb-4"
                >
                  <template #append-inner>
                    <v-btn
                      icon="mdi-content-copy"
                      variant="text"
                      size="small"
                      @click="copyApiToken"
                      :disabled="!apiToken"
                      title="复制API Token"
                    />
                  </template>
                </v-text-field>

                <v-alert
                  type="warning"
                  variant="tonal"
                  class="mb-4"
                >
                  <div class="text-body-2">
                    <div class="font-weight-medium mb-1">安全提示</div>
                    <ul class="pl-4 mb-0">
                      <li>API Token 用于STRM重定向功能，请妥善保管</li>
                      <li>不要将密钥文件提交到Git仓库</li>
                      <li>定期备份密钥文件，避免丢失</li>
                      <li>生产环境建议使用环境变量设置密钥</li>
                    </ul>
                  </div>
                </v-alert>

                <v-divider class="my-4" />
                <div class="text-subtitle-1 font-weight-medium mb-4">密钥文件位置</div>
                <v-text-field
                  model-value="./data/.vabhub_secrets.json"
                  label="密钥文件路径"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-file-lock"
                  readonly
                  hint="密钥文件存储位置（相对于应用根目录）"
                  persistent-hint
                  class="mb-4"
                />
              </v-form>

              <!-- 高级设置 -->
              <v-form v-else-if="activeCategory === 'advanced'" ref="advancedFormRef">
                <v-switch
                  v-model="settings.auto_download"
                  label="自动下载"
                  color="primary"
                  hide-details
                  class="mb-4"
                />
                <v-text-field
                  v-model.number="settings.auto_search_interval"
                  label="自动搜索间隔（秒）"
                  type="number"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-timer"
                  class="mb-4"
                />
                <v-text-field
                  v-model.number="settings.max_concurrent_downloads"
                  label="最大并发下载数"
                  type="number"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-download-multiple"
                  class="mb-4"
                />
                <v-switch
                  v-model="settings.enable_hdr"
                  label="启用HDR支持"
                  color="primary"
                  hide-details
                  class="mb-4"
                />
                <v-switch
                  v-model="settings.enable_hnr_detection"
                  label="启用HNR风险检测"
                  color="primary"
                  hide-details
                  class="mb-4"
                />
              </v-form>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import CookieCloudSettings from '@/components/cookiecloud/CookieCloudSettings.vue'

const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const activeCategory = ref('basic')
const settings = ref<any>({})
const strmConfig = ref<any>({
  enabled: true,
  strm_url_mode: 'local_redirect',  // 默认使用本地重定向模式
  media_library_path: '/media_library',
})
// Local Intel 设置（Phase 8）
const intelSettings = ref({
  intel_enabled: true,
  intel_hr_mode: 'strict',
  intel_move_check_enabled: true,
  intel_subscription_respect_site_guard: true,
})

// P4-1: 安全设置数据
const safetySettings = ref({
  mode: 'SAFE',
  hr_protection_enabled: true,
  min_ratio_for_delete: 1.0,
  min_keep_hours: 72,
  hr_move_strategy: 'copy',
  auto_approve_hours: 24
})

// 安全设置选项
const safetyModes = [
  { title: '安全模式', value: 'SAFE' },
  { title: '平衡模式', value: 'BALANCED' },
  { title: '激进模式', value: 'AGGRESSIVE' }
]

const hrMoveStrategies = [
  { title: '复制移动', value: 'copy' },
  { title: '直接移动', value: 'move' },
  { title: '禁止移动', value: 'deny' }
]

const mediaLibraryPathOptions = ref<string[]>([])
const networkInfo = ref<any>(null)
const detectingNetwork = ref(false)
const apiToken = ref<string>('')

// 安全设置辅助方法
const getSafetyModeColor = (mode: string) => {
  switch (mode) {
    case 'SAFE': return 'success'
    case 'BALANCED': return 'warning'
    case 'AGGRESSIVE': return 'error'
    default: return 'grey'
  }
}

const getSafetyModeDescription = (mode: string) => {
  switch (mode) {
    case 'SAFE': return '最高保护'
    case 'BALANCED': return '平衡保护'
    case 'AGGRESSIVE': return '最低保护'
    default: return '未知'
  }
}

// 处理分类点击
const handleCategoryClick = (category: any) => {
  if (category.external) {
    // 外部页面，使用路由导航
    router.push('/settings/rule-center')
  } else {
    // 内部设置分类
    activeCategory.value = category.value
  }
}

const categories = [
  { value: 'basic', title: '基础设置', icon: 'mdi-cog' },
  { value: 'downloader', title: '下载器设置', icon: 'mdi-download' },
  { value: 'safety', title: '安全策略', icon: 'mdi-shield-check-outline' },
  { value: 'global-rules', title: '全局规则', icon: 'mdi-shield-check' },
  { value: 'rule-center', title: '规则中心', icon: 'mdi-filter-variant', external: true },
  { value: 'notification', title: '通知设置', icon: 'mdi-bell' },
  { value: 'tmdb', title: 'TMDB设置', icon: 'mdi-movie' },
  { value: 'strm', title: 'STRM设置', icon: 'mdi-file-video-outline' },
  { value: 'local-intel', title: 'Local Intel 设置', icon: 'mdi-brain' },
  { value: 'cookiecloud', title: 'CookieCloud设置', icon: 'mdi-cookie' },
  { value: 'system', title: '系统设置', icon: 'mdi-server-security' },
  { value: 'advanced', title: '高级设置', icon: 'mdi-tune' }
]

const languages = [
  { title: '简体中文', value: 'zh-CN' },
  { title: 'English', value: 'en-US' }
]

const themes = [
  { title: '自动', value: 'auto' },
  { title: '浅色', value: 'light' },
  { title: '深色', value: 'dark' }
]

const downloaders = [
  { title: 'qBittorrent', value: 'qBittorrent' },
  { title: 'Transmission', value: 'transmission' }
]

const notificationChannels = [
  { title: '系统', value: 'system' },
  { title: '邮件', value: 'email' },
  { title: 'Telegram', value: 'telegram' },
  { title: '微信', value: 'wechat' },
  { title: 'Webhook', value: 'webhook' },
  { title: '推送', value: 'push' }
]

const tmdbLanguages = [
  { title: '简体中文', value: 'zh-CN' },
  { title: 'English', value: 'en-US' }
]

const getCategoryTitle = (category: string) => {
  const cat = categories.find(c => c.value === category)
  return cat ? cat.title : '设置'
}

const openGlobalRulesSettings = () => {
  router.push('/settings/global-rules')
}

const loadSettings = async () => {
  loading.value = true
  try {
    const response = await api.get('/settings')
    settings.value = response.data || {}
    
    // 加载API Token
    try {
      const tokenResponse = await api.get('/system/api-token')
      if (tokenResponse.data && tokenResponse.data.api_token) {
        apiToken.value = tokenResponse.data.api_token
      }
    } catch (error) {
      console.warn('加载API Token失败:', error)
      apiToken.value = ''
    }
    
           // 加载STRM配置
           try {
             const strmResponse = await api.get('/strm/config')
             if (strmResponse.data) {
               strmConfig.value = { ...strmConfig.value, ...strmResponse.data }
               // 将当前路径添加到选项列表
               if (strmConfig.value.media_library_path && !mediaLibraryPathOptions.value.includes(strmConfig.value.media_library_path)) {
                 mediaLibraryPathOptions.value.push(strmConfig.value.media_library_path)
               }
               
               // 如果选择了local_redirect模式，自动检测网络信息
               if (strmConfig.value.strm_url_mode === 'local_redirect') {
                 await detectNetworkInfo()
               }
             }
           } catch (error) {
             console.warn('加载STRM配置失败:', error)
           }
    
    // 加载 Local Intel 配置（Phase 8）
    try {
      const intelResponse = await api.get('/intel/settings')
      if (intelResponse.data) {
        intelSettings.value = { ...intelSettings.value, ...intelResponse.data }
      }
    } catch (error) {
      console.warn('加载 Local Intel 配置失败:', error)
    }
    
    // 加载常用路径选项（可以从设置中获取）
    if (settings.value.default_save_path) {
      mediaLibraryPathOptions.value.push(settings.value.default_save_path)
    }
    // 添加一些常用路径
    const commonPaths = [
      '/media_library',
      '/mnt/media_library',
      '/volume1/media_library',
      'D:/media_library',
      'E:/media_library'
    ]
    commonPaths.forEach(path => {
      if (!mediaLibraryPathOptions.value.includes(path)) {
        mediaLibraryPathOptions.value.push(path)
      }
    })
    
    // 确保通知渠道是数组
    if (settings.value.notification_channels && typeof settings.value.notification_channels === 'string') {
      try {
        settings.value.notification_channels = JSON.parse(settings.value.notification_channels)
      } catch {
        settings.value.notification_channels = [settings.value.notification_channels]
      }
    }
  } catch (error: any) {
    console.error('加载设置失败:', error)
    // 如果加载失败，尝试初始化默认设置
    try {
      await api.post('/settings/initialize')
      await loadSettings()
    } catch (initError) {
      console.error('初始化设置失败:', initError)
    }
  } finally {
    loading.value = false
  }
}

const browseMediaLibraryPath = () => {
  // 在浏览器中，无法直接打开文件夹选择对话框
  // 这里可以显示一个提示，让用户手动输入路径
  // 或者可以调用后端API来获取可用的路径列表
  // 使用prompt作为替代方案，让用户输入或选择路径
  const currentPath = strmConfig.value.media_library_path || '/media_library'
  const newPath = prompt('请输入或选择本地STRM文件存放的媒体库地址:\n\n提示：可以直接输入路径，或从常用路径中选择', currentPath)
  if (newPath !== null && newPath.trim()) {
    const trimmedPath = newPath.trim()
    strmConfig.value.media_library_path = trimmedPath
    // 如果路径不在选项中，添加到选项列表
    if (!mediaLibraryPathOptions.value.includes(trimmedPath)) {
      mediaLibraryPathOptions.value.push(trimmedPath)
    }
  }
}

// 检测网络信息
const detectNetworkInfo = async () => {
  detectingNetwork.value = true
  try {
    const response = await api.get('/strm/network-info')
    if (response.data) {
      networkInfo.value = response.data
    }
  } catch (error: any) {
    console.error('检测网络信息失败:', error)
    networkInfo.value = null
  } finally {
    detectingNetwork.value = false
  }
}

// 应用检测到的网络信息
const applyNetworkInfo = () => {
  if (networkInfo.value) {
    strmConfig.value.local_redirect_host = networkInfo.value.primary_ip || ''
    strmConfig.value.local_redirect_port = networkInfo.value.port || 0
    alert(`✅ 网络信息已应用！\n\n内网IP: ${networkInfo.value.primary_ip}\n端口: ${networkInfo.value.port}\n\n请点击"保存设置"按钮保存配置。`)
  }
}

// 复制API Token
const copyApiToken = async () => {
  if (!apiToken.value) return
  try {
    await navigator.clipboard.writeText(apiToken.value)
    alert('API Token已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    // 降级方案：使用prompt显示
    prompt('API Token（请手动复制）:', apiToken.value)
  }
}

// 监听STRM URL模式变化
watch(() => strmConfig.value.strm_url_mode, (newMode) => {
  if (newMode === 'local_redirect' && !networkInfo.value) {
    // 切换到local_redirect模式时，自动检测网络信息
    detectNetworkInfo()
  }
})

const saveSettings = async () => {
  saving.value = true
  try {
    // 如果是STRM配置，单独保存
    if (activeCategory.value === 'strm') {
      await api.put('/strm/config', strmConfig.value)
      alert('STRM设置保存成功')
      return
    }
    
    // 如果是 Local Intel 配置，单独保存（Phase 8）
    if (activeCategory.value === 'local-intel') {
      await api.put('/intel/settings', intelSettings.value)
      alert('Local Intel 设置保存成功')
      return
    }
    
    // 系统设置是只读的，不需要保存
    if (activeCategory.value === 'system') {
      alert('系统设置是只读的，无需保存')
      return
    }
    
    // 准备要保存的设置
    const categorySettings: any = {}
    const categoryMap: Record<string, string[]> = {
      basic: ['system_name', 'language', 'theme', 'timezone'],
      downloader: ['default_downloader', 'default_save_path', 'qbittorrent_host', 'qbittorrent_port', 'qbittorrent_username', 'qbittorrent_password', 'transmission_host', 'transmission_port', 'transmission_username', 'transmission_password'],
      notification: ['notification_enabled', 'notification_channels', 'email_smtp_host', 'email_smtp_port', 'email_smtp_user', 'email_smtp_password', 'email_to', 'telegram_bot_token', 'telegram_chat_id', 'wechat_webhook_url'],
      tmdb: ['tmdb_api_key', 'tmdb_language'],
      advanced: ['auto_download', 'auto_search_interval', 'max_concurrent_downloads', 'enable_hdr', 'enable_hnr_detection']
    }

    const keys = categoryMap[activeCategory.value] || []
    for (const key of keys) {
      if (settings.value.hasOwnProperty(key)) {
        categorySettings[key] = settings.value[key]
      }
    }

    await api.post('/settings/batch', {
      settings: categorySettings,
      category: activeCategory.value
    })

    alert('设置保存成功')
  } catch (error: any) {
    console.error('保存设置失败:', error)
    alert('保存失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
}
</style>
