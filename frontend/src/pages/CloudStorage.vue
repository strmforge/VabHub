<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <span class="text-h5">云存储管理</span>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              prepend-icon="mdi-plus"
              @click="openCreateDialog"
            >
              添加云存储
            </v-btn>
          </v-card-title>
          
          <v-card-text>
            <!-- 云存储列表 -->
            <v-row v-if="storages.length > 0">
              <v-col
                v-for="storage in storages"
                :key="storage.id"
                cols="12"
                md="6"
                lg="4"
              >
                <CloudStorageCard
                  :storage="storage"
                  @refresh="loadStorages"
                  @authenticate="handleAuthenticate"
                  @view-files="handleViewFiles"
                />
              </v-col>
            </v-row>
            
            <!-- 空状态 -->
            <v-alert
              v-else
              type="info"
              variant="tonal"
              class="mt-4"
            >
              还没有配置云存储，点击"添加云存储"按钮开始配置。
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- 创建/编辑对话框 -->
    <CloudStorageDialog
      v-model="dialogVisible"
      :storage="selectedStorage"
      @saved="handleSaved"
    />
    
    <!-- 二维码登录对话框（115网盘） -->
    <QRCodeDialog
      v-model="qrDialogVisible"
      :storage-id="selectedStorageId"
      @authenticated="handleAuthenticated"
    />
    
    <!-- 文件管理对话框 -->
    <FileManagerDialog
      v-model="fileManagerVisible"
      :storage-id="selectedStorageId"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import CloudStorageCard from '@/components/cloud-storage/CloudStorageCard.vue'
import CloudStorageDialog from '@/components/cloud-storage/CloudStorageDialog.vue'
import QRCodeDialog from '@/components/cloud-storage/QRCodeDialog.vue'
import FileManagerDialog from '@/components/cloud-storage/FileManagerDialog.vue'

const storages = ref<any[]>([])
const dialogVisible = ref(false)
const qrDialogVisible = ref(false)
const fileManagerVisible = ref(false)
const selectedStorage = ref<any>(null)
const selectedStorageId = ref<number | null>(null)
const loading = ref(false)

// 加载云存储列表
const loadStorages = async () => {
  try {
    loading.value = true
    const response = await api.get('/cloud-storage')
    storages.value = response.data
  } catch (error) {
    console.error('加载云存储列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 打开创建对话框
const openCreateDialog = () => {
  selectedStorage.value = null
  dialogVisible.value = true
}

// 处理保存
const handleSaved = () => {
  dialogVisible.value = false
  loadStorages()
}

// 处理认证
const handleAuthenticate = (storage: any) => {
  if (storage.provider === '115') {
    selectedStorageId.value = storage.id
    qrDialogVisible.value = true
  } else {
    // 其他提供商的认证方式
    console.log('其他提供商的认证方式')
  }
}

// 处理认证成功
const handleAuthenticated = () => {
  qrDialogVisible.value = false
  loadStorages()
}

// 处理查看文件
const handleViewFiles = (storage: any) => {
  selectedStorageId.value = storage.id
  fileManagerVisible.value = true
}

onMounted(() => {
  loadStorages()
})
</script>

<style scoped>
</style>

