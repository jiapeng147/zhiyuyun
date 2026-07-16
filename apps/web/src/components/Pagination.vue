<template>
  <div v-if="totalPages > 1 || showTotal" class="pagination naive-admin-pagination">
    <n-pagination
      v-if="totalPages > 1"
      :page="currentNum"
      :page-count="totalPages"
      :page-size="pageSizeNum"
      :page-sizes="sizes"
      :show-size-picker="sizes.length > 0"
      :display-order="['pages', 'size-picker']"
      @update:page="go"
      @update:page-size="onNaiveSizeChange"
    >
      <template #prefix>共 {{ totalNum }} 条</template>
    </n-pagination>
    <span v-else class="page-info">共 {{ totalNum }} 条</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { NPagination } from 'naive-ui'

const props = defineProps({
  total: { type: [Number, String], default: 0 },
  current: { type: [Number, String], default: 1 },
  pageSize: { type: [Number, String], default: 20 },
  sizes: { type: Array, default: () => [] }, // 如 [10, 20, 50, 100]，空数组则不显示每页条数选择
  maxVisible: { type: Number, default: 7 }, // 最多显示的页码按钮数（含省略号）
  showTotal: { type: Boolean, default: true } // 单页时是否仍显示"共 N 条"
})
const emit = defineEmits(['page-change', 'size-change'])

const totalNum = computed(() => Number(props.total) || 0)
const currentNum = computed(() => Number(props.current) || 1)
const pageSizeNum = computed(() => Number(props.pageSize) || 20)
const totalPages = computed(() => Math.max(1, Math.ceil(totalNum.value / pageSizeNum.value)))

function go(p) {
  if (p < 1 || p > totalPages.value || p === currentNum.value) return
  emit('page-change', p)
}

function onNaiveSizeChange(size) {
  emit('size-change', Number(size))
}
</script>

<style scoped>
.pagination { display: flex; align-items: center; justify-content: flex-end; gap: 10px; }
.page-info { color: var(--muted); font-size: 13px; }
</style>
