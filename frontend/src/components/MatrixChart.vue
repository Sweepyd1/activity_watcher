<!-- components/MatrixChart.vue -->
<template>
  <canvas ref="chartCanvas"></canvas>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { Chart } from 'chart.js'
import { MatrixController, MatrixElement } from 'chartjs-chart-matrix'

// Регистрируем матричный контроллер
Chart.register(MatrixController, MatrixElement)

const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  options: {
    type: Object,
    default: () => ({})
  }
})

const chartCanvas = ref(null)
let chartInstance = null

onMounted(() => {
  if (!chartCanvas.value) return
  
  chartInstance = new Chart(chartCanvas.value, {
    type: 'matrix',
    data: props.data,
    options: props.options
  })
})

// Обновляем график при изменении данных
watch(() => props.data, (newData) => {
  if (chartInstance) {
    chartInstance.data = newData
    chartInstance.update()
  }
}, { deep: true })

// Очищаем при размонтировании
onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>