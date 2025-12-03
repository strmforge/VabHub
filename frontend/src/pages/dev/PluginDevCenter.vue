<template>
  <v-container fluid class="pa-4">
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-icon size="32" class="mr-3" color="primary">mdi-puzzle-outline</v-icon>
          <div>
            <h1 class="text-h4">插件开发中心</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">
              管理已安装的插件，执行 Workflow 扩展
            </p>
          </div>
          <v-spacer />
          <v-btn
            color="primary"
            :loading="scanning"
            @click="scanPlugins"
          >
            <v-icon class="mr-2">mdi-folder-search</v-icon>
            扫描插件目录
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Tabs（PLUGIN-HUB-4 MP 风格） -->
    <v-row>
      <v-col cols="12">
        <v-tabs v-model="activeTab" color="primary">
          <v-tab value="my-plugins">
            <v-icon class="mr-2">mdi-puzzle</v-icon>
            我的插件
            <v-chip size="x-small" class="ml-2" v-if="myPlugins.length">{{ myPlugins.length }}</v-chip>
            <v-chip size="x-small" class="ml-1" color="warning" v-if="updatableCount > 0">
              {{ updatableCount }} 可更新
            </v-chip>
          </v-tab>
          <v-tab value="market">
            <v-icon class="mr-2">mdi-store</v-icon>
            插件市场
            <v-chip size="x-small" class="ml-2" color="info" v-if="marketPlugins.length">{{ marketPlugins.length }}</v-chip>
          </v-tab>
          <v-tab value="plugins">
            <v-icon class="mr-2">mdi-cog</v-icon>
            本地管理
            <v-chip size="x-small" class="ml-2" v-if="plugins.length">{{ plugins.length }}</v-chip>
          </v-tab>
          <v-tab value="workflows">
            <v-icon class="mr-2">mdi-cog-play</v-icon>
            Workflows
            <v-chip size="x-small" class="ml-2" v-if="workflows.length">{{ workflows.length }}</v-chip>
          </v-tab>
          <v-tab value="panels">
            <v-icon class="mr-2">mdi-view-dashboard</v-icon>
            面板预览
          </v-tab>
        </v-tabs>
      </v-col>
    </v-row>

    <!-- Tab Content -->
    <v-row class="mt-2">
      <v-col cols="12">
        <v-window v-model="activeTab">
          <!-- 我的插件（PLUGIN-HUB-4） -->
          <v-window-item value="my-plugins">
            <v-card>
              <v-card-title class="d-flex align-center flex-wrap">
                <v-icon class="mr-2" color="primary">mdi-puzzle</v-icon>
                我的插件
                <v-chip size="small" class="ml-2" v-if="myPlugins.length">
                  已安装 {{ myPlugins.length }} 个
                </v-chip>
                <v-chip size="small" class="ml-2" color="warning" v-if="updatableCount > 0">
                  {{ updatableCount }} 个可更新
                </v-chip>
                <v-spacer />
                
                <!-- 只看可更新 -->
                <v-switch
                  v-model="showUpdatableOnly"
                  hide-details
                  density="compact"
                  color="warning"
                  class="mr-4"
                >
                  <template #label>
                    <span class="text-body-2">只看可更新</span>
                  </template>
                </v-switch>
                
                <v-btn
                  variant="tonal"
                  size="small"
                  :loading="loadingMyPlugins"
                  @click="loadMyPlugins(true)"
                >
                  <v-icon class="mr-1">mdi-refresh</v-icon>
                  刷新
                </v-btn>
              </v-card-title>

              <v-divider />

              <!-- 加载状态 -->
              <v-card-text v-if="loadingMyPlugins" class="pa-8 text-center">
                <v-progress-circular indeterminate color="primary" />
                <div class="mt-4">加载中...</div>
              </v-card-text>

              <!-- 空状态 -->
              <v-card-text v-else-if="filteredMyPlugins.length === 0" class="pa-8 text-center">
                <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-puzzle-outline</v-icon>
                <div class="text-h6 text-medium-emphasis mb-2">
                  {{ showUpdatableOnly ? '暂无可更新的插件' : '暂无已安装插件' }}
                </div>
                <div class="text-body-2 text-medium-emphasis">
                  前往「插件市场」安装插件
                </div>
              </v-card-text>

              <!-- 插件卡片列表 -->
              <v-card-text v-else class="pa-4">
                <v-row>
                  <v-col
                    v-for="plugin in filteredMyPlugins"
                    :key="plugin.id"
                    cols="12"
                    md="6"
                    lg="4"
                  >
                    <v-card variant="outlined" class="h-100 plugin-card">
                      <!-- NEW 角标 -->
                      <v-chip
                        v-if="plugin.has_update"
                        size="x-small"
                        color="warning"
                        class="new-badge"
                      >
                        NEW
                      </v-chip>
                      
                      <v-card-title class="d-flex align-center text-subtitle-1">
                        <!-- 状态点 -->
                        <v-icon
                          :color="plugin.enabled ? 'success' : 'grey'"
                          size="x-small"
                          class="mr-2"
                        >
                          mdi-circle
                        </v-icon>
                        
                        <!-- 频道标签 -->
                        <v-chip
                          :color="getChannelColor(plugin.channel)"
                          size="x-small"
                          variant="flat"
                          class="mr-2"
                        >
                          {{ getChannelLabel(plugin.channel) }}
                        </v-chip>
                        
                        <span class="text-truncate">{{ plugin.name }}</span>
                        <v-spacer />
                        
                        <!-- 三点菜单 -->
                        <v-menu>
                          <template #activator="{ props }">
                            <v-btn icon size="small" variant="text" v-bind="props">
                              <v-icon>mdi-dots-vertical</v-icon>
                            </v-btn>
                          </template>
                          <v-list density="compact">
                            <v-list-item
                              v-if="plugin.has_update"
                              @click="confirmUpdate(plugin)"
                              :disabled="operatingPluginId === plugin.id"
                            >
                              <template #prepend>
                                <v-icon color="warning">mdi-update</v-icon>
                              </template>
                              <v-list-item-title>更新</v-list-item-title>
                            </v-list-item>
                            <v-list-item @click="confirmUninstall(plugin)" :disabled="operatingPluginId === plugin.id">
                              <template #prepend>
                                <v-icon color="error">mdi-delete</v-icon>
                              </template>
                              <v-list-item-title>卸载</v-list-item-title>
                            </v-list-item>
                            <v-divider v-if="plugin.author_url" />
                            <v-list-item v-if="plugin.author_url" :href="plugin.author_url" target="_blank">
                              <template #prepend>
                                <v-icon>mdi-open-in-new</v-icon>
                              </template>
                              <v-list-item-title>作者主页</v-list-item-title>
                            </v-list-item>
                          </v-list>
                        </v-menu>
                      </v-card-title>

                      <v-card-subtitle class="pb-0 d-flex align-center flex-wrap">
                        <span class="text-caption">v{{ plugin.local_version || plugin.version || '未知' }}</span>
                        <span v-if="plugin.hub_name" class="text-caption ml-2">
                          · {{ plugin.hub_name }}
                        </span>
                        <span v-if="plugin.author_name || plugin.author" class="text-caption ml-2">
                          · {{ plugin.author_name || plugin.author }}
                        </span>
                      </v-card-subtitle>

                      <v-card-text class="py-2">
                        <div class="text-body-2 text-medium-emphasis line-clamp-2" style="min-height: 40px;">
                          {{ plugin.description || '暂无描述' }}
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- 插件市场（PLUGIN-HUB-4） -->
          <v-window-item value="market">
            <v-card>
              <v-card-title class="d-flex align-center flex-wrap">
                <v-icon class="mr-2" color="info">mdi-store</v-icon>
                插件市场
                <v-chip size="small" class="ml-2" color="info" v-if="marketPlugins.length">
                  {{ marketPlugins.length }} 个可安装
                </v-chip>
                <v-spacer />
                
                <!-- 社区插件开关 -->
                <v-switch
                  v-model="showCommunityPlugins"
                  hide-details
                  density="compact"
                  color="orange"
                  class="mr-4"
                  @update:model-value="loadMarketPlugins()"
                >
                  <template #label>
                    <span class="text-body-2">
                      <v-icon size="small" color="orange" class="mr-1">mdi-account-group</v-icon>
                      社区插件
                    </span>
                  </template>
                </v-switch>
                
                <!-- 插件源设置按钮 -->
                <v-btn
                  variant="tonal"
                  size="small"
                  class="mr-2"
                  @click="openHubSettingsDialog"
                >
                  <v-icon class="mr-1">mdi-cog</v-icon>
                  插件源
                </v-btn>
                
                <v-btn
                  variant="tonal"
                  size="small"
                  :loading="loadingMarket"
                  @click="loadMarketPlugins(true)"
                >
                  <v-icon class="mr-1">mdi-refresh</v-icon>
                  刷新
                </v-btn>
              </v-card-title>

              <!-- 频道说明 -->
              <v-alert type="info" variant="tonal" density="compact" class="mx-4 mt-2 mb-0">
                <template #text>
                  <v-icon size="small" color="primary" class="mr-1">mdi-shield-check</v-icon>
                  <strong>官方</strong> 插件由 VabHub 官方维护。
                  <v-icon size="small" color="orange" class="ml-2 mr-1">mdi-account-group</v-icon>
                  <strong>社区</strong> 插件由第三方作者独立维护，风险自负。
                </template>
              </v-alert>

              <v-divider class="mt-3" />

              <!-- 加载状态 -->
              <v-card-text v-if="loadingMarket" class="pa-8 text-center">
                <v-progress-circular indeterminate color="primary" />
                <div class="mt-4">正在从插件市场加载...</div>
              </v-card-text>

              <!-- 错误状态 -->
              <v-alert v-else-if="marketError" type="error" variant="tonal" class="ma-4">
                <div class="font-weight-medium">无法加载插件市场</div>
                <div class="text-body-2 mt-1">{{ marketError }}</div>
              </v-alert>

              <!-- 空状态 -->
              <v-card-text v-else-if="marketPlugins.length === 0" class="pa-8 text-center">
                <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-store-off</v-icon>
                <div class="text-h6 text-medium-emphasis mb-2">暂无可安装的插件</div>
                <div class="text-body-2 text-medium-emphasis">
                  所有插件都已安装，或尝试打开「社区插件」开关
                </div>
              </v-card-text>

              <!-- 插件卡片列表 -->
              <v-card-text v-else class="pa-4">
                <v-row>
                  <v-col
                    v-for="plugin in marketPlugins"
                    :key="plugin.id"
                    cols="12"
                    md="6"
                    lg="4"
                  >
                    <v-card variant="outlined" class="h-100">
                      <v-card-title class="d-flex align-center text-subtitle-1">
                        <!-- 频道标签 -->
                        <v-chip
                          :color="getChannelColor(plugin.channel)"
                          size="x-small"
                          variant="flat"
                          class="mr-2"
                        >
                          <v-icon size="x-small" class="mr-1">{{ getChannelIcon(plugin.channel) }}</v-icon>
                          {{ getChannelLabel(plugin.channel) }}
                        </v-chip>
                        <span class="text-truncate">{{ plugin.name }}</span>
                        <v-spacer />
                        <v-chip size="x-small" color="grey">
                          v{{ plugin.version || '未知' }}
                        </v-chip>
                      </v-card-title>

                      <v-card-subtitle class="pb-0 d-flex align-center flex-wrap">
                        <span v-if="plugin.hub_name" class="text-caption">{{ plugin.hub_name }}</span>
                        <span v-if="plugin.author_name || plugin.author" class="text-caption ml-2">
                          · {{ plugin.author_name || plugin.author }}
                        </span>
                      </v-card-subtitle>

                      <v-card-text class="py-2">
                        <div class="text-body-2 text-medium-emphasis line-clamp-2" style="min-height: 40px;">
                          {{ plugin.description || '暂无描述' }}
                        </div>
                        
                        <!-- Tags -->
                        <div v-if="plugin.tags?.length" class="mt-2">
                          <v-chip
                            v-for="tag in plugin.tags.slice(0, 3)"
                            :key="tag"
                            size="x-small"
                            variant="tonal"
                            class="mr-1"
                          >
                            {{ tag }}
                          </v-chip>
                        </div>
                      </v-card-text>

                      <v-card-actions>
                        <v-btn
                          color="primary"
                          size="small"
                          :loading="operatingPluginId === plugin.id"
                          @click="confirmInstall(plugin)"
                        >
                          <v-icon class="mr-1">mdi-download</v-icon>
                          安装
                        </v-btn>
                        <v-btn
                          variant="text"
                          size="small"
                          @click="openInstallGuide(plugin)"
                        >
                          <v-icon class="mr-1">mdi-information-outline</v-icon>
                          详情
                        </v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- 本地插件管理（原 plugins Tab） -->
          <v-window-item value="plugins">
            <v-card v-if="loading">
              <v-card-text class="pa-8 text-center">
                <v-progress-circular indeterminate color="primary" />
                <div class="mt-4">加载中...</div>
              </v-card-text>
            </v-card>

            <v-card v-else-if="plugins.length === 0">
              <v-card-text class="pa-8 text-center">
                <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-puzzle-outline</v-icon>
                <div class="text-h6 text-medium-emphasis mb-2">暂无已安装插件</div>
                <div class="text-body-2 text-medium-emphasis">
                  点击「扫描插件目录」检测新插件
                </div>
              </v-card-text>
            </v-card>

            <v-card v-else>
              <v-data-table
                :headers="pluginHeaders"
                :items="plugins"
                item-key="id"
                class="elevation-0"
              >
                <!-- 名称 -->
                <template #item.display_name="{ item }">
                  <div class="d-flex align-center py-2">
                    <v-icon :color="getStatusColor(item.status)" class="mr-2">
                      {{ getStatusIcon(item.status) }}
                    </v-icon>
                    <div>
                      <div class="font-weight-medium">{{ item.display_name }}</div>
                      <div class="text-caption text-medium-emphasis">{{ item.name }}</div>
                    </div>
                  </div>
                </template>

                <!-- 版本 -->
                <template #item.version="{ item }">
                  <v-chip size="small" variant="outlined">v{{ item.version }}</v-chip>
                </template>

                <!-- 状态 -->
                <template #item.status="{ item }">
                  <v-chip :color="getStatusColor(item.status)" size="small">
                    {{ getStatusLabel(item.status) }}
                  </v-chip>
                </template>

                <!-- 能力 -->
                <template #item.capabilities="{ item }">
                  <div class="d-flex flex-wrap gap-1">
                    <!-- 扩展点能力 -->
                    <v-chip
                      v-if="item.capabilities.search_providers?.length"
                      size="x-small"
                      color="blue"
                      variant="tonal"
                    >
                      <v-icon size="x-small" class="mr-1">mdi-magnify</v-icon>
                      Search
                    </v-chip>
                    <v-chip
                      v-if="item.capabilities.bot_commands?.length"
                      size="x-small"
                      color="purple"
                      variant="tonal"
                    >
                      <v-icon size="x-small" class="mr-1">mdi-robot</v-icon>
                      Bot
                    </v-chip>
                    <v-chip
                      v-if="item.capabilities.workflows?.length"
                      size="x-small"
                      color="orange"
                      variant="tonal"
                    >
                      <v-icon size="x-small" class="mr-1">mdi-cog</v-icon>
                      Workflow
                    </v-chip>
                    <!-- PLUGIN-SDK-2：SDK 权限 -->
                    <v-chip
                      v-for="perm in (item.sdk_permissions || [])"
                      :key="perm"
                      size="x-small"
                      :color="getSdkPermissionColor(perm)"
                      variant="tonal"
                    >
                      <v-icon size="x-small" class="mr-1">mdi-key</v-icon>
                      {{ getSdkPermissionLabel(perm) }}
                    </v-chip>
                  </div>
                </template>

                <!-- 操作 -->
                <template #item.actions="{ item }">
                  <v-btn
                    v-if="item.status !== 'BROKEN'"
                    :color="item.status === 'ENABLED' ? 'warning' : 'success'"
                    size="small"
                    variant="text"
                    :loading="togglingId === item.id"
                    @click="toggleStatus(item)"
                  >
                    {{ item.status === 'ENABLED' ? '禁用' : '启用' }}
                  </v-btn>
                  <v-btn
                    size="small"
                    variant="text"
                    @click="showPluginDetail(item)"
                  >
                    详情
                  </v-btn>
                </template>
              </v-data-table>
            </v-card>
          </v-window-item>

          <!-- Plugin Hub -->
          <v-window-item value="hub">
            <v-card>
              <v-card-title class="d-flex align-center flex-wrap">
                <v-icon class="mr-2" color="info">mdi-cloud-download</v-icon>
                Plugin Hub
                <v-spacer />
                
                <!-- 社区插件开关（PLUGIN-HUB-3） -->
                <v-switch
                  v-model="showCommunityPlugins"
                  hide-details
                  density="compact"
                  color="orange"
                  class="mr-4"
                  @update:model-value="loadHubIndex()"
                >
                  <template #label>
                    <span class="text-body-2">
                      <v-icon size="small" color="orange" class="mr-1">mdi-account-group</v-icon>
                      社区插件
                    </span>
                  </template>
                </v-switch>
                
                <v-chip v-if="hubCached" size="small" variant="tonal" class="mr-2">
                  <v-icon size="x-small" class="mr-1">mdi-cached</v-icon>
                  缓存
                </v-chip>
                <v-btn
                  variant="tonal"
                  size="small"
                  :loading="loadingHub"
                  @click="loadHubIndex(true)"
                >
                  <v-icon class="mr-1">mdi-refresh</v-icon>
                  刷新
                </v-btn>
              </v-card-title>

              <!-- 频道说明（PLUGIN-HUB-3） -->
              <v-alert type="info" variant="tonal" density="compact" class="mx-4 mt-2 mb-0">
                <template #text>
                  <v-icon size="small" color="primary" class="mr-1">mdi-shield-check</v-icon>
                  <strong>官方</strong> 插件由 VabHub 官方维护。
                  <v-icon size="small" color="orange" class="ml-2 mr-1">mdi-account-group</v-icon>
                  <strong>社区</strong> 插件由第三方作者独立维护，风险自负。
                </template>
              </v-alert>

              <v-divider class="mt-3" />

              <!-- 加载状态 -->
              <v-card-text v-if="loadingHub" class="pa-8 text-center">
                <v-progress-circular indeterminate color="primary" />
                <div class="mt-4">正在从 Plugin Hub 加载插件列表...</div>
              </v-card-text>

              <!-- 错误状态 -->
              <v-alert v-else-if="hubError" type="error" variant="tonal" class="ma-4">
                <div class="font-weight-medium">无法加载 Plugin Hub</div>
                <div class="text-body-2 mt-1">{{ hubError }}</div>
              </v-alert>

              <!-- 空状态 -->
              <v-card-text v-else-if="hubPlugins.length === 0" class="pa-8 text-center">
                <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-cloud-off-outline</v-icon>
                <div class="text-h6 text-medium-emphasis mb-2">Plugin Hub 暂无插件</div>
              </v-card-text>

              <!-- 插件列表 -->
              <v-card-text v-else class="pa-4">
                <v-row>
                  <v-col
                    v-for="hp in hubPlugins"
                    :key="hp.id"
                    cols="12"
                    md="6"
                    lg="4"
                  >
                    <v-card variant="outlined" class="h-100">
                      <v-card-title class="d-flex align-center text-subtitle-1">
                        <!-- 频道标签（PLUGIN-HUB-3） -->
                        <v-chip
                          :color="getChannelColor(hp.channel)"
                          size="x-small"
                          variant="flat"
                          class="mr-2"
                          :title="hp.channel === 'community' ? '社区贡献插件，由第三方维护' : '官方维护'"
                        >
                          <v-icon size="x-small" class="mr-1">{{ getChannelIcon(hp.channel) }}</v-icon>
                          {{ getChannelLabel(hp.channel) }}
                        </v-chip>
                        <span class="text-truncate">{{ hp.name }}</span>
                        <v-spacer />
                        <v-chip
                          :color="getHubStatusColor(hp)"
                          size="x-small"
                        >
                          {{ getHubStatusLabel(hp) }}
                        </v-chip>
                      </v-card-title>

                      <v-card-subtitle class="pb-0 d-flex align-center flex-wrap">
                        <span class="text-caption">{{ hp.id }}</span>
                        <span v-if="hp.version" class="text-caption ml-2">v{{ hp.version }}</span>
                        <!-- 作者信息（PLUGIN-HUB-3） -->
                        <span v-if="hp.author_name || hp.author" class="text-caption ml-2">
                          ·
                          <template v-if="hp.author_url">
                            <a :href="hp.author_url" target="_blank" class="text-decoration-none">
                              {{ hp.author_name || hp.author }}
                            </a>
                          </template>
                          <template v-else>
                            {{ hp.author_name || hp.author }}
                          </template>
                        </span>
                      </v-card-subtitle>

                      <v-card-text class="py-2">
                        <div class="text-body-2 text-medium-emphasis line-clamp-2" style="min-height: 40px;">
                          {{ hp.description || '暂无描述' }}
                        </div>

                        <!-- Tags -->
                        <div v-if="hp.tags?.length" class="mt-2">
                          <v-chip
                            v-for="tag in hp.tags.slice(0, 3)"
                            :key="tag"
                            size="x-small"
                            variant="tonal"
                            class="mr-1"
                          >
                            {{ tag }}
                          </v-chip>
                        </div>

                        <!-- 功能支持 -->
                        <div class="mt-2 d-flex flex-wrap gap-1">
                          <v-icon
                            v-if="hp.supports?.search"
                            size="small"
                            color="blue"
                            title="搜索扩展"
                          >mdi-magnify</v-icon>
                          <v-icon
                            v-if="hp.supports?.bot_commands"
                            size="small"
                            color="purple"
                            title="Bot 命令"
                          >mdi-robot</v-icon>
                          <v-icon
                            v-if="hp.supports?.ui_panels"
                            size="small"
                            color="teal"
                            title="UI 面板"
                          >mdi-view-dashboard</v-icon>
                          <v-icon
                            v-if="hp.supports?.workflows"
                            size="small"
                            color="orange"
                            title="Workflow"
                          >mdi-cog-play</v-icon>
                        </div>
                      </v-card-text>

                      <v-card-actions>
                        <v-btn
                          v-if="hp.homepage"
                          variant="text"
                          size="small"
                          :href="hp.homepage"
                          target="_blank"
                        >
                          <v-icon size="small" class="mr-1">mdi-open-in-new</v-icon>
                          主页
                        </v-btn>
                        <v-spacer />
                        
                        <!-- 未安装：安装按钮 -->
                        <template v-if="!hp.installed">
                          <v-btn
                            color="primary"
                            variant="tonal"
                            size="small"
                            :loading="operatingPluginId === hp.id"
                            :disabled="!hp.repo"
                            @click="confirmInstall(hp)"
                          >
                            <v-icon size="small" class="mr-1">mdi-download</v-icon>
                            安装
                          </v-btn>
                          <v-btn
                            variant="text"
                            size="small"
                            @click="openInstallGuide(hp)"
                          >
                            指南
                          </v-btn>
                        </template>
                        
                        <!-- 已安装 & 有更新：更新 + 卸载 -->
                        <template v-else-if="hp.has_update">
                          <v-btn
                            color="warning"
                            variant="tonal"
                            size="small"
                            :loading="operatingPluginId === hp.id"
                            @click="confirmUpdate(hp)"
                          >
                            <v-icon size="small" class="mr-1">mdi-update</v-icon>
                            更新
                          </v-btn>
                          <v-btn
                            color="error"
                            variant="text"
                            size="small"
                            :disabled="operatingPluginId === hp.id"
                            @click="confirmUninstall(hp)"
                          >
                            卸载
                          </v-btn>
                        </template>
                        
                        <!-- 已安装 & 无更新：卸载 -->
                        <template v-else>
                          <v-chip size="small" color="success" variant="tonal" class="mr-2">
                            <v-icon size="x-small" class="mr-1">mdi-check</v-icon>
                            已安装
                          </v-chip>
                          <v-btn
                            color="error"
                            variant="text"
                            size="small"
                            :loading="operatingPluginId === hp.id"
                            @click="confirmUninstall(hp)"
                          >
                            卸载
                          </v-btn>
                        </template>
                      </v-card-actions>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- Workflows 列表 -->
          <v-window-item value="workflows">
            <v-card v-if="loadingWorkflows">
              <v-card-text class="pa-8 text-center">
                <v-progress-circular indeterminate color="primary" />
                <div class="mt-4">加载中...</div>
              </v-card-text>
            </v-card>

            <v-card v-else-if="workflows.length === 0">
              <v-card-text class="pa-8 text-center">
                <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-cog-play-outline</v-icon>
                <div class="text-h6 text-medium-emphasis mb-2">暂无 Workflow 扩展</div>
                <div class="text-body-2 text-medium-emphasis">
                  启用带有 Workflow 能力的插件后会在此显示
                </div>
              </v-card-text>
            </v-card>

            <v-card v-else>
              <v-list>
                <v-list-item
                  v-for="wf in workflows"
                  :key="wf.id"
                  class="py-3"
                >
                  <template #prepend>
                    <v-icon color="orange">mdi-cog-play</v-icon>
                  </template>

                  <v-list-item-title class="font-weight-medium">
                    {{ wf.name }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ wf.description }}
                    <span class="text-caption ml-2">(来自: {{ wf.plugin_name }})</span>
                  </v-list-item-subtitle>

                  <template #append>
                    <v-btn
                      color="primary"
                      size="small"
                      variant="tonal"
                      @click="openRunDialog(wf)"
                    >
                      <v-icon class="mr-1">mdi-play</v-icon>
                      执行
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>
            </v-card>
          </v-window-item>

          <!-- 面板预览 -->
          <v-window-item value="panels">
            <v-card>
              <v-card-title class="d-flex align-center">
                <v-icon class="mr-2">mdi-view-dashboard</v-icon>
                插件面板预览
                <v-spacer />
                <v-chip size="small" variant="tonal">dev_plugin</v-chip>
              </v-card-title>
              <v-divider />
              <v-card-text>
                <PluginPanelHost placement="dev_plugin" />
              </v-card-text>
            </v-card>
          </v-window-item>
        </v-window>
      </v-col>
    </v-row>

    <!-- 插件详情对话框 -->
    <v-dialog v-model="detailDialog" max-width="600">
      <v-card v-if="selectedPlugin">
        <v-card-title class="d-flex align-center">
          <v-icon :color="getStatusColor(selectedPlugin.status)" class="mr-2">
            {{ getStatusIcon(selectedPlugin.status) }}
          </v-icon>
          {{ selectedPlugin.display_name }}
          <v-spacer />
          <v-chip :color="getStatusColor(selectedPlugin.status)" size="small">
            {{ getStatusLabel(selectedPlugin.status) }}
          </v-chip>
        </v-card-title>

        <v-divider />

        <v-card-text>
          <v-list density="compact">
            <v-list-item>
              <v-list-item-title class="text-caption text-medium-emphasis">插件 ID</v-list-item-title>
              <v-list-item-subtitle class="font-mono">{{ selectedPlugin.name }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title class="text-caption text-medium-emphasis">版本</v-list-item-title>
              <v-list-item-subtitle>{{ selectedPlugin.version }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item v-if="selectedPlugin.author">
              <v-list-item-title class="text-caption text-medium-emphasis">作者</v-list-item-title>
              <v-list-item-subtitle>{{ selectedPlugin.author }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item v-if="selectedPlugin.description">
              <v-list-item-title class="text-caption text-medium-emphasis">描述</v-list-item-title>
              <v-list-item-subtitle>{{ selectedPlugin.description }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title class="text-caption text-medium-emphasis">入口模块</v-list-item-title>
              <v-list-item-subtitle class="font-mono">{{ selectedPlugin.entry_module }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item v-if="selectedPlugin.last_error">
              <v-list-item-title class="text-caption text-error">最后错误</v-list-item-title>
              <v-list-item-subtitle class="text-error">{{ selectedPlugin.last_error }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>

          <div class="text-subtitle-2 mt-4 mb-2">能力声明</div>
          <pre class="json-preview pa-3 rounded">{{ JSON.stringify(selectedPlugin.capabilities, null, 2) }}</pre>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn @click="detailDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Workflow 执行对话框 -->
    <v-dialog v-model="runDialog" max-width="600">
      <v-card v-if="selectedWorkflow">
        <v-card-title>
          执行 Workflow: {{ selectedWorkflow.name }}
        </v-card-title>

        <v-divider />

        <v-card-text>
          <div class="text-body-2 mb-4">{{ selectedWorkflow.description }}</div>

          <v-textarea
            v-model="workflowPayload"
            label="Payload (JSON)"
            placeholder='{"key": "value"}'
            variant="outlined"
            rows="4"
            class="font-mono"
          />

          <v-alert
            v-if="workflowResult"
            :type="workflowResult.success ? 'success' : 'error'"
            class="mt-4"
          >
            <div class="font-weight-bold mb-2">
              {{ workflowResult.success ? '执行成功' : '执行失败' }}
              <span class="text-caption">({{ workflowResult.duration_ms }}ms)</span>
            </div>
            <pre
              v-if="workflowResult.result || workflowResult.error"
              class="json-preview pa-2 rounded mt-2"
            >{{ workflowResult.result ? JSON.stringify(workflowResult.result, null, 2) : workflowResult.error }}</pre>
          </v-alert>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn @click="runDialog = false">关闭</v-btn>
          <v-btn
            color="primary"
            :loading="runningWorkflow"
            @click="executeWorkflow"
          >
            <v-icon class="mr-1">mdi-play</v-icon>
            执行
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 安装指南对话框 -->
    <v-dialog v-model="installGuideDialog" max-width="700">
      <v-card v-if="selectedHubPlugin">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="info">mdi-information</v-icon>
          {{ selectedHubPlugin.installed ? (selectedHubPlugin.has_update ? '更新指南' : '已安装') : '安装指南' }}
          <v-spacer />
          <v-chip :color="getHubStatusColor(selectedHubPlugin)" size="small">
            {{ getHubStatusLabel(selectedHubPlugin) }}
          </v-chip>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4">
          <div class="d-flex align-center mb-3">
            <div>
              <div class="text-h6">{{ selectedHubPlugin.name }}</div>
              <div class="text-caption text-medium-emphasis">{{ selectedHubPlugin.id }}</div>
            </div>
            <v-spacer />
            <v-chip v-if="selectedHubPlugin.version" size="small" variant="outlined">
              v{{ selectedHubPlugin.version }}
            </v-chip>
          </div>

          <pre class="guide-content pa-3 rounded">{{ installGuideContent }}</pre>

          <div v-if="selectedHubPlugin.repo" class="mt-3">
            <v-btn
              :href="selectedHubPlugin.repo"
              target="_blank"
              variant="tonal"
              size="small"
            >
              <v-icon size="small" class="mr-1">mdi-github</v-icon>
              查看仓库
            </v-btn>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn @click="installGuideDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 一键操作确认对话框 -->
    <v-dialog v-model="confirmDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" :color="confirmDialogColor">{{ confirmDialogIcon }}</v-icon>
          {{ confirmDialogTitle }}
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4">
          <div class="text-body-1 mb-3">{{ confirmDialogMessage }}</div>
          
          <v-alert v-if="confirmDialogType === 'uninstall'" type="warning" variant="tonal" class="mb-0">
            <strong>警告：</strong>此操作将删除插件目录，不可恢复。
          </v-alert>
          
          <div v-if="confirmDialogPlugin?.repo" class="mt-3">
            <div class="text-caption text-medium-emphasis">仓库地址：</div>
            <code class="text-body-2">{{ confirmDialogPlugin.repo }}</code>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn @click="confirmDialog = false" :disabled="operatingPluginId !== null">取消</v-btn>
          <v-btn
            :color="confirmDialogColor"
            variant="flat"
            :loading="operatingPluginId !== null"
            @click="executeConfirmedAction"
          >
            确认{{ confirmDialogType === 'install' ? '安装' : confirmDialogType === 'update' ? '更新' : '卸载' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 插件源设置对话框（PLUGIN-HUB-4） -->
    <v-dialog v-model="hubSettingsDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-cog</v-icon>
          插件市场设置
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4">
          <div class="text-body-2 text-medium-emphasis mb-3">
            每行输入一个插件市场地址，支持 plugins.json 直链或 GitHub 仓库地址。
          </div>
          
          <v-textarea
            v-model="hubSourcesText"
            placeholder="https://raw.githubusercontent.com/strmforge/vabhub-plugins/main/plugins.json
https://github.com/someone/vabhub-plugins"
            rows="6"
            auto-grow
            variant="outlined"
            hide-details
          />
          
          <v-alert type="info" variant="tonal" density="compact" class="mt-3">
            <template #text>
              <div class="text-caption">
                <strong>官方源</strong>（strmforge 组织下）会自动标记为 [官方]，其它默认为 [社区]。<br />
                删除某行即等同于移除该插件源。
              </div>
            </template>
          </v-alert>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn @click="hubSettingsDialog = false" :disabled="savingHubSources">取消</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :loading="savingHubSources"
            @click="saveHubSources"
          >
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { pluginAdminApi, pluginHubApi } from '@/services/api'
import { useToast } from 'vue-toastification'
import PluginPanelHost from '@/components/plugin/PluginPanelHost.vue'
import type {
  PluginInfo,
  WorkflowExtensionInfo,
  WorkflowRunResult,
} from '@/types/plugin'
import {
  getStatusColor,
  getStatusIcon,
  getStatusLabel,
  getSdkPermissionLabel,
  getSdkPermissionColor,
} from '@/types/plugin'
import type { RemotePluginWithLocalStatus, PluginHubConfigResponse, PluginHubSource } from '@/types/pluginHub'
import { 
  getChannelLabel, 
  getChannelColor, 
  getChannelIcon,
  isCommunityPlugin,
} from '@/types/pluginHub'

const toast = useToast()

// State
const activeTab = ref('my-plugins')  // 默认显示"我的插件"
const loading = ref(false)
const scanning = ref(false)
const plugins = ref<PluginInfo[]>([])
const togglingId = ref<number | null>(null)

// "我的插件" 状态（PLUGIN-HUB-4）
const loadingMyPlugins = ref(false)
const myPlugins = ref<RemotePluginWithLocalStatus[]>([])
const showUpdatableOnly = ref(false)

// "插件市场" 状态（PLUGIN-HUB-4）
const loadingMarket = ref(false)
const marketPlugins = ref<RemotePluginWithLocalStatus[]>([])
const marketError = ref<string | null>(null)

// Hub 源设置（PLUGIN-HUB-4）
const hubSettingsDialog = ref(false)
const hubSourcesText = ref('')
const savingHubSources = ref(false)
const hubSources = ref<PluginHubSource[]>([])

// 计算属性
const updatableCount = computed(() => myPlugins.value.filter(p => p.has_update).length)
const filteredMyPlugins = computed(() => {
  if (showUpdatableOnly.value) {
    return myPlugins.value.filter(p => p.has_update)
  }
  return myPlugins.value
})

// Plugin Hub state (保留兼容)
const loadingHub = ref(false)
const hubPlugins = ref<RemotePluginWithLocalStatus[]>([])
const hubError = ref<string | null>(null)
const hubCached = ref(false)
const installGuideDialog = ref(false)
const installGuideContent = ref('')
const selectedHubPlugin = ref<RemotePluginWithLocalStatus | null>(null)

// 社区插件配置（PLUGIN-HUB-3）
const showCommunityPlugins = ref(false)
const hubConfig = ref<PluginHubConfigResponse | null>(null)

// 一键操作状态（PLUGIN-HUB-2）
const operatingPluginId = ref<string | null>(null)
const confirmDialog = ref(false)
const confirmDialogType = ref<'install' | 'update' | 'uninstall'>('install')
const confirmDialogPlugin = ref<RemotePluginWithLocalStatus | null>(null)
const confirmDialogTitle = ref('')
const confirmDialogMessage = ref('')
const confirmDialogIcon = ref('mdi-download')
const confirmDialogColor = ref('primary')

const loadingWorkflows = ref(false)
const workflows = ref<WorkflowExtensionInfo[]>([])

const detailDialog = ref(false)
const selectedPlugin = ref<PluginInfo | null>(null)

const runDialog = ref(false)
const selectedWorkflow = ref<WorkflowExtensionInfo | null>(null)
const workflowPayload = ref('')
const workflowResult = ref<WorkflowRunResult | null>(null)
const runningWorkflow = ref(false)

// Table headers
const pluginHeaders = [
  { title: '插件', key: 'display_name', sortable: true },
  { title: '版本', key: 'version', sortable: true },
  { title: '状态', key: 'status', sortable: true },
  { title: '能力', key: 'capabilities', sortable: false },
  { title: '操作', key: 'actions', sortable: false, align: 'end' as const },
]

// Load plugins
const loadPlugins = async () => {
  loading.value = true
  try {
    plugins.value = await pluginAdminApi.list()
  } catch (error: any) {
    console.error('加载插件列表失败:', error)
    toast.error(error.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

// Load Plugin Hub config（PLUGIN-HUB-3）
const loadHubConfig = async () => {
  try {
    hubConfig.value = await pluginHubApi.getConfig()
    // 根据服务端配置初始化开关状态
    showCommunityPlugins.value = hubConfig.value.community_visible
  } catch (error) {
    console.error('加载 Plugin Hub 配置失败:', error)
  }
}

// Load Plugin Hub index (保留兼容)
const loadHubIndex = async (forceRefresh = false) => {
  loadingHub.value = true
  hubError.value = null
  try {
    const result = await pluginHubApi.getIndex({ 
      force_refresh: forceRefresh,
      include_community: showCommunityPlugins.value,
    })
    hubPlugins.value = result.plugins
    hubCached.value = result.cached
    if (forceRefresh) {
      toast.success('Plugin Hub 已刷新')
    }
  } catch (error: any) {
    console.error('加载 Plugin Hub 失败:', error)
    hubError.value = error.response?.data?.detail || '无法连接 Plugin Hub'
    if (forceRefresh) {
      toast.error('刷新 Plugin Hub 失败')
    }
  } finally {
    loadingHub.value = false
  }
}

// ============== 我的插件（PLUGIN-HUB-4） ==============

// 加载我的插件（已安装）
const loadMyPlugins = async (forceRefresh = false) => {
  loadingMyPlugins.value = true
  try {
    myPlugins.value = await pluginHubApi.list({
      installed_only: true,
      force_refresh: forceRefresh,
    })
    if (forceRefresh) {
      toast.success('我的插件已刷新')
    }
  } catch (error: any) {
    console.error('加载我的插件失败:', error)
    toast.error(error.response?.data?.detail || '加载失败')
  } finally {
    loadingMyPlugins.value = false
  }
}

// ============== 插件市场（PLUGIN-HUB-4） ==============

// 加载插件市场（未安装）
const loadMarketPlugins = async (forceRefresh = false) => {
  loadingMarket.value = true
  marketError.value = null
  try {
    marketPlugins.value = await pluginHubApi.list({
      not_installed_only: true,
      include_community: showCommunityPlugins.value,
      force_refresh: forceRefresh,
    })
    if (forceRefresh) {
      toast.success('插件市场已刷新')
    }
  } catch (error: any) {
    console.error('加载插件市场失败:', error)
    marketError.value = error.response?.data?.detail || '无法连接插件市场'
    if (forceRefresh) {
      toast.error('刷新插件市场失败')
    }
  } finally {
    loadingMarket.value = false
  }
}

// ============== Hub 源设置（PLUGIN-HUB-4） ==============

// 打开 Hub 源设置对话框
const openHubSettingsDialog = async () => {
  hubSettingsDialog.value = true
  
  try {
    hubSources.value = await pluginHubApi.getHubs()
    // 将 sources 转换为多行文本
    hubSourcesText.value = hubSources.value.map(s => s.url).join('\n')
  } catch (error: any) {
    console.error('加载 Hub 源失败:', error)
    toast.error('加载插件源列表失败')
  }
}

// 保存 Hub 源设置
const saveHubSources = async () => {
  savingHubSources.value = true
  
  try {
    // 解析多行文本为 URL 列表
    const lines = hubSourcesText.value
      .split('\n')
      .map(line => line.trim())
      .filter(line => line && (line.startsWith('http://') || line.startsWith('https://')))
    
    if (lines.length === 0) {
      toast.warning('请输入至少一个有效的插件源地址')
      savingHubSources.value = false
      return
    }
    
    // 构造 Hub 源列表
    const sources: PluginHubSource[] = lines.map((url, index) => {
      // 从 URL 推断 ID 和名称
      let id = `hub-${index}`
      let name = `插件源 ${index + 1}`
      let channel: 'official' | 'community' = 'community'
      
      try {
        const urlObj = new URL(url)
        const pathParts = urlObj.pathname.split('/').filter(Boolean)
        if (pathParts.length >= 2) {
          id = `${pathParts[0]}-${pathParts[1]}`.toLowerCase()
          name = `${pathParts[0]}/${pathParts[1]}`
          // 官方组织判定
          if (pathParts[0].toLowerCase() === 'strmforge') {
            channel = 'official'
            name = 'VabHub 官方插件市场'
          }
        }
      } catch {}
      
      return {
        id,
        name,
        url,
        channel,
        enabled: true,
      }
    })
    
    // 保存到后端
    await pluginHubApi.updateHubs(sources)
    
    toast.success('插件源设置已保存')
    hubSettingsDialog.value = false
    
    // 刷新插件市场
    await loadMarketPlugins(true)
    await loadMyPlugins(true)
    
  } catch (error: any) {
    console.error('保存 Hub 源失败:', error)
    toast.error(error.response?.data?.detail || '保存失败')
  } finally {
    savingHubSources.value = false
  }
}

// Plugin Hub helpers
const getHubStatusColor = (plugin: RemotePluginWithLocalStatus): string => {
  if (plugin.installed && plugin.has_update) return 'warning'
  if (plugin.installed) return 'success'
  return 'grey'
}

const getHubStatusLabel = (plugin: RemotePluginWithLocalStatus): string => {
  if (plugin.installed && plugin.has_update) return '可更新'
  if (plugin.installed) return '已安装'
  return '未安装'
}

// Open install guide
const openInstallGuide = async (plugin: RemotePluginWithLocalStatus) => {
  selectedHubPlugin.value = plugin
  installGuideContent.value = '加载中...'
  installGuideDialog.value = true
  
  try {
    const guide = await pluginHubApi.getInstallGuide(plugin.id)
    installGuideContent.value = guide.guide
  } catch (error: any) {
    installGuideContent.value = `无法加载安装指南：${error.response?.data?.detail || error.message}`
  }
}

// ============== 一键操作（PLUGIN-HUB-2 & 3） ==============

// 获取社区插件风险提示
const getCommunityWarning = (plugin: RemotePluginWithLocalStatus): string => {
  if (isCommunityPlugin(plugin)) {
    return '\n\n⚠️ 该插件由第三方开发，与 VabHub 官方无关。请先阅读插件仓库说明，确认风险后再操作。'
  }
  return ''
}

// 检查社区插件安装是否被禁用
const isCommunityInstallDisabled = (plugin: RemotePluginWithLocalStatus): boolean => {
  if (!isCommunityPlugin(plugin)) return false
  return hubConfig.value ? !hubConfig.value.community_install_enabled : false
}

// 确认安装
const confirmInstall = (plugin: RemotePluginWithLocalStatus) => {
  // 检查社区插件安装权限
  if (isCommunityInstallDisabled(plugin)) {
    toast.warning('社区插件已被禁用一键安装，请使用安装指南手动部署')
    openInstallGuide(plugin)
    return
  }
  
  confirmDialogPlugin.value = plugin
  confirmDialogType.value = 'install'
  confirmDialogTitle.value = '确认安装插件'
  confirmDialogMessage.value = `确定要安装插件「${plugin.name}」吗？${getCommunityWarning(plugin)}`
  confirmDialogIcon.value = 'mdi-download'
  confirmDialogColor.value = isCommunityPlugin(plugin) ? 'orange' : 'primary'
  confirmDialog.value = true
}

// 确认更新
const confirmUpdate = (plugin: RemotePluginWithLocalStatus) => {
  // 检查社区插件更新权限
  if (isCommunityInstallDisabled(plugin)) {
    toast.warning('社区插件已被禁用一键更新，请手动执行 git pull')
    return
  }
  
  confirmDialogPlugin.value = plugin
  confirmDialogType.value = 'update'
  confirmDialogTitle.value = '确认更新插件'
  confirmDialogMessage.value = `确定要更新插件「${plugin.name}」吗？当前版本：${plugin.local_version}，远程版本：${plugin.version}${getCommunityWarning(plugin)}`
  confirmDialogIcon.value = 'mdi-update'
  confirmDialogColor.value = isCommunityPlugin(plugin) ? 'orange' : 'warning'
  confirmDialog.value = true
}

// 确认卸载
const confirmUninstall = (plugin: RemotePluginWithLocalStatus) => {
  confirmDialogPlugin.value = plugin
  confirmDialogType.value = 'uninstall'
  confirmDialogTitle.value = '确认卸载插件'
  confirmDialogMessage.value = `确定要卸载插件「${plugin.name}」吗？`
  confirmDialogIcon.value = 'mdi-delete'
  confirmDialogColor.value = 'error'
  confirmDialog.value = true
}

// 执行确认的操作
const executeConfirmedAction = async () => {
  const plugin = confirmDialogPlugin.value
  if (!plugin) return
  
  operatingPluginId.value = plugin.id
  
  try {
    switch (confirmDialogType.value) {
      case 'install':
        await pluginHubApi.install(plugin.id)
        toast.success(`插件「${plugin.name}」安装成功`)
        break
      case 'update':
        await pluginHubApi.update(plugin.id)
        toast.success(`插件「${plugin.name}」更新成功`)
        break
      case 'uninstall':
        await pluginHubApi.uninstall(plugin.id)
        toast.success(`插件「${plugin.name}」已卸载`)
        break
    }
    
    // 刷新列表
    confirmDialog.value = false
    await loadHubIndex()
    await loadPlugins()
    
  } catch (error: any) {
    console.error('操作失败:', error)
    toast.error(error.response?.data?.detail || '操作失败')
  } finally {
    operatingPluginId.value = null
  }
}

// Scan plugins
const scanPlugins = async () => {
  scanning.value = true
  try {
    const result = await pluginAdminApi.scan()
    plugins.value = result.plugins
    toast.success(
      `扫描完成：新增 ${result.new_plugins}，更新 ${result.updated_plugins}，损坏 ${result.broken_plugins}`
    )
  } catch (error: any) {
    console.error('扫描插件失败:', error)
    toast.error(error.response?.data?.detail || '扫描失败')
  } finally {
    scanning.value = false
  }
}

// Toggle plugin status
const toggleStatus = async (plugin: PluginInfo) => {
  togglingId.value = plugin.id
  try {
    const newStatus = plugin.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
    const updated = await pluginAdminApi.updateStatus(plugin.id, newStatus)
    
    const index = plugins.value.findIndex(p => p.id === plugin.id)
    if (index !== -1) {
      plugins.value[index] = updated
    }
    
    toast.success(`插件 ${plugin.display_name} 已${newStatus === 'ENABLED' ? '启用' : '禁用'}`)
    
    // 刷新 workflows
    if (activeTab.value === 'workflows' || newStatus === 'ENABLED') {
      await loadWorkflows()
    }
  } catch (error: any) {
    console.error('切换状态失败:', error)
    toast.error(error.response?.data?.detail || '操作失败')
  } finally {
    togglingId.value = null
  }
}

// Show plugin detail
const showPluginDetail = (plugin: PluginInfo) => {
  selectedPlugin.value = plugin
  detailDialog.value = true
}

// Load workflows
const loadWorkflows = async () => {
  loadingWorkflows.value = true
  try {
    workflows.value = await pluginAdminApi.listWorkflows()
  } catch (error: any) {
    console.error('加载 Workflows 失败:', error)
    toast.error(error.response?.data?.detail || '加载失败')
  } finally {
    loadingWorkflows.value = false
  }
}

// Open run dialog
const openRunDialog = (wf: WorkflowExtensionInfo) => {
  selectedWorkflow.value = wf
  workflowPayload.value = ''
  workflowResult.value = null
  runDialog.value = true
}

// Execute workflow
const executeWorkflow = async () => {
  if (!selectedWorkflow.value) return

  runningWorkflow.value = true
  workflowResult.value = null

  try {
    let payload = null
    if (workflowPayload.value.trim()) {
      try {
        payload = JSON.parse(workflowPayload.value)
      } catch (e) {
        toast.error('Payload JSON 格式无效')
        runningWorkflow.value = false
        return
      }
    }

    workflowResult.value = await pluginAdminApi.runWorkflow(selectedWorkflow.value.id, payload)
  } catch (error: any) {
    console.error('执行 Workflow 失败:', error)
    workflowResult.value = {
      workflow_id: selectedWorkflow.value.id,
      success: false,
      error: error.response?.data?.detail || '执行失败',
      duration_ms: 0,
    }
  } finally {
    runningWorkflow.value = false
  }
}

// Watch tab change
watch(activeTab, async (val) => {
  if (val === 'my-plugins' && myPlugins.value.length === 0 && !loadingMyPlugins.value) {
    // 首次进入"我的插件"时加载配置和列表
    if (!hubConfig.value) {
      await loadHubConfig()
    }
    loadMyPlugins()
  }
  if (val === 'market' && marketPlugins.value.length === 0 && !loadingMarket.value) {
    // 首次进入"插件市场"时加载配置和列表
    if (!hubConfig.value) {
      await loadHubConfig()
    }
    loadMarketPlugins()
  }
  if (val === 'workflows' && workflows.value.length === 0) {
    loadWorkflows()
  }
  if (val === 'hub' && hubPlugins.value.length === 0 && !loadingHub.value) {
    // 首次进入 Plugin Hub Tab 时加载配置
    if (!hubConfig.value) {
      await loadHubConfig()
    }
    loadHubIndex()
  }
})

// Init
onMounted(async () => {
  // 加载本地插件列表
  loadPlugins()
  
  // 默认显示"我的插件"Tab，自动加载
  if (activeTab.value === 'my-plugins') {
    await loadHubConfig()
    loadMyPlugins()
  }
})
</script>

<style scoped>
.json-preview {
  background: #263238;
  color: #80cbc4;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.font-mono {
  font-family: 'Fira Code', 'Consolas', monospace;
}

.gap-1 {
  gap: 4px;
}

.guide-content {
  background: #263238;
  color: #e0e0e0;
  font-size: 13px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Fira Code', 'Consolas', monospace;
  max-height: 400px;
  overflow-y: auto;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* NEW 角标（PLUGIN-HUB-4） */
.plugin-card {
  position: relative;
}

.new-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
}
</style>
