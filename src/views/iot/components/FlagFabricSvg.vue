<template>
  <g class="flag-fabric-group">
    <defs>
      <!-- 动态波浪剪裁路径 -->
      <clipPath :id="clipId">
        <path :d="wavePath" />
      </clipPath>
    </defs>

    <!-- 剪裁范围内的旗帜内容与微光感 -->
    <g :clip-path="`url(#${clipId})`">
      <!-- 1. 未选定国家 -->
      <g v-if="!country">
        <rect x="0" y="0" :width="width" :height="height" fill="#64748B" />
        <text
          :x="width / 2"
          :y="height / 2 + 4"
          text-anchor="middle"
          fill="#FFFFFF"
          font-size="11"
          font-weight="bold"
          letter-spacing="1"
        >未选定</text>
      </g>

      <!-- 2. 上传的真实高清国旗图片 -->
      <image
        v-else-if="country.imageUrl"
        :href="country.imageUrl"
        x="0"
        y="0"
        :width="width"
        :height="height"
        preserveAspectRatio="xMidYMid slice"
      />

      <!-- 3. 五星红旗 (中华人民共和国) -->
      <g v-else-if="country.pattern === 'cn'">
        <rect x="0" y="0" :width="width" :height="height" :fill="country.c1 || '#DE2910'" />
        <!-- 大五角星 -->
        <polygon :points="bigStarPoints" :fill="country.c2 || '#FFDE00'" />
        <!-- 4 颗小五角星 (角度指向大星中心) -->
        <polygon
          v-for="(star, idx) in smallStars"
          :key="idx"
          :points="star.points"
          :fill="country.c2 || '#FFDE00'"
        />
      </g>

      <!-- 4. 太阳/圆旗 (如日本、韩国、巴西等) -->
      <g v-else-if="country.pattern === 'sun'">
        <rect x="0" y="0" :width="width" :height="height" :fill="country.c1" />
        <!-- 12 根太阳光辉射线 -->
        <line
          v-for="(ray, idx) in sunRays"
          :key="idx"
          :x1="ray.x1"
          :y1="ray.y1"
          :x2="ray.x2"
          :y2="ray.y2"
          :stroke="country.c2"
          :stroke-width="Math.max(1.4, height * 0.05)"
          stroke-linecap="round"
        />
        <!-- 太阳中心圆 -->
        <circle :cx="width / 2" :cy="height / 2" :r="height * 0.26" :fill="country.c2" />
      </g>

      <!-- 5. 横条纹双色旗 (如美条纹等) -->
      <g v-else-if="country.pattern === 'stripes'">
        <rect
          v-for="i in 6"
          :key="i"
          x="0"
          :y="(i - 1) * (height / 6)"
          :width="width"
          :height="height / 6 + 0.6"
          :fill="i % 2 === 0 ? country.c2 : country.c1"
        />
      </g>

      <!-- 6. 三横色带旗 (如德、俄、荷、西等) -->
      <g v-else-if="country.pattern === 'triband-h'">
        <rect x="0" y="0" :width="width" :height="height / 3" :fill="country.c1" />
        <rect x="0" :y="height / 3" :width="width" :height="height / 3" :fill="country.c2" />
        <rect x="0" :y="(2 * height) / 3" :width="width" :height="height / 3 + 0.6" :fill="country.c3" />
      </g>

      <!-- 7. 三纵色带旗 (如法、意、爱尔兰等) -->
      <g v-else-if="country.pattern === 'tricolor'">
        <rect x="0" y="0" :width="width / 3" :height="height" :fill="country.c1" />
        <rect :x="width / 3" y="0" :width="width / 3" :height="height" :fill="country.c2" />
        <rect :x="(2 * width) / 3" y="0" :width="width / 3 + 0.6" :height="height" :fill="country.c3" />
      </g>

      <!-- 8. 十字旗 (如瑞士、英国、北欧等) -->
      <g v-else-if="country.pattern === 'cross'">
        <rect x="0" y="0" :width="width" :height="height" :fill="country.c1" />
        <rect :x="width * 0.36" y="0" :width="width * 0.14" :height="height" :fill="country.c2" />
        <rect x="0" :y="height * 0.38" :width="width" :height="height * 0.17" :fill="country.c2" />
      </g>

      <!-- 9. 星徽旗 -->
      <g v-else-if="country.pattern === 'stars'">
        <rect x="0" y="0" :width="width" :height="height" :fill="country.c1" />
        <polygon :points="calcStar(width * 0.26, height * 0.32, height * 0.16)" :fill="country.c2" />
        <polygon :points="calcStar(width * 0.6, height * 0.24, height * 0.1)" :fill="country.c2" />
        <polygon :points="calcStar(width * 0.74, height * 0.5, height * 0.1)" :fill="country.c2" />
        <polygon :points="calcStar(width * 0.52, height * 0.68, height * 0.1)" :fill="country.c2" />
        <polygon :points="calcStar(width * 0.24, height * 0.7, height * 0.09)" :fill="country.c2" />
      </g>

      <!-- 10. 纯色单色旗或回退模式 -->
      <g v-else>
        <rect x="0" y="0" :width="width" :height="height" :fill="country.c1 || '#3A4A5E'" />
      </g>

      <!-- 丝绸光泽与微弱飘动阴影层 (增加立体感) -->
      <rect x="0" y="0" :width="width * 0.08" :height="height" fill="rgba(0,0,0,0.12)" />
      <rect :x="width * 0.9" y="0" :width="width * 0.1" :height="height" fill="rgba(255,255,255,0.12)" />
    </g>
  </g>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  country: {
    type: Object,
    default: null
  },
  width: {
    type: Number,
    default: 76
  },
  height: {
    type: Number,
    default: 50
  },
  phase: {
    type: Number,
    default: 0
  },
  clipId: {
    type: String,
    required: true
  },
  static: {
    type: Boolean,
    default: false
  }
})

