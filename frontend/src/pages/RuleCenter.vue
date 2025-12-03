<template>
  <div class="rule-center">
    <PageHeader
      title="规则中心"
      subtitle="管理订阅默认配置和过滤规则组"
    />

    <v-container fluid class="pa-4">
      <v-row>
        <v-col cols="12">
          <v-card variant="outlined">
            <v-tabs
              v-model="activeTab"
              color="primary"
              grow
              density="comfortable"
            >
              <v-tab value="defaults">
                <v-icon class="mr-2">mdi-cog-outline</v-icon>
                订阅默认配置
              </v-tab>
              <v-tab value="rule-groups">
                <v-icon class="mr-2">mdi-filter-variant</v-icon>
                过滤规则组
              </v-tab>
            </v-tabs>

            <v-window v-model="activeTab">
              <!-- 订阅默认配置标签页 -->
              <v-window-item value="defaults">
                <DefaultSubscriptionConfig />
              </v-window-item>

              <!-- 过滤规则组标签页 -->
              <v-window-item value="rule-groups">
                <FilterRuleGroups />
              </v-window-item>
            </v-window>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DefaultSubscriptionConfig from '@/components/rule-center/DefaultSubscriptionConfig.vue'
import FilterRuleGroups from '@/components/rule-center/FilterRuleGroups.vue'

const activeTab = ref('defaults')
</script>

<style scoped>
.rule-center {
  min-height: 100vh;
}

.v-window-item {
  padding: 24px;
}
</style>
