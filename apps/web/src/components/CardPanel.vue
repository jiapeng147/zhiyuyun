<template>
  <n-card class="card-panel naive-admin-card" :bordered="true">
    <template v-if="title || $slots.title || $slots.desc || desc || $slots.action" #header>
      <div class="panel-head naive-admin-card-head">
        <div>
          <h3><slot name="title">{{ title }}</slot></h3>
          <p v-if="$slots.desc || desc"><slot name="desc">{{ desc }}</slot></p>
        </div>
        <slot name="action" />
      </div>
    </template>
    <div class="card-panel-body"><slot /></div>
  </n-card>
</template>

<script setup>
import { NCard } from 'naive-ui'

defineProps({ title: String, desc: String })
</script>

<style scoped>
.card-panel {
  min-width: 0;
}
.card-panel-body {
  min-width: 0;
  overflow-x: clip;
}
</style>