// 计算五角星定点坐标
function calcStar(cx, cy, r, rot = 0) {
  const pts = []
  for (let i = 0; i < 5; i++) {
    const a = -Math.PI / 2 + i * (Math.PI * 2 / 5) + rot
    pts.push(`${(cx + Math.cos(a) * r).toFixed(1)},${(cy + Math.sin(a) * r).toFixed(1)}`)
    const a2 = a + Math.PI / 5
    pts.push(`${(cx + Math.cos(a2) * r * 0.42).toFixed(1)},${(cy + Math.sin(a2) * r * 0.42).toFixed(1)}`)
  }
  return pts.join(' ')
}

// 动态波浪轮廓路径 (贝塞尔曲线) 或 静态平整悬垂轮廓 (横向一杆挂三旗模式)
const wavePath = computed(() => {
  const w = props.width
  const h = props.height
  if (props.static) {
    return `M 0 0 L ${w} 0 L ${w} ${h} L 0 ${h} Z`
  }
  const p = props.phase
  const topMidY = Math.sin(p) * 3.2
  const topRightY = Math.sin(p + 1.4) * 5.5
  const bottomRightY = h + Math.sin(p + 2.2) * 5.5
  const bottomMidY = h + Math.sin(p + 0.7) * 3.2
  return `M 0 0 Q ${(w * 0.5).toFixed(1)} ${topMidY.toFixed(2)} ${w} ${topRightY.toFixed(2)} L ${w} ${bottomRightY.toFixed(2)} Q ${(w * 0.5).toFixed(1)} ${bottomMidY.toFixed(2)} 0 ${h} Z`
})

// 五星红旗大星
const bigStarPoints = computed(() => {
  const bx = props.width * 0.24
  const by = props.height * 0.3
  const r = props.height * 0.17
  return calcStar(bx, by, r, 0)
})

// 五星红旗 4 颗小星 (朝向大星中心)
const smallStars = computed(() => {
  const bx = props.width * 0.24
  const by = props.height * 0.3
  const w = props.width
  const h = props.height
  const smallCoords = [
    [w * 0.48, h * 0.14],
    [w * 0.58, h * 0.22],
    [w * 0.56, h * 0.38],
    [w * 0.42, h * 0.38]
  ]
  return smallCoords.map(([sx, sy]) => {
    const ang = Math.atan2(by - sy, bx - sx) + Math.PI / 2
    return {
      points: calcStar(sx, sy, h * 0.055, ang)
    }
  })
})

// 太阳光辉射线
const sunRays = computed(() => {
  const cx = props.width / 2
  const cy = props.height / 2
  const r = props.height * 0.26
  const rays = []
  for (let i = 0; i < 12; i++) {
    const a = (i * Math.PI) / 6
    rays.push({
      x1: +(cx + Math.cos(a) * r * 1.3).toFixed(1),
      y1: +(cy + Math.sin(a) * r * 1.3).toFixed(1),
      x2: +(cx + Math.cos(a) * r * 1.9).toFixed(1),
      y2: +(cy + Math.sin(a) * r * 1.9).toFixed(1)
    })
  }
  return rays
})
</script>

<style scoped>
.flag-fabric-group {
  user-select: none;
  pointer-events: none;
}
</style>
