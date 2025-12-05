<template>
  <div class="global-rules-settings">
    <PageHeader
      title="全局下载规则（HR / 画质 / 语言偏好）"
      subtitle="统一管理HR策略、质量过滤和文件行为"
    />

    <v-container fluid class="pa-4">
      <v-row>
        <!-- 三档模式选择卡片 -->
        <v-col cols="12">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-shield-check</v-icon>
              HR模式选择
            </v-card-title>
            
            <v-card-text>
              <!-- C档模式警告 -->
              <v-alert
                v-if="settings.hr_mode === 'C_PRO'"
                type="error"
                variant="tonal"
                class="mb-4"
                prominent
              >
                <v-alert-title class="text-error">老司机模式</v-alert-title>
                <div class="text-body-2 text-error-darken-1">
                  <strong>如使用，系统将禁用『网盘移动上传』或『本地移动保存』，避免导致保种炸雷，请谨慎使用。</strong>
                  <ul class="mt-2">
                    <li>STRM生成：允许</li>
                    <li>本地整理：仅复制/硬链接，禁止移动删除源文件</li>
                    <li>网盘整理：禁止移动上传，仅允许复制</li>
                  </ul>
                </div>
              </v-alert>

              <!-- A档模式提示 -->
              <v-alert
                v-else-if="settings.hr_mode === 'A_SAFE'"
                type="info"
                variant="tonal"
                class="mb-4"
              >
                <v-alert-title>保种安全模式</v-alert-title>
                <div class="text-body-2">
                  <ul>
                    <li>STRM允许</li>
                    <li>本地只允许复制/硬链接</li>
                    <li>网盘禁止移动上传</li>
                  </ul>
                </div>
              </v-alert>

              <!-- B档模式提示 -->
              <v-alert
                v-else-if="settings.hr_mode === 'B_BALANCED'"
                type="success"
                variant="tonal"
                class="mb-4"
              >
                <v-alert-title>平衡模式</v-alert-title>
                <div class="text-body-2">
                  <ul>
                    <li>STRM允许</li>
                    <li>本地移动允许</li>
                    <li>网盘移动允许</li>
                  </ul>
                </div>
              </v-alert>

              <!-- 模式选择按钮组 -->
              <v-btn-toggle
                :model-value="settings.hr_mode"
                mandatory
                variant="outlined"
                divided
                class="w-100"
              >
                <v-btn
                  value="A_SAFE"
                  size="large"
                  class="flex-grow-1"
                  :color="settings.hr_mode === 'A_SAFE' ? 'info' : undefined"
                  @click="selectHrMode('A_SAFE')"
                >
                  <div class="text-center">
                    <v-icon size="24" class="mb-1">mdi-shield-outline</v-icon>
                    <div class="text-h6">A档</div>
                    <div class="text-caption">保种安全</div>
                  </div>
                </v-btn>
                
                <v-btn
                  value="B_BALANCED"
                  size="large"
                  class="flex-grow-1"
                  :color="settings.hr_mode === 'B_BALANCED' ? 'success' : undefined"
                  @click="selectHrMode('B_BALANCED')"
                >
                  <div class="text-center">
                    <v-icon size="24" class="mb-1">mdi-balance</v-icon>
                    <div class="text-h6">B档</div>
                    <div class="text-caption">平衡模式</div>
                  </div>
                </v-btn>
                
                <v-btn
                  value="C_PRO"
                  size="large"
                  class="flex-grow-1"
                  :color="settings.hr_mode === 'C_PRO' ? 'warning' : undefined"
                  @click="selectHrMode('C_PRO')"
                >
                  <div class="text-center">
                    <v-icon size="24" class="mb-1">mdi-fire</v-icon>
                    <div class="text-h6">C档</div>
                    <div class="text-caption">老司机模式</div>
                  </div>
                </v-btn>
              </v-btn-toggle>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mt-4">
        <!-- HR策略设置 -->
        <v-col cols="12" md="6">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-filter-variant</v-icon>
              HR策略过滤
              <v-tooltip>
                <template v-slot:activator="{ props }">
                  <v-icon 
                    v-bind="props" 
                    size="small" 
                    color="grey-lighten-1" 
                    class="ml-2 cursor-pointer"
                  >
                    mdi-help-circle-outline
                  </v-icon>
                </template>
                <div>
                  <strong>HR策略说明：</strong><br>
                  • <strong>忽略：</strong>完全不管HR，显示所有种子<br>
                  • <strong>安全跳过：</strong>默认跳过H&R/HR等高风险种子<br>
                  • <strong>严格跳过：</strong>跳过H&R/HR/H3/H5/UNKNOWN等所有HR种子
                </div>
              </v-tooltip>
            </v-card-title>
            
            <v-card-text>
              <v-select
                v-model="settings.hr_policy"
                :items="hrPolicyOptions"
                label="HR策略"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-shield-check"
                class="mb-4"
                :disabled="settings.hr_mode === 'C_PRO'"
              >
                <template v-slot:append-inner>
                  <v-tooltip v-if="settings.hr_mode === 'C_PRO'" text="C档模式下自动忽略HR限制">
                    <template v-slot:activator="{ props }">
                      <v-icon v-bind="props" color="warning">mdi-lock</v-icon>
                    </template>
                  </v-tooltip>
                </template>
              </v-select>

              <v-divider class="my-4" />
              
              <div class="text-caption text-medium-emphasis mb-2">
                策略说明：
              </div>
              <div class="text-body-2">
                <div v-if="settings.hr_policy === 'IGNORE'">
                  <strong>忽略：</strong>完全不管HR，显示所有种子
                </div>
                <div v-else-if="settings.hr_policy === 'SAFE_SKIP'">
                  <strong>安全跳过：</strong>默认跳过H&R/HR等高风险种子
                </div>
                <div v-else-if="settings.hr_policy === 'STRICT_SKIP'">
                  <strong>严格跳过：</strong>跳过H&R/HR/H3/H5/UNKNOWN等所有HR种子
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 分辨率设置 -->
        <v-col cols="12" md="6">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-high-definition</v-icon>
              分辨率控制
              <v-tooltip>
                <template v-slot:activator="{ props }">
                  <v-icon 
                    v-bind="props" 
                    size="small" 
                    color="grey-lighten-1" 
                    class="ml-2 cursor-pointer"
                  >
                    mdi-help-circle-outline
                  </v-icon>
                </template>
                <div>
                  <strong>分辨率策略说明：</strong><br>
                  • <strong>自动：</strong>根据档位和内容类型自动选择合适分辨率<br>
                  • <strong>最高档位：</strong>只限制最高分辨率，允许低分辨率<br>
                  • <strong>固定档位：</strong>只选择指定分辨率档位的种子
                </div>
              </v-tooltip>
            </v-card-title>
            
            <v-card-text>
              <v-select
                v-model="settings.resolution_policy"
                :items="resolutionPolicyOptions"
                label="分辨率策略"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-cog"
                class="mb-4"
                @update:model-value="onResolutionPolicyChange"
              />

              <v-select
                v-model="settings.resolution_tier"
                :items="resolutionTierOptions"
                label="分辨率档位"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-monitor"
                class="mb-4"
                :disabled="settings.resolution_policy === 'AUTO'"
              >
                <template v-slot:append-inner>
                  <v-tooltip v-if="settings.resolution_policy === 'AUTO'" text="自动模式下档位仅作为参考">
                    <template v-slot:activator="{ props }">
                      <v-icon v-bind="props" color="info">mdi-information</v-icon>
                    </template>
                  </v-tooltip>
                </template>
              </v-select>

              <v-divider class="my-4" />
              
              <div class="text-caption text-medium-emphasis mb-2">
                策略说明：
              </div>
              <div class="text-body-2">
                <div v-if="settings.resolution_policy === 'AUTO'">
                  <strong>自动：</strong>根据档位和内容类型自动选择合适分辨率
                </div>
                <div v-else-if="settings.resolution_policy === 'MAX_TIER'">
                  <strong>最高档位：</strong>只限制最高分辨率，允许低分辨率
                </div>
                <div v-else-if="settings.resolution_policy === 'FIXED_TIER'">
                  <strong>固定档位：</strong>只选择指定分辨率档位的种子
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mt-4">
        <!-- 源质量设置 -->
        <v-col cols="12" md="6">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-quality-high</v-icon>
              源质量控制
            </v-card-title>
            
            <v-card-text>
              <v-select
                v-model="settings.source_quality_policy"
                :items="sourceQualityOptions"
                label="源质量策略"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-video-input-component"
                class="mb-4"
              />

              <v-divider class="my-4" />
              
              <div class="text-caption text-medium-emphasis mb-2">
                策略说明：
              </div>
              <div class="text-body-2">
                <div v-if="settings.source_quality_policy === 'ANY'">
                  <strong>任意：</strong>不限制源质量
                </div>
                <div v-else-if="settings.source_quality_policy === 'NO_TRASH'">
                  <strong>禁用低质：</strong>禁用CAM/TS/TC等明显低质量源
                </div>
                <div v-else-if="settings.source_quality_policy === 'HIGH_ONLY'">
                  <strong>仅高质量：</strong>只要REMUX/BLURAY/UHD/高码WEB-DL
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- HDR设置 -->
        <v-col cols="12" md="6">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-palette</v-icon>
              HDR控制
              <v-tooltip>
                <template v-slot:activator="{ props }">
                  <v-icon 
                    v-bind="props" 
                    size="small" 
                    color="grey-lighten-1" 
                    class="ml-2 cursor-pointer"
                  >
                    mdi-help-circle-outline
                  </v-icon>
                </template>
                <div>
                  <strong>HDR策略说明：</strong><br>
                  • <strong>任意：</strong>不限制HDR或SDR<br>
                  • <strong>HDR优先：</strong>优先HDR，但不强制<br>
                  • <strong>仅SDR：</strong>只选择SDR版本（兼容老电视）
                </div>
              </v-tooltip>
            </v-card-title>
            
            <v-card-text>
              <v-select
                v-model="settings.hdr_policy"
                :items="hdrPolicyOptions"
                label="HDR策略"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-eye"
                class="mb-4"
              />

              <v-divider class="my-4" />
              
              <div class="text-caption text-medium-emphasis mb-2">
                策略说明：
              </div>
              <div class="text-body-2">
                <div v-if="settings.hdr_policy === 'ANY'">
                  <strong>任意：</strong>不限制HDR或SDR
                </div>
                <div v-else-if="settings.hdr_policy === 'HDR_PREFERRED'">
                  <strong>HDR优先：</strong>优先HDR，但不强制
                </div>
                <div v-else-if="settings.hdr_policy === 'SDR_ONLY'">
                  <strong>仅SDR：</strong>只选择SDR版本
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mt-4">
        <!-- 编码设置 -->
        <v-col cols="12" md="6">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-code-tags</v-icon>
              编码控制
            </v-card-title>
            
            <v-card-text>
              <v-select
                v-model="settings.codec_policy"
                :items="codecPolicyOptions"
                label="编码策略"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-file-code"
                class="mb-4"
              />

              <v-divider class="my-4" />
              
              <div class="text-caption text-medium-emphasis mb-2">
                策略说明：
              </div>
              <div class="text-body-2">
                <div v-if="settings.codec_policy === 'ANY'">
                  <strong>任意：</strong>不限制编码格式
                </div>
                <div v-else-if="settings.codec_policy === 'PREFER_H265'">
                  <strong>H265优先：</strong>优先H265/HEVC编码
                </div>
                <div v-else-if="settings.codec_policy === 'PREFER_H264'">
                  <strong>H264优先：</strong>优先H264/AVC编码
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 3D控制 -->
        <v-col cols="12" md="6">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-cube-outline</v-icon>
              3D控制
              <v-tooltip>
                <template v-slot:activator="{ props }">
                  <v-icon 
                    v-bind="props" 
                    size="small" 
                    color="grey-lighten-1" 
                    class="ml-2 cursor-pointer"
                  >
                    mdi-help-circle-outline
                  </v-icon>
                </template>
                <div>
                  <strong>3D策略说明：</strong><br>
                  • <strong>允许3D：</strong>包含3D版本<br>
                  • <strong>禁止3D：</strong>过滤掉所有3D版本（大部分人不需要）
                </div>
              </v-tooltip>
            </v-card-title>
            
            <v-card-text>
              <v-select
                v-model="settings.extra_feature_policy"
                :items="extraFeatureOptions"
                label="3D策略"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-cube"
                class="mb-4"
              />

              <v-divider class="my-4" />
              
              <div class="text-caption text-medium-emphasis mb-2">
                策略说明：
              </div>
              <div class="text-body-2">
                <div v-if="settings.extra_feature_policy === 'ALLOW_3D'">
                  <strong>允许3D：</strong>包含3D版本
                </div>
                <div v-else-if="settings.extra_feature_policy === 'FORBID_3D'">
                  <strong>禁止3D：</strong>过滤掉所有3D版本
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mt-4">
        <!-- 字幕设置 -->
        <v-col cols="12" md="6">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-subtitles</v-icon>
              字幕控制
              <v-tooltip>
                <template v-slot:activator="{ props }">
                  <v-icon 
                    v-bind="props" 
                    size="small" 
                    color="grey-lighten-1" 
                    class="ml-2 cursor-pointer"
                  >
                    mdi-help-circle-outline
                  </v-icon>
                </template>
                <div>
                  <strong>字幕策略说明：</strong><br>
                  • <strong>任意：</strong>不限制字幕语言<br>
                  • <strong>必须中文：</strong>只选择包含简体或繁体中文的版本
                </div>
              </v-tooltip>
            </v-card-title>
            
            <v-card-text>
              <v-select
                v-model="settings.subtitle_policy"
                :items="subtitlePolicyOptions"
                label="字幕策略"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-text"
                class="mb-4"
              />

              <v-divider class="my-4" />
              
              <div class="text-caption text-medium-emphasis mb-2">
                策略说明：
              </div>
              <div class="text-body-2">
                <div v-if="settings.subtitle_policy === 'ANY'">
                  <strong>任意：</strong>不限制字幕
                </div>
                <div v-else-if="settings.subtitle_policy === 'REQUIRE_ZH'">
                  <strong>必须中文：</strong>必须包含简体或繁体中文字幕
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 音轨设置 -->
        <v-col cols="12" md="6">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-music-note</v-icon>
              音轨控制
              <v-tooltip>
                <template v-slot:activator="{ props }">
                  <v-icon 
                    v-bind="props" 
                    size="small" 
                    color="grey-lighten-1" 
                    class="ml-2 cursor-pointer"
                  >
                    mdi-help-circle-outline
                  </v-icon>
                </template>
                <div>
                  <strong>音轨策略说明：</strong><br>
                  • <strong>任意：</strong>不限制音轨语言<br>
                  • <strong>原声优先：</strong>优先选择原声版本，接受多语言<br>
                  • <strong>避开纯国语：</strong>过滤只有国语配音的版本
                </div>
              </v-tooltip>
            </v-card-title>
            
            <v-card-text>
              <v-select
                v-model="settings.audio_lang_policy"
                :items="audioLangPolicyOptions"
                label="音轨策略"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-translate"
                class="mb-4"
              />

              <v-divider class="my-4" />
              
              <div class="text-caption text-medium-emphasis mb-2">
                策略说明：
              </div>
              <div class="text-body-2">
                <div v-if="settings.audio_lang_policy === 'ANY'">
                  <strong>任意：</strong>不限制音轨语言
                </div>
                <div v-else-if="settings.audio_lang_policy === 'ORIGINAL_PREFERRED'">
                  <strong>原声优先：</strong>优先原语言+多轨
                </div>
                <div v-else-if="settings.audio_lang_policy === 'AVOID_MANDARIN_ONLY'">
                  <strong>避开纯国语：</strong>尽量避开只有国语配音的版本
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 操作按钮 -->
      <v-row class="mt-6">
        <v-col cols="12">
          <v-card variant="outlined">
            <v-card-text>
              <div class="text-caption text-medium-emphasis mb-4 text-center">
                <v-icon size="small" class="mr-1">mdi-information-outline</v-icon>
                上述规则为全局默认设置，个别订阅可在高级规则中覆盖。
              </div>
              
              <div class="d-flex justify-end gap-3">
                <v-btn
                  variant="outlined"
                  prepend-icon="mdi-restore"
                  @click="resetToDefault"
                  :loading="resetting"
                >
                  重置为默认
                </v-btn>
                
                <v-btn
                  variant="outlined"
                  prepend-icon="mdi-cog-refresh"
                  @click="resetToCurrentModeDefault"
                  color="info"
                >
                  重置为当前档默认
                </v-btn>
                
                <v-btn
                  variant="outlined"
                  prepend-icon="mdi-refresh"
                  @click="refreshSettings"
                  :loading="loading"
                >
                  刷新
                </v-btn>
                
                <v-btn
                  color="primary"
                  prepend-icon="mdi-content-save"
                  @click="saveSettings"
                  :loading="saving"
                >
                  保存设置
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- C档切换确认对话框 -->
    <v-dialog v-model="showCModeDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="text-h5">
          <v-icon class="mr-2" color="warning">mdi-alert</v-icon>
          切换到「老司机模式」
        </v-card-title>
        
        <v-card-text>
          <v-alert type="error" variant="tonal" class="mb-4">
            <strong>如使用，系统将禁用『网盘移动上传』或『本地移动保存』，避免导致保种炸雷，请谨慎使用。</strong>
          </v-alert>
          
          <div class="text-body-1">
            <p>启用老司机模式后，以下行为将被自动调整：</p>
            <ul>
              <li><strong>STRM生成：</strong>允许</li>
              <li><strong>本地整理：</strong>仅复制/硬链接，禁止移动删除源文件</li>
              <li><strong>网盘整理：</strong>禁止移动上传，仅允许复制</li>
            </ul>
            <p class="mt-3 text-warning">
              <strong>注意：移动整理将被自动关闭，仅保留复制/硬链接/STRM功能。</strong>
            </p>
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="outlined" @click="cancelCModeSwitch">
            取消
          </v-btn>
          <v-btn color="warning" @click="confirmCModeSwitch">
            确认切换
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { globalRulesApi, type GlobalRulesSettings } from '@/api/globalRules'


