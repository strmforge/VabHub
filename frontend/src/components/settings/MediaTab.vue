<!-- 媒体标签页 -->
<template>
  <div>
    <!-- TMDB API Key配置 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="text-subtitle-1 font-weight-medium">
        <v-icon icon="mdi-key" class="me-2" />
        TMDB API Key
      </v-card-title>
      <v-card-text>
        <v-text-field
          v-model="modelValue.TMDB_API_KEY"
          label="TMDB API Key"
          hint="请前往 TMDB 官网申请您的 API Key。这是使用 TMDB 功能的必需配置。"
          persistent-hint
          type="password"
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-key-variant"
          class="mb-2"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
        <v-btn
          color="primary"
          variant="text"
          prepend-icon="mdi-open-in-new"
          href="https://www.themoviedb.org/settings/api"
          target="_blank"
          size="small"
        >
          前往 TMDB 申请 API Key
        </v-btn>
        <v-alert
          v-if="!modelValue.TMDB_API_KEY"
          type="warning"
          density="compact"
          class="mt-2"
        >
          TMDB API Key 未配置，媒体搜索和识别功能将无法使用。
        </v-alert>
      </v-card-text>
    </v-card>

    <v-row>
      <v-col cols="12" md="6">
        <v-combobox
          v-model="modelValue.TMDB_API_DOMAIN"
          label="TMDB API域名"
          hint="TMDB API域名"
          persistent-hint
          :items="['api.themoviedb.org', 'api.tmdb.org']"
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-api"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-combobox
          v-model="modelValue.TMDB_IMAGE_DOMAIN"
          label="TMDB图片域名"
          hint="TMDB图片域名"
          persistent-hint
          :items="['image.tmdb.org']"
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-image"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-select
          v-model="modelValue.TMDB_LOCALE"
          label="TMDB元数据语言"
          hint="TMDB元数据语言"
          persistent-hint
          :items="tmdbLanguageItems"
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-translate"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model.number="modelValue.META_CACHE_EXPIRE"
          label="元数据缓存过期时间"
          hint="元数据缓存过期时间（小时），0为自动"
          persistent-hint
          type="number"
          min="0"
          suffix="小时"
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-timer"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.SCRAP_FOLLOW_TMDB"
          label="刮削跟随TMDB"
          hint="刮削时跟随TMDB设置"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.TMDB_SCRAP_ORIGINAL_IMAGE"
          label="刮削原始图片"
          hint="使用TMDB原始语种图片"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.FANART_ENABLE"
          label="Fanart启用"
          hint="启用Fanart图片源"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col v-if="modelValue.FANART_ENABLE" cols="12" md="6">
        <v-select
          v-model="fanartLanguageSelection"
          label="Fanart语言"
          hint="Fanart语言设置（多选）"
          persistent-hint
          :items="fanartLanguageItems"
          multiple
          chips
          closable-chips
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-translate"
        />
      </v-col>
    </v-row>

    <!-- 刮削开关设置 -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-expansion-panels variant="accordion">
          <v-expansion-panel>
            <v-expansion-panel-title class="text-lg">
              <template #default>
                <v-icon icon="mdi-checkbox-multiple-outline" class="me-2" />
                刮削开关设置
              </template>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <!-- 电影 -->
              <v-row>
                <v-col cols="12" class="pb-2">
                  <v-list-subheader class="text-lg">电影</v-list-subheader>
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.movie_nfo"
                    label="NFO"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.movie_poster"
                    label="海报"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.movie_backdrop"
                    label="背景图"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.movie_logo"
                    label="Logo"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.movie_disc"
                    label="光盘图"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.movie_banner"
                    label="横幅图"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.movie_thumb"
                    label="缩略图"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
              </v-row>

              <v-divider class="my-4" />

              <!-- 电视剧 -->
              <v-row>
                <v-col cols="12" class="pb-2">
                  <v-list-subheader class="text-lg">电视剧</v-list-subheader>
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.tv_nfo"
                    label="NFO"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.tv_poster"
                    label="海报"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.tv_backdrop"
                    label="背景图"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.tv_banner"
                    label="横幅图"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.tv_logo"
                    label="Logo"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.tv_thumb"
                    label="缩略图"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
              </v-row>

              <v-divider class="my-4" />

              <!-- 季 -->
              <v-row>
                <v-col cols="12" class="pb-2">
                  <v-list-subheader class="text-lg">季</v-list-subheader>
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.season_nfo"
                    label="NFO"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.season_poster"
                    label="海报"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.season_banner"
                    label="横幅图"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.season_thumb"
                    label="缩略图"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
              </v-row>

              <v-divider class="my-4" />

              <!-- 集 -->
              <v-row>
                <v-col cols="12" class="pb-2">
                  <v-list-subheader class="text-lg">集</v-list-subheader>
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.episode_nfo"
                    label="NFO"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
                <v-col cols="6" md="3">
                  <v-checkbox
                    v-model="scrapingSwitches.episode_thumb"
                    label="缩略图"
                    density="compact"
                    @update:model-value="$emit('update:scrapingSwitches', scrapingSwitches)"
                  />
                </v-col>
              </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: any
  scrapingSwitches: any
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'update:modelValue': [value: any], 'update:scrapingSwitches': [value: any] }>()

const tmdbLanguageItems = [
  { title: '简体中文', value: 'zh' },
  { title: '繁体中文', value: 'zh-TW' },
  { title: 'English', value: 'en' }
]

const fanartLanguageItems = [
  { title: '简体中文', value: 'zh' },
  { title: 'English', value: 'en' },
  { title: '日本語', value: 'ja' },
  { title: '한국어', value: 'ko' },
  { title: 'Deutsch', value: 'de' },
  { title: 'Français', value: 'fr' },
  { title: 'Español', value: 'es' },
  { title: 'Italiano', value: 'it' },
  { title: 'Português', value: 'pt' },
  { title: 'Русский', value: 'ru' }
]

const fanartLanguageSelection = computed({
  get: () => {
    if (!props.modelValue.FANART_LANG) return []
    return props.modelValue.FANART_LANG.split(',').filter(Boolean).map((lang: string) => lang.trim())
  },
  set: (val: string[]) => {
    props.modelValue.FANART_LANG = val.join(',')
    emit('update:modelValue', props.modelValue)
  }
})
</script>

