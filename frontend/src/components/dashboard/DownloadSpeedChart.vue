<template>
  <div class="download-speed-chart">
    <!-- TODO: 集成ApexCharts -->
    <div class="text-center text-medium-emphasis py-8">
      图表组件（待集成ApexCharts）
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data: any[]
}

const props = defineProps<Props>()

const series = computed(() => [
  {
    name: '下载速度',
    data: props.data || []
  }
])

const chartOptions = {
  chart: {
    type: 'area',
    toolbar: { show: false },
    zoom: { enabled: false }
  },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth' },
  xaxis: {
    type: 'datetime'
  },
  yaxis: {
    labels: {
      formatter: (val: number) => `${(val / 1024 / 1024).toFixed(2)} MB/s`
    }
  },
  colors: ['#2196F3'],
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.7,
      opacityTo: 0.3
    }
  }
}
</script>