// 响应式数据
const loading = ref(false)
const saving = ref(false)
const resetting = ref(false)
const showCModeDialog = ref(false)
const pendingMode = ref<string | null>(null)

const settings = reactive<GlobalRulesSettings>({
  hr_mode: 'B_BALANCED',
  hr_policy: 'SAFE_SKIP',
  resolution_policy: 'AUTO',
  resolution_tier: 'HIGH_4K',
  source_quality_policy: 'NO_TRASH',
  hdr_policy: 'ANY',
  codec_policy: 'ANY',
  subtitle_policy: 'ANY',
  audio_lang_policy: 'ANY',
  extra_feature_policy: 'FORBID_3D'
})

// 选项定义
const hrPolicyOptions = [
  { title: '忽略', value: 'IGNORE' },
  { title: '安全跳过', value: 'SAFE_SKIP' },
  { title: '严格跳过', value: 'STRICT_SKIP' }
]

const resolutionPolicyOptions = [
  { title: '自动选择', value: 'AUTO' },
  { title: '最高档位', value: 'MAX_TIER' },
  { title: '固定档位', value: 'FIXED_TIER' }
]

const resolutionTierOptions = [
  { title: '720p及以下', value: 'LOW_720P' },
  { title: '1080p及以下', value: 'MID_1080P' },
  { title: '4K及以下', value: 'HIGH_4K' }
]

