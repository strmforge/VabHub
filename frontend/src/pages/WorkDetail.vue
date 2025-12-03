<template>
  <div class="work-detail-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64" />
      <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
    </div>

    <!-- 错误状态 -->
    <v-alert
      v-else-if="error"
      type="error"
      variant="tonal"
      class="mb-4"
    >
      {{ error }}
    </v-alert>

    <!-- 内容 -->
    <div v-else-if="work">
      <!-- 页面头部 -->
      <div class="d-flex align-start mb-6">
        <v-btn
          icon
          variant="text"
          @click="$router.push('/library')"
          class="mr-4"
        >
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <PageHeader
          :title="work.title"
          :subtitle="workSubtitle"
        />
      </div>

      <!-- 作品信息卡片 -->
      <v-row class="mb-6">
        <!-- 封面 -->
        <v-col cols="12" md="3">
          <v-card>
            <v-img
              :src="work.cover_url || '/default-cover.png'"
              :lazy-src="work.cover_url || '/default-cover.png'"
              aspect-ratio="2/3"
              cover
              class="bg-grey-lighten-3"
            >
              <template v-slot:placeholder>
                <div class="d-flex align-center justify-center fill-height">
                  <v-icon size="64" color="grey-lighten-1">mdi-book-open-variant</v-icon>
                </div>
              </template>
              <template v-slot:error>
                <div class="d-flex align-center justify-center fill-height">
                  <v-icon size="64" color="grey-lighten-1">mdi-book-open-variant</v-icon>
                </div>
              </template>
            </v-img>
          </v-card>
        </v-col>

        <!-- 作品详情 -->
        <v-col cols="12" md="9">
          <v-card>
            <v-card-text>
              <div class="d-flex flex-column gap-3">
                <!-- 标题 -->
                <div>
                  <h2 class="text-h5 mb-1">{{ work.title }}</h2>
                  <div v-if="work.original_title" class="text-body-2 text-medium-emphasis">
                    {{ work.original_title }}
                  </div>
                </div>

                <!-- 基本信息 -->
                <v-divider />
                
                <!-- 操作按钮 -->
                <div class="d-flex gap-2 mb-2">
                  <v-btn
                    color="primary"
                    variant="elevated"
                    prepend-icon="mdi-book-open-page-variant"
                    @click="$router.push({ name: 'NovelReader', params: { ebookId: work.id } })"
                  >
                    阅读小说
                  </v-btn>
                </div>
                
                <div class="d-flex flex-wrap gap-4">
                  <div v-if="work.author" class="d-flex align-center">
                    <v-icon size="small" class="mr-2">mdi-account</v-icon>
                    <span class="text-body-2">{{ work.author }}</span>
                  </div>
                  
                  <div v-if="work.series" class="d-flex align-center">
                    <v-icon size="small" class="mr-2">mdi-book-multiple</v-icon>
                    <span class="text-body-2">{{ work.series }}</span>
                    <span v-if="work.volume_index" class="text-body-2 ml-1">
                      ({{ work.volume_index }})
                    </span>
                  </div>
                  
                  <div v-if="work.publish_year" class="d-flex align-center">
                    <v-icon size="small" class="mr-2">mdi-calendar</v-icon>
                    <span class="text-body-2">{{ work.publish_year }}</span>
                  </div>
                  
                  <div v-if="work.isbn" class="d-flex align-center">
                    <v-icon size="small" class="mr-2">mdi-barcode</v-icon>
                    <span class="text-body-2">{{ work.isbn }}</span>
                  </div>
                  
                  <div v-if="work.language" class="d-flex align-center">
                    <v-icon size="small" class="mr-2">mdi-translate</v-icon>
                    <span class="text-body-2">{{ work.language }}</span>
                  </div>
                </div>

                <!-- 简介 -->
                <v-divider v-if="work.description" />
                
                <div v-if="work.description">
                  <h3 class="text-subtitle-1 mb-2">简介</h3>
                  <p class="text-body-2 text-medium-emphasis" style="white-space: pre-wrap;">
                    {{ work.description }}
                  </p>
                </div>

                <!-- 标签 -->
                <v-divider v-if="work.tags" />
                
                <div v-if="work.tags">
                  <h3 class="text-subtitle-1 mb-2">标签</h3>
                  <div class="d-flex flex-wrap gap-2">
                    <v-chip
                      v-for="tag in parseTags(work.tags)"
                      :key="tag"
                      size="small"
                      variant="outlined"
                    >
                      {{ tag }}
                    </v-chip>
                  </div>
                </div>

                <!-- Dev 模式：小说源信息 & TTS 重新生成 -->
                <template v-if="isDevMode && canRegenTTS">
                  <v-divider class="mt-4" />
                  <div class="mt-4">
                    <h3 class="text-subtitle-1 mb-2 d-flex align-center">
                      <v-icon size="small" class="mr-2">mdi-code-tags</v-icon>
                      <span>Dev 工具</span>
                      <v-chip size="small" color="warning" class="ml-2">Dev Only</v-chip>
                    </h3>
                    
                    <!-- 小说源信息 -->
                    <div class="mb-3">
                      <div class="text-body-2 mb-1">
                        <strong>来源：</strong>
                        <v-chip size="small" color="info" variant="flat" class="ml-1">
                          TXT ({{ novelSource.type }})
                        </v-chip>
                      </div>
                      <div class="text-body-2 text-medium-emphasis">
                        <strong>存档路径：</strong>
                        <v-tooltip>
                          <template v-slot:activator="{ props }">
                            <span v-bind="props" class="text-truncate d-inline-block" style="max-width: 400px;">
                              {{ novelSource.archived_txt_path }}
                            </span>
                          </template>
                          <span>{{ novelSource.archived_txt_path }}</span>
                        </v-tooltip>
                      </div>
                    </div>

                    <!-- 重新生成 TTS 按钮 -->
                    <v-btn
                      color="primary"
                      variant="elevated"
                      :loading="regenLoading"
                      @click="handleRegenTTS"
                      prepend-icon="mdi-refresh"
                      class="mb-3"
                    >
                      重新生成 TTS 有声书
                    </v-btn>

                    <!-- TTS Job 历史 -->
                    <v-divider class="my-3" />
                    <div>
                      <h4 class="text-subtitle-2 mb-2">TTS Job 历史（最近 5 条）</h4>
                      <div v-if="jobsLoading" class="text-center py-2">
                        <v-progress-circular indeterminate size="small" />
                      </div>
                      <div v-else-if="ttsJobs.length === 0" class="text-body-2 text-medium-emphasis">
                        暂无 Job 记录
                      </div>
                      <v-list density="compact" v-else>
                        <v-list-item
                          v-for="job in ttsJobs"
                          :key="job.id"
                          class="px-0"
                        >
                          <v-list-item-title class="d-flex align-center">
                            <v-chip
                              :color="getJobStatusColor(job.status)"
                              size="small"
                              variant="flat"
                              class="mr-2"
                            >
                              {{ getJobStatusLabel(job.status) }}
                            </v-chip>
                            <span class="text-caption text-medium-emphasis mr-2">
                              {{ formatDateTime(job.requested_at) }}
                            </span>
                            <span v-if="job.created_files_count > 0" class="text-caption text-success">
                              +{{ job.created_files_count }} 文件
                            </span>
                          </v-list-item-title>
                        </v-list-item>
                      </v-list>
                      
                      <v-btn
                        color="secondary"
                        variant="outlined"
                        size="small"
                        :loading="createJobLoading"
                        @click="handleCreateJob"
                        prepend-icon="mdi-plus"
                        class="mt-2"
                      >
                        为本作品创建 TTS Job
                      </v-btn>
                      <div class="text-caption text-medium-emphasis mt-1">
                        执行由 <router-link to="/dev/tts-jobs" class="text-primary">/dev/tts-jobs</router-link> 页面统一 run-next
                      </div>
                    </div>

                    <!-- TTS Profile 配置 -->
                    <v-divider class="my-3" />
                    <div>
                      <h4 class="text-subtitle-2 mb-2">作品 TTS Profile</h4>
                      <div v-if="ttsProfileLoading" class="text-center py-2">
                        <v-progress-circular indeterminate size="small" />
                      </div>
                      <div v-else>
                        <!-- 显示当前 Profile -->
                        <v-card v-if="ttsProfile" variant="outlined" class="mb-3">
                          <v-card-text>
                            <div class="d-flex flex-column gap-2">
                              <div v-if="ttsProfile.provider" class="text-body-2">
                                <strong>Provider:</strong> {{ ttsProfile.provider }}
                              </div>
                              <div v-if="ttsProfile.language" class="text-body-2">
                                <strong>Language:</strong> {{ ttsProfile.language }}
                              </div>
                              <div v-if="ttsProfile.voice" class="text-body-2">
                                <strong>Voice:</strong> {{ ttsProfile.voice }}
                              </div>
                              <div v-if="ttsProfile.speed !== null" class="text-body-2">
                                <strong>Speed:</strong> {{ ttsProfile.speed }}
                              </div>
                              <div v-if="ttsProfile.pitch !== null" class="text-body-2">
                                <strong>Pitch:</strong> {{ ttsProfile.pitch }}
                              </div>
                              <div class="text-body-2">
                                <strong>Enabled:</strong> 
                                <v-chip size="small" :color="ttsProfile.enabled ? 'success' : 'error'" variant="flat">
                                  {{ ttsProfile.enabled ? '是' : '否' }}
                                </v-chip>
                              </div>
                              <div v-if="ttsProfile.notes" class="text-body-2">
                                <strong>Notes:</strong> {{ ttsProfile.notes }}
                              </div>
                              <div v-if="ttsProfile.preset_id" class="text-body-2">
                                <strong>预设:</strong> 
                                <v-chip size="small" color="info" variant="outlined" class="ml-1">
                                  {{ getPresetName(ttsProfile.preset_id) }}
                                </v-chip>
                              </div>
                            </div>
                          </v-card-text>
                        </v-card>
                        <div v-else class="text-body-2 text-medium-emphasis mb-3">
                          未配置作品级 TTS Profile，将使用全局默认配置
                        </div>

                        <!-- 编辑表单 -->
                        <v-card variant="outlined">
                          <v-card-text>
                            <v-form ref="ttsProfileForm">
                              <!-- 预设选择 -->
                              <v-select
                                v-model="ttsProfileForm.preset_id"
                                :items="voicePresets"
                                item-title="name"
                                item-value="id"
                                label="选用预设"
                                placeholder="选择预设（可选）"
                                variant="outlined"
                                density="compact"
                                class="mb-2"
                                clearable
                              >
                                <template v-slot:item="{ props, item }">
                                  <v-list-item v-bind="props">
                                    <template v-slot:title>
                                      <div class="d-flex align-center">
                                        <span>{{ item.raw.name }}</span>
                                        <v-chip
                                          v-if="item.raw.is_default"
                                          size="x-small"
                                          color="success"
                                          variant="flat"
                                          class="ml-2"
                                        >
                                          默认
                                        </v-chip>
                                      </div>
                                    </template>
                                    <template v-slot:subtitle>
                                      <span v-if="item.raw.provider || item.raw.language || item.raw.voice">
                                        {{ [item.raw.provider, item.raw.language, item.raw.voice].filter(Boolean).join(' / ') }}
                                      </span>
                                    </template>
                                  </v-list-item>
                                </template>
                              </v-select>
                              
                              <v-btn
                                v-if="ttsProfileForm.preset_id"
                                size="small"
                                variant="outlined"
                                color="primary"
                                prepend-icon="mdi-content-copy"
                                @click="handleFillFromPreset"
                                class="mb-2"
                              >
                                从预设填充字段
                              </v-btn>
                              
                              <v-divider class="my-2" />
                              
                              <v-text-field
                                v-model="ttsProfileForm.provider"
                                label="Provider"
                                placeholder="dummy / http"
                                variant="outlined"
                                density="compact"
                                class="mb-2"
                              />
                              <v-text-field
                                v-model="ttsProfileForm.language"
                                label="Language"
                                placeholder="zh-CN / en-US"
                                variant="outlined"
                                density="compact"
                                class="mb-2"
                              />
                              <v-text-field
                                v-model="ttsProfileForm.voice"
                                label="Voice"
                                placeholder="zh-CN-female-1"
                                variant="outlined"
                                density="compact"
                                class="mb-2"
                              />
                              <v-text-field
                                v-model.number="ttsProfileForm.speed"
                                label="Speed"
                                type="number"
                                placeholder="1.0"
                                min="0.5"
                                max="2.0"
                                step="0.1"
                                variant="outlined"
                                density="compact"
                                class="mb-2"
                              />
                              <v-text-field
                                v-model.number="ttsProfileForm.pitch"
                                label="Pitch"
                                type="number"
                                placeholder="0.0"
                                min="-10.0"
                                max="10.0"
                                step="0.1"
                                variant="outlined"
                                density="compact"
                                class="mb-2"
                              />
                              <v-textarea
                                v-model="ttsProfileForm.notes"
                                label="Notes"
                                placeholder="Dev notes"
                                variant="outlined"
                                density="compact"
                                rows="2"
                                class="mb-2"
                              />
                              <v-switch
                                v-model="ttsProfileForm.enabled"
                                label="启用此配置"
                                color="primary"
                                density="compact"
                                class="mb-2"
                              />
                            </v-form>
                          </v-card-text>
                          <v-card-actions>
                            <v-btn
                              color="primary"
                              variant="elevated"
                              :loading="ttsProfileSaving"
                              @click="handleSaveTTSProfile"
                              prepend-icon="mdi-content-save"
                            >
                              保存 TTS Profile
                            </v-btn>
                            <v-btn
                              v-if="ttsProfile"
                              color="error"
                              variant="outlined"
                              :loading="ttsProfileDeleting"
                              @click="handleDeleteTTSProfile"
                              prepend-icon="mdi-delete"
                            >
                              清除作品 TTS Profile
                            </v-btn>
                          </v-card-actions>
                        </v-card>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 电子书文件列表 -->
      <v-card class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-book-open-variant</v-icon>
          电子书文件
          <v-chip size="small" class="ml-2" color="success">
            {{ ebookFiles.length }}
          </v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-data-table
            :headers="ebookFileHeaders"
            :items="ebookFiles"
            :items-per-page="10"
            class="elevation-0"
            no-data-text="暂无电子书文件"
          >
            <template v-slot:item.format="{ item }">
              <v-chip size="small" color="primary" variant="flat">
                {{ item.format?.toUpperCase() || '-' }}
              </v-chip>
            </template>
            <template v-slot:item.file_size_mb="{ item }">
              {{ item.file_size_mb ? `${item.file_size_mb.toFixed(2)} MB` : '-' }}
            </template>
            <template v-slot:item.source_site_id="{ item }">
              <v-chip v-if="item.source_site_id" size="small" variant="outlined">
                {{ item.source_site_id }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
            <template v-slot:item.created_at="{ item }">
              {{ formatDate(item.created_at) }}
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>

      <!-- TTS 有声书状态 -->
      <v-card class="mb-6" v-if="work && work.id">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="purple">mdi-text-to-speech</v-icon>
          <span>TTS 有声书</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <!-- 加载状态 -->
          <v-progress-linear
            v-if="ttsStatusLoading"
            indeterminate
            color="primary"
            class="mb-4"
          />

          <!-- TTS 状态信息 -->
          <div v-if="workTTSStatus && !ttsStatusLoading" class="d-flex flex-column gap-3">
            <!-- TTS 通知提示 -->
            <div v-if="ttsNotification && !ttsNotificationLoading" class="d-flex align-center">
              <v-chip
                :color="getNotificationSeverityColor(ttsNotification.severity || 'info')"
                size="small"
                variant="flat"
                class="mr-2"
                clickable
                @click="handleNotificationChipClick"
              >
                <v-icon start size="small">
                  {{ ttsNotification.severity === 'success' ? 'mdi-check-circle' : 
                     ttsNotification.severity === 'warning' ? 'mdi-alert' : 
                     ttsNotification.severity === 'error' ? 'mdi-alert-circle' : 
                     'mdi-information' }}
                </v-icon>
                {{ getNotificationChipText(ttsNotification) }}
              </v-chip>
            </div>

            <!-- 已有 TTS 有声书提示 -->
            <div v-if="workTTSStatus.has_tts_audiobook" class="d-flex align-center">
              <v-chip size="small" color="success" variant="flat" class="mr-2">
                <v-icon start size="small">mdi-check-circle</v-icon>
                已有 TTS 有声书
              </v-chip>
            </div>

            <!-- Job 状态显示 -->
            <div v-if="workTTSStatus.last_job_status" class="d-flex align-center flex-wrap gap-2">
              <v-chip
                :color="getTTSStatusColor(workTTSStatus.last_job_status)"
                size="small"
                variant="flat"
              >
                <v-icon
                  start
                  size="small"
                  :icon="getTTSStatusIcon(workTTSStatus.last_job_status)"
                ></v-icon>
                {{ getTTSStatusLabel(workTTSStatus.last_job_status) }}
              </v-chip>

              <!-- 章节进度 -->
              <span
                v-if="workTTSStatus.total_chapters && workTTSStatus.generated_chapters !== undefined"
                class="text-body-2 text-medium-emphasis"
              >
                已生成 {{ workTTSStatus.generated_chapters }} / {{ workTTSStatus.total_chapters }} 章
              </span>

              <!-- 最后执行时间 -->
              <span
                v-if="workTTSStatus.last_job_requested_at"
                class="text-caption text-medium-emphasis"
              >
                {{ formatRelativeTime(workTTSStatus.last_job_requested_at) }}
              </span>
            </div>

            <!-- 消息提示 -->
            <v-alert
              v-if="workTTSStatus.last_job_message"
              :type="getTTSStatusAlertType(workTTSStatus.last_job_status)"
              variant="tonal"
              density="compact"
              class="mb-2"
            >
              {{ workTTSStatus.last_job_message }}
            </v-alert>

            <!-- 操作按钮 -->
            <div class="d-flex align-center gap-2">
              <v-btn
                color="primary"
                :loading="ttsEnqueueLoading"
                :disabled="
                  ttsEnqueueLoading ||
                  (workTTSStatus.last_job_status === 'queued' || workTTSStatus.last_job_status === 'running')
                "
                @click="handleEnqueueTTS"
              >
                <v-icon start>mdi-play</v-icon>
                {{
                  workTTSStatus.has_tts_audiobook || workTTSStatus.last_job_status
                    ? '重新生成 TTS 有声书'
                    : '生成 TTS 有声书'
                }}
              </v-btn>

              <v-btn
                v-if="workTTSStatus.last_job_status === 'queued' || workTTSStatus.last_job_status === 'running'"
                variant="text"
                disabled
                size="small"
              >
                任务进行中...
              </v-btn>

              <v-btn
                variant="text"
                icon
                size="small"
                @click="loadTTSStatus"
              >
                <v-icon>mdi-refresh</v-icon>
              </v-btn>
            </div>

            <!-- 提示信息 -->
            <v-alert
              type="info"
              variant="tonal"
              density="compact"
              class="mt-2"
            >
              <div class="text-caption">
                长篇小说会耗时较久，且受 TTS 限流影响。生成完成后，有声书将自动出现在下方列表中。
              </div>
            </v-alert>
          </div>

          <!-- 无状态信息 -->
          <div v-else-if="!ttsStatusLoading" class="text-body-2 text-medium-emphasis">
            暂无 TTS 状态信息
          </div>
        </v-card-text>
      </v-card>

      <!-- 有声书播放器 -->
      <v-card class="mb-6" v-if="audiobookStatus && audiobookStatus.has_audiobook">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-headphones</v-icon>
          <span>有声书播放器</span>
          <v-chip size="small" color="warning" class="ml-2">实验性</v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-row>
            <!-- 左侧：章节列表 -->
            <v-col cols="12" md="5">
              <div class="text-subtitle-2 mb-2">章节列表</div>
              <v-list density="compact" max-height="400" style="overflow-y: auto;">
                <v-list-item
                  v-for="chapter in audiobookStatus.chapters"
                  :key="chapter.file_id"
                  :active="currentFileId === chapter.file_id"
                  @click="handleChapterClick(chapter.file_id)"
                  class="cursor-pointer"
                >
                  <template v-slot:prepend>
                    <v-icon>mdi-play-circle-outline</v-icon>
                  </template>
                  <v-list-item-title>
                    {{ chapter.title }}
                    <v-chip
                      v-if="chapter.is_tts_generated"
                      size="x-small"
                      color="info"
                      variant="flat"
                      class="ml-2"
                    >
                      TTS
                    </v-chip>
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ formatDuration(chapter.duration_seconds || 0) }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>

            <!-- 右侧：播放器控制 -->
            <v-col cols="12" md="7">
              <div v-if="currentChapter">
                <div class="text-subtitle-2 mb-2">当前章节：{{ currentChapter.title }}</div>
                
                <!-- 音频播放器 -->
                <audio
                  ref="audioEl"
                  :src="currentAudioSrc"
                  @timeupdate="onTimeUpdate"
                  @ended="onEnded"
                  @loadedmetadata="onLoadedMetadata"
                  controls
                  class="mb-4"
                  style="width: 100%;"
                />

                <!-- 播放进度信息 -->
                <div class="mb-2">
                  <div class="text-body-2 text-medium-emphasis">
                    进度：{{ formatTime(currentPosition) }} / {{ formatTime(currentDuration) }}
                    <span v-if="currentChapter.duration_seconds">
                      ({{ Math.round((currentPosition / currentDuration) * 100) }}%)
                    </span>
                  </div>
                </div>

                <!-- 播放速度控制 -->
                <div class="d-flex align-center gap-2 mb-3">
                  <span class="text-body-2 text-medium-emphasis">播放速度：</span>
                  <v-btn-toggle
                    v-model="playbackRate"
                    mandatory
                    density="compact"
                    @update:model-value="handlePlaybackRateChange"
                  >
                    <v-btn size="small" :value="0.75">0.75x</v-btn>
                    <v-btn size="small" :value="1">1x</v-btn>
                    <v-btn size="small" :value="1.25">1.25x</v-btn>
                    <v-btn size="small" :value="1.5">1.5x</v-btn>
                    <v-btn size="small" :value="2">2x</v-btn>
                  </v-btn-toggle>
                </div>

                <!-- 控制按钮 -->
                <div class="d-flex flex-wrap gap-2">
                  <v-btn
                    v-if="audiobookStatus?.current_file_id && audiobookStatus?.current_position_seconds > 0"
                    size="small"
                    color="primary"
                    variant="elevated"
                    @click="handleResumeFromLastPosition"
                  >
                    <v-icon start>mdi-play</v-icon>
                    从上次位置继续
                  </v-btn>
                  <v-btn
                    size="small"
                    variant="outlined"
                    @click="handlePreviousChapter"
                    :disabled="!hasPreviousChapter"
                  >
                    <v-icon start>mdi-skip-previous</v-icon>
                    上一章
                  </v-btn>
                  <v-btn
                    size="small"
                    variant="outlined"
                    @click="handleNextChapter"
                    :disabled="!hasNextChapter"
                  >
                    <v-icon start>mdi-skip-next</v-icon>
                    下一章
                  </v-btn>
                  <v-btn
                    size="small"
                    variant="outlined"
                    @click="handleRestartChapter"
                  >
                    <v-icon start>mdi-restart</v-icon>
                    从头开始
                  </v-btn>
                </div>

                <!-- 进度同步状态 -->
                <div v-if="isUpdatingProgress" class="mt-2">
                  <v-progress-linear indeterminate color="primary" height="2" />
                  <div class="text-caption text-medium-emphasis">同步进度中...</div>
                </div>
              </div>
              <div v-else class="text-body-2 text-medium-emphasis">
                请选择章节开始播放
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 有声书文件列表 -->
      <v-card class="mb-6" v-if="workDetail && workDetail.audiobooks && workDetail.audiobooks.length > 0">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-headphones</v-icon>
          有声书文件
          <v-chip size="small" class="ml-2" color="orange">
            {{ workDetail.audiobooks.length }}
          </v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-data-table
            :headers="audiobookFileHeaders"
            :items="workDetail.audiobooks"
            :items-per-page="10"
            class="elevation-0"
            no-data-text="暂无有声书文件"
          >
            <template v-slot:item.format="{ item }">
              <v-chip size="small" color="orange" variant="flat">
                {{ item.format?.toUpperCase() || '-' }}
              </v-chip>
            </template>
            <template v-slot:item.duration_seconds="{ item }">
              {{ item.duration_seconds ? formatDuration(item.duration_seconds) : '-' }}
            </template>
            <template v-slot:item.audio_quality="{ item }">
              <span class="text-caption">
                {{ formatAudioQuality({
                  bitrate_kbps: item.bitrate_kbps,
                  sample_rate_hz: item.sample_rate_hz,
                  channels: item.channels
                }) }}
              </span>
            </template>
            <template v-slot:item.file_size_mb="{ item }">
              {{ item.file_size_mb ? `${item.file_size_mb.toFixed(2)} MB` : '-' }}
            </template>
            <template v-slot:item.narrator="{ item }">
              <v-chip v-if="item.narrator" size="small" variant="outlined">
                {{ item.narrator }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
            <template v-slot:item.source_site_id="{ item }">
              <v-chip v-if="item.source_site_id" size="small" variant="outlined">
                {{ item.source_site_id }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
            <template v-slot:item.created_at="{ item }">
              {{ formatDate(item.created_at) }}
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>

      <!-- 相关漫画 -->
      <v-card v-if="workDetail && workDetail.comics && workDetail.comics.length > 0">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="pink">mdi-book-open-page-variant</v-icon>
          相关漫画
          <v-chip size="small" class="ml-2" color="pink">
            {{ workDetail.comics.length }}
          </v-chip>
        </v-card-title>
        <v-card-subtitle class="text-caption text-medium-emphasis">
          相关漫画基于系列名 / 标题自动匹配，可能包含误差。
        </v-card-subtitle>
        <v-divider />
        <v-card-text>
          <!-- 按卷聚合显示 -->
          <v-expansion-panels variant="accordion" class="mb-4">
            <v-expansion-panel
              v-for="comic in workDetail.comics"
              :key="comic.id"
            >
              <v-expansion-panel-title>
                <div class="d-flex align-center justify-space-between w-100">
                  <div>
                    <div class="text-body-1 font-weight-medium">
                      {{ comic.title }}
                    </div>
                    <div class="text-caption text-medium-emphasis mt-1">
                      <span v-if="comic.series">{{ comic.series }}</span>
                      <span v-if="comic.volume_index" class="ml-1">
                        · 第{{ comic.volume_index }}卷
                      </span>
                      <span v-if="comic.region" class="ml-1">· {{ comic.region }}</span>
                    </div>
                  </div>
                  <v-chip size="small" color="pink" variant="flat" class="ml-2">
                    {{ getComicFileCount(comic.id) }} 个文件
                  </v-chip>
                  <!-- Dev 模式：手动绑定按钮 -->
                  <div v-if="isDevMode" class="ml-2">
                    <v-chip
                      v-if="isIncluded('comic', comic.id)"
                      size="small"
                      color="success"
                      variant="flat"
                      class="mr-1"
                    >
                      已关联
                    </v-chip>
                    <v-chip
                      v-else-if="isExcluded('comic', comic.id)"
                      size="small"
                      color="grey"
                      variant="flat"
                      class="mr-1"
                    >
                      已忽略
                    </v-chip>
                    <v-btn
                      v-if="!isIncluded('comic', comic.id) && !isExcluded('comic', comic.id)"
                      size="x-small"
                      color="success"
                      variant="outlined"
                      class="mr-1"
                      @click.stop="handleLinkAction('include', 'comic', comic.id)"
                    >
                      标记关联
                    </v-btn>
                    <v-btn
                      v-if="!isIncluded('comic', comic.id) && !isExcluded('comic', comic.id)"
                      size="x-small"
                      color="grey"
                      variant="outlined"
                      class="mr-1"
                      @click.stop="handleLinkAction('exclude', 'comic', comic.id)"
                    >
                      忽略
                    </v-btn>
                    <v-btn
                      v-if="isIncluded('comic', comic.id) || isExcluded('comic', comic.id)"
                      size="x-small"
                      color="error"
                      variant="text"
                      @click.stop="handleLinkAction('delete', 'comic', comic.id)"
                    >
                      取消
                    </v-btn>
                  </div>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <!-- 漫画基本信息 -->
                <div class="mb-4">
                  <div class="d-flex flex-wrap gap-4 mb-2">
                    <div v-if="comic.author" class="d-flex align-center">
                      <v-icon size="small" class="mr-1">mdi-account</v-icon>
                      <span class="text-body-2">作者：{{ comic.author }}</span>
                    </div>
                    <div v-if="comic.illustrator" class="d-flex align-center">
                      <v-icon size="small" class="mr-1">mdi-draw-pen</v-icon>
                      <span class="text-body-2">作画：{{ comic.illustrator }}</span>
                    </div>
                    <div v-if="comic.publish_year" class="d-flex align-center">
                      <v-icon size="small" class="mr-1">mdi-calendar</v-icon>
                      <span class="text-body-2">{{ comic.publish_year }}</span>
                    </div>
                  </div>
                </div>
                
                <!-- 漫画文件列表 -->
                <v-data-table
                  :headers="comicFileHeaders"
                  :items="getComicFilesForComic(comic.id)"
                  :items-per-page="10"
                  class="elevation-0"
                  no-data-text="暂无文件"
                >
                  <template v-slot:item.format="{ item }">
                    <v-chip size="small" color="pink" variant="flat">
                      {{ item.format?.toUpperCase() || '-' }}
                    </v-chip>
                  </template>
                  <template v-slot:item.file_size_mb="{ item }">
                    {{ item.file_size_mb ? `${item.file_size_mb.toFixed(2)} MB` : '-' }}
                  </template>
                  <template v-slot:item.page_count="{ item }">
                    {{ item.page_count ? `${item.page_count} 页` : '-' }}
                  </template>
                  <template v-slot:item.source_site_id="{ item }">
                    <v-chip v-if="item.source_site_id" size="small" variant="outlined">
                      {{ item.source_site_id }}
                    </v-chip>
                    <span v-else class="text-medium-emphasis">-</span>
                  </template>
                  <template v-slot:item.created_at="{ item }">
                    {{ formatDate(item.created_at) }}
                  </template>
                </v-data-table>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
      </v-card>

      <!-- 相关视频改编 -->
      <v-card v-if="workDetail && workDetail.videos && workDetail.videos.length > 0" class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-movie</v-icon>
          相关影视改编
          <v-chip size="small" class="ml-2" color="primary">
            {{ workDetail.videos.length }}
          </v-chip>
        </v-card-title>
        <v-card-subtitle class="text-caption text-medium-emphasis">
          根据作品标题/系列名自动匹配，结果仅供参考，可能包含误匹配。
        </v-card-subtitle>
        <v-divider />
        <v-card-text>
          <v-data-table
            :headers="videoHeaders"
            :items="workDetail.videos"
            :items-per-page="10"
            class="elevation-0"
            no-data-text="暂无相关视频"
          >
            <template v-slot:item.media_type="{ item }">
              <v-chip size="small" :color="getMediaTypeColor(item.media_type)" variant="flat">
                <v-icon start size="small">{{ getMediaTypeIcon(item.media_type) }}</v-icon>
                {{ getMediaTypeLabel(item.media_type) }}
              </v-chip>
            </template>
            <template v-slot:item.title="{ item }">
              <div>
                <div class="text-body-2 font-weight-medium">{{ item.title }}</div>
                <div v-if="item.original_title" class="text-caption text-medium-emphasis">
                  {{ item.original_title }}
                </div>
              </div>
            </template>
            <template v-slot:item.year="{ item }">
              {{ item.year || '-' }}
            </template>
            <template v-slot:item.rating="{ item }">
              <div v-if="item.rating" class="d-flex align-center">
                <v-icon size="small" color="warning" class="mr-1">mdi-star</v-icon>
                <span>{{ item.rating.toFixed(1) }}</span>
              </div>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
            <template v-slot:item.poster_url="{ item }">
              <v-img
                v-if="item.poster_url"
                :src="item.poster_url"
                width="60"
                height="90"
                cover
                class="rounded"
              />
              <v-icon v-else size="small" color="grey">mdi-image-off</v-icon>
            </template>
            <!-- Dev 模式：手动绑定按钮 -->
            <template v-if="isDevMode" v-slot:item.actions="{ item }">
              <div class="d-flex align-center gap-1">
                <v-chip
                  v-if="isIncluded('video', item.id)"
                  size="small"
                  color="success"
                  variant="flat"
                >
                  已关联
                </v-chip>
                <v-chip
                  v-else-if="isExcluded('video', item.id)"
                  size="small"
                  color="grey"
                  variant="flat"
                >
                  已忽略
                </v-chip>
                <v-btn
                  v-if="!isIncluded('video', item.id) && !isExcluded('video', item.id)"
                  size="x-small"
                  color="success"
                  variant="outlined"
                  @click="handleLinkAction('include', 'video', item.id)"
                >
                  标记关联
                </v-btn>
                <v-btn
                  v-if="!isIncluded('video', item.id) && !isExcluded('video', item.id)"
                  size="x-small"
                  color="grey"
                  variant="outlined"
                  @click="handleLinkAction('exclude', 'video', item.id)"
                >
                  忽略
                </v-btn>
                <v-btn
                  v-if="isIncluded('video', item.id) || isExcluded('video', item.id)"
                  size="x-small"
                  color="error"
                  variant="text"
                  @click="handleLinkAction('delete', 'video', item.id)"
                >
                  取消
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>

      <!-- 相关音乐 -->
      <v-card v-if="workDetail && workDetail.music && workDetail.music.length > 0" class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="teal">mdi-music</v-icon>
          相关音乐 / OST
          <v-chip size="small" class="ml-2" color="teal">
            {{ workDetail.music.length }}
          </v-chip>
        </v-card-title>
        <v-card-subtitle class="text-caption text-medium-emphasis">
          根据作品标题/系列名/作者自动匹配，结果仅供参考。
        </v-card-subtitle>
        <v-divider />
        <v-card-text>
          <v-data-table
            :headers="musicHeaders"
            :items="workDetail.music"
            :items-per-page="10"
            class="elevation-0"
            no-data-text="暂无相关音乐"
          >
            <template v-slot:item.title="{ item }">
              <div class="text-body-2 font-weight-medium">{{ item.title }}</div>
            </template>
            <template v-slot:item.artist="{ item }">
              <v-chip v-if="item.artist" size="small" variant="outlined">
                {{ item.artist }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
            <template v-slot:item.album="{ item }">
              {{ item.album || '-' }}
            </template>
            <template v-slot:item.year="{ item }">
              {{ item.year || '-' }}
            </template>
            <template v-slot:item.genre="{ item }">
              <v-chip v-if="item.genre" size="small" variant="outlined" color="teal">
                {{ item.genre }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
            <!-- Dev 模式：手动绑定按钮 -->
            <template v-if="isDevMode" v-slot:item.actions="{ item }">
              <div class="d-flex align-center gap-1">
                <v-chip
                  v-if="isIncluded('music', item.id)"
                  size="small"
                  color="success"
                  variant="flat"
                >
                  已关联
                </v-chip>
                <v-chip
                  v-else-if="isExcluded('music', item.id)"
                  size="small"
                  color="grey"
                  variant="flat"
                >
                  已忽略
                </v-chip>
                <v-btn
                  v-if="!isIncluded('music', item.id) && !isExcluded('music', item.id)"
                  size="x-small"
                  color="success"
                  variant="outlined"
                  @click="handleLinkAction('include', 'music', item.id)"
                >
                  标记关联
                </v-btn>
                <v-btn
                  v-if="!isIncluded('music', item.id) && !isExcluded('music', item.id)"
                  size="x-small"
                  color="grey"
                  variant="outlined"
                  @click="handleLinkAction('exclude', 'music', item.id)"
                >
                  忽略
                </v-btn>
                <v-btn
                  v-if="isIncluded('music', item.id) || isExcluded('music', item.id)"
                  size="x-small"
                  color="error"
                  variant="text"
                  @click="handleLinkAction('delete', 'music', item.id)"
                >
                  取消
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { workApi, workLinksApi, devTTSApi, devTTSJobsApi, devTTSWorkProfileApi, devTTSVoicePresetsApi, ttsUserApi, userNotificationsApi, audiobookUserApi } from '@/services/api'
import type { WorkComicFile, WorkLink, WorkTargetType } from '@/types/work'
import type { TTSJob, TTSWorkProfile, TTSVoicePreset, UserWorkTTSStatus, UserWorkAudiobookStatus, UserAudiobookChapter } from '@/types/tts'
import type { UserNotificationItem } from '@/types/notify'
import { formatDuration, formatAudioQuality, formatRelativeTime } from '@/utils/formatters'
import PageHeader from '@/components/common/PageHeader.vue'

// Dev 模式控制
const isDevMode = import.meta.env.DEV || import.meta.env.VITE_DEV_MODE === 'true'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(false)
const error = ref<string | null>(null)
// 为了兼容后端返回的 videos/music/links 等扩展字段，这里使用 any 放宽类型
const workDetail = ref<any | null>(null)
const links = ref<WorkLink[]>([])
const regenLoading = ref(false)
const snackbar = ref(false)

// TTS 用户流程状态
const workTTSStatus = ref<UserWorkTTSStatus | null>(null)
const ttsStatusLoading = ref(false)
const ttsEnqueueLoading = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref<'success' | 'error' | 'warning'>('success')
// const regenConfirmDialog = ref(false) // 暂未使用
const ttsJobs = ref<TTSJob[]>([])
const jobsLoading = ref(false)
const createJobLoading = ref(false)
const ttsProfile = ref<TTSWorkProfile | null>(null)
const ttsProfileLoading = ref(false)
const ttsProfileSaving = ref(false)
const ttsProfileDeleting = ref(false)
const voicePresets = ref<TTSVoicePreset[]>([])
const voicePresetsLoading = ref(false)
const ttsProfileForm = ref({
  preset_id: null as number | null,
  provider: '',
  language: '',
  voice: '',
  speed: null as number | null,
  pitch: null as number | null,
  enabled: true,
  notes: ''
})

// TTS 通知状态
const ttsNotification = ref<UserNotificationItem | null>(null)
const ttsNotificationLoading = ref(false)

// 有声书播放状态
const audiobookStatus = ref<UserWorkAudiobookStatus | null>(null)
const audiobookStatusLoading = ref(false)
const currentFileId = ref<number | null>(null)
const audioEl = ref<HTMLAudioElement | null>(null)
const currentPosition = ref(0)
const currentDuration = ref(0)
const isUpdatingProgress = ref(false)
let lastProgressSentAt = 0

// 播放速度
const playbackRate = ref(1)

// 计算属性
const work = computed(() => workDetail.value?.ebook || null)

const workSubtitle = computed(() => {
  if (!work.value) return ''
  const parts: string[] = []
  if (work.value.author) parts.push(work.value.author)
  if (work.value.series) {
    parts.push(work.value.series)
    if (work.value.volume_index) {
      parts.push(`第${work.value.volume_index}卷`)
    }
  }
  return parts.join(' · ')
})

const ebookFiles = computed(() => workDetail.value?.ebook_files || [])

// 小说源信息（Dev 模式）
const novelSource = computed(() => {
  if (!work.value?.extra_metadata) return null
  return work.value.extra_metadata.novel_source || null
})

const canRegenTTS = computed(() => {
  return isDevMode && !!novelSource.value && novelSource.value.type === 'local_txt'
})

// 表格列定义
const ebookFileHeaders = [
  { title: '格式', key: 'format', sortable: true },
  { title: '文件大小', key: 'file_size_mb', sortable: true },
  { title: '来源站点', key: 'source_site_id', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true }
]

const audiobookFileHeaders = [
  { title: '格式', key: 'format', sortable: true },
  { title: '时长', key: 'duration_seconds', sortable: true },
  { title: '音质', key: 'audio_quality', sortable: false },
  { title: '文件大小', key: 'file_size_mb', sortable: true },
  { title: '朗读者', key: 'narrator', sortable: false },
  { title: '标记', key: 'flags', sortable: false },
  { title: '来源站点', key: 'source_site_id', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true }
]

const comicFileHeaders = [
  { title: '格式', key: 'format', sortable: true },
  { title: '文件大小', key: 'file_size_mb', sortable: true },
  { title: '页数', key: 'page_count', sortable: true },
  { title: '来源站点', key: 'source_site_id', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true }
]

const videoHeaders = [
  { title: '类型', key: 'media_type', sortable: true },
  { title: '标题', key: 'title', sortable: true },
  { title: '年份', key: 'year', sortable: true },
  { title: '评分', key: 'rating', sortable: true },
  { title: '海报', key: 'poster_url', sortable: false },
  ...(isDevMode ? [{ title: '操作', key: 'actions', sortable: false }] : [])
]

const musicHeaders = [
  { title: '曲目名', key: 'title', sortable: true },
  { title: '艺术家', key: 'artist', sortable: true },
  { title: '专辑名', key: 'album', sortable: true },
  { title: '年份', key: 'year', sortable: true },
  { title: '风格', key: 'genre', sortable: true },
  ...(isDevMode ? [{ title: '操作', key: 'actions', sortable: false }] : [])
]

// 获取漫画的文件数量
const getComicFileCount = (comicId: number): number => {
  if (!workDetail.value) return 0
  return workDetail.value.comic_files.filter((cf: any) => cf.comic_id === comicId).length
}

// 获取指定漫画的文件列表
const getComicFilesForComic = (comicId: number): WorkComicFile[] => {
  if (!workDetail.value) return []
  return workDetail.value.comic_files.filter((cf: any) => cf.comic_id === comicId)
}

// 加载作品信息
const loadWork = async (ebookId: number) => {
  loading.value = true
  error.value = null

  try {
    const response = await workApi.getWorkDetail(ebookId)
    const data: any = response.data
    workDetail.value = data
    // 更新 links（如果响应中包含）
    if (data.links) {
      links.value = data.links
    } else {
      // 如果没有，单独加载
      if (isDevMode) {
      try {
        const linksResponse = await workLinksApi.listByEbook(ebookId)
        links.value = linksResponse.data || []
        } catch (err) {
          console.warn('加载 WorkLink 失败:', err)
          links.value = []
        }
      }
    }
    
    // 加载 TTS 状态
    await loadTTSStatus()
    // 加载 TTS 通知
    await loadTTSNotification()
    // 加载有声书播放状态
    await loadAudiobookStatus()
  } catch (err: any) {
    error.value = err.response?.data?.error_message || 
                 err.response?.data?.message || 
                 err.message || 
                 '加载失败，请稍后重试'
    console.error('加载作品详情失败:', err)
  } finally {
    loading.value = false
  }
}

// 加载 TTS 状态
const loadTTSStatus = async () => {
  if (!work.value?.id) return
  
  ttsStatusLoading.value = true
  try {
    const status = await ttsUserApi.getStatusByEbook(work.value.id)
    workTTSStatus.value = status
  } catch (err: any) {
    console.warn('加载 TTS 状态失败:', err)
    // 不显示错误，静默失败
    workTTSStatus.value = null
  } finally {
    ttsStatusLoading.value = false
  }
}

// 加载 TTS 通知
const loadTTSNotification = async () => {
  if (!work.value?.id) return
  
  ttsNotificationLoading.value = true
  try {
    const response = await userNotificationsApi.getRecent(50)
    const items: any[] = response.items as any[]
    // 查找该作品最近的 TTS 通知（根据约定的 TTS_* 类型和 ebook_id）
    const ebookNotifications = items.filter(n =>
      n.ebook_id === work.value?.id &&
      (n.type === 'TTS_JOB_COMPLETED' || n.type === 'TTS_JOB_FAILED' || n.type === 'AUDIOBOOK_READY')
    )
    if (ebookNotifications.length > 0) {
      ttsNotification.value = ebookNotifications[0] as UserNotificationItem
    } else {
      ttsNotification.value = null
    }
  } catch (err: any) {
    console.warn('加载 TTS 通知失败:', err)
    // 不显示错误，静默失败
    ttsNotification.value = null
  } finally {
    ttsNotificationLoading.value = false
  }
}

// 处理通知提示点击
const handleNotificationChipClick = () => {
  // 导航到 TTS Center
  router.push('/tts-center')
}

// 获取通知提示文本（这里使用 any 放宽类型，兼容不同通知结构）
const getNotificationChipText = (notification: any): string => {
  const timeStr = formatRelativeTime(notification.created_at || '')
  const msg: string = notification.message || ''
  if (notification.type === 'TTS_JOB_COMPLETED' || notification.type === 'AUDIOBOOK_READY') {
    return `上次生成成功（${timeStr}）`
  } else if (notification.type === 'TTS_JOB_PARTIAL') {
    return `上次部分生成完成（${timeStr}）`
  } else if (notification.type === 'TTS_JOB_FAILED') {
    const errorMsg = msg.length > 20 ? msg.substring(0, 20) + '...' : msg
    return `上次生成失败：${errorMsg}（${timeStr}）`
  }
  return `TTS 任务通知（${timeStr}）`
}

// 获取通知严重程度对应的颜色
const getNotificationSeverityColor = (severity: string): string => {
  const colors: Record<string, string> = {
    success: 'success',
    warning: 'warning',
    error: 'error',
    info: 'info'
  }
  return colors[severity] || 'default'
}

// 创建/重新生成 TTS Job
const handleEnqueueTTS = async () => {
  if (!work.value?.id) return
  
  ttsEnqueueLoading.value = true
  try {
    const response = await ttsUserApi.enqueueForWork(work.value.id)
    
    if (response.success) {
      // 更新本地状态
      if (workTTSStatus.value) {
        workTTSStatus.value.last_job_status = 'queued'
        workTTSStatus.value.last_job_requested_at = new Date().toISOString()
      }
      
      // 显示成功提示
      snackbarMessage.value = response.message || '已加入 TTS 队列'
      snackbarColor.value = 'success'
      snackbar.value = true
      
      // 刷新状态
      setTimeout(() => {
        loadTTSStatus()
      }, 1000)
    } else {
      snackbarMessage.value = response.message || '操作失败'
      snackbarColor.value = 'error'
      snackbar.value = true
    }
  } catch (err: any) {
    console.error('创建 TTS Job 失败:', err)
    snackbarMessage.value = err.response?.data?.detail || err.message || '操作失败'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    ttsEnqueueLoading.value = false
  }
}

// TTS 状态显示辅助函数
const getTTSStatusColor = (status?: string): string => {
  const colors: Record<string, string> = {
    queued: 'info',
    running: 'primary',
    partial: 'warning',
    success: 'success',
    failed: 'error'
  }
  return colors[status || ''] || 'default'
}

const getTTSStatusIcon = (status?: string): string => {
  const icons: Record<string, string> = {
    queued: 'mdi-clock-outline',
    running: 'mdi-play-circle',
    partial: 'mdi-alert-circle',
    success: 'mdi-check-circle',
    failed: 'mdi-alert-circle'
  }
  return icons[status || ''] || 'mdi-help-circle'
}

const getTTSStatusLabel = (status?: string): string => {
  const labels: Record<string, string> = {
    queued: '队列中',
    running: '生成中',
    partial: '部分完成',
    success: '已完成',
    failed: '执行失败'
  }
  return labels[status || ''] || status || '未知'
}

const getTTSStatusAlertType = (status?: string): 'info' | 'warning' | 'error' | 'success' => {
  if (status === 'failed') return 'error'
  if (status === 'partial') return 'warning'
  if (status === 'success') return 'success'
  return 'info'
}

// WorkLink 辅助函数
const getLinkFor = (targetType: WorkTargetType, targetId: number): WorkLink | undefined => {
  return links.value.find(
    link => link.target_type === targetType && link.target_id === targetId
  )
}

const isIncluded = (targetType: WorkTargetType, targetId: number): boolean => {
  const link = getLinkFor(targetType, targetId)
  return link?.relation === "include"
}

const isExcluded = (targetType: WorkTargetType, targetId: number): boolean => {
  const link = getLinkFor(targetType, targetId)
  return link?.relation === "exclude"
}

// 手动绑定操作
const handleLinkAction = async (
  action: "include" | "exclude" | "delete",
  targetType: WorkTargetType,
  targetId: number
) => {
  if (!workDetail.value) return
  
  try {
    if (action === "delete") {
      const link = getLinkFor(targetType, targetId)
      if (link) {
        await workLinksApi.delete(link.id)
        links.value = links.value.filter(l => l.id !== link.id)
      }
    } else {
      const response = await workLinksApi.createOrUpdate({
        ebook_id: workDetail.value.ebook.id,
        target_type: targetType,
        target_id: targetId,
        relation: action
      })
      
      // 更新 links 列表
      const existingIndex = links.value.findIndex(
        l => l.target_type === targetType && l.target_id === targetId
      )
      if (existingIndex >= 0) {
        links.value[existingIndex] = response.data
      } else {
        links.value.push(response.data)
      }
    }
    
    // 重新加载作品详情以更新显示
    await loadWork(workDetail.value.ebook.id)
  } catch (err: any) {
    console.error('操作失败:', err)
    alert(err.response?.data?.error_message || err.message || '操作失败')
  }
}

// 解析标签
const parseTags = (tags: string | null): string[] => {
  if (!tags) return []
  // 支持 JSON 数组或逗号分隔字符串
  try {
    const parsed = JSON.parse(tags)
    if (Array.isArray(parsed)) return parsed
  } catch {
    // 不是 JSON，按逗号分隔
    return tags.split(',').map(t => t.trim()).filter(t => t)
  }
  return []
}

// 格式化日期
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateString
  }
}

// 获取媒体类型标签
const getMediaTypeLabel = (mediaType: string): string => {
  const labels: Record<string, string> = {
    movie: '电影',
    tv: '剧集',
    anime: '动漫',
    short_drama: '短剧'
  }
  return labels[mediaType] || mediaType
}

// 获取媒体类型图标
const getMediaTypeIcon = (mediaType: string): string => {
  const icons: Record<string, string> = {
    movie: 'mdi-movie',
    tv: 'mdi-television',
    anime: 'mdi-animation',
    short_drama: 'mdi-television-classic'
  }
  return icons[mediaType] || 'mdi-file'
}

// 获取媒体类型颜色
const getMediaTypeColor = (mediaType: string): string => {
  const colors: Record<string, string> = {
    movie: 'primary',
    tv: 'info',
    anime: 'purple',
    short_drama: 'indigo'
  }
  return colors[mediaType] || 'grey'
}

// Dev TTS 辅助函数（兼容旧模板引用）
const handleRegenTTS = async () => {
  if (!work.value) return
  try {
    await devTTSApi.regenForWork(work.value.id)
    snackbarMessage.value = '已触发 TTS 重新生成任务（Dev）'
    snackbarColor.value = 'success'
    snackbar.value = true
  } catch (err: any) {
    console.error('Dev TTS 重新生成失败:', err)
    snackbarMessage.value = err.response?.data?.message || err.message || '操作失败'
    snackbarColor.value = 'error'
    snackbar.value = true
  }
}

const getJobStatusColor = (status: string): string => {
  return getTTSStatusColor(status)
}

const getJobStatusLabel = (status: string): string => {
  return getTTSStatusLabel(status)
}

const formatDateTime = (dateString: string): string => {
  return formatDate(dateString)
}

const handleCreateJob = async () => {
  if (!work.value) return
  createJobLoading.value = true
  try {
    await devTTSJobsApi.enqueueForWork(work.value.id)
    snackbarMessage.value = '已创建 Dev TTS Job'
    snackbarColor.value = 'success'
    snackbar.value = true
  } catch (err: any) {
    console.error('创建 Dev TTS Job 失败:', err)
    snackbarMessage.value = err.response?.data?.message || err.message || '创建失败'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    createJobLoading.value = false
  }
}

// 加载有声书播放状态
const loadAudiobookStatus = async () => {
  if (!workDetail.value?.ebook?.id) return
  
  audiobookStatusLoading.value = true
  try {
    const status = await audiobookUserApi.getWorkStatus(workDetail.value.ebook.id)
    audiobookStatus.value = status
    
    // 设置当前文件 ID
    if (status.has_audiobook) {
      currentFileId.value = status.current_file_id ?? status.chapters[0]?.file_id ?? null
    }
  } catch (err: any) {
    console.error('加载有声书状态失败:', err)
    audiobookStatus.value = null
  } finally {
    audiobookStatusLoading.value = false
  }
}

// 计算属性：当前章节
const currentChapter = computed<UserAudiobookChapter | null>(() => {
  if (!audiobookStatus.value || !currentFileId.value) return null
  return audiobookStatus.value.chapters.find(c => c.file_id === currentFileId.value) || null
})

// 计算属性：当前音频源
const currentAudioSrc = computed(() => {
  if (!currentChapter.value) return ''
  return audiobookUserApi.getFileStreamUrl(currentChapter.value.file_id)
})

// 计算属性：是否有上一章/下一章
const hasPreviousChapter = computed(() => {
  if (!audiobookStatus.value || !currentChapter.value) return false
  const idx = audiobookStatus.value.chapters.findIndex(c => c.file_id === currentChapter.value!.file_id)
  return idx > 0
})

const hasNextChapter = computed(() => {
  if (!audiobookStatus.value || !currentChapter.value) return false
  const idx = audiobookStatus.value.chapters.findIndex(c => c.file_id === currentChapter.value!.file_id)
  return idx >= 0 && idx < audiobookStatus.value.chapters.length - 1
})

// 格式化时间（秒转 MM:SS 或 HH:MM:SS）
const formatTime = (seconds: number): string => {
  if (seconds < 0 || !isFinite(seconds)) return '00:00'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  } else {
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
}

// 章节点击处理
const handleChapterClick = (fileId: number) => {
  currentFileId.value = fileId
  currentPosition.value = 0
  // 音频元素会自动切换 src，但需要等待加载
  if (audioEl.value) {
    audioEl.value.load()
  }
}

// 上一章
const handlePreviousChapter = () => {
  if (!audiobookStatus.value || !currentChapter.value) return
  const chapters = audiobookStatus.value.chapters
  const idx = chapters.findIndex(c => c.file_id === currentChapter.value!.file_id)
  if (idx > 0) {
    handleChapterClick(chapters[idx - 1].file_id)
  }
}

// 下一章
const handleNextChapter = () => {
  if (!audiobookStatus.value || !currentChapter.value) return
  const chapters = audiobookStatus.value.chapters
  const idx = chapters.findIndex(c => c.file_id === currentChapter.value!.file_id)
  if (idx >= 0 && idx < chapters.length - 1) {
    handleChapterClick(chapters[idx + 1].file_id)
  }
}

// 从头开始
const handleRestartChapter = () => {
  if (audioEl.value) {
    audioEl.value.currentTime = 0
    currentPosition.value = 0
  }
}

// 播放速度变化
const handlePlaybackRateChange = (rate: number) => {
  if (audioEl.value) {
    audioEl.value.playbackRate = rate
  }
}

// 从上次位置继续
const handleResumeFromLastPosition = () => {
  if (!audiobookStatus.value) return
  
  // 跳转到上次播放的章节
  const lastFileId = audiobookStatus.value.current_file_id
  if (lastFileId) {
    currentFileId.value = lastFileId
    // 等待音频加载后会自动跳转到保存的位置（onLoadedMetadata 处理）
    if (audioEl.value) {
      audioEl.value.load()
      audioEl.value.play()
    }
  }
}

// 音频加载元数据后，跳转到上次播放位置
const onLoadedMetadata = () => {
  if (!audioEl.value || !audiobookStatus.value) return
  
  // 如果当前章节有保存的进度，跳转到该位置
  if (currentChapter.value && currentFileId.value === audiobookStatus.value.current_file_id) {
    const savedPosition = audiobookStatus.value.current_position_seconds || 0
    if (savedPosition > 0 && savedPosition < audioEl.value.duration) {
      audioEl.value.currentTime = savedPosition
      currentPosition.value = savedPosition
    }
  }
  
  // 更新总时长
  if (audioEl.value.duration) {
    currentDuration.value = audioEl.value.duration
  }
}

// 时间更新事件（节流更新进度）
const onTimeUpdate = async () => {
  if (!audioEl.value || !audiobookStatus.value || !currentChapter.value || !workDetail.value) return
  
  const now = Date.now()
  if (now - lastProgressSentAt < 3000) {
    // 3 秒内只更新本地显示，不发送到服务器
    currentPosition.value = audioEl.value.currentTime
    return
  }
  
  lastProgressSentAt = now
  currentPosition.value = audioEl.value.currentTime
  
  const position = Math.floor(audioEl.value.currentTime)
  const duration = Math.floor(audioEl.value.duration || currentChapter.value.duration_seconds || 0)
  
  try {
    isUpdatingProgress.value = true
    const updated = await audiobookUserApi.updateWorkProgress(workDetail.value.ebook.id, {
      audiobook_file_id: currentChapter.value.file_id,
      position_seconds: position,
      duration_seconds: duration || undefined,
    })
    audiobookStatus.value = updated
  } catch (err: any) {
    console.error('更新播放进度失败:', err)
  } finally {
    isUpdatingProgress.value = false
  }
}

// 播放结束事件（自动下一章）
const onEnded = () => {
  if (!audiobookStatus.value || !currentChapter.value) return
  const chapters = audiobookStatus.value.chapters
  const idx = chapters.findIndex(c => c.file_id === currentChapter.value!.file_id)
  if (idx >= 0 && idx < chapters.length - 1) {
    handleChapterClick(chapters[idx + 1].file_id)
    // 自动播放下一章
    if (audioEl.value) {
      audioEl.value.play().catch(err => {
        console.warn('自动播放下一章失败:', err)
      })
    }
  }
}

// 监听路由参数变化
watch(
  () => route.params.ebookId,
  (newId) => {
    if (newId) {
      const ebookId = parseInt(newId as string, 10)
      if (!isNaN(ebookId)) {
        loadWork(ebookId)
      }
    }
  },
  { immediate: true }
)

// 加载预设列表
const loadVoicePresets = async () => {
  if (!isDevMode) return
  
  voicePresetsLoading.value = true
  try {
    voicePresets.value = await devTTSVoicePresetsApi.list()
  } catch (err: any) {
    console.error('加载预设列表失败:', err)
    voicePresets.value = []
  } finally {
    voicePresetsLoading.value = false
  }
}

// TTS Profile 相关函数
const loadTTSProfile = async (ebookId: number) => {
  if (!isDevMode) return
  
  ttsProfileLoading.value = true
  try {
    const profile = await devTTSWorkProfileApi.getForWork(ebookId)
    ttsProfile.value = profile
    if (profile) {
      // 填充表单
      ttsProfileForm.value = {
        preset_id: profile.preset_id ?? null,
        provider: profile.provider || '',
        language: profile.language || '',
        voice: profile.voice || '',
        speed: profile.speed ?? null,
        pitch: profile.pitch ?? null,
        enabled: profile.enabled,
        notes: profile.notes || ''
      }
    } else {
      // 重置表单
      ttsProfileForm.value = {
        preset_id: null,
        provider: '',
        language: '',
        voice: '',
        speed: null,
        pitch: null,
        enabled: true,
        notes: ''
      }
    }
  } catch (err: any) {
    console.error('加载 TTS Profile 失败:', err)
    ttsProfile.value = null
  } finally {
    ttsProfileLoading.value = false
  }
}

// 从预设填充字段
const handleFillFromPreset = () => {
  if (!ttsProfileForm.value.preset_id) return
  
  const preset = voicePresets.value.find(p => p.id === ttsProfileForm.value.preset_id)
  if (!preset) return
  
  // 填充预设的参数（只填充非空字段）
  if (preset.provider) ttsProfileForm.value.provider = preset.provider
  if (preset.language) ttsProfileForm.value.language = preset.language
  if (preset.voice) ttsProfileForm.value.voice = preset.voice
  if (preset.speed !== null) ttsProfileForm.value.speed = preset.speed ?? null
  if (preset.pitch !== null) ttsProfileForm.value.pitch = preset.pitch ?? null
}

// 获取预设名称
const getPresetName = (presetId: number | null): string => {
  if (!presetId) return '-'
  const preset = voicePresets.value.find(p => p.id === presetId)
  return preset?.name || `ID: ${presetId}`
}

const handleSaveTTSProfile = async () => {
  if (!work.value) return
  
  ttsProfileSaving.value = true
  try {
    const payload = {
      ebook_id: work.value.id,
      preset_id: ttsProfileForm.value.preset_id ?? null,
      provider: ttsProfileForm.value.provider || null,
      language: ttsProfileForm.value.language || null,
      voice: ttsProfileForm.value.voice || null,
      speed: ttsProfileForm.value.speed ?? null,
      pitch: ttsProfileForm.value.pitch ?? null,
      enabled: ttsProfileForm.value.enabled,
      notes: ttsProfileForm.value.notes || null
    }
    
    const saved = await devTTSWorkProfileApi.upsert(payload)
    ttsProfile.value = saved
    snackbarMessage.value = '已保存作品 TTS Profile'
    snackbarColor.value = 'success'
    snackbar.value = true
  } catch (err: any) {
    console.error('保存 TTS Profile 失败:', err)
    snackbarMessage.value = err.response?.data?.message || err.message || '保存失败'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    ttsProfileSaving.value = false
  }
}

const handleDeleteTTSProfile = async () => {
  if (!work.value || !ttsProfile.value) return
  
  if (!confirm('确定要清除此作品的 TTS Profile 吗？')) return
  
  ttsProfileDeleting.value = true
  try {
    await devTTSWorkProfileApi.delete(work.value.id)
    ttsProfile.value = null
    ttsProfileForm.value = {
      preset_id: null,
      provider: '',
      language: '',
      voice: '',
      speed: null,
      pitch: null,
      enabled: true,
      notes: ''
    }
    snackbarMessage.value = '已清除作品 TTS Profile'
    snackbarColor.value = 'success'
    snackbar.value = true
  } catch (err: any) {
    console.error('删除 TTS Profile 失败:', err)
    snackbarMessage.value = err.response?.data?.message || err.message || '删除失败'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    ttsProfileDeleting.value = false
  }
}

// 初始化
onMounted(() => {
  const ebookId = route.params.ebookId
  if (ebookId) {
    const id = parseInt(ebookId as string, 10)
    if (!isNaN(id)) {
      loadWork(id)
      if (isDevMode) {
        loadTTSProfile(id)
        loadVoicePresets()
      }
    } else {
      error.value = '无效的作品 ID'
    }
  } else {
    error.value = '缺少作品 ID'
  }
})

// 监听作品变化，重新加载 Profile 和 TTS 状态
watch(
  () => work.value?.id,
  (ebookId) => {
    if (ebookId) {
      if (isDevMode) {
        loadTTSProfile(ebookId)
      }
      loadTTSStatus()
    }
  }
)
</script>

<style lang="scss" scoped>
.work-detail-page {
  padding: 16px;
}
</style>

