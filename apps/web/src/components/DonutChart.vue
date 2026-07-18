<template>
  <div class="donut-row">
    <div class="donut">
      <svg class="donut-svg" viewBox="0 0 42 42" aria-hidden="true">
        <circle class="donut-track" cx="21" cy="21" r="15.9155" />
        <circle
          v-for="segment in segments"
          :key="segment.key"
          :class="['donut-segment', segment.tone]"
          cx="21"
          cy="21"
          r="15.9155"
          :stroke-dasharray="segment.dasharray"
          :stroke-dashoffset="segment.dashoffset"
        />
      </svg>
      <strong>{{ center }}</strong>
      <span>{{ label }}</span>
    </div>
    <div class="donut-legend">
      <div v-for="item in legendItems" :key="item.label"><i :class="item.tone"></i><span>{{ item.label }}</span><b>{{ item.value }}</b></div>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ center: String, label: String, items: Array })
const tones = ['tone-orange', 'tone-green', 'tone-amber', 'tone-red', 'tone-coral', 'tone-cyan']
const legendItems = computed(() => (props.items || []).map((item, index) => ({
  ...item,
  tone: tones[index % tones.length],
})))
const segments = computed(() => {
  const values = (props.items || []).map(item => Math.max(0, Number(item?.value) || 0))
  const total = values.reduce((sum, value) => sum + value, 0)
  if (!total) return []
  let cursor = 0
  return values.map((value, index) => {
    const start = cursor
    const length = (value / total) * 100
    cursor += length
    return {
      key: `${index}-${start.toFixed(2)}`,
      tone: tones[index % tones.length],
      dasharray: `${length.toFixed(2)} ${(100 - length).toFixed(2)}`,
      dashoffset: `${(-start).toFixed(2)}`,
    }
  })
})
</script>

<style scoped>
.donut-row {
  display: flex;
  align-items: center;
  gap: 24px;
}

.donut {
  position: relative;
  display: flex;
  width: 176px;
  height: 176px;
  flex: 0 0 auto;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.donut-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.donut-track,
.donut-segment {
  fill: none;
  stroke-width: 10;
}

.donut-track {
  stroke: #eef2f7;
}

.donut-segment {
  stroke-linecap: butt;
}

.donut-segment.tone-orange,
.donut-legend i.tone-orange { stroke: #ff5e19; background: #ff5e19; }
.donut-segment.tone-green,
.donut-legend i.tone-green { stroke: #18c785; background: #18c785; }
.donut-segment.tone-amber,
.donut-legend i.tone-amber { stroke: #ffb020; background: #ffb020; }
.donut-segment.tone-red,
.donut-legend i.tone-red { stroke: #ff6b6b; background: #ff6b6b; }
.donut-segment.tone-coral,
.donut-legend i.tone-coral { stroke: #ff8d5c; background: #ff8d5c; }
.donut-segment.tone-cyan,
.donut-legend i.tone-cyan { stroke: #33cdd2; background: #33cdd2; }

.donut::after {
  position: absolute;
  inset: 32px;
  border-radius: 50%;
  background: #fff;
  box-shadow: inset 0 0 0 1px #F0F0F0;
  content: "";
}

.donut strong,
.donut span {
  position: relative;
  z-index: 2;
}

.donut strong {
  font-size: 22px;
}

.donut span {
  margin-top: 4px;
  color: #758198;
  font-size: 13px;
}

.donut-legend {
  flex: 1;
}

.donut-legend div {
  display: flex;
  height: 31px;
  align-items: center;
  gap: 9px;
  color: #4b5870;
}

.donut-legend i {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.donut-legend b {
  margin-left: auto;
  color: #1b2942;
}
</style>