const sourceQualityOptions = [
  { title: '任意', value: 'ANY' },
  { title: '禁用低质', value: 'NO_TRASH' },
  { title: '仅高质量', value: 'HIGH_ONLY' }
]

const hdrPolicyOptions = [
  { title: '任意', value: 'ANY' },
  { title: 'HDR优先', value: 'HDR_PREFERRED' },
  { title: '仅SDR', value: 'SDR_ONLY' }
]

const codecPolicyOptions = [
  { title: '任意', value: 'ANY' },
  { title: 'H265优先', value: 'PREFER_H265' },
  { title: 'H264优先', value: 'PREFER_H264' }
]

const subtitlePolicyOptions = [
  { title: '任意', value: 'ANY' },
  { title: '必须中文', value: 'REQUIRE_ZH' }
]

const audioLangPolicyOptions = [
  { title: '任意', value: 'ANY' },
  { title: '原声优先', value: 'ORIGINAL_PREFERRED' },
  { title: '避开纯国语', value: 'AVOID_MANDARIN_ONLY' }
]

const extraFeatureOptions = [
  { title: '允许3D', value: 'ALLOW_3D' },
  { title: '禁止3D', value: 'FORBID_3D' }
]

// 三档模式默认配置映射
const defaultProfiles = {
  A_SAFE: {
    hr_policy: 'STRICT_SKIP',
    resolution_policy: 'MAX_TIER',
    resolution_tier: 'MID_1080P',
    source_quality_policy: 'NO_TRASH',
    hdr_policy: 'SDR_ONLY',
    codec_policy: 'ANY',
    subtitle_policy: 'ANY',
    audio_lang_policy: 'ANY',
    extra_feature_policy: 'FORBID_3D'
  },
  B_BALANCED: {
    hr_policy: 'SAFE_SKIP',
    resolution_policy: 'AUTO',
    resolution_tier: 'HIGH_4K',
    source_quality_policy: 'NO_TRASH',
    hdr_policy: 'ANY',
    codec_policy: 'ANY',
    subtitle_policy: 'ANY',
    audio_lang_policy: 'ANY',
    extra_feature_policy: 'FORBID_3D'
  },
  C_PRO: {
    hr_policy: 'IGNORE',
    resolution_policy: 'AUTO',
    resolution_tier: 'HIGH_4K',
    source_quality_policy: 'ANY',
    hdr_policy: 'HDR_PREFERRED',
    codec_policy: 'ANY',
    subtitle_policy: 'ANY',
    audio_lang_policy: 'ANY',
    extra_feature_policy: 'FORBID_3D'
  }
}

