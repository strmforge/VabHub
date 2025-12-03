import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { tvWallApi } from '@/services/api'
import type { PlayerWallWorkSummary, TvWallSmartOpenResponse } from '@/types/playerWall'

interface SmartOpenOptions {
  work: PlayerWallWorkSummary
}

export function useSmartTvWallOpen() {
  const router = useRouter()
  const toast = useToast()
  const smartOpenLoading = ref(false)

  const openMediaDetailFallback = async (work: PlayerWallWorkSummary) => {
    if (work.tmdb_id) {
      await router.push({
        name: 'MediaDetail',
        params: {
          type: work.media_type || 'movie',
          tmdbId: work.tmdb_id
        }
      })
    } else {
      toast.info('缺少 TMDB 信息，已保留当前页面')
    }
  }

  const handleDecision = async (work: PlayerWallWorkSummary, response: TvWallSmartOpenResponse) => {
    const decision = response.decision

    if (decision.kind === 'media_library' && decision.url) {
      window.open(decision.url, '_blank', 'noopener')
      return
    }

    await openMediaDetailFallback(work)
  }

  const openSmartTvWall = async ({ work }: SmartOpenOptions) => {
    if (!work || !work.id) {
      await openMediaDetailFallback(work)
      return
    }

    try {
      smartOpenLoading.value = true
      const response = await tvWallApi.smartOpen({
        media_id: work.id,
        media_type: work.media_type || 'movie'
      })
      await handleDecision(work, response)
    } catch (error: any) {
      console.error('电视墙智能打开失败:', error)
      toast.error(error?.response?.data?.detail || error?.message || '智能打开失败，已回退至详情页')
      await openMediaDetailFallback(work)
    } finally {
      smartOpenLoading.value = false
    }
  }

  return {
    smartOpenLoading,
    openSmartTvWall
  }
}