// 方法
const loadSettings = async () => {
  try {
    loading.value = true
    const response = await globalRulesApi.getGlobalRules()
    Object.assign(settings, response.data)
  } catch (error) {
    console.error('加载全局规则设置失败:', error)
    alert('加载设置失败')
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  try {
    saving.value = true
    await globalRulesApi.updateGlobalRules(settings)
    alert('设置保存成功')
  } catch (error) {
    console.error('保存全局规则设置失败:', error)
    alert('保存设置失败')
  } finally {
    saving.value = false
  }
}

const resetToDefault = async () => {
  try {
    resetting.value = true
    const response = await globalRulesApi.resetGlobalRules()
    Object.assign(settings, response.data)
    alert('已重置为默认设置')
  } catch (error) {
    console.error('重置全局规则设置失败:', error)
    alert('重置设置失败')
  } finally {
    resetting.value = false
  }
}

const refreshSettings = async () => {
  await loadSettings()
  alert('设置已刷新')
}

// HR模式切换处理
const selectHrMode = (mode: GlobalRulesSettings['hr_mode']) => {
  // 如果切换到C档且当前不是C档，显示确认对话框
  if (mode === 'C_PRO' && settings.hr_mode !== 'C_PRO') {
    pendingMode.value = mode
    showCModeDialog.value = true
  } else {
    // 其他情况直接切换
    settings.hr_mode = mode
  }
}

// 确认切换到C档
const confirmCModeSwitch = () => {
  if (pendingMode.value) {
    settings.hr_mode = pendingMode.value as GlobalRulesSettings['hr_mode']
  }
  showCModeDialog.value = false
  pendingMode.value = null
}

// 取消切换到C档
const cancelCModeSwitch = () => {
  showCModeDialog.value = false
  pendingMode.value = null
}

// 重置为当前档默认配置
const resetToCurrentModeDefault = () => {
  const currentMode = settings.hr_mode as keyof typeof defaultProfiles
  const defaultProfile = defaultProfiles[currentMode]
  
  if (defaultProfile) {
    // 保留当前的hr_mode，重置其他所有配置
    Object.assign(settings, defaultProfile)
    settings.hr_mode = currentMode // 确保当前模式不变
    alert(`已重置为${currentMode === 'A_SAFE' ? 'A档保种安全' : currentMode === 'B_BALANCED' ? 'B档平衡' : 'C档老司机'}模式的默认配置`)
  }
}

const onResolutionPolicyChange = (value: string) => {
  if (value === 'AUTO') {
    // 自动模式下，档位仅作为参考，可以重置为推荐值
    if (settings.hr_mode === 'A_SAFE') {
      settings.resolution_tier = 'MID_1080P'
    } else if (settings.hr_mode === 'B_BALANCED' || settings.hr_mode === 'C_PRO') {
      settings.resolution_tier = 'HIGH_4K'
    }
  }
}

// 生命周期
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.global-rules-settings {
  min-height: 100vh;
}

.v-btn-toggle .v-btn {
  min-width: 120px;
  height: 80px !important;
}

.text-caption {
  line-height: 1.4;
}

.text-body-2 {
  line-height: 1.5;
}

.text-body-2 ul {
  margin: 0;
  padding-left: 20px;
}

.text-body-2 li {
  margin-bottom: 4px;
}
</style>
